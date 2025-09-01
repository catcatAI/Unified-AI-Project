#!/usr/bin/env python3
"""
特征提取模块
用于从训练好的模型中提取特征
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
from PIL import Image
import librosa
import pickle

# 添加项目路径
project_root = Path(__file__).parent.parent
backend_path = project_root / "apps" / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))

# 导入模型定义
from tools.train_vision_model import SimpleVisionModel
from tools.train_audio_model import SimpleAudioModel
from tools.train_text_model import SimpleTextModel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FeatureExtractor:
    """特征提取器"""
    
    def __init__(self, model_dir: str = None):
        self.project_root = project_root
        self.model_dir = Path(model_dir) if model_dir else project_root / "training" / "models"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"使用设备: {self.device}")
        
        # 加载模型和相关组件
        self.vision_model = None
        self.audio_model = None
        self.text_model = None
        self.text_vectorizer = None
        
        self._load_models()
    
    def _load_models(self):
        """加载训练好的模型"""
        logger.info("正在加载训练好的模型...")
        
        # 加载视觉模型
        vision_model_path = self.model_dir / "vision_model.pth"
        vision_metadata_path = self.model_dir / "vision_model_metadata.json"
        if vision_model_path.exists() and vision_metadata_path.exists():
            try:
                with open(vision_metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                num_classes = metadata.get("num_classes", 4)
                
                self.vision_model = SimpleVisionModel(num_classes=num_classes).to(self.device)
                self.vision_model.load_state_dict(torch.load(vision_model_path, map_location=self.device))
                self.vision_model.eval()
                logger.info("视觉模型加载成功")
            except Exception as e:
                logger.error(f"加载视觉模型时出错: {e}")
        else:
            logger.warning("未找到视觉模型文件")
        
        # 加载音频模型
        audio_model_path = self.model_dir / "audio_model.pth"
        audio_metadata_path = self.model_dir / "audio_model_metadata.json"
        if audio_model_path.exists() and audio_metadata_path.exists():
            try:
                with open(audio_metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                num_classes = metadata.get("num_classes", 2)
                
                self.audio_model = SimpleAudioModel(num_classes=num_classes).to(self.device)
                self.audio_model.load_state_dict(torch.load(audio_model_path, map_location=self.device))
                self.audio_model.eval()
                logger.info("音频模型加载成功")
            except Exception as e:
                logger.error(f"加载音频模型时出错: {e}")
        else:
            logger.warning("未找到音频模型文件")
        
        # 加载文本模型和向量化器
        text_model_path = self.model_dir / "text_model.pth"
        text_metadata_path = self.model_dir / "text_model_metadata.json"
        text_vectorizer_path = self.model_dir / "text_vectorizer.pkl"
        if (text_model_path.exists() and text_metadata_path.exists() and 
            text_vectorizer_path.exists()):
            try:
                with open(text_metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                num_classes = metadata.get("num_classes", 3)
                input_size = metadata.get("input_size", 1000)
                
                self.text_model = SimpleTextModel(input_size=input_size, num_classes=num_classes).to(self.device)
                self.text_model.load_state_dict(torch.load(text_model_path, map_location=self.device))
                self.text_model.eval()
                
                # 加载向量化器
                with open(text_vectorizer_path, 'rb') as f:
                    self.text_vectorizer = pickle.load(f)
                
                logger.info("文本模型和向量化器加载成功")
            except Exception as e:
                logger.error(f"加载文本模型时出错: {e}")
        else:
            logger.warning("未找到文本模型文件或向量化器")
    
    def extract_vision_features(self, image_path: str) -> np.ndarray:
        """从图像中提取视觉特征"""
        if self.vision_model is None:
            logger.warning("视觉模型未加载")
            return None
        
        try:
            # 加载和预处理图像
            image = Image.open(image_path).convert('RGB')
            image = image.resize((224, 224))
            
            # 转换为tensor并标准化
            image_tensor = torch.FloatTensor(np.array(image)).permute(2, 0, 1) / 255.0
            image_tensor = (image_tensor - torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)) / torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
            image_tensor = image_tensor.unsqueeze(0).to(self.device)
            
            # 提取特征
            with torch.no_grad():
                features = self.vision_model.features(image_tensor)
                features = features.view(features.size(0), -1)
                features = features.cpu().numpy()
            
            logger.info(f"成功提取视觉特征，形状: {features.shape}")
            return features
        except Exception as e:
            logger.error(f"提取视觉特征时出错: {e}")
            return None
    
    def extract_audio_features(self, audio_path: str) -> np.ndarray:
        """从音频中提取音频特征"""
        if self.audio_model is None:
            logger.warning("音频模型未加载")
            return None
        
        try:
            # 加载音频文件
            audio, sample_rate = librosa.load(audio_path, sr=16000)
            
            # 确保音频长度一致
            target_length = 16000 * 3  # 3秒
            if len(audio) > target_length:
                audio = audio[:target_length]
            elif len(audio) < target_length:
                audio = np.pad(audio, (0, target_length - len(audio)), 'constant')
            
            # 提取MFCC特征
            mfccs = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=13)
            mfccs = mfccs[:, :100]  # 限制为100帧
            
            # 如果帧数不足，进行填充
            if mfccs.shape[1] < 100:
                mfccs = np.pad(mfccs, ((0, 0), (0, 100 - mfccs.shape[1])), 'constant')
            
            # 转换为tensor
            mfccs_tensor = torch.FloatTensor(mfccs).unsqueeze(0).to(self.device)
            
            # 提取特征
            with torch.no_grad():
                # 通过卷积层
                x = self.audio_model.relu(self.audio_model.conv1(mfccs_tensor))
                x = self.audio_model.pool(x)
                x = self.audio_model.relu(self.audio_model.conv2(x))
                x = self.audio_model.pool(x)
                features = x.view(x.size(0), -1)
                features = features.cpu().numpy()
            
            logger.info(f"成功提取音频特征，形状: {features.shape}")
            return features
        except Exception as e:
            logger.error(f"提取音频特征时出错: {e}")
            return None
    
    def extract_text_features(self, text: str) -> np.ndarray:
        """从文本中提取文本特征"""
        if self.text_model is None or self.text_vectorizer is None:
            logger.warning("文本模型或向量化器未加载")
            return None
        
        try:
            # 文本向量化
            text_vector = self.text_vectorizer.transform([text]).toarray()
            text_tensor = torch.FloatTensor(text_vector).to(self.device)
            
            # 提取特征
            with torch.no_grad():
                # 通过前两层全连接层
                x = self.text_model.relu(self.text_model.fc1(text_tensor))
                x = self.text_model.dropout(x)
                features = self.text_model.relu(self.text_model.fc2(x))
                features = features.cpu().numpy()
            
            logger.info(f"成功提取文本特征，形状: {features.shape}")
            return features
        except Exception as e:
            logger.error(f"提取文本特征时出错: {e}")
            return None
    
    def extract_multimodal_features(self, image_path: str = None, audio_path: str = None, text: str = None) -> Dict[str, np.ndarray]:
        """提取多模态特征"""
        features = {}
        
        if image_path and Path(image_path).exists():
            vision_features = self.extract_vision_features(image_path)
            if vision_features is not None:
                features["vision"] = vision_features
        
        if audio_path and Path(audio_path).exists():
            audio_features = self.extract_audio_features(audio_path)
            if audio_features is not None:
                features["audio"] = audio_features
        
        if text:
            text_features = self.extract_text_features(text)
            if text_features is not None:
                features["text"] = text_features
        
        return features

def main():
    """主函数"""
    logger.info("开始特征提取...")
    
    # 初始化特征提取器
    extractor = FeatureExtractor()
    
    # 示例：提取各种模态的特征
    # 注意：这些是示例路径，实际使用时需要替换为真实的文件路径
    
    # 提取视觉特征（示例）
    # vision_features = extractor.extract_vision_features("path/to/image.jpg")
    
    # 提取音频特征（示例）
    # audio_features = extractor.extract_audio_features("path/to/audio.wav")
    
    # 提取文本特征（示例）
    # text_features = extractor.extract_text_features("这是一段示例文本")
    
    # 提取多模态特征（示例）
    # multimodal_features = extractor.extract_multimodal_features(
    #     image_path="path/to/image.jpg",
    #     audio_path="path/to/audio.wav",
    #     text="这是一段示例文本"
    # )
    
    logger.info("特征提取模块初始化完成!")

if __name__ == "__main__":
    main()