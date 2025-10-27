# Credit Monitor - Complete Startup Guide

This guide will help you set up and run the complete Credit Monitor system with both backend API and frontend interface.

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- All required Python packages (see `requirements.txt`)
- A modern web browser (Chrome, Firefox, Safari, Edge)

### Step 1: Start the Backend API

1. **Open a terminal/command prompt** and navigate to the project directory:
   ```bash
   cd /path/to/MonitorCredit
   ```

2. **Start the backend server**:
   ```bash
   python run.py
   ```
   
   You should see output like:
   ```
   Starting Document Upload API on 0.0.0.0:8000
   API Documentation: http://0.0.0.0:8000/docs
   ReDoc Documentation: http://0.0.0.0:8000/redoc
   Press Ctrl+C to stop the server
   ```

3. **Keep this terminal window open** - the backend needs to keep running.

### Step 2: Start the Frontend

1. **Open a new terminal/command prompt** (keep the backend running in the first one)

2. **Start the frontend server**:
   ```bash
   python start_frontend.py
   ```
   
   This will:
   - Start a local server on port 3000
   - Automatically open your browser to `http://localhost:3000`
   - Serve the frontend files

3. **Alternative**: If you prefer to open the frontend manually:
   ```bash
   # Navigate to frontend directory
   cd frontend
   
   # Start a simple HTTP server
   python -m http.server 3000
   ```
   
   Then open `http://localhost:3000` in your browser.

## 🎯 What You'll See

### Backend API (Port 8000)
- **API Documentation**: `http://localhost:8000/docs` - Interactive Swagger UI
- **ReDoc Documentation**: `http://localhost:8000/redoc` - Alternative API docs
- **Health Check**: `http://localhost:8000/` - Simple status message

### Frontend Interface (Port 3000)
- **Main Dashboard**: `http://localhost:3000` - Beautiful web interface
- **Document Management**: Upload, view, and manage PDF documents
- **Transaction Processing**: View and manage extracted transactions
- **Real-time Updates**: Automatic refresh of processing status

## 📋 System Architecture

```
┌─────────────────┐    HTTP Requests    ┌─────────────────┐
│   Frontend      │ ──────────────────► │   Backend API   │
│  (Port 3000)    │                     │  (Port 8000)    │
│                 │ ◄────────────────── │                 │
└─────────────────┘    JSON Responses   └─────────────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │   Database      │
                     │  (SQLite)       │
                     └─────────────────┘
```

## 🔧 Configuration

### Backend Configuration
The backend uses environment variables for configuration. Create a `.env` file in the root directory:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Database Configuration (if using external database)
DATABASE_URL=sqlite:///./credit_monitor.db

# Google Cloud Vision API (for OCR)
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json

# OpenAI API (for transaction extraction)
OPENAI_API_KEY=your_openai_api_key
```

### Frontend Configuration
The frontend connects to the backend via the `API_BASE_URL` in `frontend/app.js`:

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

If your backend is running on a different port or host, update this value.

## 📱 Using the System

### 1. Upload a Document
1. Click "Upload Document" in the navigation bar
2. Enter a User ID (e.g., "user123")
3. Enter a Statement ID (e.g., "statement_jan_2024")
4. Select a PDF file (credit card statement, bank statement, etc.)
5. Click "Upload"

### 2. Monitor Processing
- The document will be processed in the background
- Text extraction happens automatically (Poppler + OCR)
- Transaction extraction follows text extraction
- Status updates automatically every 30 seconds

### 3. View Results
- Click the eye icon to view document details
- Click the exchange icon to view transactions
- Use filters to search for specific documents
- View processing statistics in the dashboard

## 🛠️ Troubleshooting

### Common Issues

#### Backend Won't Start
```bash
# Check if port 8000 is in use
netstat -an | grep 8000  # Linux/Mac
netstat -an | findstr 8000  # Windows

# Kill process using port 8000 (if needed)
lsof -ti:8000 | xargs kill  # Linux/Mac
# For Windows, use Task Manager or:
# netstat -ano | findstr 8000
# taskkill /PID <PID> /F
```

#### Frontend Won't Start
```bash
# Check if port 3000 is in use
netstat -an | grep 3000  # Linux/Mac
netstat -an | findstr 3000  # Windows

# Use a different port
python -m http.server 3001
```

#### CORS Errors
- The backend includes CORS middleware configured for all origins
- If you see CORS errors, ensure the backend is running and accessible
- Check that the `API_BASE_URL` in the frontend matches your backend URL

#### Database Issues
```bash
# Reset the database (WARNING: This deletes all data)
rm credit_monitor.db  # Linux/Mac
del credit_monitor.db  # Windows

# Restart the backend to recreate the database
python run.py
```

#### Missing Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# If you're using a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### Debug Mode

#### Backend Debug
- Check the terminal where the backend is running for error messages
- Visit `http://localhost:8000/docs` to test API endpoints directly
- Check the logs in the terminal for detailed error information

#### Frontend Debug
- Open browser developer tools (F12)
- Check the Console tab for JavaScript errors
- Check the Network tab for failed API requests
- Look for CORS errors or connection issues

## 🔄 Development Workflow

### Making Changes to Backend
1. Edit the Python files in the root directory
2. The backend auto-reloads when you save changes (if using `run.py`)
3. Check the terminal for any error messages

### Making Changes to Frontend
1. Edit files in the `frontend/` directory
2. Refresh your browser to see changes
3. Use browser developer tools to debug JavaScript

### Testing New Features
1. Test API endpoints using the Swagger UI at `http://localhost:8000/docs`
2. Test the frontend by uploading sample PDF files
3. Check that all features work as expected

## 📊 Monitoring and Logs

### Backend Logs
- All logs appear in the terminal where you started the backend
- Look for processing status, errors, and API request logs
- Database operations and file processing are logged

### Frontend Logs
- Open browser developer tools (F12) → Console tab
- JavaScript errors and API call results are logged here
- Network requests can be monitored in the Network tab

## 🚀 Production Deployment

For production deployment, consider:

1. **Backend**:
   - Use a production WSGI server (Gunicorn, uWSGI)
   - Set up proper environment variables
   - Use a production database (PostgreSQL, MySQL)
   - Configure proper CORS settings

2. **Frontend**:
   - Build for production (minify, optimize)
   - Serve via a web server (Nginx, Apache)
   - Configure proper caching headers

3. **Security**:
   - Use HTTPS
   - Implement proper authentication
   - Secure API keys and credentials
   - Validate file uploads

## 📞 Support

If you encounter issues:
1. Check this guide for common solutions
2. Review the error messages in the logs
3. Test individual components (backend API, frontend) separately
4. Check that all dependencies are properly installed

## 🎉 You're Ready!

Once both servers are running:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

You can start uploading documents and processing transactions through the beautiful web interface!
