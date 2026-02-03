"""
类定义修复器
修复类相关的问题,包括类名冲突、继承错误、方法定义等
"""

import ast
import re
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass

from ..core.fix_types import FixType, FixStatus
from ..core.fix_result import FixResult, FixContext
from .base_fixer import BaseFixer


@dataclass
class ClassIssue:
    """类相关问题"""
    line_number: int
    column: int
    error_type: str
    error_message: str
    class_name: str = ""
    suggested_fix: str = ""
    severity: str = "error"  # error, warning, info


class ClassFixer(BaseFixer):
    """类定义修复器"""
    
    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.fix_type = FixType.CLASS_FIX
        self.name = "ClassFixer"
        
         # 常见类相关问题模式
        self.error_patterns = {
            "undefined_base_class": {
                "pattern": r'.*name\s+\'(.+)\'\s+is\s+not\s+defined.*',
                "fix": self._fix_undefined_base_classes,
                "description": "基类未定义"
            },
            "inheritance_error": {
                "pattern": r'.*cannot\s+create\s+.*consistent\s+method\s+resolution.*',
                "fix": self._fix_inheritance_issues,
                "description": "继承错误"
            },
            "abstract_method_error": {
                "pattern": r'.*abstract\s+method.*',
                "fix": self._fix_inheritance_issues,
                "description": "抽象方法错误"
            },
            "method_resolution_order": {
                "pattern": r'.*method\s+resolution\s+order.*',
                "fix": self._fix_inheritance_issues,
                "description": "方法解析顺序错误"
            },
            "class_redefinition": {
                "pattern": r'.*class\s+\'(.+)\'\s+already\s+defined.*',
                "fix": self._fix_class_redefinitions,
                "description": "类重复定义"
            },
            "metaclass_conflict": {
                "pattern": r'.*metaclass\s+conflict.*',
                "fix": self._fix_inheritance_issues,
                "description": "元类冲突"
            }
        }
    
    def analyze(self, context: FixContext) -> List[ClassIssue]:
        """分析类相关问题"""
        self.logger.info("分析类相关问题...")
        
        issues = []
        target_files = self._get_target_files(context)
        
        for file_path in target_files:
            try:
                file_issues = self._analyze_file_classes(file_path)
                issues.extend(file_issues)
            except Exception as e:
                self.logger.error(f"分析文件 {file_path} 失败: {e}")
        
        self.logger.info(f"发现 {len(issues)} 个类相关问题")
        return issues
    
    def _analyze_file_classes(self, file_path: Path) -> List[ClassIssue]:
        """分析单个文件的类定义"""
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
            
            # 分析类定义
            class_analyzer = ClassAnalyzer(file_path, content)
            class_analyzer.visit(tree)
            issues.extend(class_analyzer.issues)
            
            # 检查继承关系
            inheritance_issues = self._check_inheritance_issues(tree, file_path)
            issues.extend(inheritance_issues)
            
            # 检查类名冲突
            naming_issues = self._check_class_naming_issues(tree, file_path)
            issues.extend(naming_issues)
            
        except Exception as e:
            self.logger.error(f"无法分析文件 {file_path}: {e}")
        
        return issues
    
    def _check_inheritance_issues(self, tree: ast.AST, file_path: Path) -> List[ClassIssue]:
        """检查继承相关问题"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 检查基类是否存在
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_name = base.id
                        if not self._is_base_class_defined(base_name, tree):
                            issues.append(ClassIssue(
                                line_number=base.lineno,
                                column=base.col_offset,
                                error_type="undefined_base_class",
                                error_message=f"基类 '{base_name}' 未定义",
                                class_name=node.name,
                                suggested_fix=self._suggest_base_class_fix(base_name)
                            ))
                
                # 检查多重继承问题
                if len(node.bases) > 1:
                    mro_issues = self._check_method_resolution_order(node)
                    issues.extend(mro_issues)
        
        return issues
    
    def _check_class_naming_issues(self, tree: ast.AST, file_path: Path) -> List[ClassIssue]:
        """检查类命名问题"""
        issues = []
        class_names = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name in class_names:
                    issues.append(ClassIssue(
                        line_number=node.lineno,
                        column=node.col_offset,
                        error_type="class_redefinition",
                        error_message=f"类 '{node.name}' 重复定义",
                        class_name=node.name,
                        suggested_fix=self._suggest_renaming_fix(node.name)
                    ))
                class_names.add(node.name)
        
        return issues
    
    def _is_base_class_defined(self, base_name: str, tree: ast.AST) -> bool:
        """检查基类是否已定义"""
        # 检查内置类型
        builtin_types = {'object', 'int', 'str', 'list', 'dict', 'tuple', 'set'}
        if base_name in builtin_types:
            return True
        
        # 检查当前文件中定义的类
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == base_name:
                return True
        
        # 检查导入的模块
        # 这里可以扩展为检查实际的导入语句
        return False
    
    def _check_method_resolution_order(self, class_node: ast.ClassDef) -> List[ClassIssue]:
        """检查方法解析顺序问题"""
        issues = []
        
        # 简化的MRO检查
        base_names = []
        for base in class_node.bases:
            if isinstance(base, ast.Name):
                base_names.append(base.id)
        
        # 检查常见的MRO问题模式
        if len(base_names) > 2:
            issues.append(ClassIssue(
                line_number=class_node.lineno,
                column=class_node.col_offset,
                error_type="method_resolution_order",
                error_message=f"多重继承可能导致方法解析顺序问题: {base_names}",
                class_name=class_node.name,
                severity="warning"
            ))
        
        return issues
    
    def _suggest_base_class_fix(self, base_name: str) -> str:
        """建议基类修复方案"""
        # 提供可能的修复建议
        suggestions = [
            f"确保 '{base_name}' 已导入",
            f"检查 '{base_name}' 的拼写",
            f"考虑使用正确的基类名称"
        ]
        return "; ".join(suggestions)
    
    def _suggest_renaming_fix(self, class_name: str) -> str:
        """建议重命名修复方案"""
        return f"将其中一个 '{class_name}' 重命名为其他名称"
    
    def fix(self, context: FixContext) -> FixResult:
        """修复类相关问题"""
        self.logger.info("开始修复类相关问题...")
        
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
                self.logger.info("未发现类相关问题")
                return FixResult(
                    fix_type=self.fix_type,
                    status=FixStatus.SUCCESS,
                    issues_found=0,
                    issues_fixed=0,
                    duration_seconds=time.time() - start_time
                )
            
             # 获取目标文件
            target_files = self._get_target_files(context)
            
            for file_path in target_files:
                try:
                    fixed_count = self._fix_file_classes(file_path, context)
                    issues_fixed += fixed_count
                    
                except Exception as e:
                    error_msg = f"修复文件 {file_path} 失败: {e}"
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
                    "files_processed": len(target_files),
                    "issues_by_type": self._categorize_issues(issues)
                }
            )
            
        except Exception as e:
            self.logger.error(f"类修复过程失败: {e}")
            return FixResult(
                fix_type=self.fix_type,
                status=FixStatus.FAILED,
                issues_found=issues_found,
                issues_fixed=issues_fixed,
                error_message=str(e),
                traceback=traceback.format_exc(),
                duration_seconds=time.time() - start_time
            )
    
    def _fix_file_classes(self, file_path: Path, context: FixContext) -> int:
        """修复单个文件的类问题"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 应用各种修复
            content = self._fix_undefined_base_classes(content)
            content = self._fix_class_redefinitions(content)
            content = self._fix_inheritance_issues(content)
            
            # 如果内容有变化,写回文件
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

    def _fix_undefined_base_classes(self, content: str) -> str:
        """修复未定义的基类"""
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # 检查类定义行
            class_match = re.match(r'^(\s*)class\s+(\w+)\s*\((.*?)\):', line)
            if class_match:
                indent = class_match.group(1)
                class_name = class_match.group(2)
                bases_str = class_match.group(3)
                
                # 分析基类
                bases = [base.strip() for base in bases_str.split(',') if base.strip()]
                fixed_bases = []
                for base in bases:
                    # 尝试修复常见的基类问题
                    fixed_base = self._fix_base_class_name(base)
                    fixed_bases.append(fixed_base)

                
                # 重新构建类定义
                if fixed_bases:
                    new_line = f"{indent}class {class_name}({', '.join(fixed_bases)})"
                else:
                    new_line = f"{indent}class {class_name}"
                
                fixed_lines.append(new_line)
                self.logger.debug(f"修复基类: {class_name}")
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_base_class_name(self, base_name: str) -> str:
        """修复基类名称"""
        # 常见的拼写错误修正
        corrections = {
            'objct': 'object',
            'obj': 'object',
            'basemodel': 'BaseModel',
            'baseagent': 'BaseAgent',
            'basefixer': 'BaseFixer'
        }
        
        return corrections.get(base_name.lower(), base_name)
    
    def _fix_class_redefinitions(self, content: str) -> str:
        """修复类重复定义"""
        # 这是一个复杂的任务,这里实现简化版本
        # 在实际应用中,可能需要更智能的重命名策略
        
        lines = content.split('\n')
        fixed_lines = []
        class_names = set()
        rename_counter = {}
        
        for line in lines:
            class_match = re.match(r'^(\s*)class\s+(\w+)', line)
            if class_match:
                indent = class_match.group(1)
                class_name = class_match.group(2)
                
                if class_name in class_names:
                    # 需要重命名
                    counter = rename_counter.get(class_name, 1) + 1
                    rename_counter[class_name] = counter
                    new_name = f"{class_name}_{counter}"
                    
                    # 替换类名
                    fixed_line = line.replace(f"class {class_name}", f"class {new_name}")
                    fixed_lines.append(fixed_line)
                    self.logger.debug(f"重命名类: {class_name} -> {new_name}")
                else:
                    class_names.add(class_name)
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
         
        return '\n'.join(fixed_lines)
    
    def _fix_inheritance_issues(self, content: str) -> str:
        """修复继承问题"""
        # 这里可以添加更复杂的继承修复逻辑
        # 目前只是一个占位符
        return content

    def _categorize_issues(self, issues: List[ClassIssue]) -> Dict[str, int]:
        """按类型分类问题"""
        categories = {}
        for issue in issues:
            error_type = issue.error_type
            categories[error_type] = categories.get(error_type, 0) + 1
        return categories


