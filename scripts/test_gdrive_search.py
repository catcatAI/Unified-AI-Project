#!/usr/bin/env python3
"""Test Google Drive API to find and read card pile files (bypassing local .gdoc shortcuts)."""

import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_SRC = PROJECT_ROOT / "apps" / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))
os.chdir(str(PROJECT_ROOT / "apps" / "backend"))

import socket
socket.setdefaulttimeout(15)

print("=" * 60)
print("📖 Google Drive API - Find & Read Card Files")
print("=" * 60)

try:
    from integrations.google_drive_service import get_drive_service
    drive = get_drive_service()
    
    # Step 1: Authenticate
    print("\n1️⃣ Authenticating...")
    if not drive.is_authenticated():
        print("   ❌ Auth failed")
        sys.exit(1)
    print("   ✅ Authenticated")
    
    # Step 2: Find the card pile folder
    print("\n2️⃣ Searching for card pile folder...")
    # Search for files with "卡片堆" or "card" in the name
    folders = drive.list_files(page_size=50, query="mimeType='application/vnd.google-apps.folder'")
    card_folder = None
    for f in folders:
        name = f.get('name', '')
        if '卡片堆' in name or '卡' in name:
            card_folder = f
            print(f"   Found: '{name}' (id: {f.get('id')})")
    
    if not card_folder:
        print("   No card pile folder found via search, trying broader search...")
        # List recent folders
        drive_folders = [f for f in folders if 'folder' in f.get('mimeType','')]
        print(f"   Total folders: {len(drive_folders)}")
        for f in drive_folders[:10]:
            print(f"     📁 {f.get('name')} ({f.get('id')})")
    
    # Step 3: Try to search for card-related documents
    print("\n3️⃣ Searching for card documents...")
    card_docs = drive.list_files(page_size=20, query="name contains '角色卡' or name contains '卡組' or name contains '卡片'")
    print(f"   Found {len(card_docs)} card-related documents:")
    for d in card_docs[:10]:
        mime = d.get('mimeType', '')
        icon = '📄' if 'document' in mime else '📎'
        print(f"     {icon} {d.get('name')} ({d.get('id')})")
    
    # Step 4: Try to read one document if found
    if card_docs:
        doc = card_docs[0]
        doc_id = doc.get('id')
        doc_name = doc.get('name')
        print(f"\n4️⃣ Reading: {doc_name}")
        content = drive.export_gdoc(doc_id, "text/plain")
        if content:
            print(f"   ✅ Read {len(content)} chars!")
            print(f"   {'─' * 40}")
            print(f"   {content[:300]}")
            print(f"   {'─' * 40}")
        else:
            print(f"   ❌ export_gdoc returned None")
    
except Exception as e:
    print(f"\n   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
