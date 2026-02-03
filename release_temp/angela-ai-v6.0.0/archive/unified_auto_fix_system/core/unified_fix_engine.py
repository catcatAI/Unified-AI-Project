"""
统一修复引擎 - 核心引擎类
整合所有修复功能,提供统一的修复接口
"""

import os
import sys
import json
import time
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, field, asdict
from enum import Enum

from .fix_types import FixType, FixStatus, FixScope, FixPriority
from .fix_result import FixResult, FixReport, FixContext
from ..modules.syntax_fixer import EnhancedSyntaxFixer
from ..modules.import_fixer import ImportFixer  
from ..modules.dependency_fixer import DependencyFixer
from ..modules.git_fixer import GitFixer
from ..modules.environment_fixer import EnvironmentFixer
from ..modules.security_fixer import SecurityFixer
from ..modules.code_style_fixer import CodeStyleFixer
from ..modules.path_fixer import PathFixer
from ..modules.configuration_fixer import ConfigurationFixer


class UnifiedFixEngine:
    """
    统一自动修复引擎

    功能特点：
    - 模块化修复器架构
    - 智能修复优先级
    - 实时备份保护
    - AI辅助修复建议
    - 完整修复报告
    - 可扩展的修复规则
    """
    
    def __init__(self, project_root: Union[str, Path], config_path: Optional[Path] = None):
        self.project_root = Path(project_root).resolve()
        self.config_path = config_path or self.project_root / "unified_auto_fix_config.json"
        
        # 初始化日志
        self._setup_logging()
        
        # 备份目录
        self.backup_dir = self.project_root / "unified_fix_backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # 修复模块
        self.modules = {}
        self._init_modules()

        # 修复统计
        self.stats = {
            "total_fixes": 0,
            "successful_fixes": 0,
            "failed_fixes": 0,
            "skipped_fixes": 0,
            "start_time": None,
            "end_time": None
        }
        
        # 加载配置
        self.config = self._load_config()
        
        self.logger.info(f"统一修复引擎初始化完成 - 项目根目录: {self.project_root}")
    
    def _setup_logging(self):
        """设置日志系统"""
        # 创建日志目录
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)

        # 创建日志文件
        log_file = log_dir / f"unified_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def _init_modules(self):
        """初始化修复模块"""
        self.modules = {
            FixType.SYNTAX_FIX: EnhancedSyntaxFixer(self.project_root),
            FixType.IMPORT_FIX: ImportFixer(self.project_root),
            FixType.DEPENDENCY_FIX: DependencyFixer(self.project_root),
            FixType.GIT_FIX: GitFixer(self.project_root),
            FixType.ENVIRONMENT_FIX: EnvironmentFixer(self.project_root),
            FixType.SECURITY_FIX: SecurityFixer(self.project_root),
            FixType.CODE_STYLE_FIX: CodeStyleFixer(self.project_root),
            FixType.PATH_FIX: PathFixer(self.project_root),
            FixType.CONFIGURATION_FIX: ConfigurationFixer(self.project_root)
        }
        
        self.logger.info(f"已加载 {len(self.modules)} 个修复模块")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "enabled_modules": list(self.modules.keys()),
            "backup_enabled": True,
            "dry_run": False,
            "ai_assisted": False,
            "max_fix_attempts": 3,
            "parallel_fixing": True,
            "custom_rules": {},
            "excluded_paths": [
                "node_modules",
                "__pycache__", 
                ".git",
                "venv",
                ".venv",
                "backup",
                "unified_fix_backups"
            ]
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                
                # 合并配置
                config = {**default_config, **user_config}
                self.logger.info("已加载用户配置文件")
                return config
            except Exception as e:
                self.logger.warning(f"配置文件加载失败,使用默认配置: {e}")
        
        return default_config
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self.logger.info("配置文件已保存")
        except Exception as e:
            self.logger.error(f"配置文件保存失败: {e}")
    
    def analyze_project(self, context: FixContext) -> Dict[str, Any]:
        """分析项目状态"""
        self.logger.info("开始分析项目状态...")
        
        analysis_result = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "issues": {},
            "statistics": {},
            "recommendations": []
        }
        
        # 分析各个模块
        for fix_type, module in self.modules.items():
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
        
        # 生成建议
        analysis_result["recommendations"] = self._generate_recommendations(analysis_result)
        
        return analysis_result
    
    def fix_issues(self, context: FixContext, specific_issues: Optional[List[str]] = None) -> FixReport:
        """修复问题"""
        self.logger.info("开始修复过程...")
        self.stats["start_time"] = datetime.now()
        
        # 创建修复报告
        fix_report = FixReport(
            timestamp=datetime.now(),
            project_root=self.project_root,
            context=context
        )
        
        try:
            # 分析项目
            analysis = self.analyze_project(context)
            fix_report.analysis_result = analysis
            
            # 备份(如果启用)
            if context.backup_enabled and self.config["backup_enabled"]:
                backup_path = self._create_backup(context)
                fix_report.backup_path = backup_path
                self.logger.info(f"已创建备份: {backup_path}")
            
            # 执行修复
            for fix_type, module in self.modules.items():
                if fix_type not in self.config["enabled_modules"]:
                    continue
                
                if specific_issues and fix_type.value not in specific_issues:
                    continue
                
                try:
                    self.logger.info(f"修复 {fix_type.value} 问题...")
                    
                    if context.dry_run or self.config["dry_run"]:
                        # 干运行模式
                        result = self._simulate_fix(module, context)
                    else:
                        # 实际修复
                        result = module.fix(context)
                    
                    fix_report.fix_results[fix_type] = result
                    self._update_stats(result)
                    
                    self.logger.info(f"{fix_type.value} 修复完成: {result.summary()}")
                    
                except Exception as e:
                    self.logger.error(f"修复 {fix_type.value} 失败: {e}")
                    error_result = FixResult(
                        fix_type=fix_type,
                        status=FixStatus.FAILED,
                        error_message=str(e),
                        traceback=traceback.format_exc()
                    )
                    fix_report.fix_results[fix_type] = error_result
                    self.stats["failed_fixes"] += 1
            
            # 验证修复结果
            self.logger.info("验证修复结果...")
            fix_report.validation_result = self._validate_fixes(context)
            
        except Exception as e:
            self.logger.error(f"修复过程失败: {e}")
            fix_report.errors.append(str(e))
            fix_report.traceback = traceback.format_exc()
        
        finally:
            self.stats["end_time"] = datetime.now()
            fix_report.statistics = self._get_final_statistics()
            
            # 保存报告
            self._save_fix_report(fix_report)
            
            self.logger.info(f"修复过程完成 - 总计: {self.stats['total_fixes']}, 成功: {self.stats['successful_fixes']}, 失败: {self.stats['failed_fixes']}")
        
        return fix_report
    
    def _create_backup(self, context: FixContext) -> Path:
        """创建备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"fix_backup_{timestamp}"
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
                # 备份整个项目(排除指定目录)
                shutil.copytree(
                    self.project_root, 
                    backup_path,
                    ignore=shutil.ignore_patterns(*self.config["excluded_paths"])
                )
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"备份创建失败: {e}")
            raise
    
    def _simulate_fix(self, module, context: FixContext) -> FixResult:
        """模拟修复(干运行)"""
        self.logger.info(f"干运行模式 - {module.__class__.__name__}")
        
        # 分析问题但不实际修复
        issues = module.analyze(context)
        
        return FixResult(
            fix_type=module.fix_type,
            status=FixStatus.SIMULATED,
            issues_found=len(issues),
            issues_fixed=0,
            details={"simulated": True, "issues": issues[:10]}  # 只显示前10个问题
        )
    
    def _update_stats(self, result: FixResult):
        """更新统计信息"""
        self.stats["total_fixes"] += 1
        
        if result.status == FixStatus.SUCCESS:
            self.stats["successful_fixes"] += 1
        elif result.status == FixStatus.FAILED:
            self.stats["failed_fixes"] += 1
        elif result.status == FixStatus.SKIPPED:
            self.stats["skipped_fixes"] += 1
    
    def _validate_fixes(self, context: FixContext) -> Dict[str, Any]:
        """验证修复结果"""
        self.logger.info("验证修复结果...")
        
        validation_result = {
            "timestamp": datetime.now().isoformat(),
            "validation_passed": True,
            "remaining_issues": {},
            "validation_errors": []
        }
        
        try:
            # 重新分析项目
            post_fix_analysis = self.analyze_project(context)
            validation_result["post_fix_analysis"] = post_fix_analysis
            
            # 检查是否还有问题
            total_remaining_issues = sum(post_fix_analysis["statistics"].values())
            validation_result["total_remaining_issues"] = total_remaining_issues
            
            if total_remaining_issues > 0:
                validation_result["validation_passed"] = False
                self.logger.warning(f"验证失败 - 仍有 {total_remaining_issues} 个问题未修复")
            else:
                self.logger.info("验证通过 - 所有问题已修复")
                
        except Exception as e:
            validation_result["validation_errors"].append(str(e))
            validation_result["validation_passed"] = False
            self.logger.error(f"验证过程失败: {e}")
        
        return validation_result
    
    def _get_final_statistics(self) -> Dict[str, Any]:
        """获取最终统计信息"""
        duration = None
        if self.stats["start_time"] and self.stats["end_time"]:
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        
        return {
            "total_fixes": self.stats["total_fixes"],
            "successful_fixes": self.stats["successful_fixes"],
            "failed_fixes": self.stats["failed_fixes"],
            "skipped_fixes": self.stats["skipped_fixes"],
            "success_rate": self.stats["successful_fixes"] / max(self.stats["total_fixes"], 1),
            "duration_seconds": duration,
            "start_time": self.stats["start_time"].isoformat() if self.stats["start_time"] else None,
            "end_time": self.stats["end_time"].isoformat() if self.stats["end_time"] else None
        }

    def _save_fix_report(self, fix_report: FixReport):
        """保存修复报告"""
        try:
            reports_dir = self.project_root / "unified_fix_reports"
            reports_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = reports_dir / f"fix_report_{timestamp}.json"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(fix_report), f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"修复报告已保存: {report_file}")
            
        except Exception as e:
            self.logger.error(f"修复报告保存失败: {e}")
    
    def _generate_recommendations(self, analysis_result: Dict[str, Any]) -> List[str]:
        """生成修复建议"""
        recommendations = []
        
        # 基于分析结果生成建议
        for fix_type, count in analysis_result["statistics"].items():
            if count > 0:
                if count > 10:
                    recommendations.append(f"发现大量 {fix_type} 问题 ({count}个),建议优先修复")
                elif count > 5:
                    recommendations.append(f"发现中等数量 {fix_type} 问题 ({count}个),建议及时修复")
                else:
                    recommendations.append(f"发现少量 {fix_type} 问题 ({count}个),可以快速修复")
        
        return recommendations
    
    def get_module_status(self) -> Dict[str, str]:
        """获取模块状态"""
        status = {}
        for fix_type, module in self.modules.items():
            status[fix_type.value] = "enabled" if module else "disabled"
        return status

    def enable_module(self, fix_type: FixType):
        """启用修复模块"""
        if fix_type in self.modules:
            self.config["enabled_modules"].append(fix_type)
            self.logger.info(f"已启用 {fix_type.value} 模块")
    
    def disable_module(self, fix_type: FixType):
        """禁用修复模块"""
        if fix_type in self.config["enabled_modules"]:
            self.config["enabled_modules"].remove(fix_type)
            self.logger.info(f"已禁用 {fix_type.value} 模块")
    
    def cleanup(self):
        """清理资源"""
        self.logger.info("清理统一修复引擎资源...")
        
        # 保存配置
        self.save_config()
        
        # 清理模块
        for module in self.modules.values():
            if hasattr(module, 'cleanup'):
                try:
                    module.cleanup()
                except Exception as e:
                    self.logger.warning(f"模块清理失败: {e}")
        
        self.logger.info("统一修复引擎清理完成")