# Mechanical Karma Predictor - Setup Guide

## 📋 Overview

**Mechanical Karma Predictor** is an end-to-end machine learning system for analyzing race telemetry data and predicting mechanical failure risks in racing vehicles. The system computes per-lap "Mechanical Karma" risk scores for vehicle components (engine, gearbox, brakes, tires) and provides real-time visualization through a modern React dashboard.

### What It Does

- **Telemetry Processing**: Ingests raw race telemetry CSV files and processes them into per-lap aggregated features
- **Feature Engineering**: Extracts meaningful statistics (mean, max, min, std) from telemetry signals like speed, RPM, brake pressure, steering angle, etc.
- **Machine Learning Predictions**: Uses trained models to predict:
  - Overall DNF (Did Not Finish) probability
  - Component-specific failure risks (engine, gearbox, brakes, tires)
- **Mechanical Karma Scoring**: Computes real-time component health scores that track degradation over laps
- **Interactive Dashboard**: React-based web interface for:
  - Uploading telemetry files
  - Viewing vehicle metrics and telemetry trends
  - Monitoring karma scores and ML predictions
  - Replaying race data lap-by-lap

### Key Features

- 📤 **File Upload**: Upload telemetry CSV files directly through the web interface
- 🚗 **Multi-Vehicle Support**: Analyze multiple vehicles from the same race
- 📊 **Interactive Charts**: Plotly-powered visualizations of telemetry trends
- ⚡ **Real-Time Karma Scores**: Component-level mechanical karma tracking (engine, gearbox, brakes, tires)
- 🤖 **ML Predictions**: AI-powered failure risk predictions
- ▶️ **Replay Controls**: Step through laps to see how karma and predictions evolve
- 📈 **Metrics Display**: Key statistics (laps, speed, DNF status)

---

## 🏗️ Project Structure

```
Hack The Track/
├── backend/                    # Python backend
│   ├── api.py                  # Flask REST API server
│   ├── requirements.txt        # Python dependencies
│   ├── artifacts/              # Trained ML models (REQUIRED)
│   │   ├── karma_model.pkl
│   │   ├── feature_scaler.pkl
│   │   ├── component_model_*.pkl
│   │   └── component_scaler_*.pkl
│   ├── logs/                   # Application logs
│   ├── src/                    # Backend source code
│   │   ├── main.py             # CLI entry point
│   │   ├── config.py           # Configuration constants
│   │   ├── data_loader.py      # CSV reading utilities
│   │   ├── feature_engineering.py  # Lap aggregation & features
│   │   ├── modeling.py         # ML model training & inference
│   │   ├── component_modeling.py   # Component-specific models
│   │   ├── karma_stream.py     # Mechanical karma computation
│   │   ├── firebase_push.py    # Firebase integration (optional)
│   │   └── utils.py            # Logging & utilities
│   ├── generate_training_data.py
│   ├── train_components.py
│   └── local_dashboard.py      # Streamlit dashboard (alternative)
│
├── frontend/                   # React frontend
│   ├── package.json            # Node.js dependencies
│   ├── vite.config.js          # Vite configuration
│   ├── src/
│   │   ├── App.jsx             # Main app component
│   │   ├── api.js              # API client
│   │   ├── components/         # React components
│   │   │   ├── FileUpload.jsx
│   │   │   ├── VehicleSelector.jsx
│   │   │   ├── MetricsDisplay.jsx
│   │   │   ├── TimeSeriesChart.jsx
│   │   │   ├── KarmaDisplay.jsx
│   │   │   ├── ModelPredictionDisplay.jsx
│   │   │   └── ReplayControls.jsx
│   │   └── main.jsx            # Entry point
│   └── index.html
│
└── data/                       # Data directory
    ├── raw/                    # Place source CSVs here
    ├── interim/                # Intermediate processing files
    └── processed/              # Final processed datasets
        ├── per_lap_features.parquet
        └── karma_stream.parquet
```

---

## 🔧 Prerequisites

Before setting up the project, ensure you have the following installed:

### Required Software

