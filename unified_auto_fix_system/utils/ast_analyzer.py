"""
AST分析器 - 高级AST分析和问题检测
"""

import ast
import builtins
import inspect
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass

from ..core.fix_types import FixType, FixStatus
from ..core.fix_result import FixContext


@dataclass
class ASTIssue:
    """AST分析问题"""



    file_path: Path
    line_number: int
    column: int
    issue_type: str
    description: str
    node_type: str
    code_snippet: str = ""
    suggested_fix: str = ""
    severity: str = "error"


class ASTAnalyzer:
    """高级AST分析器"""
    
    def __init__(self):
        self.issues = []
        self.defined_names = set()
        self.imported_names = set()
        self.builtin_names = set(dir(builtins))
        self.class_methods = {}
        self.function_params = {}
        self.decorator_info = {}
    
    def analyze_advanced(self, context: FixContext) -> Dict[str, List[ASTIssue]]:
        """执行高级AST分析"""
        self.issues = []
        target_files = self._get_target_files(context)
        
        all_issues = {
            "undefined_variables": [],
            "undefined_functions": [],
            "undefined_classes": [],
            "decorator_issues": [],
            "class_inheritance_issues": [],
            "parameter_mismatches": [],
            "return_type_issues": [],
            "import_issues": [],
            "scope_issues": [],
            "type_annotation_issues": [],
            "async_await_issues": [],
            "context_manager_issues": [],
            "descriptor_issues": [],
            "metaclass_issues": []

        }
        
        for file_path in target_files:
            try:
                file_issues = self._analyze_file_advanced(file_path)
                for issue_type, issues in file_issues.items():
                    all_issues[issue_type].extend(issues)
            except Exception as e:
                print(f"AST分析文件失败 {file_path}: {e}")
        
        return all_issues
    
    def _analyze_file_advanced(self, file_path: Path) -> Dict[str, List[ASTIssue]]:
        """分析单个文件的高级AST问题"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            # 重置分析状态
            self.defined_names = set()
            self.imported_names = set()
            self.class_methods = {}
            self.function_params = {}
            self.decorator_info = {}
            
            # 第一次遍历：收集定义信息
            self._collect_definitions(tree, file_path)
            
             # 第二次遍历：分析问题

            file_issues = {
                "undefined_variables": [],
                "undefined_functions": [],
                "undefined_classes": [],
                "decorator_issues": [],
                "class_inheritance_issues": [],
                "parameter_mismatches": [],
                "return_type_issues": [],
                "import_issues": [],
                "scope_issues": [],
                "type_annotation_issues": [],
                "async_await_issues": [],
                "context_manager_issues": [],
                "descriptor_issues": [],

 "metaclass_issues": []

            }
            
            self._analyze_undefined_names(tree, file_path, file_issues)
            self._analyze_decorators(tree, file_path, file_issues)
            self._analyze_class_inheritance(tree, file_path, file_issues)
            self._analyze_parameters(tree, file_path, file_issues)
            self._analyze_return_types(tree, file_path, file_issues)
            self._analyze_imports(tree, file_path, file_issues)
            self._analyze_scopes(tree, file_path, file_issues)
            self._analyze_type_annotations(tree, file_path, file_issues)
            self._analyze_async_await(tree, file_path, file_issues)
            self._analyze_context_managers(tree, file_path, file_issues)
            self._analyze_descriptors(tree, file_path, file_issues)
            self._analyze_metaclasses(tree, file_path, file_issues)
            
            return file_issues
            
        except SyntaxError as e:
            return {
                "syntax_errors": [ASTIssue(
#                     file_path=file_path,
#                     line_number=e.lineno or 0,
#                     column=e.offset or 0,
#                     issue_type="syntax_error",
#                     description=f"语法错误: {e}",
# 
#  node_type="module",

 severity="error"

                )]
            }
        except Exception as e:
            print(f"AST分析失败 {file_path}: {e}")

            return {}
    
    def _collect_definitions(self, tree: ast.AST, file_path: Path):
        """收集定义信息"""
        for node in ast.walk(tree):

            if isinstance(node, ast.FunctionDef):
                self.defined_names.add(node.name)
                self.function_params[node.name] = [arg.arg for arg in node.args.args]
            elif isinstance(node, ast.ClassDef):
                self.defined_names.add(node.name)
                self.class_methods[node.name] = []
                for item in node.body:

                    if isinstance(item, ast.FunctionDef):
                        self.class_methods[node.name].append(item.name)

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    if '.' in name:
                        name = name.split('.')[0]

                    self.imported_names.add(name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:


                    self.imported_names.add(node.module)
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name


                    self.imported_names.add(name)
    
    def _analyze_undefined_names(self, tree: ast.AST, file_path: Path, issues: Dict[str, List[ASTIssue]]):
        """分析未定义的名称"""

        for node in ast.walk(tree):
#             if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
    #                 name = node.id

                if (name not in self.defined_names and 
                #                     name not in self.imported_names and 

#                     name not in self.builtin_names and
                    not name.startswith('_')):  # 忽略私有名称
#                     
                    issue = ASTIssue(
#                         file_path=file_path,
#                         line_number=node.lineno,
# 
#                         column=node.col_offset,
                        issue_type="undefined_variable",

                        description=f"未定义的变量: {name}",
                        node_type="Name",
                        code_snippet=name,
                        suggested_fix=f"# 需要定义 {name} 或导入包含它的模块"
                    )
                    
                    # 分类：变量、函数、类
                    if self._looks_like_function_name(name):
                        issues["undefined_functions"].append(issue)
                    elif self._looks_like_class_name(name):
                        issues["undefined_classes"].append(issue)
                    else:
                        issues["undefined_variables"].append(issue)
#     
#     def _analyze_decorators(self, tree: ast.AST, file_path: Path, issues: Dict[str, List[ASTIssue]]):

#         """分析装饰器问题"""
#         for node in ast.walk(tree):

#             if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.decorator_list:
#                 for decorator in node.decorator_list:
#                     decorator_name = self._get_decorator_name(decorator)
#                     if decorator_name and decorator_name not in self.defined_names and decorator_name not in self.imported_names:
# 
                        issues["decorator_issues"].append(ASTIssue(
#                         file_path=file_path,
# 
#                             line_number=decorator.lineno,
                            column=decorator.col_offset,

                            issue_type="undefined_decorator",
                            description=f"未定义的装饰器: {decorator_name}",

                            node_type="decorator",
                            code_snippet=decorator_name,
                            suggested_fix=f"# 需要定义或导入装饰器: {decorator_name}"
                        ))
                    
                     # 检查装饰器参数

#                     if isinstance(decorator, ast.Call):
#                         self._check_decorator_call(decorator, file_path, issues)
#     
#     def _analyze_class_inheritance(self, tree: ast.AST, file_path: Path, issues: Dict[str, List[ASTIssue]]):

#         """分析类继承问题"""
#         for node in ast.walk(tree):

#             if isinstance(node, ast.ClassDef) and node.bases:
#                 for base in node.bases:
# 
#                     if isinstance(base, ast.Name):
#                         base_name = base.id

                        if base_name not in self.defined_names and base_name not in self.imported_names:
                            issues["class_inheritance_issues"].append(ASTIssue(
                            file_path=file_path,

                                line_number=base.lineno,
                                column=base.col_offset,
                                issue_type="undefined_base_class",
                                description=f"未定义的基类: {base_name}",
                                node_type="Name",

#                                 code_snippet=base_name,
#                                 suggested_fix=f"# 需要定义或导入基类: {base_name}"
                            ))
#     
#     def _analyze_parameters(self, tree: ast.AST, file_path: Path, issues: Dict[str, List[ASTIssue]]):
    #         """分析参数问题"""

        for node in ast.walk(tree):
#             if isinstance(node, ast.Call):
# 
#                 func_name = self._get_function_name(node.func)
#                 if func_name and func_name in self.function_params:
# 
#                     expected_params = len(self.function_params[func_name])
#                     actual_args = len(node.args)
#                     
#                     if actual_args != expected_params:
                        issues["parameter_mismatches"].append(ASTIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            issue_type="parameter_count_mismatch",
                            description=f"函数 {func_name} 参数数量不匹配: 期望 {expected_params}, 实际 {actual_args}",
                            node_type="Call",

                            code_snippet=func_name,
                            suggested_fix=f"# 检查函数 {func_name} 的参数定义"
                        ))
    
    def _analyze_return_types(self, tree: ast.AST, file_path: Path, issues: Dict[str, List[ASTIssue]]):
#         """分析返回类型问题"""
#         for node in ast.walk(tree):
    #             if isinstance(node, ast.FunctionDef):

                # 检查是否有返回语句
                #                 has_return = any(isinstance(n, ast.Return) for n in ast.walk(node))

#                 
                 # 检查函数名是否暗示返回类型

                if has_return and self._function_name_suggests_return_type(node.name):
                    # 这里可以添加更复杂的返回类型分析

                    pass
    
    def _analyze_imports(self, tree: ast.AST, file_path: Path, issues: Dict[str, List[ASTIssue]]):
        """分析导入问题"""

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                # 检查循环导入

                if self._detect_circular_import(node, file_path):
                    issues["import_issues"].append(ASTIssue(
                    file_path=file_path,

#                         line_number=node.lineno,
#                         column=node.col_offset,

#                         issue_type="circular_import",
#                         description="检测到可能的循环导入",
#                         node_type="Import",
#                         suggested_fix="# 检查并重构导入结构以避免循环依赖"
                    ))
    
    def _analyze_scopes(self, tree: ast.AST, file_path: Path, issues: Dict[str, List[ASTIssue]]):
        """分析作用域问题"""
        # 实现作用域分析逻辑

#         pass
#     
#     def _analyze_type_annotations(self, tree: ast.AST, file_path: Path, issues: Dict[str, List[ASTIssue]]):
#         """分析类型注解问题"""
        for node in ast.walk(tree):
# 
#             if isinstance(node, ast.FunctionDef) and node.returns:
                # 检查返回类型注解
                #                 return_type = self._get_annotation_name(node.returns)

#                 if return_type and return_type not in self.defined_names and return_type not in self.imported_names:
                    issues["type_annotation_issues"].append(ASTIssue(
#                         file_path=file_path,
#                         line_number=node.returns.lineno,
                        column=node.returns.col_offset,

                        issue_type="undefined_return_type",
                        description=f"未定义的返回类型: {return_type}",
#                         node_type="annotation",
                        code_snippet=return_type,
                        #                         suggested_fix=f"# 需要定义或导入返回类型: {return_type}"

                    ))
#     
#     def _analyze_async_await(self, tree: ast.AST, file_path: Path, issues: Dict[str, List[ASTIssue]]):
#         """分析异步问题"""
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
# 

                # 检查是否使用了await
                #                 has_await = any(isinstance(n, ast.Await) for n in ast.walk(node))

#                 if not has_await:
                    issues["async_await_issues"].append(ASTIssue(
#                         file_path=file_path,
#                         line_number=node.lineno,
                        column=node.col_offset,

                        issue_type="async_function_without_await",
                        description=f"异步函数 {node.name} 没有使用 await",

                        node_type="AsyncFunctionDef",
#                         code_snippet=node.name,
                        suggested_fix=f"# 考虑将 {node.name} 改为普通函数或添加 await 调用"
                    ))
            elif isinstance(node, ast.Await):
                # 检查是否在异步函数中
#                 in_async_func = False
# 
#                 parent = node
                while parent:
                    if isinstance(parent, ast.AsyncFunctionDef):

#                         in_async_func = True
                        break
#                     parent = getattr(parent, 'parent', None)
#                 

                if not in_async_func:
                    issues["async_await_issues"].append(ASTIssue(
                        file_path=file_path,
                        line_number=node.lineno,

                        column=node.col_offset,
                        issue_type="await_outside_async_function",
                        description="await 在异步函数外使用",

#                         node_type="Await",
# 
#  suggested_fix="# await 只能在异步函数中使用"

                    ))
    
#     def _analyze_context_managers(self, tree: ast.AST, file_path: Path, issues: Dict[str, List[ASTIssue]]):
        """分析上下文管理器问题"""
        for node in ast.walk(tree):
# 
            if isinstance(node, ast.With):

                # 检查上下文管理器是否有适当的 __enter__ 和 __exit__ 方法
                for item in node.items:
                    if isinstance(item.context_expr, ast.Call):

                        func_name = self._get_function_name(item.context_expr.func)
                        if func_name and not self._has_context_manager_methods(func_name):
                            issues["context_manager_issues"].append(ASTIssue(
                            file_path=file_path,

 line_number=item.context_expr.lineno,

                                column=item.context_expr.col_offset,
                                issue_type="invalid_context_manager",

#                                 description=f"对象 {func_name} 可能不是有效的上下文管理器",
#                                 node_type="Call",

#                                 code_snippet=func_name,

#                                 suggested_fix=f"# 确保 {func_name} 实现了 __enter__ 和 __exit__ 方法"
                            ))
                            #     

#     def _analyze_descriptors(self, tree: ast.AST, file_path: Path, issues: Dict[str, List[ASTIssue]]):
        """分析描述符问题"""

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 检查是否有描述符方法

                descriptor_methods = ['__get__', '__set__', '__delete__']
                has_descriptor_methods = any(
                    method in [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
#                     for method in descriptor_methods
                )
#                 
                if has_descriptor_methods:
                    # 检查描述符方法的正确性
#                     for method_name in descriptor_methods:
    #                         if method_name in [m.name for m in node.body if isinstance(m, ast.FunctionDef)]:


#                             method_node = next(m for m in node.body if isinstance(m, ast.FunctionDef) and m.name == method_name)
                            self._check_descriptor_method(method_node, file_path, issues)
#     
#     def _analyze_metaclasses(self, tree: ast.AST, file_path: Path, issues: Dict[str, List[ASTIssue]]):
#         """分析元类问题"""
# 
        for node in ast.walk(tree):
#             if isinstance(node, ast.ClassDef):
# 
                # 检查元类定义
                for keyword in node.keywords:

                    if keyword.arg == 'metaclass':
                        metaclass_name = self._get_metaclass_name(keyword.value)
                        if metaclass_name and metaclass_name not in self.defined_names:

                            issues["metaclass_issues"].append(ASTIssue(
                            file_path=file_path,

 line_number=keyword.lineno,

                                column=keyword.col_offset,
                                issue_type="undefined_metaclass",
                                description=f"未定义的元类: {metaclass_name}",
                                node_type="keyword",

                                code_snippet=metaclass_name,
                                suggested_fix=f"# 需要定义元类: {metaclass_name}"


                            ))
    
     # 辅助方法

    def _get_target_files(self, context: FixContext) -> List[Path]:
        """获取目标文件"""
        if context.target_path:
            if context.target_path.is_file():


                return [context.target_path]
            elif context.target_path.is_dir():
                return list(context.target_path.rglob("*.py"))
        
         # 默认获取所有Python文件

        return list(context.project_root.rglob("*.py"))
    
    def _looks_like_function_name(self, name: str) -> bool:
        """判断名称是否像函数名"""

        return name.islower() and '_' in name or name.islower()
    
    def _looks_like_class_name(self, name: str) -> bool:
        """判断名称是否像类名"""
        return name[0].isupper() and '_' not in name

    
    def _get_function_name(self, node: ast.AST) -> Optional[str]:
        """获取函数名"""
        if isinstance(node, ast.Name):
            return node.id

        elif isinstance(node, ast.Attribute):
            return node.attr
        return None
    
    def _get_decorator_name(self, decorator: ast.AST) -> Optional[str]:
        """获取装饰器名称"""


        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            return self._get_function_name(decorator.func)
            return None

    
    def _get_annotation_name(self, annotation: ast.AST) -> Optional[str]:
        """获取注解名称"""
        if isinstance(annotation, ast.Name):
            return annotation.id
# 
#         elif isinstance(annotation, ast.Constant):
    #             return str(annotation.value)

#         return None
#     
#     def _get_metaclass_name(self, node: ast.AST) -> Optional[str]:
    #         """获取元类名称"""

 #         if isinstance(node, ast.Name):

            return node.id

        return None
    
    def _function_name_suggests_return_type(self, name: str) -> bool:
        """函数名是否暗示返回类型"""
        return_patterns = ['get_', 'fetch_', 'find_', 'create_', 'make_']


        return any(name.startswith(pattern) for pattern in return_patterns)
    
#     def _detect_circular_import(self, node: ast.AST, file_path: Path) -> bool:
    #         """检测循环导入"""

        # 简化的循环导入检测
        # 实际实现需要更复杂的逻辑
        #         return False

#     
#     def _has_context_manager_methods(self, class_name: str) -> bool:
# 
#         """检查是否有上下文管理器方法"""
        # 这里应该检查类的实际定义
# 
        # 简化版本
#         return True
#     
#     def _check_decorator_call(self, decorator: ast.Call, file_path: Path, issues: Dict[str, List[ASTIssue]]):
        """检查装饰器调用"""

        # 检查装饰器参数是否正确
        pass
    
    def _check_descriptor_method(self, method_node: ast.FunctionDef, file_path: Path, issues: Dict[str, List[ASTIssue]]):
        """检查描述符方法"""
        # 检查描述符方法的参数签名
        expected_params = {
            '__get__': ['self', 'instance', 'owner'],
            '__set__': ['self', 'instance', 'value'],
            '__delete__': ['self', 'instance']
        }
        
        if method_node.name in expected_params:
            expected_args = expected_params[method_node.name]
            actual_args = [arg.arg for arg in method_node.args.args]
            
            if actual_args != expected_args:
                issues["descriptor_issues"].append(ASTIssue(
                    file_path=file_path,
                    line_number=method_node.lineno,
                    column=method_node.col_offset,
                    issue_type="incorrect_descriptor_signature",
                    description=f"描述符方法 {method_node.name} 参数签名不正确",
                    node_type="FunctionDef",
                    code_snippet=method_node.name,
                    suggested_fix=f"# 描述符方法 {method_node.name} 应该有参数: {', '.join(expected_args)}"
                ))