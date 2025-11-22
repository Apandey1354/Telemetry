# Mechanical Karma Predictor

End-to-end project for computing per-lap “Mechanical Karma” risk scores from race telemetry and visualizing them on a React dashboard powered by Firebase Realtime Database.

## Repository Structure

```
Hack The Track/
  ├── backend/           # Python data + model pipeline
  ├── frontend/          # React dashboard (create-react-app scaffold TBD)
  └── data/
      ├── raw/           # Drop source CSVs here
      ├── interim/       # Lap-tagged telemetry (auto-generated)
      └── processed/     # Per-lap features & scored datasets
```

## Phase Overview

1. **Phase 0 – Environment**
   - Install Python 3.10+, Node.js 18+, npm.
   - `pip install -r backend/requirements.txt` inside a virtual environment.
   - Initialize Firebase project and download `serviceAccountKey.json` into `secrets/`.
   - Create React app via `npx create-react-app frontend/karma-dashboard` (pending).

2. **Phase 1 – Data Preparation**
   - Place telemetry + metadata CSVs inside `data/raw/`.
   - `cd backend && python -m src.main ingest` to build per-lap features.

3. **Phase 2 – Modeling**
   - `python -m src.main train` trains the configured model (Random Forest by default).
   - `python -m src.main infer` scores laps and writes `data/processed/per_lap_with_karma.parquet`.

4. **Phase 3 – Firebase Integration**
   - `python -m src.main push-firebase --service-account ../secrets/serviceAccountKey.json --db-url https://<id>.firebaseio.com`.
   - Data is written beneath `/karma/{vehicle_id}`.

5. **Phase 4 – Frontend Dashboard**
   - React app subscribes to `/karma` node and renders real-time cards/bars.
   - Frontend implementation will live under `frontend/`.

## Data Files

Drop the following in `data/raw/` (filenames can be overridden via env vars):

- `R1_vir_telemetry_data.csv`
- `vir_lap_start_R1.csv`
- `vir_lap_end_R1.csv`
- `03_Provisional Results_Race 1_Anonymized.CSV`
- `weather_vir_R1.csv` (optional)

## Next Steps

1. Add the CSVs (user action).
2. Run the ingestion command and inspect generated parquet files.
3. Tune model hyperparameters or augment features as needed.
4. Scaffold the React dashboard and connect it to Firebase.
5. Iterate on alerting/visualization features (trend charts, component-level karma, etc.).

For detailed backend usage, see `backend/README.md`. Frontend docs will be added once the dashboard scaffold is generated.

