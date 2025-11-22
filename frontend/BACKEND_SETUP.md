# Backend Setup Instructions

When the frontend cannot connect to the backend API, users will see a helpful error message with instructions to run the backend locally.

## Updating the GitHub Repository URL

To update the GitHub link shown in the error message, edit the following file:

**File:** `frontend/src/components/BackendError.jsx`

**Line 5:** Update the `GITHUB_REPO_URL` constant:

```javascript
const GITHUB_REPO_URL = 'https://github.com/yourusername/your-repo-name'
```

Replace `yourusername/your-repo-name` with your actual GitHub repository path.

## How It Works

1. When the frontend tries to connect to the backend API and fails, it detects this as a connection error
2. Instead of showing a generic error, it displays a user-friendly `BackendError` component
3. The component shows:
   - Clear explanation that the backend is not available
   - Step-by-step instructions to run the backend locally
   - A link to the GitHub repository
   - A retry button to attempt reconnection

## Testing

To test the error message:

1. Make sure the backend is **not** running
2. Open the frontend application
3. Try to upload a file or load data
4. You should see the `BackendError` component with the GitHub link

## Backend Quick Start

For users who see the error message, they can follow these steps:

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/your-repo-name
cd your-repo-name

# 2. Navigate to backend
cd backend

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the API server
python api.py

# The backend will start on http://localhost:5000
```

The frontend will automatically connect once the backend is running.

