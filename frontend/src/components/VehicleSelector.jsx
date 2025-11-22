import React from 'react'
import './VehicleSelector.css'

function VehicleSelector({ vehicles, selectedVehicle, onSelect, loading }) {
  if (loading) {
    return (
      <div className="vehicle-selector">
        <h3>Vehicles</h3>
        <div className="loading">Loading...</div>
      </div>
    )
  }

  if (!vehicles || vehicles.length === 0) {
    return (
      <div className="vehicle-selector">
        <h3>Vehicles</h3>
        <div className="empty">No vehicles available</div>
      </div>
    )
  }

  return (
    <div className="vehicle-selector">
      <h3>Vehicles</h3>
      <select
        value={selectedVehicle || ''}
        onChange={(e) => onSelect(e.target.value)}
        className="vehicle-select"
      >
        {vehicles.map((vehicle) => (
          <option key={vehicle} value={vehicle}>
            {vehicle}
          </option>
        ))}
      </select>
      <p className="vehicle-count">
        {vehicles.length} vehicle{vehicles.length !== 1 ? 's' : ''} available
      </p>
    </div>
  )
}

export default VehicleSelector

