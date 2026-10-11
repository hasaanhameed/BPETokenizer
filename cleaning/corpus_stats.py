import json
from collections import Counter, defaultdict

from tqdm import tqdm

from cleaning.clean_corpus import DOCS


def main():
    totals = defaultdict(Counter)
    vocabularies = defaultdict(set)
    with DOCS.open(encoding="utf-8") as lines:
        for line in tqdm(lines, desc="stats", unit=" docs"):
            document = json.loads(line)
            words = document["text"].split()
            for group in (document["source"], "total"):
                totals[group].update(docs=1, bytes=len(document["text"].encode()), words=len(words))
                vocabularies[group].update(words)

    print(f"{'source':<12}{'MB':>10}{'docs':>12}{'words':>15}{'unique words':>15}")
    for group, counts in totals.items():
        print(
            f"{group:<12}{counts['bytes'] / 2**20:>10.1f}{counts['docs']:>12,}"
            f"{counts['words']:>15,}{len(vocabularies[group]):>15,}"
        )


if __name__ == "__main__":
    main()
