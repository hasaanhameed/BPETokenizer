# Data Card: Urdu Corpus

A cleaned UTF-8 Urdu corpus for training the BPE tokenizer in Assignment 1 and the GPT-style model in Assignment 2. It is used only inside the course and is not redistributed.

## Sources

| Source | Genre | URL | Licence | Collected | Raw | Cleaned |
|---|---|---|---|---|---|---|
| VOA Urdu (scraped by us) | News | urduvoa.com, via its sitemaps | US public domain | 2026-10-11 | 145.8 MB · 23,675 docs | 144.7 MB · 23,660 docs |
| Urdu Wikipedia | Encyclopedia | dumps.wikimedia.org, `cirrus_search_index/20261004` | CC BY-SA 4.0 | dump of 2026-10-04 | 893.1 MB · 729,894 docs | 616.8 MB · 205,253 docs |
| Urdu Wikisource | Literature | dumps.wikimedia.org, `cirrus_search_index/20261004` | CC BY-SA 4.0 (most texts are public domain) | dump of 2026-10-04 | 42.3 MB · 11,972 docs | 42.1 MB · 11,955 docs |
| MADLAD-400 `ur_clean_0000` | Web | huggingface.co/datasets/allenai/MADLAD-400 | CC BY 4.0 / ODC-BY | 2026-10-11 | 696.5 MB · 72,969 docs | 495.3 MB · 47,095 docs |

- **Evidence for the scraped data:** every record in `data/raw/voa.jsonl` stores its `url` and `fetched_at` time (UTC, 2026-10-11 11:06 to 14:49). The scraper obeyed robots.txt.
- **Raw size:** the extracted plain text before cleaning, not the size of the downloaded archives.

## Corpus Totals

| | MB | Documents | Words | Unique words |
|---|---|---|---|---|
| **Total** | 1,298.9 | 287,963 | 163,710,362 | 3,472,257 |
| train.txt | 1,276.4 | 282,203 | | |
| val.txt | 12.6 | 2,880 | | |
| test.txt | 13.5 | 2,880 | | |

Words are counted by splitting on whitespace. The split is by document (98% / 1% / 1%) with seed 42, and `<|endoftext|>` follows each document.

## Cleaning Steps

| # | Step | Documents removed | Text removed |
|---|---|---|---|
| 1 | **Extract:** article body only (VOA); plain-text field without Wikisource headers, Lua errors or template names (Wikimedia); literal `\n` restored to line breaks (MADLAD) | — | done during collection |
| 2 | **Normalize:** NFC; Arabic → Urdu letters (ي ى→ی, ك→ک, ه→ہ, ۀ→ۂ, ة→ۃ); presentation forms → base letters; digits → ASCII; tatweel and invisible characters removed; ZWNJ kept only between letters; whitespace collapsed | 3 | 0.8 MB |
| 3 | **Urdu filter:** drop lines where less than 50% of the letters are Arabic-script | 53,245 | 86.4 MB |
| 4 | **Spam:** drop documents containing فاریکس / بائنری آپشن (forex and binary-options spam) | 25,888 | 197.4 MB |
| 5 | **Stubs:** drop Wikipedia pages shorter than 500 characters | 471,385 | 193.6 MB |
| 6 | **Exact duplicates:** drop documents with an identical hash | 26 | 0.2 MB |
| 7 | **Boilerplate:** drop lines that repeat in 5 or more distinct documents | 0 | 0.3 MB |
| | **Total** | 550,547 | 478.7 MB (27%) |

## Known Gaps and Biases

- **Wikipedia dominates (47%).** The text is encyclopedic, and articles longer than 500 characters still carry template phrasing (place statistics, biography boilerplate) and many transliterated English names.
- **News comes from a single outlet.** VOA covers 2010–2025 from a US government perspective. There are no Pakistani or Indian domestic news outlets.
- **Web text is uneven.** MADLAD contains a lot of religious Q&A, and some machine-translated SEO text on topics other than forex remains.
- **Literature is small (3%)** and mostly classical ghazals. The Wikisource dump flattens poems, so each poem is one line with its verse breaks lost.
- **No Roman Urdu.** The Urdu filter keeps only Arabic-script text, so the tokenizer will see almost no Roman Urdu.
- **Formatting is lost in places.** Wikipedia articles are one line each, and all digits are ASCII after normalization.
