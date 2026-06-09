"""
scraper_base.py — Shared HTTP fetching and caching utilities for all scrapers.
"""

import json
import time
import warnings
from pathlib import Path

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

ROOT_DIR = Path(__file__).parent.parent
TMP_DIR = ROOT_DIR / ".tmp"
TMP_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",  # omit 'br' — requests can't decode brotli natively
    "Connection": "keep-alive",
}


def fetch_page(url: str, cache_key: str = None, force_refresh: bool = False) -> BeautifulSoup | None:
    """
    Fetch a URL and return a BeautifulSoup object.
    Caches the raw HTML to .tmp/<cache_key>.html when cache_key is provided.
    Returns None on failure.
    """
    if cache_key and not force_refresh:
        cache_path = TMP_DIR / f"{cache_key}.html"
        if cache_path.exists():
            with open(cache_path, "r", encoding="utf-8") as f:
                return BeautifulSoup(f.read(), "lxml")

    try:
        time.sleep(1.5)  # polite crawl delay
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        html = resp.text

        if cache_key:
            with open(TMP_DIR / f"{cache_key}.html", "w", encoding="utf-8") as f:
                f.write(html)

        return BeautifulSoup(html, "lxml")

    except requests.exceptions.HTTPError as e:
        print(f"  [scraper] HTTP {e.response.status_code} fetching {url}")
    except requests.exceptions.ConnectionError:
        print(f"  [scraper] Connection error fetching {url}")
    except requests.exceptions.Timeout:
        print(f"  [scraper] Timeout fetching {url}")
    except Exception as e:
        print(f"  [scraper] Unexpected error fetching {url}: {e}")

    return None


def fetch_feed(url: str, cache_key: str = None, force_refresh: bool = False) -> BeautifulSoup | None:
    """Like fetch_page but parses as XML — use for RSS/Atom feeds."""
    if cache_key and not force_refresh:
        cache_path = TMP_DIR / f"{cache_key}.xml"
        if cache_path.exists():
            with open(cache_path, "r", encoding="utf-8") as f:
                return BeautifulSoup(f.read(), "lxml-xml")

    try:
        time.sleep(1.0)
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        xml = resp.text

        if cache_key:
            with open(TMP_DIR / f"{cache_key}.xml", "w", encoding="utf-8") as f:
                f.write(xml)

        return BeautifulSoup(xml, "lxml-xml")

    except requests.exceptions.HTTPError as e:
        print(f"  [scraper] HTTP {e.response.status_code} fetching {url}")
    except Exception as e:
        print(f"  [scraper] Error fetching feed {url}: {e}")

    return None


def save_json(data: dict, filename: str) -> None:
    """Persist data to .tmp/<filename>."""
    with open(TMP_DIR / filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_json(filename: str) -> dict | None:
    """Load persisted JSON from .tmp/<filename>. Returns None if missing."""
    path = TMP_DIR / filename
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None
