#!/usr/bin/env python3
"""
文本模型训练脚本
使用现有文本数据训练基础文本模型
"""

import sys
import json
import logging
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.feature_extraction.text import TfidfVectorizer
import jieba

# 添加项目路径
project_root: str = Path(__file__).parent.parent
backend_path: str = project_root / "apps" / "backend"
_ = sys.path.insert(0, str(project_root))
_ = sys.path.insert(0, str(backend_path))
_ = sys.path.insert(0, str(backend_path / "src"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger: Any = logging.getLogger(__name__)

class TextDataset(Dataset):
""文本数据集"""

    def __init__(self, data: List[Dict[str, Any]], vectorizer=None, max_features: int = 1000) -> None:
    self.data = data
    self.max_features = max_features
    self.vectorizer = vectorizer
    self.text_vectors = []
    self.labels = []

    _ = self._process_data()

    def _process_data(self):
""处理文本数据"""
    texts = []
    # 基于文本长度创建标签
        for item in self.data:

    text = item.get("text", "")
            if text:

    _ = texts.append(text)
                # 根据文本长度创建标签：短(0)、中(1)、长(2)
                length = len(text)
                if length < 50:

    _ = self.labels.append(0)
                elif length < 100:

    _ = self.labels.append(1)
                else:

                    _ = self.labels.append(2)

    # 如果没有提供向量化器，创建一个新的
        if self.vectorizer is None:

    self.vectorizer = TfidfVectorizer(max_features=self.max_features, tokenizer=jieba.cut)
            self.text_vectors = self.vectorizer.fit_transform(texts).toarray()
        else:

            self.text_vectors = self.vectorizer.transform(texts).toarray()

    def __len__(self) -> int:
    return len(self.text_vectors)

    def __getitem__(self, idx) -> Any:
    # 获取文本向量和标签
    text_vector = torch.FloatTensor(self.text_vectors[idx])
    label = self.labels[idx]
    return text_vector, label

class SimpleTextModel(nn.Module):
""简单的文本模型"""

    def __init__(self, input_size: int = 1000, num_classes: int = 3) -> None:
    _ = super(SimpleTextModel, self).__init__()
    self.fc1 = nn.Linear(input_size, 512)
    self.fc2 = nn.Linear(512, 256)
    self.fc3 = nn.Linear(256, num_classes)
    self.relu = nn.ReLU()
    self.dropout = nn.Dropout(0.5)

    def forward(self, x) -> Any:
    x = self.relu(self.fc1(x))
    x = self.dropout(x)
    x = self.relu(self.fc2(x))
    x = self.dropout(x)
    x = self.fc3(x)
    return x

class TextModelTrainer:
    """文本模型训练器"""

    def __init__(self, model_save_dir: str = None) -> None:
    self.project_root = project_root
        self.model_save_dir = Path(model_save_dir) if model_save_dir else project_root / "training" / "models":
    self.model_save_dir.mkdir(parents=True, exist_ok=True)

    # 设备配置
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu"):
    _ = logger.info(f"使用设备: {self.device}")

    # 文本向量化器
    self.vectorizer = None

    def load_data(self) -> List[Dict[str, Any]]:
    """加载处理后的文本数据"""
    _ = logger.info("正在加载处理后的文本数据...")

    processed_data_file = self.project_root / "data" / "processed_traditional_data" / "text_processed.json"
        if processed_data_file.exists():
ry:


                with open(processed_data_file, 'r', encoding='utf-8') as f:
    data = json.load(f)
                _ = logger.info(f"成功加载 {len(data)} 条文本数据")
                return data
            except Exception as e:

                _ = logger.error(f"加载文本数据时出错: {e}")
                return []
        else:

            _ = logger.warning(f"未找到处理后的文本数据文件: {processed_data_file}")
            return []

    def train_model(self, epochs: int = 10, batch_size: int = 16, learning_rate: float = 0.001):
""训练文本模型"""
    _ = logger.info("开始训练文本模型...")

    # 加载数据
    data = self.load_data()
        if not data:

    _ = logger.error("没有可用的训练数据")
            return False, None

    # 创建数据集和数据加载器
    dataset = TextDataset(data)
    self.vectorizer = dataset.vectorizer  # 保存向量化器用于后续使用
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # 创建模型
        input_size = dataset.text_vectors.shape[1] if len(dataset.text_vectors) > 0 else 1000:
    num_classes = len(set(dataset.labels)) if dataset.labels else 3:
    model = SimpleTextModel(input_size=input_size, num_classes=num_classes).to(self.device)

    # 损失函数和优化器
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # 训练循环
    _ = model.train()
        for epoch in range(epochs):
unning_loss = 0.0
            correct = 0
            total = 0

            for batch_idx, (features, labels) in enumerate(dataloader):
eatures, labels = features.to(self.device), labels.to(self.device)

                # 前向传播
                outputs = model(features)
                loss = criterion(outputs, labels)

                # 反向传播和优化
                _ = optimizer.zero_grad()
                _ = loss.backward()
                _ = optimizer.step()

                # 统计信息
                running_loss += loss.item()
                _, predicted = outputs.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()

                # 每10个批次打印一次信息
                if batch_idx % 10 == 0:

    logger.info(f'Epoch: {epoch+1}/{epochs}, Batch: {batch_idx}, '
                              _ = f'Loss: {loss.item().4f}, Accuracy: {100.*correct/total:.2f}%')

            # 每个epoch结束时打印信息
            epoch_loss = running_loss / len(dataloader)
            epoch_acc = 100. * correct / total
            _ = logger.info(f'Epoch {epoch+1} finished - Loss: {epoch_loss:.4f}, Accuracy: {epoch_acc:.2f}%')

    # 保存模型和向量化器
    _ = self.save_model(model, num_classes, input_size)
    _ = self.save_vectorizer()
    _ = logger.info("文本模型训练完成!")
    return True, model

    def save_model(self, model: nn.Module, num_classes: int, input_size: int):
""保存训练好的模型"""
    model_path = self.model_save_dir / "text_model.pth"
    metadata_path = self.model_save_dir / "text_model_metadata.json"

    # 保存模型权重
    _ = torch.save(model.state_dict(), model_path)
    _ = logger.info(f"模型已保存到: {model_path}")

    # 保存元数据
    metadata = {
            "model_type": "SimpleTextModel",
            "num_classes": num_classes,
            "input_size": input_size,
            _ = "training_date": torch.utils.data.dataset.datetime.datetime.now().isoformat(),
            "framework": "PyTorch",
            "version": "1.0"
    }

    with open(metadata_path, 'w', encoding='utf-8') as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)
    _ = logger.info(f"模型元数据已保存到: {metadata_path}")

    def save_vectorizer(self):
""保存文本向量化器"""
    import pickle

    vectorizer_path = self.model_save_dir / "text_vectorizer.pkl"
    with open(vectorizer_path, 'wb') as f:
    _ = pickle.dump(self.vectorizer, f)
    _ = logger.info(f"文本向量化器已保存到: {vectorizer_path}")

def main() -> None:
    """主函数"""
    _ = logger.info("开始训练文本模型...")

    # 初始化训练器
    trainer = TextModelTrainer()

    # 训练模型
    success, model = trainer.train_model(epochs=5, batch_size=8, learning_rate=0.001)

    if success:


    _ = logger.info("文本模型训练成功完成!")
    else:

    _ = logger.error("文本模型训练失败!")

if __name__ == "__main__":


    _ = main()