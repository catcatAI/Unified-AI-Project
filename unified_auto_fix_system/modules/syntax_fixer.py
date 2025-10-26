#!/usr/bin/env python3
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
            
            # 检查其他常见语法问题
            stripped = line.strip()
            if stripped:
                # 检查是否在with语句中错误使用了==
                if 'with open(' in stripped and 'encoding == ' in stripped:
                    issues.append(SyntaxIssue(
                        line_number=i,
                        column=line.find('encoding'),
                        error_type="syntax_error",
                        error_message="在with语句中错误使用了==，应使用="
                    ))
                
                # 检查是否缺少逗号
                if '(' in stripped and ')' in stripped and '" ' in stripped and ' "' in stripped:
                    issues.append(SyntaxIssue(
                        line_number=i,
                        column=0,
                        error_type="syntax_error",
                        error_message="可能缺少逗号分隔符"
                    ))
        
        return issues
    
    def _needs_colon(self, line: str) -> bool:
        """检查是否需要冒号"""
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            return False
        
        # 需要冒号的关键字
        colon_keywords = ['class', 'def', 'if', 'elif', 'else', 'for', 'while', 
                         'try', 'except', 'finally', 'with']
        
        # 检查是否以这些关键字开头
        for keyword in colon_keywords:
            # 精确匹配关键字后跟空格的情况
            if stripped.startswith(keyword + ' '):
                return not stripped.endswith(':')
            
            # 完整关键字匹配
            if stripped == keyword:
                return True
            
            # 检查关键字后跟括号的情况（函数/类定义）
            if (stripped.startswith(keyword + '(') and ')' in stripped and 
                not stripped.endswith(':')):
                return True
            
            # 检查with语句等特殊情况
            if (stripped.startswith(keyword + ' ') and 
                not stripped.endswith(':')):
                # 检查是否是合法的with语句（包含as关键字）
                if keyword == 'with' and ' as ' in stripped:
                    return True
                # 其他控制流语句
                if keyword in ['if', 'elif', 'for', 'while', 'except']:
                    return True
        
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
        
        # 忽略空行和注释行
        if not prev_line.strip() or prev_line.strip().startswith('#'):
            return issues
        if not current_line.strip() or current_line.strip().startswith('#'):
            return issues
        
        # 计算缩进
        prev_indent = len(prev_line) - len(prev_line.lstrip())
        current_indent = len(current_line) - len(current_line.lstrip())
        
        # 检查缩进是否是4的倍数（Python标准）
        if prev_indent % 4 != 0:
            issues.append(SyntaxIssue(
                line_number=line_num-1,
                column=0,
                error_type="indentation_inconsistency",
                error_message=f"前一行缩进不规范, {prev_indent} 空格,应为4的倍数",
                severity="warning"
            ))
        
        if current_indent % 4 != 0:
            issues.append(SyntaxIssue(
                line_number=line_num,
                column=0,
                error_type="indentation_inconsistency",
                error_message=f"当前行缩进不规范, {current_indent} 空格,应为4的倍数",
                severity="warning"
            ))
        
        # 检查缩进突变
        indent_diff = abs(current_indent - prev_indent)
        if indent_diff > 8 and current_line.strip() and prev_line.strip():
            issues.append(SyntaxIssue(
                line_number=line_num,
                column=0,
                error_type="indentation_inconsistency",
                error_message=f"缩进突变过大, 前一行 {prev_indent} 空格,当前行 {current_indent} 空格,差值 {indent_diff}",
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
                # 在行尾添加冒号，但要确保不会在已经有冒号的地方添加
                if not stripped.endswith(':'):
                    fixed_line = line.rstrip() + ':'
                    fixed_lines.append(fixed_line)
                    self.logger.debug(f"修复缺少冒号: {stripped}")
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_indentation(self, content: str) -> str:
        """修复缩进问题"""
        # 使用更完善的缩进修复逻辑
        return self._fix_unexpected_indent(content)
    
    def _fix_unmatched_parentheses(self, content: str) -> str:
        """修复不匹配的括号 - 改进版本"""
        lines = content.split('\n')
        fixed_lines = []
        
        # 跟踪整个文件的括号平衡
        paren_balance = {'(': 0, '[': 0, '{': 0}
        
        for line_num, line in enumerate(lines):
            original_line = line
            
            # 更新括号平衡计数
            for char in line:
                if char in paren_balance:
                    paren_balance[char] += 1
                elif char == ')' and paren_balance['('] > 0:
                    paren_balance['('] -= 1
                elif char == ']' and paren_balance['['] > 0:
                    paren_balance['['] -= 1
                elif char == '}' and paren_balance['{'] > 0:
                    paren_balance['{'] -= 1
            
            # 修复行末不平衡的括号（更智能的方式）
            # 检查行内的括号平衡
            line_paren_count = {'(': 0, ')': 0, '[': 0, ']': 0, '{': 0, '}': 0}
            for char in line:
                if char in line_paren_count:
                    line_paren_count[char] += 1
            
            # 计算行内不平衡的括号数量
            unmatched_parens = line_paren_count['('] - line_paren_count[')']
            unmatched_brackets = line_paren_count['['] - line_paren_count[']']
            unmatched_braces = line_paren_count['{'] - line_paren_count['}']
            
            # 修复不平衡的括号
            if unmatched_parens > 0:
                # 行内有未闭合的圆括号，在行末添加
                line += ')' * unmatched_parens
            elif unmatched_parens < 0:
                # 行内有多余的右圆括号，这是一个严重错误，需要更仔细处理
                # 简单处理：在行首添加缺失的左括号
                line = '(' * abs(unmatched_parens) + line
            
            if unmatched_brackets > 0:
                # 行内有未闭合的方括号，在行末添加
                line += ']' * unmatched_brackets
            elif unmatched_brackets < 0:
                # 行内有多余的右方括号
                line = '[' * abs(unmatched_brackets) + line
            
            if unmatched_braces > 0:
                # 行内有未闭合的花括号，在行末添加
                line += '}' * unmatched_braces
            elif unmatched_braces < 0:
                # 行内有多余的右花括号
                line = '{' * abs(unmatched_braces) + line
            
            fixed_lines.append(line)
        
        # 在文件末尾添加缺失的右括号（如果有）
        missing_parens = paren_balance['(']
        missing_brackets = paren_balance['[']
        missing_braces = paren_balance['{']
        
        if missing_parens > 0 or missing_brackets > 0 or missing_braces > 0:
            # 添加缺失的右括号
            end_braces = '}' * missing_braces + ']' * missing_brackets + ')' * missing_parens
            if fixed_lines:
                fixed_lines[-1] = fixed_lines[-1] + end_braces
        
        return '\n'.join(fixed_lines)
    
    def _has_unmatched_parentheses(self, line: str) -> bool:
        """检查是否有不匹配的括号"""
        # 简化的检查
        return (line.count('(') != line.count(')') or 
                line.count('[') != line.count(']') or 
                line.count('{') != line.count('}'))
    
    def _fix_invalid_syntax(self, content: str) -> str:
        """修复无效语法"""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            fixed_line = line
            stripped = fixed_line.strip()
            
            # 修复常见的语法错误
            
            # 1. 修复赋值错误 (== 应该是 =)
            if ' =' in stripped and ' ==' not in stripped and ' !=' not in stripped:
                # 检查是否在with语句中错误使用了==
                if 'with open(' in stripped and 'encoding == ' in stripped:
                    fixed_line = fixed_line.replace('encoding == ', 'encoding=')
                elif ' as ' in stripped and ':' in stripped:
                    # 可能是在参数中错误使用了==
                    fixed_line = fixed_line.replace(' == ', ' = ')
            
            # 2. 修复缺少逗号的情况
            # 检查函数调用中可能缺少逗号的情况
            if '(' in stripped and ')' in stripped:
                # 简单的启发式检查
                if '" ' in stripped and ' "' in stripped:
                    # 可能是字符串参数之间缺少逗号
                    fixed_line = re.sub(r'("[^"]*") ([a-zA-Z_])', r'\1, \2', fixed_line)
            
            # 3. 修复多余的逗号
            if stripped.endswith(',)'):
                fixed_line = fixed_line[:-2] + ')'
            
            fixed_lines.append(fixed_line)
        
        return '\n'.join(fixed_lines)
    
    def _categorize_issues(self, issues: List[SyntaxIssue]) -> Dict[str, int]:
        """按类型分类问题"""
        categories = {}
        for issue in issues:
            error_type = issue.error_type
            categories[error_type] = categories.get(error_type, 0) + 1
        return categories
    
    def _fix_unexpected_indent(self, content: str) -> str:
        """修复意外缩进"""
        lines = content.split('\n')
        fixed_lines = []
        
        # 跟踪预期的缩进级别
        expected_indent = 0
        indent_stack = [0]  # 缩进栈，用于跟踪嵌套级别
        
        for line in lines:
            stripped = line.lstrip()
            if not stripped:  # 空行
                fixed_lines.append(line)
                continue
                
            current_indent = len(line) - len(stripped)
            
            # 检查是否是控制流语句的开始
            if stripped.startswith(('class ', 'def ', 'if ', 'elif ', 'else:', 'for ', 'while ', 'try:', 'except', 'finally:', 'with ')):
                # 如果是控制流语句，确保缩进是4的倍数
                standard_indent = (current_indent // 4) * 4
                if standard_indent != current_indent:
                    line = ' ' * standard_indent + stripped
                    current_indent = standard_indent
                
                # 更新预期缩进
                if stripped.endswith(':'):
                    indent_stack.append(current_indent + 4)
                    expected_indent = current_indent + 4
                else:
                    expected_indent = current_indent
            
            # 检查是否是块结束语句
            elif stripped.startswith(('elif ', 'else:', 'except', 'finally:')):
                # 这些语句应该与对应的开始语句有相同的缩进
                if len(indent_stack) > 1:
                    expected_indent = indent_stack[-2]
                
                # 调整缩进
                if current_indent != expected_indent:
                    line = ' ' * expected_indent + stripped
            
            # 普通语句
            else:
                # 确保缩进是4的倍数
                standard_indent = (current_indent // 4) * 4
                if standard_indent != current_indent:
                    line = ' ' * standard_indent + stripped
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_unindent_mismatch(self, content: str) -> str:
        """修复缩进不匹配"""
        # 使用与意外缩进相同的逻辑
        return self._fix_unexpected_indent(content)
    
    def _fix_eof_while_scanning(self, content: str) -> str:
        """修复扫描时遇到文件结尾"""
        # 检查是否缺少引号
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # 检查引号是否匹配
            single_quotes = line.count("'")
            double_quotes = line.count('"')
            
            # 如果引号数量是奇数，可能缺少闭合引号
            if single_quotes % 2 == 1:
                line = line + "'"  # 添加缺失的引号
            if double_quotes % 2 == 1:
                line = line + '"'  # 添加缺失的引号
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_invalid_token(self, content: str) -> str:
        """修复无效标记"""
        # 修复常见的无效标记问题
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            fixed_line = line
            
            # 修复非标准字符
            # 替换常见的非标准引号
            fixed_line = fixed_line.replace('“', '"').replace('”', '"')
            fixed_line = fixed_line.replace('‘', "'").replace('’', "'")
            
            # 修复常见的Unicode字符问题
            fixed_line = fixed_line.replace('\u2013', '-').replace('\u2014', '-')
            
            fixed_lines.append(fixed_line)
        
        return '\n'.join(fixed_lines)