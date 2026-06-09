# Workflow: FSM Role Pain Points (Reddit)

## Objective
Surface the day-to-day pain points of **field service dispatchers** and **technicians** from Reddit — not tied to any specific competitor. The goal is to feed Swivl PM and positioning with a living, role-segmented view of what actually frustrates users in the field and at the dispatch desk, independent of which tool they use.

This is complementary to `scrape_reddit.py` (which tracks competitor-specific complaints). Where that tool answers *"why are people mad at Jobber?"*, this one answers *"what breaks a dispatcher's day?"* and *"what makes a tech curse their phone?"*.

## Required Inputs
- Python 3.9+ with `requirements.txt` installed
- Internet access to `old.reddit.com` (no API key needed — uses the public JSON endpoint)
- No Reddit account needed

## Expected Outputs
- `.tmp/role_pain_data.json` — structured output with:
  - `posts`: split by role (`dispatcher`, `technician`)
  - `theme_summary`: tallies per role × theme (scheduling, routing, app UX, etc.)
  - `quotes`: top representative quotes per theme with permalinks
  - `swivl_implications`: product/positioning suggestions derived from the top themes
  - `scrape_method`: `live`, `partial`, or `illustrative_fallback`
- New tab in `run.py`: **🛠️ Role Pain Points** — renders the data as a role × theme heatmap, quote cards, and an implications panel

## Subreddits (deep dive — 12)
Trades (where techs vent):
- `r/HVAC`, `r/HVACadvice`, `r/Plumbing`, `r/electricians`, `r/askelectricians`
- `r/Appliances` (repair techs), `r/Roofing`, `r/PestControl`, `r/Landscaping`

Business / ops (where owners & dispatchers post):
- `r/FieldServiceManagement`, `r/smallbusiness`, `r/Entrepreneur`

## Query Design — Role-Tagged
Each query is tagged with a target role (`dispatcher`, `technician`, or `both`) before running. That tag is carried through on the resulting posts so we can segment by persona downstream.

**Technician-focused queries** (field pain):
- `mobile app crash` · `FSM app offline` · `app on the job` · `paperwork on job`
- `signature capture` · `parts inventory truck` · `GPS tracking` · `time tracking job`
- `dispatch sent wrong` · `stuck on job` · `job invoice on phone` · `technician app sucks`

**Dispatcher-focused queries** (office pain):
- `scheduling techs` · `dispatch board` · `route optimization` · `tech no-show`
- `customer callback dispatch` · `emergency dispatch` · `overbooked schedule` · `last minute cancel`
- `dispatcher software` · `reschedule customer` · `dispatch ETA`

**Both-role queries** (cross-cutting):
- `field service software` · `service business software` · `work order app`
- `technician dispatcher frustration`

## Theme Taxonomy (post-classification)
Keyword scan over title + selftext + top-comment body tags each post with one or more themes:

| Theme | What it captures |
|---|---|
| `scheduling` | Double-booking, shifting appts, last-minute cancels, calendar chaos |
| `routing` | Travel time, order of jobs, maps/GPS, route planning |
| `dispatch_comms` | Tech ↔ dispatcher comms, wrong info sent, ETAs, text/call overload |
| `mobile_ux` | App crashes, slow app, bad UI, battery drain, login loops |
| `offline` | No signal on job, can't sync, lost data |
| `paperwork` | Forms, signatures, photos, estimates, long data entry |
| `parts_inventory` | Truck stock, parts ordering, wrong parts sent |
| `customer_comms` | Reminders, reviews, quote approvals, no-shows |
| `billing_invoicing` | Card readers, invoice generation, collections, AR |
| `reporting` | KPIs, per-tech performance, revenue reports |
| `training_onboarding` | Tool complexity, learning curve, new hire ramp |
| `integrations` | QBO, Stripe, accounting, phone systems |

## Handling Failures

### Reddit 429 / rate limited
`scrape_role_pain.py` caches every request to `.tmp/reddit_role_*.json` and sleeps 2.5s between calls. If Reddit still blocks:
1. Wait 15+ minutes, re-run with **Force re-scrape** off — cached results fill the gaps
2. If still blocked, the tool falls back to illustrative posts labeled `source=illustrative` in the UI
3. To update fallback posts, edit `FALLBACK_POSTS` in `tools/scrape_role_pain.py`

### Comment fetch is slow
Comment scraping adds ~1 request per top post. The tool only pulls comments for the **top 5 posts per role × theme**, so the extra cost is bounded (≤60 extra requests). Disable by passing `include_comments=False`.

### Subreddit returns nothing
Some subs (e.g., `r/FieldServiceManagement`) are small and may have zero matches for niche queries. That's fine — the tool silently skips and moves on.

## Updating the Taxonomy
When you notice new recurring themes in posts that aren't covered:
1. Add a row to the table above
2. Add a new entry to `THEME_KEYWORDS` in `tools/scrape_role_pain.py`
3. Re-run with `force_refresh=True` to re-tag cached posts

## Running Standalone
```bash
cd "Competitor Analysis"
python3 tools/scrape_role_pain.py
```
Prints a role × theme summary and the top 3 quotes per theme to stdout, writes `.tmp/role_pain_data.json`.

## Cadence
Run monthly. Dispatcher/tech pain shifts more slowly than competitor pricing — more frequent runs mostly rehydrate the same themes and burn rate limit.
