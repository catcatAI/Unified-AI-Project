import requests
import json
import sys

url = "http://127.0.0.1:8000/api/v1/chat/mscu"
headers = {"Content-Type": "application/json"}
data = {
    "messages": [
        {"role": "user", "content": "請告訴我最近在我的活動資料夾裡的聊天紀錄有什麼內容？"}
    ]
}

try:
    print(f"Sending request to {url}...")
    response = requests.post(url, headers=headers, json=data, timeout=60)
    response.raise_for_status()
    print("Status Code:", response.status_code)
    print("Response Body:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
