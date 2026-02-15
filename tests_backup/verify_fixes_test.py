#!/usr/bin/env python3
"""
驗證修復效果的測試腳本
"""
import requests
import json
from typing import Dict, Tuple

BASE_URL = "http://127.0.0.1:8000"

def test_economy_transaction_with_correct_params() -> Tuple[bool, dict]:
    """測試經濟系統交易端點（使用正確的參數）"""
    print("\n測試 1: 經濟系統交易端點（使用正確參數）")
    print("-" * 80)

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/economy/transaction",
            json={
                "user_id": "test_user",
                "amount": 10.0,
                "description": "測試交易"
            },
            timeout=5
        )

        print(f"狀態碼: {response.status_code}")
        print(f"響應: {json.dumps(response.json(), ensure_ascii=False)}")

        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.json()
    except Exception as e:
        print(f"錯誤: {e}")
        return False, {"error": str(e)}

def test_mobile_status_get() -> Tuple[bool, dict]:
    """測試移動端狀態端點（GET 方法）"""
    print("\n測試 2: 移動端狀態端點（GET 方法）")
    print("-" * 80)

    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/mobile/status",
            timeout=5
        )

        print(f"狀態碼: {response.status_code}")
        print(f"響應: {json.dumps(response.json(), ensure_ascii=False)}")

        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.json()
    except Exception as e:
        print(f"錯誤: {e}")
        return False, {"error": str(e)}

def test_ops_dashboard() -> Tuple[bool, dict]:
    """測試運維儀表板（檢查 timezone 修復）"""
    print("\n測試 3: 運維儀表板（檢查 timezone 修復）")
    print("-" * 80)

    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/ops/dashboard",
            timeout=10
        )

        print(f"狀態碼: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"響應: {json.dumps(data, ensure_ascii=False)}")

            # 檢查是否有 last_update 字段
            if "last_update" in data:
                print(f"✅ last_update 字段存在: {data['last_update']}")
                return True, data
            else:
                print("⚠️ last_update 字段不存在，但請求成功")
                return True, data
        else:
            print(f"錯誤響應: {response.text}")
            return False, response.json()
    except Exception as e:
        print(f"錯誤: {e}")
        return False, {"error": str(e)}

def main():
    print("=" * 80)
    print("驗證修復效果測試")
    print("=" * 80)

    results = []

    # 測試 1: 經濟系統交易端點
    success1, data1 = test_economy_transaction_with_correct_params()
    results.append({
        "test": "economy_transaction_correct_params",
        "success": success1,
        "data": data1
    })

    # 測試 2: 移動端狀態端點（GET 方法）
    success2, data2 = test_mobile_status_get()
    results.append({
        "test": "mobile_status_get",
        "success": success2,
        "data": data2
    })

    # 測試 3: 運維儀表板
    success3, data3 = test_ops_dashboard()
    results.append({
        "test": "ops_dashboard",
        "success": success3,
        "data": data3
    })

    # 總結
    print("\n" + "=" * 80)
    print("測試總結")
    print("=" * 80)

    total = len(results)
    passed = sum(1 for r in results if r["success"])
    failed = total - passed

    print(f"總測試數: {total}")
    print(f"通過: {passed} ✅")
    print(f"失敗: {failed} ❌")
    print(f"成功率: {(passed / total * 100):.2f}%")

    print("\n詳細結果:")
    print("-" * 80)
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{result['test']}: {status}")

    # 保存結果
    output = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "success_rate": passed / total * 100 if total > 0 else 0,
        "results": results
    }

    with open("/home/cat/桌面/verify_fixes_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n詳細結果已保存到: /home/cat/桌面/verify_fixes_results.json")

    return all(r["success"] for r in results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)