import React from 'react'
import Plot from 'react-plotly.js'
import './KarmaDisplay.css'

function KarmaDisplay({ karmaData, vehicleId }) {
  if (!karmaData || !karmaData.time_series || karmaData.time_series.length === 0) {
    return (
      <div className="karma-display">
        <div className="karma-empty">No karma data available</div>
      </div>
    )
  }

  // Group by component
  const components = {}
  karmaData.time_series.forEach(item => {
    if (!components[item.component]) {
      components[item.component] = []
    }
    components[item.component].push({
      lap: item.lap,
      score: item.karma_score
    })
  })

  // Prepare traces for each component
  const traces = Object.entries(components).map(([component, data]) => {
    const sortedData = [...data].sort((a, b) => a.lap - b.lap)
    return {
      x: sortedData.map(d => d.lap),
      y: sortedData.map(d => d.score),
      name: component.charAt(0).toUpperCase() + component.slice(1),
      type: 'scatter',
      mode: 'lines+markers',
      line: { width: 2 },
      marker: { size: 6 }
    }
  })

  const layout = {
    title: {
      text: 'Mechanical Karma — Component Health Over Time',
      font: { size: 18, color: '#fff' }
    },
    xaxis: {
      title: { text: 'Lap Number', font: { color: '#fff' } },
      showgrid: true,
      gridcolor: 'rgba(255, 255, 255, 0.1)',
      color: '#fff'
    },
    yaxis: {
      title: { text: 'Karma Score (0-1)', font: { color: '#00ffc6' } },
      range: [0, 1],
      showgrid: true,
      gridcolor: 'rgba(255, 255, 255, 0.05)',
      tickformat: '.2f',
      color: '#00ffc6'
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
  }

  const config = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['pan2d', 'lasso2d'],
    displaylogo: false
  }

  // Latest scores for metrics
  const latestScores = karmaData.latest_scores || {}
  
  // Calculate trend (increasing/decreasing) for each component
  const getTrend = (component) => {
    const componentData = karmaData.time_series.filter(item => item.component === component)
    if (componentData.length < 2) return null
    const sorted = componentData.sort((a, b) => a.lap - b.lap)
    const recent = sorted.slice(-3) // Last 3 laps
    if (recent.length < 2) return null
    const trend = recent[recent.length - 1].karma_score - recent[0].karma_score
    return trend > 0.01 ? 'up' : trend < -0.01 ? 'down' : 'stable'
  }

  return (
    <div className="karma-display">
      {Object.keys(latestScores).length > 0 && (
        <div className="karma-metrics">
          {Object.entries(latestScores).map(([component, data]) => {
            const trend = getTrend(component)
            const scorePercent = (data.score * 100).toFixed(1)
            return (
              <div key={component} className="karma-metric-card">
                <div className="karma-metric-label">
                  {component.charAt(0).toUpperCase() + component.slice(1)}
                  {trend === 'up' && <span className="trend-indicator trend-up"> ↗</span>}
                  {trend === 'down' && <span className="trend-indicator trend-down"> ↘</span>}
                </div>
                <div className="karma-metric-value">
                  {scorePercent}%
                </div>
                <div className="karma-progress-bar">
                  <div 
                    className="karma-progress-fill"
                    style={{ width: `${scorePercent}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      )}
      
      <div className="karma-chart">
        <Plot
          data={traces}
          layout={layout}
          config={config}
          style={{ width: '100%', height: '400px' }}
        />
      </div>
    </div>
  )
}

export default KarmaDisplay

