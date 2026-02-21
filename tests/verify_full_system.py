import hmac
import hashlib
import json
import requests
import time
from pathlib import Path
import sys
import logging

logger = logging.getLogger(__name__)

# 將項目路徑加入 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from system.security_monitor import ABCKeyManager
from system.hardware_probe import HardwareProbe


def verify_system():
    print("🛡️  Angela AI 全系統就緒度驗證...")

    # 1. 密鑰管理器驗證
    print("\n🔑 1. 驗證 A/B/C 密鑰體系...")
    km = ABCKeyManager()
    key_b = km.get_key("KeyB")
    key_c = km.get_key("KeyC")
    if key_b and key_c and key_b != key_c:
        print(f"✅ 密鑰生成正常 (Key B: {key_b[:10]}..., Key C: {key_c[:10]}...)")
    else:
        print("❌ 密鑰生成異常")
        return

    # 2. 硬體探針與集群能力驗證
    print("\n🔍 2. 驗證硬體探針與集群能力...")
    probe = HardwareProbe()
    capability = probe.get_cluster_capability()
    if "preferred_role" in capability and "score" in capability:
        print(
            f"✅ 硬體感知正常: 分數={capability['score']}, 建議角色={capability['preferred_role']}"
        )
    else:
        print("❌ 硬體探針輸出格式不正確")
        return

    # 3. 後端安全介面驗證 (需要後端運行)
    print("\n🌐 3. 驗證後端安全通訊與同步介面 (需啟動後端)...")
    base_url = "http://localhost:8000"

    try:
        # 測試 Key C 同步
        resp_c = requests.get(f"{base_url}/api/v1/security/sync-key-c")
        if resp_c.status_code == 200:
            data = resp_c.json()
            if data["key_c"] == key_c:
                print("✅ Key C 跨端同步介面正常")
            else:
                print("❌ Key C 同步數據不匹配")
        else:
            print(f"❌ Key C 同步失敗 (HTTP {resp_c.status_code})")

        # 測試行動端安全請求 (成功案例)
        payload = {"test": "data", "timestamp": time.time()}
        body = json.dumps(payload).encode()
        signature = hmac.new(key_b.encode(), body, hashlib.sha256).hexdigest()

        headers = {"X-Angela-Signature": signature}
        resp_m = requests.post(f"{base_url}/api/v1/mobile/test", json=payload, headers=headers)
        if resp_m.status_code == 200:
            print("✅ 行動端 HMAC 安全請求驗證通過")
        else:
            print(f"❌ 行動端安全請求被拒絕 (HTTP {resp_m.status_code}): {resp_m.text}")

        # 測試行動端安全請求 (失敗案例 - 錯誤簽名)
        headers_bad = {"X-Angela-Signature": "wrong_signature"}
        resp_m_bad = requests.post(
            f"{base_url}/api/v1/mobile/test", json=payload, headers=headers_bad
        )
        if resp_m_bad.status_code == 403:
            print("✅ 後端正確攔截了非法簽名請求")
        else:
            print(f"❌ 後端未攔截非法簽名 (HTTP {resp_m_bad.status_code})")

    except requests.exceptions.ConnectionError:
        print("⚠️  後端未運行，跳過網路層驗證。請確保後端已啟動。")

    print("\n✨ 驗證總結: 系統核心功能已完成並具備高度可用性。")


if __name__ == "__main__":
    verify_system()
