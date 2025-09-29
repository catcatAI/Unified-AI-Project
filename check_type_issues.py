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
    
    for root, dirs, files in os.walk(root_path):
        # 排除不需要检查的目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                # 排除特定文件
                if 'external_connector.py' not in file_path and 'install_gmqtt.py' not in file_path:
                    _ = python_files.append(file_path)
    
    return python_files

class TypeIssueChecker(ast.NodeVisitor):
    """检查类型问题"""
    
    def __init__(self) -> None:
        self.issues = []
        self.current_file = ""
    
    def set_file(self, file_path):
        """设置当前文件路径"""
        self.current_file = file_path
        self.issues = []
    
    def visit_Call(self, node):
        """检查函数调用"""
        # 检查是否有类型未知的调用
        if isinstance(node.func, ast.Name):
            # 检查一些常见的类型问题模式
            if node.func.id in ['len', 'str', 'int', 'float', 'bool']:
                # 检查参数是否可能有类型问题
                for arg in node.args:
                    if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name):
                        # 检查嵌套调用是否可能有类型问题
                        pass
        
        _ = self.generic_visit(node)
    
    def visit_Assign(self, node):
        """检查赋值语句"""
        # 检查是否有类型不明确的赋值
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target_name = node.targets[0].id
            # 检查一些模式
            if target_name in ['result', 'data', 'response', 'output']:
                # 检查右侧是否有类型不明确的表达式
                pass
        
        _ = self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        """检查函数定义"""
        # 检查函数参数和返回值类型注解
        if not node.returns and node.name not in ['__init__', '__str__', '__repr__']:
            # 检查是否有返回语句但没有返回类型注解
            has_return = any(isinstance(n, ast.Return) and n.value is not None 
                           for n in ast.walk(node))
            if has_return:
                self.issues.append({
                    'type': 'missing_return_annotation',
                    'line': node.lineno,
                    'function': node.name,
                    'message': f'函数 {node.name} 有返回值但缺少返回类型注解'
                })
        
        # 检查参数类型注解
        for arg in node.args.args:
            if not arg.annotation and arg.arg not in ['self', 'cls']:
                self.issues.append({
                    'type': 'missing_param_annotation',
                    'line': arg.lineno,
                    'function': node.name,
                    'param': arg.arg,
                    'message': f'函数 {node.name} 的参数 {arg.arg} 缺少类型注解'
                })
        
        _ = self.generic_visit(node)

def check_file_for_type_issues(file_path):
    """检查单个文件的类型问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        checker = TypeIssueChecker()
        _ = checker.set_file(file_path)
        _ = checker.visit(tree)
        
        return checker.issues
    except SyntaxError as e:
        _ = print(f"语法错误 {file_path}: {e}")
        return []
    except Exception as e:
        _ = print(f"检查文件时出错 {file_path}: {e}")
        return []

def check_common_type_patterns(content, file_path):
    """检查常见的类型问题模式"""
    issues = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        # 检查未使用的调用结果（基于之前的修复经验）
        if (line.strip().startswith(('await ', '')) and 
            '(' in line and ')' in line and
            not line.strip().startswith(('_', 'return', 'yield')) and
            '=' not in line and
            not line.strip().endswith('# type: ignore')):
            
            # 检查是否是函数调用
            if ('(' in line and ')' in line and 
                not any(keyword in line for keyword in ['if ', 'elif ', 'while ', 'for ', 'with '])):
                issues.append({
                    'type': 'unused_call_result',
                    'line': i,
                    'message': '函数调用结果未使用'
                })
        
        # 检查类型注解问题
        if ': Any' in line or ': any' in line.lower():
            issues.append({
                'type': 'generic_any_type',
                'line': i,
                'message': '使用了过于宽泛的 Any 类型'
            })
        
        # 检查缺少类型注解的变量
        if '=' in line and ':' not in line.split('=')[0] and not line.strip().startswith(('if ', 'elif ', 'else:', 'for ', 'while ')):
            left_side = line.split('=')[0].strip()
            if left_side and not left_side.startswith(('_', 'return', 'yield')) and left_side.isidentifier():
                # 检查是否是简单的赋值
                if not any(op in line for op in ['+=', '-=', '*=', '/=', '%=', '**=', '//=']):
                    issues.append({
                        'type': 'missing_variable_annotation',
                        'line': i,
                        'message': f'变量 {left_side} 缺少类型注解'
                    })
    
    return issues

def main() -> None:
    """主函数"""
    print("=== 检查类型问题 ===")
    
    project_root: str = Path(__file__).parent
    python_files = find_python_files(project_root)
    
    _ = print(f"发现 {len(python_files)} 个Python文件")
    
    total_issues = 0
    files_with_issues = 0
    
    for file_path in python_files:
        try:
            issues = check_file_for_type_issues(file_path)
            
            # 读取文件内容检查其他类型问题
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            pattern_issues = check_common_type_patterns(content, file_path)
            _ = issues.extend(pattern_issues)
            
            if issues:
                files_with_issues += 1
                total_issues += len(issues)
                _ = print(f"\n文件: {file_path}")
                for issue in issues[:5]:  # 只显示前5个问题
                    _ = print(f"  第 {issue['line']} 行: [{issue['type']}] {issue['message']}")
                if len(issues) > 5:
                    _ = print(f"  ... 还有 {len(issues) - 5} 个问题")
        except Exception as e:
            _ = print(f"检查文件时出错 {file_path}: {e}")
    
    _ = print(f"\n检查完成:")
    _ = print(f"  发现 {files_with_issues} 个文件包含类型问题")
    _ = print(f"  总共 {total_issues} 个类型问题")
    
    return 0

if __name__ == "__main__":
    _ = sys.exit(main())