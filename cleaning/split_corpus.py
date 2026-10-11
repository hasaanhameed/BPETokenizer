import json
import random
from pathlib import Path

from cleaning.clean_corpus import DOCS, END_OF_TEXT

FINAL = Path("data/final")
SEED = 42
HELD_OUT_SHARE = 0.01


def load_documents():
    with DOCS.open(encoding="utf-8") as lines:
        return [json.loads(line)["text"] for line in lines]


def write_split(name, documents):
    path = FINAL / f"{name}.txt"
    with path.open("w", encoding="utf-8", newline="") as out:
        for text in documents:
            out.write(text + END_OF_TEXT)
    print(f"{name}: {len(documents)} documents, {path.stat().st_size / 2**20:.1f} MB")


def main():
    documents = load_documents()
    random.Random(SEED).shuffle(documents)
    held_out = round(len(documents) * HELD_OUT_SHARE)
    FINAL.mkdir(parents=True, exist_ok=True)
    write_split("val", documents[:held_out])
    write_split("test", documents[held_out : 2 * held_out])
    write_split("train", documents[2 * held_out :])


if __name__ == "__main__":
    main()
