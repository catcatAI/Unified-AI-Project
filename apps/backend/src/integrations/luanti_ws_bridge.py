#!/usr/bin/env python3
"""
Luanti WebSocket Bridge - CSM <-> HTTP API Bridge
CSM connects via WebSocket, exposes HTTP API for Angela agent
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Set
from aiohttp import web, WSMsgType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LuantiWSBridge:
    """WebSocket bridge between Luanti CSM and HTTP API"""

    def __init__(self, ws_port: int = 30002, http_port: int = 30003):
        self.ws_port = ws_port
        self.http_port = http_port
        self.csm_connections: Dict[str, web.WebSocketResponse] = {}
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.player_states: Dict[str, Dict[str, Any]] = {}

    async def handle_ws(self, request):
        """Handle WebSocket connection from CSM"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        csm_id = str(uuid.uuid4())[:8]
        self.csm_connections[csm_id] = ws
        logger.info(f"CSM connected: {csm_id} (total: {len(self.csm_connections)})")

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_csm_message(csm_id, data)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON from CSM {csm_id}")
                    except Exception as e:
                        logger.error(f"Error handling CSM message: {e}")
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WS error: {ws.exception()}")
        finally:
            self.csm_connections.pop(csm_id, None)
            logger.info(f"CSM disconnected: {csm_id} (remaining: {len(self.csm_connections)})")

        return ws

    async def _handle_csm_message(self, csm_id: str, data: dict):
        """Handle message from CSM"""
        msg_type = data.get("type")

        if data.get("type") == "state":
            # Update player state
            self.player_states[csm_id] = {
                "position": data.get("position"),
                "hp": data.get("hp"),
                "breath": data.get("breath"),
                "inventory": data.get("inventory"),
                "wielded": data.get("wielded"),
                "yaw": data.get("yaw"),
                "pitch": data.get("pitch"),
                "on_ground": data.get("on_ground"),
                "timestamp": datetime.now().isoformat(),
            }
            logger.debug(f"State update from {csm_id}: {data.get('position')}")

        elif data.get("type") == "response":
            # Response to our request
            req_id = data.get("response_to")
            if req_id and req_id in self.pending_requests:
                future = self.pending_requests.pop(req_id)
                if not future.done():
                    future.set_result(data)

        elif data.get("type") == "register":
            logger.info(f"CSM {csm_id} registered as {data.get('role')}")

        elif data.get("type") == "pong":
            pass  # heartbeat response

        elif data.get("type") == "chat":
            logger.info(f"Chat from CSM: {data.get('message')}")

    # ==================== HTTP API Endpoints ====================

    async def handle_state(self, request):
        """Get player state"""
        if not self.player_states:
            return web.json_response({"error": "No CSM connected"}, status=404)

        # Return first player's state (or merge if multiple)
        state = list(self.player_states.values())[0]
        return web.json_response(state)

    async def handle_action(self, request):
        """Send action to CSM"""
        try:
            data = await request.json()
            action_type = data.get("type")

            if not self.csm_connections:
                return web.json_response({"error": "No CSM connected"}, status=404)

            # Use first CSM (single agent for now)
            csm_id = list(self.csm_connections.keys())[0]
            ws = self.csm_connections[csm_id]

            action = {
                "type": "action",
                "action": action_type,
                **{k: v for k, v in data.items() if k != "type"},
            }

            # Send to CSM and wait for response
            req_id = str(uuid.uuid4())
            action["id"] = req_id

            future = asyncio.Future()
            self.pending_requests[req_id] = future

            await ws.send_json(action)

            try:
                response = await asyncio.wait_for(future, timeout=5.0)
                return web.json_response(response)
            except asyncio.TimeoutError:
                self.pending_requests.pop(req_id, None)
                return web.json_response({"error": "Action timeout"}, status=504)

        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def handle_frame(self, request):
        """Get frame data"""
        return web.json_response(
            {
                "frame_id": int(datetime.now().timestamp()),
                "width": 64,
                "height": 64,
                "note": "Frame capture not implemented yet",
            }
        )

    async def handle_health(self, request):
        return web.json_response(
            {
                "status": "ok",
                "csm_connected": len(self.csm_connections),
                "players": len(self.player_states),
            }
        )

    async def start(self):
        """Start both WebSocket and HTTP servers"""
        # WebSocket server for CSM
        ws_app = web.Application()
        ws_app.router.add_get("/ws", self.handle_ws)

        # HTTP API server
        http_app = web.Application()
        http_app.router.add_get("/api/state", self.handle_state)
        http_app.router.add_post("/api/action", self.handle_action)
        http_app.router.add_get("/api/frame", self.handle_frame)
        http_app.router.add_get("/health", self.handle_health)

        # Run both
        ws_runner = web.AppRunner(ws_app)
        await ws_runner.setup()
        ws_site = web.TCPSite(ws_runner, "0.0.0.0", 30002)
        await ws_site.start()

        http_runner = web.AppRunner(http_app)
        await http_runner.setup()
        http_site = web.TCPSite(http_runner, "0.0.0.0", 30003)
        await http_site.start()

        logger.info("WebSocket bridge started on ws://0.0.0.0:30002")
        logger.info("HTTP API started on http://0.0.0.0:30003")
        logger.info("Endpoints:")
        logger.info("  WS   ws://localhost:30002/ws  - CSM connection")
        logger.info("  GET  /api/state              - Player state")
        logger.info("  POST /api/action             - Send action (move/dig/place/look)")
        logger.info("  GET  /api/frame              - Frame data")
        logger.info("  GET  /health                 - Health check")


async def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    bridge = LuantiWSBridge()
    await bridge.start()

    print("\n=== Luanti WebSocket Bridge Running ===")
    print("CSM WebSocket: ws://localhost:30002/ws")
    print("HTTP API:      http://localhost:30003")
    print("Endpoints:")
    print("  GET  /api/state")
    print("  POST /api/action  {type: move|dig|place|look|chat, ...}")
    print("  GET  /health")
    print("\nWaiting for CSM connection...")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    asyncio.run(main())
