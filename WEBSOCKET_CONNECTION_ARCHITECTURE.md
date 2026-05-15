# WebSocket Connection Architecture - Unified Design
> v6.2.1 | 2026-05-15 | 连接生命周期管理规范化

---

## 1. 问题分析 (Problem Analysis)

### 1.1 当前问题

| 问题 | 位置 | 描述 |
|------|------|------|
| **ID 碎片化** | Backend (`main_api_server.py:827`) | 每次新建连接都生成新 UUID，不保留会话 |
| **双重重连** | Main + Renderer | Main process 和 BackendWebSocketClient 各自有重连逻辑 |
| **职责混乱** | `connectWebSocket()` | Main process 有自己的心跳，而 BackendWebSocketClient 也有心跳 |
| **无会话概念** | 整个系统 | 没有 session_id/client_id 贯穿整个连接生命周期 |
| **广播风暴** | `broadcast_state_updates()` | 每 30 秒向所有连接广播状态，包含已经断开的连接 |

### 1.2 当前数据流

```
Renderer                    Main Process              Backend
    │                            │                        │
    ├── new BackendWebSocket ─────┼── connectWebSocket() ───┼── new UUID (每次!)
    │                            │                        │
    ├── send() ──────────────────┼── websocket.send() ───┤
    │                            │                        │
    │── onclose ─────────────────┼── reconnect ──────────┼── new UUID (第二次!)
    │                            │                        │
    ├── _handleReconnect ────────┼── connectWebSocket() ─┤── new UUID (第三次!)
    │                            │                        │
    (重复循环...)                  │                        │
```

---

## 2. 架构设计 (Architecture Design)

### 2.1 核心原则

1. **单一会话源 (Single Session Source)**: 一个窗口生命周期内，只有一个 session_id
2. **单向重连控制 (Single Reconnect Authority)**: 只有 renderer 进程控制重连
3. **ID 贯穿 (ID Propagation)**: client_id 从后端生成，通过 IPC 传回 renderer，全程携带
4. **幂等连接 (Idempotent Connect)**: 相同 URL + 相同 session 不重复建立连接
5. **优雅降级 (Graceful Degradation)**: 网络问题不产生级联失效

### 2.2 连接模式矩阵

| 模式 | 前端数量 | 后端数量 | 会话策略 | 使用场景 |
|------|---------|---------|---------|---------|
| **S1: 单机单连** | 1 | 1 | 单一 session | 开发/测试 |
| **S2: 局域网多端** | N | 1 | 共享 backend，注册表 | 桌面 + 移动 |
| **S3: 互联网多端** | N | 1 | 唯一 session + 心跳保活 | 跨网络 |
| **S4: 局域网格** | N | M | 分布式注册，消息路由 | 企业内网 |
| **S5: 互联网 P2P** | N | 0 | 去中心化，NAT 穿透 | 纯端对端 |

### 2.3 架构分层

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Desktop    │  │    Mobile    │  │   Browser    │           │
│  │  (Electron)  │  │    (React)    │  │  (WebSocket) │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                 │                    │
│         └─────────────────┼─────────────────┘                    │
│                           │                                      │
│  ┌────────────────────────┴────────────────────────┐            │
│  │          ConnectionManager (Renderer)            │            │
│  │  - Session lifecycle                             │            │
│  │  - Reconnect with same session_id               │            │
│  │  - Heartbeat (client-side)                      │            │
│  └────────────────────────┬────────────────────────┘            │
└──────────────────────────┼──────────────────────────────────────┘
                           │ IPC (Main Process bridges)
┌──────────────────────────┼──────────────────────────────────────┐
│                        SERVER LAYER                              │
│  ┌────────────────────────┴────────────────────────┐            │
│  │              Backend ConnectionManager             │            │
│  │  - Session registry (session_id → websocket)     │            │
│  │  - Heartbeat monitoring (server-side)            │            │
│  │  - Multi-client routing                           │            │
│  └────────────────────────┬────────────────────────┘            │
│                           │                                      │
│         ┌─────────────────┼─────────────────┐                    │
│         │                 │                 │                    │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐           │
│  │   Backend 1   │  │   Backend 2   │  │   Backend N   │       │
│  │  (Primary)    │  │  (Replica)    │  │  (Replica)    │       │
│  └───────────────┘  └───────────────┘  └───────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 连接生命周期 (Connection Lifecycle)

