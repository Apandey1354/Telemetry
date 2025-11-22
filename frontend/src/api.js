import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Custom error class for backend connection errors
export class BackendConnectionError extends Error {
  constructor(message = 'Backend server is not available') {
    super(message)
    this.name = 'BackendConnectionError'
    this.isConnectionError = true
  }
}

// Helper function to check if error is a connection error
const isConnectionError = (error) => {
  if (!error.response) {
    // Network error or CORS error
    return true
  }
  // Check for common connection error status codes
  if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK' || error.code === 'ERR_CONNECTION_REFUSED') {
    return true
  }
  return false
}

// Wrapper function to handle API calls with connection error detection
const apiCall = async (apiFunction) => {
  try {
    return await apiFunction()
  } catch (error) {
    if (isConnectionError(error)) {
      throw new BackendConnectionError('Unable to connect to backend server')
    }
    throw error
  }
}

export const uploadFile = async (file) => {
  return apiCall(async () => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  })
}

export const fetchVehicles = async () => {
  return apiCall(async () => {
    const response = await api.post('/process')
    return response.data
  })
}

export const fetchVehicleData = async (vehicleId) => {
  return apiCall(async () => {
    const response = await api.get(`/vehicle/${vehicleId}`)
    return response.data
  })
}

export const fetchKarmaScores = async (vehicleId, maxLap = null) => {
  return apiCall(async () => {
    const url = maxLap 
      ? `/karma/${vehicleId}/lap/${maxLap}`
      : `/karma/${vehicleId}`
    const response = await api.get(url)
    return response.data
  })
}

export const fetchModelPredictions = async (vehicleId, maxLap = null) => {
  return apiCall(async () => {
    const url = `/model-prediction/${vehicleId}`
    const params = maxLap ? { max_lap: maxLap } : {}
    const response = await api.get(url, { params })
    return response.data
  })
}

export default api

