"""
增强版统一自动修复系统核心引擎
解决当前错误并添加高级修复功能
"""

import os
import sys
import json
import time
import logging
import traceback
import ast
import inspect
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core.fix_types import FixType, FixStatus, FixScope, FixPriority
from ..core.fix_result import FixResult, FixReport, FixContext
from ..utils.ast_analyzer import ASTAnalyzer
from ..utils.dependency_tracker import DependencyTracker
from ..utils.io_analyzer import IOAnalyzer
from ..utils.rule_engine import RuleEngine

# 导入所有修复模块
from ..modules.syntax_fixer import EnhancedSyntaxFixer
from ..modules.decorator_fixer import DecoratorFixer
from ..modules.class_fixer import ClassFixer
from ..modules.parameter_fixer import ParameterFixer
from ..modules.undefined_fixer import UndefinedFixer
from ..modules.path_fixer import PathFixer
from ..modules.data_processing_fixer import DataProcessingFixer
from ..modules.logic_graph_fixer import LogicGraphFixer
from ..modules.intelligent_iterative_fixer import IntelligentIterativeFixer


@dataclass
class EnhancedFixContext:
    """增强修复上下文"""


    project_root: Path
    target_path: Optional[Path] = None
    scope: FixScope = FixScope.PROJECT
    priority: FixPriority = FixPriority.NORMAL
    backup_enabled: bool = True
    dry_run: bool = False
    ai_assisted: bool = False
    custom_rules: Dict[str, Any] = field(default_factory=dict)
    excluded_paths: List[str] = field(default_factory=list)
    system_type: str = "general"  # general, backend, frontend, ai_system, etc.
    subsystem_type: str = "general"  # general, agents, memory, models, etc.
    function_type: str = "general"  # general, api, ui, processing, etc.
    model_type: str = "general"  # general, nlp, vision, audio, etc.
    tool_type: str = "general"  # general, database, cache, message_queue, etc.


class EnhancedUnifiedFixEngine:
    """
    增强版统一自动修复引擎
    
    功能增强：
    - 解决现有错误
    - 支持更细分的修复逻辑
    - 自动生成文件路径管理
    - 装饰器/类/参数/未定义问题修复
    - 输入输出依赖分析
    - 模型与工具专用修复规则
    - 数据处理错误修复
    - 系统/子系统专属规则
    """
    
    def __init__(self, project_root: Union[str, Path], config_path: Optional[Path] = None):
        self.project_root = Path(project_root).resolve()
        self.config_path = config_path or self.project_root / "enhanced_unified_fix_config.json"
        
        # 初始化工具
        self.ast_analyzer = ASTAnalyzer()
        self.dependency_tracker = DependencyTracker()
        self.io_analyzer = IOAnalyzer()
        self.rule_engine = RuleEngine()
        
        # 设置日志
        self._setup_logging()
        
        # 备份目录
        self.backup_dir = self.project_root / "enhanced_unified_fix_backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # 自动生成文件管理
        self.auto_generated_files = set()
        self._load_auto_generated_files()
        
        # 增强修复模块
        self.enhanced_modules = {}
        self._init_enhanced_modules()
        
         # 修复统计

        self.stats = {
            "total_fixes": 0,
            "successful_fixes": 0,
            "failed_fixes": 0,
            "skipped_fixes": 0,
            "issues_found": 0,
            "issues_fixed": 0,
            "start_time": None,
            "end_time": None,
            "auto_generated_files_managed": 0,
            "io_dependencies_fixed": 0,
            "model_tool_issues_fixed": 0,

 "system_specific_issues_fixed": 0

        }
        
        # 加载配置
        self.config = self._load_enhanced_config()
        
        self.logger.info(f"增强版统一修复引擎初始化完成 - 项目根目录: {self.project_root}")
    
    def _setup_logging(self):
        """设置日志系统"""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # 创建增强版日志文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
