# Architecture

## 1. Overview

The system is a linear pipeline in four stages. Each stage reads only the files the previous stage wrote, so you can rerun any stage on its own.

```
collection  ──►  cleaning  ──►  tokenizer  ──►  analysis
 raw text        clean splits    merges + .bin   report tables
```

| Stage | Responsibility | Input | Output |
|---|---|---|---|
| Collection | Get raw Urdu documents | Web / dataset URLs | `data/raw/<source>.jsonl` |
| Cleaning | Normalize, filter, deduplicate, split | `data/raw/*.jsonl` | `data/final/{train,val,test}.txt` |
| Tokenizer | Train byte-level BPE; encode corpus | `train.txt`, `val.txt` | `models/urdu_bpe.merges`, `data/final/{train,val}.bin` |
| Analysis | Answer Part C questions | Tokenizer, `test.txt`, samples | Tables for `report/report.pdf` |

## 2. Directory Layout

```
BPETokenizer/
├── CLAUDE.md  ARCHITECTURE.md  README.md  DATA_CARD.md  requirements.txt  .gitignore
├── plans/PLAN.md
├── collection/
│   ├── download.py
│   ├── scrape_voa.py
│   ├── download_wikimedia.py
│   └── download_madlad.py
├── cleaning/
│   ├── normalize.py
│   ├── clean_corpus.py
│   ├── split_corpus.py
│   └── corpus_stats.py
├── tokenizer/
│   ├── bpe.py
│   ├── corpus_reader.py
│   ├── train_tokenizer.py
│   └── encode_corpus.py
├── analysis/
│   ├── merges_report.py
│   ├── compare_tokenizers.py
│   └── samples/
├── tests/
│   ├── test_normalize.py
│   ├── test_bpe.py
│   ├── test_corpus_reader.py
│   └── compare_trainers.py
├── models/urdu_bpe.merges
├── report/report.pdf
└── data/                      (gitignored)
    ├── downloads/             cached source archives
    ├── raw/                   one JSONL per source
    ├── clean/                 docs.jsonl, stats.json
    └── final/                 train/val/test.txt, train/val.bin
```

**Conventions**
- The root holds only documentation and configuration. All code lives in folders.
- Every script runs from the repository root as a module, for example `python -m cleaning.clean_corpus`.
- Imports are absolute, for example `from cleaning.normalize import normalize`.
- Files named by the assignment keep those exact names.

## 3. Components

### 3.1 Collection (`collection/`)
There is one script per source. Each one downloads or scrapes, pulls out the plain text, and writes one document per line.

| Script | Source | Genre | Output |
|---|---|---|---|
| `scrape_voa.py` | VOA Urdu (self-scraped, public domain) | News | `voa.jsonl` |
| `download_wikimedia.py` | Urdu Wikipedia and Wikisource CirrusSearch dumps | Encyclopedia, literature | `wikipedia.jsonl`, `wikisource.jsonl` |
| `download_madlad.py` | MADLAD-400 `ur_clean` | Web | `madlad.jsonl` |

`download.py` is the shared downloader. `download(url)` caches each file in `data/downloads/` and sends a descriptive User-Agent.

**Raw document format** (`data/raw/<source>.jsonl`):
```json
{"id": "...", "text": "..."}
```
The scraper also records `url` and `fetched_at` as evidence that we collected the text ourselves.

### 3.2 Cleaning (`cleaning/`)

| Module | Responsibility |
|---|---|
| `normalize.py` | `normalize(text) -> str`, a pure function that unifies Urdu characters. It runs NFC first, then maps character variants, removes tatweel and invisible characters, handles ZWNJ, unifies digits and collapses whitespace. |
| `clean_corpus.py` | Runs normalize, then the line filter (mostly-Urdu lines), then boilerplate-line removal, then exact-duplicate removal. It records what each step removed in `stats.json`. |
| `split_corpus.py` | Shuffles documents with a fixed seed and splits them 98/1/1 by document. It writes `<|endoftext|>` after each document. |
| `corpus_stats.py` | Corpus totals (MB, documents, words, unique words) for `DATA_CARD.md`. |

### 3.3 Tokenizer (`tokenizer/`)

