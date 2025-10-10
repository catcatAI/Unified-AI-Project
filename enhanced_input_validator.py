#!/usr/bin/env python3
"""
增强的输入验证器
修复集成测试中的输入验证问题
"""

import json
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    issues: List[Dict[str, Any]]
    suggestions: List[str]
    confidence_score: float


class EnhancedInputValidator:
    """增强的输入验证器"""
    
    def __init__(self):
        self.validation_rules = {
            'text': self._validate_text_input,
            'code': self._validate_code_input,
            'structured': self._validate_structured_input,
            'json': self._validate_json_input
        }
    
    def validate_input(self, input_data: Dict[str, Any], input_type: str) -> ValidationResult:
        """验证输入数据"""
        if input_type not in self.validation_rules:
            return ValidationResult(
                is_valid=False,
                issues=[{"type": "validation", "severity": "error", "message": f"不支持的输入类型: {input_type}"}],
                suggestions=["请使用支持的输入类型: text, code, structured, json"],
                confidence_score=0.0
            )
        
        return self.validation_rules[input_type](input_data)
    
    def _validate_text_input(self, input_data: Dict[str, Any]) -> ValidationResult:
        """验证文本输入"""
        issues = []
        suggestions = []
        
        content = input_data.get("content", "")
        
        # 基础验证
        if not content or not content.strip():
            issues.append({
                "type": "content",
                "severity": "error",
                "message": "文本内容为空或仅包含空白字符"
            })
            suggestions.append("请提供有意义的文本内容")
        else:
            # 内容质量检查
            if len(content) < 10:
                issues.append({
                    "type": "content_length",
                    "severity": "warning",
                    "message": f"文本内容较短: {len(content)}字符"
                })
                suggestions.append("考虑提供更详细的文本描述")
            
            # 检查是否包含中文字符（对于中文处理）
            chinese_chars = len([c for c in content if '\u4e00' <= c <= '\u9fff'])
            if chinese_chars == 0 and len(content) > 20:
                issues.append({
                    "type": "language",
                    "severity": "info",
                    "message": "文本中未检测到中文字符"
                })
            
            # 检查特殊字符比例
            special_chars = len([c for c in content if not c.isalnum() and not c.isspace()])
            if len(content) > 0:
                special_ratio = special_chars / len(content)
                if special_ratio > 0.3:
                    issues.append({
                        "type": "special_chars",
                        "severity": "warning",
                        "message": f"特殊字符比例较高: {special_ratio:.1%}"
                    })
        
        # 元数据验证
        metadata = input_data.get("metadata", {})
        if not isinstance(metadata, dict):
            issues.append({
                "type": "metadata",
                "severity": "error",
                "message": "metadata必须是字典类型"
            })
        else:
            # 检查时间戳格式
            if "timestamp" in metadata:
                if not self._is_valid_timestamp(metadata["timestamp"]):
                    issues.append({
                        "type": "timestamp",
                        "severity": "warning",
                        "message": "时间戳格式可能不正确"
                    })
        
        # 计算置信度分数
        confidence_score = self._calculate_confidence_score(issues)
        
        # 确定整体有效性
        is_valid = not any(issue["severity"] == "error" for issue in issues)
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            suggestions=suggestions,
            confidence_score=confidence_score
        )
    
    def _validate_code_input(self, input_data: Dict[str, Any]) -> ValidationResult:
        """验证代码输入"""
        issues = []
        suggestions = []
        
        content = input_data.get("content", "")
        metadata = input_data.get("metadata", {})
        
        # 基础验证
        if not content or not content.strip():
            issues.append({
                "type": "content",
                "severity": "error",
                "message": "代码内容为空"
            })
            suggestions.append("请提供有效的代码内容")
        else:
            # 代码结构检查
            lines = content.split('\n')
            
            # 检查行数
            if len(lines) < 2:
                issues.append({
                    "type": "code_structure",
                    "severity": "info",
                    "message": "代码只有一行，可能过于简单"
                })
            
            # 检查缩进一致性
            indentations = []
            for line in lines:
                if line.strip():  # 跳过空行
                    indent = len(line) - len(line.lstrip())
                    indentations.append(indent)
            
            if indentations:
                # 检查是否使用空格缩进
                space_indents = [i for i in indentations if i > 0]
                if space_indents:
                    # 检查缩进是否为4的倍数（Python风格）
                    non_four_multiples = [i for i in space_indents if i % 4 != 0]
                    if non_four_multiples:
                        issues.append({
                            "type": "indentation",
                            "severity": "warning",
                            "message": f"发现非4倍数缩进: {set(non_four_multiples)}"
                        })
            
            # 检查括号平衡
            brackets = {'(': ')', '[': ']', '{': '}'}
            for open_bracket, close_bracket in brackets.items():
                open_count = content.count(open_bracket)
                close_count = content.count(close_bracket)
                if open_count != close_count:
                    issues.append({
                        "type": "bracket_balance",
                        "severity": "error",
                        "message": f"{open_bracket}{close_bracket}括号不平衡: {open_count}开, {close_count}闭"
                    })
            
            # 检查Python关键字（如果指定为Python代码）
            if metadata.get("language") == "python":
                python_keywords = ['def', 'class', 'if', 'elif', 'else', 'for', 'while', 'import', 'from']
                has_keyword = any(keyword in content for keyword in python_keywords)
                if not has_keyword and len(content) > 20:
                    issues.append({
                        "type": "python_structure",
                        "severity": "info",
                        "message": "未检测到Python关键字，可能是简单表达式"
                    })
        
        # 元数据验证
        if "language" in metadata:
            if metadata["language"] not in ["python", "javascript", "java", "cpp", "go", "rust"]:
                issues.append({
                    "type": "language",
                    "severity": "warning",
                    "message": f"不常见的编程语言: {metadata['language']}"
                })
        
        if "complexity" in metadata:
            complexity = metadata["complexity"]
            valid_complexities = ["simple", "medium", "complex"]
            if complexity not in valid_complexities:
                issues.append({
                    "type": "complexity",
                    "severity": "warning",
                    "message": f"未知的复杂度级别: {complexity}"
                })
        
        confidence_score = self._calculate_confidence_score(issues)
        is_valid = not any(issue["severity"] == "error" for issue in issues)
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            suggestions=suggestions,
            confidence_score=confidence_score
        )
    
    def _validate_structured_input(self, input_data: Dict[str, Any]) -> ValidationResult:
        """验证结构化输入"""
        issues = []
        suggestions = []
        
        content = input_data.get("content")
        
        # 基础验证
        if content is None:
            issues.append({
                "type": "content",
                "severity": "error",
                "message": "结构化内容不能为空"
            })
            suggestions.append("请提供有效的结构化数据")
        elif not isinstance(content, dict):
            issues.append({
                "type": "content_type",
                "severity": "error",
                "message": "结构化内容必须是字典类型"
            })
            suggestions.append("结构化内容应该是键值对形式")
        else:
            # 验证字典结构
            if len(content) == 0:
                issues.append({
                    "type": "content_empty",
                    "severity": "warning",
                    "message": "结构化内容为空字典"
                })
            
            # 检查键名有效性
            for key in content.keys():
                if not isinstance(key, str):
                    issues.append({
                        "type": "key_type",
                        "severity": "error",
                        "message": f"键必须是字符串类型: {type(key)}"
                    })
                    break
                
                if not key.replace('_', '').isalnum():
                    issues.append({
                        "type": "key_format",
                        "severity": "warning",
                        "message": f"键名格式不规范: {key}"
                    })
            
            # 检查值类型
            for key, value in content.items():
                if isinstance(value, (str, int, float, bool, list, dict)):
                    continue
                else:
                    issues.append({
                        "type": "value_type",
                        "severity": "warning",
                        "message": f"不支持的值类型: {key} = {type(value)}"
                    })
        
        # 元数据验证
        metadata = input_data.get("metadata", {})
        if "format" in metadata:
            if metadata["format"] not in ["json", "dict", "structured"]:
                issues.append({
                    "type": "format",
                    "severity": "warning",
                    "message": f"不常见的格式类型: {metadata['format']}"
                })
        
        if "schema_version" in metadata:
            schema_version = metadata["schema_version"]
            if not isinstance(schema_version, str):
                issues.append({
                    "type": "schema_version",
                    "severity": "warning",
                    "message": f"schema_version应该是字符串类型: {type(schema_version)}"
                })
        
        confidence_score = self._calculate_confidence_score(issues)
        is_valid = not any(issue["severity"] == "error" for issue in issues)
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            suggestions=suggestions,
            confidence_score=confidence_score
        )
    
    def _validate_json_input(self, input_data: Dict[str, Any]) -> ValidationResult:
        """验证JSON输入"""
        # JSON输入可以视为结构化输入的特例
        result = self._validate_structured_input(input_data)
        
        # 额外的JSON特定验证
        additional_issues = []
        
        try:
            # 尝试序列化为JSON来验证其有效性
            json.dumps(input_data)
        except (TypeError, ValueError) as e:
            additional_issues.append({
                "type": "json_serializable",
                "severity": "error",
                "message": f"数据无法序列化为JSON: {str(e)}"
            })
        
        result.issues.extend(additional_issues)
        
        return result
    
    def _is_valid_timestamp(self, timestamp: str) -> bool:
        """检查时间戳格式是否有效"""
        try:
            # 尝试解析ISO格式时间戳
            from datetime import datetime
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return True
        except (ValueError, AttributeError):
            return False
    
    def _calculate_confidence_score(self, issues: List[Dict[str, Any]]) -> float:
        """计算置信度分数"""
        if not issues:
            return 1.0
        
        # 根据问题严重程度计算分数
        severity_weights = {
            "error": 0.0,
            "warning": 0.7,
            "info": 0.9
        }
        
        scores = []
        for issue in issues:
            severity = issue.get("severity", "info")
            weight = severity_weights.get(severity, 0.9)
            scores.append(weight)
        
        # 取平均分数
        return sum(scores) / len(scores)


