# Plan: Urdu BPE Tokenizer, built in phases

## Context
This is CS 417 Assignment 1. The spec is `Assignment 1 - Urdu BPE Tokenizer from Scratch.pdf`, summarised in `CLAUDE.md`.

**Current repo state:**
- `CLAUDE.md`
- empty `README.md`, `requirements.txt` and `.gitignore`
- an empty `collection/` folder
- `venv/` with Python 3.14.7 and only pip installed

**Machine:** Intel Core Ultra 7 155U (12 cores), 15.4 GB RAM, about 580 GB free disk.

**Goal:** deliver
- a corpus of at least 500 MB (target about 1 GB)
- a byte-level BPE written from scratch, with 50,000 tokens
- `train.bin` and `val.bin`
- `DATA_CARD.md`
- a report of at most 4 pages

**Working rules (from CLAUDE.md):**
- Build one small module at a time and verify it before moving on.
- Write only the code that is needed.
- Code should be readable without comments.
- Follow the spec exactly.

**Two gaps in the PDF to raise with the instructor:**
1. Part C says "five questions" but lists only three.
2. Part B says "the sanity check below", but the PDF has no sanity check.

## Directory structure
All code lives in folders. The root holds only docs and config. The filenames the PDF requires are kept exactly; they just sit inside folders. Folders are created only when something goes into them.
```
BPETokenizer/                  (repo root)
├── CLAUDE.md  README.md  DATA_CARD.md  requirements.txt  .gitignore
├── plans/
│   └── PLAN.md
├── collection/                # one script per source -> data/raw/<source>.jsonl
│   ├── scrape_voa.py
│   ├── download_wikipedia.py
│   ├── download_urdu_news.py
│   └── download_madlad.py
├── cleaning/
│   ├── normalize.py           # normalize(text)
│   ├── clean_corpus.py
│   ├── split_corpus.py
│   └── corpus_stats.py
├── tokenizer/
│   ├── bpe.py                 # BPETokenizer + reference & fast trainers
│   ├── train_tokenizer.py     # train.txt -> models/urdu_bpe.merges
│   └── encode_corpus.py       # train/val.txt -> train.bin/val.bin
├── analysis/                  # Part C scripts + samples/
├── tests/                     # stdlib unittest
├── models/
│   └── urdu_bpe.merges        # saved tokenizer (deliverable, committed)
├── report/                    # report source + report.pdf
└── data/                      # gitignored: downloads/ raw/ clean/ final/
```

**Running scripts:** every script runs from the repo root as a module, for example `python -m cleaning.clean_corpus` or `python -m tokenizer.train_tokenizer`. Imports are absolute (`from cleaning.normalize import normalize`, `from tokenizer.bpe import BPETokenizer`), so no `sys.path` hacks are needed.

**One shared format:** every collector writes `data/raw/<source>.jsonl`. Each line is one document, `{"id": ..., "text": ...}`; the scraper also adds `url` and `fetched_at`. Downloaded archives are cached in `data/downloads/` so they're never fetched twice. Every later stage reads only these JSONL files.

`.gitignore` lists `venv/`, `data/` and `__pycache__/`.
`requirements.txt` lists `regex`, `numpy`, `tqdm`, `requests` and `beautifulsoup4`. `tiktoken` is added only in Phase 6, for the comparison. All of these have Windows wheels for Python 3.14.

---

## Phase 1: Collection (`collection/`)
The goal is at least 3 sources across at least 2 genres, with at least 50 MB scraped by us.

| Script | Source | Genre | Licence | How |
|---|---|---|---|---|
| `scrape_voa.py` | VOA Urdu (`www.urduvoa.com`, 133k articles from 2010–2025) | news | **US public domain** (VOA terms). Skip items credited to AP, AFP or Reuters. | Read the `sitemap.xml` index, then `sitemap_445_{1..7}.xml.gz` (gzipped `<loc>` entries, all `/a/` articles). Check URLs with `urllib.robotparser`, send about 1 request per second with an identifying User-Agent, and resume where it stopped. Use bs4 to take the title from `h1.pg-title` and the body from the `p` tags in `#article-content div.wsw`, skipping pages where it's empty (video or audio). Save `url` + `fetched_at` as evidence. Expect ~300–400 MB if run in full; at least 100 MB is required. |
| `download_wikipedia.py` | Urdu Wikipedia, CirrusSearch dump (`dumps.wikimedia.org/other/cirrus_search_index/<date>/index_name=urwiki_content/…json.bz2`, ~1.24 GB bz2) | encyclopedia | CC BY-SA 4.0 | Stream with stdlib `bz2` + `json` and keep each page's plain-text `text` field. This avoids writing a wiki-markup parser. |
| `download_urdu_news.py` | Urdu News Dataset 1M (Mendeley 834vsxnb99 v4, one 2.09 GB CSV) | news | CC BY 4.0 (research use) | Stream rows with `csv` and keep the article text column. |
| `download_madlad.py` | MADLAD-400 `ur_clean_0000.jsonl.gz` (1.31 GB) | web (blogs, religion, mixed) | CC BY 4.0 / ODC-BY | Stream with stdlib `gzip` + `json`. |

