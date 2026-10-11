import argparse
from pathlib import Path

import tiktoken

from tokenizer.bpe import END_OF_TEXT, BPETokenizer

SAMPLES_DIR = Path("analysis/samples")
SAMPLE_ORDER = ["news", "poetry", "urdu_english", "roman_urdu", "numbers_dates", "diacritics", "names"]


def load_tokenizers(merges_path):
    ours = BPETokenizer.load(merges_path)
    gpt2 = tiktoken.get_encoding("gpt2")
    o200k = tiktoken.get_encoding("o200k_base")
    return {
        "ours": ours.encode,
        "gpt2": lambda text: gpt2.encode(text, disallowed_special=()),
        "o200k_base": lambda text: o200k.encode(text, disallowed_special=()),
    }


def load_inputs(test_path):
    inputs = {"test.txt": Path(test_path).read_text(encoding="utf-8").replace(END_OF_TEXT, "\n")}
    for name in SAMPLE_ORDER:
        inputs[name] = (SAMPLES_DIR / f"{name}.txt").read_text(encoding="utf-8")
    return inputs


def main():
    parser = argparse.ArgumentParser(description="Part C Q2: tokens per word for ours, gpt2 and o200k_base.")
    parser.add_argument("--merges", default="models/urdu_bpe.merges")
    parser.add_argument("--test", default="data/final/test.txt")
    args = parser.parse_args()

    tokenizers = load_tokenizers(args.merges)
    print("| Input | Words | " + " | ".join(tokenizers) + " |")
    print("|---|---|" + "---|" * len(tokenizers))
    for name, text in load_inputs(args.test).items():
        words = len(text.split())
        ratios = [len(encode(text)) / words for encode in tokenizers.values()]
        print(f"| {name} | {words:,} | " + " | ".join(f"{ratio:.2f}" for ratio in ratios) + " |")


if __name__ == "__main__":
    main()
