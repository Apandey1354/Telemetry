import React, { useState } from 'react'
import { uploadFile, BackendConnectionError } from '../api'
import BackendError from './BackendError'
import './FileUpload.css'

function FileUpload({ onUpload, loading }) {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState(null)
  const [backendError, setBackendError] = useState(false)

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
      setMessage(null)
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setMessage({ type: 'error', text: 'Please select a file first' })
      return
    }

    try {
      setUploading(true)
      setMessage(null)
      setBackendError(false)
      const result = await uploadFile(file)
      const vehicleText = result.vehicles && result.vehicles.length > 0
        ? `Found ${result.vehicles.length} vehicle(s)`
        : ''
      setMessage({ 
        type: 'success', 
        text: `File processed successfully! ${vehicleText} (${result.rows_processed || result.rows || 0} laps processed)` 
      })
      if (onUpload) {
        onUpload(file)
      }
      setFile(null)
      // Reset file input
      document.getElementById('file-input').value = ''
    } catch (error) {
      if (error instanceof BackendConnectionError || error.isConnectionError) {
        setBackendError(true)
        setMessage(null)
      } else {
        setMessage({ 
          type: 'error', 
          text: error.response?.data?.error || error.message || 'Upload failed' 
        })
        setBackendError(false)
      }
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="file-upload">
      {backendError && (
        <div style={{ marginBottom: '1rem' }}>
          <BackendError onRetry={() => {
            setBackendError(false)
            if (file) {
              handleUpload()
            }
          }} />
        </div>
      )}
      <div className="upload-controls">
        <input
          id="file-input"
          type="file"
          accept=".csv,.parquet"
          onChange={handleFileChange}
          disabled={uploading || loading}
          className="file-input"
        />
        <button
          onClick={handleUpload}
          disabled={!file || uploading || loading}
          className="upload-button"
        >
          {uploading ? 'Uploading...' : 'Upload'}
        </button>
      </div>
      {message && !backendError && (
        <div className={`upload-message ${message.type}`}>
          {message.text}
        </div>
      )}
      <p className="upload-hint">
        Upload a telemetry CSV file to process and visualize data.
      </p>
    </div>
  )
}

export default FileUpload

