"""
Comprehensive backend startup check — imports, config, services, port, server test.
Uses :mod:`scripts._server_helper` for robustness.

Usage::

    python scripts/check_backend_startup.py
"""

import sys
import os
import traceback

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from scripts._server_helper import (
    get_src_path, get_project_root, start_server, stop_server,
    wait_for_server, test_health, get_llm_config,
)

SRC = str(get_src_path())
sys.path.insert(0, SRC)

print("=== Backend Startup Check ===\n")

# Step 1: Import main app
print("[1/5] Importing main_api_server...")
try:
    from services.main_api_server import app
    print(f"  ✅ App imported. Routes: {len(app.routes)}")
except Exception as e:
    print(f"  ❌ {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 2: Import key services
print("\n[2/5] Importing key services...")
services=[
    ("LLM Router", "services.llm.router", "AngelaLLMService"),
    ("Chat Service", "services.chat_service", "ChatService"),
    ("Model Bus", "ai.core.model_bus", "ModelBus"),
    ("ED3N Engine", "ai.ed3n.ed3n_engine", "ED3NEngine"),
    ("GARDEN Engine", "ai.garden.garden_engine", "GARDENEngine"),
]
for label, module_path, class_name in services:
    try:
        mod = __import__(module_path, fromlist=[class_name])
        getattr(mod, class_name)
        print(f"  ✅ {label}")
    except Exception as e:
        print(f"  ⚠️  {label}: {e}")

# Step 3: Check LLM provider configs
print("\n[3/5] LLM provider config...")
cfg = get_llm_config()
for name, provider in cfg.get("providers", {}).items():
    enabled = provider.get("enabled", False)
    print(f"  {'✅' if enabled else '❌'} {name}: enabled={enabled}")

# Step 4: Check port
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(("127.0.0.1", 8000))
sock.close()
port_status="in use" if result == 0 else "available"
print(f"\n[4/5] Port 8000: {port_status}")

# Step 5: Start server and test
print("\n[5/5] Starting server (10s window)...")
proc = start_server(wait_seconds=6.0)
print(f"  Server PID: {proc.pid}")

ready = wait_for_server(timeout=8.0)
if ready:
    print("  ✅ Server accepting connections")
    ok, data = test_health()
    print(f"  ✅ Health: {data}")
else:
    print("  ⚠️  Server not ready within timeout")

stop_server(proc)
print("  ✅ Server stopped")

print("\n=== Check Complete ===")
