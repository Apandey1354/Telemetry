"""
Feature engineering utilities for the Mechanical Karma model.

The main entrypoint is `build_per_lap_dataset`, which orchestrates:
1. Loading telemetry + metadata.
2. Assigning each telemetry row to a lap window.
3. Aggregating per-lap statistics.
4. Merging with race results / weather / labels.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

import pandas as pd

from . import data_loader
from .config import (
    DEFAULT_TIMESTAMP_COL,
    DEFAULT_VEHICLE_COL,
    LAP_META_COLUMNS,
    STATUS_COLUMN,
    TARGET_COLUMN,
    TELEMETRY_AGGREGATIONS,
)
from .utils import configure_logging, ensure_columns

LOGGER = configure_logging("feature_engineering")


def _normalize_lap_bounds(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure lap boundary tables expose `vehicle_id`, `lap_number`, `timestamp`.

    Raw feeds occasionally use `lap` instead of `lap_number` or place the
    timestamp in a `value` column. Standardize those here so the downstream
    logic can rely on consistent schema.
    """

    rename_map = {}
    if "lap_number" not in df.columns and "lap" in df.columns:
        rename_map["lap"] = "lap_number"
    if "timestamp" not in df.columns and "value" in df.columns:
        rename_map["value"] = "timestamp"
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def _prepare_lap_windows(
    lap_start: pd.DataFrame, lap_end: pd.DataFrame
) -> pd.DataFrame:
    """Return a dataframe with lap start/end times per vehicle."""

    lap_start = _normalize_lap_bounds(lap_start)
    lap_end = _normalize_lap_bounds(lap_end)
    required_cols = {"vehicle_id", "lap_number", "timestamp"}
    ensure_columns(lap_start, required_cols, "lap_start")
    ensure_columns(lap_end, required_cols, "lap_end")

    lap_start = (
        lap_start.sort_values(["vehicle_id", "lap_number", "timestamp"])
        .drop_duplicates(subset=["vehicle_id", "lap_number"], keep="first")
    )
    lap_end = (
        lap_end.sort_values(["vehicle_id", "lap_number", "timestamp"])
        .drop_duplicates(subset=["vehicle_id", "lap_number"], keep="last")
    )

    lap_start = lap_start.rename(columns={"timestamp": "lap_start_time"})
    lap_end = lap_end.rename(columns={"timestamp": "lap_end_time"})

    lap_windows = lap_start.merge(
        lap_end, on=["vehicle_id", "lap_number"], how="inner", validate="one_to_one"
    )
    lap_windows = lap_windows.sort_values(["vehicle_id", "lap_number"])
    ensure_columns(lap_windows, LAP_META_COLUMNS, "lap_windows")
    lap_windows["lap_duration_s"] = (
        (lap_windows["lap_end_time"] - lap_windows["lap_start_time"]).dt.total_seconds()
    )
    return lap_windows


def assign_laps(
    telemetry: pd.DataFrame,
    lap_windows: pd.DataFrame,
    *,
    vehicle_col: str = DEFAULT_VEHICLE_COL,
    time_col: str = DEFAULT_TIMESTAMP_COL,
) -> pd.DataFrame:
    """
    Attach lap numbers to raw telemetry rows using merge_asof.

    Assumes telemetry timestamps fall within the lap start/end window.
    Rows outside the windows are dropped.
    """

    ensure_columns(telemetry, [vehicle_col, time_col], "telemetry")

    telemetry = telemetry.sort_values([time_col, vehicle_col])
    lap_windows = lap_windows.sort_values(["lap_start_time", vehicle_col])

    merged = pd.merge_asof(
        telemetry,
        lap_windows,
        left_on=time_col,
        right_on="lap_start_time",
        by=vehicle_col,
        direction="backward",
        allow_exact_matches=True,
    )
    # Filter out rows that fell before the first lap or after the lap end.
    mask = merged[time_col] <= merged["lap_end_time"]
    merged = merged.loc[mask].copy()
    merged.rename(columns={"lap_number": "lap"}, inplace=True)
    return merged


