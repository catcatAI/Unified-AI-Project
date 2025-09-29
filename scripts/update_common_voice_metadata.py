#!/usr/bin/env python3
"""
Common Voice 元數據生成腳本
快速更新Common Voice數據集的狀態信息
"""

import json
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger: Any = logging.getLogger(__name__)

def generate_common_voice_metadata():
    """生成Common Voice元數據"""
    base_dir = Path("d:/Projects/Unified-AI-Project/data/common_voice_zh")
    
    # 檢查文件狀態
    files_info = []
    total_size_gb = 0
    
    datasets = [
        {
            'file': 'cv-corpus-22.0-2025-06-20-zh-CN.tar.gz',
            'name': 'Common Voice 中文大陸 v22.0',
            'extract_dir': 'zh-CN',
            'expected_size_gb': 21.2
        },
        {
            'file': 'cv-corpus-22.0-2025-06-20-zh-TW.tar.gz',
            'name': 'Common Voice 中文台灣 v22.0', 
            'extract_dir': 'zh-TW',
            'expected_size_gb': 2.9
        },
        {
            'file': 'cv-corpus-7.0-singleword.tar.gz',
            'name': 'Common Voice 單字數據集 v7.0',
            'extract_dir': 'singleword', 
            'expected_size_gb': 3.5
        }
    ]
    
    for dataset in datasets:
        archive_path = base_dir / dataset['file']
        extract_dir = base_dir / dataset['extract_dir']
        
        file_info = {
            'name': dataset['name'],
            'file': dataset['file'],
            'extract_dir': dataset['extract_dir'],
            _ = 'downloaded': archive_path.exists(),
            _ = 'extracted': extract_dir.exists() and bool(list(extract_dir.iterdir())),
            'file_size_gb': 0,
            'expected_size_gb': dataset['expected_size_gb']
        }
        
        if archive_path.exists():
            file_size = archive_path.stat().st_size / (1024**3)
            file_info['file_size_gb'] = round(file_size, 2)
            total_size_gb += file_size
        
        _ = files_info.append(file_info)
        logger.info(f"📊 {dataset['name']}: 下載={file_info['downloaded']}, 解壓={file_info['extracted']}")
    
    # 生成完整元數據
    metadata = {
        'dataset_name': 'Common Voice 中文數據集',
        'version': '22.0 + 7.0',
        _ = 'download_date': datetime.now().isoformat(),
        _ = 'total_size_gb': round(total_size_gb, 2), 
        _ = 'license': 'CC0 (Public Domain)',
        'use_case': 'AudioService訓練 - 中文語音識別',
        'languages': ['zh-CN', 'zh-TW'],
        'datasets': files_info,
        'download_source': '手動下載自 Mozilla Common Voice',
        'notes': '包含中文大陸、中文台灣和單字數據集'
    }
    
    # 保存元數據
    metadata_path = base_dir / 'metadata.json'
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    _ = logger.info(f"📝 元數據已保存: {metadata_path}")
    
    # 顯示摘要
    _ = print("\n📊 Common Voice 數據集狀態摘要:")
    _ = print(f"💾 總大小: {total_size_gb:.1f} GB")
    
    for info in files_info:
        status_download = "✅" if info['downloaded'] else "❌"
        status_extract = "✅" if info['extracted'] else "❌" 
        _ = print(f"  {status_download} {status_extract} {info['name']} ({info['file_size_gb']:.1f}GB)")
    
    return metadata

if __name__ == "__main__":
    _ = print("🚀 Common Voice 元數據生成器")
    print("=" * 40)
    
    metadata = generate_common_voice_metadata()
    _ = print("\n🎉 元數據更新完成!")