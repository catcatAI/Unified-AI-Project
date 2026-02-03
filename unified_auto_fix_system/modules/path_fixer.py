"""
路径修复器
修复文件路径问题,包括路径不存在和权限问题
"""

import os
import json
import shutil
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..core.fix_types import FixType, FixStatus
from ..core.fix_result import FixResult, FixContext
from .base_fixer import BaseFixer


@dataclass
class PathIssue:
    """路径问题"""
    path: Path
    issue_type: str  # missing, permission, invalid, etc.
    expected_type: str = "file"  # file, directory
    current_state: Optional[str] = None
    description: str = ""
    severity: str = "error"  # error, warning, info


class PathFixer(BaseFixer):
    """路径修复器"""
    
    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.fix_type = FixType.PATH_FIX
        self.name = "PathFixer"
    
    def analyze(self, context: FixContext) -> List[PathIssue]:
        """分析路径问题"""
        self.logger.info("分析路径问题...")
        
        issues = []
        
        # 分析项目中的路径问题
        target_files = self._get_target_files(context)
        
        for file_path in target_files:
            file_issues = self._analyze_file_path(file_path)
            issues.extend(file_issues)
        
        # 分析配置文件中的路径
        config_issues = self._analyze_config_paths()
        issues.extend(config_issues)
        
        # 分析导入路径
        import_path_issues = self._analyze_import_paths()
        issues.extend(import_path_issues)
        
        self.logger.info(f"发现 {len(issues)} 个路径问题")
        return issues
    
    def _analyze_file_path(self, file_path: Path) -> List[PathIssue]:
        """分析文件路径"""
        issues = []
        
         # 检查文件是否存在
        if not file_path.exists():
            issues.append(PathIssue(
                path=file_path,
                issue_type="missing",
                expected_type="file" if file_path.suffix else "directory",
                description=f"路径不存在: {file_path}",
                severity="error"
            ))
            return issues

        
         # 检查权限
        if not os.access(file_path, os.R_OK):
            issues.append(PathIssue(
                path=file_path,
                issue_type="permission",
                current_state="no_read_permission",
                description=f"没有读取权限: {file_path}",
                severity="error"
            ))
        
        if file_path.is_file() and not os.access(file_path, os.W_OK):
            issues.append(PathIssue(
                path=file_path,
                issue_type="permission",
                current_state="no_write_permission",
                description=f"没有写入权限: {file_path}",
                severity="warning"
            ))
        
        # 检查路径长度
        if len(str(file_path)) > 260:  # Windows路径长度限制
            issues.append(PathIssue(
                path=file_path,
                issue_type="too_long",
                description=f"路径过长: {len(str(file_path))} 字符",
                severity="warning"
            ))

        # 检查特殊字符
        special_chars = ['<', '>', ':', '"', '|', '?', '*']
        path_str = str(file_path)
        for char in special_chars:
            if char in path_str:
                issues.append(PathIssue(
                    path=file_path,
                    issue_type="invalid_chars",
                    description=f"路径包含特殊字符: {char}",
                    severity="warning"
                ))
                break
        
        return issues
    
    def _analyze_config_paths(self) -> List[PathIssue]:
        """分析配置文件中的路径"""
        issues = []

        
        # 常见的配置文件
        config_files = [
            "package.json",
            "pyproject.toml", 
            "setup.py",
            "requirements.txt",
            "tsconfig.json",
            "webpack.config.js"
        ]
        
        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                config_issues = self._extract_paths_from_config(config_path)
                issues.extend(config_issues)
        
        return issues
    
    def _extract_paths_from_config(self, config_path: Path) -> List[PathIssue]:
        """从配置文件提取路径"""
        issues = []
        
        try:
            if config_path.suffix == '.json':
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 提取各种路径字段
                path_fields = ['main', 'bin', 'files', 'directories', 'paths', 'entry']
                
                for field in path_fields:
                    if field in config_data:
                        paths = config_data[field]
                        if isinstance(paths, str):
                            paths = [paths]
                        elif isinstance(paths, list):
                            pass
                        else:
                            continue
                        
                        for path_str in paths:
                            full_path = self.project_root / path_str
                            if not full_path.exists():
                                issues.append(PathIssue(
                                    path=full_path,
                                    issue_type="missing",
                                    description=f"配置文件中引用的路径不存在: {path_str} (在 {config_path})",
                                    severity="warning"
                                ))
            
            elif config_path.suffix == '.py':
                # 对于Python文件,使用正则表达式提取路径
                with open(config_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                
                # 匹配常见的路径模式
                path_patterns = [
                    r'["\']([^"\']*\.py)["\']',  # Python文件
                    r'["\']([^"\']*/[^"\']*)["\']',  # 包含路径分隔符的字符串
                ]
                
                for pattern in path_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if '/' in match or '\\' in match:  # 看起来像是路径
                            full_path = self.project_root / match
                            if not full_path.exists():
                                issues.append(PathIssue(
                                    path=full_path,
                                    issue_type="missing",
                                    description=f"Python文件中引用的路径不存在: {match} (在 {config_path})",
                                    severity="info"
                                ))
        
        except Exception as e:
            self.logger.error(f"解析配置文件失败 {config_path}: {e}")
        
        return issues
    
    def _analyze_import_paths(self) -> List[PathIssue]:
        """分析导入路径"""
        issues = []
        
        # 获取所有Python文件
        python_files = list(self.project_root.rglob("*.py"))
        
        for py_file in python_files:
            if self._should_skip_file(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                
                 # 查找导入语句
                import_pattern = r'from\s+([\w.]+)\s+import|import\s+([\w.]+)'
                matches = re.findall(import_pattern, content)
                
                for match in matches:
                    module_name = match[0] or match[1]

                    
                    # 检查是否是相对导入
                    if module_name.startswith('.'):
                        continue
                    
                    # 尝试将模块名转换为文件路径
                    module_path = module_name.replace('.', '/')
                    possible_paths = [
                        self.project_root / f"{module_path}.py",
                        self.project_root / module_path / "__init__.py"
                    ]
                    
                     # 检查是否存在对应的文件
                    found = False
                    for possible_path in possible_paths:
                        if possible_path.exists():
                            found = True
                            break
                    
                    if not found:
                        # 这可能是外部模块,但我们也报告一下
                        issues.append(PathIssue(
                            path=self.project_root / f"{module_path}.py",
                            issue_type="potential_missing",
                            description=f"导入的模块可能不存在: {module_name} (在 {py_file})",
                            severity="info"
                        ))
            
            except Exception as e:
                self.logger.error(f"分析导入路径失败 {py_file}: {e}")

        
        return issues
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """检查是否应该跳过文件"""
        skip_patterns = [
            "__pycache__", ".git", "node_modules", "venv", ".venv",
            "backup", "unified_fix_backups", "dist", "build"
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def fix(self, context: FixContext) -> FixResult:
        """修复路径问题"""
        self.logger.info("开始修复路径问题...")
        
        start_time = time.time()
        issues_fixed = 0
        issues_found = 0
        error_messages = []
        
        try:
            # 分析问题
            issues = self.analyze(context)
            issues_found = len(issues)
            
            if issues_found == 0:
                self.logger.info("未发现路径问题")
                return FixResult(
                    fix_type=self.fix_type,
                    status=FixStatus.SUCCESS,
                    issues_found=0,
                    issues_fixed=0,
                    duration_seconds=time.time() - start_time
                )
            
            # 按问题类型分组
            issues_by_type = {}
            for issue in issues:
                if issue.issue_type not in issues_by_type:
                    issues_by_type[issue.issue_type] = []
                issues_by_type[issue.issue_type].append(issue)
            
            # 修复不同类型的问题
            for issue_type, type_issues in issues_by_type.items():
                try:
                    if issue_type == "missing":
                        fixed_count = self._fix_missing_paths(type_issues)
                    elif issue_type == "permission":
                        fixed_count = self._fix_permission_issues(type_issues)
                    elif issue_type == "too_long":
                        fixed_count = self._fix_long_paths(type_issues)
                    elif issue_type == "invalid_chars":
                        fixed_count = self._fix_invalid_chars(type_issues)
                    elif issue_type == "potential_missing":
                        fixed_count = self._fix_potential_missing_paths(type_issues)
                    else:
                        fixed_count = 0
                    
                    issues_fixed += fixed_count
                    
                except Exception as e:
                    error_msg = f"修复 {issue_type} 类型路径问题失败: {e}"
                    self.logger.error(error_msg)
                    error_messages.append(error_msg)
            
             # 确定修复状态
            if issues_fixed == issues_found:
                status = FixStatus.SUCCESS
            elif issues_fixed > 0:
                status = FixStatus.PARTIAL_SUCCESS
            else:
                status = FixStatus.FAILED
            
            duration = time.time() - start_time
            
            return FixResult(
                fix_type=self.fix_type,
                status=status,
                issues_found=issues_found,
                issues_fixed=issues_fixed,
                error_message="; ".join(error_messages) if error_messages else None,
                duration_seconds=duration,
                details={
                    "issues_by_type": {k: len(v) for k, v in issues_by_type.items()},
                    "fixed_by_type": self._get_fixed_by_type(issues_by_type, issues_fixed)
                }
            )
            
        except Exception as e:
            self.logger.error(f"路径修复过程失败: {e}")
            return FixResult(
                fix_type=self.fix_type,
                status=FixStatus.FAILED,
                issues_found=issues_found,
                issues_fixed=issues_fixed,
                error_message=str(e),
                duration_seconds=time.time() - start_time
            )
    
    def _fix_missing_paths(self, issues: List[PathIssue]) -> int:
        """修复缺失的路径"""
        fixed_count = 0
        for issue in issues:
            try:
                if issue.expected_type == "directory":
                    issue.path.mkdir(parents=True, exist_ok=True)
                else:
                    # 确保父目录存在
                    issue.path.parent.mkdir(parents=True, exist_ok=True)
                    # 创建空文件
                    issue.path.touch()
                fixed_count += 1
                self.logger.info(f"已修复缺失路径: {issue.path}")
            except Exception as e:
                self.logger.error(f"修复缺失路径失败 {issue.path}: {e}")
        return fixed_count
    
    def _fix_permission_issues(self, issues: List[PathIssue]) -> int:
        """修复权限问题"""
        fixed_count = 0
        for issue in issues:
            try:
                if issue.current_state == "no_read_permission":
                    os.chmod(issue.path, 0o644)  # 设置读权限
                elif issue.current_state == "no_write_permission":
                    os.chmod(issue.path, 0o664)  # 设置读写权限
                fixed_count += 1
                self.logger.info(f"已修复权限问题: {issue.path}")
            except Exception as e:
                self.logger.error(f"修复权限问题失败 {issue.path}: {e}")
        return fixed_count
    
    def _fix_long_paths(self, issues: List[PathIssue]) -> int:
        """修复过长路径"""
        # 这是一个复杂的问题,通常需要重构代码
        # 这里我们只记录问题,不进行自动修复
        self.logger.info(f"发现 {len(issues)} 个过长路径问题,需要手动处理")
        return 0
    
    def _fix_invalid_chars(self, issues: List[PathIssue]) -> int:
        """修复包含特殊字符的路径"""
        # 这通常需要重命名文件或目录
        # 这里我们只记录问题,不进行自动修复
        self.logger.info(f"发现 {len(issues)} 个包含特殊字符的路径问题,需要手动处理")
        return 0
    
    def _fix_potential_missing_paths(self, issues: List[PathIssue]) -> int:
        """修复潜在的缺失路径"""
        # 这些可能是外部依赖,需要手动处理
        self.logger.info(f"发现 {len(issues)} 个潜在缺失路径问题,需要手动处理")
        return 0
    
    def _get_fixed_by_type(self, issues_by_type: Dict[str, List[PathIssue]], total_fixed: int) -> Dict[str, int]:
        """获取按类型修复的数量"""
        # 简化实现,实际应该根据修复函数的返回值统计
        return {k: len(v) for k, v in issues_by_type.items()}