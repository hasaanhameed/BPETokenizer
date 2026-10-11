from pathlib import Path

import requests
from tqdm import tqdm

DOWNLOADS = Path("data/downloads")

session = requests.Session()
session.headers["User-Agent"] = "NUST-CS417-UrduCorpus/1.0 (university coursework)"


def download(url, filename=None):
    path = DOWNLOADS / (filename or url.rsplit("/", 1)[-1])
    if path.exists():
        return path
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".part")
    with session.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        size = int(response.headers.get("Content-Length", 0))
        with partial.open("wb") as file, tqdm(total=size, unit="B", unit_scale=True, desc=path.name) as progress:
            for chunk in response.iter_content(1 << 20):
                file.write(chunk)
                progress.update(len(chunk))
    partial.rename(path)
    return path
