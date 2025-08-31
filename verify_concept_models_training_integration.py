#!/usr/bin/env python3
"""
验证概念模型训练集成
"""

import sys
import os
from pathlib import Path
import json

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "apps" / "backend" / "src"))

def verify_training_config():
    """验证训练配置"""
    print("=== 验证训练配置 ===")
    
    # 检查训练配置文件是否存在
    config_path = project_root / "training" / "configs" / "training_preset.json"
    if not config_path.exists():
        print("❌ 训练配置文件不存在")
        return False
    
    # 读取配置文件
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("✅ 训练配置文件加载成功")
    except Exception as e:
        print(f"❌ 训练配置文件加载失败: {e}")
        return False
    
    # 检查概念模型训练场景是否存在
    training_scenarios = config.get('training_scenarios', {})
    concept_models_scenarios = [
        'concept_models_training',
        'environment_simulator_training',
        'causal_reasoning_training',
        'adaptive_learning_training',
        'alpha_deep_model_training'
    ]
    
    for scenario in concept_models_scenarios:
        if scenario in training_scenarios:
            print(f"✅ 训练场景 '{scenario}' 存在")
        else:
            print(f"❌ 训练场景 '{scenario}' 不存在")
            return False
    
    # 检查数据路径配置
    data_paths = config.get('data_paths', {})
    concept_models_data_paths = [
        'concept_models_docs',
        'environment_simulation_data',
        'causal_reasoning_data',
        'adaptive_learning_data',
        'alpha_deep_model_data'
    ]
    
    for data_path in concept_models_data_paths:
        if data_path in data_paths:
            print(f"✅ 数据路径 '{data_path}' 配置存在")
        else:
            print(f"❌ 数据路径 '{data_path}' 配置不存在")
            return False
    
    return True

def verify_training_script():
    """验证训练脚本"""
    print("\n=== 验证训练脚本 ===")
    
    # 检查训练脚本是否存在
    train_script_path = project_root / "training" / "train_model.py"
    if not train_script_path.exists():
        print("❌ 训练脚本不存在")
        return False
    
    # 检查训练脚本是否包含概念模型训练方法
    try:
        with open(train_script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_methods = [
            '_train_concept_models',
            '_train_environment_simulator',
            '_train_causal_reasoning',
            '_train_adaptive_learning',
            '_train_alpha_deep_model'
        ]
        
        for method in required_methods:
            if method in content:
                print(f"✅ 训练方法 '{method}' 存在")
            else:
                print(f"❌ 训练方法 '{method}' 不存在")
                return False
                
        # 检查训练场景处理逻辑
        if 'concept_models' in content:
            print("✅ 概念模型训练场景处理逻辑存在")
        else:
            print("❌ 概念模型训练场景处理逻辑不存在")
            return False
            
        print("✅ 训练脚本验证通过")
        return True
    except Exception as e:
        print(f"❌ 训练脚本验证失败: {e}")
        return False

def verify_document_processing_script():
    """验证文档处理脚本"""
    print("\n=== 验证文档处理脚本 ===")
    
    # 检查文档处理脚本是否存在
    doc_script_path = project_root / "tools" / "prepare_concept_models_training_data.py"
    if not doc_script_path.exists():
        print("❌ 文档处理脚本不存在")
        return False
    
    # 检查脚本是否可导入
    try:
        sys.path.append(str(project_root / "tools"))
        from prepare_concept_models_training_data import main
        print("✅ 文档处理脚本可导入")
        return True
    except Exception as e:
        print(f"❌ 文档处理脚本导入失败: {e}")
        return False

def verify_data_directory():
    """验证数据目录"""
    print("\n=== 验证数据目录 ===")
    
    # 检查概念模型训练数据目录是否存在
    data_dir = project_root / "data" / "concept_models_training_data"
    if data_dir.exists():
        print("✅ 概念模型训练数据目录存在")
        return True
    else:
        print("⚠️  概念模型训练数据目录不存在（将在首次运行时创建）")
        return True

def main():
    """主函数"""
    print("开始验证概念模型训练集成...")
    
    # 验证训练配置
    if not verify_training_config():
        print("\n❌ 训练配置验证失败")
        return False
    
    # 验证训练脚本
    if not verify_training_script():
        print("\n❌ 训练脚本验证失败")
        return False
    
    # 验证文档处理脚本
    if not verify_document_processing_script():
        print("\n❌ 文档处理脚本验证失败")
        return False
    
    # 验证数据目录
    if not verify_data_directory():
        print("\n❌ 数据目录验证失败")
        return False
    
    print("\n🎉 所有验证通过！概念模型训练集成已准备就绪")
    print("\n下一步建议:")
    print("1. 运行 'python tools/prepare_concept_models_training_data.py' 准备训练数据")
    print("2. 运行 'python training/train_model.py --preset concept_models_training' 开始训练")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)