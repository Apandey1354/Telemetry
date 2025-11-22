"""
Generate UNSAFE training dataset based on Vehicle_5.csv structure.

This dataset has FAILURES for training, but ensures:
- Brakes, Tires, and Engines are ALWAYS SAFE (never fail)
- Only Gearbox can fail (to create unsafe scenarios)
- Same row count as Vehicle_5.csv (637,776 rows)
- This is for training the model to recognize gearbox failures
"""

from __future__ import annotations

import random
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from src.config import PROCESSED_DATA_DIR
from src.config import TARGET_COLUMN, STATUS_COLUMN

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)


def generate_vehicle_telemetry_long_format(
    vehicle_id: str,
    num_laps: int,
    samples_per_lap: int = 100,
    failure_component: str | None = None,
    failure_lap: int | None = None,
) -> pd.DataFrame:
    """
    Generate telemetry in long format (like Vehicle_5.csv).
    
    Args:
        vehicle_id: Vehicle identifier
        num_laps: Number of laps
        samples_per_lap: Telemetry samples per lap
        failure_component: Which component fails (only 'gearbox' allowed, others are safe)
        failure_lap: Lap when failure occurs
    """
    
    records = []
    base_time = datetime(2025, 7, 18, 5, 18, 50)
    meta_time = datetime(2025, 7, 20, 16, 46, 40)
    
    # Base values for healthy vehicle
    base_speed = 120.0
    base_rpm = 6000.0
    base_brake_pressure = 50.0
    
    telemetry_signals = [
        'accx_can', 'accy_can', 'ath', 'pbrake_r', 'pbrake_f', 
        'gear', 'Steering_Angle', 'speed', 'nmot'
    ]
    
    for lap in range(1, num_laps + 1):
        # Determine if we're approaching or at failure
        is_failing = False
        failure_progress = 0.0
        
        # Only gearbox can fail (brakes, tires, engines are always safe)
        if failure_component == "gearbox" and failure_lap:
            if lap >= failure_lap:
                is_failing = True
                failure_progress = 1.0
            elif lap >= failure_lap - 3:
                is_failing = True
                failure_progress = (lap - (failure_lap - 3)) / 3.0
        
        # Initialize base values
        speed = base_speed + np.random.normal(0, 5)
        nmot = base_rpm + np.random.normal(0, 200)
        gear = max(1, min(6, 4 + np.random.normal(0, 0.5)))
        accx = np.random.normal(0, 0.2)
        accy = np.random.normal(0, 0.2)
        ath = 99.0 + np.random.normal(0, 1)
        brake_pressure = base_brake_pressure + np.random.normal(0, 5)
        steering_angle = np.random.normal(0, 5)
        
        # Apply gearbox failure pattern if applicable
        if failure_component == "gearbox" and is_failing:
            speed = base_speed * (1 - failure_progress * 0.3) + np.random.normal(0, 5)
            gear = max(1, min(6, 4 + np.random.normal(0, 0.5) - failure_progress * 2))
            accx = accx * (1 + failure_progress * 2)  # More erratic
        
        # Generate samples for this lap
        for sample_idx in range(samples_per_lap):
            timestamp = base_time + timedelta(seconds=lap * 120 + sample_idx * 1.2)
            meta_timestamp = meta_time + timedelta(seconds=lap * 120 + sample_idx * 1.2)
            
            # Add small variations per sample
            sample_speed = speed + np.random.normal(0, 2)
            sample_nmot = nmot + np.random.normal(0, 100)
            sample_gear = max(1, min(6, gear + np.random.normal(0, 0.2)))
            sample_accx = accx + np.random.normal(0, 0.1)
            sample_accy = accy + np.random.normal(0, 0.1)
            sample_ath = ath + np.random.normal(0, 0.5)
            sample_brake = brake_pressure + np.random.normal(0, 3)
            sample_steering = steering_angle + np.random.normal(0, 2)
            
            # Create records for each telemetry signal
            telemetry_values = {
                'accx_can': sample_accx,
                'accy_can': sample_accy,
                'ath': sample_ath,
                'pbrake_r': sample_brake * 0.8,
                'pbrake_f': sample_brake,
                'gear': sample_gear,
                'Steering_Angle': sample_steering,
                'speed': sample_speed,
                'nmot': sample_nmot,
            }
            
            for signal_name, signal_value in telemetry_values.items():
                records.append({
                    'expire_at': '',
                    'lap': lap,
                    'meta_event': 'I_R04_2025-07-20',
                    'meta_session': 'R2',
                    'meta_source': 'kafka:gr-raw',
                    'meta_time': meta_timestamp.isoformat() + 'Z',
                    'original_vehicle_id': vehicle_id,
                    'outing': 0,
                    'telemetry_name': signal_name,
                    'telemetry_value': signal_value,
                    'timestamp': timestamp.isoformat() + 'Z',
                    'vehicle_id': vehicle_id,
                    'vehicle_number': vehicle_id.split('-')[-1] if '-' in vehicle_id else '5',
                })
    
    return pd.DataFrame(records)


