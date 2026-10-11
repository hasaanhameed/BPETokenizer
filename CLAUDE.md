# Urdu BPE Tokenizer from Scratch

CS 417 (LLM), Assignment 1. The full spec is in `Assignment 1 - Urdu BPE Tokenizer from Scratch.pdf`. Treat the PDF as the source of truth and comply with it exactly.

The corpus and tokenizer feed the next assignment (training a GPT-style model), so correctness matters.

## Assignment

### Part A: Corpus
- At least 500 MB of cleaned UTF-8 Urdu text (1 GB if possible).
- At least 3 sources from at least 2 genres. At least 50 MB must be self-collected (scraping/API) with evidence. Record each source's licence.
- Follow `robots.txt`, skip logins and paywalls, and collect no personal data.
- Pipeline:
  1. Extract plain text.
  2. Run our own `normalize(text)`.
  3. Filter out non-Urdu lines, keeping natural code-mixing.
  4. Deduplicate documents and repeated boilerplate lines.
  5. Split by document 98/1/1 with a fixed seed.
- Normalization:
  - Arabic yeh/alef maksura → U+06CC
  - Arabic kaf → U+06A9
  - U+0647 → U+06C1, and keep U+06C1 and U+06BE distinct
  - Remove tatweel
  - Remove invisible characters (ZWNJ: decide and justify)
  - Pick one digit convention
  - Collapse whitespace
- Output: `train.txt`, `val.txt` and `test.txt`, with `<|endoftext|>` after each document.
- `DATA_CARD.md` (one page): a sources table (URL, licence, date, raw/cleaned size), totals (MB, docs, words, unique words), what each cleaning step removed, and known gaps and biases.

### Part B: Byte-level BPE
- Vocabulary of exactly 50,000:
  - IDs 0–255 are bytes.
  - ID 256 is `<|endoftext|>`, which is never split or merged.
  - IDs 257–49,999 are the 49,743 merges, in learned order.
- Pre-tokenize with a custom `regex` pattern that keeps Urdu words whole, including combining marks (`\p{M}`) and ZWNJ. A leading space attaches to the following word.
- Tie-break: on equal counts, merge the greater pair, compared as tuples of bytes.
- Lossless: `decode(encode(text)) == text` for any string. Normalization stays outside the tokenizer.
- Two implementations:
  1. Reference: recount all pairs after every merge.
  2. Fast:
     - Count each distinct word once, weighted by frequency.
     - Update only the affected words using a pair→words index.
     - Cache word encodings.

  The fast version must produce identical merges to the reference version on a 1 MB sample.
- Train on the full `train.txt`. Record wall-clock time and machine.
- Encode `train.txt` and `val.txt` to `train.bin` and `val.bin` as flat NumPy `uint16`.

### Part C: Report (`report.pdf`, max 4 pages)
Each answer gets a table or plot plus 2–3 sentences.
1. What the merges learned:
   - merges 1–50, then every 5,000th merge
   - merges that rebuild two-byte letters
   - merges that produce invalid-UTF-8 tokens
   - the first whole-word merge
   - the 20 longest tokens
2. Tokens per word for ours, GPT-2 (`gpt2`) and `o200k_base`. Use `test.txt` plus 7 hand-picked inputs:
   - news
   - poetry
   - Urdu with English words
   - Roman Urdu
   - numbers and dates
   - text with diacritics
   - personal names
3. Three inputs our tokenizer handles badly, with explanations.

### Deliverables
- Archive:
  - `normalize.py`
  - `bpe.py` (with `BPETokenizer`)
  - `train_tokenizer.py`
  - `encode_corpus.py`
  - collection and cleaning scripts
  - the saved tokenizer with all 49,743 merges
  - `DATA_CARD.md`
  - `report.pdf`
  - `README.md` with exact rebuild commands
- Drive link: `train.txt`, `val.txt`, `test.txt`, `train.bin` and `val.bin`.

### Library rules
- Allowed: the Python standard library, `regex`, `numpy`, `tqdm`, `requests` and `beautifulsoup4`.
- Forbidden in the implementation: `tokenizers`, `sentencepiece`, `tiktoken`, `minbpe`, any published BPE code, and Urdu NLP libraries for normalization.
- `tiktoken` and `tokenizers` are allowed **only** for the Part C comparison.

## Architecture and Plan

- **`ARCHITECTURE.md`**: the system design, including directory layout, components, data formats, data flow and conventions. Follow it, and update it whenever the design changes.
- **`plans/PLAN.md`**: the phased implementation plan, with research notes and the reasoning behind each decision.
- **`DECISION.md`**: the decision log. Every design decision is recorded there with its reason and the alternatives rejected. Add an entry whenever a new decision is made.

## Development Rules

1. **One step at a time.** Build and verify one module before moving on.
2. **Modular, clean architecture.** Each file has one clear responsibility and lives in the right folder. Never put code at the root.
3. **Only write code that is needed.** Before writing anything, ask: *is this really needed?* No speculative features, abstractions or options.
4. **Self-explanatory code.** It should be readable without comments. Use clear names and small functions. No comments unless something is truly non-obvious.
5. **Strict compliance.** Follow the assignment spec exactly, including file names, IDs, vocabulary size, tie-breaking, splits and formats. When unsure, check the PDF.
6. **Own work.** Every line of the tokenizer and normalizer is written from scratch, and it must be explainable in a viva.

## Commit Conventions

- Group changes by purpose, with one commit per logical change. Never commit unrelated files together.
- Follow [Conventional Commits](https://www.conventionalcommits.org/): `<type>: <description>`.
- Each message is a single line in the imperative mood and lowercase, with no trailing period, no body and no trailers.
- Types:
  - `feat`: new functionality
  - `fix`: bug fix
  - `docs`: documentation only
  - `test`: adding or changing tests
  - `refactor`: code change with no behaviour change
  - `chore`: config, dependencies, `.gitignore`
- Examples:
  - `feat: add voa urdu scraper`
  - `fix: keep zwnj between letters in normalize`
  - `docs: add data card`
  - `chore: add regex and numpy to requirements`
