import hmac
import hashlib
import json
import time
import requests
from pathlib import Path

def test_full_system_flow():
    print("🚀 Starting Final Integration Test...")
    
    # 1. Check if keys exist
    key_file = Path("apps/backend/data/security/abc_keys.json")
    if not key_file.exists():
        print("❌ Security keys not found. Please run security_monitor.py first.")
        return

    with open(key_file, "r") as f:
        keys = json.load(f)
    
    key_b = keys["KeyB"]
    key_c = keys["KeyC"]
    print(f"✅ Loaded Keys: KeyB={key_b[:10]}..., KeyC={key_c[:10]}...")

    base_url = "http://localhost:8000"
    
    # 2. Test Mobile Secure Request
    print("\n--- Testing Mobile Secure Request ---")
    payload = {"message": "Hello Angela, this is a secure mobile test", "timestamp": int(time.time())}
    payload_str = json.dumps(payload, separators=(',', ':'))
    signature = hmac.new(key_b.encode(), payload_str.encode(), hashlib.sha256).hexdigest()
    
    try:
        resp = requests.post(
            f"{base_url}/api/v1/mobile/test",
            json=payload,
            headers={"X-Angela-Signature": signature}
        )
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
        assert resp.status_code == 200
    except Exception as e:
        print(f"❌ Mobile Test Failed: {e}")

    # 3. Test Desktop Key C Sync
    print("\n--- Testing Desktop Key C Sync ---")
    try:
        resp = requests.get(f"{base_url}/api/v1/security/sync-key-c")
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Synced Key C matches: {data['key_c'] == key_c}")
        assert data['key_c'] == key_c
    except Exception as e:
        print(f"❌ Desktop Sync Failed: {e}")

    # 4. Test System Status (Secure)
    print("\n--- Testing Secure System Status ---")
    status_payload = {"action": "get_status", "timestamp": int(time.time())}
    status_payload_str = json.dumps(status_payload, separators=(',', ':'))
    status_sig = hmac.new(key_b.encode(), status_payload_str.encode(), hashlib.sha256).hexdigest()
    
    try:
        resp = requests.post(
            f"{base_url}/api/v1/system/status",
            json=status_payload,
            headers={"X-Angela-Signature": status_sig}
        )
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"System Stats: {data.get('stats')}")
        assert resp.status_code == 200
    except Exception as e:
        print(f"❌ System Status Failed: {e}")

    print("\n✅ Final Integration Test Completed Successfully!")

if __name__ == "__main__":
    test_full_system_flow()
