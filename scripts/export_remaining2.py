"""Export ALL remaining .gdoc files from Google Drive using DriveFS metadata."""
import sqlite3
import os
import requests
import time
import re

# Get all Google Docs with their cloud IDs
db_path = r'C:\Users\zofug\AppData\Local\Google\DriveFS\118405592145533730694\mirror_metadata_sqlite.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    SELECT i.local_title, s.cloud_id, i.mime_type
    FROM items i
    JOIN stable_ids s ON i.stable_id = s.stable_id
    WHERE i.mime_type = 'application/vnd.google-apps.document'
""")
all_docs = {}
for title, cloud_id, mime in cursor.fetchall():
    if title and cloud_id:
        all_docs[title] = cloud_id
conn.close()

# Check what we already have
export_dir = r"D:\Projects\Unified-AI-Project\data\gdrive_export"
exported = set(f.replace('.txt', '') for f in os.listdir(export_dir) if f.endswith('.txt'))

# Find missing - try matching by title (may have .gdoc suffix)
missing = {}
for title, cid in all_docs.items():
    clean = title.replace('.gdoc', '').strip()
    if clean not in exported and title not in exported:
        missing[title] = cid

print(f"Total Google Docs in DB: {len(all_docs)}")
print(f"Already exported: {len(exported)}")
print(f"Missing: {len(missing)}")

# Export all missing
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

success = 0
failed = 0
for i, (name, file_id) in enumerate(sorted(missing.items())):
    # Sanitize filename
    safe = re.sub(r'[\\/:*?"<>|]', '_', name.replace('.gdoc', '').strip())
    if not safe:
        safe = f"unnamed_{i}"
    
    url = f"https://docs.google.com/document/d/{file_id}/export?format=txt"
    try:
        resp = session.get(url, timeout=15, allow_redirects=True)
        if resp.status_code == 200 and len(resp.content) > 50:
            content = resp.text
            if content.startswith('\ufeff'):
                content = content[1:]
            fp = os.path.join(export_dir, f"{safe}.txt")
            with open(fp, 'w', encoding='utf-8') as f:
                f.write(content)
            success += 1
            print(f"[{i+1}/{len(missing)}] OK: {safe[:60]} ({len(resp.content)} bytes)")
        else:
            failed += 1
            print(f"[{i+1}/{len(missing)}] FAIL: {safe[:60]} (status={resp.status_code})")
    except Exception as e:
        failed += 1
        print(f"[{i+1}/{len(missing)}] ERROR: {safe[:60]}: {str(e)[:60]}")
    
    time.sleep(0.25)

print(f"\n=== DONE: {success} exported, {failed} failed ===")
print(f"Total files now: {len(exported) + success}")
