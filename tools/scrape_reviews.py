"""
scrape_reviews.py — G2 and Capterra ratings + pros/cons for all four competitors.

Strategy:
  1. Attempt live JSON-LD / itemprop extraction from G2 product pages.
  2. Fall back to hardcoded baselines sourced from public G2 + Capterra summaries.
     Baselines are labeled with source date so the user knows when to refresh.

Output schema per competitor:
  {
    "g2": {
      "rating": float,
      "review_count": int,
      "top_pros": [str, ...],
      "top_cons": [str, ...],
      "scrape_method": "live" | "cached" | "hardcoded",
      "url": str,
    },
    "capterra": {
      "rating": float,
      "review_count": int,
      "top_pros": [str, ...],
      "top_cons": [str, ...],
      "scrape_method": "live" | "cached" | "hardcoded",
      "url": str,
    }
  }
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scraper_base import fetch_page, save_json

# ── Hardcoded baselines (sourced from G2 + Capterra public pages, April 2024) ─

BASELINES: dict[str, dict] = {
    "Jobber": {
        "g2": {
            "rating": 4.5,
            "review_count": 280,
            "top_pros": [
                "Easy to use — field techs learn it in under a day",
                "Strong mobile app with offline capability",
                "Excellent QuickBooks integration",
                "Client Hub portal praised by home service owners",
                "Good scheduling and dispatch calendar UI",
            ],
            "top_cons": [
                "Per-user pricing gets expensive fast as team grows",
                "Limited custom reporting — exports lack flexibility",
                "No built-in VOIP / phone features",
                "GPS tracking basic compared to dedicated fleet tools",
                "Customer support response times on lower tiers are slow",
            ],
            "url": "https://www.g2.com/products/jobber/reviews",
        },
        "capterra": {
            "rating": 4.5,
            "review_count": 900,
            "top_pros": [
                "Intuitive interface for non-technical users",
                "Time-saving automation for quotes and follow-ups",
                "Works well for solo operators through small teams",
            ],
            "top_cons": [
                "Pricing jumps steeply between tiers",
                "Inventory management is absent on most plans",
                "Reporting could be deeper for business analytics",
            ],
            "url": "https://www.capterra.com/p/93417/Jobber/",
        },
    },
    "Workiz": {
        "g2": {
            "rating": 4.4,
            "review_count": 95,
            "top_pros": [
                "Built-in phone/VOIP is a standout — tracks every call",
                "Online booking widget embeds easily on any website",
                "Good for franchise and multi-location businesses",
                "Automated SMS reminders reduce no-shows",
                "Affordable entry-level pricing for solo operators",
            ],
            "top_cons": [
                "UI feels outdated compared to newer FSM tools",
                "Mobile app less polished than Jobber or HCP",
                "Limited integrations outside of QuickBooks",
                "Customer support can be slow to resolve issues",
                "Reporting features are basic",
            ],
            "url": "https://www.g2.com/products/workiz/reviews",
        },
        "capterra": {
            "rating": 4.4,
            "review_count": 320,
            "top_pros": [
                "VOIP + scheduling in one tool saves money on phone systems",
                "Easy to set up and onboard a team",
                "Booking widget drives inbound leads",
            ],
            "top_cons": [
                "Customization options are limited",
                "Some users report bugs after updates",
                "No offline mobile mode",
            ],
            "url": "https://www.capterra.com/p/161166/Workiz/",
        },
    },
    "HouseCallPro": {
        "g2": {
            "rating": 4.3,
            "review_count": 170,
            "top_pros": [
                "Instant online booking is excellent for customer acquisition",
                "Built-in consumer financing (Wisetack) helps close larger jobs",
                "Strong review automation for Google/Facebook",
                "Clean mobile app with good photo capture",
                "Recurring service agreements and maintenance plans",
            ],
            "top_cons": [
                "Per-user pricing makes it expensive at scale",
                "Advanced features locked behind higher-tier plans",
                "QuickBooks sync has occasional data errors",
                "Phone support can be hard to reach",
                "Limited inventory and parts tracking",
            ],
            "url": "https://www.g2.com/products/housecall-pro/reviews",
        },
        "capterra": {
            "rating": 4.7,
            "review_count": 2700,
            "top_pros": [
                "Best-in-class Capterra rating among FSM tools",
                "Excellent customer service reputation",
                "Feature-rich for mid-market home service businesses",
            ],
            "top_cons": [
                "Cost increases significantly as user count grows",
                "Some advanced workflows require workarounds",
                "Occasional app performance issues on Android",
            ],
            "url": "https://www.capterra.com/p/133665/HouseCall-Pro/",
        },
    },
}

# G2 product slug to URL map (for live scraping attempt)
G2_URLS = {
    "Jobber": "https://www.g2.com/products/jobber/reviews",
    "Workiz": "https://www.g2.com/products/workiz/reviews",
    "HouseCallPro": "https://www.g2.com/products/housecall-pro/reviews",
}


# ── Live scrape attempt ───────────────────────────────────────────────────────

def _try_live_g2(name: str, url: str, force_refresh: bool) -> dict | None:
    """
    Attempt to extract rating + review count from G2's JSON-LD or itemprop data.
    Returns a partial dict on success, None on failure.
    """
    soup = fetch_page(url, cache_key=f"g2_{name.lower()}", force_refresh=force_refresh)
    if not soup:
        return None

    rating = None
    review_count = None

    # Strategy 1: JSON-LD AggregateRating
    import json
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
            agg = None
            if isinstance(data, list):
                for item in data:
                    if item.get("@type") in ("Product", "SoftwareApplication"):
                        agg = item.get("aggregateRating", {})
                        break
            elif data.get("@type") in ("Product", "SoftwareApplication"):
                agg = data.get("aggregateRating", {})
            if agg:
                rating = float(agg.get("ratingValue", 0)) or None
                review_count = int(agg.get("reviewCount", 0)) or None
                if rating:
                    break
        except Exception:
            continue

    # Strategy 2: itemprop
    if not rating:
        el = soup.find(itemprop="ratingValue")
        if el:
            try:
                rating = float(el.get("content", el.get_text()))
            except Exception:
                pass
    if not review_count:
        el = soup.find(itemprop="reviewCount")
        if el:
            try:
                review_count = int(re.sub(r"\D", "", el.get("content", el.get_text())))
            except Exception:
                pass

    if rating:
        return {"rating": rating, "review_count": review_count, "scrape_method": "live"}
    return None


# ── Main scraper ──────────────────────────────────────────────────────────────

def scrape_all_reviews(force_refresh: bool = False) -> dict:
    """
    Collect G2 + Capterra review data for all four competitors.
    Saves to .tmp/reviews_data.json and returns the dict.
    """
    results = {}

    for name, baseline in BASELINES.items():
        print(f"  Reviews → {name}")

        g2_result = dict(baseline["g2"])
        g2_result["scrape_method"] = "hardcoded"

        # Attempt live G2 scrape to get fresh rating/count
        live = _try_live_g2(name, G2_URLS[name], force_refresh)
        if live:
            g2_result["rating"] = live["rating"]
            if live.get("review_count"):
                g2_result["review_count"] = live["review_count"]
            g2_result["scrape_method"] = "live+baseline"
            print(f"    G2 live: {live['rating']}★ ({live.get('review_count', '?')} reviews)")
        else:
            print(f"    G2 live scrape failed — using baseline ({g2_result['rating']}★)")

        results[name] = {
            "g2": g2_result,
            "capterra": {**baseline["capterra"], "scrape_method": "hardcoded"},
        }

    save_json(results, "reviews_data.json")
    return results


if __name__ == "__main__":
    data = scrape_all_reviews(force_refresh=True)
    for name, info in data.items():
        g2 = info["g2"]
        cap = info["capterra"]
        print(f"\n{name}")
        print(f"  G2: {g2['rating']}★ ({g2['review_count']} reviews) [{g2['scrape_method']}]")
        print(f"  Capterra: {cap['rating']}★ ({cap['review_count']} reviews)")
        print(f"  Top G2 cons:")
        for c in g2["top_cons"][:3]:
            print(f"    — {c}")
