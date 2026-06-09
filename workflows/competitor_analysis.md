# Workflow: Swivl Competitor Analysis

## Objective
Produce a bi-weekly intelligence report on Jobber, Workiz, HouseCallPro, and ServiceTitan covering pricing, recent feature releases, revenue/growth signals, G2/Capterra reviews, Reddit pain points, feature coverage matrix, and actionable gaps for Swivl.

## Required Inputs
- Python 3.9+ installed
- Dependencies installed: `pip3 install -r requirements.txt`
- (Optional) `credentials.json` for Google Doc export — see setup below

## Expected Outputs
- Live dashboard in the browser (`run.py`) — 8 tabs
- Cached JSON files in `.tmp/` (pricing, features, revenue, reviews, reddit, feature_matrix, gaps, swivl_metrics)
- Run history snapshots in `.tmp/history/`
- Google Doc with 8 tabs: Executive Summary | Jobber | Workiz | HouseCallPro | ServiceTitan | Gaps & Opportunities | Voice of Customer | Diff & History

---

## First-Time Setup

### 1. Install Python dependencies
```bash
pip3 install -r requirements.txt
```

### 2. (Optional) Set up Google Docs export

You only need to do this once. After the initial sign-in, `token.json` is cached and all future exports are one-click.

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project → **APIs & Services → Library** — enable:
   - Google Docs API
   - Google Drive API
3. **APIs & Services → OAuth consent screen** → External → add your Gmail as **Test user**
4. **Credentials → Create → OAuth 2.0 Client ID → Desktop app**
5. Download the JSON → rename to `credentials.json` → place in project root
6. On first export a browser window opens for sign-in — approve it
7. `token.json` is saved automatically; skip this step on future runs

---

## Running the Analysis

```bash
python3 -m streamlit run run.py
```

Opens the dashboard at `http://localhost:8501`.

---

## Dashboard Tabs

| Tab | What it shows |
|---|---|
| 📊 **Command Center** | Snapshot metrics, change alert badge, pricing advantage table, feature coverage bars |
| 💰 **Pricing** | Grouped bar chart (cost at 5/10/15/25/50 techs) + plan details per competitor |
| 🧩 **Feature Matrix** | 25-feature coverage grid (color-coded: green=present, red=gap, yellow=partial) |
| 🚀 **Product Updates** | Blog/RSS headlines per competitor |
| 📈 **Revenue & Funding** | Funding timeline bubble chart + revenue cards |
| 💬 **Voice of Customer** | G2/Capterra pros & cons + Reddit pain heatmap + opportunity list |
| 📅 **Diff & History** | Changes detected since last run + master run log |
| 🎯 **Gaps & Roadmap** | RAG status table + full strategic analysis + fundraising narrative |

---

## Tool Reference

| Tool | Purpose |
|---|---|
| `tools/scraper_base.py` | HTTP fetch with caching, JSON save/load helpers |
| `tools/scrape_pricing.py` | Competitor pricing pages (hardcoded + live HCP regex) |
| `tools/scrape_features.py` | Product update headlines (hardcoded + live HCP RSS) |
| `tools/scrape_revenue.py` | Hardcoded funding baselines + DuckDuckGo news |
| `tools/scrape_reviews.py` | G2/Capterra ratings + hardcoded pros/cons baselines |
| `tools/scrape_reddit.py` | old.reddit.com JSON API for FSM pain points |
| `tools/scrape_feature_matrix.py` | Hardcoded 25-feature truth table (maintained manually) |
| `tools/analyze_gaps.py` | Strategic gaps, RAG roadmap, fundraising narrative |
| `tools/swivl_metrics.py` | KPI input/storage + fundraising scorecard |
| `tools/track_history.py` | Snapshot, diff, and master summary across runs |
| `tools/google_docs_writer.py` | Creates Google Doc with 8 tabs via the Docs API |

---

## Sidebar — Swivl Metrics

The sidebar contains a **📊 Swivl Metrics** form. Enter your current KPIs here after each run:
- MRR, Logo count, User count
- Monthly churn %, NRR, CAC
- G2 rating + review count

The scorecard below the form shows RAG status against fundraising targets (NRR ≥110%, churn <10% annually, CAC payback <12 months, G2 ≥4.5★).

History is saved to `.tmp/swivl_metrics.json` (append-only).

---

## Handling Failures

### Page didn't scrape / plans not found
Most FSM sites use React — only HouseCallPro is reliably live-scrapable. If HCP scrape fails:
1. Open `housecallpro.com/pricing/` in a browser
2. Note plan names and prices
3. Update the `BASELINE` in `tools/scrape_pricing.py`

Jobber, Workiz, and ServiceTitan use hardcoded baselines — update them manually when pricing changes are announced publicly.

### Reddit rate-limited (HTTP 429)
The scraper falls back to illustrative posts automatically, labeled as `(illustrative)` in the UI. To retry live:
1. Wait 10–15 minutes
2. Enable **Force re-scrape** in the sidebar
3. Click **Run Full Analysis**

### Google export fails with auth error
Delete `token.json` from the project root and re-run — the OAuth flow restarts.

### G2 live scrape returns "hardcoded" label
G2 JS-renders review counts. The baseline data from `tools/scrape_reviews.py` is accurate as of April 2024. Update the `BASELINES` dict when ratings change significantly.

---

## Updating Baseline Data

### Revenue/funding
Update `BASELINE` in `tools/scrape_revenue.py` when major funding rounds or earnings are announced. ServiceTitan (TTAN) publishes quarterly at [investor.servicetitan.com](https://investor.servicetitan.com).

### Feature matrix
Update `FEATURES` in `tools/scrape_feature_matrix.py` when you learn a competitor has added or removed a feature. The 25-feature table is authoritative — don't rely on scraping for this.

### Review baselines
Update `BASELINES` in `tools/scrape_reviews.py` when G2/Capterra scores meaningfully change (±0.2 stars or ±100 reviews).

---

## Bi-Weekly Schedule

Recommended cadence: every two weeks on Monday morning before standup.

```bash
python3 -m streamlit run run.py
# → Click "Run Full Analysis"
# → Review Command Center for changes
# → Check Diff & History tab for what changed
# → Update Swivl Metrics in the sidebar
# → Export to Google Doc and share with the team
```
