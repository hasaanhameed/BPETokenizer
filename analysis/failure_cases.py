import argparse

import tiktoken

from tokenizer.bpe import BPETokenizer

CASES = {
    "Roman Urdu": (
        "Mujhe Urdu bolna bohat pasand hai lekin likhna mushkil lagta hai",
        "مجھے اردو بولنا بہت پسند ہے لیکن لکھنا مشکل لگتا ہے",
    ),
    "Unnormalized Arabic letters and digits": (
        "پاكستان ۱۴ اگست ۱۹۴۷ كو آزاد هوا اور يه دن هر سال منايا جاتا هے",
        "پاکستان 14 اگست 1947 کو آزاد ہوا اور یہ دن ہر سال منایا جاتا ہے",
    ),
    "Emoji": (
        "بہت خوب 😂😂🔥👍🏽",
        "بہت خوب",
    ),
}


def show_tokens(tokenizer, ids):
    pieces = []
    for i in ids:
        token = tokenizer.vocab[i]
        try:
            pieces.append(token.decode("utf-8"))
        except UnicodeDecodeError:
            pieces.append("<" + token.hex(" ") + ">")
    return " | ".join(pieces)


def describe(name, text, ours, o200k):
    ids = ours.encode(text)
    words = len(text.split())
    other = len(o200k.encode(text))
    print(f"  {name}: {words} words, ours {len(ids)} tokens ({len(ids) / words:.2f}/word), o200k_base {other} ({other / words:.2f}/word)")
    print(f"    {show_tokens(ours, ids)}")


def main():
    parser = argparse.ArgumentParser(description="Part C Q3: inputs our tokenizer handles badly.")
    parser.add_argument("--merges", default="models/urdu_bpe.merges")
    args = parser.parse_args()

    ours = BPETokenizer.load(args.merges)
    o200k = tiktoken.get_encoding("o200k_base")
    for case, (bad, good) in CASES.items():
        print(f"## {case}")
        describe("bad", bad, ours, o200k)
        describe("for contrast", good, ours, o200k)


if __name__ == "__main__":
    main()
