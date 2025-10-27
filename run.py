#!/usr/bin/env python3
"""
Simple startup script for the Document Upload API
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get configuration from environment or use defaults
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    print(f"Starting Document Upload API on {host}:{port}")
    print(f"API Documentation: http://{host}:{port}/docs")
    print(f"ReDoc Documentation: http://{host}:{port}/redoc")
    print("Press Ctrl+C to stop the server")
    
    # Start the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,  # Enable auto-reload for development
        log_level="info"
    ) 