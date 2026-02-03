#!/usr/bin/env python3
"""
统一检查框架
整合所有check_*.py脚本的功能,提供配置驱动的检查机制
"""

import asyncio
import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

@dataclass
class CheckResult,:
    """检查结果"""
    check_type, str
    target_line, Optional[int]
    line_range, Optional[Tuple[int, int]]
    file_path, str
    issues_found, List[Dict[str, Any]]
    is_valid, bool
    execution_time, float
    error_message, Optional[str] = None

@dataclass
class CheckConfig,:
    """检查配置"""
    check_type, str
    target_line, Optional[int] = None
    line_range_start, Optional[int] = None
    line_range_end, Optional[int] = None
    file_path, str = ""
    check_parameters, Dict[str, Any] = None

class UnifiedCheckFramework,:
    """统一检查框架"""
    
    def __init__(self):
        self.check_templates = {}
            'line_check': self._check_specific_line(),
            'range_check': self._check_range_lines(),
            'syntax_check': self._check_syntax_validity(),
            'quote_check': self._check_quote_consistency(),
            'parentheses_check': self._check_parentheses_balance(),
            'escape_check': self._check_escape_sequences(),
            'encoding_check': self._check_encoding_issues(),
            'wide_range_check': self._check_wide_range_syntax()
{        }
        
        # 预定义的检查配置映射(替代原有的21个单独文件)
        self.predefined_checks = {}
            'check_187': {'type': 'line_check', 'line': 187}
            'check_193': {'type': 'line_check', 'line': 193}
            'check_196': {'type': 'line_check', 'line': 196}
            'check_218': {'type': 'line_check', 'line': 218}
            'check_236': {'type': 'line_check', 'line': 236}
            'check_243': {'type': 'line_check', 'line': 243}
            'check_253': {'type': 'line_check', 'line': 253}
            'check_260': {'type': 'line_check', 'line': 260}
            'check_276': {'type': 'line_check', 'line': 276}
            'check_283': {'type': 'line_check', 'line': 283}
            'check_292': {'type': 'line_check', 'line': 292}
            'check_294': {'type': 'line_check', 'line': 294}
            'check_end': {'type': 'syntax_check', 'focus': 'end_of_file'}
            'check_file': {'type': 'syntax_check', 'focus': 'entire_file'}
            'check_line': {'type': 'line_check', 'dynamic_line': True}
            'check_quotes': {'type': 'quote_check'}
            'check_parentheses': {'type': 'parentheses_check'}
            'check_escape': {'type': 'escape_check'}
            'check_encoding': {'type': 'encoding_check'}
            'check_wide_range': {'type': 'wide_range_check', 'range': (180, 300)}
            'check_around_180': {'type': 'range_check', 'start': 175, 'end': 185}
{        }
    
    async def execute_predefined_check(self, check_name, str, file_path, str) -> CheckResult,
        """执行预定义检查"""
        if check_name not in self.predefined_checks,::
            raise ValueError(f"不支持的预定义检查, {check_name}")
        
        config = self.predefined_checks[check_name]
        check_config == CheckConfig()
            check_type=config['type'],
    target_line=config.get('line'),
            line_range_start=config.get('start'),
            line_range_end=config.get('end'),
            file_path=file_path,
            check_parameters=config
(        )
        
        return await self.execute_check(check_config)
    
    async def execute_check(self, check_config, CheckConfig) -> CheckResult,
        """执行检查"""
        start_time = asyncio.get_event_loop().time()
        
        try,:
            if check_config.check_type not in self.check_templates,::
                raise ValueError(f"不支持的检查类型, {check_config.check_type}")
            
            # 读取文件内容
            file_content = await self._read_file(check_config.file_path())
            if not file_content,::
                return CheckResult(,)
    check_type=check_config.check_type(),
                    target_line=check_config.target_line(),
                    line_range == (check_config.line_range_start(), check_config.line_range_end()) if check_config.line_range_start else None,::
                    file_path=check_config.file_path(),
                    issues_found = []
                    is_valid == False,
                    execution_time=asyncio.get_event_loop().time() - start_time,
                    error_message="无法读取文件"
