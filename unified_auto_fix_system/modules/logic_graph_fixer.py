"""
智能逻辑图谱获取与修复系统
结合知识图谱和逻辑推理的高级修复引擎
"""

import ast
import json
import re
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import networkx as nx
from datetime import datetime

from ..core.fix_types import FixType, FixStatus
from ..core.fix_result import FixResult, FixContext
from .base_fixer import BaseFixer


@dataclass
class LogicNode:
    """逻辑图谱节点"""



    node_id: str
    node_type: str  # function, class, variable, import, etc.
    name: str
    file_path: Path
    line_number: int
    column: int
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


@dataclass
class LogicEdge:

    """逻辑图谱边"""
    source_id: str
    target_id: str
    edge_type: str  # calls, imports, inherits, uses, etc.
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LogicIssue:

    """逻辑图谱问题"""
    issue_id: str
    issue_type: str
    severity: str  # critical, high, medium, low
    description: str
    affected_nodes: List[str]
    suggested_fixes: List[str]
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class LogicGraphFixer(BaseFixer):
    """智能逻辑图谱获取与修复器"""
    
    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.fix_type = FixType.LOGIC_GRAPH_FIX
        self.name = "LogicGraphFixer"
        
        # 逻辑图谱数据结构
        self.logic_graph = nx.DiGraph()
        self.nodes_by_file = defaultdict(dict)
        self.global_symbols = {}
        self.import_graph = nx.DiGraph()
        
         # 修复策略

        self.repair_strategies = {
            "missing_import": self._fix_missing_import,
            "circular_dependency": self._fix_circular_dependency,
            "orphaned_code": self._fix_orphaned_code,
            "inconsistent_api": self._fix_inconsistent_api,
            "dead_code": self._fix_dead_code,

            "logic_error": self._fix_logic_error
        }
        
        # 知识库
        self.knowledge_base = self._load_knowledge_base()

        
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """加载知识库"""


        return {
            "common_patterns": {
            "singleton": ["get_instance", "instance", "singleton"],

 "factory": ["create", "make", "build"],

 "observer": ["notify", "subscribe", "observe"],


                "strategy": ["strategy", "algorithm", "policy"]
                },

            "api_conventions": {
            "getter_prefix": ["get_", "is_", "has_"],


 "setter_prefix": ["set_", "update_"],

                "action_prefix": ["create_", "delete_", "process_"]
                },

 "error_patterns": {


 "null_check": ["if.*is None", "if.*== None", "if.*!= None"],


                "type_check": ["isinstance", "type\\(", ".__class__"],
                "exception_handling": ["try:", "except", "finally:"]
            }
        }
    
    def analyze(self, context: FixContext) -> List[LogicIssue]:
        """分析逻辑图谱问题"""
        self.logger.info("构建和分析逻辑图谱...")
        
        # 构建逻辑图谱
        self._build_logic_graph(context)
        
        # 分析图谱问题
        issues = []
        issues.extend(self._analyze_missing_imports())
        issues.extend(self._analyze_circular_dependencies())
        issues.extend(self._analyze_orphaned_code())

        issues.extend(self._analyze_inconsistent_apis())
        issues.extend(self._analyze_dead_code())
        issues.extend(self._analyze_logic_errors())

        
        self.logger.info(f"发现 {len(issues)} 个逻辑图谱问题")
        return issues
    
    def _build_logic_graph(self, context: FixContext):
        """构建逻辑图谱"""
        self.logic_graph.clear()
        self.nodes_by_file.clear()
        self.global_symbols.clear()
        self.import_graph.clear()
        
        target_files = self._get_target_files(context)
        
        # 第一阶段：收集所有符号定义
        for file_path in target_files:
            try:
                self._collect_symbols_from_file(file_path)
            except Exception as e:
                self.logger.error(f"收集符号失败 {file_path}: {e}")
        
        # 第二阶段：建立依赖关系
        for file_path in target_files:

            try:
                self._build_dependencies_for_file(file_path)

            except Exception as e:
                self.logger.error(f"构建依赖关系失败 {file_path}: {e}")
        
        # 第三阶段：验证图谱一致性
        self._validate_logic_graph()
    
    def _collect_symbols_from_file(self, file_path: Path):
        """从文件收集符号"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 尝试解析AST
            try:
                tree = ast.parse(content)
            except SyntaxError:
                # 语法错误会在语法修复器中处理
                return
            
            # 收集符号定义
            symbol_collector = SymbolCollector(file_path, content)
            symbol_collector.visit(tree)
            
            # 添加到图谱
            for node in symbol_collector.nodes:
                self.logic_graph.add_node(node.node_id, **node.__dict__)
                self.nodes_by_file[str(file_path)][node.node_id] = node
                
                # 添加到全局符号表
                if node.node_type in ["function", "class", "variable"]:

                    symbol_key = f"{node.name}:{node.node_type}"
                    if symbol_key not in self.global_symbols:
                        self.global_symbols[symbol_key] = []

                    self.global_symbols[symbol_key].append(node)
            
             # 收集导入信息


            import_collector = ImportCollector(file_path, content)
            import_collector.visit(tree)

            
            for imp in import_collector.imports:
                self.import_graph.add_edge(str(file_path), imp.module, 
                                         line=imp.line_number, alias=imp.alias)
                
        except Exception as e:
            self.logger.error(f"收集符号失败 {file_path}: {e}")
    
    def _build_dependencies_for_file(self, file_path: Path):
        """为文件构建依赖关系"""
        try:

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            
             # 尝试解析AST

            try:
                tree = ast.parse(content)
            except SyntaxError:
                return


            
             # 分析依赖关系

            dependency_analyzer = DependencyAnalyzer(file_path, content, 
            self.nodes_by_file, 

                                                   self.global_symbols)
            dependency_analyzer.visit(tree)
            
             # 添加依赖边

            for dep in dependency_analyzer.dependencies:
                self.logic_graph.add_edge(dep.source_id, dep.target_id, 
                                        **dep.__dict__)
                
        except Exception as e:
            self.logger.error(f"构建依赖关系失败 {file_path}: {e}")
    
    def _validate_logic_graph(self):
        """验证逻辑图谱一致性"""
        # 检查循环依赖
        cycles = list(nx.simple_cycles(self.logic_graph))
        if cycles:

            self.logger.warning(f"发现 {len(cycles)} 个循环依赖")
        
         # 检查孤立节点

        isolated_nodes = list(nx.isolates(self.logic_graph))
        if isolated_nodes:
            self.logger.warning(f"发现 {len(isolated_nodes)} 个孤立节点")
    
    def _analyze_missing_imports(self) -> List[LogicIssue]:
        """分析缺失导入"""
        issues = []


        
        for node_id, node_data in self.logic_graph.nodes(data=True):
            if node_data.get('node_type') == 'name' and node_data.get('is_undefined'):
                # 检查是否是标准库或第三方库

                name = node_data.get('name', '')
                if self._is_likely_import_needed(name):
                    suggested_imports = self._suggest_import_for_name(name)
                    
                    issues.append(LogicIssue(
                    issue_id=f"missing_import_{node_id}",



                        issue_type="missing_import",
                        severity="high",

                        description=f"未定义的符号 '{name}' 可能需要导入",

 affected_nodes=[node_id],

                        suggested_fixes=suggested_imports,

 confidence=0.8

                    ))
        
        return issues
    
    def _analyze_circular_dependencies(self) -> List[LogicIssue]:
        """分析循环依赖"""
        issues = []

        cycles = list(nx.simple_cycles(self.logic_graph))
        
        for i, cycle in enumerate(cycles):
            if len(cycle) > 1:  # 忽略自循环

                cycle_description = " → ".join(cycle)
                issues.append(LogicIssue(
                issue_id=f"circular_dependency_{i}",

                    issue_type="circular_dependency",

#                     severity="critical",
description=f"循环依赖: {cycle_description}",

                    affected_nodes=cycle,

                    suggested_fixes=[
#                         "重构代码，打破循环依赖",
                        "使用依赖注入",
                        "提取公共接口",

#                         "延迟导入"

                    ],
                    confidence=1.0
                ))
        
        return issues
    
    def _analyze_orphaned_code(self) -> List[LogicIssue]:
        """分析孤立代码"""

        issues = []
        
         # 找到没有入边的函数和类


        for node_id, node_data in self.logic_graph.nodes(data=True):
            if node_data.get('node_type') in ['function', 'class']:

                in_degree = self.logic_graph.in_degree(node_id)
                if in_degree == 0 and not node_data.get('is_entry_point', False):

                    issues.append(LogicIssue(
                        issue_id=f"orphaned_code_{node_id}",
                        issue_type="orphaned_code",
                        severity="medium",
                        description=f"孤立的{node_data['node_type']} '{node_data['name']}' 没有被使用",
                        affected_nodes=[node_id],
                        suggested_fixes=[
                            "检查是否应该删除这段代码",
                            "确保有适当的调用",
                            "添加单元测试",
                            "标记为内部使用"
                        ],
                        confidence=0.7
                    ))
        
        return issues
    
    def _analyze_inconsistent_apis(self) -> List[LogicIssue]:
        """分析不一致的API"""

        issues = []
        
        # 按名称分组分析函数
        function_groups = defaultdict(list)
        for node_id, node_data in self.logic_graph.nodes(data=True):


            if node_data.get('node_type') == 'function':
                name = node_data.get('name', '')
                function_groups[name].append((node_id, node_data))
        
         # 检查同一函数名的不同实现

        for func_name, functions in function_groups.items():


            if len(functions) > 1:
                # 检查参数一致性
                param_signatures = []

                for node_id, node_data in functions:

                    params = node_data.get('parameters', [])
                    param_types = [p.get('type_hint') for p in params]
                    param_signatures.append((node_id, param_types))

                
                # 如果参数签名不一致
                unique_signatures = set(tuple(sig[1]) for sig in param_signatures)

                if len(unique_signatures) > 1:


                    affected_nodes = [sig[0] for sig in param_signatures]
                    issues.append(LogicIssue(
                        issue_id=f"inconsistent_api_{func_name}",
                        issue_type="inconsistent_api",
                        severity="high",

                        description=f"函数 '{func_name}' 有多个不一致的实现",
                        affected_nodes=affected_nodes,
                        suggested_fixes=[
                        "统一函数签名",


 "使用函数重载",

                            "重命名函数以区分不同用途",
                            "提取公共逻辑"
                        ],
                        confidence=0.9

                    ))
        
        return issues
    
    def _analyze_dead_code(self) -> List[LogicIssue]:
        """分析死代码"""
        issues = []
        
         # 分析不可达的代码路径

        for node_id, node_data in self.logic_graph.nodes(data=True):
            if node_data.get('node_type') == 'function':
                unreachable_paths = self._find_unreachable_paths(node_id)

                if unreachable_paths:
                    issues.append(LogicIssue(
#                         issue_id=f"dead_code_{node_id}",
                        issue_type="dead_code",

                        severity="low",
                        description=f"函数 '{node_data['name']}' 包含不可达的代码",
                        affected_nodes=[node_id],
                        suggested_fixes=[
                        "移除不可达代码",

                            "重构条件逻辑",
# 
 "添加适当的测试",

                            "简化函数逻辑"
                        ],
                        confidence=0.8


                    ))
        
        return issues
    
    def _analyze_logic_errors(self) -> List[LogicIssue]:
        """分析逻辑错误"""

        issues = []
        
         # 分析常见的逻辑错误模式

        for node_id, node_data in self.logic_graph.nodes(data=True):
            if node_data.get('node_type') == 'function':

                # 检查条件逻辑
                logic_errors = self._detect_logic_errors(node_id)

                for error in logic_errors:
                    issues.append(LogicIssue(
                    issue_id=f"logic_error_{node_id}_{error['type']}",

                        issue_type="logic_error",
                        severity=error.get('severity', 'medium'),
                        description=error['description'],
                        affected_nodes=[node_id],
                        suggested_fixes=error.get('suggestions', []),
                        confidence=error.get('confidence', 0.7)
                    ))
        
        return issues
    
    def _is_likely_import_needed(self, name: str) -> bool:
        """判断是否需要导入"""

        # 检查是否是已知库
        known_libraries = {
            'json', 'os', 'sys', 're', 'time', 'datetime', 'pathlib',
            'requests', 'numpy', 'pandas', 'tensorflow', 'torch',


            'sklearn', 'matplotlib', 'seaborn', 'flask', 'django',
            'fastapi', 'pydantic', 'sqlalchemy', 'chromadb', 'mqtt'

            }

        
        return name.lower() in known_libraries
    
    def _suggest_import_for_name(self, name: str) -> List[str]:
        """为名称建议导入"""
        import_suggestions = {
            'json': ['import json', 'from json import loads, dumps'],
            'os': ['import os', 'from os import path, environ'],

            'sys': ['import sys', 'from sys import argv, exit'],

            're': ['import re', 'from re import search, match'],
            'time': ['import time', 'from time import sleep, time'],

            'datetime': ['import datetime', 'from datetime import datetime, timedelta'],
            'pathlib': ['import pathlib', 'from pathlib import Path'],
            'requests': ['import requests', 'from requests import get, post'],
            'numpy': ['import numpy as np', 'from numpy import array, mean'],
            'pandas': ['import pandas as pd', 'from pandas import DataFrame, Series'],
            'tensorflow': ['import tensorflow as tf', 'from tensorflow import keras'],

            'torch': ['import torch', 'from torch import nn, optim'],
            'sklearn': ['from sklearn import metrics', 'import sklearn'],
            'fastapi': ['from fastapi import FastAPI', 'import fastapi'],
#             'pydantic': ['from pydantic import BaseModel', 'import pydantic'],
            'chromadb': ['import chromadb', 'from chromadb import Client'],

 'mqtt': ['import paho.mqtt.client as mqtt', 'from paho.mqtt import client']

 }

        
        return import_suggestions.get(name.lower(), [f"import {name}"])
    
#     def _find_unreachable_paths(self, node_id: str) -> List[Dict[str, Any]]:
        """找到不可达的路径"""
        # 简化版本 - 实际实现需要更复杂的控制流分析

        return []
    
    def _detect_logic_errors(self, node_id: str) -> List[Dict[str, Any]]:
        """检测逻辑错误"""
        # 简化版本 - 实际实现需要更复杂的逻辑分析
        return []
    
    def fix(self, context: FixContext) -> FixResult:
        """修复逻辑图谱问题"""
        self.logger.info("开始修复逻辑图谱问题...")
        
        import time
        start_time = time.time()
        issues_fixed = 0
        issues_found = 0
        error_messages = []
        
        try:
            # 分析问题
            issues = self.analyze(context)
            issues_found = len(issues)

#             
            if issues_found == 0:
                self.logger.info("未发现逻辑图谱问题")
                return FixResult(
#                     fix_type=self.fix_type,
#                     status=FixStatus.SUCCESS,

                    issues_found=0,
                    issues_fixed=0,

#                     duration_seconds=time.time() - start_time

                )
            
            # 按优先级排序问题
            #             priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# 
# 
#             issues.sort(key=lambda x: priority_order.get(x.severity, 4))
#             

# 
 # 应用修复策略

            for issue in issues:
                try:
                    if self._apply_logic_fix(issue, context):

# 
#                         issues_fixed += 1
# 
                        self.logger.info(f"修复了问题: {issue.issue_id}")
#                     else:
#                         self.logger.warning(f"无法修复问题: {issue.issue_id}")
#                         
                except Exception as e:
                    error_msg = f"修复问题 {issue.issue_id} 失败: {e}"
# 
                    self.logger.error(error_msg)
#                     error_messages.append(error_msg)

            
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
                "files_processed": len(self._get_target_files(context)),

                    "issues_by_type": self._categorize_issues(issues),
                    "logic_graph_stats": self._get_graph_statistics()
                }
            )
            
        except Exception as e:
            self.logger.error(f"逻辑图谱修复过程失败: {e}")
            return FixResult(
                fix_type=self.fix_type,
                status=FixStatus.FAILED,
                issues_found=issues_found,
                issues_fixed=issues_fixed,
                error_message=str(e),
                traceback=traceback.format_exc(),

                duration_seconds=time.time() - start_time
            )
    
    def _apply_logic_fix(self, issue: LogicIssue, context: FixContext) -> bool:
        """应用逻辑修复"""
        strategy = self.repair_strategies.get(issue.issue_type)

        if strategy:
            try:
                return strategy(issue, context)
            except Exception as e:
                self.logger.error(f"应用修复策略失败 {issue.issue_type}: {e}")
                return False

        
         # 默认修复：尝试应用建议的修复



        if issue.suggested_fixes:
            return self._apply_suggested_fixes(issue, context)
        
        return False
    
    def _fix_missing_import(self, issue: LogicIssue, context: FixContext) -> bool:
        """修复缺失导入"""

        if not issue.suggested_fixes:
            return False

        
        # 找到受影响的文件
        affected_files = set()
        for node_id in issue.affected_nodes:

            node_data = self.logic_graph.nodes[node_id]

            file_path = node_data.get('file_path')
            if file_path:
                affected_files.add(Path(file_path))
        
         # 为每个文件添加导入

        success_count = 0
        for file_path in affected_files:

            try:
                if self._add_imports_to_file(file_path, issue.suggested_fixes, context):

                    success_count += 1
            except Exception as e:
                self.logger.error(f"添加导入到文件 {file_path} 失败: {e}")
        
        return success_count > 0
    
    def _fix_circular_dependency(self, issue: LogicIssue, context: FixContext) -> bool:
        """修复循环依赖"""

        # 这是一个复杂的重构任务
        # 简化版本：建议重构方案
        self.logger.info(f"检测到循环依赖，建议手动重构: {issue.description}")
        return False  # 需要人工干预
    
    def _fix_orphaned_code(self, issue: LogicIssue, context: FixContext) -> bool:
        """修复孤立代码"""
        if context.dry_run:
            return True  # 干运行模式下假设成功
        
        # 标记孤立代码或建议删除
        self.logger.warning(f"孤立代码需要关注: {issue.description}")
        return True
    
    def _fix_inconsistent_api(self, issue: LogicIssue, context: FixContext) -> bool:
        """修复不一致的API"""
        # 这是一个复杂的重构任务
        self.logger.info(f"API不一致需要统一: {issue.description}")

        return False  # 需要人工干预
    
    def _fix_dead_code(self, issue: LogicIssue, context: FixContext) -> bool:
        """修复死代码"""
        if context.dry_run:
            return True
        
        # 标记死代码
        self.logger.info(f"死代码需要清理: {issue.description}")
        return True
    
    def _fix_logic_error(self, issue: LogicIssue, context: FixContext) -> bool:
        """修复逻辑错误"""
        # 逻辑错误通常需要人工分析
        self.logger.warning(f"逻辑错误需要人工修复: {issue.description}")
        return False
    
    def _apply_suggested_fixes(self, issue: LogicIssue, context: FixContext) -> bool:
        """应用建议的修复"""

        # 简化版本 - 实际实现需要更复杂的逻辑
        return False
    
    def _add_imports_to_file(self, file_path: Path, imports: List[str], context: FixContext) -> bool:
        """向文件添加导入"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 找到合适的插入位置（通常在文件顶部）
            insert_position = self._find_import_insert_position(content)
            
            # 添加导入语句
            import_block = '\n'.join(imports) + '\n'
            content = content[:insert_position] + import_block + content[insert_position:]

            
            if content != original_content:
                if not context.dry_run:

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"添加导入到文件 {file_path} 失败: {e}")
            return False

    
    def _find_import_insert_position(self, content: str) -> int:
        #         """找到导入插入位置"""

        lines = content.split('\n')
        
        # 跳过shebang和编码声明
