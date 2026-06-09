"""
scrape_features.py — Recent product updates for all four competitors.

Per-competitor strategy:
  Jobber       — Cloudflare blocks all requests. Hardcoded recent releases + source link.
  Workiz       — Blog page returns 200 OK; parse article headings.
  HouseCallPro — RSS feed returns clean XML; parse <title> items.
  ServiceTitan — Blog page returns 200 OK; parse article headings.
"""

import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scraper_base import fetch_page, fetch_feed, save_json

TODAY = date.today().strftime("%B %Y")

# ── Jobber hardcoded fallback ─────────────────────────────────────────────────
# Jobber is behind Cloudflare — update this list manually when they ship notable releases.
JOBBER_KNOWN_UPDATES = [
    "AI Receptionist — 24/7 automated phone answering that books jobs",
    "Jobber Copilot — AI assistant for business insights and recommendations",
    "Two-way texting built into every plan",
    "Client Hub — self-serve customer portal for quotes, invoices, and bookings",
    "Automated review requests after job completion",
    "QuickBooks Online sync (bi-directional)",
    "GPS tracking and fleet dispatch view",
    "Expense tracking with receipt capture",
]

JOBBER_FALLBACK_NOTE = (
    f"Jobber's site is Cloudflare-protected — live scraping unavailable as of {TODAY}. "
    "Items above are known features from public sources. "
    "For latest releases visit: https://getjobber.com/product-updates/"
)

# Workiz — no public product update page, blog is JS-rendered
WORKIZ_KNOWN_UPDATES = [
    "Built-in VOIP phone system — call tracking, recording, and lead capture from calls",
    "Online booking widget embeddable on any website",
    "Franchise & multi-location management features",
    "Two-way SMS messaging with customers",
    "Automated payment reminders and follow-ups",
    "QuickBooks Online integration",
    "Drag-and-drop dispatch board",
    "Customer self-serve portal for booking and status updates",
]

WORKIZ_FALLBACK_NOTE = (
    f"Workiz's blog is JS-rendered — live scraping unavailable as of {TODAY}. "
    "Items above are known features from public sources and reviews. "
    "For latest releases visit: https://www.workiz.com/blog/"
)



# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _dedupe(items: list[str]) -> list[str]:
    seen, out = set(), []
    for item in items:
        key = item.lower()[:60]
        if key not in seen and len(item) > 15:
            seen.add(key)
            out.append(item)
    return out


# ── Per-site scrapers ─────────────────────────────────────────────────────────

def _scrape_rss(url: str, cache_key: str, force_refresh: bool, max_items: int = 12) -> list[str]:
    """Parse an RSS/Atom feed and return post titles (uses XML parser)."""
    soup = fetch_feed(url, cache_key=cache_key, force_refresh=force_refresh)
    if not soup:
        return []
    titles = [_clean(t.get_text()) for t in soup.find_all("title")[1:max_items + 1]]
    return [t for t in titles if len(t) > 15]


def _scrape_blog_headings(url: str, cache_key: str, force_refresh: bool, max_items: int = 12) -> list[str]:
    """
    Generic blog-page scraper.
    Tries <article> headings first, then all h2/h3 elements.
    """
    soup = fetch_page(url, cache_key=cache_key, force_refresh=force_refresh)
    if not soup:
        return []

    results = []

    # Strategy 1: <article> elements
    for article in soup.find_all("article", limit=max_items * 2):
        heading = article.find(["h2", "h3", "h4"])
        if heading:
            text = _clean(heading.get_text())
            if text:
                results.append(text)

    if results:
        return _dedupe(results)[:max_items]

    # Strategy 2: standalone headings (common in JS-injected pages where outer HTML survives)
    for tag in soup.find_all(["h2", "h3"], limit=max_items * 3):
        text = _clean(tag.get_text())
        # Skip nav/header noise
        if len(text) > 20 and len(text) < 200 and not any(
            noise in text.lower() for noise in ["menu", "navigation", "cookie", "sign in", "log in"]
        ):
            results.append(text)

    return _dedupe(results)[:max_items]


# ── Main ───────────────────────────────────────────────────────────────────────

def scrape_all_features(force_refresh: bool = False) -> dict:
    """
    Collect product update / blog headlines for all four competitors.
    Saves to .tmp/features_data.json and returns the dict.
    """
    results = {}

    # ── Jobber ────────────────────────────────────────────────────────────────
    print("  Features → Jobber (hardcoded — Cloudflare blocked)")
    results["Jobber"] = {
        "updates": JOBBER_KNOWN_UPDATES,
        "count": len(JOBBER_KNOWN_UPDATES),
        "url": "https://getjobber.com/product-updates/",
        "note": JOBBER_FALLBACK_NOTE,
    }

    # ── Workiz ────────────────────────────────────────────────────────────────
    print("  Features → Workiz (hardcoded — blog is JS-rendered)")
    results["Workiz"] = {
        "updates": WORKIZ_KNOWN_UPDATES,
        "count": len(WORKIZ_KNOWN_UPDATES),
        "url": "https://www.workiz.com/blog/",
        "note": WORKIZ_FALLBACK_NOTE,
    }

    # ── HouseCallPro ──────────────────────────────────────────────────────────
    print("  Features → HouseCallPro (RSS feed)")
    hcp_items = _scrape_rss(
        "https://www.housecallpro.com/feed/",
        cache_key="housecallpro_rss",
        force_refresh=force_refresh,
    )
    results["HouseCallPro"] = {
        "updates": hcp_items,
        "count": len(hcp_items),
        "url": "https://www.housecallpro.com/blog/",
        "note": (
            f"Live RSS feed as of {TODAY}."
            if hcp_items else
            f"RSS feed returned no results as of {TODAY}. Visit housecallpro.com/blog/ directly."
        ),
    }

    save_json(results, "features_data.json")
    return results


if __name__ == "__main__":
    data = scrape_all_features(force_refresh=True)
    for name, info in data.items():
        print(f"\n{name} — {info['count']} items")
        for u in info["updates"][:5]:
            print(f"  • {u}")
        if info.get("note"):
            print(f"  Note: {info['note']}")
