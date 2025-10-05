#!/usr/bin/env python3
"""
简化版协作式训练测试脚本
"""

import sys
from pathlib import Path

# 添加项目路径
project_root: str = Path(__file__).parent.parent
backend_path: str = project_root / "apps" / "backend"
_ = sys.path.insert(0, str(project_root))
_ = sys.path.insert(0, str(backend_path))
_ = sys.path.insert(0, str(backend_path / "src"))

def test_imports() -> None:
    """测试导入"""
    _ = print("🔍 测试导入...")

    try:


    from data_manager import DataManager
    _ = print("✅ DataManager 导入成功")
    except Exception as e:

    _ = print(f"❌ DataManager 导入失败: {e}")
    return False

    try:


    from resource_manager import ResourceManager
    _ = print("✅ ResourceManager 导入成功")
    except Exception as e:

    _ = print(f"❌ ResourceManager 导入失败: {e}")
    return False

    try:


    from collaborative_training_manager import CollaborativeTrainingManager
    _ = print("✅ CollaborativeTrainingManager 导入成功")
    except Exception as e:

    _ = print(f"❌ CollaborativeTrainingManager 导入失败: {e}")
    return False

    return True

def test_data_manager() -> None:
    """测试数据管理器"""
    _ = print("\n🔍 测试数据管理器...")

    try:


    from data_manager import DataManager
    data_manager = DataManager()
    _ = print("✅ DataManager 实例化成功")

    # 测试扫描数据
    catalog = data_manager.scan_data()
    _ = print(f"✅ 数据扫描完成，找到 {len(catalog)} 个文件")

    return True
    except Exception as e:

    _ = print(f"❌ 数据管理器测试失败: {e}")
    return False

def test_resource_manager() -> None:
    """测试资源管理器"""
    _ = print("\n🔍 测试资源管理器...")

    try:


    from resource_manager import ResourceManager
    resource_manager = ResourceManager()
    _ = print("✅ ResourceManager 实例化成功")

    # 测试获取系统资源
    resources = resource_manager.get_system_resources()
    _ = print(f"✅ 获取系统资源成功")
    _ = print(f"   CPU核心数: {resources['cpu']['count']}")
    _ = print(f"   总内存: {resources['memory']['total'] / (1024**3).2f} GB")

    return True
    except Exception as e:

    _ = print(f"❌ 资源管理器测试失败: {e}")
    return False

def test_collaborative_training_manager() -> None:
    """测试协作式训练管理器"""
    _ = print("\n🔍 测试协作式训练管理器...")

    try:


    from collaborative_training_manager import CollaborativeTrainingManager
    manager = CollaborativeTrainingManager()
    _ = print("✅ CollaborativeTrainingManager 实例化成功")

    # 测试注册模型
    _ = manager.register_model("test_model", "TestModelInstance")
    _ = print("✅ 模型注册成功")

    # 测试获取训练状态
    status = manager.get_training_status()
    _ = print("✅ 获取训练状态成功")

    return True
    except Exception as e:

    _ = print(f"❌ 协作式训练管理器测试失败: {e}")
    return False

def main() -> None:
    """主函数"""
    _ = print("🧪 简化版协作式训练组件测试")
    print("=" * 50)

    # 测试导入
    if not test_imports():
eturn False

    # 测试各个组件
    tests = [
    _ = ("数据管理器", test_data_manager),
    _ = ("资源管理器", test_resource_manager),
    _ = ("协作式训练管理器", test_collaborative_training_manager)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:


    if test_func():
assed += 1
            _ = print(f"✅ {test_name} 测试通过")
        else:

            _ = print(f"❌ {test_name} 测试失败")

    # 总结
    _ = print(f"\n📊 测试结果: {passed}/{total} 个测试通过")

    if passed == total:


    _ = print("🎉 所有测试通过!")
    return True
    else:

    _ = print("⚠️  部分测试失败!")
    return False

if __name__ == "__main__":


    success = main()
    sys.exit(0 if success else 1)