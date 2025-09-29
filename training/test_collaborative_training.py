#!/usr/bin/env python3
"""
协作式训练测试脚本
"""

import sys
from pathlib import Path

# 添加项目路径
project_root: str = Path(__file__).parent.parent
backend_path: str = project_root / "apps" / "backend"
_ = sys.path.insert(0, str(project_root))
_ = sys.path.insert(0, str(backend_path))
_ = sys.path.insert(0, str(backend_path / "src"))

import logging
# 使用绝对导入而不是相对导入
from training.collaborative_training_manager import CollaborativeTrainingManager
from training.data_manager import DataManager
from training.resource_manager import ResourceManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger: Any = logging.getLogger(__name__)

def test_data_manager() -> None:
    """测试数据管理器"""
    _ = logger.info("🔍 测试数据管理器...")
    
    try:
        data_manager = DataManager()
        
        # 扫描数据
        catalog = data_manager.scan_data()
        _ = logger.info(f"   扫描到 {len(catalog)} 个文件")
        
        # 获取数据统计
        stats = data_manager.get_data_statistics()
        _ = logger.info(f"   总文件数: {stats['total_files']}")
        _ = logger.info(f"   总大小: {stats['total_size'] / (1024*1024):.2f} MB")
        
        # 为概念模型准备数据
        concept_data = data_manager.prepare_training_data("concept_models")
        _ = logger.info(f"   为概念模型准备了 {len(concept_data)} 个训练文件")
        
        _ = logger.info("✅ 数据管理器测试通过")
        return True
    except Exception as e:
        _ = logger.error(f"❌ 数据管理器测试失败: {e}")
        return False

def test_resource_manager() -> None:
    """测试资源管理器"""
    _ = logger.info("🖥️  测试资源管理器...")
    
    try:
        resource_manager = ResourceManager()
        
        # 获取系统资源
        resources = resource_manager.get_system_resources()
        _ = logger.info(f"   CPU使用率: {resources['cpu']['usage_percent']:.1f}%")
        _ = logger.info(f"   内存使用率: {resources['memory']['usage_percent']:.1f}%")
        _ = logger.info(f"   GPU数量: {len(resources['gpu'])}")
        
        # 测试模型资源需求
        requirements = resource_manager.get_model_resource_requirements("concept_models")
        _ = logger.info(f"   概念模型资源需求: {requirements}")
        
        # 尝试分配资源
        allocation = resource_manager.allocate_resources(requirements, "concept_models")
        if allocation:
            _ = logger.info("✅ 资源分配成功")
        else:
            _ = logger.warning("⚠️  资源分配失败")
        
        _ = logger.info("✅ 资源管理器测试完成")
        return True
    except Exception as e:
        _ = logger.error(f"❌ 资源管理器测试失败: {e}")
        return False

def test_collaborative_training_manager() -> None:
    """测试协作式训练管理器"""
    _ = logger.info("🔄 测试协作式训练管理器...")
    
    try:
        manager = CollaborativeTrainingManager()
        
        # 注册一些模型
        _ = manager.register_model("concept_models", "ConceptModelsInstance")
        _ = manager.register_model("environment_simulator", "EnvironmentSimulatorInstance")
        
        # 显示注册的模型
        _ = logger.info(f"   已注册 {len(manager.models)} 个模型")
        
        # 准备训练数据
        model_data = manager.prepare_training_data()
        _ = logger.info(f"   为 {len(model_data)} 个模型准备了训练数据")
        
        # 分配资源
        model_resources = manager.allocate_resources_for_models()
        _ = logger.info(f"   为 {len(model_resources)} 个模型分配了资源")
        
        # 获取训练状态
        status = manager.get_training_status()
        _ = logger.info(f"   训练状态: {status['is_training']}")
        
        _ = logger.info("✅ 协作式训练管理器测试完成")
        return True
    except Exception as e:
        _ = logger.error(f"❌ 协作式训练管理器测试失败: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

def main() -> None:
    """主函数"""
    _ = print("🧪 测试协作式训练组件...")
    print("=" * 50)
    
    # 测试各个组件
    tests = [
        _ = ("数据管理器", test_data_manager),
        _ = ("资源管理器", test_resource_manager),
        _ = ("协作式训练管理器", test_collaborative_training_manager)
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