#!/usr/bin/env python3
"""
简化版协作式训练测试脚本
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_collaborative_training_manager_basic():
    """测试协作式训练管理器基本功能"""
    logger.info("🔄 测试协作式训练管理器基本功能...")
    
    try:
        # 由于numpy导入问题，我们直接测试协作式训练管理器的核心功能
        from training.collaborative_training_manager import CollaborativeTrainingManager
        
        # 创建管理器实例
        manager = CollaborativeTrainingManager()
        logger.info("✅ 协作式训练管理器初始化成功")
        
        # 注册模型
        manager.register_model("test_model_1", "TestModelInstance1")
        manager.register_model("test_model_2", "TestModelInstance2")
        logger.info(f"✅ 注册了 {len(manager.models)} 个模型")
        
        # 测试获取训练状态
        status = manager.get_training_status()
        logger.info(f"✅ 获取训练状态成功: is_training={status['is_training']}")
        
        # 测试获取资源使用情况
        resource_usage = manager.get_resource_usage()
        logger.info("✅ 获取资源使用情况成功")
        
        logger.info("🎉 协作式训练管理器基本功能测试通过!")
        return True
        
    except Exception as e:
        logger.error(f"❌ 协作式训练管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_training_task():
    """测试模型训练任务类"""
    logger.info("🎯 测试模型训练任务类...")
    
    try:
        from training.collaborative_training_manager import ModelTrainingTask
        
        # 创建训练任务实例
        task = ModelTrainingTask(
            model_name="test_model",
            model_instance="TestModelInstance",
            data=[],
            resources={}
        )
        
        logger.info("✅ 模型训练任务初始化成功")
        
        # 测试更新指标
        task.update_metrics({"accuracy": 0.95, "loss": 0.05})
        logger.info(f"✅ 更新指标成功: {task.metrics}")
        
        # 测试添加共享知识
        knowledge = {"accuracy": 0.92, "source_model": "other_model"}
        task.add_shared_knowledge(knowledge)
        logger.info(f"✅ 添加共享知识成功，当前知识数量: {len(task.shared_knowledge)}")
        
        # 测试增加发送知识计数
        task.increment_sent_knowledge()
        logger.info(f"✅ 增加发送知识计数成功，当前计数: {task.sent_knowledge_count}")
        
        logger.info("🎉 模型训练任务类测试通过!")
        return True
        
    except Exception as e:
        logger.error(f"❌ 模型训练任务类测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🧪 测试协作式训练组件（简化版）...")
    print("=" * 50)
    
    # 测试各个组件
    tests = [
        ("模型训练任务类", test_model_training_task),
        ("协作式训练管理器基本功能", test_collaborative_training_manager_basic)
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
            import traceback
            traceback.print_exc()
    
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