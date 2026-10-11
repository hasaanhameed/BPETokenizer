import argparse
import os
from itertools import batched
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from tqdm import tqdm

from tokenizer.bpe import BPETokenizer
from tokenizer.corpus_reader import read_chunks

CACHE_LIMIT = 1_000_000

tokenizer = None


def load_tokenizer(merges_path):
    global tokenizer
    tokenizer = BPETokenizer.load(merges_path)


def encode_chunk(chunk):
    if len(tokenizer.cache) > CACHE_LIMIT:
        tokenizer.cache.clear()
    return np.asarray(tokenizer.encode(chunk), dtype=np.uint16)


def encode_file(pool, text_path, bin_path, workers):
    total = 0
    with open(bin_path, "wb") as out, tqdm(desc=f"Encoding {text_path.name}", unit="chunk") as progress:
        for batch in batched(read_chunks(text_path), workers):
            for ids in pool.map(encode_chunk, batch):
                ids.tofile(out)
                total += len(ids)
            progress.update(len(batch))
    return total


def main():
    parser = argparse.ArgumentParser(description="Encode train.txt and val.txt into flat uint16 token files.")
    parser.add_argument("--data-dir", default="data/final")
    parser.add_argument("--merges", default="models/urdu_bpe.merges")
    parser.add_argument("--splits", nargs="+", default=["train", "val"])
    args = parser.parse_args()

    vocab_size = len(BPETokenizer.load(args.merges).vocab)
    if vocab_size > 2**16:
        raise SystemExit(f"Vocabulary of {vocab_size:,} does not fit in uint16")

    workers = os.cpu_count()
    with Pool(workers, initializer=load_tokenizer, initargs=(args.merges,)) as pool:
        for split in args.splits:
            text_path = Path(args.data_dir) / f"{split}.txt"
            bin_path = text_path.with_suffix(".bin")
            total = encode_file(pool, text_path, bin_path, workers)
            print(f"{bin_path}: {total:,} tokens, {bin_path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
