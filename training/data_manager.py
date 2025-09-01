#!/usr/bin/env python3
"""
数据管理器
负责自动检测、分类和处理训练数据
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
import mimetypes
import hashlib
from datetime import datetime
import numpy as np

# 添加项目路径
import sys
project_root = Path(__file__).parent.parent
backend_path = project_root / "apps" / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))

# 导入路径配置模块
try:
    from apps.backend.src.path_config import (
        PROJECT_ROOT, 
        DATA_DIR, 
        TRAINING_DIR, 
        get_data_path, 
        resolve_path
    )
except ImportError:
    # 如果路径配置模块不可用，使用默认路径处理
    PROJECT_ROOT = project_root
    DATA_DIR = PROJECT_ROOT / "data"
    TRAINING_DIR = PROJECT_ROOT / "training"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataManager:
    """数据管理器，负责自动检测、分类和处理训练数据"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.data_catalog = {}
        self.data_quality_scores = {}
        self.supported_formats = {
            'image': ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'],
            'audio': ['.wav', '.mp3', '.flac', '.aac', '.ogg'],
            'text': ['.txt', '.md', '.json', '.csv', '.xml'],
            'video': ['.mp4', '.avi', '.mov', '.mkv', '.flv'],
            'document': ['.pdf', '.doc', '.docx', '.ppt', '.pptx']
        }
        self.model_data_mapping = {
            'vision_service': ['image', 'document'],
            'audio_service': ['audio'],
            'causal_reasoning_engine': ['text'],
            'multimodal_service': ['image', 'audio', 'text', 'video'],
            'math_model': ['text'],
            'logic_model': ['text'],
            'concept_models': ['text', 'json'],
            'environment_simulator': ['text', 'json'],
            'causal_reasoning_engine': ['text', 'json'],  # 添加对因果推理引擎的JSON数据支持
            'adaptive_learning_controller': ['text', 'json'],
            'alpha_deep_model': ['text', 'json']
        }
    
    def scan_data(self) -> Dict[str, Any]:
        """扫描并分类所有数据"""
        logger.info(f"🔍 开始扫描数据目录: {self.data_dir}")
        
        # 清空之前的数据目录
        self.data_catalog = {}
        
        # 遍历数据目录
        for root, dirs, files in os.walk(self.data_dir):
            # 跳过隐藏目录
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                # 跳过隐藏文件
                if file.startswith('.'):
                    continue
                    
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.data_dir)
                
                # 获取文件信息
                try:
                    stat = file_path.stat()
                    file_info = {
                        'path': str(file_path),
                        'relative_path': str(relative_path),
                        'size': stat.st_size,
                        'modified_time': stat.st_mtime,
                        'extension': file_path.suffix.lower(),
                        'type': self._classify_file(file_path)
                    }
                    
                    # 添加到数据目录
                    self.data_catalog[str(relative_path)] = file_info
                except Exception as e:
                    logger.warning(f"⚠️ 无法获取文件信息 {file_path}: {e}")
        
        logger.info(f"✅ 数据扫描完成，共发现 {len(self.data_catalog)} 个文件")
        return self.data_catalog
    
    def _classify_file(self, file_path: Path) -> str:
        """根据文件扩展名分类文件"""
        extension = file_path.suffix.lower()
        
        for data_type, extensions in self.supported_formats.items():
            if extension in extensions:
                return data_type
        
        # 尝试使用mimetypes分类
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            if mime_type.startswith('image/'):
                return 'image'
            elif mime_type.startswith('audio/'):
                return 'audio'
            elif mime_type.startswith('video/'):
                return 'video'
            elif mime_type.startswith('text/'):
                return 'text'
            elif mime_type == 'application/pdf':
                return 'document'
        
        # 默认分类为文本
        return 'text'
    
    def assess_data_quality(self, file_path: str) -> Dict[str, Any]:
        """评估单个文件的数据质量"""
        path = Path(file_path)
        if not path.exists():
            return {'quality_score': 0, 'issues': ['文件不存在']}
        
        quality_info = {
            'quality_score': 0,
            'file_size': path.stat().st_size,
            'modified_time': path.stat().st_mtime,
            'issues': []
        }
        
        try:
            # 文件大小评估
            if quality_info['file_size'] < 10:  # 小于10字节
                quality_info['issues'].append('文件过小')
                quality_info['quality_score'] -= 20
            elif quality_info['file_size'] > 100 * 1024 * 1024:  # 大于100MB
                quality_info['issues'].append('文件过大')
                quality_info['quality_score'] -= 10
            else:
                quality_info['quality_score'] += 20
            
            # 文件类型特定检查
            file_type = self._classify_file(path)
            if file_type == 'image':
                quality_info = self._assess_image_quality(path, quality_info)
            elif file_type == 'audio':
                quality_info = self._assess_audio_quality(path, quality_info)
            elif file_type == 'text':
                quality_info = self._assess_text_quality(path, quality_info)
            
            # 文件完整性检查
            if self._is_file_corrupted(path):
                quality_info['issues'].append('文件可能已损坏')
                quality_info['quality_score'] -= 30
            else:
                quality_info['quality_score'] += 10
                
        except Exception as e:
            quality_info['issues'].append(f'评估错误: {str(e)}')
            quality_info['quality_score'] = 0
        
        # 确保分数在0-100范围内
        quality_info['quality_score'] = max(0, min(100, quality_info['quality_score']))
        
        self.data_quality_scores[str(path)] = quality_info
        return quality_info
    
    def _assess_image_quality(self, file_path: Path, quality_info: Dict) -> Dict:
        """评估图像文件质量"""
        try:
            # 尝试导入PIL来检查图像文件
            from PIL import Image
            with Image.open(file_path) as img:
                width, height = img.size
                # 检查图像尺寸
                if width < 10 or height < 10:
                    quality_info['issues'].append('图像尺寸过小')
                    quality_info['quality_score'] -= 15
                elif width > 10000 or height > 10000:
                    quality_info['issues'].append('图像尺寸过大')
                    quality_info['quality_score'] -= 10
                else:
                    quality_info['quality_score'] += 15
                    
                # 检查图像模式
                if img.mode not in ['RGB', 'RGBA', 'L']:
                    quality_info['issues'].append(f'图像模式不常见: {img.mode}')
        except ImportError:
            # 如果没有PIL，跳过图像特定检查
            pass
        except Exception as e:
            quality_info['issues'].append(f'图像读取错误: {str(e)}')
            quality_info['quality_score'] -= 20
        
        return quality_info
    
    def _assess_audio_quality(self, file_path: Path, quality_info: Dict) -> Dict:
        """评估音频文件质量"""
        # 简单的音频文件质量检查
        try:
            # 检查文件扩展名是否为支持的音频格式
            extension = file_path.suffix.lower()
            if extension in ['.wav', '.mp3', '.flac']:
                quality_info['quality_score'] += 10
            else:
                quality_info['issues'].append(f'音频格式可能不支持: {extension}')
        except Exception as e:
            quality_info['issues'].append(f'音频检查错误: {str(e)}')
            quality_info['quality_score'] -= 10
        
        return quality_info
    
    def _assess_text_quality(self, file_path: Path, quality_info: Dict) -> Dict:
        """评估文本文件质量"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 检查文件内容
            if len(content.strip()) == 0:
                quality_info['issues'].append('文件内容为空')
                quality_info['quality_score'] -= 30
            elif len(content) < 10:
                quality_info['issues'].append('文件内容过少')
                quality_info['quality_score'] -= 15
            else:
                quality_info['quality_score'] += 20
                
            # 检查编码问题
            try:
                content.encode('utf-8')
                quality_info['quality_score'] += 5
            except UnicodeError:
                quality_info['issues'].append('编码问题')
                quality_info['quality_score'] -= 10
                
        except UnicodeDecodeError:
            quality_info['issues'].append('文件编码不支持')
            quality_info['quality_score'] -= 25
        except Exception as e:
            quality_info['issues'].append(f'文本读取错误: {str(e)}')
            quality_info['quality_score'] -= 20
        
        return quality_info
    
    def _is_file_corrupted(self, file_path: Path) -> bool:
        """检查文件是否可能已损坏"""
        try:
            # 计算文件的MD5哈希值
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            
            # 简单检查：如果文件大小为0，则认为已损坏
            if file_path.stat().st_size == 0:
                return True
                
            return False
        except Exception:
            return True
    
    def get_data_by_type(self, data_type: str) -> List[Dict[str, Any]]:
        """根据数据类型获取文件列表"""
        result = []
        for file_info in self.data_catalog.values():
            if file_info['type'] == data_type:
                result.append(file_info)
        return result
    
    def get_high_quality_data(self, min_quality_score: int = 70) -> Dict[str, List[Dict[str, Any]]]:
        """获取高质量数据（按类型分组）"""
        high_quality_data = {}
        
        # 先评估所有数据的质量
        for file_path in self.data_catalog.keys():
            self.assess_data_quality(file_path)
        
        # 按类型分组高质量数据
        for file_path, quality_info in self.data_quality_scores.items():
            if quality_info['quality_score'] >= min_quality_score:
                file_info = self.data_catalog.get(file_path)
                if file_info:
                    data_type = file_info['type']
                    if data_type not in high_quality_data:
                        high_quality_data[data_type] = []
                    high_quality_data[data_type].append(file_info)
        
        return high_quality_data
    
    def prepare_training_data(self, model_type: str) -> List[Dict[str, Any]]:
        """为特定模型类型准备训练数据"""
        logger.info(f"📦 为模型 {model_type} 准备训练数据")
        
        # 获取该模型支持的数据类型
        supported_types = self.model_data_mapping.get(model_type, [])
        if not supported_types:
            logger.warning(f"⚠️ 未找到模型 {model_type} 的数据映射")
            return []
        
        # 收集支持的数据
        training_data = []
        for data_type in supported_types:
            data_files = self.get_data_by_type(data_type)
            training_data.extend(data_files)
        
        # 对于概念模型，直接添加概念模型训练数据
        if model_type in ['concept_models', 'environment_simulator', 'causal_reasoning_engine', 
                         'adaptive_learning_controller', 'alpha_deep_model']:
            # 添加概念模型专用训练数据
            concept_data_dir = self.data_dir / "concept_models_training_data"
            if concept_data_dir.exists():
                for json_file in concept_data_dir.glob("*.json"):
                    # 根据模型类型过滤数据
                    if self._is_data_relevant_for_model(json_file.name, model_type):
                        file_info = {
                            'path': str(json_file),
                            'relative_path': str(json_file.relative_to(self.data_dir)),
                            'size': json_file.stat().st_size,
                            'modified_time': json_file.stat().st_mtime,
                            'extension': '.json',
                            'type': 'json'
                        }
                        training_data.append(file_info)
        
        # 过滤高质量数据
        high_quality_data = self.get_high_quality_data()
        filtered_data = []
        for data_item in training_data:
            # 检查数据是否在高质量数据中
            data_type = data_item['type']
            if data_type in high_quality_data:
                high_quality_files = [f['path'] for f in high_quality_data[data_type]]
                if data_item['path'] in high_quality_files:
                    filtered_data.append(data_item)
            else:
                # 如果没有高质量数据检查，直接添加
                filtered_data.append(data_item)
        
        logger.info(f"✅ 为模型 {model_type} 准备了 {len(filtered_data)} 个训练数据文件")
        return filtered_data
    
    def _is_data_relevant_for_model(self, filename: str, model_type: str) -> bool:
        """检查数据文件是否与特定模型相关"""
        # 根据文件名和模型类型判断相关性
        if model_type == 'environment_simulator' and 'environment' in filename:
            return True
        elif model_type == 'causal_reasoning_engine' and 'causal' in filename:
            return True
        elif model_type == 'adaptive_learning_controller' and 'adaptive' in filename:
            return True
        elif model_type == 'alpha_deep_model' and 'alpha' in filename:
            return True
        elif model_type == 'concept_models':
            # 概念模型可以使用所有概念数据
            return any(keyword in filename for keyword in ['environment', 'causal', 'adaptive', 'alpha'])
        
        return False

    def get_data_statistics(self) -> Dict[str, Any]:
        """获取数据统计信息"""
        if not self.data_catalog:
            self.scan_data()
        
        stats = {
            'total_files': len(self.data_catalog),
            'file_types': {},
            'total_size': 0,
            'last_scan_time': datetime.now().isoformat()
        }
        
        # 统计各类文件数量和大小
        for file_info in self.data_catalog.values():
            file_type = file_info['type']
            if file_type not in stats['file_types']:
                stats['file_types'][file_type] = {'count': 0, 'size': 0}
            
            stats['file_types'][file_type]['count'] += 1
            stats['file_types'][file_type]['size'] += file_info['size']
            stats['total_size'] += file_info['size']
        
        return stats
    
    def save_data_catalog(self, catalog_path: str = None):
        """保存数据目录到文件"""
        if not catalog_path:
            catalog_path = TRAINING_DIR / "data_catalog.json"
        
        catalog_data = {
            'catalog': self.data_catalog,
            'quality_scores': self.data_quality_scores,
            'statistics': self.get_data_statistics(),
            'generated_at': datetime.now().isoformat()
        }
        
        try:
            with open(catalog_path, 'w', encoding='utf-8') as f:
                json.dump(catalog_data, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 数据目录已保存到: {catalog_path}")
        except Exception as e:
            logger.error(f"❌ 保存数据目录失败: {e}")
    
    def load_data_catalog(self, catalog_path: str = None):
        """从文件加载数据目录"""
        if not catalog_path:
            catalog_path = TRAINING_DIR / "data_catalog.json"
        
        if not Path(catalog_path).exists():
            logger.warning(f"⚠️ 数据目录文件不存在: {catalog_path}")
            return False
        
        try:
            with open(catalog_path, 'r', encoding='utf-8') as f:
                catalog_data = json.load(f)
            
            self.data_catalog = catalog_data.get('catalog', {})
            self.data_quality_scores = catalog_data.get('quality_scores', {})
            logger.info(f"✅ 数据目录已从 {catalog_path} 加载")
            return True
        except Exception as e:
            logger.error(f"❌ 加载数据目录失败: {e}")
            return False


def main():
    """主函数，用于测试DataManager"""
    print("🔍 测试数据管理器...")
    
    # 初始化数据管理器
    data_manager = DataManager()
    
    # 扫描数据
    catalog = data_manager.scan_data()
    print(f"📊 扫描到 {len(catalog)} 个文件")
    
    # 显示数据统计
    stats = data_manager.get_data_statistics()
    print(f"📈 数据统计:")
    print(f"  总文件数: {stats['total_files']}")
    print(f"  总大小: {stats['total_size'] / (1024*1024):.2f} MB")
    print(f"  文件类型分布:")
    for file_type, info in stats['file_types'].items():
        print(f"    {file_type}: {info['count']} 个文件, {info['size'] / (1024*1024):.2f} MB")
    
    # 评估几个文件的质量
    print(f"\n🔍 数据质量评估:")
    sample_files = list(catalog.keys())[:3]  # 取前3个文件进行评估
    for file_path in sample_files:
        quality = data_manager.assess_data_quality(file_path)
        print(f"  {file_path}: 质量评分 {quality['quality_score']}/100")
        if quality['issues']:
            print(f"    问题: {', '.join(quality['issues'])}")
    
    # 为不同模型准备数据
    print(f"\n📦 训练数据准备:")
    for model_type in ['vision_service', 'audio_service', 'causal_reasoning_engine']:
        training_data = data_manager.prepare_training_data(model_type)
        print(f"  {model_type}: {len(training_data)} 个训练文件")
    
    # 保存数据目录
    data_manager.save_data_catalog()
    print(f"\n✅ 数据管理器测试完成")


if __name__ == "__main__":
    main()