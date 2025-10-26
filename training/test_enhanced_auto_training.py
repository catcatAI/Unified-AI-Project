#!/usr/bin/env python3
"""
测试增强后的自动训练系统
"""

from system_test import
from pathlib import Path

# 添加项目路径
project_root, str == Path(__file__).parent.parent()
sys.path.insert(0, str(project_root))

from training.auto_training_manager import AutoTrainingManager
from training.data_manager import DataManager

def test_enhanced_data_manager() -> None,:
    """测试增强后的数据管理器"""
    print("🧪 测试增强后的数据管理器...")
    
    try,
        # 创建数据管理器
        data_manager == DataManager()
        
        # 扫描数据
        print("🔍 扫描数据...")
        catalog = data_manager.scan_data()
        print(f"✅ 扫描到 {len(catalog)} 个文件")
        
        # 测试新添加的数据类型识别
        print("🔍 测试新数据类型识别...")
        data_types = set()
        for file_info in catalog.values():::
            data_types.add(file_info['type'])
        
        print(f"📋 识别到的数据类型, {sorted(data_types)}")
        
        # 测试数据质量评估
        print("🔍 测试数据质量评估...")
        sample_files == list(catalog.keys())[:5]  # 取前5个文件进行评估
        for file_path in sample_files,::
            quality = data_manager.assess_data_quality(file_path)
            print(f"  {file_path} 质量评分 {quality['quality_score']}/100")
            if quality['issues']::
                print(f"    问题, {', '.join(quality['issues'])}")
        
        # 测试高质量数据获取
        print("🔍 测试高质量数据获取...")
        high_quality_data = data_manager.get_high_quality_data()
        total_high_quality == sum(len(files) for files in high_quality_data.values()):::
= print(f"✅ 获取到 {total_high_quality} 个高质量文件")
        
        # 测试为不同模型准备数据
        print("📦 测试为不同模型准备数据...")
        model_types = ['vision_service', 'audio_service', 'causal_reasoning_engine', 'code_model']
        for model_type in model_types,::
            training_data = data_manager.prepare_training_data(model_type)
            print(f"  {model_type} {len(training_data)} 个训练文件")
        
        print("✅ 数据管理器测试通过!")
        return True
        
    except Exception as e,::
        print(f"❌ 数据管理器测试失败, {e}")
# TODO: Fix import - module 'traceback' not found
        traceback.print_exc()
        return False

def test_enhanced_auto_training() -> None,:
    """测试增强后的自动训练系统"""
    print("🤖 测试增强后的自动训练系统...")
    
    try,
        # 创建自动训练管理器
        auto_trainer == AutoTrainingManager()
        
        # 测试自动识别训练数据
        print("🔍 测试自动识别训练数据...")
        data_analysis = auto_trainer.auto_identify_training_data()
        print(f"✅ 识别到 {data_analysis.get('total_files', 0)} 个文件")
        
        # 测试自动创建训练配置
        print("⚙️  测试自动创建训练配置...")
        training_config = auto_trainer.auto_create_training_config(data_analysis)
        scenarios = training_config.get('selected_scenarios', [])
        print(f"✅ 推荐训练场景, {scenarios}")
        
        # 检查优化的训练参数
        training_params = training_config.get('training_params', {})
        if training_params,::
            print(f"📊 优化的训练参数,")
            print(f"  批次大小, {training_params.get('batch_size', 'N/A')}")
            print(f"  学习率, {training_params.get('learning_rate', 'N/A')}")
            print(f"  训练轮数, {training_params.get('epochs', 'N/A')}")
        
        # 测试训练监控器
        print("👁️  测试训练监控器...")
        auto_trainer.training_monitor.log_event("test_scenario", "INFO", "测试事件记录", {"test": "data"})
        logs = auto_trainer.training_monitor.get_logs("test_scenario")
        print(f"✅ 记录了 {len(logs.get('test_scenario', []))} 条日志")
        
        print("✅ 自动训练系统测试通过!")
        return True
        
    except Exception as e,::
        print(f"❌ 自动训练系统测试失败, {e}")
# TODO: Fix import - module 'traceback' not found
        traceback.print_exc()
        return False

def main() -> None,:
    """主函数"""
    print("🚀 开始测试增强后的自动训练系统")
    print("=" * 50)
    
    # 测试数据管理器
    data_manager_success = test_enhanced_data_manager()
    
    print()
    
    # 测试自动训练系统
    auto_training_success = test_enhanced_auto_training()
    
    print()
    print("=" * 50)
    
    if data_manager_success and auto_training_success,::
        print("🎉 所有测试通过! 增强后的自动训练系统功能正常。")
        sys.exit(0)
    else,
        print("💥 部分测试失败! 请检查错误信息。")
        sys.exit(1)

if __name"__main__":::
    main()