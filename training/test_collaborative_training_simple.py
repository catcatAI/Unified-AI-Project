#!/usr/bin/env python3
"""
简化版协作式训练测试脚本
"""

import sys
from pathlib import Path

# 添加项目路径
project_root: str = Path(__file__).parent.parent
_ = sys.path.insert(0, str(project_root))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger: Any = logging.getLogger(__name__)

def test_collaborative_training_manager_basic() -> None:
    """测试协作式训练管理器基本功能"""
    _ = logger.info("🔄 测试协作式训练管理器基本功能...")
    
    try:
        # 由于numpy导入问题，我们直接测试协作式训练管理器的核心功能
        from training.collaborative_training_manager import CollaborativeTrainingManager
        
        # 创建管理器实例
        manager = CollaborativeTrainingManager()
        _ = logger.info("✅ 协作式训练管理器初始化成功")
        
        # 注册模型
        _ = manager.register_model("test_model_1", "TestModelInstance1")
        _ = manager.register_model("test_model_2", "TestModelInstance2")
        _ = logger.info(f"✅ 注册了 {len(manager.models)} 个模型")
        
        # 测试获取训练状态
        status = manager.get_training_status()
        logger.info(f"✅ 获取训练状态成功: is_training={status['is_training']}")
        
        # 测试获取资源使用情况
        resource_usage = manager.get_resource_usage()
        _ = logger.info("✅ 获取资源使用情况成功")
        
        _ = logger.info("🎉 协作式训练管理器基本功能测试通过!")
        return True
        
    except Exception as e:
        _ = logger.error(f"❌ 协作式训练管理器测试失败: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

def test_model_training_task() -> None:
    """测试模型训练任务类"""
    _ = logger.info("🎯 测试模型训练任务类...")
    
    try:
        from training.collaborative_training_manager import ModelTrainingTask
        
        # 创建训练任务实例
        task = ModelTrainingTask(
            model_name="test_model",
            model_instance="TestModelInstance",
            data=[],
            resources={}
        )
        
        _ = logger.info("✅ 模型训练任务初始化成功")
        
        # 测试更新指标
        _ = task.update_metrics({"accuracy": 0.95, "loss": 0.05})
        _ = logger.info(f"✅ 更新指标成功: {task.metrics}")
        
        # 测试添加共享知识
        knowledge = {"accuracy": 0.92, "source_model": "other_model"}
        _ = task.add_shared_knowledge(knowledge)
        _ = logger.info(f"✅ 添加共享知识成功，当前知识数量: {len(task.shared_knowledge)}")
        
        # 测试增加发送知识计数
        _ = task.increment_sent_knowledge()
        _ = logger.info(f"✅ 增加发送知识计数成功，当前计数: {task.sent_knowledge_count}")
        
        _ = logger.info("🎉 模型训练任务类测试通过!")
        return True
        
    except Exception as e:
        _ = logger.error(f"❌ 模型训练任务类测试失败: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

def main() -> None:
    """主函数"""
    _ = print("🧪 测试协作式训练组件（简化版）...")
    print("=" * 50)
    
    # 测试各个组件
    tests = [
        _ = ("模型训练任务类", test_model_training_task),
        _ = ("协作式训练管理器基本功能", test_collaborative_training_manager_basic)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        _ = print(f"\n📋 运行 {test_name} 测试...")
        try:
            if test_func():
                passed += 1
                _ = print(f"✅ {test_name} 测试通过")
            else:
                _ = print(f"❌ {test_name} 测试失败")
        except Exception as e:
            _ = print(f"❌ {test_name} 测试出错: {e}")
            import traceback
            _ = traceback.print_exc()
    
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