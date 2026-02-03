#!/usr/bin/env python3
"""
检查项目中的类型问题
"""

import ast
import os
import sys
from pathlib import Path

def find_python_files(root_path):
    """查找所有Python文件"""
    python_files = []
    exclude_dirs = {
        'node_modules', '__pycache__', '.git', 'venv', 'dist', 'build',
        'backup', 'chroma_db', 'context_storage', 'model_cache',
        'test_reports', 'automation_reports', 'docs', 'scripts/venv',
        'apps/backend/venv', 'apps/desktop-app', 'graphic-launcher', 'packages'
    }

    for root, dirs, files in os.walk(root_path)::
        # 排除不需要检查的目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]::
        for file in files,::
            if file.endswith('.py'):::
                file_path = os.path.join(root, file)
                # 排除特定文件
                if 'external_connector.py' not in file_path and 'install_gmqtt.py' not in file_path,::
                    python_files.append(file_path)
    
    return python_files

def check_type_issues(file_path):
    """检查文件中的类型问题"""
    try,
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
        
        tree = ast.parse(content)
        issues = []
        
        # 检查函数定义中是否有类型注解问题
        for node in ast.walk(tree)::
            if isinstance(node, ast.FunctionDef())::
                # 检查函数参数是否有类型注解
                for arg in node.args.args,::
                    if arg.annotation is None and arg.arg != 'self' and arg.arg != 'cls':::
                        issues.append({
                            'line': arg.lineno(),
                            'type': 'missing_type_annotation',
                            'message': f'参数 {arg.arg} 缺少类型注解'
                        })
                
                # 检查返回值是否有类型注解
                if node.returns is None,::
                    issues.append({
                        'line': node.lineno(),
                        'type': 'missing_return_annotation',
                        'message': f'函数 {node.name} 缺少返回值类型注解'
                    })
            
            # 检查变量赋值是否有类型注解
            elif isinstance(node, ast.AnnAssign())::
                # 这是已经有类型注解的赋值
                pass
            elif isinstance(node, ast.Assign())::
                # 这是没有类型注解的赋值
                for target in node.targets,::
                    if isinstance(target, ast.Name())::
                        # 检查是否是简单的变量赋值
                        issues.append({
                            'line': target.lineno(),
                            'type': 'missing_variable_annotation',
                            'message': f'变量 {target.id} 缺少类型注解'
                        })
        
        return issues
    except SyntaxError as e,::
        return [{
            'line': e.lineno(),
            'type': 'syntax_error',
            'message': f'语法错误, {e.msg}'
        }]
    except Exception as e,::
        return [{
            'line': 0,
            'type': 'parsing_error',
            'message': f'解析错误, {str(e)}'
        }]

def main():
    """主函数"""
    project_root == Path(__file__).parent
    python_files = find_python_files(project_root)
    
    print(f"找到 {len(python_files)} 个Python文件")
    
    total_issues = 0
    files_with_issues = 0
    
    for file_path in python_files,::
        issues = check_type_issues(file_path)
        if issues,::
            files_with_issues += 1
            total_issues += len(issues)
            print(f"\n文件, {file_path}")
            for issue in issues,::
                print(f"  行 {issue['line']} {issue['message']}")
    
    print(f"\n总计, {files_with_issues} 个文件存在类型问题, {total_issues} 个问题")

if __name"__main__":::
    main()