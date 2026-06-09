# Swivl Competitor Intelligence — Team Guide

A live Streamlit dashboard tracking Jobber, Workiz, and HouseCallPro across pricing, features, reviews, Reddit sentiment, and strategic gaps.

---

## Quick Start (Anyone on Your Machine / Local Network)

### Step 1 — First time only

Open Terminal, navigate to this folder:

```bash
cd ~/Desktop/Competitor\ Analysis
```

Make the launcher executable (one-time):

```bash
chmod +x launch.sh
```

### Step 2 — Start the dashboard

```bash
./launch.sh
```

The script will install all dependencies automatically on the first run (~60 seconds). After that, startup is instant.

The terminal will print two URLs:

```
LOCAL URL:   http://localhost:8501
NETWORK URL: http://192.168.1.X:8501   ← share this with teammates on the same Wi-Fi
```

---

## Share with the Whole Team (Permanent URL — Free)

For a URL anyone on the team can access **at any time from anywhere**, deploy to **Streamlit Community Cloud** (free, no server needed):

### 1. Push this folder to GitHub

```bash
cd ~/Desktop/Competitor\ Analysis
git init
git add .
git commit -m "Initial competitor intelligence dashboard"
gh repo create swivl-competitor-intel --private --push --source=.
```

> If you don't have the GitHub CLI, create the repo at github.com and push normally.

### 2. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click **New app**
4. Select the `swivl-competitor-intel` repo, branch `main`, file `run.py`
5. Click **Deploy**

Within ~2 minutes you'll get a permanent URL like:

```
https://swivl-competitor-intel.streamlit.app
```

Share that URL with the team — no install, no setup, accessible from any browser.

---

## Running the Analysis

Once the dashboard is open:

1. Click **▶ Run Full Analysis** — this scrapes pricing, features, reviews, Reddit, and builds the gap analysis (~2 minutes)
2. Results are cached in `.tmp/` — future loads are instant
3. Toggle **Force re-scrape** in the sidebar to refresh with live data
4. Use the **Google Doc Export** button to push a full report to Google Docs (requires one-time OAuth setup — see sidebar instructions)

---

## What Each Tab Shows

| Tab | What it covers |
|-----|---------------|
| 💬 Voice of Customer | G2 & Capterra ratings + top pros/cons for all 8 competitors (3 direct, 5 indirect) |
| 🛠️ Role Pain Points | Real Reddit pain points by persona — Owner, Dispatcher, Tech, Admin, Customer, Sales, Ops |
| 🎯 Gaps & Roadmap | RAG feature table · TAM/SAM/SOM · ICP profiles · Tier 1/2/3 build roadmap · GTM gaps |

---

## Pricing Reference (Verified June 2026)

### Swivl

| Plan | Price | Credits/mo | Users |
|------|-------|-----------|-------|
| Starter | **Free** | 250 | Unlimited |
| Growth | $49/mo | 1,500 | Unlimited |
| Scale Pro ⭐ | $149/mo | 4,800 | Unlimited |
| Organization | $299/mo | 12,000 | Unlimited |

Credits power: AI Receptionist (10 cr/min), AI Estimator (60 cr/estimate), GPS (5 cr/hr), SMS (1 cr/msg).

### Competitors (per-user pricing)

| Competitor | Entry Plan | 10-tech cost | 25-tech cost |
|-----------|-----------|-------------|-------------|
| Jobber (Grow) | $199/mo (10 users) | ~$490/mo | ~$1,195/mo |
| Workiz (Pro) | $325/mo (5 users) | ~$757/mo | ~$1,405/mo |
| HouseCallPro (MAX) | $329/mo (8 users) | ~$399/mo | ~$889/mo |
| **Swivl (Scale Pro)** | **$149/mo flat** | **$149/mo** | **$149/mo** |

---

## Updating Competitor Data

- **Pricing baselines**: edit `tools/scrape_pricing.py` → `BASELINE` dict
- **Review data**: edit `run.py` → `VOC_DATA` dict  
- **Feature gaps & roadmap**: edit `tools/analyze_gaps.py`
- **Indirect competitors**: edit `tools/scrape_indirect_competitors.py`

All static data is clearly labeled with source comments and a date.

---

## Folder Structure

```
Competitor Analysis/
├── run.py                    ← Main Streamlit app (start here)
├── launch.sh                 ← One-click starter script
├── START_HERE.md             ← This file
├── requirements.txt          ← Python dependencies
├── tools/
│   ├── analyze_gaps.py       ← Strategic gaps, roadmap, ICP, market sizing
│   ├── scrape_pricing.py     ← Competitor pricing scraper
│   ├── scrape_features.py    ← Feature changelog scraper
│   ├── scrape_reviews.py     ← G2 / Capterra review scraper
│   ├── scrape_reddit.py      ← Reddit pain point scraper
│   ├── scrape_role_pain.py   ← Persona-based Reddit analysis
│   ├── scrape_feature_matrix.py  ← Feature comparison matrix
│   ├── scrape_indirect_competitors.py
│   ├── track_history.py      ← Snapshot & diff engine
│   ├── swivl_metrics.py      ← Swivl KPI tracker
│   └── google_docs_writer.py ← Google Doc export
├── .tmp/                     ← Cached analysis data (auto-generated)
└── credentials.json          ← Google OAuth (add yours for Doc export)
```