# 
#         log_file = log_dir / f"enhanced_unified_fix_{timestamp}.log"
# 
#         
        logging.basicConfig(
#         level=logging.INFO,

            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',

            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def _init_enhanced_modules(self):
        """初始化增强修复模块"""
        self.enhanced_modules = {
            FixType.SYNTAX_FIX: EnhancedSyntaxFixer(self.project_root),
            FixType.IMPORT_FIX: self._create_enhanced_import_fixer(),
            FixType.DEPENDENCY_FIX: self._create_enhanced_dependency_fixer(),
            FixType.GIT_FIX: self._create_enhanced_git_fixer(),
            FixType.ENVIRONMENT_FIX: self._create_enhanced_environment_fixer(),
            FixType.SECURITY_FIX: self._create_enhanced_security_fixer(),
            FixType.CODE_STYLE_FIX: self._create_enhanced_code_style_fixer(),
            FixType.PATH_FIX: self._create_enhanced_path_fixer(),
            FixType.CONFIGURATION_FIX: self._create_enhanced_configuration_fixer(),
            # 新增专用修复模块
            "DECORATOR_FIX": DecoratorFixer(self.project_root),
            "CLASS_FIX": ClassFixer(self.project_root),
            "PARAMETER_FIX": ParameterFixer(self.project_root),

            "UNDEFINED_FIX": UndefinedFixer(self.project_root),
            "DATA_PROCESSING_FIX": DataProcessingFixer(self.project_root),

            "LOGIC_GRAPH_FIX": LogicGraphFixer(self.project_root),
            "INTELLIGENT_ITERATIVE_FIX": IntelligentIterativeFixer(self.project_root)

 }

        
        self.logger.info(f"已加载 {len(self.enhanced_modules)} 个增强修复模块")
    
    def _create_enhanced_import_fixer(self):
        """创建增强版导入修复器"""
        from ..modules.import_fixer import ImportFixer
        return ImportFixer(self.project_root)
    
    def _create_enhanced_dependency_fixer(self):
        """创建增强版依赖修复器"""
        from ..modules.dependency_fixer import DependencyFixer
        return DependencyFixer(self.project_root)
    
    def _create_enhanced_git_fixer(self):
        """创建增强版Git修复器"""
        from ..modules.git_fixer import GitFixer
        return GitFixer(self.project_root)
    
    def _create_enhanced_environment_fixer(self):
        """创建增强版环境修复器"""
        from ..modules.environment_fixer import EnvironmentFixer
        return EnvironmentFixer(self.project_root)
    
    def _create_enhanced_security_fixer(self):
        """创建增强版安全修复器"""
        from ..modules.security_fixer import SecurityFixer
        return SecurityFixer(self.project_root)
    
    def _create_enhanced_code_style_fixer(self):
        """创建增强版代码风格修复器"""
        from ..modules.code_style_fixer import CodeStyleFixer
        return CodeStyleFixer(self.project_root)
    
    def _create_enhanced_path_fixer(self):
        """创建增强版路径修复器"""
        from ..modules.path_fixer import PathFixer
        return PathFixer(self.project_root)
    
    def _create_enhanced_configuration_fixer(self):
        """创建增强版配置修复器"""

        from ..modules.configuration_fixer import ConfigurationFixer
        return ConfigurationFixer(self.project_root)
    
    def _load_enhanced_config(self) -> Dict[str, Any]:
        """加载增强版配置文件"""
        default_config = {
            "enabled_modules": list(self.enhanced_modules.keys()),
            "backup_enabled": True,
            "dry_run": False,
            "ai_assisted": True,
            "max_fix_attempts": 3,
            "parallel_fixing": True,
            "auto_generated_file_tracking": True,
            "io_dependency_tracking": True,

            "model_tool_analysis": True,
            "system_specific_rules": True,

            "advanced_ast_analysis": True,

 "rule_engine_enabled": True,

            "learning_enabled": True,
            "custom_rules": {},

            "excluded_paths": [
            "node_modules", "__pycache__", ".git", "venv", ".venv",

                "backup", "unified_fix_backups", "dist", "build",
                ".pytest_cache", "auto_fix_workspace"
            ],
            "auto_generated_patterns": [
            "*.log", "*.tmp", "*.cache", "*.pyc", "__pycache__",

                "*.backup", "*.temp", "generated_*", "auto_*"

            ],
            "system_categories": {
                "ai_systems": ["agents", "memory", "models", "training"],
                "backend_systems": ["api", "services", "database"],

 "frontend_systems": ["ui", "components", "dashboard"],

                "infrastructure": ["config", "deployment", "monitoring"]
            },
            "model_types": ["nlp", "vision", "audio", "multimodal", "rl", "gan"],
            "tool_types": ["database", "cache", "message_queue", "storage", "api_client"],
            "repair_priorities": {
                "critical": ["syntax", "security", "undefined"],
                "high": ["import", "dependency", "io"],
                "medium": ["style", "configuration", "path"],
                "low": ["optimization", "formatting"]
            }
            }

        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:

                    user_config = json.load(f)
                
                # 深度合并配置
                config = self._deep_merge(default_config, user_config)
                self.logger.info("已加载用户增强配置")
                return config
            except Exception as e:
                self.logger.warning(f"增强配置文件加载失败，使用默认配置: {e}")
        
        return default_config
    
    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """深度合并字典"""

        result = base.copy()
        for key, value in update.items():

            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result
    
    def _load_auto_generated_files(self):
        """加载自动生成的文件列表"""

        tracking_file = self.project_root / "auto_generated_files.json"
        if tracking_file.exists():
            try:

                with open(tracking_file, 'r', encoding='utf-8') as f:

                    files = json.load(f)
                    self.auto_generated_files = {Path(f) for f in files}

            except Exception as e:
                self.logger.warning(f"加载自动生成的文件列表失败: {e}")
    
    def _save_auto_generated_files(self):
        """保存自动生成的文件列表"""
        tracking_file = self.project_root / "auto_generated_files.json"
        try:
            with open(tracking_file, 'w', encoding='utf-8') as f:
                json.dump([str(f) for f in self.auto_generated_files], f, indent=2)
        except Exception as e:
            self.logger.error(f"保存自动生成的文件列表失败: {e}")

    
    def analyze_project_enhanced(self, context: EnhancedFixContext) -> Dict[str, Any]:
        """增强版项目分析"""

        self.logger.info("开始增强版项目分析...")
        
        analysis_result = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "context": asdict(context),
            "issues": {},
            "statistics": {},
            "auto_generated_files": [],
            "io_dependencies": {},
            "model_tool_issues": {},
            "system_specific_issues": {},
            "recommendations": [],
            "risk_assessment": {}
        }
        
        # 分析自动生成的文件
        if self.config["auto_generated_file_tracking"]:
            self.logger.info("分析自动生成的文件...")
            auto_gen_issues = self._analyze_auto_generated_files(context)
            analysis_result["auto_generated_files"] = auto_gen_issues
        
        # 分析输入输出依赖
        if self.config["io_dependency_tracking"]:
            self.logger.info("分析输入输出依赖...")
            io_deps = self._analyze_io_dependencies(context)
            analysis_result["io_dependencies"] = io_deps
        
        # 分析模型与工具问题
        if self.config["model_tool_analysis"]:
            self.logger.info("分析模型与工具问题...")
            model_tool_issues = self._analyze_model_tool_issues(context)
            analysis_result["model_tool_issues"] = model_tool_issues
        
        # 分析系统特定问题
        if self.config["system_specific_rules"]:
            self.logger.info("分析系统特定问题...")
            system_issues = self._analyze_system_specific_issues(context)
            analysis_result["system_specific_issues"] = system_issues
        
        # 高级AST分析
        if self.config["advanced_ast_analysis"]:
            self.logger.info("执行高级AST分析...")
            ast_issues = self._perform_advanced_ast_analysis(context)
            for issue_type, issues in ast_issues.items():
                if issue_type not in analysis_result["issues"]:
                    analysis_result["issues"][issue_type] = []
                analysis_result["issues"][issue_type].extend(issues)
        
        # 规则引擎分析
        if self.config["rule_engine_enabled"]:
            self.logger.info("执行规则引擎分析...")
            rule_issues = self._perform_rule_engine_analysis(context)
            for issue_type, issues in rule_issues.items():
                if issue_type not in analysis_result["issues"]:
                    analysis_result["issues"][issue_type] = []
                analysis_result["issues"][issue_type].extend(issues)
        
        # 基础分析（原有功能）
        for fix_type, module in self.enhanced_modules.items():
            if fix_type in self.config["enabled_modules"]:
                try:

                    self.logger.info(f"分析 {fix_type.value} 问题...")
                    issues = module.analyze(context)
                    analysis_result["issues"][fix_type.value] = issues
                    analysis_result["statistics"][fix_type.value] = len(issues)

                    
                    if issues:
                        self.logger.info(f"发现 {len(issues)} 个 {fix_type.value} 问题")
                except Exception as e:
                    self.logger.error(f"分析 {fix_type.value} 失败: {e}")
                    analysis_result["issues"][fix_type.value] = []
        
        # 生成建议和风险评估
        analysis_result["recommendations"] = self._generate_enhanced_recommendations(analysis_result)

        analysis_result["risk_assessment"] = self._perform_risk_assessment(analysis_result)

        
        return analysis_result
    
    def _analyze_auto_generated_files(self, context: EnhancedFixContext) -> List[Dict[str, Any]]:
        """分析自动生成的文件"""
        issues = []
        
        # 查找可能的自动生成文件
        patterns = self.config["auto_generated_patterns"]
        
        for pattern in patterns:
            for file_path in self.project_root.rglob(pattern):
                if self._should_analyze_file(file_path):

                    issue = {
                        "file_path": str(file_path),
                        "pattern": pattern,
                        "issue_type": "auto_generated_file",

                        "severity": "info",
                        "suggested_action": "track_and_manage"
                    }
                    
                    # 检查文件是否在正确的位置
                    if not self._is_in_appropriate_location(file_path):
                        issue["issue_type"] = "misplaced_auto_generated_file"

                        issue["severity"] = "warning"
                        issue["suggested_action"] = "relocate"
                    
                    issues.append(issue)
                    self.auto_generated_files.add(file_path)
        
        return issues
    
    def _is_in_appropriate_location(self, file_path: Path) -> bool:
        """检查文件是否在适当的位置"""
        # 根据文件类型判断应该在哪里
        if file_path.suffix == '.log':
            return 'logs' in str(file_path) or 'log' in str(file_path)

        elif file_path.suffix == '.cache':
            return 'cache' in str(file_path) or '.cache' in str(file_path)
        elif file_path.suffix == '.tmp':
            return 'temp' in str(file_path) or 'tmp' in str(file_path)
        
        return True  # 默认认为位置合适
    
    def _analyze_io_dependencies(self, context: EnhancedFixContext) -> Dict[str, Any]:
        """分析输入输出依赖"""
        return self.io_analyzer.analyze_project_io(context)
    
    def _analyze_model_tool_issues(self, context: EnhancedFixContext) -> Dict[str, Any]:
        """分析模型与工具问题"""
        issues = {
            "model_issues": [],
            "tool_issues": [],
            "interface_issues": [],
            "compatibility_issues": []
            }

        
        # 分析AI模型相关问题
        if context.model_type != "general":

            model_issues = self._analyze_specific_model_issues(context)
            issues["model_issues"] = model_issues
        
        # 分析工具相关问题
        if context.tool_type != "general":
            tool_issues = self._analyze_specific_tool_issues(context)
            issues["tool_issues"] = tool_issues
        
        # 分析接口问题
        interface_issues = self._analyze_model_tool_interfaces(context)
        issues["interface_issues"] = interface_issues
        
        # 分析兼容性问题
        compatibility_issues = self._analyze_compatibility_issues(context)
        issues["compatibility_issues"] = compatibility_issues
        
        return issues
    
    def _analyze_system_specific_issues(self, context: EnhancedFixContext) -> Dict[str, Any]:
        """分析系统特定问题"""

        issues = {}
        
         # 根据系统类型分析特定问题


        if context.system_type != "general":
            system_fixer = self.enhanced_modules.get("SYSTEM_SPECIFIC_FIX")

            if system_fixer:

                system_issues = system_fixer.analyze_system_specific(context)
                issues[context.system_type] = system_issues


        
        # 根据子系统类型分析
        if context.subsystem_type != "general":


            subsystem_fixer = self.enhanced_modules.get("SYSTEM_SPECIFIC_FIX")
            if subsystem_fixer:
                subsystem_issues = subsystem_fixer.analyze_subsystem_specific(context)
                issues[context.subsystem_type] = subsystem_issues
        
        return issues
    
    def _perform_advanced_ast_analysis(self, context: EnhancedFixContext) -> Dict[str, Any]:
        """执行高级AST分析"""
        return self.ast_analyzer.analyze_advanced(context)
    
    def _perform_rule_engine_analysis(self, context: EnhancedFixContext) -> Dict[str, Any]:
        """执行规则引擎分析"""


        return self.rule_engine.analyze_with_rules(context)
    
    def _generate_enhanced_recommendations(self, analysis_result: Dict[str, Any]) -> List[str]:
        """生成增强版建议"""

        recommendations = []
        
        # 基于分析结果生成具体建议
        total_issues = sum(len(issues) for issues in analysis_result.get("issues", {}).values())
        
        if total_issues > 50:
            recommendations.append("发现大量问题，建议优先处理关键错误，然后逐步解决其他问题")
        
        # 自动生成文件管理建议
        if analysis_result.get("auto_generated_files"):
            recommendations.append("发现自动生成文件，建议建立统一的文件管理策略")
        
        # IO依赖建议
        if analysis_result.get("io_dependencies"):
            io_deps = analysis_result["io_dependencies"]
            if io_deps.get("missing_inputs"):
                recommendations.append("发现缺失的输入依赖，建议检查文件路径和数据源")
            if io_deps.get("unreachable_outputs"):
                recommendations.append("发现无法访问的输出路径，建议检查权限和目录结构")
        
         # 模型工具建议

        if analysis_result.get("model_tool_issues"):
            model_issues = analysis_result["model_tool_issues"]
            if model_issues.get("compatibility_issues"):
                recommendations.append("发现模型工具兼容性问题，建议检查版本和接口")
        
        return recommendations
    
    def _perform_risk_assessment(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行风险评估"""
        risk_assessment = {

            "overall_risk": "low",
            "critical_issues": 0,

            "high_risk_areas": [],
            "risk_factors": []
            }

        
        # 统计关键问题
        issues = analysis_result.get("issues", {})
        for issue_type, issue_list in issues.items():
            if issue_type in ["syntax_fix", "security_fix", "undefined_fix"]:
                risk_assessment["critical_issues"] += len(issue_list)
        
        # 评估整体风险
        if risk_assessment["critical_issues"] > 10:
            risk_assessment["overall_risk"] = "high"
        elif risk_assessment["critical_issues"] > 5:
            risk_assessment["overall_risk"] = "medium"
        
        return risk_assessment
    
    def fix_issues_enhanced(self, context: EnhancedFixContext, 
                           specific_issues: Optional[List[str]] = None) -> FixReport:
        """增强版问题修复"""
        self.logger.info("开始增强版修复过程...")
        self.stats["start_time"] = datetime.now()
        
        # 创建修复报告
        fix_report = FixReport(
            timestamp=datetime.now(),
            project_root=self.project_root,
            context=context
        )
        
        try:
            # 增强版分析
            analysis = self.analyze_project_enhanced(context)
            fix_report.analysis_result = analysis
            
            # 备份（如果启用）
            if context.backup_enabled and self.config["backup_enabled"]:
                backup_path = self._create_enhanced_backup(context)
                fix_report.backup_path = backup_path
                self.logger.info(f"已创建增强备份: {backup_path}")
            
            # 修复自动生成文件问题
            if analysis.get("auto_generated_files"):
                self._fix_auto_generated_files(analysis["auto_generated_files"], context)
            
            # 修复IO依赖问题
            if analysis.get("io_dependencies"):
                self._fix_io_dependencies(analysis["io_dependencies"], context)
            
            # 修复模型工具问题
            if analysis.get("model_tool_issues"):
                self._fix_model_tool_issues(analysis["model_tool_issues"], context)
            
            # 修复系统特定问题
            if analysis.get("system_specific_issues"):
                self._fix_system_specific_issues(analysis["system_specific_issues"], context)
            
            # 执行基础修复（原有功能）
            self._execute_enhanced_fixes(context, specific_issues, fix_report)
            
            # 验证修复结果
            self.logger.info("验证增强版修复结果...")
            fix_report.validation_result = self._validate_enhanced_fixes(context)
            
        except Exception as e:
            self.logger.error(f"增强版修复过程失败: {e}")
            fix_report.errors.append(str(e))
            fix_report.traceback = traceback.format_exc()
        
        finally:
            self.stats["end_time"] = datetime.now()
            fix_report.statistics = self._get_enhanced_final_statistics()
#             
             # 保存自动生成文件列表

            if self.config["auto_generated_file_tracking"]:
                self._save_auto_generated_files()
            
             # 保存报告

            self._save_enhanced_fix_report(fix_report)
# 
            
            self.logger.info(f"增强版修复过程完成 - 总计: {self.stats['total_fixes']}, 成功: {self.stats['successful_fixes']}")
        
        return fix_report
    
    def _create_enhanced_backup(self, context: EnhancedFixContext) -> Path:
        """创建增强版备份"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_name = f"enhanced_fix_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        try:
            import shutil
            
            if context.target_path:
                # 备份特定文件/目录
                if context.target_path.is_file():
                    backup_path.mkdir(exist_ok=True)

                    shutil.copy2(context.target_path, backup_path / context.target_path.name)
                else:
                    shutil.copytree(context.target_path, backup_path / context.target_path.name)
            else:
                # 备份整个项目（排除指定目录）
                shutil.copytree(
                self.project_root, 

                    backup_path,
                    ignore=shutil.ignore_patterns(*self.config["excluded_paths"])
                )
            
            # 备份自动生成文件列表
            if self.auto_generated_files:
                files_backup = backup_path / "auto_generated_files_backup.json"
                with open(files_backup, 'w', encoding='utf-8') as f:
                    json.dump([str(f) for f in self.auto_generated_files], f, indent=2)
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"增强备份创建失败: {e}")
            raise
    
    def _fix_auto_generated_files(self, auto_gen_issues: List[Dict[str, Any]], context: EnhancedFixContext):
        """修复自动生成文件问题"""
        for issue in auto_gen_issues:
            try:

                if issue["issue_type"] == "misplaced_auto_generated_file":
                    self._relocate_auto_generated_file(Path(issue["file_path"]), context)
                else:
                    self._track_auto_generated_file(Path(issue["file_path"]), context)

            except Exception as e:
                self.logger.error(f"修复自动生成文件问题失败: {e}")
    
    def _relocate_auto_generated_file(self, file_path: Path, context: EnhancedFixContext):
        """重新定位自动生成文件"""

        # 根据文件类型确定合适的位置
        appropriate_dir = self._determine_appropriate_directory(file_path)
        
        if appropriate_dir and appropriate_dir != file_path.parent:
            new_path = appropriate_dir / file_path.name
            
            if not context.dry_run:
                appropriate_dir.mkdir(parents=True, exist_ok=True)
                file_path.rename(new_path)
                self.logger.info(f"重新定位自动生成文件: {file_path} -> {new_path}")


                
                 # 更新跟踪列表

                self.auto_generated_files.discard(file_path)
                self.auto_generated_files.add(new_path)
            else:
                self.logger.info(f"干运行 - 建议重新定位: {file_path} -> {new_path}")
    
    def _determine_appropriate_directory(self, file_path: Path) -> Optional[Path]:
        """确定适当的目录"""

        if file_path.suffix == '.log':
            return self.project_root / "logs"
        elif file_path.suffix == '.cache':
            return self.project_root / "cache"
        elif file_path.suffix == '.tmp':
            return self.project_root / "temp"

        elif 'generated' in file_path.name.lower():
            return self.project_root / "generated"


        
        return None
    
    def _track_auto_generated_file(self, file_path: Path, context: EnhancedFixContext):
        """跟踪自动生成文件"""
        if file_path not in self.auto_generated_files:
            self.auto_generated_files.add(file_path)

            self.logger.info(f"跟踪新的自动生成文件: {file_path}")

    
    def _fix_io_dependencies(self, io_deps: Dict[str, Any], context: EnhancedFixContext):
        """修复IO依赖问题"""
        self.io_analyzer.fix_io_issues(io_deps, context)
    
    def _fix_model_tool_issues(self, model_tool_issues: Dict[str, Any], context: EnhancedFixContext):
        """修复模型工具问题"""
        for issue_type, issues in model_tool_issues.items():
            fixer = self.enhanced_modules.get("MODEL_TOOL_FIX")
            if fixer and issues:
                fixer.fix_specific_issues(issue_type, issues, context)


    
