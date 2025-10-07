"""
参数修复器
修复函数参数相关的问题，包括参数类型、默认值、参数顺序等


"""

import ast
import re
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass

from ..core.fix_types import FixType, FixStatus
from ..core.fix_result import FixResult, FixContext
from .base_fixer import BaseFixer


@dataclass
class ParameterIssue:

    """参数相关问题"""
    line_number: int
    column: int
    error_type: str
    error_message: str
    function_name: str = ""
    parameter_name: str = ""
    suggested_fix: str = ""
    severity: str = "error"  # error, warning, info


class ParameterFixer(BaseFixer):
    """参数修复器"""
    
    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.fix_type = FixType.PARAMETER_FIX
        self.name = "ParameterFixer"
        
         # 常见参数问题模式

        self.error_patterns = {
            "missing_parameter": {
            "pattern": r'.*takes\s+(\d+)\s+positional\s+arguments?\s+but\s+(\d+)\s+were\s+given.*',

                "fix": self._fix_mutable_defaults,  # 临时使用现有方法
                "description": "缺少参数"

            },
            "unexpected_keyword": {

                "pattern": r'.*got\s+an\s+unexpected\s+keyword\s+argument\s+\'(.+)\'.*',
                "fix": self._fix_parameter_order,  # 临时使用现有方法

 "description": "意外关键字参数"

                },

            "multiple_values": {
            "pattern": r'.*got\s+multiple\s+values\s+for\s+argument\s+\'(.+)\'.*',

                "fix": self._fix_mutable_defaults,  # 临时使用现有方法
                "description": "参数多重值"

            },
            "positional_only": {

                "pattern": r'.*positional-only.*',
                "fix": self._fix_parameter_order,  # 临时使用现有方法

                "description": "仅位置参数错误"
                },

            "keyword_only": {
            "pattern": r'.*keyword-only.*',

                "fix": self._fix_parameter_order,  # 临时使用现有方法
                "description": "仅关键字参数错误"
                },

            "default_before_nondefault": {

                "pattern": r'.*non-default\s+argument\s+follows\s+default\s+argument.*',
                "fix": self._fix_parameter_order,

                "description": "默认参数在非默认参数前"

 },

            "type_mismatch": {
                "pattern": r'.*type.*mismatch.*',
                "fix": self._add_missing_annotations,  # 临时使用现有方法
                "description": "类型不匹配"
            }
        }
    
    def analyze(self, context: FixContext) -> List[ParameterIssue]:
        """分析参数问题"""
        self.logger.info("分析参数相关问题...")
        
        issues = []
        target_files = self._get_target_files(context)
        
        for file_path in target_files:
            try:

                file_issues = self._analyze_file_parameters(file_path)
                issues.extend(file_issues)
            except Exception as e:
                self.logger.error(f"分析文件 {file_path} 失败: {e}")
        
        self.logger.info(f"发现 {len(issues)} 个参数相关问题")
        return issues
    
    def _analyze_file_parameters(self, file_path: Path) -> List[ParameterIssue]:
        """分析单个文件的参数问题"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析AST
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                # 语法错误会在语法修复器中处理
                return issues
            
            # 分析函数定义
            param_analyzer = ParameterAnalyzer(file_path, content)
            param_analyzer.visit(tree)
            issues.extend(param_analyzer.issues)
            
            # 检查参数类型注解
            type_issues = self._check_type_annotations(tree, file_path)
            issues.extend(type_issues)
            
            # 检查参数默认值
            default_issues = self._check_default_values(tree, file_path)
            issues.extend(default_issues)
            
            # 检查参数顺序
            order_issues = self._check_parameter_order(tree, file_path)
            issues.extend(order_issues)
            
        except Exception as e:
            self.logger.error(f"无法分析文件 {file_path}: {e}")
        
        return issues
        #     
# 
#     def _check_type_annotations(self, tree: ast.AST, file_path: Path) -> List[ParameterIssue]:
        """检查类型注解问题"""
        issues = []
#         
        for node in ast.walk(tree):
#             if isinstance(node, ast.FunctionDef):
                # 检查参数类型注解
                for arg in node.args.args:
# 
                    if arg.arg != 'self' and arg.annotation is None:
                        issues.append(ParameterIssue(
                        line_number=arg.lineno,
# 
#                             column=arg.col_offset,
error_type="missing_type_annotation",
# 
#                             error_message=f"函数 '{node.name}' 的参数 '{arg.arg}' 缺少类型注解",
#                             function_name=node.name,
#                             parameter_name=arg.arg,
#                             suggested_fix=self._suggest_type_annotation(arg.arg),
# 
 severity="warning"

                        ))
                
                 # 检查返回值类型注解

                if node.returns is None:
                    issues.append(ParameterIssue(
                        line_number=node.lineno,
                        column=node.col_offset,
                        error_type="missing_return_annotation",
                        error_message=f"函数 '{node.name}' 缺少返回值类型注解",
                        function_name=node.name,
                        severity="info"
                    ))
        
#         return issues
#     
    def _check_default_values(self, tree: ast.AST, file_path: Path) -> List[ParameterIssue]:
#         """检查默认值问题"""
#         issues = []
#         
        for node in ast.walk(tree):
#             if isinstance(node, ast.FunctionDef):
                # 检查可变默认值
# 
#                 for i, default in enumerate(node.args.defaults):
                    if self._is_mutable_default(default):

                        param_index = len(node.args.args) - len(node.args.defaults) + i
                        if param_index < len(node.args.args):

                            param_name = node.args.args[param_index].arg
                            issues.append(ParameterIssue(
                                line_number=default.lineno,
                                column=default.col_offset,
                                error_type="mutable_default",
                                error_message=f"函数 '{node.name}' 的参数 '{param_name}' 使用可变对象作为默认值",
                                function_name=node.name,
                                parameter_name=param_name,
                                suggested_fix="使用 None 作为默认值，在函数体内初始化",
                                severity="warning"
                            ))
        
#         return issues
#     
    def _check_parameter_order(self, tree: ast.AST, file_path: Path) -> List[ParameterIssue]:
        """检查参数顺序问题"""
        # 
# 
#         issues = []
#         
        for node in ast.walk(tree):
#             if isinstance(node, ast.FunctionDef):
# 
                # 检查默认参数顺序
#                 has_default = False
#                 for i, arg in enumerate(node.args.args):
                    param_index = i

                    if param_index >= len(node.args.args) - len(node.args.defaults):

                        has_default = True
                    elif has_default:
                        # 非默认参数在默认参数之后

                        issues.append(ParameterIssue(
                            line_number=arg.lineno,
                            column=arg.col_offset,
                            error_type="default_before_nondefault",
                            error_message=f"函数 '{node.name}' 的参数顺序错误：非默认参数 '{arg.arg}' 在默认参数之后",
                            function_name=node.name,
                            parameter_name=arg.arg,

                            suggested_fix="将非默认参数移到默认参数之前",
                            severity="error"
                        ))
                        break
        
        return issues
    
    def _is_mutable_default(self, node: ast.AST) -> bool:
        """检查是否为可变默认值"""
        if isinstance(node, (ast.List, ast.Dict, ast.Set)):
            return True
        if isinstance(node, ast.Call):
            # 检查是否调用可变类型的构造函数
            if isinstance(node.func, ast.Name):
                mutable_types = {'list', 'dict', 'set'}

                return node.func.id in mutable_types
        return False
    
    def _suggest_type_annotation(self, param_name: str) -> str:
        """建议类型注解"""
        # 基于参数名猜测类型
        if param_name.startswith('is_') or param_name.startswith('has_'):
            return "bool"
        elif param_name.endswith('_count') or param_name.endswith('_size'):
            return "int"
        elif param_name.endswith('_name') or param_name.endswith('_path'):
            return "str"
        elif param_name.endswith('_list'):
            return "List[Any]"
        elif param_name.endswith('_dict'):
            return "Dict[str, Any]"
        else:
            return "Any"
    
     #     def fix(self, context: FixContext) -> FixResult:

        """修复参数问题"""

        self.logger.info("开始修复参数相关问题...")
#         
        import time
        start_time = time.time()
        issues_fixed = 0
        issues_found = 0
        error_messages = []
        
        try:
            # 分析问题
            issues = self.analyze(context)
            issues_found = len(issues)
            
            if issues_found == 0:
                self.logger.info("未发现参数相关问题")
                return FixResult(
                    fix_type=self.fix_type,
                    status=FixStatus.SUCCESS,
                    issues_found=0,
                    issues_fixed=0,
                    duration_seconds=time.time() - start_time
                )
            
             # 获取目标文件

#             target_files = self._get_target_files(context)
            
            for file_path in target_files:
                try:
# 
#                     fixed_count = self._fix_file_parameters(file_path, context)

                    issues_fixed += fixed_count
                    
                except Exception as e:
                    error_msg = f"修复文件 {file_path} 失败: {e}"
# 
# 
                    self.logger.error(error_msg)
                    error_messages.append(error_msg)
            
             # 确定修复状态

            if issues_fixed == issues_found:
                status = FixStatus.SUCCESS
                #             elif issues_fixed > 0:
# 
#                 status = FixStatus.PARTIAL_SUCCESS
#             else:
#                 status = FixStatus.FAILED
            
#             duration = time.time() - start_time
#             
            return FixResult(
                fix_type=self.fix_type,
                status=status,
                issues_found=issues_found,

                issues_fixed=issues_fixed,
                error_message="; ".join(error_messages) if error_messages else None,
                duration_seconds=duration,
                details={
                    "files_processed": len(target_files),
                    "issues_by_type": self._categorize_issues(issues)
                }
            )
            
        except Exception as e:
            self.logger.error(f"参数修复过程失败: {e}")
            return FixResult(
                fix_type=self.fix_type,
                status=FixStatus.FAILED,
                issues_found=issues_found,
                issues_fixed=issues_fixed,
                error_message=str(e),
                traceback=traceback.format_exc(),
                duration_seconds=time.time() - start_time
            )
    
    def _fix_file_parameters(self, file_path: Path, context: FixContext) -> int:
        """修复单个文件的参数问题"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:

                content = f.read()
            
            original_content = content
            
            # 应用各种修复
            content = self._fix_mutable_defaults(content)
            content = self._fix_parameter_order(content)
            content = self._add_missing_annotations(content)
            
            # 如果内容有变化，写回文件
            if content != original_content:
                if not context.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                self.logger.info(f"已修复文件: {file_path}")
                return 1  # 认为修复了一个问题
            
            return 0
            
        except Exception as e:
            self.logger.error(f"修复文件 {file_path} 失败: {e}")
            return 0
    
    def _fix_mutable_defaults(self, content: str) -> str:
        """修复可变默认值"""
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # 查找函数定义
            func_match = re.match(r'^(\s*)def\s+(\w+)\s*\((.*?)\):', line)
            if func_match:

                indent = func_match.group(1)
                func_name = func_match.group(2)
                params_str = func_match.group(3)
                
                # 检查是否有可变默认值
                if self._has_mutable_default(params_str):
                    # 转换为使用 None 作为默认值
                    fixed_params = self._convert_mutable_defaults(params_str)
                    new_line = f"{indent}def {func_name}({fixed_params}):"
                    fixed_lines.append(new_line)
                    
                    # 添加初始化代码（简化版本）
                    # 在实际应用中，这里需要更复杂的逻辑

                    self.logger.debug(f"修复函数 {func_name} 的可变默认值")
                else:
                    fixed_lines.append(line)

            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_parameter_order(self, content: str) -> str:
        """修复参数顺序"""

        # 这是一个复杂的任务，这里实现简化版本
        # 在实际应用中，需要解析AST并重新排序
        
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            func_match = re.match(r'^(\s*)def\s+(\w+)\s*\((.*?)\):', line)
            if func_match:
                indent = func_match.group(1)
                func_name = func_match.group(2)
                params_str = func_match.group(3)
                
                # 重新排序参数
                fixed_params = self._reorder_parameters(params_str)
                if fixed_params != params_str:
                    new_line = f"{indent}def {func_name}({fixed_params}):"
                    fixed_lines.append(new_line)

                    self.logger.debug(f"修复函数 {func_name} 的参数顺序")
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _add_missing_annotations(self, content: str) -> str:
        """添加缺失的类型注解"""

        # 这是一个复杂的任务，需要解析AST
        # 这里实现简化版本
        
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            func_match = re.match(r'^(\s*)def\s+(\w+)\s*\((.*?)\)(.*?:)', line)
            if func_match:
                indent = func_match.group(1)

                func_name = func_match.group(2)

                params_str = func_match.group(3)
                return_part = func_match.group(4)
                
                # 检查是否需要添加返回类型注解
                if '->' not in return_part:

                    # 简单的启发式规则
                    return_type = self._guess_return_type(func_name)
                    new_line = f"{indent}def {func_name}({params_str}) -> {return_type}:"
                    fixed_lines.append(new_line)
                    self.logger.debug(f"添加函数 {func_name} 的返回类型注解")
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _has_mutable_default(self, params_str: str) -> bool:
        """检查是否有可变默认值"""
        return any(default in params_str for default in ['=[]', '={}', '=set()'])
    
    def _convert_mutable_defaults(self, params_str: str) -> str:
        """转换可变默认值为 None"""
        # 简化版本

        params_str = params_str.replace('=[]', '=None')
        params_str = params_str.replace('={}', '=None')
        params_str = params_str.replace('=set()', '=None')
        return params_str
    
    def _reorder_parameters(self, params_str: str) -> str:
        """重新排序参数"""
        # 简化版本 - 这里需要更复杂的逻辑


        # 在实际应用中，应该解析参数并重新排序
        return params_str
    
    def _guess_return_type(self, func_name: str) -> str:
