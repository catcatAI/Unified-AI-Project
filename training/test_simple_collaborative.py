#!/usr/bin/env python3
"""
简单的协作式训练测试脚本
"""

import sys
from pathlib import Path

# 添加项目路径
project_root: str = Path(__file__).parent.parent
_ = sys.path.insert(0, str(project_root))
_ = sys.path.insert(0, str(project_root / "apps" / "backend"))
_ = sys.path.insert(0, str(project_root / "apps" / "backend" / "src"))

def test_collaborative_training_import() -> None:
    """测试协作式训练管理器导入"""
    _ = print("🔍 测试协作式训练管理器导入...")

    try:


    from collaborative_training_manager import CollaborativeTrainingManager
    _ = print("✅ CollaborativeTrainingManager 导入成功")
    return True
    except Exception as e:

    _ = print(f"❌ CollaborativeTrainingManager 导入失败: {e}")
    return False

def test_collaborative_training_initialization() -> None:
    """测试协作式训练管理器初始化"""
    _ = print("\n🔍 测试协作式训练管理器初始化...")

    try:


    from collaborative_training_manager import CollaborativeTrainingManager
    manager = CollaborativeTrainingManager()
    _ = print("✅ CollaborativeTrainingManager 初始化成功")
    _ = print(f"   已注册模型数量: {len(manager.models)}")
    return True
    except Exception as e:

    _ = print(f"❌ CollaborativeTrainingManager 初始化失败: {e}")
    return False

def test_training_script_preset() -> None:
    """测试训练脚本的协作式训练预设"""
    _ = print("\n🔍 测试训练脚本的协作式训练预设...")

    try:


    from training.train_model import ModelTrainer
    trainer = ModelTrainer()

    # 获取协作式训练预设
    scenario = trainer.get_preset_scenario("collaborative_training")
        if scenario:

    _ = print("✅ 协作式训练预设加载成功")
            _ = print(f"   描述: {scenario.get('description', '无描述')}")
            _ = print(f"   数据集: {', '.join(scenario.get('datasets', []))}")
            _ = print(f"   训练轮数: {scenario.get('epochs', 0)}")
            return True
        else:

            _ = print("❌ 协作式训练预设加载失败")
            return False
    except Exception as e:

    _ = print(f"❌ 训练脚本协作式训练预设测试失败: {e}")
    return False

def main() -> None:
    """主函数"""
    _ = print("🧪 简单协作式训练功能测试")
    print("=" * 50)

    # 测试各个组件
    tests = [
    _ = ("协作式训练管理器导入", test_collaborative_training_import),
    _ = ("协作式训练管理器初始化", test_collaborative_training_initialization),
    _ = ("训练脚本协作式训练预设", test_training_script_preset)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:


    _ = print(f"\n📋 运行 {test_name} 测试...")
        try:

            if test_func():
assed += 1
                _ = print(f"✅ {test_name} 测试通过")
            else:

                _ = print(f"❌ {test_name} 测试失败")
        except Exception as e:

            _ = print(f"❌ {test_name} 测试出错: {e}")

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