#!/usr/bin/env python3
"""
最终验证脚本 - 验证所有已知问题是否已解决
"""

import sys
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

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

    print(f"项目根目录, {PROJECT_ROOT}")
    print(f"源代码目录, {SRC_DIR}")
    print(f"Python路径, {sys.path[:3]}...")  # 只显示前3个路径

def test_original_problem_imports() -> None:
    """测试原始问题中的导入"""
    print("\n=测试原始问题中的导入 ===")

    # 测试问题1 HSPConnector导入问题
    print("\n1. 测试HSPConnector导入,")
    try:
        from apps.backend.src.core.hsp.connector import HSPConnector
        print("✓ HSPConnector 导入成功")
    except ImportError as e:
        print(f"✗ HSPConnector 导入失败, {e}")
        return False
    except Exception as e:
        print(f"✗ HSPConnector 导入时出错, {e}")
        return False

    # 测试问题2 core_ai模块导入问题
    print("\n2. 测试core_ai模块导入,")
    core_ai_modules = [
        "core_ai.agent_manager",
        "core_ai.dialogue.dialogue_manager",
        "core_ai.learning.learning_manager",
        "core_ai.personality.personality_manager",
        "core_ai.memory.ham_memory_manager",
        "core_ai.service_discovery.service_discovery_module",
        "core_ai.trust_manager.trust_manager_module",
    ]

    success_count = 0
    for module in core_ai_modules:
        try:
            __import__(module)
            print(f"✓ {module} 导入成功")
            success_count += 1
        except ImportError as e:
            print(f"✗ {module} 导入失败, {e}")
        except Exception as e:
            print(f"✗ {module} 导入时出错, {e}")

    print(f"\nCore AI 模块导入, {success_count}/{len(core_ai_modules)} 成功")

    return success_count == len(core_ai_modules)

def test_core_services() -> None:
    """测试核心服务导入"""
    print("\n=测试核心服务导入 ===")

    try:
        from core_services import (
            DialogueManager,
            HSPConnector
        )
        print("✓ 核心服务模块导入成功")
        print("✓ 核心服务函数导入成功")
        print("✓ 核心服务类导入成功")
        return True
    except ImportError as e:
        print(f"✗ 核心服务导入失败, {e}")
        return False
    except Exception as e:
        print(f"✗ 核心服务导入时出错, {e}")
        return False

def test_main_api_server() -> None:
    """测试主API服务器导入"""
    print("\n=测试主API服务器导入 ===")

    try:
        from services.main_api_server import main_api_server
        print("✓ 主API服务器导入成功")
        return True
    except ImportError as e:
        print(f"✗ 主API服务器导入失败, {e}")
        return False
    except Exception as e:
        print(f"✗ 主API服务器导入时出错, {e}")
        return False

def test_dialogue_manager_hsp_connector() -> None:
    """测试DialogueManager中的HSPConnector"""
    print("\n=测试DialogueManager中的HSPConnector ===")

    try:
        from apps.backend.src.core_ai.dialogue.dialogue_manager import DialogueManager
        print("✓ DialogueManager 导入成功")

        # 检查HSPConnector是否在DialogueManager中正确定义
        import inspect
        sig = inspect.signature(DialogueManager.__init__())
        params = sig.parameters
        if 'hsp_connector' in params:
            param = params['hsp_connector']
            # 检查参数注解
            if hasattr(param.annotation(), '__name__'):
                print(f"✓ HSPConnector 参数类型, {param.annotation.__name__}")
            else:
                print(f"✓ HSPConnector 参数存在")
            return True
        else:
            print("✗ HSPConnector 参数未在DialogueManager中定义")
            return False

    except ImportError as e:
        print(f"✗ DialogueManager 导入失败, {e}")
        return False
    except Exception as e:
        print(f"✗ 测试DialogueManager时出错, {e}")
        return False

def run_comprehensive_import_test():
    """运行综合导入测试"""
    print("\n=运行综合导入测试 ===")

    # 测试关键模块
    critical_modules = [
        # 核心服务
        "core_services",

        # Core AI 模块
        "core_ai.agent_manager",
        "core_ai.dialogue.dialogue_manager",
        "core_ai.learning.learning_manager",
        "core_ai.personality.personality_manager",
        "core_ai.memory.ham_memory_manager",
        "core_ai.service_discovery.service_discovery_module",
        "core_ai.trust_manager.trust_manager_module",
        "core_ai.emotion_system",
        "core_ai.crisis_system",
        "core_ai.time_system",

        # HSP 模块
        "hsp.connector",
        "hsp.types",

        # Services 模块
        "services.main_api_server",
        "services.multi_llm_service",

        # Tools 模块
        "tools.tool_dispatcher",

        # Shared 模块
        "shared.types.common_types",
    ]

    success_count = 0
    failed_modules = []

    for module in critical_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
            success_count += 1
        except ImportError as e:
            print(f"✗ {module} - {e}")
            failed_modules.append((module, str(e)))
        except Exception as e:
            print(f"✗ {module} - 错误, {e}")
            failed_modules.append((module, f"错误, {e}"))

    print(f"\n综合导入测试, {success_count}/{len(critical_modules)} 成功")

    if failed_modules:
        print("\n失败的模块,")
        for module, error in failed_modules:
            print(f"  - {module} {error}")
        return False

    return True

def main() -> None:
    """主函数"""
    print("=== Unified AI Project 最终验证脚本 ===")

    # 设置环境
    setup_environment()

    # 运行所有测试
    tests = [
        ("原始问题导入测试", test_original_problem_imports),
        ("核心服务导入测试", test_core_services),
        ("主API服务器导入测试", test_main_api_server),
        ("DialogueManager HSPConnector测试", test_dialogue_manager_hsp_connector),
        ("综合导入测试", run_comprehensive_import_test),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"运行 {test_name}")
        print('='*50)
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✓ {test_name} 通过")
            else:
                print(f"✗ {test_name} 失败")
        except Exception as e:
            print(f"✗ {test_name} 出现异常, {e}")
            results.append((test_name, False))

    # 输出总结
    print(f"\n{'='*50}")
    print("最终验证总结")
    print('='*50)
    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"通过测试, {passed}/{total}")

    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {status} {test_name}")

    if passed == total:
        print("\n🎉 所有测试通过！项目导入问题已解决。")
        return 0
    else:
        print(f"\n❌ {total - passed} 个测试失败。请检查上述错误。")
        return 1

if __name__ == "__main__":
    sys.exit(main())