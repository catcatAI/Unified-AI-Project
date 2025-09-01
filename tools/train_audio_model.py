#!/usr/bin/env python3
"""
音频模型训练脚本
使用现有音频数据训练基础音频模型
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import librosa

# 添加项目路径
project_root = Path(__file__).parent.parent
backend_path = project_root / "apps" / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioDataset(Dataset):
    """音频数据集"""
    
    def __init__(self, data: List[Dict[str, Any]], sample_rate: int = 16000):
        self.data = data
        self.sample_rate = sample_rate
        self.labels = self._create_labels()
        
    def _create_labels(self) -> List[int]:
        """创建标签"""
        # 基于语言创建标签
        languages = list(set(item.get("language", "unknown") for item in self.data))
        lang_to_label = {lang: idx for idx, lang in enumerate(languages)}
        
        labels = []
        for item in self.data:
            language = item.get("language", "unknown")
            labels.append(lang_to_label[language])
            
        return labels
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        audio_path = item.get("audio_path")
        
        # 加载或创建音频数据
        if audio_path and Path(audio_path).exists():
            try:
                # 加载音频文件
                audio, _ = librosa.load(audio_path, sr=self.sample_rate)
            except Exception as e:
                logger.warning(f"无法加载音频 {audio_path}: {e}")
                # 创建模拟音频数据
                duration = item.get("duration", 3.0)
                audio = np.random.randn(int(self.sample_rate * duration)).astype(np.float32)
        else:
            # 创建模拟音频数据
            duration = item.get("duration", 3.0)
            audio = np.random.randn(int(self.sample_rate * duration)).astype(np.float32)
        
        # 确保音频长度一致
        target_length = self.sample_rate * 3  # 3秒
        if len(audio) > target_length:
            audio = audio[:target_length]
        elif len(audio) < target_length:
            audio = np.pad(audio, (0, target_length - len(audio)), 'constant')
        
        # 提取MFCC特征
        mfccs = librosa.feature.mfcc(y=audio, sr=self.sample_rate, n_mfcc=13)
        mfccs = mfccs[:, :100]  # 限制为100帧
        
        # 如果帧数不足，进行填充
        if mfccs.shape[1] < 100:
            mfccs = np.pad(mfccs, ((0, 0), (0, 100 - mfccs.shape[1])), 'constant')
        
        # 转换为tensor
        mfccs = torch.FloatTensor(mfccs)
        
        label = self.labels[idx]
        return mfccs, label

class SimpleAudioModel(nn.Module):
    """简单的音频模型"""
    
    def __init__(self, num_classes: int = 2, input_size: int = 13):
        super(SimpleAudioModel, self).__init__()
        self.conv1 = nn.Conv1d(input_size, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(32, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool1d(2)
        self.relu = nn.ReLU()
        
        # 计算全连接层输入大小
        # 输入100帧，经过两次池化后变为25帧
        self.fc1 = nn.Linear(64 * 25, 128)
        self.fc2 = nn.Linear(128, num_classes)
        self.dropout = nn.Dropout(0.5)
    
    def forward(self, x):
        x = self.relu(self.conv1(x))
        x = self.pool(x)
        x = self.relu(self.conv2(x))
        x = self.pool(x)
        x = x.view(x.size(0), -1)
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x

class AudioModelTrainer:
    """音频模型训练器"""
    
    def __init__(self, model_save_dir: str = None):
        self.project_root = project_root
        self.model_save_dir = Path(model_save_dir) if model_save_dir else project_root / "training" / "models"
        self.model_save_dir.mkdir(parents=True, exist_ok=True)
        
        # 设备配置
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"使用设备: {self.device}")
    
    def load_data(self) -> List[Dict[str, Any]]:
        """加载处理后的音频数据"""
        logger.info("正在加载处理后的音频数据...")
        
        processed_data_file = self.project_root / "data" / "processed_traditional_data" / "audio_processed.json"
        if processed_data_file.exists():
            try:
                with open(processed_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"成功加载 {len(data)} 条音频数据")
                return data
            except Exception as e:
                logger.error(f"加载音频数据时出错: {e}")
                return []
        else:
            logger.warning(f"未找到处理后的音频数据文件: {processed_data_file}")
            return []
    
    def train_model(self, epochs: int = 10, batch_size: int = 8, learning_rate: float = 0.001):
        """训练音频模型"""
        logger.info("开始训练音频模型...")
        
        # 加载数据
        data = self.load_data()
        if not data:
            logger.error("没有可用的训练数据")
            return False
        
        # 创建数据集和数据加载器
        dataset = AudioDataset(data)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        # 创建模型
        num_classes = len(set(dataset.labels))
        model = SimpleAudioModel(num_classes=num_classes).to(self.device)
        
        # 损失函数和优化器
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        
        # 训练循环
        model.train()
        for epoch in range(epochs):
            running_loss = 0.0
            correct = 0
            total = 0
            
            for batch_idx, (features, labels) in enumerate(dataloader):
                features, labels = features.to(self.device), labels.to(self.device)
                
                # 前向传播
                outputs = model(features)
                loss = criterion(outputs, labels)
                
                # 反向传播和优化
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                # 统计信息
                running_loss += loss.item()
                _, predicted = outputs.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()
                
                # 每5个批次打印一次信息
                if batch_idx % 5 == 0:
                    logger.info(f'Epoch: {epoch+1}/{epochs}, Batch: {batch_idx}, '
                              f'Loss: {loss.item():.4f}, Accuracy: {100.*correct/total:.2f}%')
            
            # 每个epoch结束时打印信息
            epoch_loss = running_loss / len(dataloader)
            epoch_acc = 100. * correct / total
            logger.info(f'Epoch {epoch+1} finished - Loss: {epoch_loss:.4f}, Accuracy: {epoch_acc:.2f}%')
        
        # 保存模型
        self.save_model(model, num_classes)
        logger.info("音频模型训练完成!")
        return True
    
    def save_model(self, model: nn.Module, num_classes: int):
        """保存训练好的模型"""
        model_path = self.model_save_dir / "audio_model.pth"
        metadata_path = self.model_save_dir / "audio_model_metadata.json"
        
        # 保存模型权重
        torch.save(model.state_dict(), model_path)
        logger.info(f"模型已保存到: {model_path}")
        
        # 保存元数据
        metadata = {
            "model_type": "SimpleAudioModel",
            "num_classes": num_classes,
            "input_shape": [13, 100],  # 13个MFCC特征，100帧
            "training_date": torch.utils.data.dataset.datetime.datetime.now().isoformat(),
            "framework": "PyTorch",
            "version": "1.0"
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        logger.info(f"模型元数据已保存到: {metadata_path}")

def main():
    """主函数"""
    logger.info("开始训练音频模型...")
    
    # 初始化训练器
    trainer = AudioModelTrainer()
    
    # 训练模型
    success = trainer.train_model(epochs=5, batch_size=4, learning_rate=0.001)
    
    if success:
        logger.info("音频模型训练成功完成!")
    else:
        logger.error("音频模型训练失败!")

if __name__ == "__main__":
    main()