### 3.1 Session 状态机

```
┌─────────┐
│ CLOSED  │ ◄─────────────────────────────────────────────┐
└────┬────┘                                              │
     │ connect(session_id)                                │
     ▼                                                    │
┌─────────┐     ┌─────────────┐     ┌────────┐     ┌──────┴──┐
│ CONNECTING │──►│ HAND_SHAKING │──►│ OPEN │──►│ CLOSING │
└─────────┘     └─────────────┘     └────────┘     └─────────┘
                        │               │
                        │               ▼
                        │        ┌────────────┐
                        │        │  RE_CONNECT │ (same session)
                        │        └────────────┘
                        │
                        └───────────────────► (failure) → CLOSED
```

### 3.2 Session 传输协议

#### 客户端 → 服务端

```json
{
  "type": "connect",
  "session_id": "uuid-v4-or-generated",
  "client_type": "desktop|mobile|browser",
  "client_version": "6.2.1",
  "capabilities": ["heartbeat", "state_sync", "tactile"],
  "timestamp": "ISO-8601"
}
```

#### 服务端 → 客户端

```json
{
  "type": "connected",
  "session_id": "confirmed-session-id",
  "server_session_id": "server-assigned-uuid",
  "timestamp": "ISO-8601",
  "heartbeat_interval": 30,
  "server_version": "6.0.4"
}
```

### 3.3 重连协议

```json
{
  "type": "reconnect",
  "session_id": "original-session-id",
  "last_sequence": 123,
  "timestamp": "ISO-8601"
}
```

服务端响应:

```json
{
  "type": "reconnected",
  "session_id": "original-session-id",
  "resumed_from_sequence": 124,
  "missed_messages": [...]
}
```

---

## 4. 实现规范 (Implementation Spec)

### 4.1 后端改动 (Python/FastAPI)

#### 4.1.1 核心 Session 管理

```python
# services/connection_session.py

class ConnectionSession:
    """单一连接会话"""
    def __init__(self, websocket: WebSocket, client_id: str, session_id: str):
        self.websocket = websocket
        self.client_id = client_id      # 唯一连接标识 (UUID)
        self.session_id = session_id     # 会话标识 (可跨连接持久化)
        self.created_at = datetime.now()
        self.last_heartbeat = datetime.now()
        self.sequence = 0
        self.metadata = {}

class SessionManager:
    """会话管理器 - 单例"""
    
    def __init__(self):
        self._sessions: Dict[str, ConnectionSession] = {}  # client_id → Session
        self._sessions_by_session_id: Dict[str, List[ConnectionSession]] = {}  # session_id → [Sessions]
        self._lock = asyncio.Lock()
    
    async def register(self, websocket: WebSocket, session_id: str, metadata: dict) -> ConnectionSession:
        """注册新连接或恢复已有会话"""
        async with self._lock:
            # 检查是否有相同 session_id 的活跃连接
            existing = self._find_by_session_id(session_id)
            if existing:
                # 旧连接替换
                await self.unregister(existing.client_id)
            
            client_id = str(uuid.uuid4())
            session = ConnectionSession(websocket, client_id, session_id)
            session.metadata = metadata
            
            self._sessions[client_id] = session
            if session_id not in self._sessions_by_session_id:
                self._sessions_by_session_id[session_id] = []
            self._sessions_by_session_id[session_id].append(session)
            
            return session
    
    async def unregister(self, client_id: str):
        """注销连接"""
        async with self._lock:
            if client_id in self._sessions:
                session = self._sessions[client_id]
                self._sessions.pop(client_id)
                if session.session_id in self._sessions_by_session_id:
                    self._sessions_by_session_id[session.session_id] = [
                        s for s in self._sessions_by_session_id[session.session_id]
                        if s.client_id != client_id
                    ]
    
    def get(self, client_id: str) -> Optional[ConnectionSession]:
        return self._sessions.get(client_id)
    
    def get_by_session_id(self, session_id: str) -> List[ConnectionSession]:
        return self._sessions_by_session_id.get(session_id, [])
    
    def _find_by_session_id(self, session_id: str) -> Optional[ConnectionSession]:
        sessions = self._sessions_by_session_id.get(session_id, [])
        return sessions[0] if sessions else None
    
    async def send_to_session(self, session_id: str, message: dict):
        """向所有相同 session_id 的连接发送消息"""
        for session in self.get_by_session_id(session_id):
            try:
                await session.websocket.send_json(message)
            except Exception:
                pass
    
    async def broadcast(self, message: dict, exclude_session_ids: List[str] = None):
        """广播消息"""
        for session in list(self._sessions.values()):
            if exclude_session_ids and session.session_id in exclude_session_ids:
                continue
            try:
                await session.websocket.send_json(message)
            except Exception:
                await self.unregister(session.client_id)
```

