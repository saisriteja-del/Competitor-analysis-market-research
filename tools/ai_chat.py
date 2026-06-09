"""Claude-powered Q&A engine over all competitor and Swivl data."""

import os
import json
from typing import Optional

try:
    import anthropic
    _CLIENT_AVAILABLE = True
except ImportError:
    _CLIENT_AVAILABLE = False

from data.swivl import COMPANY, PRICING, POSITIONING, DIFFERENTIATORS, STRENGTHS, WEAKNESSES, FEATURES
from data.competitors import (
    DIRECT_COMPETITORS, INDIRECT_COMPETITORS,
    FEATURE_LABELS, FEATURE_CATEGORIES,
    calc_monthly_cost, swivl_monthly_cost,
)

_SYSTEM_PROMPT_CACHE: Optional[str] = None


def _build_system_prompt() -> str:
    global _SYSTEM_PROMPT_CACHE
    if _SYSTEM_PROMPT_CACHE:
        return _SYSTEM_PROMPT_CACHE

    # Build pricing section
    pricing_lines = ["## Swivl Pricing (Unlimited Users)"]
    for p in PRICING["plans"]:
        ai_note = " (includes AI Receptionist)" if p.get("ai_receptionist") else ""
        pricing_lines.append(f"- {p['name']}: ${p['price']}/mo, {p['credits']} credits/mo{ai_note}")
    pricing_lines.append("\n## Credit Costs")
    for feature, info in PRICING["credit_costs"].items():
        pricing_lines.append(f"- {feature}: {info['cost']} {info['unit']}")

    # Build competitor section
    comp_lines = ["## Direct Competitors (Detailed)"]
    for name, c in DIRECT_COMPETITORS.items():
        comp_lines.append(f"\n### {name}")
        comp_lines.append(f"URL: {c['url']}")
        comp_lines.append(f"Summary: {c['one_liner']}")
        comp_lines.append(f"Threat Level: {c['threat_level']}")
        comp_lines.append(f"Pricing Model: {c['pricing_model']}")
        comp_lines.append(f"Free Tier: {'Yes' if c.get('free_tier') else 'No'}, Trial: {c.get('trial', 'None')}")
        comp_lines.append(f"G2: {c.get('g2_rating', 'N/A')}★ ({c.get('g2_reviews', 0)} reviews), Capterra: {c.get('capterra_rating', 'N/A')}★ ({c.get('capterra_reviews', 0)} reviews)")

        plans = c.get("plans", [])
        if plans:
            plan_str = " | ".join(
                f"{p['name']} ${p.get('base', '?')}" + (f"+${p.get('per_user', 0)}/user" if p.get("per_user") else "")
                for p in plans if p.get("base") is not None
            )
            comp_lines.append(f"Plans: {plan_str}")

        # TCO at 1, 5, 10, 25 users
        tco_vals = []
        for n in [1, 5, 10, 25]:
            cost = calc_monthly_cost(name, n)
            swivl = swivl_monthly_cost(n)
            if cost is not None:
                tco_vals.append(f"{n} techs: ${cost:.0f}/mo ({'+' if cost > swivl else '-'}${abs(cost-swivl):.0f} vs Swivl $149)")
        if tco_vals:
            comp_lines.append("TCO vs Swivl Scale Pro ($149 flat): " + " | ".join(tco_vals))

        comp_lines.append(f"Top Pros: {'; '.join(c.get('top_pros', []))}")
        comp_lines.append(f"Top Cons: {'; '.join(c.get('top_cons', []))}")
        comp_lines.append(f"Where Swivl wins: {'; '.join(c.get('losses_vs_swivl', []))}")
        comp_lines.append(f"Where Swivl loses: {'; '.join(c.get('wins_vs_swivl', []))}")
        comp_lines.append(f"How to beat: {c.get('how_to_beat', '')}")

        objections = c.get("objection_handling", {})
        if objections:
            comp_lines.append("Objection responses:")
            for obj, resp in objections.items():
                comp_lines.append(f'  - "{obj}": {resp}')

        ai_features = {k: v for k, v in c.get("features", {}).items() if "ai_" in k}
        has_ai = any(v == "full" or v == "partial" for v in ai_features.values())
        comp_lines.append(f"AI Features: {'None' if not has_ai else ', '.join(k for k, v in ai_features.items() if v in ('full', 'partial'))}")

    comp_lines.append("\n## Indirect Competitors")
    for name, c in INDIRECT_COMPETITORS.items():
        comp_lines.append(f"- {c['display_name']} ({c['url']}): {c['one_liner']} Threat: {c['threat_level']}. {c['key_insight']}")

    # Build differentiators section
    diff_lines = ["## Swivl Key Differentiators"]
    for d in DIFFERENTIATORS:
        diff_lines.append(f"- {d}")

    # Build SWOT
    swot_lines = [
        "\n## Strengths",
        *[f"- {s}" for s in STRENGTHS],
        "\n## Weaknesses",
        *[f"- {w}" for w in WEAKNESSES],
    ]

    system_prompt = f"""You are the Swivl competitive intelligence assistant. You help the Swivl team answer questions about competitors, positioning, and sales strategy with accuracy and confidence.

## About Swivl
{COMPANY['one_liner']}
Founded: {COMPANY['founded']}, HQ: {COMPANY['hq']}, Founder: {COMPANY['founder']}
Sales motion: {COMPANY['sales_motion']} — signups: {COMPANY['signups']}, active businesses: {COMPANY['active_businesses']}

## Positioning Pillars
{chr(10).join(f"- {p['name']}: {p['description']}" for p in POSITIONING['pillars'])}

## ICP
{POSITIONING['icp']['primary_buyer']}
Verticals: {', '.join(POSITIONING['icp']['verticals'])}
Pain points: {', '.join(POSITIONING['icp']['pain_points'])}

{chr(10).join(pricing_lines)}

{chr(10).join(diff_lines)}
{chr(10).join(swot_lines)}

{chr(10).join(comp_lines)}

## Instructions
- Answer confidently with specific data: prices, ratings, feature gaps, TCO comparisons
- When comparing pricing, always show the math (e.g., Jobber Grow at 10 techs = $490/mo vs. Swivl $149)
- Lead with Swivl's advantages — you represent Swivl's interests
- For sales questions, give direct, usable battlecard language
- For feature questions, cite specific statuses (full/partial/none/addon) from the data
- If you don't have data for something, say so clearly rather than guessing
- Keep answers concise unless the question requires depth
- Format with headers/bullets when helpful for readability"""

    _SYSTEM_PROMPT_CACHE = system_prompt
    return system_prompt


def ask_question(question: str, history: list[dict]) -> str:
    """Ask a question about competitors. Returns the assistant's response as a string."""
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not _CLIENT_AVAILABLE:
        return "The `anthropic` package is not installed. Run: `pip install anthropic>=0.25.0`"

    if not api_key:
        return (
            "**API key not configured.**\n\n"
            "To enable AI Q&A:\n"
            "1. Get an API key at [console.anthropic.com](https://console.anthropic.com)\n"
            "2. **Locally**: add `ANTHROPIC_API_KEY=sk-ant-...` to your `.env` file\n"
            "3. **Streamlit Cloud**: add it under App Settings → Secrets\n\n"
            "All other tabs work without the API key."
        )

    client = anthropic.Anthropic(api_key=api_key)

    messages = []
    for msg in history:
        if msg["role"] in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": question})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=_build_system_prompt(),
        messages=messages,
    )

    return response.content[0].text
