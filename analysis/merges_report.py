import argparse
from collections import Counter
from pathlib import Path

import regex

from tokenizer.bpe import BPETokenizer, split_words

WHOLE_WORD = regex.compile(r" \p{L}[\p{L}\p{M}]+")
MIN_WORD_COUNT = 100


def show(token):
    try:
        return repr(token.decode("utf-8"))
    except UnicodeDecodeError:
        return "invalid: " + token.hex(" ")


def is_valid_utf8(token):
    try:
        token.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def merge_rows(tokenizer, ranks):
    print("| Merge | ID | Left + Right | Token |")
    print("|---|---|---|---|")
    for rank in ranks:
        new_id = 256 + rank
        a, b = tokenizer.merges[rank - 1]
        print(f"| {rank} | {new_id} | {show(tokenizer.vocab[a])} + {show(tokenizer.vocab[b])} | {show(tokenizer.vocab[new_id])} |")


def rebuilds_letter(tokenizer, rank):
    a, b = tokenizer.merges[rank - 1]
    token = tokenizer.vocab[256 + rank]
    return a < 256 and b < 256 and is_valid_utf8(token) and len(token.decode("utf-8")) == 1


def first_whole_word(tokenizer, word_counts):
    for rank in range(1, len(tokenizer.merges) + 1):
        token = tokenizer.vocab[256 + rank]
        if is_valid_utf8(token):
            text = token.decode("utf-8")
            if WHOLE_WORD.fullmatch(text) and word_counts[text] >= MIN_WORD_COUNT:
                return rank, text
    return None


def main():
    parser = argparse.ArgumentParser(description="Part C Q1: what did the merges learn?")
    parser.add_argument("--merges", default="models/urdu_bpe.merges")
    parser.add_argument("--test", default="data/final/test.txt")
    args = parser.parse_args()

    tokenizer = BPETokenizer.load(args.merges)
    ranks = range(1, len(tokenizer.merges) + 1)

    print("## Merges 1-50")
    merge_rows(tokenizer, range(1, 51))
    print("\n## Every 5,000th merge")
    merge_rows(tokenizer, [*range(5000, len(tokenizer.merges) + 1, 5000), len(tokenizer.merges)])

    letter_rebuilds = [rank for rank in ranks if rebuilds_letter(tokenizer, rank)]
    print(f"\n## Merges that rebuild a two-byte letter: {len(letter_rebuilds)}")
    print(", ".join(f"{rank}:{tokenizer.vocab[256 + rank].decode('utf-8')}" for rank in letter_rebuilds[:60]))
    print(f"Among merges 1-50: {sum(rank <= 50 for rank in letter_rebuilds)}")

    invalid = [rank for rank in ranks if not is_valid_utf8(tokenizer.vocab[256 + rank])]
    print(f"\n## Merges that are not valid UTF-8 on their own: {len(invalid)} of {len(tokenizer.merges)}")
    print(", ".join(f"{rank}:{show(tokenizer.vocab[256 + rank])}" for rank in invalid[:30]))
    print(f"Among merges 1-50: {sum(rank <= 50 for rank in invalid)}")

    word_counts = Counter(split_words(Path(args.test).read_text(encoding="utf-8")))
    rank, word = first_whole_word(tokenizer, word_counts)
    print(f"\n## First whole word: merge {rank}, {word!r}, seen {word_counts[word]:,} times in test.txt")

    print("\n## 20 longest tokens (by characters)")
    valid_ids = [i for i in range(257, len(tokenizer.vocab)) if is_valid_utf8(tokenizer.vocab[i])]
    longest = sorted(valid_ids, key=lambda i: (-len(tokenizer.vocab[i].decode("utf-8")), i))[:20]
    print("| Merge | Characters | Bytes | Token |")
    print("|---|---|---|---|")
    for i in longest:
        token = tokenizer.vocab[i]
        print(f"| {i - 256} | {len(token.decode('utf-8'))} | {len(token)} | {show(token)} |")


if __name__ == "__main__":
    main()
