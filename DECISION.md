# Decision Log

This file records every design decision in the project: what was decided, why, and which alternatives were rejected. New entries are added as decisions are made.

## Sources

### D1. Use four sources across four genres
- **Decision:** VOA Urdu (news), Urdu Wikipedia (encyclopedia), Urdu Wikisource (literature) and MADLAD-400 Urdu (web).
- **Why:** The PDF requires at least three sources from at least two genres. Four genres give the tokenizer and the Assignment 2 model a broader mix of Urdu.
- **Rejected:**
  - OSCAR: access is gated and currently suspended.
  - CC-100: it has no licence.
  - UFAL Urdu Monolingual Corpus: it is one sentence per line with no document boundaries, which conflicts with splitting by document.

### D2. Scrape VOA Urdu for the self-collected portion
- **Decision:** Scrape `www.urduvoa.com` using its sitemaps, with robots.txt checked for every URL.
- **Why:** VOA content is US public domain, its robots.txt allows article pages, its sitemaps list about 133k articles, and its HTML is simple and server-rendered.
- **Rejected:**
  - BBC Urdu: its robots.txt forbids building datasets.
  - UrduPoint: Cloudflare blocks automated access.
  - Geo: no usable sitemap.
  - Express and ARY: all rights reserved.
- **Note:** VOA articles often cite agencies, for example "according to Reuters". These are VOA's own Urdu write-ups, not reprinted wire copy, so they are kept.

### D3. Drop the Urdu News Dataset 1M
- **Decision:** Don't use it.
- **Why:** The dataset's own preprocessing deleted the letter آ and all punctuation. For example, `اسلام باد` appears instead of `اسلام آباد`, and `خری` instead of `آخری`, and sentences run together without `۔`. The missing letters can't be restored, and training on this text would teach the tokenizer broken words.
- **Replaced by:** Urdu Wikisource, which also adds a literature genre.

### D4. Read Wikimedia text from the CirrusSearch dumps
- **Decision:** Use the `cirrus_search_index` dumps, which include a plain-text `text` field, instead of the XML dumps.
- **Why:** The text is already rendered, so we don't need to write a wiki-markup parser.
- **Rejected:** The XML dump with our own markup stripping. That means more code and more ways to make mistakes.

### D5. Collection targets: VOA 150 MB, MADLAD capped at 700 MB
- **Decision:** Stop VOA at 150 MB, which is three times the 50 MB minimum. Take the first 700 MB of MADLAD. Keep all of Wikipedia and Wikisource.
- **Why:** These sizes bring the corpus to well over 1 GB and stop the noisier web text from dominating it.

### D6. Scrape VOA with four parallel workers
- **Decision:** 4 threads, each waiting 1 second between its own requests, so at most about 4 requests per second.
- **Why:** One request at a time took 2.24 seconds per article, which meant about 15 hours to reach 150 MB. With four workers it takes about 4 hours. robots.txt sets no crawl-delay, and 4 requests per second is a light load for a news site served from a CDN.

## Cleaning

### D7. Drop Wikipedia pages shorter than 500 characters
- **Decision:** Apply a minimum length of 500 characters to Wikipedia only.
- **Why:** 487k of Wikipedia's 730k pages are bot-generated stubs built from templates, for example "X County has an area of … and a population of …". Keeping them would make template phrases dominate the corpus and use up merges on them.
- **Rejected:** One minimum length for every source. It would also delete short ghazals from Wikisource.

### D8. Keep all clean text
- **Decision:** Don't trim the cleaned corpus down to 1 GB.
- **Why:** More data helps the GPT in Assignment 2. BPE training cost depends mostly on the number of unique words, not on raw size.

### D9. Strip Wikisource page headers during extraction
- **Decision:** Remove the `{title} [(year)] by {author} {page_id}{title}[year]{author}` header that starts every Wikisource page. If the page has a subtitle and the author can't be found again, cut everything up to the page ID instead.
- **Why:** It adds the English word "by", page IDs and run-together words to every poem.
- **Note:** The space after "by" is a non-breaking space (U+00A0), so the match uses `\s`.

### D13. Remove Wikimedia rendering failures
- **Decision:** In both wikis, delete Lua error messages (`لوا خطا … ۔`) and the names of templates that failed to render (`سانچہ:…`, for example `سانچہ:PD-India`).
- **Why:** They are error output, not Urdu text. Lua errors appeared in 6,394 Wikisource pages and 241 Wikipedia pages, and template names appeared 5,355 times in Wikisource.

### D14. Keep only main-namespace Wikimedia pages
- **Decision:** Keep namespace 0 (articles and poems) and drop Wikisource's Page (250) and Index (252) namespaces.
- **Why:** Page and Index pages still contain raw wiki markup (`<noinclude>`, `{{gap}}`, `'''`), and Index pages are only book metadata. Together they are about 1,250 pages and under 0.3% of the corpus, which isn't worth writing a markup stripper for.

## Normalization

### D10. Apply NFC before mapping letters
- **Decision:** Run Unicode NFC first, then map character variants.
- **Why:** ئ (U+0626) decomposes into *Arabic* yeh plus hamza. If Arabic yeh were mapped to Urdu yeh first, ئ could no longer recompose.

### D11. Keep ZWNJ only between letters
- **Decision:** Keep U+200C when it sits between two letters, remove it anywhere else, and collapse repeats.
- **Why:** Urdu uses ZWNJ on purpose inside compound words, as in بے‌شمار, to keep them visually separate while they remain one word. At a word edge it has no effect, and it would turn `کتاب` and `کتاب‌` into two different tokens.

### D15. Base the normalization map on a character inventory
- **Decision:** Count the variant, invisible, digit and whitespace code points in a 30 MB sample of every source, then map only the variants that actually occur.
- **Map:**
  - ي and ى → ی
  - ك → ک
  - ه → ہ
  - ۀ → ۂ
  - ة → ۃ
  - Arabic presentation forms → base letters (NFKC), for example ﷺ → its full phrase
  - both Arabic digit sets → ASCII
- **Removed:**
  - tatweel
  - soft hyphen
  - ZWSP, ZWJ and BOM
  - LRM, RLM and ALM
  - the bidi embeddings and isolates
  - the invisible separator (U+2063)
- **Why the inventory added ة → ۃ:** Arabic teh marbuta appears up to 563 times per million characters (in Wikipedia), alongside the Urdu form ۃ, so it is the same kind of duplicate as yeh and kaf.
- **Kept as they are:** diacritics, honorific signs (U+0610–U+0614), Urdu punctuation, curly quotes and ornate parentheses. They are legitimate Urdu text.

### D12. Unify all digits to ASCII
- **Decision:** Map Arabic-Indic (U+0660–U+0669) and Extended Arabic-Indic (U+06F0–U+06F9) digits to 0–9.
- **Why:** The PDF asks us to pick one convention. ASCII digits are the most common form in web and news Urdu, and English text uses them too.
