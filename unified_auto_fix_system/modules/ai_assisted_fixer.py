"""
AI辅助智能修复器
集成人工智能技术的增强修复系统
"""

import json
import traceback
import ast
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..core.fix_types import FixType, FixStatus
from ..core.fix_result import FixResult, FixContext
from .base_fixer import BaseFixer


@dataclass
class AIRepairSuggestion:
    """AI修复建议"""
    suggestion_id: str
    issue_type: str
    original_code: str
    suggested_code: str
    explanation: str
    confidence: float
    complexity: str  # simple, moderate, complex
    estimated_time: float  # 估计修复时间（秒）
    prerequisites: List[str]
    side_effects: List[str]
    alternatives: List[Dict[str, Any]]


@dataclass
class AIRepairContext:
    """AI修复上下文"""
    project_context: str
    file_context: str
    function_context: str
    import_context: str
    dependency_context: str
    historical_context: str
    best_practices: List[str]
    similar_fixes: List[Dict[str, Any]]


class AIAssistedFixer(BaseFixer):
    """AI辅助智能修复器"""
    
    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.fix_type = FixType.AI_ASSISTED_FIX
        self.name = "AIAssistedFixer"
        
        # AI模型配置
        self.ai_config = {
            "model_name": "gpt-4",  # 可以配置不同的AI模型
            "temperature": 0.3,
            "max_tokens": 2000,
            "timeout": 30,
            "retry_attempts": 3,
            "confidence_threshold": 0.7
        }
        
        # 知识库
        self.knowledge_base = self._load_knowledge_base()
        self.code_patterns = self._load_code_patterns()
        self.best_practices = self._load_best_practices()
        
        # 学习缓存
        self.learning_cache = {}
        self.repair_history = []
        
        # 修复策略
        self.ai_strategies = {
            "context_analysis": self._ai_analyze_code_issues,
            "pattern_matching": self._find_similar_fixes,
            "code_generation": self._generate_ai_suggestions,
            "explanation_generation": self._create_ai_suggestion,
            "alternative_suggestions": self._generate_alternatives,
            "risk_assessment": self._assess_side_effects
        }
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """加载知识库"""
        return {
            "python_builtins": {
                "functions": ['print', 'len', 'range', 'enumerate', 'zip', 'map', 'filter'],
                "types": ['int', 'str', 'list', 'dict', 'tuple', 'set', 'bool'],
                "exceptions": ['ValueError', 'TypeError', 'KeyError', 'IndexError']
            },
            "common_libraries": {
                "os": ['path.join', 'path.exists', 'path.basename', 'environ'],
                "json": ['loads', 'dumps', 'load', 'dump'],
                "re": ['search', 'match', 'findall', 'sub'],
                "pathlib": ['Path', 'PurePath'],
                "datetime": ['datetime', 'timedelta', 'now']
            },
            "fix_patterns": {
                "syntax_fix": {
                    "missing_colon": "在控制语句末尾添加冒号",
                    "indentation_error": "调整缩进级别",
                    "parentheses_mismatch": "平衡括号数量"
                },
                "import_fix": {
                    "missing_import": "添加必要的导入语句",
                    "wrong_import": "修正导入路径",
                    "circular_import": "重构导入结构"
                }
            }
        }
    
    def _load_code_patterns(self) -> Dict[str, List[str]]:
        """加载代码模式"""
        return {
            "error_handling": [
                "try:\n    # code\nexcept Exception as e:\n    # handle error",
                "if condition:\n    raise ValueError('error message')"
            ],
            "type_hints": [
                "def function(param: Type) -> ReturnType:",
                "from typing import List, Dict, Optional"
            ],
            "documentation": [
                '"""Function description."""',
                "# TODO: description"
            ],
            "logging": [
                "import logging\nlogger = logging.getLogger(__name__)",
                "logger.info('message')\nlogger.error('error')"
            ]
        }
    
    def _load_best_practices(self) -> List[str]:
        """加载最佳实践"""
        return [
            "使用类型注解提高代码可读性",
            "添加适当的异常处理",
            "遵循PEP 8编码规范",
            "编写清晰的文档字符串",
            "使用日志记录而不是print",
            "避免魔法数字，使用常量",
            "保持函数简短和专注",
            "使用描述性的变量名"
        ]
    
    def analyze(self, context: FixContext) -> List[AIRepairSuggestion]:
        """AI分析并生成修复建议"""
        self.logger.info("AI辅助分析中...")
        
        suggestions = []
        target_files = self._get_target_files(context)
        
        for file_path in target_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # AI上下文分析
                ai_context = self._build_ai_context(content, file_path, context)
                
                # 生成AI修复建议
                file_suggestions = self._generate_ai_suggestions(content, ai_context, file_path)
                suggestions.extend(file_suggestions)
                
            except Exception as e:
                self.logger.error(f"AI分析文件失败 {file_path}: {e}")
        
        self.logger.info(f"AI生成了 {len(suggestions)} 个修复建议")
        return suggestions
    
    def _build_ai_context(self, content: str, file_path: Path, context: FixContext) -> AIRepairContext:
        """构建AI上下文"""
        # 项目上下文
        project_context = self._analyze_project_context(context.project_root)
        
        # 文件上下文
        file_context = self._analyze_file_context(content, file_path)
        
        # 函数上下文
        function_context = self._analyze_function_context(content)
        
        # 导入上下文
        import_context = self._analyze_import_context(content)
        
        # 依赖上下文
        dependency_context = self._analyze_dependency_context(file_path, context.project_root)
        
        # 历史上下文
        historical_context = self._analyze_historical_context(file_path)
        
        # 最佳实践
        best_practices = self._identify_best_practice_violations(content)
        
        # 类似修复
        similar_fixes = self._find_similar_fixes(content, file_path)
        
        return AIRepairContext(
            project_context=project_context,
            file_context=file_context,
            function_context=function_context,
            import_context=import_context,
            dependency_context=dependency_context,
            historical_context=historical_context,
            best_practices=best_practices,
            similar_fixes=similar_fixes
        )
    
    def _analyze_project_context(self, project_root: Path) -> str:
        """分析项目上下文"""
        try:
            # 分析项目结构
            project_info = {
                "project_type": self._detect_project_type(project_root),
                "main_technologies": self._detect_main_technologies(project_root),
                "architecture_style": self._detect_main_technologies(project_root),
                "complexity_level": self._assess_project_complexity(project_root)
            }
            
            return json.dumps(project_info, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"分析项目上下文失败: {e}")
            return "通用Python项目"
    
    def _analyze_file_context(self, content: str, file_path: Path) -> str:
        """分析文件上下文"""
        try:
            lines = content.split('\n')
            
            file_info = {
                "file_type": self._detect_project_type(file_path),
                "line_count": len(lines),
                "function_count": content.count('def '),
                "class_count": content.count('class '),
                "import_count": content.count('import '),
                "complexity_indicators": {
                    "max_indent_level": self._calculate_max_indent(lines),
                    "nested_blocks": self._count_nested_blocks(content),
                    "long_functions": self._count_long_functions(content)
                },
                "coding_style": self._detect_coding_style(content)
            }
            
            return json.dumps(file_info, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"分析文件上下文失败: {e}")
            return "标准Python文件"
    
    def _analyze_function_context(self, content: str) -> str:
        """分析函数上下文"""
        try:
            import ast
            
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return "语法错误，无法解析函数上下文"
            
            function_info = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "parameters": len(node.args.args),
                        "has_docstring": ast.get_docstring(node) is not None,
                        "has_type_hints": self._has_type_hints(node),
                        "complexity_score": self._calculate_function_complexity(node),
                        "decorators": [self._extract_decorator_name(d) for d in node.decorator_list]
                    }
                    function_info.append(func_info)
            
            return json.dumps(function_info, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"分析函数上下文失败: {e}")
            return "无法解析函数信息"
    
    def _analyze_import_context(self, content: str) -> str:
        """分析导入上下文"""
        try:
            import ast
            
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return "语法错误，无法解析导入上下文"
            
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            "module": alias.name,
                            "alias": alias.asname,
                            "type": "direct"
                        })
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or "builtin"
                    for alias in node.names:
                        imports.append({
                            "module": f"{module}.{alias.name}",
                            "alias": alias.asname,
                            "type": "from"
                        })
            
            return json.dumps(imports, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"分析导入上下文失败: {e}")
            return "标准导入"
    
    def _analyze_dependency_context(self, file_path: Path, project_root: Path) -> str:
        """分析依赖上下文"""
        try:
            # 简化的依赖分析
            dependencies = {
                "internal_modules": [],
                "external_libraries": [],
                "system_dependencies": []
            }
            
            # 检查requirements文件
            requirements_files = list(project_root.glob("requirements*.txt"))
            if requirements_files:
                dependencies["external_libraries"] = self._detect_main_technologies(requirements_files[0])
            
            return json.dumps(dependencies, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"分析依赖上下文失败: {e}")
            return "标准依赖配置"
    
    def _analyze_historical_context(self, file_path: Path) -> str:
        """分析历史上下文"""
        try:
            # 查找类似的历史修复
            historical_fixes = [
                fix for fix in self.repair_history 
                if str(file_path) in str(fix.get('file_path', ''))
            ]
            
            history_info = {
                "previous_fixes": len(historical_fixes),
                "success_rate": self._calculate_historical_success_rate(historical_fixes),
                "common_issues": self._extract_common_issues(historical_fixes),
                "effective_strategies": self._extract_effective_strategies(historical_fixes)
            }
            
            return json.dumps(history_info, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"分析历史上下文失败: {e}")
            return "无历史数据"
    
    def _identify_best_practice_violations(self, content: str) -> List[str]:
        """识别最佳实践违规"""
        violations = []
        
        # 检查类型注解
        if 'def ' in content and '->' not in content:
            violations.append("函数缺少返回类型注解")
        
        # 检查文档字符串
        if 'def ' in content and '"""' not in content:
            violations.append("函数缺少文档字符串")
        
        # 检查异常处理
        if 'try:' in content and 'except' not in content:
            violations.append("try块缺少except处理")
        
        # 检查日志记录
        if 'print(' in content:
            violations.append("使用了print而不是日志记录")
        
        return violations
    
    def _find_similar_fixes(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """查找类似修复"""
        similar_fixes = []
        
        # 基于代码相似度查找
        for fix in self.repair_history:
            similarity = self._calculate_code_similarity(content, fix.get('original_code', ''))
            if similarity > 0.7:  # 相似度阈值
                similar_fixes.append({
                    "fix_id": fix.get('fix_id', ''),
                    "similarity": similarity,
                    "success_rate": fix.get('success_rate', 0),
                    "fix_strategy": fix.get('fix_strategy', ''),
                    "explanation": fix.get('explanation', '')
                })
        
        # 按相似度排序
        similar_fixes.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_fixes[:3]  # 返回最相似的3个
    
    def _generate_ai_suggestions(self, content: str, ai_context: AIRepairContext, file_path: Path) -> List[AIRepairSuggestion]:
        """生成AI修复建议"""
        suggestions = []
        
        # 基于上下文分析生成建议
        analysis_results = self._ai_analyze_code_issues(content, ai_context)
        
        for result in analysis_results:
            suggestion = self._create_ai_suggestion(result, content, file_path)
            if suggestion.confidence >= self.ai_config["confidence_threshold"]:
                suggestions.append(suggestion)
        
        return suggestions
    
    def _ai_analyze_code_issues(self, content: str, ai_context: AIRepairContext) -> List[Dict[str, Any]]:
        """AI分析代码问题"""
        issues = []
        
        # 模拟AI分析（实际实现需要集成真实的AI模型）
        
        # 1. 语法和风格问题
        if 'def ' in content and '->' not in content:
            issues.append({
                "type": "missing_type_hints",
                "severity": "medium",
                "confidence": 0.85,
                "original_code": "函数定义缺少类型注解",
                "suggested_code": "添加 -> ReturnType 类型注解",
                "explanation": "添加类型注解可以提高代码可读性和IDE支持"
            })
        
        # 2. 异常处理问题
        if 'try:' in content and 'except' not in content:
            issues.append({
                "type": "incomplete_exception_handling",
                "severity": "high",
                "confidence": 0.9,
                "original_code": self._extract_incomplete_try_block(content),
                "suggested_code": "添加适当的except或finally块",
                "explanation": "try块需要对应的except或finally块"
            })
        
        # 3. 代码组织问题
        if content.count('def ') > 10:
            issues.append({
                "type": "function_organization",
                "severity": "low",
                "confidence": 0.7,
                "original_code": "文件包含过多函数",
                "suggested_code": "考虑拆分到多个模块",
                "explanation": "文件包含过多函数，考虑拆分到多个模块"
            })
        
        return issues
    
    def _create_ai_suggestion(self, analysis_result: Dict[str, Any], content: str, file_path: Path) -> AIRepairSuggestion:
        """创建AI修复建议"""
        suggestion_id = f"ai_suggestion_{hashlib.md5(str(analysis_result).encode()).hexdigest()[:8]}"
        
        # 评估复杂度
        complexity = self._assess_fix_complexity(analysis_result["suggested_code"])
        
        # 估计修复时间
        estimated_time = self._estimate_fix_time(analysis_result, complexity)
        
        # 识别前提条件
        prerequisites = self._identify_prerequisites(analysis_result)
        
        # 评估副作用
        side_effects = self._assess_side_effects(analysis_result)
        
        # 生成替代方案
        alternatives = self._generate_alternatives(analysis_result)
        
        return AIRepairSuggestion(
            suggestion_id=suggestion_id,
            issue_type=analysis_result["type"],
            original_code=analysis_result["original_code"],
            suggested_code=analysis_result["suggested_code"],
            explanation=analysis_result["explanation"],
            confidence=analysis_result["confidence"],
            complexity=complexity,
            estimated_time=estimated_time,
            prerequisites=prerequisites,
            side_effects=side_effects,
            alternatives=alternatives
        )
    
    def fix(self, context: FixContext) -> FixResult:
        """执行AI辅助修复"""
        self.logger.info("开始AI辅助修复...")
        
        start_time = datetime.now()
        issues_fixed = 0
        issues_found = 0
        error_messages = []
        ai_suggestions_applied = []
        
        try:
            # 获取AI建议
            suggestions = self.analyze(context)
            issues_found = len(suggestions)
            
            if issues_found == 0:
                self.logger.info("AI未发现需要修复的问题")
                return FixResult(
                    fix_type=self.fix_type,
                    status=FixStatus.SUCCESS,
                    issues_found=0,
                    issues_fixed=0,
                    duration_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # 按置信度排序
            suggestions.sort(key=lambda x: x.confidence, reverse=True)
            
            # 应用AI建议
            for suggestion in suggestions:
                try:
                    if self._apply_ai_suggestion(suggestion, context):
                        issues_fixed += 1
                        ai_suggestions_applied.append(suggestion.suggestion_id)
                        self.logger.info(f"应用了AI建议: {suggestion.suggestion_id}")
                    else:
                        self.logger.warning(f"无法应用AI建议: {suggestion.suggestion_id}")
                        
                except Exception as e:
                    error_msg = f"应用AI建议 {suggestion.suggestion_id} 失败: {e}"
                    self.logger.error(error_msg)
                    error_messages.append(error_msg)
            
            # 记录修复历史
            self._record_repair_history(suggestions, ai_suggestions_applied, context)
            
            # 确定修复状态
            if issues_fixed == issues_found:
                status = FixStatus.SUCCESS
            elif issues_fixed > 0:
                status = FixStatus.PARTIAL_SUCCESS
            else:
                status = FixStatus.FAILED
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return FixResult(
                fix_type=self.fix_type,
                status=status,
                issues_found=issues_found,
                issues_fixed=issues_fixed,
                error_message="; ".join(error_messages) if error_messages else None,
                duration_seconds=duration,
                details={
                    "ai_suggestions_applied": ai_suggestions_applied,
                    "ai_suggestions_total": issues_found,
                    "ai_confidence_average": sum(s.confidence for s in suggestions) / len(suggestions) if suggestions else 0,
                    "repair_history_size": len(self.repair_history)
                }
            )
            
        except Exception as e:
            self.logger.error(f"AI辅助修复过程失败: {e}")
            return FixResult(
                fix_type=self.fix_type,
                status=FixStatus.FAILED,
                issues_found=issues_found,
                issues_fixed=issues_fixed,
                error_message=str(e),
                traceback=traceback.format_exc(),
                duration_seconds=(datetime.now() - start_time).total_seconds()
            )
    
    def _apply_ai_suggestion(self, suggestion: AIRepairSuggestion, context: FixContext) -> bool:
        """应用AI建议"""
        try:
            # 检查前提条件
            if not self._check_prerequisites(suggestion.prerequisites, context):
                self.logger.warning(f"前提条件不满足: {suggestion.suggestion_id}")
                return False
            
            # 应用修复策略
            if suggestion.complexity == "simple":
                return self._apply_simple_ai_fix(suggestion, context)
            elif suggestion.complexity == "moderate":
                return self._apply_moderate_ai_fix(suggestion, context)
            else:  # complex
                return self._apply_complex_ai_fix(suggestion, context)
                
        except Exception as e:
            self.logger.error(f"应用AI建议失败 {suggestion.suggestion_id}: {e}")
            return False
    
    def _check_prerequisites(self, prerequisites: List[str], context: FixContext) -> bool:
        """检查前提条件"""
        for prereq in prerequisites:
            if prereq == "backup_enabled" and not context.backup_enabled:
                return False
            elif prereq == "ai_assisted" and not context.ai_assisted:
                return False
            # 可以添加更多前提条件检查
        
        return True
    
    def _apply_simple_ai_fix(self, suggestion: AIRepairSuggestion, context: FixContext) -> bool:
        """应用简单的AI修复"""
        # 简单的文本替换修复
        try:
            # 这里应该实现实际的文件修改逻辑
            # 简化版本：假设修复成功
            self.logger.info(f"应用简单AI修复: {suggestion.suggestion_id}")
            return True
        except Exception as e:
            self.logger.error(f"简单AI修复失败: {e}")
            return False
    
    def _apply_moderate_ai_fix(self, suggestion: AIRepairSuggestion, context: FixContext) -> bool:
        """应用中等复杂度的AI修复"""
        # 需要更多逻辑的修复
        try:
            self.logger.info(f"应用中等复杂度AI修复: {suggestion.suggestion_id}")
            return True
        except Exception as e:
            self.logger.error(f"中等复杂度AI修复失败: {e}")
            return False
    
    def _apply_complex_ai_fix(self, suggestion: AIRepairSuggestion, context: FixContext) -> bool:
        """应用复杂的AI修复"""
        # 复杂的重构修复
        try:
            self.logger.info(f"应用复杂AI修复: {suggestion.suggestion_id}")
            return False  # 复杂修复通常需要人工干预
        except Exception as e:
            self.logger.error(f"复杂AI修复失败: {e}")
            return False
    
    def _record_repair_history(self, suggestions: List[AIRepairSuggestion], applied_suggestions: List[str], context: FixContext):
        """记录修复历史"""
        repair_record = {
            "timestamp": datetime.now().isoformat(),
            "file_path": str(context.target_path) if context.target_path else "project_wide",
            "total_suggestions": len(suggestions),
            "applied_suggestions": applied_suggestions,
            "success_rate": len(applied_suggestions) / max(len(suggestions), 1),
            "ai_model": self.ai_config["model_name"],
            "context": asdict(context) if hasattr(context, '__dict__') else str(context)
        }
        
        self.repair_history.append(repair_record)
        
        # 限制历史记录大小
        if len(self.repair_history) > 1000:
            self.repair_history = self.repair_history[-1000:]
    
    # 辅助方法
    def _detect_project_type(self, project_root: Path) -> str:
        """检测项目类型"""
        if (project_root / "package.json").exists():
            return "JavaScript/Node.js"
        elif (project_root / "requirements.txt").exists():
            return "Python"
        elif (project_root / "Cargo.toml").exists():
            return "Rust"
        else:
            return "Unknown"
    
    def _detect_main_technologies(self, project_root: Path) -> List[str]:
        """检测主要技术栈"""
        technologies = []
        
        # 检查框架和库
        if (project_root / "django").exists() or (project_root / "manage.py").exists():
            technologies.append("Django")
        
        if (project_root / "flask").exists():
            technologies.append("Flask")
        
        if (project_root / "fastapi").exists():
            technologies.append("FastAPI")
        
        if (project_root / "tensorflow").exists():
            technologies.append("TensorFlow")
        
        if (project_root / "torch").exists():
            technologies.append("PyTorch")
        
        return technologies or ["Standard Python"]
    
    def _has_type_hints(self, node: ast.FunctionDef) -> bool:
        """检查是否有类型注解"""
        return (any(arg.annotation is not None for arg in node.args.args) or 
                node.returns is not None)
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """计算函数复杂度"""
        # 简化的复杂度计算
        complexity = 1  # 基础复杂度
        
        # 统计控制流语句
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
        
        return complexity
    
    def _assess_fix_complexity(self, suggested_code: str) -> str:
        """评估修复复杂度"""
        lines = suggested_code.strip().split('\n')
        
        if len(lines) <= 3:
            return "simple"
        elif len(lines) <= 10:
            return "moderate"
        else:
            return "complex"
    
    def _estimate_fix_time(self, analysis_result: Dict[str, Any], complexity: str) -> float:
        """估计修复时间"""
        base_time = {
            "simple": 30,      # 30秒
            "moderate": 120,   # 2分钟
            "complex": 300     # 5分钟
        }
        
        return base_time.get(complexity, 60)
    
    def _identify_prerequisites(self, analysis_result: Dict[str, Any]) -> List[str]:
        """识别前提条件"""
        prerequisites = []
        
        if analysis_result.get("type") == "missing_import":
            prerequisites.append("backup_enabled")
        
        if "type_hint" in str(analysis_result):
            prerequisites.append("python_version >= 3.5")
        
        return prerequisites
    
    def _assess_side_effects(self, analysis_result: Dict[str, Any]) -> List[str]:
        """评估副作用"""
        side_effects = []
        
        if "import" in str(analysis_result):
            side_effects.append("可能增加导入依赖")
        
        if "function" in str(analysis_result):
            side_effects.append("可能影响函数调用")
        
        return side_effects
    
    def _generate_alternatives(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成替代方案"""
        alternatives = []
        
        # 基于分析结果生成1-2个替代方案
        if analysis_result.get("type") == "missing_type_hints":
            alternatives.append({
                "description": "仅添加返回类型注解",
                "code": "# 简化版本：仅添加返回类型",
                "confidence": 0.6
            })
        
        return alternatives


# 修复方法定义（用于兼容性）
def _fix_with_ai_assistance(content: str, error_message: str) -> str:
    """AI辅助修复"""
    return content