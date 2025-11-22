"""
Generate synthetic training dataset with component failure labels.

This script creates realistic telemetry data with known failure patterns
for training the Mechanical Karma model.
"""

from __future__ import annotations

import random
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from src.config import PROCESSED_DATA_DIR, RAW_DATA_DIR
from src.config import TARGET_COLUMN, STATUS_COLUMN

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)


def generate_vehicle_telemetry(
    vehicle_id: str,
    num_laps: int,
    failure_component: str | None = None,
    failure_lap: int | None = None,
) -> pd.DataFrame:
    """
    Generate synthetic telemetry data for a vehicle.
    
    Args:
        vehicle_id: Vehicle identifier
        num_laps: Number of laps to generate
        failure_component: Which component fails ('engine', 'gearbox', 'brakes', 'tires', None)
        failure_lap: Lap number when failure occurs (if None, no failure)
    """
    
    records = []
    base_time = datetime(2025, 1, 1, 12, 0, 0)
    
    # Base values for healthy vehicle
    base_speed = 120.0
    base_rpm = 6000.0
    base_brake_pressure = 50.0
    
    for lap in range(1, num_laps + 1):
        # Determine if we're approaching or at failure
        is_failing = False
        failure_progress = 0.0
        
        if failure_component and failure_lap:
            if lap >= failure_lap:
                is_failing = True
                failure_progress = 1.0
            elif lap >= failure_lap - 3:  # Degradation in last 3 laps
                is_failing = True
                failure_progress = (lap - (failure_lap - 3)) / 3.0
        
        # Initialize all variables with default (healthy) values
        speed = base_speed + np.random.normal(0, 5)
        nmot = base_rpm + np.random.normal(0, 200)
        gear = max(1, min(6, 4 + np.random.normal(0, 0.5)))
        accx_std = 0.5 + np.random.normal(0, 0.1)
        brake_pressure = base_brake_pressure + np.random.normal(0, 5)
        pbrake_f = brake_pressure + np.random.normal(0, 5)
        pbrake_r = brake_pressure * 0.8 + np.random.normal(0, 5)
        steering_std = 5.0 + np.random.normal(0, 1)
        
        # Apply failure patterns
        if failure_component == "engine":
            # Engine failure: RPM drops, speed decreases, temperature anomalies
            speed = base_speed * (1 - failure_progress * 0.4) + np.random.normal(0, 5)
            nmot = base_rpm * (1 - failure_progress * 0.5) + np.random.normal(0, 200)
            speed = max(20, speed)
            nmot = max(1000, nmot)
        elif failure_component == "gearbox":
            # Gearbox failure: Gear shifting issues, acceleration problems
            speed = base_speed * (1 - failure_progress * 0.3) + np.random.normal(0, 5)
            gear = max(1, min(6, 4 + np.random.normal(0, 0.5) - failure_progress * 2))
            accx_std = 0.5 + failure_progress * 1.5  # More erratic acceleration
        elif failure_component == "brakes":
            # Brake failure: Reduced brake pressure, longer stopping
            brake_pressure = base_brake_pressure * (1 - failure_progress * 0.6)
            brake_pressure = max(10, brake_pressure)
            pbrake_f = brake_pressure + np.random.normal(0, 5)
            pbrake_r = brake_pressure * 0.8 + np.random.normal(0, 5)
        elif failure_component == "tires":
            # Tire failure: Steering issues, reduced grip
            speed = base_speed * (1 - failure_progress * 0.2) + np.random.normal(0, 5)
            steering_std = 5.0 + failure_progress * 15.0  # More erratic steering
        
        # Create per-lap aggregated features
        record = {
            "vehicle_id": vehicle_id,
            "lap": lap,
            "speed_mean": speed,
            "speed_max": speed * 1.2,
            "Steering_Angle_mean": np.random.normal(0, 2),
            "Steering_Angle_std": steering_std,
            "ath_mean": 95.0 + np.random.normal(0, 2),
            "ath_max": 100.0 + np.random.normal(0, 2),
            "ath_std": 2.0 + np.random.normal(0, 0.5),
            "pbrake_f_mean": pbrake_f,
            "pbrake_f_max": pbrake_f * 1.3,
            "pbrake_r_mean": pbrake_r,
            "pbrake_r_max": pbrake_r * 1.3,
            "nmot_mean": nmot,
            "nmot_max": nmot * 1.1,
            "nmot_std": 200 + np.random.normal(0, 50),
            "accx_can_mean": np.random.normal(0, 0.2),
            "accx_can_max": 2.0 + np.random.normal(0, 0.3),
            "accx_can_min": -2.0 + np.random.normal(0, 0.3),
            "accx_can_std": accx_std,
            "accy_can_mean": np.random.normal(0, 0.2),
            "accy_can_max": 1.5 + np.random.normal(0, 0.3),
            "accy_can_min": -1.5 + np.random.normal(0, 0.3),
            "accy_can_std": 0.5 + np.random.normal(0, 0.1),
            "gear_mean": gear,
            "gear_max": min(6, gear + 1),
            "samples_per_lap": 100 + np.random.randint(-10, 10),
            "failure_component": failure_component if is_failing else None,
            "failure_lap": failure_lap if is_failing else None,
        }
        
        records.append(record)
    
    return pd.DataFrame(records)