#### 4.1.2 WebSocket 端点改造

```python
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str = None):
    # 1. 接受连接
    await websocket.accept()
    
    # 2. 等待连接握手消息
    try:
        handshake = await asyncio.wait_for(websocket.receive_json(), timeout=10)
    except asyncio.TimeoutError:
        await websocket.close(code=4001, reason="Handshake timeout")
        return
    
    # 3. 验证并注册会话
    client_session_id = session_id or handshake.get("session_id") or str(uuid.uuid4())
    client_type = handshake.get("client_type", "unknown")
    client_version = handshake.get("client_version", "unknown")
    
    session = await session_manager.register(
        websocket, 
        client_session_id,
        {"client_type": client_type, "client_version": client_version}
    )
    
    # 4. 发送确认
    await websocket.send_json({
        "type": "connected",
        "client_id": session.client_id,        # 后端分配的唯一ID
        "session_id": session.session_id,      # 客户端提供的会话ID
        "timestamp": datetime.now().isoformat(),
        "server_version": "6.0.4",
        "heartbeat_interval": 30
    })
    
    # 5. 消息循环
    while True:
        try:
            data = await asyncio.wait_for(
                websocket.receive_json(), 
                timeout=session_manager.heartbeat_timeout
            )
            session.last_heartbeat = datetime.now()
            session.sequence += 1
            
            # 处理消息...
            await handle_message(session, data)
            
        except asyncio.TimeoutError:
            await websocket.close(code=4002, reason="Heartbeat timeout")
            break
        except WebSocketDisconnect:
            break
        except Exception as e:
            logger.error(f"Message error: {e}")
            continue
    
    # 6. 清理会话
    await session_manager.unregister(session.client_id)
```

### 4.2 前端改动 (JavaScript/Electron)

#### 4.2.1 Session 管理器

