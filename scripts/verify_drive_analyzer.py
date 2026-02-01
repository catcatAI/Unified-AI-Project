import requests
import json
import sys

API_URL = "http://127.0.0.1:8000/api/v1"

def verify_drive_analyzer():
    print(f"Testing Drive Analyzer endpoint at {API_URL}/drive/analyze...")
    
    try:
        # Trigger analysis
        response = requests.post(f"{API_URL}/drive/analyze", params={"limit": 5}, timeout=300)
        
        if response.status_code == 200:
            data = response.json()
            analysis = data.get("analysis", "No analysis found")
            
            print("\n✅ Drive Analyzer Verification Passed!")
            print(f"Analysis Length: {len(analysis)} chars")
            print("-" * 40)
            print("Preview of Analysis:")
            print("-" * 40)
            print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
            print("-" * 40)
            return True
        else:
            print(f"❌ Verification Failed: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        return False

if __name__ == "__main__":
    success = verify_drive_analyzer()
    sys.exit(0 if success else 1)