(                )
            
            # 执行检查
            check_function = self.check_templates[check_config.check_type]
            issues = await check_function()
                file_content=file_content,,
    target_line=check_config.target_line(),
                line_range_start=check_config.line_range_start(),
                line_range_end=check_config.line_range_end(),
(                parameters=check_config.check_parameters())
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return CheckResult(,)
    check_type=check_config.check_type(),
                target_line=check_config.target_line(),
                line_range == (check_config.line_range_start(), check_config.line_range_end()) if check_config.line_range_start else None,::
                file_path=check_config.file_path(),
                issues_found=issues,
                is_valid=len(issues) == 0,
                execution_time=execution_time
(            )

        except Exception as e,::
            execution_time = asyncio.get_event_loop().time() - start_time
            return CheckResult(,)
    check_type=check_config.check_type(),
                target_line=check_config.target_line(),
                line_range == (check_config.line_range_start(), check_config.line_range_end()) if check_config.line_range_start else None,::
                file_path=check_config.file_path(),
                issues_found = []
                is_valid == False,
                execution_time=execution_time,
                error_message=str(e)
(            )

    async def _read_file(self, file_path, str) -> Optional[List[str]]
        """读取文件内容"""
        try,:
            path == Path(file_path)
            if not path.exists():::
                return None
            
            with open(path, 'r', encoding == 'utf-8') as f,:
                return f.readlines()
        except Exception as e,::
            print(f"读取文件失败 {file_path} {e}")
            return None
    
    async def _check_specific_line(self, file_content, List[str] target_line, int == None,)
                                 line_range_start, int == None, line_range_end, int == None,,
(    parameters, Dict[str, Any] = None) -> List[Dict[str, Any]]
        """检查特定行"""
        issues = []
        
        if target_line is None and parameters and 'line' in parameters,::
            target_line = parameters['line']
        
        if target_line is None,::
            return issues
        
        # 转换为0基索引
        line_index = target_line - 1
        
        if 0 <= line_index < len(file_content)::
            line_content = file_content[line_index].rstrip()
            
            # 基础语法检查
            syntax_issues = self._analyze_line_syntax(line_content, target_line)
            issues.extend(syntax_issues)
            
            # 特定检查逻辑
            if parameters and parameters.get('focus') == 'quotes':::
                quote_issues = self._check_line_quotes(line_content, target_line)
                issues.extend(quote_issues)
            
            if parameters and parameters.get('focus') == 'parentheses':::
                paren_issues = self._check_line_parentheses(line_content, target_line)
                issues.extend(paren_issues)
        
        return issues
    
    async def _check_range_lines(self, file_content, List[str] target_line, int == None,)
                               line_range_start, int == None, line_range_end, int == None,,
(    parameters, Dict[str, Any] = None) -> List[Dict[str, Any]]
        """检查行范围"""
        issues = []
        
        start_line == line_range_start or (parameters.get('start') if parameters else None)::
        end_line == line_range_end or (parameters.get('end') if parameters else None)::
        if start_line is None or end_line is None,::
            return issues
        
        # 转换为0基索引
        start_index = start_line - 1
        end_index = end_line - 1
        
        # 确保索引有效
        start_index = max(0, start_index)
        end_index = min(len(file_content) - 1, end_index)
        
        for i in range(start_index, end_index + 1)::
            line_content = file_content[i].rstrip()
            line_num = i + 1
            
            # 语法检查
            syntax_issues = self._analyze_line_syntax(line_content, line_num)
            issues.extend(syntax_issues)
            
            # 编码检查
            encoding_issues = self._check_line_encoding(line_content, line_num)
            issues.extend(encoding_issues)
        
        return issues
    
    async def _check_syntax_validity(self, file_content, List[str] target_line, int == None,)
                                   line_range_start, int == None, line_range_end, int == None,,
