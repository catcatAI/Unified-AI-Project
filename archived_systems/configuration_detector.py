#!/usr/bin/env python3
"""
配置问题检测器
检测项目配置相关问题
"""

import re
from pathlib import Path

def analyze_configuration_issues(project_path='.'):
    """分析项目中的配置问题"""
    try:
        issues = []
        
        # 检查配置文件
        config_files = [
            '.gitignore', 'setup.py', 'setup.cfg', 'pyproject.toml',
            'tox.ini', '.flake8', '.pylintrc', 'mypy.ini'
        ]
        
        missing_configs = []
        for config_file in config_files:
            if not Path(project_path).joinpath(config_file).exists():
                missing_configs.append(config_file)
        
        if missing_configs:
            issues.append({
                'line': 0,
                'type': 'missing_configuration_files',
                'message': f'缺少配置文件: {", ".join(missing_configs)}',
                'severity': 'low'
            })
        
        # 检查环境配置
        env_files = list(Path(project_path).glob('.env*'))
        if env_files:
            for env_file in env_files:
                try:
                    with open(env_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 检查敏感信息
                    if re.search(r'password|secret|key|token', content, re.IGNORECASE):
                        issues.append({
                            'file': str(env_file),
                            'line': 0,
                            'type': 'sensitive_config',
                            'message': '配置文件可能包含敏感信息',
                            'severity': 'high'
                        })
                    
                except Exception as e:
                    issues.append({
                        'file': str(env_file),
                        'line': 0,
                        'type': 'config_file_error',
                        'message': f'配置文件读取错误: {e}',
                        'severity': 'medium'
                    })
        
        return issues
    except Exception as e:
        return [{'line': 0, 'type': 'project_error', 'message': str(e), 'severity': 'high'}]

def main():
    """主函数"""
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = '.'
    
    issues = analyze_configuration_issues(project_path)
    print(f"发现 {len(issues)} 个配置问题")
    for issue in issues:
        file_info = f"文件 {issue.get('file', '项目')}: " if 'file' in issue else ""
        print(f"  {file_info}{issue['message']} (严重程度: {issue['severity']})")
    return len(issues)

if __name__ == "__main__":
    import sys
    sys.exit(main())
