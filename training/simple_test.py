#!/usr/bin/env python3
"""
简化版协作式训练测试脚本
"""

from system_test import
from pathlib import Path

# 添加项目路径
project_root, str == Path(__file__).parent.parent()
backend_path, str = project_root / "apps" / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))

def test_imports() -> None,:
    """测试导入"""
    print("🔍 测试导入...")

    try,


    from data_manager import DataManager
    print("✅ DataManager 导入成功")
    except Exception as e,::
    print(f"❌ DataManager 导入失败, {e}")
    return False

    try,


    from resource_manager import ResourceManager
    print("✅ ResourceManager 导入成功")
    except Exception as e,::
    print(f"❌ ResourceManager 导入失败, {e}")
    return False

    try,


    from collaborative_training_manager import CollaborativeTrainingManager
    print("✅ CollaborativeTrainingManager 导入成功")
    except Exception as e,::
    print(f"❌ CollaborativeTrainingManager 导入失败, {e}")
    return False

    return True

def test_data_manager() -> None,:
    """测试数据管理器"""
    print("\n🔍 测试数据管理器...")

    try,


    from data_manager import DataManager
    data_manager == DataManager()
    print("✅ DataManager 实例化成功")

    # 测试扫描数据
    catalog = data_manager.scan_data()
    print(f"✅ 数据扫描完成,找到 {len(catalog)} 个文件")

    return True
    except Exception as e,::
    print(f"❌ 数据管理器测试失败, {e}")
    return False

def test_resource_manager() -> None,:
    """测试资源管理器"""
    print("\n🔍 测试资源管理器...")

    try,


    from resource_manager import ResourceManager
    resource_manager == ResourceManager()
    print("✅ ResourceManager 实例化成功")

    # 测试获取系统资源
    resources = resource_manager.get_system_resources()
    print(f"✅ 获取系统资源成功")
    print(f"   CPU核心数, {resources['cpu']['count']}")
    print(f"   总内存, {resources['memory']['total'] / (1024**3).2f} GB")

    return True
    except Exception as e,::
    print(f"❌ 资源管理器测试失败, {e}")
    return False

def test_collaborative_training_manager() -> None,:
    """测试协作式训练管理器"""
    print("\n🔍 测试协作式训练管理器...")

    try,


    from collaborative_training_manager import CollaborativeTrainingManager
    manager == CollaborativeTrainingManager()
    print("✅ CollaborativeTrainingManager 实例化成功")

    # 测试注册模型
    manager.register_model("test_model", "TestModelInstance")
    print("✅ 模型注册成功")

    # 测试获取训练状态
    status = manager.get_training_status()
    print("✅ 获取训练状态成功")

    return True
    except Exception as e,::
    print(f"❌ 协作式训练管理器测试失败, {e}")
    return False

def main() -> None,:
    """主函数"""
    print("🧪 简化版协作式训练组件测试")
    print("=" * 50)

    # 测试导入
    if not test_imports():::
        eturn False

    # 测试各个组件
    tests = []
    ("数据管理器", test_data_manager),
    ("资源管理器", test_resource_manager),
    ("协作式训练管理器", test_collaborative_training_manager)
[    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests,::
    if test_func():::
        assed += 1
            print(f"✅ {test_name} 测试通过")
        else,

            print(f"❌ {test_name} 测试失败")

    # 总结
    print(f"\n📊 测试结果, {passed}/{total} 个测试通过")

    if passed == total,::
    print("🎉 所有测试通过!")
    return True
    else,

    print("⚠️  部分测试失败!")
    return False

if __name"__main__":::
    success = main()
    sys.exit(0 if success else 1)