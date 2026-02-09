"""
Real ExternalConnector for HSP - HTTP-based inter-process communication.

Enables agents running as subprocesses to communicate with each other
and with the central HSP message router.
"""

import asyncio
import json
import logging
import os
import uuid
import httpx
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class MessageRouter:
    """
    Central message router for HSP communication.
    Agents register with this router and messages are forwarded accordingly.
    """
    
    _instance = None
    _router_port = 11435  # Default router port
    
    def __init__(self, host: str = "127.0.0.1", port: int = None):
        self.host = host
        self.port = port or MessageRouter._router_port
        self.registry: Dict[str, Dict[str, Any]] = {}  # agent_id -> info
        self.message_history: List[Dict[str, Any]] = []
        self._server = None
        self._running = False
        
    @classmethod
    def get_instance(cls, port: int = None) -> "MessageRouter":
        """Get or create the singleton MessageRouter."""
        if cls._instance is None:
            cls._instance = cls(port=port)
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset the singleton (for testing)."""
        cls._instance = None
    
    async def start(self):
        """Start the HTTP server for the message router."""
        if self._running:
            return
        
        from httpx import ASGITransport, AsyncClient
        from fastapi import FastAPI, HTTPException
        import uvicorn
        
        app = FastAPI()
        
        @app.post("/register")
        async def register_agent(data: Dict[str, Any]):
            agent_id = data.get("agent_id")
            port = data.get("port")
            capabilities = data.get("capabilities", [])
            if agent_id:
                self.registry[agent_id] = {
                    "port": port,
                    "capabilities": capabilities,
                    "registered_at": datetime.now(timezone.utc).isoformat(),
                    "host": "127.0.0.1"
                }
                logger.info(f"Agent registered: {agent_id} at port {port}")
                return {"status": "registered", "agent_id": agent_id}
            raise HTTPException(status_code=400, detail="Missing agent_id")
        
        @app.post("/unregister")
        async def unregister_agent(data: Dict[str, Any]):
            agent_id = data.get("agent_id")
            if agent_id and agent_id in self.registry:
                del self.registry[agent_id]
                logger.info(f"Agent unregistered: {agent_id}")
                return {"status": "unregistered"}
            raise HTTPException(status_code=404, detail="Agent not found")
        
        @app.get("/registry")
        async def get_registry():
            return {"agents": self.registry}
        
        @app.post("/send")
        async def send_message(data: Dict[str, Any]):
            target_id = data.get("target_id")
            message = data.get("message", {})
            
            if target_id in self.registry:
                target = self.registry[target_id]
                target_port = target["port"]
                
                # Forward message to target agent
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"http://127.0.0.1:{target_port}/message",
                            json=message,
                            timeout=5.0
                        )
                    return {"status": "delivered", "target": target_id}
                except Exception as e:
                    logger.error(f"Failed to deliver message to {target_id}: {e}")
                    return {"status": "failed", "error": str(e)}
            else:
                return {"status": "failed", "error": "Target not found"}
        
        @app.post("/broadcast")
        async def broadcast_message(data: Dict[str, Any]):
            message = data.get("message", {})
            results = []
            for agent_id, info in self.registry.items():
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"http://127.0.0.1:{info['port']}/message",
                            json=message,
                            timeout=5.0
                        )
                        results.append({"agent": agent_id, "status": "delivered"})
                except Exception as e:
                    results.append({"agent": agent_id, "status": "failed", "error": str(e)})
            return {"status": "broadcast", "results": results}
        
        self._server = uvicorn.Server(uvicorn.Config(app, host=self.host, port=self.port, log_level="error"))
        await self._server.serve()
    
    async def stop(self):
        """Stop the HTTP server."""
        if self._server:
            self._running = False
            self._server.should_exit = True


class ExternalConnector:
    """
    Real ExternalConnector for HSP communication between agents.
    
    Each agent instance has its own HTTP server to receive messages
    and uses HTTP client to send messages to other agents.
    """
    
    def __init__(self, ai_id: str = None, config: Dict[str, Any] = None, **kwargs):
        self.ai_id = ai_id or f"agent_{uuid.uuid4().hex[:8]}"
        self.config = config or {}
        self.router_host = self.config.get("router_host", "127.0.0.1")
        self.router_port = self.config.get("router_port", 11435)
        self.agent_port = self.config.get("agent_port", 0)  # 0 = auto-assign
        
        # Message handling
        self._message_callbacks: List[Callable] = []
        self._request_callbacks: Dict[str, Callable] = {}
        self._server = None
        self._app = None
        self._running = False
        
        # Statistics
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0
        }
        
        logger.info(f"ExternalConnector initialized for: {self.ai_id}")
    
    async def initialize(self) -> bool:
        """Initialize the HTTP server and register with router."""
        try:
            from httpx import ASGITransport, AsyncClient
            import uvicorn
            
            # Create agent HTTP server
            from fastapi import FastAPI, HTTPException
            app = FastAPI()
            
            @app.post("/message")
            async def receive_message(data: Dict[str, Any]):
                self.stats["messages_received"] += 1
                logger.debug(f"[{self.ai_id}] Received message: {data.get('message_id', 'unknown')}")
                
                # Call registered callbacks
                for callback in self._message_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(data)
                        else:
                            callback(data)
                    except Exception as e:
                        logger.error(f"[{self.ai_id}] Message callback error: {e}")
                
                return {"status": "received"}
            
            @app.get("/health")
            async def health_check():
                return {"status": "healthy", "agent_id": self.ai_id}
            
            @app.get("/stats")
            async def get_stats():
                return self.stats
            
            self._app = app
            
            # Find available port
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', 0))
                self.agent_port = s.getsockname()[1]
            
            # Start server
            self._server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=self.agent_port, log_level="error"))
            
            # Register with router
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"http://{self.router_host}:{self.router_port}/register",
                    json={
                        "agent_id": self.ai_id,
                        "port": self.agent_port,
                        "capabilities": self.config.get("capabilities", [])
                    },
                    timeout=5.0
                )
            
            logger.info(f"[{self.ai_id}] Registered with router at port {self.agent_port}")
            return True
            
        except Exception as e:
            logger.error(f"[{self.ai_id}] Initialization failed: {e}")
            self.stats["errors"] += 1
            return False
    
    async def connect(self) -> bool:
        """Alias for initialize()."""
        return await self.initialize()
    
    async def send(self, message: Dict[str, Any]) -> bool:
        """
        Send a message to another agent via the router.
        
        Args:
            message: Message dictionary with 'target_id' and payload
        """
        target_id = message.get("target_id") or message.get("recipient_id")
        if not target_id:
            logger.error(f"[{self.ai_id}] No target specified in message")
            self.stats["errors"] += 1
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://{self.router_host}:{self.router_port}/send",
                    json={
                        "target_id": target_id,
                        "message": {
                            **message,
                            "sender_id": self.ai_id,
                            "message_id": message.get("message_id", uuid.uuid4().hex),
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    },
                    timeout=10.0
                )
                result = response.json()
                
                if result.get("status") == "delivered":
                    self.stats["messages_sent"] += 1
                    logger.debug(f"[{self.ai_id}] Message sent to {target_id}")
                    return True
                else:
                    logger.warning(f"[{self.ai_id}] Message delivery failed: {result.get('error')}")
                    self.stats["errors"] += 1
                    return False
                    
        except Exception as e:
            logger.error(f"[{self.ai_id}] Send failed: {e}")
            self.stats["errors"] += 1
            return False
    
    async def broadcast(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Broadcast a message to all registered agents.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://{self.router_host}:{self.router_port}/broadcast",
                    json={
                        "message": {
                            **message,
                            "sender_id": self.ai_id,
                            "message_id": message.get("message_id", uuid.uuid4().hex),
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    },
                    timeout=30.0
                )
                return response.json()
        except Exception as e:
            logger.error(f"[{self.ai_id}] Broadcast failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def on_message(self, callback: Callable):
        """Register a callback for incoming messages."""
        self._message_callbacks.append(callback)
        return callback
    
    async def get_registry(self) -> Dict[str, Any]:
        """Get the current registry of agents."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://{self.router_host}:{self.router_port}/registry",
                    timeout=5.0
                )
                return response.json()
        except Exception as e:
            logger.error(f"[{self.ai_id}] Failed to get registry: {e}")
            return {"agents": {}}
    
    async def disconnect(self):
        """Unregister from router and shutdown."""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"http://{self.router_host}:{self.router_port}/unregister",
                    json={"agent_id": self.ai_id},
                    timeout=5.0
                )
            logger.info(f"[{self.ai_id}] Unregistered from router")
        except Exception as e:
            logger.error(f"[{self.ai_id}] Disconnect error: {e}")
    
    async def get_stats(self) -> Dict[str, int]:
        """Get connection statistics."""
        return self.stats


async def start_router(host: str = "127.0.0.1", port: int = 11435) -> MessageRouter:
    """Start the central message router."""
    router = MessageRouter.get_instance(port=port)
    await router.start()
    return router


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1 and sys.argv[1] == "router":
        # Start as router
        router = asyncio.run(start_router())
    else:
        # Demo: create connector
        connector = ExternalConnector(ai_id="test_agent")
        asyncio.run(connector.connect())
        print(f"Agent started with ID: {connector.ai_id}")