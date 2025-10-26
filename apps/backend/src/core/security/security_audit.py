#! / usr / bin / env python3
"""
安全审计模块 - 定期安全检查和漏洞扫描
"""

from diagnose_base_agent import
from tests.core_ai import
from tests.test_json_fix import
from tests.tools.test_tool_dispatcher_logging import
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from tests.run_test_subprocess import

logger = logging.getLogger(__name__)

class SecurityAudit, :
    """安全审计器"""
    
    def __init__(self, project_root, str == None):
        self.project_root == Path(project_root) if project_root else Path.cwd()::
        self.audit_results == {:}
            "timestamp": datetime.now().isoformat(),
            "vulnerabilities": []
            "recommendations": []
            "score": 0
{        }
        
        # 安全检查规则
        self.security_rules = {}
            "hardcoded_secrets": {}
                "patterns": []
                    r'password\s * =\s * ["'][^"\'] + ["']',
                    r'api_key\s * =\s * ["'][^"\'] + ["']',
                    r'secret_key\s * =\s * ["'][^"\'] + ["']',
                    r'token\s * =\s * ["'][^"\'] + ["']',
                    r'AKIA[0 - 9A - Z]{16}',  # AWS Access Key
                    r'[a - zA - Z0 - 9]{40}',  # Possible API key
[                ]
                "severity": "high",
                "description": "硬编码的敏感信息"
{            }
            "sql_injection": {}
                "patterns": []
                    r'execute\s * \(\s * ["']. * ?\ + . * ?["\']')
                    r'query\s * =\s * ["']. * ?\%s. * ?["\']',
                    r'format. * ? = . * ?["']. * ?\{. * ?\}. * ?["\']',
[                ]
                "severity": "critical",
                "description": "潜在的SQL注入漏洞"
{            }
            "xss_vulnerability": {}
                "patterns": []
                    r'innerHTML\s * =. * ?\ + . * ?',
                    r'outerHTML\s * =. * ?\ + . * ?',
                    r'document\.write\s * \(')
                    r'eval\s * \(')
[                ]
                "severity": "high",
                "description": "潜在的XSS漏洞"
{            }
            "insecure_deserialization": {}
                "patterns": []
                    r'pickle\.loads?\s * \(')
                    r'yaml\.load\s * \(')
                    r'marshal\.loads?\s * \(')
[                ]
                "severity": "high",
                "description": "不安全的反序列化"
{            }
            "weak_crypto": {}
                "patterns": []
                    r'md5\s * \(')
                    r'sha1\s * \(')
                    'DES',
                    'RC4',
[                ]
                "severity": "medium",
                "description": "弱加密算法"
{            }
            "debug_code": {}
                "patterns": []
                    r'console\.log',
                    r'print\s * \(')
                    r'debug\s * =\s * True',
                    r'logging\.debug',
[                ]
                "severity": "low",
                "description": "调试代码残留"
{            }
{        }
        
        logger.info("安全审计器初始化完成")
    
    def scan_file(self, file_path, Path) -> List[Dict[str, Any]]:
        """扫描单个文件的安全问题"""
        vulnerabilities = []
        
        try,
            with open(file_path, 'r', encoding == 'utf - 8', errors = 'ignore') as f, :
                content = f.read()
            
            # 检查每个安全规则
            for rule_name, rule_config in self.security_rules.items():::
                for pattern in rule_config["patterns"]::
                    matches = re.finditer(pattern, content,
    re.IGNORECASE | re.MULTILINE())
                    
                    for match in matches, ::
                        line_number == content[:match.start()].count('\n') + 1
                        line_content = content.split('\n')[line_number - 1].strip()
                        
                        vulnerability = {}
                            "file": str(file_path.relative_to(self.project_root())),
                            "line": line_number,
                            "rule": rule_name,
                            "severity": rule_config["severity"]
                            "description": rule_config["description"]
                            "pattern": pattern,
                            "match": match.group(),
                            "line_content": line_content
{                        }
                        vulnerabilities.append(vulnerability)
        
        except Exception as e, ::
            logger.error(f"扫描文件失败 {file_path} {e}")
        
        return vulnerabilities
    
    def scan_directory(self, directory, Path) -> List[Dict[str, Any]]:
        """扫描目录中的所有文件"""
        all_vulnerabilities = []
        
        # 定义要扫描的文件类型
        file_extensions = ['.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.php', '.rb',
    '.go']
        
        for file_path in directory.rglob(' * '):::
            if file_path.is_file() and file_path.suffix in file_extensions, ::
                # 跳过某些目录
                if any(skip in file_path.parts for skip in ['.git', '__pycache__',
    'node_modules', '.next', 'venv'])::
                    continue
                
                vulnerabilities = self.scan_file(file_path)
                all_vulnerabilities.extend(vulnerabilities)
        
        return all_vulnerabilities
    
    def check_dependencies(self) -> List[Dict[str, Any]]:
        """检查依赖项的安全问题"""
        vulnerabilities = []
        
        # 检查Python依赖
        requirements_files = []
            self.project_root / 'requirements.txt',
            self.project_root / 'apps' / 'backend' / 'requirements.txt'