```javascript
// js/session-manager.js

class ConnectionSession {
    constructor(url) {
        this.url = url
        this.clientId = null           // 后端分配的 client_id
        this.sessionId = this._loadOrCreateSessionId()
        this.state = 'CLOSED'
        this.ws = null
        this._connectTimer = null
        this._heartbeatTimer = null
        this._intentionalClose = false
    }
    
    _loadOrCreateSessionId() {
        // 从 localStorage 恢复 session_id
        let sid = localStorage.getItem('angela_session_id')
        if (!sid) {
            sid = this._generateSessionId()
            localStorage.setItem('angela_session_id', sid)
        }
        return sid
    }
    
    _generateSessionId() {
        return 'sess_' + Date.now().toString(36) + '_' + Math.random().toString(36).substr(2, 9)
    }
    
    connect() {
        if (this.state === 'CONNECTING' || this.state === 'OPEN') {
            console.log('[Session] Already connecting/open')
            return
        }
        
        this._intentionalClose = false
        this.state = 'CONNECTING'
        
        const wsUrl = `${this.url}?session_id=${encodeURIComponent(this.sessionId)}`
        console.log('[Session] Connecting with:', this.sessionId)
        
        this.ws = new WebSocket(wsUrl)
        
        this.ws.onopen = () => {
            console.log('[Session] WebSocket open, waiting for handshake...')
        }
        
        this.ws.onmessage = (event) => {
            const msg = JSON.parse(event.data)
            this._handleMessage(msg)
        }
        
        this.ws.onerror = (error) => {
            console.error('[Session] WebSocket error:', error)
            this._scheduleReconnect()
        }
        
        this.ws.onclose = (code, reason) => {
            console.log('[Session] WebSocket closed:', code, reason)
            this._cleanup()
            
            if (!this._intentionalClose) {
                this._scheduleReconnect()
            }
        }
    }
    
    _handleMessage(msg) {
        switch (msg.type) {
            case 'connected':
                this.clientId = msg.client_id
                this.state = 'OPEN'
                console.log('[Session] Connected! client_id:', this.clientId, 'session_id:', msg.session_id)
                
                // 保存 server-assigned session_id (如果有)
                if (msg.session_id && msg.session_id !== this.sessionId) {
                    console.log('[Session] Server assigned new session_id:', msg.session_id)
                    this.sessionId = msg.session_id
                    localStorage.setItem('angela_session_id', this.sessionId)
                }
                
                this._startHeartbeat()
                this._fireEvent('connected', msg)
                break
                
            case 'heartbeat_ack':
                console.log('[Session] Heartbeat ack received')
                break
                
            case 'reconnected':
                console.log('[Session] Reconnected, resuming from seq:', msg.resumed_from_sequence)
                if (msg.missed_messages) {
                    msg.missed_messages.forEach(m => this._fireEvent('message', m))
                }
                break
                
            default:
                this._fireEvent('message', msg)
        }
    }
    
    send(message) {
        if (this.state !== 'OPEN') {
            console.warn('[Session] Not connected, queuing message')
            return false
        }
        
        try {
            this.ws.send(JSON.stringify(message))
            return true
        } catch (e) {
            console.error('[Session] Send failed:', e)
            return false
        }
    }
    
    disconnect() {
        this._intentionalClose = true
        this._cleanup()
        if (this.ws) {
            this.ws.close(1000, 'Client disconnect')
        }
        this.state = 'CLOSED'
    }
    
    _scheduleReconnect() {
        if (this._intentionalClose) return
        
        this.state = 'RECONNECTING'
        const delay = Math.min(1000 * Math.pow(2, this._reconnectAttempts || 0), 30000)
        this._reconnectAttempts = (this._reconnectAttempts || 0) + 1
        
        console.log(`[Session] Reconnecting in ${delay}ms (attempt ${this._reconnectAttempts})`)
        
        this._connectTimer = setTimeout(() => {
            this.connect()
        }, delay)
    }
    
    _startHeartbeat() {
        this._stopHeartbeat()
        this._heartbeatTimer = setInterval(() => {
            if (this.state === 'OPEN' && this.ws) {
                this.send({ type: 'heartbeat', timestamp: Date.now(), client_id: this.clientId })
            }
        }, 30000)
    }
    
    _stopHeartbeat() {
        if (this._heartbeatTimer) {
            clearInterval(this._heartbeatTimer)
            this._heartbeatTimer = null
        }
    }
    
    _cleanup() {
        this._stopHeartbeat()
        if (this._connectTimer) {
            clearTimeout(this._connectTimer)
            this._connectTimer = null
        }
    }
    
    _fireEvent(type, data) {
        // Event emission
    }
}
```

#### 4.2.2 Main Process 简化

```javascript
// main.js - WebSocket 部分 (简化后)

let wsSession = null

// IPC handler: renderer 请求连接
ipcMain.on('websocket-connect', (event, { url, sessionId }) => {
    console.log('[Main] IPC: websocket-connect received')
    
    // 创建一个新的 ConnectionSession
    wsSession = new ConnectionSession(url)
    
    // 监听 session 事件
    wsSession.on('connected', (data) => {
        sendToMainWindow('websocket-connected', data)
    })
    
    wsSession.on('message', (message) => {
        sendToMainWindow('websocket-message', message)
    })
    
    wsSession.on('disconnected', (data) => {
        sendToMainWindow('websocket-disconnected', data)
    })
    
    // 开始连接
    wsSession.connect()
})

ipcMain.on('websocket-send', (event, message) => {
    if (wsSession) {
        const success = wsSession.send(message)
        event.reply('websocket-send-result', { success })
    } else {
        event.reply('websocket-send-result', { success: false, error: 'No session' })
    }
})

ipcMain.on('websocket-disconnect', () => {
    if (wsSession) {
        wsSession.disconnect()
        wsSession = null
    }
})
```

---

## 5. 多端架构 (Multi-Endpoint Architecture)

### 5.1 局域网分布式 (LAN Distributed)