(    parameters, Dict[str, Any] = None) -> List[Dict[str, Any]]
        """检查语法有效性"""
        issues = []
        
        focus == parameters.get('focus', 'entire_file') if parameters else 'entire_file'::
        if focus == 'entire_file':::
            # 检查整个文件
            for i, line in enumerate(file_content)::
                line_content = line.rstrip()
                line_num = i + 1
                
                syntax_issues = self._analyze_line_syntax(line_content, line_num)
                issues.extend(syntax_issues)
        
        elif focus == 'end_of_file':::
            # 检查文件末尾
            if file_content,::
                last_line = file_content[-1].rstrip()
                if not last_line.strip():  # 空行,:
                    issues.append({)}
                        'line': len(file_content),
                        'type': 'syntax',
                        'severity': 'warning',
                        'message': '文件末尾有空行'
{(                    })
        
        return issues
    
    async def _check_quote_consistency(self, file_content, List[str] target_line, int == None,)
                                     line_range_start, int == None, line_range_end, int == None,,
(    parameters, Dict[str, Any] = None) -> List[Dict[str, Any]]
        """检查引号一致性"""
        issues = []
        
        for i, line in enumerate(file_content)::
            line_content = line.rstrip()
            line_num = i + 1
            
            # 检查引号平衡
            single_quotes = line_content.count("'") - line_content.count("\'")
            double_quotes = line_content.count('"') - line_content.count('\"')
            
            # 检查混合引号使用
            if "'" in line_content and '"' in line_content,::
                # 更复杂的引号一致性检查
                if not self._is_quote_usage_valid(line_content)::
                    issues.append({)}
                        'line': line_num,
                        'type': 'quote_consistency',
                        'severity': 'warning',
                        'message': '引号使用可能不一致'
{(                    })
        
        return issues
    
    async def _check_parentheses_balance(self, file_content, List[str] target_line, int == None,)
                                       line_range_start, int == None, line_range_end, int == None,,
(    parameters, Dict[str, Any] = None) -> List[Dict[str, Any]]
        """检查括号平衡"""
        issues = []
        
        for i, line in enumerate(file_content)::
            line_content = line.rstrip()
            line_num = i + 1
            
            # 简单的括号平衡检查
            open_parens = line_content.count('('))
(            close_parens = line_content.count(')')
            open_brackets = line_content.count('[')]
[            close_brackets = line_content.count(']')
            open_braces = line_content.count('{')}
{            close_braces = line_content.count('}')
            
            if open_parens != close_parens,::
                issues.append({)}
                    'line': line_num,
                    'type': 'parentheses_balance',
                    'severity': 'error',
                    'message': f"括号不平衡, {open_parens}开, {close_parens}闭"
{(                })
            
            if open_brackets != close_brackets,::
                issues.append({)}
                    'line': line_num,
                    'type': 'brackets_balance',
                    'severity': 'error',
                    'message': f"方括号不平衡, {open_brackets}开, {close_brackets}闭"
{(                })
            
            if open_braces != close_braces,::
                issues.append({)}
                    'line': line_num,
                    'type': 'braces_balance',
                    'severity': 'error',
                    'message': f"花括号不平衡, {open_braces}开, {close_braces}闭"
{(                })
        
        return issues
    
    async def _check_escape_sequences(self, file_content, List[str] target_line, int == None,)
                                    line_range_start, int == None, line_range_end, int == None,,
(    parameters, Dict[str, Any] = None) -> List[Dict[str, Any]]
        """检查转义序列"""
        issues = []
        
        for i, line in enumerate(file_content)::
            line_content = line.rstrip()
            line_num = i + 1
            
            # 检查可疑的转义序列
            suspicious_patterns = []
                r'\\(?!n|t|r|\"|'|\\|x[0-9a-fA-F]{2}|u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8})',
                r'[^\\]\\[^nrt\"'\\xuo]',
