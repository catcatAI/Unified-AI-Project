"""
Check backend server startup — attempts to import the app and 
verify all critical modules load without error.
Usage: python scripts/check_backend_startup.py
"""
import sys
import os
import time
import traceback

SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))
sys.path.insert(0, SRC)

print("=== Backend Startup Check ===")

# Step 1: Try importing the main app
print("\n[1/5] Importing main_api_server...")
try:
    from services.main_api_server import app
    print(f"  ✅ App imported. Routes: {len(app.routes)}")
except Exception as e:
    print(f"  ❌ {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 2: Try importing key services
print("\n[2/5] Importing key services...")
services = [
    ("LLM Router", "services.llm.router", "AngelaLLMService"),
    ("Chat Service", "services.chat_service", "ChatService"),
    ("Model Bus", "ai.core.model_bus", "ModelBus"),
    ("ED3N Engine", "ai.ed3n.ed3n_engine", "ED3NEngine"),
    ("GARDEN Engine", "ai.garden.garden_engine", "GARDENEngine"),
]
for label, module_path, class_name in services:
    try:
        mod = __import__(module_path, fromlist=[class_name])
        cls = getattr(mod, class_name)
        print(f"  ✅ {label}: {class_name} imported")
    except Exception as e:
        print(f"  ⚠️  {label}: {e}")

# Step 3: Check config/LLM providers
print("\n[3/5] Checking LLM providers...")
config_dir = os.path.join(SRC, "..", "configs", "system")
import yaml
config_path = os.path.join(os.path.dirname(SRC), "configs", "system", "llm.default.yaml")
try:
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    for name, provider in cfg.get("providers", {}).items():
        enabled = provider.get("enabled", False)
        api_key_set = bool(os.environ.get(provider.get("env_key", "").split("}")[0].split("{")[-1] if "{" in provider.get("env_key", "") else provider.get("env_key", ""), ""))
        print(f"  {'✅' if enabled else '❌'} {name}: enabled={enabled}")
except Exception as e:
    print(f"  ⚠️  Config check: {e}")

# Step 4: Check if server can be started with uvicorn
print("\n[4/5] Testing uvicorn startup (5s timeout)...")
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(("127.0.0.1", 8000))
sock.close()
print(f"  Port 8000: {'in use' if result == 0 else 'available'}")

# Step 5: Quick server start test
print("\n[5/5] Starting server for 3 seconds...")
import subprocess
import signal

startup_code = """
import sys
sys.path.insert(0, "apps/backend/src")
from services.main_api_server import app
import uvicorn
uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
"""

proc = subprocess.Popen(
    [sys.executable, "-u", "-c", startup_code],
    cwd=os.path.dirname(SRC),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True, bufsize=1
)

# Wait and check
time.sleep(4)
poll = proc.poll()
if poll is not None:
    output = proc.stdout.read()
    print(f"  ❌ Server exited with code {poll}")
    # Show errors (last part of output)
    for line in output.split("\n")[-20:]:
        if "error" in line.lower() or "traceback" in line.lower() or "exception" in line.lower():
            print(f"     {line}")
    print(f"  Full output tail:\\n{output[-1000:]}")
else:
    print(f"  ✅ Server running (PID {proc.pid})")
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:8000/api/v1/ops/health")
        resp = urllib.request.urlopen(req, timeout=3)
        print(f"  ✅ Health: {resp.status}")
        print(f"     {resp.read().decode()[:300]}")
    except Exception as e:
        print(f"  ⚠️  Health request: {e}")
    proc.terminate()
    proc.wait()
    print("  ✅ Server stopped cleanly")

print("\n=== Check Complete ===")
