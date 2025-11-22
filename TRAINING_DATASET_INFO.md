# Unsafe Training Dataset

## Overview

Created an **UNSAFE** training dataset with **637,776 rows** (matching Vehicle_5.csv size) where:

### Safety Guarantees ✅
- **Brakes**: ALWAYS SAFE (never fail)
- **Tires**: ALWAYS SAFE (never fail)  
- **Engine**: ALWAYS SAFE (never fail)

### Failure Scenarios ⚠️
- **Gearbox**: CAN FAIL (30% of vehicles have gearbox failures)
- This creates unsafe scenarios for training while keeping brakes/tires/engines safe

## Dataset Details

- **File**: `data/processed/unsafe_training_data_raw.csv`
- **Format**: Long format (same as Vehicle_5.csv)
- **Rows**: 637,776 (exact match to Vehicle_5.csv)
- **Vehicles**: 50 vehicles
- **Structure**: 
  - `telemetry_name` and `telemetry_value` columns
  - Same format as Vehicle_5.csv
  - Can be uploaded directly through React app

## How to Use

### Option 1: Upload via React App
1. Start the backend API: `cd backend && python api.py`
2. Start React app: `cd frontend && npm run dev`
3. Upload `data/processed/unsafe_training_data_raw.csv` through the web interface
4. The system will process it automatically

### Option 2: Process Manually
```bash
# Copy to raw data directory
cp data/processed/unsafe_training_data_raw.csv data/raw/R1_vir_telemetry_data.csv

# Process it
cd backend
python -m src.main ingest

# Train the model
python -m src.main train --dataset-path ../data/processed/per_lap_features.parquet
```

## Training the Model

After processing, train with:

```bash
cd backend
python -m src.main train --dataset-path ../data/processed/per_lap_features.parquet
```

The model will learn:
- ✅ Brakes, Tires, Engines are always safe (no failure patterns)
- ⚠️ Gearbox can fail (will learn gearbox failure patterns)

## Expected Results

When you train component models:

- **Engine model**: Should predict 0% risk (always safe)
- **Brakes model**: Should predict 0% risk (always safe)
- **Tires model**: Should predict 0% risk (always safe)
- **Gearbox model**: Should predict failures correctly (30% of vehicles fail)

This creates a model that knows brakes/tires/engines are safe, but can detect gearbox issues.