def generate_safe_training_dataset(
    target_rows: int = 637776,
    num_vehicles: int = 50,
    failure_rate: float = 0.3,
) -> pd.DataFrame:
    """
    Generate training dataset where brakes, tires, and engines are always safe.
    
    Only gearbox can fail.
    """
    
    print(f"Generating UNSAFE training dataset with ~{target_rows:,} rows...")
    print(f"  Vehicles: {num_vehicles}")
    print(f"  Failure rate: {failure_rate * 100}% (gearbox failures only)")
    print(f"  Brakes, Tires, Engines: ALWAYS SAFE (never fail)")
    print(f"  Gearbox: CAN FAIL (for training unsafe scenarios)")
    
    all_records = []
    # Calculate based on Vehicle_5.csv structure
    # Vehicle_5 has ~637,776 rows, let's estimate:
    # If we have 9 telemetry signals and ~100 samples per signal per lap
    # That's ~900 rows per lap
    # So ~708 laps for 637,776 rows
    
    # More accurate: match Vehicle_5.csv structure exactly
    samples_per_lap = 100  # Samples per signal per lap
    num_signals = 9  # accx_can, accy_can, ath, pbrake_r, pbrake_f, gear, Steering_Angle, speed, nmot
    rows_per_lap = samples_per_lap * num_signals  # ~900 rows per lap
    
    # Calculate laps needed
    total_laps_needed = target_rows // rows_per_lap
    laps_per_vehicle = total_laps_needed // num_vehicles
    
    print(f"  Rows per lap: ~{rows_per_lap}")
    print(f"  Laps per vehicle: ~{laps_per_vehicle}")
    print(f"  Total laps: ~{total_laps_needed}")
    
    for i in range(num_vehicles):
        vehicle_id = f"TRAIN-UNSAFE-{i+1:03d}"
        
        # Determine if this vehicle fails (gearbox only - brakes/tires/engines are always safe)
        will_fail = np.random.random() < failure_rate
        failure_component = "gearbox" if will_fail else None
        failure_lap = None
        
        if will_fail:
            # Failure occurs in last 30% of race (more realistic failure window)
            failure_lap = int(laps_per_vehicle * (0.7 + np.random.random() * 0.3))
            if failure_lap < 1:
                failure_lap = 1
        
        # Generate telemetry
        vehicle_data = generate_vehicle_telemetry_long_format(
            vehicle_id,
            laps_per_vehicle,
            samples_per_lap,
            failure_component,
            failure_lap
        )
        
        all_records.append(vehicle_data)
        
        if (i + 1) % 10 == 0:
            print(f"  Generated {i + 1}/{num_vehicles} vehicles...")
    
    # Combine all vehicles
    df = pd.concat(all_records, ignore_index=True)
    
    # Adjust to match exact target if needed
    if len(df) < target_rows:
        # Add more rows from the last vehicle
        last_vehicle_id = f"TRAIN-SAFE-{num_vehicles:03d}"
        additional_rows_needed = target_rows - len(df)
        additional_laps = (additional_rows_needed // (num_signals * samples_per_lap)) + 1
        
        additional_data = generate_vehicle_telemetry_long_format(
            last_vehicle_id,
            additional_laps,
            samples_per_lap,
            None,  # No failure
            None
        )
        
        # Take only what we need
        additional_data = additional_data.head(additional_rows_needed)
        df = pd.concat([df, additional_data], ignore_index=True)
    elif len(df) > target_rows:
        # Trim to exact size
        df = df.head(target_rows)
    
    print(f"\nGenerated {len(df):,} rows")
    print(f"  Target was: {target_rows:,} rows")
    print(f"  Difference: {abs(len(df) - target_rows):,} rows")
    
    return df


def main():
    """Generate and save unsafe training dataset."""
    
    num_vehicles = 50
    failure_rate = 0.3  # 30% gearbox failures
    
    # Generate dataset
    df = generate_safe_training_dataset(
        target_rows=637776,  # Match Vehicle_5.csv
        num_vehicles=num_vehicles,
        failure_rate=failure_rate,
    )
    
    # Count failures for summary (estimate based on failure rate)
    estimated_failures = int(num_vehicles * failure_rate)
    
    # Save raw telemetry (long format)
    output_path = PROCESSED_DATA_DIR / "unsafe_training_data_raw.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    print(f"\nSaved raw telemetry to: {output_path}")
    
    # Also save as CSV (full file, matching Vehicle_5.csv format)
    csv_path = PROCESSED_DATA_DIR / "unsafe_training_data_raw.csv"
    print(f"Saving full CSV (this may take a moment for {len(df):,} rows)...")
    df.to_csv(csv_path, index=False)
    print(f"Saved full CSV to: {csv_path}")
    
    print("\n" + "="*60)
    print("UNSAFE Training Dataset Summary:")
    print(f"  Total rows: {len(df):,} (matches Vehicle_5.csv)")
    print(f"  Vehicles: {df['vehicle_id'].nunique()}")
    print(f"  Max laps: {df['lap'].max()}")
    print(f"  Telemetry signals: {df['telemetry_name'].nunique()}")
    print(f"  Expected failures: ~{estimated_failures} vehicles (gearbox only)")
    print("\nSafety Guarantees:")
    print("  ✓ Brakes: ALWAYS SAFE (never fail)")
    print("  ✓ Tires: ALWAYS SAFE (never fail)")
    print("  ✓ Engine: ALWAYS SAFE (never fail)")
    print("  ✗ Gearbox: CAN FAIL (for training)")
    print("\nNext Steps:")
    print("  1. Upload this CSV through the React app to process it")
    print("  2. Or process manually: python -m src.main ingest")
    print("  3. Train model: python -m src.main train")
    print("="*60)


if __name__ == "__main__":
    main()