def pivot_telemetry_signals(
    telemetry_with_laps: pd.DataFrame,
    *,
    signal_name_col: str = "telemetry_name",
    signal_value_col: str = "telemetry_value",
) -> pd.DataFrame:
    """
    Convert long-format telemetry (name/value rows) into wide columns per signal.

    Many feeds (including the VIR sample) encode each telemetry measurement as
    `telemetry_name` + `telemetry_value`. Aggregations downstream expect one
    column per signal, so we pivot here while preserving timestamps and lap
    metadata.
    """

    telemetry_with_laps = telemetry_with_laps.loc[:, ~telemetry_with_laps.columns.duplicated()]

    required_cols = {
        DEFAULT_VEHICLE_COL,
        "lap",
        DEFAULT_TIMESTAMP_COL,
        signal_name_col,
        signal_value_col,
    }
    if not required_cols.issubset(telemetry_with_laps.columns):
        return telemetry_with_laps

    index_cols = [DEFAULT_VEHICLE_COL, "lap", DEFAULT_TIMESTAMP_COL]
    meta_cols = [
        col
        for col in ["lap_start_time", "lap_end_time", "lap_duration_s"]
        if col in telemetry_with_laps.columns
    ]

    pivot_source = telemetry_with_laps[index_cols + meta_cols + [signal_name_col, signal_value_col]]
    pivoted = (
        pivot_source.pivot_table(
            index=index_cols,
            columns=signal_name_col,
            values=signal_value_col,
            aggfunc="mean",
        )
        .reset_index()
    )
    if meta_cols:
        pivoted = pivoted.merge(
            pivot_source[index_cols + meta_cols].drop_duplicates(),
            on=index_cols,
            how="left",
        )
    pivoted.columns = [col if not isinstance(col, tuple) else col[-1] for col in pivoted.columns]
    return pivoted


def aggregate_per_lap(telemetry_with_laps: pd.DataFrame) -> pd.DataFrame:
    """Compute summary statistics per vehicle/lap."""

    ensure_columns(telemetry_with_laps, ["lap", DEFAULT_VEHICLE_COL], "lap-tagged telemetry")

    agg_dict: Dict[str, List[str]] = {}
    for spec in TELEMETRY_AGGREGATIONS:
        if spec.column in telemetry_with_laps.columns:
            agg_dict[spec.column] = list(spec.stats)

    if not agg_dict:
        raise ValueError(
            "None of the configured telemetry columns were found. "
            "Update TELEMETRY_AGGREGATIONS in config.py to match your CSV schema."
        )

    grouped = telemetry_with_laps.groupby([DEFAULT_VEHICLE_COL, "lap"]).agg(agg_dict)
    grouped.columns = [f"{col}_{stat}" for col, stat in grouped.columns.to_flat_index()]
    grouped = grouped.reset_index()

    meta_cols = ["lap_start_time", "lap_end_time", "lap_duration_s"]
    available_meta = [c for c in meta_cols if c in telemetry_with_laps.columns]
    meta = (
        telemetry_with_laps.groupby([DEFAULT_VEHICLE_COL, "lap"])[available_meta]
        .first()
        .reset_index()
        if available_meta
        else None
    )

    sample_counts = (
        telemetry_with_laps.groupby([DEFAULT_VEHICLE_COL, "lap"]).size().reset_index(name="samples_per_lap")
    )
    grouped = grouped.merge(sample_counts, on=[DEFAULT_VEHICLE_COL, "lap"], how="left")

    if meta is not None:
        grouped = grouped.merge(meta, on=[DEFAULT_VEHICLE_COL, "lap"], how="left")

    return grouped


def merge_with_results(
    per_lap: pd.DataFrame,
    results: pd.DataFrame,
) -> pd.DataFrame:
    """Attach race results (vehicle metadata + STATUS) to per-lap features."""

    ensure_columns(results, ["vehicle_id", STATUS_COLUMN], "race_results")
    merged = per_lap.merge(results, on="vehicle_id", how="left")
    merged[TARGET_COLUMN] = merged[STATUS_COLUMN].eq("DNF").astype(int)
    return merged


