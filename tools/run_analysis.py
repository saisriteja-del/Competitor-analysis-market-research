"""
Competitive analysis engine — refreshes data across all dashboard tabs.

What it updates:
  • product_updates.json   → Product Updates tab (new news entries)
  • analysis_cache.json    → All tabs (ratings, feature alerts, pricing alerts)

No API key required. Uses DuckDuckGo HTML search + G2 scraping.

CLI:  python tools/run_analysis.py
App:  from tools.run_analysis import analyze_all
      result = analyze_all(write_fn=st.write)
"""

import json
import re
import time
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
from bs4 import BeautifulSoup

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_TMP            = Path(__file__).parent.parent / ".tmp"
_UPDATES_FILE   = _TMP / "product_updates.json"
_CACHE_FILE     = _TMP / "analysis_cache.json"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

_SKIP_DOMAINS = {
    "linkedin.com", "twitter.com", "x.com", "facebook.com",
    "youtube.com", "reddit.com", "glassdoor.com", "indeed.com",
    "techradar.com", "pcmag.com", "cnet.com",
    "alternativeto.net", "sourceforge.net",
}

# Review / comparison sites are ok for ratings but skipped for news
_REVIEW_DOMAINS = {"g2.com", "capterra.com", "getapp.com", "trustpilot.com",
                   "softwareadvice.com", "getapp.com"}

# ── G2 slug overrides (when company name ≠ G2 slug) ──────────────────────────
_G2_SLUGS = {
    "HousecallPro":  "housecall-pro",
    "ServiceTitan":  "servicetitan",
    "Workiz":        "workiz",
    "FieldEdge":     "fieldedge",
    "FieldPulse":    "fieldpulse",
    "ServiceFusion": "service-fusion",
    "mHelpDesk":     "mhelpdesk",
    "Kickserv":      "kickserv",
    "ZohoFSM":       "zoho-fsm",
    "Zuper":         "zuper",
    "Jobber":        "jobber",
}

# ── Search queries: 2 per competitor ─────────────────────────────────────────
_QUERIES = {
    "Jobber":        ["Jobber field service new feature launch 2026",
                      "Jobber product update blog release 2026"],
    "HousecallPro":  ["Housecall Pro product update new feature 2026",
                      "Housecall Pro AI launch announcement 2026"],
    "ServiceTitan":  ["ServiceTitan product release new feature 2026",
                      "ServiceTitan AI feature update 2026"],
    "Workiz":        ["Workiz new feature product update 2026",
                      "Workiz AI launch announcement 2026"],
    "FieldEdge":     ["FieldEdge new feature update 2026",
                      "FieldEdge field service release 2026"],
    "FieldPulse":    ["FieldPulse product update new feature 2026",
                      "FieldPulse Operator AI launch 2026"],
    "ServiceFusion": ["Service Fusion product update 2026",
                      "ServiceFusion new feature release 2026"],
    "mHelpDesk":     ["mHelpDesk product update new feature 2026",
                      "mHelpDesk feature release 2026"],
    "Kickserv":      ["Kickserv product update feature 2026",
                      "Kickserv release update 2026"],
    "ZohoFSM":       ["Zoho FSM product update new feature 2026",
                      "Zoho field service management release 2026"],
    "Zuper":         ["Zuper field service product update 2026",
                      "Zuper AI feature launch 2026"],
}

_UPCOMING_WORDS = {
    "coming soon", "upcoming", "announcing", "preview", "beta", "roadmap",
    "will launch", "planned", "in development", "early access", "sneak peek",
    "future release",
}

_CATEGORY_RULES = [
    ("AI / Automation",     ["ai ", " ai", "artificial intelligence", "automat",
                              "bot", "receptionist", "copilot", "intelligent",
                              "smart dispatch", "predictive", "machine learning",
                              "gpt", "llm", "genius answering", "voice agent"]),
    ("Funding / Acquisition", ["funding", "series a", "series b", "series c",
                                "raised", "acquisition", "acqui", "merger", "ipo",
                                "investment", "million", "billion", "venture"]),
    ("Integration",           ["integrat", "connect", "api ", "sync", "quickbooks",
                                "salesforce", "stripe", "zapier", "webhook"]),
    ("Pricing Change",        ["price", "pricing", "plan ", "plans", "cost",
                                "subscription", "tier", "free tier", "discount"]),
    ("UI/UX Update",          ["redesign", "ui ", "ux ", "mobile app", "interface",
                                "dashboard", "new look", "experience",
                                "platform redesign", "rebuilt", "revamp"]),
    ("Partnership",           ["partnership", "partnered", "partner with",
                                "collaboration", "joins", "teams with"]),
]

# Keywords that suggest a feature alert (review Feature Matrix)
_FEATURE_ALERT_WORDS = [
    "launches", "introduces", "new feature", "now available", "released",
    "adds ", "added ", "ships ", "shipped ", "rolls out", "just launched",
    "announce", "debut", "ga launch", "general availability",
]

