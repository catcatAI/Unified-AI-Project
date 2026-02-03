import requests
import json

base_url = "http://127.0.0.1:8000/api/v1/auth"
headers = {"Content-Type": "application/json"}

# Test successful login
login_url = f"{base_url}/login"
login_payload_success = {
    "username": "test",
    "password": "password"
}

print("--- Testing successful login ---")
try:
    response = requests.post(login_url, headers=headers, data=json.dumps(login_payload_success))
    response.raise_for_status()
    login_response = response.json()
    print(f"Login Success Response: {login_response}")
    user_info = login_response.get("user")
except requests.exceptions.ConnectionError:
    print("Error: Could not connect to the backend. Is it running?")
    user_info = None
except requests.exceptions.RequestException as e:
    print(f"Error during successful login test: {e}")
    user_info = None

# Test failed login
login_payload_fail = {
    "username": "wrong_user",
    "password": "wrong_password"
}

print("\n--- Testing failed login ---")
try:
    response = requests.post(login_url, headers=headers, data=json.dumps(login_payload_fail))
    response.raise_for_status()
    print(f"Login Fail Response (unexpected success): {response.json()}")
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        print(f"Login Fail Response (expected 401): {e.response.json()}")
    else:
        print(f"Login Fail Response (unexpected error): {e}")
except requests.exceptions.ConnectionError:
    print("Error: Could not connect to the backend. Is it running?")
except requests.exceptions.RequestException as e:
    print(f"Error during failed login test: {e}")


# Test authorization (if login was successful)
if user_info:
    authorize_url = f"{base_url}/authorize"

    # Test successful authorization
    authorize_payload_success = {
        "user_info": user_info,
        "required_roles": ["user"]
    }
    print("\n--- Testing successful authorization ---")
    try:
        response = requests.post(authorize_url, headers=headers, data=json.dumps(authorize_payload_success))
        response.raise_for_status()
        print(f"Authorize Success Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error during successful authorization test: {e}")

    # Test failed authorization
    authorize_payload_fail = {
        "user_info": user_info,
        "required_roles": ["admin"]
    }
    print("\n--- Testing failed authorization ---")
    try:
        response = requests.post(authorize_url, headers=headers, data=json.dumps(authorize_payload_fail))
        response.raise_for_status()
        print(f"Authorize Fail Response (unexpected success): {response.json()}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print(f"Authorize Fail Response (expected 403): {e.response.json()}")
        else:
            print(f"Authorize Fail Response (unexpected error): {e}")
    except requests.exceptions.RequestException as e:
        print(f"Error during failed authorization test: {e}")