**News sites we're not scraping:**
- BBC Urdu: its robots.txt forbids building datasets.
- UrduPoint: Cloudflare blocks it.
- Geo: no sitemap.
- Express and ARY: all rights reserved. They're a fallback only.

**Sources we're not using:**
- OSCAR: access is gated and currently suspended.
- CC-100: it has no licence.
- UFAL: it is sentence-per-line with no document boundaries, which clashes with the split-by-document rule.

**Target (confirmed):** about 1 GB of cleaned text from 4 sources across 3 genres.

**Rough budget:**
- VOA: 100–150 MB
- Wikipedia: all of it, whatever survives cleaning
- News 1M and MADLAD: split the remaining space

Each `download_*.py` stops streaming once it reaches a fixed MB constant, so news doesn't swamp everything else.

**Verify:** each script prints the document count and MB. Then open a few random documents per source and check them by eye.

## Phase 2: Normalization (`cleaning/normalize.py`)
`normalize(text) -> str` is a pure function. The steps, in order:
1. **`unicodedata.normalize("NFC")` first.** This composes hamza and madda sequences such as ۂ, أ and آ. It has to happen before mapping Arabic yeh to Urdu yeh: ئ decomposes to *Arabic* yeh plus hamza, so mapping first would break it.
2. **Character map** (`str.translate`):
   - ي U+064A and ى U+0649 → ی U+06CC
   - ك U+0643 → ک U+06A9
   - ه U+0647 → ہ U+06C1
   - ۀ U+06C0 → ۂ U+06C2
   - Arabic presentation forms (U+FB50–U+FDFF and U+FE70–U+FEFF) → their base letters, using NFKC on just those characters
3. **Remove** tatweel U+0640 and invisible characters:
   - ZWJ U+200D and ZWSP U+200B
   - LRM U+200E, RLM U+200F and ALM U+061C
   - bidi embeddings and isolates U+202A–U+202E and U+2066–U+2069
   - BOM U+FEFF
4. **ZWNJ:** keep it only between two letters. That's how Urdu uses it on purpose, as in بے‌شمار, to keep a compound word as one unit. Remove it at word edges and collapse repeats, so `کتاب` and `کتاب‌` don't become two separate tokens.
5. **Digits:** map Arabic-Indic U+0660–U+0669 and Extended U+06F0–U+06F9 to ASCII 0–9. This is one convention; the ASCII form is the most common in web and news Urdu, and it's shared with English.
6. **Whitespace:** turn NBSP and other `\p{Zs}` into a plain space, collapse runs of spaces and tabs, strip each line, and collapse repeated blank lines into one newline.

**Before finalising the map**, run a quick code-point frequency count on a sample of the raw data. The PDF invites us to "explore more" variants, and this tells us which ones actually occur.

**Verify:** `tests/test_normalize.py` has one test per rule, including that ہ and ھ stay distinct and that ئ survives.

## Phase 3: Cleaning and splits (`cleaning/`)
**`clean_corpus.py`** reads `data/raw/*.jsonl` and writes `data/clean/docs.jsonl` plus `data/clean/stats.json`, which records the bytes and documents removed at each step.
1. Extraction already happened in Phase 1.
2. Normalize each document with `normalize()`.
3. **Line filter:** keep a line if most of its letters are Arabic-script and it contains Urdu letters. English words inside Urdu sentences are allowed. Drop documents that end up empty.
4. **Boilerplate:** remove lines (by hash) that repeat across many documents.
5. **Exact duplicates:** remove documents whose normalized-text hash has already been seen.

**`split_corpus.py`:**
- Shuffle documents with a fixed seed (`random.Random(42)`).
- Split 98 / 1 / 1 by document.
- Write `data/final/{train,val,test}.txt`, with `<|endoftext|>` after each document.

**`corpus_stats.py`** reports MB, documents, words and unique words for the data card.

**Verify:**
- the split sizes come out at 98/1/1
- no document appears in more than one split
- spot-check samples by eye

Then write `DATA_CARD.md`: a sources table (URL, licence, date, raw and cleaned size), totals, what each cleaning step removed, and gaps and biases.

