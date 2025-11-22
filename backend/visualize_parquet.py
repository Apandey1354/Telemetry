#!/usr/bin/env python
"""Quick visualization helper for per-lap parquet outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARQUET = PROJECT_ROOT / "data" / "processed" / "per_lap_features.parquet"


def pick_default_vehicle(df: pd.DataFrame) -> list[str]:
    """Return top 5 vehicles with most laps to help users choose."""

    return (
        df.groupby("vehicle_id")["lap"]
            .count()
            .sort_values(ascending=False)
            .index[:5]
            .tolist()
    )


def plot_vehicle(df: pd.DataFrame, vehicle_id: str) -> None:
    """Plot a few key lap-level metrics for a single vehicle."""

    vehicle_df = df[df["vehicle_id"] == vehicle_id].sort_values("lap")
    if vehicle_df.empty:
        raise ValueError(f"No rows found for vehicle_id={vehicle_id}")

    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)

    vehicle_df.plot(
        x="lap",
        y="speed_mean",
        marker="o",
        ax=axes[0],
        title=f"{vehicle_id} – Speed (mean)",
    )
    vehicle_df.plot(
        x="lap",
        y="accx_can_mean",
        marker="o",
        ax=axes[1],
        title="Longitudinal Accel (mean)",
    )
    vehicle_df.plot(
        x="lap",
        y="pbrake_f_max",
        marker="o",
        ax=axes[2],
        title="Front Brake Pressure (max)",
    )
    axes[2].set_xlabel("Lap")
    plt.tight_layout()
    plt.show()


def main(parquet_path: Path, vehicle_id: str | None) -> None:
    df = pd.read_parquet(parquet_path)

    if vehicle_id is None:
        print("Please choose a vehicle_id using --vehicle. Examples:")
        for vid in pick_default_vehicle(df):
            print("  ", vid)
        return

    plot_vehicle(df, vehicle_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualize per-lap parquet outputs.")
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_PARQUET,
        help="Path to per_lap_features parquet file",
    )
    parser.add_argument(
        "--vehicle",
        type=str,
        help="Vehicle ID to plot, e.g. GR86-002-2",
    )
    args = parser.parse_args()
    main(args.file, args.vehicle)

