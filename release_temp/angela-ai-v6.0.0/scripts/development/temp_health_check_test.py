import requests
import json

url = "http://127.0.0.1:8000/api/v1/health"
headers = {"Content-Type": "application/json"}

print("--- Testing Health Check ---")
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    print(f"Health Check Response: {response.json()}")
except requests.exceptions.ConnectionError:
    print("Error: Could not connect to the backend. Is it running?")
except requests.exceptions.RequestException as e:
    print(f"Error during health check: {e}")
