"""
scrape_indirect_competitors.py — Profiles for indirect competitors to Swivl.

Indirect competitors are tools that serve some of the same customer needs but are
not purpose-built FSM platforms targeting the same segment. They represent:
  1. Alternatives customers consider during the buying process
  2. Tools Swivl customers might be migrating FROM
  3. Adjacent platforms that could expand into Swivl's space

Profiles are hardcoded from public sources — no live scraping needed.
"""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scraper_base import save_json

INDIRECT_COMPETITORS: list[dict] = [
    {
        "name": "FieldPulse",
        "type": "Emerging FSM",
        "tagline": "Modern FSM built for small service businesses",
        "pricing_model": "Flat rate",
        "pricing_est": "Starts ~$99/mo for small teams; scales by features not users",
        "target_market": "1–15 technicians; solo operators and small crews",
        "key_strengths": [
            "Modern, clean UI — frequently praised over Jobber's dated look",
            "Flat-rate pricing model (similar to Swivl) — attractive for growing teams",
            "Strong mobile app with good offline capability",
            "QuickBooks and Stripe integrations",
            "Lower price point than Jobber at entry level",
        ],
        "key_weaknesses": [
            "Smaller brand / lower market awareness vs. Jobber or HCP",
            "No AI features or website builder",
            "Limited marketing / ad management tools",
            "Smaller integration ecosystem",
            "No multi-location or franchise support",
        ],
        "why_indirect": "Growing fast in the 1–15 tech segment; overlaps with Swivl's lower end. Flat-rate model makes them the closest pricing analogue to Swivl.",
        "swivl_angle": "Swivl beats FieldPulse on AI features (AI Receptionist, AI Estimate, MAX Ads, Website Builder) and breadth of modules. FieldPulse is a price competitor at the low end.",
        "url": "https://fieldpulse.com",
        "founded": "2015",
        "hq": "Austin, TX",
    },
    {
        "name": "ServiceM8",
        "type": "Niche FSM",
        "tagline": "Job management for trade businesses",
        "pricing_model": "Per-job (unique) + flat monthly base",
        "pricing_est": "$29/mo base + $0.08 per job dispatch (capped tiers available)",
        "target_market": "1–20 technicians; trades-focused (electrical, plumbing, HVAC)",
        "key_strengths": [
            "Unique per-job pricing model — very cost-effective for low-volume businesses",
            "Deep Apple ecosystem integration (iOS-first design)",
            "Strong job forms and checklists for trades compliance",
            "Popular in Australia, UK, Canada — strong international presence",
            "Clean client-facing job card and invoice emails",
        ],
        "key_weaknesses": [
            "iOS-only native app (Android is limited)",
            "Per-job model becomes expensive at higher volumes",
            "US market presence is limited vs. Jobber",
            "No AI features, website builder, or ad management",
            "Limited reporting and business analytics",
        ],
        "why_indirect": "Appeals to trades-focused small businesses. Unique pricing model attracts low-volume operators. Not a direct head-to-head but competes for the same SMB buyer mindshare.",
        "swivl_angle": "Swivl wins on AI, marketing tools, and scalability. ServiceM8's per-job model advantages disappear at higher job volumes — use this in comparisons.",
        "url": "https://servicem8.com",
        "founded": "2010",
        "hq": "Sydney, Australia",
    },
    {
        "name": "mHelpDesk",
        "type": "Established SMB FSM",
        "tagline": "Field service software that handles everything",
        "pricing_model": "Per user",
        "pricing_est": "Starts ~$169/mo for 1 user; contact sales for teams",
        "target_market": "5–50 technicians; established small-to-mid businesses",
        "key_strengths": [
            "Established product with broad feature coverage",
            "Good customer support reputation",
            "Strong QuickBooks integration",
            "Customizable job forms and checklists",
            "Backed by HomeAdvisor (Angi) — distribution advantage",
        ],
        "key_weaknesses": [
            "Outdated UI — frequently cited in reviews as feeling 'legacy'",
            "Per-user pricing compounds at scale",
            "No AI features or marketing tools",
            "Mobile app rated significantly lower than Jobber",
            "HomeAdvisor backing creates conflict of interest concerns for some users",
        ],
        "why_indirect": "Competes in the 5–50 tech range. Long-standing product with loyal but aging customer base — a migration opportunity for Swivl.",
        "swivl_angle": "Swivl's modern AI-native platform and flat pricing are strong migration arguments for mHelpDesk customers frustrated by per-user costs and dated UX.",
        "url": "https://mhelpdesk.com",
        "founded": "2009",
        "hq": "Fairfax, VA",
    },
    {
        "name": "Kickserv",
        "type": "Budget FSM",
        "tagline": "Simple, affordable field service management",
        "pricing_model": "Per user",
        "pricing_est": "Free tier (1 user); paid from $47/mo for small teams",
        "target_market": "1–10 technicians; price-sensitive early-stage businesses",
        "key_strengths": [
            "Free tier available — lowest barrier to entry in the market",
            "Very affordable entry pricing vs. Jobber",
            "Simple, easy to learn for non-technical operators",
            "QuickBooks and Google Calendar integrations",
        ],
        "key_weaknesses": [
            "Very limited feature set compared to Jobber or Swivl",
            "No AI features, GPS tracking, or inventory management",
            "Poor mobile app reviews",
            "Not scalable beyond 10–15 users",
            "Minimal customer support",
        ],
        "why_indirect": "Attracts the most price-sensitive segment. Customers outgrow it quickly — a stepping stone, not a long-term solution. Represents the 'spreadsheet to software' transition buyer.",
        "swivl_angle": "Kickserv users who are growing are natural Swivl prospects. Swivl's flat rate addresses the per-user anxiety as they add their next hire.",
        "url": "https://www.kickserv.com",
        "founded": "2006",
        "hq": "Portland, OR",
    },
    {
        "name": "Zoho FSM",
        "type": "Ecosystem FSM",
        "tagline": "Field service management as part of the Zoho ecosystem",
        "pricing_model": "Per user",
        "pricing_est": "~$30/user/mo (part of Zoho One bundle at $37/user/mo for all apps)",
        "target_market": "10–100 technicians already using Zoho CRM, Books, or Desk",
        "key_strengths": [
            "Deep integration with Zoho CRM, Books, Projects, Desk — one unified ecosystem",
            "Very competitive pricing via Zoho One bundle",
            "Strong reporting and analytics leveraging Zoho Analytics",
            "Reasonable mobile app",
            "Good automation capabilities via Zoho Flow",
        ],
        "key_weaknesses": [
            "Weak brand presence in field service trades market",
            "FSM module is newer — less mature than Jobber or HCP",
            "No AI features specific to field service",
            "No trades-specific templates or vertical focus",
            "Customer support quality varies",
        ],
        "why_indirect": "Attracts businesses already in the Zoho ecosystem. If a business uses Zoho CRM, Zoho FSM is a natural path. Represents the 'ecosystem lock-in' competitor.",
        "swivl_angle": "Swivl wins on field service-specific AI features, flat pricing advantage, and purpose-built FSM depth. Zoho FSM is a generalist — Swivl is a specialist.",
        "url": "https://www.zoho.com/fsm/",
        "founded": "2022 (FSM module)",
        "hq": "Chennai, India / Austin, TX",
    },
    {
        "name": "DIY Stack (QuickBooks + Google Workspace)",
        "type": "No-FSM Alternative",
        "tagline": "Spreadsheets, email, and QuickBooks for job tracking",
        "pricing_model": "Per user (each tool separately)",
        "pricing_est": "QuickBooks $30–$100/mo + Google Workspace $12/user/mo + manual scheduling = $150–$300/mo with significant labor overhead",
        "target_market": "0–5 technicians; earliest-stage businesses not yet ready to invest in FSM software",
        "key_strengths": [
            "Zero learning curve — tools they already know",
            "Flexible — no vendor lock-in",
            "QuickBooks is accounting industry standard",
            "Low upfront cost perception",
        ],
        "key_weaknesses": [
            "Zero automation — every task is manual",
            "No job tracking, dispatch, or GPS",
            "No customer portal or professional invoicing flow",
            "Scales very poorly — collapses at 3+ technicians",
            "No mobile field app for technicians",
            "Total cost of owner time often exceeds FSM software cost",
        ],
        "why_indirect": "The 'status quo' competitor — the biggest category of non-adopters. Many Swivl prospects are currently on this stack. Defeating 'do nothing' is often the real sales motion.",
        "swivl_angle": "Swivl's onboarding and time-to-value story should target this segment explicitly. A clear ROI message ('save 10 hours/week by replacing your spreadsheet') converts these buyers.",
        "url": "N/A",
        "founded": "N/A",
        "hq": "N/A",
    },
]


def build_indirect_competitors() -> dict:
    """Build the indirect competitors dataset and save to .tmp/indirect_competitors.json."""
    result = {
        "competitors": INDIRECT_COMPETITORS,
        "count": len(INDIRECT_COMPETITORS),
        "types": list({c["type"] for c in INDIRECT_COMPETITORS}),
    }
    save_json(result, "indirect_competitors.json")
    return result


if __name__ == "__main__":
    data = build_indirect_competitors()
    for c in data["competitors"]:
        print(f"\n{'─'*60}")
        print(f"{c['name']} [{c['type']}]")
        print(f"  Pricing: {c['pricing_model']} — {c['pricing_est']}")
        print(f"  Target:  {c['target_market']}")
        print(f"  Swivl angle: {c['swivl_angle']}")
