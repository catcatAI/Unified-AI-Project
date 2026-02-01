import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_proactive_messaging():
    print("--- Phase 2.2: Proactive Messaging Test ---\n")
    
    # 1. Initialize
    print("[1/4] Initializing...")
    init_res = requests.post(f"{BASE_URL}/ai/init")
    print(f"Init Status: {init_res.status_code}\n")
    
    # 2. Trigger high happiness (should trigger "sharing_joy" or "curious_question")
    print("[2/4] Triggering high happiness...")
    for i in range(3):
        interact_payload = {
            "input_type": "message",
            "payload": {"text": f"You're amazing Angela! #{i+1}"}
        }
        res = requests.post(f"{BASE_URL}/pet/interact", json=interact_payload)
        if res.status_code == 200:
            print(f"  Interaction {i+1}: Success")
        time.sleep(1)
    
    # 3. Check status
    print("\n[3/4] Checking personality status...")
    status_res = requests.get(f"{BASE_URL}/pet/status")
    status = status_res.json()
    personality = status.get("personality", {})
    print(f"  Mood: {personality.get('mood')}")
    print(f"  Happiness: {personality.get('emotions', {}).get('happiness')}")
    print(f"  Excitement: {personality.get('emotions', {}).get('excitement')}")
    
    # 4. Wait for heartbeat and check proactive messages
    print("\n[4/4] Waiting 65 seconds for personality heartbeat...")
    time.sleep(65)
    
    proactive_res = requests.get(f"{BASE_URL}/pet/proactive")
    proactive_data = proactive_res.json()
    
    print(f"\nProactive Messages Found: {proactive_data.get('count', 0)}")
    for msg in proactive_data.get('messages', []):
        print(f"\n  Trigger: {msg.get('trigger_type')}")
        print(f"  Tone: {msg.get('tone')}")
        print(f"  Text: {msg.get('text')[:100]}...")

if __name__ == "__main__":
    test_proactive_messaging()
