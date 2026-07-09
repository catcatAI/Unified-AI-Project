#!/usr/bin/env python3
"""Test reading an actual .gdoc file from the card pile."""

import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_SRC = PROJECT_ROOT / "apps" / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))
os.chdir(str(PROJECT_ROOT / "apps" / "backend"))

CARD_PILE = r"G:\我的雲端硬碟\卡片堆"
TIMEOUT = 15  # seconds per API call

print("=" * 60)
print("📖 .gdoc Reader End-to-End Test")
print("=" * 60)

import socket
socket.setdefaulttimeout(TIMEOUT)

# Find .gdoc files
gdoc_files = sorted([f for f in os.listdir(CARD_PILE) if f.endswith('.gdoc')])
print(f"\n📂 Found {len(gdoc_files)} .gdoc files in card pile")
print(f"   First file: {gdoc_files[0]}")
print(f"   Last file:  {gdoc_files[-1]}")

# Try to read a small one (pick one with a short name, likely less content)
# Let's pick a few candidates
candidates = [f for f in gdoc_files if any(kw in f for kw in ["基調", "簡介", "卡片設計", "Ver 3", "V3"])]
if candidates:
    test_file = os.path.join(CARD_PILE, candidates[0])
else:
    test_file = os.path.join(CARD_PILE, gdoc_files[0])

fname = os.path.basename(test_file)
print(f"\n📖 Attempting to read: {fname}")

try:
    from core.card.parser.gdoc_reader import read_gdoc_file
    print(f"   gdoc_reader imported ✅")
    
    import time
    start = time.time()
    content = read_gdoc_file(test_file)
    elapsed = time.time() - start
    
    if content:
        print(f"\n   ✅ SUCCESS in {elapsed:.1f}s!")
        print(f"   Content length: {len(content)} characters")
        print(f"\n   {'─' * 50}")
        print(f"   First 500 chars:")
        print(f"   {content[:500]}")
        print(f"   {'─' * 50}")
        if len(content) > 500:
            print(f"   ... ({len(content) - 500} more chars)")
    else:
        print(f"\n   ❌ Failed (returned None) in {elapsed:.1f}s")
        
except Exception as e:
    print(f"\n   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
