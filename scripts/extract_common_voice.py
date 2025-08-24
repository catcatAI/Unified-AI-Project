#!/usr/bin/env python3
"""
Common Voice 數據集解壓縮腳本
"""

import os
import tarfile
import gzip
from pathlib import Path
import logging
from datetime import datetime
import json

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('common_voice_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def extract_tar_gz(archive_path: Path, extract_dir: Path) -> bool:
    """解壓縮tar.gz文件"""
    try:
        logger.info(f"📦 開始解壓縮: {archive_path.name}")
        
        # 創建解壓目錄
        extract_dir.mkdir(exist_ok=True)
        
        with tarfile.open(archive_path, 'r:gz') as tar:
            # 使用 extractall 方法，更高效
            try:
                # Python 3.12+ 支持 filter 參數以解決 deprecation warning
                tar.extractall(path=extract_dir, filter='data')
                logger.info(f"✅ 解壓縮完成: {archive_path.name}")
                return True
            except TypeError:
                # 舊版本 Python 沒有 filter 參數，使用傳統方法
                logger.info("使用傳統方法解壓縮...")
                tar.extractall(path=extract_dir)
                logger.info(f"✅ 解壓縮完成: {archive_path.name}")
                return True
            
    except Exception as e:
        logger.error(f"❌ 解壓縮失敗 {archive_path.name}: {e}")
        return False

def process_common_voice_datasets():
    """處理所有Common Voice數據集"""
    base_dir = Path("d:/Projects/Unified-AI-Project/data/common_voice_zh")
    
    datasets = [
        {
            'file': 'cv-corpus-22.0-2025-06-20-zh-CN.tar.gz',
            'name': 'Common Voice 中文大陸 v22.0',
            'extract_dir': 'zh-CN'
        },
        {
            'file': 'cv-corpus-22.0-2025-06-20-zh-TW.tar.gz', 
            'name': 'Common Voice 中文台灣 v22.0',
            'extract_dir': 'zh-TW'
        },
        {
            'file': 'cv-corpus-7.0-singleword.tar.gz',
            'name': 'Common Voice 單字數據集 v7.0', 
            'extract_dir': 'singleword'
        }
    ]
    
    results = {}
    total_size = 0
    
    for dataset in datasets:
        archive_path = base_dir / dataset['file']
        extract_dir = base_dir / dataset['extract_dir']
        
        if not archive_path.exists():
            logger.warning(f"⚠️ 文件不存在: {archive_path}")
            results[dataset['name']] = False
            continue
        
        # 檢查是否已經解壓
        if extract_dir.exists() and list(extract_dir.iterdir()):
            logger.info(f"⏭️ 已解壓: {dataset['name']}")
            results[dataset['name']] = True
        else:
            # 解壓縮
            success = extract_tar_gz(archive_path, extract_dir)
            results[dataset['name']] = success
        
        # 計算大小
        if archive_path.exists():
            file_size = archive_path.stat().st_size / (1024**3)  # GB
            total_size += file_size
    
    # 生成元數據
    metadata = {
        'datasets': datasets,
        'extraction_date': datetime.now().isoformat(),
        'total_size_gb': round(total_size, 2),
        'results': results,
        'license': 'CC0 (Public Domain)',
        'use_case': 'AudioService訓練 - 中文語音識別'
    }
    
    with open(base_dir / 'metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # 顯示結果
    print("\n📊 Common Voice 數據集處理結果:")
    for name, success in results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"  • {name}: {status}")
    
    print(f"\n💾 總大小: {total_size:.1f} GB")
    print(f"📖 元數據已保存: {base_dir / 'metadata.json'}")
    
    return results

if __name__ == "__main__":
    print("🚀 Common Voice 數據集解壓縮工具")
    print("=" * 50)
    
    results = process_common_voice_datasets()
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    print(f"\n🎉 完成! 成功處理 {success_count}/{total_count} 個數據集")