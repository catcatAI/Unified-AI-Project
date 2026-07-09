#!/usr/bin/env python3
"""Quick test: just check if Google Drive token can authenticate (no API calls)."""

import sys
import os
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_SRC = PROJECT_ROOT / "apps" / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))
os.chdir(str(PROJECT_ROOT / "apps" / "backend"))

TOKEN_PATH = PROJECT_ROOT / "apps" / "backend" / "data" / "google_tokens.json"
CRED_PATH = PROJECT_ROOT / "apps" / "backend" / "config" / "credentials.json"

print("=" * 60)
print("🔑 Google Drive Quick Auth Test")
print("=" * 60)

if TOKEN_PATH.exists():
    with open(TOKEN_PATH) as f:
        t = json.load(f)
    print(f"\nToken file: {TOKEN_PATH.stat().st_size} bytes")
    print(f"  Has refresh_token: {'✅' if t.get('refresh_token') else '❌'}")
    print(f"  Client ID: {str(t.get('client_id',''))[:25]}...")
    expiry = t.get('expiry', 'N/A')
    print(f"  Expiry: {expiry}")

if CRED_PATH.exists():
    print(f"\nCredentials: ✅ {CRED_PATH.stat().st_size} bytes")

try:
    from google.auth.transport.requests import Request
    print(f"\nGoogle auth libs: ✅ imported OK")
except Exception as e:
    print(f"\nGoogle auth libs: ❌ {e}")

try:
    from integrations.google_drive_service import get_drive_service
    drive = get_drive_service()
    print(f"\nDriveService: ✅ created")
    
    # Try is_authenticated with short timeout
    import socket
    socket.setdefaulttimeout(10)
    
    import time
    start = time.time()
    result = drive.is_authenticated()
    elapsed = time.time() - start
    
    if result:
        print(f"  ✅ Authenticated! ({elapsed:.1f}s)")
        print(f"\n🎉 Google Drive token is VALID!")
        print(f"  The .gdoc reader should work.")
    else:
        print(f"  ❌ Not authenticated ({elapsed:.1f}s)")
        print(f"\nToken is expired or credentials are wrong.")
        print(f"Need to re-authenticate via OAuth flow.")
        
except Exception as e:
    print(f"\n  ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
