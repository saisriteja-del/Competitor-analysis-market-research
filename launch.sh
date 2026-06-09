#!/bin/bash
# ──────────────────────────────────────────────────────────
#  Swivl Competitor Intelligence — One-Click Launcher
#  Run this once to install dependencies and start the app.
#  After the first run, deps are cached — startup is instant.
# ──────────────────────────────────────────────────────────

set -e
cd "$(dirname "$0")"

echo ""
echo "  🔍  Swivl Competitor Intelligence"
echo "  ──────────────────────────────────"

# ── 1. Python check ──────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "  ❌  Python 3 not found. Install from https://python.org and re-run."
    exit 1
fi

PYTHON=$(command -v python3)
echo "  ✓  Python: $($PYTHON --version)"

# ── 2. Virtual environment ───────────────────────────────
if [ ! -d ".venv" ]; then
    echo "  →  Creating virtual environment..."
    $PYTHON -m venv .venv
fi
source .venv/bin/activate

# ── 3. Install / upgrade dependencies ────────────────────
echo "  →  Installing dependencies (first run may take ~60s)..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# ── 4. Launch ────────────────────────────────────────────
echo ""
echo "  ✅  Starting dashboard..."
echo ""
echo "  LOCAL URL:   http://localhost:8501"
echo "  NETWORK URL: http://$(ipconfig getifaddr en0 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}'):8501"
echo "               (share this with teammates on the same Wi-Fi)"
echo ""
echo "  Press Ctrl+C to stop."
echo ""

streamlit run run.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false
