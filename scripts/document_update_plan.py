#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文檔更新計畫腳本

此腳本實現了系統化的專案文件更新計畫，包含以下功能：
1. 掃描專案目錄，建立檔案清單與路徑映射表
2. 標記所有代碼檔案與對應的MD文檔
3. 建立代碼檔案與MD文檔的關聯組
4. 設計文件更新流程與標準
5. 建立更新狀態追蹤機制
6. 制定最終文檔校驗與報告生成方案
"""

import os
import re
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
import glob

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("document_update.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("document_update")

# 專案根目錄
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 文檔狀態追蹤文件
STATUS_FILE = PROJECT_ROOT / "doc_update_status.json"

# 忽略的目錄
IGNORE_DIRS = [
    ".git", ".github", "node_modules", "__pycache__", ".pytest_cache",
    "venv", "env", ".venv", ".env", "dist", "build", "coverage"
]

# 代碼文件擴展名
CODE_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "React TypeScript",
    ".jsx": "React JavaScript",
    ".java": "Java",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++ Header",
    ".sh": "Shell Script",
    ".bat": "Batch Script",
    ".ps1": "PowerShell Script"
}

# 文檔文件擴展名
DOC_EXTENSIONS = {
    ".md": "Markdown",
    ".rst": "reStructuredText",
    ".txt": "Text"
}

# 文檔更新狀態
class DocStatus:
    PENDING = "待更新"
    IN_PROGRESS = "更新中"
    COMPLETED = "已更新"
    NEEDS_REVIEW = "需審查"
    NOT_NEEDED = "無需更新"

class DocumentUpdatePlan:
    def __init__(self):
        self.code_files = {}
        self.doc_files = {}
        self.associations = {}
        self.status_data = self._load_status()
        
    def _load_status(self) -> Dict:
        """載入文檔更新狀態"""
        if STATUS_FILE.exists():
            try:
                with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"載入狀態文件失敗: {e}")
                return self._create_initial_status()
        else:
            return self._create_initial_status()
    
    def _create_initial_status(self) -> Dict:
        """創建初始狀態數據"""
        return {
            "last_update": datetime.datetime.now().isoformat(),
            "files": {},
            "stats": {
                "total": 0,
                "pending": 0,
                "in_progress": 0,
                "completed": 0,
                "needs_review": 0,
                "not_needed": 0
            }
        }
    
    def _save_status(self):
        """保存文檔更新狀態"""
        self.status_data["last_update"] = datetime.datetime.now().isoformat()
        
        # 更新統計數據
        stats = {
            "total": len(self.status_data["files"]),
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "needs_review": 0,
            "not_needed": 0
        }
        
        for file_data in self.status_data["files"].values():
            status = file_data.get("status", DocStatus.PENDING)
            if status == DocStatus.PENDING:
                stats["pending"] += 1
            elif status == DocStatus.IN_PROGRESS:
                stats["in_progress"] += 1
            elif status == DocStatus.COMPLETED:
                stats["completed"] += 1
            elif status == DocStatus.NEEDS_REVIEW:
                stats["needs_review"] += 1
            elif status == DocStatus.NOT_NEEDED:
                stats["not_needed"] += 1
        
        self.status_data["stats"] = stats
        
        try:
            with open(STATUS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.status_data, f, ensure_ascii=False, indent=2)
            logger.info(f"狀態已保存至 {STATUS_FILE}")
        except Exception as e:
            logger.error(f"保存狀態文件失敗: {e}")
    
    def scan_project(self):
        """掃描專案目錄，建立檔案清單與路徑映射表"""
        logger.info("開始掃描專案目錄...")
        
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # 跳過忽略的目錄
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            rel_path = os.path.relpath(root, PROJECT_ROOT)
            if rel_path == ".":
                rel_path = ""
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_file_path = os.path.join(rel_path, file).replace("\\", "/")
                
                _, ext = os.path.splitext(file)
                
                # 收集代碼文件
                if ext.lower() in CODE_EXTENSIONS:
                    self.code_files[rel_file_path] = {
                        "path": file_path,
                        "type": CODE_EXTENSIONS[ext.lower()],
                        "rel_path": rel_file_path
                    }
                
                # 收集文檔文件
                if ext.lower() in DOC_EXTENSIONS:
                    self.doc_files[rel_file_path] = {
                        "path": file_path,
                        "type": DOC_EXTENSIONS[ext.lower()],
                        "rel_path": rel_file_path
                    }
        
        logger.info(f"掃描完成。找到 {len(self.code_files)} 個代碼文件和 {len(self.doc_files)} 個文檔文件。")
    
    def create_associations(self):
        """建立代碼文件與MD文檔的關聯組"""
        logger.info("開始建立代碼文件與文檔的關聯...")
        
        # 1. 基於路徑相似性建立關聯
        for code_path, code_info in self.code_files.items():
            code_dir = os.path.dirname(code_path)
            code_name = os.path.splitext(os.path.basename(code_path))[0]
            
            # 尋找同目錄下的文檔
            same_dir_docs = []
            for doc_path, doc_info in self.doc_files.items():
                doc_dir = os.path.dirname(doc_path)
                doc_name = os.path.splitext(os.path.basename(doc_path))[0]
                
                # 同目錄且名稱相似
                if doc_dir == code_dir and (doc_name.lower() == code_name.lower() or 
                                           code_name.lower() in doc_name.lower() or 
                                           doc_name.lower() == "readme"):
                    same_dir_docs.append(doc_path)
            
            # 尋找上層目錄的文檔
            parent_dir_docs = []
            if code_dir:  # 非根目錄
                for doc_path, doc_info in self.doc_files.items():
                    doc_dir = os.path.dirname(doc_path)
                    doc_name = os.path.splitext(os.path.basename(doc_path))[0]
                    
                    # 上層目錄且名稱相似或為README
                    if doc_dir and code_dir.startswith(doc_dir) and (doc_name.lower() == os.path.basename(code_dir).lower() or 
                                                                    doc_name.lower() == "readme"):
                        parent_dir_docs.append(doc_path)
            
            # 關聯文檔
            associated_docs = same_dir_docs + parent_dir_docs
            if associated_docs:
                self.associations[code_path] = associated_docs
                
                # 更新狀態
                for doc_path in associated_docs:
                    if doc_path not in self.status_data["files"]:
                        self.status_data["files"][doc_path] = {
                            "status": DocStatus.PENDING,
                            "associated_code": [code_path],
                            "last_update": None,
                            "notes": ""
                        }
                    else:
                        if "associated_code" not in self.status_data["files"][doc_path]:
                            self.status_data["files"][doc_path]["associated_code"] = []
                        if code_path not in self.status_data["files"][doc_path]["associated_code"]:
                            self.status_data["files"][doc_path]["associated_code"].append(code_path)
            else:
                # 沒有關聯文檔，可能需要創建
                logger.warning(f"代碼文件 {code_path} 沒有關聯文檔")
        
        # 2. 處理沒有關聯代碼的文檔
        for doc_path, doc_info in self.doc_files.items():
            if doc_path not in self.status_data["files"]:
                self.status_data["files"][doc_path] = {
                    "status": DocStatus.PENDING,
                    "associated_code": [],
                    "last_update": None,
                    "notes": "沒有關聯代碼文件"
                }
        
        logger.info(f"關聯建立完成。{len(self.associations)} 個代碼文件有關聯文檔。")
        self._save_status()
    
    def generate_update_plan(self):
        """生成文檔更新計畫"""
        logger.info("生成文檔更新計畫...")
        
        # 按目錄分組
        dir_groups = {}
        for doc_path, doc_info in self.status_data["files"].items():
            doc_dir = os.path.dirname(doc_path)
            if doc_dir not in dir_groups:
                dir_groups[doc_dir] = []
            dir_groups[doc_dir].append(doc_path)
        
        # 生成更新計畫
        update_plan = {
            "generated_at": datetime.datetime.now().isoformat(),
            "total_docs": len(self.status_data["files"]),
            "stats": self.status_data["stats"],
            "groups": []
        }
        
        for dir_path, doc_paths in sorted(dir_groups.items()):
            group = {
                "directory": dir_path,
                "documents": []
            }
            
            for doc_path in sorted(doc_paths):
                doc_info = self.status_data["files"][doc_path]
                group["documents"].append({
                    "path": doc_path,
                    "status": doc_info["status"],
                    "associated_code_count": len(doc_info.get("associated_code", [])),
                    "last_update": doc_info["last_update"]
                })
            
            update_plan["groups"].append(group)
        
        # 保存更新計畫
        plan_file = PROJECT_ROOT / "doc_update_plan.json"
        try:
            with open(plan_file, 'w', encoding='utf-8') as f:
                json.dump(update_plan, f, ensure_ascii=False, indent=2)
            logger.info(f"更新計畫已保存至 {plan_file}")
        except Exception as e:
            logger.error(f"保存更新計畫失敗: {e}")
        
        return update_plan
    
    def generate_markdown_report(self):
        """生成Markdown格式的報告"""
        logger.info("生成Markdown報告...")
        
        report = []
        report.append("# 專案文件更新計畫報告")
        report.append(f"\n生成時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("\n## 概況")
        report.append(f"- 總文檔數: {self.status_data['stats']['total']}")
        report.append(f"- 待更新: {self.status_data['stats']['pending']}")
        report.append(f"- 更新中: {self.status_data['stats']['in_progress']}")
        report.append(f"- 已更新: {self.status_data['stats']['completed']}")
        report.append(f"- 需審查: {self.status_data['stats']['needs_review']}")
        report.append(f"- 無需更新: {self.status_data['stats']['not_needed']}")
        
        # 按目錄分組
        dir_groups = {}
        for doc_path, doc_info in self.status_data["files"].items():
            doc_dir = os.path.dirname(doc_path)
            if doc_dir not in dir_groups:
                dir_groups[doc_dir] = []
            dir_groups[doc_dir].append((doc_path, doc_info))
        
        # 生成目錄分組報告
        report.append("\n## 文檔分組")
        
        for dir_path, doc_items in sorted(dir_groups.items()):
            dir_display = dir_path if dir_path else "[根目錄]"
            report.append(f"\n### {dir_display}")
            report.append("| 文檔 | 狀態 | 關聯代碼數 | 最後更新 |")
            report.append("| ---- | ---- | ---------- | -------- |")
            
            for doc_path, doc_info in sorted(doc_items):
                doc_name = os.path.basename(doc_path)
                status = doc_info["status"]
                code_count = len(doc_info.get("associated_code", []))
                last_update = doc_info["last_update"] if doc_info["last_update"] else "未更新"
                
                report.append(f"| {doc_name} | {status} | {code_count} | {last_update} |")
        
        # 保存報告
        report_file = PROJECT_ROOT / "doc_update_report.md"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(report))
            logger.info(f"報告已保存至 {report_file}")
        except Exception as e:
            logger.error(f"保存報告失敗: {e}")
        
        return "\n".join(report)
    
    def create_document_template(self, doc_path: str) -> str:
        """創建文檔模板"""
        doc_info = self.status_data["files"].get(doc_path)
        if not doc_info:
            return ""
        
        associated_code = doc_info.get("associated_code", [])
        doc_name = os.path.splitext(os.path.basename(doc_path))[0]
        
        template = []
        template.append(f"# {doc_name}")
        template.append("\n## 概述")
        template.append("[在此描述此模組的主要功能和用途]")
        
        template.append("\n## 功能特性")
        template.append("- [功能點1]")
        template.append("- [功能點2]")
        template.append("- [功能點3]")
        
        if associated_code:
            template.append("\n## 相關代碼文件")
            for code_path in associated_code:
                template.append(f"- `{code_path}`")
            
            template.append("\n## 主要接口")
            template.append("```python")
            template.append("# 示例代碼")
            template.append("def example_function(param1, param2):")
            template.append("    # 函數說明")
            template.append("    # 實現細節")
            template.append("    pass")
            template.append("```")
        
        template.append("\n## 使用示例")
        template.append("```python")
        template.append("# 使用示例代碼")
        template.append("```")
        
        template.append("\n## 依賴關係")
        template.append("- [依賴項1]")
        template.append("- [依賴項2]")
        
        template.append("\n## 未來規劃")
        template.append("- [規劃項1]")
        template.append("- [規劃項2]")
        
        template.append("\n## 注意事項")
        template.append("- [注意事項1]")
        template.append("- [注意事項2]")
        
        return "\n".join(template)
    
    def run(self):
        # 執行文檔更新計畫
        logger.info("開始執行文檔更新計畫...")
        
        # 1. 掃描專案目錄
        self.scan_project()
        
        # 2. 建立關聯
        self.create_associations()
        
        # 3. 生成更新計畫
        self.generate_update_plan()
        
        # 4. 生成報告
        self.generate_markdown_report()
        
        logger.info("文檔更新計畫執行完成。")


def main():
    # 主函數
    plan = DocumentUpdatePlan()
    plan.run()


def scan_directory(directory, patterns):
    """掃描目錄並返回符合模式的文件列表
    
    Args:
        directory: 要掃描的目錄路徑
        patterns: 文件模式列表，如 ["*.py", "*.md"]
        
    Returns:
        符合模式的文件路徑列表
    """
    result = []
    for pattern in patterns:
        # 使用glob模式匹配文件
        pattern_path = os.path.join(directory, pattern)
        files = glob.glob(pattern_path)
        result.extend(files)
    return result

def associate_files(code_files, doc_files):
    """建立代碼文件和文檔文件的關聯
    
    Args:
        code_files: 代碼文件路徑列表
        doc_files: 文檔文件路徑列表
        
    Returns:
        關聯字典，格式為 {code_file: [doc_file1, doc_file2, ...]}
    """
    associations = {}
    
    # 簡單的關聯邏輯：基於文件名（不含擴展名）匹配
    for code_file in code_files:
        code_basename = os.path.splitext(os.path.basename(code_file))[0]
        associated_docs = []
        
        for doc_file in doc_files:
            doc_basename = os.path.splitext(os.path.basename(doc_file))[0]
            
            # 如果文檔文件名包含代碼文件名，則建立關聯
            if code_basename == doc_basename or code_basename in doc_basename:
                associated_docs.append(doc_file)
        
        if associated_docs:
            associations[code_file] = associated_docs
    
    return associations

if __name__ == "__main__":
    main()