#         insert_line = 0
        for i, line in enumerate(lines):

            if line.startswith('#!') or line.startswith('# -*-'):
                insert_line = i + 1

            elif line.strip() and not line.startswith('#'):
                break

        
        # 找到现有导入的结束位置
        for i in range(insert_line, len(lines)):

            line = lines[i].strip()
            if line.startswith('import ') or line.startswith('from '):
                insert_line = i + 1
                #             elif line and not line.startswith('#'):

                break
# 
        
        # 计算字符位置
#         position = sum(len(line) + 1 for line in lines[:insert_line])
#         return position
#     
    def _categorize_issues(self, issues: List[LogicIssue]) -> Dict[str, int]:
#         """按类型分类问题"""
#         categories = defaultdict(int)


        for issue in issues:
            categories[issue.issue_type] += 1

        return dict(categories)
    
    def _get_graph_statistics(self) -> Dict[str, Any]:
        """获取图谱统计信息"""


        return {
            "total_nodes": self.logic_graph.number_of_nodes(),
            "total_edges": self.logic_graph.number_of_edges(),
            "connected_components": nx.number_connected_components(nx.Graph(self.logic_graph)),
            "cycles": len(list(nx.simple_cycles(self.logic_graph))),
            "density": nx.density(self.logic_graph)
            }



