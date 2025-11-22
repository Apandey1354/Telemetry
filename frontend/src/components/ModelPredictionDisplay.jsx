import React from 'react'
import Plot from 'react-plotly.js'
import './ModelPredictionDisplay.css'

function ModelPredictionDisplay({ predictions, vehicleId }) {
  if (!predictions || !predictions.predictions || predictions.predictions.length === 0) {
    return (
      <div className="model-prediction-display">
        <div className="prediction-empty">No model predictions available</div>
      </div>
    )
  }

  const predictionData = predictions.predictions.sort((a, b) => a.lap - b.lap)
  const latest = predictions.latest
  const mostAtRisk = predictions.most_at_risk_component

  // Prepare chart data - overall DNF probability
  const trace = {
    x: predictionData.map(d => d.lap),
    y: predictionData.map(d => d.dnf_probability),
    name: 'DNF Probability',
    type: 'scatter',
    mode: 'lines+markers',
    line: { 
      width: 3,
      color: '#e74c3c'
    },
    marker: { 
      size: 8,
      color: predictionData.map(d => {
        if (d.dnf_probability > 70) return '#e74c3c'
        if (d.dnf_probability > 40) return '#f39c12'
        return '#27ae60'
      })
    },
    fill: 'tozeroy',
    fillcolor: 'rgba(231, 76, 60, 0.1)'
  }

  const layout = {
    title: {
      text: 'ML Model Prediction - Mechanical Failure Risk Over Time',
      font: { size: 18, color: '#fff' }
    },
    xaxis: {
      title: { text: 'Lap Number', font: { color: '#fff' } },
      showgrid: true,
      gridcolor: 'rgba(255, 255, 255, 0.1)',
      color: '#fff'
    },
    yaxis: {
      title: { text: 'Failure Probability (%)', font: { color: '#ff3358' } },
      range: [0, 100],
      showgrid: true,
      gridcolor: 'rgba(255, 255, 255, 0.05)',
      color: '#ff3358'
    },
    shapes: [
      {
        type: 'rect',
        xref: 'paper',
        yref: 'y',
        x0: 0,
        y0: 0,
        x1: 1,
        y1: 40,
        fillcolor: 'rgba(39, 174, 96, 0.1)',
        line: { width: 0 }
      },
      {
        type: 'rect',
        xref: 'paper',
        yref: 'y',
        x0: 0,
        y0: 40,
        x1: 1,
        y1: 70,
        fillcolor: 'rgba(243, 156, 18, 0.1)',
        line: { width: 0 }
      },
      {
        type: 'rect',
        xref: 'paper',
        yref: 'y',
        x0: 0,
        y0: 70,
        x1: 1,
        y1: 100,
        fillcolor: 'rgba(231, 76, 60, 0.1)',
        line: { width: 0 }
      }
    ],
    annotations: [
      {
        x: 0.02,
        y: 20,
        text: 'Low Risk',
        showarrow: false,
        font: { color: '#27ae60', size: 10 }
      },
      {
        x: 0.02,
        y: 55,
        text: 'Medium Risk',
        showarrow: false,
        font: { color: '#f39c12', size: 10 }
      },
      {
        x: 0.02,
        y: 85,
        text: 'High Risk',
        showarrow: false,
        font: { color: '#e74c3c', size: 10 }
      }
    ],
    hovermode: 'x unified',
    legend: {
      bgcolor: 'rgba(15, 17, 23, 0.9)',
      bordercolor: 'rgba(255, 255, 255, 0.2)',
      borderwidth: 1,
      font: { color: '#fff' }
    },
    margin: { l: 70, r: 40, t: 60, b: 60 },
    paper_bgcolor: 'rgba(10, 13, 20, 0.5)',
    plot_bgcolor: 'rgba(10, 13, 20, 0.3)',
    font: { family: 'Space Grotesk, sans-serif' }
  }

  const config = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['pan2d', 'lasso2d'],
    displaylogo: false
  }

  const getRiskColor = (probability) => {
    if (probability > 70) return '#e74c3c'
    if (probability > 40) return '#f39c12'
    return '#27ae60'
  }

  const getRiskLabel = (probability) => {
    if (probability > 70) return 'HIGH RISK'
    if (probability > 40) return 'MEDIUM RISK'
    return 'LOW RISK'
  }

  // Check if we have component-specific predictions
  const hasComponentPredictions = latest && (
    latest.engine_prob !== undefined || 
    latest.gearbox_prob !== undefined || 
    latest.brakes_prob !== undefined || 
    latest.tires_prob !== undefined
  )

  return (
    <div className="model-prediction-display">
      {hasComponentPredictions ? (
        // Show component-specific risks prominently
        <>
          <div className="component-risks-header">
            <h3>Component-Specific Failure Risk</h3>
            <p className="subtitle">ML Model Predictions by Component</p>
          </div>
          
          {mostAtRisk && mostAtRisk.probability > 10 && (
            <div className="component-risk-alert">
              <div className="alert-header">
                <span className="alert-icon">⚠️</span>
                <strong>Highest Risk Component:</strong>
              </div>
              <div className="alert-content">
                <span className="component-name">{mostAtRisk.component.charAt(0).toUpperCase() + mostAtRisk.component.slice(1)}</span>
                <span className="component-prob">{mostAtRisk.probability.toFixed(1)}% failure risk</span>
              </div>
            </div>
          )}

          <div className="component-probabilities-main">
            {['engine', 'gearbox', 'brakes', 'tires'].map(comp => {
              const prob = latest[`${comp}_prob`] || 0
              const riskLevel = prob > 70 ? 'high' : prob > 40 ? 'medium' : 'low'
              return (
                <div key={comp} className={`component-risk-card risk-${riskLevel}`}>
                  <div className="component-risk-header">
                    <div className="component-icon">
                      {comp === 'engine' && '🔧'}
                      {comp === 'gearbox' && '⚙️'}
                      {comp === 'brakes' && '🛑'}
                      {comp === 'tires' && '🛞'}
                    </div>
                    <div className="component-title">
                      <h4>{comp.charAt(0).toUpperCase() + comp.slice(1)}</h4>
                      <span className={`risk-badge-small risk-${riskLevel}`}>
                        {riskLevel.toUpperCase()} RISK
                      </span>
                    </div>
                  </div>
                  <div className="component-risk-value" style={{ color: getRiskColor(prob) }}>
                    {prob.toFixed(1)}%
                  </div>
                  <div className="component-risk-progress">
                    <div 
                      className="component-risk-fill"
                      style={{ 
                        width: `${prob}%`,
                        backgroundColor: getRiskColor(prob)
                      }}
                    />
                  </div>
                  <div className="component-risk-lap">
                    Lap {latest.lap}
                  </div>
                </div>
              )
            })}
          </div>
        </>
      ) : (
        // Fallback to overall risk if component predictions not available
        latest && (
          <div className="prediction-metric-card">
            <div className="prediction-header">
              <h4>Current Failure Risk</h4>
              <span className="risk-badge" style={{ backgroundColor: getRiskColor(latest.dnf_probability) }}>
                {getRiskLabel(latest.dnf_probability)}
              </span>
            </div>
            <div className="prediction-value" style={{ color: getRiskColor(latest.dnf_probability) }}>
              {latest.dnf_probability.toFixed(1)}%
            </div>
            <div className="prediction-subtitle">
              Lap {latest.lap} - Overall DNF Probability
            </div>
            <div className="prediction-progress-bar">
              <div 
                className="prediction-progress-fill"
                style={{ 
                  width: `${latest.dnf_probability}%`,
                  backgroundColor: getRiskColor(latest.dnf_probability)
                }}
              />
            </div>
          </div>
        )
      )}

      {/* Component risk trends over time */}
      {hasComponentPredictions && (
        <div className="component-trends-chart">
          <h4>Component Risk Trends Over Time</h4>
          <Plot
            data={[
              {
                x: predictionData.map(d => d.lap),
                y: predictionData.map(d => d.engine_prob || 0),
                name: 'Engine',
                type: 'scatter',
                mode: 'lines+markers',
                line: { width: 2, color: '#e74c3c' },
                marker: { size: 6 }
              },
              {
                x: predictionData.map(d => d.lap),
                y: predictionData.map(d => d.gearbox_prob || 0),
                name: 'Gearbox',
                type: 'scatter',
                mode: 'lines+markers',
                line: { width: 2, color: '#f39c12' },
                marker: { size: 6 }
              },
              {
                x: predictionData.map(d => d.lap),
                y: predictionData.map(d => d.brakes_prob || 0),
                name: 'Brakes',
                type: 'scatter',
                mode: 'lines+markers',
                line: { width: 2, color: '#9b59b6' },
                marker: { size: 6 }
              },
              {
                x: predictionData.map(d => d.lap),
                y: predictionData.map(d => d.tires_prob || 0),
                name: 'Tires',
                type: 'scatter',
                mode: 'lines+markers',
                line: { width: 2, color: '#3498db' },
                marker: { size: 6 }
              }
            ]}
            layout={{
              title: {
                text: 'Component Failure Risk Over Time',
                font: { size: 18, color: '#fff' }
              },
              xaxis: {
                title: { text: 'Lap Number', font: { color: '#fff' } },
                showgrid: true,
                gridcolor: 'rgba(255, 255, 255, 0.1)',
                color: '#fff'
              },
              yaxis: {
                title: { text: 'Failure Probability (%)', font: { color: '#ff3358' } },
                range: [0, 100],
                showgrid: true,
                gridcolor: 'rgba(255, 255, 255, 0.05)',
                color: '#ff3358'
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
              margin: { l: 70, r: 40, t: 60, b: 60 },
              paper_bgcolor: 'rgba(10, 13, 20, 0.5)',
              plot_bgcolor: 'rgba(10, 13, 20, 0.3)',
              font: { family: 'Space Grotesk, sans-serif' }
            }}
            config={config}
            style={{ width: '100%', height: '400px' }}
          />
        </div>
      )}

      {/* Overall DNF chart (secondary) */}
      {!hasComponentPredictions && (
        <div className="prediction-chart">
          <Plot
            data={[trace]}
            layout={layout}
            config={config}
            style={{ width: '100%', height: '400px' }}
          />
        </div>
      )}

      <div className="prediction-info">
        <p>
          <strong>Component-Specific ML Predictions:</strong> Each component (Engine, Gearbox, Brakes, Tires) 
          has its own trained machine learning model that predicts failure risk based on telemetry patterns. 
          The risk increases as the models detect patterns that historically led to failures in each specific component.
          {mostAtRisk && mostAtRisk.probability > 10 && (
            <> Currently, <strong>{mostAtRisk.component}</strong> shows the highest risk at {mostAtRisk.probability.toFixed(1)}%.</>
          )}
        </p>
      </div>
    </div>
  )
}

export default ModelPredictionDisplay

