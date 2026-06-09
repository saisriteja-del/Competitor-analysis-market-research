"""
google_docs_writer.py — Create a Google Doc with tabs for each competitor run.

Tab layout (Google Docs 2024 tabs feature):
  1. Executive Summary
  2. Jobber
  3. Workiz
  4. HouseCallPro
  5. ServiceTitan
  6. Gaps & Opportunities

OAuth credentials must be in credentials.json at the project root.
Run once interactively; token.json is cached for subsequent headless runs.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    raise SystemExit(
        "Google client libraries not installed.\n"
        "Run:  pip install google-auth google-auth-oauthlib google-api-python-client"
    )

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]

CREDS_PATH = ROOT_DIR / "credentials.json"
TOKEN_PATH = ROOT_DIR / "token.json"


# ── Auth ───────────────────────────────────────────────────────────────────────

def authenticate():
    """Return an authenticated Google Docs service client."""
    if not CREDS_PATH.exists():
        raise FileNotFoundError(
            "credentials.json not found in project root.\n\n"
            "Setup steps:\n"
            "  1. Go to https://console.cloud.google.com\n"
            "  2. Create a project → APIs & Services → Enable:\n"
            "       • Google Docs API\n"
            "       • Google Drive API\n"
            "  3. OAuth consent screen → External → add your Gmail as test user\n"
            "  4. Credentials → Create → OAuth 2.0 Client ID → Desktop app\n"
            "  5. Download JSON → rename to credentials.json → place in project root\n"
            "  6. Re-run this export"
        )

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())

    return build("docs", "v1", credentials=creds)


# ── Low-level Docs API helpers ─────────────────────────────────────────────────

def _batch(service, doc_id: str, requests: list) -> dict:
    return (
        service.documents()
        .batchUpdate(documentId=doc_id, body={"requests": requests})
        .execute()
    )


def _create_tab(service, doc_id: str, title: str) -> str:
    """Create a new tab and return its tabId."""
    resp = _batch(service, doc_id, [
        {"createTab": {"tab": {"tabProperties": {"title": title}}}}
    ])
    replies = resp.get("replies", [{}])
    tab_props = replies[0].get("createTab", {}).get("tab", {}).get("tabProperties", {})
    return tab_props.get("tabId", "")


def _write_to_tab(service, doc_id: str, tab_id: str, text: str) -> None:
    """Insert text at index 1 of the given tab."""
    if not text:
        return
    _batch(service, doc_id, [
        {
            "insertText": {
                "location": {"index": 1, "tabId": tab_id},
                "text": text,
            }
        }
    ])


def _get_default_tab_id(service, doc_id: str) -> str:
    doc = service.documents().get(documentId=doc_id).execute()
    tabs = doc.get("tabs", [])
    if tabs:
        return tabs[0].get("tabProperties", {}).get("tabId", "")
    return ""


def _rename_tab(service, doc_id: str, tab_id: str, title: str) -> None:
    try:
        _batch(service, doc_id, [
            {
                "updateTabProperties": {
                    "tabProperties": {"tabId": tab_id, "title": title},
                    "fields": "title",
                }
            }
        ])
    except HttpError:
        pass  # not critical if rename fails


# ── Content builders ───────────────────────────────────────────────────────────

def _summary_text(data: dict, run_date: str) -> str:
    pricing = data.get("pricing", {})
    gaps = data.get("gaps", {})

    lines = [
        f"SWIVL COMPETITOR INTELLIGENCE REPORT\n",
        f"Generated: {run_date}\n",
        f"Competitors tracked: Jobber | Workiz | HouseCallPro | ServiceTitan\n\n",
        "━━━ KEY SWIVL ADVANTAGE ━━━\n\n",
        "Swivl charges a flat monthly rate with unlimited users. Every competitor\n"
        "charges per technician. At 15+ techs, Swivl is typically 3–5× cheaper.\n\n",
        "━━━ PRICING SNAPSHOT ━━━\n\n",
    ]

    for name, info in pricing.items():
        plans = info.get("plans", [])
        plan_summary = f"{len(plans)} plans found" if plans else "Not publicly listed"
        lines.append(f"  {name}: {plan_summary}  |  Per-user: {info.get('per_user', '—')}\n")

    lines.append("\n━━━ TOP OPPORTUNITIES ━━━\n\n")
    for opp in gaps.get("opportunities", [])[:6]:
        lines.append(f"  → {opp}\n")

    lines.append("\n━━━ SWIVL STRENGTHS ━━━\n\n")
    for adv in gaps.get("swivl_advantages", []):
        lines.append(f"  ✓ {adv}\n")

    return "".join(lines)


def _competitor_text(name: str, data: dict) -> str:
    pricing = data.get("pricing", {}).get(name, {})
    features = data.get("features", {}).get(name, {})
    revenue = data.get("revenue", {}).get(name, {})

    lines = [f"{name.upper()} — COMPETITOR PROFILE\n\n"]

    # Pricing
    lines.append("━━━ PRICING ━━━\n\n")
    plans = pricing.get("plans", [])
    if plans:
        for p in plans:
            lines.append(f"  {p['name']}: {p['price']}\n")
    else:
        lines.append("  Plans not found — verify at source URL\n")
    lines.append(f"  Per-user pricing: {pricing.get('per_user', '—')}\n")
    lines.append(f"  Source: {pricing.get('url', '')}\n")
    if pricing.get("note"):
        lines.append(f"  Note: {pricing['note']}\n")

    # Recent Features
    lines.append("\n━━━ RECENT FEATURES & UPDATES ━━━\n\n")
    updates = features.get("updates", [])
    if updates:
        for u in updates[:10]:
            lines.append(f"  • {u}\n")
    else:
        lines.append("  No updates scraped — check source URL\n")
    lines.append(f"  Source: {features.get('url', '')}\n")

    # Revenue & Growth
    lines.append("\n━━━ REVENUE & GROWTH ━━━\n\n")
    lines.append(f"  Status:           {revenue.get('status', '—')}\n")
    lines.append(f"  Estimated Revenue:{revenue.get('estimated_revenue', '—')}\n")
    lines.append(f"  Total Raised:     {revenue.get('total_raised', '—')}\n")
    lines.append(f"  Last Funding:     {revenue.get('last_funding', '—')}\n")
    lines.append(f"  Employees:        {revenue.get('employees', '—')}\n")
    lines.append(f"  G2 Rating:        {revenue.get('g2_rating', '—')} ({revenue.get('g2_reviews', '—')} reviews)\n")
    lines.append(f"  HQ:               {revenue.get('hq', '—')}\n")
    lines.append(f"  Founded:          {revenue.get('founded', '—')}\n")
    if revenue.get("notes"):
        lines.append(f"  Context:          {revenue['notes']}\n")

    news = revenue.get("recent_news", [])
    if news:
        lines.append("\n  Recent News:\n")
        for item in news:
            lines.append(f"    — {item}\n")

    return "".join(lines)


def _gaps_text(data: dict) -> str:
    gaps = data.get("gaps", {})
    lines = ["GAPS & OPPORTUNITIES — SWIVL FUNDRAISING ANALYSIS\n\n"]

    # Strategic Position
    pos = gaps.get("strategic_position", {})
    if pos:
        lines.append("━━━ STRATEGIC POSITION ━━━\n\n")
        lines.append(f"  {pos.get('summary', '')}\n\n")
        lines.append(f"  Target Wedge: {pos.get('target_wedge', '')}\n")
        lines.append(f"  Market Signal: {pos.get('market_signal', '')}\n")
        lines.append(f"  Swivl Angle: {pos.get('swivl_angle', '')}\n\n")

    # Fundraising Narrative
    narrative = gaps.get("fundraising_narrative", {})
    if narrative:
        lines.append("━━━ FUNDRAISING NARRATIVE ━━━\n\n")
        lines.append(f"  Headline: {narrative.get('headline', '')}\n\n")
        lines.append(f"  Market: {narrative.get('market_size', '')}\n\n")
        lines.append("  Why Now:\n")
        for w in narrative.get("why_now", []):
            lines.append(f"    • {w}\n")
        lines.append(f"\n  The Ask: {narrative.get('the_ask', '')}\n\n")
        lines.append("  Proof Points to Build:\n")
        for p in narrative.get("proof_points_to_build", []):
            lines.append(f"    • {p}\n")
        lines.append("\n")

    # Feature Roadmap
    roadmap = gaps.get("feature_roadmap", {})
    if roadmap:
        lines.append("━━━ FEATURE BUILD ROADMAP ━━━\n\n")
        for tier_key in ["tier_1", "tier_2", "tier_3"]:
            tier = roadmap.get(tier_key, {})
            if not tier:
                continue
            lines.append(f"{tier.get('label', '')}\n")
            lines.append(f"  {tier.get('rationale', '')}\n\n")
            for item in tier.get("items", []):
                lines.append(f"  ► {item['feature']}\n")
                lines.append(f"    Why: {item['why']}\n")
                lines.append(f"    Competitor gap: {item.get('competitor_gap', '')}\n")
                lines.append(f"    Fundraising impact: {item.get('fundraising_impact', '')}\n")
                if item.get("build_suggestion"):
                    lines.append(f"    How to build: {item['build_suggestion']}\n")
                lines.append("\n")

    # Swivl Advantages
    lines.append("━━━ SWIVL DEFENSIBLE ADVANTAGES ━━━\n\n")
    for adv in gaps.get("swivl_advantages", []):
        lines.append(f"  ✓ {adv}\n")

    # Pricing
    lines.append(f"\n━━━ PRICING ANALYSIS ━━━\n\n  {gaps.get('pricing_analysis', '')}\n\n")

    # GTM Gaps
    gtm = gaps.get("gtm_gaps", [])
    if gtm:
        lines.append("━━━ GO-TO-MARKET GAPS ━━━\n\n")
        for g in gtm:
            lines.append(f"  {g['gap']}\n")
            lines.append(f"    {g['detail']}\n")
            lines.append(f"    Action: {g['action']}\n\n")

    # Metrics
    metrics = gaps.get("metrics_to_build", [])
    if metrics:
        lines.append("━━━ METRICS TO BUILD TOWARD ━━━\n\n")
        for m in metrics:
            lines.append(f"  {m['metric']}: {m['target']}\n")
            lines.append(f"    {m['why']}\n\n")

    # Competitor weaknesses
    lines.append("━━━ COMPETITOR WEAKNESSES TO EXPLOIT ━━━\n\n")
    for name, weaknesses in gaps.get("competitor_weaknesses", {}).items():
        lines.append(f"  {name}:\n")
        for w in weaknesses:
            lines.append(f"    • {w}\n")

    return "".join(lines)


# ── Main export function ───────────────────────────────────────────────────────

def _reviews_text(data: dict) -> str:
    reviews = data.get("reviews", {})
    reddit = data.get("reddit", {})
    lines = ["VOICE OF CUSTOMER — G2, CAPTERRA & REDDIT\n\n"]

    for name in ["Jobber", "Workiz", "HouseCallPro", "ServiceTitan"]:
        info = reviews.get(name, {})
        g2 = info.get("g2", {})
        cap = info.get("capterra", {})

        lines.append(f"━━━ {name.upper()} ━━━\n\n")

        lines.append(f"  G2: {g2.get('rating', '—')}★  ({g2.get('review_count', '—')} reviews)\n")
        lines.append("  Top Pros:\n")
        for p in g2.get("top_pros", [])[:5]:
            lines.append(f"    + {p}\n")
        lines.append("  Top Cons:\n")
        for c in g2.get("top_cons", [])[:5]:
            lines.append(f"    − {c}\n")
        lines.append(f"  Source: {g2.get('url', '')}\n\n")

        lines.append(f"  Capterra: {cap.get('rating', '—')}★  ({cap.get('review_count', '—')} reviews)\n")
        for c in cap.get("top_cons", [])[:3]:
            lines.append(f"    − {c}\n")
        lines.append("\n")

    # Reddit pain summary
    pain = reddit.get("pain_point_summary", {})
    if pain:
        lines.append("━━━ REDDIT PAIN POINT SUMMARY ━━━\n\n")
        for comp, tags in pain.items():
            if tags:
                tag_str = "  |  ".join(f"{t}: {n}" for t, n in tags.items())
                lines.append(f"  {comp}: {tag_str}\n")

    opps = reddit.get("swivl_opportunities", [])
    if opps:
        lines.append("\n━━━ SWIVL OPPORTUNITIES FROM REDDIT ━━━\n\n")
        for opp in opps:
            lines.append(f"  → {opp}\n")

    return "".join(lines)


def _diff_text(data: dict) -> str:
    diff = data.get("diff", {})
    lines = ["DIFF & HISTORY — CHANGES SINCE LAST RUN\n\n"]

    lines.append(f"  Run ID:       {diff.get('current_run_id', '—')}\n")
    lines.append(f"  Previous run: {diff.get('previous_run_id', 'First run')}\n")
    lines.append(f"  Computed at:  {diff.get('computed_at', '—')}\n")
    lines.append(f"  Total changes: {diff.get('total_changes', 0)}\n\n")

    summary = diff.get("summary", [])
    if summary:
        lines.append("━━━ CHANGE SUMMARY ━━━\n\n")
        for s in summary:
            lines.append(f"  • {s}\n")
    else:
        lines.append("  No changes detected since last run.\n")

    for section_key, section_label in [
        ("pricing_changes", "PRICING CHANGES"),
        ("review_changes", "REVIEW COUNT CHANGES"),
        ("reddit_changes", "REDDIT PAIN SHIFTS"),
        ("feature_changes", "FEATURE MATRIX CHANGES"),
    ]:
        items = diff.get(section_key, [])
        if items:
            lines.append(f"\n━━━ {section_label} ━━━\n\n")
            for item in items:
                lines.append(f"  {item}\n")

    return "".join(lines)


def create_competitor_doc(data: dict) -> str:
    """
    Create a Google Doc with eight tabs and populate each with analysis data.
    Returns the URL of the created document.
    """
    service = authenticate()

    run_date = datetime.now().strftime("%B %d, %Y")
    title = f"Swivl Competitor Analysis — {run_date}"

    # Create doc
    doc = service.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]
    print(f"  Doc created: {doc_id}")

    # Rename the default tab to "Executive Summary"
    default_tab_id = _get_default_tab_id(service, doc_id)
    if default_tab_id:
        _rename_tab(service, doc_id, default_tab_id, "Executive Summary")

    # Create remaining tabs
    tab_ids: dict[str, str] = {"Executive Summary": default_tab_id}
    for tab_name in [
        "Jobber", "Workiz", "HouseCallPro",
        "Gaps & Opportunities", "Voice of Customer", "Diff & History",
    ]:
        print(f"  Creating tab: {tab_name}")
        tab_id = _create_tab(service, doc_id, tab_name)
        if tab_id:
            tab_ids[tab_name] = tab_id

    # Build content map
    content: dict[str, str] = {
        "Executive Summary": _summary_text(data, run_date),
        "Jobber": _competitor_text("Jobber", data),
        "Workiz": _competitor_text("Workiz", data),
        "HouseCallPro": _competitor_text("HouseCallPro", data),
        "Gaps & Opportunities": _gaps_text(data),
        "Voice of Customer": _reviews_text(data),
        "Diff & History": _diff_text(data),
    }

    # Write content to each tab
    for tab_name, text in content.items():
        tab_id = tab_ids.get(tab_name)
        if tab_id and text:
            print(f"  Writing → {tab_name}")
            try:
                _write_to_tab(service, doc_id, tab_id, text)
            except HttpError as e:
                print(f"  Warning: could not write to '{tab_name}': {e}")

    url = f"https://docs.google.com/document/d/{doc_id}/edit"
    print(f"\n  ✓ Report ready: {url}")
    return url


if __name__ == "__main__":
    # Quick test with cached data
    sys.path.insert(0, str(ROOT_DIR / "tools"))
    from scraper_base import load_json

    test_data = {
        "pricing": load_json("pricing_data.json") or {},
        "features": load_json("features_data.json") or {},
        "revenue": load_json("revenue_data.json") or {},
        "gaps": load_json("gaps_data.json") or {},
    }
    url = create_competitor_doc(test_data)
    print(f"Document URL: {url}")
