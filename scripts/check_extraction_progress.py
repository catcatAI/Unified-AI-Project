#!/usr/bin/env python3
"""
快速檢查Common Voice解壓進度
"""

import json
from pathlib import Path
from datetime import datetime

def check_extraction_status():
    base_dir = Path("d:/Projects/Unified-AI-Project/data/common_voice_zh")
    progress_file = base_dir / "extraction_progress.json"
    
    print("🚀 Common Voice 解壓進度檢查")
    print("=" * 40)
    
    # 檢查進度文件
    if progress_file.exists():
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            
            for dataset_name, info in progress_data.items():
                extracted = info.get('extracted_count', 0)
                total = info.get('total_count', 0)
                if total > 0:
                    percentage = (extracted / total) * 100
                    print(f"📊 {dataset_name}: {extracted:,}/{total:,} ({percentage:.2f}%)")
                else:
                    print(f"📊 {dataset_name}: {extracted:,} 個文件")
                    
                last_update = info.get('last_update', 'Unknown')
                print(f"   最後更新: {last_update}")
                print()
        except Exception as e:
            print(f"❌ 無法讀取進度文件: {e}")
    else:
        print("📝 尚未創建進度文件")
    
    # 檢查實際目錄
    print("\n📁 實際目錄狀態:")
    for dirname in ['zh-CN', 'zh-TW', 'singleword']:
        dir_path = base_dir / dirname
        if dir_path.exists():
            try:
                file_count = len(list(dir_path.rglob('*')))
                print(f"✅ {dirname}: {file_count:,} 個項目")
            except Exception as e:
                print(f"⚠️ {dirname}: 檢查失敗 - {e}")
        else:
            print(f"❌ {dirname}: 目錄不存在")

if __name__ == "__main__":
    check_extraction_status()