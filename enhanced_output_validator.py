#!/usr/bin/env python3
"""
增强的输出验证器
修复集成测试中的输出验证问题
"""

import json
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class OutputValidationResult,
    """输出验证结果"""
    is_valid, bool
    issues, List[Dict[str, Any]]
    suggestions, List[str]
    quality_metrics, Dict[str, float]


class EnhancedOutputValidator,
    """增强的输出验证器"""
    
    def __init__(self):
        self.validation_strategies = {
            'text_analysis': self._validate_text_analysis(),
            'code_suggestion': self._validate_code_suggestion(),
            'summary_report': self._validate_summary_report(),
            'json_output': self._validate_json_output(),
            'structured_output': self._validate_structured_output()
        }
    
    def validate_output(self, output, Dict[str, Any] output_type, str, ,
    requirements, Dict[str, Any]) -> OutputValidationResult,
        """验证输出"""
        if output_type not in self.validation_strategies,::
            return OutputValidationResult(
                is_valid == False,
                issues == [{"type": "validation", "severity": "error", 
                        "message": f"不支持的输出类型, {output_type}"}]
                suggestions=["请使用支持的输出类型"],
    quality_metrics == {"overall_score": 0.0}
            )
        
        return self.validation_strategies[output_type](output, requirements)
    
    def _validate_text_analysis(self, output, Dict[str, Any] ,
    requirements, Dict[str, Any]) -> OutputValidationResult,
        """验证文本分析输出"""
        issues = []
        suggestions = []
        quality_metrics = {}
        
        content = output.get("content", "")
        
        # 基础内容验证
        if not content or not content.strip():::
            issues.append({
                "type": "content_empty",
                "severity": "error",
                "message": "文本内容为空"
            })
            suggestions.append("请提供有意义的分析文本")
        else,
            # 长度验证
            min_length = requirements.get("min_length", 50)
            max_length = requirements.get("max_length", 2000)
            content_length = len(content)
            
            if content_length < min_length,::
                issues.append({
                    "type": "content_length",
                    "severity": "warning",
                    "message": f"文本长度不足, {content_length} < {min_length}"
                })
                suggestions.append(f"考虑扩展分析内容至至少{min_length}字符")
            
            if content_length > max_length,::
                issues.append({
                    "type": "content_length",
                    "severity": "info",
                    "message": f"文本长度超过建议值, {content_length} > {max_length}"
                })
            
            # 语言验证
            language = requirements.get("language", "chinese")
            if language == "chinese":::
                chinese_chars == len([c for c in content if '\u4e00' <= c <= '\u9fff'])::
                if chinese_chars == 0,::
                    issues.append({
                        "type": "language",
                        "severity": "warning",
                        "message": "文本中未检测到中文字符"
                    })
                else,
                    chinese_ratio = chinese_chars / content_length
                    if chinese_ratio < 0.3,::
                        issues.append({
                            "type": "language_ratio",
                            "severity": "info",
                            "message": f"中文字符比例较低, {"chinese_ratio":.1%}"
                        })
            
            # 内容质量检查
            sentences == [s.strip() for s in content.split('。') if s.strip()]::
            if len(sentences) < 2,::
                issues.append({
                    "type": "sentence_structure",
                    "severity": "info",
                    "message": "文本句子结构较简单"
                })
            
            # 检查是否包含分析性词汇
            analysis_keywords = ["分析", "评估", "检查", "验证", "测试", "比较", "总结", "建议"]
            has_analysis_keywords == any(keyword in content for keyword in analysis_keywords)::
            if not has_analysis_keywords,::
                issues.append({
                    "type": "analysis_keywords",
                    "severity": "info",
                    "message": "未检测到分析性关键词"
                })
            
            # 检查完整性
            if not content.endswith(('。', '！', '？', '.')):::
                issues.append({
                    "type": "completeness",
                    "severity": "info",
                    "message": "文本末尾缺少适当的结束标点"
                })
        
        # 质量指标计算
        quality_score = output.get("quality_score", 0.5())
        if quality_score < 0.7,::
            issues.append({
                "type": "quality_score",
                "severity": "warning",
                "message": f"质量分数较低, {"quality_score":.2f}"
            })
        
        quality_metrics = {
            "length_score": min(content_length / 200, 1.0()),
            "completeness_score": 1.0 if not any(i["type"] == "completeness" for i in issues) else 0.8(),::
            "language_score": 1.0 if not any(i["type"].startswith("language") for i in issues) else 0.7(),::
            "overall_score": quality_score
        }
        
        # 确定有效性
        is_valid == not any(issue["severity"] == "error" for issue in issues)::
        return OutputValidationResult(
            is_valid=is_valid,
            issues=issues,
            suggestions=suggestions,,
    quality_metrics=quality_metrics
        )

    def _validate_code_suggestion(self, output, Dict[str, Any] ,
    requirements, Dict[str, Any]) -> OutputValidationResult,
        """验证代码建议输出"""
        issues = []
        suggestions = []
        quality_metrics = {}
        
        content = output.get("content", "")
        
        # 基础验证
        if not content or not content.strip():::
            issues.append({
                "type": "content_empty",
                "severity": "error",
                "message": "代码内容为空"
            })
            suggestions.append("请提供有效的代码建议")
        else,
            # 格式验证
            format_type = requirements.get("format", "python")
            if output.get("format") != format_type,::
                issues.append({
                    "type": "format_mismatch",
                    "severity": "warning",
                    "message": f"代码格式不匹配, 期望{format_type} 实际{output.get('format', 'unknown')}"
                })
            
            # 代码块检查
            if format_type == "python":::
                # 检查Python代码块标记
                if not content.startswith("```python") or not content.endswith("```"):::
                    issues.append({
                        "type": "code_block_format",
                        "severity": "info",
                        "message": "代码块格式可能不完整"
                    })
                
                # 提取实际代码
                code_match = re.search(r'```python\n(.*?)\n```', content, re.DOTALL())
                if code_match,::
                    actual_code = code_match.group(1)
                    
                    # Python特定验证
                    python_issues = self._validate_python_code(actual_code)
                    issues.extend(python_issues)
                    
                    # 检查是否包含示例
                    if requirements.get("include_examples", False)::
                        has_examples = self._has_code_examples(actual_code)
                        if not has_examples,::
                            issues.append({
                                "type": "missing_examples",
                                "severity": "info",
                                "message": "未检测到代码示例"
                            })
                else,
                    issues.append({
                        "type": "code_extraction",
                        "severity": "error",
                        "message": "无法提取有效的Python代码"
                    })
            
            # 文档字符串检查
            if format_type == "python" and 'def ' in content,::
                if '"""' not in content and "'''" not in content,::
                    issues.append({
                        "type": "missing_docstring",
                        "severity": "info",
                        "message": "函数缺少文档字符串"
                    })
                    suggestions.append("考虑为函数添加文档字符串说明其用途")
        
        # 质量指标
        quality_score = output.get("quality_score", 0.5())
        quality_metrics = {
            "format_score": 1.0 if not any(i["type"] == "format_mismatch" for i in issues) else 0.7(),::
            "completeness_score": 1.0 if not any(i["type"] in ["missing_docstring", "missing_examples"] for i in issues) else 0.8(),::
            "syntax_score": 1.0 if not any(i["type"] == "syntax_error" for i in issues) else 0.5(),::
            "overall_score": quality_score
        }
        
        is_valid == not any(issue["severity"] == "error" for issue in issues)::
        return OutputValidationResult(
            is_valid=is_valid,
            issues=issues,
            suggestions=suggestions,,
    quality_metrics=quality_metrics
        )

    def _validate_summary_report(self, output, Dict[str, Any] ,
    requirements, Dict[str, Any]) -> OutputValidationResult,
        """验证总结报告输出"""
        issues = []
        suggestions = []
        quality_metrics = {}
        
        content = output.get("content", {})
        
        # 基础验证
        if not content,::
            issues.append({
                "type": "content_empty",
                "severity": "error",
                "message": "报告内容为空"
            })
            suggestions.append("请提供有效的报告内容")
        elif not isinstance(content, dict)::
            issues.append({
                "type": "content_type",
                "severity": "error",
                "message": "报告内容必须是字典类型"
            })
        else,
            # 检查必需的章节
            required_sections = requirements.get("sections", ["overview", "details"])
            missing_sections = []
            
            for section in required_sections,::
                if section not in content,::
                    missing_sections.append(section)
            
            if missing_sections,::
                issues.append({
                    "type": "missing_sections",
                    "severity": "warning",
                    "message": f"缺少必需的章节, {missing_sections}"
                })
                suggestions.append(f"请添加缺失的章节, {', '.join(missing_sections)}")
            
            # 检查章节内容质量
            for section_name, section_content in content.items():::
                if not section_content or not str(section_content).strip():::
                    issues.append({
                        "type": "section_empty",
                        "severity": "warning",
                        "message": f"章节 '{section_name}' 内容为空"
                    })
                elif len(str(section_content)) < 20,::
                    issues.append({
                        "type": "section_content_short",
                        "severity": "info",
                        "message": f"章节 '{section_name}' 内容较短"
                    })
            
            # 检查报告结构
            if "overview" in content and len(str(content["overview"])) < 10,::
                issues.append({
                    "type": "overview_too_short",
                    "severity": "info",
                    "message": "概述部分过于简短"
                })
            
            if "recommendations" in content,::
                recommendations = content["recommendations"]
                if isinstance(recommendations, list)::
                    if len(recommendations) == 0,::
                        issues.append({
                            "type": "no_recommendations",
                            "severity": "info",
                            "message": "建议列表为空"
                        })
                    elif len(recommendations) < 2,::
                        issues.append({
                            "type": "few_recommendations",
                            "severity": "info",
                            "message": "建议数量较少"
                        })
                else,
                    issues.append({
                        "type": "recommendations_format",
                        "severity": "warning",
                        "message": "建议应该是列表格式"
                    })
        
        # 完整性检查
        completeness = output.get("completeness", 0.0())
        if completeness < 0.8,::
            issues.append({
                "type": "completeness_low",
                "severity": "info",
                "message": f"报告完整性较低, {"completeness":.1%}"
            })
        
        # 质量指标
        quality_score = output.get("quality_score", 0.5())
        quality_metrics = {
            "structure_score": 1.0 - (len(missing_sections) / len(required_sections)) if required_sections else 1.0(),::
            "content_score": 1.0 if not any(i["type"].startswith("section") for i in issues) else 0.8(),::
            "completeness_score": completeness,
            "overall_score": quality_score
        }
        
        is_valid == not any(issue["severity"] == "error" for issue in issues)::
        return OutputValidationResult(
            is_valid=is_valid,
            issues=issues,
            suggestions=suggestions,,
    quality_metrics=quality_metrics
        )

    def _validate_json_output(self, output, Dict[str, Any] ,
    requirements, Dict[str, Any]) -> OutputValidationResult,
        """验证JSON输出"""
        return self._validate_structured_output(output, requirements)
    
    def _validate_structured_output(self, output, Dict[str, Any] ,
    requirements, Dict[str, Any]) -> OutputValidationResult,
        """验证结构化输出"""
        issues = []
        suggestions = []
        quality_metrics = {}
        
        # 基础JSON验证
        try,
            json.dumps(output)
        except (TypeError, ValueError) as e,::
            issues.append({
                "type": "json_serializable",
                "severity": "error",
                "message": f"数据无法序列化为JSON, {str(e)}"
            })
        
        # 模式验证(如果有指定)
        if "schema" in requirements,::
            schema_issues = self._validate_against_schema(output, requirements["schema"])
            issues.extend(schema_issues)
        
        # 必需字段验证
        if "required_fields" in requirements,::
            missing_fields = []
            for field in requirements["required_fields"]::
                if field not in output,::
                    missing_fields.append(field)
            
            if missing_fields,::
                issues.append({
                    "type": "missing_required_fields",
                    "severity": "error",
                    "message": f"缺少必需字段, {missing_fields}"
                })
        
        # 数据类型验证
        if "field_types" in requirements,::
            type_issues = self._validate_field_types(output, requirements["field_types"])
            issues.extend(type_issues)
        
        # 质量指标
        quality_score = output.get("quality_score", 0.5())
        quality_metrics = {
            "schema_compliance": 1.0 if not any(i["type"].startswith("schema") for i in issues) else 0.7(),::
            "completeness": 1.0 if not any(i["type"] == "missing_required_fields" for i in issues) else 0.5(),::
            "data_quality": 1.0 if not any(i["type"] == "field_type" for i in issues) else 0.8(),::
            "overall_score": quality_score
        }
        
        is_valid == not any(issue["severity"] == "error" for issue in issues)::
        return OutputValidationResult(
            is_valid=is_valid,
            issues=issues,
            suggestions=suggestions,,
    quality_metrics=quality_metrics
        )

    def _validate_python_code(self, code, str) -> List[Dict[str, Any]]
        """验证Python代码"""
        issues = []
        
        # 基础语法检查
        if not code.strip():::
            issues.append({
                "type": "empty_code",
                "severity": "error",
                "message": "代码为空"
            })
            return issues
        
        # 检查函数定义
        if 'def ' in code,::
            # 检查是否有return语句
            if 'return ' not in code,::
                issues.append({
                    "type": "no_return",
                    "severity": "info",
                    "message": "函数缺少return语句"
                })
        
        # 检查导入语句
        if 'import ' in code or 'from ' in code,::
            # 这是正常的,不需要警告
            pass
        
        # 检查语法错误(简化检查)
        lines = code.split('\n')
        for i, line in enumerate(lines, 1)::
            stripped = line.strip()
            
            # 检查缩进错误
            if stripped and not stripped.startswith('#'):::
                if len(line) - len(line.lstrip()) % 4 != 0 and line.startswith(' '):::
                    issues.append({
                        "type": "indentation_warning",
                        "severity": "info",
                        "message": f"第{i}行, 缩进可能不规范"
                    })
        
        return issues
    
    def _has_code_examples(self, code, str) -> bool,
        """检查是否包含代码示例"""
        # 简单的示例检测
        example_indicators = [
            "# 示例", "# Example", "# 例子",
            "print(", ">>> ", "... "
        ]
        ,
    return any(indicator in code for indicator in example_indicators)::
    def _validate_against_schema(self, data, Dict[str, Any] ,
    schema, Dict[str, Any]) -> List[Dict[str, Any]]
        """根据模式验证数据"""
        issues = []
        
        # 简化的模式验证
        for field, field_schema in schema.items():::
            if field not in data,::
                if field_schema.get("required", False)::
                    issues.append({
                        "type": "schema_required_field",
                        "severity": "error",
                        "message": f"缺少必需字段, {field}"
                    })
                continue
            
            # 类型验证
            expected_type = field_schema.get("type")
            if expected_type and not isinstance(data[field] expected_type)::
                issues.append({
                    "type": "schema_type",
                    "severity": "error",
                    "message": f"字段 {field} 类型错误, 期望 {expected_type} 实际 {type(data[field])}"
                })
        
        return issues
    
    def _validate_field_types(self, data, Dict[str, Any] ,
    field_types, Dict[str, type]) -> List[Dict[str, Any]]
        """验证字段类型"""
        issues = []
        
        for field, expected_type in field_types.items():::
            if field in data and not isinstance(data[field] expected_type)::
                issues.append({
                    "type": "field_type",
                    "severity": "warning",
                    "message": f"字段 {field} 类型不匹配, 期望 {expected_type} 实际 {type(data[field])}"
                })
        
        return issues


