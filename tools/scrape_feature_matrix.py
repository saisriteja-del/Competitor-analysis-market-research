"""
scrape_feature_matrix.py — Hardcoded 25-feature truth table for Swivl vs. 4 competitors.

No live scraping — this is maintained manually as a authoritative source of truth.
Values: true | false | "partial"

Run directly to print the matrix and regenerate .tmp/feature_matrix.json.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scraper_base import save_json

# ── Feature truth table ───────────────────────────────────────────────────────
# Categories and features are ordered strategically:
#   Pricing → Core FSM → Mobile → Field Ops → Catalog → Retention
#   → Customer → Comms → Marketing → Integrations → Fintech → Scale → AI

FEATURES: list[dict] = [
    # Pricing
    {
        "id": 1,
        "feature": "Flat / unlimited-user pricing (Command Center)",
        "category": "Pricing",
        "Swivl": True,
        "Jobber": False,
        "Workiz": False,
        "HouseCallPro": False,
        "swivl_note": "Command Center USP — fixed monthly price regardless of headcount; competitors charge $30–100 per additional tech",
        "description": "Swivl's Command Center is priced flat — one monthly rate unlocks the full platform for your entire team, with no per-seat add-ons. While Jobber, Workiz, and HouseCallPro all charge per technician, Swivl customers can double their field team without touching their software budget.",
        "swivl_usp": True,
    },
    {
        "id": 2,
        "feature": "Free tier or trial available",
        "category": "Pricing",
        "Swivl": "partial",
        "Jobber": "partial",
        "Workiz": True,
        "HouseCallPro": False,
        "swivl_note": "Free trial offered; no permanent free tier",
        "description": "Ability to try the platform at no cost — either a permanent free plan with limited features, or a time-limited full-access trial before committing to a paid plan.",
    },
    # Core FSM
    {
        "id": 3,
        "feature": "Work order management",
        "category": "Core FSM",
        "Swivl": True,
        "Jobber": True,
        "Workiz": True,
        "HouseCallPro": True,
        "swivl_note": "",
        "description": "Digital job tickets capturing every detail: what needs doing, who's assigned, on-site findings, and completion status. Replaces paper forms and verbal handoffs between office and field.",
    },
    {
        "id": 4,
        "feature": "Scheduling & dispatch",
        "category": "Core FSM",
        "Swivl": True,
        "Jobber": True,
        "Workiz": True,
        "HouseCallPro": True,
        "swivl_note": "",
        "description": "Visual calendar showing team availability, location, and job routing. Drag-and-drop booking and technician assignment — the core of any field service operation.",
    },
    {
        "id": 5,
        "feature": "Invoicing & estimates",
        "category": "Core FSM",
        "Swivl": True,
        "Jobber": True,
        "Workiz": True,
        "HouseCallPro": True,
        "swivl_note": "",
        "description": "Create professional quotes in the field, convert to invoices after job completion, and collect payment on-site. Eliminates paper billing, manual follow-up, and delayed cash collection.",
    },
    {
        "id": 6,
        "feature": "Customer CRM",
        "category": "Core FSM",
        "Swivl": True,
        "Jobber": True,
        "Workiz": True,
        "HouseCallPro": True,
        "swivl_note": "",
        "description": "Central database of all clients: contact info, job history, site notes, and communication records. Know exactly who your customer is before the technician knocks on their door.",
    },
    # Mobile
    {
        "id": 7,
        "feature": "Mobile app (iOS + Android)",
        "category": "Mobile",
        "Swivl": True,
        "Jobber": True,
        "Workiz": True,
        "HouseCallPro": True,
        "swivl_note": "",
        "description": "Field technicians work entirely from their phones — view jobs, update status, capture photos, collect signatures, and process payments without returning to the office.",
    },
    {
        "id": 8,
        "feature": "Offline mobile mode",
        "category": "Mobile",
        "Swivl": True,
        "Jobber": True,
        "Workiz": False,
        "HouseCallPro": "partial",
        "swivl_note": "Now available — field workers can operate in basements, rural areas, and low-signal buildings",
        "description": "App continues working in areas without cell coverage — common in basements, rural areas, and commercial buildings. Data syncs automatically when connectivity returns.",
    },
    # Field Ops
    {
        "id": 9,
        "feature": "GPS tracking",
        "category": "Field Ops",
        "Swivl": True,
        "Jobber": True,
        "Workiz": True,
        "HouseCallPro": True,
        "swivl_note": "",
        "description": "Real-time location of all field technicians. Helps dispatch the closest tech to a new job, verify on-site arrival times, and build efficient daily routes.",
    },
    {
        "id": 10,
        "feature": "Time tracking",
        "category": "Field Ops",
        "Swivl": True,
        "Jobber": True,
        "Workiz": True,
        "HouseCallPro": True,
        "swivl_note": "",
        "description": "Logs hours worked per job for accurate labor costing, payroll processing, and customer billing. Technicians clock in and out directly from the field.",
    },
    # Catalog
    {
        "id": 11,
        "feature": "Pricebook / service catalog",
        "category": "Catalog",
        "Swivl": True,
        "Jobber": True,
        "Workiz": True,
        "HouseCallPro": True,
        "swivl_note": "",
        "description": "Pre-built list of services and prices so technicians can add line items quickly and consistently — no looking up rates per call, no pricing variance across your team.",
    },
    {
        "id": 12,
        "feature": "Inventory & materials tracking",
        "category": "Catalog",
        "Swivl": True,
        "Jobber": False,
        "Workiz": False,
        "HouseCallPro": "partial",
        "swivl_note": "Swivl advantage — Jobber + Workiz both lack this",
        "description": "Track parts and materials used on each job. Know what's in your service trucks and warehouse; get low-stock alerts before running out on a job site.",
    },
    # Retention
    {
        "id": 13,
        "feature": "Recurring service agreements",
        "category": "Retention",
        "Swivl": "partial",
        "Jobber": "partial",
        "Workiz": False,
        "HouseCallPro": True,
        "swivl_note": "In progress — currently being developed; will close the gap on predictable recurring revenue",
        "description": "Automatically schedule and bill repeat customers (e.g., HVAC seasonal tune-ups, monthly maintenance). Creates predictable recurring revenue — the closest thing to a subscription model for field service businesses.",
    },
    {
        "id": 14,
        "feature": "Review request automation",
        "category": "Retention",
        "Swivl": True,
        "Jobber": True,
        "Workiz": False,
        "HouseCallPro": True,
        "swivl_note": "",
        "description": "Automatically texts or emails customers asking for a Google or Facebook review after job completion. Critical for local SEO and acquiring new customers through word-of-mouth.",
    },
    # Customer
    {
        "id": 15,
        "feature": "Client self-serve portal",
        "category": "Customer",
        "Swivl": False,
        "Jobber": True,
        "Workiz": True,
        "HouseCallPro": True,
        "swivl_note": "Gap — all 3 direct competitors have this",
        "description": "Customers log in to view job status, approve estimates, pay invoices, and book appointments — without calling your office. Reduces inbound calls and speeds up payment collection.",
    },
    # Comms
    {
        "id": 16,
        "feature": "Two-way SMS / texting",
        "category": "Comms",
        "Swivl": True,
        "Jobber": True,
        "Workiz": True,
        "HouseCallPro": True,
        "swivl_note": "Swivl has SMS module with automated notifications and two-way messaging",
        "description": "Send and receive text messages with customers inside the platform. Field techs communicate professionally without sharing their personal phone numbers.",
    },
    {
        "id": 17,
        "feature": "Built-in VOIP / phone",
        "category": "Comms",
        "Swivl": "partial",
        "Jobber": False,
        "Workiz": True,
        "HouseCallPro": False,
        "swivl_note": "AI Receptionist answers calls and captures leads 24/7 — not full VOIP but covers inbound call automation",
        "description": "Make and receive business calls through the software itself, with call recording, transcripts, and routing — all tied to customer records. Swivl's AI Receptionist answers calls 24/7 and captures leads.",
    },
    # Marketing
    {
        "id": 18,
        "feature": "AI website builder",
        "category": "Marketing",
        "Swivl": True,
        "Jobber": False,
        "Workiz": False,
        "HouseCallPro": False,
        "swivl_note": "Unique Swivl differentiator — no competitor has this",
        "description": "Automatically generates a professional service business website from your business info. No web designer, no monthly agency fees — your online presence is live in minutes.",
    },
    {
        "id": 19,
        "feature": "Ad management suite",
        "category": "Marketing",
        "Swivl": True,
        "Jobber": False,
        "Workiz": False,
        "HouseCallPro": False,
        "swivl_note": "Unique Swivl differentiator",
        "description": "Run and optimize Google and Facebook ads directly from the platform. Tracks which ads lead to booked jobs, so you know your true cost-per-job from paid marketing.",
    },
    # Integrations
    {
        "id": 20,
        "feature": "QuickBooks / accounting sync",
        "category": "Integrations",
        "Swivl": True,
        "Jobber": True,
        "Workiz": True,
        "HouseCallPro": True,
        "swivl_note": "",
        "description": "Two-way sync between the FSM platform and QuickBooks. Invoices, payments, and customer data flow automatically — no double-entry, no end-of-month reconciliation nightmare.",
    },
    {
        "id": 21,
        "feature": "Zapier / automation hub",
        "category": "Integrations",
        "Swivl": False,
        "Jobber": True,
        "Workiz": False,
        "HouseCallPro": False,
        "swivl_note": "Moderate gap",
        "description": "Connect to 5,000+ apps (Slack, Gmail, Salesforce, etc.) without writing code. Trigger custom automations when jobs are created, completed, invoiced, or when customers respond.",
    },
    # Fintech
    {
        "id": 22,
        "feature": "Consumer financing (embedded)",
        "category": "Fintech",
        "Swivl": False,
        "Jobber": False,
        "Workiz": False,
        "HouseCallPro": True,
        "swivl_note": "Only HCP has this — low priority",
        "description": "Offer customers payment plans or buy-now-pay-later directly at the point of invoicing. Increases average ticket size for high-cost jobs like HVAC replacements or roofing.",
    },
    # Scale
    {
        "id": 23,
        "feature": "Multi-location / franchise",
        "category": "Scale",
        "Swivl": False,
        "Jobber": False,
        "Workiz": True,
        "HouseCallPro": "partial",
        "swivl_note": "Tier 2 roadmap item",
        "description": "Manage multiple business locations, regions, or franchise units from a single account — separate reporting per location, shared resources, unified billing.",
    },
    # AI
    {
        "id": 24,
        "feature": "Native AI automation layer",
        "category": "AI",
        "Swivl": True,
        "Jobber": "partial",
        "Workiz": False,
        "HouseCallPro": False,
        "swivl_note": "Swivl unique advantage — no direct competitor has this at SMB price point",
        "description": "AI that acts on behalf of the business: answering calls, drafting estimates, flagging at-risk customers, and recommending follow-ups — without manual intervention from the owner.",
    },
    {
        "id": 25,
        "feature": "Per-user pricing model",
        "category": "Pricing",
        "Swivl": False,
        "Jobber": True,
        "Workiz": True,
        "HouseCallPro": True,
        "swivl_note": "Intentionally absent — Command Center's flat pricing is the direct counter-positioning to all three competitors",
        "description": "Charges a separate monthly fee for each technician added. Costs scale linearly with headcount — a business adding their 10th technician might pay $300–$1,000 more per month depending on the platform. Swivl's Command Center eliminates this entirely with flat-rate pricing.",
        "counter_position": True,
    },
]

COMPANIES = ["Swivl", "Jobber", "Workiz", "HouseCallPro"]


# ── Analysis helpers ───────────────────────────────────────────────────────────

def _is_present(val) -> bool:
    return val is True or val == "partial"


def _competitive_gap(row: dict) -> bool:
    """True when Swivl lacks the feature AND 2+ competitors have it."""
    if _is_present(row["Swivl"]):
        return False
    competitor_count = sum(
        1 for c in COMPANIES[1:] if _is_present(row[c])
    )
    return competitor_count >= 2


def compute_scores() -> dict[str, dict]:
    """Return feature coverage score per company (full + partial)."""
    scores = {}
    for company in COMPANIES:
        full = sum(1 for r in FEATURES if r[company] is True)
        partial = sum(1 for r in FEATURES if r[company] == "partial")
        scores[company] = {
            "full": full,
            "partial": partial,
            "total": full + partial,
            "pct": round((full + 0.5 * partial) / len(FEATURES) * 100, 1),
        }
    return scores


# ── Main builder ──────────────────────────────────────────────────────────────

def build_feature_matrix() -> dict:
    """
    Return the full feature matrix dict and persist to .tmp/feature_matrix.json.
    """
    gaps = [r for r in FEATURES if _competitive_gap(r)]
    swivl_only = [r for r in FEATURES if r["Swivl"] is True and all(
        not _is_present(r[c]) for c in COMPANIES[1:]
    )]

    result = {
        "features": FEATURES,
        "companies": COMPANIES,
        "scores": compute_scores(),
        "competitive_gaps": [r["feature"] for r in gaps],
        "swivl_unique": [r["feature"] for r in swivl_only],
        "total_features": len(FEATURES),
    }
    save_json(result, "feature_matrix.json")
    return result


if __name__ == "__main__":
    data = build_feature_matrix()

    # Pretty print matrix
    scores = data["scores"]
    header = f"{'Feature':<35} {'Swivl':<10} {'Jobber':<10} {'Workiz':<10} {'HCP':<10} {'ST':<10}"
    print(header)
    print("─" * len(header))

    current_cat = ""
    for row in data["features"]:
        if row["category"] != current_cat:
            current_cat = row["category"]
            print(f"\n  [{current_cat}]")

        def fmt(v):
            if v is True:
                return "✓"
            if v is False:
                return "✗"
            return "~"

        gap = " ← GAP" if _competitive_gap(row) else ""
        print(f"  {row['feature']:<33} {fmt(row['Swivl']):<10} {fmt(row['Jobber']):<10} "
              f"{fmt(row['Workiz']):<10} {fmt(row['HouseCallPro']):<10}{gap}")

    print(f"\n{'─'*70}")
    print("Coverage scores:")
    for company, s in scores.items():
        print(f"  {company:<16} {s['total']:>2}/{len(FEATURES)} features  ({s['pct']}%)")

    print(f"\nSwivl competitive gaps ({len(data['competitive_gaps'])}):")
    for g in data["competitive_gaps"]:
        print(f"  ⚠  {g}")

    print(f"\nSwivl-unique features ({len(data['swivl_unique'])}):")
    for u in data["swivl_unique"]:
        print(f"  ★  {u}")
