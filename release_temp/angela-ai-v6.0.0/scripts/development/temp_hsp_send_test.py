import requests
import json

url = "http://127.0.0.1:8000/api/v1/hsp/send"
headers = {"Content-Type": "application/json"}
payload = {
    "topic": "agent/command",
    "payload": {"command": "start_task", "agent_id": "agent_X"}
}

try:
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    print(f"HSP Send Response: {response.json()}")
except requests.exceptions.ConnectionError:
    print("Error: Could not connect to the backend. Is it running?")
except requests.exceptions.RequestException as e:
    print(f"Error sending HSP message: {e}")
