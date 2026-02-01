import requests
import time

print("Waiting for server to start...")
time.sleep(5)

print("Testing health endpoint...")
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
