"""
Competitor research engine.
- get_suggestions(): returns curated FSM companies + AI-expanded list
- build_full_profile(): returns complete competitor profile via web research + Claude
- scrape_homepage(): extracts tagline/description from a URL
"""

import os
import json
import re
import requests
from urllib.parse import unquote, parse_qs, urlparse
from bs4 import BeautifulSoup

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Curated discovery list — FSM and adjacent companies with known URLs
# ---------------------------------------------------------------------------
DISCOVERY_LIST = [
    # ── Direct FSM ──────────────────────────────────────────────────────────
    {"name": "Commusoft",      "type": "direct",   "url": "https://www.commusoft.co.uk",     "hint": "UK-origin FSM for trades, expanding in US"},
    {"name": "Vonigo",         "type": "direct",   "url": "https://www.vonigo.com",          "hint": "FSM for franchise service businesses"},
    {"name": "BuildOps",       "type": "direct",   "url": "https://buildops.com",            "hint": "Commercial subcontractor FSM (HVAC, electrical)"},
    {"name": "Simpro",         "type": "direct",   "url": "https://simpro.com",              "hint": "Trade business management — Australia origin, US growing"},
    {"name": "BigChange",      "type": "direct",   "url": "https://www.bigchange.com",       "hint": "Mobile workforce management platform"},
    {"name": "Tradify",        "type": "direct",   "url": "https://www.tradifyhq.com",       "hint": "Job management for small trade businesses"},
    {"name": "Fergus",         "type": "direct",   "url": "https://www.fergus.com",          "hint": "Trade job management — New Zealand origin"},
    {"name": "RazorSync",      "type": "direct",   "url": "https://razorsync.com",           "hint": "FSM for small-medium service companies"},
    {"name": "FieldAware",     "type": "direct",   "url": "https://fieldaware.com",          "hint": "Mobile-first FSM platform"},
    {"name": "Gorilla Desk",   "type": "direct",   "url": "https://www.gorilladesks.com",    "hint": "Pest control and lawn care business software"},
    {"name": "Skimmer",        "type": "direct",   "url": "https://www.getskimmer.com",      "hint": "Pool service management software"},
    {"name": "Payzerware",     "type": "direct",   "url": "https://payzerware.com",          "hint": "HVAC and plumbing FSM with financing"},
    {"name": "ServiceBridge",  "type": "direct",   "url": "https://www.servicebridge.com",   "hint": "FSM for franchise service businesses"},
    {"name": "Zuper",          "type": "direct",   "url": "https://www.zuper.co",            "hint": "AI-powered FSM with strong mobile app"},
    {"name": "ServiceM8",      "type": "direct",   "url": "https://www.servicem8.com",       "hint": "Field service app popular in Australia/US"},
    {"name": "FieldVibe",      "type": "direct",   "url": "https://www.fieldvibe.com",       "hint": "Simple scheduling app for field service"},
    {"name": "Joblogic",       "type": "direct",   "url": "https://www.joblogic.com",        "hint": "FSM with compliance and asset management"},
    {"name": "MobiWork",       "type": "direct",   "url": "https://www.mobiwork.com",        "hint": "Mobile workforce and field service solutions"},
    {"name": "Wintac",         "type": "direct",   "url": "https://www.wintac.com",          "hint": "HVAC and plumbing service management"},
    {"name": "ServiceBox",     "type": "direct",   "url": "https://www.getservicebox.com",   "hint": "Job management for trade contractors"},
    {"name": "Loc8",           "type": "direct",   "url": "https://www.loc8.com",            "hint": "Asset management and FSM for facilities"},
    {"name": "Jonas Service",  "type": "direct",   "url": "https://www.jonas-software.com",  "hint": "FSM for HVAC, plumbing, electrical — mid-market"},
    {"name": "ServiceChannel", "type": "direct",   "url": "https://servicechannel.com",      "hint": "Facilities management and contractor marketplace"},
    {"name": "FieldEdge",      "type": "direct",   "url": "https://fieldedge.com",           "hint": "FSM for HVAC, plumbing, electrical contractors"},
    # ── Indirect / Adjacent ─────────────────────────────────────────────────
    {"name": "FieldNation",    "type": "indirect", "url": "https://www.fieldnation.com",     "hint": "Freelance tech marketplace — IT field work"},
    {"name": "Invoice Ninja",  "type": "indirect", "url": "https://www.invoiceninja.com",    "hint": "Invoicing for freelancers and small businesses"},
    {"name": "ServiceTrade",   "type": "indirect", "url": "https://servicetrade.com",        "hint": "Commercial service business management"},
    {"name": "DispatchTrack",  "type": "indirect", "url": "https://www.dispatchtrack.com",   "hint": "Last-mile delivery and service route optimization"},
    {"name": "OptimoRoute",    "type": "indirect", "url": "https://optimoroute.com",         "hint": "Route optimization for field service and delivery"},
    {"name": "WorkWave",       "type": "indirect", "url": "https://workwave.com",            "hint": "FSM for pest control, lawn, and security"},
    {"name": "Aspire",         "type": "indirect", "url": "https://www.youraspire.com",      "hint": "Business management for landscaping companies"},
    {"name": "ServicePower",   "type": "indirect", "url": "https://servicepower.com",        "hint": "Warranty and service network management"},
]

