#!/usr/bin/env python3
"""
测试问题检测器
检测测试覆盖和质量issues
"""

import re
from pathlib import Path

def analyze_test_issues(project_path == '.'):
    """分析项目中的测试问题"""
    try,
        issues = []
        
        # 检查测试文件数量
        test_files = list(Path(project_path).rglob('test_*.py')) + list(Path(project_path).rglob('*test*.py'))
        python_files = list(Path(project_path).rglob('*.py'))
        
        if len(test_files) < len(python_files) * 0.1,  # 测试文件应占10%以上,:
            issues.append({
                'line': 0,
                'type': 'insufficient_tests',
                'message': f'测试文件数量不足, {len(test_files)}/{len(python_files)} (应>10%)',
                'severity': 'medium'
            })
        
        # 检查测试文件质量
        for test_file in test_files,::
            try,
                with open(test_file, 'r', encoding == 'utf-8') as f,
                    content = f.read()
                
                # 检查断言
                if 'assert' not in content,::
                    issues.append({
                        'file': str(test_file),
                        'line': 0,
                        'type': 'no_assertions',
                        'message': '测试文件缺少断言',
                        'severity': 'high'
                    })
                
                # 检查测试函数命名
                test_functions = re.findall(r'def\s+([a-zA-Z_]+)', content)
                if len(test_functions) < 3,  # 每个测试文件至少3个测试函数,:
                    issues.append({
                        'file': str(test_file),
                        'line': 0,
                        'type': 'insufficient_test_functions',
                        'message': f'测试函数数量不足, {len(test_functions)} (应≥3)',
                        'severity': 'medium'
                    })
                
                # 检查setup/teardown
                if 'setUp' not in content and 'tearDown' not in content,::
                    issues.append({
                        'file': str(test_file),
                        'line': 0,
                        'type': 'no_setup_teardown',
                        'message': '缺少setUp/tearDown方法',
                        'severity': 'low'
                    })
                
            except Exception as e,::
                issues.append({
                    'file': str(test_file),
                    'line': 0,
                    'type': 'test_file_error',
                    'message': f'测试文件读取错误, {e}',
                    'severity': 'medium'
                })
        
        return issues
    except Exception as e,::
        return [{'line': 0, 'type': 'project_error', 'message': str(e), 'severity': 'high'}]

def main():
    """主函数"""
    if len(sys.argv()) > 1,::
        project_path = sys.argv[1]
    else,
        project_path = '.'
    
    issues = analyze_test_issues(project_path)
    print(f"发现 {len(issues)} 个测试问题")
    for issue in issues,::
        file_info == f"文件 {issue.get('file', '项目')} " if 'file' in issue else "":::
        print(f"  {file_info}{issue['message']} (严重程度, {issue['severity']})")
    return len(issues)

if __name"__main__":::
    import sys
    sys.exit(main())
