"""LuantiConnector chat dispatch 回歸（R87 死路徑 #14）。

歷史 bug：_handle_message 的 chat 分支呼叫不存在的 self._dispatch ——
AttributeError 落入外層 except 設 state=ERROR，chat 事件與後續處理中斷。
修復後 chat 訊息必須送達透過 register_handler 註冊的 handler。
"""

import asyncio
import json

from apps.backend.src.integrations.luanti_connector import ConnectionState, LuantiConnector


def _async(value):
    """包成 coroutine 供 await 的最小輔助。"""

    async def _inner():
        return value

    return _inner()


def _make_connector() -> LuantiConnector:
    connector = LuantiConnector.__new__(LuantiConnector)
    from apps.backend.src.integrations.luanti_connector import LuantiConfig

    connector.config = LuantiConfig()
    connector.state = ConnectionState.READY
    connector._handlers = {}
    connector._response_futures = {}
    connector._ws = None
    connector._reader_task = None
    connector._ping_task = None
    return connector


def test_chat_message_reaches_registered_handler():
    connector = _make_connector()
    received = []
    connector.on("chat", lambda msg: _async(received.append(msg)))

    raw = json.dumps({"type": "chat", "player": "tester", "message": "hello"})
    asyncio.run(connector._handle_message(raw))

    assert len(received) == 1
    assert received[0]["message"] == "hello"
    # 修復前：AttributeError → state 被 except 設成 ERROR
    assert connector.state == ConnectionState.READY


def test_chat_without_handler_is_noop_not_crash():
    connector = _make_connector()
    raw = json.dumps({"type": "chat", "player": "tester", "message": "hi"})
    asyncio.run(connector._handle_message(raw))
    assert connector.state == ConnectionState.READY
