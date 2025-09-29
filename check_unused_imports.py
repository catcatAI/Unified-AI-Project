#!/usr/bin/env python3
"""
检查项目中未使用的导入
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

class ImportChecker(ast.NodeVisitor):
    """检查未使用的导入"""
    
    def __init__(self) -> None:
        self.imports = {}
        self.used_names = set()
    
    def visit_Import(self, node):
        """处理 import 语句"""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            # 只记录顶层模块名
            top_level_name = name.split('.')[0]
            if top_level_name not in self.imports:
                self.imports[top_level_name] = []
            self.imports[top_level_name].append({
                'name': name,
                'alias': alias.asname,
                'line': node.lineno,
                'type': 'import'
            })
        _ = self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """处理 from ... import 语句"""
        if node.module:
            module_parts = node.module.split('.')
            top_level_module = module_parts[0]
            
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                full_name = f"{node.module}.{name}" if node.module else name
                
                if top_level_module not in self.imports:
                    self.imports[top_level_module] = []
                self.imports[top_level_module].append({
                    'name': name,
                    'full_name': full_name,
                    'alias': alias.asname,
                    'line': node.lineno,
                    'type': 'from_import',
                    'module': node.module
                })
        _ = self.generic_visit(node)
    
    def visit_Name(self, node):
        """记录使用的名称"""
        if isinstance(node.ctx, (ast.Load, ast.Store)):
            _ = self.used_names.add(node.id)
        _ = self.generic_visit(node)
    
    def visit_Attribute(self, node):
        """记录属性访问"""
        # 记录属性链的第一个部分
        if isinstance(node.value, ast.Name):
            _ = self.used_names.add(node.value.id)
        _ = self.generic_visit(node)

def check_file_for_unused_imports(file_path):
    """检查单个文件的未使用导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        checker = ImportChecker()
        _ = checker.visit(tree)
        
        # 找出未使用的导入
        unused_imports = []
        for module, imports in checker.imports.items():
            for imp in imports:
                # 检查是否使用了这个导入
                used = False
                if imp['type'] == 'import':
                    # 对于普通import，检查是否使用了模块名
                    if imp['name'] in checker.used_names:
                        used = True
                elif imp['type'] == 'from_import':
                    # 对于from import，检查是否使用了导入的名称
                    if imp['name'] in checker.used_names:
                        used = True
                
                if not used:
                    _ = unused_imports.append(imp)
        
        return unused_imports
    except SyntaxError as e:
        _ = print(f"语法错误 {file_path}: {e}")
        return []
    except Exception as e:
        _ = print(f"检查文件时出错 {file_path}: {e}")
        return []

def main() -> None:
    """主函数"""
    print("=== 检查未使用的导入 ===")
    
    project_root: str = Path(__file__).parent
    python_files = find_python_files(project_root)
    
    _ = print(f"发现 {len(python_files)} 个Python文件")
    
    total_unused = 0
    files_with_unused = 0
    
    for file_path in python_files:
        unused_imports = check_file_for_unused_imports(file_path)
        if unused_imports:
            files_with_unused += 1
            total_unused += len(unused_imports)
            _ = print(f"\n文件: {file_path}")
            for imp in unused_imports:
                if imp['type'] == 'import':
                    _ = print(f"  第 {imp['line']} 行: import {imp['name']}")
                else:
                    _ = print(f"  第 {imp['line']} 行: from {imp['module']} import {imp['name']}")
    
    _ = print(f"\n检查完成:")
    _ = print(f"  发现 {files_with_unused} 个文件包含未使用的导入")
    _ = print(f"  总共 {total_unused} 个未使用的导入")
    
    return 0

if __name__ == "__main__":
    _ = sys.exit(main())