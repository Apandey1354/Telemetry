import React, { useState } from 'react'
import Plot from 'react-plotly.js'
import './TimeSeriesChart.css'

function TimeSeriesChart({ data, vehicleId }) {
  const [selectedMetrics, setSelectedMetrics] = useState(['speed', 'acceleration', 'brake'])

  if (!data || data.length === 0) {
    return (
      <div className="chart-container section-card">
        <div className="chart-empty">No telemetry data available for visualization</div>
      </div>
    )
  }

  // Prepare data for Plotly
  const laps = [...new Set(data.map(d => d.lap))].sort((a, b) => a - b)
  
  const traces = []

  // Speed metrics
  if (selectedMetrics.includes('speed')) {
    traces.push({
      x: laps,
      y: laps.map(lap => {
        const lapData = data.filter(d => d.lap === lap)
        const speed = lapData.length > 0 ? (lapData[0].speed_mean || 0) : 0
        return speed
      }),
      name: 'Speed (km/h)',
      type: 'scatter',
      mode: 'lines+markers',
      line: { color: '#00ffc6', width: 3 },
      marker: { size: 8, color: '#00ffc6' },
      yaxis: 'y'
    })
  }

  // Acceleration metrics
  if (selectedMetrics.includes('acceleration')) {
    traces.push({
      x: laps,
      y: laps.map(lap => {
        const lapData = data.filter(d => d.lap === lap)
        const accel = lapData.length > 0 ? (lapData[0].accx_can_mean || 0) : 0
        return accel
      }),
      name: 'Acceleration X (m/s²)',
      type: 'scatter',
      mode: 'lines+markers',
      line: { color: '#ff3358', width: 2 },
      marker: { size: 6, color: '#ff3358' },
      yaxis: 'y2'
    })
  }

  // Brake pressure
  if (selectedMetrics.includes('brake')) {
    traces.push({
      x: laps,
      y: laps.map(lap => {
        const lapData = data.filter(d => d.lap === lap)
        const brake = lapData.length > 0 ? (lapData[0].pbrake_f_max || 0) : 0
        return brake
      }),
      name: 'Brake Pressure Max (bar)',
      type: 'scatter',
      mode: 'lines+markers',
      line: { color: '#ff8038', width: 2 },
      marker: { size: 6, color: '#ff8038' },
      yaxis: 'y3'
    })
  }

  // Additional metrics if available
  if (selectedMetrics.includes('rpm') && data.some(d => d.rpm_mean !== undefined)) {
    traces.push({
      x: laps,
      y: laps.map(lap => {
        const lapData = data.filter(d => d.lap === lap)
        return lapData.length > 0 ? (lapData[0].rpm_mean || 0) : 0
      }),
      name: 'RPM Mean',
      type: 'scatter',
      mode: 'lines+markers',
      line: { color: '#9b59b6', width: 2 },
      marker: { size: 6, color: '#9b59b6' },
      yaxis: 'y4'
    })
  }

  const layout = {
    title: {
      text: `Vehicle #${vehicleId} — Telemetry Analysis`,
      font: { size: 18, color: '#fff' }
    },
    xaxis: {
      title: { text: 'Lap Number', font: { color: '#fff' } },
      showgrid: true,
      gridcolor: 'rgba(255, 255, 255, 0.1)',
      color: '#fff'
    },
    yaxis: {
      title: { text: 'Speed (km/h)', font: { color: '#00ffc6' } },
      side: 'left',
      showgrid: true,
      gridcolor: 'rgba(255, 255, 255, 0.05)',
      color: '#00ffc6'
    },
    yaxis2: {
      title: { text: 'Acceleration (m/s²)', font: { color: '#ff3358' } },
      overlaying: 'y',
      side: 'right',
      showgrid: false,
      color: '#ff3358'
    },
    yaxis3: {
      title: { text: 'Brake Pressure (bar)', font: { color: '#ff8038' } },
      overlaying: 'y',
      side: 'right',
      anchor: 'free',
      position: 0.95,
      showgrid: false,
      color: '#ff8038'
    },
    hovermode: 'x unified',
    legend: {
      x: 0,
      y: 1,
      bgcolor: 'rgba(15, 17, 23, 0.9)',
      bordercolor: 'rgba(255, 255, 255, 0.2)',
      borderwidth: 1,
      font: { color: '#fff' }
    },
    margin: { l: 70, r: 80, t: 60, b: 60 },
    paper_bgcolor: 'rgba(10, 13, 20, 0.5)',
    plot_bgcolor: 'rgba(10, 13, 20, 0.3)',
    font: { family: 'Space Grotesk, sans-serif' }
  }

  const config = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
    displaylogo: false,
    toImageButtonOptions: {
      format: 'png',
      filename: `vehicle-${vehicleId}-telemetry`,
      height: 600,
      width: 1200,
      scale: 2
    }
  }

  const toggleMetric = (metric) => {
    setSelectedMetrics(prev => 
      prev.includes(metric) 
        ? prev.filter(m => m !== metric)
        : [...prev, metric]
    )
  }

  return (
    <div className="chart-container">
      <div className="chart-controls">
        <div className="chart-controls-label">Display Metrics:</div>
        <div className="chart-controls-buttons">
          <button
            className={`chart-control-button ${selectedMetrics.includes('speed') ? 'active' : ''}`}
            onClick={() => toggleMetric('speed')}
          >
            Speed
          </button>
          <button
            className={`chart-control-button ${selectedMetrics.includes('acceleration') ? 'active' : ''}`}
            onClick={() => toggleMetric('acceleration')}
          >
            Acceleration
          </button>
          <button
            className={`chart-control-button ${selectedMetrics.includes('brake') ? 'active' : ''}`}
            onClick={() => toggleMetric('brake')}
          >
            Brake Pressure
          </button>
          {data.some(d => d.rpm_mean !== undefined) && (
            <button
              className={`chart-control-button ${selectedMetrics.includes('rpm') ? 'active' : ''}`}
              onClick={() => toggleMetric('rpm')}
            >
              RPM
            </button>
          )}
        </div>
      </div>
      
      <div className="chart-wrapper">
        <Plot
          data={traces}
          layout={layout}
          config={config}
          style={{ width: '100%', height: '500px' }}
        />
      </div>

      <div className="chart-info">
        <div className="chart-info-item">
          <span className="chart-info-label">Data Points:</span>
          <span className="chart-info-value">{data.length}</span>
        </div>
        <div className="chart-info-item">
          <span className="chart-info-label">Laps Shown:</span>
          <span className="chart-info-value">{laps.length}</span>
        </div>
        <div className="chart-info-item">
          <span className="chart-info-label">Lap Range:</span>
          <span className="chart-info-value">{laps[0]} - {laps[laps.length - 1]}</span>
        </div>
      </div>
    </div>
  )
}

export default TimeSeriesChart
