# Mechanical Karma React Dashboard

A modern React dashboard for visualizing mechanical karma (failure risk) predictions from race telemetry data.

## Features

- 📤 **File Upload**: Upload telemetry CSV files for processing
- 🚗 **Vehicle Selection**: Browse and select from available vehicles
- 📊 **Interactive Charts**: Plotly-powered visualizations of telemetry trends
- ⚡ **Karma Scores**: Real-time component-level mechanical karma tracking
- ▶️ **Replay Controls**: Step through laps to see how karma evolves
- 📈 **Metrics Display**: Key statistics (laps, speed, DNF status)

## Setup

### Prerequisites

- Node.js 18+ and npm
- Python backend running (see backend setup)

### Installation

```bash
cd frontend
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

Make sure the Flask API backend is running on `http://localhost:5000` (see `backend/api.py`)

### Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Usage

1. **Start the backend API**:
   ```bash
   cd backend
   python api.py
   ```

2. **Start the React app**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Upload a telemetry file** using the upload component in the sidebar

4. **Select a vehicle** from the dropdown

5. **View visualizations** and use replay controls to step through laps

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── FileUpload.jsx
│   │   ├── VehicleSelector.jsx
│   │   ├── MetricsDisplay.jsx
│   │   ├── TimeSeriesChart.jsx
│   │   ├── KarmaDisplay.jsx
│   │   └── ReplayControls.jsx
│   ├── api.js              # API client
│   ├── App.jsx             # Main app component
│   └── main.jsx            # Entry point
├── index.html
├── vite.config.js
└── package.json
```

## API Endpoints

The app communicates with the Flask backend at `/api`:

- `POST /api/upload` - Upload telemetry file
- `POST /api/process` - Get processed vehicle data
- `GET /api/vehicle/<id>` - Get specific vehicle data
- `GET /api/karma/<id>` - Get karma scores for vehicle
- `GET /api/karma/<id>/lap/<lap>` - Get karma up to specific lap

## Technologies

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Plotly.js** - Interactive charts
- **Axios** - HTTP client
- **CSS3** - Styling



