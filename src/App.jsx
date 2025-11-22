import React, { useState, useEffect } from 'react'
import FileUpload from './components/FileUpload'
import VehicleSelector from './components/VehicleSelector'
import MetricsDisplay from './components/MetricsDisplay'
import TimeSeriesChart from './components/TimeSeriesChart'
import KarmaDisplay from './components/KarmaDisplay'
import ModelPredictionDisplay from './components/ModelPredictionDisplay'
import ReplayControls from './components/ReplayControls'
import BackendError from './components/BackendError'
import { fetchVehicles, fetchVehicleData, fetchKarmaScores, fetchModelPredictions, BackendConnectionError } from './api'
import './App.css'

function App() {
  const [vehicles, setVehicles] = useState([])
  const [selectedVehicle, setSelectedVehicle] = useState(null)
  const [vehicleData, setVehicleData] = useState(null)
  const [karmaData, setKarmaData] = useState(null)
  const [modelPredictions, setModelPredictions] = useState(null)
  const [currentLap, setCurrentLap] = useState(null)
  const [replayEnabled, setReplayEnabled] = useState(false)
  const [isReplaying, setIsReplaying] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [backendError, setBackendError] = useState(false)

  // Load vehicles on mount
  useEffect(() => {
    loadVehicles()
  }, [])

  // Load vehicle data when selected
  useEffect(() => {
    if (selectedVehicle) {
      loadVehicleData(selectedVehicle)
      loadModelPredictions(selectedVehicle)
    }
  }, [selectedVehicle])

  // Load karma data and model predictions when lap changes
  useEffect(() => {
    if (selectedVehicle && currentLap !== null) {
      loadKarmaData(selectedVehicle)
      loadModelPredictions(selectedVehicle)
    }
  }, [selectedVehicle, currentLap, replayEnabled])

  const loadVehicles = async () => {
    try {
      setLoading(true)
      setBackendError(false)
      setError(null)
      const data = await fetchVehicles()
      setVehicles(data.vehicles || [])
      if (data.vehicles && data.vehicles.length > 0 && !selectedVehicle) {
        setSelectedVehicle(data.vehicles[0])
      }
      return data
    } catch (err) {
      if (err instanceof BackendConnectionError || err.isConnectionError) {
        setBackendError(true)
        setError(null)
      } else {
        setError(err.message)
        setBackendError(false)
      }
      return null
    } finally {
      setLoading(false)
    }
  }

  const loadVehicleData = async (vehicleId) => {
    try {
      setBackendError(false)
      setError(null)
      const data = await fetchVehicleData(vehicleId)
      setVehicleData(data)
      if (data.metrics && !currentLap) {
        setCurrentLap(data.metrics.max_lap)
      }
    } catch (err) {
      if (err instanceof BackendConnectionError || err.isConnectionError) {
        setBackendError(true)
        setError(null)
      } else {
        setError(err.message)
        setBackendError(false)
      }
    }
  }

  const loadKarmaData = async (vehicleId) => {
    try {
      setBackendError(false)
      setError(null)
      if (replayEnabled && currentLap !== null) {
        const data = await fetchKarmaScores(vehicleId, currentLap)
        setKarmaData(data)
      } else if (currentLap !== null) {
        const data = await fetchKarmaScores(vehicleId, currentLap)
        setKarmaData(data)
      } else {
        const data = await fetchKarmaScores(vehicleId)
        setKarmaData(data)
      }
    } catch (err) {
      if (err instanceof BackendConnectionError || err.isConnectionError) {
        setBackendError(true)
        setError(null)
      } else {
        setError(err.message)
        setBackendError(false)
      }
    }
  }

  const loadModelPredictions = async (vehicleId) => {
    try {
      setBackendError(false)
      setError(null)
      const maxLap = replayEnabled && currentLap !== null ? currentLap : null
      const data = await fetchModelPredictions(vehicleId, maxLap)
      setModelPredictions(data)
    } catch (err) {
      if (err instanceof BackendConnectionError || err.isConnectionError) {
        setBackendError(true)
        setError(null)
      } else if (!err.message.includes('Model not found')) {
        setError(err.message)
        setBackendError(false)
      }
      setModelPredictions(null)
    }
  }

  const handleFileUpload = async (file) => {
    try {
      setLoading(true)
      setError(null)
      const data = await loadVehicles()
      setTimeout(async () => {
        const vehicleList = data?.vehicles || vehicles
        const vehicle = selectedVehicle || (vehicleList.length > 0 ? vehicleList[0] : null)
        if (vehicle) {
          if (!selectedVehicle) {
            setSelectedVehicle(vehicle)
          }
          await loadVehicleData(vehicle)
          setReplayEnabled(true)
          setCurrentLap(1)
          setTimeout(() => {
            setIsReplaying(true)
          }, 100)
        }
      }, 1000)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleReplayStep = (lap) => {
    setCurrentLap(lap)
    if (vehicleData && lap >= vehicleData.metrics?.max_lap) {
      setIsReplaying(false)
    }
  }

  const handleReplayToggle = (enabled) => {
    setReplayEnabled(enabled)
    if (!enabled) {
      setIsReplaying(false)
      if (vehicleData?.metrics) {
        setCurrentLap(vehicleData.metrics.max_lap)
      }
    }
  }

  const handleReplayPlayPause = () => {
    setIsReplaying(!isReplaying)
  }

  const getDisplayData = () => {
    if (!vehicleData || !currentLap) return null
    return vehicleData.data.filter(d => d.lap <= currentLap)
  }

  return (
    <div className="app">
      {/* Professional Race Header */}
      <header className="app-header hero-shell">
        <div className="hero-content">
          <div className="hero-eyebrow">RACE ANALYTICS DASHBOARD</div>
          <h1>Mechanical Karma Racing Intelligence</h1>
          <p>Advanced telemetry analysis and predictive failure detection for competitive racing</p>
          {selectedVehicle && vehicleData && (
            <div className="hero-actions">
              <div className="hero-stats">
                <div className="hero-stat">
                  <span className="hero-stat-label">Vehicle</span>
                  <span className="hero-stat-value">#{selectedVehicle}</span>
                </div>
                {vehicleData.metrics && (
                  <>
                    <div className="hero-stat">
                      <span className="hero-stat-label">Laps</span>
                      <span className="hero-stat-value">{vehicleData.metrics.max_lap || 0}</span>
                    </div>
                    <div className="hero-stat">
                      <span className="hero-stat-label">Status</span>
                      <span className={`hero-stat-value ${vehicleData.metrics.dnf_flag ? 'status-dnf' : 'status-active'}`}>
                        {vehicleData.metrics.dnf_flag ? 'DNF' : 'Active'}
                      </span>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </header>

      <div className="app-container">
        {/* Control Sidebar */}
        <aside className="sidebar glass section-card">
          <div className="sidebar-section">
            <h3 className="sidebar-title">Data Management</h3>
            <FileUpload onUpload={handleFileUpload} loading={loading} />
          </div>
          
          <div className="sidebar-section">
            <h3 className="sidebar-title">Vehicle Selection</h3>
            <VehicleSelector
              vehicles={vehicles}
              selectedVehicle={selectedVehicle}
              onSelect={setSelectedVehicle}
              loading={loading}
            />
          </div>

          {vehicleData && (
            <div className="sidebar-section">
              <h3 className="sidebar-title">Race Replay</h3>
              <ReplayControls
                minLap={vehicleData.metrics?.min_lap || 1}
                maxLap={vehicleData.metrics?.max_lap || 1}
                currentLap={currentLap || vehicleData.metrics?.max_lap || 1}
                enabled={replayEnabled}
                isPlaying={isReplaying}
                onStep={handleReplayStep}
                onToggle={handleReplayToggle}
                onPlayPause={handleReplayPlayPause}
              />
            </div>
          )}
        </aside>

        {/* Main Dashboard Content */}
        <main className="main-content">
          {backendError && (
            <BackendError onRetry={loadVehicles} />
          )}
          
          {error && !backendError && (
            <div className="error section-card">
              <div className="error-icon">⚠️</div>
              <div className="error-content">
                <strong>Error:</strong> {error}
              </div>
            </div>
          )}

          {loading && !vehicleData && (
            <div className="loading section-card">
              <div className="loading-spinner"></div>
              <p>Loading race data...</p>
            </div>
          )}

          {selectedVehicle && vehicleData && (
            <>
              {/* Vehicle Status Header */}
              <div className="vehicle-header section-card">
                <div className="vehicle-header-content">
                  <div>
                    <h2 className="vehicle-title">
                      <span className="vehicle-icon">🏎️</span>
                      Vehicle #{selectedVehicle}
                    </h2>
                    <p className="lap-info">
                      {replayEnabled ? (
                        <>
                          <span className="replay-badge">REPLAY MODE</span>
                          Lap {currentLap || vehicleData.metrics?.max_lap || 'N/A'} of {vehicleData.metrics?.max_lap || 'N/A'}
                          {isReplaying && (
                            <span className="replay-indicator"> ▶ LIVE</span>
                          )}
                        </>
                      ) : (
                        <>
                          Complete Race Data • {vehicleData.metrics?.max_lap || 0} Total Laps
                        </>
                      )}
                    </p>
                  </div>
                  {vehicleData.metrics && (
                    <div className="vehicle-status-badges">
                      {vehicleData.metrics.dnf_flag ? (
                        <span className="status-badge status-badge-dnf">DNF</span>
                      ) : (
                        <span className="status-badge status-badge-active">RACING</span>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Performance Metrics Grid */}
              <MetricsDisplay metrics={vehicleData.metrics} />

              {/* Telemetry Analysis Section */}
              <div className="section-card">
                <div className="section-card__header">
                  <div>
                    <h2>Telemetry Analysis</h2>
                    <p className="section-card__subtitle">Real-time vehicle performance metrics and trends</p>
                  </div>
                </div>
                <div className="section-card__body">
                  <TimeSeriesChart data={getDisplayData()} vehicleId={selectedVehicle} />
                </div>
              </div>

              {/* ML Predictions Section */}
              {modelPredictions && (
                <div className="section-card">
                  <div className="section-card__header">
                    <div>
                      <h2>AI Failure Prediction</h2>
                      <p className="section-card__subtitle">Machine learning model predictions for component failure risk</p>
                    </div>
                  </div>
                  <div className="section-card__body">
                    <ModelPredictionDisplay
                      predictions={modelPredictions}
                      vehicleId={selectedVehicle}
                    />
                  </div>
                </div>
              )}

              {/* Mechanical Karma Section */}
              <div className="section-card">
                <div className="section-card__header">
                  <div>
                    <h2>Mechanical Karma Analysis</h2>
                    <p className="section-card__subtitle">Component health scores and degradation trends</p>
                  </div>
                </div>
                <div className="section-card__body">
                  {karmaData ? (
                    <KarmaDisplay
                      karmaData={karmaData}
                      vehicleId={selectedVehicle}
                    />
                  ) : (
                    <div className="empty-state">Loading karma data...</div>
                  )}
                </div>
              </div>
            </>
          )}

          {!selectedVehicle && !loading && (
            <div className="empty-state section-card">
              <div className="empty-icon">🏁</div>
              <h3>No Race Data Available</h3>
              <p>Upload telemetry data to begin race analysis and failure prediction.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

export default App
