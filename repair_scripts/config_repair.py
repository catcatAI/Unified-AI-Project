#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置文件修復腳本
用於創建或修復項目中缺失的配置文件

使用方法:
    python config_repair.py [--check] [--fix] [--backup] [--verbose]
"""

import os
import sys
import json
import shutil
import argparse
import logging
from pathlib import Path
from datetime import datetime

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('config_repair')

# 項目根目錄
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 需要檢查和修復的配置文件列表
CONFIG_FILES = {
    # 主配置文件
    'config/settings.json': {
        'content': {
            'project_name': 'Unified-AI-Project',
            'version': '0.1.0',
            'debug': False,
            'log_level': 'info',
            'api_timeout': 30,
            'max_retries': 3,
            'data_dir': 'data',
            'output_dir': 'output',
            'models_dir': 'models',
            'temp_dir': 'temp'
        }
    },
    # 模型配置
    'config/models.json': {
        'content': {
            'default_model': 'gpt-3.5-turbo',
            'available_models': [
                'gpt-3.5-turbo',
                'gpt-4',
                'llama-2-7b',
                'llama-2-13b',
                'claude-2'
            ],
            'embedding_model': 'text-embedding-ada-002',
            'model_settings': {
                'temperature': 0.7,
                'max_tokens': 1000,
                'top_p': 1.0,
                'frequency_penalty': 0.0,
                'presence_penalty': 0.0
            }
        }
    },
    # API配置
    'config/api.json': {
        'content': {
            'openai': {
                'api_key_env': 'OPENAI_API_KEY',
                'base_url': 'https://api.openai.com/v1',
                'organization': ''
            },
            'anthropic': {
                'api_key_env': 'ANTHROPIC_API_KEY',
                'base_url': 'https://api.anthropic.com'
            },
            'huggingface': {
                'api_key_env': 'HF_API_KEY',
                'base_url': 'https://api-inference.huggingface.co/models'
            }
        }
    },
    # 數據處理配置
    'config/data_processing.json': {
        'content': {
            'chunk_size': 1000,
            'chunk_overlap': 200,
            'text_splitter': 'recursive',
            'separators': ['\n\n', '\n', '. ', ', '],
            'encoding': 'utf-8',
            'supported_formats': ['txt', 'pdf', 'docx', 'md', 'html', 'csv', 'json']
        }
    },
    # 日誌配置
    'config/logging.json': {
        'content': {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'standard',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'class': 'logging.FileHandler',
                    'level': 'DEBUG',
                    'formatter': 'standard',
                    'filename': 'logs/app.log',
                    'mode': 'a'
                }
            },
            'loggers': {
                '': {
                    'handlers': ['console', 'file'],
                    'level': 'INFO',
                    'propagate': True
                }
            }
        }
    },
    # 環境變量示例文件
    '.env.example': {
        'content_str': """# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
HF_API_KEY=your_huggingface_api_key_here

# Project Settings
DEBUG=False
LOG_LEVEL=info
"""
    }
}

# 要排除的目錄
EXCLUDED_DIRS = [
    '.git',
    'venv',
    'env',
    '.venv',
    '.env',
    '__pycache__',
    'node_modules',
    'dist',
    'build',
    'logs',
    'temp',
    'summaries',
    'repair_scripts'
]

def parse_args():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description='配置文件修復工具')
    parser.add_argument('--check', action='store_true', help='只檢查問題，不修復')
    parser.add_argument('--fix', action='store_true', help='修復發現的問題')
    parser.add_argument('--backup', action='store_true', help='修復前備份文件')
    parser.add_argument('--verbose', action='store_true', help='顯示詳細日誌')
    
    args = parser.parse_args()
    
    # 如果沒有指定--check或--fix，默認為--check
    if not (args.check or args.fix):
        args.check = True
    
    return args

def setup_logging(verbose):
    """設置日誌級別"""
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

def backup_file(file_path):
    """備份文件"""
    if not os.path.exists(file_path):
        return False
    
    backup_dir = PROJECT_ROOT / 'backups' / datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs(backup_dir, exist_ok=True)
    
    rel_path = os.path.relpath(file_path, PROJECT_ROOT)
    backup_path = backup_dir / rel_path
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    
    shutil.copy2(file_path, backup_path)
    logger.debug(f"已備份文件: {file_path} -> {backup_path}")
    return True

def create_config_file(file_path, config_data):
    """創建配置文件"""
    abs_path = PROJECT_ROOT / file_path
    
    # 確保目錄存在
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    
    # 寫入配置文件
    if 'content' in config_data:
        with open(abs_path, 'w', encoding='utf-8') as f:
            json.dump(config_data['content'], f, indent=4, ensure_ascii=False)
    elif 'content_str' in config_data:
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(config_data['content_str'])
    
    logger.info(f"已創建配置文件: {file_path}")
    return True

def check_config_files(fix=False, backup=False):
    """檢查並修復配置文件"""
    missing_files = []
    fixed_files = []
    
    for file_path, config_data in CONFIG_FILES.items():
        abs_path = PROJECT_ROOT / file_path
        
        if not os.path.exists(abs_path):
            missing_files.append(file_path)
            logger.warning(f"缺失配置文件: {file_path}")
            
            if fix:
                if backup:
                    backup_file(abs_path)
                
                if create_config_file(file_path, config_data):
                    fixed_files.append(file_path)
    
    return missing_files, fixed_files

def check_config_directories():
    """檢查並創建必要的目錄"""
    required_dirs = [
        'config',
        'logs',
        'data',
        'output',
        'models',
        'temp'
    ]
    
    created_dirs = []
    
    for dir_name in required_dirs:
        dir_path = PROJECT_ROOT / dir_name
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"已創建目錄: {dir_name}")
            created_dirs.append(dir_name)
    
    return created_dirs

def main():
    """主函數"""
    args = parse_args()
    setup_logging(args.verbose)
    
    logger.info("開始檢查配置文件...")
    
    # 檢查並創建必要的目錄
    created_dirs = check_config_directories()
    if created_dirs:
        logger.info(f"已創建 {len(created_dirs)} 個必要目錄")
    
    # 檢查配置文件
    missing_files, fixed_files = check_config_files(fix=args.fix, backup=args.backup)
    
    # 輸出結果
    if missing_files:
        logger.warning(f"發現 {len(missing_files)} 個缺失的配置文件")
        for file in missing_files:
            logger.debug(f"  - {file}")
        
        if args.fix:
            logger.info(f"已修復 {len(fixed_files)} 個配置文件")
            for file in fixed_files:
                logger.debug(f"  - {file}")
        elif not args.fix:
            logger.info("使用 --fix 參數來修復這些問題")
    else:
        logger.info("所有配置文件都已存在")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())