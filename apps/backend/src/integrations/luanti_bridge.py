#!/usr/bin/env python3
"""
Luanti Bridge - HTTP API bridge for Luanti/Minetest UDP server
Connects to Luanti UDP server and exposes HTTP API for Angela AI agent
"""

import asyncio
import json
import logging
import socket
import struct
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from aiohttp import web

logger = logging.getLogger(__name__)

# Minetest Protocol Constants
PROTOCOL_VERSION = 53
TOCLIENT_HELLO = 0
TOSERVER_INIT = 1
TOCLIENT_INIT = 2
TOCLIENT_DISCONNECT = 3
TOCLIENT_MOVE = 4
TOSERVER_MOVE = 5
TOCLIENT_BLOCKS = 6
TOSERVER_BLOCK = 7
TOCLIENT_INVENTORY = 8
TOSERVER_INVENTORY = 9
TOCLIENT_HELLO = 0
TOCLIENT_SPAWN = 10
TOCLIENT_DESPAWN = 11
TOCLIENT_ENTITY = 11
TOSERVER_INTERACT = 12
TOCLIENT_HUD = 13
TOCLIENT_ENTITY_ACTION = 14
TOSERVER_CHAT = 15
TOCLIENT_CHAT = 16


@dataclass
class PlayerState:
    position: tuple = (0.0, 0.0, 0.0)
    yaw: float = 0.0
    pitch: float = 0.0
    hp: int = 20
    max_hp: int = 20
    breath: int = 10
    inventory: Dict[str, int] = field(default_factory=dict)
    wielded_item: str = ""
    is_on_ground: bool = True
    velocity: tuple = (0.0, 0.0, 0.0)


@dataclass
class ConnectionState:
    peer_id: int = 0
    connected: bool = False
    player_name: str = ""
    last_packet_time: float = 0