def create_smart_validator() -> EnhancedInputValidator:
    """创建智能验证器"""
    return EnhancedInputValidator()


async def test_enhanced_validator():
    """测试增强验证器"""
    print("=== 测试增强输入验证器 ===\n")
    
    validator = create_smart_validator()
    
    # 测试用例
    test_cases = [
        {
            "name": "有效的文本输入",
            "input": {
                "type": "text",
                "content": "请分析这个Python函数的功能和实现细节",
                "metadata": {"source": "user", "timestamp": "2025-10-10T10:00:00"}
            }
        },
        {
            "name": "有效的代码输入",
            "input": {
                "type": "code",
                "content": "def add(x, y):\n    return x + y",
                "metadata": {"language": "python", "complexity": "simple"}
            }
        },
        {
            "name": "有效的结构化输入",
            "input": {
                "type": "structured",
                "content": {
                    "task": "code_analysis",
                    "parameters": {
                        "target_file": "example.py",
                        "analysis_type": "comprehensive"
                    }
                },
                "metadata": {"format": "json", "schema_version": "1.0"}
            }
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"--- {test_case['name']} ---")
        
        input_type = test_case["input"]["type"]
        result = validator.validate_input(test_case["input"], input_type)
        
        print(f"验证结果: {'✅ 通过' if result.is_valid else '❌ 失败'}")
        print(f"置信度分数: {result.confidence_score:.2f}")
        
        if result.issues:
            print("发现的问题:")
            for issue in result.issues:
                print(f"  - {issue['severity']}: {issue['message']}")
        
        if result.suggestions:
            print("建议:")
            for suggestion in result.suggestions:
                print(f"  - {suggestion}")
        
        if not result.is_valid:
            all_passed = False
        
        print()
    
    print("=== 增强验证器测试完成 ===")
    return all_passed


if __name__ == '__main__':
    import asyncio
    success = asyncio.run(test_enhanced_validator())
    
    if success:
        print("\n🎉 增强输入验证器工作正常！")
        exit(0)
    else:
        print("\n❌ 增强输入验证器存在问题")
        exit(1)
