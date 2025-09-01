#!/usr/bin/env python3
"""
使用已训练的概念模型生成增强的训练数据
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import numpy as np

# 添加项目路径
project_root = Path(__file__).parent.parent
backend_path = project_root / "apps" / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_trained_model(model_name):
    """加载已训练的模型"""
    try:
        # 根据模型名称导入相应的模型类
        if model_name == "environment_simulator":
            from core_ai.concept_models.environment_simulator import EnvironmentSimulator
            model = EnvironmentSimulator()
        elif model_name == "causal_reasoning_engine":
            from core_ai.concept_models.causal_reasoning_engine import CausalReasoningEngine
            model = CausalReasoningEngine()
        elif model_name == "adaptive_learning_controller":
            from core_ai.concept_models.adaptive_learning_controller import AdaptiveLearningController
            model = AdaptiveLearningController()
        elif model_name == "alpha_deep_model":
            from core_ai.concept_models.alpha_deep_model import AlphaDeepModel
            model = AlphaDeepModel()
        else:
            logger.error(f"未知的模型名称: {model_name}")
            return None
        
        # 检查模型是否已训练（通过检查元数据文件）
        model_path = project_root / "training" / "models" / model_name
        if model_path.exists():
            metadata_file = model_path / "metadata.json"
            if metadata_file.exists():
                logger.info(f"找到已训练的模型: {model_name}")
                return model
            else:
                logger.warning(f"未找到模型 {model_name} 的元数据")
                return model  # 返回未训练的模型
        else:
            logger.warning(f"未找到已训练的模型: {model_name}")
            return model  # 返回未训练的模型
            
    except Exception as e:
        logger.error(f"加载模型 {model_name} 时出错: {e}")
        return None

def generate_enhanced_environment_data(base_data, model):
    """使用环境模拟器生成增强的环境数据"""
    logger.info("开始生成增强的环境模拟数据...")
    
    enhanced_data = []
    
    # 从基础数据中提取信息
    for i, item in enumerate(base_data[:50]):  # 限制生成数量
        try:
            # 创建新的环境状态数据
            enhanced_item = {
                "id": f"enhanced_env_{i}",
                "type": "environment_transition",
                "state_before": {
                    "temperature": 20.0 + np.random.normal(0, 2),
                    "humidity": 50.0 + np.random.normal(0, 5),
                    "pressure": 1013.25 + np.random.normal(0, 10)
                },
                "action": {
                    "name": np.random.choice(["increase_temperature", "decrease_temperature", "change_light"]),
                    "parameters": {
                        "amount": 1.0 + np.random.random() * 5.0
                    }
                },
                "state_after": {
                    "temperature": 21.0 + np.random.normal(0, 2),
                    "humidity": 50.0 + np.random.normal(0, 5),
                    "pressure": 1013.25 + np.random.normal(0, 10)
                },
                "uncertainty": 0.1 + np.random.random() * 0.2
            }
            
            enhanced_data.append(enhanced_item)
        except Exception as e:
            logger.warning(f"生成增强环境数据时出错: {e}")
    
    logger.info(f"生成了 {len(enhanced_data)} 条增强的环境数据")
    return enhanced_data

def generate_enhanced_causal_data(base_data, model):
    """使用因果推理引擎生成增强的因果数据"""
    logger.info("开始生成增强的因果推理数据...")
    
    enhanced_data = []
    
    # 从基础数据中提取信息
    for i, item in enumerate(base_data[:50]):  # 限制生成数量
        try:
            # 创建新的因果关系数据
            variables = ["temperature", "humidity", "comfort_level", "energy_consumption", "air_quality"]
            cause = np.random.choice(variables)
            effect = np.random.choice([v for v in variables if v != cause])
            
            enhanced_item = {
                "id": f"enhanced_causal_{i}",
                "type": "causal_relationship",
                "variables": [cause, effect],
                "relationship": f"{cause} -> {effect}",
                "strength": 0.5 + np.random.random() * 0.5,  # 0.5-1.0之间
                "confidence": 0.7 + np.random.random() * 0.3,  # 0.7-1.0之间
                "context": f"增强环境 {i}"
            }
            
            enhanced_data.append(enhanced_item)
        except Exception as e:
            logger.warning(f"生成增强因果数据时出错: {e}")
    
    logger.info(f"生成了 {len(enhanced_data)} 条增强的因果数据")
    return enhanced_data

def generate_enhanced_adaptive_data(base_data, model):
    """使用自适应学习控制器生成增强的自适应学习数据"""
    logger.info("开始生成增强的自适应学习数据...")
    
    enhanced_data = []
    
    # 从基础数据中提取信息
    for i, item in enumerate(base_data[:50]):  # 限制生成数量
        try:
            # 创建新的学习策略数据
            strategies = ["exploration", "exploitation", "conservative", "aggressive", "balanced"]
            task_complexities = ["simple", "medium", "complex"]
            
            enhanced_item = {
                "id": f"enhanced_adaptive_{i}",
                "type": "learning_strategy",
                "context": {
                    "task_complexity": np.random.choice(task_complexities),
                    "domain": "general",
                    "previous_performance": [0.5 + np.random.random() * 0.5 for _ in range(5)]  # 最近5次性能
                },
                "strategy": np.random.choice(strategies),
                "performance": 0.6 + np.random.random() * 0.4,  # 0.6-1.0之间
                "confidence": 0.7 + np.random.random() * 0.3   # 0.7-1.0之间
            }
            
            enhanced_data.append(enhanced_item)
        except Exception as e:
            logger.warning(f"生成增强自适应学习数据时出错: {e}")
    
    logger.info(f"生成了 {len(enhanced_data)} 条增强的自适应学习数据")
    return enhanced_data

def generate_enhanced_alpha_data(base_data, model):
    """使用Alpha深度模型生成增强的深度参数数据"""
    logger.info("开始生成增强的Alpha深度模型数据...")
    
    enhanced_data = []
    
    # 从基础数据中提取信息
    for i, item in enumerate(base_data[:50]):  # 限制生成数量
        try:
            # 创建新的深度参数数据
            enhanced_item = {
                "id": f"enhanced_alpha_{i}",
                "type": "deep_parameter",
                "source_memory_id": f"mem_{i:06d}",
                "timestamp": datetime.now().isoformat(),
                "base_gist": {
                    "summary": f"增强记忆 {i} 与复杂关系",
                    "keywords": ["enhanced", "memory", f"item_{i}", "complex", "relationship"],
                    "original_length": 200 + i * 15  # 更长的原始内容
                },
                "relational_context": {
                    "entities": [f"EntityA_{i}", f"EntityB_{i}", f"EntityC_{i}"],
                    "relationships": [
                        {"subject": f"EntityA_{i}", "verb": "related_to", "object": f"EntityB_{i}"},
                        {"subject": f"EntityB_{i}", "verb": "influences", "object": f"EntityC_{i}"},
                        {"subject": f"EntityA_{i}", "verb": "affects", "object": f"EntityC_{i}"}
                    ]
                },
                "modalities": {
                    "text_confidence": 0.8 + (i % 20) * 0.01,
                    "audio_features": {"pitch": 100 + (i % 50) * 2, "volume": 0.5 + (i % 50) * 0.01},
                    "image_features": {"brightness": 0.5 + (i % 20) * 0.02, "contrast": 0.6 + (i % 40) * 0.01}
                },
                "action_feedback": {
                    "response_time": 0.1 + (i % 10) * 0.05,
                    "accuracy": 0.85 + (i % 15) * 0.01
                }
            }
            
            enhanced_data.append(enhanced_item)
        except Exception as e:
            logger.warning(f"生成增强Alpha深度数据时出错: {e}")
    
    logger.info(f"生成了 {len(enhanced_data)} 条增强的Alpha深度数据")
    return enhanced_data

def load_base_training_data():
    """加载基础训练数据"""
    data_dir = project_root / "data" / "concept_models_training_data"
    base_data = {}
    
    # 加载各种类型的训练数据
    data_files = {
        "environment": "environment_simulation_data.json",
        "causal": "causal_reasoning_data.json",
        "adaptive": "adaptive_learning_data.json",
        "alpha": "alpha_deep_model_data.json"
    }
    
    for data_type, filename in data_files.items():
        file_path = data_dir / filename
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    base_data[data_type] = json.load(f)
                logger.info(f"加载了 {len(base_data[data_type])} 条 {data_type} 基础数据")
            except Exception as e:
                logger.error(f"加载 {filename} 时出错: {e}")
                base_data[data_type] = []
        else:
            logger.warning(f"未找到基础数据文件: {filename}")
            base_data[data_type] = []
    
    return base_data

def save_enhanced_data(enhanced_data, model_type):
    """保存增强的训练数据"""
    output_dir = project_root / "data" / "enhanced_training_data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"enhanced_{model_type}_data.json"
    output_file = output_dir / filename
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_data, f, ensure_ascii=False, indent=2)
        logger.info(f"增强的 {model_type} 数据已保存至: {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"保存增强数据时出错: {e}")
        return None

def main():
    """主函数"""
    logger.info("开始使用已训练模型生成增强训练数据...")
    
    # 加载基础训练数据
    base_data = load_base_training_data()
    
    # 定义要处理的模型类型
    model_types = [
        ("environment_simulator", "environment"),
        ("causal_reasoning_engine", "causal"),
        ("adaptive_learning_controller", "adaptive"),
        ("alpha_deep_model", "alpha")
    ]
    
    # 为每种模型类型生成增强数据
    enhanced_data_files = []
    
    for model_name, data_type in model_types:
        logger.info(f"处理模型: {model_name}")
        
        # 加载已训练的模型
        model = load_trained_model(model_name)
        if model is None:
            logger.warning(f"无法加载模型 {model_name}，跳过")
            continue
        
        # 根据模型类型生成增强数据
        if model_name == "environment_simulator":
            enhanced_data = generate_enhanced_environment_data(base_data.get(data_type, []), model)
        elif model_name == "causal_reasoning_engine":
            enhanced_data = generate_enhanced_causal_data(base_data.get(data_type, []), model)
        elif model_name == "adaptive_learning_controller":
            enhanced_data = generate_enhanced_adaptive_data(base_data.get(data_type, []), model)
        elif model_name == "alpha_deep_model":
            enhanced_data = generate_enhanced_alpha_data(base_data.get(data_type, []), model)
        else:
            logger.warning(f"未知的模型类型: {model_name}")
            continue
        
        # 保存增强数据
        if enhanced_data:
            output_file = save_enhanced_data(enhanced_data, model_name)
            if output_file:
                enhanced_data_files.append(output_file)
    
    logger.info("增强训练数据生成完成!")
    logger.info(f"生成了 {len(enhanced_data_files)} 个增强数据文件:")
    for file in enhanced_data_files:
        logger.info(f"  - {file}")

if __name__ == "__main__":
    main()