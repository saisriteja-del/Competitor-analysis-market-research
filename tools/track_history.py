"""
track_history.py — Snapshot, diff, and master summary for competitor analysis runs.

File layout:
  .tmp/history/{run_id}.json  — full data snapshot per run
  .tmp/latest_diff.json       — diff between last two runs
  .tmp/master_summary.json    — append-only audit log of all run summaries

Run IDs are ISO timestamps: 2024-07-15T14-32-00
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
TMP_DIR = ROOT_DIR / ".tmp"
HISTORY_DIR = TMP_DIR / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

MASTER_SUMMARY_PATH = TMP_DIR / "master_summary.json"
LATEST_DIFF_PATH = TMP_DIR / "latest_diff.json"


# ── Snapshot ───────────────────────────────────────────────────────────────────

def save_snapshot(all_data: dict) -> str:
    """
    Write a full-data snapshot to .tmp/history/{run_id}.json.
    Returns the run_id string.
    """
    run_id = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    snapshot = {
        "run_id": run_id,
        "recorded_at": datetime.now().isoformat(),
        **all_data,
    }
    path = HISTORY_DIR / f"{run_id}.json"
    with open(path, "w") as f:
        json.dump(snapshot, f, indent=2)
    return run_id


def load_previous_snapshot(exclude_run_id: str = None) -> dict | None:
    """
    Return the most recent snapshot (optionally excluding a specific run_id).
    Returns None if no prior snapshots exist.
    """
    files = sorted(HISTORY_DIR.glob("*.json"), reverse=True)
    for f in files:
        if exclude_run_id and f.stem == exclude_run_id:
            continue
        with open(f) as fp:
            return json.load(fp)
    return None


# ── Diff ───────────────────────────────────────────────────────────────────────

def _diff_pricing(current: dict, previous: dict) -> list[dict]:
    """Detect plan price changes and new/removed plans."""
    changes = []
    curr_pricing = current.get("pricing", {})
    prev_pricing = previous.get("pricing", {})

    for company in curr_pricing:
        curr_plans = {p["name"]: p["price"] for p in curr_pricing[company].get("plans", [])}
        prev_plans = {p["name"]: p["price"] for p in prev_pricing.get(company, {}).get("plans", [])}

        for plan_name, price in curr_plans.items():
            if plan_name not in prev_plans:
                changes.append({
                    "type": "new_plan",
                    "company": company,
                    "plan": plan_name,
                    "new_price": price,
                    "old_price": None,
                })
            elif price != prev_plans[plan_name]:
                changes.append({
                    "type": "price_change",
                    "company": company,
                    "plan": plan_name,
                    "old_price": prev_plans[plan_name],
                    "new_price": price,
                })

        for plan_name in prev_plans:
            if plan_name not in curr_plans:
                changes.append({
                    "type": "removed_plan",
                    "company": company,
                    "plan": plan_name,
                    "old_price": prev_plans[plan_name],
                    "new_price": None,
                })

    return changes


def _diff_reviews(current: dict, previous: dict) -> list[dict]:
    """Detect significant review count shifts (threshold: +50 reviews)."""
    changes = []
    THRESHOLD = 50
    curr_reviews = current.get("reviews", {})
    prev_reviews = previous.get("reviews", {})

    for company in curr_reviews:
        curr_count = curr_reviews[company].get("g2", {}).get("review_count", 0) or 0
        prev_count = prev_reviews.get(company, {}).get("g2", {}).get("review_count", 0) or 0
        delta = curr_count - prev_count
        if abs(delta) >= THRESHOLD:
            changes.append({
                "type": "review_surge" if delta > 0 else "review_drop",
                "company": company,
                "platform": "G2",
                "old_count": prev_count,
                "new_count": curr_count,
                "delta": delta,
            })

    return changes


def _diff_reddit(current: dict, previous: dict) -> list[dict]:
    """Detect rising pain tags (threshold: +5 posts per tag per competitor)."""
    changes = []
    THRESHOLD = 5
    curr_reddit = current.get("reddit", {})
    prev_reddit = previous.get("reddit", {})

    curr_pain = curr_reddit.get("pain_point_summary", {})
    prev_pain = prev_reddit.get("pain_point_summary", {})

    for company, tags in curr_pain.items():
        for tag, count in tags.items():
            prev_count = prev_pain.get(company, {}).get(tag, 0)
            delta = count - prev_count
            if delta >= THRESHOLD:
                changes.append({
                    "type": "rising_pain_tag",
                    "company": company,
                    "tag": tag,
                    "old_count": prev_count,
                    "new_count": count,
                    "delta": delta,
                })

    return changes


def _diff_features(current: dict, previous: dict) -> list[dict]:
    """Detect feature matrix changes."""
    changes = []
    curr_matrix = {r["feature"]: r for r in current.get("feature_matrix", {}).get("features", [])}
    prev_matrix = {r["feature"]: r for r in previous.get("feature_matrix", {}).get("features", [])}

    for feature, curr_row in curr_matrix.items():
        if feature not in prev_matrix:
            continue
        prev_row = prev_matrix[feature]
        for company in ["Swivl", "Jobber", "Workiz", "HouseCallPro", "ServiceTitan"]:
            if curr_row.get(company) != prev_row.get(company):
                changes.append({
                    "type": "feature_change",
                    "company": company,
                    "feature": feature,
                    "old_value": prev_row.get(company),
                    "new_value": curr_row.get(company),
                })

    return changes


def compute_diff(current: dict, previous: dict) -> dict:
    """
    Compare two full-data dicts and return a structured diff.
    """
    pricing_changes = _diff_pricing(current, previous)
    review_changes = _diff_reviews(current, previous)
    reddit_changes = _diff_reddit(current, previous)
    feature_changes = _diff_features(current, previous)

    all_changes = pricing_changes + review_changes + reddit_changes + feature_changes

    diff = {
        "computed_at": datetime.now().isoformat(),
        "current_run_id": current.get("run_id", "unknown"),
        "previous_run_id": previous.get("run_id", "unknown"),
        "total_changes": len(all_changes),
        "pricing_changes": pricing_changes,
        "review_changes": review_changes,
        "reddit_changes": reddit_changes,
        "feature_changes": feature_changes,
        "summary": _diff_summary(all_changes),
    }

    with open(LATEST_DIFF_PATH, "w") as f:
        json.dump(diff, f, indent=2)

    return diff


def _diff_summary(changes: list[dict]) -> list[str]:
    lines = []
    for c in changes:
        t = c["type"]
        if t == "price_change":
            lines.append(f"{c['company']} — {c['plan']}: {c['old_price']} → {c['new_price']}")
        elif t == "new_plan":
            lines.append(f"{c['company']} — new plan added: {c['plan']} at {c['new_price']}")
        elif t == "removed_plan":
            lines.append(f"{c['company']} — plan removed: {c['plan']} (was {c['old_price']})")
        elif t == "review_surge":
            lines.append(f"{c['company']} G2 review surge: +{c['delta']} reviews ({c['old_count']} → {c['new_count']})")
        elif t == "review_drop":
            lines.append(f"{c['company']} G2 reviews dropped: {c['delta']} ({c['old_count']} → {c['new_count']})")
        elif t == "rising_pain_tag":
            lines.append(f"{c['company']} — Reddit '{c['tag']}' pain rising: +{c['delta']} posts")
        elif t == "feature_change":
            old = "✓" if c["old_value"] is True else ("~" if c["old_value"] == "partial" else "✗")
            new = "✓" if c["new_value"] is True else ("~" if c["new_value"] == "partial" else "✗")
            lines.append(f"{c['company']} — '{c['feature']}' changed: {old} → {new}")
    return lines


# ── Master summary ─────────────────────────────────────────────────────────────

def update_master_summary(run_id: str, diff: dict) -> None:
    """Append a run entry to the append-only master summary log."""
    if MASTER_SUMMARY_PATH.exists():
        with open(MASTER_SUMMARY_PATH) as f:
            store = json.load(f)
    else:
        store = {"runs": []}

    store["runs"].append({
        "run_id": run_id,
        "recorded_at": datetime.now().isoformat(),
        "total_changes": diff.get("total_changes", 0),
        "summary": diff.get("summary", []),
    })

    with open(MASTER_SUMMARY_PATH, "w") as f:
        json.dump(store, f, indent=2)


def load_master_summary() -> dict:
    if not MASTER_SUMMARY_PATH.exists():
        return {"runs": []}
    with open(MASTER_SUMMARY_PATH) as f:
        return json.load(f)


def load_latest_diff() -> dict | None:
    if not LATEST_DIFF_PATH.exists():
        return None
    with open(LATEST_DIFF_PATH) as f:
        return json.load(f)


# ── Full pipeline helper ───────────────────────────────────────────────────────

def run_history_pipeline(all_data: dict) -> tuple[str, dict | None]:
    """
    Convenience function called by run.py after analysis completes.
    1. Load previous snapshot
    2. Save current snapshot
    3. Compute diff (if previous exists)
    4. Update master summary
    Returns (run_id, diff_or_None).
    """
    previous = load_previous_snapshot()
    run_id = save_snapshot(all_data)

    diff = None
    if previous:
        # reload current snapshot to get the run_id embedded
        current = all_data.copy()
        current["run_id"] = run_id
        diff = compute_diff(current, previous)
        update_master_summary(run_id, diff)
    else:
        # First ever run — write empty diff
        diff = {
            "computed_at": datetime.now().isoformat(),
            "current_run_id": run_id,
            "previous_run_id": None,
            "total_changes": 0,
            "pricing_changes": [],
            "review_changes": [],
            "reddit_changes": [],
            "feature_changes": [],
            "summary": ["First run — no previous snapshot to compare against."],
        }
        with open(LATEST_DIFF_PATH, "w") as fp:
            json.dump(diff, fp, indent=2)
        update_master_summary(run_id, diff)

    return run_id, diff


if __name__ == "__main__":
    # Smoke test
    test_data = {
        "pricing": {
            "Jobber": {"plans": [{"name": "Core", "price": "$49/user/mo"}]},
        },
        "reviews": {},
        "reddit": {},
        "feature_matrix": {},
    }
    run_id, diff = run_history_pipeline(test_data)
    print(f"Run ID: {run_id}")
    if diff:
        print(f"Changes: {diff['total_changes']}")
        for s in diff["summary"]:
            print(f"  • {s}")
    summary = load_master_summary()
    print(f"\nMaster summary: {len(summary['runs'])} run(s) logged")
