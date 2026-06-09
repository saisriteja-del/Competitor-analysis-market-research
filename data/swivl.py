# Swivl platform data — sourced from internal engineering docs and competitive brief (June 2026)

COMPANY = {
    "name": "Swivl",
    "url": "swivl.tech",
    "founded": "2022–2023",
    "hq": "Atlanta, GA",
    "dev_center": "Bengaluru, India",
    "founder": "Rob Heller",
    "sales_motion": "PLG (Product-Led Growth)",
    "target_segment": "SMB home & field service businesses (1–30 technicians)",
    "signups": "5,000+",
    "active_businesses": "50+",
    "tagline": "All-in-one field service management software with AI — built for the trades.",
    "one_liner": "AI-first FSM platform targeting SMB contractors frustrated with expensive lead marketplaces, manual estimating, and enterprise software complexity.",
}

PRICING = {
    "model": "Credit-based consumption on flat monthly tiers — unlimited users on all plans",
    "unlimited_users": True,
    "no_contract": True,
    "free_tier": True,
    "plans": [
        {"name": "Starter",      "price": 0,   "credits": 250,   "trial": None,     "ai_receptionist": False, "recommended": False},
        {"name": "Growth",       "price": 49,  "credits": 1500,  "trial": "28-day", "ai_receptionist": False, "recommended": False},
        {"name": "Scale Pro",    "price": 149, "credits": 4800,  "trial": "28-day", "ai_receptionist": True,  "recommended": True},
        {"name": "Organization", "price": 299, "credits": 12000, "trial": None,     "ai_receptionist": True,  "recommended": False},
    ],
    "credit_costs": {
        "GPS Tracking":       {"cost": 5,   "unit": "credits/hr/tech"},
        "AI Estimator":       {"cost": 60,  "unit": "credits/estimate"},
        "AI Receptionist":    {"cost": 10,  "unit": "credits/minute"},
        "SMS":                {"cost": 1,   "unit": "credit/SMS"},
        "MAX Ads":            {"cost": 400, "unit": "credits/month"},
        "Instant Quote":      {"cost": 20,  "unit": "credits/quote"},
        "Storage":            {"cost": 10,  "unit": "credits/GB"},
        "Document Scanner":   {"cost": 1,   "unit": "credit/page"},
        "AI Text":            {"cost": 1,   "unit": "credit/page"},
    },
}

POSITIONING = {
    "pillars": [
        {
            "name": "Stop Overpaying for Leads",
            "description": "Anti-marketplace: avoid 20% commission fees to Angi/HomeAdvisor. Use Swivl's website builder and ad tools to capture leads directly.",
        },
        {
            "name": "Price with Precision AI",
            "description": "Eliminate gut-feeling quotes. AI analyzes labor, materials, and overhead to ensure every estimate is profitable.",
        },
        {
            "name": "Scale Without the Chaos",
            "description": "From dispatch to final invoice — automate workflow so teams spend less time on paperwork and more time in the field.",
        },
    ],
    "icp": {
        "primary_buyer": "Owner-operator or office manager of an SMB home service business (1–30 technicians)",
        "verticals": ["Plumbing", "HVAC", "Electrical", "Roofing", "Handyman", "Lawn Care", "Commercial Cleaning", "Solar", "Property Maintenance", "Carpentry", "General Contracting"],
        "pain_points": ["Expensive lead gen fees", "Inaccurate estimates", "Dispatch chaos", "Slow invoicing", "No real-time team visibility"],
        "anti_persona": "Enterprise (50+ techs), industrial/IoT field service, government/facilities",
    },
}

DIFFERENTIATORS = [
    "Only FSM with a FREE AI website builder on every plan",
    "Unlimited users on all plans — no per-seat pricing ever",
    "AI-native core: AI Receptionist, AI Estimator, AI Copilot built in (not add-ons)",
    "Anti-marketplace positioning — unique angle vs. all FSM competitors",
    "Founder built + sold a real plumbing business (authentic credibility)",
    "Credit-based model = usage-based expansion without a sales rep",
    "28-day free trial — 2× longer than Jobber & HousecallPro's 14-day",
    "PLG + high-touch CS hybrid: self-serve signup + human account manager",
    "GPS Rule Engine with natural language rule authoring",
    "AI Walkthrough — voice-guided in-app help unique to the market",
]

STRENGTHS = [
    "AI-native from day one — AI Receptionist, Estimator, Website Builder are core features",
    "Founder authenticity — built and sold a real service business",
    "Unlimited users on all plans — major pricing advantage vs. per-seat competitors",
    "Free AI website builder creates switching costs and lowers acquisition barrier",
    "Permanent free Starter plan reduces trial anxiety",
    "Low price floor ($49/mo) vs. ServiceTitan ($398+) and competitive with Jobber ($49)",
    "GPS Rule Engine: natural language rule authoring — unique in the market",
    "28-day trial — longer than most FSM competitors",
]

WEAKNESSES = [
    "GPS credit metering creates pricing anxiety — heavy GPS users exhaust plans fast",
    "5,000 signups vs. 50 active businesses — activation/conversion gap",
    "No public G2/Capterra reviews yet — limited third-party social proof",
    "Only QuickBooks + Stripe confirmed integrations vs. Jobber's 700+",
    "Credit model complexity — requires mental math for flat-pricing buyers",
    "Small publicly listed team (4 people) — engineering capacity questions",
]

# Feature capability map — status values: "full" | "partial" | "none" | "addon"
FEATURES = {
    "scheduling_dispatch":      "full",
    "route_optimization":       "none",
    "customer_self_scheduling": "full",
    "recurring_jobs":           "full",
    "gps_realtime":             "full",
    "gps_reports":              "full",
    "job_costing":              "full",
    "offline_mobile":           "full",
    "photos_docs":              "full",
    "digital_signatures":       "full",
    "asset_management":         "full",
    "inventory":                "full",
    "subcontractor_mgmt":       "full",
    "invoicing":                "full",
    "estimates":                "full",
    "payments":                 "full",
    "pricebook":                "full",
    "commission_mgmt":          "full",
    "quickbooks_sync":          "full",
    "customer_financing":       "full",
    "crm":                      "full",
    "lead_management":          "full",
    "reviews_reputation":       "full",
    "website_builder":          "full",
    "sms_email_automation":     "full",
    "google_business":          "full",
    "ai_receptionist":          "full",
    "ai_estimator":             "full",
    "ai_document_scanner":      "full",
    "ai_copilot":               "full",
    "ai_text_generation":       "full",
    "job_reports":              "full",
    "time_reports":             "full",
    "gps_mileage_reports":      "full",
    "revenue_dashboard":        "full",
}