| Module | Responsibility |
|---|---|
| `bpe.py` | The `BPETokenizer` class (`encode`, `decode`, `save`, `load`) and two trainers: `train_reference` and `train_fast`. Both share `count_pairs`, `merge_word` and `pair_key`, so they cannot drift apart. |
| `corpus_reader.py` | `read_chunks(path)` streams a text file in ~8M-character chunks, each cut just after an `<|endoftext|>`, so no document is split. It opens files with `newline=""` so `\r\n` survives byte for byte. |
| `train_tokenizer.py` | Counts pre-tokenized words in `train.txt` in parallel (one `Counter` per chunk, then merged), trains 49,743 merges and saves `models/urdu_bpe.merges`. It reports the wall-clock time and the machine. |
| `encode_corpus.py` | Encodes `train.txt` and `val.txt` into flat `uint16` NumPy arrays (`.bin`). Each worker loads the tokenizer once and keeps a word cache, which is cleared once it passes 1M entries to bound memory. Chunks are processed in ordered batches, so the output follows the document order. |

**Vocabulary layout**

| IDs | Meaning |
|---|---|
| 0–255 | Raw bytes |
| 256 | `<|endoftext|>`, never split and never merged |
| 257–49,999 | Merges, in the order they were learned (49,743 of them) |

**Pre-tokenization pattern** (`regex` module):
```
 ?[\p{L}\p{M}\u200c]+| ?\p{N}{1,3}| ?[^\s\p{L}\p{M}\p{N}]+|\s+(?!\S)|\s+
```
- Letters, combining marks and ZWNJ form one word, so diacritics never split a word.
- A leading space attaches to the following word.
- Every character matches some branch, so encoding is lossless.

**Training**
- **Reference trainer:** recounts every pair after every merge. It is used only to verify the fast trainer.
- **Fast trainer:**
  - counts each unique word once, weighted by its frequency;
  - keeps an index from each pair to the words that contain it;
  - after a merge, updates counts only for the words that contained the merged pair;
  - picks the next pair from a max-heap (`heapq.heappush_max` / `heappop_max`, Python 3.14). A new entry is pushed whenever a pair's count changes, and on pop any entry whose count no longer matches the current count is skipped.
- **Tie-break:** among pairs with the highest count, pick the pair that is greatest when compared as a tuple of bytes. Both trainers rank pairs with the same key, `(count, bytes_a, bytes_b, id_a, id_b)`. The trailing IDs only matter if two different IDs ever decode to the same bytes, and they keep the order total.
- **Encoding:** each word starts as its UTF-8 bytes, and the adjacent pair with the lowest merge ID is merged repeatedly until no learned pair is left. Literal `<|endoftext|>` in the text becomes ID 256.

**Saved tokenizer format** (`models/urdu_bpe.merges`): plain text with one merge per line, `<id_a> <id_b>`, in the order learned. The full vocabulary is rebuilt from these merges when the file is loaded.

### 3.4 Analysis (`analysis/`)

| Module | Report question |
|---|---|
| `merges_report.py` | Q1. Selected merges as decoded text, two-byte letter rebuilds, invalid-UTF-8 tokens, the first whole word and the 20 longest tokens. |
| `compare_tokenizers.py` | Q2. Tokens per word for our tokenizer, `gpt2` and `o200k_base` on `test.txt` and the 7 hand-picked samples. |
| `samples/` | The 7 hand-picked inputs. They also supply the Q3 failure cases. |

## 4. Data Flow

```
data/downloads/  ──collection──►  data/raw/*.jsonl
data/raw/*.jsonl ──clean_corpus──► data/clean/docs.jsonl + stats.json
data/clean/      ──split_corpus──► data/final/{train,val,test}.txt
train.txt        ──train_tokenizer──► models/urdu_bpe.merges
train/val.txt    ──encode_corpus──►   data/final/{train,val}.bin
```

## 5. Dependencies

| Package | Used by |
|---|---|
| Python standard library | All stages |
| `requests`, `beautifulsoup4` | Collection |
| `regex` | Pre-tokenization |
| `numpy` | `.bin` output |
| `tqdm` | Progress bars |
| `tiktoken` | Analysis only, for comparison |

No tokenizer library and no Urdu NLP library is used in normalization or the tokenizer.

## 6. Testing

| Test | Verifies |
|---|---|
| `tests/test_normalize.py` | Each normalization rule |
| `tests/test_bpe.py` | Lossless round-trip, pre-tokenization, vocabulary layout, a hand-worked sanity check, tie-breaking, and fast == reference on small texts |
| `tests/test_corpus_reader.py` | Chunks rejoin to the exact file and end at document boundaries |
| `tests/compare_trainers.py` | The reference and fast trainers learn identical merges on a 1 MB sample |
