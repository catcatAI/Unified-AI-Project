"""
基础修复器类
所有修复模块的基类
"""

import os
import abc
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..core.fix_types import FixType, FixStatus, FixContext
from ..core.fix_result import FixResult


class BaseFixer(abc.ABC):
    """基础修复器类"""



    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.fix_type = None  # 子类必须设置
        self.name = self.__class__.__name__
        
        # 设置日志
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        
         # 修复统计

        self.stats = {
            "total_fixes": 0,
            "successful_fixes": 0,
            "failed_fixes": 0,
            "issues_found": 0,

 "issues_fixed": 0

        }
    
    @abc.abstractmethod
    def analyze(self, context: FixContext) -> List[Any]:
        """
        分析问题
        
        Args:
            context: 修复上下文
            
        Returns:
            问题列表
        """
        pass
    
    @abc.abstractmethod
    def fix(self, context: FixContext) -> FixResult:
        """
        修复问题
        
        Args:
            context: 修复上下文
            
        Returns:
            修复结果
        """
        pass
    
    def _get_target_files(self, context: FixContext) -> List[Path]:
        """
        获取目标文件列表
        
        Args:
            context: 修复上下文
            
        Returns:
            目标文件路径列表
        """
        target_files = []
        
        if context.target_path:
            # 特定目标
            if context.target_path.is_file():
                target_files.append(context.target_path)
            elif context.target_path.is_dir():
                target_files.extend(self._get_python_files_in_directory(context.target_path))
        else:
            # 根据范围获取文件
            if context.scope.value == "project":
                target_files.extend(self._get_python_files_in_directory(self.project_root))
            elif context.scope.value == "backend":
                backend_dir = self.project_root / "apps" / "backend"
                if backend_dir.exists():
                    target_files.extend(self._get_python_files_in_directory(backend_dir))
            elif context.scope.value == "frontend":
                frontend_dir = self.project_root / "apps" / "frontend-dashboard"
                if frontend_dir.exists():
                    target_files.extend(self._get_javascript_files_in_directory(frontend_dir))
            elif context.scope.value == "desktop":
                desktop_dir = self.project_root / "apps" / "desktop-app"
                if desktop_dir.exists():
                    target_files.extend(self._get_javascript_files_in_directory(desktop_dir))
        
         # 过滤排除的路径

        filtered_files = []
        excluded_paths = context.excluded_paths or []


        excluded_paths.extend([
            "node_modules", "__pycache__", ".git", "venv", ".venv",
            "backup", "unified_fix_backups", "dist", "build"

        ])
        
        for file_path in target_files:
            # 检查是否包含排除的路径
            should_exclude = False
            for excluded in excluded_paths:
                if excluded in str(file_path):
                    should_exclude = True
                    break
            
            if not should_exclude:
                filtered_files.append(file_path)

        
        return filtered_files
    
    def _get_python_files_in_directory(self, directory: Path) -> List[Path]:
        """获取目录中的Python文件"""
        python_files = []
        
        try:
            for py_file in directory.rglob("*.py"):
                if py_file.is_file():
                    python_files.append(py_file)
        except Exception as e:
            self.logger.error(f"获取目录 {directory} 中的Python文件失败: {e}")
        
        return python_files
    
    def _get_javascript_files_in_directory(self, directory: Path) -> List[Path]:
        """获取目录中的JavaScript/TypeScript文件"""
        js_files = []
        
        try:
            for ext in ["*.js", "*.jsx", "*.ts", "*.tsx"]:
                for js_file in directory.rglob(ext):
                    if js_file.is_file():
                        js_files.append(js_file)
        except Exception as e:
            self.logger.error(f"获取目录 {directory} 中的JavaScript文件失败: {e}")
        
        return js_files
    
    def _get_file_content(self, file_path: Path) -> Optional[str]:
        """获取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

        except Exception as e:
            self.logger.error(f"读取文件 {file_path} 失败: {e}")
            return None

    
    def _write_file_content(self, file_path: Path, content: str) -> bool:
        """写入文件内容"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return True
        except Exception as e:
            self.logger.error(f"写入文件 {file_path} 失败: {e}")

            return False
    
    def _create_backup(self, file_path: Path, backup_suffix: str = ".backup") -> Optional[Path]:
        """创建文件备份"""
        try:
            backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)
            import shutil

            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            self.logger.error(f"创建备份失败 {file_path}: {e}")
            return None
    
    def _log_fix_result(self, result: FixResult):
        """记录修复结果"""
        self.stats["total_fixes"] += 1
        self.stats["issues_found"] += result.issues_found
        self.stats["issues_fixed"] += result.issues_fixed
        
        if result.status == FixStatus.SUCCESS:
            self.stats["successful_fixes"] += 1
            self.logger.info(f"修复成功: {result.summary()}")
        elif result.status == FixStatus.FAILED:
            self.stats["failed_fixes"] += 1

            self.logger.error(f"修复失败: {result.summary()}")
        elif result.status == FixStatus.PARTIAL_SUCCESS:
            self.stats["successful_fixes"] += 1  # 部分成功也算成功

            self.logger.warning(f"部分修复成功: {result.summary()}")
        elif result.status == FixStatus.SKIPPED:
            self.logger.info(f"修复已跳过: {result.summary()}")
    
    def get_statistics(self) -> Dict[str, int]:
        """获取修复统计"""


        return self.stats.copy()
    
    def reset_statistics(self):
        """重置统计信息"""
        self.stats = {
        "total_fixes": 0,

            "successful_fixes": 0,

            "failed_fixes": 0,
            "issues_found": 0,

            "issues_fixed": 0
            }

    
    def cleanup(self):
        """清理资源"""
        self.logger.info(f"清理 {self.name} 资源...")

        # 子类可以重写此方法进行特定的清理操作
    
    def __str__(self):
        return f"{self.name}(fix_type={self.fix_type.value if self.fix_type else 'None'})"
    
    def __repr__(self):
        return self.__str__()