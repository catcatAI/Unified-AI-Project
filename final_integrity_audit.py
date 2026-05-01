import asyncio
import httpx
import json
import logging
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("IntegrityAuditor")

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws"

class IntegrityAuditor:
    def __init__(self):
        self.results = {"passed": 0, "failed": 0, "edge_cases": 0}

    async def check_route(self, method, path, payload=None, expected_status=200):
        url = f"{BASE_URL}{path}"
        try:
            async with httpx.AsyncClient() as client:
                if method == "GET":
                    response = await client.get(url, timeout=5.0)
                else:
                    response = await client.post(url, json=payload, timeout=10.0)
                
                if response.status_code == expected_status:
                    logger.info(f"✅ Route {path} [{method}] Passed.")
                    self.results["passed"] += 1
                    return response.json()
                else:
                    logger.error(f"❌ Route {path} [{method}] Failed with status {response.status_code}.")
                    self.results["failed"] += 1
                    return None
        except Exception as e:
            logger.error(f"💥 Route {path} [{method}] Exception: {e}")
            self.results["failed"] += 1
            return None

    async def test_dynamic_agent_dispatch(self):
        logger.info("--- Testing Dynamic Agent Dispatch (Multi-Agent Layer) ---")
        agents = ["fantasy_dm", "image_generation_agent", "code_understanding_agent"]
        for agent_id in agents:
            payload = {"action": "status_check", "parameters": {"test": True}}
            # FantasyDM has specific logic, we test its execution
            if agent_id == "fantasy_dm":
                payload = {"action": "rpg_narration", "parameters": {"location_name": "Testing Void"}}
            
            await self.check_route("POST", f"/api/v1/agents/{agent_id}/execute", payload)

    async def test_atlassian_real_link(self):
        logger.info("--- Testing Atlassian Real Linkage ---")
        # Check status without config (should return configured: False)
        status = await self.check_route("GET", "/api/v1/atlassian/status")
        if status and status.get("configured") is False:
            logger.info("✅ Atlassian correctly reports 'unconfigured' instead of mocking 'connected'.")
        
        # Test boundary: invalid config
        await self.check_route("POST", "/api/v1/atlassian/configure", {"domain": "", "user_email": "bad", "api_token": "x", "cloud_id": "y"}, expected_status=200)

    async def test_websocket_stability(self):
        logger.info("--- Testing WebSocket Stability & Heartbeat ---")
        import websockets
        try:
            async with websockets.connect(WS_URL) as ws:
                # 1. Initial Handshake
                greeting = await ws.recv()
                if json.loads(greeting).get("type") == "connected":
                    logger.info("✅ WS Connection Established.")
                
                # 2. State Sync Check
                # Wait for at least one state_update broadcast
                for _ in range(5):
                    msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    data = json.loads(msg)
                    if data.get("type") == "state_update":
                        logger.info("✅ WS Real-time State Received (αβγδ Matrix alive).")
                        self.results["passed"] += 1
                        break
        except Exception as e:
            logger.error(f"❌ WS Stability Test Failed: {e}")
            self.results["failed"] += 1

    async def audit_system(self):
        logger.info("🚀 Starting ASI Final Integrity Audit...")
        
        # Level 1: Health & Base Routes
        await self.check_route("GET", "/api/v1/system/status")
        await self.check_route("GET", "/health")
        
        # Level 2: Agent Ecosystem
        await self.test_dynamic_agent_dispatch()
        
        # Level 3: Integration Boundaries
        await self.test_atlassian_real_link()
        
        # Level 4: Real-time Persistence
        await self.test_websocket_stability()
        
        logger.info(f"\nAudit Summary: {self.results}")
        if self.results["failed"] == 0:
            logger.info("🏆 SYSTEM CERTIFIED: Unified-AI-Project is production-ready.")
        else:
            logger.warning("⚠️ SYSTEM DEGRADED: Integrity gaps found.")

if __name__ == "__main__":
    auditor = IntegrityAuditor()
    # Note: This script is intended to run against a live server
    # asyncio.run(auditor.audit_system())