#     def _fix_system_specific_issues(self, system_issues: Dict[str, Any], context: EnhancedFixContext):
        """修复系统特定问题"""

        for system_type, issues in system_issues.items():
            fixer = self.enhanced_modules.get("SYSTEM_SPECIFIC_FIX")
            if fixer and issues:

                fixer.fix_system_specific_issues(system_type, issues, context)
    
    def _execute_enhanced_fixes(self, context: EnhancedFixContext, 
                               specific_issues: Optional[List[str]],
                               fix_report: FixReport):
#         """执行增强版修复"""
        # 并行修复处理

        if self.config["parallel_fixing"] and not context.dry_run:
            self._execute_parallel_fixes(context, specific_issues, fix_report)

        else:
            self._execute_sequential_fixes(context, specific_issues, fix_report)

    
    def _execute_parallel_fixes(self, context: EnhancedFixContext, 
                               specific_issues: Optional[List[str]],
                               fix_report: FixReport):
        """并行执行修复"""
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []


            
            for fix_type, module in self.enhanced_modules.items():
                if specific_issues and str(fix_type) not in specific_issues:

                    continue
#                 
#                 if fix_type in self.config["enabled_modules"]:
                    future = executor.submit(self._fix_module_with_error_handling, 
                                           module, context, fix_type)
                    futures.append((fix_type, future))
            
            # 收集结果
            for fix_type, future in futures:


                try:
                    result = future.result(timeout=300)  # 5分钟超时
