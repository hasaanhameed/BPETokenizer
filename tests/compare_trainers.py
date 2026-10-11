import argparse
import time
from pathlib import Path

from tokenizer.bpe import END_OF_TEXT, count_words, train_fast, train_reference


def read_sample(path, max_bytes):
    docs, size = [], 0
    for doc in Path(path).read_text(encoding="utf-8").split(END_OF_TEXT):
        if size >= max_bytes:
            break
        docs.append(doc + END_OF_TEXT)
        size += len(docs[-1].encode("utf-8"))
    return "".join(docs)


def timed(train, *args):
    start = time.perf_counter()
    merges = train(*args)
    return merges, time.perf_counter() - start


def main():
    parser = argparse.ArgumentParser(description="Check that the fast and reference trainers learn identical merges.")
    parser.add_argument("--input", default="data/final/train.txt")
    parser.add_argument("--bytes", type=int, default=1_000_000)
    parser.add_argument("--merges", type=int, default=5_000)
    args = parser.parse_args()

    text = read_sample(args.input, args.bytes)
    print(f"Sample: {len(text.encode('utf-8')):,} bytes from {args.input}")

    fast_merges, fast_seconds = timed(train_fast, count_words(text), args.merges)
    print(f"Fast:      {len(fast_merges):,} merges in {fast_seconds:,.1f} s")
    reference_merges, reference_seconds = timed(train_reference, text, args.merges)
    print(f"Reference: {len(reference_merges):,} merges in {reference_seconds:,.1f} s")

    if fast_merges != reference_merges:
        first_diff = next(i for i, pair in enumerate(zip(fast_merges, reference_merges)) if pair[0] != pair[1])
        raise SystemExit(f"DIFFERENT: first mismatch at merge {first_diff + 1}")
    print(f"IDENTICAL: all {len(fast_merges):,} merges match")


if __name__ == "__main__":
    main()
