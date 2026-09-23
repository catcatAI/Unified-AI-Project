"""Desktop WS client contract E2E — R85 Electron 契約鎖定。

背景：Electron main process（``apps/desktop-app/electron_app/main.js``）是
獨立的 WS 客戶端實作，契約與 web-dashboard（R84）不同源。本測試鎖定
main.js 實際發送的訊息形狀與後端 websocket_manager 分發的對應：

1. 握手：``{"type": "connect", "session_id": null, "client_type": "desktop",
   "client_version": "7.5.0-dev"}``（main.js:1483）→ ``connected``
2. 心跳：``{"type": "heartbeat", "timestamp": ...}``（main.js:1519）
   → ``heartbeat_ack``
3. 聊天：shared-js ``backend-websocket.js`` sendMessage 發送
   ``{"type": "chat_message", "data": {"message_id", "content"}}``，
   後端 chat_response 必須原樣回傳 ``message_id`` 供 promise 配對 resolve
   （backend-websocket.js:1297 ``_handleChatResponse``）。

以 FastAPI TestClient 直接驅動 websocket_handler，不需要真實 backend 進程。
"""

import json

import pytest

fastapi_testclient = pytest.importorskip("fastapi.testclient")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from services.websocket_manager import websocket_handler  # noqa: E402


def _make_app() -> FastAPI:
    app = FastAPI()
    app.websocket("/ws")(websocket_handler)
    return app


def _recv_json(ws):
    return json.loads(ws.receive_text())


def _desktop_handshake(ws) -> dict:
    """按 main.js:1483 的形狀發送握手並等待 connected。"""
    ws.send_json(
        {
            "type": "connect",
            "session_id": None,
            "client_type": "desktop",
            "client_version": "7.5.0-dev",
            "timestamp": "2026-09-23T00:00:00Z",
        }
    )
    return _recv_json(ws)


def test_desktop_connect_handshake_gets_session():
    """main.js 握手（type=connect, session_id=null）→ connected 帶 client_id/session_id。"""
    client = TestClient(_make_app())
    with client.websocket_connect("/ws") as ws:
        ack = _desktop_handshake(ws)
        assert ack["type"] == "connected"
        assert ack.get("client_id")
        assert ack.get("session_id")  # server 為 null session_id 生成 uuid


def test_desktop_heartbeat_gets_ack():
    """main.js:1519 心跳 → heartbeat_ack（desktop 依此判斷連線活著）。"""
    client = TestClient(_make_app())
    with client.websocket_connect("/ws") as ws:
        _desktop_handshake(ws)
        ws.send_json({"type": "heartbeat", "timestamp": 1})
        hb = _recv_json(ws)
        assert hb["type"] == "heartbeat_ack"


def test_desktop_chat_message_id_roundtrip():
    """聊天閉環：chat_message(data.message_id) → chat_response 原樣回傳 message_id。

    shared-js 以 message_id 配對 pending promise；後端若不回傳，
    客戶端會等到 30s 假逾時（backend-websocket.js:712 timeout 邏輯）。
    """
    client = TestClient(_make_app())
    with client.websocket_connect("/ws") as ws:
        _desktop_handshake(ws)

        message_id = "1758576000000"
        ws.send_json(
            {
                "type": "chat_message",
                "data": {
                    "message_id": message_id,
                    "content": "1+1等於幾？",
                    "timestamp": "2026-09-23T00:00:01Z",
                },
            }
        )
        reply = _recv_json(ws)
        assert reply["type"] == "chat_response"
        assert reply["message_id"] == message_id  # promise 配對契約
        assert reply["sender"] == "angela"
        # 數學題走確定性引擎；LLM 不可用時也不應該是空內容
        assert reply["content"]
        assert "error" not in reply or reply["error"] == ""


def test_desktop_unknown_type_gets_echo():
    """desktop 轉發未知類型到 renderer 前不會炸——後端 echo 兜底契約。"""
    client = TestClient(_make_app())
    with client.websocket_connect("/ws") as ws:
        _desktop_handshake(ws)
        ws.send_json({"type": "totally_unknown", "data": {"x": 1}})
        echo = _recv_json(ws)
        assert echo["type"] == "echo"
        assert echo["original"]["type"] == "totally_unknown"
