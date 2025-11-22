"""
Mechanical Karma stream simulation.

Takes per-lap features and produces smoothed per-component "karma" scores
that mimic real-time risk tracking.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd

from .config import PROCESSED_DATA_DIR
from .utils import configure_logging

LOGGER = configure_logging("karma_stream")


@dataclass(frozen=True)
class ComponentSpec:
    name: str
    feature_weights: Dict[str, float]
    description: str


COMPONENT_SPECS: List[ComponentSpec] = [
    ComponentSpec(
        name="engine",
        feature_weights={"speed_mean": 0.4, "nmot_mean": 0.6},
        description="RPM + sustained speed stress",
    ),
    ComponentSpec(
        name="gearbox",
        feature_weights={"gear_mean": 0.5, "accx_can_std": 0.5},
        description="Gear usage and longitudinal jolts",
    ),
    ComponentSpec(
        name="brakes",
        feature_weights={"pbrake_f_max": 0.6, "pbrake_r_max": 0.4},
        description="Brake pressure spikes front/rear",
    ),
    ComponentSpec(
        name="tires",
        feature_weights={"speed_mean": 0.3, "Steering_Angle_std": 0.7},
        description="Cornering + abrasion load",
    ),
]


def _column_stats(df: pd.DataFrame, columns: Iterable[str]) -> Dict[str, tuple[float, float]]:
    stats = {}
    for col in columns:
        series = df[col].dropna()
        if series.empty:
            stats[col] = (0.0, 0.0)
        else:
            stats[col] = (float(series.min()), float(series.max()))
    return stats


def _normalize(value: float | int | None, min_val: float, max_val: float) -> float:
    if value is None or pd.isna(value):
        return 0.0
    if max_val <= min_val:
        return 0.0
    return max(0.0, min(1.0, (float(value) - min_val) / (max_val - min_val)))


def _component_score(row: pd.Series, stats: Dict[str, tuple[float, float]], spec: ComponentSpec) -> float:
    weighted_sum = 0.0
    total_weight = 0.0
    for feature, weight in spec.feature_weights.items():
        min_val, max_val = stats.get(feature, (0.0, 0.0))
        norm_val = _normalize(row.get(feature), min_val, max_val)
        weighted_sum += weight * norm_val
        total_weight += weight
    if total_weight == 0:
        return 0.0
    return weighted_sum / total_weight


def compute_stream(df: pd.DataFrame, *, smoothing: float = 0.6, wear_rate: float = 0.002) -> pd.DataFrame:
    """
    Compute Mechanical Karma scores from an in-memory per-lap dataframe.
    
    Args:
        df: Per-lap feature dataframe
        smoothing: EMA smoothing factor (0-1, higher = more smoothing)
        wear_rate: Base wear accumulation per lap (0-1, simulates natural degradation)
    """

    if df.empty:
        return pd.DataFrame(columns=["vehicle_id", "lap", "component", "instant_score", "karma_score"])

    required_cols = set().union(*(spec.feature_weights.keys() for spec in COMPONENT_SPECS))
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Dataset missing required columns for karma stream: {missing}")

    stats = _column_stats(df, required_cols)

    records: List[dict] = []
    sorted_df = df.sort_values(["vehicle_id", "lap"])
    smoothed_scores: Dict[tuple[str, str], float] = {}
    
    # Track starting lap for each vehicle to calculate relative wear
    vehicle_start_laps: Dict[str, int] = {}

    for _, row in sorted_df.iterrows():
        vehicle_id = row["vehicle_id"]
        lap = int(row["lap"])
        
        # Track starting lap
        if vehicle_id not in vehicle_start_laps:
            vehicle_start_laps[vehicle_id] = lap
        
        # Calculate relative lap position (for wear accumulation)
        relative_lap = lap - vehicle_start_laps[vehicle_id] + 1
        
        for spec in COMPONENT_SPECS:
            instant = _component_score(row, stats, spec)
            key = (vehicle_id, spec.name)
            prev = smoothed_scores.get(key, instant)
            
            # Apply EMA smoothing to instant stress
            smoothed = smoothing * prev + (1 - smoothing) * instant
            
            # Add cumulative wear that increases over time
            # Wear accumulates based on lap number, simulating natural degradation
            wear_accumulation = min(0.5, wear_rate * relative_lap)  # Cap wear at 0.5
            
            # Combine smoothed stress with accumulated wear
            # Higher instant stress increases wear rate
            stress_multiplier = 1.0 + (instant * 0.5)  # Stress increases wear by up to 50%
            total_wear = wear_accumulation * stress_multiplier
            
            # Final karma is smoothed stress + accumulated wear (capped at 1.0)
            final_karma = min(1.0, smoothed + total_wear)
            
            smoothed_scores[key] = final_karma
            records.append(
                {
                    "vehicle_id": vehicle_id,
                    "lap": lap,
                    "component": spec.name,
                    "instant_score": instant,
                    "karma_score": final_karma,
                }
            )

    return pd.DataFrame(records)


def simulate_stream(
    dataset_path: Path | None = None,
    *,
    smoothing: float = 0.6,
    wear_rate: float = 0.002,
    output_path: Path | None = None,
) -> pd.DataFrame:
    """
    Generate smoothed mechanical karma scores per vehicle/component per lap.
    
    Args:
        dataset_path: Path to per-lap features parquet
        smoothing: EMA smoothing factor
        wear_rate: Base wear accumulation per lap (simulates degradation)
        output_path: Optional path to save results
    """

    dataset_path = dataset_path or PROCESSED_DATA_DIR / "per_lap_features.parquet"
    df = pd.read_parquet(dataset_path)
    result = compute_stream(df, smoothing=smoothing, wear_rate=wear_rate)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.suffix == ".csv":
            result.to_csv(output_path, index=False)
        else:
            result.to_parquet(output_path, index=False)
        LOGGER.info("Saved karma stream to %s", output_path)
    return result


__all__ = ["simulate_stream", "compute_stream", "COMPONENT_SPECS"]

