"""
Configuration constants for the Mechanical Karma backend.

Centralizes folder paths, expected CSV filenames, and feature engineering
settings so they can be tuned without rewriting business logic.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence

from dotenv import load_dotenv

# Load optional .env overrides if present.
load_dotenv()

# Base directories -----------------------------------------------------------

SRC_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SRC_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

DATA_ROOT = Path(os.getenv("DATA_ROOT", PROJECT_ROOT / "data")).resolve()
RAW_DATA_DIR = DATA_ROOT / "raw"
INTERIM_DATA_DIR = DATA_ROOT / "interim"
PROCESSED_DATA_DIR = DATA_ROOT / "processed"
ARTIFACT_DIR = BACKEND_DIR / "artifacts"
LOG_DIR = BACKEND_DIR / "logs"

for _path in (RAW_DATA_DIR, INTERIM_DATA_DIR, PROCESSED_DATA_DIR, ARTIFACT_DIR, LOG_DIR):
    _path.mkdir(parents=True, exist_ok=True)


# Filenames ------------------------------------------------------------------

RAW_FILES = {
    "telemetry": os.getenv("TELEMETRY_CSV", "R1_vir_telemetry_data.csv"),
    "lap_start": os.getenv("LAP_START_CSV", "vir_lap_start_R1.csv"),
    "lap_end": os.getenv("LAP_END_CSV", "vir_lap_end_R1.csv"),
    "results": os.getenv("RESULTS_CSV", "03_Provisional Results_Race 1_Anonymized.CSV"),
    "weather": os.getenv("WEATHER_CSV", "weather_vir_R1.csv"),  # optional
}

DEFAULT_TIMESTAMP_COL = os.getenv("TELEMETRY_TIME_COL", "meta_time")
DEFAULT_VEHICLE_COL = os.getenv("TELEMETRY_VEHICLE_COL", "vehicle_id")

# Aggregations ---------------------------------------------------------------


@dataclass(frozen=True)
class AggregationSpec:
    """Defines aggregations to compute for a numeric telemetry column."""

    column: str
    stats: Sequence[str] = ("mean", "max", "min", "std")
    rename: Dict[str, str] | None = None

    def output_columns(self) -> List[str]:
        postfix_map = self.rename or {}
        cols = []
        for stat in self.stats:
            suffix = postfix_map.get(stat, stat)
            cols.append(f"{self.column}_{suffix}")
        return cols


TELEMETRY_AGGREGATIONS: Sequence[AggregationSpec] = (
    AggregationSpec("speed", stats=("mean", "max")),
    AggregationSpec("Steering_Angle", stats=("mean", "std")),
    AggregationSpec("ath", stats=("mean", "max", "std")),
    AggregationSpec("pbrake_f", stats=("mean", "max")),
    AggregationSpec("pbrake_r", stats=("mean", "max")),
    AggregationSpec("nmot", stats=("mean", "max", "std")),
    AggregationSpec("accx_can", stats=("mean", "max", "min", "std")),
    AggregationSpec("accy_can", stats=("mean", "max", "min", "std")),
    AggregationSpec("gear", stats=("mean", "max")),
)

LAP_META_COLUMNS = ["vehicle_id", "lap_number", "lap_start_time", "lap_end_time"]

TARGET_COLUMN = "dnf_flag"
STATUS_COLUMN = "STATUS"

# Modeling -------------------------------------------------------------------


@dataclass
class TrainingConfig:
    test_size: float = float(os.getenv("TEST_SPLIT", 0.2))
    random_state: int = int(os.getenv("SEED", 42))
    scale_features: bool = True
    model_type: str = os.getenv("MODEL_TYPE", "random_forest")
    save_path: Path = ARTIFACT_DIR / "karma_model.pkl"
    scaler_path: Path = ARTIFACT_DIR / "feature_scaler.pkl"


TRAINING_CONFIG = TrainingConfig()


# Firebase -------------------------------------------------------------------

FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL", "")
SERVICE_ACCOUNT_PATH = Path(
    os.getenv("SERVICE_ACCOUNT_PATH", PROJECT_ROOT / "secrets" / "serviceAccountKey.json")
).expanduser()


def raw_file_path(name: str) -> Path:
    """Return a Path for a configured raw CSV by key."""

    if name not in RAW_FILES:
        raise KeyError(f"Unknown raw file key '{name}'. Valid keys: {tuple(RAW_FILES.keys())}")
    return RAW_DATA_DIR / RAW_FILES[name]


__all__ = [
    "RAW_FILES",
    "RAW_DATA_DIR",
    "INTERIM_DATA_DIR",
    "PROCESSED_DATA_DIR",
    "ARTIFACT_DIR",
    "LOG_DIR",
    "DEFAULT_TIMESTAMP_COL",
    "DEFAULT_VEHICLE_COL",
    "TELEMETRY_AGGREGATIONS",
    "LAP_META_COLUMNS",
    "TARGET_COLUMN",
    "STATUS_COLUMN",
    "TRAINING_CONFIG",
    "FIREBASE_DB_URL",
    "SERVICE_ACCOUNT_PATH",
    "raw_file_path",
]




