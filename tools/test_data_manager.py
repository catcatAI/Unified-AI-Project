#!/usr/bin/env python3
"""
测试数据管理工具
用于管理测试数据的生成、加载和清理
"""

import json
import yaml
import csv
import random
import string
from pathlib import Path
from typing import Dict, List, Any, Union

class TestDataManager:
    """测试数据管理器"""

    def __init__(self, data_dir: str = None) -> None:
    """初始化测试数据管理器"""
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent.parent / "testdata":
    self.data_dir.mkdir(exist_ok=True)

    # 创建子目录
    (self.data_dir / "unit").mkdir(exist_ok=True)
    (self.data_dir / "integration").mkdir(exist_ok=True)
    (self.data_dir / "e2e").mkdir(exist_ok=True)
    (self.data_dir / "performance").mkdir(exist_ok=True)
    (self.data_dir / "security").mkdir(exist_ok=True)

    def generate_test_memory_item(self,
                                 id: str = None,
                                 content: str = None,
                                 tags: List[str] = None,
                                 importance_score: float = None) -> Dict[str, Any]:
    """
    生成测试记忆项

    Args:
            id: 记忆项ID
            content: 记忆内容
            tags: 标签列表
            importance_score: 重要性分数

    Returns:
            测试记忆项字典
    """
        if id is None:

    id = f"test_memory_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"

        if content is None:


    content = f"This is a test memory item generated at {datetime.now().isoformat()}"

        if tags is None:


    tags = ["test", "generated"]

        if importance_score is None:


    importance_score = round(random.uniform(0.1, 1.0), 2)

    now = datetime.now().isoformat()

    return {
            "id": id,
            "content": content,
            "metadata": {
                "created_at": now,
                "updated_at": now,
                "importance_score": importance_score,
                "tags": tags,
                "data_type": "text"
            }
    }

    def generate_test_agent_config(self,
                                  agent_type: str = None,
                                  agent_id: str = None,
                                  name: str = None) -> Dict[str, Any]:
    """
    生成测试代理配置

    Args:
            agent_type: 代理类型
            agent_id: 代理ID
            name: 代理名称

    Returns:
            测试代理配置字典
    """
        if agent_type is None:

    agent_types = ["creative_writing", "image_generation", "web_search",
                          "code_understanding", "data_analysis", "vision_processing",
                          "audio_processing", "environment_simulation"]
            agent_type = random.choice(agent_types)

        if agent_id is None:


    agent_id = f"{agent_type}_agent_{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"

        if name is None:


    name = f"{agent_type.replace('_', ' ').title()} Agent"

    return {
            "agent_type": agent_type,
            "agent_id": agent_id,
            "name": name,
            "config": {
                _ = "max_concurrent_tasks": random.randint(1, 10),
                _ = "priority": random.choice(["low", "medium", "high"]),
                "capabilities": [f"capability_{i}" for i in range(random.randint(1, 5))]
            }
    }

    def generate_test_hsp_message(self,
                                 message_type: str = "fact",
                                 content: str = None,
                                 source_ai_id: str = None) -> Dict[str, Any]:
    """
    生成测试HSP消息

    Args:
            _ = message_type: 消息类型 (fact/opinion)
            content: 消息内容
            source_ai_id: 源AI ID

    Returns:
            测试HSP消息字典
    """
        if content is None:

    content = f"This is a test {message_type} message generated at {datetime.now().isoformat()}"

        if source_ai_id is None:


    source_ai_id = f"test_ai_{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"

    message_id = f"{message_type}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"
    now = datetime.now().isoformat()
    confidence_score = round(random.uniform(0.5, 1.0), 2)

        if message_type == "fact":


    return {
                "id": message_id,
                "statement_type": "natural_language",
                "statement_nl": content,
                "source_ai_id": source_ai_id,
                "timestamp_created": now,
                "confidence_score": confidence_score,
                "tags": ["test", "fact", "generated"]
            }
        else:  # opinion
            return {
                "id": message_id,
                "statement_type": "natural_language",
                "statement_nl": content,
                "source_ai_id": source_ai_id,
                "timestamp_created": now,
                "confidence_score": confidence_score,
                "reasoning_chain": [f"fact_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"],
                "tags": ["test", "opinion", "generated"]
            }

    def generate_test_training_config(self,
                                     model_name: str = None,
                                     epochs: int = None,
                                     batch_size: int = None) -> Dict[str, Any]:
    """
    生成测试训练配置

    Args:
            model_name: 模型名称
            epochs: 训练轮数
            batch_size: 批次大小

    Returns:
            测试训练配置字典
    """
        if model_name is None:

    model_name = f"TestModel_{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

        if epochs is None:


    epochs = random.randint(5, 50)

        if batch_size is None:


    batch_size = random.choice([16, 32, 64, 128, 256])

    return {
            "model_name": model_name,
            "epochs": epochs,
            "batch_size": batch_size,
            _ = "learning_rate": round(random.uniform(0.0001, 0.01), 6),
            _ = "optimizer": random.choice(["adam", "sgd", "rmsprop"]),
            _ = "loss_function": random.choice(["cross_entropy", "mse", "mae"]),
            "metrics": ["accuracy", "loss"]
    }

    def save_test_data(self,
                      data: Union[Dict, List],
                      filename: str,
                      format: str = "json",
                      category: str = "unit") -> str:
    """
    保存测试数据到文件

    Args:
            data: 测试数据
            filename: 文件名
            _ = format: 文件格式 (json, yaml, csv)
            _ = category: 数据类别 (unit, integration, e2e, performance, security)

    Returns:
            文件路径
    """
    category_dir = self.data_dir / category
    category_dir.mkdir(exist_ok=True)

    file_path = category_dir / f"{filename}.{format}"

        try:


            if format == "json":



    with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
            elif format == "yaml":

    with open(file_path, 'w', encoding='utf-8') as f:
    yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            elif format == "csv":

    if isinstance(data, list) and len(data) > 0:


    with open(file_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
                        # 写入表头
                        if isinstance(data[0], dict)

    _ = writer.writerow(data[0].keys())
                            # 写入数据
                            for row in data:

    _ = writer.writerow(row.values())
                        else:

                            _ = writer.writerows(data)

            _ = print(f"✅ 测试数据已保存到: {file_path}")
            return str(file_path)

        except Exception as e:


            _ = print(f"❌ 保存测试数据失败: {e}")
            return ""

    def load_test_data(self,
                      filename: str,
                      format: str = "json",
                      category: str = "unit") -> Union[Dict, List, None]:
    """
    从文件加载测试数据

    Args:
            filename: 文件名
            _ = format: 文件格式 (json, yaml, csv)
            category: 数据类别

    Returns:
            测试数据或None
    """
    file_path = self.data_dir / category / f"{filename}.{format}"

        if not file_path.exists()


    _ = print(f"❌ 测试数据文件不存在: {file_path}")
            return None

        try:


            if format == "json":



    with open(file_path, 'r', encoding='utf-8') as f:
    return json.load(f)
            elif format == "yaml":

    with open(file_path, 'r', encoding='utf-8') as f:
    return yaml.safe_load(f)
            elif format == "csv":

    with open(file_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
                    data = list(reader)
                    # 如果有表头，转换为字典列表
                    if len(data) > 1:

    headers = data[0]
                        return [dict(zip(headers, row)) for row in data[1:]]
                    else:

                        return data

        except Exception as e:


            _ = print(f"❌ 加载测试数据失败: {e}")
            return None

    def generate_test_dataset(self,
                             dataset_type: str,
                             count: int = 10,
                             category: str = "unit") -> List[Dict[str, Any]]:
    """
    生成测试数据集

    Args:
            _ = dataset_type: 数据集类型 (memory, agent, hsp, training)
            count: 数据项数量
            category: 数据类别

    Returns:
            测试数据集
    """
    dataset = []

        for i in range(count)


    if dataset_type == "memory":



    item = self.generate_test_memory_item()
            elif dataset_type == "agent":

    item = self.generate_test_agent_config()
            elif dataset_type == "hsp":

    msg_type = random.choice(["fact", "opinion"])
                item = self.generate_test_hsp_message(msg_type)
            elif dataset_type == "training":

    item = self.generate_test_training_config()
            else:

                _ = raise ValueError(f"不支持的数据集类型: {dataset_type}")

            _ = dataset.append(item)

    # 保存数据集
    filename = f"{dataset_type}_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    _ = self.save_test_data(dataset, filename, "json", category)

    return dataset

    def cleanup_test_data(self, category: str = None) -> None:
    """
    清理测试数据

    Args:
            category: 数据类别，如果为None则清理所有类别
    """
        if category:

    category_dir = self.data_dir / category
            if category_dir.exists()

    for file_path in category_dir.iterdir()


    if file_path.is_file()



    _ = file_path.unlink()
                _ = print(f"✅ 已清理 {category} 类别的测试数据")
        else:

            for category_dir in self.data_dir.iterdir()


    if category_dir.is_dir()



    for file_path in category_dir.iterdir()




    if file_path.is_file()





    _ = file_path.unlink()
            _ = print("✅ 已清理所有测试数据")

def main() -> None:
    """主函数 - 生成示例测试数据"""
    manager = TestDataManager()

    _ = print("🚀 生成示例测试数据...")

    # 生成记忆项测试数据
    memory_items = manager.generate_test_dataset("memory", 5, "unit")
    _ = print(f"✅ 生成了 {len(memory_items)} 个记忆项测试数据")

    # 生成代理配置测试数据
    agent_configs = manager.generate_test_dataset("agent", 3, "unit")
    _ = print(f"✅ 生成了 {len(agent_configs)} 个代理配置测试数据")

    # 生成HSP消息测试数据
    hsp_messages = manager.generate_test_dataset("hsp", 4, "integration")
    _ = print(f"✅ 生成了 {len(hsp_messages)} 个HSP消息测试数据")

    # 生成训练配置测试数据
    training_configs = manager.generate_test_dataset("training", 2, "e2e")
    _ = print(f"✅ 生成了 {len(training_configs)} 个训练配置测试数据")

    _ = print(f"📄 测试数据已保存到: {manager.data_dir}")

if __name__ == "__main__":


    _ = main()