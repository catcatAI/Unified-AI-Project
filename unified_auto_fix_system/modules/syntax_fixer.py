"""
增强语法修复器
修复Python语法错误,包括缩进、缺少冒号、括号不匹配等
"""

import ast
import re
import traceback
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from ..core.fix_types import FixType, FixStatus
from ..core.fix_result import FixResult, FixContext
from .base_fixer import BaseFixer


@dataclass
class SyntaxIssue:
    """语法问题"""
    line_number: int
    column: int
    error_type: str
    error_message: str
    suggested_fix: str = ""
    severity: str = "error"  # error, warning, info


class EnhancedSyntaxFixer(BaseFixer):
    """增强语法修复器"""
    
    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.fix_type = FixType.SYNTAX_FIX
        self.name = "EnhancedSyntaxFixer"
        
        # 常见语法错误模式
        self.error_patterns = {
            "missing_colon": {
                "pattern": r'^\s*(class|def|if|elif|else|for|while|try|except|finally|with)\s+[^:]*$',
                "fix": self._fix_missing_colons,
                "description": "缺少冒号"
            },
            "invalid_indentation": {
                "pattern": r'.*indentation.*',
                "fix": self._fix_indentation,
                "description": "缩进错误"
            },
            "unmatched_parentheses": {
                "pattern": r'.*parenthes.*|.*bracket.*',
                "fix": self._fix_unmatched_parentheses,
                "description": "括号不匹配"
            },
            "invalid_syntax": {
                "pattern": r'.*invalid syntax.*',
                "fix": self._fix_invalid_syntax,
                "description": "无效语法"
            },
            "unexpected_indent": {
                "pattern": r'.*unexpected indent.*',
                "fix": self._fix_unexpected_indent,
                "description": "意外缩进"
            },
            "unindent_does_not_match": {
                "pattern": r'.*unindent does not match.*',
                "fix": self._fix_unindent_mismatch,
                "description": "缩进不匹配"
            },
            "eof_while_scanning": {
                "pattern": r'.*EOF while scanning.*',
                "fix": self._fix_eof_while_scanning,
                "description": "扫描时遇到文件结尾"
            },
            "invalid_token": {
                "pattern": r'.*invalid token.*',
                "fix": self._fix_invalid_token,
                "description": "无效标记"
            }
        }
    
    def analyze(self, context: FixContext) -> List[SyntaxIssue]:
        """分析语法问题"""
        self.logger.info("分析语法问题...")
        
        issues = []
        target_files = self._get_target_files(context)

        for file_path in target_files:
            try:
                file_issues = self._analyze_file(file_path)
                issues.extend(file_issues)
            except Exception as e:
                self.logger.error(f"分析文件 {file_path} 失败: {e}")
        
        self.logger.info(f"发现 {len(issues)} 个语法问题")
        return issues
    
    def _analyze_file(self, file_path: Path) -> List[SyntaxIssue]:
        """分析单个文件"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 尝试解析AST
            try:
                ast.parse(content)
                return issues  # 没有语法错误
            except SyntaxError as e:
                issues.append(SyntaxIssue(
                    line_number=e.lineno or 0,
                    column=e.offset or 0,
                    error_type="syntax_error",
                    error_message=str(e)
                ))
            
            # 额外的语法检查
            additional_issues = self._check_additional_syntax_issues(content)
            issues.extend(additional_issues)
            
        except Exception as e:
            self.logger.error(f"无法读取文件 {file_path}: {e}")
        
        return issues
    
    def _check_additional_syntax_issues(self, content: str) -> List[SyntaxIssue]:
        """检查额外的语法问题"""
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # 检查缺少冒号
            if self._needs_colon(line):
                issues.append(SyntaxIssue(
                    line_number=i,
                    column=len(line),
                    error_type="missing_colon",
                    error_message="语句末尾缺少冒号",
                    suggested_fix=self._suggest_colon_fix(line)
                ))
            
            # 检查括号匹配
            paren_issues = self._check_parentheses_balance(line, i)
            issues.extend(paren_issues)
            
            # 检查缩进一致性
            if i > 1:
                indent_issues = self._check_indentation_consistency(lines[i-2], line, i)
                issues.extend(indent_issues)
        
        return issues
    
    def _needs_colon(self, line: str) -> bool:
        """检查是否需要冒号"""
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            return False
        
        # 需要冒号的关键字
        colon_keywords = ['class', 'def', 'if', 'elif', 'else', 'for', 'while', 
                         'try', 'except', 'finally', 'with']
        for keyword in colon_keywords:
            if stripped.startswith(keyword + ' '):
                return not stripped.endswith(':')
        
        return False
    
    def _suggest_colon_fix(self, line: str) -> str:
        """建议冒号修复"""
        return line.rstrip() + ':'
    
    def _check_parentheses_balance(self, line: str, line_num: int) -> List[SyntaxIssue]:
        """检查括号平衡"""
        issues = []
        
        # 统计各种括号
        parentheses = {'(': 0, ')': 0, '[': 0, ']': 0, '{': 0, '}': 0}
        
        for char in line:
            if char in parentheses:
                parentheses[char] += 1
        
        # 检查不平衡
        if parentheses['('] != parentheses[')']:
            issues.append(SyntaxIssue(
                line_number=line_num,
                column=0,
                error_type="unmatched_parentheses",
                error_message=f"圆括号不平衡, {parentheses['(']} 开, {parentheses[')']} 闭"
            ))
        
        if parentheses['['] != parentheses[']']:
            issues.append(SyntaxIssue(
                line_number=line_num,
                column=0,
                error_type="unmatched_brackets",
                error_message=f"方括号不平衡, {parentheses['[']} 开, {parentheses[']']} 闭"
            ))
        
        if parentheses['{'] != parentheses['}']:
            issues.append(SyntaxIssue(
                line_number=line_num,
                column=0,
                error_type="unmatched_braces",
                error_message=f"花括号不平衡, {parentheses['{']} 开, {parentheses['}']} 闭"
            ))
        
        return issues
    
    def _check_indentation_consistency(self, prev_line: str, current_line: str, line_num: int) -> List[SyntaxIssue]:
        """检查缩进一致性"""
        issues = []
        
        # 简单的缩进检查逻辑
        prev_indent = len(prev_line) - len(prev_line.lstrip())
        current_indent = len(current_line) - len(current_line.lstrip())
        
        # 检查缩进突变
        if abs(current_indent - prev_indent) > 4 and current_line.strip() and prev_line.strip():
            issues.append(SyntaxIssue(
                line_number=line_num,
                column=0,
                error_type="indentation_inconsistency",
                error_message=f"缩进不一致, 前一行 {prev_indent} 空格,当前行 {current_indent} 空格",
                severity="warning"
            ))

        return issues
    
    def fix(self, context: FixContext) -> FixResult:
        """修复语法问题"""
        self.logger.info("开始修复语法问题...")
        
        start_time = time.time()
        issues_fixed = 0
        issues_found = 0
        error_messages = []
        
        try:
            # 分析问题
            issues = self.analyze(context)
            issues_found = len(issues)
            
            if issues_found == 0:
                self.logger.info("未发现语法问题")
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
                    fixed_count = self._fix_file(file_path, context)
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
            self.logger.error(f"语法修复过程失败: {e}")
            return FixResult(
                fix_type=self.fix_type,
                status=FixStatus.FAILED,
                issues_found=issues_found,
                issues_fixed=issues_fixed,
                error_message=str(e),
                traceback=traceback.format_exc(),
                duration_seconds=time.time() - start_time
            )
    
    def _fix_file(self, file_path: Path, context: FixContext) -> int:
        """修复单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            
            # 应用各种修复
            content = self._fix_missing_colons(content)
            content = self._fix_indentation(content)
            content = self._fix_unmatched_parentheses(content)
            content = self._fix_invalid_syntax(content)
            
            # 如果内容有变化,写回文件
            if content != original_content:
                if not context.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                self.logger.info(f"已修复文件, {file_path}")
                return 1  # 认为修复了一个问题
            
            return 0
            
        except Exception as e:
            self.logger.error(f"修复文件 {file_path} 失败: {e}")
            return 0
    
    def _fix_missing_colons(self, content: str) -> str:
        """修复缺少冒号的问题"""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # 跳过空行和注释
            if not stripped or stripped.startswith('#'):
                fixed_lines.append(line)
                continue

            # 检查是否需要冒号
            if self._needs_colon(line):
                # 在行尾添加冒号
                indent = line[:len(line) - len(line.lstrip())]
                fixed_line = line.rstrip() + ':'
                fixed_lines.append(fixed_line)
                self.logger.debug(f"修复缺少冒号, {stripped}")
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_indentation(self, content: str) -> str:
        """修复缩进问题"""
        # 这里可以实现更复杂的缩进修复逻辑
        # 目前只是简单的标准化
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # 将Tab转换为空格
            fixed_line = line.replace('\t', '    ')
            fixed_lines.append(fixed_line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_unmatched_parentheses(self, content: str) -> str:
        """修复不匹配的括号"""
        # 这是一个复杂的任务,这里实现简化版本
        # 在实际应用中,可能需要更智能的分析
        
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # 简单的括号平衡检查
            if self._has_unmatched_parentheses(line):
                # 尝试修复(简化版本)
                fixed_line = self._try_fix_parentheses(line)
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _has_unmatched_parentheses(self, line: str) -> bool:
        """检查是否有不匹配的括号"""
        # 简化的检查
        return (line.count('(') != line.count(')') or 
                line.count('[') != line.count(']') or 
                line.count('{') != line.count('}'))
    
    def _try_fix_parentheses(self, line: str) -> str:
        """尝试修复括号"""
        # 简化的修复逻辑
        # 在实际应用中,这里需要更智能的分析
        
        # 如果行尾有不匹配的左括号,尝试添加右括号
        if line.count('(') > line.count(')'):
            line += ')' * (line.count('(') - line.count(')'))
        
        if line.count('[') > line.count(']'):
            line += ']' * (line.count('[') - line.count(']'))
        
        if line.count('{') > line.count('}'):
            line += '}' * (line.count('{') - line.count('}'))
        
        return line
    
    def _fix_invalid_syntax(self, content: str) -> str:
        """修复无效语法"""
        # 这里可以添加更多特定的语法修复规则
        # 目前只是一个占位符
        return content
    
    def _categorize_issues(self, issues: List[SyntaxIssue]) -> Dict[str, int]:
        """按类型分类问题"""
        categories = {}
        for issue in issues:
            error_type = issue.error_type
            categories[error_type] = categories.get(error_type, 0) + 1
        return categories
    
    def _fix_unexpected_indent(self, content: str) -> str:
        """修复意外缩进"""
        # 实现意外缩进修复逻辑
        return content
    
    def _fix_unindent_mismatch(self, content: str) -> str:
        """修复缩进不匹配"""
        # 实现缩进不匹配修复逻辑
        return content
    
    def _fix_eof_while_scanning(self, content: str) -> str:
        """修复扫描时遇到文件结尾"""
        # 实现EOF修复逻辑
        return content
    
    def _fix_invalid_token(self, content: str) -> str:
        """修复无效标记"""
        # 实现无效标记修复逻辑
        return content