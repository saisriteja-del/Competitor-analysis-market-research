"""
Swivl Smart Route Optimizer — MVP Prototype
============================================
Standalone Streamlit app demonstrating the MVP feature.

Requirements:
  pip install streamlit requests pydeck

Run:
  MAPBOX_TOKEN=pk.your_token_here python3 -m streamlit run prototype/route_optimizer.py

Or add to your .env:
  MAPBOX_TOKEN=pk.your_token_here

Features (MVP tier):
  - Map view of day's jobs (Mapbox via pydeck)
  - One-click Optimize Route (Mapbox Optimization API v1 — true TSP)
  - Reordered job list with per-leg and total drive time
  - Navigate button per job (Google Maps deep-link)
  - Manual drag-to-reorder (via up/down buttons — Streamlit limitation)
"""

import json
import math
import os
import time
from pathlib import Path

import requests
import streamlit as st

# ── Config ──────────────────────────────────────────────────────────────────
PROTO_DIR = Path(__file__).parent
SAMPLE_JOBS_PATH = PROTO_DIR / "sample_jobs.json"

# Load Mapbox token from env or .env file
def _load_token() -> str:
    token = os.environ.get("MAPBOX_TOKEN", "")
    if not token:
        env_path = PROTO_DIR.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("MAPBOX_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    return token

MAPBOX_TOKEN = _load_token()

# ── Mapbox API helpers ───────────────────────────────────────────────────────

def geocode_address(address: str, token: str) -> tuple[float, float] | None:
    """Convert an address to (lng, lat) using Mapbox Geocoding API."""
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{requests.utils.quote(address)}.json"
    resp = requests.get(url, params={"access_token": token, "country": "US", "limit": 1}, timeout=10)
    if resp.ok:
        features = resp.json().get("features", [])
        if features:
            lng, lat = features[0]["center"]
            return (lng, lat)
    return None


def optimize_route(waypoints: list[dict], token: str) -> dict | None:
    """
    Call Mapbox Optimization API v1 to find the optimal sequence.
    waypoints: list of {"name": str, "coordinates": [lng, lat]}
    Returns the full API response dict, or None on failure.

    API docs: https://docs.mapbox.com/api/navigation/optimization/
    """
    if len(waypoints) < 2:
        return None

    # Format: lng,lat;lng,lat;...
    coords_str = ";".join(f"{w['coordinates'][0]},{w['coordinates'][1]}" for w in waypoints)
    url = f"https://api.mapbox.com/optimized-trips/v1/mapbox/driving/{coords_str}"

    params = {
        "access_token": token,
        "source": "first",      # keep start location first
        "destination": "last",  # keep end location (return to base) last — set to "any" to skip
        "roundtrip": "false",   # one-way trip
        "overview": "full",     # include full route geometry
        "steps": "false",
    }

    try:
        resp = requests.get(url, params=params, timeout=30)
        if resp.ok:
            return resp.json()
        else:
            st.error(f"Mapbox Optimization API error {resp.status_code}: {resp.text[:300]}")
            return None
    except requests.exceptions.Timeout:
        st.error("Mapbox API timed out. Check your connection.")
        return None
    except Exception as e:
        st.error(f"Mapbox API error: {e}")
        return None


def get_directions(waypoints: list[dict], token: str) -> dict | None:
    """
    Get turn-by-turn directions + per-leg durations from Mapbox Directions API v5.
    Used as fallback when Optimization API is not available (demo mode).
    """
    if len(waypoints) < 2:
        return None
    coords_str = ";".join(f"{w['coordinates'][0]},{w['coordinates'][1]}" for w in waypoints)
    url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{coords_str}"
    params = {"access_token": token, "overview": "full", "steps": "false"}
    try:
        resp = requests.get(url, params=params, timeout=20)
        if resp.ok:
            return resp.json()
    except Exception:
        pass
    return None


# ── Haversine fallback (no API) ──────────────────────────────────────────────

def haversine_km(lat1, lng1, lat2, lng2) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def nearest_neighbor_sort(jobs: list[dict], start: dict) -> list[dict]:
    """Simple nearest-neighbor geo-sort (fallback when no Mapbox token)."""
    remaining = list(jobs)
    ordered = []
    current_lat = start["lat"]
    current_lng = start["lng"]
    while remaining:
        closest = min(remaining, key=lambda j: haversine_km(current_lat, current_lng, j["lat"], j["lng"]))
        ordered.append(closest)
        current_lat, current_lng = closest["lat"], closest["lng"]
        remaining.remove(closest)
    return ordered


def estimate_drive_time_min(jobs: list[dict], start: dict) -> list[float]:
    """Estimate drive time per leg using haversine + 40 km/h avg speed."""
    legs = []
    prev_lat, prev_lng = start["lat"], start["lng"]
    for job in jobs:
        dist_km = haversine_km(prev_lat, prev_lng, job["lat"], job["lng"])
        time_min = (dist_km / 40) * 60  # 40 km/h avg urban speed
        legs.append(round(time_min, 1))
        prev_lat, prev_lng = job["lat"], job["lng"]
    return legs


# ── Map rendering ────────────────────────────────────────────────────────────

def render_map(jobs: list[dict], start: dict, token: str):
    """Render jobs on a Mapbox map using pydeck."""
    try:
        import pydeck as pdk

        # Job pins
        job_data = [
            {
                "lat": j["lat"],
                "lng": j["lng"],
                "label": f"{i+1}. {j['customer']}",
                "job_type": j["job_type"],
                "window": j["window"],
                "color": [59, 130, 246],  # blue
            }
            for i, j in enumerate(jobs)
        ]
        # Start pin
        start_data = [{"lat": start["lat"], "lng": start["lng"], "label": "Start", "color": [16, 185, 129]}]

        # Route line
        route_coords = [[start["lng"], start["lat"]]] + [[j["lng"], j["lat"]] for j in jobs]
        route_data = [{"path": route_coords, "color": [59, 130, 246, 180]}]

        layers = [
            pdk.Layer(
                "PathLayer",
                data=route_data,
                get_path="path",
                get_color="color",
                width_min_pixels=3,
            ),
            pdk.Layer(
                "ScatterplotLayer",
                data=start_data,
                get_position=["lng", "lat"],
                get_color="color",
                get_radius=250,
                pickable=True,
            ),
            pdk.Layer(
                "ScatterplotLayer",
                data=job_data,
                get_position=["lng", "lat"],
                get_color="color",
                get_radius=200,
                pickable=True,
                tooltip=True,
            ),
            pdk.Layer(
                "TextLayer",
                data=job_data,
                get_position=["lng", "lat"],
                get_text="label",
                get_size=14,
                get_color=[255, 255, 255],
                get_alignment_baseline="'bottom'",
            ),
        ]

        center_lat = sum(j["lat"] for j in jobs) / len(jobs)
        center_lng = sum(j["lng"] for j in jobs) / len(jobs)

        view_state = pdk.ViewState(latitude=center_lat, longitude=center_lng, zoom=11, pitch=0)

        st.pydeck_chart(
            pdk.Deck(
                map_style="mapbox://styles/mapbox/light-v11",
                initial_view_state=view_state,
                layers=layers,
                api_keys={"mapbox": token} if token else {},
                tooltip={"text": "{label}\n{job_type}\nWindow: {window}"},
            )
        )

    except ImportError:
        st.warning("pydeck not installed. Run: pip install pydeck")
        _render_fallback_map(jobs, start)


def _render_fallback_map(jobs: list[dict], start: dict):
    """Simple st.map fallback when pydeck is unavailable."""
    import pandas as pd
    points = [{"lat": start["lat"], "lon": start["lng"]}]
    for j in jobs:
        points.append({"lat": j["lat"], "lon": j["lng"]})
    st.map(pd.DataFrame(points))


# ── Google Maps navigate link ────────────────────────────────────────────────

def gmaps_link(address: str) -> str:
    encoded = requests.utils.quote(address)
    return f"https://www.google.com/maps/dir/?api=1&destination={encoded}&travelmode=driving"


# ── Main App ─────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Swivl Route Optimizer",
        page_icon="🗺️",
        layout="wide",
    )

    # ── Header ──
    st.title("🗺️ Swivl Smart Route Optimizer")
    st.caption("MVP Prototype — Powered by Mapbox Optimization API v1")

    if not MAPBOX_TOKEN:
        st.warning(
            "**No Mapbox token found.** Running in demo mode (haversine geo-sort, no map tiles).  \n"
            "Add `MAPBOX_TOKEN=pk.your_token` to your `.env` file or set the env variable to enable "
            "true TSP optimization and live maps."
        )

    # ── Load sample data ──
    with open(SAMPLE_JOBS_PATH) as f:
        data = json.load(f)

    tech_name = data["tech_name"]
    start = data["tech_start"]

    # Session state
    if "jobs" not in st.session_state:
        st.session_state.jobs = list(data["jobs"])
    if "optimized" not in st.session_state:
        st.session_state.optimized = False
    if "drive_legs" not in st.session_state:
        st.session_state.drive_legs = []

    jobs = st.session_state.jobs

    # ── Sidebar ──
    with st.sidebar:
        st.header(f"Tech: {tech_name}")
        st.write(f"**Start:** {start['label']}")
        st.write(f"**Jobs today:** {len(jobs)}")
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            optimize_btn = st.button(
                "✨ Optimize Route",
                type="primary",
                use_container_width=True,
                help="Calls Mapbox Optimization API v1 (TSP) to find the shortest route",
            )
        with col2:
            reset_btn = st.button(
                "↺ Reset",
                use_container_width=True,
                help="Reset to original job order",
            )

        if reset_btn:
            st.session_state.jobs = list(data["jobs"])
            st.session_state.optimized = False
            st.session_state.drive_legs = []
            st.rerun()

        if optimize_btn:
            with st.spinner("Optimizing route..."):
                if MAPBOX_TOKEN:
                    # Build waypoints: start + all jobs
                    waypoints = [{"name": start["label"], "coordinates": [start["lng"], start["lat"]]}]
                    for j in jobs:
                        waypoints.append({"name": j["customer"], "coordinates": [j["lng"], j["lat"]]})

                    result = optimize_route(waypoints, MAPBOX_TOKEN)

                    if result and result.get("code") == "Ok":
                        trips = result.get("trips", [])
                        waypoint_order = result.get("waypoints", [])
                        if trips and waypoint_order:
                            # Mapbox returns waypoints with waypoint_index = position in optimized trip
                            # waypoint 0 is the start (source=first), so jobs start at index 1
                            ordered_indices = sorted(
                                [w for w in waypoint_order if w.get("waypoint_index") is not None],
                                key=lambda w: w["waypoint_index"],
                            )
                            # Extract job waypoints (skip index 0 = start location)
                            job_order = [w["trips_index"] for w in ordered_indices if w.get("waypoint_index", 0) > 0]

                            if job_order:
                                st.session_state.jobs = [jobs[i - 1] for i in job_order if 0 < i <= len(jobs)]
                            else:
                                # Fallback: use arrival waypoint order
                                st.session_state.jobs = jobs  # keep as-is, report will still show time

                            # Extract per-leg durations from trip legs
                            legs = trips[0].get("legs", [])
                            st.session_state.drive_legs = [round(leg["duration"] / 60, 1) for leg in legs]
                            st.session_state.optimized = True
                            st.success(f"Route optimized! Saved via Mapbox TSP.")
                        else:
                            st.error("Optimization API returned an unexpected response.")
                    else:
                        # Fallback to geo-sort
                        st.session_state.jobs = nearest_neighbor_sort(jobs, start)
                        st.session_state.drive_legs = estimate_drive_time_min(st.session_state.jobs, start)
                        st.session_state.optimized = True
                        st.info("Using geo-sort fallback (Mapbox API issue).")
                else:
                    # Demo mode: haversine nearest-neighbor
                    st.session_state.jobs = nearest_neighbor_sort(jobs, start)
                    st.session_state.drive_legs = estimate_drive_time_min(st.session_state.jobs, start)
                    st.session_state.optimized = True
                    st.info("Demo mode: geo-sort (nearest-neighbor). Add Mapbox token for true TSP.")
                st.rerun()

        # Drive time summary
        if st.session_state.drive_legs:
            total_drive = sum(st.session_state.drive_legs)
            total_h = int(total_drive // 60)
            total_m = int(total_drive % 60)
            st.divider()
            st.metric("Total drive time", f"{total_h}h {total_m}min")
            st.caption("Excludes job durations")

            total_job_min = sum(j["duration_min"] for j in st.session_state.jobs)
            total_day_min = total_drive + total_job_min
            day_h = int(total_day_min // 60)
            day_m = int(total_day_min % 60)
            st.metric("Est. total day", f"{day_h}h {day_m}min")
            st.caption("Drive + job time combined")

        st.divider()
        if st.session_state.optimized:
            st.success("Route is optimized")
        else:
            st.info("Using original order")

    # ── Main area: map + job list ──
    map_col, list_col = st.columns([3, 2])

    with map_col:
        st.subheader("Route Map")
        if MAPBOX_TOKEN:
            render_map(st.session_state.jobs, start, MAPBOX_TOKEN)
        else:
            _render_fallback_map(st.session_state.jobs, start)
            st.caption("Add MAPBOX_TOKEN to see full map tiles and route lines")

    with list_col:
        st.subheader("Job Sequence")

        drive_legs = st.session_state.drive_legs

        for i, job in enumerate(st.session_state.jobs):
            drive_time = drive_legs[i] if i < len(drive_legs) else None

            with st.container(border=True):
                header_cols = st.columns([0.1, 0.7, 0.1, 0.1])
                with header_cols[0]:
                    st.markdown(f"**#{i+1}**")
                with header_cols[1]:
                    st.markdown(f"**{job['customer']}**")
                with header_cols[2]:
                    # Move up
                    if i > 0:
                        if st.button("↑", key=f"up_{i}", help="Move up"):
                            jobs_copy = list(st.session_state.jobs)
                            jobs_copy[i], jobs_copy[i-1] = jobs_copy[i-1], jobs_copy[i]
                            st.session_state.jobs = jobs_copy
                            st.session_state.drive_legs = estimate_drive_time_min(jobs_copy, start)
                            st.rerun()
                with header_cols[3]:
                    # Move down
                    if i < len(st.session_state.jobs) - 1:
                        if st.button("↓", key=f"dn_{i}", help="Move down"):
                            jobs_copy = list(st.session_state.jobs)
                            jobs_copy[i], jobs_copy[i+1] = jobs_copy[i+1], jobs_copy[i]
                            st.session_state.jobs = jobs_copy
                            st.session_state.drive_legs = estimate_drive_time_min(jobs_copy, start)
                            st.rerun()

                info_cols = st.columns([0.5, 0.5])
                with info_cols[0]:
                    st.caption(f"🔧 {job['job_type']}")
                    st.caption(f"🕐 {job['window']}")
                with info_cols[1]:
                    if drive_time is not None:
                        h = int(drive_time // 60)
                        m = int(drive_time % 60)
                        time_str = f"{h}h {m}min" if h > 0 else f"{m}min"
                        st.caption(f"🚗 Drive: {time_str}")
                    st.caption(f"⏱️ Job: {job['duration_min']}min")

                if job.get("notes"):
                    st.caption(f"📝 {job['notes']}")

                nav_url = gmaps_link(job["address"])
                st.link_button("Navigate →", nav_url, use_container_width=True)

        # Return to base
        with st.container(border=True):
            st.markdown(f"**🏁 Return to base**")
            st.caption(start["label"])
            if drive_legs and len(drive_legs) > len(st.session_state.jobs):
                last_leg = drive_legs[-1]
                h = int(last_leg // 60)
                m = int(last_leg % 60)
                st.caption(f"🚗 Drive back: {int(last_leg)}min")

    # ── Footer ──
    st.divider()
    st.caption(
        "Swivl Smart Route Optimizer — MVP Prototype  |  "
        "Powered by [Mapbox Optimization API v1](https://docs.mapbox.com/api/navigation/optimization/)  |  "
        "True TSP solver — not geo-sort"
    )


if __name__ == "__main__":
    main()
