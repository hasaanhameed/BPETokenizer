import bz2
import json
import re
from pathlib import Path

from collection.download import download, session

DUMPS = "https://dumps.wikimedia.org/other/cirrus_search_index/"
WIKIS = {"wikipedia": "urwiki", "wikisource": "urwikisource"}
RENDER_ERRORS = re.compile(r"لوا خطا[^۔]*۔|سانچہ:\S+")


def latest_dump_date():
    return max(re.findall(r'href="(\d{8})/"', session.get(DUMPS, timeout=30).text))


def dump_files(date, wiki):
    folder = f"{DUMPS}{date}/index_name={wiki}_content/"
    listing = session.get(folder, timeout=30).text
    return [folder + name for name in re.findall(rf'href="({wiki}_content-[^"]+\.json\.bz2)"', listing)]


def pages(path):
    with bz2.open(path, "rt", encoding="utf-8") as lines:
        for line in lines:
            page = json.loads(line)
            if page.get("namespace") == 0 and page.get("text"):
                yield page


def without_wikisource_header(page):
    header = re.match(rf".*? by\s(.+?)\s{page['page_id']}", page["text"])
    if header is None:
        return page["text"]
    rest = page["text"][header.end():]
    _, found, body = rest.partition(header[1])
    return body if found else rest


def extract_text(source, page):
    text = without_wikisource_header(page) if source == "wikisource" else page["text"]
    return RENDER_ERRORS.sub("", text).strip()


def main():
    date = latest_dump_date()
    print(f"dump date: {date}")
    for source, wiki in WIKIS.items():
        output = Path(f"data/raw/{source}.jsonl")
        output.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with output.open("w", encoding="utf-8") as out:
            for url in dump_files(date, wiki):
                for page in pages(download(url)):
                    text = extract_text(source, page)
                    if not text:
                        continue
                    record = {"id": page["page_id"], "text": text}
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    count += 1
        print(f"{source}: {count} pages, {output.stat().st_size / 2**20:.1f} MB")


if __name__ == "__main__":
    main()
