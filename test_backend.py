#!/usr/bin/env python3
"""
Simple script to test if the backend is running and accessible
"""
import requests
import sys

def test_backend():
    base_url = "http://localhost:8000"
    
    print("Testing backend connection...")
    print(f"Backend URL: {base_url}")
    
    try:
        # Test root endpoint
        response = requests.get(f"{base_url}/")
        print(f"Root endpoint status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Backend is running and accessible")
        else:
            print(f"✗ Backend responded with status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to backend. Is it running?")
        print("Start the backend with: python run.py")
        return False
    except Exception as e:
        print(f"✗ Error testing backend: {e}")
        return False
    
    try:
        # Test documents endpoint
        response = requests.get(f"{base_url}/documents/")
        print(f"Documents endpoint status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Documents endpoint is working")
        else:
            print(f"✗ Documents endpoint error: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error testing documents endpoint: {e}")
    
    return True

if __name__ == "__main__":
    success = test_backend()
    if not success:
        sys.exit(1)
