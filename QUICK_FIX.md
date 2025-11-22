# Quick Fix for File Upload Issue

The API has been updated to actually process uploaded CSV files. Here's what changed:

## What Was Fixed

1. **File Processing**: The upload endpoint now:
   - Processes the CSV file (pivots telemetry signals if in long format)
   - Aggregates data per lap
   - Generates karma scores
   - Saves processed data to `data/processed/`

2. **Data Format Support**: The API now handles:
   - Long format data (telemetry_name, telemetry_value columns)
   - Data with existing lap information
   - Multiple timestamp column formats (meta_time, timestamp)

## To Apply the Fix

1. **Restart the Backend Server**:
   - Stop the current backend server (Ctrl+C)
   - Start it again:
     ```bash
     cd backend
     python api.py
     ```

2. **Upload Your File Again**:
   - Go to http://localhost:3000
   - Use the file upload component
   - Select your `data.csv` file
   - Click "Upload"

3. **The System Will**:
   - Process the CSV file
   - Generate per-lap features
   - Compute karma scores
   - Display vehicles in the dropdown
   - Show charts and karma visualizations

## Expected Behavior

After uploading `data.csv`:
- You should see a success message with number of vehicles found
- Vehicles should appear in the dropdown
- Selecting a vehicle should show:
  - Metrics (laps, speed, DNF flag)
  - Time series charts
  - Karma scores per component

## Troubleshooting

If you still see issues:

1. **Check Browser Console** (F12) for errors
2. **Check Backend Terminal** for error messages
3. **Verify File Format**: Your CSV should have:
   - `vehicle_id` column
   - `lap` column (or lap information)
   - `telemetry_name` and `telemetry_value` columns (if in long format)
   - Or already pivoted telemetry columns

4. **Check Processed Files**:
   ```bash
   ls data/processed/
   ```
   You should see `per_lap_features.parquet` and `karma_stream.parquet` after upload






