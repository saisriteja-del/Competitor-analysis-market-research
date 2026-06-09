# Workflow: Smart Route Optimizer — Market Research & MVP

## Objective

Produce a market research report and MVP feature spec for Swivl's Smart Route Optimizer, covering how Jobber, Workiz, and HouseCallPro implement route optimization in the US FSM market, and defining what Swivl should ship first.

## Outputs

| Output | Location | Description |
|--------|----------|-------------|
| Research data | `.tmp/route_optimizer_research.json` | Raw competitor feature inventory, pain points, market context, live search results |
| MVP analysis | `.tmp/route_optimizer_mvp.json` | Synthesized competitor table, gap analysis, and structured MVP spec |
| Report (deliverable) | `outputs/route_optimizer_report.md` | Human-readable document — market research + MVP spec |
| Prototype | `prototype/route_optimizer.py` | Runnable Streamlit app demonstrating MVP behavior |

## How to Run

### Step 1: Research
```bash
python3 tools/research_route_optimizer.py
```
Runs DuckDuckGo searches per competitor + caches to `.tmp/`. Hardcoded baseline data covers features, limitations, G2 sentiment.

### Step 2: Analyze & Generate Report
```bash
python3 tools/analyze_route_mvp.py
```
Reads `.tmp/route_optimizer_research.json` → synthesizes competitor table + gap analysis → writes `outputs/route_optimizer_report.md`.

### Step 3: Run the Prototype
```bash
# With a real Mapbox token (true TSP optimization + map tiles):
MAPBOX_TOKEN=pk.your_token_here python3 -m streamlit run prototype/route_optimizer.py

# Demo mode (no token — haversine geo-sort, no map tiles):
python3 -m streamlit run prototype/route_optimizer.py
```

Get a free Mapbox token at: https://account.mapbox.com/

## Refresh Cadence

- **Re-run research every quarter** (competitor routing features evolve slowly)
- **Update hardcoded baselines** in `tools/research_route_optimizer.py` when:
  - A competitor ships a major routing update
  - New G2/Capterra reviews reveal a change in customer sentiment
  - A competitor changes their pricing tier that affects routing access

## Key Findings (April 2026)

1. **No competitor offers true TSP** — all use geo-sort (nearest-neighbor). Swivl can be first.
2. **Time windows are universally ignored** in auto-optimize. Major customer complaint on G2.
3. **Mobile reorder is unavailable** across all three. Swivl MVP should be mobile-first.
4. **Workiz has zero auto-optimization** — pure manual, a direct migration argument.
5. **HouseCallPro's "On My Way" SMS** is the most-praised routing-adjacent feature. Phase 2 priority.

## MVP Scope Boundary

**Ship in MVP:**
- Map view of day's jobs
- One-click Optimize Route (Mapbox Optimization API v1 — true TSP)
- Reordered job list with per-leg + total drive time
- Navigate deep-link per job (Google Maps / Apple Maps)
- Manual drag-to-reorder override

**Do not ship in MVP (Phase 2+):**
- Time-window-aware optimization
- Real-time traffic rerouting
- Customer ETA SMS
- Multi-tech dispatcher view
- Predictive job duration

## Prototype Architecture

The prototype (`prototype/route_optimizer.py`) uses:

| Concern | Solution |
|---------|----------|
| Map rendering | `pydeck` with Mapbox GL tiles |
| Route optimization | Mapbox Optimization API v1 (TSP, up to 12 waypoints) |
| Drive time estimates | Mapbox Optimization API response (or haversine fallback) |
| Navigation | Google Maps deep-link (`maps.google.com/dir/`) |
| Reorder | Streamlit up/down buttons (drag-to-reorder in production) |
| Token | `MAPBOX_TOKEN` env var or `.env` file |

Sample job data: `prototype/sample_jobs.json` — 8 HVAC jobs in Austin, TX.

## Mapbox Pricing Notes

| Tier | Requests/month | Cost |
|------|---------------|------|
| Free | 100,000 | $0 |
| Pay-as-you-go | 100K+ | ~$0.004/request |

At 500 optimizations/day (large deployment): ~15K/month — well within free tier.
At 5,000/day (very large): ~$1.80/day — negligible as per-customer infrastructure cost.

## Updating This Workflow

When you ship Phase 2 (time windows, ETA SMS), update:
1. `COMPETITOR_BASELINE` in `tools/research_route_optimizer.py` — add the new features to competitor records
2. The `MVP_SPEC` tiers in `tools/analyze_route_mvp.py` — move Phase 2 items to "shipped"
3. The feature matrix in `tools/scrape_feature_matrix.py` — add "Smart Route Optimizer" as a Swivl feature (true)
4. This workflow file with updated findings