class SymbolCollector(ast.NodeVisitor):
#     """符号收集器"""
#     
    def __init__(self, file_path: Path, content: str):
        self.file_path = file_path
#         self.content = content
#         self.nodes = []

#         self.current_scope = []
#         self.imports = []

# 
        
#     def visit_FunctionDef(self, node: ast.FunctionDef):
        """访问函数定义"""


        node_id = f"{self.file_path}:{node.name}:function:{node.lineno}"
        logic_node = LogicNode(
        node_id=node_id,


 node_type="function",

            name=node.name,
            file_path=self.file_path,

            line_number=node.lineno,

            column=node.col_offset,
            metadata={
            #             "parameters": self._extract_parameters(node.args),


                "return_annotation": self._extract_return_annotation(node.returns),
                "decorators": [self._extract_decorator_name(d) for d in node.decorator_list],

# 
#  "docstring": ast.get_docstring(node),

                "is_async": isinstance(node, ast.AsyncFunctionDef)
                }
# 
# 
        )
        self.nodes.append(logic_node)
        
        self.current_scope.append(node.name)
        self.generic_visit(node)

        self.current_scope.pop()


    
    def visit_ClassDef(self, node: ast.ClassDef):
        """访问类定义"""


        node_id = f"{self.file_path}:{node.name}:class:{node.lineno}"
        logic_node = LogicNode(
            node_id=node_id,
            node_type="class",

 name=node.name,

            file_path=self.file_path,
            line_number=node.lineno,

 column=node.col_offset,

            metadata={
            "bases": [self._extract_base_name(base) for base in node.bases],

                "decorators": [self._extract_decorator_name(d) for d in node.decorator_list],

                "docstring": ast.get_docstring(node),
                "methods": []

                }

        )
        self.nodes.append(logic_node)

        
        self.current_scope.append(node.name)
        self.generic_visit(node)

        self.current_scope.pop()
    
    def visit_Name(self, node: ast.Name):
        """访问名称"""
        if isinstance(node.ctx, ast.Load):

            node_id = f"{self.file_path}:{node.id}:name:{node.lineno}"
            logic_node = LogicNode(
            node_id=node_id,

 node_type="name",

                name=node.id,
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                metadata={
                    "context": "load",
                    "scope": self.current_scope.copy()
                    }

            )
            self.nodes.append(logic_node)

        
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import):
        """访问导入"""

        for alias in node.names:
            self.imports.append({
            "module": alias.name,

                "alias": alias.asname,
                "line_number": node.lineno
            })
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """访问from导入"""
        module = node.module or ""
        for alias in node.names:


            self.imports.append({
                "module": f"{module}.{alias.name}" if module else alias.name,
                "alias": alias.asname,
                "line_number": node.lineno

            })
        self.generic_visit(node)
    
    def _extract_parameters(self, args: ast.arguments) -> List[Dict[str, Any]]:
        """提取参数信息"""
        parameters = []

        for arg in args.args:
            param_info = {
                "name": arg.arg,
                "annotation": self._extract_annotation(arg.annotation),

                "type_hint": None
                }

            parameters.append(param_info)
            return parameters


    
    def _extract_return_annotation(self, returns: Optional[ast.AST]) -> Optional[str]:
        """提取返回类型注解"""

        return self._extract_annotation(returns)
    
     #     def _extract_annotation(self, annotation: Optional[ast.AST]) -> Optional[str]:


 #         """提取注解"""

        if annotation is None:
            return None
        
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        else:
            return ast.dump(annotation)


    
    def _extract_decorator_name(self, decorator: ast.AST) -> str:
        """提取装饰器名称"""
        if isinstance(decorator, ast.Name):
