#!/usr/bin/env python3
"""
Download all Google Docs from the card pile folder via Google Drive API.
Saves as .md files in a temp directory so Angela AI can process them.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_SRC = PROJECT_ROOT / "apps" / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))
os.chdir(str(PROJECT_ROOT / "apps" / "backend"))

CARD_PILE_FOLDER_ID = "1IAEM8Fmsp-czVJOgivGLbx10EQ1SThai"
OUTPUT_DIR = PROJECT_ROOT / "data" / "card_pile_downloaded"

import socket
socket.setdefaulttimeout(30)

print("=" * 60)
print("📥 Downloading All Cards from Google Drive")
print("=" * 60)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

try:
    from integrations.google_drive_service import get_drive_service
    drive = get_drive_service()
    
    if not drive.is_authenticated():
        print("❌ Auth failed")
        sys.exit(1)
    print("✅ Authenticated\n")

    # List ALL files in the card pile folder
    print(f"📂 Listing all files in card pile folder...")
    all_items = []
    page_token = None
    while True:
        params = {
            "q": f"'{CARD_PILE_FOLDER_ID}' in parents and trashed=false",
            "pageSize": 200,
            "fields": "nextPageToken,files(id,name,mimeType,size,modifiedTime)",
        }
        if page_token:
            params["pageToken"] = page_token
        results = drive._get_service().files().list(**params).execute()
        all_items.extend(results.get("files", []))
        page_token = results.get("nextPageToken")
        if not page_token:
            break
    
    print(f"   Total items: {len(all_items)}")
    
    # Separate Google Docs from other files
    docs = [f for f in all_items if f.get('mimeType') == 'application/vnd.google-apps.document']
    others = [f for f in all_items if f.get('mimeType') != 'application/vnd.google-apps.document']
    
    print(f"   Google Docs: {len(docs)}")
    if others:
        print(f"   Other: {len(others)}")
        for o in others:
            mt = o.get('mimeType', '?').split('.')[-1]
            print(f"     {o['name']} ({mt})")
    
    # Download each Google Doc
    print(f"\n📖 Downloading {len(docs)} Google Docs...")
    success = 0
    fail = 0
    errors = []
    
    for i, doc in enumerate(docs):
        doc_id = doc['id']
        doc_name = doc['name']
        # Sanitize filename
        safe_name = "".join(c for c in doc_name if c.isalnum() or c in ' .,-_()[]（）【】').strip()
        if not safe_name:
            safe_name = f"doc_{doc_id[:8]}"
        safe_name = safe_name[:100]  # Limit length
        
        out_path = OUTPUT_DIR / f"{safe_name}.md"
        if out_path.exists():
            print(f"   [{i+1}/{len(docs)}] ⏭️  {safe_name} (already exists)")
            continue
        
        try:
            content = drive.export_gdoc(doc_id, "text/plain")
            if content:
                # Add metadata header
                full_content = f"""---
source: Google Docs
doc_id: {doc_id}
original_name: {doc_name}
downloaded: {datetime.now().isoformat()}
---

{content}
"""
                out_path.write_text(full_content, encoding='utf-8')
                char_count = len(content)
                preview = content[:80].replace('\n', ' ').strip()
                print(f"   [{i+1}/{len(docs)}] ✅ {safe_name} ({char_count} chars)")
                print(f"       → {preview}...")
                success += 1
            else:
                print(f"   [{i+1}/{len(docs)}] ❌ {safe_name} (export returned None)")
                fail += 1
                errors.append(f"{safe_name}: export returned None")
        except Exception as e:
            print(f"   [{i+1}/{len(docs)}] ❌ {safe_name} ({e})")
            fail += 1
            errors.append(f"{safe_name}: {e}")
    
    # Summary
    print(f"\n{'=' * 60}")
    print(f"📊 Download Summary:")
    print(f"   Total docs: {len(docs)}")
    print(f"   Success:    {success}")
    print(f"   Failed:     {fail}")
    print(f"   Output:     {OUTPUT_DIR}")
    
    if errors:
        print(f"\n⚠️ Errors ({len(errors)}):")
        for e in errors[:10]:
            print(f"   • {e}")
    
    # Calculate total content size
    total_chars = sum(p.stat().st_size for p in OUTPUT_DIR.glob("*.md"))
    print(f"\n📦 Total content: {total_chars:,} bytes ({total_chars/1024:.0f} KB)")
    
    # List all downloaded files
    print(f"\n📋 Downloaded files:")
    md_files = sorted(OUTPUT_DIR.glob("*.md"))
    for f in md_files:
        size = f.stat().st_size
        name = f.stem[:60]
        print(f"   {size:>8,} B  {name}")

except Exception as e:
    print(f"\n❌ Fatal error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
