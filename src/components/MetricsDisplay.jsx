import React from 'react'
import './MetricsDisplay.css'

function MetricsDisplay({ metrics }) {
  if (!metrics) return null

  const formatSpeed = (speed) => {
    if (!speed) return 'N/A'
    return `${speed.toFixed(1)} km/h`
  }

  const formatNumber = (num) => {
    if (num === null || num === undefined) return 'N/A'
    return num.toLocaleString()
  }

  const getStatusColor = (dnf) => {
    return dnf ? '#ff3358' : '#00ffc6'
  }

  const getStatusLabel = (dnf) => {
    return dnf ? 'Did Not Finish' : 'Race Complete'
  }

  return (
    <div className="metrics-display">
      <div className="metrics-grid">
        {/* Primary Metrics */}
        <div className="metric-card metric-card-primary">
          <div className="metric-icon">🏁</div>
          <div className="metric-content">
            <div className="metric-label">Total Laps</div>
            <div className="metric-value metric-value-large">{formatNumber(metrics.laps_recorded || metrics.max_lap || 0)}</div>
            <div className="metric-subtitle">Race Distance</div>
          </div>
        </div>

        <div className="metric-card metric-card-primary">
          <div className="metric-icon">⚡</div>
          <div className="metric-content">
            <div className="metric-label">Average Speed</div>
            <div className="metric-value metric-value-large">{formatSpeed(metrics.avg_speed)}</div>
            <div className="metric-subtitle">Mean Velocity</div>
          </div>
        </div>

        <div className="metric-card metric-card-primary">
          <div className="metric-icon">🎯</div>
          <div className="metric-content">
            <div className="metric-label">Race Status</div>
            <div className="metric-value metric-value-large" style={{ color: getStatusColor(metrics.dnf_flag) }}>
              {metrics.dnf_flag ? 'DNF' : 'FINISHED'}
            </div>
            <div className="metric-subtitle">{getStatusLabel(metrics.dnf_flag)}</div>
          </div>
        </div>

        {/* Secondary Metrics */}
        {metrics.max_lap !== undefined && (
          <div className="metric-card">
            <div className="metric-content">
              <div className="metric-label">Max Lap</div>
              <div className="metric-value">{formatNumber(metrics.max_lap)}</div>
            </div>
          </div>
        )}

        {metrics.min_lap !== undefined && (
          <div className="metric-card">
            <div className="metric-content">
              <div className="metric-label">Min Lap</div>
              <div className="metric-value">{formatNumber(metrics.min_lap)}</div>
            </div>
          </div>
        )}

        {metrics.dnf_flag !== undefined && (
          <div className="metric-card">
            <div className="metric-content">
              <div className="metric-label">DNF Flag</div>
              <div className="metric-value" style={{ color: metrics.dnf_flag ? '#ff3358' : '#00ffc6' }}>
                {metrics.dnf_flag ? 'Yes' : 'No'}
              </div>
            </div>
          </div>
        )}

        {/* Additional metrics if available */}
        {metrics.speed_max !== undefined && (
          <div className="metric-card">
            <div className="metric-content">
              <div className="metric-label">Max Speed</div>
              <div className="metric-value">{formatSpeed(metrics.speed_max)}</div>
            </div>
          </div>
        )}

        {metrics.speed_min !== undefined && (
          <div className="metric-card">
            <div className="metric-content">
              <div className="metric-label">Min Speed</div>
              <div className="metric-value">{formatSpeed(metrics.speed_min)}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default MetricsDisplay
