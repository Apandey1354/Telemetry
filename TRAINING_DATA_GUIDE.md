# Training Data Generation Guide

## Overview

The `generate_training_data.py` script creates a synthetic dataset with labeled component failures for training the Mechanical Karma model.

## Generated Dataset

**Location**: `data/processed/training_data_with_failures.parquet`

### Dataset Statistics
- **Total Vehicles**: 100
- **Total Laps**: ~2,890 records
- **Failure Rate**: 30% (24 vehicles with failures)
- **Laps per Vehicle**: 10-50 laps

### Failure Distribution
- **Engine Failures**: 5 vehicles
- **Gearbox Failures**: 5 vehicles  
- **Brake Failures**: 7 vehicles
- **Tire Failures**: 7 vehicles
- **No Failures**: 76 vehicles

## Failure Patterns

The synthetic data includes realistic failure patterns:

### Engine Failure
- **Symptoms**: RPM drops, speed decreases, temperature anomalies
- **Telemetry Changes**: 
  - `nmot_mean` decreases by up to 50%
  - `speed_mean` decreases by up to 40%
  - Degradation occurs over last 3 laps before failure

### Gearbox Failure
- **Symptoms**: Gear shifting issues, acceleration problems
- **Telemetry Changes**:
  - `gear_mean` becomes erratic
  - `accx_can_std` increases (more erratic acceleration)
  - `speed_mean` decreases by up to 30%

### Brake Failure
- **Symptoms**: Reduced brake pressure, longer stopping distances
- **Telemetry Changes**:
  - `pbrake_f_max` and `pbrake_r_max` decrease by up to 60%
  - Brake pressure drops significantly

### Tire Failure
- **Symptoms**: Steering issues, reduced grip
- **Telemetry Changes**:
  - `Steering_Angle_std` increases significantly (more erratic)
  - `speed_mean` decreases slightly

## Dataset Columns

The dataset includes all required features for training:

### Per-Lap Aggregated Features
- `speed_mean`, `speed_max`
- `Steering_Angle_mean`, `Steering_Angle_std`
- `ath_mean`, `ath_max`, `ath_std`
- `pbrake_f_mean`, `pbrake_f_max`
- `pbrake_r_mean`, `pbrake_r_max`
- `nmot_mean`, `nmot_max`, `nmot_std`
- `accx_can_mean`, `accx_can_max`, `accx_can_min`, `accx_can_std`
- `accy_can_mean`, `accy_can_max`, `accy_can_min`, `accy_can_std`
- `gear_mean`, `gear_max`
- `samples_per_lap`

### Labels
- `vehicle_id`: Vehicle identifier
- `lap`: Lap number
- `STATUS`: "DNF" or "FINISHED"
- `dnf_flag`: Binary label (1 = DNF, 0 = Finished)
- `failed_component`: Which component failed ("engine", "gearbox", "brakes", "tires", "none")
- `failure_component`: Component that failed (NaN if no failure)
- `failure_lap`: Lap number when failure occurred (NaN if no failure)

## Training the Model

### Option 1: Use the generated dataset directly

```bash
cd backend
python -m src.main train --dataset-path data/processed/training_data_with_failures.parquet
```

### Option 2: Use as part of your existing pipeline

The dataset is already in the correct format and can be used directly with the training command.

## Customizing the Dataset

You can modify `generate_training_data.py` to:

1. **Change dataset size**:
   ```python
   df = generate_training_dataset(
       num_vehicles=200,  # More vehicles
       min_laps=15,
       max_laps=60,
       failure_rate=0.4,  # 40% failure rate
   )
   ```

2. **Adjust failure patterns**: Modify the telemetry generation in `generate_vehicle_telemetry()` to change how failures manifest

3. **Add more components**: Extend the failure patterns to include other components

## Validation

After training, you can validate the model:

```bash
# Check training metrics
cat backend/artifacts/training_metrics.json

# Run inference on test data
python -m src.main infer
```

## Notes

- The dataset uses realistic telemetry patterns with noise
- Failures typically occur in the last 20% of a race
- Degradation patterns appear 3 laps before actual failure
- All telemetry values are within realistic ranges
- The dataset is balanced for both failure and non-failure cases

## Next Steps

1. **Train the model** with the generated dataset
2. **Evaluate performance** on test data
3. **Tune hyperparameters** if needed
4. **Use the trained model** for inference on real telemetry data