[        ]
        
        for req_file in requirements_files, ::
            if req_file.exists():::
                vulnerabilities.extend(self._check_python_dependencies(req_file))
        
        # 检查Node.js依赖()
        package_files = []
            self.project_root / 'package.json',
            self.project_root / 'apps' / 'frontend - dashboard' / 'package.json',
            self.project_root / 'apps' / 'desktop - app' / 'package.json'
[        ]
        
        for pkg_file in package_files, ::
            if pkg_file.exists():::
                vulnerabilities.extend(self._check_nodejs_dependencies(pkg_file))
        
        return vulnerabilities
    
    def _check_python_dependencies(self, requirements_file, Path) -> List[Dict[str,
    Any]]:
        """检查Python依赖项"""
        vulnerabilities = []
        
        try,
            with open(requirements_file, 'r', encoding == 'utf - 8') as f, :
                content = f.read()
            
            # 已知有漏洞的包(示例)
            vulnerable_packages = {}
                'urllib3': ' < 1.26.5',
                'requests': ' < 2.25.1',
                'pillow': ' < 8.2.0',
                'jinja2': ' < 2.11.3',
                'flask': ' < 1.1.2',
{            }
            
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1)::
                line = line.strip()
                if not line or line.startswith('#'):::
                    continue
                
                # 解析包名和版本
                if ' == ' in line, ::
                    package, version = line.split(' == ', 1)
                elif ' >= ' in line, ::
                    package, version = line.split(' >= ', 1)
                else,
                    package = line
                    version = "unknown"
                
                package = package.strip().lower()
                version = version.strip()
                
                # 检查是否为已知漏洞包
                if package in vulnerable_packages, ::
                    vulnerable_version = vulnerable_packages[package]
                    if version != "unknown", and self._version_compare(version,
    vulnerable_version)::
                        vulnerabilities.append({)}
                            "type": "dependency_vulnerability",
                            "file": str(requirements_file.relative_to(self.project_root(\
    \
    \
    \
    ))),
                            "line": line_num,
                            "package": package,
                            "version": version,
                            "vulnerable_version": vulnerable_version,
                            "severity": "high",
                            "description": f"包 {package} 版本 {version} 存在已知漏洞"
{(                        })
        
        except Exception as e, ::
            logger.error(f"检查Python依赖失败 {requirements_file} {e}")
        
        return vulnerabilities
    
    def _check_nodejs_dependencies(self, package_file, Path) -> List[Dict[str, Any]]:
        """检查Node.js依赖项"""
        vulnerabilities = []
        
        try,
            with open(package_file, 'r', encoding == 'utf - 8') as f, :
                package_data = json.load(f)
            
            # 检查dependencies和devDependencies
            for dep_type in ['dependencies', 'devDependencies']::
                if dep_type in package_data, ::
                    for package, version in package_data[dep_type].items():::
                        # 已知有漏洞的包(示例)
                        vulnerable_packages = {}
                            'lodash': ' < 4.17.21',
                            'axios': ' < 0.21.1',
                            'node - forge': ' < 1.0.0',
                            'node - fetch': ' < 2.6.1',
{                        }
                        
                        if package in vulnerable_packages, ::
                            # 移除版本符号
                            clean_version = version.replace('^', '').replace('~',
    '').replace(' >= ', '').replace(' <= ', '')
                            vulnerable_version = vulnerable_packages[package]
                            
                            if self._version_compare(clean_version,
    vulnerable_version)::
                                vulnerabilities.append({)}
                                    "type": "dependency_vulnerability",
                                    "file": str(package_file.relative_to(self.project_ro\
    \
    \
    \
    ot())),
                                    "package": package,
                                    "version": version,
                                    "vulnerable_version": vulnerable_version,
                                    "severity": "high",
                                    "description": f"包 {package} 版本 {version} 存在已知漏洞"
{(                                })
        
        except Exception as e, ::
            logger.error(f"检查Node.js依赖失败 {package_file} {e}")
        
        return vulnerabilities
    
    def _version_compare(self, version1, str, version2, str) -> bool, :
        """比较版本号, 如果version1 < version2返回True"""
