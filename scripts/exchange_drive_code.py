import requests
import sys

def exchange_code(code):
    url = "http://localhost:8000/api/v1/drive/auth/callback"
    try:
        response = requests.post(url, params={"code": code})
        if response.status_code == 200:
            print("Successfully exchanged code for tokens!")
            print(response.json())
        else:
            print(f"Failed to exchange code: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error connecting to backend: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        exchange_code(sys.argv[1])
    else:
        print("Please provide the authorization code as an argument.")
