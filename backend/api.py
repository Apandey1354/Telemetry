"""Flask API for Mechanical Karma React dashboard."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path
from typing import Dict, Any

import pandas as pd
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from src import feature_engineering, karma_stream, modeling
from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR
from src.modeling import run_inference, load_artifacts

app = Flask(__name__)
CORS(app)  # Enable CORS for React app

# Temporary directory for uploaded files
UPLOAD_DIR = Path(tempfile.gettempdir()) / "karma_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def process_uploaded_file(file, filename: str) -> Path:
    """Save uploaded file to temporary directory."""
    filepath = UPLOAD_DIR / secure_filename(filename)
    file.save(str(filepath))
    return filepath


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})


def process_uploaded_telemetry(filepath: Path) -> pd.DataFrame:
    """Process uploaded telemetry CSV and return per-lap features."""
    from src import feature_engineering
    from src.config import DEFAULT_TIMESTAMP_COL, DEFAULT_VEHICLE_COL
    
    # Check which timestamp column exists
    sample_df = pd.read_csv(filepath, nrows=1)
    timestamp_col = None
    for col in [DEFAULT_TIMESTAMP_COL, "timestamp", "meta_time"]:
        if col in sample_df.columns:
            timestamp_col = col
            break
    
    # Read the CSV with appropriate timestamp parsing
    parse_dates = [timestamp_col] if timestamp_col else []
    df = pd.read_csv(filepath, low_memory=False, parse_dates=parse_dates)
    
    # Check if data is in long format (telemetry_name, telemetry_value)
    if "telemetry_name" in df.columns and "telemetry_value" in df.columns:
        # Ensure we have the required columns for pivoting
        if "lap" not in df.columns:
            raise ValueError("Lap information required. Please ensure 'lap' column exists in the CSV.")
        
        # Use timestamp column for pivoting (use meta_time or timestamp)
        time_col = timestamp_col if timestamp_col else "timestamp"
        if time_col not in df.columns:
            # Try to use any timestamp-like column
            time_cols = [c for c in df.columns if 'time' in c.lower() or 'timestamp' in c.lower()]
            if time_cols:
                time_col = time_cols[0]
            else:
                raise ValueError("No timestamp column found for processing")
        
        # Temporarily rename to match expected column name
        if time_col != DEFAULT_TIMESTAMP_COL:
            df = df.rename(columns={time_col: DEFAULT_TIMESTAMP_COL})
        
        # Pivot the telemetry signals
        telemetry_pivoted = feature_engineering.pivot_telemetry_signals(
            df,
            signal_name_col="telemetry_name",
            signal_value_col="telemetry_value"
        )
        
        # Rename back if needed
        if time_col != DEFAULT_TIMESTAMP_COL and DEFAULT_TIMESTAMP_COL in telemetry_pivoted.columns:
            telemetry_pivoted = telemetry_pivoted.rename(columns={DEFAULT_TIMESTAMP_COL: time_col})
    else:
        # Data is already in wide format
        telemetry_pivoted = df
    
    # Ensure lap column exists
    if "lap" not in telemetry_pivoted.columns:
        raise ValueError("Lap information not found in data")
    
    # Aggregate per lap
    per_lap = feature_engineering.aggregate_per_lap(telemetry_pivoted)
    
    # Add dummy DNF flag if not present (for karma computation)
    if "dnf_flag" not in per_lap.columns:
        per_lap["dnf_flag"] = 0
    
    return per_lap


@app.route("/api/upload", methods=["POST"])
def upload_and_process():
    """Upload telemetry file and process it."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400
        
        # Save uploaded file temporarily
        filepath = process_uploaded_file(file, file.filename)
        
        # Read and validate CSV structure
        df_sample = pd.read_csv(filepath, nrows=5)
        required_cols = ["vehicle_id"]
        missing = [col for col in required_cols if col not in df_sample.columns]
        if missing:
            return jsonify({
                "error": f"Missing required columns: {missing}",
                "available_columns": list(df_sample.columns)
            }), 400
        
        # Process the telemetry file
        per_lap = process_uploaded_telemetry(filepath)
        
        # Save processed data
        output_path = PROCESSED_DATA_DIR / "per_lap_features.parquet"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        per_lap.to_parquet(output_path, index=False)
        
        # Generate karma stream
        karma_df = karma_stream.compute_stream(per_lap)
        karma_path = PROCESSED_DATA_DIR / "karma_stream.parquet"
        karma_df.to_parquet(karma_path, index=False)
        
        # Get vehicle list
        vehicles = sorted(per_lap["vehicle_id"].unique().tolist())
        
        return jsonify({
            "message": "File processed successfully",
            "filename": file.filename,
            "rows_processed": len(per_lap),
            "vehicles": vehicles,
            "total_laps": len(per_lap),
            "min_lap": int(per_lap["lap"].min()),
            "max_lap": int(per_lap["lap"].max())
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route("/api/process", methods=["POST"])
def process_data():
    """Process uploaded files and return per-lap features."""
    try:
        # This endpoint would process all uploaded files
        # For now, we'll use existing processed data if available
        per_lap_path = PROCESSED_DATA_DIR / "per_lap_features.parquet"
        
        if not per_lap_path.exists():
            return jsonify({
                "error": "No processed data found. Please run the ingestion pipeline first."
            }), 404
        
        df = pd.read_parquet(per_lap_path)
        
        # Convert to JSON-serializable format
        df = df.sort_values(["vehicle_id", "lap"])
        data = df.to_dict(orient="records")
        
        # Get unique vehicles
        vehicles = sorted(df["vehicle_id"].unique().tolist())
        
        return jsonify({
            "vehicles": vehicles,
            "data": data,
            "total_laps": len(df),
            "min_lap": int(df["lap"].min()),
            "max_lap": int(df["lap"].max())
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/vehicle/<vehicle_id>", methods=["GET"])
def get_vehicle_data(vehicle_id: str):
    """Get data for a specific vehicle."""
    try:
        per_lap_path = PROCESSED_DATA_DIR / "per_lap_features.parquet"
        
        if not per_lap_path.exists():
            return jsonify({"error": "No processed data found"}), 404
        
        df = pd.read_parquet(per_lap_path)
        vehicle_df = df[df["vehicle_id"] == vehicle_id].sort_values("lap")
        
        if vehicle_df.empty:
            return jsonify({"error": f"Vehicle {vehicle_id} not found"}), 404
        
        data = vehicle_df.to_dict(orient="records")
        
        # Calculate metrics
        metrics = {
            "laps_recorded": int(vehicle_df["lap"].nunique()),
            "avg_speed": float(vehicle_df["speed_mean"].mean()) if "speed_mean" in vehicle_df.columns else 0,
            "dnf_flag": int(vehicle_df["dnf_flag"].max()) if "dnf_flag" in vehicle_df.columns else 0,
            "min_lap": int(vehicle_df["lap"].min()),
            "max_lap": int(vehicle_df["lap"].max())
        }
        
        return jsonify({
            "vehicle_id": vehicle_id,
            "data": data,
            "metrics": metrics
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/karma/<vehicle_id>", methods=["GET"])
def get_karma_scores(vehicle_id: str):
    """Get karma scores for a specific vehicle."""
    try:
        max_lap_param = request.args.get("max_lap")
        max_lap = int(max_lap_param) if max_lap_param else None
        
        per_lap_path = PROCESSED_DATA_DIR / "per_lap_features.parquet"
        
        if not per_lap_path.exists():
            return jsonify({"error": "No processed data found"}), 404
        
        df = pd.read_parquet(per_lap_path)
        vehicle_df = df[df["vehicle_id"] == vehicle_id].sort_values("lap")
        
        if vehicle_df.empty:
            return jsonify({"error": f"Vehicle {vehicle_id} not found"}), 404
        
        # Filter by max_lap if provided
        if max_lap is not None:
            vehicle_df = vehicle_df[vehicle_df["lap"] <= max_lap]
        
        if vehicle_df.empty:
            return jsonify({"error": f"No data for vehicle {vehicle_id}"}), 404
        
        # Compute karma stream
        karma_df = karma_stream.compute_stream(vehicle_df)
        
        # Get latest scores per component
        latest_scores = {}
        for component in karma_df["component"].unique():
            component_data = karma_df[karma_df["component"] == component]
            if not component_data.empty:
                latest = component_data.sort_values("lap").iloc[-1]
                latest_scores[component] = {
                    "score": float(latest["karma_score"]),
                    "lap": int(latest["lap"])
                }
        
        # Get time series data
        karma_data = karma_df.to_dict(orient="records")
        
        return jsonify({
            "vehicle_id": vehicle_id,
            "latest_scores": latest_scores,
            "time_series": karma_data
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/karma/<vehicle_id>/lap/<int:max_lap>", methods=["GET"])
def get_karma_up_to_lap(vehicle_id: str, max_lap: int):
    """Get karma scores up to a specific lap (for replay)."""
    try:
        per_lap_path = PROCESSED_DATA_DIR / "per_lap_features.parquet"
        
        if not per_lap_path.exists():
            return jsonify({"error": "No processed data found"}), 404
        
        df = pd.read_parquet(per_lap_path)
        vehicle_df = df[
            (df["vehicle_id"] == vehicle_id) & 
            (df["lap"] <= max_lap)
        ].sort_values("lap")
        
        if vehicle_df.empty:
            return jsonify({"error": f"No data for vehicle {vehicle_id} up to lap {max_lap}"}), 404
        
        # Compute karma stream
        karma_df = karma_stream.compute_stream(vehicle_df)
        karma_data = karma_df.to_dict(orient="records")
        
        return jsonify({
            "vehicle_id": vehicle_id,
            "max_lap": max_lap,
            "time_series": karma_data
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/model-prediction/<vehicle_id>", methods=["GET"])
def get_model_predictions(vehicle_id: str):
    """Get ML model predictions (DNF probability) for a vehicle."""
    try:
        max_lap_param = request.args.get("max_lap")
        max_lap = int(max_lap_param) if max_lap_param else None
        
        per_lap_path = PROCESSED_DATA_DIR / "per_lap_features.parquet"
        
        if not per_lap_path.exists():
            return jsonify({"error": "No processed data found"}), 404
        
        df = pd.read_parquet(per_lap_path)
        vehicle_df = df[df["vehicle_id"] == vehicle_id].sort_values("lap")
        
        if vehicle_df.empty:
            return jsonify({"error": f"Vehicle {vehicle_id} not found"}), 404
        
        # Filter by max_lap if provided (for replay)
        if max_lap is not None:
            vehicle_df = vehicle_df[vehicle_df["lap"] <= max_lap]
        
        if vehicle_df.empty:
            return jsonify({"error": f"No data for vehicle {vehicle_id}"}), 404
        
        # Load trained model
        try:
            model, scaler = load_artifacts()
        except FileNotFoundError:
            return jsonify({
                "error": "Model not found. Please train the model first.",
                "hint": "Run: python -m src.main train"
            }), 404
        
        # Prepare features (same as training)
        # Use the same logic as modeling._split_features
        from src.config import TARGET_COLUMN
        ignore_cols = {
            TARGET_COLUMN, 
            "lap", 
            "vehicle_id", 
            "STATUS",
            "failed_component",
            "failure_component",
            "failure_lap",
        }
        numeric_cols = [c for c in vehicle_df.columns 
                       if c not in ignore_cols 
                       and pd.api.types.is_numeric_dtype(vehicle_df[c])]
        X = vehicle_df[numeric_cols].copy()
        
        # Scale if scaler exists
        if scaler is not None:
            X_scaled = scaler.transform(X)
        else:
            X_scaled = X.values
        
        # Get predictions
        probabilities = model.predict_proba(X_scaled)[:, 1]  # DNF probability
        
        # Try to get component-specific predictions if available
        component_predictions = None
        try:
            from src.component_modeling import predict_component_failures
            component_df = predict_component_failures(vehicle_df)
            component_predictions = {}
            for component in ["engine", "gearbox", "brakes", "tires"]:
                col = f"{component}_failure_prob"
                if col in component_df.columns:
                    component_predictions[component] = component_df[col].tolist()
        except (FileNotFoundError, ImportError):
            # Component models not trained, that's okay
            pass
        
        # Create time series data
        predictions = []
        for idx, (_, row) in enumerate(vehicle_df.iterrows()):
            pred = {
                "lap": int(row["lap"]),
                "dnf_probability": float(probabilities[idx] * 100),  # Convert to percentage
                "risk_level": "high" if probabilities[idx] > 0.7 else "medium" if probabilities[idx] > 0.4 else "low"
            }
            
            # Add component probabilities if available
            if component_predictions:
                for component in ["engine", "gearbox", "brakes", "tires"]:
                    if component in component_predictions:
                        pred[f"{component}_prob"] = float(component_predictions[component][idx])
            
            predictions.append(pred)
        
        # Get latest prediction
        latest = predictions[-1] if predictions else None
        
        # Determine most at-risk component
        most_at_risk = None
        if component_predictions and latest:
            component_probs = {
                comp: latest.get(f"{comp}_prob", 0)
                for comp in ["engine", "gearbox", "brakes", "tires"]
            }
            if component_probs:
                most_at_risk = max(component_probs.items(), key=lambda x: x[1])
                most_at_risk = {
                    "component": most_at_risk[0],
                    "probability": most_at_risk[1]
                }
        
        return jsonify({
            "vehicle_id": vehicle_id,
            "predictions": predictions,
            "latest": latest,
            "most_at_risk_component": most_at_risk,
            "max_lap": int(vehicle_df["lap"].max()) if not vehicle_df.empty else None
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)




