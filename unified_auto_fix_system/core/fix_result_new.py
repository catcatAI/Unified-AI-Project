"""
修复结果定义
定义修复结果的数据结构
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from .fix_types import FixType, FixStatus, FixScope, FixPriority


@dataclass
class FixResult:
    """单个修复结果"""
    fix_type: FixType
    status: FixStatus
    target_path: Optional[Path] = None
    issues_found: int = 0
    issues_fixed: int = 0
    error_message: Optional[str] = None
    traceback: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0.0
    backup_path: Optional[Path] = None
    
    def summary(self) -> str:
        """获取结果摘要"""
        if self.status == FixStatus.SUCCESS:
            return f"成功修复 {self.issues_fixed} 个问题"
        elif self.status == FixStatus.PARTIAL_SUCCESS:
            return f"部分成功,修复 {self.issues_fixed}/{self.issues_found} 个问题"
        elif self.status == FixStatus.FAILED:
            return f"修复失败, {self.error_message or '未知错误'}"
        elif self.status == FixStatus.SKIPPED:
            return "修复已跳过"
        elif self.status == FixStatus.SIMULATED:
            return f"模拟修复,发现 {self.issues_found} 个问题"
        else:
            return f"修复状态, {self.status.value}"
    
    def is_successful(self) -> bool:
        """检查是否修复成功"""
        return self.status in [FixStatus.SUCCESS, FixStatus.PARTIAL_SUCCESS]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "fix_type": self.fix_type.value,
            "status": self.status.value,
            "target_path": str(self.target_path) if self.target_path else None,
            "issues_found": self.issues_found,
            "issues_fixed": self.issues_fixed,
            "error_message": self.error_message,
            "details": self.details,
            "duration_seconds": self.duration_seconds,
            "backup_path": str(self.backup_path) if self.backup_path else None
        }


@dataclass
class FixContext:
    """修复上下文"""
    project_root: Path
    target_path: Optional[Path] = None
    scope: FixScope = FixScope.PROJECT
    priority: FixPriority = FixPriority.NORMAL
    backup_enabled: bool = True
    dry_run: bool = False
    ai_assisted: bool = False
    custom_rules: Dict[str, Any] = field(default_factory=dict)
    excluded_paths: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "project_root": str(self.project_root),
            "target_path": str(self.target_path) if self.target_path else None,
            "scope": self.scope.value,
            "priority": self.priority.value,
            "backup_enabled": self.backup_enabled,
            "dry_run": self.dry_run,
            "ai_assisted": self.ai_assisted,
            "custom_rules": self.custom_rules,
            "excluded_paths": self.excluded_paths
        }


@dataclass
class FixReport:
    """修复报告"""
    timestamp: datetime
    project_root: Path
    context: FixContext
    fix_results: Dict[FixType, FixResult] = field(default_factory=dict)
    analysis_result: Optional[Dict[str, Any]] = None
    validation_result: Optional[Dict[str, Any]] = None
    backup_path: Optional[Path] = None
    statistics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    traceback: Optional[str] = None
    
    def get_successful_fixes(self) -> List[FixResult]:
        """获取成功的修复结果"""
        return [result for result in self.fix_results.values() if result.is_successful()]
    def get_failed_fixes(self) -> List[FixResult]:
        """获取失败的修复结果"""
        return [result for result in self.fix_results.values() if result.status == FixStatus.FAILED]
    def get_total_issues_found(self) -> int:
        """获取发现的问题总数"""
        return sum(result.issues_found for result in self.fix_results.values())
    def get_total_issues_fixed(self) -> int:
        """获取修复的问题总数"""
        return sum(result.issues_fixed for result in self.fix_results.values())
    def get_success_rate(self) -> float:
        """获取修复成功率"""
        successful = len(self.get_successful_fixes())
        total = len(self.fix_results)
        return successful / max(total, 1)
    
    def get_summary(self) -> str:
        """获取报告摘要"""
        total_fixed = self.get_total_issues_fixed()
        total_found = self.get_total_issues_found()
        success_rate = self.get_success_rate()
        
        summary = f"修复报告摘要:\n"
        summary += f"  总计发现问题: {total_found}\n"
        summary += f"  成功修复问题: {total_fixed}\n"
        summary += f"  修复成功率: {success_rate:.1%}\n"
        summary += f"  修复模块数: {len(self.fix_results)}\n"
        
        if self.errors:
            summary += f"  错误数: {len(self.errors)}\n"
        
        if self.warnings:
            summary += f"  警告数: {len(self.warnings)}\n"
        
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "project_root": str(self.project_root),
            "context": self.context.to_dict(),
            "fix_results": {
                fix_type.value: result.to_dict() 
                for fix_type, result in self.fix_results.items()
            },
            "analysis_result": self.analysis_result,
            "validation_result": self.validation_result,
            "backup_path": str(self.backup_path) if self.backup_path else None,
            "statistics": self.statistics,
            "errors": self.errors,
            "warnings": self.warnings,
            "traceback": self.traceback
        }


@dataclass
class FixStatistics:
    """修复统计信息"""
    total_fixes: int = 0
    successful_fixes: int = 0
    failed_fixes: int = 0
    skipped_fixes: int = 0
    total_issues_found: int = 0
    total_issues_fixed: int = 0
    total_duration_seconds: float = 0.0
    def get_success_rate(self) -> float:
        """获取成功率"""
        return self.successful_fixes / max(self.total_fixes, 1)
    
    def update_with_result(self, result: FixResult):
        """使用修复结果更新统计"""
        self.total_fixes += 1
        self.total_issues_found += result.issues_found
        self.total_issues_fixed += result.issues_fixed
        if result.is_successful():
            self.successful_fixes += 1
        elif result.status == FixStatus.FAILED:
            self.failed_fixes += 1
        elif result.status == FixStatus.SKIPPED:
            self.skipped_fixes += 1
        
        self.total_duration_seconds += result.duration_seconds
    def get_summary(self) -> str:
        """获取统计摘要"""
        return (
            f"修复统计: 总计{self.total_fixes}次修复, "
            f"成功{self.successful_fixes}次 ({self.get_success_rate():.1%}), "
            f"失败{self.failed_fixes}次, 跳过{self.skipped_fixes}次, "
            f"发现问题{self.total_issues_found}个, 修复问题{self.total_issues_fixed}个"
        )


class FixResultManager:
    """修复结果管理器"""
    
    def __init__(self):
        self.results: List[FixResult] = []
        self.statistics = FixStatistics()
    
    def add_result(self, result: FixResult):
        """添加修复结果"""
        self.results.append(result)
        self.statistics.update_with_result(result)
    
    def get_results_by_type(self, fix_type: FixType) -> List[FixResult]:
        """按类型获取修复结果"""
        return [result for result in self.results if result.fix_type == fix_type]
    def get_results_by_status(self, status: FixStatus) -> List[FixResult]:
        """按状态获取修复结果"""
        return [result for result in self.results if result.status == status]
    def get_successful_results(self) -> List[FixResult]:
        """获取成功的修复结果"""
        return [result for result in self.results if result.is_successful()]
    def get_failed_results(self) -> List[FixResult]:
        """获取失败的修复结果"""
        return [result for result in self.results if result.status == FixStatus.FAILED]
    def generate_report(self) -> FixReport:
        """生成修复报告"""
        # 这里可以基于收集的结果生成完整的修复报告
        # 简化版本,实际使用时需要更多上下文信息
        return FixReport(
            timestamp=datetime.now(),
            project_root=Path("."),  # 需要根据实际情况设置
            context=FixContext(project_root=Path(".")),  # 需要根据实际情况设置
            fix_results={result.fix_type: result for result in self.results}
        )

    def clear(self):
        """清空所有结果"""
        self.results.clear()
        self.statistics = FixStatistics()
    
    def export_to_json(self, file_path: Union[str, Path]):
        """导出结果为JSON"""
        data = {
            "results": [result.to_dict() for result in self.results],
            "statistics": {
                "total_fixes": self.statistics.total_fixes,
                "successful_fixes": self.statistics.successful_fixes,
                "failed_fixes": self.statistics.failed_fixes,
                "skipped_fixes": self.statistics.skipped_fixes,
                "total_issues_found": self.statistics.total_issues_found,
                "total_issues_fixed": self.statistics.total_issues_fixed,
                "success_rate": self.statistics.get_success_rate(),
                "total_duration_seconds": self.statistics.total_duration_seconds
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(data, f, indent=2, ensure_ascii=False)
