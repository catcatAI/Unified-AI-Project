#!/usr/bin/env python3
"""Find card pile folder and read all Google Docs within it."""

import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_SRC = PROJECT_ROOT / "apps" / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))
os.chdir(str(PROJECT_ROOT / "apps" / "backend"))

import socket
socket.setdefaulttimeout(20)

print("=" * 60)
print("📖 Find Card Pile & Read Google Docs")
print("=" * 60)

try:
    from integrations.google_drive_service import get_drive_service
    drive = get_drive_service()
    
    if not drive.is_authenticated():
        print("❌ Auth failed")
        sys.exit(1)
    print("✅ Authenticated\n")

    # Step 1: Find all folders with "卡片" in name
    print("1️⃣ Finding card pile folder...")
    results = drive._get_service().files().list(
        q="mimeType='application/vnd.google-apps.folder' and name contains '卡片'",
        pageSize=30,
        fields="files(id,name,mimeType,parents)"
    ).execute()
    folders = results.get('files', [])
    print(f"   Found {len(folders)} folder(s):")
    for f in folders:
        print(f"     📁 {f['name']} (id={f['id']})")
    
    # If found, list files inside
    if folders:
        card_folder = folders[0]  # Use first match
        folder_id = card_folder['id']
        
        print(f"\n2️⃣ Listing files inside '{card_folder['name']}'...")
        results = drive._get_service().files().list(
            q=f"'{folder_id}' in parents",
            pageSize=200,
            fields="files(id,name,mimeType,size,modifiedTime)"
        ).execute()
        files = results.get('files', [])
        
        doc_count = sum(1 for f in files if f.get('mimeType') == 'application/vnd.google-apps.document')
        other_count = len(files) - doc_count
        print(f"   Total files: {len(files)}")
        print(f"   Google Docs: {doc_count}")
        print(f"   Other files: {other_count}")
        
        # Show all file types
        from collections import Counter
        types = Counter(f.get('mimeType','?') for f in files)
        for mt, cnt in types.most_common():
            short = mt.split('.')[-1] if '.' in mt else mt[:40]
            print(f"     {cnt:3d} × {short}")
        
        # Print names of Google Docs
        google_docs = [f for f in files if f.get('mimeType') == 'application/vnd.google-apps.document']
        print(f"\n3️⃣ Google Docs ({len(google_docs)} total):")
        for i, d in enumerate(google_docs):
            print(f"     {i+1:2d}. 📄 {d['name']}")
        
        # Try to read the first 3 docs
        if google_docs:
            print(f"\n4️⃣ Reading first 3 docs...")
            for i, d in enumerate(google_docs[:3]):
                doc_id = d['id']
                name = d['name']
                print(f"\n   [{i+1}] {name}")
                content = drive.export_gdoc(doc_id, "text/plain")
                if content:
                    print(f"       ✅ {len(content)} chars")
                    print(f"       {'─'*30}")
                    print(f"       {content[:200]}")
                    print(f"       {'─'*30}")
                else:
                    print(f"       ❌ export failed")
    
    else:
        print("\n❌ No card-related folders found")
        print("   Listing all folders (top 20):")
        results = drive._get_service().files().list(
            q="mimeType='application/vnd.google-apps.folder'",
            pageSize=20,
            fields="files(id,name)"
        ).execute()
        all_folders = results.get('files', [])
        for f in all_folders:
            print(f"     📁 {f['name']}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
