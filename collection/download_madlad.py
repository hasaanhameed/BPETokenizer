import gzip
import json
from pathlib import Path

from collection.download import download

URL = "https://huggingface.co/datasets/allenai/MADLAD-400/resolve/main/data/ur/ur_clean_0000.jsonl.gz"
OUTPUT = Path("data/raw/madlad.jsonl")
TARGET_BYTES = 700 * 2**20


def documents(path):
    with gzip.open(path, "rt", encoding="utf-8") as lines:
        for line in lines:
            yield json.loads(line)["text"].replace("\\n", "\n").replace("\\t", "\t")


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with OUTPUT.open("w", encoding="utf-8") as out:
        for text in documents(download(URL)):
            if out.tell() >= TARGET_BYTES:
                break
            out.write(json.dumps({"id": count, "text": text}, ensure_ascii=False) + "\n")
            count += 1
    print(f"{count} documents, {OUTPUT.stat().st_size / 2**20:.1f} MB")


if __name__ == "__main__":
    main()
