#!/usr/bin/env python3
"""
综合问题发现系统
整合所有检测工具，发现项目中的各种问题
"""

import os
import sys
import re
import ast
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class ComprehensiveDiscoverySystem:
    """综合问题发现系统"""
    
    def __init__(self):
        self.discovered_issues = []
        self.issue_categories = {
            "syntax": [],
            "logic": [],
            "security": [],
            "performance": [],
            "documentation": [],
            "architecture": []
        }
    
    def discover_all_issues(self, project_path: str = ".") -> Dict[str, Any]:
        """发现所有类型的问题"""
        print("🔍 启动综合问题发现系统...")
        
        project_path = Path(project_path)
        
        discovery_results = {
            "timestamp": datetime.now().isoformat(),
            "project_path": str(project_path),
            "total_files_scanned": 0,
            "issues_by_category": {},
            "total_issues": 0,
            "severity_breakdown": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
        
        # 扫描Python文件
        python_files = list(project_path.glob("*.py"))
        discovery_results["total_files_scanned"] = len(python_files)
        
        for py_file in python_files:
            if py_file.name.startswith('test_'):
                continue
            
            print(f"📄 扫描文件: {py_file.name}")
            
            # 语法问题发现
            syntax_issues = self.discover_syntax_issues(py_file)
            self.issue_categories["syntax"].extend(syntax_issues)
            
            # 逻辑问题发现
            logic_issues = self.discover_logic_issues(py_file)
            self.issue_categories["logic"].extend(logic_issues)
            
            # 安全问题发现
            security_issues = self.discover_security_issues(py_file)
            self.issue_categories["security"].extend(security_issues)
            
            # 性能问题发现
            performance_issues = self.discover_performance_issues(py_file)
            self.issue_categories["performance"].extend(performance_issues)
            
            # 文档问题发现
            documentation_issues = self.discover_documentation_issues(py_file)
            self.issue_categories["documentation"].extend(documentation_issues)
        
        # 架构问题发现
        architecture_issues = self.discover_architecture_issues(project_path)
        self.issue_categories["architecture"].extend(architecture_issues)
        
        # 统计结果
        discovery_results["issues_by_category"] = {
            category: len(issues) for category, issues in self.issue_categories.items()
        }
        
        # 统计所有问题
        all_issues = []
        for issues in self.issue_categories.values():
            all_issues.extend(issues)
        
        discovery_results["total_issues"] = len(all_issues)
        
        # 按严重程度统计
        for issue in all_issues:
            severity = issue.get("severity", "low")
            if severity in discovery_results["severity_breakdown"]:
                discovery_results["severity_breakdown"][severity] += 1
        
        return discovery_results
    
    def discover_syntax_issues(self, file_path: Path) -> List[Dict[str, Any]]:
        """发现语法问题"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 基本语法检查
            try:
                ast.parse(content)
            except SyntaxError as e:
                issues.append({
                    "type": "syntax_error",
                    "file": str(file_path),
                    "line": e.lineno,
                    "column": e.offset,
                    "message": f"语法错误: {e.msg}",
                    "severity": "high"
                })
            
            # 检查常见的语法问题
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # 检查行长度
                if len(line) > 120:
                    issues.append({
                        "type": "line_too_long",
                        "file": str(file_path),
                        "line": i,
                        "message": f"行长度超过120字符 ({len(line)})",
                        "severity": "low"
                    })
                
                # 检查缩进
                if line.strip() and not line.startswith('#'):
                    leading_spaces = len(line) - len(line.lstrip())
                    if leading_spaces % 4 != 0 and leading_spaces > 0:
                        issues.append({
                            "type": "indentation_error",
                            "file": str(file_path),
                            "line": i,
                            "message": "缩进不是4的倍数",
                            "severity": "low"
                        })
                
                # 检查未使用的导入
                if line.strip().startswith(('import ', 'from ')):
                    import_name = re.search(r'import\s+(\w+)', line)
                    if import_name:
                        imported_module = import_name.group(1)
                        # 简单检查是否在文件后面使用
                        remaining_content = '\n'.join(lines[i:])
                        if not re.search(r'\b' + imported_module + r'\b', remaining_content):
                            issues.append({
                                "type": "unused_import",
                                "file": str(file_path),
                                "line": i,
                                "message": f"可能未使用的导入: {imported_module}",
                                "severity": "low"
                            })
            
        except Exception as e:
            issues.append({
                "type": "file_read_error",
                "file": str(file_path),
                "message": f"文件读取错误: {e}",
                "severity": "high"
            })
        
        return issues
    
    def discover_logic_issues(self, file_path: Path) -> List[Dict[str, Any]]:
        """发现逻辑问题"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                
                # 检查空循环
                if re.search(r'for\s+\w+\s+in\s+.+:\s*$', stripped):
                    issues.append({
                        "type": "empty_loop",
                        "file": str(file_path),
                        "line": i,
                        "message": "可能的空循环",
                        "severity": "medium"
                    })
                
                # 检查空条件
                if re.search(r'if\s+.+:\s*$', stripped):
                    issues.append({
                        "type": "empty_if",
                        "file": str(file_path),
                        "line": i,
                        "message": "可能的空if语句",
                        "severity": "medium"
                    })
                
                # 检查硬编码值
                if re.search(r'if\s+\w+\s*==\s*["\'][^"\']*["\']', stripped):
                    issues.append({
                        "type": "hardcoded_value",
                        "file": str(file_path),
                        "line": i,
                        "message": "可能的硬编码值",
                        "severity": "low"
                    })
                
                # 检查未使用的变量
                var_assign = re.search(r'(\w+)\s*=\s*.+', stripped)
                if var_assign:
                    var_name = var_assign.group(1)
                    # 检查变量是否在后续被使用
                    remaining_content = '\n'.join(lines[i:])
                    if not re.search(r'\b' + var_name + r'\b', remaining_content):
                        issues.append({
                            "type": "unused_variable",
                            "file": str(file_path),
                            "line": i,
                            "message": f"变量 '{var_name}' 可能未被使用",
                            "severity": "low"
                        })
            
        except Exception as e:
            issues.append({
                "type": "logic_check_error",
                "file": str(file_path),
                "message": f"逻辑检查错误: {e}",
                "severity": "medium"
            })
        
        return issues
    
    def discover_security_issues(self, file_path: Path) -> List[Dict[str, Any]]:
        """发现安全问题"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查硬编码敏感信息
            secret_patterns = [
                (r'password\s*=\s*["\'][^"\']+["\']', "硬编码密码", "high"),
                (r'api_key\s*=\s*["\'][^"\']+["\']', "硬编码API密钥", "high"),
                (r'secret\s*=\s*["\'][^"\']+["\']', "硬编码密钥", "high"),
                (r'token\s*=\s*["\'][^"\']+["\']', "硬编码令牌", "high")
            ]
            
            for pattern, description, severity in secret_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    value = match.group(0)
                    if not self.is_test_data(value):
                        issues.append({
                            "type": "hardcoded_secret",
                            "file": str(file_path),
                            "line": self.get_line_number(content, match.start()),
                            "message": f"发现{description}",
                            "severity": severity
                        })
            
            # 检查SQL注入风险
            sql_patterns = [
                (r'execute\s*\(\s*["\'].*%.*["\']', "格式化SQL", "high"),
                (r'execute\s*\(\s*["\'].*\+.*["\']', "拼接SQL", "high")
            ]
            
            for pattern, description, severity in sql_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    issues.append({
                        "type": "sql_injection_risk",
                        "file": str(file_path),
                        "message": f"{description}可能导致SQL注入",
                        "severity": severity
                    })
            
            # 检查代码注入风险
            injection_patterns = [
                (r'eval\s*\(', "eval函数", "critical"),
                (r'exec\s*\(', "exec函数", "critical"),
                (r'system\s*\(', "system函数", "high")
            ]
            
            for pattern, description, severity in injection_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    issues.append({
                        "type": "code_injection_risk",
                        "file": str(file_path),
                        "message": f"{description}可能导致代码注入",
                        "severity": severity
                    })
            
        except Exception as e:
            issues.append({
                "type": "security_check_error",
                "file": str(file_path),
                "message": f"安全检查错误: {e}",
                "severity": "medium"
            })
        
        return issues
    
    def discover_performance_issues(self, file_path: Path) -> List[Dict[str, Any]]:
        """发现性能问题"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查文件大小
            if len(content) > 10000:  # 10KB
                issues.append({
                    "type": "large_file",
                    "file": str(file_path),
                    "message": f"文件过大 ({len(content)} 字符)，可能影响加载性能",
                    "severity": "low"
                })
            
            # 检查复杂循环
            if content.count('for ') > 10:
                issues.append({
                    "type": "complex_loops",
                    "file": str(file_path),
                    "message": f"文件中循环过多 ({content.count('for ')} 个)，可能影响性能",
                    "severity": "low"
                })
            
            # 检查深层嵌套
            nested_ifs = re.findall(r'if.*:\s*\n.*if.*:', content)
            if len(nested_ifs) > 5:
                issues.append({
                    "type": "deep_nesting",
                    "file": str(file_path),
                    "message": f"发现深层嵌套 ({len(nested_ifs)} 处)，可能影响可读性和性能",
                    "severity": "low"
                })
            
        except Exception as e:
            issues.append({
                "type": "performance_check_error",
                "file": str(file_path),
                "message": f"性能检查错误: {e}",
                "severity": "low"
            })
        
        return issues
    
    def discover_documentation_issues(self, file_path: Path) -> List[Dict[str, Any]]:
        """发现文档问题"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查模块文档字符串
            if not content.strip().startswith('"""'):
                issues.append({
                    "type": "missing_module_docstring",
                    "file": str(file_path),
                    "message": "缺少模块文档字符串",
                    "severity": "low"
                })
            
            # 检查函数文档
            functions = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
            docstring_functions = re.findall(r'def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\):\s*\n\s*"""', content)
            
            if len(functions) > len(docstring_functions):
                issues.append({
                    "type": "missing_function_docstrings",
                    "file": str(file_path),
                    "message": f"{len(functions) - len(docstring_functions)} 个函数缺少文档字符串",
                    "severity": "low"
                })
            
            # 检查类文档
            classes = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
            docstring_classes = re.findall(r'class\s+[a-zA-Z_][a-zA-Z0-9_]*[^(]*:\s*\n\s*"""', content)
            
            if len(classes) > len(docstring_classes):
                issues.append({
                    "type": "missing_class_docstrings",
                    "file": str(file_path),
                    "message": f"{len(classes) - len(docstring_classes)} 个类缺少文档字符串",
                    "severity": "low"
                })
            
        except Exception as e:
            issues.append({
                "type": "documentation_check_error",
                "file": str(file_path),
                "message": f"文档检查错误: {e}",
                "severity": "low"
            })
        
        return issues
    
    def discover_architecture_issues(self, project_path: Path) -> List[Dict[str, Any]]:
        """发现架构问题"""
        issues = []
        
        # 检查关键文件
        critical_files = [
            "unified_agi_ecosystem.py",
            "comprehensive_discovery_system.py",
            "enhanced_unified_fix_system.py",
            "comprehensive_test_system.py"
        ]
        
        for file_name in critical_files:
            file_path = project_path / file_name
            if not file_path.exists():
                issues.append({
                    "type": "missing_critical_file",
                    "file": file_name,
                    "message": f"关键文件缺失: {file_name}",
                    "severity": "high"
                })
        
        # 检查关键目录
        key_directories = ["apps", "packages", "docs", "tests", "tools"]
        for directory in key_directories:
            dir_path = project_path / directory
            if not dir_path.exists() or not dir_path.is_dir():
                issues.append({
                    "type": "missing_key_directory",
                    "directory": directory,
                    "message": f"关键目录缺失: {directory}",
                    "severity": "medium"
                })
        
        return issues
    
    def is_test_data(self, value: str) -> bool:
        """判断是否为测试数据"""
        test_indicators = [
            'test', 'example', 'sample', 'demo', 'dummy',
            '123', 'abc', 'xxx', 'placeholder'
        ]
        
        value_lower = value.lower()
        return any(indicator in value_lower for indicator in test_indicators)
    
    def get_line_number(self, content: str, position: int) -> int:
        """获取位置对应的行号"""
        return content[:position].count('\n') + 1
    
    def generate_discovery_report(self, results: Dict[str, Any]) -> str:
        """生成发现问题报告"""
        report = []
        
        report.append("# 🔍 综合问题发现报告")
        report.append(f"\n**发现时间**: {results['timestamp']}")
        report.append(f"**项目路径**: {results['project_path']}")
        report.append(f"**扫描文件数**: {results['total_files_scanned']}")
        report.append(f"**发现问题总数**: {results['total_issues']}")
        
        # 严重程度统计
        severity_stats = results["severity_breakdown"]
        report.append(f"\n## 📊 问题严重程度分布")
        report.append(f"- 🔴 严重问题: {severity_stats['critical']}")
        report.append(f"- 🟠 高危问题: {severity_stats['high']}")
        report.append(f"- 🟡 中危问题: {severity_stats['medium']}")
        report.append(f"- 🟢 低危问题: {severity_stats['low']}")
        
        # 分类统计
        report.append(f"\n## 📋 问题分类统计")
        for category, count in results["issues_by_category"].items():
            report.append(f"- {category}: {count}")
        
        # 详细问题列表
        if results["total_issues"] > 0:
            report.append(f"\n## 🔍 详细问题列表")
            
            # 按严重程度排序显示
            all_issues = []
            for issues in self.issue_categories.values():
                all_issues.extend(issues)
            
            # 按严重程度排序
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 4))
            
            for issue in all_issues[:20]:  # 只显示前20个问题
                severity_icon = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(issue.get("severity", "low"), "⚪")
                
                file_info = f"文件 {issue.get('file', '未知')}: " if 'file' in issue else ""
                line_info = f" (行 {issue['line']})" if 'line' in issue else ""
                
                report.append(f"{severity_icon} {file_info}{issue['message']}{line_info}")
            
            if len(all_issues) > 20:
                report.append(f"\n... 还有 {len(all_issues) - 20} 个问题")
        
        return "\n".join(report)

def main():
    """主函数"""
    print("🚀 启动综合问题发现系统...")
    
    discovery = ComprehensiveDiscoverySystem()
    
    try:
        # 发现问题
        results = discovery.discover_all_issues()
        
        # 生成报告
        report = discovery.generate_discovery_report(results)
        
        # 保存报告
        report_file = "comprehensive_discovery_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📋 发现问题报告已保存到: {report_file}")
        print(f"🏁 发现完成，共发现 {results['total_issues']} 个问题")
        
        # 显示关键统计
        print(f"\n📊 关键统计:")
        for category, count in results["issues_by_category"].items():
            print(f"{category}: {count}")
        
    except Exception as e:
        print(f"❌ 发现问题失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)