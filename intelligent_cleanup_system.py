#!/usr/bin/env python3
"""
智能清理系统
检测并清理修复脚本造成的重复、无效和有害文件
"""

import os
import re
import hashlib
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntelligentCleanupSystem:
    """智能清理系统"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.cleanup_dir = self.project_root / "cleanup_archive"
        self.cleanup_dir.mkdir(exist_ok=True)
        
        # 清理统计
        self.cleanup_stats = {
            "total_files_scanned": 0,
            "duplicate_files_removed": 0,
            "empty_files_removed": 0,
            "test_files_archived": 0,
            "backup_files_removed": 0,
            "broken_files_fixed": 0,
            "space_saved_mb": 0
        }
        
        # 有害文件模式
        self.harmful_patterns = [
            r"check_\d+\.py$",  # 编号检查脚本
            r"fix_.*\.py$",     # 修复脚本
            r"test_.*repair.*\.py$",  # 修复测试文件
            r".*_backup.*\.py$",      # 备份文件
            r".*\.bak$",              # 通用备份文件
            r".*\.tmp$",              # 临时文件
        ]
        
        # 重复文件特征
        self.duplicate_patterns = [
            r"def test_.*\(self\):.*pass",  # 空测试函数
            r"print\([\"'].*[\"']\)",       # 简单打印语句
            r"#.*TODO.*",                  # TODO注释
            r"#.*FIXME.*",                 # FIXME注释
        ]
        
        logger.info(f"智能清理系统初始化完成 - 项目根目录: {self.project_root}")
    
    def perform_intelligent_cleanup(self, dry_run: bool = True) -> Dict[str, Any]:
        """执行智能清理"""
        logger.info(f"开始智能清理 (dry_run={dry_run})")
        start_time = datetime.now()
        
        # 1. 扫描所有文件
        all_files = self._scan_all_files()
        self.cleanup_stats["total_files_scanned"] = len(all_files)
        
        # 2. 查找重复文件
        duplicates = self._find_duplicate_files(all_files)
        
        # 3. 查找有害文件
        harmful_files = self._find_harmful_files(all_files)
        
        # 4. 查找空文件和损坏文件
        empty_files = self._find_empty_files(all_files)
        broken_files = self._find_broken_files(all_files)
        
        # 5. 分析文件内容质量
        low_quality_files = self._find_low_quality_files(all_files)
        
        # 6. 执行清理（如果不是dry_run）
        if not dry_run:
            self._remove_duplicate_files(duplicates)
            self._archive_harmful_files(harmful_files)
            self._remove_empty_files(empty_files)
            self._fix_broken_files(broken_files)
            self._archive_low_quality_files(low_quality_files)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 生成清理报告
        report = {
            "success": True,
            "dry_run": dry_run,
            "duration_seconds": duration,
            "stats": self.cleanup_stats.copy(),
            "cleanup_summary": {
                "duplicate_files": len(duplicates),
                "harmful_files": len(harmful_files),
                "empty_files": len(empty_files),
                "broken_files": len(broken_files),
                "low_quality_files": len(low_quality_files),
                "space_saved_mb": self.cleanup_stats["space_saved_mb"]
            },
            "details": {
                "duplicates": duplicates,
                "harmful_files": harmful_files,
                "empty_files": empty_files,
                "broken_files": broken_files,
                "low_quality_files": low_quality_files
            }
        }
        
        logger.info(f"清理完成 - 扫描了 {len(all_files)} 个文件，节省了 {self.cleanup_stats['space_saved_mb']:.2f} MB")
        return report
    
    def _scan_all_files(self) -> List[Path]:
        """扫描所有文件"""
        all_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # 跳过归档目录和清理目录
            if "archived" in root or "cleanup" in root:
                continue
                
            for file in files:
                file_path = Path(root) / file
                all_files.append(file_path)
        
        return all_files
    
    def _find_duplicate_files(self, files: List[Path]) -> List[Dict[str, Any]]:
        """查找重复文件"""
        file_hashes = defaultdict(list)
        duplicates = []
        
        for file_path in files:
            try:
                # 计算文件哈希
                file_hash = self._calculate_file_hash(file_path)
                if file_hash:
                    file_hashes[file_hash].append(file_path)
            except Exception as e:
                logger.warning(f"计算文件哈希失败 {file_path}: {e}")
        
        # 找出重复文件
        for file_hash, file_list in file_hashes.items():
            if len(file_list) > 1:
                # 保留最旧的文件，删除其他的
                file_list.sort(key=lambda x: x.stat().st_mtime)
                keeper = file_list[0]
                
                for file_to_remove in file_list[1:]:
                    duplicates.append({
                        "hash": file_hash,
                        "keeper": str(keeper),
                        "removal": str(file_to_remove),
                        "size_bytes": file_to_remove.stat().st_size
                    })
        
        return duplicates
    
    def _calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """计算文件哈希"""
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return None
    
    def _find_harmful_files(self, files: List[Path]) -> List[Dict[str, Any]]:
        """查找有害文件"""
        harmful_files = []
        
        for file_path in files:
            file_name = file_path.name
            
            # 检查文件名是否匹配有害模式
            for pattern in self.harmful_patterns:
                if re.match(pattern, file_name):
                    harmful_files.append({
                        "file_path": str(file_path),
                        "pattern_matched": pattern,
                        "size_bytes": file_path.stat().st_size,
                        "reason": "匹配有害文件模式"
                    })
                    break
            
            # 检查文件内容是否有害
            if self._is_harmful_content(file_path):
                harmful_files.append({
                    "file_path": str(file_path),
                    "pattern_matched": "content_analysis",
                    "size_bytes": file_path.stat().st_size,
                    "reason": "包含有害内容模式"
                })
        
        return harmful_files
    
    def _is_harmful_content(self, file_path: Path) -> bool:
        """检查文件内容是否有害"""
        try:
            if file_path.suffix != '.py':
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查有害内容模式
            harmful_patterns = [
                r"with open\('.*check.*\.py', 'r'\)",  # 硬编码检查文件
                r"print\([\"'].*检查.*[\"']\)",        # 简单检查输出
                r"#.*修复.*脚本.*",                    # 修复脚本注释
                r"^#.*\d+.*$",                         # 编号注释
            ]
            
            for pattern in harmful_patterns:
                if re.search(pattern, content, re.MULTILINE):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _find_empty_files(self, files: List[Path]) -> List[str]:
        """查找空文件"""
        empty_files = []
        
        for file_path in files:
            try:
                if file_path.stat().st_size == 0:
                    empty_files.append(str(file_path))
                elif file_path.suffix == '.py':
                    # 检查Python文件是否只有导入或只有注释
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    if not content or self._is_minimal_python_file(content):
                        empty_files.append(str(file_path))
                        
            except Exception as e:
                logger.warning(f"检查空文件失败 {file_path}: {e}")
        
        return empty_files
    
    def _is_minimal_python_file(self, content: str) -> bool:
        """检查是否是极简的Python文件"""
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # 只有导入语句或只有pass语句
        non_import_lines = [line for line in lines if not line.startswith(('import ', 'from '))]
        
        if len(non_import_lines) <= 2:
            # 检查是否只有注释、空行、pass、或者简单的print
            minimal_patterns = [
                r'^#.*$',           # 注释
                r'^pass$',          # pass语句
                r'^print\(.*\)$',   # print语句
                r'^""".*"""$',     # 文档字符串
            ]
            
            for line in non_import_lines:
                if not any(re.match(pattern, line) for pattern in minimal_patterns):
                    return False
            
            return True
        
        return False
    
    def _find_broken_files(self, files: List[Path]) -> List[Dict[str, Any]]:
        """查找损坏的文件"""
        broken_files = []
        
        for file_path in files:
            if file_path.suffix == '.py':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 尝试解析Python语法
                    import ast
                    ast.parse(content)
                    
                except SyntaxError as e:
                    broken_files.append({
                        "file_path": str(file_path),
                        "error_type": "SyntaxError",
                        "error_message": str(e),
                        "line_number": e.lineno,
                        "size_bytes": file_path.stat().st_size
                    })
                
                except Exception as e:
                    broken_files.append({
                        "file_path": str(file_path),
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "size_bytes": file_path.stat().st_size
                    })
        
        return broken_files
    
    def _find_low_quality_files(self, files: List[Path]) -> List[Dict[str, Any]]:
        """查找低质量文件"""
        low_quality_files = []
        
        for file_path in files:
            if file_path.suffix == '.py':
                quality_score = self._assess_file_quality(file_path)
                
                if quality_score < 0.3:  # 质量分数很低
                    low_quality_files.append({
                        "file_path": str(file_path),
                        "quality_score": quality_score,
                        "size_bytes": file_path.stat().st_size,
                        "reason": "代码质量过低"
                    })
        
        return low_quality_files
    
    def _assess_file_quality(self, file_path: Path) -> float:
        """评估文件质量（0-1分数）"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # 计算质量指标
            total_lines = len(lines)
            if total_lines == 0:
                return 0.0
            
            code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            comment_lines = len([line for line in lines if line.strip().startswith('#')])
            
            # 检查是否有函数定义
            has_functions = bool(re.search(r'^def \w+', content, re.MULTILINE))
            
            # 检查是否有类定义
            has_classes = bool(re.search(r'^class \w+', content, re.MULTILINE))
            
            # 检查是否有文档字符串
            has_docstrings = bool(re.search(r'""".*"""', content, re.DOTALL))
            
            # 计算质量分数
            score = 0.0
            
            # 代码行数比例
            if code_lines / total_lines > 0.3:
                score += 0.3
            
            # 有函数定义
            if has_functions:
                score += 0.2
            
            # 有类定义
            if has_classes:
                score += 0.2
            
            # 有文档字符串
            if has_docstrings:
                score += 0.1
            
            # 有注释
            if comment_lines > 0:
                score += 0.1
            
            # 文件大小合理
            if 100 < file_path.stat().st_size < 10000:
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception:
            return 0.0
    
    def _remove_duplicate_files(self, duplicates: List[Dict[str, Any]]) -> None:
        """移除重复文件"""
        for duplicate in duplicates:
            try:
                file_to_remove = Path(duplicate["removal"])
                if file_to_remove.exists():
                    file_to_remove.unlink()
                    self.cleanup_stats["duplicate_files_removed"] += 1
                    self.cleanup_stats["space_saved_mb"] += duplicate["size_bytes"] / (1024 * 1024)
                    logger.debug(f"移除重复文件: {file_to_remove}")
            except Exception as e:
                logger.warning(f"移除重复文件失败: {e}")
    
    def _archive_harmful_files(self, harmful_files: List[Dict[str, Any]]) -> None:
        """归档有害文件"""
        for harmful_file in harmful_files:
            try:
                file_path = Path(harmful_file["file_path"])
                if file_path.exists():
                    # 移动到归档目录
                    archive_path = self.cleanup_dir / "harmful_files" / file_path.name
                    archive_path.parent.mkdir(exist_ok=True)
                    
                    shutil.move(str(file_path), str(archive_path))
                    self.cleanup_stats["space_saved_mb"] += harmful_file["size_bytes"] / (1024 * 1024)
                    logger.debug(f"归档有害文件: {file_path} -> {archive_path}")
            except Exception as e:
                logger.warning(f"归档有害文件失败: {e}")
    
    def _remove_empty_files(self, empty_files: List[str]) -> None:
        """移除空文件"""
        for empty_file in empty_files:
            try:
                file_path = Path(empty_file)
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    self.cleanup_stats["empty_files_removed"] += 1
                    self.cleanup_stats["space_saved_mb"] += file_size / (1024 * 1024)
                    logger.debug(f"移除空文件: {file_path}")
            except Exception as e:
                logger.warning(f"移除空文件失败: {e}")
    
    def _fix_broken_files(self, broken_files: List[Dict[str, Any]]) -> None:
        """修复损坏文件"""
        # 这里可以集成之前的真实修复系统
        # 暂时只记录，不自动修复
        for broken_file in broken_files:
            logger.info(f"发现损坏文件: {broken_file['file_path']} - {broken_file['error_message']}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="智能清理系统")
    parser.add_argument("--path", default=".", help="要清理的路径")
    parser.add_argument("--dry-run", action="store_true", help="只分析，不执行清理")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建清理系统
    cleanup_system = IntelligentCleanupSystem(args.path)
    
    # 执行清理
    result = cleanup_system.perform_intelligent_cleanup(dry_run=args.dry_run)
    
    # 输出结果
    if result["success"]:
        print(f"清理分析完成！" if args.dry_run else "清理完成！")
        print(f"扫描文件: {result['stats']['total_files_scanned']}")
        print(f"重复文件: {result['cleanup_summary']['duplicate_files']}")
        print(f"有害文件: {result['cleanup_summary']['harmful_files']}")
        print(f"空文件: {result['cleanup_summary']['empty_files']}")
        print(f"损坏文件: {result['cleanup_summary']['broken_files']}")
        print(f"低质量文件: {result['cleanup_summary']['low_quality_files']}")
        print(f"节省空间: {result['cleanup_summary']['space_saved_mb']:.2f} MB")
        
        if args.dry_run:
            print("\n注意: 这是干运行模式，没有实际执行清理操作")
            print("使用 --dry-run=false 来执行实际清理")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())