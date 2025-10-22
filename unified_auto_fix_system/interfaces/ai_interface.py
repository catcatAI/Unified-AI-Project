"""
AI/AGI接口
为AI代理和AGI系统提供统一的自动修复接口
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from datetime import datetime

from ..core.unified_fix_engine import UnifiedFixEngine, FixContext
from ..core.fix_result import FixReport
from ..core.fix_types import FixType, FixScope, FixPriority, FixStatus


@dataclass
class AIFixRequest:
    """AI修复请求"""
    agent_id: str
    request_type: str  # analyze, fix, status, config
    target_path: Optional[str] = None
    fix_types: Optional[List[str]] = None
    scope: str = "project"
    priority: str = "normal"
    ai_assisted: bool = True
    custom_rules: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AIFixResponse:
    """AI修复响应"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AIFixInterface:
    """
    AI/AGI自动修复接口

    为AI代理和AGI系统提供统一的自动修复服务接口：
    - 问题分析和诊断
    - 智能修复建议
    - 修复执行和监控
    - 学习和优化
    """
    
    def __init__(self, project_root: Union[str, Path], config_path: Optional[Path] = None):
        self.project_root = Path(project_root).resolve()
        self.config_path = config_path
        
        # 初始化统一修复引擎
        self.fix_engine = UnifiedFixEngine(self.project_root, config_path)
        
        # 设置AI接口专用日志
        self.logger = logging.getLogger(f"{__name__}.AIFixInterface")
        
        # 修复历史记录
        self.fix_history = []
        
        # AI学习数据
        self.learning_data = {
            "successful_fixes": [],
            "failed_fixes": [],
            "patterns": {},
            "recommendations": {}
        }
    
    def process_request(self, request: AIFixRequest) -> AIFixResponse:
        """处理AI修复请求"""
        self.logger.info(f"处理AI修复请求: {request.request_type} from {request.agent_id}")
        
        try:
            if request.request_type == "analyze":
                return self._handle_analyze_request(request)
            elif request.request_type == "fix":
                return self._handle_fix_request(request)
            elif request.request_type == "status":
                return self._handle_status_request(request)
            elif request.request_type == "config":
                return self._handle_config_request(request)
            else:
                return AIFixResponse(
                    success=False,
                    message=f"未知的请求类型: {request.request_type}",
                    error="invalid_request_type"
                )
        
        except Exception as e:
            self.logger.error(f"处理AI请求失败: {e}")
            return AIFixResponse(
                success=False,
                message="处理请求时发生错误",
                error=str(e)
            )
    
    def _handle_analyze_request(self, request: AIFixRequest) -> AIFixResponse:
        """处理分析请求"""
        try:
            # 创建修复上下文
            context = self._create_fix_context(request)
            
            # 分析项目
            analysis_result = self.fix_engine.analyze_project(context)
            
            # AI增强分析
            ai_enhanced_result = self._enhance_analysis_with_ai(analysis_result, request)
            
            # 记录历史
            self._record_analysis_history(request, {"analysis_result": ai_enhanced_result})

            return AIFixResponse(
                success=True,
                message="项目分析完成",
                data={
                    "analysis_result": ai_enhanced_result,
                    "recommended_fixes": self._get_recommended_fixes(analysis_result),
                    "priority_issues": self._identify_priority_issues(analysis_result),
                    "ai_insights": self._generate_ai_insights(analysis_result)
                }
            )
        
        except Exception as e:
            self.logger.error(f"分析请求处理失败: {e}")
            return AIFixResponse(
                success=False,
                message="项目分析失败",
                error=str(e)
            )
    
    def _handle_fix_request(self, request: AIFixRequest) -> AIFixResponse:
        """处理修复请求"""
        try:
            # 创建修复上下文
            context = self._create_fix_context(request)
            
            # AI预处理 - 优化修复策略
            optimized_context = self._optimize_fix_strategy(context, request)
            
            # 执行修复
            fix_report = self.fix_engine.fix_issues(optimized_context, request.fix_types)
            
            # AI后处理 - 学习和改进
            self._learn_from_fix_results(fix_report, request)
            
            # 记录历史
            self._record_fix_history(request, fix_report)
            
            # 生成AI增强报告
            enhanced_report = self._enhance_fix_report_with_ai(fix_report, request)
            
            return AIFixResponse(
                success=True,
                message="修复执行完成",
                data={
                    "fix_report": enhanced_report,
                    "ai_recommendations": self._generate_ai_recommendations(fix_report),
                    "next_steps": self._suggest_next_steps(fix_report),
                    "learning_updates": self._get_learning_updates()
                }
            )
        
        except Exception as e:
            self.logger.error(f"修复请求处理失败: {e}")
            return AIFixResponse(
                success=False,
                message="修复执行失败",
                error=str(e)
            )
    
    def _handle_status_request(self, request: AIFixRequest) -> AIFixResponse:
        """处理状态请求"""
        try:
            status_info = {
                "engine_status": "running",
                "project_root": str(self.fix_engine.project_root),
                "modules_enabled": len([m for m in self.fix_engine.get_module_status().values() if m == "enabled"]),
                "total_fixes": self.fix_engine.stats["total_fixes"],
                "successful_fixes": self.fix_engine.stats["successful_fixes"],
                "failed_fixes": self.fix_engine.stats["failed_fixes"]
            }
            
            return AIFixResponse(
                success=True,
                message="状态信息获取成功",
                data=status_info
            )
        except Exception as e:
            return AIFixResponse(
                success=False,
                message="状态信息获取失败",
                error=str(e)
            )
    
    def _handle_config_request(self, request: AIFixRequest) -> AIFixResponse:
        """处理配置请求"""
        try:
            config_info = {
                "config": self.fix_engine.config,
                "config_path": str(self.fix_engine.config_path)
            }
            
            return AIFixResponse(
                success=True,
                message="配置信息获取成功",
                data=config_info
            )
        except Exception as e:
            return AIFixResponse(
                success=False,
                message="配置信息获取失败",
                error=str(e)
            )
    
    def _create_fix_context(self, request: AIFixRequest) -> FixContext:
        """创建修复上下文"""
        # 解析目标路径
        target_path = None
        if request.target_path:
            target_path = Path(request.target_path)
            if not target_path.is_absolute():
                target_path = self.fix_engine.project_root / target_path
        
        # 解析范围
        scope_map = {
            "project": FixScope.PROJECT,
            "backend": FixScope.BACKEND,
            "frontend": FixScope.FRONTEND,
            "desktop": FixScope.DESKTOP,
            "file": FixScope.SPECIFIC_FILE,
            "directory": FixScope.SPECIFIC_DIRECTORY
        }
        scope = scope_map.get(request.scope, FixScope.PROJECT)
        
        # 解析优先级
        priority_map = {
            "critical": FixPriority.CRITICAL,
            "high": FixPriority.HIGH,
            "normal": FixPriority.NORMAL,
            "low": FixPriority.LOW
        }
        priority = priority_map.get(request.priority, FixPriority.NORMAL)
        
        # 创建上下文
        context = FixContext(
            project_root=self.fix_engine.project_root,
            target_path=target_path,
            scope=scope,
            priority=priority,
            backup_enabled=True,
            dry_run=False,
            ai_assisted=request.ai_assisted,
            custom_rules=request.custom_rules or {}
        )
        
        return context
    
    def _get_recommended_fixes(self, analysis_result: Dict[str, Any]) -> List[str]:
        """获取推荐修复"""
        recommendations = []
        issues = analysis_result.get("issues", {})
        
        for fix_type, issue_list in issues.items():
            if issue_list:
                count = len(issue_list)
                if count > 10:
                    recommendations.append(f"发现大量 {fix_type} 问题 ({count}个),建议优先修复")
                elif count > 5:
                    recommendations.append(f"发现中等数量 {fix_type} 问题 ({count}个),建议及时修复")
                else:
                    recommendations.append(f"发现少量 {fix_type} 问题 ({count}个),可以快速修复")
        
        return recommendations
    
    def _identify_priority_issues(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """识别优先级问题"""
        priority_issues = {}
        issues = analysis_result.get("issues", {})
        
        # 识别关键问题
        critical_types = ["syntax_fix", "security_fix", "dependency_fix"]
        critical_issues = {}
        for ct in critical_types:
            if ct in issues and issues[ct]:
                critical_issues[ct] = issues[ct]
        
        priority_issues["critical"] = critical_issues
        priority_issues["total_critical"] = sum(len(v) for v in critical_issues.values())
        
        return priority_issues
    
    def _generate_ai_insights(self, analysis_result: Dict[str, Any]) -> List[str]:
        """生成AI洞察"""
        insights = []
        issues = analysis_result.get("issues", {})
        
        total_issues = sum(len(v) for v in issues.values())
        if total_issues > 50:
            insights.append("项目存在大量问题，建议进行全面重构")
        elif total_issues > 20:
            insights.append("项目存在中等问题，建议分阶段修复")
        else:
            insights.append("项目问题较少，可以快速修复")
        
        return insights
    
    def _optimize_fix_strategy(self, context: FixContext, request: AIFixRequest) -> FixContext:
        """优化修复策略"""
        # 这里可以实现AI驱动的修复策略优化
        # 目前返回原始上下文
        return context
    
    def _learn_from_fix_results(self, fix_report: FixReport, request: AIFixRequest):
        """从修复结果中学习"""
        # 这里可以实现AI学习机制
        # 目前只是记录成功和失败的修复
        if fix_report.get_success_rate() >= 0.8:
            self.learning_data["successful_fixes"].append({
                "request": request.to_dict(),
                "report": fix_report.to_dict(),
                "timestamp": datetime.now().isoformat()
            })
        else:
            self.learning_data["failed_fixes"].append({
                "request": request.to_dict(),
                "report": fix_report.to_dict(),
                "timestamp": datetime.now().isoformat()
            })
    
    def _enhance_analysis_with_ai(self, analysis_result: Dict[str, Any], request: AIFixRequest) -> Dict[str, Any]:
        """使用AI增强分析"""
        # 添加AI增强的分析结果
        enhanced_result = analysis_result.copy()
        enhanced_result["ai_enhanced"] = {
            "health_score": self._calculate_project_health(analysis_result),
            "priority_issues": self._identify_priority_issues(analysis_result),
            "ai_insights": self._generate_ai_insights(analysis_result),
            "recommended_approach": "建议按优先级顺序修复关键问题"
        }
        return enhanced_result
    
    def _enhance_fix_report_with_ai(self, fix_report: FixReport, request: AIFixRequest) -> Dict[str, Any]:
        """使用AI增强修复报告"""
        # 添加AI增强的修复报告信息
        enhanced_report = fix_report.to_dict()
        enhanced_report["ai_enhanced"] = {
            "next_steps": "建议进行回归测试确保修复没有引入新问题",
            "learning_outcome": "本次修复为AI学习模型提供了新的训练数据",
            "improvement_suggestions": ["建议增加单元测试覆盖率", "建议优化代码结构"]
        }
        return enhanced_report
    
    def _generate_ai_recommendations(self, fix_report: FixReport) -> List[str]:
        """生成AI推荐"""
        recommendations = []
        success_rate = fix_report.get_success_rate()
        
        if success_rate < 0.5:
            recommendations.append("修复成功率较低，建议重新评估修复策略")
        elif success_rate < 0.8:
            recommendations.append("修复成功率中等，建议关注失败的修复项")
        else:
            recommendations.append("修复成功率较高，建议进行代码审查")
        
        return recommendations
    
    def _suggest_next_steps(self, fix_report: FixReport) -> List[str]:
        """建议下一步操作"""
        next_steps = []
        failed_fixes = fix_report.get_failed_fixes()
        
        if failed_fixes:
            next_steps.append("分析失败的修复项，找出根本原因")
            next_steps.append("考虑使用不同的修复策略或工具")
        
        next_steps.append("运行测试套件验证修复效果")
        next_steps.append("提交修复结果到版本控制系统")
        
        return next_steps
    
    def _get_learning_updates(self) -> Dict[str, Any]:
        """获取学习更新"""
        return {
            "successful_fixes_count": len(self.learning_data["successful_fixes"]),
            "failed_fixes_count": len(self.learning_data["failed_fixes"]),
            "patterns_count": len(self.learning_data["patterns"]),
            "recommendations_count": len(self.learning_data["recommendations"])
        }
    
    def _calculate_project_health(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """计算项目健康度"""
        try:
            # 计算总问题数
            total_issues = sum(len(issues) for issues in analysis_result.get("issues", {}).values())
            
            # 计算健康分数 (问题越少分数越高)
            health_score = max(0, 100 - min(total_issues, 100))
            
            return {
                "health_score": health_score,
                "total_issues": total_issues,
                "critical_issues": len(analysis_result.get("issues", {}).get("syntax_fix", [])) +
                                 len(analysis_result.get("issues", {}).get("security_fix", [])),
                "health_status": "good" if health_score > 80 else "fair" if health_score > 60 else "poor"
            }

        except Exception as e:
            self.logger.error(f"计算项目健康度失败: {e}")
            return {
                "health_score": 0,
                "total_issues": 0,
                "critical_issues": 0,
                "health_status": "unknown",
                "error": str(e)
            }
    
    def _record_analysis_history(self, request: AIFixRequest, result: Dict[str, Any]):
        """记录分析历史"""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": request.agent_id,
            "request_type": request.request_type,
            "result": result
        }
        
        self.fix_history.append((request.agent_id, history_entry))
        
        # 限制历史记录数量
        if len(self.fix_history) > 1000:
            self.fix_history = self.fix_history[-1000:]
    
    def _record_fix_history(self, request: AIFixRequest, fix_report: FixReport):
        """记录修复历史"""
        self._record_analysis_history(request, {"fix_report": fix_report.to_dict()})