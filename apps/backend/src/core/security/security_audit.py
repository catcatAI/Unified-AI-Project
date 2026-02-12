# =============================================================================
# ANGELA-MATRIX: L6[执行层] 全层级 [A] L2+
# =============================================================================
#
# 职责: 安全审计模块，定期安全检查和漏洞扫描
# 维度: 涉及所有维度
# 安全: 使用 Key A (后端控制)
# 成熟度: L2+ 等级
#
# =============================================================================

"""安全审计模块 - 定期安全检查和漏洞扫描
"""

import logging
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("security_audit")

class SecurityAudit:
    """安全审计器"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "vulnerabilities": [],
            "recommendations": [],
            "score": 0
        }

        # 安全检查规则
        self.security_rules = {
            "hardcoded_secrets": {
                "patterns": [
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r'api_key\s*=\s*["\'][^"\']+["\']',
                    r'secret_key\s*=\s*["\'][^"\']+["\']',
                    r'token\s*=\s*["\'][^"\']+["\']',
                    r'AKIA[0-9A-Z]{16}',  # AWS Access Key
                    r'[a-zA-Z0-9]{40}',  # Possible API key
                ],
                "severity": "high",
                "description": "硬编码的敏感信息"
            },
            "sql_injection": {
                "patterns": [
                    r'execute\s*\(\s*["\'].*?\+.*?["\']',
                    r'query\s*=\s*["\'].*?%s.*?["\']',
                    r'format.*?=\s*["\'].*?\{.*?\}.*?["\']',
                ],
                "severity": "critical",
                "description": "潜在的SQL注入漏洞"
            },
            "command_injection": {
                "patterns": [
                    r'os\.system\s*\(\s*["\'].*?\+.*?["\']',
                    r'subprocess\.call\s*\(\s*.*shell=True',
                ],
                "severity": "critical",
                "description": "潜在的命令注入漏洞"
            },
            "weak_cryptography": {
                "patterns": [
                    r'md5\s*\(',
                    r'sha1\s*\(',
                ],
                "severity": "medium",
                "description": "弱加密算法"
            }
        }

    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """扫描单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            return {

                'file': file_path,
                'error': str(e),
                'vulnerabilities': []
            }

        vulnerabilities = []

        for rule_name, rule in self.security_rules.items():
            for pattern in rule['patterns']:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    vulnerabilities.append({
                        'type': rule_name,
                        'severity': rule['severity'],
                        'description': rule['description'],
                        'line': content[:match.start()].count('\n') + 1,
                        'column': match.start() - content.rfind('\n', 0, match.start()) - 1,
                        'code': match.group(0)
                    })

        return {
            'file': file_path,
            'vulnerabilities': vulnerabilities
        }

    def scan_directory(self, directory: Optional[str] = None, file_pattern: str = "*.py") -> Dict[str, Any]:
        """扫描目录"""
        target_dir = Path(directory) if directory else self.project_root
        all_vulnerabilities = []
        scanned_files = []

        for file_path in target_dir.rglob(file_pattern):
            if file_path.is_file():
                result = self.scan_file(str(file_path))
                if result.get('vulnerabilities'):
                    all_vulnerabilities.extend(result['vulnerabilities'])
                scanned_files.append(str(file_path))

        # 按严重程度分类
        vulnerabilities_by_severity = {
            'critical': [v for v in all_vulnerabilities if v['severity'] == 'critical'],
            'high': [v for v in all_vulnerabilities if v['severity'] == 'high'],
            'medium': [v for v in all_vulnerabilities if v['severity'] == 'medium'],
            'low': [v for v in all_vulnerabilities if v['severity'] == 'low']
        }

        # 计算安全分数
        score = self._calculate_security_score(vulnerabilities_by_severity)

        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "vulnerabilities": vulnerabilities_by_severity,
            "total_vulnerabilities": len(all_vulnerabilities),
            "scanned_files": len(scanned_files),
            "score": score,
            "recommendations": self._generate_recommendations(vulnerabilities_by_severity)
        }

        return self.audit_results

    def _calculate_security_score(self, vulnerabilities_by_severity: Dict[str, List[Dict[str, Any]]]) -> int:
        """计算安全分数"""
        critical = len(vulnerabilities_by_severity.get('critical', []))
        high = len(vulnerabilities_by_severity.get('high', []))
        medium = len(vulnerabilities_by_severity.get('medium', []))

        # 基础分 100
        score = 100
        score -= critical * 20  # 每个关键漏洞扣 20 分
        score -= high * 10      # 每个高危漏洞扣 10 分
        score -= medium * 5     # 每个中危漏洞扣 5 分

        return max(0, score)

    def _generate_recommendations(self, vulnerabilities_by_severity: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """生成安全建议"""
        recommendations = []

        if vulnerabilities_by_severity.get('critical'):
            recommendations.append("立即修复所有关键级别的安全漏洞")

        if vulnerabilities_by_severity.get('high'):
            recommendations.append("优先修复高危级别的安全漏洞")

        if vulnerabilities_by_severity.get('medium'):
            recommendations.append("计划修复中危级别的安全漏洞")

        # 检查常见问题
        for v in vulnerabilities_by_severity.get('critical', []):
            if v['type'] == 'hardcoded_secrets':
                recommendations.append("将所有硬编码的密钥移到环境变量或配置文件")

        return recommendations

    def generate_report(self, output_file: Optional[str] = None):
        """生成安全审计报告"""
        import json

        report = {
            'summary': {
                'score': self.audit_results['score'],
                'total_vulnerabilities': self.audit_results['total_vulnerabilities'],
                'scanned_files': self.audit_results['scanned_files'],
                'timestamp': self.audit_results['timestamp']
            },
            'vulnerabilities_by_severity': {
                k: [{'file': v['file'], 'line': v['line'], 'type': v['type']} for v in vals]
                for k, vals in self.audit_results['vulnerabilities'].items()
            },
            'recommendations': self.audit_results['recommendations']
        }

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

        return report

# 全局实例
_security_audit: Optional[SecurityAudit] = None

def get_security_audit(project_root: Optional[str] = None) -> SecurityAudit:
    """获取全局安全审计实例"""
    global _security_audit
    if _security_audit is None:
        _security_audit = SecurityAudit(project_root)
    return _security_audit