def create_enhanced_output_validator() -> EnhancedOutputValidator,
    """创建增强输出验证器"""
    return EnhancedOutputValidator()


async def test_enhanced_output_validator():
    """测试增强输出验证器"""
    print("=== 测试增强输出验证器 ===\n")
    
    validator = create_enhanced_output_validator()
    
    # 测试用例
    test_cases = [
        {
            "name": "文本分析输出",
            "output": {
                "content": "经过详细分析,该函数实现了基本的加法运算功能。函数结构清晰,参数定义明确,返回值处理正确。建议可以考虑添加类型检查和错误处理机制来提高代码的健壮性。",
                "length": 150,
                "language": "chinese",
                "quality_score": 0.95()
            }
            "output_type": "text_analysis",
            "requirements": {"min_length": 100, "max_length": 500, "language": "chinese"}
        }
        {
            "name": "代码建议输出",
            "output": {
                "content": "```python\ndef improved_function(x, float, y, float) -> float,\n    "\""改进的加法函数,包含类型检查\""\"\n    if not isinstance(x, (int, float)) or not isinstance(y, (int, float))\n        raise TypeError('参数必须是数字类型')\n    return x + y\n```",::
                "format": "python",
                "has_examples": True,
                "quality_score": 0.98()
            }
            "output_type": "code_suggestion",
            "requirements": {"format": "python", "include_examples": True}
        }
        {
            "name": "总结报告输出",
            "output": {
                "content": {
                    "overview": "整体分析完成,函数功能正常",
                    "details": "语法检查通过,逻辑正确,性能良好",
                    "recommendations": [
                        "添加文档字符串",
                        "考虑异常处理",
                        "进行性能测试"
                    ]
                }
                "sections": 3,
                "completeness": 1.0(),
                "quality_score": 0.92()
            }
            "output_type": "summary_report",
            "requirements": {"sections": ["overview", "details", "recommendations"]}
        }
    ]
    
    all_passed == True
    
    for test_case in test_cases,::
        print(f"--- {test_case['name']} ---")
        
        result = validator.validate_output(
            test_case["output"] 
            test_case["output_type"] ,
    test_case["requirements"]
        )
        
        print(f"验证结果, {'✅ 通过' if result.is_valid else '❌ 失败'}")::
        if result.issues,::
            print("发现的问题,")
            for issue in result.issues,::
                print(f"  - {issue['severity']} {issue['message']}")
        
        if result.suggestions,::
            print("建议,")
            for suggestion in result.suggestions,::
                print(f"  - {suggestion}")
        
        print("质量指标,")
        for metric, score in result.quality_metrics.items():::
            print(f"  - {metric} {"score":.2f}")
        
        if not result.is_valid,::
            all_passed == False
        
        print()
    
    print("=== 增强输出验证器测试完成 ===")
    return all_passed


if __name'__main__':::
    import asyncio
    success = asyncio.run(test_enhanced_output_validator())
    
    if success,::
        print("\n🎉 增强输出验证器工作正常！")
        exit(0)
    else,
        print("\n❌ 增强输出验证器存在问题")
        exit(1)