def generate_training_dataset(
    num_vehicles: int = 100,
    min_laps: int = 10,
    max_laps: int = 50,
    failure_rate: float = 0.3,
) -> pd.DataFrame:
    """
    Generate a complete training dataset with failure labels.
    
    Args:
        num_vehicles: Number of vehicles to generate
        min_laps: Minimum laps per vehicle
        max_laps: Maximum laps per vehicle
        failure_rate: Probability that a vehicle will have a failure
    """
    
    all_records = []
    components = ["engine", "gearbox", "brakes", "tires"]
    
    for i in range(num_vehicles):
        vehicle_id = f"TRAIN-{i+1:03d}"
        num_laps = np.random.randint(min_laps, max_laps + 1)
        
        # Determine if this vehicle fails
        will_fail = np.random.random() < failure_rate
        
        if will_fail:
            # Randomly select which component fails
            failure_component = np.random.choice(components)
            # Failure occurs in last 20% of race or randomly
            if np.random.random() < 0.7:
                failure_lap = int(num_laps * (0.8 + np.random.random() * 0.2))
            else:
                failure_lap = np.random.randint(int(num_laps * 0.5), num_laps + 1)
        else:
            failure_component = None
            failure_lap = None
        
        # Generate telemetry
        vehicle_data = generate_vehicle_telemetry(
            vehicle_id, num_laps, failure_component, failure_lap
        )
        all_records.append(vehicle_data)
    
    # Combine all vehicles
    df = pd.concat(all_records, ignore_index=True)
    
    # Add STATUS and dnf_flag columns
    df[STATUS_COLUMN] = df["failure_component"].apply(
        lambda x: "DNF" if pd.notna(x) else "FINISHED"
    )
    df[TARGET_COLUMN] = (df[STATUS_COLUMN] == "DNF").astype(int)
    
    # Add component failure type (for multi-class if needed)
    df["failed_component"] = df["failure_component"].fillna("none")
    
    return df


def main():
    """Generate and save training dataset."""
    
    print("Generating synthetic training dataset...")
    print(f"  Vehicles: 100")
    print(f"  Failure rate: 30%")
    print(f"  Laps per vehicle: 10-50")
    
    df = generate_training_dataset(
        num_vehicles=100,
        min_laps=10,
        max_laps=50,
        failure_rate=0.3,
    )
    
    # Save to processed directory
    output_path = PROCESSED_DATA_DIR / "training_data_with_failures.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    print(f"\nDataset generated successfully!")
    print(f"  Total records: {len(df)}")
    print(f"  Vehicles: {df['vehicle_id'].nunique()}")
    print(f"  DNF vehicles: {df[df[TARGET_COLUMN] == 1]['vehicle_id'].nunique()}")
    print(f"  Finished vehicles: {df[df[TARGET_COLUMN] == 0]['vehicle_id'].nunique()}")
    
    # Component failure breakdown
    print(f"\nFailure breakdown by component:")
    failures = df[df["failed_component"] != "none"].groupby("failed_component")["vehicle_id"].nunique()
    for component, count in failures.items():
        print(f"  {component}: {count} vehicles")
    
    print(f"\nSaved to: {output_path}")
    print(f"\nTo use this dataset for training:")
    print(f"  python -m src.main train --dataset-path {output_path}")
    
    # Also save as CSV for inspection
    csv_path = PROCESSED_DATA_DIR / "training_data_with_failures.csv"
    df.to_csv(csv_path, index=False)
    print(f"  Also saved as CSV: {csv_path}")


if __name__ == "__main__":
    main()




