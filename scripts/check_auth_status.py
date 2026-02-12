import requests
import logging
logger = logging.getLogger(__name__)

def check_auth():
    url = "http://localhost:8000/api/v1/drive/auth/status"
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_auth()