def merge_weather(
    per_lap: pd.DataFrame,
    weather: pd.DataFrame,
    *,
    time_col: str = "timestamp",
) -> pd.DataFrame:
    """Incorporate weather metrics using forward-fill per lap."""

    ensure_columns(weather, [time_col], "weather")

    weather = weather.sort_values(time_col)
    per_lap = per_lap.sort_values(time_col) if time_col in per_lap.columns else per_lap
    merged = pd.merge_asof(
        per_lap.sort_values(time_col),
        weather,
        on=time_col,
        direction="backward",
    )
    return merged


def build_per_lap_dataset() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load raw CSVs and construct the per-lap dataset.

    Returns:
        Lap-tagged telemetry (intermediate) and aggregated per-lap dataframe.
    """

    LOGGER.info("Loading raw telemetry + metadata CSVs")
    telemetry = data_loader.load_csv(
        "telemetry",
        parse_dates=[DEFAULT_TIMESTAMP_COL],
    )
    vehicle_lookup = (
        telemetry[[DEFAULT_VEHICLE_COL, "vehicle_number"]]
        .dropna(subset=["vehicle_number"])
        .drop_duplicates(subset=["vehicle_number"])
    )
    vehicle_lookup["vehicle_number"] = (
        vehicle_lookup["vehicle_number"].astype(str).str.strip()
    )
    lap_start = data_loader.load_csv("lap_start", parse_dates=["timestamp"])
    lap_end = data_loader.load_csv("lap_end", parse_dates=["timestamp"])
    results = data_loader.load_csv("results")
    if "vehicle_number" not in results.columns and "NUMBER" in results.columns:
        results["vehicle_number"] = results["NUMBER"].astype(str).str.strip()
    elif "vehicle_number" in results.columns:
        results["vehicle_number"] = results["vehicle_number"].astype(str).str.strip()

    if DEFAULT_VEHICLE_COL not in results.columns:
        results = results.merge(
            vehicle_lookup,
            on="vehicle_number",
            how="left",
            suffixes=("", "_lookup"),
        )
        lookup_col = f"{DEFAULT_VEHICLE_COL}_lookup"
        if lookup_col in results.columns:
            results[DEFAULT_VEHICLE_COL] = results[DEFAULT_VEHICLE_COL].fillna(
                results.pop(lookup_col)
            )

    missing_vehicle = results[DEFAULT_VEHICLE_COL].isna()
    if missing_vehicle.any():
        missing_numbers = (
            results.loc[missing_vehicle, "vehicle_number"].dropna().unique().tolist()
        )
        LOGGER.warning(
            "Dropping %s results rows without vehicle_id (car numbers: %s)",
            missing_vehicle.sum(),
            missing_numbers,
        )
        results = results.loc[~missing_vehicle].copy()

    LOGGER.info("Assigning laps to telemetry samples")
    lap_windows = _prepare_lap_windows(lap_start, lap_end)
    telemetry_with_lap = assign_laps(telemetry, lap_windows)
    telemetry_with_lap = pivot_telemetry_signals(telemetry_with_lap)
    LOGGER.info("Telemetry rows after lap assignment: %s", len(telemetry_with_lap))

    LOGGER.info("Aggregating features per lap")
    per_lap = aggregate_per_lap(telemetry_with_lap)

    LOGGER.info("Merging race results + labels")
    per_lap = merge_with_results(per_lap, results)

    dataset_path = data_loader.save_dataframe(
        per_lap, data_loader.PROCESSED_DATA_DIR / "per_lap_features.parquet"
    )
    LOGGER.info("Saved per-lap dataset to %s", dataset_path)

    interim_path = data_loader.save_dataframe(
        telemetry_with_lap,
        data_loader.INTERIM_DATA_DIR / "telemetry_with_laps.parquet",
    )
    LOGGER.info("Saved lap-tagged telemetry to %s", interim_path)

    return telemetry_with_lap, per_lap


__all__ = [
    "assign_laps",
    "aggregate_per_lap",
    "merge_with_results",
    "merge_weather",
    "build_per_lap_dataset",
]

