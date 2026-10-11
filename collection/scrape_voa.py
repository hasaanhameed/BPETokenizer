import gzip
import json
import re
import time
import urllib.robotparser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from itertools import batched
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SITE = "https://www.urduvoa.com"
USER_AGENT = "NUST-CS417-UrduCorpus/1.0 (university coursework)"
OUTPUT = Path("data/raw/voa.jsonl")
TARGET_BYTES = 150 * 1024 * 1024
DELAY_SECONDS = 1.0
WORKERS = 4
BATCH_SIZE = 100


def article_sitemaps(session):
    index = session.get(f"{SITE}/sitemap.xml", timeout=30).text
    return re.findall(r"<loc>([^<]*/sitemap_445_\d+\.xml\.gz)</loc>", index)


def article_urls(session, sitemap_url):
    xml = gzip.decompress(session.get(sitemap_url, timeout=60).content).decode("utf-8")
    return re.findall(r"<loc>([^<]*/a/[^<]*)</loc>", xml)


def fetch(session, url):
    try:
        response = session.get(url, timeout=30)
    except requests.RequestException:
        return ""
    return response.text if response.status_code == 200 else ""


def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.select_one("h1.pg-title")
    body = soup.select_one("#article-content div.wsw")
    if title is None or body is None:
        return ""
    paragraphs = [p.get_text().strip() for p in body.find_all("p")]
    paragraphs = [p for p in paragraphs if p]
    if not paragraphs:
        return ""
    return "\n".join([title.get_text().strip(), *paragraphs])


def scrape(session, url):
    text = extract_text(fetch(session, url))
    time.sleep(DELAY_SECONDS)
    if not text:
        return None
    return {
        "id": url.rsplit("/", 1)[-1].removesuffix(".html"),
        "url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "text": text,
    }


def scraped_urls():
    if not OUTPUT.exists():
        return set()
    with OUTPUT.open(encoding="utf-8") as lines:
        return {json.loads(line)["url"] for line in lines}


def pending_urls(session, robots, done):
    for sitemap in article_sitemaps(session):
        for url in article_urls(session, sitemap):
            if url not in done and robots.can_fetch(USER_AGENT, url):
                yield url


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    robots = urllib.robotparser.RobotFileParser(f"{SITE}/robots.txt")
    robots.read()
    done = scraped_urls()

    with OUTPUT.open("a", encoding="utf-8") as out, ThreadPoolExecutor(WORKERS) as pool:
        for batch in batched(pending_urls(session, robots, done), BATCH_SIZE):
            if OUTPUT.stat().st_size >= TARGET_BYTES:
                return
            for record in pool.map(lambda url: scrape(session, url), batch):
                if record:
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    done.add(record["url"])
            out.flush()
            print(f"{len(done)} articles, {OUTPUT.stat().st_size / 2**20:.1f} MB", flush=True)


if __name__ == "__main__":
    main()