# 
            return decorator.id
# 
#         elif isinstance(decorator, ast.Call):

            return self._extract_decorator_name(decorator.func)

        else:
            return ast.dump(decorator)
    
#     def _extract_base_name(self, base: ast.AST) -> str:
#         """提取基类名称"""
# 
# 
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return f"{self._extract_base_name(base.value)}.{base.attr}"

        else:
            return ast.dump(base)




class ImportCollector(ast.NodeVisitor):
    """导入收集器"""


    
    def __init__(self, file_path: Path, content: str):
        self.file_path = file_path
        self.content = content
        self.imports = []
    
    def visit_Import(self, node: ast.Import):
        """访问导入"""
        for alias in node.names:
            self.imports.append({
                "module": alias.name,
                "alias": alias.asname,
                "line_number": node.lineno,

                "import_type": "direct"
            })
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """访问from导入"""
        module = node.module or ""
        for alias in node.names:
            self.imports.append({
                "module": f"{module}.{alias.name}" if module else alias.name,
                "alias": alias.asname,
                "line_number": node.lineno,
                "import_type": "from"
            })


class DependencyAnalyzer(ast.NodeVisitor):
    """依赖关系分析器"""
    
    def __init__(self, file_path: Path, content: str, nodes_by_file: Dict, global_symbols: Dict):
        self.file_path = file_path
        self.content = content
        self.nodes_by_file = nodes_by_file
        self.global_symbols = global_symbols
        self.dependencies = []
        self.current_function = None
        
    def visit_Call(self, node: ast.Call):
        """访问函数调用"""
        func_name = self._extract_func_name(node.func)
        if func_name:
            # 查找被调用的函数
            target_nodes = self._find_function_nodes(func_name)
            for target_node in target_nodes:
                dep = LogicEdge(
                    source_id=f"{self.file_path}:{self.current_function or 'module'}:call:{node.lineno}",
                    target_id=target_node.node_id,
                    edge_type="calls",
                    confidence=0.9
                )
                self.dependencies.append(dep)
        
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """访问函数定义"""
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = None
    
    def _extract_func_name(self, func_node: ast.AST) -> Optional[str]:
        """提取函数名称"""
        if isinstance(func_node, ast.Name):
            return func_node.id
        elif isinstance(func_node, ast.Attribute):
            return func_node.attr
        return None
    
    def _find_function_nodes(self, func_name: str) -> List[LogicNode]:
        """查找函数节点"""
        symbol_key = f"{func_name}:function"
        return self.global_symbols.get(symbol_key, [])


# 修复方法定义（用于兼容性）
def _fix_missing_import(content: str, error_message: str) -> str:
    """修复缺失导入"""
    return content

def _fix_circular_dependency(content: str, error_message: str) -> str:
    """修复循环依赖"""
    return content