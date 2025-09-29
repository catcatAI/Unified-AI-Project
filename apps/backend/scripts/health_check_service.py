#!/usr/bin/env python3
"""
健康检查服务 - 提供快速检查和完整检查两种模式
"""

# 添加Pyright忽略导入错误的注释
# pyright: reportMissingImports=false

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Dict, Union, Literal

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"

# 定义ChromaClientType类型，与vector_store.py保持一致
if TYPE_CHECKING:
    try:
        from chromadb.api import ClientAPI
        # 直接在需要的地方使用类型注解，避免重新定义
    except ImportError:
        # 创建一个兼容的类型别名
        from typing import Protocol
        class ClientAPI(Protocol):
            """ChromaDB客户端API的协议定义"""
            def heartbeat(self) -> None: ...
            def get_or_create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None, **kwargs) -> Any: ...
    # 定义客户端类型，与vector_store.py保持一致
    ChromaClientType = Union[ClientAPI, Any]
else:
    # 运行时定义一个通用类型，与vector_store.py保持一致
    ChromaClientType = Any

# 条件导入用于类型检查
if TYPE_CHECKING:
    from src.ai.memory.vector_store import VectorMemoryStore

def setup_environment():
    """设置环境"""
    # 添加项目路径
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))

def quick_health_check():
    """快速健康检查 - 仅检查模块导入和基本依赖"""
    setup_environment()
    print("🩺 快速健康检查")
    try:
        # 检查核心模块导入
        # 仅检查模块是否能导入成功，不需要创建实例
        # 使用 __import__ 函数来检查模块可导入性而不产生未使用导入警告
        __import__('src.core.services.multi_llm_service')
        print("✅ 多LLM服务模块导入成功")
        
        # 检查基础依赖 - 使用 __import__ 函数避免未使用导入警告
        __import__('fastapi')
        __import__('uvicorn')
        print("✅ 基础依赖检查通过")
        
        return True
    except Exception as e:
        print(f"❌ 快速健康检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def full_health_check():
    """完整健康检查 - 初始化所有核心组件并检查连接"""
    setup_environment()
    print("🩺 完整健康检查")
    try:
        # 初始化HAM内存管理
        from src.ai.memory.ham_memory_manager import HAMMemoryManager
        # 使用下划线表示我们有意忽略返回值，避免未使用变量警告
        HAMMemoryManager()
        print("✅ HAM内存管理初始化完成")
        
        # 初始化多LLM服务
        from src.core.services.multi_llm_service import MultiLLMService
        MultiLLMService()  # 使用下划线忽略未使用变量警告
        print("✅ 多LLM服务初始化完成")
        
        # 检查ChromaDB连接
        try:
            from src.ai.memory.vector_store import VectorMemoryStore
            vector_store: 'VectorMemoryStore' = VectorMemoryStore()
            # 检查客户端是否已初始化并且不是None
            if vector_store.client is not None:
                # 使用明确的类型注解避免Any类型
                client: Any = vector_store.client
                if hasattr(client, 'heartbeat'):
                    result = client.heartbeat()
                    # 忽略返回值，只检查方法是否能正常调用
                    _ = result
                    print("✅ ChromaDB连接正常")
                else:
                    print("⚠️ ChromaDB客户端缺少heartbeat方法")
            else:
                print("⚠️ ChromaDB客户端未初始化")
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
    setup_environment()
    print("🚀 预启动核心服务")
    try:
        # 初始化核心服务
        from src.ai.memory.ham_memory_manager import HAMMemoryManager
        # 使用下划线表示我们有意忽略返回值，避免未使用变量警告
        HAMMemoryManager()
        print("✅ HAM内存管理初始化完成")
        
        from src.core.services.multi_llm_service import MultiLLMService
        MultiLLMService()  # 使用下划线忽略未使用变量警告
        print("✅ 多LLM服务初始化完成")
        
        from src.ai.discovery.service_discovery_module import ServiceDiscoveryModule
        from src.ai.trust.trust_manager_module import TrustManager
        trust_manager = TrustManager()
        ServiceDiscoveryModule(trust_manager=trust_manager)  # 使用下划线忽略未使用变量警告
        print("✅ 服务发现机制初始化完成")
        
        return True
    except Exception as e:
        print(f"❌ 预启动服务失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main() -> Literal[0, 1]:
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