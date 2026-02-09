#!/usr/bin/env python3
"""
Angela AI Desktop App Comprehensive Test Suite
Tests frontend components, backend communication, and UI functionality
"""

import sys
import json
import asyncio
import time
from datetime import datetime

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_header(text):
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}{text:^60}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{RESET}")

class DesktopAppTester:
    def __init__(self):
        self.results = {
            "backend": {"passed": 0, "failed": 0, "tests": []},
            "websocket": {"passed": 0, "failed": 0, "tests": []},
            "api": {"passed": 0, "failed": 0, "tests": []},
            "ui": {"passed": 0, "failed": 0, "tests": []},
            "live2d": {"passed": 0, "failed": 0, "tests": []},
        }

    def add_result(self, category, passed, message):
        status = "PASS" if passed else "FAIL"
        self.results[category]["tests"].append({
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        if passed:
            self.results[category]["passed"] += 1
            print_success(message)
        else:
            self.results[category]["failed"] += 1
            print_error(message)

    async def test_backend_health(self):
        print_header("Backend Health Tests")
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                # Test health endpoint
                async with session.get('http://127.0.0.1:8000/health') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status") == "healthy":
                            self.add_result("backend", True, "Backend health check passed")
                        else:
                            self.add_result("backend", False, f"Backend status: {data.get('status')}")
                    else:
                        self.add_result("backend", False, f"Health check returned status {resp.status}")

                # Test root endpoint
                async with session.get('http://127.0.0.1:8000/') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        version = data.get("version", "unknown")
                        self.add_result("backend", True, f"Backend API version: {version}")
                    else:
                        self.add_result("backend", False, f"Root endpoint returned status {resp.status}")

        except ImportError:
            self.add_result("backend", False, "aiohttp not installed, using curl instead")
            import subprocess
            result = subprocess.run(['curl', '-s', 'http://127.0.0.1:8000/health'],
                                  capture_output=True, text=True)
            if result.returncode == 0 and '"status":"healthy"' in result.stdout:
                self.add_result("backend", True, "Backend health check passed (curl)")
            else:
                self.add_result("backend", False, f"Backend health check failed: {result.stderr}")
        except Exception as e:
            self.add_result("backend", False, f"Backend test error: {str(e)[:80]}")

    async def test_pet_api(self):
        print_header("Pet API Tests")
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                # Test pet status
                async with session.get('http://127.0.0.1:8000/api/v1/pet/status') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        pet_id = data.get("pet_id", "unknown")
                        state = data.get("state", {})
                        self.add_result("api", True, f"Pet API working: {pet_id} - animation: {state.get('current_animation')}")
                    else:
                        self.add_result("api", False, f"Pet status returned status {resp.status}")

                # Test pet interact (correct endpoint: /interaction)
                async with session.post('http://127.0.0.1:8000/api/v1/pet/interaction',
                                       json={"type": "pet", "intensity": 0.5}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response_msg = data.get("response", "")[:50]
                        self.add_result("api", True, f"Pet interaction works: {response_msg}")
                    else:
                        self.add_result("api", False, f"Pet interact returned status {resp.status}")

                # Test economy endpoint
                async with session.get('http://127.0.0.1:8000/api/v1/economy/status') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        coins = data.get("coins", 0)
                        self.add_result("api", True, f"Economy API working: {coins} coins")
                    else:
                        self.add_result("api", False, f"Economy status returned status {resp.status}")

        except Exception as e:
            self.add_result("api", False, f"API test error: {str(e)[:80]}")

    async def test_websocket(self):
        print_header("WebSocket Tests")
        try:
            import aiohttp
            from aiohttp import WSMessage

            async with aiohttp.ClientSession() as session:
                async with session.ws_connect('http://127.0.0.1:8000/ws') as ws:
                    # Test connection
                    self.add_result("websocket", True, "WebSocket connection established")

                    # Send ping
                    await ws.send_json({"type": "ping", "timestamp": int(time.time())})

                    # Wait for response
                    try:
                        msg = await asyncio.wait_for(ws.receive(), timeout=5.0)
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            msg_type = data.get("type", "unknown")
                            self.add_result("websocket", True, f"WebSocket message received: {msg_type}")
                        else:
                            self.add_result("websocket", False, f"Unexpected message type: {msg.type}")
                    except asyncio.TimeoutError:
                        self.add_result("websocket", False, "WebSocket timeout waiting for response")

        except ImportError:
            self.add_result("websocket", False, "aiohttp not installed for WebSocket tests")
        except Exception as e:
            self.add_result("websocket", False, f"WebSocket test error: {str(e)[:80]}")

    def test_frontend_code(self):
        print_header("Frontend Code Tests")
        import os

        base_path = "/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app"

        # Test critical files exist
        critical_files = [
            "index.html",
            "main.js",
            "preload.js",
            "js/app.js",
            "js/live2d-manager.js",
            "js/input-handler.js",
            "js/backend-websocket.js",
            "js/dialogue-ui.js",
        ]

        for file in critical_files:
            file_path = os.path.join(base_path, file)
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                self.add_result("ui", True, f"{file} exists ({size} bytes)")
            else:
                self.add_result("ui", False, f"{file} not found")

        # Test index.html has required elements
        index_html = os.path.join(base_path, "index.html")
        if os.path.exists(index_html):
            with open(index_html, 'r', encoding='utf-8') as f:
                content = f.read()

            required_elements = [
                'id="live2d-canvas"',
                'id="click-layer"',
                'id="dialogue-container"',
                'id="loading-overlay"',
                'backend-websocket.js',
                'dialogue-ui.js',
                'input-handler.js',
            ]

            for element in required_elements:
                if element in content:
                    self.add_result("ui", True, f"Index.html contains: {element[:30]}")
                else:
                    self.add_result("ui", False, f"Index.html missing: {element[:30]}")

        # Test dialogue-ui.js functionality
        dialogue_js = os.path.join(base_path, "js/dialogue-ui.js")
        if os.path.exists(dialogue_js):
            with open(dialogue_js, 'r', encoding='utf-8') as f:
                content = f.read()

            required_features = [
                'class DialogueUI',
                'sendMessage',
                'addMessage',
                'addSystemMessage',
                'dialogue-input',
                'dialogue-messages',
            ]

            for feature in required_features:
                if feature in content:
                    self.add_result("ui", True, f"DialogueUI has: {feature}")
                else:
                    self.add_result("ui", False, f"DialogueUI missing: {feature}")

    def test_live2d_code(self):
        print_header("Live2D Code Tests")
        import os

        live2d_js = "/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app/js/live2d-manager.js"

        if not os.path.exists(live2d_js):
            self.add_result("live2d", False, "Live2D manager not found")
            return

        with open(live2d_js, 'r', encoding='utf-8') as f:
            content = f.read()

        required_features = [
            ('class Live2DManager', 'Live2D Manager class'),
            ('loadModel', 'Model loading'),
            ('setExpression', 'Expression control'),
            ('triggerMotionByPart', 'Body part touch response'),
            ('startAnimation', 'Animation loop'),
            ('clickableRegions', 'Click regions'),
            ('eyeTracking', 'Eye tracking'),
        ]

        for feature, desc in required_features:
            if feature in content:
                self.add_result("live2d", True, f"Live2D: {desc}")
            else:
                self.add_result("live2d", False, f"Live2D missing: {desc}")

    def test_main_js(self):
        print_header("Main Process (main.js) Tests")
        import os

        main_js = "/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app/main.js"

        if not os.path.exists(main_js):
            self.add_result("ui", False, "main.js not found")
            return

        with open(main_js, 'r', encoding='utf-8') as f:
            content = f.read()

        required_features = [
            ('requestSingleInstanceLock', 'Single instance lock'),
            ('WebSocket', 'WebSocket server/client'),
            ('connectWebSocket', 'WebSocket connection'),
            ('createMainWindow', 'Window creation'),
            ('createTray', 'System tray'),
            ('ipcMain', 'IPC handlers'),
            ('live2d-load-model', 'Live2D model loading'),
        ]

        for feature, desc in required_features:
            if feature in content:
                self.add_result("ui", True, f"main.js: {desc}")
            else:
                self.add_result("ui", False, f"main.js missing: {desc}")

    async def run_all_tests(self):
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}{'Angela AI Desktop App Test Suite':^60}{RESET}")
        print(f"{BOLD}{datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^60}{RESET}")
        print(f"{BOLD}{'='*60}{RESET}")

        # Run async tests
        await self.test_backend_health()
        await self.test_websocket()
        await self.test_pet_api()

        # Run sync tests
        self.test_frontend_code()
        self.test_live2d_code()
        self.test_main_js()

        # Print summary
        print_header("Test Summary")
        total_passed = 0
        total_failed = 0

        for category, results in self.results.items():
            passed = results["passed"]
            failed = results["failed"]
            total = passed + failed
            total_passed += passed
            total_failed += failed

            status = f"{GREEN}PASS{RESET}" if failed == 0 else f"{YELLOW}PARTIAL{RESET}" if failed < passed else f"{RED}FAIL{RESET}"
            print(f"{category.upper():15} {status:10} {passed:3}/{total:3} passed")

        print(f"\n{BOLD}{'Total':15} {GREEN if total_failed == 0 else YELLOW if total_failed < total_passed else RED}{total_passed}/{total_passed + total_failed}{RESET} tests passed")

        return self.results

async def main():
    tester = DesktopAppTester()
    results = await tester.run_all_tests()

    # Save results
    with open("/home/cat/桌面/Unified-AI-Project/test_results.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{BOLD}Results saved to: /home/cat/桌面/Unified-AI-Project/test_results.json{RESET}")

if __name__ == "__main__":
    asyncio.run(main())