```
┌─────────────────────────────────────────────────────────────┐
│                     LAN Network                              │
│                                                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                      │
│  │Desktop 1│  │Mobile 1 │  │Mobile 2 │   ← Clients          │
│  │  :8000  │  │  :8000  │  │  :8000  │                      │
│  └────┬────┘  └────┬────┘  └────┬────┘                      │
│       │            │            │                            │
│       └────────────┼────────────┘                            │
│                    │                                         │
│            ┌───────┴───────┐                                 │
│            │  Primary :8000│  ← Single backend               │
│            │  (or Cluster) │                                 │
│            └───────────────┘                                 │
└─────────────────────────────────────────────────────────────┘
```

**特点**: 低延迟，所有客户端连接同一后端实例

### 5.2 互联网多客户端 (Internet Multi-Client)

```
┌─────────────────────┐                    ┌─────────────────────┐
│   Desktop Client    │◄──────────────►    │   Cloud Backend     │
│   192.168.1.x       │    NAT/Firewall    │   (VPS/Docker)      │
│                     │                    │   1.2.3.4:8000      │
└─────────────────────┘                    └─────────────────────┘
                                                    │
                                                    │ Broadcast
                                                    ▼
                                            ┌─────────────────────┐
                                            │   Mobile Client     │
                                            │   (Carrier NAT)     │
                                            └─────────────────────┘
```

**特点**: 需要心跳保活，处理 NAT 超时

### 5.3 互联网 P2P (Future)

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  Desktop A  │◄──────►│  Desktop B  │◄──────►│  Mobile C   │
│ (Public IP) │  WebRTC │  (Symmetric │  WebRTC │  (Carrier)  │
│             │         │   NAT)      │         │             │
└─────────────┘         └─────────────┘         └─────────────┘
      │                       │                       │
      └───────────────────────┴───────────────────────┘
                          │
                    ┌─────┴─────┐
                    │ Signaling │
                    │  Server   │
                    │  (Only)   │
                    └───────────┘
```

**注意**: 当前架构不支持 P2P，未来版本可能引入 WebRTC

---

## 6. 迁移计划 (Migration Plan)

### Phase 1: 修复当前问题 (Immediate)

| 步骤 | 文件 | 改动 | 风险 |
|------|------|------|------|
| 1.1 | `backend/main_api_server.py` | 添加 `session_id` 参数到 WebSocket 端点 | 低 |
| 1.2 | `backend/main_api_server.py` | 改造 `ConnectionManager` 支持 session 注册 | 中 |
| 1.3 | `frontend/backend-websocket.js` | 添加 session_id 传输 | 低 |
| 1.4 | `frontend/main.js` | 移除 auto-reconnect (已完成) | 低 |
| 1.5 | `frontend/backend-websocket.js` | 重连时携带 session_id | 中 |

### Phase 2: 规范化 Session 管理

| 步骤 | 文件 | 改动 | 风险 |
|------|------|------|------|
| 2.1 | `backend/` | 创建 `services/connection_session.py` | 中 |
| 2.2 | `frontend/js/` | 创建 `js/session-manager.js` | 中 |
| 2.3 | `frontend/main.js` | 集成 SessionManager | 中 |
| 2.4 | `frontend/backend-websocket.js` | 使用 SessionManager | 高 |

### Phase 3: 多端支持

| 步骤 | 文件 | 改动 | 风险 |
|------|------|------|------|
| 3.1 | `backend/` | 添加多客户端注册表 | 中 |
| 3.2 | `backend/` | 实现 session 路由 | 中 |
| 3.3 | `mobile/` | 创建 React Native WebSocket client | 中 |
| 3.4 | `mobile/` | 集成 SessionManager | 高 |

### Phase 4: 互联网架构 (Future)

| 步骤 | 文件 | 改动 | 风险 |
|------|------|------|------|
| 4.1 | `backend/` | 添加 TURN/STUN 支持 | 高 |
| 4.2 | `backend/` | 实现 P2P 信令服务器 | 高 |
| 4.3 | `frontend/` | 添加 WebRTC 支持 | 高 |

---

## 7. 测试计划 (Test Plan)

### 7.1 单元测试

```python
# tests/test_connection_session.py

def test_session_creation():
    sm = SessionManager()
    session = sm.register(ws, "test-session-1")
    assert session.session_id == "test-session-1"
    assert sm.get(session.client_id) == session

