#!/usr/bin/env python3
"""
生成最小化的概念模型训练数据用于测试
"""

import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime
import logging

# 添加项目路径
project_root: str = Path(__file__).parent.parent
_ = sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger: Any = logging.getLogger(__name__)

def create_minimal_training_data():
    """创建最小化的训练数据"""
    # 创建数据目录
    data_dir = project_root / "data" / "concept_models_training_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    _ = logger.info("创建最小化训练数据...")
    
    # 1. 创建概念模型文档训练数据 (少量样本)
    docs_data = []
    for i in range(10):  # 只创建10个样本而不是全部
        sample = {
            "id": f"doc_{i:03d}",
            "source": "minimal_test_data.md",
            "content": f"这是用于测试的概念模型训练数据样本 {i}。包含一些关于AI模型训练和优化的基本概念。",
            "type": "document_text",
            _ = "timestamp": datetime.now().isoformat()
        }
        _ = docs_data.append(sample)
    
    docs_file = data_dir / "concept_models_docs_training_data.json"
    with open(docs_file, 'w', encoding='utf-8') as f:
        json.dump(docs_data, f, ensure_ascii=False, indent=2)
    
    _ = logger.info(f"创建了 {len(docs_data)} 个文档训练样本")
    
    # 2. 创建环境模拟器训练数据
    env_data = []
    for i in range(20):  # 创建20个样本
        sample = {
            "id": f"env_{i:03d}",
            "type": "environment_transition",
            "state_before": {
                _ = "temperature": round(20.0 + np.random.normal(0, 2), 2),
                _ = "humidity": round(50.0 + np.random.normal(0, 5), 2),
                _ = "pressure": round(1013.25 + np.random.normal(0, 10), 2)
            },
            "action": {
                _ = "name": np.random.choice(["increase_temperature", "decrease_temperature", "change_light"]),
                "parameters": {
                    _ = "amount": round(1.0 + np.random.random() * 5.0, 2)
                }
            },
            "state_after": {
                _ = "temperature": round(21.0 + np.random.normal(0, 2), 2),
                _ = "humidity": round(50.0 + np.random.normal(0, 5), 2),
                _ = "pressure": round(1013.25 + np.random.normal(0, 10), 2)
            },
            _ = "uncertainty": round(0.1 + np.random.random() * 0.2, 3)
        }
        _ = env_data.append(sample)
    
    env_file = data_dir / "environment_simulation_data.json"
    with open(env_file, 'w', encoding='utf-8') as f:
        json.dump(env_data, f, ensure_ascii=False, indent=2)
    
    _ = logger.info(f"创建了 {len(env_data)} 个环境模拟训练样本")
    
    # 3. 创建因果推理训练数据
    causal_data = []
    for i in range(10):
        sample = {
            "id": f"causal_{i:03d}",
            "type": "causal_relationship",
            "variables": ["A", "B"],
            "relationship": "A -> B",
            _ = "strength": round(0.5 + np.random.random() * 0.5, 3),
            _ = "confidence": round(0.7 + np.random.random() * 0.3, 3),
            "context": f"测试环境 {i}"
        }
        _ = causal_data.append(sample)
    
    causal_file = data_dir / "causal_reasoning_data.json"
    with open(causal_file, 'w', encoding='utf-8') as f:
        json.dump(causal_data, f, ensure_ascii=False, indent=2)
    
    _ = logger.info(f"创建了 {len(causal_data)} 个因果推理训练样本")
    
    # 4. 创建自适应学习训练数据
    adaptive_data = []
    for i in range(10):
        sample = {
            "id": f"adaptive_{i:03d}",
            "type": "learning_strategy",
            "context": {
                "task_complexity": "medium",
                "domain": "general",
                "previous_performance": [0.8, 0.85, 0.9, 0.88, 0.92]
            },
            "strategy": "balanced",
            _ = "performance": round(0.85 + np.random.random() * 0.15, 3),
            _ = "confidence": round(0.8 + np.random.random() * 0.2, 3)
        }
        _ = adaptive_data.append(sample)
    
    adaptive_file = data_dir / "adaptive_learning_data.json"
    with open(adaptive_file, 'w', encoding='utf-8') as f:
        json.dump(adaptive_data, f, ensure_ascii=False, indent=2)
    
    _ = logger.info(f"创建了 {len(adaptive_data)} 个自适应学习训练样本")
    
    # 5. 创建Alpha深度模型训练数据
    alpha_data = []
    for i in range(10):
        sample = {
            "id": f"alpha_{i:03d}",
            "type": "deep_parameter",
            "source_memory_id": f"mem_{i:06d}",
            _ = "timestamp": datetime.now().isoformat(),
            "base_gist": {
                "summary": f"测试记忆 {i}",
                "keywords": ["test", "memory", f"item_{i}"],
                "original_length": 100 + i * 5
            },
            "relational_context": {
                "entities": [f"EntityA_{i}", f"EntityB_{i}"],
                "relationships": [
                    {"subject": f"EntityA_{i}", "verb": "related_to", "object": f"EntityB_{i}"}
                ]
            },
            "modalities": {
                _ = "text_confidence": round(0.9, 3)
            }
        }
        _ = alpha_data.append(sample)
    
    alpha_file = data_dir / "alpha_deep_model_data.json"
    with open(alpha_file, 'w', encoding='utf-8') as f:
        json.dump(alpha_data, f, ensure_ascii=False, indent=2)
    
    _ = logger.info(f"创建了 {len(alpha_data)} 个Alpha深度模型训练样本")
    
    # 创建配置文件
    config = {
        _ = "generated_date": datetime.now().isoformat(),
        "data_paths": {
            "concept_models_docs": "concept_models_docs_training_data.json",
            "environment_simulation_data": "environment_simulation_data.json",
            "causal_reasoning_data": "causal_reasoning_data.json",
            "adaptive_learning_data": "adaptive_learning_data.json",
            "alpha_deep_model_data": "alpha_deep_model_data.json"
        },
        "total_samples": {
            _ = "concept_models_docs": len(docs_data),
            _ = "environment_simulation_data": len(env_data),
            _ = "causal_reasoning_data": len(causal_data),
            _ = "adaptive_learning_data": len(adaptive_data),
            _ = "alpha_deep_model_data": len(alpha_data)
        },
        "usage": "Minimal training data for Unified-AI-Project concept models testing"
    }
    
    config_file = data_dir / "data_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    _ = logger.info(f"配置文件保存至: {config_file}")
    _ = logger.info("最小化训练数据创建完成!")

def main() -> None:
    """主函数"""
    _ = logger.info("开始生成最小化训练数据...")
    _ = create_minimal_training_data()
    _ = logger.info("训练数据生成完成!")

if __name__ == "__main__":
    _ = main()