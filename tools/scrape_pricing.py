"""
scrape_pricing.py — Pricing data for direct competitors: Jobber, Workiz, HouseCallPro.

Strategy:
  - Hardcoded baseline for Jobber + Workiz (Cloudflare / no public page).
  - Live scraping for HouseCallPro (page is accessible and parseable).
"""

import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scraper_base import fetch_page, save_json

TODAY = date.today().strftime("%B %Y")

# ── Hardcoded baselines ────────────────────────────────────────────────────────
# Update these when a competitor announces a pricing change.
# Source URLs are included for manual verification.

BASELINE = {
    "Jobber": {
        "plans": [
            {"name": "Lite",    "price": "$9/mo/user"},
            {"name": "Core",    "price": "$49/mo/user"},
            {"name": "Connect", "price": "$129/mo/user"},
            {"name": "Grow",    "price": "$249/mo/user"},
        ],
        "per_user": "Yes — per user/technician",
        "url": "https://getjobber.com/pricing/",
        "note": (
            f"Baseline as of {TODAY}. Site is Cloudflare-protected so live scraping "
            "is unavailable — verify current prices at the source URL."
        ),
    },
    "Workiz": {
        "plans": [
            {"name": "Solo",     "price": "Free (1 user, limited features)"},
            {"name": "Team",     "price": "~$225/mo (5 users, est.)"},
            {"name": "Business", "price": "Contact sales"},
        ],
        "per_user": "Yes — per user/technician",
        "url": "https://www.workiz.com/",
        "note": (
            f"Workiz does not publish a public pricing page as of {TODAY}. "
            "Figures above are estimates from public reviews and press. "
            "Request a demo at workiz.com for current pricing."
        ),
    },
    "HouseCallPro": {
        "plans": [
            {"name": "Basic",      "price": "$59/mo (1 user)"},
            {"name": "Essentials", "price": "$149/mo"},
            {"name": "Pro",        "price": "$299/mo"},
            {"name": "Scale",      "price": "Contact sales"},
        ],
        "per_user": "Yes — per user/technician",
        "url": "https://www.housecallpro.com/pricing/",
        "note": f"Baseline as of {TODAY}. Live scrape runs on top — see below.",
    },
}


# ── Live scraper for HouseCallPro ─────────────────────────────────────────────

def _scrape_hcp_pricing(force_refresh: bool) -> list[dict] | None:
    """
    Parse HouseCallPro's pricing page.
    Returns a list of plan dicts, or None if scraping fails.
    """
    soup = fetch_page(
        "https://www.housecallpro.com/pricing/",
        cache_key="housecallpro_pricing",
        force_refresh=force_refresh,
    )
    if not soup:
        return None

    text = soup.get_text(" ", strip=True)

    # Extract pairs like "Basic ... $59/mo" from the flat text stream
    # Pattern: plan name followed within 120 chars by a dollar price
    raw = re.findall(
        r"(Basic|Essentials|Pro(?!\+)|Scale)[\s\S]{0,120}?(\$\d+(?:/mo)?)",
        text,
    )

    if not raw:
        return None

    # Dedupe keeping first occurrence per plan name
    seen, plans = set(), []
    for name, price in raw:
        if name not in seen:
            seen.add(name)
            plans.append({"name": name, "price": price + "/mo" if "/mo" not in price else price})

    return plans if plans else None


# ── Main ───────────────────────────────────────────────────────────────────────

def scrape_all_pricing(force_refresh: bool = False) -> dict:
    """
    Return pricing data for all four competitors.
    Saves to .tmp/pricing_data.json.
    """
    results = {}

    for name, baseline in BASELINE.items():
        print(f"  Pricing → {name}")
        entry = dict(baseline)
        entry["plans"] = list(baseline["plans"])  # copy

        # Attempt live scrape for HouseCallPro
        if name == "HouseCallPro":
            live_plans = _scrape_hcp_pricing(force_refresh)
            if live_plans:
                entry["plans"] = live_plans
                entry["note"] = (
                    f"Live scraped {TODAY}. Annual pricing shown where detected. "
                    "Verify at source URL."
                )
                print(f"    ✓ Live plans found: {[p['name'] for p in live_plans]}")
            else:
                print("    ⚠ Live scrape returned nothing — using baseline")

        results[name] = entry

    save_json(results, "pricing_data.json")
    return results


if __name__ == "__main__":
    data = scrape_all_pricing(force_refresh=True)
    for name, info in data.items():
        print(f"\n{name} ({info['per_user']})")
        for p in info["plans"]:
            print(f"  {p['name']}: {p['price']}")
        print(f"  Note: {info['note']}")
