#!/usr/bin/env python3
"""
Luanti Polling Bridge - HTTP API for polling-based Luanti agent
Server polls this bridge for commands via POST /api/poll
Agent queries state via GET /api/state
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import deque
from aiohttp import web

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class PollingBridge:
    """Polling-based HTTP bridge for Luanti agent"""

    def __init__(self, http_port: int = 30003):
        self.http_port = http_port
        self.command_queue: deque = deque()
        self.player_state: Dict[str, Any] = {}
        self.pending_actions: List[Dict[str, Any]] = []
        # Player chat overheard by the poller (register_on_chat_message).
        # Single consumer (the agent) drains via take_chat_events().
        self.chat_events: List[Dict[str, Any]] = []
        self._chat_seq = 0
        # Outbound speech lane: chat must not be overwritten by the 10Hz
        # action latest-wins slot, or replies die before the next poll.
        # handle_poll delivers chats first, then the latest action.
        self.outbox_chat: List[Dict[str, Any]] = []

    async def handle_poll(self, request):
        """Server polls for commands - returns actions to execute"""
        try:
            data = await request.json()
            logger.debug(f"Poll received: {data.get('position')}")

            # Update player state (goto_/scan ride along opaquely for
            # the coordinate-grounded behavior library)
            self.player_state = {
                "position": data.get("position"),
                "hp": data.get("hp"),
                "max_hp": data.get("max_hp"),
                "breath": data.get("breath"),
                "inventory": data.get("inventory"),
                "wielded": data.get("wielded"),
                "yaw": data.get("yaw"),
                "pitch": data.get("pitch"),
                "on_ground": data.get("on_ground"),
                "goto_": data.get("goto_"),
                "scan": data.get("scan"),
                "vision": data.get("vision"),
                "in_water": data.get("in_water", False),
                "in_lava": data.get("in_lava", False),
                "timestamp": datetime.now().isoformat(),
            }

            # Return pending actions: speech first, then the latest action
            actions = self.outbox_chat + self.pending_actions
            self.outbox_chat = []
            self.pending_actions = []

            return web.json_response({"actions": actions})

        except Exception as e:
            logger.error(f"Poll error: {e}")
            return web.json_response({"actions": [], "error": str(e)}, status=500)

    async def handle_state(self, request):
        """Get current player state"""
        if not self.player_state:
            return web.json_response({"error": "No state available"}, status=404)
        return web.json_response(self.player_state)

    async def handle_action(self, request):
        """Queue action from agent"""
        try:
            data = await request.json()
            action_type = data.get("type")

            action = {
                "type": action_type,
                "id": str(uuid.uuid4()),
                **{k: v for k, v in data.items() if k != "type"},
            }

            self.pending_actions.append(action)
            logger.info(f"Queued action: {action_type}")

            return web.json_response({"ok": True, "action_id": action["id"]})

        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def handle_health(self, request):
        return web.json_response(
            {
                "status": "ok",
                "has_state": bool(self.player_state),
                "pending_actions": len(self.pending_actions),
                "pending_chats": len(self.chat_events),
            }
        )

    async def handle_chat_post(self, request):
        """Poller forwards an overheard player chat message."""
        try:
            data = await request.json()
            self._chat_seq += 1
            event = {
                "id": self._chat_seq,
                "player": str(data.get("player", "unknown")),
                "message": str(data.get("message", ""))[:500],
                "timestamp": datetime.now().isoformat(),
            }
            self.chat_events.append(event)
            # Bounded: the agent drains every tick, but never let a dead
            # agent grow this without limit.
            del self.chat_events[:-50]
            return web.json_response({"ok": True, "chat_id": event["id"]})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def handle_chat_get(self, request):
        """Agent drains overheard chat (single consumer)."""
        events = self.chat_events
        self.chat_events = []
        return web.json_response({"events": events})

    def take_chat_events(self) -> List[Dict[str, Any]]:
        """Sync drain for the in-process agent (no HTTP needed)."""
        events = self.chat_events
        self.chat_events = []
        return events

    def queue_action(self, action: Dict[str, Any]) -> str:
        """Queue an action from the autonomous agent (sync, no HTTP needed).

        Latest-wins with a 1-slot cap: the agent produces at 10Hz while the
        poller drains at ~0.5Hz, so an unbounded queue fills with stale
        actions from dead subgoals and starves the current one. Freshness
        beats history here — every action type (move/dig/place/craft) is
        either continuous (newest direction wins) or single-shot idempotent.
        """
        action_id = str(uuid.uuid4())
        normalized = {"id": action_id, **action}
        if normalized.get("type") == "chat":
            self.outbox_chat.append(normalized)
            del self.outbox_chat[:-5]
            logger.info(f"Queued speech: {normalized.get('message', '')[:80]}")
            return action_id
        if self.pending_actions:
            self.pending_actions[-1] = normalized
        else:
            self.pending_actions.append(normalized)
        logger.info(f"Queued action: {normalized.get('type')}")
        return action_id

    async def start(self):
        app = web.Application()
        app.router.add_post("/api/poll", self.handle_poll)
        app.router.add_get("/api/state", self.handle_state)
        app.router.add_post("/api/action", self.handle_action)
        app.router.add_post("/api/chat", self.handle_chat_post)
        app.router.add_get("/api/chat", self.handle_chat_get)
        app.router.add_get("/health", self.handle_health)

        self._runner = web.AppRunner(app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, "0.0.0.0", self.http_port)
        await self._site.start()

        logger.info(f"Polling bridge started on http://0.0.0.0:{self.http_port}")
        logger.info("Endpoints:")
        logger.info("  POST /api/poll  - Server polls for commands")
        logger.info("  GET  /api/state             - Agent queries state")
        logger.info("  POST /api/action            - Agent queues action")
        logger.info("  GET  /health                - Health check")

    async def stop(self):
        """Stop the polling bridge"""
        try:
            if hasattr(self, "_site") and self._site:
                await self._site.stop()
        except RuntimeError as e:
            if "not registered" not in str(e):
                raise
        try:
            if hasattr(self, "_runner") and self._runner:
                await self._runner.cleanup()
        except Exception:
            pass
        logger.info("Polling bridge stopped")


async def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    bridge = PollingBridge(http_port=30003)
    await bridge.start()

    print("\n=== Luanti Polling Bridge Running ===")
    print("Server polls:     POST http://localhost:30003/api/poll")
    print("Agent queries:  GET  http://localhost:30003/api/state")
    print("Agent actions:  POST http://localhost:30003/api/action")
    print("Health:         GET  http://localhost:30003/health")
    print("\nWaiting for server to poll...")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    asyncio.run(main())
