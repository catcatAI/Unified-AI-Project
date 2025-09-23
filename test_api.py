import requests

try:
    response = requests.get('http://localhost:8000/')
    print("Status code:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)