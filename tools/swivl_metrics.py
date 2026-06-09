"""
swivl_metrics.py — Save and load Swivl's own KPI metrics.

Metrics are entered manually via the Streamlit sidebar form.
History is append-only so you can track progress run-over-run.

Schema (current):
  mrr               — Monthly Recurring Revenue ($)
  arr               — computed: mrr * 12
  user_count        — total active users / seats
  logo_count        — total paying customers (companies)
  churn_rate_monthly — monthly churn % (e.g. 2.5 for 2.5%)
  nrr               — Net Revenue Retention % (e.g. 105)
  cac               — Customer Acquisition Cost ($)
  avg_acv           — computed: arr / logo_count if both present
  g2_rating         — current G2 star rating (float)
  g2_review_count   — total G2 reviews (int)
  recorded_at       — ISO timestamp of when metrics were saved
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
TMP_DIR = ROOT_DIR / ".tmp"
TMP_DIR.mkdir(exist_ok=True)

METRICS_PATH = TMP_DIR / "swivl_metrics.json"

# Fundraising targets — used to show RAG status in scorecard
TARGETS = {
    "arr_growth_target": "3× YoY",
    "nrr_target": 110,          # %
    "churn_annual_target": 10,  # % annual (≈ 0.87% monthly)
    "cac_payback_months": 12,   # months
    "g2_rating_target": 4.5,
}


def load_swivl_metrics() -> dict:
    """Return current metrics dict (or empty shell if not yet saved)."""
    if not METRICS_PATH.exists():
        return {}
    with open(METRICS_PATH) as f:
        data = json.load(f)
    return data.get("current", {})


def save_swivl_metrics(new_metrics: dict) -> None:
    """
    Append new_metrics to history and update the 'current' snapshot.
    new_metrics should be the raw form values (no computed fields).
    """
    # Compute derived fields
    mrr = new_metrics.get("mrr") or 0
    logo_count = new_metrics.get("logo_count") or 0

    entry = {**new_metrics}
    entry["arr"] = mrr * 12
    if logo_count > 0 and entry["arr"] > 0:
        entry["avg_acv"] = round(entry["arr"] / logo_count, 2)
    else:
        entry["avg_acv"] = None
    entry["recorded_at"] = datetime.now().isoformat()

    # Load existing
    if METRICS_PATH.exists():
        with open(METRICS_PATH) as f:
            store = json.load(f)
    else:
        store = {"current": {}, "history": []}

    store["current"] = entry
    store["history"].append(entry)

    with open(METRICS_PATH, "w") as f:
        json.dump(store, f, indent=2)


def load_metrics_history() -> list[dict]:
    """Return the full history list (oldest first)."""
    if not METRICS_PATH.exists():
        return []
    with open(METRICS_PATH) as f:
        store = json.load(f)
    return store.get("history", [])


def scorecard(metrics: dict) -> list[dict]:
    """
    Return a list of scorecard rows, each with:
      metric, value, target, status (green/amber/red), note
    """
    rows = []

    def _rag(condition_green, condition_amber=None):
        if condition_green:
            return "green"
        if condition_amber and condition_amber:
            return "amber"
        return "red"

    # NRR
    nrr = metrics.get("nrr")
    if nrr is not None:
        rows.append({
            "metric": "Net Revenue Retention",
            "value": f"{nrr}%",
            "target": f"≥{TARGETS['nrr_target']}%",
            "status": _rag(nrr >= TARGETS["nrr_target"], nrr >= 100),
            "note": "Above 100% = expansion > churn",
        })

    # Monthly churn
    churn_m = metrics.get("churn_rate_monthly")
    if churn_m is not None:
        churn_annual = round(churn_m * 12, 1)
        rows.append({
            "metric": "Annual Churn (est.)",
            "value": f"~{churn_annual}%",
            "target": f"<{TARGETS['churn_annual_target']}%",
            "status": _rag(churn_annual < TARGETS["churn_annual_target"],
                           churn_annual < 20),
            "note": f"{churn_m}% monthly × 12",
        })

    # CAC payback
    cac = metrics.get("cac")
    avg_acv = metrics.get("avg_acv")
    if cac and avg_acv:
        payback_months = round(cac / (avg_acv / 12), 1)
        rows.append({
            "metric": "CAC Payback",
            "value": f"{payback_months} months",
            "target": f"<{TARGETS['cac_payback_months']} months",
            "status": _rag(payback_months <= TARGETS["cac_payback_months"],
                           payback_months <= 18),
            "note": f"CAC ${cac:,.0f} / ACV ${avg_acv:,.0f}",
        })

    # G2 rating
    g2 = metrics.get("g2_rating")
    if g2 is not None:
        rows.append({
            "metric": "G2 Rating",
            "value": f"{g2} ★",
            "target": f"≥{TARGETS['g2_rating_target']} ★",
            "status": _rag(g2 >= TARGETS["g2_rating_target"], g2 >= 4.0),
            "note": f"{metrics.get('g2_review_count', '—')} reviews",
        })

    # ARR
    arr = metrics.get("arr")
    if arr:
        rows.append({
            "metric": "ARR",
            "value": f"${arr:,.0f}",
            "target": TARGETS["arr_growth_target"],
            "status": "amber",
            "note": "Track YoY to show growth trajectory",
        })

    return rows


if __name__ == "__main__":
    # Quick smoke test
    test = {
        "mrr": 15000,
        "logo_count": 45,
        "user_count": 180,
        "churn_rate_monthly": 2.1,
        "nrr": 108,
        "cac": 800,
        "g2_rating": 4.6,
        "g2_review_count": 12,
    }
    save_swivl_metrics(test)
    loaded = load_swivl_metrics()
    print("Saved + loaded:")
    for k, v in loaded.items():
        print(f"  {k}: {v}")
    print("\nScorecard:")
    for row in scorecard(loaded):
        icon = {"green": "✓", "amber": "~", "red": "✗"}[row["status"]]
        print(f"  {icon} {row['metric']}: {row['value']} (target {row['target']}) — {row['note']}")