# Keywords that suggest a pricing alert (verify Pricing tab)
_PRICING_ALERT_WORDS = [
    "price", "pricing", "new plan", "plan update", "now free",
    "cost increase", "subscription change", "tier change", "price hike",
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _detect_category(title: str, snippet: str) -> str:
    text = (title + " " + snippet).lower()
    for cat, kws in _CATEGORY_RULES:
        if any(kw in text for kw in kws):
            return cat
    return "New Feature"


def _is_upcoming(title: str, snippet: str) -> bool:
    text = (title + " " + snippet).lower()
    return any(kw in text for kw in _UPCOMING_WORDS)


def _is_relevant(title: str, snippet: str, name: str) -> bool:
    text = (title + " " + snippet).lower()
    variants = {name.lower(), name.lower().replace("housecallpro", "housecall pro"),
                name.lower().replace("zohofsm", "zoho fsm")}
    if not any(v in text for v in variants):
        return False
    if any(w in text for w in ["we're hiring", "job opening", "apply now", "careers"]):
        return False
    years = set(re.findall(r'\b(202[3-6])\b', text))
    if years and max(years) < "2025":
        return False
    return True


def _is_duplicate(new_title: str, pool: list) -> bool:
    stop = {
        "the", "a", "an", "is", "are", "for", "in", "on", "at", "to", "of",
        "and", "or", "with", "new", "how", "why", "your", "our", "its",
        "from", "will", "can", "has", "have", "this", "that", "by", "now",
        "all", "more", "get",
    }

    def sig(s):
        return {w for w in re.sub(r"[^a-z0-9 ]", "", s.lower()).split()
                if w not in stop and len(w) > 2}

    nw = sig(new_title)
    if not nw:
        return False
    for entry in pool:
        ew = sig(entry.get("title", ""))
        if ew and len(nw & ew) / max(len(nw), len(ew)) >= 0.5:
            return True
    return False


def _search_ddg(query: str, max_results: int = 5) -> list:
    try:
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers=_HEADERS,
            timeout=12,
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for div in soup.select(".result"):
            title_el   = div.select_one(".result__title")
            snippet_el = div.select_one(".result__snippet")
            url_el     = div.select_one("a.result__a")
            if not title_el or not url_el:
                continue
            title   = title_el.get_text(strip=True)
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            href    = url_el.get("href", "")
            url = href
            if "uddg=" in href:
                params = parse_qs(urlparse(href).query)
                if "uddg" in params:
                    url = unquote(params["uddg"][0])
            domain = urlparse(url).netloc.lower().replace("www.", "")
            if any(d in domain for d in _SKIP_DOMAINS | _REVIEW_DOMAINS):
                continue
            results.append({"title": title, "url": url, "snippet": snippet})
            if len(results) >= max_results:
                break
        return results
    except Exception:
        return []


def _scrape_g2_rating(name: str) -> dict:
    """Scrape G2 for updated rating and review count."""
    slug = _G2_SLUGS.get(name, re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"))
    url  = f"https://www.g2.com/products/{slug}/reviews"
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=10)
        if resp.status_code != 200:
            return {}
        soup = BeautifulSoup(resp.text, "html.parser")
        rating, reviews = None, 0
        for sel in ['[data-star-rating]', '.fw-semibold.c-midnight-100',
                    'span[itemprop="ratingValue"]', '.product-rating__number']:
            el = soup.select_one(sel)
            if el:
                m = re.search(r"(\d+\.\d+)", el.get_text(strip=True))
                if m:
                    rating = round(float(m.group(1)), 1)
                    break
        for sel in ['.x-current-review-count', '[data-total-reviews]',
                    'span[itemprop="reviewCount"]']:
            el = soup.select_one(sel)
            if el:
                txt = re.sub(r"[^0-9]", "", el.get_text())
                if txt:
                    reviews = int(txt)
                    break
        return {"g2_rating": rating, "g2_reviews": reviews} if rating else {}
    except Exception:
        return {}


def _detect_alerts(name: str, results: list) -> tuple:
    """
    From search results, return (feature_alert_str | None, pricing_alert_str | None).
    """
    feature_alert = None
    pricing_alert = None

    for r in results:
        text = (r["title"] + " " + r["snippet"]).lower()
        if not feature_alert and any(kw in text for kw in _FEATURE_ALERT_WORDS):
            # Trim title to 80 chars for the alert message
            short = r["title"][:80].rstrip() + ("…" if len(r["title"]) > 80 else "")
            feature_alert = f"New release detected: \"{short}\" — review Feature Matrix"
        if not pricing_alert and any(kw in text for kw in _PRICING_ALERT_WORDS):
            short = r["title"][:80].rstrip() + ("…" if len(r["title"]) > 80 else "")
            pricing_alert = f"Possible pricing change: \"{short}\" — verify in Pricing tab"
        if feature_alert and pricing_alert:
            break

    return feature_alert, pricing_alert


# ─────────────────────────────────────────────────────────────────────────────
# Core per-competitor analysis
# ─────────────────────────────────────────────────────────────────────────────

def analyze_competitor(name: str, existing_pool: list) -> dict:
    """
    Full single-competitor analysis:
      1. News search → new product update entries
      2. G2 scrape   → updated rating/review count
      3. Alert detection → feature_alert, pricing_alert strings

    Returns {
      "new_updates": [...],
      "rating":      {"g2_rating": float, "g2_reviews": int} | {},
      "feature_alert": str | None,
      "pricing_alert": str | None,
    }
    """
    queries  = _QUERIES.get(name, [f"{name} product update 2026"])
    today    = datetime.now().strftime("%Y-%m-%d")
    all_results: list = []
    new_updates: list = []

    for query in queries:
        results = _search_ddg(query, max_results=4)
        time.sleep(1.5)
        all_results.extend(results)

        for r in results:
            if not _is_relevant(r["title"], r["snippet"], name):
                continue
            if _is_duplicate(r["title"], existing_pool + new_updates):
                continue
            upcoming = _is_upcoming(r["title"], r["snippet"])
            new_updates.append({
                "competitor":  name,
                "title":       f"🔜 {r['title']}" if upcoming else r["title"],
                "category":    _detect_category(r["title"], r["snippet"]),
                "date":        today,
                "summary":     r["snippet"][:500] if r["snippet"] else r["title"],
                "source_url":  r["url"],
            })

    # G2 rating
    rating = _scrape_g2_rating(name)
    time.sleep(1.0)

    # Alerts
    feature_alert, pricing_alert = _detect_alerts(name, all_results)

    return {
        "new_updates":    new_updates,
        "rating":         rating,
        "feature_alert":  feature_alert,
        "pricing_alert":  pricing_alert,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def analyze_all(write_fn=print) -> dict:
    """
    Research all 11 direct competitors and refresh data across all tabs.

    Args:
        write_fn: callable for progress output — pass st.write for live
                  Streamlit streaming, or the default print for CLI.

    Writes:
        .tmp/product_updates.json  — new updates prepended
        .tmp/analysis_cache.json   — ratings + alerts for all tabs

    Returns:
        {
          "total":           int,          # new product updates added
          "ratings_updated": int,          # competitors with refreshed G2 data
          "feature_alerts":  {name: str},
          "pricing_alerts":  {name: str},
        }
    """
    competitors = list(_QUERIES.keys())

    existing: list = []
    if _UPDATES_FILE.exists():
        try:
            existing = json.loads(_UPDATES_FILE.read_text())
        except Exception:
            pass

    all_new:         list = []
    ratings_cache:   dict = {}
    feature_alerts:  dict = {}
    pricing_alerts:  dict = {}
    ratings_updated: int  = 0

    for i, name in enumerate(competitors, 1):
        write_fn(f"🔍 **{name}** — searching & scraping... ({i}/{len(competitors)})")
        try:
            res = analyze_competitor(name, existing + all_new)

            # Product updates
            new = res["new_updates"]
            all_new.extend(new)

            # Ratings
            if res["rating"]:
                ratings_cache[name] = res["rating"]
                ratings_updated += 1

            # Alerts
            if res["feature_alert"]:
                feature_alerts[name] = res["feature_alert"]
            if res["pricing_alert"]:
                pricing_alerts[name] = res["pricing_alert"]

            # Progress line
            parts = []
            if new:
                parts.append(f"{len(new)} new update(s)")
            if res["rating"]:
                r = res["rating"]
                parts.append(f"G2 {r.get('g2_rating', '?')}★ ({r.get('g2_reviews', 0):,} reviews)")
            if res["feature_alert"]:
                parts.append("⚡ feature alert")
            if res["pricing_alert"]:
                parts.append("💰 pricing alert")

            if parts:
                write_fn(f"✅ **{name}**: {' · '.join(parts)}")
            else:
                write_fn(f"— **{name}**: no changes detected")

        except Exception as exc:
            write_fn(f"⚠️ **{name}**: error — {str(exc)[:100]}")

    # ── Persist product updates ───────────────────────────────────────────────
    _TMP.mkdir(exist_ok=True)
    _UPDATES_FILE.write_text(json.dumps(all_new + existing, indent=2))

    # ── Persist analysis cache (used by all tabs) ─────────────────────────────
    cache = {
        "last_analyzed":   datetime.now().isoformat(),
        "ratings":         ratings_cache,
        "feature_alerts":  feature_alerts,
        "pricing_alerts":  pricing_alerts,
        "product_updates_added": len(all_new),
    }
    _CACHE_FILE.write_text(json.dumps(cache, indent=2))

    return {
        "total":           len(all_new),
        "ratings_updated": ratings_updated,
        "feature_alerts":  feature_alerts,
        "pricing_alerts":  pricing_alerts,
    }


if __name__ == "__main__":
    print("=== Swivl Competitive Analysis ===\n")
    result = analyze_all(write_fn=print)
    print(f"\nDone.")
    print(f"  Product updates added : {result['total']}")
    print(f"  Ratings refreshed     : {result['ratings_updated']}")
    print(f"  Feature alerts        : {len(result['feature_alerts'])}")
    print(f"  Pricing alerts        : {len(result['pricing_alerts'])}")
