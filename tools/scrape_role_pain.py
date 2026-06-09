"""
scrape_role_pain.py — Surface role-specific pain points from Reddit for FSM
dispatchers and technicians.

Unlike scrape_reddit.py (which is competitor-focused), this tool is
persona-focused. Each query is tagged with a role upfront, and the scraper
carries that tag through so the output is segmented by dispatcher vs. tech.

See workflows/role_pain_points.md for the full SOP.

Usage:
    python3 tools/scrape_role_pain.py             # live scrape + cache
    python3 tools/scrape_role_pain.py --no-comments   # skip comment scraping
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Iterable

import requests

ROOT_DIR = Path(__file__).parent.parent
TMP_DIR = ROOT_DIR / ".tmp"
TMP_DIR.mkdir(exist_ok=True)

REDDIT_HEADERS = {
    "User-Agent": "Swivl-RolePain-Bot/1.0 (role-based FSM research; contact: swivl.tech)",
    "Accept": "application/json",
}

REQUEST_SLEEP = 2.5   # seconds between requests — Reddit is strict
COMMENT_SLEEP = 2.0
MAX_POSTS_PER_QUERY = 10
TWO_YEARS_SECS = 60 * 60 * 24 * 365 * 2

# ── Subreddits ────────────────────────────────────────────────────────────────
SUBREDDITS = [
    "HVAC",
    "HVACadvice",
    "Plumbing",
    "electricians",
    "askelectricians",
    "Appliances",
    "Roofing",
    "PestControl",
    "Landscaping",
    "FieldServiceManagement",
    "smallbusiness",
    "Entrepreneur",
]

# ── Role-tagged query plan ────────────────────────────────────────────────────
# Each entry: (query, role)   role ∈ {"technician", "dispatcher", "both"}
QUERIES: list[tuple[str, str]] = [
    # Technician pain
    ("mobile app crash", "technician"),
    ("FSM app offline", "technician"),
    ("app on the job", "technician"),
    ("paperwork on job", "technician"),
    ("signature capture", "technician"),
    ("parts inventory truck", "technician"),
    ("GPS tracking technician", "technician"),
    ("time tracking job", "technician"),
    ("dispatch sent wrong", "technician"),
    ("stuck on job site", "technician"),
    ("invoice on phone", "technician"),
    ("technician app", "technician"),

    # Dispatcher pain
    ("scheduling techs", "dispatcher"),
    ("dispatch board", "dispatcher"),
    ("route optimization", "dispatcher"),
    ("tech no show", "dispatcher"),
    ("customer callback dispatch", "dispatcher"),
    ("emergency dispatch", "dispatcher"),
    ("overbooked schedule", "dispatcher"),
    ("last minute cancel", "dispatcher"),
    ("dispatcher software", "dispatcher"),
    ("reschedule customer", "dispatcher"),
    ("dispatch ETA", "dispatcher"),

    # Cross-cutting
    ("field service software", "both"),
    ("service business software", "both"),
    ("work order app", "both"),
    ("technician dispatcher frustration", "both"),
]

# ── Theme taxonomy ────────────────────────────────────────────────────────────
THEME_KEYWORDS: dict[str, list[str]] = {
    "scheduling": [
        "schedule", "double book", "double-book", "reschedule", "cancel",
        "overbook", "calendar", "booking", "appointment",
    ],
    "routing": [
        "route", "routing", "drive time", "travel time", "map", "gps",
        "optimize route", "zig zag", "back and forth",
    ],
    "dispatch_comms": [
        "dispatcher", "dispatch", "eta", "wrong address", "wrong info",
        "texted me", "called me", "radio", "communicate",
    ],
    "mobile_ux": [
        "app crash", "app sucks", "ui", "ux", "slow app", "login loop",
        "battery drain", "clunky app", "buggy app", "freezes",
    ],
    "offline": [
        "offline", "no signal", "no service", "can't sync", "lost data",
        "basement", "rural", "dead zone",
    ],
    "paperwork": [
        "paperwork", "signature", "form", "photo", "estimate", "data entry",
        "typing on phone", "fat finger",
    ],
    "parts_inventory": [
        "parts", "inventory", "truck stock", "warehouse", "wrong part",
        "order part", "out of stock",
    ],
    "customer_comms": [
        "reminder", "review", "quote approval", "customer no show",
        "customer cancel", "text customer", "auto reminder",
    ],
    "billing_invoicing": [
        "invoice", "invoicing", "collect payment", "card reader",
        "receivable", "collections", "payment processing",
    ],
    "reporting": [
        "report", "kpi", "dashboard", "metrics", "per tech", "revenue report",
        "profitability",
    ],
    "training_onboarding": [
        "onboarding", "training", "learning curve", "hard to learn",
        "new hire", "ramp up", "complicated",
    ],
    "integrations": [
        "quickbooks", "qbo", "stripe", "integration", "accounting",
        "phone system", "api", "webhook",
    ],
}

# ── FSM relevance guard ──────────────────────────────────────────────────────
# A post must mention at least one of these terms (title OR body) to count,
# UNLESS it came from a trade-specific subreddit where context already implies FSM.
FSM_VOCAB = [
    "dispatch", "technician", "tech ", "field service", "service call",
    "job site", "jobsite", "work order", "scheduling", "schedule",
    "service business", "trades", "trade business", "truck", "van",
    "customer ", "estimate", "invoice", "route",
    "hvac", "plumb", "electric", "roofing", "pest", "landscap",
    "appliance", "handyman",
]
TRADE_SUBS = {
    "HVAC", "HVACadvice", "Plumbing", "electricians", "askelectricians",
    "Appliances", "Roofing", "PestControl", "Landscaping",
    "FieldServiceManagement",
}


def _is_fsm_relevant(post: dict) -> bool:
    """Lightweight guard so broad business subs don't drag in off-topic posts."""
    if post.get("subreddit") in TRADE_SUBS:
        return True
    blob = (post.get("title", "") + " " + post.get("body", "")).lower()
    return any(term in blob for term in FSM_VOCAB)


