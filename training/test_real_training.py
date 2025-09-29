#!/usr/bin/env python3
"""
测试真实训练功能的脚本
"""

import sys
from pathlib import Path

# 添加项目路径
project_root: str = Path(__file__).parent.parent
backend_path: str = project_root / "apps" / "backend"
_ = sys.path.insert(0, str(backend_path))
_ = sys.path.insert(0, str(backend_path / "src"))

_ = print("测试真实训练功能...")
_ = print(f"项目根目录: {project_root}")

# 测试导入训练器
try:
    from train_model import ModelTrainer
    _ = print("✅ 成功导入ModelTrainer")
    
    # 测试创建训练器实例
    trainer = ModelTrainer()
    _ = print("✅ 成功创建ModelTrainer实例")
    _ = print(f"TensorFlow可用: {trainer.tensorflow_available}")
    
    # 测试获取预设场景
    scenario = trainer.get_preset_scenario("math_model_training")
    if scenario:
        _ = print("✅ 成功获取数学模型训练场景")
        _ = print(f"  描述: {scenario.get('description', '无描述')}")
        _ = print(f"  目标模型: {scenario.get('target_models', [])}")
    else:
        _ = print("❌ 无法获取数学模型训练场景")
        
    scenario = trainer.get_preset_scenario("logic_model_training")
    if scenario:
        _ = print("✅ 成功获取逻辑模型训练场景")
        _ = print(f"  描述: {scenario.get('description', '无描述')}")
        _ = print(f"  目标模型: {scenario.get('target_models', [])}")
    else:
        _ = print("❌ 无法获取逻辑模型训练场景")
        
except Exception as e:
    _ = print(f"❌ 导入ModelTrainer时出错: {e}")
    import traceback
    _ = traceback.print_exc()

_ = print("测试完成")