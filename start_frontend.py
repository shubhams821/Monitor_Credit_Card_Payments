#!/usr/bin/env python3
"""
Simple HTTP server for serving the frontend files
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

def start_frontend_server():
    # Change to the frontend directory
    frontend_dir = Path(__file__).parent / "frontend"
    os.chdir(frontend_dir)
    
    # Server configuration
    PORT = 3000
    Handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"Frontend server started at http://localhost:{PORT}")
            print(f"Serving files from: {frontend_dir}")
            print("Press Ctrl+C to stop the server")
            
            # Open browser automatically
            webbrowser.open(f"http://localhost:{PORT}")
            
            # Start the server
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"Port {PORT} is already in use. Please stop any other server using this port.")
        else:
            print(f"Error starting server: {e}")

if __name__ == "__main__":
    start_frontend_server()
