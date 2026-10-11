# Urdu BPE Tokenizer from Scratch

CS 417 Large Language Models, Assignment 1. NUST SEECS, Spring 2026.

This repository builds a byte-level Byte-Pair Encoding (BPE) tokenizer for Urdu without using any tokenizer library. It covers three parts:

1. **Corpus:** collect and clean at least 500 MB of Urdu text, then split it into train, validation and test sets.
2. **Tokenizer:** implement byte-level BPE in plain Python and train a 50,000-token vocabulary.
3. **Analysis:** study the learned vocabulary and compare it with GPT-2 and `o200k_base`.

The corpus and tokenizer are the inputs to Assignment 2, which trains a GPT-style model on them.

## Documentation

| Document | Contents |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design: components, data formats, data flow |
| [plans/PLAN.md](plans/PLAN.md) | Phased implementation plan and design decisions |
| [DATA_CARD.md](DATA_CARD.md) | Corpus sources, licences, statistics and known biases |

## Repository Structure

```
collection/   scrapers and dataset downloaders
cleaning/     normalization, cleaning and train/val/test split
tokenizer/    BPE implementation, training and corpus encoding
analysis/     Part C analysis scripts
tests/        unit tests
models/       trained tokenizer (urdu_bpe.merges)
report/       final report
data/         generated data (not tracked)
```

## Setup

You need Python 3.14.

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Run every command from the repository root. The commands below follow the planned pipeline, and this section will be updated as each stage is implemented.

```bash
# 1. Collect raw text
python -m collection.scrape_voa
python -m collection.download_wikimedia
python -m collection.download_madlad

# 2. Clean and split
python -m cleaning.clean_corpus
python -m cleaning.split_corpus

# 3. Train the tokenizer and encode the corpus
python -m tokenizer.train_tokenizer
python -m tokenizer.encode_corpus

# Tests
python -m unittest discover tests
```

## Outputs

| File | Description | Location |
|---|---|---|
| `models/urdu_bpe.merges` | 49,743 merges in learned order | Repository |
| `train.txt`, `val.txt`, `test.txt` | Cleaned corpus splits | Shared drive |
| `train.bin`, `val.bin` | Token IDs as flat `uint16` NumPy arrays | Shared drive |

## Rules

- The tokenizer and normalizer are written from scratch.
- Allowed in the implementation: the Python standard library, `regex`, `numpy`, `tqdm`, `requests` and `beautifulsoup4`.
- `tiktoken` is used only for the Part C comparison.
