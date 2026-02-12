"""
全面组件连接检查
检查所有组件的初始化和连接关系
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

sys.path.insert(0, 'apps/backend')

print("="*80)
print("COMPREHENSIVE COMPONENT CONNECTION AUDIT")
print("="*80)
print()

# 1. 检查所有核心组件文件
print("1. 核心组件文件检查")
print("-"*80)

component_files = {
    "CognitiveOrchestrator": {
        "path": "src/core/orchestrator.py",
        "purpose": "认知编排器 - 核心大脑"
    },
    "HAMMemoryManager": {
        "path": "src/ai/memory/ham_memory_manager.py",
        "purpose": "记忆系统 - 存储和检索"
    },
    "EconomyManager": {
        "path": "src/game/economy_manager.py",
        "purpose": "经济系统 - 余额、交易、物品"
    },
    "UniversalCreationEngine": {
        "path": "src/core/universal_creation_engine.py",
        "purpose": "通用创作引擎 - 代码、文学、游戏等"
    },
    "SystemManager": {
        "path": "src/core/managers/system_manager_actor.py",
        "purpose": "系统管理器 - 协调所有组件"
    }
}

for name, info in component_files.items():
    full_path = Path(info["path"])
    if full_path.exists():
        size = full_path.stat().st_size
        print(f"✅ {name:30} {info['path']:40} ({size:,} bytes)")
    else:
        print(f"❌ {name:30} {info['path']:40} (MISSING)")
print()

# 2. 检查组件间的依赖关系
print("2. 组件依赖关系分析")
print("-"*80)

dependencies = [
    {
        "source": "CognitiveOrchestrator",
        "depends_on": ["HAMMemoryManager"],
        "connection_type": "import - 异步调用",
        "methods": ["store_experience", "retrieve_relevant_memories"]
    },
    {
        "source": "SystemManager",
        "depends_on": ["CognitiveOrchestrator", "HAMMemoryManager", "EconomyManager", "DesktopPet"],
        "connection_type": "实例引用 - 初始化时创建",
        "methods": ["get_cognitive_orchestrator", "get_ham_memory_manager"]
    },
    {
        "source": "UniversalCreationEngine",
        "depends_on": ["CognitiveOrchestrator"],
        "connection_type": "可选 - 通过 orchestrator 调用",
        "methods": ["process_user_input"]
    }
]

for dep in dependencies:
    print(f"\n{dep['source']} 依赖:")
    for dep_name in dep['depends_on']:
        print(f"  → {dep_name:30} ({dep['connection_type']})")
    print(f"     使用方法: {', '.join(dep['methods'])}")
print()

# 3. 检查实际代码中的导入和调用
print("3. 实际代码导入和调用检查")
print("-"*80)

# 检查 orchestrator 的导入
orchestrator_file = Path("src/core/orchestrator.py")
if orchestrator_file.exists():
    content = orchestrator_file.read_text(encoding='utf-8')
    
    print("Orchestrator 导入的组件:")
    if "HAMMemoryManager" in content:
        print("  ✅ HAMMemoryManager - 已导入")
    else:
        print("  ❌ HAMMemoryManager - 未导入")
    
    if "EconomyManager" in content:
        print("  ✅ EconomyManager - 已导入")
    else:
        print("  ❌ EconomyManager - 未导入")
    
    if "UniversalCreationEngine" in content:
        print("  ✅ UniversalCreationEngine - 已导入")
    else:
        print("  ❌ UniversalCreationEngine - 未导入")
print()

# 4. 测试组件实例化和基本功能
print("4. 组件实例化测试")
print("-"*80)

async def test_components():
    results = {}
    
    # 测试 HAMMemoryManager
    try:
        from src.ai.memory.ham_memory_manager import HAMMemoryManager
        ham = HAMMemoryManager()
        
        # 测试基本功能
        test_exp = {"content": "test", "type": "test"}
        await ham.store_experience(test_exp)
        memories = await ham.retrieve_relevant_memories("test", limit=3)
        
        results["HAMMemoryManager"] = {
            "status": "✅ PASS",
            "functions": ["store_experience", "retrieve_relevant_memories"],
            "details": f"Stored 1, Retrieved {len(memories)}"
        }
    except Exception as e:
        logger.error(f'Error in {__name__}: {e}', exc_info=True)
        results["HAMMemoryManager"] = {

            "status": "❌ FAIL",
            "error": str(e)
        }
    
    # 测试 EconomyManager
    try:
        from src.game.economy_manager import EconomyManager
        econ = EconomyManager({"db_path": ":memory:"})
        
        balance = econ.get_balance("test_user")
        econ.process_transaction({"user_id": "test_user", "amount": 50})
        
        results["EconomyManager"] = {
            "status": "✅ PASS",
            "functions": ["get_balance", "process_transaction"],
            "details": f"Balance: {balance}"
        }
    except Exception as e:
        logger.error(f'Error in {__name__}: {e}', exc_info=True)
        results["EconomyManager"] = {

            "status": "❌ FAIL",
            "error": str(e)
        }
    
    # 测试 CognitiveOrchestrator
    try:
        from src.core.orchestrator import CognitiveOrchestrator
        orch = CognitiveOrchestrator()
        await orch.initialize()
        
        # 测试基本对话
        result = await orch.process_user_input("Hello")
        
        await orch.shutdown()
        
        results["CognitiveOrchestrator"] = {
            "status": "✅ PASS",
            "functions": ["initialize", "process_user_input", "shutdown"],
            "details": f"Response: {result.get('response', 'N/A')[:30]}..."
        }
    except Exception as e:
        logger.error(f'Error in {__name__}: {e}', exc_info=True)
        results["CognitiveOrchestrator"] = {

            "status": "❌ FAIL",
            "error": str(e)
        }
    
    # 测试 UniversalCreationEngine
    try:
        from src.core.universal_creation_engine import UniversalCreationEngine
        engine = UniversalCreationEngine()
        
        result = await engine.process_user_input("hello")
        
        results["UniversalCreationEngine"] = {
            "status": "✅ PASS",
            "functions": ["process_user_input"],
            "details": f"Mode: {result.get('mode', 'N/A')}"
        }
    except Exception as e:
        logger.error(f'Error in {__name__}: {e}', exc_info=True)
        results["UniversalCreationEngine"] = {

            "status": "❌ FAIL",
            "error": str(e)
        }
    
    # 显示结果
    for name, result in results.items():
        status = result["status"]
        print(f"\n{name:30} {status}")
        if "functions" in result:
            print(f"  功能: {', '.join(result['functions'])}")
        if "details" in result:
            print(f"  详情: {result['details']}")
        if "error" in result:
            print(f"  错误: {result['error']}")
    
    # 5. 连接状态总结
    print("\n" + "="*80)
    print("5. 组件连接状态总结")
    print("="*80)
    
    connected = 0
    total = len(results)
    
    for name, result in results.items():
        if "PASS" in result["status"]:
            connected += 1
            print(f"✅ {name:30} 已连接并正常工作")
        else:
            print(f"❌ {name:30} 未连接或有错误")
    
    print(f"\n连接率: {connected}/{total} ({connected/total*100:.1f}%)")
    
    # 6. 找出未连接的部分
    print("\n" + "="*80)
    print("6. 未连接组件分析")
    print("="*80)
    
    missing_connections = []
    
    for name, result in results.items():
        if "FAIL" in result["status"]:
            missing_connections.append({
                "component": name,
                "error": result.get("error", "Unknown error")
                "impact": "影响系统功能"
            })
    
    if missing_connections:
        print("\n发现的未连接组件:")
        for item in missing_connections:
            print(f"\n❌ {item['component']}:")
            print(f"   错误: {item['error']}")
            print(f"   影响: {item['impact']}")
    else:
        print("\n✅ 所有核心组件都已连接！")
    
    return results

results = asyncio.run(test_components())

print()
print("="*80)
print("审计完成时间:", datetime.now().isoformat())
print("="*80)
