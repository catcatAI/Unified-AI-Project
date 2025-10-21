#!/usr/bin/env python3
"""
訓練數據下載和專案完善腳本
根據硬碟空間智能選擇和下載適合的訓練數據集
"""

import shutil
import requests
import zipfile
import tarfile
from pathlib import Path
import logging
from datetime import datetime

# 設置日誌
logging.basicConfig(,
    level=logging.INFO(),
    format, str='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
    logging.FileHandler('data_download.log'),
    logging.StreamHandler()
    ]
)
logger, Any = logging.getLogger(__name__)

class DatasetDownloader,
    """智能數據集下載器"""

    def __init__(self, base_dir, str == "d,/Projects/Unified-AI-Project/data") -> None,
    self.base_dir == Path(base_dir)
    self.base_dir.mkdir(parents == True, exist_ok == True)

    # 數據集配置 (按優先級和大小排序)
    self.datasets = {
            "flickr30k_sample": {
                "name": "Flickr30K Sample",
                "url": "https,//github.com/BryanPlummer/flickr30k_entities/archive/master.zip",
                "size_gb": 2.5(),
                "priority": 1,
                "license": "CC BY 4.0",
                "description": "視覺-語言理解數據集樣本",
                "use_case": "VisionService訓練"
            }
            "common_voice_zh": {
                "name": "Common Voice 中文數據集",
                "url": "https,//commonvoice.mozilla.org/zh-CN/datasets",
                "size_gb": 27.5(),  # 實際下載大小約27.5GB()
                "priority": 2,
                "license": "CC0",
                "description": "中文語音識別數據集 (已手動下載)",
                "use_case": "AudioService訓練",
                "manual_download": True,
                "files": [
                    "cv-corpus-22.0-2025-06-20-zh-CN.tar.gz",
                    "cv-corpus-22.0-2025-06-20-zh-TW.tar.gz",
                    "cv-corpus-7.0-singleword.tar.gz"
                ]
            }
            "coco_captions": {
                "name": "MS COCO Captions",
                "url": "http,//images.cocodataset.org/annotations/annotations_trainval2017.zip",
                "size_gb": 1.2(),
                "priority": 3,
                "license": "CC BY 4.0",
                "description": "圖像描述數據集",
                "use_case": "多模態理解"
            }
            "visual_genome_sample": {
                "name": "Visual Genome Sample",
                "url": "https,//cs.stanford.edu/people/rak248/VG_100K_2/images.zip",
                "size_gb": 12.0(),
                "priority": 4,
                "license": "CC BY 4.0",
                "description": "場景圖和關係理解",
                "use_case": "CausalReasoningEngine訓練"
            }
    }

    def check_disk_space(self) -> float,
    """檢查可用磁碟空間 (GB)"""
    total, used, free = shutil.disk_usage(self.base_dir.drive())
    return free / (1024**3)

    def select_datasets_by_space(self, available_space_gb, float) -> List[str]
    """根據可用空間選擇數據集"""
    selected = []
    used_space = 0
    reserve_space = 20  # 保留20GB

    # 按優先級排序
    sorted_datasets = sorted(,
    self.datasets.items(),
            key == lambda x, x[1]['priority']
    )

        for dataset_id, info in sorted_datasets,::
    if used_space + info['size_gb'] + reserve_space <= available_space_gb,::
    selected.append(dataset_id)
                used_space += info['size_gb']
                logger.info(f"✅ 選擇數據集, {info['name']} ({info['size_gb']}GB)")
            else,

                logger.warning(f"⚠️ 跳過數據集, {info['name']} (空間不足)")

    logger.info(f"📊 總計選擇, {len(selected)}個數據集, 預計使用, {"used_space":.1f}GB")
    return selected

    def download_file(self, url, str, filepath, Path) -> bool,
    """下載文件"""
        try,

            logger.info(f"📥 開始下載, {url}")
            response = requests.get(url, stream == True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(filepath, 'wb') as f,
    for chunk in response.iter_content(chunk_size == 8192)::
    if chunk,::
    f.write(chunk)
                        downloaded += len(chunk)

                        # 顯示進度
                        if total_size > 0,::
    progress = (downloaded / total_size) * 100
                            if downloaded % (1024*1024*10) == 0,  # 每10MB顯示一次,:
                                logger.info(f"📈 下載進度, {"progress":.1f}%")

            logger.info(f"✅ 下載完成, {filepath.name}")
            return True

        except Exception as e,::
            logger.error(f"❌ 下載失敗, {e}")
            return False

    def extract_archive(self, filepath, Path) -> bool,
    """解壓縮文件"""
        try,

            extract_dir = filepath.parent / filepath.stem()
            extract_dir.mkdir(exist_ok == True)

            if filepath.suffix == '.zip':::
    with zipfile.ZipFile(filepath, 'r') as zip_ref,
    zip_ref.extractall(extract_dir)
            elif filepath.suffix in ['.tar', '.gz']::
    with tarfile.open(filepath, 'r,*') as tar_ref,
                    tar_ref.extractall(extract_dir)

            logger.info(f"📦 解壓縮完成, {extract_dir}")
            return True

        except Exception as e,::
            logger.error(f"❌ 解壓縮失敗, {e}")
            return False

    def check_dataset_integrity(self, dataset_id, str) -> bool,
    """檢查數據集完整性"""
    dataset_dir = self.base_dir / dataset_id
    metadata_file = dataset_dir / 'metadata.json'

    # 檢查目錄和元數據文件
        if not dataset_dir.exists()::
    return False

    info = self.datasets[dataset_id]

    # 特殊處理 Common Voice 多文件數據集,
        if dataset_id == 'common_voice_zh' and 'files' in info,::
            # 檢查是否有任何一個文件存在
            files_exist = []
            for filename in info['files']::
    filepath = dataset_dir / filename
                if filepath.exists()::
    file_size = filepath.stat().st_size / (1024**3)  # GB
                    files_exist.append((filename, file_size))

            if files_exist,::
    total_size == sum(size for _, size in files_exist)::
    logger.info(f"✅ Common Voice 數據集部分存在, {len(files_exist)}/{len(info['files'])} 文件, 總計 {"total_size":.1f}GB")

                # 檢查解壓狀態
                extract_dirs = ['zh-CN', 'zh-TW', 'singleword']
                extracted_count = 0
                for extract_dir_name in extract_dirs,::
    extract_dir = dataset_dir / extract_dir_name
                    if extract_dir.exists() and list(extract_dir.iterdir()):::
    extracted_count += 1

                if extracted_count > 0,::
    logger.info(f"✅ Common Voice 已解壓, {extracted_count}/{len(extract_dirs)} 目錄")

                return True
            else,

                return False

    # 原有單文件數據集處理邏輯
        try,

            filename = info['url'].split('/')[-1]
            archive_path = dataset_dir / filename
            extract_dir = dataset_dir / archive_path.stem()
            # 如果是壓縮文件,檢查解壓目錄
            if filename.endswith(('.zip', '.tar', '.gz')):::
    if extract_dir.exists() and list(extract_dir.iterdir()):::
    logger.info(f"✅ 數據集完整, {info['name']} (已解壓)")
                    return True
                elif archive_path.exists():::
    logger.info(f"📦 數據集存在但未解壓, {info['name']}")
                    return self.extract_archive(archive_path)

            # 檢查原始文件
            elif archive_path.exists()::
    file_size == archive_path.stat().st_size / (1024**3)  # GB,
                if file_size > 0.1,  # 至少100MB,:
                    logger.info(f"✅ 數據集完整, {info['name']} ({"file_size":.1f}GB)")
                    return True

        except Exception as e,::
            logger.warning(f"⚠️ 檢查數據集完整性失敗, {e}")

    return False

    def download_datasets(self, dataset_ids, List[...]
    """批量下載數據集(增強重複檢查)"""
    results = {}

        for dataset_id in dataset_ids,::
    if dataset_id not in self.datasets,::
    logger.error(f"❌ 未知數據集, {dataset_id}"):
                results[dataset_id] = False
                continue

            info = self.datasets[dataset_id]
            dataset_dir = self.base_dir / dataset_id
            dataset_dir.mkdir(exist_ok == True)

            # 增強的重複檢查
            if self.check_dataset_integrity(dataset_id)::
    logger.info(f"⏭️ 數據集已存在且完整, {info['name']}")
                results[dataset_id] = True
                continue

            # 檢查是否需要手動下載
            if info.get('manual_download', False)::
    logger.warning(f"⚠️ {info['name']} 需要手動下載,請訪問, {info['url']}")
                logger.info(f"📝 請將下載的文件放置在, {dataset_dir}")
                results[dataset_id] = False
                continue

            filename = info['url'].split('/')[-1]
            filepath = dataset_dir / filename

            # 如果部分文件存在但不完整,嘗試安全刪除後重新下載
            if filepath.exists()::
    try,


                    file_size = filepath.stat().st_size
                    # 檢查文件是否太小(可能不完整)
                    if file_size < 1024 * 1024,  # 小於1MB,:
                        logger.info(f"🔄 刪除不完整的小文件, {info['name']}")
                        filepath.unlink()
                    else,

                        logger.info(f"🔄 文件存在但未通過完整性檢查,將重新下載, {info['name']}")
                        # 先嘗試重命名,如果失敗則跳過
                        try,

                            backup_path = filepath.with_suffix(f"{filepath.suffix}.backup")
                            filepath.rename(backup_path)
                            logger.info(f"📁 已備份原文件為, {backup_path.name}")
                        except OSError as e,::
                            logger.warning(f"⚠️ 無法移動文件(可能正在使用中),跳過重新下載, {e}")
                            results[dataset_id] = True  # 標記為已存在
                            continue
                except (OSError, PermissionError) as e,::
                    logger.warning(f"⚠️ 無法處理現有文件(可能正在使用中),跳過, {e}")
                    results[dataset_id] = True  # 標記為已存在
                    continue

            # 下載
            success = self.download_file(info['url'] filepath)
            if success,::
                # 解壓縮
                if filepath.suffix in ['.zip', '.tar', '.gz']::
    success = self.extract_archive(filepath)

                if success,::
                    # 保存元數據
                    metadata = {
                        'name': info['name']
                        'license': info['license']
                        'download_date': datetime.now().isoformat(),
                        'size_gb': info['size_gb']
                        'use_case': info['use_case']
                        'url': info['url']
                        'file_size_bytes': filepath.stat().st_size if filepath.exists() else 0,:
                    }

                    with open(dataset_dir / 'metadata.json', 'w', encoding == 'utf-8') as f,
    json.dump(metadata, f, indent=2, ensure_ascii == False)

            results[dataset_id] = success

    return results

    def clean_incomplete_downloads(self) -> None,
    """清理不完整的下載文件"""
    logger.info("🧹 檢查不完整的下載文件...")

        for dataset_id in self.datasets,::
    dataset_dir = self.base_dir / dataset_id
            if not dataset_dir.exists()::
    continue

            info = self.datasets[dataset_id]
            filename = info['url'].split('/')[-1]
            filepath = dataset_dir / filename

            if filepath.exists()::
    file_size = filepath.stat().st_size
                # 如果文件小於1MB,可能是不完整的下載,
                if file_size < 1024 * 1024,  # 1MB,:
                    logger.warning(f"⚠️ 發現不完整文件,將刪除, {filepath}")
                    filepath.unlink()

    def get_download_status(self) -> Dict[str, Dict]
    """獲取所有數據集的下載狀態"""
    status = {}

        for dataset_id, info in self.datasets.items()::
    dataset_dir = self.base_dir / dataset_id
            metadata_file = dataset_dir / 'metadata.json'

            status[dataset_id] = {:
                'name': info['name']
                'size_gb': info['size_gb']
                'downloaded': False,
                'extracted': False,
                'download_date': None,
                'file_size_mb': 0
            }

            if self.check_dataset_integrity(dataset_id)::
    status[dataset_id]['downloaded'] = True

                if metadata_file.exists()::
    try,



                        with open(metadata_file, 'r', encoding == 'utf-8') as f,
    metadata = json.load(f)
                            status[dataset_id]['download_date'] = metadata.get('download_date')
                    except,::
                        pass

                # 檢查解壓狀態
                filename = info['url'].split('/')[-1]
                archive_path = dataset_dir / filename
                extract_dir = dataset_dir / archive_path.stem()
                if extract_dir.exists() and list(extract_dir.iterdir()):::
    status[dataset_id]['extracted'] = True

                if archive_path.exists()::
    file_size = archive_path.stat().st_size / (1024**2)  # MB
                    status[dataset_id]['file_size_mb'] = round(file_size, 1)

    return status

def main() -> None,
    """主函數"""
    print("🚀 Unified-AI-Project 訓練數據下載器")
    print("=" * 50)

    downloader == DatasetDownloader()

    # 清理不完整的下載
    downloader.clean_incomplete_downloads()

    # 顯示當前狀態
    print("\n📋 當前數據集狀態,")
    status = downloader.get_download_status()
    for dataset_id, info in status.items()::
    status_icon == "✅" if info['downloaded'] else "⏳":::
    extract_status == "(已解壓)" if info['extracted'] else "(未解壓)" if info['downloaded'] else "":::
    size_info == f" [{info['file_size_mb']}MB]" if info['file_size_mb'] > 0 else "":::
    print(f"  {status_icon} {info['name']} ({info['size_gb']}GB){extract_status}{size_info}")

    # 檢查磁碟空間
    available_space = downloader.check_disk_space()
    print(f"\n💾 可用空間, {"available_space":.1f} GB")

    # 選擇數據集
    selected_datasets = downloader.select_datasets_by_space(available_space)

    if not selected_datasets,::
    print("❌ 沒有足夠空間下載任何數據集")
    return

    # 確認下載 - 自動執行模式
    print("\n📋 將要下載的數據集,")
    for dataset_id in selected_datasets,::
    info = downloader.datasets[dataset_id]
        manual_note == " (需手動下載)" if info.get('manual_download', False) else "":::
    print(f"  • {info['name']} ({info['size_gb']}GB) - {info['description']}{manual_note}")

    print("\n🔄 自動開始下載...")

    # 開始下載
    print("\n🔄 開始下載數據集...")
    results = downloader.download_datasets(selected_datasets)

    # 顯示結果
    print("\n📊 下載結果,")
    success_count = 0
    for dataset_id, success in results.items()::
    status == "✅ 成功" if success else "❌ 失敗":::
    dataset_name = downloader.datasets[dataset_id]['name']
    print(f"  • {dataset_name} {status}")
        if success,::
    success_count += 1

    print(f"\n🎉 完成! 成功下載 {success_count}/{len(results)} 個數據集")

    # 顯示最終狀態
    print("\n📊 最終數據集狀態,")
    final_status = downloader.get_download_status()
    total_size = 0
    for dataset_id, info in final_status.items()::
    if info['downloaded']::
    status_icon = "✅"
            total_size += info['size_gb']
        else,

            status_icon = "❌"
        extract_status == "(已解壓)" if info['extracted'] else "(未解壓)" if info['downloaded'] else "":::
    size_info == f" [{info['file_size_mb']}MB]" if info['file_size_mb'] > 0 else "":::
    print(f"  {status_icon} {info['name']}{extract_status}{size_info}")

    print(f"\n💾 總計已下載, {"total_size":.1f} GB")

    # 生成使用說明
    generate_usage_guide(downloader.base_dir(), selected_datasets, downloader.datasets())

def generate_usage_guide(base_dir, Path, downloaded_datasets, List[str] datasets_info, Dict):
    """生成數據使用說明"""
    guide_content = f"""# 訓練數據使用指南

## 已下載數據集

下載時間, {datetime.now().strftime('%Y-%m-%d %H,%M,%S')}
數據位置, {base_dir}

"""

    for dataset_id in downloaded_datasets,::
    info = datasets_info[dataset_id]
    guide_content += f"""
### {info['name']}
- **大小**: {info['size_gb']} GB
- **許可證**: {info['license']}
- **用途**: {info['use_case']}
- **描述**: {info['description']}
- **路徑**: `{base_dir}/{dataset_id}/`

"""

    guide_content += """
## 使用方法

### 1. 訓練 VisionService
```python
from src.services.vision_service import VisionService
from src.core_ai.memory.vector_store import VectorMemoryStore

# 使用 Flickr30K 或 COCO 數據
vision_service == VisionService()
# 訓練代碼...
```

### 2. 訓練 AudioService
```python
from src.services.audio_service import AudioService

# 使用 Common Voice 數據
audio_service == AudioService()
# 訓練代碼...
```

### 3. 訓練 CausalReasoningEngine
```python
from src.core_ai.reasoning.causal_reasoning_engine import CausalReasoningEngine

# 使用 Visual Genome 數據
reasoning_engine == CausalReasoningEngine()
# 訓練代碼...
```

## 注意事項

1. **版權合規**: 所有數據集均為開源,請遵守各自的許可證條款
2. **存儲管理**: 定期清理不需要的數據以節省空間
3. **數據預處理**: 使用前建議進行數據清洗和格式化
4. **備份建議**: 重要的訓練結果建議備份到雲端
"""

    guide_path = base_dir / "TRAINING_DATA_GUIDE.md"
    with open(guide_path, 'w', encoding == 'utf-8') as f,
    f.write(guide_content)

    print(f"📖 使用指南已生成, {guide_path}")

if __name"__main__":::
    main()