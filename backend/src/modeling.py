"""
Model training + inference helpers for Mechanical Karma.
"""

from __future__ import annotations

import json
import pickle
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from joblib import dump, load
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

from .config import TARGET_COLUMN, TRAINING_CONFIG
from .data_loader import load_per_lap_dataset
from .utils import configure_logging, ensure_columns

LOGGER = configure_logging("modeling")


def _select_model(name: str):
    """Return a model instance based on config."""

    if name == "mlp":
        return MLPClassifier(
            hidden_layer_sizes=(128, 64),
            activation="relu",
            learning_rate_init=1e-3,
            max_iter=300,
            random_state=TRAINING_CONFIG.random_state,
        )
    if name == "random_forest":
        return RandomForestClassifier(
            n_estimators=400,
            max_depth=12,
            min_samples_split=4,
            random_state=TRAINING_CONFIG.random_state,
            n_jobs=-1,
        )
    raise ValueError(f"Unsupported model type '{name}'.")


def _split_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Separate features and target; drop non-numeric metadata columns."""

    ensure_columns(df, [TARGET_COLUMN], "per_lap dataset")

    ignore_cols = {
        TARGET_COLUMN, 
        "lap", 
        "vehicle_id", 
        "STATUS",
        "failed_component",
        "failure_component",
        "failure_lap",
    }
    
    # Get numeric columns only, excluding ignored columns
    numeric_cols = []
    for c in df.columns:
        if c not in ignore_cols:
            # Check if column is numeric (int, float, bool)
            if pd.api.types.is_numeric_dtype(df[c]):
                numeric_cols.append(c)

    if not numeric_cols:
        raise ValueError("No numeric feature columns found in dataset")
    
    X = df[numeric_cols].copy()
    y = df[TARGET_COLUMN].astype(int)
    return X, y


def train(per_lap_path: Path | None = None) -> Dict[str, float]:
    """Train the configured model and persist artifacts."""

    df = load_per_lap_dataset(per_lap_path)
    X, y = _split_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TRAINING_CONFIG.test_size,
        stratify=y,
        random_state=TRAINING_CONFIG.random_state,
    )

    scaler = None
    if TRAINING_CONFIG.scale_features:
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)
    else:
        X_train = X_train.values
        X_test = X_test.values

    model = _select_model(TRAINING_CONFIG.model_type)
    LOGGER.info("Training %s model on %s samples", TRAINING_CONFIG.model_type, len(X_train))
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    report = classification_report(y_test, y_pred, output_dict=True)
    auc = roc_auc_score(y_test, y_prob)

    # Save artifacts
    TRAINING_CONFIG.save_path.parent.mkdir(parents=True, exist_ok=True)
    dump(model, TRAINING_CONFIG.save_path)
    LOGGER.info("Saved model to %s", TRAINING_CONFIG.save_path)

    feature_meta = {"feature_names": X.columns.tolist()}
    (TRAINING_CONFIG.save_path.parent / "feature_meta.json").write_text(
        json.dumps(feature_meta, indent=2)
    )

    if scaler is not None:
        dump(scaler, TRAINING_CONFIG.scaler_path)
        LOGGER.info("Saved scaler to %s", TRAINING_CONFIG.scaler_path)

    metrics = {
        "roc_auc": float(auc),
        "precision_dnf": report["1"]["precision"],
        "recall_dnf": report["1"]["recall"],
        "f1_dnf": report["1"]["f1-score"],
        "accuracy": report["accuracy"],
    }
    (TRAINING_CONFIG.save_path.parent / "training_metrics.json").write_text(
        json.dumps(metrics, indent=2)
    )
    LOGGER.info("Training metrics: %s", metrics)
    return metrics


def load_artifacts(model_path: Path | None = None, scaler_path: Path | None = None):
    """Load persisted model + scaler."""

    model_path = model_path or TRAINING_CONFIG.save_path
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. Train the model first.")
    model = load(model_path)

    scaler = None
    scaler_path = scaler_path or TRAINING_CONFIG.scaler_path
    if scaler_path.exists():
        scaler = load(scaler_path)
    return model, scaler


def run_inference(per_lap_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Generate karma scores (DNF probability) for the supplied dataset.

    Returns the dataframe with an added `karma_score` column (0-100 scale).
    """

    if per_lap_df is None:
        per_lap_df = load_per_lap_dataset()
    model, scaler = load_artifacts()

    X, _ = _split_features(per_lap_df)
    if scaler is not None:
        X = scaler.transform(X)
    else:
        X = X.values

    probs = model.predict_proba(X)[:, 1]
    per_lap_df = per_lap_df.copy()
    per_lap_df["karma_score"] = (probs * 100).round(2)
    return per_lap_df


__all__ = ["train", "run_inference", "load_artifacts"]