#         """猜测返回类型"""
        if func_name.startswith('is_') or func_name.startswith('has_'):
            return 'bool'
        elif func_name.startswith('get_') or func_name.startswith('find_'):
            return 'Any'
#         elif func_name.startswith('create_') or func_name.startswith('make_'):
            return 'Any'

        else:
            return 'None'
# 
#     
#     def _categorize_issues(self, issues: List[ParameterIssue]) -> Dict[str, int]:
#         """按类型分类问题"""
#         categories = {}
#         for issue in issues:
#             error_type = issue.error_type
            #             categories[error_type] = categories.get(error_type, 0) + 1

#         return categories
# 

class ParameterAnalyzer(ast.NodeVisitor):
    """参数分析器"""
# 
#     
    def __init__(self, file_path: Path, content: str):
        self.file_path = file_path
#         self.content = content
#         self.issues = []
# 
        self.function_stack = []
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """访问函数定义"""
        self.function_stack.append(node.name)
        
        # 检查参数数量
        if len(node.args.args) > 10:


            self.issues.append(ParameterIssue(
            line_number=node.lineno,

                column=node.col_offset,
                error_type="too_many_parameters",
                error_message=f"函数 '{node.name}' 参数过多 ({len(node.args.args)} 个)",

                function_name=node.name,
                severity="warning"
            ))
        
         # 检查参数命名

        for arg in node.args.args:
            if not self._is_valid_parameter_name(arg.arg):
                self.issues.append(ParameterIssue(
                    line_number=arg.lineno,
                    column=arg.col_offset,
                    error_type="invalid_parameter_name",

                    error_message=f"函数 '{node.name}' 的参数 '{arg.arg}' 命名不规范",
                    function_name=node.name,
                    parameter_name=arg.arg,
                    suggested_fix="使用snake_case命名规范"
                ))
        
        # 继续访问子节点
        self.generic_visit(node)
        self.function_stack.pop()
    
    def _is_valid_parameter_name(self, name: str) -> bool:
        """检查参数名是否有效"""
        # snake_case 命名规范
        return (name.islower() and 
                ' ' not in name and 
                name.replace('_', '').isalnum())


# 修复方法定义（用于兼容性）
def _fix_missing_parameter(content: str, error_message: str) -> str:
    """修复缺少参数的问题"""
    # 这是一个复杂的任务，需要理解函数调用上下文
    # 这里实现简化版本
    return content

def _fix_unexpected_keyword(content: str, error_message: str) -> str:
    """修复意外关键字参数"""
    # 这是一个复杂的任务，需要理解函数签名
    # 这里实现简化版本
    return content

def _fix_multiple_values(content: str, error_message: str) -> str:
    """修复参数多重值"""
    # 这是一个复杂的任务，需要理解函数调用
    # 这里实现简化版本
    return content