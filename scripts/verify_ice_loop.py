import requests
import time
import json

BASE_URL = "http://127.0.0.1:8000"

def test_ice_loop():
    print("--- Testing ICE Loop (Self-Evolution) ---")
    
    # 0. Wait for Backend
    print("Waiting for backend...")
    for _ in range(30):
        try:
            res = requests.get(f"{BASE_URL}/api/v1/health")
            if res.status_code == 200:
                print("Backend is healthy.")
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    else:
        print("Backend failed to start in time.")
        return

    # 1. Initialize Components
    print("Initializing components...")
    res = requests.post(f"{BASE_URL}/api/v1/ai/init")
    if res.status_code == 200:
        print(f"Init Result: {json.dumps(res.json(), indent=2)}")
    else:
        print(f"Init Failed: {res.status_code} - {res.text}")
        return
    
    # 2. Simulate Interactions (Investigate Phase)
    interactions = [
        "Hello, who are you?",
        "What is the capital of France?",
        "Tell me a joke about AI.",
        "How do I use the search tool?",
        "What time is it now?"
    ]
    
    for msg in interactions:
        print(f"Sending input: '{msg}'")
        res = requests.post(f"{BASE_URL}/api/v1/chat/mscu", json={"message": msg})
        if res.status_code == 200:
            print(f"Response: {res.json()['response'][:50]}...")
        else:
            print(f"Error: {res.status_code} - {res.text}")
        time.sleep(1)

    # 3. Trigger Consolidation (Consolidate & Exploit Phases)
    print("\n--- Triggering 'Dream' (Consolidation) ---")
    res = requests.post(f"{BASE_URL}/api/v1/ai/dream", params={"batch_size": 5})
    if res.status_code == 200:
        summary = res.json()
        print(f"Consolidation Summary: {json.dumps(summary, indent=2)}")
    else:
        print(f"Error triggering dream: {res.status_code} - {res.text}")

    # 4. Verify Memory Storage
    print("\n--- Verifying Memory Storage ---")
    res = requests.post(f"{BASE_URL}/api/v1/memory/retrieve", json={"query": "Best Practice", "limit": 5})
    if res.status_code == 200:
        memories = res.json().get("memories", [])
        print(f"Found {len(memories)} Best Practice memories.")
        for i, mem in enumerate(memories):
            print(f"[{i}] {mem['document'][:100]}...")
    else:
        print(f"Error searching memory: {res.status_code} - {res.text}")


if __name__ == "__main__":
    test_ice_loop()
