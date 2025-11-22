"""
Data loading helpers for the Mechanical Karma pipeline.

All loaders rely on the filenames declared in `config.RAW_FILES`. This keeps
environment-specific paths out of logic modules and makes testing easier.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

from .config import INTERIM_DATA_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR, raw_file_path
from .utils import ensure_columns

CSV_OPTIONS = {
    "results": {"sep": ";"},
    "weather": {"sep": ";"},
}

def load_csv(
    key: str,
    *,
    parse_dates: Optional[Iterable[str]] = None,
    dtype: Optional[dict] = None,
    usecols: Optional[Iterable[str]] = None,
    **kwargs,
) -> pd.DataFrame:
    """
    Load a CSV identified by the `RAW_FILES` key.

    Args:
        key: One of `telemetry`, `lap_start`, `lap_end`, `results`, `weather`.
        parse_dates: Columns to parse as datetimes.
        dtype: Optional dtype mapping.
        usecols: Optional subset of columns to load.
        kwargs: Forwarded to `pandas.read_csv`.
    """

    csv_path = raw_file_path(key)
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Missing {key} CSV at {csv_path}. Drop the file into {RAW_DATA_DIR} and retry."
        )

    extra_options = CSV_OPTIONS.get(key, {})

    df = pd.read_csv(
        csv_path,
        parse_dates=parse_dates,
        dtype=dtype,
        usecols=usecols,
        low_memory=False,
        **extra_options,
        **kwargs,
    )
    if df.empty:
        raise ValueError(f"Loaded zero rows from {csv_path}. Verify the CSV contents.")
    return df


def save_dataframe(df: pd.DataFrame, path: Path, *, format: str = "parquet") -> Path:
    """
    Persist a DataFrame to disk using the desired format.

    Supported formats: `parquet`, `csv`.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    if format == "parquet":
        df.to_parquet(path, index=False)
    elif format == "csv":
        df.to_csv(path, index=False)
    else:
        raise ValueError(f"Unsupported format '{format}'.")
    return path


def load_per_lap_dataset(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Convenience loader for the processed per-lap feature table.
    Defaults to `data/processed/per_lap_features.parquet`.
    """

    if path is None:
        default_path = PROCESSED_DATA_DIR / "per_lap_features.parquet"
    else:
        # Resolve relative paths - try multiple locations
        if not path.is_absolute():
            # Try relative to PROCESSED_DATA_DIR first
            default_path = PROCESSED_DATA_DIR / path.name
            if not default_path.exists():
                # Try as path relative to PROCESSED_DATA_DIR
                default_path = PROCESSED_DATA_DIR / path
                if not default_path.exists():
                    # Try as absolute path from project root
                    from .config import PROJECT_ROOT
                    default_path = PROJECT_ROOT / path
                    if not default_path.exists():
                        # Try as absolute path from backend directory
                        from .config import BACKEND_DIR
                        default_path = BACKEND_DIR / path
        else:
            default_path = path
    
    if not default_path.exists():
        raise FileNotFoundError(
            f"Per-lap dataset not found at {default_path}. "
            f"Tried resolving: {path if path else 'default'}. "
            f"Run `python -m src.main ingest` first or provide correct path."
        )
    if default_path.suffix == ".parquet":
        return pd.read_parquet(default_path)
    return pd.read_csv(default_path)


def ensure_lap_bounds(df: pd.DataFrame) -> pd.DataFrame:
    """Validate that lap start/end tables contain the required columns."""

    expected = {"vehicle_id", "lap_number", "timestamp"}
    ensure_columns(df, expected, df_name="lap boundary table")
    return df


__all__ = [
    "load_csv",
    "save_dataframe",
    "load_per_lap_dataset",
    "ensure_lap_bounds",
    "RAW_DATA_DIR",
    "INTERIM_DATA_DIR",
    "PROCESSED_DATA_DIR",
]

