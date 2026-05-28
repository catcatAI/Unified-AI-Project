"""
Connection Session Management
=============================

Unified session lifecycle management for WebSocket connections.
Supports:
- Single client single session
- Multi-client with session registry
- Session persistence across reconnects
- Session-based message routing

Author: Angela AI v6.2.1
Version: 6.2.1
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """Session lifecycle states"""
    CLOSED = "closed"
    CONNECTING = "connecting"
    OPEN = "open"
    CLOSING = "closing"
    RECONNECTING = "reconnecting"


@dataclass
class ConnectionSession:
    """
    Represents a single WebSocket connection session.
    
    Attributes:
        client_id: Backend-assigned unique connection identifier (UUID)
        session_id: Client-provided session identifier (persistent across reconnects)
        websocket: The actual WebSocket connection
        state: Current session state
        created_at: Session creation timestamp
        last_heartbeat: Last heartbeat received timestamp
        sequence: Message sequence number for ordering
        metadata: Additional session metadata (client_type, version, etc.)
    """
    client_id: str
    session_id: str
    websocket: Any
    state: SessionState = SessionState.CONNECTING
    created_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    sequence: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.client_id)
    
    @property
    def is_active(self) -> bool:
        return self.state in (SessionState.OPEN, SessionState.CONNECTING)


@dataclass
class SessionStats:
    """Statistics for a session manager"""
    total_sessions: int = 0
    active_sessions: int = 0
    total_messages: int = 0
    failed_messages: int = 0


class SessionManager:
    """
    Centralized session management for all WebSocket connections.
    
    Features:
    - Session registration and lifecycle tracking
    - Session-to-client mapping for multi-client support
    - Heartbeat monitoring per session
    - Message buffering for disconnected clients
    - Session-based routing and broadcasting
    
    Usage:
        sm = SessionManager()
        
        # Register new session
        session = await sm.register(websocket, session_id, metadata)
        
        # Send to specific session
        await sm.send_to_session(session.session_id, message)
        
        # Broadcast to all
        await sm.broadcast(message)
        
        # Unregister on disconnect
        await sm.unregister(session.client_id)
    """
    
    def __init__(
        self,
        heartbeat_interval: int = 30,
        heartbeat_timeout: int = 120,
        max_buffer_size: int = 10
    ):
        # Session storage: client_id → ConnectionSession
        self._sessions: Dict[str, ConnectionSession] = {}
        
        # Session group storage: session_id → List[ConnectionSession]
        # Multiple connections can share same session_id (multi-device)
        self._sessions_by_id: Dict[str, List[ConnectionSession]] = {}
        
        # Message buffers for offline sessions
        self._message_buffers: Dict[str, List[Dict[str, Any]]] = {}
        
        # Configuration
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_timeout
        self.max_buffer_size = max_buffer_size
        
        # Stats
        self._stats = SessionStats()
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        
        # Background heartbeat monitor tasks
        self._heartbeat_tasks: Dict[str, asyncio.Task] = {}
        
        logger.info("[SessionManager] Initialized with heartbeat_interval=%ds, timeout=%ds",
                   heartbeat_interval, heartbeat_timeout)
    
    async def register(
        self,
        websocket: Any,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        single_device_mode: bool = False
    ) -> ConnectionSession:
        """
        Register a new WebSocket connection as a session.
        
        By default, multiple connections can share the same session_id (multi-device mode).
        Set single_device_mode=True to replace existing connections with the same session_id.
        
        Args:
            websocket: The WebSocket connection
            session_id: Client-provided session identifier (generated if None)
            metadata: Additional metadata (client_type, version, etc.)
            single_device_mode: If True, replace existing connections with same session_id
        
        Returns:
            ConnectionSession: The newly registered session
        """
        async with self._lock:
            # Generate session_id if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Generate unique client_id for this specific connection
            client_id = str(uuid.uuid4())
            
            # In single-device mode, replace old connections with same session_id
            if single_device_mode:
                existing_sessions = self._sessions_by_id.get(session_id, [])
                if existing_sessions:
                    logger.info(f"[SessionManager] Session {session_id} exists (single-device mode), replacing old connection")
                    for old_session in existing_sessions:
                        try:
                            await old_session.websocket.close(code=1001, reason="Replaced by new connection")
                        except Exception:
                            pass
                        await self._unregister_internal(old_session.client_id)
            
            # Create new session
            session = ConnectionSession(
                client_id=client_id,
                session_id=session_id,
                websocket=websocket,
                state=SessionState.OPEN,
                metadata=metadata or {}
            )
            session.last_heartbeat = datetime.now()
            
            # Store in registries
            self._sessions[client_id] = session
            if session_id not in self._sessions_by_id:
                self._sessions_by_id[session_id] = []
            self._sessions_by_id[session_id].append(session)
            
            # Initialize message buffer
            self._message_buffers[client_id] = []
            
            # Update stats
            self._stats.total_sessions += 1
            self._stats.active_sessions = len(self._sessions)
            
            # Start heartbeat monitor
            task = asyncio.create_task(self._heartbeat_monitor(session))
            self._heartbeat_tasks[client_id] = task
            
            logger.info(f"[SessionManager] Registered session: client_id={client_id}, session_id={session_id}")
            
            return session
    
    async def unregister(self, client_id: str, reason: str = "Normal close"):
        """Unregister a session by client_id"""
        async with self._lock:
            await self._unregister_internal(client_id, reason)
    
    async def _unregister_internal(self, client_id: str, reason: str = "Normal close"):
        """Internal unregister (called with lock held)"""
        if client_id not in self._sessions:
            return
        
        session = self._sessions[client_id]
        
        # Remove from registries
        self._sessions.pop(client_id, None)
        
        if session.session_id in self._sessions_by_id:
            self._sessions_by_id[session.session_id] = [
                s for s in self._sessions_by_id[session.session_id]
                if s.client_id != client_id
            ]
            if not self._sessions_by_id[session.session_id]:
                self._sessions_by_id.pop(session.session_id, None)
        
        # Clean up message buffer
        self._message_buffers.pop(client_id, None)
        
        # Cancel heartbeat task
        task = self._heartbeat_tasks.pop(client_id, None)
        if task and not task.done():
            task.cancel()
        
        # Update stats
        self._stats.active_sessions = len(self._sessions)
        
        logger.info(f"[SessionManager] Unregistered: client_id={client_id}, reason={reason}")
    
    async def _heartbeat_monitor(self, session: ConnectionSession):
        """Background task to monitor heartbeat for a session"""
        while session.client_id in self._sessions:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                if session.client_id not in self._sessions:
                    break
                
                time_since_heartbeat = (datetime.now() - session.last_heartbeat).total_seconds()
                
                if time_since_heartbeat > self.heartbeat_timeout:
                    logger.warning(
                        f"[SessionManager] Heartbeat timeout for {session.client_id} "
                        f"(last: {time_since_heartbeat:.1f}s ago)"
                        , exc_info=True
                    )
                    try:
                        await session.websocket.close(code=4002, reason="Heartbeat timeout")
                    except Exception:
                        pass
                    await self._unregister_internal(session.client_id, "Heartbeat timeout")
                    break
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[SessionManager] Heartbeat monitor error: {e}", exc_info=True)
                break
    
    async def send_to_session(self, session_id: str, message: dict, buffer: bool = True) -> int:
        """
        Send message to all connections with the given session_id.
        
        Args:
            session_id: The session identifier
            message: The message to send (will be JSON serialized)
            buffer: If True, buffer messages for disconnected clients
        
        Returns:
            int: Number of clients that received the message
        """
        sessions = self._sessions_by_id.get(session_id, [])
        sent_count = 0
        
        for session in sessions:
            if session.state == SessionState.OPEN:
                try:
                    await session.websocket.send_json(message)
                    sent_count += 1
                    self._stats.total_messages += 1
                    
                    # Clear buffer on successful send
                    if session.client_id in self._message_buffers:
                        self._message_buffers[session.client_id].clear()
                        
                except Exception as e:
                    logger.warning(f"[SessionManager] Send failed for {session.client_id}: {e}", exc_info=True)
                    self._stats.failed_messages += 1
                    if buffer:
                        self._buffer_message(session.client_id, message)
        
        return sent_count
    
    async def send_to_client(self, client_id: str, message: dict) -> bool:
        """
        Send message to a specific client.
        
        Args:
            client_id: The client identifier
            message: The message to send
        
        Returns:
            bool: True if message was sent successfully
        """
        session = self._sessions.get(client_id)
        if not session or session.state != SessionState.OPEN:
            return False
        
        try:
            await session.websocket.send_json(message)
            self._stats.total_messages += 1
            return True
        except Exception as e:
            logger.warning(f"[SessionManager] Send to {client_id} failed: {e}", exc_info=True)
            self._stats.failed_messages += 1
            return False
    
    async def broadcast(
        self,
        message: dict,
        exclude_session_ids: Optional[List[str]] = None
    ) -> int:
        """
        Broadcast message to all connected sessions.
        
        Args:
            message: The message to broadcast
            exclude_session_ids: List of session_ids to exclude from broadcast
        
        Returns:
            int: Number of clients that received the message
        """
        exclude_set = set(exclude_session_ids or [])
        sent_count = 0
        
        for session in list(self._sessions.values()):
            if session.session_id in exclude_set:
                continue
            
            if session.state == SessionState.OPEN:
                try:
                    await session.websocket.send_json(message)
                    sent_count += 1
                    self._stats.total_messages += 1
                except Exception as e:
                    logger.warning(f"[SessionManager] Broadcast to {session.client_id} failed: {e}", exc_info=True)
                    self._stats.failed_messages += 1
                    await self._unregister_internal(session.client_id, f"Broadcast failed: {e}")
        
        return sent_count
    
    def _buffer_message(self, client_id: str, message: dict):
        """Buffer a message for a disconnected client"""
        if client_id not in self._message_buffers:
            self._message_buffers[client_id] = []
        
        buffer = self._message_buffers[client_id]
        buffer.append(message)
        
        # Limit buffer size
        while len(buffer) > self.max_buffer_size:
            buffer.pop(0)
    
    def get_buffered_messages(self, client_id: str) -> List[Dict[str, Any]]:
        """Get buffered messages for a client (on reconnect)"""
        return self._message_buffers.get(client_id, []).copy()
    
    def clear_buffer(self, client_id: str):
        """Clear buffered messages for a client"""
        if client_id in self._message_buffers:
            self._message_buffers[client_id].clear()
    
    def get(self, client_id: str) -> Optional[ConnectionSession]:
        """Get session by client_id"""
        return self._sessions.get(client_id)
    
    def get_by_session_id(self, session_id: str) -> List[ConnectionSession]:
        """Get all sessions sharing the same session_id"""
        return self._sessions_by_id.get(session_id, [])
    
    def get_active_session_ids(self) -> List[str]:
        """Get list of active session_ids"""
        return list(self._sessions_by_id.keys())
    
    def get_stats(self) -> SessionStats:
        """Get session manager statistics"""
        self._stats.active_sessions = len(self._sessions)
        return self._stats
    
    def get_all_connections_info(self) -> List[Dict[str, Any]]:
        """Get information about all connections (for debugging/admin)"""
        return [
            {
                "client_id": session.client_id,
                "session_id": session.session_id,
                "state": session.state.value,
                "created_at": session.created_at.isoformat(),
                "last_heartbeat": session.last_heartbeat.isoformat(),
                "sequence": session.sequence,
                "metadata": session.metadata,
            }
            for session in self._sessions.values()
        ]
    
    async def update_heartbeat(self, client_id: str):
        """Update last heartbeat time for a client"""
        if client_id in self._sessions:
            self._sessions[client_id].last_heartbeat = datetime.now()
    
    def increment_sequence(self, client_id: str) -> int:
        """Increment and return sequence number for a client"""
        if client_id in self._sessions:
            self._sessions[client_id].sequence += 1
            return self._sessions[client_id].sequence
        return 0


# Singleton instance for use across the application
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create the singleton SessionManager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


async def shutdown_session_manager():
    """Gracefully shutdown the session manager"""
    global _session_manager
    if _session_manager:
        # Cancel all heartbeat tasks
        for task in _session_manager._heartbeat_tasks.values():
            if not task.done():
                task.cancel()
        await asyncio.gather(*_session_manager._heartbeat_tasks.values(), return_exceptions=True)
        _session_manager = None
        logger.info("[SessionManager] Shutdown complete")