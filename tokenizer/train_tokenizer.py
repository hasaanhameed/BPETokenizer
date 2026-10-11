import argparse
import os
import platform
import time
from collections import Counter
from itertools import batched
from multiprocessing import Pool
from pathlib import Path

from tqdm import tqdm

from tokenizer.bpe import BPETokenizer, count_words, train_fast
from tokenizer.corpus_reader import read_chunks

NUM_MERGES = 49_743


def count_corpus(path):
    counts = Counter()
    workers = os.cpu_count()
    with Pool(workers) as pool, tqdm(desc="Counting words", unit="chunk") as progress:
        for batch in batched(read_chunks(path), workers):
            for chunk_counts in pool.map(count_words, batch):
                counts.update(chunk_counts)
            progress.update(len(batch))
    return counts


def describe_machine():
    return f"{platform.processor()}, {os.cpu_count()} logical cores, {platform.platform()}, Python {platform.python_version()}"


def main():
    parser = argparse.ArgumentParser(description="Train the byte-level BPE tokenizer on train.txt.")
    parser.add_argument("--input", default="data/final/train.txt")
    parser.add_argument("--output", default="models/urdu_bpe.merges")
    parser.add_argument("--merges", type=int, default=NUM_MERGES)
    args = parser.parse_args()

    start = time.perf_counter()
    counts = count_corpus(args.input)
    counted = time.perf_counter()
    print(f"{counts.total():,} words, {len(counts):,} distinct")

    merges = train_fast(counts, args.merges, progress=True)
    trained = time.perf_counter()
    if len(merges) < args.merges:
        print(f"Warning: only {len(merges):,} merges possible, {args.merges:,} requested")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    BPETokenizer(merges).save(args.output)
    print(f"Saved {len(merges):,} merges to {args.output}")
    print(f"Counting: {counted - start:,.1f} s, merging: {trained - counted:,.1f} s, total: {trained - start:,.1f} s")
    print(f"Machine: {describe_machine()}")


if __name__ == "__main__":
    main()