# Full feature key list matching data/competitors.py
FEATURE_KEYS = [
    "scheduling_dispatch", "route_optimization", "customer_self_scheduling", "recurring_jobs",
    "gps_realtime", "gps_reports", "job_costing", "offline_mobile", "photos_docs",
    "digital_signatures", "asset_management", "inventory", "subcontractor_mgmt",
    "invoicing", "estimates", "payments", "pricebook", "commission_mgmt",
    "quickbooks_sync", "customer_financing", "crm", "lead_management",
    "reviews_reputation", "website_builder", "sms_email_automation", "google_business",
    "ai_receptionist", "ai_estimator", "ai_document_scanner", "ai_copilot",
    "ai_text_generation", "job_reports", "time_reports", "gps_mileage_reports",
    "revenue_dashboard",
]

_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
_SKIP_DOMAINS = {"g2.com", "capterra.com", "getapp.com", "trustpilot.com", "linkedin.com",
                 "twitter.com", "facebook.com", "youtube.com", "reddit.com", "softwareadvice.com",
                 "sourceforge.net", "alternativeto.net", "crunchbase.com"}


def get_suggestions(existing_names: list) -> list:
    """Return discovery list filtered to exclude already-tracked competitors."""
    existing_lower = {n.lower() for n in existing_names}
    filtered = [c for c in DISCOVERY_LIST if c["name"].lower() not in existing_lower]

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            already = ", ".join(list(existing_names)[:30])
            prompt = (
                "List 8 US field service management (FSM) or home service software companies "
                f"NOT already in this list: {already}.\n"
                "Include a mix of direct FSM tools and adjacent tools.\n"
                "Return ONLY valid JSON array, no other text:\n"
                '[{"name":"...","type":"direct"|"indirect","url":"https://...","hint":"one sentence"}]'
            )
            resp = client.messages.create(
                model="claude-sonnet-4-6", max_tokens=600,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text.strip()
            if "```" in text:
                text = text.split("```")[1].lstrip("json").strip()
            ai_suggestions = json.loads(text)
            for s in ai_suggestions:
                if s.get("name", "").lower() not in existing_lower:
                    filtered.append(s)
        except Exception:
            pass

    return filtered


def scrape_homepage(url: str) -> dict:
    """Scrape a company homepage for tagline and description."""
    if not url or not url.startswith("http"):
        return {}
    try:
        resp = requests.get(url, timeout=8, headers=_HEADERS)
        soup = BeautifulSoup(resp.text, "html.parser")

        title = soup.find("title")
        title_text = title.get_text(strip=True) if title else ""

        meta = (soup.find("meta", attrs={"name": "description"}) or
                soup.find("meta", attrs={"property": "og:description"}))
        description = meta.get("content", "").strip() if meta else ""

        h1 = soup.find("h1")
        h1_text = h1.get_text(strip=True) if h1 else ""

        # Grab a bit more: subheadings and intro text
        paras = []
        for p in soup.select("p")[:6]:
            t = p.get_text(strip=True)
            if len(t) > 40:
                paras.append(t)

        return {
            "title": title_text,
            "description": description,
            "h1": h1_text,
            "paragraphs": paras[:3],
            "url": url,
        }
    except Exception:
        return {}


def _find_website_url(name: str) -> str:
    """Search DuckDuckGo to find a company's official website."""
    try:
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": f'"{name}" field service software official site'},
            headers=_HEADERS,
            timeout=10,
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.select("a.result__a"):
            href = a.get("href", "")
            if not href:
                continue
            # DDG wraps URLs in redirect links
            if "uddg=" in href:
                parsed = urlparse(href)
                params_map = parse_qs(parsed.query)
                if "uddg" in params_map:
                    url = unquote(params_map["uddg"][0])
                    domain = urlparse(url).netloc.lower().replace("www.", "")
                    if not any(skip in domain for skip in _SKIP_DOMAINS):
                        return url
            elif href.startswith("http"):
                domain = urlparse(href).netloc.lower().replace("www.", "")
                if not any(skip in domain for skip in _SKIP_DOMAINS):
                    return href
    except Exception:
        pass
    return ""


def _scrape_g2(name: str) -> dict:
    """Try to get G2 rating and review count for a company."""
    try:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        url = f"https://www.g2.com/products/{slug}/reviews"
        resp = requests.get(url, headers=_HEADERS, timeout=8)
        if resp.status_code != 200:
            return {}
        soup = BeautifulSoup(resp.text, "html.parser")

        # Rating
        rating = None
        for sel in ['[data-star-rating]', '.fw-semibold.c-midnight-100', 'span[itemprop="ratingValue"]']:
            el = soup.select_one(sel)
            if el:
                txt = el.get_text(strip=True)
                m = re.search(r"(\d+\.\d+)", txt)
                if m:
                    rating = float(m.group(1))
                    break

        # Review count
        reviews = 0
        for sel in ['.x-current-review-count', '[data-total-reviews]']:
            el = soup.select_one(sel)
            if el:
                txt = re.sub(r"[^0-9]", "", el.get_text())
                if txt:
                    reviews = int(txt)
                    break

        return {"rating": rating or "N/A", "reviews": reviews}
    except Exception:
        return {}


def _research_with_scraping(name: str, url: str, comp_type: str, homepage: dict) -> dict:
    """Build a partial competitor profile using only web scraping (no API key)."""
    g2 = _scrape_g2(name)

    description = (
        homepage.get("description")
        or homepage.get("h1")
        or (homepage.get("paragraphs", [""])[0] if homepage.get("paragraphs") else "")
        or f"{name} — field service management software"
    )
    tagline = homepage.get("h1") or homepage.get("title", "").split("|")[0].split("–")[0].strip() or "—"

    threat = "high" if comp_type == "direct" else "low"

    return {
        "url": url,
        "one_liner": description[:200],
        "founded": "—",
        "hq": "—",
        "funding": "—",
        "ownership": "—",
        "est_arr": "—",
        "team_size": "—",
        "threat_level": threat,
        "pricing_model": "per_user",
        "plans": [],
        "free_tier": False,
        "trial": "—",
        "tagline": tagline[:150],
        "g2_rating": g2.get("rating", "N/A"),
        "capterra_rating": "N/A",
        "g2_reviews": g2.get("reviews", 0),
        "capterra_reviews": 0,
        "top_pros": [],
        "top_cons": [],
        "wins_vs_swivl": [],
        "losses_vs_swivl": [],
        "how_to_beat": "Configure an Anthropic API key for full AI-powered battle card analysis.",
        "objection_handling": {},
        "features": {k: "none" for k in FEATURE_KEYS},
        "_custom": True,
        "_partial": True,
    }


def build_full_profile(name: str, url: str = "", comp_type: str = "direct") -> dict:
    """
    Build a complete competitor profile.
    1. Looks up URL from DISCOVERY_LIST if not provided
    2. Falls back to DuckDuckGo search for the URL
    3. Scrapes homepage for real description/tagline
    4. Uses Claude API for full profile if key is configured
    5. Falls back to scraping-only partial profile
    """
    # Step 1: Resolve URL
    if not url:
        for item in DISCOVERY_LIST:
            if item["name"].lower() == name.lower():
                url = item.get("url", "")
                break
    if not url:
        url = _find_website_url(name)

    # Step 2: Scrape homepage
    homepage = scrape_homepage(url) if url else {}
    homepage_ctx = ""
    if homepage:
        homepage_ctx = (
            f"\nHomepage scraped data:"
            f"\n  Title: {homepage.get('title', '')}"
            f"\n  H1: {homepage.get('h1', '')}"
            f"\n  Meta description: {homepage.get('description', '')}"
            f"\n  Key paragraphs: {' | '.join(homepage.get('paragraphs', []))}"
        )

    # Step 3: Try Claude API for full AI research
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            feature_list = ", ".join(FEATURE_KEYS)
            prompt = f"""Research "{name}" (website: {url or 'unknown'}) as a competitor to Swivl.{homepage_ctx}

Swivl: AI-first FSM for home service contractors (1–30 techs). Features: scheduling, GPS, AI receptionist, AI estimator, invoicing, website builder. Pricing: $0–$299/mo flat unlimited users.

Return ONLY valid JSON (no markdown) with this exact structure:
{{
  "url": "{url}",
  "one_liner": "one sentence description",
  "founded": "year or —",
  "hq": "City, State or —",
  "funding": "e.g. $50M raised or Bootstrapped or —",
  "ownership": "VC-backed|PE-backed|Bootstrapped|Public",
  "est_arr": "e.g. ~$30M ARR or —",
  "team_size": "e.g. ~150 or —",
  "threat_level": "high|medium|low",
  "pricing_model": "per_user|flat_unlimited_users|tiered_flat|base_plus_per_user|tiered_enterprise",
  "plans": [
    {{"name": "Starter", "base": 49, "per_user": 0, "included": null, "note": ""}}
  ],
  "free_tier": false,
  "trial": "14-day or —",
  "tagline": "their actual tagline or headline",
  "g2_rating": 4.3,
  "capterra_rating": 4.4,
  "g2_reviews": 120,
  "capterra_reviews": 200,
  "top_pros": ["3-5 actual user-cited pros"],
  "top_cons": ["3-5 actual user-cited cons"],
  "wins_vs_swivl": ["2-3 things they do better than Swivl"],
  "losses_vs_swivl": ["2-3 things Swivl does better than them"],
  "how_to_beat": "Concrete sales tactic paragraph for the Swivl team",
  "objection_handling": {{"common objection": "sharp response"}},
  "features": {{
    {', '.join(f'"{k}": "full|partial|none|addon"' for k in FEATURE_KEYS)}
  }}
}}"""

            resp = client.messages.create(
                model="claude-sonnet-4-6", max_tokens=2500,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text.strip()
            if "```" in text:
                text = text.split("```")[1].lstrip("json").strip()
            profile = json.loads(text)

            for k in FEATURE_KEYS:
                profile.setdefault("features", {})[k] = profile.get("features", {}).get(k, "none")

            profile["_custom"] = True
            profile["display_name"] = name
            return profile

        except Exception:
            pass

    # Step 4: Scraping-only fallback
    return _research_with_scraping(name, url, comp_type, homepage)
