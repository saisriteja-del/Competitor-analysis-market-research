"""
scrape_reddit.py — Scrape Reddit for user pain points about FSM competitors.

Uses old.reddit.com JSON API (server-rendered, no JS required).
User-Agent must be descriptive per Reddit API ToS.

Subreddits searched:
  smallbusiness, Entrepreneur, HVAC, plumbing, FieldServiceManagement, electricians

Queries per competitor:
  "{name} pricing", "{name} alternative", "{name} problems", "left {name}"

Pain tags detected via keyword scan:
  pricing, support, mobile, onboarding, features, scaling, bugs, contracts
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests

ROOT_DIR = Path(__file__).parent.parent
TMP_DIR = ROOT_DIR / ".tmp"
TMP_DIR.mkdir(exist_ok=True)

REDDIT_HEADERS = {
    "User-Agent": "Swivl-Intel-Bot/1.0 (competitor research; contact: swivl.tech)",
    "Accept": "application/json",
}

SUBREDDITS = [
    "smallbusiness",
    "Entrepreneur",
    "HVAC",
    "plumbing",
    "FieldServiceManagement",
    "electricians",
]

COMPETITORS = ["Jobber", "Workiz", "HouseCallPro"]

QUERY_TEMPLATES = [
    "{name} pricing",
    "{name} alternative",
    "{name} problems",
    "left {name}",
    "switched from {name}",
]

PAIN_KEYWORDS: dict[str, list[str]] = {
    "pricing": ["expensive", "price", "cost", "pricing", "subscription", "per user", "per seat", "too much"],
    "support": ["support", "customer service", "help", "unresponsive", "slow response"],
    "mobile": ["mobile app", "app crash", "offline", "android", "iphone", "ios"],
    "onboarding": ["onboarding", "setup", "implementation", "training", "steep learning", "complicated"],
    "features": ["missing", "feature request", "doesn't have", "no integration", "lack"],
    "scaling": ["scale", "growing team", "more users", "franchise", "multi location"],
    "bugs": ["bug", "glitch", "broken", "doesn't work", "error", "crash"],
    "contracts": ["contract", "locked in", "cancel", "cancellation", "yearly commitment"],
}

# Hardcoded illustrative fallback posts (used if Reddit is rate-limited)
FALLBACK_POSTS = {
    "Jobber": [
        {
            "title": "Jobber pricing getting ridiculous — $249/user?",
            "subreddit": "smallbusiness",
            "pain_tags": ["pricing"],
            "url": "https://old.reddit.com/r/smallbusiness",
            "source": "illustrative",
        },
        {
            "title": "Switched from Jobber — hit the user pricing wall at 12 techs",
            "subreddit": "FieldServiceManagement",
            "pain_tags": ["pricing", "scaling"],
            "url": "https://old.reddit.com/r/FieldServiceManagement",
            "source": "illustrative",
        },
        {
            "title": "Jobber has no offline mode — deal breaker for rural jobs",
            "subreddit": "HVAC",
            "pain_tags": ["mobile", "features"],
            "url": "https://old.reddit.com/r/HVAC",
            "source": "illustrative",
        },
    ],
    "Workiz": [
        {
            "title": "Workiz UI feels like it was built in 2015",
            "subreddit": "smallbusiness",
            "pain_tags": ["features"],
            "url": "https://old.reddit.com/r/smallbusiness",
            "source": "illustrative",
        },
        {
            "title": "Workiz customer support took 3 days to reply",
            "subreddit": "Entrepreneur",
            "pain_tags": ["support"],
            "url": "https://old.reddit.com/r/Entrepreneur",
            "source": "illustrative",
        },
    ],
    "HouseCallPro": [
        {
            "title": "HouseCallPro billing me more each month — per user pricing is insane",
            "subreddit": "plumbing",
            "pain_tags": ["pricing", "scaling"],
            "url": "https://old.reddit.com/r/plumbing",
            "source": "illustrative",
        },
        {
            "title": "HouseCallPro Pro tier missing key reporting features",
            "subreddit": "FieldServiceManagement",
            "pain_tags": ["features"],
            "url": "https://old.reddit.com/r/FieldServiceManagement",
            "source": "illustrative",
        },
    ],
}


# ── Pain tag detection ─────────────────────────────────────────────────────────

def detect_pain_tags(text: str) -> list[str]:
    text_lower = text.lower()
    tags = []
    for tag, keywords in PAIN_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            tags.append(tag)
    return tags


# ── Reddit fetching ────────────────────────────────────────────────────────────

def _fetch_reddit_search(subreddit: str, query: str, cache_key: str, force_refresh: bool) -> list[dict]:
    """Search a subreddit via old.reddit.com JSON and return post dicts."""
    cache_path = TMP_DIR / f"reddit_{cache_key}.json"

    if not force_refresh and cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)

    url = (
        f"https://old.reddit.com/r/{subreddit}/search.json"
        f"?q={requests.utils.quote(query)}&restrict_sr=on&sort=relevance&limit=10&t=year"
    )

    try:
        time.sleep(2.0)  # polite delay — Reddit is strict about rate limits
        resp = requests.get(url, headers=REDDIT_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        posts = data.get("data", {}).get("children", [])
        result = []
        for post in posts:
            pd = post.get("data", {})
            title = pd.get("title", "")
            selftext = pd.get("selftext", "")
            combined = f"{title} {selftext}"
            result.append({
                "title": title,
                "subreddit": subreddit,
                "score": pd.get("score", 0),
                "url": f"https://reddit.com{pd.get('permalink', '')}",
                "pain_tags": detect_pain_tags(combined),
                "source": "live",
            })

        if cache_key:
            with open(cache_path, "w") as f:
                json.dump(result, f, indent=2)

        return result

    except requests.exceptions.HTTPError as e:
        print(f"  [reddit] HTTP {e.response.status_code} for r/{subreddit} query '{query}'")
    except requests.exceptions.ConnectionError:
        print(f"  [reddit] Connection error for r/{subreddit}")
    except requests.exceptions.Timeout:
        print(f"  [reddit] Timeout for r/{subreddit}")
    except Exception as e:
        print(f"  [reddit] Error for r/{subreddit}: {e}")

    return []


# ── Pain summary ──────────────────────────────────────────────────────────────

def _summarize_pain(posts: list[dict]) -> dict[str, int]:
    """Count pain tag occurrences across all posts."""
    counts: dict[str, int] = {}
    for post in posts:
        for tag in post.get("pain_tags", []):
            counts[tag] = counts.get(tag, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


# ── Swivl opportunities from pain ─────────────────────────────────────────────

def _derive_opportunities(pain_summary: dict) -> list[str]:
    """Map top competitor pains to Swivl positioning opportunities."""
    opportunities = []
    pain_totals: dict[str, int] = {}
    for competitor_pain in pain_summary.values():
        for tag, count in competitor_pain.items():
            pain_totals[tag] = pain_totals.get(tag, 0) + count

    if pain_totals.get("pricing", 0) >= 3:
        opportunities.append(
            "Per-user pricing anger is widespread — lead messaging with Swivl's flat rate, "
            "especially for teams 10+ techs"
        )
    if pain_totals.get("scaling", 0) >= 2:
        opportunities.append(
            "Growing teams dread bill shock — create a 'cost at scale' calculator comparing Swivl vs. competitors"
        )
    if pain_totals.get("onboarding", 0) >= 2:
        opportunities.append(
            "Painful onboarding (especially ServiceTitan) — Swivl's fast setup is a differentiator to highlight"
        )
    if pain_totals.get("mobile", 0) >= 2:
        opportunities.append(
            "Mobile app issues are common — invest in offline mode and field-first UX"
        )
    if pain_totals.get("support", 0) >= 2:
        opportunities.append(
            "Poor support experience mentioned frequently — a Swivl 'human-first support' promise is competitive"
        )
    if pain_totals.get("contracts", 0) >= 2:
        opportunities.append(
            "Long-term contracts are a pain point — Swivl's month-to-month flexibility is an asset"
        )

    return opportunities


# ── Main scraper ──────────────────────────────────────────────────────────────

def scrape_reddit(force_refresh: bool = False) -> dict:
    """
    Scrape Reddit pain points for all four competitors.
    Saves to .tmp/reddit_data.json and returns the dict.
    """
    all_posts: dict[str, list[dict]] = {c: [] for c in COMPETITORS}
    reddit_blocked = False

    for competitor in COMPETITORS:
        print(f"  Reddit → {competitor}")
        competitor_posts = []

        for sub in SUBREDDITS:
            for query_tmpl in QUERY_TEMPLATES[:3]:  # limit to 3 queries × 6 subs = 18 calls max
                query = query_tmpl.format(name=competitor)
                slug = re.sub(r"[^a-z0-9]", "_", f"{competitor}_{sub}_{query_tmpl}".lower())[:50]
                posts = _fetch_reddit_search(sub, query, slug, force_refresh)
                competitor_posts.extend(posts)

        # Deduplicate by URL
        seen = set()
        deduped = []
        for post in competitor_posts:
            if post["url"] not in seen:
                seen.add(post["url"])
                deduped.append(post)

        # If no live posts, fall back to illustrative
        if not deduped:
            reddit_blocked = True
            deduped = FALLBACK_POSTS.get(competitor, [])
            print(f"    No live posts — using {len(deduped)} illustrative fallbacks")
        else:
            print(f"    Found {len(deduped)} posts")

        # Keep top posts by score
        deduped.sort(key=lambda p: p.get("score", 0), reverse=True)
        all_posts[competitor] = deduped[:20]

    # Build pain summary
    pain_summary = {c: _summarize_pain(all_posts[c]) for c in COMPETITORS}
    opportunities = _derive_opportunities(pain_summary)

    result = {
        "posts": all_posts,
        "pain_point_summary": pain_summary,
        "swivl_opportunities": opportunities,
        "scrape_method": "illustrative_fallback" if reddit_blocked else "live",
        "note": (
            "Reddit results are illustrative examples based on common FSM community themes."
            if reddit_blocked
            else "Live Reddit posts from FSM-related subreddits."
        ),
    }

    with open(TMP_DIR / "reddit_data.json", "w") as f:
        json.dump(result, f, indent=2)

    return result


if __name__ == "__main__":
    data = scrape_reddit(force_refresh=True)
    print(f"\nScrape method: {data['scrape_method']}")
    print("\nPain point summary:")
    for company, pain in data["pain_point_summary"].items():
        if pain:
            print(f"  {company}: {pain}")
    print("\nSwivl opportunities:")
    for opp in data["swivl_opportunities"]:
        print(f"  → {opp}")
    print(f"\nTotal posts collected:")
    for company, posts in data["posts"].items():
        print(f"  {company}: {len(posts)} posts")
