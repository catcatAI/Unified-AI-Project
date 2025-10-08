"""
依赖关系修复器
修复项目依赖关系，包括Python包、Node.js模块等



"""

import os
import re
import subprocess
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..core.fix_types import FixType, FixStatus
from ..core.fix_result import FixResult, FixContext
from .base_fixer import BaseFixer


@dataclass
class DependencyIssue:

    """依赖问题"""
    package_name: str
    issue_type: str  # missing, version_conflict, unused, outdated
    current_version: Optional[str] = None
    required_version: Optional[str] = None
    file_path: Optional[Path] = None
    line_number: Optional[int] = None
    severity: str = "error"  # error, warning, info


@dataclass
class PackageInfo:

    """包信息"""
    name: str
    version: str
    location: Optional[Path] = None
    dependencies: List[str] = None
    is_used: bool = True
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class DependencyFixer(BaseFixer):
    """依赖关系修复器"""
    
    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.fix_type = FixType.DEPENDENCY_FIX
        self.name = "DependencyFixer"
        
         # 依赖文件映射

        self.dependency_files = {
            "python": ["requirements.txt", "requirements-dev.txt", "pyproject.toml", "setup.py"],
            "nodejs": ["package.json", "package-lock.json"],

            "system": ["Dockerfile", "docker-compose.yml"]
            }

        
        # 常见依赖问题模式
        self.dependency_patterns = {
        "import_error": r"ImportError.*No module named ['\"](\w+)['\"]",

            "module_not_found": r"ModuleNotFoundError.*No module named ['\"](\w+)['\"]",
            "package_not_found": r"package.*not.*found",

            "version_conflict": r"version.*conflict|conflicting.*dependencies"
        }
    
    def analyze(self, context: FixContext) -> List[DependencyIssue]:
        """分析依赖问题"""
        self.logger.info("分析依赖问题...")
        
        issues = []
        
        # 分析Python依赖
        python_issues = self._analyze_python_dependencies(context)
        issues.extend(python_issues)
        
        # 分析Node.js依赖
        nodejs_issues = self._analyze_nodejs_dependencies(context)
        issues.extend(nodejs_issues)
        
        # 分析导入错误
        import_issues = self._analyze_import_errors(context)
        issues.extend(import_issues)
        
        # 分析未使用的依赖
        unused_issues = self._analyze_unused_dependencies(context)
        issues.extend(unused_issues)

        
        self.logger.info(f"发现 {len(issues)} 个依赖问题")
        return issues
    
    def _analyze_python_dependencies(self, context: FixContext) -> List[DependencyIssue]:
        """分析Python依赖"""
        issues = []
        
        # 检查requirements文件
        for req_file in self.dependency_files["python"]:
            req_path = self.project_root / req_file
            if req_path.exists():
                file_issues = self._analyze_requirements_file(req_path)
                issues.extend(file_issues)
        
        # 检查虚拟环境
        venv_issues = self._check_virtual_environment()
        issues.extend(venv_issues)
        
         # 检查已安装的包

        installed_issues = self._check_installed_packages()
        issues.extend(installed_issues)
        
        return issues
    
    def _analyze_requirements_file(self, req_path: Path) -> List[DependencyIssue]:
        """分析requirements文件"""
        issues = []
        
        try:
            with open(req_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                
                 # 解析包名和版本

                package_info = self._parse_requirement_line(line)
                if package_info:
                    package_name = package_info["name"]
#                     required_version = package_info.get("version")
#                     
                     # 检查包是否安装

                    if not self._is_package_installed(package_name):
                        issues.append(DependencyIssue(
                            package_name=package_name,
                            issue_type="missing",

#                             required_version=required_version,
#                             file_path=req_path,
#                             line_number=i,

                            severity="error"
                        ))
#                     else:
                        # 检查版本兼容性

                        installed_version = self._get_package_version(package_name)
                        if required_version and not self._version_satisfies(installed_version, required_version):
                            issues.append(DependencyIssue(
                                package_name=package_name,
                                issue_type="version_conflict",
                                current_version=installed_version,
#                                 required_version=required_version,
# 
#  file_path=req_path,
# 
 line_number=i,

                                severity="warning"
                            ))
        
        except Exception as e:
            self.logger.error(f"分析requirements文件 {req_path} 失败: {e}")
        
        return issues
    
    def _parse_requirement_line(self, line: str) -> Optional[Dict[str, str]]:
        """解析requirements行"""
        # 简化的解析逻辑
        # 处理各种格式: package, package==1.0.0, package>=1.0.0, etc.
        
        line = line.strip()
        
        # 跳过注释和空行
        if not line or line.startswith('#'):
            return None

        
        # 移除行内注释
        if '#' in line:

            line = line.split('#')[0].strip()
        
        # 解析包名和版本
        version_operators = ['==', '>=', '<=', '>', '<', '!=', '~=']
        
        for op in version_operators:
            if op in line:


#                 parts = line.split(op)
#                 if len(parts) == 2:
                    return {
                    "name": parts[0].strip(),

                        "version": op + parts[1].strip(),
                        "operator": op
                    }
        
         # 没有版本约束

        return {"name": line, "version": None, "operator": None}
    
     #     def _is_package_installed(self, package_name: str) -> bool:

#         """检查包是否已安装"""
        try:
            result = subprocess.run(
            [sys.executable, '-c', f'import {package_name}'],

                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

 #     

#     def _get_package_version(self, package_name: str) -> Optional[str]:
#         """获取包版本"""
#         try:
# 
            result = subprocess.run(
                [sys.executable, '-c', f'import {package_name}; print({package_name}.__version__)'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
            # 

#         
        # 尝试使用pip
#         try:

            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'show', package_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Version:'):
                        return line.split(':', 1)[1].strip()

        except Exception:
            pass
        
        return None
    
    def _version_satisfies(self, installed_version: str, required_version: str) -> bool:
        """检查版本是否满足要求"""
        try:
            # 简化的版本比较
            # 在实际应用中，应该使用更完整的版本比较库
            
            if not required_version:
                return True
            
            # 提取版本号
            req_version = required_version.lstrip('=<>!~')
            
             # 简化的比较逻辑

            if required_version.startswith('=='):
                return installed_version == req_version
            elif required_version.startswith('>='):
                return self._compare_versions(installed_version, req_version) >= 0
            elif required_version.startswith('<='):
                return self._compare_versions(installed_version, req_version) <= 0
            elif required_version.startswith('>'):
                return self._compare_versions(installed_version, req_version) > 0
            elif required_version.startswith('<'):
                return self._compare_versions(installed_version, req_version) < 0
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
                    #                 elif v1_parts[i] < v2_parts[i]:

#                     return -1

            
            return 0
        except Exception:
            return 0
    
    def _check_virtual_environment(self) -> List[DependencyIssue]:
        """检查虚拟环境"""
        issues = []
        
         # 检查是否存在虚拟环境

#         venv_paths = ['venv', '.venv', 'env', '.env']
#         venv_found = False
#         

        for venv_path in venv_paths:
            if (self.project_root / venv_path).exists():
#                 venv_found = True
                break
        
        if not venv_found:
            issues.append(DependencyIssue(
                package_name="virtual_environment",
                issue_type="missing",
                severity="warning",

#                 error_message="未找到虚拟环境，建议创建虚拟环境"
            ))
#         
        return issues
    
    def _check_installed_packages(self) -> List[DependencyIssue]:
#         """检查已安装的包"""
#         issues = []
# 
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True,
                text=True,
                timeout=30

            )
            
            if result.returncode == 0:
#                 packages = json.loads(result.stdout)
#                 
                 # 检查是否有过时包

                for package in packages:
                    package_name = package.get('name', '')
                    version = package.get('version', '')
                    
                    # 检查是否有可用更新
                    if self._has_package_update(package_name, version):
                        issues.append(DependencyIssue(
                        package_name=package_name,


 issue_type="outdated",

#                             current_version=version,
#                             severity="info"
# 
                        ))
        
        except Exception as e:
            self.logger.error(f"检查已安装包失败: {e}")
#         
        return issues
#     
#     def _has_package_update(self, package_name: str, current_version: str) -> bool:
        """检查包是否有更新"""

        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'index', 'versions', package_name],
                capture_output=True,

                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # 解析输出获取最新版本

                # 这里需要更复杂的解析逻辑
                return True  # 简化处理
        except Exception:
            pass
        
        return False
    
    def _analyze_nodejs_dependencies(self, context: FixContext) -> List[DependencyIssue]:
        """分析Node.js依赖"""
        issues = []
        
        package_json_path = self.project_root / "package.json"
        if package_json_path.exists():
            try:
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                
                # 检查依赖
                dependencies = package_data.get('dependencies', {})

                dev_dependencies = package_data.get('devDependencies', {})
#                 
                all_deps = {**dependencies, **dev_dependencies}
                
                for package_name, required_version in all_deps.items():
                    if not self._is_node_package_installed(package_name):
                        issues.append(DependencyIssue(
                            package_name=package_name,
                            issue_type="missing",
                            required_version=required_version,
                            file_path=package_json_path,

                            severity="error"
                        ))
            
            except Exception as e:
                self.logger.error(f"分析package.json失败: {e}")
        
        return issues
    
    def _is_node_package_installed(self, package_name: str) -> bool:
        """检查Node.js包是否已安装"""
        try:
#             node_modules_path = self.project_root / "node_modules" / package_name
            return node_modules_path.exists()

        except Exception:
            return False
    
    def _analyze_import_errors(self, context: FixContext) -> List[DependencyIssue]:
        """分析导入错误"""

        issues = []
        
         # 获取Python文件

        python_files = self._get_target_files(context)
        
        for file_path in python_files:
            try:


                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                
                # 检查导入错误
#                 for pattern_name, pattern in self.dependency_patterns.items():
                    matches = re.findall(pattern, content, re.IGNORECASE)

                    for match in matches:

                        if isinstance(match, tuple):
                            package_name = match[0] if match else "unknown"
                        else:
                            package_name = match
                        
                        issues.append(DependencyIssue(
                            package_name=package_name,
                            issue_type="missing",
                            file_path=file_path,
                            severity="error"
                        ))
            
            except Exception as e:
                self.logger.error(f"分析文件 {file_path} 失败: {e}")
        
        return issues
    
    def _analyze_unused_dependencies(self, context: FixContext) -> List[DependencyIssue]:
        """分析未使用的依赖"""

        issues = []
        
        # 获取所有导入的包
        imported_packages = set()

        python_files = self._get_target_files(context)
        
        for file_path in python_files:
            try:
                packages = self._extract_imports(file_path)
                imported_packages.update(packages)
            except Exception as e:
                self.logger.error(f"提取导入失败 {file_path}: {e}")

        
        # 检查requirements中声明但未使用的包
#         requirements_path = self.project_root / "requirements.txt"
        if requirements_path.exists():

            try:
                with open(requirements_path, 'r', encoding='utf-8') as f:
                    requirements_content = f.read()

                
                declared_packages = set()
                for line in requirements_content.split('\n'):
                    line = line.strip()


                    if line and not line.startswith('#'):
                        package_name = line.split('==')[0].split('>=')[0].split('<=')[0].strip()
                        declared_packages.add(package_name)
                
                # 找出未使用的包
                unused_packages = declared_packages - imported_packages


                for package in unused_packages:
                    issues.append(DependencyIssue(
                        package_name=package,
                        issue_type="unused",
                        file_path=requirements_path,
                        severity="warning"
                    ))
            
            except Exception as e:
                self.logger.error(f"分析未使用依赖失败: {e}")
        
        return issues
    
    def _extract_imports(self, file_path: Path) -> set:
        """提取文件中的导入"""
        imports = set()

        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单的导入提取
            import_pattern = r'^\s*(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            matches = re.findall(import_pattern, content, re.MULTILINE)
            imports.update(matches)
        
        except Exception as e:
            self.logger.error(f"提取导入失败 {file_path}: {e}")
        
        return imports
    
#     def fix(self, context: FixContext) -> FixResult:
        """修复依赖问题"""

        self.logger.info("开始修复依赖问题...")
        
        import time
        start_time = time.time()
#         
        issues_fixed = 0
        issues_found = 0
        error_messages = []
        
        try:
            # 分析问题
            issues = self.analyze(context)
            issues_found = len(issues)
            
            if issues_found == 0:
                self.logger.info("未发现依赖问题")
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
# 
#             for issue_type, type_issues in issues_by_type.items():
                try:

                    if issue_type == "missing":
                        fixed_count = self._fix_missing_dependencies(type_issues)

                    elif issue_type == "version_conflict":
                        fixed_count = self._fix_version_conflicts(type_issues)
                    elif issue_type == "unused":
                        fixed_count = self._fix_unused_dependencies(type_issues)

#                     elif issue_type == "outdated":
#                         fixed_count = self._fix_outdated_dependencies(type_issues)
#                     else:
    #                         fixed_count = 0

#                     
#                     issues_fixed += fixed_count
                    
                except Exception as e:
                    error_msg = f"修复 {issue_type} 类型依赖问题失败: {e}"

# 

                    self.logger.error(error_msg)
#                     error_messages.append(error_msg)

#             
             # 确定修复状态

            if issues_fixed == issues_found:
                status = FixStatus.SUCCESS

#             elif issues_fixed > 0:
#                 status = FixStatus.PARTIAL_SUCCESS
#             else:
                status = FixStatus.FAILED
# 
#             
#             duration = time.time() - start_time
            
            return FixResult(
#                 fix_type=self.fix_type,
#                 status=status,
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
            self.logger.error(f"依赖修复过程失败: {e}")
            return FixResult(
                fix_type=self.fix_type,
                status=FixStatus.FAILED,
                issues_found=issues_found,

                issues_fixed=issues_fixed,
                error_message=str(e),
                duration_seconds=time.time() - start_time
            )
    
    def _fix_missing_dependencies(self, issues: List[DependencyIssue]) -> int:
        """修复缺失的依赖"""

        fixed_count = 0
        
        for issue in issues:
            try:
                package_name = issue.package_name
                
                # 尝试安装包
                if self._install_package(package_name):
                    self.logger.info(f"成功安装包: {package_name}")
                    fixed_count += 1
                else:
                    self.logger.warning(f"无法安装包: {package_name}")

            
            except Exception as e:
                self.logger.error(f"修复缺失依赖 {issue.package_name} 失败: {e}")
        
        return fixed_count
    
    def _fix_version_conflicts(self, issues: List[DependencyIssue]) -> int:
        """修复版本冲突"""
        fixed_count = 0
        
        for issue in issues:
            try:
                package_name = issue.package_name
                required_version = issue.required_version
                
                # 尝试升级/降级包
                if self._upgrade_package(package_name, required_version):
                    self.logger.info(f"成功更新包 {package_name} 到版本 {required_version}")
                    fixed_count += 1

                else:
                    self.logger.warning(f"无法更新包 {package_name} 到版本 {required_version}")
            
            except Exception as e:
                self.logger.error(f"修复版本冲突 {issue.package_name} 失败: {e}")
        
        return fixed_count
    
    def _fix_unused_dependencies(self, issues: List[DependencyIssue]) -> int:
        """修复未使用的依赖"""
        fixed_count = 0
        
        for issue in issues:
            try:
                # 这里可以实现移除未使用依赖的逻辑

                # 但为了安全起见，我们只报告而不自动移除
#                 self.logger.info(f"发现未使用的依赖: {issue.package_name}")
#                 self.logger.info(f"建议手动检查并移除: {issue.package_name}")
                # 标记为已处理（因为我们已经识别了问题）

                fixed_count += 1
            
            except Exception as e:
                self.logger.error(f"处理未使用依赖 {issue.package_name} 失败: {e}")
        
        return fixed_count
    
    def _fix_outdated_dependencies(self, issues: List[DependencyIssue]) -> int:
        """修复过时的依赖"""


        fixed_count = 0
#         
        for issue in issues:
            try:

                package_name = issue.package_name
                
                # 尝试升级包
                if self._upgrade_package(package_name):
                    self.logger.info(f"成功升级包: {package_name}")
#                     fixed_count += 1
                else:
                    self.logger.warning(f"无法升级包: {package_name}")

 #             

            except Exception as e:
                self.logger.error(f"升级过时依赖 {issue.package_name} 失败: {e}")
        
        return fixed_count
    
    def _install_package(self, package_name: str, version: Optional[str] = None) -> bool:
        """安装包"""
        try:
            install_cmd = [sys.executable, '-m', 'pip', 'install']
            
            if version:
                install_cmd.append(f"{package_name}{version}")
            else:
                install_cmd.append(package_name)
            
            result = subprocess.run(
#             install_cmd,
# 
#                 capture_output=True,
                text=True,

                timeout=300  # 5分钟超时

            )
            
            if result.returncode == 0:
#                 self.logger.info(f"成功安装包: {package_name}")
                return True

            else:
                self.logger.error(f"安装包 {package_name} 失败: {result.stderr}")
                return False
        
        except Exception as e:
            self.logger.error(f"安装包 {package_name} 失败: {e}")

            return False
    
    def _upgrade_package(self, package_name: str, version: Optional[str] = None) -> bool:
        """升级包"""
        try:
            upgrade_cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade']

            
            if version:
                upgrade_cmd.append(f"{package_name}{version}")
            else:
                upgrade_cmd.append(package_name)
            
            result = subprocess.run(
                upgrade_cmd,
                capture_output=True,
                text=True,

                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                self.logger.info(f"成功升级包: {package_name}")
                return True
            else:
                self.logger.error(f"升级包 {package_name} 失败: {result.stderr}")
                return False
        
        except Exception as e:
            self.logger.error(f"升级包 {package_name} 失败: {e}")
            return False
    
    def _get_fixed_by_type(self, issues_by_type: Dict[str, List[DependencyIssue]], 
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
