#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Angela AI 全面檢查腳本
檢查範圍：Python 代碼、JavaScript 代碼、配置文件、依賴、文檔
"""

import os
import sys
import ast
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

# 顏色輸出
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class Issue:
    def __init__(self, priority: str, category: str, file_path: str,
                 line_num: int, message: str, fix_suggestion: str):
        self.priority = priority  # P0, P1, P2, P3
        self.category = category  # syntax, import, config, logic, etc.
        self.file_path = file_path
        self.line_num = line_num
        self.message = message
        self.fix_suggestion = fix_suggestion

    def __str__(self):
        color = {
            'P0': Colors.FAIL,
            'P1': Colors.WARNING,
            'P2': Colors.OKCYAN,
            'P3': Colors.OKBLUE
        }.get(self.priority, Colors.ENDC)

        return f"{color}[{self.priority}]{Colors.ENDC} {self.category} in {self.file_path}:{self.line_num}\n  {self.message}\n  Fix: {self.fix_suggestion}"

class ComprehensiveAuditor:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues: List[Issue] = []
        self.stats = defaultdict(lambda: defaultdict(int))

    def add_issue(self, priority: str, category: str, file_path: str,
                  line_num: int, message: str, fix_suggestion: str):
        issue = Issue(priority, category, file_path, line_num, message, fix_suggestion)
        self.issues.append(issue)
        self.stats[priority][category] += 1

    def audit_python_syntax(self):
        """檢查 Python 語法錯誤"""
        print(f"\n{Colors.HEADER}檢查 Python 語法...{Colors.ENDC}")

        py_files = list(self.project_root.rglob("*.py"))
        print(f"找到 {len(py_files)} 個 Python 文件")

        errors = []
        for py_file in py_files:
            # 跳過虛擬環境和 node_modules
            if 'venv' in str(py_file) or 'node_modules' in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                ast.parse(content)
            except SyntaxError as e:
                rel_path = py_file.relative_to(self.project_root)
                self.add_issue(
                    priority='P0',
                    category='syntax',
                    file_path=str(rel_path),
                    line_num=e.lineno or 0,
                    message=f"語法錯誤: {e.msg}",
                    fix_suggestion=f"檢查第 {e.lineno} 行附近的語法"
                )
                errors.append((str(rel_path), e.lineno, e.msg))

        if errors:
            print(f"{Colors.FAIL}發現 {len(errors)} 個語法錯誤{Colors.ENDC}")
            for file_path, line, msg in errors[:10]:
                print(f"  {Colors.FAIL}✗{Colors.ENDC} {file_path}:{line} - {msg}")
        else:
            print(f"{Colors.OKGREEN}✓ 所有 Python 文件語法正確{Colors.ENDC}")

    def check_python_imports(self):
        """檢查 Python 導入問題"""
        print(f"\n{Colors.HEADER}檢查 Python 導入...{Colors.ENDC}")

        # 檢查關鍵文件的導入
        critical_files = [
            'apps/backend/src/services/main_api_server.py',
            'apps/backend/src/services/angela_llm_service.py',
            'apps/backend/src/pet/pet_manager.py',
            'apps/backend/src/core/autonomous/state_matrix.py',
            'apps/backend/src/core/hsp/connector.py',
        ]

        for file_path in critical_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                self.add_issue(
                    priority='P0',
                    category='missing_file',
                    file_path=file_path,
                    line_num=0,
                    message=f"關鍵文件不存在",
                    fix_suggestion=f"創建或恢復文件: {file_path}"
                )
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)
                imports = []

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ''
                        for alias in node.names:
                            imports.append(f"{module}.{alias.name}")

                # 檢查常見問題導入
                problematic_imports = []
                for imp in imports:
                    if 'tensorflow' in imp and 'tensorflow.compat' not in imp:
                        problematic_imports.append(imp)

                if problematic_imports:
                    self.add_issue(
                        priority='P2',
                        category='import_compatibility',
                        file_path=file_path,
                        line_num=0,
                        message=f"可能存在兼容性問題的導入: {', '.join(problematic_imports)}",
                        fix_suggestion="考慮使用 tensorflow.compat.v1 或更新版本的 API"
                    )

            except Exception as e:
                self.add_issue(
                    priority='P0',
                    category='import_check_failed',
                    file_path=file_path,
                    line_num=0,
                    message=f"導入檢查失敗: {str(e)}",
                    fix_suggestion="檢查文件語法和導入語句"
                )

    def check_config_files(self):
        """檢查配置文件"""
        print(f"\n{Colors.HEADER}檢查配置文件...{Colors.ENDC}")

        config_files = [
            'apps/backend/configs/multi_llm_config.json',
            'apps/backend/configs/system_config.yaml',
            'apps/backend/configs/hsp_fallback_config.json',
            '.env.example',
        ]

        for config_file in config_files:
            full_path = self.project_root / config_file

            if not full_path.exists():
                self.add_issue(
                    priority='P1',
                    category='missing_config',
                    file_path=config_file,
                    line_num=0,
                    message=f"配置文件不存在",
                    fix_suggestion=f"創建配置文件: {config_file}"
                )
                continue

            # 檢查 JSON 配置
            if config_file.endswith('.json'):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # 檢查 multi_llm_config.json
                    if 'multi_llm_config' in config_file:
                        if not isinstance(data, dict):
                            self.add_issue(
                                priority='P0',
                                category='config_format',
                                file_path=config_file,
                                line_num=0,
                                message="配置格式錯誤：應為字典",
                                fix_suggestion="檢查 JSON 格式"
                            )
                        else:
                            # 檢查是否至少有一個 LLM 配置啟用
                            enabled_count = sum(1 for cfg in data.values() if isinstance(cfg, dict) and cfg.get('enabled', False))
                            if enabled_count == 0:
                                self.add_issue(
                                    priority='P1',
                                    category='config_value',
                                    file_path=config_file,
                                    line_num=0,
                                    message="沒有啟用的 LLM 配置",
                                    fix_suggestion="至少啟用一個 LLM 後端"
                                )

                except json.JSONDecodeError as e:
                    self.add_issue(
                        priority='P0',
                        category='config_syntax',
                        file_path=config_file,
                        line_num=e.lineno or 0,
                        message=f"JSON 語法錯誤: {e.msg}",
                        fix_suggestion="檢查 JSON 語法"
                    )

            # 檢查 YAML 配置
            elif config_file.endswith('.yaml') or config_file.endswith('.yml'):
                try:
                    import yaml
                    with open(full_path, 'r', encoding='utf-8') as f:
                        yaml.safe_load(f)
                except ImportError:
                    self.add_issue(
                        priority='P2',
                        category='missing_dependency',
                        file_path=config_file,
                        line_num=0,
                        message="無法檢查 YAML 文件（缺少 PyYAML）",
                        fix_suggestion="安裝 PyYAML: pip install pyyaml"
                    )
                except yaml.YAMLError as e:
                    self.add_issue(
                        priority='P0',
                        category='config_syntax',
                        file_path=config_file,
                        line_num=e.problem_mark.line + 1 if e.problem_mark else 0,
                        message=f"YAML 語法錯誤: {str(e)}",
                        fix_suggestion="檢查 YAML 語法"
                    )

    def check_environment_files(self):
        """檢查環境配置"""
        print(f"\n{Colors.HEADER}檢查環境配置...{Colors.ENDC}")

        env_files = ['.env', '.env.example', '.env.production']

        for env_file in env_files:
            full_path = self.project_root / env_file

            if not full_path.exists():
                if env_file == '.env.example':
                    self.add_issue(
                        priority='P2',
                        category='missing_env_template',
                        file_path=env_file,
                        line_num=0,
                        message=f"環境變量模板文件不存在",
                        fix_suggestion=f"創建 {env_file} 作為環境變量模板"
                    )
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # 檢查格式問題
                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if line and not line.startswith('#') and '=' not in line:
                        self.add_issue(
                            priority='P2',
                            category='env_format',
                            file_path=env_file,
                            line_num=i,
                            message=f"環境變量格式錯誤: {line}",
                            fix_suggestion="使用 KEY=VALUE 格式"
                        )

            except Exception as e:
                self.add_issue(
                    priority='P1',
                    category='env_read_failed',
                    file_path=env_file,
                    line_num=0,
                    message=f"讀取環境文件失敗: {str(e)}",
                    fix_suggestion="檢查文件權限和格式"
                )

    def check_documentation(self):
        """檢查文檔一致性"""
        print(f"\n{Colors.HEADER}檢查文檔...{Colors.ENDC}")

        # 檢查主要文檔文件
        doc_files = [
            'README.md',
            'CHANGELOG.md',
            'AGENTS.md',
            'QUICKSTART.md',
        ]

        # 檢查版本號一致性
        version_pattern = r'\d+\.\d+\.\d+'
        versions = {}

        for doc_file in doc_files:
            full_path = self.project_root / doc_file

            if not full_path.exists():
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 提取版本號
                import re
                matches = re.findall(version_pattern, content)
                if matches:
                    versions[doc_file] = matches[0]

            except Exception as e:
                pass

        # 檢查版本號是否一致
        if len(versions) > 1:
            version_values = list(versions.values())
            if len(set(version_values)) > 1:
                self.add_issue(
                    priority='P3',
                    category='doc_version_inconsistency',
                    file_path=', '.join(versions.keys()),
                    line_num=0,
                    message=f"文檔版本號不一致: {versions}",
                    fix_suggestion="統一所有文檔中的版本號"
                )

    def check_package_json(self):
        """檢查 package.json"""
        print(f"\n{Colors.HEADER}檢查 package.json...{Colors.ENDC}")

        package_json_path = self.project_root / 'package.json'

        if not package_json_path.exists():
            self.add_issue(
                priority='P0',
                category='missing_package_json',
                file_path='package.json',
                line_num=0,
                message="package.json 不存在",
                fix_suggestion="創建 package.json 或檢查項目結構"
            )
            return

        try:
            with open(package_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 檢查必需字段
            required_fields = ['name', 'version', 'description']
            for field in required_fields:
                if field not in data:
                    self.add_issue(
                        priority='P1',
                        category='package_json_missing_field',
                        file_path='package.json',
                        line_num=0,
                        message=f"缺少必需字段: {field}",
                        fix_suggestion=f"添加 {field} 字段到 package.json"
                    )

            # 檢查腳本
            if 'scripts' in data:
                required_scripts = ['dev', 'test', 'build']
                for script in required_scripts:
                    if script not in data['scripts']:
                        self.add_issue(
                            priority='P2',
                            category='package_json_missing_script',
                            file_path='package.json',
                            line_num=0,
                            message=f"缺少常用腳本: {script}",
                            fix_suggestion=f"添加 {script} 腳本"
                        )

        except json.JSONDecodeError as e:
            self.add_issue(
                priority='P0',
                category='package_json_syntax',
                file_path='package.json',
                line_num=e.lineno or 0,
                message=f"JSON 語法錯誤: {e.msg}",
                fix_suggestion="檢查 JSON 語法"
            )

    def check_requirements_txt(self):
        """檢查 requirements.txt"""
        print(f"\n{Colors.HEADER}檢查 requirements.txt...{Colors.ENDC}")

        requirements_files = [
            'requirements.txt',
            'apps/backend/requirements.txt',
            'apps/backend/requirements-dev.txt',
        ]

        for req_file in requirements_files:
            full_path = self.project_root / req_file

            if not full_path.exists():
                if req_file == 'requirements.txt':
                    self.add_issue(
                        priority='P1',
                        category='missing_requirements',
                        file_path=req_file,
                        line_num=0,
                        message="requirements.txt 不存在",
                        fix_suggestion="創建 requirements.txt"
                    )
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # 檢查格式問題
                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    # 檢查是否包含版本號
                    if '==' not in line and '>=' not in line and '<=' not in line and '~=' not in line and '!=' not in line:
                        if not line.startswith(('-', '#', 'git+', 'http')):
                            self.add_issue(
                                priority='P3',
                                category='requirement_no_version',
                                file_path=req_file,
                                line_num=i,
                                message=f"缺少版本號: {line}",
                                fix_suggestion="添加版本約束（建議使用 >= 或 ==）"
                            )

            except Exception as e:
                self.add_issue(
                    priority='P1',
                    category='requirements_read_failed',
                    file_path=req_file,
                    line_num=0,
                    message=f"讀取 requirements.txt 失敗: {str(e)}",
                    fix_suggestion="檢查文件權限"
                )

    def run_all_checks(self):
        """運行所有檢查"""
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}Angela AI 全面檢查 v6.2.2{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"項目根目錄: {self.project_root}")

        self.audit_python_syntax()
        self.check_python_imports()
        self.check_config_files()
        self.check_environment_files()
        self.check_documentation()
        self.check_package_json()
        self.check_requirements_txt()

    def generate_report(self):
        """生成檢查報告"""
        print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}檢查報告{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")

        # 統計
        total_issues = len(self.issues)
        priority_counts = {p: len([i for i in self.issues if i.priority == p])
                          for p in ['P0', 'P1', 'P2', 'P3']}

        print(f"\n{Colors.BOLD}問題統計:{Colors.ENDC}")
        print(f"  總計: {total_issues} 個問題")
        print(f"  {Colors.FAIL}P0 (關鍵): {priority_counts['P0']}{Colors.ENDC}")
        print(f"  {Colors.WARNING}P1 (高優先級): {priority_counts['P1']}{Colors.ENDC}")
        print(f"  {Colors.OKCYAN}P2 (中優先級): {priority_counts['P2']}{Colors.ENDC}")
        print(f"  {Colors.OKBLUE}P3 (低優先級): {priority_counts['P3']}{Colors.ENDC}")

        # 按優先級顯示問題
        for priority in ['P0', 'P1', 'P2', 'P3']:
            priority_issues = [i for i in self.issues if i.priority == priority]
            if not priority_issues:
                continue

            color = {
                'P0': Colors.FAIL,
                'P1': Colors.WARNING,
                'P2': Colors.OKCYAN,
                'P3': Colors.OKBLUE
            }[priority]

            print(f"\n{color}{Colors.BOLD}{'='*60}{Colors.ENDC}")
            print(f"{color}{Colors.BOLD}{priority} 問題 ({len(priority_issues)} 個){Colors.ENDC}")
            print(f"{color}{Colors.BOLD}{'='*60}{Colors.ENDC}")

            for issue in priority_issues[:20]:  # 每個優先級最多顯示 20 個
                print(f"\n{issue}")

            if len(priority_issues) > 20:
                print(f"\n... 還有 {len(priority_issues) - 20} 個 {priority} 問題未顯示")

        # 系統狀態評估
        print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}系統狀態評估{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")

        if priority_counts['P0'] == 0 and priority_counts['P1'] == 0:
            print(f"{Colors.OKGREEN}✓ 系統狀態良好{Colors.ENDC}")
            print(f"  - 無關鍵問題")
            print(f"  - 無高優先級問題")
            print(f"  - {priority_counts['P2']} 個中優先級問題需要關注")
            print(f"  - {priority_counts['P3']} 個低優先級問題可以稍後處理")
        elif priority_counts['P0'] == 0:
            print(f"{Colors.WARNING}⚠ 系統有需要注意的問題{Colors.ENDC}")
            print(f"  - {priority_counts['P1']} 個高優先級問題需要儘快處理")
            print(f"  - {priority_counts['P2']} 個中優先級問題需要關注")
            print(f"  - {priority_counts['P3']} 個低優先級問題可以稍後處理")
        else:
            print(f"{Colors.FAIL}✗ 系統存在嚴重問題{Colors.ENDC}")
            print(f"  - {priority_counts['P0']} 個關鍵問題必須立即修復")
            print(f"  - {priority_counts['P1']} 個高優先級問題需要儘快處理")
            print(f"  - {priority_counts['P2']} 個中優先級問題需要關注")
            print(f"  - {priority_counts['P3']} 個低優先級問題可以稍後處理")

        return {
            'total_issues': total_issues,
            'priority_counts': priority_counts,
            'issues': self.issues
        }

def main():
    """主函數"""
    project_root = Path(__file__).parent / 'Unified-AI-Project'

    auditor = ComprehensiveAuditor(str(project_root))
    auditor.run_all_checks()
    report = auditor.generate_report()

    # 保存報告到 JSON
    report_path = Path(__file__).parent / 'ANGELA_AI_AUDIT_REPORT_v6.2.2.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total_issues': report['total_issues'],
            'priority_counts': report['priority_counts'],
            'issues': [
                {
                    'priority': i.priority,
                    'category': i.category,
                    'file_path': i.file_path,
                    'line_num': i.line_num,
                    'message': i.message,
                    'fix_suggestion': i.fix_suggestion
                }
                for i in report['issues']
            ]
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{Colors.OKGREEN}報告已保存到: {report_path}{Colors.ENDC}")

    # 返回退出碼
    if report['priority_counts']['P0'] > 0:
        sys.exit(1)
    elif report['priority_counts']['P1'] > 0:
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()