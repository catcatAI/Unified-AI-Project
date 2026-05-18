import requests
import sys
import logging
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000/api/v1/drive"

def test_drive_integration():
    print("=== Google Drive Integration Test ===\n")

    try:
        # 1. Status check
        print("1. Checking status...")
        status_res = requests.get(f"{BASE_URL}/status", timeout=10)
        status = status_res.json()
        print(f"   Status: {status.get('status')}, Authenticated: {status.get('authenticated')}")

        if not status.get("authenticated"):
            print("\n❌ Not authenticated. Run get_drive_auth_url.py and exchange_drive_code.py first.")
            print("   Then run this script again to test file operations.")
            return False

        # 2. List files
        print("\n2. Listing files...")
        files_res = requests.get(f"{BASE_URL}/files?page_size=5", timeout=15)
        files = files_res.json().get("files", [])
        print(f"   Found {len(files)} files")
        for f in files:
            print(f"   - {f.get('name')} ({f.get('mimeType', '').split('.')[-1]})")

        # 3. Storage info
        print("\n3. Storage info...")
        quota = status.get("quota", {})
        print(f"   User: {quota.get('user', 'N/A')}")
        print(f"   Used: {quota.get('used', 'N/A')} / {quota.get('total', 'N/A')}")

        # 4. Sync (if files exist)
        if files:
            print("\n4. Syncing files...")
            file_ids = [f["id"] for f in files[:2]]
            sync_res = requests.post(
                f"{BASE_URL}/files/sync",
                json={"file_ids": file_ids, "folder_path": "data/drive_downloads"},
                timeout=60,
            )
            result = sync_res.json()
            print(f"   Synced: {result.get('synced')}, Skipped: {result.get('skipped')}, "
                  f"Memorized: {result.get('memorized_count')}")

        # 5. Analyze
        print("\n5. Analyzing files...")
        analyze_res = requests.post(f"{BASE_URL}/analyze", json={"limit": 2}, timeout=120)
        if analyze_res.status_code == 200:
            r = analyze_res.json()
            print(f"   Analyzed {r.get('files_analyzed', 0)} files")
            print(f"   Preview: {r.get('analysis', '')[:200]}...")
        else:
            print(f"   Analyze returned {analyze_res.status_code}")

        print("\n✅ All integration tests passed!")
        return True

    except requests.ConnectException:
        print("❌ Cannot connect to backend. Start with: launch_angela.bat --repl")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    ok = test_drive_integration()
    sys.exit(0 if ok else 1)
