"""Swivl Competitor Analysis Dashboard — 6-tab Streamlit app."""

import os
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
    DIRECT_COMPETITORS, INDIRECT_COMPETITORS,
    FEATURE_LABELS, FEATURE_CATEGORIES,
    calc_monthly_cost, swivl_monthly_cost,
)
from tools.ai_chat import ask_question

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
THREAT_ORDER = {"high": 0, "medium": 1, "low": 2, "none": 3}
FEATURE_DISPLAY = {"full": "✅ Full", "partial": "⚠️ Partial", "none": "❌ None", "addon": "🔒 Add-on"}
THREAT_BADGE = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low", "none": "⚪ None"}

def kpi(value, label):
    return f'<div class="kpi-card"><p class="kpi-value">{value}</p><p class="kpi-label">{label}</p></div>'

# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------
st.title("🔍 Competitor Analysis")
st.caption("Swivl competitive intelligence — updated June 2026")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tabs = st.tabs([
    "📊 Overview",
    "🛠️ Feature Matrix",
    "💰 Pricing",
    "💬 Voice of Customer",
    "🎯 Battlecards",
    "🤖 Ask Anything",
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
        st.markdown(kpi(f"{no_ai}/10", "Competitors Without AI"), unsafe_allow_html=True)

    st.divider()

    st.subheader("Pricing vs. AI Capability (10-technician team)")

    bubble_rows = []
    swivl_ai = sum(1 for k, v in FEATURES.items() if "ai_" in k and v == "full")
    bubble_rows.append({
        "name": "Swivl",
        "monthly_cost": swivl_monthly_cost(10),
        "ai_features": swivl_ai,
        "threat": "swivl",
        "type": "Swivl",
    })
    for name, c in DIRECT_COMPETITORS.items():
        cost = calc_monthly_cost(name, 10)
        ai_count = sum(1 for k, v in c.get("features", {}).items() if "ai_" in k and v in ("full", "partial"))
        bubble_rows.append({
            "name": name,
            "monthly_cost": cost if cost is not None else 0,
            "ai_features": ai_count,
            "threat": c.get("threat_level", "low"),
            "type": "Direct",
        })

    bubble_df = pd.DataFrame(bubble_rows)
    color_scale = alt.Scale(
        domain=["swivl", "high", "medium", "low"],
        range=["#0068C9", "#DC2626", "#D97706", "#16A34A"],
    )
    chart = (
        alt.Chart(bubble_df)
        .mark_circle(opacity=0.85)
        .encode(
            x=alt.X("monthly_cost:Q", title="Monthly Cost at 10 Techs ($)", scale=alt.Scale(zero=True)),
            y=alt.Y("ai_features:Q", title="Native AI Features", scale=alt.Scale(zero=True)),
            size=alt.value(260),
            color=alt.Color("threat:N", scale=color_scale, legend=alt.Legend(title="Threat")),
            tooltip=["name", "monthly_cost", "ai_features", "threat"],
        )
        .properties(height=340)
    )
    labels = (
        alt.Chart(bubble_df)
        .mark_text(dy=-14, fontSize=11, fontWeight="bold")
        .encode(
            x="monthly_cost:Q",
            y="ai_features:Q",
            text="name:N",
        )
    )
    st.altair_chart((chart + labels).interactive(), use_container_width=True)

    st.divider()

    col_left, col_right = st.columns([3, 2])
    with col_left:
        st.subheader("Competitive Threat Ranking")
        sorted_comps = sorted(
            DIRECT_COMPETITORS.items(),
            key=lambda x: THREAT_ORDER.get(x[1].get("threat_level", "low"), 3),
        )
        rows = []
        for name, c in sorted_comps:
            rows.append({
                "Competitor": name,
                "Threat": THREAT_BADGE.get(c.get("threat_level", "low"), ""),
                "Pricing Model": c.get("pricing_model", "").replace("_", " ").title(),
                "Free Tier": "✅" if c.get("free_tier") else "❌",
                "Has AI": "✅" if any(v != "none" for k, v in c.get("features", {}).items() if "ai_" in k) else "❌",
                "G2 ★": c.get("g2_rating", "N/A"),
            })
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    with col_right:
        st.subheader("Swivl Differentiators")
        for d in DIFFERENTIATORS:
            st.markdown(f"• {d}")

# ===========================================================================
# TAB 2 — FEATURE MATRIX
# ===========================================================================
with tabs[1]:
    st.subheader("Feature Comparison Matrix")

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

    styled = matrix_df.style.applymap(style_cell, subset=["Swivl"] + comp_names)
    st.dataframe(styled, hide_index=True, use_container_width=True, height=600)
    st.caption("✅ Full  ⚠️ Partial  ❌ None  🔒 Add-on")

# ===========================================================================
# TAB 3 — PRICING
# ===========================================================================
with tabs[2]:
    st.subheader("Monthly Cost Comparison")

    num_techs = st.slider("Team size (technicians)", min_value=1, max_value=50, value=10, step=1)

    pricing_rows = [{"Competitor": "Swivl (Scale Pro)", "Monthly Cost": swivl_monthly_cost(num_techs), "Color": "swivl"}]
    for name, c in DIRECT_COMPETITORS.items():
        cost = calc_monthly_cost(name, num_techs)
        if cost is not None:
            pricing_rows.append({"Competitor": name, "Monthly Cost": cost, "Color": c.get("threat_level", "low")})

    pricing_df = pd.DataFrame(pricing_rows).sort_values("Monthly Cost")

    color_scale2 = alt.Scale(
        domain=["swivl", "high", "medium", "low"],
        range=["#0068C9", "#DC2626", "#D97706", "#16A34A"],
    )
    bar_chart = (
        alt.Chart(pricing_df)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            y=alt.Y("Competitor:N", sort="-x", title=None),
            x=alt.X("Monthly Cost:Q", title="Monthly Cost ($)"),
            color=alt.Color("Color:N", scale=color_scale2, legend=None),
            tooltip=["Competitor", "Monthly Cost"],
        )
        .properties(height=max(280, len(pricing_rows) * 36))
    )
    text_labels = (
        alt.Chart(pricing_df)
        .mark_text(align="left", dx=4, fontWeight="bold")
        .encode(
            y=alt.Y("Competitor:N", sort="-x"),
            x="Monthly Cost:Q",
            text=alt.Text("Monthly Cost:Q", format="$,.0f"),
        )
    )
    st.altair_chart((bar_chart + text_labels).interactive(), use_container_width=True)

    swivl_cost = swivl_monthly_cost(num_techs)
    top_threat = next(
        (name for name, c in sorted(
            DIRECT_COMPETITORS.items(),
            key=lambda x: THREAT_ORDER.get(x[1].get("threat_level"), 3),
        ) if calc_monthly_cost(name, num_techs) is not None),
        None,
    )
    if top_threat:
        rival_cost = calc_monthly_cost(top_threat, num_techs)
        if rival_cost and rival_cost > swivl_cost:
            savings = rival_cost - swivl_cost
            st.success(
                f"**Swivl saves ${savings:,.0f}/mo vs. {top_threat}** at {num_techs} technicians — "
                f"that's **${savings * 12:,.0f}/year**."
            )

    st.divider()
    st.subheader("Swivl Plan Details")
    plan_rows = []
    for p in PRICING["plans"]:
        plan_rows.append({
            "Plan": p["name"],
            "Price": f"${p['price']}/mo",
            "Credits": f"{p['credits']:,}",
            "AI Receptionist": "✅" if p.get("ai_receptionist") else "❌",
            "Trial": p.get("trial") or "—",
        })
    st.dataframe(pd.DataFrame(plan_rows), hide_index=True, use_container_width=True)

    with st.expander("View all competitor plan details"):
        for name, c in DIRECT_COMPETITORS.items():
            plans = [p for p in c.get("plans", []) if p.get("base") is not None]
            if not plans:
                continue
            st.markdown(f"**{name}** — {c.get('pricing_model', '').replace('_', ' ').title()}")
            rows = []
            for p in plans:
                base = f"${p['base']}/mo"
                per_user = f"+${p['per_user']}/user" if p.get("per_user") else "Unlimited"
                rows.append({"Plan": p["name"], "Base": base, "Per User": per_user, "Note": p.get("note", "")})
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

# ===========================================================================
# TAB 4 — VOICE OF CUSTOMER
# ===========================================================================
with tabs[3]:
    st.subheader("Voice of Customer — Reviews & Ratings")

    selected_comp = st.selectbox("Select competitor", list(DIRECT_COMPETITORS.keys()), key="voc_comp")
    c = DIRECT_COMPETITORS[selected_comp]

    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        st.metric("G2 Rating", f"{c.get('g2_rating', 'N/A')}★", f"{c.get('g2_reviews', 0):,} reviews")
    with rc2:
        st.metric("Capterra Rating", f"{c.get('capterra_rating', 'N/A')}★", f"{c.get('capterra_reviews', 0):,} reviews")
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
    st.subheader("One-Page Competitive Battlecards")

    selected_bc = st.selectbox("Select competitor", list(DIRECT_COMPETITORS.keys()), key="bc_comp")
    c = DIRECT_COMPETITORS[selected_bc]

    bc1, bc2 = st.columns([2, 1])
    with bc1:
        st.markdown(f"### {selected_bc}")
        st.caption(c.get("one_liner", ""))

        st.markdown("**🎯 How to Beat**")
        st.info(c.get("how_to_beat", "No battlecard data yet."))

        objections = c.get("objection_handling", {})
        if objections:
            st.markdown("**🛡️ Objection Handling**")
            for obj, resp in objections.items():
                with st.expander(f'"{obj}"'):
                    st.write(resp)

    with bc2:
        st.markdown("**📊 Quick Stats**")
        st.markdown(f"- Founded: {c.get('founded', 'N/A')}")
        st.markdown(f"- Funding: {c.get('funding', 'N/A')}")
        st.markdown(f"- Team Size: {c.get('team_size', 'N/A')}")
        st.markdown(f"- Threat: {THREAT_BADGE.get(c.get('threat_level', 'low'), '')}")
        st.markdown(f"- G2: {c.get('g2_rating', 'N/A')}★  |  Capterra: {c.get('capterra_rating', 'N/A')}★")
        st.markdown(f"- Free Tier: {'Yes' if c.get('free_tier') else 'No'}")
        st.markdown(f"- Trial: {c.get('trial', 'None')}")

        cost_10 = calc_monthly_cost(selected_bc, 10)
        if cost_10:
            diff = cost_10 - swivl_monthly_cost(10)
            sign = "+" if diff > 0 else ""
            st.markdown(f"- 10-tech cost: **${cost_10:.0f}/mo** ({sign}${diff:.0f} vs Swivl)")

        st.divider()
        st.markdown("**Where Swivl Wins**")
        for item in c.get("losses_vs_swivl", []):
            st.markdown(f"✅ {item}")

        st.divider()
        st.markdown("**Where They Win**")
        for item in c.get("wins_vs_swivl", []):
            st.markdown(f"⚠️ {item}")

# ===========================================================================
# TAB 6 — ASK ANYTHING
# ===========================================================================
with tabs[5]:
    st.subheader("🤖 Ask Anything")
    st.caption("AI-powered Q&A backed by Claude — ask about pricing, features, objections, or anything else.")

    api_key_present = bool(os.getenv("ANTHROPIC_API_KEY"))
    if not api_key_present:
        st.warning(
            "**API key not set.** Add `ANTHROPIC_API_KEY` to your `.env` (local) or "
            "Streamlit Cloud secrets to enable AI Q&A. All other tabs work without it."
        )

    examples = [
        "How does Swivl pricing compare to Jobber for 10 techs?",
        "What's the best objection response when a prospect says 'We use HousecallPro'?",
        "Which competitors have AI features?",
        "What are Swivl's biggest weaknesses?",
        "How do we beat ServiceTitan in a deal?",
        "What does ServiceFusion offer vs. Swivl?",
    ]

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.markdown("**Example questions:**")
    ex_cols = st.columns(3)
    for i, ex in enumerate(examples):
        with ex_cols[i % 3]:
            if st.button(ex, key=f"ex_{i}", use_container_width=True, disabled=not api_key_present):
                st.session_state.chat_history.append({"role": "user", "content": ex})
                with st.spinner("Thinking..."):
                    reply = ask_question(ex, st.session_state.chat_history[:-1])
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                st.rerun()

    st.divider()

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask a competitor question...", disabled=not api_key_present):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = ask_question(prompt, st.session_state.chat_history[:-1])
            st.markdown(reply)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})

    if st.session_state.chat_history:
        if st.button("🗑️ Clear chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()