def test_session_reconnect():
    sm = SessionManager()
    s1 = sm.register(ws1, "session-1")
    sm.unregister(s1.client_id)
    s2 = sm.register(ws2, "session-1")  # 恢复同一 session
    assert s2.session_id == "session-1"

def test_broadcast_excludes():
    sm = SessionManager()
    s1 = sm.register(ws1, "exclude-me")
    sm.register(ws2, "include-me")
    sm.broadcast({"type": "test"}, exclude_session_ids=["exclude-me"])
    # ws1 should not receive, ws2 should receive
```

### 7.2 集成测试

```python
# tests/test_websocket_lifecycle.py

async def test_single_client_lifecycle():
    """单客户端: 连接 → 使用 → 断开"""
    async with websockets.connect(URL) as ws:
        # 握手
        await ws.send({"type": "connect", "session_id": "test-1"})
        resp = await ws.recv()
        assert resp["type"] == "connected"
        client_id = resp["client_id"]
        
        # 使用
        await ws.send({"type": "heartbeat"})
        resp = await ws.recv()
        assert resp["type"] == "heartbeat_ack"
        
        # 断开 (模拟)
        await ws.close()

async def test_reconnect_with_same_session():
    """重连: 断开 → 同 session_id 重连"""
    # 连接
    async with websockets.connect(URL) as ws1:
        await ws1.send({"type": "connect", "session_id": "test-reconnect"})
        resp = await ws1.recv()
        original_client_id = resp["client_id"]
    
    # 同 session 重连
    async with websockets.connect(URL) as ws2:
        await ws2.send({"type": "connect", "session_id": "test-reconnect"})
        resp = await ws2.recv()
        new_client_id = resp["client_id"]
        assert new_client_id != original_client_id
        assert resp["type"] == "connected"

async def test_multi_client_broadcast():
    """多客户端: 所有客户端都收到广播"""
    clients = []
    for i in range(3):
        ws = await websockets.connect(URL)
        await ws.send({"type": "connect", "session_id": f"multi-{i}"})
        await ws.recv()
        clients.append(ws)
    
    # 广播
    # 等待所有客户端收到消息
```

---

## 8. 验收标准 (Acceptance Criteria)

### 8.1 基础要求

- [ ] 单客户端: 连接后 client_id 保持不变，直到明确断开
- [ ] 重连: 使用相同 session_id 重连，server 识别为同一会话
- [ ] 无重复连接: 同一 session 不会产生多个活跃连接
- [ ] 心跳: 30 秒间隔，超时 120 秒断开

### 8.2 多端要求

- [ ] 局域网: 两个客户端同时连接，各自保持独立 session
- [ ] 广播: 消息正确发送到所有连接的客户端
- [ ] 隔离: 一个客户端断开不影响其他客户端

### 8.3 性能要求

- [ ] 连接建立时间 < 500ms
- [ ] 重连间隔: 1s, 2s, 4s, 8s... 最大 30s
- [ ] 支持 100+ 并发连接

---

## 9. 附录: 当前代码映射

### 后端

| 当前代码 | 位置 | 问题 | 目标 |
|---------|------|------|------|
| `ConnectionManager` | `main_api_server.py:799` | 无 session 概念 | `SessionManager` |
| `uuid.uuid4()` | `main_api_server.py:827` | 每次新建 ID | 复用 session_id |
| `broadcast_state_updates()` | `main_api_server.py:972` | 遍历所有连接 | 按 session 路由 |

### 前端

| 当前代码 | 位置 | 问题 | 目标 |
|---------|------|------|------|
| `connectWebSocket()` | `main.js:1379` | 无 session 概念 | 使用 SessionManager |
| `BackendWebSocketClient` | `backend-websocket.js:21` | 双重心跳/重连 | 合并到 SessionManager |
| IPC `websocket-connect` | `main.js:1511` | 触发新建连接 | 触发 session 连接 |

---

## 10. 实现优先级

```
P0 (阻塞问题):
  [x] 1. 后端: 实现 SessionManager
  [x] 2. 后端: WebSocket 端点接受 session_id
  [x] 3. 前端: BackendWebSocketClient 携带 session_id 连接
  [x] 4. 前端: Main process 使用 session-based 连接

