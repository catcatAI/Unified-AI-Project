import requests
import json

url = "http://127.0.0.1:8000/api/v1/monitor/cpu"
headers = {"Content-Type": "application/json"}

print("--- Testing CPU Monitor ---")
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    print(f"CPU Monitor Response: {response.json()}")
except requests.exceptions.ConnectionError:
    print("Error: Could not connect to the backend. Is it running?")
except requests.exceptions.RequestException as e:
    print(f"Error getting CPU usage: {e}")
