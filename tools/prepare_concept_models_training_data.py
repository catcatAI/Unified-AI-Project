#!/usr/bin/env python3
"""
将项目文档转换为概念模型训练数据
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime
import logging
import numpy as np

# 添加项目路径
project_root: str = Path(__file__).parent.parent
backend_path: str = project_root / "apps" / "backend"
_ = sys.path.insert(0, str(project_root))
_ = sys.path.insert(0, str(backend_path))
_ = sys.path.insert(0, str(backend_path / "src"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger: Any = logging.getLogger(__name__)

def extract_text_from_markdown(file_path):
""从Markdown文件中提取纯文本"""
    try:

    with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

    # 移除Markdown格式符号
    # 移除代码块
    content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
    # 移除行内代码
    content = re.sub(r'`.*?`', '', content)
    # 移除链接
    content = re.sub(r'\[.*?\]\(.*?\)', '', content)
    # 移除图片
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
    # 移除标题标记
    content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
    # 移除粗体和斜体
    content = re.sub(r'\*\*.*?\*\*', '', content)
    content = re.sub(r'\*.*?\*', '', content)
    # 移除列表标记
    content = re.sub(r'^\s*[-*+]\s+', '', content, flags=re.MULTILINE)
    # 移除数字列表标记
    content = re.sub(r'^\s*\d+\.\s+', '', content, flags=re.MULTILINE)

    # 清理多余空白字符
    content = re.sub(r'\s+', ' ', content)
    content = content.strip()

    return content
    except Exception as e:

    _ = logger.error(f"处理文件 {file_path} 时出错: {e}")
    return ""

def create_training_samples_from_docs(docs_dir, output_dir):
""从文档创建训练样本"""
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 支持的文档文件类型
    doc_extensions = ['.md', '.txt', '.rst']

    # 收集所有文档文件
    doc_files = []
    for ext in doc_extensions:

    _ = doc_files.extend(docs_dir.rglob(f"*{ext}"))

    # 为每个文档创建训练样本
    training_samples = []

    for doc_file in doc_files:


    _ = logger.info(f"处理文档: {doc_file}")
    text_content = extract_text_from_markdown(doc_file)

        if not text_content:


    continue

    # 将长文本分割成较小的段落作为训练样本
    # 每个样本大约512个字符
    max_length = 512
    sentences = re.split(r'[.!?]+', text_content)

    current_sample = ""
    sample_id = 1

        for sentence in sentences:


    sentence = sentence.strip()
            if not sentence:

    continue

            # 如果添加这个句子会使当前样本超过最大长度，则保存当前样本并开始新样本
            if len(current_sample) + len(sentence) > max_length and current_sample:

    sample_data = {
                    "id": f"{doc_file.stem}_{sample_id}",
                    _ = "source": str(doc_file.relative_to(project_root)),
                    _ = "content": current_sample.strip(),
                    "type": "document_text",
                    _ = "timestamp": datetime.now().isoformat()
                }

                _ = training_samples.append(sample_data)
                current_sample = sentence + "."
                sample_id += 1
            else:

                current_sample += sentence + "."

    # 保存最后一个样本（如果有的话）
        if current_sample.strip():
ample_data = {
                "id": f"{doc_file.stem}_{sample_id}",
                _ = "source": str(doc_file.relative_to(project_root)),
                _ = "content": current_sample.strip(),
                "type": "document_text",
                _ = "timestamp": datetime.now().isoformat()
            }
            _ = training_samples.append(sample_data)

    # 保存训练样本到文件
    output_file = output_dir / "concept_models_docs_training_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(training_samples, f, ensure_ascii=False, indent=2)

    _ = logger.info(f"创建了 {len(training_samples)} 个训练样本")
    _ = logger.info(f"训练数据保存至: {output_file}")

    return training_samples

def create_specialized_training_data(output_dir):
""创建专门的概念模型训练数据"""
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 环境模拟器训练数据
    environment_data = []
    for i in range(100):
