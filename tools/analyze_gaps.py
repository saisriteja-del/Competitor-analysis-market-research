"""
analyze_gaps.py — Strategic gaps & opportunities for Swivl.

Context: Swivl is a 2-year-old early-stage FSM startup targeting SMBs (2–200 people).
Goal: Identify what to build next to close competitive gaps and build a fundable narrative.

Output sections:
  strategic_position    — Where Swivl sits and why the moment is right
  swivl_advantages      — Defensible strengths to double down on
  feature_roadmap       — Prioritized build plan (Tier 1 / 2 / 3)
  gtm_gaps              — Go-to-market gaps to close alongside product
  competitor_weaknesses — Exploitable weaknesses per competitor
  pricing_analysis      — Pricing model comparison and opportunity
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scraper_base import save_json, load_json

# ── Swivl known feature set ────────────────────────────────────────────────────
# Sourced from Swivl help docs (April 2026): https://docs.google.com/spreadsheets/d/1OWi0mj428aanpJjbvSjgFKbQEXzt6Xd0amyMV8QpflU

SWIVL_FEATURES = [
    # ── Account & Setup ───────────────────────────────────────────────────────
    "Sign Up + Log In — onboarding and account access",
    "Company Profile — business details, branding, service area config",
    "My Profile — individual user preferences and settings",
    "Asset Setup — initial configuration of company assets",
    "Billing & Usage — subscription management and usage tracking",

    # ── Dashboard & Navigation ────────────────────────────────────────────────
    "Dashboard / Command Center — centralized overview of jobs, revenue, and team activity",

    # ── Work Orders & Scheduling ──────────────────────────────────────────────
    "Jobs — create, assign, track, and complete field service jobs",
    "Task Scheduler — schedule tasks across the team calendar",
    "Task — individual task management linked to jobs and technicians",
    "Scheduling & Dispatch — drag-and-drop scheduling with real-time adjustments",
    "Assign Jobs Based on Technician Availability and Proximity",

    # ── CRM & Customer Management ─────────────────────────────────────────────
    "Customers — full CRM with customer history, notes, and communications",
    "Leads — lead capture and pipeline management",
    "Tags and Service Areas — segment customers and define coverage zones",

    # ── Estimating & Invoicing ────────────────────────────────────────────────
    "Estimates — create and send professional estimates to customers",
    "AI Estimate — AI-powered estimate generation from job details",
    "AI Estimator Rules — configure AI estimate logic and pricing rules",
    "Invoices — generate, send, and track invoices with payment status",
    "AI Doc Scanner — scan paper invoices/docs and auto-import into Swivl",

    # ── Finance & Payments ────────────────────────────────────────────────────
    "Finance — track job costs, expenses, payments, and outstanding balances",
    "Sales Commission Report — track and calculate technician commissions",
    "Pricebook — service catalog with items, pricing, and descriptions linked to jobs",

    # ── Subcontractors & Suppliers ────────────────────────────────────────────
    "Subcontractors — manage and assign subcontractor relationships",
    "Suppliers — manage supplier contacts and materials sourcing",

    # ── Fleet, Tools & Equipment ──────────────────────────────────────────────
    "Tools & Equipment Management — add, track, and assign tools to jobs",
    "Vehicle Setup — manage company vehicles and fleet",
    "GPS Tracking — real-time technician and vehicle location tracking",
    "GPS Report — historical GPS logs and route analysis",
    "GPS Rules — automated alerts and rules based on GPS events",

    # ── Time & Reporting ──────────────────────────────────────────────────────
    "Time Report — technician clock-in/out, time tracking per job",
    "Jobs Report — comprehensive job performance and revenue reporting",
    "Reporting & Analytics — custom reports on revenue, productivity, trends",

    # ── Communications ────────────────────────────────────────────────────────
    "SMS — two-way SMS messaging and automated notifications to customers",
    "Email — automated and manual email communications with customers",
    "AI Receptionist — AI-powered phone answering that captures leads and books jobs 24/7",
    "AI Receptionist Rules — configure AI receptionist behavior and call routing",

    # ── Marketing & Growth ────────────────────────────────────────────────────
    "Website Builder — AI-powered website creation for service businesses",
    "MAX Ads — integrated ad management suite (Google, Facebook campaigns)",
    "Reviews & Ratings — automated review requests and reputation management",

    # ── Users & Access ────────────────────────────────────────────────────────
    "Users & Roles — team member management with role-based permissions",

    # ── AI & Automation ───────────────────────────────────────────────────────
    "Swivl MAX — AI automation layer with rules engine and workflow triggers",
    "Knowledge Base — training and internal documentation hub",

    # ── Integrations ──────────────────────────────────────────────────────────
    "Integrations — QuickBooks Online (bi-directional), Stripe payments, and more",

    # ── Pricing Model ─────────────────────────────────────────────────────────
    "Flat monthly rate — unlimited users on all plans (Starter FREE · Growth $49/mo · Scale Pro $149/mo · Organization $299/mo) · credit-based AI features",
]

COMPETITOR_PROFILES = {
    "Jobber": {
        "strengths": [
            "Strong brand recognition — dominant in SMB home services",
            "50+ third-party integrations (Zapier, QuickBooks, Google, Mailchimp, etc.)",
            "Polished mobile app with offline mode",
            "Client Hub — self-serve customer portal for quotes, bookings, invoices",
            "Two-way texting on all plans",
            "Automated review requests after job completion",
            "Largest review presence on G2 and Capterra (1,000+ reviews each)",
        ],
        "pricing_model": "Per user / technician",
        "known_weaknesses": [
            "Costs scale painfully — 15 techs on Grow = $3,735/mo vs. Swivl flat rate",
            "No built-in marketing or ad management",
            "No AI automation — Copilot is bolt-on, not native",
            "No website builder",
        ],
    },
    "Workiz": {
        "strengths": [
            "Built-in VOIP phone system — call tracking, recording, lead capture from calls",
            "Strong online booking widget",
            "Franchise & multi-location management",
            "Two-way SMS",
            "Affordable at small team sizes",
        ],
        "pricing_model": "Per user / technician",
        "known_weaknesses": [
            "Weaker reporting vs. Jobber and HouseCallPro",
            "No marketing or ad suite",
            "No AI layer",
            "Smaller integration ecosystem",
            "No publicly available pricing — creates trust friction for buyers",
        ],
    },
    "HouseCallPro": {
        "strengths": [
            "Large active community (HCP Community) — high switching cost via peer network",
            "Recurring service agreements — drives predictable revenue for customers",
            "Consumer financing (Wisetack partnership) — increases average job value",
            "Google + Yelp review automation",
            "Flat-rate pricebook with real-time updates",
        ],
        "pricing_model": "Per user / technician",
        "known_weaknesses": [
            "Expensive at scale — Pro plan requires per-user add-ons",
            "Customer support flagged in G2 reviews",
            "No AI automation or website builder",
            "No ad management suite",
        ],
    },
}


# ── Core analysis functions ────────────────────────────────────────────────────

def _strategic_position() -> dict:
    return {
        "summary": (
            "Swivl occupies the most attractive whitespace in field service management: "
            "the 10–100 person service business that has outgrown simple tools but is "
            "priced out of ServiceTitan. Jobber and HouseCallPro own the 1–10 person market "
            "but their per-user pricing becomes a growth tax at scale. "
            "The FSM SaaS category "
            "category is fundable and large. Swivl's timing is right: AI is table stakes, "
            "and Swivl is the only FSM platform built AI-native from day one."
        ),
        "target_wedge": "Teams of 10–50 people who are paying $2,000–$5,000/mo on Jobber and looking for relief",
        "market_signal": "ServiceTitan IPO at ~$685M ARR validates FSM SaaS at scale. Jobber raised $370M at ~$100M ARR. The category is proven.",
        "swivl_angle": (
            "Three structural advantages that compound over time: "
            "(1) Flat unlimited-user pricing — the only FSM platform that gets cheaper per seat as you grow; "
            "(2) AI-native architecture — website builder, ad management, and automation are core, not add-ons; "
            "(3) Operator-built — the founding story is a proof of concept, not a pitch."
        ),
    }


def _feature_roadmap() -> dict:
    """
    Three-tier feature roadmap prioritized by fundraising impact and effort.
    Tier 1 = build before the raise (close objection gaps).
    Tier 2 = build during / right after raise (Series A demo features).
    Tier 3 = post-raise vision (moat builders).
    """
    return {
        "tier_1": {
            "label": "Tier 1 — Build Before the Raise (Close Table-Stakes Gaps)",
            "rationale": (
                "These are features every serious buyer asks about in a demo. "
                "Missing them creates objection points that kill deals and hurt "
                "the 'feature parity' story with investors. Low-to-medium effort, "
                "high signal."
            ),
            "items": [
                {
                    "feature": "Client Self-Serve Portal",
                    "why": (
                        "Jobber's Client Hub is their #1 demo moment — customers can view quotes, "
                        "approve jobs, and pay invoices without calling the office. "
                        "Every mid-size buyer will ask if Swivl has this. "
                        "Also drives NPS and reduces admin overhead for customers."
                    ),
                    "competitor_gap": "Jobber, Workiz, and HouseCallPro all have versions of this",
                    "strategic_impact": "Closes the single most common Jobber comparison objection",
                    "build_suggestion": "Customer-facing branded portal: view/approve estimates, pay invoices, request bookings, track job status",
                },
                {
                    "feature": "Recurring Service Agreements",
                    "why": (
                        "HouseCallPro's stickiest feature. Enables customers to sell "
                        "annual maintenance contracts (e.g. HVAC tune-up 2x/year). "
                        "Creates predictable revenue for both the service business and Swivl's retention. "
                        "VCs love recurring revenue within recurring revenue."
                    ),
                    "competitor_gap": "HouseCallPro's strongest retention mechanic — it locks in customers for years",
                    "strategic_impact": "Improves Swivl's own NRR story; shows you understand the SMB operator's cash flow",
                    "build_suggestion": "Agreement templates with auto-scheduling, auto-invoicing, and renewal reminders",
                },
                {
                    "feature": "SMS & Email Automation Templates",
                    "why": (
                        "Swivl has two-way SMS — the next step is making it a retention engine. "
                        "Automated sequences for job reminders, follow-ups, seasonal re-engagement, "
                        "and review requests are what Jobber and HouseCallPro charge premium tier prices for. "
                        "Swivl should make these configurable workflows, not one-off messages."
                    ),
                    "competitor_gap": "HouseCallPro charges for their 'Marketing' automation tier; Jobber locks it behind Connect/Grow",
                    "strategic_impact": "Turns Swivl's existing SMS feature into a retention moat; directly improves NRR",
                    "build_suggestion": "Visual workflow builder for SMS/email sequences triggered by job status, invoice age, or inactivity. Start with 5 pre-built templates (job confirmation, ETA alert, invoice reminder, review request, win-back).",
                },
                {
                    "feature": "Integration Marketplace Expansion",
                    "why": (
                        "Jobber has 50+ integrations and buyers start every evaluation with "
                        "'does it connect to X?' QuickBooks and Stripe are a start — "
                        "but Zapier/Make, Google Calendar, Mailchimp, and CompanyCam are "
                        "expected. Each integration is also a distribution channel."
                    ),
                    "competitor_gap": "Jobber has 50+ native integrations; Swivl has 2",
                    "strategic_impact": "Shows ecosystem thinking; each partner is a co-marketing channel",
                    "build_suggestion": "Prioritize: Zapier (unlocks 5,000+ apps), Google Calendar, CompanyCam (job photos), Mailchimp. Use OAuth-based webhooks.",
                },
            ],
        },
        "tier_2": {
            "label": "Tier 2 — Build During the Raise (Series A Demo Features)",
            "rationale": (
                "These are the features that make investors say 'this is different.' "
                "They either unlock new revenue streams, new customer segments, or create "
                "switching costs that justify a premium valuation multiple."
            ),
            "items": [
                {
                    "feature": "Customer Financing (Embedded Lending)",
                    "why": (
                        "HouseCallPro partnered with Wisetack to let customers finance jobs on the spot. "
                        "A $4,000 HVAC repair becomes a $180/mo payment — conversion rates jump dramatically. "
                        "This also increases Swivl's GMV flowing through the platform, "
                        "which is a key SaaS-fintech metric VCs love."
                    ),
                    "competitor_gap": "HouseCallPro has it; Jobber does not — clear opening",
                    "strategic_impact": "Unlocks a take-rate revenue stream on top of SaaS subscription — improves unit economics story dramatically",
                    "build_suggestion": "Partner with Wisetack, Greensky, or Acorn Finance. Embed 'offer financing' button in estimate/invoice flow.",
                },
                {
                    "feature": "Offline-First Mobile App",
                    "why": (
                        "Field techs work in basements, rural areas, and commercial buildings with no signal. "
                        "Jobber markets offline mode aggressively — it's a top reason buyers choose them. "
                        "Without offline, Swivl is unusable in many real job scenarios."
                    ),
                    "competitor_gap": "Jobber has offline mode; it's a top feature in their reviews",
                    "strategic_impact": "Required for credibility in the field; shows you understand the actual job site",
                    "build_suggestion": "Service worker + local SQLite sync. Jobs, checklists, and photos work offline; sync on reconnect.",
                },
                {
                    "feature": "Built-In VOIP / Phone System",
                    "why": (
                        "Workiz built their entire growth story around VOIP — every inbound call is a lead, "
                        "tracked, recorded, and attached to a customer record. "
                        "For service businesses, the phone is the #1 lead source. "
                        "A platform that answers calls and auto-creates jobs is a massive workflow win."
                    ),
                    "competitor_gap": "Workiz's core differentiator — their whole brand is built around it",
                    "strategic_impact": "Turns Swivl into the system of record for every inbound lead, not just booked jobs — dramatically expands platform value",
                    "build_suggestion": "Twilio Voice + call recording + auto-transcription. Map calls to customer records. Add 'missed call = new lead' automation.",
                },
                {
                    "feature": "Multi-Location / Franchise Mode",
                    "why": (
                        "A single franchise owner with 5 locations is worth 5x a solo operator — same sales motion, "
                        "5x ACV. Workiz and ServiceTitan both target franchises. "
                        "Swivl's flat pricing model is actually more franchise-friendly than any competitor "
                        "(pay per location, not per tech across all locations)."
                    ),
                    "competitor_gap": "Workiz has this; HouseCallPro is limited",
                    "strategic_impact": "Opens enterprise expansion path; dramatically increases ACV and LTV",
                    "build_suggestion": "Parent/child account hierarchy. Consolidated reporting across locations. Location-specific branding and pricebooks.",
                },
            ],
        },
        "tier_3": {
            "label": "Tier 3 — Post-Raise Vision (Moat Builders)",
            "rationale": (
                "These are the features that create defensibility and justify a premium multiple. "
                "Not needed for the raise — but having a credible vision here is what separates "
                "a seed deck from a Series A deck."
            ),
            "items": [
                {
                    "feature": "Swivl Intelligence — AI Dispatch & Job Optimization",
                    "why": "ServiceTitan's Titan Intelligence is their enterprise moat. Swivl can build a lighter, SMB-friendly version using the job data it accumulates across 40+ verticals.",
                    "strategic_impact": "Data network effect — the more jobs on Swivl, the smarter routing and pricing suggestions get",
                    "build_suggestion": "Start with route optimization (Google Maps API), then layer in job duration predictions from historical data.",
                },
                {
                    "feature": "Community / Pro Network",
                    "why": "HouseCallPro's community is their biggest churn reducer. Pros help each other, which means they stay. A community also generates organic content and referrals.",
                    "strategic_impact": "Network effect moat — stickiness that no feature can replicate",
                    "build_suggestion": "Start with a Slack or Circle community. Graduate to in-app forums tied to verticals (HVAC pros, plumbers, etc.).",
                },
                {
                    "feature": "Embedded Insurance & Financial Products",
                    "why": "Service businesses are chronically underinsured and underbanked. A platform with job + revenue data is positioned to offer GL insurance, workers comp, and revenue-based financing at better rates than brokers.",
                    "strategic_impact": "Fintech multiple on top of SaaS multiple — transforms Swivl into an infrastructure company",
                    "build_suggestion": "Partner with Next Insurance, Pie Insurance, or Embroker. Revenue-based advance via Capchase/Pipe pattern.",
                },
                {
                    "feature": "Vertical Benchmarking & Industry Data",
                    "why": "Swivl sits across 40+ service verticals. Aggregated, anonymized job data (avg ticket by zip code, seasonal demand curves) is enormously valuable to operators — and could become a standalone product.",
                    "strategic_impact": "Data product creates a second revenue stream and a proprietary moat no competitor can copy",
                    "build_suggestion": "Start with in-app insights ('Your average HVAC ticket is 12% above the regional median'). Graduate to a paid benchmarking report.",
                },
            ],
        },
    }


def _gtm_gaps() -> list[dict]:
    return [
        {
            "gap": "G2 & Capterra Review Volume",
            "detail": (
                "Jobber has 1,000+ reviews on both platforms — that review density wins the SEO battle "
                "for 'best field service software' searches. Swivl is invisible in these results. "
                "This is a top-of-funnel GTM gap that no product improvement fixes."
            ),
            "action": "Launch a structured review campaign: email every active customer post-job, offer a 1-month credit for a verified G2 review. Target 100 reviews in 90 days.",
        },
        {
            "gap": "YouTube & SEO Content",
            "detail": (
                "Jobber dominates YouTube with 'how to run a service business' tutorials. "
                "Their content ranks for terms their ICP searches before they even look for software. "
                "This is the cheapest long-term CAC reduction available."
            ),
            "action": "Produce 2 videos/week targeting 'how to [run/grow/manage] a [plumbing/HVAC/cleaning] business'. Feature real Swivl customers as the protagonists.",
        },
        {
            "gap": "Pricing Page Transparency",
            "detail": (
                "Swivl's pricing should be prominently published and include a cost comparison calculator. "
                "Buyers who find a clear 'at 15 techs you save $2,800/mo vs. Jobber' table will self-qualify. "
                "This is the single highest-leverage conversion page on the website."
            ),
            "action": "Build a pricing page with an interactive cost comparison: 'Enter your team size → see your Jobber bill vs. Swivl bill'.",
        },
        {
            "gap": "Partner / Referral Channel",
            "detail": (
                "Home service supply chains are untapped. HVAC distributors, plumbing supply houses, and "
                "trade associations have direct relationships with exactly Swivl's ICP. "
                "Jobber has started building this; it's not too late for Swivl."
            ),
            "action": "Identify 5 regional trade distributors or associations. Offer a white-labeled or co-branded referral program with rev-share.",
        },
    ]


def _icp_profiles() -> dict:
    """
    Ideal Customer Profile for each competitor + Swivl's sweet spot.
    Used to sharpen sales targeting and investor positioning.
    """
    return {
        "Jobber": {
            "company_size": "1–15 technicians",
            "annual_revenue": "$100K–$2M/year",
            "industries": ["Lawn care", "Cleaning", "Landscaping", "Pool service", "Pest control", "Window washing"],
            "buyer_persona": "Owner-operator, often running solo or with a small crew",
            "primary_pain": "Looks unprofessional on paper invoices; getting paid late; scheduling chaos",
            "buying_trigger": "Just hired first employee, or tired of texting job details manually",
            "price_sensitivity": "High — will churn over a $50/mo price increase; cost is the #1 objection",
            "decision_maker": "Owner (sole decision-maker)",
            "avg_acv_est": "~$1,800–$3,600/yr",
            "swivl_opportunity": "Customers who have grown past 10 techs face bill shock — Jobber's pricing model becomes a growth tax. These are Swivl's highest-intent prospects.",
        },
        "Workiz": {
            "company_size": "1–10 technicians",
            "annual_revenue": "$50K–$500K/year",
            "industries": ["Locksmith", "Appliance repair", "Garage door", "Junk removal", "Carpet cleaning"],
            "buyer_persona": "Owner who relies heavily on inbound phone calls for new jobs",
            "primary_pain": "Missing calls = missing revenue; needs phone, SMS, and dispatch unified in one tool",
            "buying_trigger": "Growing call volume, too many missed leads going to voicemail",
            "price_sensitivity": "Medium — will pay more if VOIP saves them a separate phone system cost",
            "decision_maker": "Owner",
            "avg_acv_est": "~$1,200–$2,700/yr",
            "swivl_opportunity": "Workiz's UI is dated and mobile app is weak. Customers who have outgrown the basic tool and need stronger reporting and AI automation are a natural fit for Swivl.",
        },
        "HouseCallPro": {
            "company_size": "2–30 technicians",
            "annual_revenue": "$200K–$5M/year",
            "industries": ["HVAC", "Plumbing", "Electrical", "General home services", "Roofing"],
            "buyer_persona": "Owner or operations manager who wants to move from reactive to recurring service model",
            "primary_pain": "Needs recurring maintenance agreements to create predictable revenue; wants community and peer benchmarking",
            "buying_trigger": "Expanding service area, adding a second crew, or wanting to offer annual maintenance contracts",
            "price_sensitivity": "Medium — will pay premium if ROI is clearly demonstrated (especially via financing + review automation)",
            "decision_maker": "Owner or Operations Manager",
            "avg_acv_est": "~$3,600–$12,000/yr",
            "swivl_opportunity": "HCP's per-user cost spikes hard at 15–25 techs. Growing HCP customers are the second-highest-intent Swivl prospect after Jobber churners.",
        },
        "Swivl": {
            "company_size": "10–100 technicians",
            "annual_revenue": "$500K–$10M/year",
            "industries": ["Any field service vertical — 40+ trades covered"],
            "buyer_persona": "Owner or ops lead who is paying too much on Jobber as their team grows, or who needs AI-native tools Jobber doesn't offer",
            "primary_pain": "Per-user pricing is becoming a growth tax; competitors don't offer marketing tools (website + ads) alongside FSM",
            "buying_trigger": "Jobber bill exceeds $2,000/mo (typically around 12–15 techs), or owner is looking for an integrated website + FSM solution",
            "price_sensitivity": "Low on flat-rate value — the savings at 15+ techs are self-evident",
            "decision_maker": "Owner (1–30 tech range) or COO/Operations Manager (30–100 tech range)",
            "avg_acv_est": "~$588–$3,588/yr (Growth $49/mo to Organization $299/mo)",
            "swivl_opportunity": "N/A — this is the target. Free Starter tier creates a self-serve PLG motion. Focus paid conversion on Jobber churners at 10–50 techs and SMBs who want a unified growth + ops platform.",
        },
    }


def _market_sizing() -> dict:
    """
    TAM / SAM / SOM analysis for Swivl's fundraising narrative.
    Sources are cited inline. All figures in USD.
    """
    return {
        "tam": {
            "label": "Total Addressable Market (TAM)",
            "value": "$5.2B",
            "description": (
                "Global field service management software market in 2024. "
                "Growing at ~12% CAGR to an estimated $8.2B by 2028 as AI and mobile "
                "drive digital adoption across trades."
            ),
            "sources": [
                "MarketsandMarkets: Field Service Management Market Report 2024",
                "Grand View Research: FSM Software Global Market 2024–2030",
                "ServiceTitan S-1 (Dec 2024): references $25B+ total addressable market including adjacent services spend",
            ],
            "key_facts": [
                "ServiceTitan IPO at $685M ARR (Dec 2024) validates FSM SaaS as a large, fundable category",
                "Jobber raised $370M and serves ~250,000 service professionals — still less than 20% of the US market",
                "FSM is recession-resistant: field service (HVAC, plumbing, electrical) is non-discretionary",
                "Blue-collar workforce growing faster than white-collar — 6.5% YoY vs. 2.1% for knowledge workers (BLS 2024)",
            ],
        },
        "sam": {
            "label": "Serviceable Addressable Market (SAM)",
            "value": "$2.1B",
            "description": (
                "US-only field service businesses with 2–200 employees that are software-ready "
                "and English-speaking. Excludes enterprise (200+ employees, better served by ServiceTitan) "
                "and solo operators (1 person, lower ARPU and higher churn)."
            ),
            "sources": [
                "US Census Bureau: ~1.3M field service establishments in the US (NAICS codes 2381–2389, 5617, 8111)",
                "Jobber internal estimate (from investor materials): ~500,000 SMB field service businesses with 2–50 employees",
                "Average FSM software spend per SMB: ~$3,000–$6,000/yr (blended from G2 pricing data)",
            ],
            "key_facts": [
                "~500,000 US field service SMBs with 2–50 employees — the core software-buying segment",
                "Only ~15–20% currently use dedicated FSM software; the rest use spreadsheets, QuickBooks, or generic tools",
                "Software adoption is accelerating post-COVID as customer expectations for digital scheduling rise",
            ],
        },
        "som": {
            "label": "Serviceable Obtainable Market (SOM) — 5-Year Target",
            "value": "$20M ARR",
            "description": (
                "Realistic 5-year capture for Swivl focused on the 10–100 technician segment "
                "in the US. This is Swivl's highest-intent wedge — businesses too large for "
                "Jobber's economics and too small for ServiceTitan's complexity."
            ),
            "sources": [
                "Internal estimate: ~85,000 US field service businesses with 10–100 employees",
                "Swivl target ACV: $4,800/yr (Growth plan $299/mo × 12, blended with Scale Pro)",
                "5-year capture assumption: 0.5% of SAM = ~2,500 logos at target ACV",
            ],
            "key_facts": [
                "~85,000 target businesses in the 10–100 technician range in the US",
                "2,500 logos × $4,800 ACV = ~$12M ARR (conservative, no upsell)",
                "With NRR of 110%+ from expansion: same 2,500 logos → ~$20M ARR by year 5",
                "Swivl needs <0.5% market share of its TAM to reach Series A metrics ($3–5M ARR)",
                "Free Starter plan creates a PLG motion — lower CAC and broader top-of-funnel than any direct competitor",
            ],
            "swivl_wedge": (
                "The 10–50 technician segment is the most underserved in FSM. "
                "Jobber's pricing becomes punitive ($2,000–$5,000/mo) at this scale. "
                "ServiceTitan's minimum contract is 6-figures and takes months to implement. "
                "Swivl is the only flat-rate, AI-native FSM platform built specifically for this gap."
            ),
        },
        "competitive_benchmarks": [
            {
                "company": "ServiceTitan",
                "arr": "$685M",
                "customers": "~11,000",
                "implied_acv": "~$62,000",
                "note": "Public (TTAN, Dec 2024 IPO). Validates category at scale.",
            },
            {
                "company": "Jobber",
                "arr": "~$100–150M (est.)",
                "customers": "~250,000 service professionals",
                "implied_acv": "~$500 (many solo operators dilute ACV)",
                "note": "Private. Raised $370M total. Dominant in 1–10 tech segment.",
            },
            {
                "company": "HouseCallPro",
                "arr": "~$50–80M (est.)",
                "customers": "~40,000+",
                "implied_acv": "~$1,500",
                "note": "Private. Raised $65M. Strong in HVAC/plumbing residential.",
            },
            {
                "company": "Swivl Target",
                "arr": "$3–5M (Series A threshold)",
                "customers": "~700–1,000 logos",
                "implied_acv": "~$4,800",
                "note": "Needs 3× YoY growth and NRR >110% to be Series A-ready.",
            },
        ],
    }


def _rag_roadmap() -> list[dict]:
    """
    RAG (Red / Amber / Green) status table for the feature roadmap.
    Red   = Swivl missing the feature AND 2+ competitors have it (critical gap)
    Amber = Swivl has partial support OR only 1 competitor has it (watch list)
    Green = Swivl has the feature (strength to maintain)

    This list focuses on competitively significant features only (not table stakes
    that everyone has).
    """
    return [
        # ── Red: Critical gaps ────────────────────────────────────────────────
        {
            "feature": "Client Self-Serve Portal",
            "status": "red",
            "tier": "Tier 1",
            "priority": "Critical",
            "competitors_with_it": "Jobber, Workiz, HouseCallPro",
            "strategic_impact": "Closes top Jobber comparison objection; reduces admin load for customers",
        },
        {
            "feature": "Two-Way SMS / Texting",
            "status": "green",
            "tier": "Strength",
            "priority": "Maintain",
            "competitors_with_it": "Jobber, Workiz, HouseCallPro",
            "strategic_impact": "Swivl has this — ensure it's prominently demoed; feature parity achieved",
        },
        {
            "feature": "Recurring Service Agreements",
            "status": "red",
            "tier": "Tier 1",
            "priority": "Critical",
            "competitors_with_it": "HouseCallPro",
            "strategic_impact": "Unlocks predictable contract revenue for SMB operators; improves Swivl NRR",
        },
        {
            "feature": "Offline Mobile Mode",
            "status": "red",
            "tier": "Tier 2",
            "priority": "High",
            "competitors_with_it": "Jobber",
            "strategic_impact": "Required for rural/commercial field work credibility",
        },
        {
            "feature": "Zapier / Automation Hub",
            "status": "red",
            "tier": "Tier 1",
            "priority": "High",
            "competitors_with_it": "Jobber",
            "strategic_impact": "Opens 5,000+ integration connections; each partner is a distribution channel",
        },
        # ── Amber: Partial / watch list ───────────────────────────────────────
        {
            "feature": "Consumer Financing (Embedded)",
            "status": "amber",
            "tier": "Tier 2",
            "priority": "Medium",
            "competitors_with_it": "HouseCallPro (Wisetack)",
            "strategic_impact": "Unlocks take-rate revenue stream; improves average job value for customers",
        },
        {
            "feature": "Built-In VOIP / Phone",
            "status": "amber",
            "tier": "Tier 2",
            "priority": "Medium",
            "competitors_with_it": "Workiz",
            "strategic_impact": "AI Receptionist covers inbound lead capture — expand to full VOIP for call recording and routing",
        },
        {
            "feature": "Multi-Location / Franchise Mode",
            "status": "amber",
            "tier": "Tier 2",
            "priority": "Medium",
            "competitors_with_it": "Workiz",
            "strategic_impact": "5× ACV per franchise owner; opens enterprise segment",
        },
        {
            "feature": "Free Tier / Trial",
            "status": "amber",
            "tier": "Tier 1",
            "priority": "Medium",
            "competitors_with_it": "Workiz (free tier), Jobber (trial)",
            "strategic_impact": "Improves top-of-funnel conversion for self-serve SMB buyers",
        },
        # ── Green: Swivl strengths ────────────────────────────────────────────
        {
            "feature": "Flat / Unlimited-User Pricing",
            "status": "green",
            "tier": "Strength",
            "priority": "Maintain",
            "competitors_with_it": "None",
            "strategic_impact": "Core positioning — no competitor can copy without breaking their revenue model",
        },
        {
            "feature": "AI Website Builder",
            "status": "green",
            "tier": "Strength",
            "priority": "Maintain",
            "competitors_with_it": "None",
            "strategic_impact": "Unique differentiator — generates customer leads before they even need FSM",
        },
        {
            "feature": "Ad Management Suite",
            "status": "green",
            "tier": "Strength",
            "priority": "Maintain",
            "competitors_with_it": "None",
            "strategic_impact": "Expands Swivl's value proposition beyond operations into growth",
        },
        {
            "feature": "Native AI Automation Layer",
            "status": "green",
            "tier": "Strength",
            "priority": "Expand",
            "competitors_with_it": "ServiceTitan (partial)",
            "strategic_impact": "AI-native architecture is the long-term moat; expand automations each sprint",
        },
        {
            "feature": "Inventory & Materials Tracking",
            "status": "green",
            "tier": "Strength",
            "priority": "Maintain",
            "competitors_with_it": "ServiceTitan",
            "strategic_impact": "Advantage over Jobber + Workiz; highlight in demos for trade businesses",
        },
    ]


# ── Main ────────────────────────────────────────────────────────────────────────

def analyze_gaps(all_data: dict) -> dict:
    pricing_data = all_data.get("pricing", {})

    # Core advantages — sourced from Swivl help docs (April 2026)
    swivl_advantages = [
        "Free forever Starter plan — the only FSM platform with a true free tier (no credit card required)",
        "Flat unlimited-user pricing — Growth $49/mo and Scale Pro $149/mo are 10–20× cheaper than Jobber at equivalent team sizes",
        "AI-native architecture — AI Receptionist, AI Estimate, AI Doc Scanner, and MAX Ads are core features, not add-ons",
        "Operator-built credibility — founding story is a proof of concept (25% YoY, 30-truck fleet, exited)",
        "Broadest industry coverage (40+ verticals) vs. most competitors who focus on 3–5 trades",
        "Swivl MAX rules engine — workflow automation at base tiers, not locked behind enterprise plans",
        "Reviews & ratings management with website sync — competitors charge for this or don't offer it",
        "Built-in Website Builder + MAX Ads — Swivl is the only FSM platform that also grows your customer base",
        "Subcontractors + Suppliers modules — full supply-chain visibility, not just technician scheduling",
        "AI Doc Scanner — scan paper quotes/invoices to digitize instantly; no competitor has this",
        "Sales Commission Reporting — field-ready financial tracking built in at all tiers",
    ]

    # Pricing analysis — verified June 2026 from swivl.tech/pricing
    pricing_analysis = (
        "Swivl's flat unlimited-user pricing is its single most powerful commercial differentiator. "
        "Swivl starts FREE (Starter plan, 250 credits/mo) — the only FSM platform with a free tier. "
        "Growth at $49/mo and Scale Pro at $149/mo are dramatically cheaper than any competitor at equivalent team sizes. "
        "At 15 technicians, a Jobber Grow customer pays ~$3,735/mo vs. Swivl Scale Pro at $149 flat — "
        "a $42,000+ annual difference. "
        "Every per-user competitor (Jobber, Workiz, HouseCallPro) becomes less competitive as a team grows — "
        "Swivl's pricing model is anti-churn by design. "
        "The credit system (SMS, GPS, AI Receptionist, AI Estimator) lets Swivl monetize usage without punishing headcount growth, "
        "which is structurally unique in the FSM category."
    )

    result = {
        "strategic_position": _strategic_position(),
        "swivl_advantages": swivl_advantages,
        "feature_roadmap": _feature_roadmap(),
        "gtm_gaps": _gtm_gaps(),
        "pricing_analysis": pricing_analysis,
        "competitor_weaknesses": {
            name: profile["known_weaknesses"]
            for name, profile in COMPETITOR_PROFILES.items()
        },
        "competitor_strengths": {
            name: profile["strengths"]
            for name, profile in COMPETITOR_PROFILES.items()
        },
        "rag_roadmap": _rag_roadmap(),
        "icp_profiles": _icp_profiles(),
        "market_sizing": _market_sizing(),
    }

    save_json(result, "gaps_data.json")
    return result


if __name__ == "__main__":
    cached = {
        "pricing": load_json("pricing_data.json") or {},
        "features": load_json("features_data.json") or {},
        "revenue": load_json("revenue_data.json") or {},
    }
    result = analyze_gaps(cached)

    pos = result["strategic_position"]
    print(f"\nSTRATEGIC POSITION\n{pos['summary']}\n")

    roadmap = result["feature_roadmap"]
    for tier_key in ["tier_1", "tier_2", "tier_3"]:
        tier = roadmap[tier_key]
        print(f"\n{tier['label']}")
        for item in tier["items"]:
            print(f"  ► {item['feature']}")
            print(f"    Why: {item['why'][:120]}...")

    pos2 = result["strategic_position"]
    print(f"\nSTRATEGIC ANGLE\n{pos2['swivl_angle']}")
    print(f"\nPRICING ANALYSIS\n{result['pricing_analysis']}")
