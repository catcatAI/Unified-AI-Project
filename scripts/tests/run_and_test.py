import subprocess
import sys
import os
import time
import requests
import threading
import uvicorn

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'apps', 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import the minimal backend module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import minimal_backend

def run_server():
    """Run the server in a separate thread."""
    uvicorn.run(
        "minimal_backend:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

def test_api():
    """Test the API endpoints."""
    print("Waiting for server to start...")
    time.sleep(3)
    
    print("\nTesting health endpoint...")
    try:
        response = requests.get("http://localhost:8000/api/v1/health", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

    print("\nTesting pet status endpoint...")
    try:
        response = requests.get("http://localhost:8000/api/v1/pet/status", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

    print("\nTesting pet needs endpoint...")
    try:
        response = requests.get("http://localhost:8000/api/v1/pet/angelas-pet-123/needs", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

    print("\nTesting economy endpoint...")
    try:
        response = requests.get("http://localhost:8000/api/v1/economy/angelas-pet-123", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

    print("\nAll tests completed!")

if __name__ == "__main__":
    # Start server in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Run tests
    test_api()
