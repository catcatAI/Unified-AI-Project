#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文檔更新狀態管理工具

此腳本提供了一個命令行工具，用於管理文檔更新狀態，包括：
1. 查看文檔更新狀態
2. 更新文檔狀態
3. 添加註釋
4. 生成更新報告
"""

import os
import sys
import json
import argparse
import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 專案根目錄
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 文檔狀態追蹤文件
STATUS_FILE = PROJECT_ROOT / "doc_update_status.json"

# 文檔更新狀態
class DocStatus:
    PENDING = "待更新"
    IN_PROGRESS = "更新中"
    COMPLETED = "已更新"
    NEEDS_REVIEW = "需審查"
    NOT_NEEDED = "無需更新"
    
    @classmethod
    def get_all_statuses(cls):
        return [cls.PENDING, cls.IN_PROGRESS, cls.COMPLETED, cls.NEEDS_REVIEW, cls.NOT_NEEDED]


class DocStatusManager:
    def __init__(self, status_file=None):
        self.status_file = Path(status_file) if status_file else STATUS_FILE
        self.status_data = self._load_status()
    
    def _load_status(self) -> Dict:
        """載入文檔更新狀態"""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"錯誤：載入狀態文件失敗: {e}")
                return self._create_initial_status()
        else:
            print(f"警告：狀態文件不存在，將創建新文件: {self.status_file}")
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
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(self.status_data, f, ensure_ascii=False, indent=2)
            print(f"狀態已保存至 {self.status_file}")
        except Exception as e:
            print(f"錯誤：保存狀態文件失敗: {e}")
    
    def update_status(self, doc_path: str, status: str, notes: str = ""):
        """更新文檔狀態
        
        Args:
            doc_path: 文檔路徑
            status: 狀態值，應為DocStatus中的一個
            notes: 可選的註釋
        """
        # 標準化路徑
        doc_path = os.path.normpath(doc_path)
        
        # 檢查狀態是否有效
        if status not in DocStatus.get_all_statuses():
            print(f"錯誤：無效的狀態值 '{status}'。有效值為: {DocStatus.get_all_statuses()}")
            return
        
        # 更新或添加文檔狀態
        if doc_path not in self.status_data["files"]:
            self.status_data["files"][doc_path] = {
                "status": status,
                "last_update": datetime.datetime.now().isoformat(),
                "notes": notes
            }
        else:
            self.status_data["files"][doc_path]["status"] = status
            self.status_data["files"][doc_path]["last_update"] = datetime.datetime.now().isoformat()
            if notes:
                self.status_data["files"][doc_path]["notes"] = notes
        
        # 保存更新
        self._save_status()
    
    def get_status(self, doc_path: str) -> Dict:
        """獲取文檔狀態
        
        Args:
            doc_path: 文檔路徑
            
        Returns:
            文檔狀態信息字典
        """
        # 標準化路徑
        doc_path = os.path.normpath(doc_path)
        
        if doc_path in self.status_data["files"]:
            return self.status_data["files"][doc_path]
        else:
            return {"status": "未知", "notes": ""}
            
    def get_all_statuses(self) -> List[Dict]:
        """獲取所有文檔狀態
        
        Returns:
            所有文檔狀態的列表
        """
        return list(self.status_data["files"].values())
        
    def filter_by_status(self, status: str) -> Dict[str, Dict]:
        """按狀態篩選文檔
        
        Args:
            status: 狀態值
            
        Returns:
            符合狀態的文檔字典 {doc_path: doc_info}
        """
        return {path: info for path, info in self.status_data["files"].items() 
                if info.get("status") == status}
    
    def list_docs(self, status_filter: Optional[str] = None, directory: Optional[str] = None):
        """列出文檔及其狀態"""
        if not self.status_data["files"]:
            print("沒有找到任何文檔記錄。請先運行 document_update_plan.py 掃描專案。")
            return
        
        # 過濾文檔
        filtered_docs = {}
        for doc_path, doc_info in self.status_data["files"].items():
            # 狀態過濾
            if status_filter and doc_info.get("status") != status_filter:
                continue
            
            # 目錄過濾
            if directory:
                doc_dir = os.path.dirname(doc_path)
                if not doc_dir.startswith(directory):
                    continue
            
            filtered_docs[doc_path] = doc_info
        
        if not filtered_docs:
            filter_desc = []
            if status_filter:
                filter_desc.append(f"狀態={status_filter}")
            if directory:
                filter_desc.append(f"目錄={directory}")
            
            print(f"沒有找到符合條件的文檔: {', '.join(filter_desc)}")
            return
        
        # 打印文檔列表
        print(f"找到 {len(filtered_docs)} 個文檔:")
        print("\n{:<4} {:<50} {:<10} {:<15}".format("序號", "文檔路徑", "狀態", "最後更新"))
        print("-" * 80)
        
        for i, (doc_path, doc_info) in enumerate(sorted(filtered_docs.items()), 1):
            status = doc_info.get("status", DocStatus.PENDING)
            last_update = doc_info.get("last_update", "未更新")
            if last_update and last_update != "未更新":
                try:
                    last_update = datetime.datetime.fromisoformat(last_update).strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            print("{:<4} {:<50} {:<10} {:<15}".format(
                i, doc_path[:50], status, last_update
            ))
    
    def show_doc_details(self, doc_path: str):
        """顯示文檔詳細信息"""
        if doc_path not in self.status_data["files"]:
            print(f"錯誤：找不到文檔 '{doc_path}'")
            return
        
        doc_info = self.status_data["files"][doc_path]
        
        print("\n文檔詳情:")
        print(f"路徑: {doc_path}")
        print(f"狀態: {doc_info.get('status', DocStatus.PENDING)}")
        print(f"最後更新: {doc_info.get('last_update', '未更新')}")
        
        associated_code = doc_info.get("associated_code", [])
        if associated_code:
            print(f"\n關聯代碼文件 ({len(associated_code)}):")
            for i, code_path in enumerate(associated_code, 1):
                print(f"  {i}. {code_path}")
        else:
            print("\n關聯代碼文件: 無")
        
        notes = doc_info.get("notes", "")
        print(f"\n註釋: {notes if notes else '無'}")
    
    def update_doc_status(self, doc_path: str, status: str, notes: Optional[str] = None):
        """更新文檔狀態"""
        if doc_path not in self.status_data["files"]:
            print(f"錯誤：找不到文檔 '{doc_path}'")
            return False
        
        if status not in DocStatus.get_all_statuses():
            print(f"錯誤：無效的狀態 '{status}'")
            print(f"有效狀態: {', '.join(DocStatus.get_all_statuses())}")
            return False
        
        # 更新狀態
        self.status_data["files"][doc_path]["status"] = status
        self.status_data["files"][doc_path]["last_update"] = datetime.datetime.now().isoformat()
        
        # 更新註釋
        if notes is not None:
            self.status_data["files"][doc_path]["notes"] = notes
        
        self._save_status()
        print(f"已更新文檔 '{doc_path}' 的狀態為 '{status}'")
        return True
    
    def generate_report(self):
        """生成Markdown格式的報告"""
        print("生成Markdown報告...")
        
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
                if last_update and last_update != "未更新":
                    try:
                        last_update = datetime.datetime.fromisoformat(last_update).strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                
                report.append(f"| {doc_name} | {status} | {code_count} | {last_update} |")
        
        # 保存報告
        report_file = PROJECT_ROOT / "doc_update_report.md"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(report))
            print(f"報告已保存至 {report_file}")
        except Exception as e:
            print(f"錯誤：保存報告失敗: {e}")
        
        return "\n".join(report)


def parse_args():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description="文檔更新狀態管理工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # list 命令
    list_parser = subparsers.add_parser("list", help="列出文檔及其狀態")
    list_parser.add_argument("--status", "-s", choices=DocStatus.get_all_statuses(),
                           help="按狀態過濾")
    list_parser.add_argument("--dir", "-d", help="按目錄過濾")
    
    # show 命令
    show_parser = subparsers.add_parser("show", help="顯示文檔詳細信息")
    show_parser.add_argument("doc_path", help="文檔路徑")
    
    # update 命令
    update_parser = subparsers.add_parser("update", help="更新文檔狀態")
    update_parser.add_argument("doc_path", help="文檔路徑")
    update_parser.add_argument("status", choices=DocStatus.get_all_statuses(),
                             help="新狀態")
    update_parser.add_argument("--notes", "-n", help="添加註釋")
    
    # report 命令
    subparsers.add_parser("report", help="生成更新報告")
    
    return parser.parse_args()


def main():
    """主函數"""
    args = parse_args()
    manager = DocStatusManager()
    
    if args.command == "list":
        manager.list_docs(args.status, args.dir)
    elif args.command == "show":
        manager.show_doc_details(args.doc_path)
    elif args.command == "update":
        manager.update_doc_status(args.doc_path, args.status, args.notes)
    elif args.command == "report":
        manager.generate_report()
    else:
        print("請指定子命令: list, show, update, report")
        print("使用 -h 或 --help 查看幫助")


if __name__ == "__main__":
    main()