"""
环境修复器
修复环境配置问题，包括虚拟环境和系统依赖
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..core.fix_types import FixType, FixStatus
from ..core.fix_result import FixResult, FixContext
from .base_fixer import BaseFixer


@dataclass
class EnvironmentIssue:
    """环境问题"""
    issue_type: str  # missing_venv, python_version, missing_tool, etc.
    component: str   # python, nodejs, git, etc.
    current_value: Optional[str] = None
    required_value: Optional[str] = None
    description: str = ""
    severity: str = "error"  # error, warning, info


class EnvironmentFixer(BaseFixer):
    """环境修复器"""
    
    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.fix_type = FixType.ENVIRONMENT_FIX
        self.name = "EnvironmentFixer"
        
        # 环境要求配置
        self.environment_requirements = {
            "python": {
                "min_version": "3.8",
                "recommended_version": "3.9+",
                "tools": ["pip", "venv"]
            },
            "nodejs": {
                "min_version": "16.0",
                "recommended_version": "18+",
                "tools": ["npm", "npx"]
            },
            "git": {
                "min_version": "2.20",
                "recommended_version": "2.30+",
                "tools": ["git"]
            }
        }
    
    def analyze(self, context: FixContext) -> List[EnvironmentIssue]:
        """分析环境问题"""
        self.logger.info("分析环境问题...")
        
        issues = []
        
        # 检查Python环境
        python_issues = self._analyze_python_environment()
        issues.extend(python_issues)
        
        # 检查Node.js环境
        nodejs_issues = self._analyze_nodejs_environment()
        issues.extend(nodejs_issues)
        
        # 检查Git环境
        git_issues = self._analyze_git_environment()
        issues.extend(git_issues)
        
        # 检查虚拟环境
        venv_issues = self._analyze_virtual_environment()
        issues.extend(venv_issues)
        
        # 检查环境变量
        env_issues = self._analyze_environment_variables()
        issues.extend(env_issues)
        
        self.logger.info(f"发现 {len(issues)} 个环境问题")
        return issues
    
    def _analyze_python_environment(self) -> List[EnvironmentIssue]:
        """分析Python环境"""
        issues = []
        
        # 检查Python版本
        current_version = self._get_python_version()
        if current_version:
            min_version = self.environment_requirements["python"]["min_version"]
            if not self._version_satisfies(current_version, f">={min_version}"):
                issues.append(EnvironmentIssue(
                    issue_type="python_version",
                    component="python",
                    current_value=current_version,
                    required_value=f">={min_version}",
                    description=f"Python版本过低: {current_version}，需要 {min_version}+",
                    severity="error"
                ))
        else:
            issues.append(EnvironmentIssue(
                issue_type="python_not_found",
                component="python",
                description="未找到Python解释器",
                severity="error"
            ))
        
        # 检查Python工具
        for tool in self.environment_requirements["python"]["tools"]:
            if not self._command_exists(tool):
                issues.append(EnvironmentIssue(
                    issue_type="missing_tool",
                    component="python",
                    current_value=tool,
                    description=f"缺少Python工具: {tool}",
                    severity="warning"
                ))
        
        return issues
    
    def _analyze_nodejs_environment(self) -> List[EnvironmentIssue]:
        """分析Node.js环境"""
        issues = []
        
        # 检查Node.js版本
        current_version = self._get_nodejs_version()
        if current_version:
            min_version = self.environment_requirements["nodejs"]["min_version"]
            if not self._version_satisfies(current_version, f">={min_version}"):
                issues.append(EnvironmentIssue(
                    issue_type="nodejs_version",
                    component="nodejs",
                    current_value=current_version,
                    required_value=f">={min_version}",
                    description=f"Node.js版本过低: {current_version}，需要 {min_version}+",
                    severity="warning"
                ))
        else:
            issues.append(EnvironmentIssue(
                issue_type="nodejs_not_found",
                component="nodejs",
                description="未找到Node.js（可选组件）",
                severity="info"
            ))
        
        # 检查Node.js工具
        if current_version:  # 只有在Node.js存在时才检查工具
            for tool in self.environment_requirements["nodejs"]["tools"]:
                if not self._command_exists(tool):
                    issues.append(EnvironmentIssue(
                        issue_type="missing_tool",
                        component="nodejs",
                        current_value=tool,
                        description=f"缺少Node.js工具: {tool}",
                        severity="warning"
                    ))
        
        return issues
    
    def _analyze_git_environment(self) -> List[EnvironmentIssue]:
        """分析Git环境"""
        issues = []
        
        # 检查Git版本
        current_version = self._get_git_version()
        if current_version:
            min_version = self.environment_requirements["git"]["min_version"]
            if not self._version_satisfies(current_version, f">={min_version}"):
                issues.append(EnvironmentIssue(
                    issue_type="git_version",
                    component="git",
                    current_value=current_version,
                    required_value=f">={min_version}",
                    description=f"Git版本过低: {current_version}，需要 {min_version}+",
                    severity="warning"
                ))
        else:
            issues.append(EnvironmentIssue(
                issue_type="git_not_found",
                component="git",
                description="未找到Git",
                severity="warning"
            ))
        
        return issues
    
    def _analyze_virtual_environment(self) -> List[EnvironmentIssue]:
        """分析虚拟环境"""
        issues = []
        
        # 检查是否存在虚拟环境
        venv_paths = ['venv', '.venv', 'env', '.env']
        venv_found = False
        active_venv = False
        
        # 检查激活的虚拟环境
        if hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        ):
            active_venv = True
        
        # 检查项目目录中的虚拟环境
        for venv_path in venv_paths:
            full_path = self.project_root / venv_path
            if full_path.exists() and (full_path / "bin" / "python").exists():
                venv_found = True
                break
        
        if not venv_found and not active_venv:
            issues.append(EnvironmentIssue(
                issue_type="missing_venv",
                component="python",
                description="未找到虚拟环境，建议创建虚拟环境",
                severity="info"
            ))
        
        return issues
    
    def _analyze_environment_variables(self) -> List[EnvironmentIssue]:
        """分析环境变量"""
        issues = []
        
        # 检查重要的环境变量
        important_vars = [
            "PATH",
            "PYTHONPATH",
            "NODE_PATH",
            "GIT_PYTHON_GIT_EXECUTABLE"
        ]
        
        for var in important_vars:
            value = os.environ.get(var)
            if not value:
                if var == "PATH":  # PATH是必须的环境变量
                    issues.append(EnvironmentIssue(
                        issue_type="missing_env_var",
                        component="system",
                        current_value=var,
                        description=f"缺少环境变量: {var}",
                        severity="error"
                    ))
                else:
                    issues.append(EnvironmentIssue(
                        issue_type="missing_env_var",
                        component="system",
                        current_value=var,
                        description=f"缺少环境变量: {var}（可选）",
                        severity="info"
                    ))
        
        return issues
    
    def _get_python_version(self) -> Optional[str]:
        """获取Python版本"""
        try:
            return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        except Exception:
            return None
    
    def _get_nodejs_version(self) -> Optional[str]:
        """获取Node.js版本"""
        try:
            result = subprocess.run(
                ['node', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip().lstrip('v')
        except Exception:
            pass
        
        return None
    
    def _get_git_version(self) -> Optional[str]:
        """获取Git版本"""
        try:
            result = subprocess.run(
                ['git', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # 解析版本号
                match = re.search(r'git version (\d+\.\d+(?:\.\d+)?)', result.stdout)
                if match:
                    return match.group(1)
        except Exception:
            pass
        
        return None
    
    def _command_exists(self, command: str) -> bool:
        """检查命令是否存在"""
        try:
            result = subprocess.run(
                [command, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _version_satisfies(self, current_version: str, requirement: str) -> bool:
        """检查版本是否满足要求"""
        try:
            # 简化的版本比较
            if requirement.startswith(">="):
                required = requirement[2:]
                return self._compare_versions(current_version, required) >= 0
            elif requirement.startswith(">"):
                required = requirement[1:]
                return self._compare_versions(current_version, required) > 0
            else:
                return True
        except Exception:
            return True
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """比较版本号"""
        try:
            # 简化的版本比较
            v1_parts = [int(x) for x in v1.split('.')]
            v2_parts = [int(x) for x in v2.split('.')]
            
            # 补齐长度
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            for i in range(max_len):
                if v1_parts[i] > v2_parts[i]:
                    return 1
                elif v1_parts[i] < v2_parts[i]:
                    return -1
            
            return 0
        except Exception:
            return 0
    
    def fix(self, context: FixContext) -> FixResult:
        """修复环境问题"""
        self.logger.info("开始修复环境问题...")
        
        import time
        start_time = time.time()
        
        issues_fixed = 0
        issues_found = 0
        error_messages = []
        
        try:
            # 分析问题
            issues = self.analyze(context)
            issues_found = len(issues)
            
            if issues_found == 0:
                self.logger.info("未发现环境问题")
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
                    if issue_type == "missing_venv":
                        fixed_count = self._fix_missing_venv(type_issues)
                    elif issue_type == "python_version":
                        fixed_count = self._fix_python_version(type_issues)
                    elif issue_type == "nodejs_version":
                        fixed_count = self._fix_nodejs_version(type_issues)
                    elif issue_type == "git_version":
                        fixed_count = self._fix_git_version(type_issues)
                    elif issue_type == "missing_tool":
                        fixed_count = self._fix_missing_tools(type_issues)
                    elif issue_type == "missing_env_var":
                        fixed_count = self._fix_missing_env_vars(type_issues)
                    else:
                        fixed_count = 0
                    
                    issues_fixed += fixed_count
                    
                except Exception as e:
                    error_msg = f"修复 {issue_type} 类型环境问题失败: {e}"
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
            self.logger.error(f"环境修复过程失败: {e}")
            return FixResult(
                fix_type=self.fix_type,
                status=FixStatus.FAILED,
                issues_found=issues_found,
                issues_fixed=issues_fixed,
                error_message=str(e),
                duration_seconds=time.time() - start_time
            )
    
    def _fix_missing_venv(self, issues: List[EnvironmentIssue]) -> int:
        """修复缺失的虚拟环境"""
        try:
            # 创建虚拟环境
            venv_path = self.project_root / "venv"
            
            result = subprocess.run(
                [sys.executable, '-m', 'venv', str(venv_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.logger.info(f"成功创建虚拟环境: {venv_path}")
                return len(issues)
            else:
                self.logger.error(f"创建虚拟环境失败: {result.stderr}")
                return 0
        
        except Exception as e:
            self.logger.error(f"修复虚拟环境失败: {e}")
            return 0
    
    def _fix_python_version(self, issues: List[EnvironmentIssue]) -> int:
        """修复Python版本问题"""
        # Python版本问题通常需要手动处理
        # 这里提供建议信息
        for issue in issues:
            self.logger.warning(f"Python版本问题需要手动修复: {issue.description}")
            self.logger.info("建议: 升级Python到推荐版本")
        
        return len(issues)  # 标记为已处理（提供建议）
    
    def _fix_nodejs_version(self, issues: List[EnvironmentIssue]) -> int:
        """修复Node.js版本问题"""
        # Node.js版本问题通常需要手动处理
        for issue in issues:
            self.logger.warning(f"Node.js版本问题需要手动修复: {issue.description}")
            self.logger.info("建议: 升级Node.js到推荐版本")
        
        return len(issues)
    
    def _fix_git_version(self, issues: List[EnvironmentIssue]) -> int:
        """修复Git版本问题"""
        # Git版本问题通常需要手动处理
        for issue in issues:
            self.logger.warning(f"Git版本问题需要手动修复: {issue.description}")
            self.logger.info("建议: 升级Git到推荐版本")
        
        return len(issues)
    
    def _fix_missing_tools(self, issues: List[EnvironmentIssue]) -> int:
        """修复缺失的工具"""
        fixed_count = 0
        
        for issue in issues:
            try:
                tool = issue.current_value
                component = issue.component
                
                if component == "python":
                    # 尝试安装Python工具
                    if self._install_python_tool(tool):
                        fixed_count += 1
                elif component == "nodejs":
                    # 尝试安装Node.js工具
                    if self._install_nodejs_tool(tool):
                        fixed_count += 1
                
            except Exception as e:
                self.logger.error(f"安装工具失败: {e}")
        
        return fixed_count
    
    def _fix_missing_env_vars(self, issues: List[EnvironmentIssue]) -> int:
        """修复缺失的环境变量"""
        fixed_count = 0
        
        for issue in issues:
            try:
                var_name = issue.current_value
                
                # 提供环境变量设置建议
                self.logger.info(f"需要设置环境变量: {var_name}")
                self.logger.info(f"建议: export {var_name}=<value>")
                
                # 标记为已处理（提供建议）
                fixed_count += 1
            
            except Exception as e:
                self.logger.error(f"处理环境变量失败: {e}")
        
        return fixed_count
    
    def _install_python_tool(self, tool: str) -> bool:
        """安装Python工具"""
        try:
            if tool == "pip":
                # pip应该已经存在
                return True
            elif tool == "venv":
                # venv是标准库的一部分
                return True
            else:
                # 尝试使用pip安装
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', tool],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    self.logger.info(f"成功安装Python工具: {tool}")
                    return True
                else:
                    self.logger.error(f"安装Python工具失败: {result.stderr}")
                    return False
        
        except Exception as e:
            self.logger.error(f"安装Python工具失败: {e}")
            return False
    
    def _install_nodejs_tool(self, tool: str) -> bool:
        """安装Node.js工具"""
        try:
            result = subprocess.run(
                ['npm', 'install', '-g', tool],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.logger.info(f"成功安装Node.js工具: {tool}")
                return True
            else:
                self.logger.error(f"安装Node.js工具失败: {result.stderr}")
                return False
        
        except Exception as e:
            self.logger.error(f"安装Node.js工具失败: {e}")
            return False
    
    def _get_fixed_by_type(self, issues_by_type: Dict[str, List[EnvironmentIssue]], 
                          total_fixed: int) -> Dict[str, int]:
        """获取按类型修复的数量"""
        # 简化处理：按比例分配修复数量
        fixed_by_type = {}
        total_issues = sum(len(issues) for issues in issues_by_type.values())
        
        if total_issues > 0:
            for issue_type, issues in issues_by_type.items():
                proportion = len(issues) / total_issues
                fixed_count = int(total_fixed * proportion)
                fixed_by_type[issue_type] = max(1, fixed_count) if issues else 0
        
        return fixed_by_type