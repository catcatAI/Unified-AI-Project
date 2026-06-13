import os
import requests
import logging
logger = logging.getLogger(__name__)

BASE_URL = os.environ.get("ANGELA_API_URL", "http://127.0.0.1:8000")

def check_auth():
    url = f"{BASE_URL}/api/v1/drive/auth/status"
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")
    except requests.exceptions.ConnectionError:
        print(f"Cannot connect to backend at {BASE_URL}. Is it running?")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_auth()