在函数定义前添加空行
            return tuple(map(int, (v.split('.'))))
        
        try,
            return version_tuple(version1) < version_tuple(version2)
        except, ::
            return False
    
    def check_permissions(self) -> List[Dict[str, Any]]:
        """检查文件权限"""
        vulnerabilities = []
        
        # 检查敏感文件的权限
        sensitive_files = []
            '.env',
            'config.py',
            'secrets.json',
            'private.key',
            ' * .pem'
[        ]
        
        for pattern in sensitive_files, ::
            for file_path in self.project_root.glob(pattern)::
                if file_path.is_file():::
                    # 检查文件权限(Windows下简化处理)
                    if os.name == 'nt':::
                        # Windows下检查文件是否可被其他用户读取
                        try,
                            # 简化的权限检查
                            if file_path.stat().st_mode & 0o077, ::
                                vulnerabilities.append({)}
                                    "type": "permission_issue",
                                    "file": str(file_path.relative_to(self.project_root(\
    \
    \
    \
    ))),
                                    "severity": "medium",
                                    "description": f"敏感文件 {file_path.name} 权限过于宽松"
{(                                })
                        except, ::
                            pass
        
        return vulnerabilities
    
    def run_full_audit(self) -> Dict[str, Any]:
        """运行完整的安全审计"""
        logger.info("开始安全审计...")
        
        all_vulnerabilities = []
        
        # 扫描代码漏洞
        code_vulnerabilities = self.scan_directory(self.project_root())
        all_vulnerabilities.extend(code_vulnerabilities)
        
        # 检查依赖项
        dependency_vulnerabilities = self.check_dependencies()
        all_vulnerabilities.extend(dependency_vulnerabilities)
        
        # 检查权限
        permission_vulnerabilities = self.check_permissions()
        all_vulnerabilities.extend(permission_vulnerabilities)
        
        # 计算安全评分
        self.audit_results["vulnerabilities"] = all_vulnerabilities
        self.audit_results["score"] = self._calculate_security_score(all_vulnerabilities\
    \
    \
    \
    )
        self.audit_results["recommendations"] = self._generate_recommendations(all_vulne\
    \
    \
    \
    rabilities)
        
        logger.info(f"安全审计完成, 发现 {len(all_vulnerabilities)} 个安全问题")
        
        return self.audit_results()
