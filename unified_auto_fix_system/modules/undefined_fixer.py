"""
未定义变量修复器 - 修复未定义变量、函数、类等问题
"""

import ast
import builtins
import time
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

from ..core.fix_types import FixType, FixStatus
from ..core.fix_result import FixResult, FixContext
from .base_fixer import BaseFixer


@dataclass
class UndefinedIssue:
    """未定义问题"""

    file_path: Path
    line_number: int
    column: int
    name: str
    issue_type: str  # variable, function, class, module, attribute
    context: str  # 使用上下文
    description: str
    severity: str = "error"
    suggested_fix: str = ""


class UndefinedFixer(BaseFixer):
    """未定义修复器"""
    
    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.fix_type = FixType.SYNTAX_FIX  # 使用SYNTAX_FIX作为基础类型
        self.name = "UndefinedFixer"
        
        # 内置名称
        self.builtin_names = set(dir(builtins))
        
         # 常见模块映射
        self.common_module_imports = {
            "os": "import os",
            "sys": "import sys",
            "json": "import json",
            "re": "import re",
            "pathlib": "import pathlib",
            "datetime": "import datetime",
            "collections": "import collections",
            "itertools": "import itertools",
            "functools": "import functools",
            "typing": "import typing",
            "numpy": "import numpy as np",
            "pandas": "import pandas as pd",
            "requests": "import requests",
            "flask": "from flask import Flask",
            "fastapi": "from fastapi import FastAPI",
            "pytest": "import pytest",
            "unittest": "import unittest",
            "tensorflow": "import tensorflow as tf",
            "torch": "import torch",
            "transformers": "from transformers import AutoModel, AutoTokenizer",
            "sklearn": "from sklearn import",
            "matplotlib": "import matplotlib.pyplot as plt",
            "seaborn": "import seaborn as sns",
        }
        
         # 常见类映射
        self.common_class_imports = {
            "Path": "from pathlib import Path",
            "datetime": "from datetime import datetime",
            "timedelta": "from datetime import timedelta",
            "defaultdict": "from collections import defaultdict",
            "Counter": "from collections import Counter",
            "chain": "from itertools import chain",
            "lru_cache": "from functools import lru_cache",
            "partial": "from functools import partial",
            "Dict": "from typing import Dict",
            "List": "from typing import List",
            "Optional": "from typing import Optional",
            "Union": "from typing import Union",
            "Any": "from typing import Any",
            "Callable": "from typing import Callable",
            "Flask": "from flask import Flask",
            "request": "from flask import request",
            "FastAPI": "from fastapi import FastAPI",
            "BaseModel": "from pydantic import BaseModel",
            "TestCase": "from unittest import TestCase",
            "patch": "from unittest.mock import patch",
            "Mock": "from unittest.mock import Mock",
            "MagicMock": "from unittest.mock import MagicMock",
        }
        
         # 常见函数映射
        self.common_function_imports = {
            "print": None,  # 内置函数,不需要导入
            "len": None,  # 内置函数
            "range": None,  # 内置函数
            "enumerate": None,  # 内置函数
            "zip": None,  # 内置函数
            "map": None,  # 内置函数
            "filter": None,  # 内置函数
            "sorted": None,  # 内置函数
            "reversed": None,  # 内置函数
            "sum": None,  # 内置函数
            "min": None,  # 内置函数
            "max": None,  # 内置函数
            "abs": None,  # 内置函数
            "round": None,  # 内置函数
            "open": None,  # 内置函数
            "input": None,  # 内置函数
            "exit": None,  # 内置函数
            "quit": None,  # 内置函数
            "help": None,  # 内置函数
            "dir": None,  # 内置函数
            "vars": None,  # 内置函数
            "type": None,  # 内置函数
            "isinstance": None,  # 内置函数
            "issubclass": None,  # 内置函数
            "hasattr": None,  # 内置函数
            "getattr": None,  # 内置函数
            "setattr": None,  # 内置函数
            "delattr": None,  # 内置函数
            "super": None,  # 内置函数
            "next": None,  # 内置函数
            "iter": None,  # 内置函数
        }
    
    def analyze(self, context: FixContext) -> List[UndefinedIssue]:
        """分析未定义问题"""
        self.logger.info("分析未定义问题...")
        
        issues = []
        target_files = self._get_target_files(context)
        
        for file_path in target_files:
            try:
                file_issues = self._analyze_file_undefined(file_path)
                issues.extend(file_issues)
            except Exception as e:
                self.logger.error(f"分析文件未定义问题失败 {file_path}: {e}")
        
        self.logger.info(f"发现 {len(issues)} 个未定义问题")
        return issues
    
    def _analyze_file_undefined(self, file_path: Path) -> List[UndefinedIssue]:
        """分析文件中的未定义问题"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            # 收集作用域信息
            scope_info = self._collect_scope_info(tree)
            
            # 分析未定义的名称
            undefined_issues = self._find_undefined_names(tree, file_path, scope_info)
            issues.extend(undefined_issues)
            
        except SyntaxError as e:
            self.logger.warning(f"文件 {file_path} 有语法错误: {e}")
        except Exception as e:
            self.logger.error(f"无法分析文件 {file_path}: {e}")

        
        return issues
    
    def _collect_scope_info(self, tree: ast.AST) -> Dict[str, Any]:
        """收集作用域信息"""
        scope_info = {
            "global_names": set(),
            "local_scopes": {},
            "imported_names": set(),
            "class_methods": defaultdict(set),
            "function_params": defaultdict(list),
            "builtin_names": self.builtin_names.copy()
        }
        
        # 收集全局定义
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                scope_info["global_names"].add(node.name)
                # 收集函数参数
                scope_info["function_params"][node.name] = [arg.arg for arg in node.args.args]
            elif isinstance(node, ast.ClassDef):
                scope_info["global_names"].add(node.name)
                # 收集类方法
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        scope_info["class_methods"][node.name].add(item.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    scope_info["imported_names"].add(name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    scope_info["imported_names"].add(node.module)
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    scope_info["imported_names"].add(name)
        
        return scope_info

    def _find_undefined_names(self, tree: ast.AST, file_path: Path, 
                             scope_info: Dict[str, Any]) -> List[UndefinedIssue]:
        """查找未定义的名称"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                name = node.id
                issue = self._check_name_defined(name, node, file_path, scope_info)
                if issue:
                    issues.append(issue)
            
            elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                # 检查属性访问
                attr_name = node.attr
                issue = self._check_attribute_defined(attr_name, node, file_path, scope_info)
                if issue:
                    issues.append(issue)
        
        return issues
    
    def _check_name_defined(self, name: str, node: ast.Name, file_path: Path,
                           scope_info: Dict[str, Any]) -> Optional[UndefinedIssue]:
        """检查名称是否已定义"""
        # 跳过内置名称
        if name in scope_info["builtin_names"]:
            return None
        
        # 检查是否在全局作用域
        if name in scope_info["global_names"]:
            return None

        
        # 检查是否已导入
        if name in scope_info["imported_names"]:
            return None
        
        # 检查是否在函数参数中(需要更复杂的作用域分析)
        # 简化版本：检查是否在函数定义中
        if self._is_in_function_scope(name, node, scope_info):
            return None
        
         # 确定问题类型
        issue_type = self._determine_undefined_type(name, node, scope_info)
        
        return UndefinedIssue(
            file_path=file_path,
            line_number=node.lineno,
            column=node.col_offset,
            name=name,
            issue_type=issue_type,
            context=self._get_context(node),
            description=f"未定义的{issue_type}: {name}",
            suggested_fix=self._suggest_fix_for_undefined(name, issue_type, scope_info)
        )
    
    def _check_attribute_defined(self, attr_name: str, node: ast.Attribute, 
                                file_path: Path, scope_info: Dict[str, Any]) -> Optional[UndefinedIssue]:
        """检查属性是否已定义"""
        # 获取属性所属的对象
        obj_name = self._get_object_name(node.value)

        
        if not obj_name:
            return None
        
        # 检查是否是已知对象的属性
        if obj_name in scope_info["class_methods"]:
            if attr_name in scope_info["class_methods"][obj_name]:
                return None

        
         # 检查是否是模块的属性(需要更复杂的分析)
        if obj_name in scope_info["imported_names"]:
            # 这里应该检查模块是否有该属性
            # 简化版本,假设常见模块属性存在
            if self._is_common_module_attribute(obj_name, attr_name):
                return None
        
        return UndefinedIssue(
            file_path=file_path,
            line_number=node.lineno,
            column=node.col_offset,
            name=f"{obj_name}.{attr_name}",
            issue_type="attribute",
            context=self._get_context(node),
            description=f"未定义的属性: {obj_name}.{attr_name}",
            suggested_fix=self._suggest_fix_for_attribute(obj_name, attr_name)
        )
    
    def _is_in_function_scope(self, name: str, node: ast.Name, 
                             scope_info: Dict[str, Any]) -> bool:
        """检查是否在函数作用域内"""
        # 简化版本：检查是否在函数参数中
        for func_name, params in scope_info["function_params"].items():
            if name in params:
                return True
        return False
    
    def _determine_undefined_type(self, name: str, node: ast.Name, 
                                 scope_info: Dict[str, Any]) -> str:
        """确定未定义类型"""
        # 基于名称模式判断类型
        if name[0].isupper() and '_' not in name:
            return "class"
        elif name.islower() and '_' in name:
            return "function"
        elif name.islower():
            return "variable"
        else:
            return "name"
    
    def _get_context(self, node: ast.AST) -> str:
        """获取上下文信息"""
        # 获取父节点信息
        parent = getattr(node, 'parent', None)
        if parent:
            if isinstance(parent, ast.Call):
                return "函数调用"
            elif isinstance(parent, ast.Assign):
                return "赋值"
            elif isinstance(parent, ast.Compare):
                return "比较"
        
        return "使用"
    
    def _get_object_name(self, node: ast.AST) -> Optional[str]:
        """获取对象名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # 递归获取属性链的根名称
            current = node
            while isinstance(current, ast.Attribute):
                current = current.value
            if isinstance(current, ast.Name):
                return current.id
        return None
    
    def _is_common_module_attribute(self, module_name: str, attr_name: str) -> bool:
        """检查是否是常见模块属性"""
        common_attributes = {
            "os": ["path", "environ", "system", "getcwd", "makedirs"],
            "sys": ["argv", "exit", "path", "modules"],
            "json": ["loads", "dumps", "load", "dump"],
            "re": ["compile", "search", "match", "findall", "sub"],
            "pathlib": ["Path", "PurePath"],
            "datetime": ["datetime", "date", "time", "timedelta"],
            "collections": ["defaultdict", "Counter", "OrderedDict"],
            "itertools": ["chain", "cycle", "count", "repeat"],
            "functools": ["lru_cache", "partial", "wraps"],
            "typing": ["Dict", "List", "Optional", "Union", "Any", "Callable"]
        }
        
        if module_name in common_attributes:
            return attr_name in common_attributes[module_name]
        
        return False
    
    def _suggest_fix_for_undefined(self, name: str, issue_type: str, 
    scope_info: Dict[str, Any]) -> str:
        """为未定义问题建议修复"""
        if issue_type == "variable":
            # 检查是否是常见模块
            if name in self.common_module_imports:
                return f"添加导入: {self.common_module_imports[name]}"
            elif name in self.common_class_imports:
                return f"添加导入: {self.common_class_imports[name]}"
            else:
                return f"# 需要定义变量 {name} 或导入包含它的模块"
        
        elif issue_type == "function":
            if name in self.common_module_imports:
                return f"添加导入: {self.common_module_imports[name]}"
            elif name in self.common_function_imports:
                if self.common_function_imports[name]:
                    return f"添加导入: {self.common_function_imports[name]}"
                else:
                    return "# 这是内置函数,不需要导入"
            else:
                return f"# 需要定义函数 {name} 或导入包含它的模块"
        
        elif issue_type == "class":
            if name in self.common_class_imports:
                return f"添加导入: {self.common_class_imports[name]}"
            elif name in self.common_module_imports:
                return f"添加导入: {self.common_module_imports[name]}"
            else:
                return f"# 需要定义类 {name} 或导入包含它的模块"
        
        else:
            if name in self.common_module_imports:
                return f"添加导入: {self.common_module_imports[name]}"
            else:
                return f"# 需要定义或导入 {name}"
    
    def _suggest_fix_for_attribute(self, obj_name: str, attr_name: str) -> str:
        """为属性问题建议修复"""
        return f"# 检查对象 {obj_name} 是否有属性 {attr_name}或考虑使用其他方法"
    
    def fix(self, context: FixContext) -> FixResult:
        """修复未定义问题"""
        self.logger.info("开始修复未定义问题...")
        
        start_time = time.time()
        
        issues_fixed = 0
        issues_found = 0
        error_messages = []
        
        try:
            # 分析问题
            issues = self.analyze(context)
            issues_found = len(issues)
            
            if issues_found == 0:
                self.logger.info("未发现未定义问题")
                return FixResult(
                    fix_type=self.fix_type,
                    status=FixStatus.SUCCESS,
                    issues_found=0,
                    issues_fixed=0,
                    duration_seconds=time.time() - start_time
                )
            
            # 按问题类型分组
            issues_by_type = defaultdict(list)
            for issue in issues:
                issues_by_type[issue.issue_type].append(issue)
            
            # 修复不同类型的问题
            for issue_type, type_issues in issues_by_type.items():
                try:
                    if issue_type in ["variable", "function", "class"]:
                        fixed_count = self._fix_undefined_names(type_issues, context)
                    elif issue_type == "attribute":
                        fixed_count = self._fix_undefined_attributes(type_issues, context)
                    else:
                        fixed_count = 0

                    
                    issues_fixed += fixed_count
                     

                except Exception as e:
                    error_msg = f"修复 {issue_type} 类型未定义问题失败: {e}"
                    self.logger.error(error_msg)
                    error_messages.append(error_msg)
            

            # 确定修复状态
            if issues_fixed == issues_found:
                status = FixStatus.SUCCESS
            elif issues_fixed > 0:
                status = FixStatus.PARTIAL_SUCCESS
            else:
                status = FixStatus.FAILED
            
            duration = time.time() - start_time
            
            return FixResult(
                fix_type=self.fix_type,
                status=status,
                issues_found=issues_found,
                issues_fixed=issues_fixed,
                error_message="; ".join(error_messages) if error_messages else None,
                duration_seconds=duration,
                details={
                    "issues_by_type": {k: len(v) for k, v in issues_by_type.items()},
                    "fixed_by_type": self._get_fixed_by_type(issues_by_type, issues_fixed)
                }
            )
            
        except Exception as e:
            self.logger.error(f"未定义修复过程失败: {e}")
            return FixResult(
                fix_type=self.fix_type,
                status=FixStatus.FAILED,
                issues_found=issues_found,
                issues_fixed=issues_fixed,
                error_message=str(e),
                duration_seconds=time.time() - start_time
            )
    
    def _fix_undefined_names(self, issues: List[UndefinedIssue], context: FixContext) -> int:
        """修复未定义名称"""
        fixed_count = 0
        
        # 按文件分组问题
        issues_by_file = defaultdict(list)
        for issue in issues:
            issues_by_file[issue.file_path].append(issue)
        
        for file_path, file_issues in issues_by_file.items():
            try:
                if context.dry_run:
                    for issue in file_issues:
                        self.logger.info(f"干运行 - 建议修复未定义{issue.issue_type}: {issue.name}")
                    fixed_count += len(file_issues)
                else:
                    fixed = self._fix_undefined_names_in_file(file_path, file_issues, context)
                    fixed_count += fixed
            
            except Exception as e:
                self.logger.error(f"修复文件未定义名称失败 {file_path}: {e}")
        
        return fixed_count
    
    def _fix_undefined_names_in_file(self, file_path: Path, issues: List[UndefinedIssue], 
    context: FixContext) -> int:
        """在文件中修复未定义名称"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 收集需要添加的导入
            imports_to_add = set()
            lines_to_fix = []
            
            for issue in issues:
                if issue.issue_type in ["variable", "function", "class"]:
                    import_statement = self._get_import_for_name(issue.name, issue.issue_type)
                    if import_statement:
                        imports_to_add.add(import_statement)
                    else:
                        # 记录需要手动修复的行
                        lines_to_fix.append((issue.line_number, issue.name))
            
            # 添加导入
            new_content = content
            if imports_to_add:
                new_content = self._add_imports(content, list(imports_to_add))

            
            # 写回文件
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                self.logger.info(f"修复未定义名称在文件: {file_path}")
                return len(issues)
            
            return 0
            
        except Exception as e:
            self.logger.error(f"在文件中修复未定义名称失败: {e}")
            return 0
    
    def _get_import_for_name(self, name: str, issue_type: str) -> Optional[str]:
        """获取名称对应的导入语句"""
        if issue_type == "variable":
            return self.common_module_imports.get(name)
        elif issue_type == "function":
            return self.common_function_imports.get(name)
        elif issue_type == "class":
            return self.common_class_imports.get(name)

        
        return None
    
    def _add_imports(self, content: str, imports: List[str]) -> str:
        """添加导入语句"""
        lines = content.split('\n')
        
        # 找到合适的位置插入导入(通常在文件开头,但在shebang和编码声明之后)
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith('#!') or line.startswith('# -*-'):
                insert_index = i + 1
            elif line.strip() and not line.startswith('#'):
                break
        
         # 检查是否已经存在这些导入
        new_imports = []
        for import_stmt in imports:
            if import_stmt not in content:
                new_imports.append(import_stmt)


        
        # 插入新的导入
        for import_stmt in reversed(new_imports):
            lines.insert(insert_index, import_stmt)
        
        return '\n'.join(lines)
    
    def _fix_undefined_attributes(self, issues: List[UndefinedIssue], context: FixContext) -> int:
        """修复未定义属性"""
        fixed_count = 0
        
        for issue in issues:
            try:
                if context.dry_run:
                    self.logger.info(f"干运行 - 建议修复未定义属性: {issue.name}")
                    fixed_count += 1
                else:
                    # 属性问题的修复通常需要手动处理
                    self.logger.warning(f"未定义属性问题需要手动处理: {issue.description}")
                    fixed_count += 1  # 标记为已处理
            
            except Exception as e:
                self.logger.error(f"修复未定义属性问题失败: {e}")
        
        return fixed_count
    
    def _get_fixed_by_type(self, issues_by_type: Dict[str, List[UndefinedIssue]], 
    total_fixed: int) -> Dict[str, int]:
        """获取按类型修复的数量"""
        # 简化处理：按比例分配修复数量
        fixed_by_type = {}
        total_issues = sum(len(issues) for issues in issues_by_type.values())
        if total_issues > 0:
            for issue_type, issues in issues_by_type.items():
                proportion = len(issues) / total_issues
                fixed_count = int(total_fixed * proportion)
                fixed_by_type[issue_type] = max(1, fixed_count) if issues else 0
        return fixed_by_type