class MinetestProtocol:
    """Minimal Minetest protocol implementation for bridge"""

    def __init__(self, host: str = "127.0.0.1", port: int = 30000, player_name: str = "AngelaAI"):
        self.host = host
        self.port = port
        self.player_name = player_name
        self.sock: Optional[socket.socket] = None
        self.state = ConnectionState()
        self.player = PlayerState()
        self._running = False
        self._callbacks: Dict[str, List[callable]] = {}

    def connect(self) -> bool:
        """Connect to Minetest server"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(5.0)

            # Send TOCLIENT_HELLO with protocol version
            hello = struct.pack("!B I", TOCLIENT_HELLO, PROTOCOL_VERSION)
            self.sock.sendto(hello, (self.host, self.port))

            # Wait for TOCLIENT_INIT response
            data, addr = self.sock.recvfrom(4096)
            if data and len(data) > 1:
                msg_type = data[0]
                if msg_type == TOCLIENT_INIT:
                    self._parse_init(data)
                    self.state.connected = True
                    logger.info(f"Connected to Minetest server at {self.host}:{self.port}")
                    return True

        except Exception as e:
            logger.error(f"Connection failed: {e}")
        return False

    def _parse_init(self, data: bytes):
        """Parse TOCLIENT_INIT packet"""
        # Simplified parsing - extract peer_id and player info
        offset = 1
        if len(data) >= 5:
            self.state.peer_id = struct.unpack("!I", data[offset : offset + 4])[0]
            offset += 4
            # Skip player name and other fields for now
            logger.info(f"Peer ID: {self.state.peer_id}")

    def send_move(self, position: tuple, yaw: float, pitch: float, velocity: tuple = (0, 0, 0)):
        """Send TOSERVER_MOVE packet"""
        if not self.sock or not self.state.connected:
            return
        try:
            # TOSERVER_MOVE packet
            # position (3 floats), yaw (float), pitch (float), velocity (3 floats), flags (byte)
            packet = struct.pack(
                "!B f f f f f f f f f B",
                TOSERVER_MOVE,
                position[0],
                position[1],
                position[2],
                yaw,
                pitch,
                velocity[0],
                velocity[1],
                velocity[2],
                0,  # flags
            )
            self.sock.sendto(packet, (self.host, self.port))
        except Exception as e:
            logger.error(f"Send move failed: {e}")

    def send_interact(self, action: str, target: Optional[tuple] = None):
        """Send TOSERVER_INTERACT packet"""
        if not self.sock or not self.state.connected:
            return
        try:
            # Simplified interaction packet
            packet = struct.pack("!B B", TOSERVER_INTERACT, 0)
            self.sock.sendto(packet, (self.host, self.port))
        except Exception as e:
            logger.error(f"Send interact failed: {e}")

    def receive_loop(self):
        """Main receive loop"""
        self._running = True
        while self._running and self.sock:
            try:
                self.sock.settimeout(1.0)
                data, addr = self.sock.recvfrom(4096)
                if data:
                    self._handle_packet(data)
                    self.state.last_packet_time = time.time()
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Receive error: {e}")
                break

    def _handle_packet(self, data: bytes):
        """Handle incoming packet"""
        if not data:
            return
        msg_type = data[0]

        if msg_type == TOCLIENT_SPAWN:
            self._handle_spawn(data)
        elif msg_type == TOCLIENT_MOVE:
            self._handle_move(data)
        elif msg_type == TOCLIENT_CHAT:
            self._handle_chat(data)
        elif msg_type == TOCLIENT_INVENTORY:
            self._handle_inventory(data)
        # Add more handlers as needed

    def _handle_spawn(self, data: bytes):
        """Handle spawn packet"""
        # Simplified - update player state
        pass

    def _handle_move(self, data: bytes):
        """Handle move update"""
        pass

    def _handle_chat(self, data: bytes):
        """Handle chat message"""
        pass

    def _handle_inventory(self, data: bytes):
        """Handle inventory update"""
        pass

    def disconnect(self):
        """Disconnect from server"""
        self._running = False
        if self.sock:
            try:
                disconnect_packet = struct.pack("!B", TOCLIENT_DISCONNECT)
                self.sock.sendto(disconnect_packet, (self.host, self.port))
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        self.state.connected = False


class LuantiBridge:
    """HTTP API Bridge for Luanti/Minetest"""

    def __init__(self, host: str = "127.0.0.1", game_port: int = 30000, http_port: int = 30002):
        self.protocol = MinetestProtocol(host=host, port=game_port)
        self.http_port = http_port
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        self.app.router.add_get("/api/state", self.handle_state)
        self.app.router.add_post("/api/action", self.handle_action)
        self.app.router.add_get("/api/frame", self.handle_frame)
        self.app.router.add_get("/health", self.handle_health)

    async def start(self):
        """Start the bridge"""
        # Connect to Minetest server
        if not self.protocol.connect():
            raise RuntimeError("Failed to connect to Minetest server")

        # Start receive loop in background
        self.protocol._running = True
        asyncio.create_task(self._receive_loop())

        # Start HTTP server
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.http_port)
        await site.start()
        logger.info(f"Luanti Bridge HTTP API started on port {self.http_port}")

    async def _receive_loop(self):
        """Async receive loop"""
        while self.protocol._running and self.protocol.sock:
            try:
                self.protocol.sock.settimeout(0.1)
                data, addr = self.protocol.sock.recvfrom(4096)
                if data:
                    self.protocol._handle_packet(data)
            except socket.timeout:
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Receive error: {e}")
                await asyncio.sleep(0.1)

    async def handle_state(self, request):
        """Get player state"""
        p = self.protocol.player
        return web.json_response(
            {
                "position": {"x": p.position[0], "y": p.position[1], "z": p.position[2]},
                "yaw": p.yaw,
                "pitch": p.pitch,
                "hp": p.hp,
                "max_hp": p.max_hp,
                "breath": p.breath,
                "inventory": p.inventory,
                "wielded": p.wielded_item,
                "on_ground": p.is_on_ground,
            }
        )

    async def handle_action(self, request):
        """Handle action request"""
        try:
            data = await request.json()
            action_type = data.get("type")

            if action_type == "move":
                self.protocol.send_move(
                    (data.get("forward", 0), 0, data.get("strafe", 0)),
                    data.get("yaw", 0),
                    data.get("pitch", 0),
                )
                return web.json_response({"ok": True})

            elif action_type == "look":
                # Look is handled in move packet
                return web.json_response({"ok": True})

            elif action_type == "dig":
                self.protocol.send_interact("dig")
                return web.json_response({"ok": True})

            elif action_type == "place":
                self.protocol.send_interact("place")
                return web.json_response({"ok": True})

            elif action_type == "chat":
                # Send chat message
                return web.json_response({"ok": True})

            return web.json_response({"error": "Unknown action"}, status=400)

        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def handle_frame(self, request):
        """Get frame data (placeholder)"""
        return web.json_response({"frame_id": int(time.time()), "width": 64, "height": 64})

    async def handle_health(self, request):
        return web.json_response({"status": "ok", "connected": self.protocol.state.connected})

    async def stop(self):
        """Stop the bridge"""
        self.protocol.disconnect()


async def main():
    logging.basicConfig(level=logging.INFO)

    bridge = LuantiBridge(host="127.0.0.1", game_port=30000, http_port=30002)

    try:
        await bridge.start()
        print("Luanti Bridge running on http://0.0.0.0:30002")
        print("Endpoints:")
        print("  GET  /api/state  - Get player state")
        print("  POST /api/action - Send action (move/dig/place/look/chat)")
        print("  GET  /api/frame  - Get frame data")
        print("  GET  /health     - Health check")

        # Keep running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await bridge.stop()


if __name__ == "__main__":
    asyncio.run(main())