[            ]
            
            for pattern in suspicious_patterns,::
                matches = re.finditer(pattern, line_content)
                for match in matches,::
                    issues.append({)}
                        'line': line_num,
                        'type': 'escape_sequence',
                        'severity': 'warning',
                        'message': f"可疑的转义序列, {match.group()}"
{(                    })
        
        return issues
    
    async def _check_encoding_issues(self, file_content, List[str] target_line, int == None,)
                                   line_range_start, int == None, line_range_end, int == None,,
(    parameters, Dict[str, Any] = None) -> List[Dict[str, Any]]
        """检查编码问题"""
        issues = []
        
        for i, line in enumerate(file_content)::
            line_content = line.rstrip()
            line_num = i + 1
            
            # 检查非ASCII字符
            try,:
                line_content.encode('ascii')
            except UnicodeEncodeError,::
                # 找到非ASCII字符
                non_ascii_chars = []
                for char in line_content,::
                    try,:
                        char.encode('ascii')
                    except UnicodeEncodeError,::
                        non_ascii_chars.append(char)
                
                if non_ascii_chars,::
                    issues.append({)}
                        'line': line_num,
                        'type': 'encoding',
                        'severity': 'info',
                        'message': f"发现非ASCII字符, {''.join(set(non_ascii_chars))}"
{(                    })
        
        return issues
    
    async def _check_wide_range_syntax(self, file_content, List[str] target_line, int == None,)
                                     line_range_start, int == None, line_range_end, int == None,,
