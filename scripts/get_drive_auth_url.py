
import requests
import sys

def get_url():
    try:
        response = requests.get('http://localhost:8000/api/v1/drive/auth/url', timeout=10)
        if response.status_code == 200:
            print(response.json().get('url'))
        else:
            print(f"Error: {response.status_code} - {response.text}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Failed to connect: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    get_url()
