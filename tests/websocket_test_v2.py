#!/usr/bin/env python3
"""
WebSocket 連接測試腳本 v2
修復了 websockets 異常處理
"""

import asyncio
import websockets
import json
from datetime import datetime

WS_URL = "ws://127.0.0.1:8000/ws"

async def test_websocket():
    """測試 WebSocket 連接"""
    print("=" * 80)
    print("WebSocket 連接測試")
    print("=" * 80)
    print(f"連接 URL: {WS_URL}")
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        async with websockets.connect(WS_URL, timeout=10) as websocket:
            print("✓ WebSocket 連接成功建立")

            # 發送測試消息
            test_message = {
                "type": "test",
                "message": "WebSocket 測試",
                "timestamp": datetime.now().isoformat()
            }

            print(f"\n發送測試消息: {json.dumps(test_message, ensure_ascii=False)}")
            await websocket.send(json.dumps(test_message))

            # 接收響應
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"✓ 收到響應: {response}")
            except asyncio.TimeoutError:
                print("✗ 等待響應超時")

            print("\n✓ WebSocket 連接測試通過")
            return True

    except websockets.exceptions.InvalidHandshake as e:
        print(f"✗ WebSocket 連接失敗 - 握手失敗: {e}")
        return False
    except websockets.exceptions.ConnectionClosed as e:
        print(f"✗ WebSocket 連接關閉: {e}")
        return False
    except ConnectionRefusedError:
        print("✗ WebSocket 連接被拒絕 - 服務可能未運行")
        return False
    except Exception as e:
        print(f"✗ WebSocket 連接錯誤: {type(e).__name__}: {e}")
        return False
    finally:
        print("\n" + "=" * 80)
        print(f"結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

if __name__ == "__main__":
    try:
        result = asyncio.run(test_websocket())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n測試被用戶中斷")
        exit(1)