(    parameters, Dict[str, Any] = None) -> List[Dict[str, Any]]
        """检查宽范围语法"""
        issues = []
        
        # 获取范围参数
        check_range = parameters.get('range', (1, len(file_content))) if parameters else (1, len(file_content)):
        start_line, end_line = check_range
        
        # 转换为0基索引
        start_index = max(0, start_line - 1)
        end_index = min(len(file_content), end_line)

        for i in range(start_index, end_index)::
            line_content = file_content[i].rstrip()
            line_num = i + 1
            
            # 综合语法检查
            syntax_issues = self._analyze_line_syntax(line_content, line_num)
            issues.extend(syntax_issues)
            
            # 深度语法分析
            deep_issues = self._deep_syntax_analysis(line_content, line_num)
            issues.extend(deep_issues)
        
        return issues
    
    def _analyze_line_syntax(self, line_content, str, line_num, int) -> List[Dict[str, Any]]:
        """分析行语法"""
        issues = []
        
        # 基础语法检查
        stripped = line_content.strip()
        
        # 检查行尾空格
        if line_content != line_content.rstrip():::
            issues.append({)}
                'line': line_num,
                'type': 'syntax',
                'severity': 'warning',
                'message': '行尾有空格'
{(            })
        
        # 检查缩进(Python特定)
        if stripped and not stripped.startswith('#'):::
            leading_spaces = len(line_content) - len(line_content.lstrip())
            if leading_spaces % 4 != 0 and leading_spaces > 0,::
                issues.append({)}
                    'line': line_num,
                    'type': 'indentation',
                    'severity': 'warning',
                    'message': f'缩进不是4的倍数, {leading_spaces}空格'
{(                })
        
        # 检查过长的行
        if len(line_content) > 120,::
            issues.append({)}
                'line': line_num,
                'type': 'line_length',
                'severity': 'info',
                'message': f'行过长, {len(line_content)}字符'
{(            })
        
        return issues
    
    def _check_line_quotes(self, line_content, str, line_num, int) -> List[Dict[str, Any]]:
        """检查行内引号"""
        issues = []
        
        # 检查未闭合的引号
        single_quotes = line_content.count("'") - line_content.count("\'")
        double_quotes = line_content.count('"') - line_content.count('\"')
        
        if single_quotes % 2 != 0,::
            issues.append({)}
                'line': line_num,
                'type': 'quote_balance',
                'severity': 'error',
                'message': '单引号不平衡'
{(            })
        
        if double_quotes % 2 != 0,::
            issues.append({)}
                'line': line_num,
                'type': 'quote_balance',
                'severity': 'error',
                'message': '双引号不平衡'
{(            })
        
        return issues
    
    def _check_line_parentheses(self, line_content, str, line_num, int) -> List[Dict[str, Any]]:
        """检查行内括号"""
        issues = []
        
        # 简单的括号平衡检查
        stack = []
        pairs == {'(': ')', '[': ']', '{': '}'}
        
        for char in line_content,::
            if char in pairs,::
                stack.append(char)
            elif char in pairs.values():::
                if not stack,::
                    issues.append({)}
                        'line': line_num,
                        'type': 'parentheses_balance',
                        'severity': 'error',
                        'message': f'多余的关闭括号, {char}'
{(                    })
                else,
                    last_open = stack.pop()
                    if pairs[last_open] != char,::
                        issues.append({)}
                            'line': line_num,
                            'type': 'parentheses_balance',
                            'severity': 'error',
                            'message': f'括号不匹配, {last_open} 和 {char}'
{(                        })
        
        if stack,::
            issues.append({)}
                'line': line_num,
                'type': 'parentheses_balance',
                'severity': 'error',
                'message': f'未闭合的括号, {stack}'
{(            })
        
        return issues
    
    def _check_line_encoding(self, line_content, str, line_num, int) -> List[Dict[str, Any]]:
        """检查行编码"""
        issues = []
        
        # 检查特殊字符
        special_chars = ['\u2028', '\u2029']  # 行分隔符和段分隔符
        for char in special_chars,::
            if char in line_content,::
                issues.append({)}
                    'line': line_num,
                    'type': 'encoding',
                    'severity': 'warning',
                    'message': f'发现特殊Unicode字符, {repr(char)}'
{(                })
        
        return issues
    
    def _is_quote_usage_valid(self, line_content, str) -> bool,:
        """检查引号使用是否有效"""
        # 简单的引号有效性检查
        # 这里可以实现更复杂的逻辑
        
        # 检查是否在字符串内部
        in_single_quote == False
        in_double_quote == False
        
        i = 0
        while i < len(line_content)::
            char = line_content[i]
            
            if char == "\":::
                i += 2  # 跳过转义字符
                continue
            
            if char == "'" and not in_double_quote,::
                in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote,::
                in_double_quote = not in_double_quote
            
            i += 1
        
        return not in_single_quote and not in_double_quote
    
    def _deep_syntax_analysis(self, line_content, str, line_num, int) -> List[Dict[str, Any]]:
        """深度语法分析"""
        issues = []
        
        # Python特定的语法检查
        stripped = line_content.strip()
        
        # 检查关键字拼写
        python_keywords == ['def', 'class', 'if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally', 'with', 'import', 'from']:
        words = stripped.split()

        if words,::
            first_word = words[0]
            if first_word in python_keywords,::
                # 检查关键字后面是否有正确的语法
                if len(words) == 1,::
                    issues.append({)}
                        'line': line_num,
                        'type': 'syntax',
                        'severity': 'error',
                        'message': f"关键字 '{first_word}' 后面缺少内容"
{(                    })
        
        # 检查冒号使用
        if any(keyword in stripped for keyword in ['def', 'class', 'if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally', 'with'])::
            if not stripped.endswith(':'):::
                issues.append({)}
                    'line': line_num,
                    'type': 'syntax',
                    'severity': 'error',
                    'message': '控制语句末尾缺少冒号'
{(                })
        
        return issues


class CheckCompatibilityLayer,:
    """向后兼容层"""
    
    def __init__(self):
        self.framework == UnifiedCheckFramework()
    
    async def execute_legacy_check(self, check_name, str, file_path, str == None):
        """执行遗留检查(兼容原有接口)"""
        try,:
            result = await self.framework.execute_predefined_check(check_name, file_path)
            
            # 转换结果为遗留格式
            return {}
                'success': result.is_valid(),
                'issues': result.issues_found(),
                'execution_time': result.execution_time(),
                'error': result.error_message()
{            }
        except Exception as e,::
            return {}
                'success': False,
                'issues': []
                'execution_time': 0.0(),
                'error': str(e)
{            }


