import gzip
import json
import re
import time
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SITE = "https://www.urduvoa.com"
USER_AGENT = "NUST-CS417-UrduCorpus/1.0 (university coursework)"
OUTPUT = Path("data/raw/voa.jsonl")
TARGET_BYTES = 150 * 1024 * 1024
DELAY_SECONDS = 1.0


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


def scraped_urls():
    if not OUTPUT.exists():
        return set()
    with OUTPUT.open(encoding="utf-8") as lines:
        return {json.loads(line)["url"] for line in lines}


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    robots = urllib.robotparser.RobotFileParser(f"{SITE}/robots.txt")
    robots.read()
    done = scraped_urls()

    with OUTPUT.open("a", encoding="utf-8") as out:
        for sitemap in article_sitemaps(session):
            for url in article_urls(session, sitemap):
                if OUTPUT.stat().st_size >= TARGET_BYTES:
                    return
                if url in done or not robots.can_fetch(USER_AGENT, url):
                    continue
                text = extract_text(fetch(session, url))
                time.sleep(DELAY_SECONDS)
                if not text:
                    continue
                record = {
                    "id": url.rsplit("/", 1)[-1].removesuffix(".html"),
                    "url": url,
                    "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "text": text,
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                out.flush()
                done.add(url)
                if len(done) % 100 == 0:
                    print(f"{len(done)} articles, {OUTPUT.stat().st_size / 2**20:.1f} MB", flush=True)


if __name__ == "__main__":
    main()