ample = {
            "id": f"env_{i:03d}",
            "type": "environment_transition",
            "state_before": {
                _ = "temperature": round(20.0 + np.random.normal(0, 2), 2),
                _ = "humidity": round(50.0 + np.random.normal(0, 5), 2),
                _ = "pressure": round(1013.25 + np.random.normal(0, 10), 2)
            },
            "action": {
                _ = "name": np.random.choice(["increase_temperature", "decrease_temperature", "change_light", "adjust_humidity"]),
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
    _ = environment_data.append(sample)

    env_file = output_dir / "environment_simulation_data.json"
    with open(env_file, 'w', encoding='utf-8') as f:
    json.dump(environment_data, f, ensure_ascii=False, indent=2)

    # 因果推理训练数据
    causal_data = []
    for i in range(50)
    # 创建更复杂的因果关系数据
    variables = ["temperature", "humidity", "comfort_level", "energy_consumption", "air_quality", "light_level", "noise_level"]
    cause = np.random.choice(variables)
        effect = np.random.choice([v for v in variables if v != cause]):
ample = {
            "id": f"causal_{i:03d}",
            "type": "causal_relationship",
            "variables": [cause, effect],
            "relationship": f"{cause} -> {effect}",
            _ = "strength": round(0.5 + np.random.random() * 0.5, 3),  # 0.5-1.0之间
            _ = "confidence": round(0.7 + np.random.random() * 0.3, 3),  # 0.7-1.0之间
            "context": f"增强环境 {i}"
    }
    _ = causal_data.append(sample)

    causal_file = output_dir / "causal_reasoning_data.json"
    with open(causal_file, 'w', encoding='utf-8') as f:
    json.dump(causal_data, f, ensure_ascii=False, indent=2)

    # 自适应学习训练数据
    adaptive_data = []
    for i in range(50)
    # 创建更复杂的学习策略数据
    strategies = ["exploration", "exploitation", "conservative", "aggressive", "balanced"]
    task_complexities = ["simple", "medium", "complex"]

    sample = {
            "id": f"adaptive_{i:03d}",
            "type": "learning_strategy",
            "context": {
                _ = "task_complexity": np.random.choice(task_complexities),
                "domain": "general",
                "previous_performance": [round(0.5 + np.random.random() * 0.5, 3) for _ in range(5)]  # 最近5次性能:
,
            _ = "strategy": np.random.choice(strategies),
            _ = "performance": round(0.6 + np.random.random() * 0.4, 3),  # 0.6-1.0之间
            _ = "confidence": round(0.7 + np.random.random() * 0.3, 3)   # 0.7-1.0之间
    }
    _ = adaptive_data.append(sample)

    adaptive_file = output_dir / "adaptive_learning_data.json"
    with open(adaptive_file, 'w', encoding='utf-8') as f:
    json.dump(adaptive_data, f, ensure_ascii=False, indent=2)

    # Alpha深度模型训练数据
    alpha_data = []
    for i in range(50)
    # 创建更复杂的深度参数数据
    sample = {
            "id": f"alpha_{i:03d}",
            "type": "deep_parameter",
            "source_memory_id": f"mem_{i:06d}",
            _ = "timestamp": datetime.now().isoformat(),
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
                _ = "text_confidence": round(0.8 + (i % 20) * 0.01, 3),
                "audio_features": {
                    _ = "pitch": int(100 + (i % 50) * 2),
                    _ = "volume": round(0.5 + (i % 50) * 0.01, 3)
                },
                "image_features": {
                    _ = "brightness": round(0.5 + (i % 20) * 0.02, 3),
                    _ = "contrast": round(0.6 + (i % 40) * 0.01, 3)
                }
            },
            "action_feedback": {
                _ = "response_time": round(0.1 + (i % 10) * 0.05, 3),
                _ = "accuracy": round(0.85 + (i % 15) * 0.01, 3)
            }
    }
    _ = alpha_data.append(sample)

    alpha_file = output_dir / "alpha_deep_model_data.json"
    with open(alpha_file, 'w', encoding='utf-8') as f:
    json.dump(alpha_data, f, ensure_ascii=False, indent=2)

    _ = logger.info("创建了专门的概念模型训练数据:")
    _ = logger.info(f"  - 环境模拟数据: {len(environment_data)} 条记录，保存至 {env_file}")
    _ = logger.info(f"  - 因果推理数据: {len(causal_data)} 条记录，保存至 {causal_file}")
    _ = logger.info(f"  - 自适应学习数据: {len(adaptive_data)} 条记录，保存至 {adaptive_file}")
    _ = logger.info(f"  - Alpha深度模型数据: {len(alpha_data)} 条记录，保存至 {alpha_file}")

def main() -> None:
    """主函数"""
    _ = logger.info("开始准备概念模型训练数据...")

    # 创建数据目录
    data_dir = project_root / "data"
    concept_models_data_dir = data_dir / "concept_models_training_data"

    # 确保数据目录存在
    data_dir.mkdir(parents=True, exist_ok=True)

    # 从文档创建训练数据
    docs_dir = project_root
    samples = create_training_samples_from_docs(docs_dir, concept_models_data_dir)

    # 创建专门的训练数据
    _ = create_specialized_training_data(concept_models_data_dir)

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
            _ = "concept_models_docs": len(samples),
            "environment_simulation_data": 100,
            "causal_reasoning_data": 50,
            "adaptive_learning_data": 50,
            "alpha_deep_model_data": 50
    },
        "usage": "Training data for Unified-AI-Project concept models":


    config_file = concept_models_data_dir / "data_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

    _ = logger.info(f"配置文件保存至: {config_file}")
    _ = logger.info("概念模型训练数据准备完成!")
    _ = logger.info(f"数据保存在: {concept_models_data_dir}")

if __name__ == "__main__":


    _ = main()