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

from ..core.unified_fix_engine import UnifiedFixEngine
from ..core.fix_types import FixType, FixScope, FixPriority, FixStatus
from ..core.fix_result import FixResult, FixReport, FixContext


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
    timestamp: str = None
    
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
# 
            elif request.request_type == "status":
                return self._handle_status_request(request)
            elif request.request_type == "config":
                return self._handle_config_request(request)
                # 
# 
            else:
                return AIFixResponse(
                success=False,
                # 

                    message=f"未知的请求类型: {request.request_type}",
                    error="invalid_request_type"
                )
        
        except Exception as e:
#             self.logger.error(f"处理AI请求失败: {e}")

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
# 
            analysis_result = self.fix_engine.analyze_project(context)
#             
            # AI增强分析
            ai_enhanced_result = self._enhance_analysis_with_ai(analysis_result, request)
            
             # 记录历史
# 
            self._record_analysis_history(request, ai_enhanced_result)

 #             

            return AIFixResponse(
                success=True,
                message="项目分析完成",
# 
                data={
                    "analysis_result": ai_enhanced_result,
                    "recommended_fixes": self._get_recommended_fixes(analysis_result),



                    "priority_issues": self._identify_priority_issues(analysis_result),
                    "ai_insights": self._generate_ai_insights(analysis_result)
# 

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
# 
            
             # 执行修复

            fix_report = self.fix_engine.fix_issues(optimized_context, request.fix_types)
            
            # AI后处理 - 学习和改进
            self._learn_from_fix_results(fix_report, request)

#             
            # 记录历史
            self._record_fix_history(request, fix_report)
            #             

            # 生成AI增强报告
            enhanced_report = self._enhance_fix_report_with_ai(fix_report, request)
            
            return AIFixResponse(
                success=True,
                message="修复执行完成",


                data={

                    "fix_report": enhanced_report,
                    "ai_recommendations": self._generate_ai_recommendations(fix_report),
# 
# 
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
# 
            )
#     
    def _handle_status_request(self, request: AIFixRequest) -> AIFixResponse:
        """处理状态请求"""
        try:
            # 获取引擎状态
            module_status = self.fix_engine.get_module_status()
            
             # 获取修复历史

#             recent_history = self._get_recent_fix_history(limit=10)
#             
             # 获取学习状态
             # 


            learning_status = self._get_learning_status()
            
             # 获取项目健康度

            project_health = self._calculate_project_health()
            
            return AIFixResponse(
            success=True,


                message="状态查询完成",
                data={
                    "engine_status": module_status,
                    "recent_history": recent_history,
# 
# 
                    "learning_status": learning_status,
# 
"project_health": project_health,

                    "statistics": self._get_engine_statistics()


                }
            )
#         
        except Exception as e:
#             self.logger.error(f"状态请求处理失败: {e}")

            return AIFixResponse(
                success=False,
                message="状态查询失败",
# 

 #                 error=str(e)

            )
    
#     def _handle_config_request(self, request: AIFixRequest) -> AIFixResponse:
#         """处理配置请求"""
        try:
            if request.custom_rules:

                # 更新配置
                # 

                self.fix_engine.config.update(request.custom_rules)
                self.fix_engine.save_config()



                
                return AIFixResponse(
                    success=True,
                    message="配置更新成功"
                )
            else:
                # 返回当前配置
                return AIFixResponse(
                success=True,

                    message="配置查询完成",
                    data={

                        "current_config": self.fix_engine.config,
                        "available_modules": [fix_type.value for fix_type in FixType],
                        "recommended_settings": self._get_recommended_settings()
                    }
                )
        
        except Exception as e:
            self.logger.error(f"配置请求处理失败: {e}")
            return AIFixResponse(
#                 success=False,
                message="配置操作失败",
#                 error=str(e)
            )
    
    def _create_fix_context(self, request: AIFixRequest) -> FixContext:
        """创建修复上下文"""
        # 解析目标路径
        target_path = None

        if request.target_path:
            target_path = Path(request.target_path)
# 
            if not target_path.is_absolute():
                target_path = self.project_root / target_path
        
        # 解析修复类型
#         fix_types = []
#         if request.fix_types:

            for fix_type_str in request.fix_types:
                try:
                    fix_type = FixType(fix_type_str)


                    fix_types.append(fix_type)
                except ValueError:
                    self.logger.warning(f"未知的修复类型: {fix_type_str}")
        
         # 创建上下文

        context = FixContext(
            project_root=self.project_root,
            target_path=target_path,
            scope=FixScope(request.scope),

 priority=FixPriority(request.priority),

            ai_assisted=request.ai_assisted,

            custom_rules=request.custom_rules or {}
        )
        
        return context
    
    def _enhance_analysis_with_ai(self, analysis_result: Dict[str, Any], 
                                 request: AIFixRequest) -> Dict[str, Any]:
        """使用AI增强分析结果"""
        # AI分析增强逻辑
        enhanced_result = analysis_result.copy()
        
        # 添加AI洞察
        ai_insights = []
        
         # 分析问题模式


        for fix_type, issues in analysis_result.get("issues", {}).items():
            if len(issues) > 10:
                ai_insights.append({
                    "type": "pattern_detection",
                    "fix_type": fix_type,
                    "message": f"发现大量{fix_type}问题，可能存在系统性问题",
                    "confidence": 0.8,
                    "recommendation": "建议优先处理此类型问题"
                })
        
        # 基于历史数据预测
        if request.agent_id in self.learning_data["recommendations"]:
            historical_data = self.learning_data["recommendations"][request.agent_id]
            ai_insights.extend(historical_data.get("insights", []))
        
        enhanced_result["ai_insights"] = ai_insights
        enhanced_result["ai_confidence"] = self._calculate_ai_confidence(analysis_result)
        
        return enhanced_result
    
    def _optimize_fix_strategy(self, context: FixContext, 
                              request: AIFixRequest) -> FixContext:
        """AI优化修复策略"""
        # 基于历史数据优化修复顺序
        if request.agent_id in self.learning_data["patterns"]:
            patterns = self.learning_data["patterns"][request.agent_id]


            
             # 调整优先级

            if "preferred_fix_order" in patterns:

                # 重新排序修复类型
                preferred_order = patterns["preferred_fix_order"]


 # 这里可以实现具体的优先级调整逻辑

                pass
        
        # 基于问题类型调整策略
        if request.fix_types:


            if "syntax_fix" in request.fix_types:
                # 语法修复优先
                context.priority = FixPriority.HIGH
            elif "security_fix" in request.fix_types:
                # 安全修复最高优先级
                context.priority = FixPriority.CRITICAL

        
        return context
    
    def _learn_from_fix_results(self, fix_report: FixReport, request: AIFixRequest):
        """从修复结果中学习"""


        agent_id = request.agent_id
        
        # 记录成功的修复
        if fix_report.get_success_rate() > 0.8:  # 成功率大于80%
            success_data = {
                "timestamp": datetime.now().isoformat(),
                "fix_types": [ft.value for ft in fix_report.fix_results.keys()],

                "success_rate": fix_report.get_success_rate(),

                "context": request.context
            }
            
            if agent_id not in self.learning_data["successful_fixes"]:
                self.learning_data["successful_fixes"][agent_id] = []
            self.learning_data["successful_fixes"][agent_id].append(success_data)
        
         # 记录失败的修复

        failed_fixes = fix_report.get_failed_fixes()
        if failed_fixes:
            failure_data = {
                "timestamp": datetime.now().isoformat(),
                "failed_fixes": [asdict(result) for result in failed_fixes],
                "context": request.context
            }
            
            if agent_id not in self.learning_data["failed_fixes"]:
                self.learning_data["failed_fixes"][agent_id] = []
            self.learning_data["failed_fixes"][agent_id].append(failure_data)
        
        # 更新模式识别
        self._update_pattern_recognition(agent_id, fix_report)
    
    def _update_pattern_recognition(self, agent_id: str, fix_report: FixReport):
        """更新模式识别"""
        if agent_id not in self.learning_data["patterns"]:

            self.learning_data["patterns"][agent_id] = {}
        
        patterns = self.learning_data["patterns"][agent_id]
        
        # 分析修复类型偏好
        successful_fixes = fix_report.get_successful_fixes()
        if successful_fixes:


            fix_type_order = [result.fix_type.value for result in successful_fixes]
            patterns["preferred_fix_order"] = fix_type_order

        
        # 分析成功率模式
        total_fixes = len(fix_report.fix_results)

        successful_count = len(successful_fixes)
        
        if total_fixes > 0:
            success_rate = successful_count / total_fixes
            patterns["last_success_rate"] = success_rate

            
            # 更新平均成功率
            if "avg_success_rate" not in patterns:


                patterns["avg_success_rate"] = []
            patterns["avg_success_rate"].append(success_rate)
            
             # 保持最近10次的记录


            if len(patterns["avg_success_rate"]) > 10:
                patterns["avg_success_rate"] = patterns["avg_success_rate"][-10:]
    
    def _get_recommended_fixes(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取推荐的修复"""

        recommendations = []
        
        # 基于问题严重程度推荐
        for fix_type, issues in analysis_result.get("issues", {}).items():


            if len(issues) > 0:
                severity = "high" if len(issues) > 10 else "medium" if len(issues) > 5 else "low"
                
                recommendations.append({
                "fix_type": fix_type,

                    "priority": severity,

                    "issue_count": len(issues),
                    "estimated_effort": self._estimate_fix_effort(fix_type, len(issues)),

                    "confidence": 0.8
                })
        
        # 按优先级排序
        recommendations.sort(key=lambda x: (x["priority"], -x["issue_count"]))

        
        return recommendations[:5]  # 返回前5个推荐
    
    def _identify_priority_issues(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别优先级问题"""
        priority_issues = []


        
         # 语法错误最高优先级

        syntax_issues = analysis_result.get("issues", {}).get("syntax_fix", [])

        if syntax_issues:
            priority_issues.append({
                "type": "syntax_fix",
                "count": len(syntax_issues),
                "priority": "critical",



                "reason": "语法错误会阻止代码运行"
            })
        
         # 安全漏洞次高优先级

        security_issues = analysis_result.get("issues", {}).get("security_fix", [])
        if security_issues:
            priority_issues.append({
            "type": "security_fix",

 "count": len(security_issues),

 "priority": "high",

                "reason": "安全漏洞可能导致系统被攻击"
            })
        
        return priority_issues
    
    def _generate_ai_insights(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成AI洞察"""
        insights = []


        
        # 问题趋势分析
        total_issues = sum(len(issues) for issues in analysis_result.get("issues", {}).values())
        
        if total_issues > 50:
            insights.append({
                "type": "trend_analysis",
                "title": "高问题密度",

                "description": f"发现 {total_issues} 个问题，建议进行系统性重构",

                "confidence": 0.9,
                "actionable": True

            })
        
        # 代码质量评估
        syntax_issues = len(analysis_result.get("issues", {}).get("syntax_fix", []))
        import_issues = len(analysis_result.get("issues", {}).get("import_fix", []))

        
        if syntax_issues > 10 or import_issues > 20:
            insights.append({
                "type": "quality_assessment",
                "title": "代码质量警告",
                "description": "存在大量基础代码质量问题，建议加强代码审查",

 "confidence": 0.8,

                "actionable": True

            })
        
        return insights
    
    def _enhance_fix_report_with_ai(self, fix_report: FixReport, 
                                   request: AIFixRequest) -> Dict[str, Any]:
        """使用AI增强修复报告"""
        base_report = asdict(fix_report)


        
        # 添加AI分析
        ai_analysis = {
            "fix_effectiveness": self._calculate_fix_effectiveness(fix_report),
            "learning_improvements": self._identify_learning_improvements(fix_report),

 "predictive_insights": self._generate_predictive_insights(fix_report),


 "agent_performance": self._evaluate_agent_performance(request.agent_id, fix_report)

        }
        
        base_report["ai_analysis"] = ai_analysis
        return base_report

    
    def _calculate_fix_effectiveness(self, fix_report: FixReport) -> Dict[str, Any]:
        """计算修复效果"""
        success_rate = fix_report.get_success_rate()

        total_fixed = fix_report.get_total_issues_fixed()

        total_found = fix_report.get_total_issues_found()
        
        return {
        "success_rate": success_rate,


 "fix_efficiency": total_fixed / max(total_found, 1),


 "quality_score": self._calculate_quality_score(success_rate, total_fixed),

            "improvement_potential": self._calculate_improvement_potential(fix_report)

        }
    
    def _calculate_quality_score(self, success_rate: float, total_fixed: int) -> float:
        """计算质量分数"""

 # 基于成功率和修复数量计算质量分数


        base_score = success_rate * 100
        quantity_bonus = min(total_fixed / 10, 10)  # 最多10分奖励
        
        return min(base_score + quantity_bonus, 100)
    
    def _calculate_improvement_potential(self, fix_report: FixReport) -> float:
        """计算改进潜力"""
        failed_fixes = fix_report.get_failed_fixes()

        if not failed_fixes:

            return 0.0
#         
        # 基于失败修复的复杂度和数量计算改进潜力
        total_failed = len(failed_fixes)


        complexity_factor = sum(1 for fix in failed_fixes if fix.fix_type in [
            FixType.SECURITY_FIX, FixType.PERFORMANCE_FIX
        ])
        
        return min((total_failed + complexity_factor * 2) / 10, 1.0)
    
    def _get_engine_statistics(self) -> Dict[str, Any]:
        """获取引擎统计信息"""

        return {
#         "total_fixes": self.fix_engine.stats["total_fixes"],
# 
"successful_fixes": self.fix_engine.stats["successful_fixes"],


            "success_rate": self.fix_engine.stats["successful_fixes"] / max(self.fix_engine.stats["total_fixes"], 1),
            "module_status": self.fix_engine.get_module_status(),
            "learning_data_size": {

 "successful_fixes": sum(len(fixes) for fixes in self.learning_data["successful_fixes"].values()),

                "failed_fixes": sum(len(fixes) for fixes in self.learning_data["failed_fixes"].values()),
                "patterns": len(self.learning_data["patterns"])

 }
# 
# 
 }

    
    def _get_recent_fix_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的修复历史"""
        # 从所有代理的修复历史中提取最近的记录


        all_history = []
        for agent_id, history in self.fix_history:

            all_history.extend(history)
        
        # 按时间排序并返回最近的记录
        all_history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return all_history[:limit]

    
    def _get_learning_status(self) -> Dict[str, Any]:
        """获取学习状态"""

        return {
            "patterns_learned": len(self.learning_data["patterns"]),
            "successful_experiences": sum(len(fixes) for fixes in self.learning_data["successful_fixes"].values()),
            "failure_experiences": sum(len(fixes) for fixes in self.learning_data["failed_fixes"].values()),
            "learning_effectiveness": self._calculate_learning_effectiveness()


        }
    
    def _calculate_learning_effectiveness(self) -> float:
        """计算学习效果"""

        total_successes = sum(len(fixes) for fixes in self.learning_data["successful_fixes"].values())
        total_failures = sum(len(fixes) for fixes in self.learning_data["failed_fixes"].values())
        
        if total_successes + total_failures == 0:
            return 0.0
        
        return total_successes / (total_successes + total_failures)
    
    def _calculate_project_health(self) -> Dict[str, Any]:
        """计算项目健康度"""
        # 创建临时上下文进行分析
        context = FixContext(
        project_root=self.project_root,

            scope=FixScope.PROJECT
        )
        
        try:
            analysis_result = self.fix_engine.analyze_project(context)
            
            # 计算健康度分数
            total_issues = sum(len(issues) for issues in analysis_result.get("issues", {}).values())
            
            # 基于问题数量和类型计算健康度
            health_score = max(0, 100 - total_issues)
            
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
        self._record_analysis_history(request, {"fix_report": asdict(fix_report)})