class ClassAnalyzer(ast.NodeVisitor):
    """类定义分析器"""
    
    def __init__(self, file_path: Path, content: str):
        self.file_path = file_path
        self.content = content
        self.issues = []
        self.class_names = set()

    
    def visit_ClassDef(self, node: ast.ClassDef):
        """访问类定义"""
        # 检查类名是否符合命名规范
        if not self._is_valid_class_name(node.name):
            self.issues.append(ClassIssue(
                line_number=node.lineno,
                column=node.col_offset,
                error_type="invalid_class_name",
                error_message=f"类名 '{node.name}' 不符合命名规范",
                class_name=node.name,
                suggested_fix="使用PascalCase命名规范"
            ))
        
        # 检查类名重复
        if node.name in self.class_names:
            self.issues.append(ClassIssue(
                line_number=node.lineno,
                column=node.col_offset,
                error_type="class_redefinition",
                error_message=f"类 '{node.name}' 在当前文件中重复定义",
                class_name=node.name))
        self.class_names.add(node.name)
        
        # 继续访问子节点
        self.generic_visit(node)
    
    def _is_valid_class_name(self, name: str) -> bool:
        """检查类名是否有效"""
        # PascalCase 命名规范
        return (name[0].isupper() and 
                '_' not in name and 
                name.isalnum())


# 修复方法定义(用于兼容性)
class FixEngine:
    """修复引擎 - 占位符类用于兼容性"""
    def __init__(self, project_root: Path):
        self.project_root = project_root