#                     fix_report.fix_results[fix_type] = result
#                     self._update_enhanced_stats(result)
                except Exception as e:
                    self.logger.error(f"并行修复 {fix_type} 失败: {e}")

                    error_result = FixResult(
                        fix_type=fix_type,
                        status=FixStatus.FAILED,
                        error_message=str(e)
                    )
                    fix_report.fix_results[fix_type] = error_result
                    self.stats["failed_fixes"] += 1
    
    def _execute_sequential_fixes(self, context: EnhancedFixContext, 
                                 specific_issues: Optional[List[str]],
                                 fix_report: FixReport):
        """顺序执行修复"""
        for fix_type, module in self.enhanced_modules.items():
            if specific_issues and str(fix_type) not in specific_issues:
                continue
            
            if fix_type in self.config["enabled_modules"]:
                try:
                    self.logger.info(f"修复 {fix_type.value if hasattr(fix_type, 'value') else fix_type} 问题...")
                    
                    if context.dry_run or self.config["dry_run"]:
                        result = self._simulate_enhanced_fix(module, context)

                    else:
                        result = self._fix_module_with_error_handling(module, context, fix_type)

                    
                    fix_report.fix_results[fix_type] = result
                    self._update_enhanced_stats(result)
#                     
                    self.logger.info(f"{fix_type.value if hasattr(fix_type, 'value') else fix_type} 修复完成: {result.summary()}")
                    
                except Exception as e:
                    self.logger.error(f"修复 {fix_type.value if hasattr(fix_type, 'value') else fix_type} 失败: {e}")
                    error_result = FixResult(
#                         fix_type=fix_type,
# status=FixStatus.FAILED,


 error_message=str(e),

                        traceback=traceback.format_exc()

                    )