P1 (核心功能):
  [x] 5. 前端: 移除主进程 auto-reconnect (已完成)
  [x] 6. 前端: 重连时携带 session_id
  [x] 7. 后端: 多客户端注册表
  [x] 8. 后端: 按 session 广播

P2 (优化):
  [ ] 9. 前端: 创建 session-manager.js (可选重构)
  [ ] 10. 前端: 简化 main.js WebSocket 处理
  [ ] 11. 测试: 重连恢复测试
```

---

## 11. 实现进度 (Implementation Progress)

### Phase 1: P0 完成 ✅

| 任务 | 状态 | 文件 |
|------|------|------|
| SessionManager 类 | ✅ 完成 | `services/connection_session.py` |
| ConnectionManager 改造 | ✅ 完成 | `services/main_api_server.py:793-950` |
| WebSocket 端点 session 支持 | ✅ 完成 | `services/main_api_server.py:967-1095` |
| BackendWebSocketClient session_id | ✅ 完成 | `js/backend-websocket.js:21-155` |
| Main process session 支持 | ✅ 完成 | `main.js:1371-1448` |
| Preload IPC 更新 | ✅ 完成 | `preload.js:107-113` |

### Phase 2: P1 完成 ✅

| 任务 | 状态 | 文件 |
|------|------|------|
| 移除主进程 auto-reconnect | ✅ 完成 | `main.js:1443-1469` |
| 重连携带 session_id | ✅ 完成 | `js/backend-websocket.js:609-611` |
| 多客户端注册表 | ✅ 完成 | `services/connection_session.py` |
| 按 session 广播 | ✅ 完成 | `services/connection_session.py` |

### Phase 3: 待完成

| 任务 | 状态 | 文件 |
|------|------|------|
| 创建 js/session-manager.js | ⏳ 待定 | 可选重构 |
| 简化 main.js WebSocket | ⏳ 待定 | 可选重构 |
| 重连恢复测试 | ⏳ 待定 | `tests/test_websocket_lifecycle.py` |

### 核心改动总结

#### 后端改动

1. **新增 `services/connection_session.py`**:
   - `ConnectionSession` dataclass: 存储 client_id, session_id, websocket, state, metadata
   - `SessionManager` class: 会话注册表, 心跳监控, 消息缓冲, 广播
   - `get_session_manager()`: 单例获取

2. **改造 `services/main_api_server.py`**:
   - `ConnectionManager` now delegates to `SessionManager`
   - WebSocket 端点接受 `connect` 握手消息
   - 握手消息包含: `session_id`, `client_type`, `client_version`
   - 返回 `connected` 消息包含: `client_id`, `session_id`, `server_version`

#### 前端改动

1. **Desktop/Electron (`js/backend-websocket.js`)**:
   - 添加 `sessionId` (从 localStorage 恢复或新建)
   - 添加 `clientId` (从后端接收)
   - 添加 `_loadOrCreateSessionId()`, `_buildUrl()`, `_buildHandshake()`
   - 连接时发送握手消息
   - 重连时复用同一 `sessionId`

2. **Desktop/Electron (`main.js`)**:
   - 添加 `wsSessionInfo` 存储 session 信息
   - `connectWebSocket()` 发送握手消息
   - 收到 `connected` 消息后才标记连接成功
   - 移除 auto-reconnect

3. **Preload (`preload.js`)**:
   - IPC `websocket-connect` 增加 `sessionInfo` 参数

### 消息流程

```
客户端                              后端
   │                                  │
   ├── WebSocket 连接 ───────────────►│
   │                                  │
   │◄── 等待握手 ◄────────────────────│
   │                                  │
   ├── {type:'connect', session_id} ► │
   │                                  │
   │◄── {type:'connected', client_id} ◄│
   │     session_id, server_version    │
   │                                  │
   ├── {type:'heartbeat'} ──────────►│
   │                                  │
   │◄── {type:'heartbeat_ack'} ◄─────│
   │                                  │
   (正常通信...)                       │
   │                                  │
   ├── {type:'state_update'} ────────►│
   │                                  │
   ├── 断开连接                       │
   │                                  │
   (重连时复用同一 session_id)           │
```

---

**最后更新**: 2026-05-16
**状态**: P0+P1 完成, P2 待定
**下一步**: 运行集成测试验证