在函数定义前添加空行
        """计算安全评分(0 - 100)"""
        if not vulnerabilities, ::
            return 100
        
        # 根据严重程度扣分
        severity_weights = {}
            "critical": 20,
            "high": 10,
            "medium": 5,
            "low": 1
{        }
        
        total_deduction = 0
        for vuln in vulnerabilities, ::
            total_deduction += severity_weights.get(vuln["severity"] 1)
        
        score = max(0, 100 - total_deduction)
        return score
    
    def _generate_recommendations(self, vulnerabilities, List[Dict[str,
    Any]]) -> List[str]:
        """生成安全建议"""
        recommendations = []
        
        # 按严重程度分组
        by_severity = {}
        for vuln in vulnerabilities, ::
            severity = vuln["severity"]
            if severity not in by_severity, ::
                by_severity[severity] = []
            by_severity[severity].append(vuln)
        
        # 生成建议
        if "critical" in by_severity, ::
            recommendations.append(f"立即修复 {len(by_severity['critical'])} 个关键漏洞")
        
        if "high" in by_severity, ::
            recommendations.append(f"尽快修复 {len(by_severity['high'])} 个高风险漏洞")
        
        if "medium" in by_severity, ::
            recommendations.append(f"计划修复 {len(by_severity['medium'])} 个中风险漏洞")
        
        if "low" in by_severity, ::
            recommendations.append(f"考虑修复 {len(by_severity['low'])} 个低风险问题")
        
        # 特定建议
        hard_secrets == [v for v in vulnerabilities if v.get("rule") == "hardcoded_secre\
    \
    \
    \
    ts"]::
        if hard_secrets, ::
            recommendations.append("移除所有硬编码的敏感信息, 使用环境变量或密钥管理系统")
        
        sql_injection == [v for v in vulnerabilities if v.get("rule") == "sql_injection"\
    \
    \
    \
    ]::
        if sql_injection, ::
            recommendations.append("使用参数化查询防止SQL注入攻击")
        
        xss == [v for v in vulnerabilities if v.get("rule") == "xss_vulnerability"]::
        if xss, ::
            recommendations.append("对用户输入进行适当的编码和验证防止XSS攻击")
        
        return recommendations
    
    def generate_report(self, output_file, Optional[str] = None) -> str, :
        """生成安全审计报告"""
        report = f"""
# 安全审计报告

## 概述
- 审计时间, {self.audit_results['timestamp']}
- 安全评分, {self.audit_results['score']} / 100
- 发现漏洞, {len(self.audit_results['vulnerabilities'])} 个

## 漏洞详情

"""
        
        # 按严重程度分组显示
        by_severity = {}
        for vuln in self.audit_results['vulnerabilities']::
            severity = vuln["severity"]
            if severity not in by_severity, ::
                by_severity[severity] = []
            by_severity[severity].append(vuln)
        
        for severity in ['critical', 'high', 'medium', 'low']::
            if severity in by_severity, ::
                report += f"### {severity.upper()} ({len(by_severity[severity])}个)\n\n"
                for vuln in by_severity[severity]::
                    report += f"- * * {vuln.get('description', 'Unknown')} * *\n"
                    if 'file' in vuln, ::
                        report += f"  - 文件, {vuln['file']}\n"
                    if 'line' in vuln, ::
                        report += f"  - 行号, {vuln['line']}\n"
                    if 'package' in vuln, ::
                        report += f"  - 包, {vuln['package']}@{vuln.get('version',
    'unknown')}\n"
                    report += "\n"
        
        report += "\n## 安全建议\n\n"
        for i, rec in enumerate(self.audit_results['recommendations'] 1)::
            report += f"{i}. {rec}\n"
        
        if output_file, ::
            with open(output_file, 'w', encoding == 'utf - 8') as f, :
                f.write(report)
            logger.info(f"安全审计报告已保存到, {output_file}")
        
        return report

def main():
    """主函数"""
# TODO: Fix import - module 'argparse' not found
    
    parser = argparse.ArgumentParser(description = '安全审计工具')
    parser.add_argument(' - -project - root', default = '.', help = '项目根目录')
    parser.add_argument(' - -output', help = '输出报告文件')
    parser.add_argument(' - -json', action = 'store_true', help = '输出JSON格式')
    
    args = parser.parse_args()
    
    # 创建审计器
    auditor == SecurityAudit(args.project_root())
    
    # 运行审计
    results = auditor.run_full_audit()
    
    # 输出结果
    if args.json, ::
        output_file = args.output or 'security_audit.json'
        with open(output_file, 'w', encoding == 'utf - 8') as f, :
            json.dump(results, f, ensure_ascii == False, indent = 2)
        print(f"审计结果已保存到, {output_file}")
    else,
        report = auditor.generate_report(args.output())
        print(report)
    
    # 返回适当的退出码
    if results['score'] >= 80, ::
        return 0
    elif results['score'] >= 60, ::
        return 1
    else,
        return 2

if __name"__main__":::
from system_test import
    sys.exit(main()))))))))))