- **Python 3.10+** ([Download](https://www.python.org/downloads/))
  - Verify: `python --version` or `python3 --version`
- **Node.js 18+** and **npm** ([Download](https://nodejs.org/))
  - Verify: `node --version` and `npm --version`
- **pip** (usually comes with Python)
  - Verify: `pip --version`

### System Requirements

- **Operating System**: Windows, macOS, or Linux
- **Disk Space**: At least 2GB free space
- **RAM**: 4GB minimum (8GB recommended for large datasets)
- **Internet Connection**: Required for downloading dependencies

---

## 📦 Installation

### Step 1: Clone or Download the Project

If you have the project files, navigate to the project directory:

```bash
cd "Hack The Track"
```

### Step 2: Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create a Python virtual environment (recommended):**
   
   **Windows:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
   
   **macOS/Linux:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   This will install:
   - Core data science libraries (pandas, numpy, scikit-learn, tensorflow)
   - Flask API server
   - Firebase integration
   - Visualization tools (plotly, matplotlib)
   - And other required packages

4. **Verify model artifacts exist:**
   
   Check that the following files exist in `backend/artifacts/`:
   - `karma_model.pkl` - Main DNF prediction model
   - `feature_scaler.pkl` - Feature scaler
   - `component_model_engine.pkl` (optional)
   - `component_model_gearbox.pkl` (optional)
   - `component_model_brakes.pkl` (optional)
   - `component_model_tires.pkl` (optional)
   
   **Note:** If models are missing, see the "Training Models" section below.

5. **Create data directories (auto-created, but you can verify):**
   ```bash
   # The application auto-creates these, but you can check:
   mkdir -p ../data/processed
   mkdir -p ../data/raw
   mkdir -p ../data/interim
   ```

### Step 3: Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd ../frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```
   
   This will install:
   - React 18
   - Vite (build tool)
   - Plotly.js (charts)
   - Axios (HTTP client)
   - And other frontend dependencies

3. **Verify installation:**
   ```bash
   npm list --depth=0
   ```

---

## ⚙️ Configuration

### Backend Configuration

The backend uses environment variables for configuration. Create a `.env` file in the `backend/` directory (optional):

```env
# Data directory (default: ../data)
DATA_ROOT=../data

# Firebase configuration (optional, for real-time database)
FIREBASE_DB_URL=https://your-project.firebaseio.com
SERVICE_ACCOUNT_PATH=../secrets/serviceAccountKey.json

# Model configuration
MODEL_TYPE=random_forest
TEST_SPLIT=0.2
SEED=42

# API port (configured in api.py)
PORT=5000
```

### Frontend Configuration

The frontend expects the backend API at `http://localhost:5000` by default.

To change the API URL, edit `frontend/vite.config.js`:

```javascript
export default {
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
}
```

For production, update `frontend/src/api.js` to point to your production API URL.

---

## 🚀 Running the Application

### Development Mode (Recommended for Testing)

You'll need **two terminal windows**:

#### Terminal 1: Start Backend API

```bash
cd backend

# Activate virtual environment (if not already active)
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Start Flask API server
python api.py
```

The backend will start on `http://localhost:5000`

You should see:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

#### Terminal 2: Start Frontend

```bash
cd frontend

# Start Vite development server
npm run dev
```

The frontend will start on `http://localhost:3000` (or another port if 3000 is busy)

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

### Access the Application

1. Open your web browser
2. Navigate to `http://localhost:3000`
3. You should see the Mechanical Karma dashboard

### Production Mode

For production deployment, see `DEPLOYMENT.md` for detailed instructions.

---

## 📊 Using the Application

### 1. Upload Telemetry Data

1. **Click "Upload File"** in the sidebar
2. **Select a telemetry CSV file** with the following structure:

   **Required columns:**
   - `vehicle_id` - Unique vehicle identifier
   - `lap` - Lap number
   - `telemetry_name` and `telemetry_value` (for long format)
   - OR individual telemetry columns (for wide format)
   - `meta_time` or `timestamp` - Timestamp for time-based processing

   **Example telemetry signals:**
   - `speed`, `Steering_Angle`, `ath`, `pbrake_f`, `pbrake_r`
   - `nmot` (RPM), `accx_can`, `accy_can`, `gear`

3. **Wait for processing** - The file will be uploaded and processed automatically
4. **View results** - Once processed, vehicles will appear in the dropdown

### 2. Select a Vehicle

1. **Choose a vehicle** from the "Vehicle Selection" dropdown
2. **View metrics** including:
   - Total laps recorded
   - Average speed
   - DNF status
   - Lap range

### 3. Explore the Dashboard

The dashboard shows several sections:

- **Performance Metrics**: Key statistics about the selected vehicle
- **Telemetry Analysis**: Interactive charts showing telemetry trends over laps
- **AI Failure Prediction**: ML model predictions for DNF probability and component risks
- **Mechanical Karma Analysis**: Component health scores (engine, gearbox, brakes, tires)

### 4. Use Replay Controls

1. **Enable Replay Mode** using the toggle in the sidebar
2. **Step through laps** using the previous/next buttons or slider
3. **Watch karma scores and predictions evolve** as you progress through the race
4. **Use play/pause** for automatic progression

---

## 🔌 API Endpoints

The backend provides a REST API at `http://localhost:5000/api`:

### Health Check
- `GET /api/health` - Check if backend is running
  ```bash
  curl http://localhost:5000/api/health
  ```

### File Upload & Processing
- `POST /api/upload` - Upload and process telemetry file
  ```bash
  curl -X POST -F "file=@your_file.csv" http://localhost:5000/api/upload
  ```

### Data Retrieval
- `GET /api/process` - Get all processed vehicle data
- `GET /api/vehicle/<vehicle_id>` - Get data for specific vehicle
- `GET /api/karma/<vehicle_id>` - Get karma scores for vehicle
- `GET /api/karma/<vehicle_id>/lap/<max_lap>` - Get karma up to specific lap (for replay)
- `GET /api/model-prediction/<vehicle_id>` - Get ML model predictions

### Example API Usage

```bash
# Get all vehicles
curl http://localhost:5000/api/process

# Get specific vehicle data
curl http://localhost:5000/api/vehicle/GR86-002-2

# Get karma scores
curl http://localhost:5000/api/karma/GR86-002-2

# Get karma up to lap 10
curl http://localhost:5000/api/karma/GR86-002-2/lap/10

# Get model predictions
curl http://localhost:5000/api/model-prediction/GR86-002-2
```

---

## 🧪 Training Models

If model artifacts are missing or you want to retrain with new data:

### Step 1: Prepare Training Data

You can either:
- Use existing processed data: `data/processed/per_lap_features.parquet`
- Generate training data with failure labels:
  ```bash
  cd backend
  python generate_training_data.py
  ```

### Step 2: Train the Main Model

```bash
cd backend

# Activate virtual environment
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Train the main DNF prediction model
python -m src.main train
```

This will:
- Load the training dataset
- Split into train/test sets
- Train a Random Forest model (or configured model type)
- Save model to `artifacts/karma_model.pkl`
- Save scaler to `artifacts/feature_scaler.pkl`
- Generate training metrics

### Step 3: Train Component Models (Optional)

```bash
# Train component-specific failure prediction models
python train_components.py
```

This will train separate models for:
- Engine failure prediction
- Gearbox failure prediction
- Brakes failure prediction
- Tires failure prediction

Models are saved to `artifacts/component_model_*.pkl`

### Step 4: Verify Models

```bash
# Check that models were created
ls artifacts/*.pkl
```

You should see:
- `karma_model.pkl`
- `feature_scaler.pkl`
- `component_model_engine.pkl` (if component training was run)
- `component_model_gearbox.pkl`
- `component_model_brakes.pkl`
- `component_model_tires.pkl`

---

## 🔄 Backend CLI Commands

The backend provides a CLI for data processing and model management:

```bash
cd backend

# Activate virtual environment first
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Build per-lap dataset from raw CSVs
python -m src.main ingest

# Train the karma model
python -m src.main train

# Run inference and save karma scores
python -m src.main infer

# Generate karma stream (component scores)
python -m src.main karma-stream

# Train component models
python -m src.main train-components

# Push scores to Firebase (optional)
python -m src.main push-firebase --service-account ../secrets/serviceAccountKey.json --db-url https://your-project.firebaseio.com
```

---

## 🐛 Troubleshooting

### Backend Issues

#### Problem: Module not found errors
```bash
# Solution: Ensure virtual environment is activated and dependencies are installed
cd backend
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

#### Problem: Model files not found
```bash
# Solution: Train the models first
cd backend
python -m src.main train
python train_components.py  # Optional
```

#### Problem: Port 5000 already in use
```bash
# Windows: Find and kill the process
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux: Find and kill the process
lsof -i :5000
kill -9 <PID>

# Or change the port in api.py
```

#### Problem: Import errors
```bash
# Solution: Ensure you're running from the correct directory
cd backend
python api.py  # Not from project root
```

### Frontend Issues

#### Problem: npm install fails
```bash
# Solution: Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### Problem: API requests fail (CORS errors)
```bash
# Solution: Check that backend is running on port 5000
# Verify vite.config.js proxy configuration
# Check browser console for specific error messages
```

#### Problem: Build fails
```bash
# Solution: Check Node.js version (needs 18+)
node --version

# Update dependencies
cd frontend
npm update
```

#### Problem: Frontend can't connect to backend
```bash
# Solution: 
# 1. Verify backend is running: curl http://localhost:5000/api/health
# 2. Check vite.config.js proxy settings
# 3. Check browser console for errors
# 4. Verify no firewall blocking port 5000
```

### Data Issues

#### Problem: No data after upload
```bash
# Solution: 
# 1. Check CSV file format - ensure required columns exist (vehicle_id, lap)
# 2. Check backend logs in backend/logs/
# 3. Verify file was processed: check data/processed/per_lap_features.parquet
# 4. Check browser console for API errors
```

#### Problem: Karma scores not showing
```bash
# Solution:
# 1. Verify karma_stream.parquet exists in data/processed/
# 2. Or upload a file with lap information
# 3. Check that models are trained and available
# 4. Check backend logs for errors
```

#### Problem: Model predictions not showing
```bash
# Solution:
# 1. Verify karma_model.pkl exists in backend/artifacts/
# 2. Train the model: python -m src.main train
# 3. Check backend logs for model loading errors
```

### General Issues

#### Problem: Virtual environment not activating
```bash
# Windows: Use backslashes
venv\Scripts\activate

# macOS/Linux: Use forward slashes
source venv/bin/activate

# If still not working, recreate the virtual environment
rm -rf venv  # or rmdir /s venv on Windows
python -m venv venv
# Then activate again
```

#### Problem: Permission errors
```bash
# Solution: Run with appropriate permissions
# On Linux/Mac, you might need sudo for some operations
# On Windows, run as administrator if needed
```

---

## 📝 Data Format Requirements

### Telemetry CSV Format

Your telemetry CSV file should have one of these formats:

#### Format 1: Long Format (Recommended)
```
vehicle_id,lap,meta_time,telemetry_name,telemetry_value
GR86-002-2,1,2024-01-01 10:00:00,speed,120.5
GR86-002-2,1,2024-01-01 10:00:01,nmot,6500
GR86-002-2,1,2024-01-01 10:00:02,pbrake_f,85.2
...
```

#### Format 2: Wide Format
```
vehicle_id,lap,meta_time,speed,nmot,pbrake_f,pbrake_r,Steering_Angle,...
GR86-002-2,1,2024-01-01 10:00:00,120.5,6500,85.2,45.3,12.5,...
GR86-002-2,1,2024-01-01 10:00:01,125.3,6800,0.0,0.0,8.2,...
...
```

### Required Columns

- `vehicle_id` - **Required**: Unique identifier for each vehicle
- `lap` - **Required**: Lap number
- `meta_time` or `timestamp` - **Required**: Timestamp for time-based processing

### Supported Telemetry Signals

The system processes these telemetry signals (if present):
- `speed` - Vehicle speed
- `nmot` - Engine RPM
- `pbrake_f` - Front brake pressure
- `pbrake_r` - Rear brake pressure
- `Steering_Angle` - Steering angle
- `ath` - Throttle position
- `accx_can` - Longitudinal acceleration
- `accy_can` - Lateral acceleration
- `gear` - Current gear

---

## 📚 Additional Resources

- **Backend Documentation**: See `backend/README.md` for detailed backend usage
- **Frontend Documentation**: See `frontend/README.md` for frontend details
- **Deployment Guide**: See `DEPLOYMENT.md` for production deployment instructions
- **Training Data Guide**: See `TRAINING_DATA_GUIDE.md` for information on training datasets

---

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs**: 
   - Backend logs: `backend/logs/`
   - Browser console: Open Developer Tools (F12) → Console tab

2. **Verify installation**:
   ```bash
   # Backend
   cd backend
   python --version  # Should be 3.10+
   pip list  # Check installed packages
   
   # Frontend
   cd frontend
   node --version  # Should be 18+
   npm list --depth=0  # Check installed packages
   ```

3. **Test API connectivity**:
   ```bash
   curl http://localhost:5000/api/health
   ```

4. **Check file permissions**: Ensure the application has read/write access to:
   - `data/` directory
   - `backend/artifacts/` directory
   - `backend/logs/` directory

---

## ✅ Quick Start Checklist

- [ ] Python 3.10+ installed
- [ ] Node.js 18+ and npm installed
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Model artifacts exist in `backend/artifacts/` (or trained)
- [ ] Backend API running on port 5000
- [ ] Frontend running on port 3000
- [ ] Can access dashboard at `http://localhost:3000`
- [ ] Can upload and process telemetry files

---

## 🎯 Next Steps

After setup:

1. **Upload a telemetry file** through the web interface
2. **Explore the dashboard** features
3. **Train models** with your own data (if needed)
4. **Customize features** in `backend/src/config.py`
5. **Deploy to production** (see `DEPLOYMENT.md`)

---

**Last Updated**: Comprehensive setup guide created for Mechanical Karma Predictor project.

