#!/usr/bin/env python3
"""
Start Angela AI backend, send card processing task via chat API,
and let Angela handle the card game development document generation.
"""

import sys
import os
import json
import time
import subprocess
import socket
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / "apps" / "backend"
BACKEND_SRC = BACKEND_DIR / "src"
CARD_DATA_DIR = PROJECT_ROOT / "data" / "card_pile_downloaded"
OUTPUT_DIR = Path(r"G:\我的雲端硬碟\卡片開發")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Count cards
md_files = sorted(CARD_DATA_DIR.glob("*.md"))
total_chars = sum(f.stat().st_size for f in md_files)
print(f"Cards: {len(md_files)} files, {total_chars//1024} KB")
print(f"Output: {OUTPUT_DIR}")

# Start server
print("Starting Angela backend...")
env = os.environ.copy()
env["PYTHONPATH"] = str(BACKEND_SRC)
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "services.main_api_server:app",
     "--host", "127.0.0.1", "--port", "8000"],
    cwd=str(BACKEND_DIR), env=env,
    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
)

# Wait for server
start = time.time()
while time.time() - start < 120:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    if sock.connect_ex(("127.0.0.1", 8000)) == 0:
        sock.close()
        print(f"✅ Server ready in {int(time.time()-start)}s")
        break
    sock.close()
    time.sleep(1)
else:
    print("❌ Server timeout")
    proc.kill()
    sys.exit(1)

# Send task to Angela
import urllib.request

task = f"""I need you to create a complete card game development document from my card collection.

There are {len(md_files)} card documents in: {CARD_DATA_DIR}

Please:
1. Read ALL card files from that directory
2. Categorize them (character cards, organization cards, nation cards, rule cards, scene cards, event cards, etc.)
3. Check for conflicts, missing fields, and inconsistencies
4. Auto-fill missing information where possible
5. Generate a comprehensive card game development document

Output your work to: {OUTPUT_DIR}

Also create an index file listing all cards with their categories.

Start by reading the files. Tell me your findings as you go."""

data = json.dumps({
    "message": task,
    "session_id": f"card-dev-{int(time.time())}",
    "user_name": "GameMaster"
}).encode()

req = urllib.request.Request(
    "http://127.0.0.1:8000/chat/unified",
    data=data, headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=600) as resp:
        result = json.loads(resp.read())
    text = result.get("response_text", "")
    print(f"\n📝 Angela says ({len(text)} chars):")
    print(text[:300])
except Exception as e:
    stderr = proc.stderr.read().decode()[:500] if proc.stderr else ""
    print(f"❌ Error: {e}")
    if stderr:
        print(f"   Server: {stderr}")

print(f"\nServer running at http://127.0.0.1:8000")
print("Ctrl+C to stop")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    proc.terminate()
    print("Stopped.")
