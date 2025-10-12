#!/usr/bin/env python3
"""
AI引擎模組導入測試
基於真實系統數據驗證導入問題
"""

import sys
import os
import traceback

# 添加項目路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps/backend/src'))

def test_import(module_path, class_name=None):
    """測試模組導入"""
    try:
        if class_name:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✅ {module_path}.{class_name} 導入成功")
            return True
        else:
            __import__(module_path)
            print(f"✅ {module_path} 導入成功")
            return True
    except Exception as e:
        print(f"❌ {module_path}{f'.{class_name}' if class_name else ''} 導入失敗: {type(e).__name__}: {e}")
        return False

def main():
    print("🔍 AI引擎模組導入測試（基於真實系統）")
    print("=" * 60)
    
    # 測試基礎組件
    tests = [
        ("agents.base_agent", "BaseAgent"),
        ("ai.agents", None),
        ("hsp.types", "HSPTaskRequestPayload"),
        ("core.services.multi_llm_service", "MultiLLMService"),
    ]
    
    passed = 0
    total = len(tests)
    
    for module_path, class_name in tests:
        if test_import(module_path, class_name):
            passed += 1
    
    print("=" * 60)
    print(f"結果: {passed}/{total} 測試通過")
    
    if passed < total:
        print("發現導入問題，需要修復依賴關係")
        return 1
    else:
        print("所有模組導入正常")
        return 0

if __name__ == "__main__":
    sys.exit(main())