# ── Fallback / illustrative posts (used only if all live queries fail) ───────
FALLBACK_POSTS: list[dict] = [
    {
        "title": "Dispatcher here — scheduling software keeps letting us double-book",
        "subreddit": "FieldServiceManagement",
        "role": "dispatcher",
        "themes": ["scheduling", "mobile_ux"],
        "url": "https://old.reddit.com/r/FieldServiceManagement",
        "body": "Every Friday we end up with two techs on the same job. The software doesn't flag the conflict until someone opens the board.",
        "source": "illustrative",
    },
    {
        "title": "App goes offline in basements and I lose 20 min of notes",
        "subreddit": "HVAC",
        "role": "technician",
        "themes": ["offline", "mobile_ux", "paperwork"],
        "url": "https://old.reddit.com/r/HVAC",
        "body": "Every residential call where I'm in a basement my FSM app drops. Notes and photos don't sync back when I pop up.",
        "source": "illustrative",
    },
    {
        "title": "Why does my dispatcher always send me the wrong address?",
        "subreddit": "Plumbing",
        "role": "technician",
        "themes": ["dispatch_comms"],
        "url": "https://old.reddit.com/r/Plumbing",
        "body": "Third time this month I've shown up to the wrong unit in an apartment complex. Address in the app is correct but unit # isn't captured.",
        "source": "illustrative",
    },
    {
        "title": "Route optimization in Jobber/HCP is basically nonexistent",
        "subreddit": "smallbusiness",
        "role": "dispatcher",
        "themes": ["routing"],
        "url": "https://old.reddit.com/r/smallbusiness",
        "body": "I manually drag appointments around every morning to avoid sending my tech from downtown to the suburbs to downtown again.",
        "source": "illustrative",
    },
    {
        "title": "Parts inventory sync between truck and warehouse is a nightmare",
        "subreddit": "electricians",
        "role": "technician",
        "themes": ["parts_inventory", "integrations"],
        "url": "https://old.reddit.com/r/electricians",
        "body": "I use up the last of a breaker on a job and nobody at the warehouse knows until I'm back. Our FSM doesn't sync with QBO inventory.",
        "source": "illustrative",
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _cache_path(key: str) -> Path:
    safe = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")[:80]
    return TMP_DIR / f"reddit_role_{safe}.json"


def detect_themes(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for theme, keywords in THEME_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            found.append(theme)
    return found


# ── Fetchers ──────────────────────────────────────────────────────────────────

def _search_subreddit(subreddit: str, query: str, force_refresh: bool) -> list[dict]:
    """Search one subreddit for one query via old.reddit.com JSON."""
    cache_key = f"search_{subreddit}_{query}"
    cache = _cache_path(cache_key)

    if not force_refresh and cache.exists():
        try:
            with open(cache) as f:
                return json.load(f)
        except Exception:
            pass

    url = (
        f"https://old.reddit.com/r/{subreddit}/search.json"
        f"?q={requests.utils.quote(query)}"
        f"&restrict_sr=on&sort=relevance&limit={MAX_POSTS_PER_QUERY}&t=year"
    )
    try:
        time.sleep(REQUEST_SLEEP)
        resp = requests.get(url, headers=REDDIT_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        code = getattr(e.response, "status_code", "?")
        print(f"  [role_pain] HTTP {code} r/{subreddit} q='{query}'")
        return []
    except Exception as e:
        print(f"  [role_pain] err r/{subreddit} q='{query}': {e}")
        return []

    now = time.time()
    posts = []
    for child in data.get("data", {}).get("children", []):
        pd_ = child.get("data", {})
        created = pd_.get("created_utc", 0)
        if created and (now - created) > TWO_YEARS_SECS:
            continue
        posts.append({
            "id": pd_.get("id"),
            "title": pd_.get("title", ""),
            "body": pd_.get("selftext", "") or "",
            "subreddit": pd_.get("subreddit", subreddit),
            "score": pd_.get("score", 0),
            "num_comments": pd_.get("num_comments", 0),
            "created_utc": created,
            "permalink": pd_.get("permalink", ""),
            "url": f"https://old.reddit.com{pd_.get('permalink', '')}",
        })

    try:
        with open(cache, "w") as f:
            json.dump(posts, f, indent=2)
    except Exception:
        pass
    return posts


def _fetch_top_comment(permalink: str, force_refresh: bool) -> str:
    """Fetch the single top comment body for a post — used for theme tagging + quote material."""
    if not permalink:
        return ""
    cache = _cache_path(f"comments_{permalink}")
    if not force_refresh and cache.exists():
        try:
            with open(cache) as f:
                return json.load(f).get("body", "")
        except Exception:
            pass

    url = f"https://old.reddit.com{permalink}.json?limit=3&sort=top"
    try:
        time.sleep(COMMENT_SLEEP)
        resp = requests.get(url, headers=REDDIT_HEADERS, timeout=15)
        resp.raise_for_status()
        listing = resp.json()
    except Exception as e:
        print(f"  [role_pain] comment fetch failed {permalink}: {e}")
        return ""

    body = ""
    if isinstance(listing, list) and len(listing) >= 2:
        children = listing[1].get("data", {}).get("children", [])
        for c in children:
            if c.get("kind") != "t1":
                continue
            body = c.get("data", {}).get("body", "") or ""
            if body and body != "[deleted]" and body != "[removed]":
                break

    try:
        with open(cache, "w") as f:
            json.dump({"body": body}, f, indent=2)
    except Exception:
        pass
    return body


# ── Main pipeline ─────────────────────────────────────────────────────────────

def scrape_role_pain(force_refresh: bool = False, include_comments: bool = True) -> dict:
    """
    Scrape role-based FSM pain points from Reddit.
    Saves to .tmp/role_pain_data.json and returns the dict.
    """
    all_posts: list[dict] = []
    seen_ids: set[str] = set()
    live_any = False
    live_fail_count = 0
    query_count = 0

    for query, role in QUERIES:
        for subreddit in SUBREDDITS:
            query_count += 1
            posts = _search_subreddit(subreddit, query, force_refresh)
            if posts:
                live_any = True
            else:
                live_fail_count += 1

            for p in posts:
                pid = p.get("id")
                if not pid or pid in seen_ids:
                    continue
                if not _is_fsm_relevant(p):
                    continue  # prune off-topic drag-ins from broad subs
                seen_ids.add(pid)
                p["role"] = role
                p["matched_query"] = query
                all_posts.append(p)

        print(f"  [role_pain] {query!r} ({role}) — running total: {len(all_posts)} posts")

    # Pull top comment for the top ~60 posts (by score) to enrich theme tagging
    if include_comments and all_posts:
        top_for_comments = sorted(all_posts, key=lambda p: p.get("score", 0), reverse=True)[:60]
        for p in top_for_comments:
            comment_body = _fetch_top_comment(p.get("permalink", ""), force_refresh)
            if comment_body:
                p["top_comment"] = comment_body

    # Theme tagging
    for p in all_posts:
        combined = " ".join([
            p.get("title", ""),
            p.get("body", ""),
            p.get("top_comment", ""),
        ])
        p["themes"] = detect_themes(combined)

    # If nothing came back at all → illustrative fallback
    scrape_method = "live"
    if not all_posts:
        all_posts = list(FALLBACK_POSTS)
        scrape_method = "illustrative_fallback"
    elif live_fail_count > (query_count * 0.6):
        scrape_method = "partial"

    # Role × theme tally
    theme_summary = {
        "dispatcher": {},
        "technician": {},
        "both": {},
    }
    for p in all_posts:
        role = p.get("role", "both")
        bucket = theme_summary.setdefault(role, {})
        for theme in p.get("themes", []):
            bucket[theme] = bucket.get(theme, 0) + 1

    # Sort each bucket
    for role in theme_summary:
        theme_summary[role] = dict(
            sorted(theme_summary[role].items(), key=lambda x: x[1], reverse=True)
        )

    # Top quotes per theme (use post body or top comment, whichever is meatier)
    quotes_by_theme: dict[str, list[dict]] = {}
    for theme in THEME_KEYWORDS:
        candidates = [p for p in all_posts if theme in p.get("themes", [])]
        candidates.sort(key=lambda p: p.get("score", 0), reverse=True)
        quote_list = []
        for p in candidates[:5]:
            quote_text = (p.get("top_comment") or p.get("body") or p.get("title") or "")
            quote_text = quote_text.strip().replace("\n", " ")
            if len(quote_text) > 350:
                quote_text = quote_text[:340].rsplit(" ", 1)[0] + "…"
            quote_list.append({
                "role": p.get("role"),
                "subreddit": p.get("subreddit"),
                "title": p.get("title"),
                "quote": quote_text,
                "score": p.get("score", 0),
                "url": p.get("url"),
                "source": p.get("source", "live"),
            })
        if quote_list:
            quotes_by_theme[theme] = quote_list

    # Swivl product implications
    implications = _derive_implications(theme_summary)

    # Posts split by role (sorted by score)
    posts_by_role = {"dispatcher": [], "technician": [], "both": []}
    for p in all_posts:
        posts_by_role.setdefault(p.get("role", "both"), []).append(p)
    for role in posts_by_role:
        posts_by_role[role].sort(key=lambda p: p.get("score", 0), reverse=True)
        posts_by_role[role] = posts_by_role[role][:50]

    result = {
        "posts": posts_by_role,
        "theme_summary": theme_summary,
        "quotes": quotes_by_theme,
        "swivl_implications": implications,
        "scrape_method": scrape_method,
        "subreddits_searched": SUBREDDITS,
        "total_queries": query_count,
        "total_posts": sum(len(v) for v in posts_by_role.values()),
        "note": {
            "live": "Live Reddit data, past 12 months.",
            "partial": "Some queries failed (likely rate-limited). Mix of live + cached.",
            "illustrative_fallback": "Reddit blocked all queries — showing illustrative examples.",
        }[scrape_method],
    }

    with open(TMP_DIR / "role_pain_data.json", "w") as f:
        json.dump(result, f, indent=2)

    return result


def _derive_implications(theme_summary: dict) -> list[dict]:
    """Translate theme tallies into concrete Swivl product/positioning implications."""
    totals: dict[str, int] = {}
    for role_bucket in theme_summary.values():
        for theme, count in role_bucket.items():
            totals[theme] = totals.get(theme, 0) + count

    implications: list[dict] = []

    if totals.get("scheduling", 0) >= 3:
        implications.append({
            "theme": "scheduling",
            "audience": "dispatcher",
            "implication": "Dispatchers keep hitting double-booking and last-minute cancel chaos. Surface a conflict-detection + one-tap reschedule flow prominently in the dispatch board.",
        })
    if totals.get("routing", 0) >= 3:
        implications.append({
            "theme": "routing",
            "audience": "dispatcher",
            "implication": "Route planning is done manually by dispatchers even in tools that claim routing. A visible auto-route button with explainable ordering (not a black box) is underbuilt in the market.",
        })
    if totals.get("mobile_ux", 0) >= 3:
        implications.append({
            "theme": "mobile_ux",
            "audience": "technician",
            "implication": "Tech-facing app UX is the #1 complaint surface. Invest in speed, offline-first state, and minimal taps to close a job.",
        })
    if totals.get("offline", 0) >= 2:
        implications.append({
            "theme": "offline",
            "audience": "technician",
            "implication": "Offline is a real workflow (basements, rural, underground). Treat offline-first as a marketed capability, not a footnote.",
        })
    if totals.get("dispatch_comms", 0) >= 2:
        implications.append({
            "theme": "dispatch_comms",
            "audience": "both",
            "implication": "Wrong address / wrong unit / missing context between dispatcher and tech is a recurring theme. Build structured pre-job briefs (unit #, gate code, contact) that the dispatcher must fill before the card moves to the tech.",
        })
    if totals.get("parts_inventory", 0) >= 2:
        implications.append({
            "theme": "parts_inventory",
            "audience": "technician",
            "implication": "Truck-to-warehouse inventory sync is broken in most tools. A lightweight 'used on job' button that decrements stock and triggers reorder is a wedge.",
        })
    if totals.get("paperwork", 0) >= 2:
        implications.append({
            "theme": "paperwork",
            "audience": "technician",
            "implication": "Typing on a phone while dirty/in the rain is painful. Lean into voice notes, templates, and photo-first documentation.",
        })
    if totals.get("billing_invoicing", 0) >= 2:
        implications.append({
            "theme": "billing_invoicing",
            "audience": "dispatcher",
            "implication": "Collections AR pain from the back office — a 'close job + take payment in one screen' flow is still differentiated.",
        })
    if totals.get("integrations", 0) >= 2:
        implications.append({
            "theme": "integrations",
            "audience": "both",
            "implication": "QBO / Stripe / phone system integration gaps are called out repeatedly. Document + demo these integrations prominently in sales.",
        })

    return implications


# ── CLI ───────────────────────────────────────────────────────────────────────

def _main(argv: Iterable[str]) -> None:
    parser = argparse.ArgumentParser(description="Scrape Reddit for FSM role pain points.")
    parser.add_argument("--no-comments", action="store_true", help="Skip top-comment enrichment.")
    parser.add_argument("--force", action="store_true", help="Force re-fetch (ignore cache).")
    args = parser.parse_args(list(argv))

    data = scrape_role_pain(force_refresh=args.force, include_comments=not args.no_comments)

    print(f"\nScrape method: {data['scrape_method']}")
    print(f"Total posts: {data['total_posts']}")
    print("\nRole × theme tally:")
    for role, themes in data["theme_summary"].items():
        if themes:
            top = ", ".join(f"{t}:{c}" for t, c in list(themes.items())[:5])
            print(f"  {role:<11s} {top}")
    print("\nTop 3 quotes per theme:")
    for theme, quotes in list(data["quotes"].items())[:8]:
        print(f"\n  [{theme}]")
        for q in quotes[:3]:
            print(f"    • ({q['role']}, r/{q['subreddit']}, {q['score']}↑) {q['quote'][:140]}")
    print("\nSwivl implications:")
    for imp in data["swivl_implications"]:
        print(f"  → [{imp['theme']} / {imp['audience']}] {imp['implication']}")


if __name__ == "__main__":
    _main(sys.argv[1:])
