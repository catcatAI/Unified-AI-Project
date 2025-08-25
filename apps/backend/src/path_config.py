"""
统一路径配置管理模块
用于处理项目中的所有路径配置，确保跨平台兼容性
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"

# 训练目录
TRAINING_DIR = PROJECT_ROOT / "training"

# 模型目录
MODELS_DIR = TRAINING_DIR / "models"

# 检查点目录
CHECKPOINTS_DIR = TRAINING_DIR / "checkpoints"

# 配置目录
CONFIGS_DIR = TRAINING_DIR / "configs"

def get_data_path(dataset_name: str) -> Path:
    """
    获取数据集路径
    
    Args:
        dataset_name: 数据集名称
        
    Returns:
        Path: 数据集路径
    """
    return DATA_DIR / dataset_name

def get_training_config_path(config_name: str) -> Path:
    """
    获取训练配置文件路径
    
    Args:
        config_name: 配置文件名称
        
    Returns:
        Path: 配置文件路径
    """
    return CONFIGS_DIR / config_name

def resolve_path(path_str: str) -> Path:
    """
    解析路径字符串，支持相对路径和绝对路径
    
    Args:
        path_str: 路径字符串
        
    Returns:
        Path: 解析后的路径对象
    """
    path = Path(path_str)
    if path.is_absolute():
        return path
    else:
        return PROJECT_ROOT / path

# 确保必要的目录存在
DIRECTORIES = [
    DATA_DIR,
    TRAINING_DIR,
    MODELS_DIR,
    CHECKPOINTS_DIR,
    CONFIGS_DIR
]

for directory in DIRECTORIES:
    directory.mkdir(parents=True, exist_ok=True)