"""Utility helpers shared across backend modules."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .config import LOG_DIR


def configure_logging(name: str = "karma") -> logging.Logger:
    """Return a module-level logger writing both to stdout and a log file."""

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    LOG_DIR.mkdir(exist_ok=True, parents=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    logfile = LOG_DIR / f"{name}_{timestamp}.log"

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(logfile)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def ensure_columns(df, required: Iterable[str], df_name: str = "DataFrame") -> None:
    """Raise ValueError if any required columns are missing."""

    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{df_name} missing columns: {missing}")


__all__ = ["configure_logging", "ensure_columns"]

