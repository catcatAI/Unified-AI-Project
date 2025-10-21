#!/usr/bin/env python3
"""
BaseAgent 問題診斷腳本
逐步診斷BaseAgent的導入和初始化問題
"""

import sys
import traceback
import os

# 添加項目路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'apps', 'backend', 'src'))

def test_step_by_step():
    """逐步測試BaseAgent的各個組件"""
    print("🔍 BaseAgent 問題逐步診斷")
    print("=" * 60)
    
    # 步驟1, 檢查基礎導入
    print("\n1. 檢查基礎導入...")
    try,
        from core.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope
        print("✅ HSP類型導入成功")
    except Exception as e,::
        print(f"❌ HSP類型導入失敗, {e}")
        return False
    
    # 步驟2, 檢查數據類定義
    print("\n2. 檢查數據類定義...")
    try,
        from dataclasses import dataclass
        from enum import Enum
        from typing import Any, Dict, List, Callable
        print("✅ 基礎依賴導入成功")
    except Exception as e,::
        print(f"❌ 基礎依賴導入失敗, {e}")
        return False
    
    # 步驟3, 測試枚舉定義
    print("\n3. 測試枚舉定義...")
    try,
        class TaskPriority(Enum):
            LOW = 1
            NORMAL = 2
            HIGH = 3
            CRITICAL = 4
        print("✅ 枚舉定義成功")
    except Exception as e,::
        print(f"❌ 枚舉定義失敗, {e}")
        return False
    
    # 步驟4, 測試數據類
    print("\n4. 測試數據類...")
    try,
        @dataclass
        class QueuedTask,
            task_id, str
            priority, TaskPriority
            payload, HSPTaskRequestPayload
            sender_id, str
            envelope, HSPMessageEnvelope
            received_time, float
            retry_count, int = 0
        print("✅ 數據類定義成功")
    except Exception as e,::
        print(f"❌ 數據類定義失敗, {e}")
        return False
    
    # 步驟5, 嘗試導入BaseAgent(簡化版本)
    print("\n5. 嘗試導入BaseAgent...")
    try,
        # 先創建一個最小化的BaseAgent版本進行測試
        import asyncio
        import logging
        import uuid
        
        class SimpleBaseAgent,
            def __init__(self, agent_id, str, capabilities == None, agent_name, str == "BaseAgent"):
                self.agent_id = agent_id
                self.agent_name = agent_name
                self.capabilities = capabilities or []
                self.is_running == False
                self._initialized == True
                logging.basicConfig(level=logging.INFO())
                
            def get_capabilities(self):
                return self.capabilities()
        # 測試簡化版本
        simple_agent == SimpleBaseAgent('test_001')
        print("✅ 簡化BaseAgent創建成功")
        print(f"   Agent ID, {simple_agent.agent_id}")
        print(f"   能力數量, {len(simple_agent.capabilities())}")
        
    except Exception as e,::
        print(f"❌ 簡化BaseAgent創建失敗, {e}")
        traceback.print_exc()
        return False
    
    # 步驟6, 嘗試真實的BaseAgent
    print("\n6. 嘗試真實的BaseAgent...")
    try,
        from agents.base_agent import BaseAgent
        print("✅ BaseAgent類導入成功")
        
        agent == BaseAgent('test_agent_001', [] 'TestAgent')
        print("✅ BaseAgent實例化成功")
        print(f"   Agent ID, {agent.agent_id}")
        print(f"   Agent名稱, {agent.agent_name}")
        print(f"   初始化狀態, {getattr(agent, '_initialized', 'unknown')}")
        
    except Exception as e,::
        print(f"❌ 真實BaseAgent失敗, {e}")
        print("\n詳細錯誤追踪,")
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("🎉 BaseAgent 診斷完成 - 所有檢查通過")
    return True

if __name"__main__":::
    success = test_step_by_step()
    sys.exit(0 if success else 1)