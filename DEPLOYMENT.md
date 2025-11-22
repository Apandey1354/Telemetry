# Deployment Guide - Mechanical Karma Application

This guide provides step-by-step instructions for deploying the Mechanical Karma application (frontend, backend, and data) to a production environment.

## 📋 Prerequisites

Before deploying, ensure you have:

- **Python 3.10+** installed
- **Node.js 18+** and **npm** installed
- **pip** (Python package manager)
- At least **2GB** of free disk space
- Internet connection for downloading dependencies

## 📁 Project Structure

After cleanup, your deployment-ready structure should look like:

```
Hack The Track/
├── backend/
│   ├── api.py                    # Flask API server
│   ├── requirements.txt          # Python dependencies
│   ├── artifacts/                # Trained ML models (REQUIRED)
│   │   ├── karma_model.pkl
│   │   ├── feature_scaler.pkl
│   │   ├── component_model_*.pkl
│   │   └── component_scaler_*.pkl
│   └── src/                      # Backend source code
├── frontend/
│   ├── package.json              # Node.js dependencies
│   ├── vite.config.js            # Vite configuration
│   └── src/                      # React source code
└── data/
    └── processed/                # Processed data (optional)
        ├── per_lap_features.parquet
        └── karma_stream.parquet
```

## 🚀 Deployment Steps

### Step 1: Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create a Python virtual environment (recommended):**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify model artifacts exist:**
   ```bash
   # Check that these files exist:
   # backend/artifacts/karma_model.pkl
   # backend/artifacts/feature_scaler.pkl
   # backend/artifacts/component_model_*.pkl (optional)
   ```

   If models are missing, you'll need to train them first (see "Training Models" section below).

