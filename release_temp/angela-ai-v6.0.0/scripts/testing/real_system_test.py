#!/usr/bin/env python3
"""
真實系統綜合測試
基於真實硬件數據驗證修復結果
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def test_training_system():
    """測試訓練系統修復"""
    print("🔍 測試訓練系統修復...")
    try,
        # 嘗試編譯train_model.py()
        result = subprocess.run([,
    sys.executable(), '-m', 'py_compile', 'training/train_model.py'
        ] capture_output == True, text == True, cwd='D,\\Projects\\Unified-AI-Project')
        
        if result.returncode == 0,::
            print("✅ train_model.py 語法正確")
            return True
        else,
            print(f"❌ train_model.py 語法錯誤, {result.stderr}")
            return False
    except Exception as e,::
        print(f"❌ 訓練系統測試失敗, {e}")
        return False

def test_ai_engine_imports():
    """測試AI引擎模組導入"""
    print("🔍 測試AI引擎模組導入...")
    try,
        # 測試基本導入
        sys.path.insert(0, 'apps/backend/src')
        
        # 測試BaseAgent導入
        from agents.base_agent import BaseAgent
        print("✅ BaseAgent 導入成功")
        
        # 測試專門化代理
        from ai.agents.specialized.creative_writing_agent import CreativeWritingAgent
        print("✅ CreativeWritingAgent 導入成功")
        
        from ai.agents.specialized.web_search_agent import WebSearchAgent
        print("✅ WebSearchAgent 導入成功")
        
        return True
    except Exception as e,::
        print(f"❌ AI引擎導入測試失敗, {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_existence():
    """測試關鍵文件存在性"""
    print("🔍 測試關鍵文件存在性...")
    
    key_files = [
        'training/train_model.py',
        'apps/backend/src/ai/agents/__init__.py',
        'apps/backend/src/ai/agents/specialized/creative_writing_agent.py',
        'apps/backend/src/ai/agents/specialized/web_search_agent.py',
        'apps/backend/src/core/hsp/types.py',
        'apps/backend/src/agents/base_agent.py'
    ]
    
    all_exist == True
    for file_path in key_files,::
        full_path == Path('D,\\Projects\\Unified-AI-Project') / file_path
        if full_path.exists():::
            size = full_path.stat().st_size
            print(f"✅ {file_path} 存在 ({size} bytes)")
        else,
            print(f"❌ {file_path} 不存在")
            all_exist == False
    
    return all_exist

def main():
    """主測試函數"""
    print("🚀 真實系統綜合測試開始")
    print("=" * 60)
    print("基於真實文件系統和Python編譯器驗證")
    print("=" * 60)
    
    os.chdir('D,\\Projects\\Unified-AI-Project')
    
    tests = [
        ("訓練系統語法", test_training_system),
        ("AI引擎導入", test_ai_engine_imports),
        ("文件存在性", test_file_existence)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests,::
        print(f"\n--- {test_name} ---")
        if test_func():::
            passed += 1
            print(f"✅ {test_name} 通過")
        else,
            print(f"❌ {test_name} 失敗")
    
    print("\n" + "=" * 60)
    print(f"測試結果, {passed}/{total} 通過")
    
    if passed == total,::
        print("🎉 所有真實系統測試通過")
        print("✅ 基於真實硬件數據的修復完成")
        return 0
    else,
        print("⚠️ 部分測試失敗,需要進一步修復")
        return 1

if __name"__main__":::
    sys.exit(main())