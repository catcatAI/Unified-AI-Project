#!/usr/bin/env python3
"""
将项目文档转换为概念模型训练数据
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
import logging

# 添加项目路径
project_root = Path(__file__).parent.parent
backend_path = project_root / "apps" / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_text_from_markdown(file_path):
    """从Markdown文件中提取纯文本"""
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
        logger.error(f"处理文件 {file_path} 时出错: {e}")
        return ""

def create_training_samples_from_docs(docs_dir, output_dir):
    """从文档创建训练样本"""
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 支持的文档文件类型
    doc_extensions = ['.md', '.txt', '.rst']
    
    # 收集所有文档文件
    doc_files = []
    for ext in doc_extensions:
        doc_files.extend(docs_dir.rglob(f"*{ext}"))
    
    # 为每个文档创建训练样本
    training_samples = []
    
    for doc_file in doc_files:
        logger.info(f"处理文档: {doc_file}")
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
                    "source": str(doc_file.relative_to(project_root)),
                    "content": current_sample.strip(),
                    "type": "document_text",
                    "timestamp": datetime.now().isoformat()
                }
                
                training_samples.append(sample_data)
                current_sample = sentence + "."
                sample_id += 1
            else:
                current_sample += sentence + "."
        
        # 保存最后一个样本（如果有的话）
        if current_sample.strip():
            sample_data = {
                "id": f"{doc_file.stem}_{sample_id}",
                "source": str(doc_file.relative_to(project_root)),
                "content": current_sample.strip(),
                "type": "document_text",
                "timestamp": datetime.now().isoformat()
            }
            training_samples.append(sample_data)
    
    # 保存训练样本到文件
    output_file = output_dir / "concept_models_docs_training_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(training_samples, f, ensure_ascii=False, indent=2)
    
    logger.info(f"创建了 {len(training_samples)} 个训练样本")
    logger.info(f"训练数据保存至: {output_file}")
    
    return training_samples

def create_specialized_training_data(output_dir):
    """创建专门的概念模型训练数据"""
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 环境模拟器训练数据
    environment_data = []
    for i in range(100):
        sample = {
            "id": f"env_{i}",
            "type": "environment_transition",
            "state_before": {"temperature": 20.0 + i * 0.1, "humidity": 50.0 + i * 0.2},
            "action": {"name": "increase_temperature", "parameters": {"amount": 1.0 + (i % 5) * 0.5}},
            "state_after": {"temperature": 21.0 + i * 0.1, "humidity": 50.0 + i * 0.2},
            "uncertainty": 0.1 + (i % 10) * 0.01
        }
        environment_data.append(sample)
    
    env_file = output_dir / "environment_simulation_data.json"
    with open(env_file, 'w', encoding='utf-8') as f:
        json.dump(environment_data, f, ensure_ascii=False, indent=2)
    
    # 因果推理训练数据
    causal_data = []
    for i in range(50):
        sample = {
            "id": f"causal_{i}",
            "type": "causal_relationship",
            "variables": ["temperature", "comfort_level"],
            "relationship": "temperature -> comfort_level",
            "strength": 0.8 + (i % 20) * 0.01,
            "confidence": 0.9 + (i % 10) * 0.01
        }
        causal_data.append(sample)
    
    causal_file = output_dir / "causal_reasoning_data.json"
    with open(causal_file, 'w', encoding='utf-8') as f:
        json.dump(causal_data, f, ensure_ascii=False, indent=2)
    
    # 自适应学习训练数据
    adaptive_data = []
    for i in range(50):
        sample = {
            "id": f"adaptive_{i}",
            "type": "learning_strategy",
            "context": {"task_complexity": 0.5 + (i % 5) * 0.1, "domain": "general"},
            "strategy": "strategy_" + str(i % 5),
            "performance": 0.7 + (i % 30) * 0.01
        }
        adaptive_data.append(sample)
    
    adaptive_file = output_dir / "adaptive_learning_data.json"
    with open(adaptive_file, 'w', encoding='utf-8') as f:
        json.dump(adaptive_data, f, ensure_ascii=False, indent=2)
    
    # Alpha深度模型训练数据
    alpha_data = []
    for i in range(50):
        sample = {
            "id": f"alpha_{i}",
            "type": "deep_parameter",
            "source_memory_id": f"mem_{i:06d}",
            "timestamp": datetime.now().isoformat(),
            "base_gist": {
                "summary": f"Sample memory {i}",
                "keywords": ["sample", "memory", f"item_{i}"],
                "original_length": 100 + i * 10
            },
            "relational_context": {
                "entities": ["EntityA", "EntityB"],
                "relationships": [{"subject": "EntityA", "verb": "related_to", "object": "EntityB"}]
            },
            "modalities": {
                "text_confidence": 0.9 + (i % 10) * 0.01
            }
        }
        alpha_data.append(sample)
    
    alpha_file = output_dir / "alpha_deep_model_data.json"
    with open(alpha_file, 'w', encoding='utf-8') as f:
        json.dump(alpha_data, f, ensure_ascii=False, indent=2)
    
    logger.info("创建了专门的概念模型训练数据:")
    logger.info(f"  - 环境模拟数据: {env_file}")
    logger.info(f"  - 因果推理数据: {causal_file}")
    logger.info(f"  - 自适应学习数据: {adaptive_file}")
    logger.info(f"  - Alpha深度模型数据: {alpha_file}")

def main():
    """主函数"""
    logger.info("开始准备概念模型训练数据...")
    
    # 创建数据目录
    data_dir = project_root / "data"
    concept_models_data_dir = data_dir / "concept_models_training_data"
    
    # 从文档创建训练数据
    docs_dir = project_root
    samples = create_training_samples_from_docs(docs_dir, concept_models_data_dir)
    
    # 创建专门的训练数据
    create_specialized_training_data(concept_models_data_dir)
    
    logger.info("概念模型训练数据准备完成!")
    logger.info(f"数据保存在: {concept_models_data_dir}")

if __name__ == "__main__":
    main()