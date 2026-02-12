import requests
import logging
logger = logging.getLogger(__name__)

def sync_now():
    BASE_URL = "http://127.0.0.1:8000/api/v1"
    
    # 1. Get file IDs
    print("Fetching file list...")
    files_res = requests.get(f"{BASE_URL}/drive/files?page_size=5")
    files = files_res.json().get('files', [])
    if not files:
        print("No files found on Drive.")
        return
    
    file_ids = [f['id'] for f in files[:3]]
    print(f"Syncing files: {[f['name'] for f in files[:3]]}")
    
    # 2. Sync
    sync_res = requests.post(
        f"{BASE_URL}/drive/files/sync",
        json={"file_ids": file_ids}
    )
    
    print(f"Sync Result: {sync_res.status_code}")
    print(sync_res.json())

if __name__ == "__main__":
    sync_now()
