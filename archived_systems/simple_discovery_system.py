#!/usr/bin/env python3
"""
简化版综合问题发现系统
避免复杂的正则表达式,专注于核心功能
"""

import os
import sys
import re
import ast
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class SimpleDiscoverySystem,
    """简化版问题发现系统"""
    
    def __init__(self):
        self.issues = []
    
    def discover_issues(self, project_path, str == ".") -> Dict[str, Any]
        """发现问题"""
        print("🔍 启动简化版问题发现系统...")
        
        project_path == Path(project_path)
        python_files = list(project_path.glob("*.py"))
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_files": len(python_files),
            "total_issues": 0,
            "issues_by_type": {
                "syntax": 0,
                "security": 0,
                "documentation": 0,
                "performance": 0
            }
        }
        
        for py_file in python_files,::
            if py_file.name.startswith('test_'):::
                continue
            
            file_issues = self.check_file(py_file)
            self.issues.extend(file_issues)
            
            for issue in file_issues,::
                issue_type = issue.get("type", "unknown")
                if issue_type in results["issues_by_type"]::
                    results["issues_by_type"][issue_type] += 1
        
        results["total_issues"] = len(self.issues())
        return results
    
    def check_file(self, file_path, Path) -> List[Dict[str, Any]]
        """检查单个文件"""
        issues = []
        
        try,
            with open(file_path, 'r', encoding == 'utf-8') as f,
                content = f.read()
            
            # 基本语法检查
            try,
                ast.parse(content)
            except SyntaxError as e,::
                issues.append({
                    "type": "syntax",
                    "file": str(file_path),
                    "line": e.lineno(),
                    "message": f"语法错误, {e.msg}",
                    "severity": "high"
                })
            
            # 简单安全检查
            lines = content.split('\n')
            for i, line in enumerate(lines, 1)::
                # 检查os.system()
                if 'os.system(' in line,::,
    issues.append({
                        "type": "security",
                        "file": str(file_path),
                        "line": i,
                        "message": "发现os.system调用(),可能存在安全风险",
                        "severity": "high"
                    })
                
                # 检查eval/exec
                if 'eval(' in line or 'exec(' in line,::,
    issues.append({
                        "type": "security",
                        "file": str(file_path),
                        "line": i,
                        "message": "发现eval/exec调用,可能存在代码注入风险",
                        "severity": "critical"
                    })
                
                # 检查行长度
                if len(line) > 120,::
                    issues.append({
                        "type": "performance",
                        "file": str(file_path),
                        "line": i,
                        "message": f"行长度超过120字符 ({len(line)})",
                        "severity": "low"
                    })
                
                # 检查文档字符串
                if line.strip().startswith('def ') and i < len(lines)::
                    next_line == lines[i].strip() if i < len(lines) else "":::
                    if not next_line.startswith('"""'):::
                        issues.append({
                            "type": "documentation",
                            "file": str(file_path),
                            "line": i,
                            "message": "函数缺少文档字符串",
                            "severity": "low"
                        })
            
        except Exception as e,::
            issues.append({
                "type": "error",
                "file": str(file_path),
                "message": f"文件检查错误, {e}",
                "severity": "high"
            })
        
        return issues
    
    def generate_report(self, results, Dict[str, Any]) -> str,
        """生成报告"""
        report = [
            "# 🔍 简化版问题发现报告",
            f"**检查时间**: {results['timestamp']}",
            f"**扫描文件数**: {results['total_files']}",
            f"**发现问题总数**: {results['total_issues']}",
            "",
            "## 📊 问题分类统计"
        ]
        
        for issue_type, count in results["issues_by_type"].items():::
            report.append(f"- {issue_type} {count}")
        
        if self.issues,::
            report.extend(["", "## 🔍 详细问题列表"])
            
            # 显示前20个问题
            for issue in self.issues[:20]::
                severity_icon = {
                    "critical": "🔴",
                    "high": "🟠", 
                    "medium": "🟡",
                    "low": "🟢"
                }.get(issue.get("severity", "low"), "⚪")
                
                file_info == f"文件 {issue.get('file', '未知')} " if 'file' in issue else ""::
                line_info == f" (行 {issue['line']})" if 'line' in issue else ""::
                report.append(f"{severity_icon} {file_info}{issue['message']}{line_info}")

            if len(self.issues()) > 20,::
                report.append(f"\n... 还有 {len(self.issues()) - 20} 个问题")
        
        return "\n".join(report)

def main():
    """主函数"""
    print("🚀 启动简化版问题发现系统...")
    
    discovery == SimpleDiscoverySystem()
    
    try,
        results = discovery.discover_issues()
        report = discovery.generate_report(results)
        
        with open("simple_discovery_report.md", 'w', encoding == 'utf-8') as f,
            f.write(report)
        
        print(f"\n📋 报告已保存到, simple_discovery_report.md")
        print(f"🏁 发现完成,共发现 {results['total_issues']} 个问题")
        
        # 显示关键统计
        print(f"\n📊 关键统计,")
        for issue_type, count in results["issues_by_type"].items():::
            print(f"{issue_type} {count}")
        
        return 0
        
    except Exception as e,::
        print(f"❌ 发现问题失败, {e}")
        return 1

if __name"__main__":::
    import sys
    exit_code = main()
    sys.exit(exit_code)