"""
Component-specific failure prediction models.

Trains separate models for each component (engine, gearbox, brakes, tires)
to predict which specific component is at risk of failure.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from joblib import dump, load
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from .config import ARTIFACT_DIR, TRAINING_CONFIG
from .data_loader import load_per_lap_dataset
from .utils import configure_logging

LOGGER = configure_logging("component_modeling")

COMPONENTS = ["engine", "gearbox", "brakes", "tires"]


def _split_features_for_component(df: pd.DataFrame) -> pd.DataFrame:
    """Split features for component models (same logic as main model)."""
    from .config import TARGET_COLUMN
    
    ignore_cols = {
        TARGET_COLUMN, 
        "lap", 
        "vehicle_id", 
        "STATUS",
        "failed_component",
        "failure_component",
        "failure_lap",
    }
    
    # Get numeric columns only
    numeric_cols = []
    for c in df.columns:
        if c not in ignore_cols:
            if pd.api.types.is_numeric_dtype(df[c]):
                numeric_cols.append(c)
    
    if not numeric_cols:
        raise ValueError("No numeric feature columns found in dataset")
    
    X = df[numeric_cols].copy()
    return X


def train_component_models(per_lap_path: Path | None = None) -> Dict[str, Dict[str, float]]:
    """
    Train separate models for each component.
    
    Returns metrics for each component model.
    """
    df = load_per_lap_dataset(per_lap_path)
    
    # Check if we have component failure data
    if "failed_component" not in df.columns and "failure_component" not in df.columns:
        raise ValueError(
            "Dataset must have 'failed_component' or 'failure_component' column. "
            "Use training_data_with_failures.parquet for component-specific training."
        )
    
    # Use failed_component if available, otherwise failure_component
    component_col = "failed_component" if "failed_component" in df.columns else "failure_component"
    
    # Get features
    X = _split_features_for_component(df)
    
    # Prepare data: only use rows where we know the component status
    # For each component, create binary labels (failed this component or not)
    component_models = {}
    component_metrics = {}
    
    for component in COMPONENTS:
        LOGGER.info("Training model for component: %s", component)
        
        # Create binary target: 1 if this component failed, 0 otherwise
        y_component = (df[component_col] == component).astype(int)
        
        # Skip if no failures for this component
        if y_component.sum() == 0:
            LOGGER.warning("No failures for component %s, skipping", component)
            continue
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y_component,
            test_size=TRAINING_CONFIG.test_size,
            stratify=y_component,
            random_state=TRAINING_CONFIG.random_state,
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=4,
            random_state=TRAINING_CONFIG.random_state,
            n_jobs=-1,
        )
        
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test_scaled)
        y_prob = model.predict_proba(X_test_scaled)[:, 1]
        
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        
        # Save model and scaler
        model_path = ARTIFACT_DIR / f"component_model_{component}.pkl"
        scaler_path = ARTIFACT_DIR / f"component_scaler_{component}.pkl"
        
        dump(model, model_path)
        dump(scaler, scaler_path)
        
        component_models[component] = {
            "model_path": str(model_path),
            "scaler_path": str(scaler_path),
        }
        
        metrics = {
            "precision": report.get("1", {}).get("precision", 0.0),
            "recall": report.get("1", {}).get("recall", 0.0),
            "f1": report.get("1", {}).get("f1-score", 0.0),
            "accuracy": report.get("accuracy", 0.0),
            "support": report.get("1", {}).get("support", 0),
        }
        
        component_metrics[component] = metrics
        LOGGER.info("Component %s metrics: %s", component, metrics)
    
    # Save component model metadata
    metadata = {
        "components": list(component_models.keys()),
        "model_paths": component_models,
        "metrics": component_metrics,
    }
    
    metadata_path = ARTIFACT_DIR / "component_models_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2))
    LOGGER.info("Saved component models metadata to %s", metadata_path)
    
    return component_metrics


def predict_component_failures(per_lap_df: pd.DataFrame) -> pd.DataFrame:
    """
    Predict failure probability for each component.
    
    Returns dataframe with added columns:
    - engine_failure_prob
    - gearbox_failure_prob
    - brakes_failure_prob
    - tires_failure_prob
    - predicted_component (component with highest probability)
    """
    # Load component models metadata
    metadata_path = ARTIFACT_DIR / "component_models_metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(
            "Component models not found. Train component models first: "
            "python -m src.component_modeling train"
        )
    
    metadata = json.loads(metadata_path.read_text())
    component_models = metadata["model_paths"]
    
    # Get features
    X = _split_features_for_component(per_lap_df)
    
    # Predict for each component
    component_probs = {}
    
    for component in COMPONENTS:
        if component not in component_models:
            # No model for this component, set probability to 0
            component_probs[f"{component}_failure_prob"] = 0.0
            continue
        
        try:
            model = load(component_models[component]["model_path"])
            scaler = load(component_models[component]["scaler_path"])
            
            X_scaled = scaler.transform(X)
            probs = model.predict_proba(X_scaled)[:, 1]
            
            component_probs[f"{component}_failure_prob"] = probs * 100  # Convert to percentage
        except Exception as e:
            LOGGER.warning("Error predicting for component %s: %s", component, e)
            component_probs[f"{component}_failure_prob"] = 0.0
    
    # Add probabilities to dataframe
    result_df = per_lap_df.copy()
    for col, probs in component_probs.items():
        result_df[col] = probs
    
    # Predict most likely component to fail
    prob_cols = [f"{c}_failure_prob" for c in COMPONENTS if f"{c}_failure_prob" in result_df.columns]
    if prob_cols:
        result_df["predicted_component"] = result_df[prob_cols].idxmax(axis=1).str.replace("_failure_prob", "")
        result_df["max_component_prob"] = result_df[prob_cols].max(axis=1)
    else:
        result_df["predicted_component"] = "none"
        result_df["max_component_prob"] = 0.0
    
    return result_df


def load_component_models() -> Dict[str, Tuple]:
    """Load all component models and scalers."""
    metadata_path = ARTIFACT_DIR / "component_models_metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError("Component models not found. Train them first.")
    
    metadata = json.loads(metadata_path.read_text())
    component_models = {}
    
    for component, paths in metadata["model_paths"].items():
        model = load(paths["model_path"])
        scaler = load(paths["scaler_path"])
        component_models[component] = (model, scaler)
    
    return component_models


__all__ = [
    "train_component_models",
    "predict_component_failures",
    "load_component_models",
    "COMPONENTS",
]

