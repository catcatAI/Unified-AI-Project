#!/usr/bin/env python3
"""
Common Voice 數據集解壓縮工具 - 改進版
支持續傳、進度保存和更好的錯誤處理
"""

import tarfile
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('common_voice_extraction_improved.log'),
        logging.StreamHandler()
    ]
)
logger: Any = logging.getLogger(__name__)

class ImprovedCommonVoiceExtractor:
    """改進的Common Voice 解壓器"""

    def __init__(self, base_dir: str = "d:/Projects/Unified-AI-Project/data/common_voice_zh") -> None:
        self.base_dir = Path(base_dir)
        self.progress_file = self.base_dir / "extraction_progress.json"

    def save_progress(self, dataset_name: str, extracted_count: int, total_count: int) -> None:
        """保存解壓進度"""
        progress_data = {}
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
            except:
                progress_data = {}

        progress_data[dataset_name] = {
            'extracted_count': extracted_count,
            'total_count': total_count,
            'last_update': datetime.now().isoformat()
        }

        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2)

    def load_progress(self, dataset_name: str) -> int:
        """加載解壓進度"""
        if not self.progress_file.exists():
            return 0

        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                return progress_data.get(dataset_name, {}).get('extracted_count', 0)
        except:
            return 0

    def extract_with_resume(self, archive_path: Path, extract_dir: Path, dataset_name: str) -> bool:
        """支持續傳的解壓縮"""
        try:
            logger.info(f"🔄 開始解壓縮: {archive_path.name}")

            # 創建解壓目錄
            extract_dir.mkdir(parents=True, exist_ok=True)

            # 加載之前的進度
            start_from = self.load_progress(dataset_name)

            with tarfile.open(archive_path, 'r:gz') as tar:
                members = tar.getmembers()
                total_files = len(members)

                logger.info(f"📊 總文件數: {total_files}")
                if start_from > 0:
                    logger.info(f"🔄 從第 {start_from} 個文件續傳")

                # 使用 extractall 但只處理未解壓的文件
                if start_from == 0:
                    # 第一次解壓，使用 extractall 更高效
                    try:
                        logger.info("⚡ 使用高速解壓模式...")
                        tar.extractall(path=extract_dir, filter='data')
                        logger.info(f"✅ 解壓縮完成: {dataset_name}")
                        self.save_progress(dataset_name, total_files, total_files)
                        return True
                    except TypeError:
                        # Python版本不支持filter參數
                        logger.info("⚡ 使用標準解壓模式...")
                        tar.extractall(path=extract_dir)
                        logger.info(f"✅ 解壓縮完成: {dataset_name}")
                        self.save_progress(dataset_name, total_files, total_files)
                        return True
                    except Exception as e:
                        logger.warning(f"⚠️ 高速解壓失敗，切換到逐個文件模式: {e}")
                        # 繼續使用逐個文件模式

                # 逐個文件解壓（續傳模式）
                for i, member in enumerate(members):
                    if i < start_from:
                        continue

                    try:
                        tar.extract(member, extract_dir)

                        # 每1000個文件顯示進度並保存
                        if (i + 1) % 1000 == 0:
                            progress = ((i + 1) / total_files) * 100
                            logger.info(f"📈 解壓進度: {progress:.1f}% ({i + 1}/{total_files})")
                            self.save_progress(dataset_name, i + 1, total_files)

                    except KeyboardInterrupt:
                        logger.info(f"⏸️ 用戶中斷，已保存進度: {i}/{total_files}")
                        self.save_progress(dataset_name, i, total_files)
                        return False
                    except Exception as e:
                        logger.warning(f"⚠️ 跳過文件 {member.name}: {e}")
                        continue

                logger.info(f"✅ 解壓縮完成: {dataset_name}")
                self.save_progress(dataset_name, total_files, total_files)
                return True

        except Exception as e:
            logger.error(f"❌ 解壓縮失敗 {dataset_name}: {e}")
            return False

    def extract_all_datasets(self) -> 'dict[str, bool]':
        """解壓所有數據集"""
        datasets = [
            {
                'file': 'cv-corpus-22.0-2025-06-20-zh-CN.tar.gz',
                'name': 'zh-CN',
                'display_name': 'Common Voice 中文大陸 v22.0'
            },
            {
                'file': 'cv-corpus-22.0-2025-06-20-zh-TW.tar.gz',
                'name': 'zh-TW',
                'display_name': 'Common Voice 中文台灣 v22.0'
            },
            {
                'file': 'cv-corpus-7.0-singleword.tar.gz',
                'name': 'singleword',
                'display_name': 'Common Voice 單字數據集 v7.0'
            }
        ]

        results = {}

        for dataset in datasets:
            archive_path = self.base_dir / dataset['file']
            extract_dir = self.base_dir / dataset['name']

            if not archive_path.exists():
                logger.warning(f"⚠️ 文件不存在: {archive_path}")
                results[dataset['name']] = False
                continue

            # 檢查是否已完全解壓
            progress = self.load_progress(dataset['name'])
            if progress > 0:
                logger.info(f"🔄 {dataset['display_name']} 將從中斷處續傳")

            success = self.extract_with_resume(archive_path, extract_dir, dataset['name'])
            results[dataset['name']] = success

        return results

def main() -> None:
    """主函數"""
    print("🚀 Common Voice 數據集解壓縮工具 - 改進版")
    print("支持續傳和進度保存")
    print("=" * 60)

    extractor = ImprovedCommonVoiceExtractor()

    # 開始解壓
    results = extractor.extract_all_datasets()

    # 顯示結果
    print("\n📊 解壓結果:")
    for dataset_name, success in results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"  • {dataset_name}: {status}")

    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)

    print(f"\n🎉 完成! 成功解壓 {success_count}/{total_count} 個數據集")

    if success_count < total_count:
        print("\n💡 提示: 如果解壓被中斷，可以重新運行此腳本續傳")

if __name__ == "__main__":
    main()