import requests
import time
import json
import logging
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000/api/v1"

def test_phase_2_loop():
    print("--- Phase 2: Spark of Life Verification ---")
    
    # 1. Initialize Components
    print("\n[1/3] Initializing Components...")
    try:
        init_res = requests.post(f"{BASE_URL}/ai/init")
        print(f"Init Status: {init_res.status_code}")
        print(init_res.json())
    except Exception as e:
        print(f"Initialization failed: {e}")
        return

    # 2. Check Initial Balance
    print("\n[2/3] Checking Initial Balance...")
    bal_res = requests.get(f"{BASE_URL}/economy/balance")
    initial_balance = bal_res.json().get("balance", 0)
    print(f"Initial Balance: {initial_balance}")

    # 3. Interact with Pet (Dynamic Quality Chat)
    print("\n[3/3] Interacting with Pet (Quality Assessment Test)...")
    interactions = [
        "Hello Angela! Tell me something perfect and excellent about AGI.",
        "Give me a short, incomplete answer."
    ]
    
    for msg in interactions:
        print(f"\nUser: {msg}")
        interact_payload = {
            "input_type": "message",
            "payload": {"text": msg}
        }
        res = requests.post(f"{BASE_URL}/pet/interact", json=interact_payload)
        
        if res.status_code == 200:
            data = res.json()
            response = data.get("pet_response")
            metadata = data.get("metadata", {})
            quality = metadata.get("quality_score", 0)
            
            # Check Status for Personality updates
            status_res = requests.get(f"{BASE_URL}/pet/status")
            status_data = status_res.json()
            personality = status_data.get("personality", {})
            print(f"Mood: {personality.get('mood')}")
            print(f"Happiness: {personality.get('emotions', {}).get('happiness')}")
            
            # Check Balance after each
            new_bal_res = requests.get(f"{BASE_URL}/economy/balance")
            current_balance = new_bal_res.json().get("balance", 0)
            reward = current_balance - initial_balance
            print(f"Current Balance: {current_balance} (Cumulative Reward: {reward:.2f})")
            initial_balance = current_balance
        else:
            print(f"Interaction failed: {res.status_code}")
            print(res.text)

if __name__ == "__main__":
    test_phase_2_loop()
