# React App Setup Guide

This guide will help you set up and run the new React dashboard that replaces the Streamlit app.

## Quick Start

### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install Flask and flask-cors along with all other dependencies.

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 3. Start the Backend API

In one terminal:

```bash
cd backend
python api.py
```

The API will run on `http://localhost:5000`

### 4. Start the React App

In another terminal:

```bash
cd frontend
npm run dev
```

The app will run on `http://localhost:3000` and automatically open in your browser.

## How It Works

### Backend API (`backend/api.py`)

The Flask API provides endpoints for:
- **File Upload**: `/api/upload` - Accepts telemetry CSV files
- **Data Processing**: `/api/process` - Returns processed vehicle data
- **Vehicle Data**: `/api/vehicle/<id>` - Get specific vehicle metrics
- **Karma Scores**: `/api/karma/<id>` - Get mechanical karma scores

### React Frontend (`frontend/`)

The React app provides:
- File upload interface
- Vehicle selection dropdown
- Interactive Plotly charts
- Karma score visualization
- Replay controls for stepping through laps

## Features

✅ **File Upload**: Upload telemetry CSV files directly in the browser
✅ **Real-time Visualization**: See telemetry trends and karma scores
✅ **Component Tracking**: Track engine, gearbox, brakes, and tires separately
✅ **Replay Mode**: Step through laps to see how karma evolves over time
✅ **Responsive Design**: Works on desktop and mobile devices

## Troubleshooting

### Backend won't start
- Make sure port 5000 is not in use
- Check that all Python dependencies are installed
- Ensure processed data exists in `data/processed/per_lap_features.parquet`

### Frontend won't start
- Make sure Node.js 18+ is installed
- Run `npm install` in the frontend directory
- Check that port 3000 is available

### No data showing
- Make sure you've run the ingestion pipeline first:
  ```bash
  cd backend
  python -m src.main ingest
  python -m src.main karma-stream
  ```
- Or upload a telemetry file through the web interface

### CORS errors
- The Flask API has CORS enabled, but if you see errors, check that the API is running on port 5000
- The Vite proxy should handle this automatically

## Next Steps

1. **Process your data** (if not already done):
   ```bash
   cd backend
   python -m src.main ingest
   python -m src.main train
   python -m src.main infer
   python -m src.main karma-stream
   ```

2. **Start both servers** (backend and frontend)

3. **Open the app** at `http://localhost:3000`

4. **Upload a file** or select from existing processed data

## Differences from Streamlit App

- **File Upload**: Now built into the web interface
- **Better Performance**: React is faster for large datasets
- **Modern UI**: Cleaner, more responsive design
- **API-based**: Can be deployed separately or integrated with other services
- **No Python dependency in browser**: Pure JavaScript frontend

Enjoy your new React dashboard! 🚀






