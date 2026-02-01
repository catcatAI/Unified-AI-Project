import requests
import json

url = "http://127.0.0.1:8000/api/v1/chat/mscu"
headers = {"Content-Type": "application/json"}
data = {
    "messages": [
        {"role": "user", "content": "test"}
    ],
    "context_variables": {}
}

try:
    print(f"Sending request to {url}...")
    response = requests.post(url, headers=headers, json=data, timeout=10)
    print("Status Code:", response.status_code)
    try:
        print("Response Body:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception:
        print("Response Text:", response.text)
except Exception as e:
    print(f"Error: {e}")
