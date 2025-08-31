#!/usr/bin/env python3
"""
简单的协作式训练测试脚本
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "apps" / "backend"))
sys.path.insert(0, str(project_root / "apps" / "backend" / "src"))

def test_collaborative_training_import():
    """测试协作式训练管理器导入"""
    print("🔍 测试协作式训练管理器导入...")
    
    try:
        from collaborative_training_manager import CollaborativeTrainingManager
        print("✅ CollaborativeTrainingManager 导入成功")
        return True
    except Exception as e:
        print(f"❌ CollaborativeTrainingManager 导入失败: {e}")
        return False

def test_collaborative_training_initialization():
    """测试协作式训练管理器初始化"""
    print("\n🔍 测试协作式训练管理器初始化...")
    
    try:
        from collaborative_training_manager import CollaborativeTrainingManager
        manager = CollaborativeTrainingManager()
        print("✅ CollaborativeTrainingManager 初始化成功")
        print(f"   已注册模型数量: {len(manager.models)}")
        return True
    except Exception as e:
        print(f"❌ CollaborativeTrainingManager 初始化失败: {e}")
        return False

def test_training_script_preset():
    """测试训练脚本的协作式训练预设"""
    print("\n🔍 测试训练脚本的协作式训练预设...")
    
    try:
        from training.train_model import ModelTrainer
        trainer = ModelTrainer()
        
        # 获取协作式训练预设
        scenario = trainer.get_preset_scenario("collaborative_training")
        if scenario:
            print("✅ 协作式训练预设加载成功")
            print(f"   描述: {scenario.get('description', '无描述')}")
            print(f"   数据集: {', '.join(scenario.get('datasets', []))}")
            print(f"   训练轮数: {scenario.get('epochs', 0)}")
            return True
        else:
            print("❌ 协作式训练预设加载失败")
            return False
    except Exception as e:
        print(f"❌ 训练脚本协作式训练预设测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🧪 简单协作式训练功能测试")
    print("=" * 50)
    
    # 测试各个组件
    tests = [
        ("协作式训练管理器导入", test_collaborative_training_import),
        ("协作式训练管理器初始化", test_collaborative_training_initialization),
        ("训练脚本协作式训练预设", test_training_script_preset)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 运行 {test_name} 测试...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试出错: {e}")
    
    # 总结
    print(f"\n📊 测试结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过!")
        return True
    else:
        print("⚠️  部分测试失败!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)