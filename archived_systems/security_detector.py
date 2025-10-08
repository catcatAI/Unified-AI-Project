#!/usr/bin/env python3
"""
安全检测器
检测项目中的安全漏洞和风险
"""

import re
import sys
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

class SecurityDetector:
    """安全漏洞检测器"""
    
    def __init__(self):
        self.vulnerabilities = []
        self.security_issues = []
    
    def scan_security_issues(self, file_path: Path) -> List[Dict[str, Any]]:
        """扫描安全问题"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查各种安全问题
            issues.extend(self.check_hardcoded_secrets(content, file_path))
            issues.extend(self.check_sql_injection_risks(content, file_path))
            issues.extend(self.check_xss_vulnerabilities(content, file_path))
            issues.extend(self.check_code_injection(content, file_path))
            issues.extend(self.check_file_inclusion(content, file_path))
            issues.extend(self.check_weak_crypto(content, file_path))
            issues.extend(self.check_access_control(content, file_path))
            
        except Exception as e:
            issues.append({
                "type": "scan_error",
                "file": str(file_path),
                "message": f"安全扫描失败: {e}",
                "severity": "high"
            })
        
        return issues
    
    def check_hardcoded_secrets(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """检查硬编码敏感信息"""
        issues = []
        
        # 常见的敏感信息模式
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "硬编码密码", "high"),
            (r'passwd\s*=\s*["\'][^"\']+["\']', "硬编码密码", "high"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "硬编码API密钥", "high"),
            (r'apikey\s*=\s*["\'][^"\']+["\']', "硬编码API密钥", "high"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "硬编码密钥", "high"),
            (r'token\s*=\s*["\'][^"\']+["\']', "硬编码令牌", "high"),
            (r'private_key\s*=\s*["\'][^"\']+["\']', "硬编码私钥", "critical"),
            (r'database_url\s*=\s*["\'][^"\']+["\']', "硬编码数据库URL", "high"),
            (r'connection_string\s*=\s*["\'][^"\']+["\']', "硬编码连接字符串", "high")
        ]
        
        for pattern, description, severity in secret_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # 检查是否为示例或测试数据
                value = match.group(0)
                if not self.is_test_data(value):
                    issues.append({
                        "type": "hardcoded_secret",
                        "file": str(file_path),
                        "line": self.get_line_number(content, match.start()),
                        "message": f"发现{description}: {value[:30]}...",
                        "severity": severity
                    })
        
        return issues
    
    def check_sql_injection_risks(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """检查SQL注入风险"""
        issues = []
        
        # SQL注入风险模式
        sql_injection_patterns = [
            (r'execute\s*\(\s*["\'].*%s.*["\'].*%', "字符串格式化SQL", "high"),
            (r'execute\s*\(\s*["\'].*\+.*["\'].*\+', "字符串拼接SQL", "high"),
            (r'query\s*=\s*["\'].*%.*["\']', "格式化查询字符串", "medium"),
            (r'sql\s*=\s*["\'].*\+.*["\']', "拼接SQL字符串", "medium")
        ]
        
        for pattern, description, severity in sql_injection_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                issues.append({
                    "type": "sql_injection_risk",
                    "file": str(file_path),
                    "line": self.get_line_number(content, match.start()),
                    "message": f"{description}可能导致SQL注入",
                    "severity": severity
                })
        
        return issues
    
    def check_xss_vulnerabilities(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """检查XSS漏洞"""
        issues = []
        
        # XSS漏洞模式
        xss_patterns = [
            (r'innerHTML\s*=\s*', "innerHTML赋值", "high"),
            (r'document\.write\s*\(', "document.write", "high"),
            (r'eval\s*\(', "eval函数", "critical"),
            (r'Function\s*\(', "Function构造函数", "high"),
            (r'setTimeout\s*\(\s*["\']', "字符串setTimeout", "medium"),
            (r'setInterval\s*\(\s*["\']', "字符串setInterval", "medium")
        ]
        
        for pattern, description, severity in xss_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                issues.append({
                    "type": "xss_vulnerability",
                    "file": str(file_path),
                    "line": self.get_line_number(content, match.start()),
                    "message": f"{description}可能导致XSS攻击",
                    "severity": severity
                })
        
        return issues
    
    def check_code_injection(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """检查代码注入风险"""
        issues = []
        
        # 代码注入风险模式
        injection_patterns = [
            (r'exec\s*\(', "exec函数", "critical"),
            (r'system\s*\(', "system函数", "critical"),
            (r'subprocess\.call\s*\(', "subprocess.call", "high"),
            (r'os\.system\s*\(', "os.system", "high"),
            (r'pickle\.loads\s*\(', "pickle.loads", "high"),
            (r'yaml\.load\s*\(', "yaml.load", "medium")
        ]
        
        for pattern, description, severity in injection_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                issues.append({
                    "type": "code_injection_risk",
                    "file": str(file_path),
                    "line": self.get_line_number(content, match.start()),
                    "message": f"{description}可能导致代码注入",
                    "severity": severity
                })
        
        return issues
    
    def check_file_inclusion(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """检查文件包含漏洞"""
        issues = []
        
        # 文件包含风险模式
        file_patterns = [
            (r'open\s*\(\s*[^,)]*\+', "动态文件打开", "medium"),
            (r'file\s*=\s*[^,)]*\+', "动态文件路径", "medium"),
            (r'path\s*=\s*[^,)]*\+', "动态路径拼接", "medium")
        ]
        
        for pattern, description, severity in file_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                issues.append({
                    "type": "file_inclusion_risk",
                    "file": str(file_path),
                    "line": self.get_line_number(content, match.start()),
                    "message": f"{description}可能导致路径遍历攻击",
                    "severity": severity
                })
        
        return issues
    
    def check_weak_crypto(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """检查弱加密算法"""
        issues = []
        
        # 弱加密算法模式
        crypto_patterns = [
            (r'md5\s*\(', "MD5哈希", "medium"),
            (r'sha1\s*\(', "SHA1哈希", "medium"),
            (r'random\.random\s*\(', "弱随机数", "low"),
            (r'random\.randint\s*\(', "弱随机数", "low")
        ]
        
        for pattern, description, severity in crypto_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                issues.append({
                    "type": "weak_crypto",
                    "file": str(file_path),
                    "line": self.get_line_number(content, match.start()),
                    "message": f"{description}不够安全",
                    "severity": severity
                })
        
        return issues
    
    def check_access_control(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """检查访问控制问题"""
        issues = []
        
        # 访问控制问题模式
        access_patterns = [
            (r'chmod\s*\(\s*0o777', "过度权限", "medium"),
            (r'access\s*=\s*["\']public["\']', "公开访问", "low"),
            (r'authenticated\s*=\s*False', "禁用认证", "high"),
            (r'require_auth\s*=\s*False', "禁用认证要求", "high")
        ]
        
        for pattern, description, severity in access_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                issues.append({
                    "type": "access_control_issue",
                    "file": str(file_path),
                    "line": self.get_line_number(content, match.start()),
                    "message": f"{description}可能存在安全风险",
                    "severity": severity
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
    
    def generate_security_report(self, all_issues: List[Dict[str, Any]]) -> str:
        """生成安全检查报告"""
        report = []
        
        report.append("# 🔒 安全检查报告")
        report.append(f"\n**检查时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**总问题数**: {len(all_issues)}")
        
        if all_issues:
            # 按严重程度分组
            critical_issues = [issue for issue in all_issues if issue['severity'] == 'critical']
            high_issues = [issue for issue in all_issues if issue['severity'] == 'high']
            medium_issues = [issue for issue in all_issues if issue['severity'] == 'medium']
            low_issues = [issue for issue in all_issues if issue['severity'] == 'low']
            
            if critical_issues:
                report.append(f"\n### 🔴 严重问题 ({len(critical_issues)})")
                for issue in critical_issues:
                    file_info = f"文件 {issue.get('file', '未知')}: " if 'file' in issue else ""
                    line_info = f" (行 {issue['line']})" if 'line' in issue else ""
                    report.append(f"- {file_info}{issue['message']}{line_info}")
            
            if high_issues:
                report.append(f"\n### 🟠 高危问题 ({len(high_issues)})")
                for issue in high_issues:
                    file_info = f"文件 {issue.get('file', '未知')}: " if 'file' in issue else ""
                    line_info = f" (行 {issue['line']})" if 'line' in issue else ""
                    report.append(f"- {file_info}{issue['message']}{line_info}")
            
            if medium_issues:
                report.append(f"\n### 🟡 中危问题 ({len(medium_issues)})")
                for issue in medium_issues:
                    file_info = f"文件 {issue.get('file', '未知')}: " if 'file' in issue else ""
                    line_info = f" (行 {issue['line']})" if 'line' in issue else ""
                    report.append(f"- {file_info}{issue['message']}{line_info}")
            
            if low_issues:
                report.append(f"\n### 🟢 低危问题 ({len(low_issues)})")
                for issue in low_issues:
                    file_info = f"文件 {issue.get('file', '未知')}: " if 'file' in issue else ""
                    line_info = f" (行 {issue['line']})" if 'line' in issue else ""
                    report.append(f"- {file_info}{issue['message']}{line_info}")
        else:
            report.append("\n✅ 未发现安全问题")
        
        report.append(f"\n## 💡 安全建议")
        report.append("- 使用环境变量存储敏感信息")
        report.append("- 使用参数化查询防止SQL注入")
        report.append("- 对用户输入进行验证和清理")
        report.append("- 使用安全的加密算法")
        report.append("- 实施适当的访问控制")
        
        return "\n".join(report)

def main():
    """主函数"""
    print("🔒 启动安全检查器...")
    
    detector = SecurityDetector()
    
    # 扫描Python文件
    python_files = list(Path('.').glob('*.py'))
    all_issues = []
    
    for py_file in python_files:
        if py_file.name.startswith('test_'):
            continue
        
        print(f"🔍 扫描文件: {py_file.name}")
        issues = detector.scan_security_issues(py_file)
        all_issues.extend(issues)
    
    # 生成报告
    report = detector.generate_security_report(all_issues)
    
    # 保存报告
    report_file = "security_check_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📋 安全检查报告已保存到: {report_file}")
    
    # 显示统计
    critical_count = len([issue for issue in all_issues if issue['severity'] == 'critical'])
    high_count = len([issue for issue in all_issues if issue['severity'] == 'high'])
    medium_count = len([issue for issue in all_issues if issue['severity'] == 'medium'])
    low_count = len([issue for issue in all_issues if issue['severity'] == 'low'])
    
    print(f"🏁 扫描完成:")
    print(f"🔴 严重问题: {critical_count}")
    print(f"🟠 高危问题: {high_count}")
    print(f"🟡 中危问题: {medium_count}")
    print(f"🟢 低危问题: {low_count}")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)