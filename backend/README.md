# Mechanical Karma Backend

This backend folder contains the Python tooling for preparing telemetry data, training a prototype Mechanical Karma model, and pushing the resulting scores to Firebase for live visualization.

## Contents

- `requirements.txt` – Python dependencies for the end-to-end pipeline.
- `src/` – Source modules grouped by responsibility:
  - `config.py` – Centralized file paths and column mappings.
  - `data_loader.py` – Helpers to read raw CSVs and validate schemas.
  - `feature_engineering.py` – Lap assignment and per-lap aggregation logic.
  - `modeling.py` – Utilities for splitting data, training models, and saving artifacts.
  - `firebase_push.py` – Functions to push scores to Firebase Realtime Database.
  - `main.py` – Orchestration entry point (CLI) tying all steps together.

## Quickstart

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # or source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
```

Place the supplied CSVs inside `../data/raw/`:

```
data/raw/
  ├── R1_vir_telemetry_data.csv
  ├── vir_lap_start_R1.csv
  ├── vir_lap_end_R1.csv
  ├── 03_Provisional Results_Race 1_Anonymized.CSV
  └── weather_vir_R1.csv          # optional
```

## Running the Pipeline

```bash
python -m src.main ingest       # builds per-lap dataset
python -m src.main train        # trains baseline model
python -m src.main infer        # runs inference on latest dataset
python -m src.main push-firebase --service-account ../secrets/serviceAccountKey.json
python -m src.main karma-stream  # generate per-component Mechanical Karma
python visualize_parquet.py --vehicle GR86-002-2  # quick lap visualization
streamlit run local_dashboard.py  # local frontend (no Firebase)
```

Each sub-command produces log output in `backend/logs/` (directory auto-created on first run) and writes intermediate files to `../data/interim/` and final datasets to `../data/processed/`.

## Environment Variables

Create a `.env` inside `backend/` (optional) for overrides:

```
DATA_ROOT=../data
FIREBASE_DB_URL=https://<project-id>.firebaseio.com
```

Any value specified in `.env` supersedes defaults in `config.py`.

## Next Steps

1. Drop the CSVs into `data/raw/`.
2. Run `python -m src.main ingest` to verify parsing and feature generation.
3. Iterate on `modeling.py` to test different algorithms (Random Forest, MLP, LSTM).
4. Configure Firebase credentials and run `push-firebase`.
5. Wire up the frontend dashboard to the `/karma` tree in Realtime Database.
6. Use `visualize_parquet.py` for quick lap-to-lap comparisons during experimentation.
7. Run `streamlit run local_dashboard.py` to explore Mechanical Karma locally without Firebase.

Feel free to expand on this structure as the project grows (e.g., add notebooks, automated tests, or deployment scripts).***




