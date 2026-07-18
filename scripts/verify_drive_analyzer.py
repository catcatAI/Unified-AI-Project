import requests
import sys
import logging
logger = logging.getLogger(__name__)

API_URL = "http://127.0.0.1:8000/api/v1"

def verify_drive_status():
    print("=== Google Drive Integration Verification ===\n")

    try:
        status = requests.get(f"{API_URL}/drive/status", timeout=10).json()
        print(f"Status: {status.get('status')}")
        print(f"Authenticated: {status.get('authenticated')}")
        quota = status.get('quota', {})
        if quota:
            print(f"User: {quota.get('user', 'N/A')}")
            print(f"Storage: {quota.get('used', 'N/A')} / {quota.get('total', 'N/A')}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接後端。請先啟動 run_angela.py")
        return False
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return False


def verify_drive_analyzer():
    print(f"\nTesting Drive Analyzer at {API_URL}/drive/analyze...")
    try:
        response = requests.post(f"{API_URL}/drive/analyze", json={"limit": 3}, timeout=120)
        if response.status_code == 200:
            data = response.json()
            analysis = data.get("analysis", "No analysis")
            print("\n✅ Drive Analyzer Passed!")
            print(f"Files analyzed: {data.get('files_analyzed', 0)}")
            print("-" * 40)
            print(analysis[:800] + ("..." if len(analysis) > 800 else ""))
            print("-" * 40)
            return True
        elif response.status_code == 401:
            print("❌ 未認證。請先執行：")
            print("  python scripts/get_drive_auth_url.py")
            print("  python scripts/exchange_drive_code.py <code>")
            return False
        else:
            print(f"❌ Verification Failed: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接後端")
        return False
    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        return False


if __name__ == "__main__":
    s_ok = verify_drive_status()
    a_ok = verify_drive_analyzer() if s_ok else False
    print(f"\n{'✅ All checks passed!' if (s_ok and a_ok) else '⚠️  Some checks failed'}")
    sys.exit(0 if (s_ok and a_ok) else 1)
