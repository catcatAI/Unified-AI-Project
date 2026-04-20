import sys
import json
import time
import httpx
import asyncio
from src.capabilities import OSCapabilities

# Backend configuration
BACKEND_URL = "http://127.0.0.1:8000"

async def call_angela_api(method, endpoint, data=None):
    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                res = await client.get(f"{BACKEND_URL}{endpoint}")
            else:
                res = await client.post(f"{BACKEND_URL}{endpoint}", json=data)
            return res.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

async def main():
    os_cap = OSCapabilities()
    
    if len(sys.argv) < 2:
        print("Usage: python bridge.py <command> [args...]")
        return

    command = sys.argv[1]

    # Auto-scrub workspace on any new command
    os_cap.scrub_workspace()

    if command == "snapshot":
        path = os_cap.take_screenshot()
        print(json.dumps({"status": "success", "action": "screenshot", "path": path}))
    
    elif command == "clipboard":
        print(json.dumps({"status": "success", "content": os_cap.get_clipboard()}))

    # --- NEW: Angela Soul Bridge Commands ---
    elif command == "angela":
        if len(sys.argv) < 3:
            print("Usage: python bridge.py angela <status|pulse|think|rest>")
            return
        
        sub = sys.argv[2]
        
        if sub == "status":
            # Fetches GSI-4 Governance Stats
            res = await call_angela_api("GET", "/api/v1/system/status")
            print(json.dumps(res, indent=2))
        
        elif sub == "think":
            msg = sys.argv[3] if len(sys.argv) > 3 else "Hello Angela"
            res = await call_angela_api("POST", "/angela/chat", {"message": msg})
            print(json.dumps(res, indent=2))
            
        elif sub == "stimulate":
            part = sys.argv[3] if len(sys.argv) > 3 else "head"
            res = await call_angela_api("POST", "/api/v1/tactile/touch", {
                "object_id": "cli_tester",
                "contact_point": {"body_part": part, "pressure": 0.8}
            })
            print(json.dumps(res, indent=2))

        elif sub == "rest":
            # Manually trigger sleep cycle (memory consolidation)
            res = await call_angela_api("POST", "/api/v1/actions/execute", {
                "name": "consolidate_memories",
                "category": "SYSTEM",
                "parameters": {"limit": 50}
            })
            print(json.dumps(res, indent=2))

    elif command == "list_windows":
        titles = os_cap.get_all_window_titles()
        print(json.dumps({"status": "success", "titles": titles}))

    elif command == "task":
        try:
            actions = json.loads(sys.argv[2])
            results = []
            with os_cap as session:
                for act in actions:
                    name = act.get("name")
                    args = act.get("args", [])
                    method = getattr(session, name, None)
                    if method:
                        res = method(*args)
                        results.append({"action": name, "result": res})
                        time.sleep(1)
            print(json.dumps({"status": "success", "results": results}))
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}))

    elif command == "summary":
        titles = os_cap.get_all_window_titles()
        clipboard = os_cap.get_clipboard()
        print(json.dumps({
            "status": "success", 
            "active_windows_count": len(titles),
            "window_preview": titles[:5],
            "clipboard_preview": clipboard[:100]
        }))
    
    else:
        print(json.dumps({"status": "error", "message": f"Unknown command: {command}"}))

if __name__ == "__main__":
    asyncio.run(main())
