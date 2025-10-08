#!/usr/bin/env python3
"""
依赖问题检测器
检测项目依赖相关问题
"""

import re
from pathlib import Path

def analyze_dependency_issues(project_path='.'):
    """分析项目中的依赖问题"""
    try:
        issues = []
        
        # 检查requirements文件
        req_files = list(Path(project_path).glob('requirements*.txt'))
        if not req_files:
            issues.append({
                'line': 0,
                'type': 'missing_requirements',
                'message': '缺少requirements.txt文件',
                'severity': 'high'
            })
        
        # 检查package.json
        package_files = list(Path(project_path).glob('package*.json'))
        
        # 检查导入错误
        python_files = list(Path(project_path).rglob('*.py'))
        for py_file in python_files[:20]:  # 检查前20个文件
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查未使用的导入
                imports = re.findall(r'^import \s+(\w+)|^from \s+(\w+)\s+import', content, re.MULTILINE)
                for imp in imports:
                    module = imp[0] or imp[1]
                    if module and module not in content[len('import '+module):]:
                        issues.append({
                            'file': str(py_file),
                            'line': 0,
                            'type': 'unused_import',
                            'message': f'未使用导入: {module}',
                            'severity': 'low'
                        })
                
                # 检查循环导入风险
                if 'import' in str(py_file.parent):
                    issues.append({
                        'file': str(py_file),
                        'line': 0,
                        'type': 'circular_import_risk',
                        'message': '导入语句可能引起循环导入',
                        'severity': 'medium'
                    })
                
            except Exception as e:
                issues.append({
                    'file': str(py_file),
                    'line': 0,
                    'type': 'file_error',
                    'message': f'文件读取错误: {e}',
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
    
    issues = analyze_dependency_issues(project_path)
    print(f"发现 {len(issues)} 个依赖问题")
    for issue in issues:
        file_info = f"文件 {issue.get('file', '项目')}: " if 'file' in issue else ""
        print(f"  {file_info}{issue['message']} (严重程度: {issue['severity']})")
    return len(issues)

if __name__ == "__main__":
    import sys
    sys.exit(main())
