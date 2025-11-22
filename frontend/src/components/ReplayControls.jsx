import React, { useEffect, useRef } from 'react'
import './ReplayControls.css'

function ReplayControls({
  minLap,
  maxLap,
  currentLap,
  enabled,
  isPlaying,
  onStep,
  onToggle,
  onPlayPause
}) {
  const intervalRef = useRef(null)

  useEffect(() => {
    if (enabled && isPlaying && currentLap < maxLap) {
      intervalRef.current = setInterval(() => {
        onStep(Math.min(maxLap, currentLap + 1))
      }, 1000) // 1 second per lap
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [enabled, isPlaying, currentLap, maxLap, onStep])

  const progress = ((currentLap - minLap) / Math.max(1, maxLap - minLap)) * 100

  return (
    <div className="replay-controls">
      <div className="replay-header">
        <h3>Replay Controls</h3>
        <label className="replay-toggle">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => onToggle(e.target.checked)}
          />
          <span>Enable Replay</span>
        </label>
      </div>

      {enabled && (
        <>
          <div className="replay-buttons">
            <button
              onClick={onPlayPause}
              className="replay-button play-pause"
              disabled={currentLap >= maxLap && !isPlaying}
            >
              {isPlaying ? '⏸ Pause' : '▶ Play'}
            </button>
            {currentLap >= maxLap && isPlaying && (
              <div style={{ fontSize: '0.8rem', color: '#666', marginTop: '0.5rem' }}>
                Replay complete!
              </div>
            )}
            <button
              onClick={() => onStep(Math.min(maxLap, currentLap + 1))}
              className="replay-button"
              disabled={currentLap >= maxLap}
            >
              +1 Lap
            </button>
            <button
              onClick={() => onStep(minLap)}
              className="replay-button"
            >
              Reset
            </button>
          </div>

          <div className="replay-info">
            <div className="lap-indicator">
              Lap {currentLap} / {maxLap}
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default ReplayControls