## Phase 4: BPE (`tokenizer/bpe.py`)
**Layout:**
- `0–255`: bytes
- `256`: `<|endoftext|>`
- `257–49,999`: merges

**Pre-tokenization pattern** (`regex` module):
```
 ?[\p{L}\p{M}\u200c]+| ?\p{N}{1,3}| ?[^\s\p{L}\p{M}\p{N}]+|\s+(?!\S)|\s+
```
- Combining marks and ZWNJ count as part of a word, so اُردُو stays whole.
- A leading space attaches to the following word, as in GPT-2.
- English contractions are dropped because they're not needed for Urdu.
- Every character falls into some branch, so nothing can be lost.
- Numbers split into chunks of at most 3 digits.

**`BPETokenizer`:**
- `encode(text)`:
  - Split on the special token; it maps to 256 and is never split or merged.
  - Pre-tokenize with the regex.
  - Encode each word by applying merges in rank order, with a per-word cache.
- `decode(ids)`: join the byte strings for the IDs and decode as UTF-8.
- `save(path)` / `load(path)`: a text file with one merge per line, `a b`, in learned order (49,743 lines).

**Two trainers.** Both take a sequence of pre-tokenized words and a number of merges, and return the same merge list.
- **Reference:** keep every word occurrence and recount all pairs after every merge.
- **Fast:**
  1. Count each distinct word once, weighted by its frequency.
  2. Keep an index from each pair to the words that contain it, and update counts only for those words after a merge.
  3. Pick the best pair with a max-heap (Python 3.14 `heapq.heappush_max` / `heappop_max`). On pop, skip entries whose count is stale.

**Tie-break (both trainers):** sort key `(count, vocab[a], vocab[b])`, so on equal counts the greater pair as a tuple of bytes wins. Training stops early if no pairs are left; that only happens on tiny inputs.

**Verify (`tests/test_bpe.py`):**
- round-trip on the empty string, emoji, English, newlines, Urdu with diacritics and text containing the special token
- اُردُو is a single pre-token
- the ID layout is correct
- tie-breaking on a toy corpus
- reference and fast trainers produce identical merges on a small text

`tests/compare_trainers.py` also checks that both trainers produce identical merges on a **1 MB sample** of train.txt, for as many merges as the reference version can finish in reasonable time. Its output is evidence for the report.

## Phase 5: Train and encode
**`tokenizer/train_tokenizer.py`:**
1. Stream `train.txt` and split it on `<|endoftext|>`.
2. Pre-tokenize and count words in parallel (`multiprocessing.Pool` over chunks), then merge the counts.
3. Run the fast trainer for 49,743 merges, with `tqdm` progress.
4. Save `models/urdu_bpe.merges`.
5. Print the wall-clock time and the machine, for the report.

**`tokenizer/encode_corpus.py`:** encode `train.txt` and `val.txt` in parallel chunks, using the word cache, and append to `data/final/{train,val}.bin` as flat `np.uint16`.

**Verify:**
- the merges file has exactly 49,743 lines
- the maximum ID is under 50,000
- decoding a slice of `val.bin` equals the matching text
- `train.bin` has the size we expect

`README.md` gets the exact commands, from installing requirements through collection, cleaning, training and encoding.

## Phase 6: Analysis and report (`analysis/`, `report/`)
- **`analysis/merges_report.py` (Q1):**
  - merges 1–50 and every 5,000th merge, shown as decoded text
  - which early merges rebuild a two-byte letter
  - which merges produce a token that is not valid UTF-8 on its own
  - the first merge that is a whole word
  - the 20 longest tokens
- **`analysis/compare_tokenizers.py` (Q2):**
  - tokens per word (whitespace-split words) for ours, `tiktoken` `gpt2` and `o200k_base`
  - run on `test.txt` and 7 hand-written samples in `analysis/samples/`: news, poetry, Urdu with English, Roman Urdu, numbers and dates, diacritics, names
- **Q3:** pick three inputs our tokenizer handles badly and explain why. Likely candidates are Roman Urdu, heavy diacritics and rare names.
- **Report:** tables only, so no plotting library is needed. At most 4 pages, saved as `report/report.pdf`. It covers the regex design, the normalization choices (ZWNJ and digits), training time and machine, and Q1–Q3.

## Final check
- The deliverables list in `CLAUDE.md` is complete.
- A fresh venv plus the README commands rebuilds the tokenizer from `train.txt` with identical merges, because training is deterministic.
- Package the archive. `train/val/test.txt` and `train/val.bin` go on the Drive link.
