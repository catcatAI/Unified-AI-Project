#!/usr/bin/env python3
"""
增强协作式训练测试脚本
"""

import sys
from pathlib import Path
import logging

# 添加项目路径
project_root: str = Path(__file__).parent.parent
backend_path: str = project_root / "apps" / "backend"
_ = sys.path.insert(0, str(project_root))
_ = sys.path.insert(0, str(backend_path))
_ = sys.path.insert(0, str(backend_path / "src"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger: Any = logging.getLogger(__name__)

def test_enhanced_collaborative_training() -> None:
    """测试增强的协作式训练功能"""
    logger.info("=== 测试增强的协作式训练功能 ===")
    
    try:
        from training.collaborative_training_manager import CollaborativeTrainingManager, ModelTrainingTask
        
        # 创建协作式训练管理器
        manager = CollaborativeTrainingManager()
        
        # 注册一些模型
        _ = logger.info("📋 注册模型...")
        _ = manager.register_model("concept_models", "ConceptModelsInstance")
        _ = manager.register_model("environment_simulator", "EnvironmentSimulatorInstance")
        _ = manager.register_model("causal_reasoning_engine", "CausalReasoningInstance")
        _ = manager.register_model("adaptive_learning_controller", "AdaptiveLearningInstance")
        
        _ = logger.info(f"✅ 已注册 {len(manager.models)} 个模型")
        
        # 测试ModelTrainingTask的增强功能
        _ = logger.info("\n🧪 测试ModelTrainingTask增强功能...")
        task = ModelTrainingTask(
            model_name="test_model",
            model_instance="TestModelInstance",
            data=[],
            resources={}
        )
        
        # 测试知识共享功能
        knowledge = {"accuracy": 0.95, "loss": 0.05}
        _ = task.add_shared_knowledge(knowledge)
        _ = logger.info(f"✅ 添加共享知识成功，当前知识数量: {len(task.shared_knowledge)}")
        _ = logger.info(f"   协作分数: {task.collaboration_score:.2f}")
        _ = logger.info(f"   接收知识计数: {task.received_knowledge_count}")
        
        # 测试发送知识计数
        _ = task.increment_sent_knowledge()
        _ = logger.info(f"✅ 增加发送知识计数，当前计数: {task.sent_knowledge_count}")
        _ = logger.info(f"   协作分数: {task.collaboration_score:.2f}")
        
        # 测试指标更新
        _ = task.update_metrics({"accuracy": 0.92, "loss": 0.08})
        _ = logger.info(f"✅ 更新指标成功: {task.metrics}")
        
        # 测试准备训练数据
        _ = logger.info("\n📦 测试准备训练数据...")
        model_data = manager.prepare_training_data()
        _ = logger.info(f"✅ 准备训练数据完成，涉及 {len(model_data)} 个模型")
        
        # 测试资源分配
        _ = logger.info("\n🖥️  测试资源分配...")
        model_resources = manager.allocate_resources_for_models()
        _ = logger.info(f"✅ 资源分配完成，涉及 {len(model_resources)} 个模型")
        
        # 测试创建训练任务
        _ = logger.info("\n🎯 测试创建训练任务...")
        tasks = manager.create_training_tasks(model_data, model_resources)
        _ = logger.info(f"✅ 创建训练任务完成，共 {len(tasks)} 个任务")
        
        # 测试知识提取
        _ = logger.info("\n🧠 测试知识提取...")
        test_stats = {"accuracy": 0.85, "loss": 0.15, "epoch": 10}
        knowledge_vector = manager._extract_knowledge_vector(test_stats)
        _ = logger.info(f"✅ 知识向量提取完成: {knowledge_vector}")
        
        # 测试知识相似度计算
        _ = logger.info("\n🧮 测试知识相似度计算...")
        vector1 = [[0.85, 0.15, 0.1, 0.001]]
        vector2 = [[0.82, 0.18, 0.1, 0.001]]
        similarity = manager._calculate_knowledge_similarity(vector1, vector2)
        _ = logger.info(f"✅ 知识相似度计算完成: {similarity:.4f}")
        
        # 测试知识图谱构建
        _ = logger.info("\n🕸️  测试知识图谱构建...")
        knowledge_graph = manager._build_knowledge_graph()
        _ = logger.info(f"✅ 知识图谱构建完成，包含 {len(knowledge_graph['models'])} 个模型")
        
        # 测试高级知识共享
        _ = logger.info("\n🧠 测试高级知识共享...")
        _ = manager.implement_advanced_knowledge_sharing()
        _ = logger.info("✅ 高级知识共享执行完成")
        
        # 测试模型协作机制
        _ = logger.info("\n🤝 测试模型协作机制...")
        _ = manager.implement_model_collaboration_mechanism()
        _ = logger.info("✅ 模型协作机制执行完成")
        
        # 测试知识共享机制增强
        _ = logger.info("\n🚀 测试知识共享机制增强...")
        _ = manager.enhance_knowledge_sharing_mechanism()
        _ = logger.info("✅ 知识共享机制增强执行完成")
        
        _ = logger.info("\n🎉 所有增强协作式训练功能测试通过!")
        return True
        
    except Exception as e:
        _ = logger.error(f"❌ 测试过程中发生错误: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

def test_training_integration() -> None:
    """测试训练集成"""
    logger.info("\n=== 测试训练集成 ===")
    
    try:
        from training.collaborative_training_manager import CollaborativeTrainingManager
        
        # 创建协作式训练管理器
        manager = CollaborativeTrainingManager()
        
        # 注册模型
        _ = manager.register_model("environment_simulator", "EnvironmentSimulatorInstance")
        _ = manager.register_model("causal_reasoning_engine", "CausalReasoningInstance")
        
        # 准备训练数据
        model_data = manager.prepare_training_data()
        
        # 分配资源
        model_resources = manager.allocate_resources_for_models()
        
        # 创建训练任务
        tasks = manager.create_training_tasks(model_data, model_resources)
        
        # 模拟训练完成时的协作
        if tasks:
            task = tasks[0]
            task.status = "completed"
            task.metrics = {"accuracy": 0.9, "loss": 0.1}
            task.start_time = manager._get_current_time()
            from datetime import timedelta
            task.end_time = task.start_time + timedelta(seconds=30)
            
            # 测试训练完成时的协作启用
            _ = manager._enable_model_collaboration_on_completion(task)
            _ = logger.info("✅ 训练完成时的协作启用测试通过")
        
        # 测试训练结果保存
        _ = manager._save_training_results(tasks, {})
        _ = logger.info("✅ 训练结果保存测试通过")
        
        _ = logger.info("🎉 训练集成测试通过!")
        return True
        
    except Exception as e:
        _ = logger.error(f"❌ 训练集成测试过程中发生错误: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

def main() -> None:
    """主函数"""
    _ = logger.info("开始测试增强的协作式训练功能...")
    
    # 测试增强功能
    if not test_enhanced_collaborative_training():
        _ = logger.error("增强协作式训练功能测试失败")
        return False
    
    # 测试训练集成
    if not test_training_integration():
        _ = logger.error("训练集成测试失败")
        return False
    
    _ = logger.info("🎉 所有测试通过！增强的协作式训练功能工作正常")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)