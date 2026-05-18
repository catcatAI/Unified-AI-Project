import requests
import sys
import logging
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000/api/v1/drive"

def sync_files():
    try:
        status = requests.get(f"{BASE_URL}/status", timeout=10).json()
        if not status.get("authenticated"):
            print("❌ Google Drive 未認證。請先執行：")
            print("  python scripts/get_drive_auth_url.py")
            print("  python scripts/exchange_drive_code.py <code>")
            sys.exit(1)

        files_res = requests.get(f"{BASE_URL}/files?page_size=10", timeout=15)
        files = files_res.json().get("files", [])
        print(f"找到 {len(files)} 個檔案")

        if not files:
            print("沒有檔案可以同步")
            return

        file_ids = [f["id"] for f in files[:5]]
        sync_res = requests.post(
            f"{BASE_URL}/files/sync",
            json={"file_ids": file_ids, "folder_path": "data/drive_downloads"},
            timeout=60,
        )
        result = sync_res.json()
        print(f"同步完成：")
        print(f"  下載: {result.get('synced', 0)} 個")
        print(f"  跳過: {result.get('skipped', 0)} 個")
        print(f"  存入記憶: {result.get('memorized_count', 0)} 個")
        for f in result.get("files", []):
            flag = "✅" if f.get("memorized") else ("⏭️" if f.get("skipped") else "❌")
            print(f"  {flag} {f.get('name')}")

    except requests.ConnectException:
        print("❌ 無法連接後端。請先啟動 launch_angela.bat --repl")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    sync_files()
