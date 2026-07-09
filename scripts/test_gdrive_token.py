#!/usr/bin/env python3
"""Test Google Drive OAuth token validity and try to read a .gdoc file."""

import sys
import os
import json
from pathlib import Path

# Add backend src to path
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_SRC = PROJECT_ROOT / "apps" / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

# Change to backend directory (where config/credentials.json is relative to)
os.chdir(str(PROJECT_ROOT / "apps" / "backend"))

print("=" * 60)
print("🔑 Google Drive Token Test")
print("=" * 60)

# Check credentials file
CRED_PATH = PROJECT_ROOT / "apps" / "backend" / "config" / "credentials.json"
TOKEN_PATH = PROJECT_ROOT / "apps" / "backend" / "data" / "google_tokens.json"

print(f"\n📁 Checking credential files...")
print(f"  credentials.json: {'✅ EXISTS' if CRED_PATH.exists() else '❌ MISSING'} ({CRED_PATH.stat().st_size} bytes)" if CRED_PATH.exists() else f"  credentials.json: ❌ MISSING")
print(f"  google_tokens.json: {'✅ EXISTS' if TOKEN_PATH.exists() else '❌ MISSING'} ({TOKEN_PATH.stat().st_size} bytes)" if TOKEN_PATH.exists() else f"  google_tokens.json: ❌ MISSING")

if TOKEN_PATH.exists():
    with open(TOKEN_PATH) as f:
        token_data = json.load(f)
    print(f"\n📋 Token info:")
    print(f"  Token type: {token_data.get('token_type', 'unknown')}")
    print(f"  Has refresh_token: {'✅' if token_data.get('refresh_token') else '❌ No'}")
    print(f"  Client ID: {token_data.get('client_id', 'N/A')[:20]}...")
    expiry = token_data.get('expiry', 'N/A')
    print(f"  Expiry: {expiry}")

print("\n🔄 Testing Google Drive API connection...")
try:
    from integrations.google_drive_service import get_drive_service, GoogleDriveService
    drive = get_drive_service()
    
    # First check if already authenticated
    if drive.is_authenticated():
        print("  ✅ Token valid — already authenticated!")
    else:
        print("  ❌ Token invalid or expired")
        print("  ℹ️  Need to re-authenticate via OAuth flow")
        
        # Check if credentials.json exists for re-auth
        if CRED_PATH.exists():
            print("  ✅ credentials.json available for re-authentication")
        else:
            print("  ❌ credentials.json missing — cannot re-authenticate")
        sys.exit(1)

    # Try to list files (limited)
    print("\n📂 Testing Drive API call (list files, limit 5)...")
    try:
        files = drive.list_files(page_size=5)
        print(f"  ✅ Success! Found {len(files)} file(s):")
        for f in files[:5]:
            mime = f.get('mimeType', '?')
            name = f.get('name', '?')
            icon = "📄" if "document" in mime else "📁" if "folder" in mime else "📎"
            print(f"    {icon} {name} ({mime})")
    except Exception as e:
        print(f"  ❌ API call failed: {e}")
        sys.exit(1)

    # Try to read a .gdoc file from the card pile
    CARD_PILE = PROJECT_ROOT / "G:" / "我的雲端硬碟" / "卡片堆"
    # Also try the direct path
    from pathlib import PureWindowsPath
    try:
        gdoc_dir = r"G:\我的雲端硬碟\卡片堆"
        print(f"\n📇 Checking card pile directory: {gdoc_dir}")
        from core.card.parser.gdoc_reader import read_gdoc_file
        
        # Get one .gdoc file to test
        import glob as pyglob
        gdoc_files = pyglob.glob(os.path.join(gdoc_dir, "*.gdoc"))
        print(f"  Found {len(gdoc_files)} .gdoc files")
        
        if gdoc_files:
            test_file = gdoc_files[0]
            fname = os.path.basename(test_file)
            print(f"\n📖 Attempting to read: {fname}")
            print(f"  (this calls Google Drive API to export the document)...")
            content = read_gdoc_file(test_file)
            if content:
                print(f"  ✅ SUCCESS! Read {len(content)} characters")
                print(f"  First 200 chars:")
                print(f"  {'─' * 40}")
                print(f"  {content[:200]}")
                print(f"  {'─' * 40}")
            else:
                print(f"  ❌ Failed to read document content")
        else:
            print("  ⚠️  No .gdoc files found")
            
    except Exception as e:
        print(f"  ⚠️  Card pile test: {e}")

except ImportError as e:
    print(f"  ❌ Import failed: {e}")
    print(f"  Python path: {sys.path[:3]}")
    sys.exit(1)
except Exception as e:
    print(f"  ❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ Test complete!")
print("=" * 60)
