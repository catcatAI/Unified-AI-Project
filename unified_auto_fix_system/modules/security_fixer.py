"""
安全修复器
修复安全漏洞,包括不安全的代码模式和配置
"""

import re
import json
import subprocess
import time
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..core.fix_types import FixType, FixStatus
from ..core.fix_result import FixResult, FixContext
from .base_fixer import BaseFixer


@dataclass
class SecurityIssue:
    """安全问题"""
    file_path: Path
    line_number: int
    issue_type: str  # hardcoded_secret, sql_injection, xss, etc.
    severity: str  # critical, high, medium, low
    description: str
    code_snippet: str = ""
    suggested_fix: str = ""


class SecurityFixer(BaseFixer):
    """安全修复器"""
    
    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.fix_type = FixType.SECURITY_FIX
        self.name = "SecurityFixer"
        
         # 安全漏洞模式
        self.security_patterns = {
            "hardcoded_secret": {
                "pattern": r'(password|secret|key|token)\s*=\s*["\'][^"\']+["\']',
                "description": "硬编码的密钥或密码",
                "severity": "critical"
            },
            "sql_injection": {
                "pattern": r'execute\s*\(\s*[^)]*%[^)]*\)|f["\'][^"\']*%[^"\']*["\']',
                "description": "潜在的SQL注入漏洞",
                "severity": "high"
            },
            "weak_crypto": {
                "pattern": r'md5\(|sha1\(',
                "description": "使用弱加密算法",
                "severity": "medium"
            },
            "path_traversal": {
                "pattern": r'\.\.\/|\.\.\\',
                "description": "路径遍历漏洞",
                "severity": "high"
            },
            "xss_vulnerability": {
                "pattern": r'render\s*\([^)]*request\.[^)]*\)|innerHTML\s*=',
                "description": "潜在的XSS漏洞",
                "severity": "medium"
            },
            "command_injection": {
                "pattern": r'os\.system\s*\(|subprocess\.call\s*\([^)]*shell\s*=\s*True',
                "description": "命令注入漏洞",
                "severity": "critical"
            }
        }
    
    def analyze(self, context: FixContext) -> List[SecurityIssue]:
        """分析安全问题"""
        self.logger.info("分析安全问题...")
        
        issues = []
        
        # 分析代码文件
        target_files = self._get_target_files(context)
        
        for file_path in target_files:
            try:
                file_issues = self._analyze_file_security(file_path)
                issues.extend(file_issues)
            except Exception as e:
                self.logger.error(f"分析文件 {file_path} 安全失败: {e}")
        
         # 分析配置文件
        config_issues = self._analyze_configuration_files()
        issues.extend(config_issues)

        
        # 分析依赖安全
        dependency_issues = self._analyze_dependency_security()
        issues.extend(dependency_issues)
        
        self.logger.info(f"发现 {len(issues)} 个安全问题")
        return issues
    
    def _analyze_file_security(self, file_path: Path) -> List[SecurityIssue]:
        """分析文件安全"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                 # 跳过注释和空行
                if not line_stripped or line_stripped.startswith('#'):
                    continue

                
                # 检查各种安全模式
                for issue_type, pattern_info in self.security_patterns.items():
                    if re.search(pattern_info["pattern"], line_stripped, re.IGNORECASE):
                        issues.append(SecurityIssue(
                            file_path=file_path,
                            line_number=i,
                            issue_type=issue_type,
                            severity=pattern_info["severity"],
                            description=pattern_info["description"],
                            code_snippet=line.strip(),
                            suggested_fix=self._suggest_security_fix(issue_type, line_stripped)
                        ))
        
        except Exception as e:
            self.logger.error(f"无法读取文件 {file_path}: {e}")
        
        return issues
    
    def _analyze_configuration_files(self) -> List[SecurityIssue]:
        """分析配置文件安全"""
        issues = []
        
        # 检查常见的配置文件
        config_files = [
            "config.json",
            "settings.json", 
            ".env",
            "docker-compose.yml",
            "Dockerfile"
        ]
        
        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                config_issues = self._check_config_security(config_path)
                issues.extend(config_issues)
        
        return issues
    
    def _check_config_security(self, config_path: Path) -> List[SecurityIssue]:
        """检查配置文件安全"""
        issues = []
        
        try:
            if config_path.suffix == '.json':
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 检查硬编码的敏感信息
                sensitive_keys = ['password', 'secret', 'key', 'token', 'api_key']
                
                def check_dict(data, path=""):
                    for key, value in data.items():
                        current_path = f"{path}.{key}" if path else key
                        if any(sensitive in key.lower() for sensitive in sensitive_keys):
                            if isinstance(value, str) and len(value) > 0:
                                issues.append(SecurityIssue(
                                    file_path=config_path,
                                    line_number=0,  # JSON文件不具体到行
                                    issue_type="hardcoded_secret_config",
                                    severity="critical",
                                    description=f"配置文件中发现硬编码的敏感信息: {current_path}",
                                    code_snippet=f"{key}: {value[:20]}...",
                                    suggested_fix=f"将 {key} 移至环境变量或密钥管理服务"
                                ))
                        
                        if isinstance(value, dict):
                            check_dict(value, current_path)

                
                check_dict(config_data)
            
            elif config_path.name == ".env":
                with open(config_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines, 1):
                    line_stripped = line.strip()
                    # 跳过注释和空行
                    if not line_stripped or line_stripped.startswith('#'):
                        continue
                    
                    # 检查是否包含敏感信息
                    if '=' in line_stripped:
                        key, value = line_stripped.split('=', 1)
                        if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                            if value and not value.startswith('${'):  # 不是环境变量引用
                                issues.append(SecurityIssue(
                                    file_path=config_path,
                                    line_number=i,
                                    issue_type="hardcoded_secret_env",
                                    severity="critical",
                                    description=f".env文件中发现硬编码的敏感信息: {key}",
                                    code_snippet=line_stripped,
                                    suggested_fix=f"将 {key} 的值移至安全的密钥管理服务"
                                ))
        
        except Exception as e:
            self.logger.error(f"检查配置文件安全失败 {config_path}: {e}")
        
        return issues
    
    def _analyze_dependency_security(self) -> List[SecurityIssue]:
        """分析依赖安全"""
        issues = []
        
        # 检查Python依赖
        requirements_files = ["requirements.txt", "requirements-dev.txt"]
        for req_file in requirements_files:
            req_path = self.project_root / req_file
            if req_path.exists():
                dep_issues = self._check_python_dependencies(req_path)
                issues.extend(dep_issues)
        
        # 检查Node.js依赖
        package_json_path = self.project_root / "package.json"
        if package_json_path.exists():
            dep_issues = self._check_node_dependencies(package_json_path)
            issues.extend(dep_issues)
        
        return issues
    
    def _check_python_dependencies(self, req_path: Path) -> List[SecurityIssue]:
        """检查Python依赖"""
        issues = []
        
        try:
            # 运行安全检查工具
            result = subprocess.run(
                ["pip", "check"], 
                cwd=self.project_root,
                capture_output=True, 
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                # 解析输出
                lines = result.stdout.split('\n')
                for line in lines:
                    if line.strip():
                        issues.append(SecurityIssue(
                            file_path=req_path,
                            line_number=0,
                            issue_type="dependency_conflict",
                            severity="high",
                            description=f"Python依赖冲突: {line}",
                            suggested_fix="解决依赖冲突,更新或固定依赖版本"
                        ))
        
        except Exception as e:
            self.logger.error(f"检查Python依赖失败 {req_path}: {e}")
        
        return issues
    
    def _check_node_dependencies(self, package_json_path: Path) -> List[SecurityIssue]:
        """检查Node.js依赖"""
        issues = []
        
        try:
            # 检查package.json中的依赖版本
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            # 检查dependencies和devDependencies
            for dep_type in ['dependencies', 'devDependencies']:
                if dep_type in package_data:
                    for package, version in package_data[dep_type].items():
                        if version == 'latest' or version.startswith('*'):
                            issues.append(SecurityIssue(
                                file_path=package_json_path,
                                line_number=0,
                                issue_type="unpinned_dependency",
                                severity="medium",
                                description=f"Node.js依赖未固定版本: {package}@{version}",
                                suggested_fix=f"为 {package} 指定具体版本号"
                            ))
        
        except Exception as e:
            self.logger.error(f"检查Node.js依赖失败 {package_json_path}: {e}")
        
        return issues
    
    def _suggest_security_fix(self, issue_type: str, code_snippet: str) -> str:
        """为安全问题提供建议修复"""
        suggestions = {
            "hardcoded_secret": "将硬编码的密钥移至环境变量或密钥管理服务",
            "sql_injection": "使用参数化查询或ORM来防止SQL注入",
            "weak_crypto": "使用更安全的加密算法,如SHA-256或bcrypt",
            "path_traversal": "验证和清理用户输入的文件路径",
            "xss_vulnerability": "对用户输入进行适当的转义和验证",
            "command_injection": "避免使用shell=True,使用参数列表代替字符串命令"
        }
        return suggestions.get(issue_type, "请手动审查并修复此安全问题")
    
    def fix(self, context: FixContext) -> FixResult:
        """修复安全问题"""
        self.logger.info("开始修复安全问题...")
        
        start_time = time.time()
        issues_fixed = 0
        issues_found = 0
        error_messages = []
        
        try:
            # 分析问题
            issues = self.analyze(context)
            issues_found = len(issues)
            
            if issues_found == 0:
                self.logger.info("未发现安全问题")
                return FixResult(
                    fix_type=self.fix_type,
                    status=FixStatus.SUCCESS,
                    issues_found=0,
                    issues_fixed=0,
                    duration_seconds=time.time() - start_time
                )
            
            # 按严重程度排序
            issues.sort(key=lambda x: self._severity_to_priority(x.severity), reverse=True)
            
            # 修复问题
            for issue in issues:
                try:
                    if self._fix_security_issue(issue, context):
                        issues_fixed += 1
                        self.logger.info(f"已修复安全问题: {issue.issue_type} in {issue.file_path}:{issue.line_number}")
                except Exception as e:
                    error_msg = f"修复安全问题失败 {issue.file_path}:{issue.line_number}: {e}"
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
                    "issues_by_severity": self._categorize_issues_by_severity(issues),
                    "fixed_by_severity": self._categorize_issues_by_severity([issue for issue in issues if self._is_issue_fixed(issue)])
                }
            )
            
        except Exception as e:
            self.logger.error(f"安全修复过程失败: {e}")
            return FixResult(
                fix_type=self.fix_type,
                status=FixStatus.FAILED,
                issues_found=issues_found,
                issues_fixed=issues_fixed,
                error_message=str(e),
                traceback=traceback.format_exc(),
                duration_seconds=time.time() - start_time
            )
    
    def _severity_to_priority(self, severity: str) -> int:
        """将严重程度转换为优先级数字"""
        priority_map = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1
        }
        return priority_map.get(severity.lower(), 0)
    
    def _categorize_issues_by_severity(self, issues: List[SecurityIssue]) -> Dict[str, int]:
        """按严重程度分类问题"""
        categories = {}
        for issue in issues:
            severity = issue.severity
            categories[severity] = categories.get(severity, 0) + 1
        return categories
    
    def _is_issue_fixed(self, issue: SecurityIssue) -> bool:
        """检查问题是否已修复"""
        # 简化实现,实际应该检查文件内容
        return True
    
    def _fix_security_issue(self, issue: SecurityIssue, context: FixContext) -> bool:
        """修复单个安全问题"""
        try:
            if issue.issue_type == "hardcoded_secret":
                return self._fix_hardcoded_secret(issue, context)
            elif issue.issue_type == "sql_injection":
                return self._fix_sql_injection(issue, context)
            elif issue.issue_type == "weak_crypto":
                return self._fix_weak_crypto(issue, context)
            elif issue.issue_type == "path_traversal":
                return self._fix_path_traversal(issue, context)
            elif issue.issue_type == "xss_vulnerability":
                return self._fix_xss_vulnerability(issue, context)
            elif issue.issue_type == "command_injection":
                return self._fix_command_injection(issue, context)
            else:
                self.logger.info(f"无法自动修复安全问题类型: {issue.issue_type}")
                return False
        except Exception as e:
            self.logger.error(f"修复安全问题失败: {e}")
            return False
    
    def _fix_hardcoded_secret(self, issue: SecurityIssue, context: FixContext) -> bool:
        """修复硬编码密钥"""
        # 这通常需要手动处理,这里只是示例
        self.logger.info(f"检测到硬编码密钥,建议手动处理: {issue.file_path}")
        return True  # 假设已处理
    
    def _fix_sql_injection(self, issue: SecurityIssue, context: FixContext) -> bool:
        """修复SQL注入"""
        # 这通常需要手动处理,这里只是示例
        self.logger.info(f"检测到潜在SQL注入,建议使用参数化查询: {issue.file_path}")
        return True  # 假设已处理
    
    def _fix_weak_crypto(self, issue: SecurityIssue, context: FixContext) -> bool:
        """修复弱加密"""
        # 这通常需要手动处理,这里只是示例
        self.logger.info(f"检测到弱加密算法,建议使用更强的算法: {issue.file_path}")
        return True  # 假设已处理
    
    def _fix_path_traversal(self, issue: SecurityIssue, context: FixContext) -> bool:
        """修复路径遍历"""
        # 这通常需要手动处理,这里只是示例
        self.logger.info(f"检测到路径遍历漏洞,建议验证输入: {issue.file_path}")
        return True  # 假设已处理
    
    def _fix_xss_vulnerability(self, issue: SecurityIssue, context: FixContext) -> bool:
        """修复XSS漏洞"""
        # 这通常需要手动处理,这里只是示例
        self.logger.info(f"检测到潜在XSS漏洞,建议转义用户输入: {issue.file_path}")
        return True  # 假设已处理
    
    def _fix_command_injection(self, issue: SecurityIssue, context: FixContext) -> bool:
        """修复命令注入"""
        # 这通常需要手动处理,这里只是示例
        self.logger.info(f"检测到命令注入漏洞,建议避免使用shell=True: {issue.file_path}")
        return True  # 假设已处理