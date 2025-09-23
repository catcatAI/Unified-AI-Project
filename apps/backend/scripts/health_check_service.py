#!/usr/bin/env python3
"""
健康检查服务 - 提供快速检查和完整检查两种模式
"""

import os
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"

def setup_environment():
    """设置环境"""
    # 添加项目路径
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))

def quick_health_check():
    """快速健康检查 - 仅检查模块导入和基本依赖"""
    print("🩺 快速健康检查")
    try:
        # 检查核心模块导入
        from src.ai.memory.ham_memory_manager import HAMMemoryManager
        print("✅ HAM内存管理模块导入成功")
        
        from src.core.services.multi_llm_service import MultiLLMService
        print("✅ 多LLM服务模块导入成功")
        
        from src.hsp.connector import HSPConnector
        print("✅ HSP连接器模块导入成功")
        
        # 检查基础依赖
        import fastapi
        import uvicorn
        import chromadb
        print("✅ 基础依赖检查通过")
        
        return True
    except Exception as e:
        print(f"❌ 快速健康检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def full_health_check():
    """完整健康检查 - 初始化所有核心组件并检查连接"""
    print("🩺 完整健康检查")
    try:
        # 初始化HAM内存管理
        from src.ai.memory.ham_memory_manager import HAMMemoryManager
        ham_manager = HAMMemoryManager()
        print("✅ HAM内存管理初始化完成")
        
        # 初始化多LLM服务
        from src.core.services.multi_llm_service import MultiLLMService
        llm_service = MultiLLMService()
        print("✅ 多LLM服务初始化完成")
        
        # 初始化HSP连接器
        from src.hsp.connector import HSPConnector
        hsp_connector = HSPConnector(
            ai_id="did:hsp:health_check_ai",
            broker_address="localhost",
            broker_port=1883
        )
        print("✅ HSP连接器初始化完成")
        
        # 检查ChromaDB连接
        try:
            from src.ai.memory.vector_store import VectorMemoryStore
            vector_store = VectorMemoryStore()
            # 尝试执行一个简单的操作来验证连接
            vector_store.client.heartbeat()
            print("✅ ChromaDB连接正常")
        except Exception as e:
            print(f"⚠️ ChromaDB连接检查失败: {e}")
        
        return True
    except Exception as e:
        print(f"❌ 完整健康检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def prelaunch_services():
    """预启动所有功能 - 初始化核心服务但不启动完整功能"""
    print("🚀 预启动核心服务")
    try:
        # 初始化核心服务
        from src.ai.memory.ham_memory_manager import HAMMemoryManager
        ham_manager = HAMMemoryManager()
        print("✅ HAM内存管理初始化完成")
        
        from src.core.services.multi_llm_service import MultiLLMService
        llm_service = MultiLLMService()
        print("✅ 多LLM服务初始化完成")
        
        from src.core.services.service_discovery import ServiceDiscoveryModule
        service_discovery = ServiceDiscoveryModule()
        print("✅ 服务发现机制初始化完成")
        
        # 初始化HSP连接器
        from src.hsp.connector import HSPConnector
        hsp_connector = HSPConnector(
            ai_id="did:hsp:prelaunch_ai",
            broker_address="localhost",
            broker_port=1883
        )
        print("✅ HSP连接器初始化完成")
        
        return True
    except Exception as e:
        print(f"❌ 预启动服务失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    setup_environment()
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "quick":
            return 0 if quick_health_check() else 1
        elif mode == "full":
            return 0 if full_health_check() else 1
        elif mode == "prelaunch":
            return 0 if prelaunch_services() else 1
        else:
            print("用法: health_check_service.py [quick|full|prelaunch]")
            return 1
    else:
        # 默认执行快速健康检查
        return 0 if quick_health_check() else 1

if __name__ == "__main__":
    exit(main())