"""Swivl Competitor Analysis Dashboard — 6-tab Streamlit app."""

import os
import json
from pathlib import Path
from datetime import datetime
import streamlit as st
import pandas as pd
import altair as alt

# Load .env for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Competitor Analysis",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Inline CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
  [data-testid="stSidebar"]          { display: none !important; }
  [data-testid="collapsedControl"]   { display: none !important; }
  .block-container { padding-top: 1.5rem !important; }

  .kpi-card {
    background: #fff;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 1.1rem 1.4rem;
    text-align: center;
  }
  .kpi-value { font-size: 2rem; font-weight: 700; color: #0068C9; margin: 0; }
  .kpi-label { font-size: 0.78rem; color: #64748B; margin: 0; text-transform: uppercase; letter-spacing: .05em; }

  [data-testid="stTabBar"] button { font-size: .88rem !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Data imports
# ---------------------------------------------------------------------------
from data.swivl import COMPANY, PRICING, POSITIONING, DIFFERENTIATORS, STRENGTHS, WEAKNESSES, FEATURES
from data.competitors import (
    DIRECT_COMPETITORS as _DC_BASE,
    INDIRECT_COMPETITORS as _IC_BASE,
    FEATURE_LABELS, FEATURE_CATEGORIES,
    calc_monthly_cost, swivl_monthly_cost,
)

# ---------------------------------------------------------------------------
# Custom competitor storage (persists across sessions)
# ---------------------------------------------------------------------------
_CUSTOM_FILE = Path(__file__).parent / ".tmp" / "custom_competitors.json"

def _load_custom():
    if _CUSTOM_FILE.exists():
        try:
            return json.loads(_CUSTOM_FILE.read_text())
        except Exception:
            pass
    return {"direct": {}, "indirect": {}}

def _save_custom(data: dict):
    _CUSTOM_FILE.parent.mkdir(exist_ok=True)
    _CUSTOM_FILE.write_text(json.dumps(data, indent=2))

_custom_data = _load_custom()
DIRECT_COMPETITORS   = {**_DC_BASE, **_custom_data.get("direct", {})}
INDIRECT_COMPETITORS = {**_IC_BASE, **_custom_data.get("indirect", {})}

# ---------------------------------------------------------------------------
# Competitor classification helpers
# ---------------------------------------------------------------------------
from tools.research_competitor import get_suggestions, build_full_profile, scrape_homepage

def _build_indirect_entry(name, profile):
    return {
        "display_name": name,
        "url": profile.get("url", profile.get("website", "")),
        "one_liner": profile.get("one_liner", ""),
        "threat_level": profile.get("threat_level", "low"),
        "overlap": "To be researched.",
        "pricing_note": profile.get("pricing_note", "—"),
        "key_insight": profile.get("key_insight", "Manually added."),
        "_custom": True,
    }

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
THREAT_ORDER = {"high": 0, "medium": 1, "low": 2, "none": 3}
FEATURE_DISPLAY = {"full": "✅ Full", "partial": "⚠️ Partial", "none": "❌ None", "addon": "🔒 Add-on"}
THREAT_BADGE = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low", "none": "⚪ None"}

def kpi(value, label):
    return f'<div class="kpi-card"><p class="kpi-value">{value}</p><p class="kpi-label">{label}</p></div>'

# ---------------------------------------------------------------------------
# Analysis cache — load once, used by all tabs
# ---------------------------------------------------------------------------
_CACHE_FILE = Path(__file__).parent / ".tmp" / "analysis_cache.json"
_cache: dict = {}
if _CACHE_FILE.exists():
    try:
        _cache = json.loads(_CACHE_FILE.read_text())
    except Exception:
        pass

# Merge fresh G2 ratings into DIRECT_COMPETITORS (non-destructive overlay)
for _cname, _rating_data in _cache.get("ratings", {}).items():
    if _cname in DIRECT_COMPETITORS:
        DIRECT_COMPETITORS[_cname].update(_rating_data)

_feature_alerts: dict = _cache.get("feature_alerts", {})
_pricing_alerts: dict = _cache.get("pricing_alerts", {})
_last_analyzed = "Never"
if _cache.get("last_analyzed"):
    try:
        _last_analyzed = datetime.fromisoformat(_cache["last_analyzed"]).strftime("%b %d, %Y at %I:%M %p")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Title + global Run Analysis CTA
# ---------------------------------------------------------------------------
_hdr_left, _hdr_right = st.columns([5, 1])
with _hdr_left:
    st.title("🔍 Competitor Analysis")
with _hdr_right:
    st.markdown("<div style='padding-top:14px'></div>", unsafe_allow_html=True)
    _run_clicked = st.button("🔄 Run Analysis", type="primary",
                             use_container_width=True, key="global_run_analysis")

if _run_clicked:
    from tools.run_analysis import analyze_all
    with st.status("Running competitive analysis across all tabs...", expanded=True) as _status:
        _result = analyze_all(write_fn=st.write)
        _total  = _result.get("total", 0)
        _ru     = _result.get("ratings_updated", 0)
        _fa     = len(_result.get("feature_alerts", {}))
        _pa     = len(_result.get("pricing_alerts", {}))
        _status.update(
            label=(
                f"✅ Analysis complete — "
                f"{_total} new update(s) · "
                f"{_ru} rating(s) refreshed · "
                f"{_fa} feature alert(s) · "
                f"{_pa} pricing alert(s)"
            ),
            state="complete",
            expanded=False,
        )
    st.rerun()

st.caption(f"Swivl competitive intelligence — last analyzed: **{_last_analyzed}**")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tabs = st.tabs([
    "📊 Competitors",
    "🛠️ Feature Matrix",
    "💰 Pricing",
    "💬 Voice of Customer",
    "🎯 Battlecards",
    "📰 Product Updates",
    "🔥 Pain Points",
])

# ===========================================================================
# TAB 1 — OVERVIEW
# ===========================================================================
with tabs[0]:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(kpi(len(DIRECT_COMPETITORS), "Direct Competitors"), unsafe_allow_html=True)
    with col2:
        st.markdown(kpi(len(INDIRECT_COMPETITORS), "Indirect Competitors"), unsafe_allow_html=True)
    with col3:
        high_threats = sum(1 for c in DIRECT_COMPETITORS.values() if c.get("threat_level") == "high")
        st.markdown(kpi(f"🔴 {high_threats}", "High-Threat"), unsafe_allow_html=True)
    with col4:
        no_ai = sum(
            1 for c in DIRECT_COMPETITORS.values()
            if all(v == "none" for k, v in c.get("features", {}).items() if "ai_" in k)
        )
        st.markdown(kpi(f"{no_ai}/{len(DIRECT_COMPETITORS)}", "Competitors Without AI"), unsafe_allow_html=True)

    st.divider()

    THREAT_REASONING = {
        # Direct
        "Jobber":         "Largest SMB FSM user base (300K+), same ICP, strongest brand — biggest head-to-head threat.",
        "HousecallPro":   "Most reviews in the category (2,700+ Capterra), mobile-first, same buyer profile.",
        "Workiz":         "Built-in VOIP + free tier targets exact same SMB segment and is growing fast.",
        "ServiceTitan":   "Enterprise-focused and expensive but sets AI/feature expectations for the whole category.",
        "FieldEdge":      "Legacy HVAC/plumbing brand with loyal customer base; PE-backed, slower to lose customers.",
        "FieldPulse":     "Highest satisfaction ratings (4.8★) — hard to displace happy customers.",
        "ServiceFusion":  "Same flat unlimited-user pricing philosophy — most structurally similar to Swivl.",
        "mHelpDesk":      "Owned by Angi (Swivl's anti-marketplace target); dated product with no AI.",
        "Kickserv":       "Too basic for growth — hits ceiling at 5–7 techs. Customers outgrow it toward Swivl.",
        "ZohoFSM":        "Only relevant for existing Zoho customers; not trades-native, very low review volume.",
        "Zuper":          "AI-first FSM at same price point and ICP as Swivl — Dispatch AI, mobile-first, multi-trade. Most direct AI competitor.",
        # Indirect
        "SalesforceFS":   "Enterprise-only, irrelevant to Swivl's ICP — but shapes analyst category AI expectations.",
        "ServiceMax":     "Industrial/manufacturing FSM, completely different buyer. No overlap with Swivl's ICP.",
        "Connecteam":     "Workforce management, not FSM — competes for the same SMB owner's budget and attention.",
        "VerizonConnect": "GPS hardware-first telematics; attracts contractors searching for tracking before finding Swivl.",
        "Samsara":        "AI-enhanced fleet GPS — overlaps with Swivl's GPS module for larger vehicle fleets.",
        "MSDynamics365":  "Enterprise Microsoft ecosystem — no overlap with Swivl's SMB trades ICP.",
        "QuickBooks":     "Incumbent accounting tool all Swivl customers use — any scheduling expansion is a direct threat.",
        "Angi":           "Swivl's anti-marketplace positioning directly targets frustrated Angi contractors.",
        "Thumbtack":      "Same lead marketplace displacement opportunity as Angi; adding contractor business tools.",
        "GoogleBusiness": "Free incumbent for reviews and local search — substitutes for Swivl's website builder and leads.",
    }

    st.subheader("Competitive Threat Ranking — All 20 Competitors")

    all_rows = []

    # Direct competitors
    sorted_direct = sorted(
        DIRECT_COMPETITORS.items(),
        key=lambda x: THREAT_ORDER.get(x[1].get("threat_level", "low"), 3),
    )
    for name, c in sorted_direct:
        all_rows.append({
            "Competitor": name,
            "Type": "Direct",
            "Threat": THREAT_BADGE.get(c.get("threat_level", "low"), ""),
            "Free Tier": "✅" if c.get("free_tier") else "❌",
            "Has AI": "✅" if any(v != "none" for k, v in c.get("features", {}).items() if "ai_" in k) else "❌",
            "G2 ★": f"{c['g2_rating']:.1f}" if c.get("g2_rating") is not None else "N/A",
            "Why This Threat Level": THREAT_REASONING.get(name, ""),
        })

    # Indirect competitors
    indirect_threat_order = {"medium": 1, "low": 2, "none": 3}
    sorted_indirect = sorted(
        INDIRECT_COMPETITORS.items(),
        key=lambda x: indirect_threat_order.get(x[1].get("threat_level", "none"), 3),
    )
    for name, c in sorted_indirect:
        threat = c.get("threat_level", "none")
        all_rows.append({
            "Competitor": c.get("display_name", name),
            "Type": "Indirect",
            "Threat": THREAT_BADGE.get(threat, "⚪ None"),
            "Free Tier": "—",
            "Has AI": "—",
            "G2 ★": "—",
            "Why This Threat Level": THREAT_REASONING.get(name, c.get("key_insight", "")),
        })

    ranking_df = pd.DataFrame(all_rows)

    def highlight_type(row):
        if row["Type"] == "Direct":
            return [""] * len(row)
        return ["color: #64748B; font-style: italic;"] * len(row)

    st.dataframe(
        ranking_df.style.apply(highlight_type, axis=1),
        hide_index=True,
        width="stretch",
        height=680,
    )

    st.divider()
    st.subheader("Swivl Differentiators")
    diff_cols = st.columns(2)
    for i, d in enumerate(DIFFERENTIATORS):
        with diff_cols[i % 2]:
            st.markdown(f"• {d}")

    # -----------------------------------------------------------------------
    # Competitor Profiles — Messaging, ICP, TAM/SAM/SOM
    # -----------------------------------------------------------------------
    COMP_PROFILES = {
        # ── Direct ──────────────────────────────────────────────────────────
        "Jobber": {
            "messaging": [
                "Simplest FSM trusted by 300K+ home service pros",
                "Quote, schedule, invoice and get paid — all in one place",
                "Built for every home service trade",
            ],
            "icp": "Owner-operators of 1–50 tech residential home service businesses (HVAC, plumbing, landscaping, cleaning) in US, Canada, UK, Australia. Mobile-first, price-conscious, want simplicity.",
            "tam": "$6B — global SMB field service software",
            "sam": "$2B — English-speaking residential home service, 1–50 techs",
            "som": "~$100M ARR (est.) — largest SMB FSM player",
        },
        "HousecallPro": {
            "messaging": [
                "Run and grow your home service business",
                "Mobile-first — manage everything from your phone",
                "'On My Way' texts that customers love",
            ],
            "icp": "1–20 tech residential home service contractors in the US (plumbing, HVAC, electrical, cleaning). Mobile-first operators who want strong customer communication tools.",
            "tam": "$5B — US home service software market",
            "sam": "$1.5B — residential SMB, 1–20 techs, mobile-first",
            "som": "~$50M ARR (est.)",
        },
        "ServiceTitan": {
            "messaging": [
                "The operating system for the trades",
                "Built for contractors who want to dominate their market",
                "Data-driven decisions for every job",
            ],
            "icp": "10–500+ tech commercial and residential trades contractors (HVAC, plumbing, electrical, roofing). Businesses with dedicated office staff, dispatchers, and managers — not owner-operators.",
            "tam": "$12B — US trades contracting software",
            "sam": "$4B — businesses with 10+ techs in core trades",
            "som": "~$500M ARR (est.) — dominant mid-market player",
        },
        "Workiz": {
            "messaging": [
                "All-in-one FSM with built-in phone system",
                "Never miss a customer call again",
                "Book more jobs with online booking",
            ],
            "icp": "1–20 tech home service businesses that live on the phone — locksmiths, garage door, appliance repair, junk removal. VOIP dependency is key differentiator.",
            "tam": "$4B — SMB FSM + VOIP-enabled service businesses",
            "sam": "$800M — phone-heavy home service SMBs, 1–20 techs",
            "som": "~$15–30M ARR (est.)",
        },
        "FieldEdge": {
            "messaging": [
                "FSM built specifically for HVAC, plumbing and electrical",
                "Flat-rate pricing with a built-in pricebook",
                "Deep QuickBooks integration for the trades",
            ],
            "icp": "5–50 tech HVAC, plumbing, and electrical contractors with established flat-rate pricing workflows and existing QuickBooks dependency. Prefer a trades-specific tool over generalist FSM.",
            "tam": "$3B — HVAC/plumbing/electrical software",
            "sam": "$900M — 5–50 tech specialty trades with flat-rate pricing",
            "som": "~$20–50M ARR (est.)",
        },
        "FieldPulse": {
            "messaging": [
                "Highest-rated contractor software — 4.8★ on G2 and Capterra",
                "Simple, powerful, with real human support",
                "Everything you need, nothing you don't",
            ],
            "icp": "1–30 tech contractors who prioritize ease-of-use and customer support over feature depth. Any residential trade vertical. Buyers who've been burned by complex enterprise tools.",
            "tam": "$5B — SMB FSM",
            "sam": "$1B — simplicity-focused SMB contractors, 1–30 techs",
            "som": "~$5–15M ARR (est.)",
        },
        "ServiceFusion": {
            "messaging": [
                "Simple, affordable field service management",
                "Flat pricing — unlimited users, no surprises",
                "Everything your field service business needs in one place",
            ],
            "icp": "5–50 tech home and commercial service businesses looking for predictable flat-rate pricing. Budget-conscious buyers who've outgrown per-seat tools.",
            "tam": "$4B — SMB FSM",
            "sam": "$800M — flat-rate pricing-sensitive SMBs, 5–50 techs",
            "som": "~$20–40M ARR (est.)",
        },
        "mHelpDesk": {
            "messaging": [
                "Easy field service management for small businesses",
                "Seamless QuickBooks integration",
                "Connected to Angi for built-in lead generation",
            ],
            "icp": "1–20 tech residential service businesses already using Angi/HomeAdvisor for leads. QuickBooks-dependent buyers who want a simple bridge between leads and invoices.",
            "tam": "$3B — US small home service software",
            "sam": "$500M — Angi ecosystem contractors, 1–20 techs",
            "som": "~$10–20M ARR (est.)",
        },
        "Kickserv": {
            "messaging": [
                "Simple CRM and field service for contractors",
                "Affordable — start free, grow when ready",
                "Works with QuickBooks out of the box",
            ],
            "icp": "1–10 tech contractors transitioning off pen-and-paper or spreadsheets. First-time software buyers who are price-sensitive and need minimal onboarding.",
            "tam": "$2B — micro-SMB service businesses",
            "sam": "$400M — 1–10 tech first-time software buyers",
            "som": "~$2–8M ARR (est.)",
        },
        "ZohoFSM": {
            "messaging": [
                "End-to-end FSM for the Zoho ecosystem",
                "Seamlessly integrated with Zoho CRM, Books and Desk",
                "Configurable for any service workflow",
            ],
            "icp": "Businesses already using 2+ Zoho products (CRM, Books, Desk) who want to add FSM without switching platforms. Not trades-specific — any service vertical.",
            "tam": "$4B — FSM (Zoho targets mid-market and enterprise)",
            "sam": "$600M — existing Zoho customer base needing FSM",
            "som": "Early stage — very low review volume",
        },
        "Zuper": {
            "messaging": [
                "Field Service, Your Way — fully configurable FSM",
                "AI-powered dispatch and intelligent scheduling",
                "Built for multi-trade contractors with enterprise integrations",
            ],
            "icp": "5–100 tech multi-trade or multi-location contractors (HVAC, plumbing, electrical, commercial cleaning) needing customizable workflows, asset tracking, and Salesforce/SAP integrations. Mid-market to enterprise lean.",
            "tam": "$5B — SMB to mid-market FSM",
            "sam": "$1.2B — configurable FSM for multi-trade contractors, 5–100 techs",
            "som": "~$8M ARR (est.) — growing",
        },
        # ── Indirect ────────────────────────────────────────────────────────
        "SalesforceFS": {
            "founded": "1999 (Salesforce Corp.)",
            "revenue": "Part of Salesforce — $34.9B total revenue (FY2024)",
            "messaging": [
                "Field service connected to your entire Salesforce CRM",
                "Einstein AI for predictive scheduling",
                "Enterprise-grade uptime and security",
            ],
            "icp": "Enterprise companies (500+ employees) with complex field operations, already on Salesforce CRM and Sales Cloud. Requires dedicated Salesforce admin.",
            "tam": "$15B — enterprise FSM globally",
            "sam": "$5B — Salesforce-connected enterprise FSM",
            "som": "Part of Salesforce's $34B+ ARR",
        },
        "ServiceMax": {
            "founded": "2007 (acquired by Salesforce 2023)",
            "revenue": "~$100M ARR (est.) before Salesforce acquisition",
            "messaging": [
                "Asset-centric FSM for complex equipment maintenance",
                "Maximize asset uptime — minimize service costs",
                "Built for medical device, industrial, and manufacturing",
            ],
            "icp": "Enterprise manufacturers and healthcare orgs managing 10,000+ physical assets — medical devices, industrial equipment, aerospace. IT-led purchase.",
            "tam": "$8B — industrial/medical FSM",
            "sam": "$2B — asset-intensive enterprise FSM",
            "som": "~$100M ARR (est., now part of Salesforce)",
        },
        "Connecteam": {
            "founded": "2016",
            "revenue": "~$50M ARR (est.)",
            "messaging": [
                "All-in-one app for deskless workers",
                "Replace WhatsApp groups and paper schedules",
                "Free for up to 10 users",
            ],
            "icp": "SMB businesses with deskless/frontline workers (retail, construction, cleaning, hospitality) needing HR, scheduling, and team comms — not job-to-invoice FSM workflows.",
            "tam": "$5B — deskless workforce management",
            "sam": "$1.5B — SMB deskless workforce apps",
            "som": "~$50M ARR (est.)",
        },
        "VerizonConnect": {
            "founded": "2016 (brand formed from Verizon fleet acquisitions)",
            "revenue": "Part of Verizon — $134.8B total revenue (2023)",
            "messaging": [
                "GPS fleet management backed by Verizon's network",
                "See your entire fleet in real time",
                "Reduce fuel costs and improve driver safety",
            ],
            "icp": "Fleet-heavy businesses (5–200 vehicles) prioritizing GPS tracking and telematics — often larger service companies or logistics operators.",
            "tam": "$10B — global fleet telematics",
            "sam": "$3B — US commercial fleet tracking, SMB to mid-market",
            "som": "Part of Verizon's $135B revenue",
        },
        "Samsara": {
            "founded": "2015",
            "revenue": "~$1.1B ARR (FY2024, public company NYSE: IOT)",
            "messaging": [
                "The connected operations platform",
                "AI-powered fleet safety and efficiency",
                "Real-time visibility across your entire operation",
            ],
            "icp": "Mid-to-large fleet operators (20–500 vehicles) in transportation, construction, utilities, and field service needing advanced telematics + compliance.",
            "tam": "$55B — connected operations market",
            "sam": "$10B — fleet telematics + operations software",
            "som": "~$1.1B ARR (public company, NYSE: IOT)",
        },
        "MSDynamics365": {
            "founded": "1975 (Microsoft Corp.); Dynamics 365 FSM launched 2016",
            "revenue": "Part of Microsoft — $245B total revenue (FY2024)",
            "messaging": [
                "Intelligent field service with Microsoft Copilot AI",
                "Connected across the entire Microsoft 365 ecosystem",
                "AI-powered scheduling optimization",
            ],
            "icp": "Enterprise organizations (1,000+ employees) already on Microsoft 365/Azure needing FSM. IT-led purchase, requires implementation partner.",
            "tam": "$15B — enterprise FSM",
            "sam": "$4B — Microsoft-ecosystem enterprise FSM",
            "som": "Part of Microsoft's $245B+ revenue",
        },
        "QuickBooks": {
            "founded": "1983 (Intuit Inc.); QuickBooks launched 1992",
            "revenue": "~$4.5B ARR — QuickBooks segment (Intuit FY2024)",
            "messaging": [
                "America's #1 small business accounting software",
                "Get paid faster — invoices, payroll, and taxes",
                "Know exactly where your money is going",
            ],
            "icp": "Small businesses of all types needing accounting. Virtually all Swivl customers already use QuickBooks — Swivl integrates with it rather than displacing it.",
            "tam": "$50B — global SMB accounting software",
            "sam": "$8B — US SMB accounting + adjacent tools",
            "som": "~$4.5B ARR (Intuit QuickBooks segment)",
        },
        "Angi": {
            "founded": "1995 (as ServiceMagic); rebranded Angi 2021",
            "revenue": "~$1.8B revenue (2023, public company ANGI)",
            "messaging": [
                "Find trusted pros for any home project",
                "Read real reviews, compare quotes",
                "Book instantly — Angi Guaranteed",
            ],
            "icp": "Homeowners seeking service pros. Contractors are the supply side — paying per-lead fees of 15–25% that Swivl's anti-marketplace positioning directly attacks.",
            "tam": "$600B — US home services market",
            "sam": "$4B — US home service lead generation",
            "som": "~$1.8B revenue (public company, ANGI)",
        },
        "Thumbtack": {
            "founded": "2008",
            "revenue": "~$300M revenue (est.)",
            "messaging": [
                "Find the right local pro for any project",
                "Personalized matches in seconds",
                "Thumbtack Pro — manage your business and get reviews",
            ],
            "icp": "Local service pros of all types; Thumbtack Pro is expanding into scheduling and CRM — same displacement opportunity Swivl targets with Angi.",
            "tam": "$400B — US local services",
            "sam": "$3B — local service lead marketplace",
            "som": "~$300M revenue (est.)",
        },
        "GoogleBusiness": {
            "founded": "1998 (Google); Google My Business launched 2014",
            "revenue": "Free product — Alphabet total revenue $307B (2023)",
            "messaging": [
                "Show up when customers search for you — for free",
                "Manage your business profile across Google Search and Maps",
                "Get more calls and bookings with Local Service Ads",
            ],
            "icp": "Every local business — universally adopted. Every Swivl customer already has a Google Business Profile. Free tools substitute for Swivl's website builder and lead capture.",
            "tam": "Universal — every local business globally",
            "sam": "$2B — US local business tools and advertising",
            "som": "Free product; revenue via Google Ads ecosystem ($237B+)",
        },
    }

    st.divider()
    st.subheader("Messaging, ICP & Market Size — All 20 Competitors")
    st.caption("Direct competitors first, then indirect. Expand any card for full detail.")

    all_comp_items = (
        list(DIRECT_COMPETITORS.items()) +
        [(k, v) for k, v in INDIRECT_COMPETITORS.items()]
    )

    card_cols = st.columns(2)
    for idx, (key, comp_data) in enumerate(all_comp_items):
        profile = COMP_PROFILES.get(key, {})
        display_name = comp_data.get("display_name", key)
        threat = comp_data.get("threat_level", "none")
        comp_type = "Direct" if key in DIRECT_COMPETITORS else "Indirect"

        with card_cols[idx % 2]:
            with st.expander(f"{THREAT_BADGE.get(threat, '⚪')}  **{display_name}** — {comp_type}"):
                # Founded + Revenue — pull from DIRECT_COMPETITORS for direct, COMP_PROFILES for indirect
                if key in DIRECT_COMPETITORS:
                    founded = DIRECT_COMPETITORS[key].get("founded", "—")
                    revenue = DIRECT_COMPETITORS[key].get("est_arr", "—")
                else:
                    founded = profile.get("founded", "—")
                    revenue = profile.get("revenue", "—")

                meta_cols = st.columns(2)
                with meta_cols[0]:
                    st.markdown(f"**📅 Founded:** {founded}")
                with meta_cols[1]:
                    st.markdown(f"**💰 Revenue:** {revenue}")

                st.divider()

                if profile.get("messaging"):
                    st.markdown("**📣 Messaging**")
                    for m in profile["messaging"]:
                        st.markdown(f"• {m}")

                if profile.get("icp"):
                    st.markdown("**🎯 ICP**")
                    st.markdown(profile["icp"])

                if profile.get("tam"):
                    st.markdown("**📈 Market Size (est.)**")
                    st.markdown(f"- **TAM:** {profile['tam']}")
                    st.markdown(f"- **SAM:** {profile['sam']}")

# ===========================================================================
# TAB 2 — FEATURE MATRIX
# ===========================================================================
with tabs[1]:
    st.subheader("Feature Comparison Matrix")

    if _feature_alerts:
        with st.expander(f"⚡ {len(_feature_alerts)} feature change alert(s) detected — click to review", expanded=False):
            for _comp, _alert in _feature_alerts.items():
                st.warning(f"**{_comp}** — {_alert}")

    cat_options = ["All Categories"] + list(FEATURE_CATEGORIES.keys())
    selected_cat = st.selectbox("Filter by category", cat_options, key="feat_cat")

    if selected_cat == "All Categories":
        feature_keys = list(FEATURE_LABELS.keys())
    else:
        feature_keys = FEATURE_CATEGORIES[selected_cat]

    comp_names = list(DIRECT_COMPETITORS.keys())

    rows = []
    for fk in feature_keys:
        row = {"Feature": FEATURE_LABELS.get(fk, fk)}
        row["Swivl"] = FEATURE_DISPLAY.get(FEATURES.get(fk, "none"), "❌ None")
        for name in comp_names:
            status = DIRECT_COMPETITORS[name].get("features", {}).get(fk, "none")
            row[name] = FEATURE_DISPLAY.get(status, "❌ None")
        rows.append(row)

    matrix_df = pd.DataFrame(rows)

    def style_cell(val):
        if isinstance(val, str):
            if val.startswith("✅"):
                return "background-color: #DCFCE7; color: #166534; font-weight: 600;"
            elif val.startswith("⚠️"):
                return "background-color: #FEF9C3; color: #854D0E; font-weight: 600;"
            elif val.startswith("❌"):
                return "background-color: #FEE2E2; color: #991B1B;"
            elif val.startswith("🔒"):
                return "background-color: #F3E8FF; color: #6B21A8; font-weight: 600;"
        return ""

    styled = matrix_df.style.map(style_cell, subset=["Swivl"] + comp_names)
    st.dataframe(styled, hide_index=True, width="stretch", height=600)
    st.caption("✅ Full  ⚠️ Partial  ❌ None  🔒 Add-on")

# ===========================================================================
# TAB 3 — PRICING
# ===========================================================================
with tabs[2]:

    if _pricing_alerts:
        with st.expander(f"💰 {len(_pricing_alerts)} pricing change alert(s) detected — click to review", expanded=False):
            for _comp, _alert in _pricing_alerts.items():
                st.warning(f"**{_comp}** — {_alert}")

    # -----------------------------------------------------------------------
    # Competitor Pricing Model Explainers
    # -----------------------------------------------------------------------
    st.subheader("How Each Competitor Charges")
    st.caption("Understanding the pricing model before comparing costs.")

    PRICING_EXPLAINERS = {
        "Swivl": {
            "model": "Flat monthly — unlimited users",
            "summary": "One flat fee covers your entire team, no matter how many technicians you add. AI features (GPS, AI Estimator, AI Receptionist) are consumed as credits included in your plan.",
            "plans_note": "Starter $0 · Growth $49 · Scale Pro $149 · Org $299 — all unlimited users.",
            "watch_out": "Heavy GPS or AI Receptionist usage can exhaust credits; top up or upgrade plan.",
            "verdict": "✅ Most predictable for growing teams — cost doesn't increase as you hire.",
        },
        "Jobber": {
            "model": "Per-user monthly (billed annually)",
            "summary": "Each plan includes a fixed number of users; every additional seat costs $29/mo extra. Costs grow linearly as your team grows.",
            "plans_note": "Core $49 (1 user) · Connect $139 (5 users) · Grow $199 (10 users) · Plus $699 (15 users). All +$29/user beyond included.",
            "watch_out": "A 10-tech team on Grow = $199 base + $0 extra = $199. An 11th tech jumps you to $228. GPS is a paid add-on.",
            "verdict": "⚠️ Gets expensive fast above 10 techs. No AI features.",
        },
        "HousecallPro": {
            "model": "Tiered flat (user-capped per tier)",
            "summary": "Plans are capped at a maximum number of users. Basic fits 1 user, Essentials fits 5, MAX starts at 8 then charges $35/extra user.",
            "plans_note": "Basic $79 (1 user) · Essentials $189 (up to 5) · MAX $329 (up to 8, then +$35/user).",
            "watch_out": "At 10 techs you must be on MAX: $329 + 2×$35 = $399/mo. Annual contract required for best rates.",
            "verdict": "⚠️ Good for small teams; per-user charge on MAX plan hurts at scale.",
        },
        "ServiceTitan": {
            "model": "Tiered enterprise (flat per tier, contact sales)",
            "summary": "Three tiers with flat monthly pricing. Includes unlimited users at each tier. Requires a 1–3 year contract and a 60–90 day onboarding process.",
            "plans_note": "Starter $398 · Essentials $498 · The Works $598 — all unlimited users. Pricing publicly listed but negotiable.",
            "watch_out": "Long-term contracts, expensive implementation fees ($5K–$20K+), and dedicated admin required.",
            "verdict": "🔴 Built for 10+ tech teams with office staff. Overkill — and expensive — for owner-operators.",
        },
        "Workiz": {
            "model": "Base + per-user above included seats (annual)",
            "summary": "Lite plan is free for 2 users. Paid plans include 5 users and charge per additional seat. Annual billing required for advertised rates.",
            "plans_note": "Lite $0 (2 users) · Standard $275/mo (5 included, +$46/user) · Pro $325/mo (5 included, +$54/user). Billed annually.",
            "watch_out": "Month-to-month rates are ~20% higher. At 10 techs on Pro: $325 + 5×$54 = $595/mo.",
            "verdict": "⚠️ VOIP is the standout feature; pricing becomes steep at scale.",
        },
        "FieldEdge": {
            "model": "Per-user (contact sales — opaque pricing)",
            "summary": "No public pricing. Requires a sales call. Estimated at $125–$175/user/mo based on customer reports. Trades-specific pricebook is the core value prop.",
            "plans_note": "Select and Premium tiers — pricing only available after a demo.",
            "watch_out": "Lack of pricing transparency is a red flag. Customers report being locked into multi-year contracts.",
            "verdict": "🔴 No free tier, no self-serve, no transparent pricing. High barrier to evaluate.",
        },
        "FieldPulse": {
            "model": "Per-user (contact sales — opaque pricing)",
            "summary": "No public pricing page. Estimated $60–$99/user/mo from customer reviews. Positioned on quality and support rather than price.",
            "plans_note": "Single Standard plan — contact sales for pricing.",
            "watch_out": "Despite the high satisfaction score, lack of transparent pricing creates friction in the buying process.",
            "verdict": "⚠️ Great product but pricing opacity means you can't self-evaluate. No free tier.",
        },
        "ServiceFusion": {
            "model": "Flat monthly — unlimited users (3 tiers)",
            "summary": "Same unlimited-user philosophy as Swivl. Three tiers with increasing feature access. No per-seat charges ever.",
            "plans_note": "Starter $208 · Plus $325 · Pro $533 — all unlimited users, annual billing.",
            "watch_out": "Entry price $208 is higher than Swivl Scale Pro ($149). No free tier, no AI features. Annual contract required.",
            "verdict": "⚠️ Right pricing model but higher entry price ($208 vs $149) and no AI.",
        },
        "mHelpDesk": {
            "model": "Tiered flat (contact sales)",
            "summary": "Tiered pricing with estimated costs from customer reports. Owned by Angi — the lead marketplace Swivl targets. No GPS or AI features.",
            "plans_note": "Basic ~$169 · Standard ~$299 · Enterprise custom. Pricing requires a sales conversation.",
            "watch_out": "Owned by Angi — there's a built-in incentive to steer you toward their lead marketplace fees.",
            "verdict": "🔴 Conflict of interest with Angi ownership. No GPS, no AI, no free tier.",
        },
        "Kickserv": {
            "model": "Tiered flat (user-capped per tier)",
            "summary": "Lowest-cost FSM in the market. Each tier caps the number of users. Good entry point but feature ceiling is low — no GPS, no AI, no offline mobile.",
            "plans_note": "Free (1 user) · Lite $19 (2 users) · Standard $69 (5 users) · Business $129 (10 users).",
            "watch_out": "Hit a ceiling at 7–10 techs — no growth path within the platform.",
            "verdict": "⚠️ Great for getting started. Customers outgrow it quickly and migrate to Swivl.",
        },
        "ZohoFSM": {
            "model": "Per-user monthly (two roles)",
            "summary": "Charges per user based on role — Field Agent or Supervisor. Only cost-effective if already deeply embedded in the Zoho ecosystem.",
            "plans_note": "Field Agent $30/user/mo · Supervisor $45/user/mo.",
            "watch_out": "At 10 techs (all Field Agents) = $300/mo vs Swivl $149. No trades-native features.",
            "verdict": "⚠️ Only makes sense for existing Zoho customers. Not built for the trades.",
        },
        "Zuper": {
            "model": "Per-user (annual contract — contact sales)",
            "summary": "Three tiers priced per user. No public pricing page — requires a sales conversation. Annual contracts only. Most SMBs land on Core. Premium unlocks full AI suite.",
            "plans_note": "Starter ~$50/user/mo · Core ~$89/user/mo · Premium ~$150/user/mo. All billed annually.",
            "watch_out": "At 10 techs on Core = $890/mo vs. Swivl Scale Pro $149 flat. Annual-only contracts with no self-serve trial — high friction to evaluate.",
            "verdict": "🔴 Per-user pricing is 4–6× more expensive than Swivl at team scale. No free tier, no month-to-month.",
        },
    }

    # Display in 2-column grid
    exp_cols = st.columns(2)
    all_providers = ["Swivl"] + list(DIRECT_COMPETITORS.keys())
    for i, provider in enumerate(all_providers):
        info = PRICING_EXPLAINERS.get(provider, {})
        if not info:
            continue
        with exp_cols[i % 2]:
            with st.expander(f"**{provider}** — {info.get('model', '')}"):
                st.markdown(f"**How it works:** {info['summary']}")
                st.markdown(f"**Plans:** {info['plans_note']}")
                st.markdown(f"**Watch out:** {info['watch_out']}")
                st.markdown(f"**Verdict:** {info['verdict']}")

    st.divider()
    st.subheader("All Plans — Monthly Cost Comparison")

    num_techs = st.slider("Team size (technicians)", min_value=1, max_value=50, value=10, step=1)

    # -----------------------------------------------------------------------
    # Build one row per plan (Swivl + all competitors)
    # -----------------------------------------------------------------------
    def plan_cost_at(comp_data: dict, plan: dict, n: int) -> float | None:
        model = comp_data.get("pricing_model", "")
        base = plan.get("base")
        if base is None:
            return None
        per_user = plan.get("per_user", 0) or 0
        included = plan.get("included", 1) or 1
        max_u = plan.get("max_users", 9999) or 9999

        if model in ("per_user", "base_plus_per_user"):
            return base + max(0, n - included) * per_user
        if model == "tiered_flat":
            if n <= max_u:
                return float(base)
            return base + (n - max_u) * per_user
        return float(base)

    all_plan_rows = []

    # Swivl plans (unlimited users — flat regardless of team size)
    for p in PRICING["plans"]:
        all_plan_rows.append({
            "Provider": "Swivl",
            "Plan Label": f"Swivl · {p['name']}",
            "Monthly Cost": float(p["price"]),
            "Color": "swivl",
            "Users": "Unlimited",
            "Note": f"{p['credits']:,} credits/mo",
        })

    # Competitor plans
    for name, comp in DIRECT_COMPETITORS.items():
        for p in comp.get("plans", []):
            cost = plan_cost_at(comp, p, num_techs)
            if cost is None:
                continue
            per_user = p.get("per_user", 0) or 0
            included = p.get("included") or "∞"
            users_note = f"Unlimited" if not per_user else f"+${per_user}/user above {included}"
            all_plan_rows.append({
                "Provider": name,
                "Plan Label": f"{name} · {p['name']}",
                "Monthly Cost": cost,
                "Color": comp.get("threat_level", "low"),
                "Users": users_note,
                "Note": p.get("note", ""),
            })

    all_plans_df = pd.DataFrame(all_plan_rows).sort_values("Monthly Cost")

    color_scale2 = alt.Scale(
        domain=["swivl", "high", "medium", "low"],
        range=["#0068C9", "#DC2626", "#D97706", "#16A34A"],
    )
    bar_chart = (
        alt.Chart(all_plans_df)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            y=alt.Y("Plan Label:N", sort=alt.SortField("Monthly Cost", order="ascending"), title=None),
            x=alt.X("Monthly Cost:Q", title="Monthly Cost ($)"),
            color=alt.Color("Color:N", scale=color_scale2, legend=alt.Legend(title="Provider")),
            tooltip=["Plan Label", "Monthly Cost", "Users", "Note"],
        )
        .properties(height=max(340, len(all_plan_rows) * 28))
    )
    text_labels = (
        alt.Chart(all_plans_df)
        .mark_text(align="left", dx=4, fontSize=11, fontWeight="bold")
        .encode(
            y=alt.Y("Plan Label:N", sort=alt.SortField("Monthly Cost", order="ascending")),
            x="Monthly Cost:Q",
            text=alt.Text("Monthly Cost:Q", format="$,.0f"),
        )
    )
    st.altair_chart((bar_chart + text_labels).interactive(), width="stretch")

    # Savings callout — compare Swivl Scale Pro vs most threatening competitor's cheapest plan
    swivl_scale_pro = 149.0
    top_threat_name = next(
        (name for name, comp in sorted(
            DIRECT_COMPETITORS.items(),
            key=lambda x: THREAT_ORDER.get(x[1].get("threat_level"), 3),
        ) if any(
            plan_cost_at(comp, p, num_techs) is not None
            for p in comp.get("plans", [])
        )),
        None,
    )
    if top_threat_name:
        top_comp = DIRECT_COMPETITORS[top_threat_name]
        rival_costs = [
            plan_cost_at(top_comp, p, num_techs)
            for p in top_comp.get("plans", [])
            if plan_cost_at(top_comp, p, num_techs) is not None
        ]
        if rival_costs:
            rival_min = min(rival_costs)
            if rival_min > swivl_scale_pro:
                savings = rival_min - swivl_scale_pro
                st.success(
                    f"**Swivl Scale Pro saves ${savings:,.0f}/mo vs. {top_threat_name}'s cheapest plan** "
                    f"at {num_techs} technicians — that's **${savings * 12:,.0f}/year**."
                )

    st.divider()

    # -----------------------------------------------------------------------
    # Savings table — competitor plan vs each Swivl plan at selected team size
    # -----------------------------------------------------------------------
    st.subheader(f"Savings vs. Swivl — {num_techs} Technicians")
    st.caption(
        "Green = Swivl is cheaper (you save). Red = Swivl costs more. "
        "Annual savings shown in parentheses."
    )

    swivl_plans = PRICING["plans"]  # [{name, price, ...}, ...]

    savings_rows = []
    for name, comp in DIRECT_COMPETITORS.items():
        for p in comp.get("plans", []):
            comp_cost = plan_cost_at(comp, p, num_techs)
            if comp_cost is None:
                continue
            row = {
                "Competitor": name,
                "Plan": p["name"],
                f"Their Cost / mo": f"${comp_cost:,.0f}",
            }
            for sp in swivl_plans:
                swivl_cost = float(sp["price"])
                diff = comp_cost - swivl_cost          # positive = Swivl cheaper
                annual = diff * 12
                if diff > 0:
                    row[f"vs Swivl {sp['name']} (${sp['price']})"] = f"+${diff:,.0f}/mo  (save ${annual:,.0f}/yr)"
                elif diff < 0:
                    row[f"vs Swivl {sp['name']} (${sp['price']})"] = f"-${abs(diff):,.0f}/mo  (costs ${abs(annual):,.0f}/yr more)"
                else:
                    row[f"vs Swivl {sp['name']} (${sp['price']})"] = "Same price"
            savings_rows.append(row)

    savings_df = pd.DataFrame(savings_rows)
    swivl_col_names = [f"vs Swivl {sp['name']} (${sp['price']})" for sp in swivl_plans]

    def style_savings(val):
        if isinstance(val, str):
            if val.startswith("+"):
                return "background-color: #DCFCE7; color: #166534; font-weight: 600;"
            elif val.startswith("-"):
                return "background-color: #FEE2E2; color: #991B1B; font-weight: 600;"
            elif val == "Same price":
                return "background-color: #F1F5F9; color: #64748B;"
        return ""

    st.dataframe(
        savings_df.style.map(style_savings, subset=swivl_col_names),
        hide_index=True,
        width="stretch",
        height=min(800, len(savings_rows) * 36 + 60),
    )

# ===========================================================================
# TAB 4 — VOICE OF CUSTOMER
# ===========================================================================
with tabs[3]:
    st.subheader("Voice of Customer — Reviews & Ratings")

    selected_comp = st.selectbox("Select competitor", list(DIRECT_COMPETITORS.keys()), key="voc_comp")
    c = DIRECT_COMPETITORS[selected_comp]

    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        g2 = f"{c['g2_rating']:.1f}" if c.get("g2_rating") is not None else "N/A"
        st.metric("G2 Rating", f"{g2}★", f"{c.get('g2_reviews', 0):,} reviews")
    with rc2:
        cap = f"{c['capterra_rating']:.1f}" if c.get("capterra_rating") is not None else "N/A"
        st.metric("Capterra Rating", f"{cap}★", f"{c.get('capterra_reviews', 0):,} reviews")
    with rc3:
        total = c.get("g2_reviews", 0) + c.get("capterra_reviews", 0)
        st.metric("Total Reviews", f"{total:,}", "G2 + Capterra")

    st.divider()

    col_pros, col_cons = st.columns(2)
    with col_pros:
        st.markdown("**👍 Top Customer Pros**")
        for pro in c.get("top_pros", []):
            st.markdown(f"• {pro}")

    with col_cons:
        st.markdown("**👎 Top Customer Cons**")
        for con in c.get("top_cons", []):
            st.markdown(f"• {con}")

    st.divider()
    st.markdown("**💡 Swivl Sales Angle**")
    for item in c.get("losses_vs_swivl", []):
        st.markdown(f"• {item}")

# ===========================================================================
# TAB 5 — BATTLECARDS
# ===========================================================================
with tabs[4]:
    st.subheader("Competitive Battlecards")

    selected_bc = st.selectbox("Select competitor", list(DIRECT_COMPETITORS.keys()), key="bc_comp")
    c = DIRECT_COMPETITORS[selected_bc]

    # ── Row 1: Identity bar ─────────────────────────────────────────────────
    st.markdown(f"### {selected_bc} &nbsp; {THREAT_BADGE.get(c.get('threat_level','low'),'')}", unsafe_allow_html=True)
    st.caption(c.get("one_liner", ""))

    id1, id2, id3, id4, id5 = st.columns(5)
    id1.metric("Founded", c.get("founded", "—"))
    id2.metric("Funding", c.get("funding", "—").split("(")[0].strip())
    id3.metric("Team Size", c.get("team_size", "—"))
    id4.metric("G2", f"{c['g2_rating']:.1f}★ ({c.get('g2_reviews',0):,})" if c.get("g2_rating") is not None else "—")
    id5.metric("Capterra", f"{c['capterra_rating']:.1f}★ ({c.get('capterra_reviews',0):,})" if c.get("capterra_rating") is not None else "—")

    st.divider()

    # ── Row 2: Pricing vs Swivl ─────────────────────────────────────────────
    st.markdown("#### 💰 Pricing Comparison")
    pr_cols = st.columns([1, 1, 1])
    with pr_cols[0]:
        st.markdown(f"**{selected_bc} pricing model**")
        st.markdown(f"`{c.get('pricing_model','').replace('_',' ').title()}`")
        plans = [p for p in c.get("plans", []) if p.get("base") is not None]
        for p in plans:
            per = f" +${p['per_user']}/user" if p.get("per_user") else " · unlimited users"
            note = f" _{p['note']}_" if p.get("note") else ""
            st.markdown(f"- **{p['name']}** — ${p['base']}/mo{per}{note}")
        if c.get("free_tier"):
            st.success("✅ Has free tier")
        else:
            st.error("❌ No free tier")
        st.markdown(f"Trial: **{c.get('trial','None')}**")

    with pr_cols[1]:
        st.markdown("**Swivl plans (unlimited users)**")
        for sp in PRICING["plans"]:
            ai = " _(incl. AI Receptionist)_" if sp.get("ai_receptionist") else ""
            st.markdown(f"- **{sp['name']}** — ${sp['price']}/mo · {sp['credits']:,} credits{ai}")
        st.success("✅ Has free tier")
        st.markdown("Trial: **28-day**")

    with pr_cols[2]:
        st.markdown("**Cost at common team sizes**")
        cost_data = []
        for n in [1, 5, 10, 25]:
            comp_cost = calc_monthly_cost(selected_bc, n)
            swivl_cost = 149.0
            if comp_cost is not None:
                diff = comp_cost - swivl_cost
                arrow = f"🟢 Save ${diff:,.0f}/mo" if diff > 0 else f"🔴 +${abs(diff):,.0f}/mo more"
                cost_data.append({
                    "Techs": n,
                    f"{selected_bc}": f"${comp_cost:,.0f}",
                    "Swivl Scale Pro": "$149",
                    "Δ": arrow,
                })
        if cost_data:
            st.dataframe(pd.DataFrame(cost_data), hide_index=True, width="stretch")

    st.divider()

    # ── Row 3: Features ─────────────────────────────────────────────────────
    st.markdown("#### 🛠️ Feature Comparison")
    feat_cols = st.columns(2)

    comp_features = c.get("features", {})
    swivl_wins_feat, they_win_feat, tied_feat = [], [], []
    for fk, label in FEATURE_LABELS.items():
        swivl_status = FEATURES.get(fk, "none")
        comp_status  = comp_features.get(fk, "none")
        s_score = {"full": 2, "partial": 1, "addon": 1, "none": 0}
        sw, cw = s_score[swivl_status], s_score[comp_status]
        row_str = f"{label}: Swivl {FEATURE_DISPLAY[swivl_status]} vs {FEATURE_DISPLAY[comp_status]}"
        if sw > cw:
            swivl_wins_feat.append(row_str)
        elif cw > sw:
            they_win_feat.append(row_str)
        else:
            tied_feat.append(row_str)

    with feat_cols[0]:
        st.markdown(f"**✅ Swivl leads ({len(swivl_wins_feat)} features)**")
        for f in swivl_wins_feat:
            st.markdown(f"• {f}")
    with feat_cols[1]:
        st.markdown(f"**⚠️ {selected_bc} leads ({len(they_win_feat)} features)**")
        for f in they_win_feat:
            st.markdown(f"• {f}")

    with st.expander(f"🤝 Tied features ({len(tied_feat)})"):
        for f in tied_feat:
            st.markdown(f"• {f}")

    st.divider()

    # ── Row 4: Voice of Customer ─────────────────────────────────────────────
    st.markdown("#### 💬 Voice of Customer")
    voc1, voc2 = st.columns(2)
    with voc1:
        st.markdown(f"**👍 What customers love about {selected_bc}**")
        for pro in c.get("top_pros", []):
            st.markdown(f"• {pro}")
    with voc2:
        st.markdown(f"**👎 What customers complain about {selected_bc}**")
        for con in c.get("top_cons", []):
            st.markdown(f"• {con}")

    st.divider()

    # ── Row 5: Sales strategy ────────────────────────────────────────────────
    st.markdown("#### 🎯 Sales Strategy")
    s1, s2 = st.columns([3, 2])
    with s1:
        st.markdown("**How to beat them**")
        st.info(c.get("how_to_beat", "—"))

        objections = c.get("objection_handling", {})
        if objections:
            st.markdown("**🛡️ Objection Handling**")
            for obj, resp in objections.items():
                with st.expander(f'"{obj}"'):
                    st.write(resp)

    with s2:
        st.markdown("**✅ Where Swivl wins**")
        for item in c.get("losses_vs_swivl", []):
            st.markdown(f"• {item}")
        st.markdown("**⚠️ Where they win**")
        for item in c.get("wins_vs_swivl", []):
            st.markdown(f"• {item}")

# ===========================================================================
# TAB 6 — PRODUCT UPDATES  (tabs[5])
# ===========================================================================
_UPDATES_FILE = Path(__file__).parent / ".tmp" / "product_updates.json"

def _load_updates() -> list:
    try:
        if _UPDATES_FILE.exists():
            return json.loads(_UPDATES_FILE.read_text())
    except Exception:
        pass
    return []

def _save_updates(updates: list):
    _UPDATES_FILE.parent.mkdir(exist_ok=True)
    _UPDATES_FILE.write_text(json.dumps(updates, indent=2))

_UPDATE_CATEGORIES = [
    "New Feature", "Pricing Change", "UI/UX Update", "Integration",
    "AI / Automation", "Funding / Acquisition", "Partnership", "Other",
]
_CAT_COLORS = {
    "New Feature":        "#DCFCE7",
    "Pricing Change":     "#FEF9C3",
    "UI/UX Update":       "#EDE9FE",
    "Integration":        "#DBEAFE",
    "AI / Automation":    "#FCE7F3",
    "Funding / Acquisition": "#FEE2E2",
    "Partnership":        "#D1FAE5",
    "Other":              "#F1F5F9",
}

with tabs[5]:
    all_updates = _load_updates()

    all_comp_names = (
        [v.get("display_name") or k for k, v in DIRECT_COMPETITORS.items()] +
        [v.get("display_name") or k for k, v in INDIRECT_COMPETITORS.items()]
    )

    # ── Add update form ──────────────────────────────────────────────────────
    with st.expander("➕ Log a new product update", expanded=not bool(all_updates)):
        with st.form("add_update_form", clear_on_submit=True):
            f1, f2 = st.columns([2, 1])
            with f1:
                comp_choice = st.selectbox("Competitor", sorted(all_comp_names))
                title = st.text_input("Update title", placeholder="e.g. Zuper launches AI Dispatch Assistant")
            with f2:
                category = st.selectbox("Category", _UPDATE_CATEGORIES)
                update_date = st.date_input("Date")

            summary = st.text_area(
                "Summary",
                placeholder="What changed? Why does it matter for Swivl?",
                height=100,
            )
            source_url = st.text_input("Source URL (optional)", placeholder="https://...")
            submitted = st.form_submit_button("Save Update", type="primary")

        if submitted:
            if title.strip() and summary.strip():
                new_entry = {
                    "competitor": comp_choice,
                    "title": title.strip(),
                    "category": category,
                    "date": str(update_date),
                    "summary": summary.strip(),
                    "source_url": source_url.strip(),
                }
                all_updates.insert(0, new_entry)
                _save_updates(all_updates)
                st.success(f"Update logged for **{comp_choice}**.")
                st.rerun()
            else:
                st.error("Title and summary are required.")

    st.divider()

    if not all_updates:
        st.info("No updates logged yet. Use the form above to track competitor product changes.")
    else:
        # ── Filters ──────────────────────────────────────────────────────────
        fc1, fc2, fc3 = st.columns([2, 2, 1])
        with fc1:
            filter_comp = st.selectbox(
                "Filter by competitor",
                ["All competitors"] + sorted({u["competitor"] for u in all_updates}),
                key="upd_filter_comp",
            )
        with fc2:
            filter_cat = st.selectbox(
                "Filter by category",
                ["All categories"] + _UPDATE_CATEGORIES,
                key="upd_filter_cat",
            )
        with fc3:
            st.markdown("<div style='margin-top:1.8rem'>", unsafe_allow_html=True)
            if st.button("🗑 Clear all", key="clear_updates"):
                _save_updates([])
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        filtered = [
            u for u in all_updates
            if (filter_comp == "All competitors" or u["competitor"] == filter_comp)
            and (filter_cat == "All categories" or u["category"] == filter_cat)
        ]

        st.caption(f"Showing {len(filtered)} of {len(all_updates)} updates")
        st.markdown("")

        for u in filtered:
            cat_color = _CAT_COLORS.get(u["category"], "#F1F5F9")
            source_md = f" &nbsp;·&nbsp; [Source ↗]({u['source_url']})" if u.get("source_url") else ""
            st.markdown(
                f"""<div style="border:1px solid #E2E8F0;border-radius:10px;padding:1rem 1.2rem;margin-bottom:.75rem;background:#fff">
  <div style="display:flex;align-items:center;gap:.6rem;margin-bottom:.4rem">
    <span style="font-weight:700;font-size:1rem">{u['competitor']}</span>
    <span style="background:{cat_color};padding:2px 10px;border-radius:20px;font-size:.75rem;font-weight:600">{u['category']}</span>
    <span style="color:#64748B;font-size:.8rem;margin-left:auto">{u['date']}{source_md}</span>
  </div>
  <div style="font-weight:600;margin-bottom:.3rem">{u['title']}</div>
  <div style="color:#475569;font-size:.9rem">{u['summary']}</div>
</div>""",
                unsafe_allow_html=True,
            )

# ===========================================================================
# TAB 7 — PAIN POINTS  (tabs[6])
# ===========================================================================
_REDDIT_FILE  = Path(__file__).parent / ".tmp" / "reddit_data.json"
_ROLE_FILE    = Path(__file__).parent / ".tmp" / "role_pain_data.json"
_PERSONA_FILE = Path(__file__).parent / ".tmp" / "fsm_all_personas.json"
_KEY_POSTS    = Path(__file__).parent / ".tmp" / "fsm_key_posts.json"

def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except Exception:
        return {}

with tabs[6]:
    st.subheader("Field Service Pain Points")
    st.caption("Synthesized from Reddit, G2, Capterra, and FSM community forums.")

    _rd   = _load_json(_REDDIT_FILE)
    _role = _load_json(_ROLE_FILE)
    _kp   = _load_json(_KEY_POSTS)

    # ── Section 1: Top Pain Categories (all competitors combined) ────────────
    st.markdown("### Top Pain Categories Across Competitors")

    _pain_summary: dict = _rd.get("pain_point_summary", {})
    _theme_summary: dict = _role.get("theme_summary", {})

    # Aggregate pain counts across all competitors
    _agg_pains: dict = {}
    for _comp, _cats in _pain_summary.items():
        for _cat, _count in _cats.items():
            _agg_pains[_cat] = _agg_pains.get(_cat, 0) + _count

    # Aggregate role themes (dispatcher + technician + both)
    _agg_themes: dict = {}
    for _role_name, _themes in _theme_summary.items():
        for _theme, _count in _themes.items():
            _agg_themes[_theme] = _agg_themes.get(_theme, 0) + _count

    _pp_col, _theme_col = st.columns(2)

    with _pp_col:
        st.markdown("**By Competitor Complaint Category** *(Reddit & review sites)*")
        if _agg_pains:
            _pain_df = pd.DataFrame(
                sorted(_agg_pains.items(), key=lambda x: -x[1]),
                columns=["Pain Category", "Mentions"],
            )
            _pain_chart = (
                alt.Chart(_pain_df)
                .mark_bar(color="#EF4444", cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("Mentions:Q", title="Mention Count"),
                    y=alt.Y("Pain Category:N", sort="-x", title=""),
                    tooltip=["Pain Category", "Mentions"],
                )
                .properties(height=280)
            )
            st.altair_chart(_pain_chart, width="stretch")
        else:
            st.info("No competitor pain data loaded yet.")

    with _theme_col:
        st.markdown("**By Workflow Theme** *(dispatcher + technician roles)*")
        if _agg_themes:
            _theme_df = pd.DataFrame(
                sorted(_agg_themes.items(), key=lambda x: -x[1])[:12],
                columns=["Theme", "Mentions"],
            )
            _theme_df["Theme"] = _theme_df["Theme"].str.replace("_", " ").str.title()
            _theme_chart = (
                alt.Chart(_theme_df)
                .mark_bar(color="#F97316", cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("Mentions:Q", title="Mention Count"),
                    y=alt.Y("Theme:N", sort="-x", title=""),
                    tooltip=["Theme", "Mentions"],
                )
                .properties(height=280)
            )
            st.altair_chart(_theme_chart, width="stretch")
        else:
            st.info("No role theme data loaded yet.")

    st.divider()

    # ── Section 2: Pain Points by Competitor ─────────────────────────────────
    st.markdown("### Pain Points by Competitor")

    _comp_pain_options = list(_pain_summary.keys()) if _pain_summary else []
    if _comp_pain_options:
        _sel_comp = st.selectbox("Select competitor", _comp_pain_options, key="pp_comp_sel")
        _comp_cats = _pain_summary.get(_sel_comp, {})
        if _comp_cats:
            _comp_df = pd.DataFrame(
                sorted(_comp_cats.items(), key=lambda x: -x[1]),
                columns=["Pain Category", "Mentions"],
            )
            _comp_chart = (
                alt.Chart(_comp_df)
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("Pain Category:N", sort="-y", title=""),
                    y=alt.Y("Mentions:Q", title="Mention Count"),
                    color=alt.Color("Pain Category:N", legend=None,
                                    scale=alt.Scale(scheme="tableau10")),
                    tooltip=["Pain Category", "Mentions"],
                )
                .properties(height=250)
            )
            st.altair_chart(_comp_chart, width="stretch")
    else:
        st.info("Run Analysis to populate competitor-specific pain data.")

    st.divider()

    # ── Section 3: Pain by Role ───────────────────────────────────────────────
    st.markdown("### Pain Points by Role")

    _role_tabs = st.tabs(["👷 Technician", "📡 Dispatcher", "🏢 Owner / Both"])

    _role_map = {
        "technician": (_role_tabs[0], "#3B82F6"),
        "dispatcher": (_role_tabs[1], "#8B5CF6"),
        "both":       (_role_tabs[2], "#10B981"),
    }

    for _rkey, (_rtab, _rcolor) in _role_map.items():
        with _rtab:
            _rthemes = _theme_summary.get(_rkey, {})
            if _rthemes:
                _role_df = pd.DataFrame(
                    sorted(_rthemes.items(), key=lambda x: -x[1])[:10],
                    columns=["Theme", "Mentions"],
                )
                _role_df["Theme"] = _role_df["Theme"].str.replace("_", " ").str.title()
                _role_chart = (
                    alt.Chart(_role_df)
                    .mark_bar(color=_rcolor, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                    .encode(
                        x=alt.X("Mentions:Q", title="Mention Count"),
                        y=alt.Y("Theme:N", sort="-x", title=""),
                        tooltip=["Theme", "Mentions"],
                    )
                    .properties(height=300)
                )
                st.altair_chart(_role_chart, width="stretch")
            else:
                st.info("No role data available.")

    st.divider()

    # ── Section 4: Key Posts from the Field ──────────────────────────────────
    st.markdown("### Real Stories from the Field")
    st.caption("Verbatim posts from Reddit and FSM forums — the exact language customers use.")

    _KEY_POST_LABELS = {
        "tech_billing_proof":    ("Customers disputing hourly charges", "🧾", "Technician"),
        "customer_service_fee":  ("Customer upset about service call fee",  "😤", "Customer"),
        "owner_cashflow_empty":  ("Owner struggling with late payments",     "💸", "Owner"),
        "owner_disputes":        ("Disputes with difficult customers",       "⚔️", "Owner"),
        "landscaping_tools":     ("Landscaper evaluating FSM tools",         "🌿", "Owner"),
        "cleaning_contract":     ("Cleaning business contract frustrations", "🧹", "Owner"),
        "double_entry_fsm":      ("Double data entry between tools",         "🔁", "Admin"),
        "servicetitan_alt":      ("Looking for ServiceTitan alternative",    "🔍", "Owner"),
    }

    if _kp:
        _kp_cols = st.columns(2)
        for _ki, (_kkey, _kpost) in enumerate(_kp.items()):
            _label_info = _KEY_POST_LABELS.get(_kkey, (_kkey.replace("_", " ").title(), "📝", "User"))
            _label, _icon, _persona = _label_info
            with _kp_cols[_ki % 2]:
                with st.expander(f"{_icon} **{_label}** — *{_persona}*"):
                    if _kpost.get("title"):
                        st.markdown(f"**Post:** {_kpost['title']}")
                    body = _kpost.get("body", "")
                    if body:
                        # Show first 600 chars
                        preview = body[:600].rstrip()
                        if len(body) > 600:
                            preview += "…"
                        st.markdown(f"> {preview}")
    else:
        st.info("No key posts loaded.")

    st.divider()

    # ── Section 5: Swivl Opportunities ───────────────────────────────────────
    st.markdown("### Swivl Opportunities from Pain Data")
    st.caption("Each pain point is a win waiting to happen — these are the highest-signal openings.")

    _opp_list  = _rd.get("swivl_opportunities", [])
    _impl_list = _role.get("swivl_implications", [])

    _opp_col, _impl_col = st.columns(2)

    with _opp_col:
        st.markdown("**📣 Messaging Opportunities** *(from competitor complaints)*")
        if _opp_list:
            for _opp in _opp_list:
                st.markdown(
                    f'<div style="border-left:3px solid #22C55E;padding:.5rem .8rem;'
                    f'margin-bottom:.5rem;background:#F0FDF4;border-radius:0 6px 6px 0;'
                    f'font-size:.88rem">{_opp}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No opportunities data yet.")

    with _impl_col:
        st.markdown("**⚡ Product Implications** *(from role pain themes)*")
        if _impl_list:
            for _impl in _impl_list[:8]:
                _theme  = _impl.get("theme", "").replace("_", " ").title() if isinstance(_impl, dict) else ""
                _audience = _impl.get("audience", "") if isinstance(_impl, dict) else ""
                _text   = _impl.get("implication", str(_impl)) if isinstance(_impl, dict) else str(_impl)
                _badge  = f'<span style="font-size:.72rem;background:#E0E7FF;color:#3730A3;padding:1px 7px;border-radius:10px;margin-right:6px">{_theme}</span>' if _theme else ""
                st.markdown(
                    f'<div style="border-left:3px solid #6366F1;padding:.5rem .8rem;'
                    f'margin-bottom:.5rem;background:#EEF2FF;border-radius:0 6px 6px 0;'
                    f'font-size:.88rem">{_badge}{_text}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No implications data yet.")