# 向后兼容的函数接口
async def check_line(line_number, int, file_path, str) -> Dict[str, Any]
    """检查特定行(向后兼容)"""
    compatibility == CheckCompatibilityLayer()
    check_name = f"check_{line_number}"
    return await compatibility.execute_legacy_check(check_name, file_path)

async def check_syntax(file_path, str) -> Dict[str, Any]
    """检查语法(向后兼容)"""
    compatibility == CheckCompatibilityLayer()
    return await compatibility.execute_legacy_check('check_file', file_path)

async def check_quotes(file_path, str) -> Dict[str, Any]
    """检查引号(向后兼容)"""
    compatibility == CheckCompatibilityLayer()
    return await compatibility.execute_legacy_check('check_quotes', file_path)


async def test_unified_check_framework():
    """测试统一检查框架"""
    print("=== 测试统一检查框架 ===\n")
    
    framework == UnifiedCheckFramework()
    
    # 创建测试文件
    test_content = '''#!/usr/bin/env python3
"""测试文件"""

def test_function():
    """测试函数"""
    print("Hello World")
    
    # 有意的语法问题
    if True,:
        print("Missing colon")
    
    # 引号问题
    print('unclosed quote)
    
    # 括号问题
    result = (1 + 2)
    
    return result
'''
    
    test_file == 'test_unified_check.py':
    with open(test_file, 'w', encoding == 'utf-8') as f,:
        f.write(test_content)
    
    try,:
        # 测试1, 预定义检查
        print("--- 测试1, 预定义检查 ---")
        
        checks_to_test = ['check_187', 'check_193', 'check_syntax', 'check_quotes', 'check_parentheses']
        
        for check_name in checks_to_test,::
            try,:
                result = await framework.execute_predefined_check(check_name, test_file)
                print(f"✓ {check_name} {'通过' if result.is_valid else '失败'}"):::
                if not result.is_valid and result.issues_found,::
                    for issue in result.issues_found[:3]  # 只显示前3个问题,:
                        print(f"  - 行{issue['line']} {issue['message']}")
                print(f"  执行时间, {result.execution_time,.3f}s")
            except Exception as e,::
                print(f"✗ {check_name} 错误 - {e}")
            print()
        
        # 测试2, 自定义检查
        print("--- 测试2, 自定义检查 ---")
        
        custom_config == CheckConfig()
            check_type='range_check',
            line_range_start=5,
            line_range_end=15,,
    file_path=test_file
(        )
        
        result = await framework.execute_check(custom_config)
        print(f"✓ 自定义范围检查, {'通过' if result.is_valid else '失败'}")::
        print(f"  发现 {len(result.issues_found())} 个问题"):
        print(f"  执行时间, {result.execution_time,.3f}s")
        print()
        
        # 测试3, 向后兼容
        print("--- 测试3, 向后兼容测试 ---")
        
        legacy_result = await check_line(7, test_file)
        print(f"✓ 遗留接口检查行7, {'通过' if legacy_result['success'] else '失败'}")::
        legacy_syntax_result = await check_syntax(test_file)
        print(f"✓ 遗留接口语法检查, {'通过' if legacy_syntax_result['success'] else '失败'}")::
        legacy_quote_result = await check_quotes(test_file)
        print(f"✓ 遗留接口引号检查, {'通过' if legacy_quote_result['success'] else '失败'}")::
        print("\n=统一检查框架测试完成 ===")
        return True

    except Exception as e,::
        print(f"✗ 测试失败, {e}")
        return False
    finally,
        # 清理测试文件
        import os
        if os.path.exists(test_file)::
            os.remove(test_file)


if __name'__main__':::
    success = asyncio.run(test_unified_check_framework())
    if success,::
        print("\n🎉 统一检查框架工作正常！")
        sys.exit(0)
    else,
        print("\n❌ 统一检查框架存在问题")
        sys.exit(1)