#                     fix_report.fix_results[fix_type] = error_result
                    self.stats["failed_fixes"] += 1

    
    def _fix_module_with_error_handling(self, module, context: EnhancedFixContext, fix_type) -> FixResult:
#         """带错误处理的模块修复"""
        try:
            return module.fix(context)

        except AttributeError as e:
            # 处理方法不存在的情况


            if "_fix_missing_colon" in str(e):
                self.logger.warning(f"修复模块 {fix_type} 缺少方法，尝试降级修复")
                return self._degraded_fix(module, context, fix_type)

            else:
                raise
        except Exception as e:
            self.logger.error(f"模块修复错误 {fix_type}: {e}")
            raise
    
    def _degraded_fix(self, module, context: EnhancedFixContext, fix_type) -> FixResult:
        """降级修复（当高级方法不可用时）"""
        # 使用基础修复逻辑

        try:
            # 尝试使用模块的基础修复能力
            if hasattr(module, 'fix_basic'):
                return module.fix_basic(context)

            elif hasattr(module, 'analyze'):
                # 只分析问题，不提供修复
                issues = module.analyze(context)
                return FixResult(
                    fix_type=fix_type,
                    status=FixStatus.SKIPPED,
                    issues_found=len(issues),


                    issues_fixed=0,
                    details={"reason": "高级修复方法不可用，降级到分析模式"}
                )
            else:
                return FixResult(
                    fix_type=fix_type,
                    status=FixStatus.NOT_APPLICABLE,
                    issues_found=0,
                    issues_fixed=0,
                    details={"reason": "模块没有可用的修复方法"}
                )
        except Exception as e:
            return FixResult(
                fix_type=fix_type,
                status=FixStatus.FAILED,

                error_message=f"降级修复失败: {e}"
            )
    
    def _simulate_enhanced_fix(self, module, context: EnhancedFixContext) -> FixResult:
        """模拟增强版修复（干运行）"""
        self.logger.info(f"干运行模式 - {module.__class__.__name__}")
        
         # 分析问题但不实际修复

        issues = module.analyze(context)
        
        return FixResult(
        fix_type=getattr(module, 'fix_type', FixType.SYNTAX_FIX),

            status=FixStatus.SIMULATED,
            issues_found=len(issues),

 issues_fixed=0,

 details={

                "simulated": True, 
                "issues": issues[:10],  # 只显示前10个问题
                "would_fix": len(issues)


            }
        )
    
    def _validate_enhanced_fixes(self, context: EnhancedFixContext) -> Dict[str, Any]:
        """验证增强版修复结果"""
        self.logger.info("验证增强版修复结果...")
        
        validation_result = {
            "timestamp": datetime.now().isoformat(),
            "validation_passed": True,

 "remaining_issues": {},

 "validation_errors": [],

            "performance_impact": {},
            "security_impact": {}
            }


        
        try:
            # 重新分析项目
            post_fix_analysis = self.analyze_project_enhanced(context)

            validation_result["post_fix_analysis"] = post_fix_analysis
            
            # 检查是否还有问题
            total_remaining = sum(len(issues) for issues in post_fix_analysis.get("issues", {}).values())
            validation_result["total_remaining_issues"] = total_remaining
            
            # 评估性能影响
            validation_result["performance_impact"] = self._assess_performance_impact(post_fix_analysis)
            
             # 评估安全影响

            validation_result["security_impact"] = self._assess_security_impact(post_fix_analysis)
            
            if total_remaining > 0:
                validation_result["validation_passed"] = False

                self.logger.warning(f"验证失败 - 仍有 {total_remaining} 个问题未修复")
            else:
                self.logger.info("验证通过 - 所有问题已修复")
                
        except Exception as e:
            validation_result["validation_errors"].append(str(e))
            validation_result["validation_passed"] = False
            self.logger.error(f"验证过程失败: {e}")
        
        return validation_result
    
    def _assess_performance_impact(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """评估性能影响"""
        return {
            "potential_bottlenecks": len(analysis_result.get("issues", {}).get("performance_fix", [])),
            "optimization_opportunities": len(analysis_result.get("issues", {}).get("performance_fix", [])),
            "memory_usage_concerns": len(analysis_result.get("issues", {}).get("memory_fix", [])),

            "io_performance_issues": len(analysis_result.get("io_dependencies", {}).get("performance_issues", []))
            }


    
    def _assess_security_impact(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """评估安全影响"""

        return {
            "critical_vulnerabilities": len([issue for issue in analysis_result.get("issues", {}).get("security_fix", []) 
                                           if issue.get("severity") == "critical"]),
            "high_risk_issues": len([issue for issue in analysis_result.get("issues", {}).get("security_fix", [])
                                   if issue.get("severity") == "high"]),
                                   "data_exposure_risks": len(analysis_result.get("issues", {}).get("data_exposure", [])),

            "access_control_issues": len(analysis_result.get("issues", {}).get("access_control", []))
        }
    
    def _update_enhanced_stats(self, result: FixResult):
        """更新增强版统计信息"""

        self.stats["total_fixes"] += 1

        self.stats["issues_found"] += result.issues_found
        self.stats["issues_fixed"] += result.issues_fixed
        
        if result.status == FixStatus.SUCCESS:
            self.stats["successful_fixes"] += 1

        elif result.status == FixStatus.FAILED:
            self.stats["failed_fixes"] += 1
        elif result.status == FixStatus.SKIPPED:
            self.stats["skipped_fixes"] += 1
    
    def _get_enhanced_final_statistics(self) -> Dict[str, Any]:
        """获取增强版最终统计信息"""
        duration = None

        if self.stats["start_time"] and self.stats["end_time"]:
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        
        return {
        "total_fixes": self.stats["total_fixes"],

            "successful_fixes": self.stats["successful_fixes"],
            "failed_fixes": self.stats["failed_fixes"],
            "skipped_fixes": self.stats["skipped_fixes"],
            "success_rate": self.stats["successful_fixes"] / max(self.stats["total_fixes"], 1),
            "total_issues_found": self.stats["issues_found"],
            "total_issues_fixed": self.stats["issues_fixed"],
            "fix_efficiency": self.stats["issues_fixed"] / max(self.stats["issues_found"], 1),

            "duration_seconds": duration,
            "start_time": self.stats["start_time"].isoformat() if self.stats["start_time"] else None,
            "end_time": self.stats["end_time"].isoformat() if self.stats["end_time"] else None,
            "auto_generated_files_managed": self.stats["auto_generated_files_managed"],
            "io_dependencies_fixed": self.stats["io_dependencies_fixed"],
            "model_tool_issues_fixed": self.stats["model_tool_issues_fixed"],
            "system_specific_issues_fixed": self.stats["system_specific_issues_fixed"]
        }
    
    def _save_enhanced_fix_report(self, fix_report: FixReport):
        """保存增强版修复报告"""
        try:

            reports_dir = self.project_root / "enhanced_unified_fix_reports"
            reports_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = reports_dir / f"enhanced_fix_report_{timestamp}.json"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(fix_report), f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"增强版修复报告已保存: {report_file}")
            
        except Exception as e:
            self.logger.error(f"增强版修复报告保存失败: {e}")
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """检查是否应该分析文件"""
        return not any(pattern in str(file_path) for pattern in self.config["excluded_paths"])
    
    def get_enhanced_module_status(self) -> Dict[str, str]:
        """获取增强模块状态"""
        status = {}
        for module_name, module in self.enhanced_modules.items():
            status[str(module_name)] = "enabled" if module else "disabled"
        return status
    
    def enable_enhanced_module(self, module_name: str):
        """启用增强修复模块"""
        if module_name in self.enhanced_modules:
            if module_name not in self.config["enabled_modules"]:
                self.config["enabled_modules"].append(module_name)
            self.logger.info(f"已启用增强模块: {module_name}")
    
    def disable_enhanced_module(self, module_name: str):
        """禁用增强修复模块"""
        if module_name in self.config["enabled_modules"]:
            self.config["enabled_modules"].remove(module_name)
            self.logger.info(f"已禁用增强模块: {module_name}")
    
    def cleanup(self):
        """清理增强版资源"""
        self.logger.info("清理增强版统一修复引擎资源...")
        
        # 保存配置
        self.save_enhanced_config()
        
        # 保存自动生成文件列表
        if self.config["auto_generated_file_tracking"]:
            self._save_auto_generated_files()
        
        # 清理模块
        for module in self.enhanced_modules.values():
            if hasattr(module, 'cleanup'):
                try:
                    module.cleanup()
                except Exception as e:
                    self.logger.warning(f"增强模块清理失败: {e}")
        
        self.logger.info("增强版统一修复引擎清理完成")
    
    def save_enhanced_config(self):
        """保存增强版配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self.logger.info("增强版配置文件已保存")
        except Exception as e:
            self.logger.error(f"增强版配置文件保存失败: {e}")