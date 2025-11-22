#!/usr/bin/env python
"""Streamlit dashboard for local Mechanical Karma exploration."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import time

import pandas as pd
import plotly.express as px
import streamlit as st

from src import karma_stream

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


@st.cache_data(show_spinner=False)
def load_parquet(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def load_per_lap(path: Optional[Path] = None) -> pd.DataFrame:
    path = path or PROCESSED_DIR / "per_lap_features.parquet"
    df = load_parquet(path)
    df = df.sort_values(["vehicle_id", "lap"])
    return df


def load_karma(path: Optional[Path] = None) -> pd.DataFrame:
    path = path or PROCESSED_DIR / "karma_stream.parquet"
    if not path.exists():
        return pd.DataFrame()
    df = load_parquet(path)
    return df


def render_time_series(vehicle_df: pd.DataFrame) -> None:
    fig = px.line(
        vehicle_df,
        x="lap",
        y=["speed_mean", "accx_can_mean", "pbrake_f_max"],
        markers=True,
        labels={"value": "Metric Value", "variable": "Metric"},
        title=f"{vehicle_df['vehicle_id'].iloc[0]} — Lap Trends",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_karma(karma_df: pd.DataFrame, vehicle_id: str) -> None:
    if karma_df.empty:
        st.info("Run `python -m src.main karma-stream` to generate component scores.")
        return

    subset = karma_df[karma_df["vehicle_id"] == vehicle_id]
    if subset.empty:
        st.warning("No karma data for this vehicle.")
        return

    latest = (
        subset.sort_values("lap")
        .groupby("component")
        .tail(1)
        .set_index("component")["karma_score"]
    )
    cols = st.columns(len(latest))
    for (component, score), col in zip(latest.items(), cols):
        col.metric(component.title(), f"{score:.2f}")

    fig = px.line(
        subset,
        x="lap",
        y="karma_score",
        color="component",
        title="Mechanical Karma — per Component",
    )
    st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="Mechanical Karma Dashboard", layout="wide")
    st.title("Mechanical Karma – Local Dashboard")
    st.caption("Real-time feelings coming soon. Powered by per-lap features + simulated karma stream.")

    with st.sidebar:
        st.header("Data")
        per_lap_path = st.text_input(
            "Per-lap dataset",
            value=str(PROCESSED_DIR / "per_lap_features.parquet"),
        )
        karma_path = st.text_input(
            "Karma stream dataset",
            value=str(PROCESSED_DIR / "karma_stream.parquet"),
        )

    per_lap_df = load_per_lap(Path(per_lap_path))
    karma_df = load_karma(Path(karma_path))
    min_lap = int(per_lap_df["lap"].min())
    max_lap = int(per_lap_df["lap"].max())

    if "replay_lap" not in st.session_state:
        st.session_state["replay_lap"] = max_lap
    if "replay_running" not in st.session_state:
        st.session_state["replay_running"] = False

    with st.sidebar.expander("Replay controls", expanded=False):
        replay_enabled = st.checkbox("Enable replay", value=False, key="replay_enabled")
        if not replay_enabled:
            st.session_state["replay_running"] = False
            st.session_state["replay_lap"] = max_lap
        else:
            speed = st.slider("Seconds per lap", 0.1, 2.0, 0.5, 0.1)
            if st.button("Play / Pause"):
                st.session_state["replay_running"] = not st.session_state["replay_running"]
            col1, col2 = st.columns(2)
            if col1.button("Step +1 lap"):
                st.session_state["replay_lap"] = min(max_lap, st.session_state["replay_lap"] + 1)
            if col2.button("Reset replay"):
                st.session_state["replay_lap"] = min_lap
            progress = (st.session_state["replay_lap"] - min_lap) / max(1, max_lap - min_lap)
            st.progress(progress)

            if st.session_state["replay_running"]:
                if st.session_state["replay_lap"] < max_lap:
                    time.sleep(speed)
                    st.session_state["replay_lap"] += 1
                    st.rerun()
                else:
                    st.session_state["replay_running"] = False

    current_lap = st.session_state["replay_lap"] if st.session_state.get("replay_enabled") else max_lap
    display_df = per_lap_df[per_lap_df["lap"] <= current_lap]
    if display_df.empty:
        st.warning("No laps available yet. Add more data or reset replay.")
        return

    vehicle_ids = sorted(per_lap_df["vehicle_id"].unique())
    selected_vehicle = st.sidebar.selectbox("Vehicle", vehicle_ids, index=0)

    vehicle_df = display_df[display_df["vehicle_id"] == selected_vehicle]
    if vehicle_df.empty:
        st.warning(
            f"No telemetry for {selected_vehicle} at or before lap {current_lap}. "
            "Advance the replay or reset."
        )
        return
    st.subheader(f"Vehicle {selected_vehicle}")
    st.caption(f"Showing laps ≤ {current_lap}")

    cols = st.columns(3)
    cols[0].metric("Laps recorded", int(vehicle_df["lap"].nunique()))
    cols[1].metric("Avg Speed", f"{vehicle_df['speed_mean'].mean():.1f} km/h")
    cols[2].metric("DNF Flag", int(vehicle_df["dnf_flag"].max()))

    render_time_series(vehicle_df)
    st.subheader("Mechanical Karma")
    if st.session_state.get("replay_enabled"):
        karma_live = karma_stream.compute_stream(display_df)
    else:
        karma_live = (
            karma_df[karma_df["lap"] <= current_lap]
            if not karma_df.empty
            else karma_stream.compute_stream(display_df)
        )
    render_karma(karma_live, selected_vehicle)


if __name__ == "__main__":
    main()

