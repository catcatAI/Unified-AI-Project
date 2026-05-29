import sys, asyncio, logging
from pathlib import Path

BACKEND_SRC = Path("apps/backend/src").resolve()
sys.path.insert(0, str(BACKEND_SRC))

from integrations.google_drive_service import GoogleDriveService

async def main():
    svc = GoogleDriveService._create()
    if not svc.is_authenticated():
        print("Not authenticated, running auth...")
        return

    files = svc.list_files(query="name contains '6張角色卡' and mimeType='application/vnd.google-apps.document'")
    if not files:
        print("File not found")
        return

    fid = files[0]["id"]
    name = files[0].get("name", "?")
    print(f"Found: {name} (id={fid})")
    
    try:
        meta = svc.get_file_metadata(fid)
        print(f"Metadata: size maybe {meta.get('size', 'N/A')}")
    except Exception as e:
        print(f"Metadata error: {e}")

    try:
        content = svc.download_file_content(fid)
        if content:
            print(f"Content length: {len(content)} chars")
            print("=== FIRST 500 CHARS ===")
            print(content[:500])
            print("=== LAST 300 CHARS ===")
            print(content[-300:])
        else:
            print("Empty content")
    except Exception as e:
        print(f"Export error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
