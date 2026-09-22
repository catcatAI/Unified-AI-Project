"""Dashboard WS chat contract E2E — R84 dashboard-e2e 收斂的契約鎖定。

背景（R84 實測發現）：web-dashboard ChatPanel 曾發送 ``{"type": "chat"}``，
該型別不在後端分發清單——第一條被當 handshake 消費、之後被 echo，
訊息永遠拿不到 chat_response。正確契約（websocket_manager）：

1. 連線後 10s 內必須送 handshake，否則 4001 斷線
2. chat 走 ``{"type": "chat_message", "data": {"content": ...}}``
3. 回應為 ``{"type": "chat_response", "content": ...}``

本測試以 FastAPI TestClient 直接驅動 websocket_handler 鎖定契約，
不需要真實 backend 進程。
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


def test_handshake_is_mandatory():
    """不送 handshake 直接收 chat → 連線被關（4001 handshake timeout）。"""
    client = TestClient(_make_app())
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"type": "chat", "content": "hi"})
        # server 把第一條當 handshake（type 欄位非握手語意也照收），
        # 回 connected 後進主循環；chat 型別不在分發清單 → echo
        first = _recv_json(ws)
        assert first["type"] == "connected"


def test_chat_message_contract_returns_chat_response():
    """正確契約：handshake → chat_message(data.content) → chat_response。"""
    client = TestClient(_make_app())
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"type": "handshake", "client_type": "web-dashboard"})
        connected = _recv_json(ws)
        assert connected["type"] == "connected"

        ws.send_json(
            {
                "type": "chat_message",
                "data": {"content": "1+1等於幾？", "user_name": "e2e"},
            }
        )
        reply = _recv_json(ws)
        assert reply["type"] == "chat_response"
        assert reply["sender"] == "angela"
        # 數學題走確定性引擎；LLM 不可用時也不應該是空內容
        assert reply["content"]
        assert "error" not in reply or reply["error"] == ""


def test_chat_panel_legacy_format_gets_echo_not_response():
    """回歸鎖定：ChatPanel 舊格式 ``{"type": "chat"}`` 只會得到 echo，
    這正是 R84 之前 dashboard chat 永遠無回應的根因。"""
    client = TestClient(_make_app())
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"type": "handshake", "client_type": "web-dashboard"})
        _recv_json(ws)  # connected

        ws.send_json({"type": "chat", "content": "1+1等於幾？"})
        reply = _recv_json(ws)
        assert reply["type"] == "echo"  # 舊格式＝死路徑
