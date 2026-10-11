import hashlib
import json
from collections import Counter, defaultdict
from itertools import batched
from multiprocessing import Pool
from pathlib import Path

import regex
from tqdm import tqdm

from cleaning.normalize import normalize

SOURCES = ["voa", "wikipedia", "wikisource", "madlad"]
RAW = Path("data/raw")
CLEAN = Path("data/clean")
FILTERED = CLEAN / "filtered.jsonl"
DOCS = CLEAN / "docs.jsonl"
STATS = CLEAN / "stats.json"

END_OF_TEXT = "<|endoftext|>"
MIN_URDU_LETTER_SHARE = 0.5
MIN_WIKIPEDIA_CHARS = 500
BOILERPLATE_MIN_DOCS = 5
SPAM_TERMS = ["فاریکس", "بائنری آپشن"]

FILTER_STEPS = ["raw", "normalized", "urdu_lines", "spam", "min_length"]
BATCH_SIZE = 20_000
CHUNK_SIZE = 200

LETTER = regex.compile(r"\p{L}")
ARABIC_LETTER = regex.compile(r"(?=\p{L})\p{Arabic}")


def is_mostly_urdu(line):
    letters = len(LETTER.findall(line))
    return letters > 0 and len(ARABIC_LETTER.findall(line)) / letters >= MIN_URDU_LETTER_SHARE


def urdu_lines(text):
    return "\n".join(line for line in text.split("\n") if is_mostly_urdu(line))


def is_spam(text):
    return any(term in text for term in SPAM_TERMS)


def without_boilerplate(text, line_counts):
    return "\n".join(line for line in text.split("\n") if line_counts[line_hash(line)] < BOILERPLATE_MIN_DOCS)


def line_hash(line):
    return hashlib.blake2b(line.encode(), digest_size=8).digest()


def document_hash(text):
    return hashlib.blake2b(text.encode(), digest_size=16).digest()


def byte_size(text):
    return len(text.encode())


def record(stats, source, step, size):
    entry = stats[source].setdefault(step, {"docs": 0, "bytes": 0})
    if size:
        entry["docs"] += 1
        entry["bytes"] += size


def raw_documents():
    for source in SOURCES:
        with (RAW / f"{source}.jsonl").open(encoding="utf-8") as lines:
            for line in tqdm(lines, desc=source, unit=" docs"):
                yield source, json.loads(line)["text"]


def filtered(document):
    source, text = document
    sizes = [byte_size(text)]
    text = normalize(text.replace(END_OF_TEXT, ""))
    sizes.append(byte_size(text))
    text = urdu_lines(text)
    sizes.append(byte_size(text))
    if is_spam(text):
        text = ""
    sizes.append(byte_size(text))
    if source == "wikipedia" and len(text) < MIN_WIKIPEDIA_CHARS:
        text = ""
    sizes.append(byte_size(text))
    return source, sizes, text


def filter_documents(stats):
    seen = set()
    line_counts = Counter()
    with FILTERED.open("w", encoding="utf-8") as out, Pool() as pool:
        for batch in batched(raw_documents(), BATCH_SIZE):
            for source, sizes, text in pool.map(filtered, batch, chunksize=CHUNK_SIZE):
                for step, size in zip(FILTER_STEPS, sizes):
                    record(stats, source, step, size)
                if not text:
                    continue
                digest = document_hash(text)
                if digest in seen:
                    continue
                seen.add(digest)
                record(stats, source, "deduplicated", byte_size(text))
                line_counts.update({line_hash(line) for line in text.split("\n")})
                out.write(json.dumps({"source": source, "text": text}, ensure_ascii=False) + "\n")
    return line_counts


def remove_boilerplate(stats, line_counts):
    with FILTERED.open(encoding="utf-8") as lines, DOCS.open("w", encoding="utf-8") as out:
        for line in tqdm(lines, desc="boilerplate", unit=" docs"):
            document = json.loads(line)
            text = without_boilerplate(document["text"], line_counts)
            record(stats, document["source"], "boilerplate", byte_size(text))
            if text:
                out.write(json.dumps({"source": document["source"], "text": text}, ensure_ascii=False) + "\n")


def main():
    CLEAN.mkdir(parents=True, exist_ok=True)
    stats = defaultdict(dict)
    line_counts = filter_documents(stats)
    remove_boilerplate(stats, line_counts)
    STATS.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    for source, steps in stats.items():
        print(f"{source}: {steps['raw']['bytes'] / 2**20:.1f} MB -> {steps['boilerplate']['bytes'] / 2**20:.1f} MB")


if __name__ == "__main__":
    main()
