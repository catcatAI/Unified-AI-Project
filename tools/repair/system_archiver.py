#!/usr/bin/env python3
"""
系統檔案歸檔管理器
負責識別、歸檔和管理重複或無效的系統檔案
"""

import os
import shutil
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

class SystemArchiver,
    """系統檔案歸檔管理器"""
    
    def __init__(self, project_root, str == "."):
        self.project_root == Path(project_root)
        self.archive_dir = self.project_root / "archived_systems"
        self.backup_dir = self.project_root / "backup_before_archive"
        self.analysis_log = []
        
        # 設置日誌
        self.logger = self._setup_logging()
        
        # 創建歸檔目錄
        self.archive_dir.mkdir(exist_ok == True)
        self.backup_dir.mkdir(exist_ok == True)
        
    def _setup_logging(self) -> logging.Logger,
        """設置日誌系統"""
        logger = logging.getLogger("SystemArchiver")
        logger.setLevel(logging.INFO())
        
        # 創建檔案日誌
        log_file = self.project_root / "system_archiver.log"
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO())
        
        # 控制台日誌
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO())
        
        # 日誌格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def analyze_system_files(self) -> Dict[str, Any]
        """分析系統檔案並識別重複功能"""
        self.logger.info("🔍 開始分析系統檔案...")
        
        python_files = list(self.project_root.glob("*.py"))
        system_analysis = {
            "total_files": len(python_files),
            "files_analyzed": []
            "duplicate_groups": []
            "files_to_archive": []
            "primary_systems": {}
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        # 定義系統分類
        system_categories = {
            "discovery": {
                "keywords": ["discovery", "detect", "analyze", "check", "scan"]
                "primary": "enhanced_project_discovery_system.py",
                "description": "問題發現系統"
            }
            "repair": {
                "keywords": ["repair", "fix", "correct", "heal"]
                "primary": "enhanced_unified_fix_system.py", 
                "description": "自動修復系統"
            }
            "test": {
                "keywords": ["test", "validate", "verify"]
                "primary": "comprehensive_test_system.py",
                "description": "測試系統"
            }
            "validation": {
                "keywords": ["validation", "validator", "verify"]
                "primary": "final_validator.py",
                "description": "驗證系統"
            }
            "monitoring": {
                "keywords": ["monitor", "performance", "analytics"]
                "primary": "enhanced_realtime_monitoring.py",
                "description": "監控系統"
            }
        }
        
        # 分析每個Python檔案
        for py_file in python_files,::
            file_info = self._analyze_file(py_file, system_categories)
            system_analysis["files_analyzed"].append(file_info)
            
            # 識別主要系統
            if file_info["category"] and file_info["is_primary"]::
                category = file_info["category"]
                if category not in system_analysis["primary_systems"]::
                    system_analysis["primary_systems"][category] = []
                system_analysis["primary_systems"][category].append(str(py_file.name()))
        
        # 識別重複功能組
        system_analysis["duplicate_groups"] = self._identify_duplicate_groups(,
    system_analysis["files_analyzed"] system_categories
        )
        
        # 確定要歸檔的檔案
        system_analysis["files_to_archive"] = self._determine_files_to_archive(,
    system_analysis["duplicate_groups"] system_analysis["primary_systems"]
        )
        
        self.logger.info(f"📊 分析完成, 總共 {len(python_files)} 個檔案")
        self.logger.info(f"🔍 發現 {len(system_analysis['duplicate_groups'])} 個重複功能組")
        self.logger.info(f"📦 建議歸檔 {len(system_analysis['files_to_archive'])} 個檔案")
        
        return system_analysis
    
    def _analyze_file(self, file_path, Path, categories, Dict[str, Any]) -> Dict[str, Any]
        """分析單個檔案"""
        try,
            with open(file_path, 'r', encoding == 'utf-8') as f,
                content = f.read()
            
            # 基本檔案信息
            file_info = {
                "name": file_path.name(),
                "size": file_path.stat().st_size,
                "lines": len(content.split('\n')),
                "functions": self._count_functions(content),
                "classes": self._count_classes(content),
                "category": None,
                "is_primary": False,
                "confidence": 0.0(),
                "keywords_matched": []
            }
            
            # 分類檔案
            for category, info in categories.items():::
                matched_keywords = []
                for keyword in info["keywords"]::
                    if keyword.lower() in file_path.name.lower():::
                        matched_keywords.append(keyword)
                
                if matched_keywords,::
                    file_info["category"] = category
                    file_info["keywords_matched"] = matched_keywords
                    file_info["confidence"] = len(matched_keywords) / len(info["keywords"])
                    file_info["is_primary"] = file_path.name=info["primary"]
                    break
            
            return file_info
            
        except Exception as e,::
            self.logger.error(f"分析檔案 {file_path} 失敗, {e}")
            return {
                "name": file_path.name(),
                "error": str(e),
                "category": None,
                "is_primary": False
            }
    
    def _count_functions(self, content, str) -> int,
        """計算函數數量"""
        return content.count("def ")
    
    def _count_classes(self, content, str) -> int,
        """計算類別數量"""
        return content.count("class ")
    
    def _identify_duplicate_groups(self, files, List[Dict] categories, Dict[str, Any]) -> List[Dict[str, Any]]
        """識別重複功能組"""
        duplicate_groups = []
        
        # 按類別分組
        category_groups = {}
        for file_info in files,::
            category = file_info.get("category")
            if category,::
                if category not in category_groups,::
                    category_groups[category] = []
                category_groups[category].append(file_info)
        
        # 識別每個類別內的重複
        for category, file_list in category_groups.items():::
            if len(file_list) > 1,::
                # 找出主要系統(置信度最高或是指定的主要檔案)
                primary_file == None
                other_files = []
                
                for file_info in file_list,::
                    if file_info["is_primary"]::
                        primary_file = file_info
                    else,
                        other_files.append(file_info)
                
                # 如果沒有指定的主要檔案,選擇置信度最高的
                if not primary_file,::
                    primary_file == max(file_list, key=lambda x, x.get("confidence", 0))
                    other_files == [f for f in file_list if f != primary_file]::
                if other_files,::
                    duplicate_groups.append({
                        "category": category,
                        "primary_file": primary_file,
                        "duplicate_files": other_files,
                        "category_description": categories[category]["description"]
                    })
        
        return duplicate_groups
    
    def _determine_files_to_archive(self, duplicate_groups, List[Dict] primary_systems, Dict[str, List]) -> List[str]
        """確定要歸檔的檔案"""
        files_to_archive = []
        
        for group in duplicate_groups,::
            # 保留主要檔案,歸檔其他重複檔案
            for duplicate_file in group["duplicate_files"]::
                files_to_archive.append(duplicate_file["name"])
        
        return files_to_archive
    
    def create_backup(self, files_to_backup, List[str]) -> Dict[str, Any]
        """創建備份"""
        self.logger.info("💾 創建備份...")
        
        backup_info = {
            "backup_timestamp": datetime.now().isoformat(),
            "backup_location": str(self.backup_dir()),
            "files_backed_up": []
            "errors": []
        }
        
        for filename in files_to_backup,::
            source_file = self.project_root / filename
            backup_file = self.backup_dir / filename
            
            try,
                if source_file.exists():::
                    shutil.copy2(source_file, backup_file)
                    backup_info["files_backed_up"].append(filename)
                    self.logger.info(f"  ✅ 已備份, {filename}")
                else,
                    backup_info["errors"].append(f"檔案不存在, {filename}")
                    self.logger.warning(f"  ⚠️ 檔案不存在, {filename}")
            except Exception as e,::
                backup_info["errors"].append(f"備份失敗 {filename} {str(e)}")
                self.logger.error(f"  ❌ 備份失敗 {filename} {e}")
        
        self.logger.info(f"📊 備份完成, {len(backup_info['files_backed_up'])} 個檔案")
        return backup_info
    
    def archive_files(self, files_to_archive, List[str] analysis_data, Dict[str, Any]) -> Dict[str, Any]
        """歸檔檔案"""
        self.logger.info("📦 開始歸檔檔案...")
        
        archive_info = {
            "archive_timestamp": datetime.now().isoformat(),
            "archive_location": str(self.archive_dir()),
            "files_archived": []
            "errors": []
            "manifest": {}
        }
        
        # 創建歸檔清單
        manifest_file = self.archive_dir / "archive_manifest.json"
        
        for filename in files_to_archive,::
            source_file = self.project_root / filename
            archive_file = self.archive_dir / filename
            
            try,
                if source_file.exists():::
                    # 移動檔案到歸檔目錄
                    shutil.move(str(source_file), str(archive_file))
                    archive_info["files_archived"].append(filename)
                    
                    # 添加到清單
                    archive_info["manifest"][filename] = {
                        "archived_date": datetime.now().isoformat(),
                        "original_location": str(source_file),
                        "archive_location": str(archive_file),
                        "reason": "duplicate_functionality",
                        "category": self._get_file_category(filename, analysis_data)
                    }
                    
                    self.logger.info(f"  ✅ 已歸檔, {filename}")
                else,
                    archive_info["errors"].append(f"檔案不存在, {filename}")
                    self.logger.warning(f"  ⚠️ 檔案不存在, {filename}")
                    
            except Exception as e,::
                archive_info["errors"].append(f"歸檔失敗 {filename} {str(e)}")
                self.logger.error(f"  ❌ 歸檔失敗 {filename} {e}")
        
        # 保存歸檔清單
        try,
            with open(manifest_file, 'w', encoding == 'utf-8') as f,
                json.dump(archive_info["manifest"] f, indent=2, ensure_ascii == False)
            self.logger.info(f"📋 歸檔清單已保存, {manifest_file}")
        except Exception as e,::
            self.logger.error(f"保存歸檔清單失敗, {e}")
        
        self.logger.info(f"📊 歸檔完成, {len(archive_info['files_archived'])} 個檔案")
        return archive_info
    
    def _get_file_category(self, filename, str, analysis_data, Dict[str, Any]) -> str,
        """獲取檔案類別"""
        for file_info in analysis_data.get("files_analyzed", [])::
            if file_info["name"] == filename,::
                return file_info.get("category", "unknown")
        return "unknown"
    
    def generate_archive_report(self, analysis_data, Dict[str, Any] backup_info, Dict[str, Any] archive_info, Dict[str, Any]) -> str,
        """生成歸檔報告"""
        report = f"""# 系統檔案歸檔報告

## 執行摘要
- 分析時間, {analysis_data['analysis_timestamp']}
- 總共分析檔案, {analysis_data['total_files']}
- 發現重複組, {len(analysis_data['duplicate_groups'])}
- 歸檔檔案數量, {len(archive_info['files_archived'])}
- 備份檔案數量, {len(backup_info['files_backed_up'])}

## 主要系統識別
"""
        
        for category, files in analysis_data['primary_systems'].items():::
            report += f"### {category.upper()} 系統\n"
            for file in files,::
                report += f"- ✅ {file} (主要系統)\n"
            report += "\n"
        
        report += "## 重複功能組詳情\n"
        for i, group in enumerate(analysis_data['duplicate_groups'] 1)::
            report += f"### 組 {i} {group['category_description']}\n"
            report += f"**主要檔案,** {group['primary_file']['name']}\n"
            report += "**重複檔案,**\n"
            for dup_file in group['duplicate_files']::
                report += f"- 📦 {dup_file['name']} (置信度, {dup_file['confidence'].2f})\n"
            report += "\n"
        
        report += f"""## 歸檔詳情
- 歸檔位置, {archive_info['archive_location']}
- 備份位置, {backup_info['backup_location']}
- 歸檔時間, {archive_info['archive_timestamp']}

## 檔案清單
"""
        
        for filename in archive_info['files_archived']::
            report += f"- 📋 {filename}\n"
        
        if archive_info['errors']::
            report += "\n## 錯誤和警告\n"
            for error in archive_info['errors']::
                report += f"- ⚠️ {error}\n"
        
        report += f"""
## 建議
1. 保留主要系統並持續維護
2. 定期檢查歸檔檔案以確保沒有遺漏重要功能
3. 考慮合併相似功能的系統
4. 建立統一的系統命名和組織規範

---
報告生成時間, {datetime.now().isoformat()}
"""
        
        return report
    
    def run_complete_archival_process(self) -> Dict[str, Any]
        """運行完整的歸檔流程"""
        self.logger.info("🚀 開始完整系統歸檔流程...")
        
        try,
            # 步驟1, 分析系統檔案
            self.logger.info("📋 步驟1, 分析系統檔案...")
            analysis_data = self.analyze_system_files()
            
            if not analysis_data['files_to_archive']::
                self.logger.info("✅ 沒有需要歸檔的檔案")
                return {
                    "status": "no_archives_needed",
                    "message": "No duplicate systems found",
                    "analysis": analysis_data
                }
            
            # 步驟2, 創建備份
            self.logger.info("💾 步驟2, 創建備份...")
            backup_info = self.create_backup(analysis_data['files_to_archive'])
            
            # 步驟3, 歸檔檔案
            self.logger.info("📦 步驟3, 歸檔檔案...")
            archive_info = self.archive_files(analysis_data['files_to_archive'] analysis_data)
            
            # 步驟4, 生成報告
            self.logger.info("📝 步驟4, 生成報告...")
            report = self.generate_archive_report(analysis_data, backup_info, archive_info)
            
            # 保存報告
            report_file = self.archive_dir / f"archive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(report_file, 'w', encoding == 'utf-8') as f,
                f.write(report)
            
            self.logger.info(f"✅ 完整歸檔流程完成,報告保存至, {report_file}")
            
            return {
                "status": "success",
                "analysis": analysis_data,
                "backup": backup_info,
                "archive": archive_info,
                "report_file": str(report_file),
                "files_archived": len(archive_info['files_archived']),
                "files_backed_up": len(backup_info['files_backed_up'])
            }
            
        except Exception as e,::
            self.logger.error(f"歸檔流程失敗, {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Archival process failed"
            }

# 使用示例
if __name"__main__":::
    # 設置日誌
    logging.basicConfig(,
    level=logging.INFO(),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 系統檔案歸檔管理器")
    print("=" * 50)
    
    # 創建歸檔管理器
    archiver == SystemArchiver()
    
    # 運行完整歸檔流程
    result = archiver.run_complete_archival_process()
    
    if result["status"] == "success":::
        print(f"\n✅ 歸檔成功!")
        print(f"📊 歸檔檔案數量, {result['files_archived']}")
        print(f"💾 備份檔案數量, {result['files_backed_up']}")
        print(f"📝 報告檔案, {result['report_file']}")
    else,
        print(f"\n❌ 歸檔失敗, {result.get('message', 'Unknown error')}")
        if "error" in result,::
            print(f"錯誤詳情, {result['error']}")
