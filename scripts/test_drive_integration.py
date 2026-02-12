import requests
import time
import logging
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000/api/v1"

def test_drive_integration():
    print("--- Phase 3.1: Google Drive Integration Test ---\n")
    
    # 1. Check auth status
    print("[1/5] Checking authentication status...")
    status_res = requests.get(f"{BASE_URL}/drive/auth/status")
    print(f"Auth Status: {status_res.json()}\n")
    
    # 2. Authenticate (if not already)
    if not status_res.json().get('authenticated'):
        print("[2/5] Starting OAuth authentication...")
        print("⚠️  A browser window will open for Google login.")
        print("Please authorize the application and return here.\n")
        
        auth_res = requests.post(f"{BASE_URL}/drive/auth/authenticate")
        if auth_res.status_code == 200:
            print("✅ Authentication successful!\n")
        else:
            print(f"❌ Authentication failed: {auth_res.text}\n")
            return
    else:
        print("[2/5] Already authenticated, skipping...\n")
    
    # 3. List files
    print("[3/5] Listing files from Google Drive...")
    files_res = requests.get(f"{BASE_URL}/drive/files?page_size=10")
    files_data = files_res.json()
    files = files_data.get('files', [])
    
    print(f"Found {len(files)} files:")
    for i, file in enumerate(files[:5], 1):
        print(f"  {i}. {file['name']} ({file['mimeType']})")
    print()
    
    # 4. Sync first 3 files
    if files:
        print("[4/5] Syncing first 3 files...")
        file_ids = [f['id'] for f in files[:3]]
        
        sync_res = requests.post(
            f"{BASE_URL}/drive/files/sync",
            json={"file_ids": file_ids}
        )
        
        sync_data = sync_res.json()
        if 'synced' not in sync_data:
             print(f"❌ Sync failed. Response: {sync_data}")
        else:
             print(f"Synced: {sync_data.get('synced')} files")
             print(f"Skipped: {sync_data.get('skipped')} files (unchanged)\n")
        
        for file in sync_data.get('files', []):
            print(f"  ✓ {file['name']} ({file['content_length']} chars)")
        print()
    
    # 5. Get sync stats
    print("[5/5] Getting sync statistics...")
    stats_res = requests.get(f"{BASE_URL}/drive/sync/stats")
    stats = stats_res.json()
    print(f"Total synced files: {stats.get('total_files')}")
    print(f"Last sync: {stats.get('last_sync')}\n")
    
    print("✅ Drive integration test complete!")

if __name__ == "__main__":
    test_drive_integration()