5. **Create data directories (if they don't exist):**
   ```bash
   # The application will auto-create these, but you can create them manually:
   mkdir -p ../data/processed
   mkdir -p ../data/raw
   mkdir -p ../data/interim
   ```

### Step 2: Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd ../frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Build the production frontend:**
   ```bash
   npm run build
   ```

   This creates an optimized production build in `frontend/dist/`.

### Step 3: Running the Application

#### Option A: Development Mode (Testing)

**Terminal 1 - Start Backend:**
```bash
cd backend
python api.py
```

The backend will run on `http://localhost:5000`

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm run dev
```

The frontend will run on `http://localhost:3000` and automatically proxy API requests to the backend.

#### Option B: Production Mode

**Start Backend:**
```bash
cd backend
# Using gunicorn (recommended for production)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api:app

# OR using Flask's built-in server (development only)
python api.py
```

**Serve Frontend:**
```bash
cd frontend
# Serve the built files using a static file server
# Option 1: Using Python
cd dist
python -m http.server 3000

# Option 2: Using Node.js serve
npm install -g serve
serve -s dist -l 3000

# Option 3: Using nginx or Apache (configure to serve frontend/dist/)
```

### Step 4: Environment Configuration (Optional)

Create a `.env` file in the `backend/` directory for custom configuration:

```env
# Data directory (default: ../data)
DATA_ROOT=../data

# Firebase configuration (optional)
FIREBASE_DB_URL=https://your-project.firebaseio.com
SERVICE_ACCOUNT_PATH=../secrets/serviceAccountKey.json

# API port (default: 5000)
PORT=5000
```

## 🔧 Configuration

### Backend API Configuration

The API runs on port **5000** by default. To change this:

1. Edit `backend/api.py`:
   ```python
   if __name__ == "__main__":
       app.run(debug=False, port=5000, host='0.0.0.0')
   ```

2. Or set environment variable:
   ```bash
   export PORT=5000
   ```

### Frontend Configuration

The frontend expects the backend API at `http://localhost:5000` by default.

To change the API URL, edit `frontend/vite.config.js`:
```javascript
proxy: {
  '/api': {
    target: 'http://your-backend-url:5000',
    changeOrigin: true
  }
}
```

For production builds, update `frontend/src/api.js` to point to your production API URL.

## 📊 Data Requirements

### Required Files

- **Model Artifacts** (in `backend/artifacts/`):
  - `karma_model.pkl` - Main DNF prediction model
  - `feature_scaler.pkl` - Feature scaler for model input
  - `component_model_*.pkl` - Component-specific models (optional)
  - `component_scaler_*.pkl` - Component scalers (optional)

### Optional Files

- **Processed Data** (in `data/processed/`):
  - `per_lap_features.parquet` - Pre-processed telemetry data
  - `karma_stream.parquet` - Pre-computed karma scores

  **Note:** If these files don't exist, users can upload telemetry CSV files through the web interface, and the application will process them automatically.

## 🎯 Using the Application

### 1. Upload Telemetry Data

1. Open the application in your browser (default: `http://localhost:3000`)
2. Click "Upload File" and select a telemetry CSV file
3. The file should contain columns:
   - `vehicle_id` (required)
   - `lap` (required)
   - `telemetry_name` and `telemetry_value` (for long format)
   - OR individual telemetry columns (for wide format)
   - `meta_time` or `timestamp` (for time-based processing)

### 2. View Vehicle Data

1. After uploading, select a vehicle from the dropdown
2. View telemetry metrics and karma scores
3. Use replay controls to step through laps

### 3. API Endpoints

The backend provides these REST API endpoints:

- `GET /api/health` - Health check
- `POST /api/upload` - Upload and process telemetry file
- `GET /api/process` - Get all processed vehicle data
- `GET /api/vehicle/<vehicle_id>` - Get data for specific vehicle
- `GET /api/karma/<vehicle_id>` - Get karma scores for vehicle
- `GET /api/karma/<vehicle_id>/lap/<max_lap>` - Get karma up to specific lap
- `GET /api/model-prediction/<vehicle_id>` - Get ML model predictions

## 🧪 Training Models (If Needed)

If model artifacts are missing, you need to train them:

1. **Prepare training data:**
   ```bash
   cd backend
   python generate_training_data.py
   ```

2. **Train the main model:**
   ```bash
   python -m src.main train
   ```

3. **Train component models (optional):**
   ```bash
   python train_components.py
   ```

4. **Verify models were created:**
   ```bash
   ls artifacts/*.pkl
   ```

## 🐛 Troubleshooting

### Backend Issues

**Problem: Module not found errors**
```bash
# Solution: Ensure you're in the virtual environment and dependencies are installed
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**Problem: Model files not found**
```bash
# Solution: Train the models first (see "Training Models" section)
# Or ensure artifacts/ directory contains the required .pkl files
```

**Problem: Port 5000 already in use**
```bash
# Solution: Change the port in api.py or kill the process using port 5000
# Windows: netstat -ano | findstr :5000
# Linux/Mac: lsof -i :5000
```

### Frontend Issues

**Problem: npm install fails**
```bash
# Solution: Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Problem: API requests fail**
```bash
# Solution: Check that backend is running on port 5000
# Check browser console for CORS errors
# Verify vite.config.js proxy configuration
```

**Problem: Build fails**
```bash
# Solution: Check Node.js version (needs 18+)
node --version
# Update dependencies
npm update
```

### Data Issues

**Problem: No data after upload**
```bash
# Solution: Check CSV file format
# Ensure required columns exist: vehicle_id, lap
# Check backend logs for processing errors
```

**Problem: Karma scores not showing**
```bash
# Solution: Verify karma_stream.parquet exists
# Or upload a file with lap information
# Check that models are trained and available
```

## 📦 Deployment Checklist

Before deploying to production:

- [ ] All Python dependencies installed (`pip install -r requirements.txt`)
- [ ] All Node.js dependencies installed (`npm install`)
- [ ] Model artifacts exist in `backend/artifacts/`
- [ ] Frontend built for production (`npm run build`)
- [ ] Backend API tested and working
- [ ] Environment variables configured (if needed)
- [ ] Ports configured correctly (5000 for backend, 3000 for frontend)
- [ ] CORS configured for production domain
- [ ] Static files served correctly
- [ ] Health check endpoint responding (`/api/health`)

## 🌐 Production Deployment Options

### Option 1: Cloud Platforms

**Heroku:**
- Add `Procfile` with: `web: gunicorn -w 4 -b 0.0.0.0:$PORT api:app`
- Deploy backend and frontend separately

**AWS/GCP/Azure:**
- Deploy backend as containerized service
- Deploy frontend to CDN or static hosting
- Use load balancer for backend

### Option 2: VPS/Server

1. Install Python 3.10+ and Node.js 18+
2. Clone repository
3. Follow deployment steps above
4. Use systemd/PM2 to keep services running
5. Configure nginx as reverse proxy

### Option 3: Docker (Recommended)

Create `Dockerfile` for backend and frontend, then use docker-compose for orchestration.

## 📝 Notes

- The application can work without pre-processed data files - users can upload CSV files directly
- Model artifacts are required for predictions to work
- Logs are automatically created in `backend/logs/` directory
- Temporary uploaded files are stored in system temp directory
- Processed data is saved to `data/processed/` for faster subsequent access

## 🆘 Support

For issues or questions:
1. Check the logs in `backend/logs/`
2. Verify all dependencies are installed
3. Ensure model artifacts exist
4. Check API health endpoint: `curl http://localhost:5000/api/health`

---

**Last Updated:** Deployment cleanup completed - unnecessary training and raw data files removed.

