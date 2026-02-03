import requests
import json

url = "http://127.0.0.1:8000/api/v1/chat/mscu"
headers = {"Content-Type": "application/json"}
data = {
    "message": "根據活動紀錄，請告訴我關於未來的預測和物理世界的變化，AI的觀點是什麼？"
}

try:
    print("Querying AI for summary...")
    response = requests.post(url, headers=headers, json=data, timeout=300)
    response.raise_for_status()
    print("AI Response:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
