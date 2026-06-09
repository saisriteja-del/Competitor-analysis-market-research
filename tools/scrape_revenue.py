"""
scrape_revenue.py — Collect revenue & growth signals for all four competitors.

Strategy:
  1. Start with a hardcoded baseline of publicly known figures
     (funding rounds, IPO data, employee ranges from LinkedIn/public sources).
  2. Scrape G2 and Capterra for live ratings + review counts as market-traction proxies.
  3. Scrape DuckDuckGo HTML search for recent news headlines per company.

All estimates are clearly labeled. Private companies never publish revenue,
so estimates come from funding announcements, industry research, and press.
"""

import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scraper_base import fetch_page, save_json

# ── Baseline data from public sources (funding announcements, press, IPO filings) ──
# Update this dict whenever a major funding round or earnings release is published.
BASELINE = {
    "Jobber": {
        "estimated_revenue": "~$100M–$150M ARR (est.)",
        "total_raised": "$370M+",
        "last_funding": "Series D — $100M (2021)",
        "employees": "500–700",
        "founded": "2011",
        "hq": "Edmonton, Canada",
        "status": "Private",
        "notes": "Largest FSM player by brand recognition in the SMB segment.",
    },
    "Workiz": {
        "estimated_revenue": "~$20M–$40M ARR (est.)",
        "total_raised": "~$10M",
        "last_funding": "Seed/Series A (est. 2019)",
        "employees": "100–200",
        "founded": "2018",
        "hq": "San Diego, CA",
        "status": "Private",
        "notes": "Known for built-in VOIP calling and strong entry-level pricing.",
    },
    "HouseCallPro": {
        "estimated_revenue": "~$50M–$80M ARR (est.)",
        "total_raised": "$65M+",
        "last_funding": "Series B — $30M (2021)",
        "employees": "300–500",
        "founded": "2013",
        "hq": "San Diego, CA",
        "status": "Private",
        "notes": "Large community of home-service pros; strong review presence on G2/Capterra.",
    },
}

def _scrape_news(name: str, force_refresh: bool) -> list[str]:
    """
    Search DuckDuckGo HTML for recent news about the competitor.
    Returns up to 5 headline strings.
    """
    query = f"{name} field service management software news 2024 2025"
    url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"

    soup = fetch_page(url, cache_key=f"{name.lower()}_news", force_refresh=force_refresh)
    if not soup:
        return []

    headlines = []
    for result in soup.find_all("a", class_=re.compile(r"result__a|result-link", re.I))[:8]:
        text = result.get_text(strip=True)
        if text and 20 < len(text) < 200:
            headlines.append(text)

    return headlines[:5]


def scrape_all_revenue(force_refresh: bool = False) -> dict:
    """
    Assemble revenue & growth profile for all competitors.
    Saves to .tmp/revenue_data.json and returns the dict.
    """
    results = {}

    for name, baseline in BASELINE.items():
        print(f"  Revenue → {name}")

        entry = dict(baseline)
        entry["data_as_of"] = datetime.now().strftime("%B %Y")
        # G2 ratings are now collected in scrape_reviews.py (Voice of Customer tab)
        entry["g2_rating"] = "See Voice of Customer tab"
        entry["g2_reviews"] = "—"

        # Recent news
        news = _scrape_news(name, force_refresh=force_refresh)
        entry["recent_news"] = news

        results[name] = entry

    save_json(results, "revenue_data.json")
    return results


if __name__ == "__main__":
    data = scrape_all_revenue(force_refresh=True)
    for name, info in data.items():
        print(f"\n{name}")
        print(f"  Revenue (est.): {info['estimated_revenue']}")
        print(f"  Funding:        {info['total_raised']} | Last: {info['last_funding']}")
        print(f"  Employees:      {info['employees']}")
        print(f"  G2:             {info.get('g2_rating', '—')} ({info.get('g2_reviews', '—')} reviews)")
        for n in info.get("recent_news", []):
            print(f"  News: {n}")
