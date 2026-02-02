import requests
import json

url = "http://127.0.0.1:8000/api/v1/tools/dispatch"
headers = {"Content-Type": "application/json"}
payload = {
    "tool_name": "non_existent_tool",
    "kwargs": {}
}

print("--- Testing Non-Existent Tool Dispatch ---")
try:
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    print(f"Dispatch Tool Response (unexpected success): {response.json()}")
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        print(f"Dispatch Tool Response (expected 404): {e.response.json()}")
    else:
        print(f"Dispatch Tool Response (unexpected error): {e}")
except requests.exceptions.ConnectionError:
    print("Error: Could not connect to the backend. Is it running?")
except requests.exceptions.RequestException as e:
    print(f"Error dispatching tool: {e}")
