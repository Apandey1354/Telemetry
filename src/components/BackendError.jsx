import React from 'react'
import './BackendError.css'

// Update this with your actual GitHub repository URL
const GITHUB_REPO_URL = 'https://github.com/yourusername/your-repo-name'

function BackendError({ onRetry }) {
  return (
    <div className="backend-error">
      <div className="backend-error__icon">🔌</div>
      <div className="backend-error__content">
        <h3 className="backend-error__title">Backend Server Not Available</h3>
        <p className="backend-error__message">
          The frontend is running, but it cannot connect to the backend API server.
          To use this application, you need to run the backend server locally.
        </p>
        <div className="backend-error__instructions">
          <h4>How to Run the Backend:</h4>
          <ol>
            <li>Clone the repository from GitHub</li>
            <li>Navigate to the <code>backend</code> directory</li>
            <li>Install dependencies: <code>pip install -r requirements.txt</code></li>
            <li>Run the API server: <code>python api.py</code></li>
            <li>The backend will start on <code>http://localhost:5000</code></li>
          </ol>
        </div>
        <div className="backend-error__actions">
          <a 
            href={GITHUB_REPO_URL} 
            target="_blank" 
            rel="noopener noreferrer"
            className="backend-error__link"
          >
            📦 View Repository on GitHub
          </a>
          {onRetry && (
            <button 
              onClick={onRetry}
              className="backend-error__retry"
            >
              🔄 Retry Connection
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default BackendError

