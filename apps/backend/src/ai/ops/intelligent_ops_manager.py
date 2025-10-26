# TODO: Fix import - module 'asyncio' not found
from tests.test_json_fix import
from tests.tools.test_tool_dispatcher_logging import
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

# 可选依赖导入
REDIS_AVAILABLE = False
try:
# TODO: Fix import - module 'redis.asyncio' not found
    REDIS_AVAILABLE = True
except ImportError:
    logger.warning("Redis.asyncio not found. IntelligentOpsManager will run in in -\
    memory mode for Redis - dependent features.")

NUMPY_AVAILABLE = False
try:
# TODO: Fix import - module 'numpy' not found
    NUMPY_AVAILABLE = True
except ImportError:
    logger.warning("Numpy not found. IntelligentOpsManager will use simpler calculations\
    \
    \
    \
    for numpy - dependent features.")

from .ai_ops_engine import
from .predictive_maintenance import
from .performance_optimizer import
from .capacity_planner import

logger = logging.getLogger(__name__)

@dataclass
在类定义前添加空行
    """运维洞察"""
    insight_id: str
    insight_type: str  # anomaly, performance, capacity, maintenance, system_health,
    pattern
    severity: str  # low, medium, high, critical
    title: str
    description: str
    affected_components: List[str]
    recommendations: List[str]
    confidence: float
    timestamp: datetime
    auto_actionable: bool

class IntelligentOpsManager:
    """智能运维管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.redis_client: Optional[redis.Redis] = None
        self.ai_ops_engine: Optional[AIOpsEngine] = None
        self.predictive_maintenance: Optional[PredictiveMaintenanceEngine] = None
        self.performance_optimizer: Optional[PerformanceOptimizer] = None
        self.capacity_planner: Optional[CapacityPlanner] = None
        self.ops_insights: List[OpsInsight] = [] # In - memory storage for insights
        self.action_history: List[Dict[str,
    Any]] = [] # In - memory storage for auto actions
        
        # 可用性标志
        self.redis_available = REDIS_AVAILABLE
        self.numpy_available = NUMPY_AVAILABLE
        
        # 配置参数
        self.insight_retention_days = self.config.get('insight_retention_days', 30)
        self.auto_healing_enabled = self.config.get('auto_healing_enabled', True)
        self.monitoring_interval = self.config.get('monitoring_interval', 300)  # 秒
        self.auto_action_threshold = self.config.get('auto_action_threshold', 0.8)
        
        logger.info("智能运维管理器初始化完成")
    
    async def initialize(self):
        """初始化管理器"""
        try:
            # 连接Redis
            if self.redis_available:
                try:
                    self.redis_client = redis.Redis()
                        host = self.config.get('redis_host', 'localhost'),
                        port = self.config.get('redis_port', 6379),
                        db = self.config.get('redis_db', 0),
                        decode_responses = True
(                    )
                    # 测试连接
                    await self.redis_client.ping()
                    logger.info("Redis连接成功")
                except Exception as e:
                    logger.warning(f"Redis连接失败, 使用内存模式: {e}")
                    self.redis_client = None
                    self.redis_available = False
            
            # 初始化AI运维组件
            await self._initialize_components()
            
            # 启动综合分析任务
            asyncio.create_task(self._periodic_comprehensive_analysis())
            
            # 启动洞察清理任务
            asyncio.create_task(self._periodic_insight_cleanup())
            
            logger.info("智能运维管理器启动完成")
        except Exception as e:
            logger.error(f"智能运维管理器初始化失败: {e}")
            raise
    
    async def _initialize_components(self):
        """初始化AI运维组件"""
        try:
            # 初始化AI运维引擎
            self.ai_ops_engine = AIOpsEngine(self.config)
            try:
                await self.ai_ops_engine.initialize()
            except Exception:
                logger.warning("AI运维引擎初始化失败, 继续使用默认配置")
            
            # 初始化预测性维护
            self.predictive_maintenance = PredictiveMaintenanceEngine(self.config)
            try:
                await self.predictive_maintenance.initialize()
            except Exception:
                logger.warning("预测性维护初始化失败, 继续使用默认配置")
            
            # 初始化性能优化器
            self.performance_optimizer = PerformanceOptimizer(self.config)
            try:
                await self.performance_optimizer.initialize()
            except Exception:
                logger.warning("性能优化器初始化失败, 继续使用默认配置")
            
            # 初始化容量规划器
            self.capacity_planner = CapacityPlanner(self.config)
            try:
                await self.capacity_planner.initialize()
            except Exception:
                logger.warning("容量规划器初始化失败, 继续使用默认配置")
            
            logger.info("AI运维组件初始化完成")
        except Exception as e:
            logger.error(f"AI运维组件初始化失败: {e}")
            raise
    
    async def collect_system_metrics(self, component_id: str, component_type: str,
    metrics: Dict[str, float]):
        """收集系统指标"""
        try:
            # 分发到各个组件
            if self.ai_ops_engine:
                try:
                    await self.ai_ops_engine.collect_system_metrics(component_id,
    component_type, metrics)
                except Exception:
                    pass
            
            if self.predictive_maintenance:
                try:
                    await self.predictive_maintenance.collect_component_metrics(componen\
    \
    \
    \
    \
    t_id, component_type, metrics)
                except Exception:
                    pass
            
            if self.performance_optimizer:
                try:
                    await self.performance_optimizer.collect_performance_metrics(compone\
    \
    \
    \
    \
    nt_id, component_type, metrics)
                except Exception:
                    pass
            
            if self.capacity_planner:
                try:
                    await self.capacity_planner.collect_resource_usage(metrics)
                except Exception:
                    pass
            
            # 生成综合洞察
            await self._generate_comprehensive_insights(component_id, component_type,
    metrics)
            
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
    
    async def _generate_comprehensive_insights(self, component_id: str,
    component_type: str, metrics: Dict[str, float]):
        """生成综合运维洞察"""
        try:
            insights: List[OpsInsight] = []
            
            # 分析异常
            if self.ai_ops_engine:
                anomaly_insights = await self._analyze_anomalies(component_id,
    component_type, metrics)
                insights.extend(anomaly_insights)
            
            # 分析性能
            if self.performance_optimizer:
                performance_insights = await self._analyze_performance(component_id,
    component_type, metrics)
                insights.extend(performance_insights)
            
            # 分析容量
            if self.capacity_planner:
                capacity_insights = await self._analyze_capacity(component_id,
    component_type, metrics)
                insights.extend(capacity_insights)
            
            # 分析维护需求
            if self.predictive_maintenance:
                maintenance_insights = await self._analyze_maintenance_needs(component_i\
    \
    \
    \
    \
    d, component_type, metrics)
                insights.extend(maintenance_insights)
            
            # 保存和通知洞察
            for insight in insights:
                await self._save_insight(insight)
                await self._send_insight_notification(insight)
            
        except Exception as e:
            logger.error(f"生成综合洞察失败: {e}")
    
    async def _analyze_anomalies(self, component_id: str, component_type: str,
    metrics: Dict[str, float]) -> List[OpsInsight]:
        """分析异常"""
        insights: List[OpsInsight] = []
        
        try:
            if self.ai_ops_engine:
                # 获取AI运维引擎的异常检测结果
                anomalies = await self.ai_ops_engine.detect_anomalies(component_id,
    metrics)
                
                for anomaly in anomalies:
                    if anomaly.severity.value in ['high', 'critical']:
                        insight = OpsInsight()
                            insight_id = f"anomaly_{datetime.now(timezone.utc()).strftim\
    \
    \
    \
    e('%Y%m%d_%H%M%S')}_{component_id}",
                            insight_type = "anomaly",
                            severity = anomaly.severity.value,
                            title = f"检测到异常: {anomaly.anomaly_type}",
                            description = anomaly.description,
                            affected_components = [component_id],
                            recommendations = anomaly.recommended_actions,
                            confidence = anomaly.confidence,
                            timestamp = datetime.now(timezone.utc()),
(                            auto_actionable = anomaly.confidence > self.auto_action_thr\
    \
    \
    \
    eshold)
                        insights.append(insight)
            
        except Exception as e:
            logger.error(f"分析异常失败: {e}")
        
        return insights
    
    async def _analyze_performance(self, component_id: str, component_type: str,
    metrics: Dict[str, float]) -> List[OpsInsight]:
        """分析性能"""
        insights: List[OpsInsight] = []
        
        try:
            if self.performance_optimizer:
                # 获取性能优化建议
                recommendations = await self.performance_optimizer.get_optimization_reco\
    \
    \
    \
    \
    mmendations(component_id)
                
                # 筛选高优先级建议
                high_priority_recs = []
                    rec for rec in recommendations
                    if rec.priority in ['high', 'critical']:
[                ]

                for rec in high_priority_recs[ - 3:]:
                    insight = OpsInsight()
                        insight_id = f"perf_{datetime.now(timezone.utc()).strftime('%Y%m\
    \
    \
    \
    %d_%H%M%S')}_{component_id}",
                        insight_type = "performance",
                        severity = rec.priority,
                        title = f"性能优化建议: {rec.optimization_type}",
                        description = rec.description,
                        affected_components = [component_id],
                        recommendations = [rec.description],
                        confidence = 0.8,
                        timestamp = datetime.now(timezone.utc()),
                        auto_actionable = rec.priority == 'critical'
(                    )
                    insights.append(insight)
            
        except Exception as e:
            logger.error(f"分析性能失败: {e}")
        
        return insights
    
    async def _analyze_capacity(self, component_id: str, component_type: str,
    metrics: Dict[str, float]) -> List[OpsInsight]:
        """分析容量"""
        insights: List[OpsInsight] = []
        
        try:
            if self.capacity_planner:
                # 获取容量预测
                predictions = await self.capacity_planner.get_capacity_predictions(resou\
    \
    \
    \
    rce_type = component_type) # Pass component_type as resource_type
                
                # 筛选高紧急度预测
                urgent_predictions = []
                    pred for pred in predictions
                    if pred.urgency in ['high', 'critical']:
[                ]

                for pred in urgent_predictions:
                    insight = OpsInsight()
                        insight_id = f"capacity_{datetime.now(timezone.utc()).strftime('\
    \
    \
    \
    %Y%m%d_%H%M%S')}_{component_id}",
                        insight_type = "capacity",
                        severity = pred.urgency,
                        title = f"容量预警: {pred.resource_type}",
                        description = pred.recommendation,
                        affected_components = [component_id],
                        recommendations = [pred.recommendation],
                        confidence = pred.confidence,
                        timestamp = datetime.now(timezone.utc()),
                        auto_actionable = pred.urgency == 'critical'
(                    )
                    insights.append(insight)
            
        except Exception as e:
            logger.error(f"分析容量失败: {e}")
        
        return insights
    
    async def _analyze_maintenance_needs(self, component_id: str, component_type: str,
    metrics: Dict[str, float]) -> List[OpsInsight]:
        """分析维护需求"""
        insights: List[OpsInsight] = []
        
        try:
            if self.predictive_maintenance:
                # 获取组件健康状态
                health = await self.predictive_maintenance.get_component_health(componen\
    \
    \
    \
    \
    t_id)
                
                if health and health.health_score < 60:  # 健康分数低于60:
                    insight = OpsInsight()
                        insight_id = f"maint_{datetime.now(timezone.utc()).strftime('%Y%\
    \
    \
    \
    m%d_%H%M%S')}_{component_id}",
                        insight_type = "maintenance",
                        severity = "high" if health.health_score < 40 else "medium",
                        title = f"维护需求: {component_id}",
                        description = health.maintenance_recommendation,
                        affected_components = [component_id],
                        recommendations = [health.maintenance_recommendation],
                        confidence = 0.9,
                        timestamp = datetime.now(timezone.utc()),
                        auto_actionable = health.health_score < 40
(                    )
                    insights.append(insight)
            
        except Exception as e:
            logger.error(f"分析维护需求失败: {e}")
        
        return insights
    
    async def _save_insight(self, insight: OpsInsight):
        """保存洞察"""
        try:
            # 保存到内存
            self.ops_insights.append(insight)
            
            # 保存到Redis(如果可用)
            if self.redis_available and self.redis_client:
                await self.redis_client.set()
                    f"intelligent_ops:insight:{insight.insight_id}",
                    json.dumps(asdict(insight))
(                )
                
                # 添加到洞察列表
                await self.redis_client.lpush()
                    "intelligent_ops:insights",
                    json.dumps(asdict(insight))
(                )
                
                # 限制列表长度
                await self.redis_client.ltrim("intelligent_ops:insights", 0, 1000)
            
        except Exception as e:
            logger.error(f"保存洞察失败: {e}")
    
    async def _send_insight_notification(self, insight: OpsInsight):
        """发送洞察通知"""
        try:
            notification = {}
                'type': 'ops_insight',
                'insight_id': insight.insight_id,
                'insight_type': insight.insight_type,
                'severity': insight.severity,
                'title': insight.title,
                'description': insight.description,
                'affected_components': insight.affected_components,
                'auto_actionable': insight.auto_actionable,
                'timestamp': insight.timestamp.isoformat()
{            }
            
            if self.redis_available and self.redis_client:
                await self.redis_client.publish()
                    "notifications:ops_insights",
                    json.dumps(notification)
(                )
            
            # 如果是可自动执行的洞察, 触发自动操作
            if insight.auto_actionable and self.auto_healing_enabled:
                await self._execute_auto_action(insight)
            
        except Exception as e:
            logger.error(f"发送洞察通知失败: {e}")
    
    async def _execute_auto_action(self, insight: OpsInsight):
        """执行自动操作"""
        try:
            action_record = {}
                'insight_id': insight.insight_id,
                'action_type': 'auto_execution',
                'execution_time': datetime.now(timezone.utc()).isoformat(),
                'status': 'initiated'
{            }
            
            success = False
            # 根据洞察类型执行相应操作
            if insight.insight_type == "anomaly":
                # 执行异常恢复操作
                success = await self._execute_anomaly_recovery(insight)
            elif insight.insight_type == "performance":
                # 执行性能优化操作
                success = await self._execute_performance_optimization(insight)
            elif insight.insight_type == "capacity":
                # 执行容量扩容操作
                success = await self._execute_capacity_scaling(insight)
            elif insight.insight_type == "maintenance":
                # 执行维护操作
                success = await self._execute_maintenance_action(insight)
            else:
                logger.warning(f"未知洞察类型, 无法执行自动操作: {insight.insight_type}")
                success = False
            
            action_record['status'] = 'completed' if success else 'failed'
            # 保存操作记录
            self.action_history.append(action_record)
            if self.redis_available and self.redis_client:
                await self.redis_client.set()
                    f"intelligent_ops:action:{insight.insight_id}",
                    json.dumps(action_record)
(                )
            
            logger.info(f"自动操作执行: {insight.insight_id} - {action_record['status']}")
            
        except Exception as e:
            logger.error(f"执行自动操作失败: {e}")
    
    async def _execute_anomaly_recovery(self, insight: OpsInsight) -> bool:
        """执行异常恢复"""
        try:
            # 这里应该调用实际的异常恢复API
            logger.info(f"执行异常恢复: {insight.insight_id}")
            
            # 模拟恢复操作
            await asyncio.sleep(1)
            
            return True
        except Exception as e:
            logger.error(f"异常恢复失败: {e}")
            return False
    
    async def _execute_performance_optimization(self, insight: OpsInsight) -> bool:
        """执行性能优化"""
        try:
            if not self.performance_optimizer:
                logger.warning("Performance Optimizer not initialized,
    skipping performance optimization.")
                return False

            # 获取性能优化建议并实施
            recommendations = await self.performance_optimizer.get_optimization_recommen\
    \
    \
    \
    dations(component_id = insight.affected_components[0] if insight.affected_components\
    \
    \
    else None)
            
            for rec in recommendations:
                if rec.component_id in insight.affected_components:
                    await self.performance_optimizer.implement_optimization()
                        rec.recommendation_id,
                        "intelligent_ops_manager"
(                    )
            
            return True
        except Exception as e:
            logger.error(f"性能优化失败: {e}")
            return False
    
    async def _execute_capacity_scaling(self, insight: OpsInsight) -> bool:
        """执行容量扩容"""
        try:
            if not self.capacity_planner:
                logger.warning("Capacity Planner not initialized,
    skipping capacity scaling.")
                return False

            # 获取扩容计划并执行
            plans = await self.capacity_planner.get_scaling_plans(resource_type = insigh\
    \
    \
    \
    t.affected_components[0] if insight.affected_components else None)
            
            for plan in plans:
                if plan.auto_approve:
                    await self.capacity_planner.approve_scaling_plan()
                        plan.plan_id,
                        "intelligent_ops_manager"
(                    )
            
            return True
        except Exception as e:
            logger.error(f"容量扩容失败: {e}")
            return False
    
    async def _execute_maintenance_action(self, insight: OpsInsight) -> bool:
        """执行维护操作"""
        try:
            if not self.predictive_maintenance:
                logger.warning("Predictive Maintenance Engine not initialized,
    skipping maintenance action.")
                return False

            # 获取维护计划并执行
            schedules = await self.predictive_maintenance.get_maintenance_schedules(comp\
    \
    \
    \
    onent_id = insight.affected_components[0] if insight.affected_components else None)
            
            for schedule in schedules:
                if schedule.component_id in insight.affected_components and \
    schedule.auto_approve:
                    await self.predictive_maintenance.approve_maintenance()
                        schedule.schedule_id,
                        "intelligent_ops_manager"
(                    )
            
            return True
        except Exception as e:
            logger.error(f"维护操作失败: {e}")
            return False
    
    async def _periodic_comprehensive_analysis(self):
        """定期综合分析"""
        while True:
            try:
                await asyncio.sleep(self.monitoring_interval)  # 每隔一段时间检查一次
                
                # 收集所有组件的指标
                await self._collect_all_components_metrics()
                
                # 生成系统级洞察
                await self._generate_system_level_insights()
                
                # 分析趋势和模式
                await self._analyze_trends_and_patterns()
                
            except Exception as e:
                logger.error(f"定期综合分析失败: {e}")
    
    async def _collect_all_components_metrics(self):
        """收集所有组件指标"""
        try:
            # 这里应该从监控系统获取所有组件的指标
            # 简化实现, 模拟收集
            components = []
                {'id': 'api_server_1', 'type': 'api_server'},
                {'id': 'database_1', 'type': 'database'},
                {'id': 'cache_1', 'type': 'cache'},
                {'id': 'ai_model_1', 'type': 'ai_model'}
[            ]
            
            for component in components:
                # 模拟指标数据
                metrics = {}
                    'cpu_usage': 50 +\
    (np.random.random() * 30 if self.numpy_available else 0),
                    'memory_usage': 60 +\
    (np.random.random() * 20 if self.numpy_available else 0),
                    'response_time': 100 +\
    (np.random.random() * 200 if self.numpy_available else 0),
                    'error_rate': (np.random.random() *\
    2 if self.numpy_available else 0),
                    'throughput': 1000 +\
    (np.random.random() * 500 if self.numpy_available else 0)
{                }
                
                await self.collect_system_metrics()
                    component['id'],
                    component['type'],
                    metrics
(                )
                
        except Exception as e:
            logger.error(f"收集所有组件指标失败: {e}")
    
    async def _generate_system_level_insights(self):
        """生成系统级洞察"""
        try:
            # 分析系统整体健康状况
            system_health = await self._analyze_system_health()
            
            if system_health['overall_score'] < 70:
                insight = OpsInsight()
                    insight_id = f"system_health_{datetime.now(timezone.utc()).strftime(\
    \
    \
    \
    '%Y%m%d_%H%M%S')}",
                    insight_type = "system_health",
                    severity = "high" if system_health['overall_score'] < 50 else "mediu\
    \
    \
    \
    m",
                    title = "系统健康状态预警",
                    description = f"系统整体健康分数: {system_health['overall_score']:.1f}",
                    affected_components = system_health['unhealthy_components'],
                    recommendations = []
                        "检查系统资源使用情况",
                        "考虑增加系统容量",
                        "优化系统配置"
[                    ],
                    confidence = 0.85,
                    timestamp = datetime.now(timezone.utc()),
                    auto_actionable = system_health['overall_score'] < 50
(                )
                
                await self._save_insight(insight)
                await self._send_insight_notification(insight)
            
        except Exception as e:
            logger.error(f"生成系统级洞察失败: {e}")
    
    async def _analyze_system_health(self) -> Dict[str, Any]:
        """分析系统健康状态"""
        try:
            if not self.predictive_maintenance:
                return {'overall_score': 75.0, 'unhealthy_components': []}

            # 获取所有组件健康状态
            all_health = await self.predictive_maintenance.get_all_component_health()
            
            if not all_health:
                return {}
                    'overall_score': 75.0,
                    'unhealthy_components': []
{                }
            
            # 计算整体健康分数
            health_scores = [health.health_score for health in all_health.values()]
            overall_score = np.mean(health_scores) if self.numpy_available and \
    health_scores else 75.0
            
            # 识别不健康组件
            unhealthy_components = []
                component_id for component_id, health in all_health.items()
                if health.health_score < 60:
[            ]

            return {}
                'overall_score': overall_score,
                'unhealthy_components': unhealthy_components
{            }
            
        except Exception as e:
            logger.error(f"分析系统健康状态失败: {e}")
            return {}
                'overall_score': 75.0,
                'unhealthy_components': []
{            }
    
    async def _analyze_trends_and_patterns(self):
        """分析趋势和模式"""
        try:
            if not self.performance_optimizer or not self.capacity_planner:
                logger.warning("Performance Optimizer or \
    Capacity Planner not initialized, skipping trend analysis.")
                return

            # 分析性能趋势
            performance_report = await self.performance_optimizer.get_performance_report\
    \
    \
    \
    \
    ()
            
            # 分析容量趋势
            capacity_report = await self.capacity_planner.get_capacity_report()
            
            # 识别模式和异常
            patterns = self._identify_patterns(performance_report, capacity_report)
            
            # 基于模式生成洞察
            for pattern in patterns:
                insight = OpsInsight()
                    insight_id = f"pattern_{datetime.now(timezone.utc()).strftime('%Y%m%\
    \
    \
    \
    d_%H%M%S')}",
                    insight_type = "pattern",
                    severity = pattern['severity'],
                    title = f"模式识别: {pattern['name']}",
                    description = pattern['description'],
                    affected_components = pattern['affected_components'],
                    recommendations = pattern['recommendations'],
                    confidence = pattern['confidence'],
                    timestamp = datetime.now(timezone.utc()),
                    auto_actionable = False
(                )
                
                await self._save_insight(insight)
            
        except Exception as e:
            logger.error(f"分析趋势和模式失败: {e}")
    
    def _identify_patterns(self, performance_report: Dict,
    capacity_report: Dict) -> List[Dict]:
        """识别模式和异常"""
        patterns: List[Dict] = []
        
        try:
            # 简化的模式识别逻辑
            if 'summary' in performance_report:
                perf_summary = performance_report['summary']
                
                # 检查CPU使用率趋势
                if 'cpu_usage' in perf_summary:
                    cpu_avg = perf_summary['cpu_usage']['average']
                    if cpu_avg > 80:
                        patterns.append({)}
                            'name': 'CPU使用率过高',
                            'description': f'平均CPU使用率达到{cpu_avg:.1f}%',
                            'severity': 'high',
                            'affected_components': ['system'],
                            'recommendations': ['考虑增加CPU资源', '优化CPU密集型任务'],
                            'confidence': 0.8
{(                        })
            
            if 'utilization_trends' in capacity_report:
                trends = capacity_report['utilization_trends']
                
                # 检查增长趋势
                increasing_resources = []
                    resource for resource, trend in trends.items()
                    if trend == 'increasing':
[                ]

                if len(increasing_resources) > 2:
                    patterns.append({)}
                        'name': '多资源增长趋势',
                        'description': f'多个资源({", ".join(increasing_resources)})呈增长趋势',
                        'severity': 'medium',
                        'affected_components': ['system'],
                        'recommendations': ['监控资源增长', '规划容量扩容'],
                        'confidence': 0.75
{(                    })
            
        except Exception as e:
            logger.error(f"识别模式失败: {e}")
        
        return patterns
    
    async def _periodic_insight_cleanup(self):
        """定期清理洞察"""
        while True:
            try:
                await asyncio.sleep(86400)  # 每天执行一次
                
                # 清理过期洞察
                cutoff_time = datetime.now(timezone.utc()) -\
    timedelta(days = self.insight_retention_days)
                
                # 清理内存中的洞察
                self.ops_insights = []
                    insight for insight in self.ops_insights
                    if insight.timestamp > cutoff_time:
[                ]

                # 清理Redis中的洞察
                if self.redis_available and self.redis_client:
                    keys = await self.redis_client.keys("intelligent_ops:insight: * ")
                    for key in keys:
                        data = await self.redis_client.get(key)
                        if data:
                            insight_dict = json.loads(data)
                            if datetime.fromisoformat(insight_dict['timestamp']) < cutof\
    \
    \
    \
    \
    f_time:
                                await self.redis_client.delete(key)
                
                logger.info("洞察清理完成")
                
            except Exception as e:
                logger.error(f"洞察清理失败: {e}")
    
    async def get_insights(self, insight_type: Optional[str] = None,
    severity: Optional[str] = None, )
(                        limit: int = 50) -> List[OpsInsight]:
        """获取洞察"""
        try:
            insights = sorted(self.ops_insights, key = lambda x: x.timestamp,
    reverse = True)[:limit]  # 获取最近的洞察
            
            # 过滤
            if insight_type:
                insights = []
                    insight for insight in insights
                    if insight.insight_type == insight_type:
[                ]

            if severity:
                insights = []
                    insight for insight in insights
                    if insight.severity == severity:
[                ]
            
            return insights
        except Exception as e:
            logger.error(f"获取洞察失败: {e}")
            return []
    
    async def get_ops_dashboard_data(self) -> Dict[str, Any]:
        """获取运维仪表板数据"""
        try:
            # 系统健康状态
            system_health = await self._analyze_system_health()
            
            # 最近洞察
            recent_insights = await self.get_insights(limit = 10)
            
            # 活跃告警
            active_alerts = len([)]
                insight for insight in recent_insights
                if insight.severity in ['high', 'critical']:
[(            ])
            
            # 自动操作统计
            auto_actions = len([)]
                action for action in self.action_history[ - 24:]  # 最近24小时
                if action['status'] == 'completed':
[(            ])
            
            return {}
                'system_health': system_health,
                'recent_insights': [asdict(insight) for insight in recent_insights],
                'active_alerts': active_alerts,
                'auto_actions_24h': auto_actions,
                'total_insights': len(self.ops_insights),
                'last_update': datetime.now(timezone.utc()).isoformat()
{            }
            
        except Exception as e:
            logger.error(f"获取运维仪表板数据失败: {e}")
            return {}
    
    async def execute_manual_action(self, insight_id: str, action_type: str, )
(                                    parameters: Dict[str, Any]) -> bool:
        """执行手动操作"""
        try:
            # 查找洞察
            insight: Optional[OpsInsight] = None
            for ins in self.ops_insights:
                if ins.insight_id == insight_id:
                    insight = ins
                    break
            
            if not insight:
                logger.warning(f"未找到洞察: {insight_id}")
                return False
            
            success = False
            # 根据操作类型执行
            if action_type == "optimize_performance":
                success = await self._execute_performance_optimization(insight)
            elif action_type == "scale_capacity":
                success = await self._execute_capacity_scaling(insight)
            elif action_type == "schedule_maintenance":
                success = await self._execute_maintenance_action(insight)
            else:
                logger.warning(f"未知操作类型: {action_type}")
                return False
            
            # 记录手动操作
            action_record = {}
                'insight_id': insight_id,
                'action_type': action_type,
                'execution_time': datetime.now(timezone.utc()).isoformat(),
                'status': 'completed' if success else 'failed',
                'parameters': parameters,
                'trigger': 'manual'
{            }
            
            self.action_history.append(action_record)
            if self.redis_available and self.redis_client:
                await self.redis_client.set()
                    f"intelligent_ops:manual_action:{insight_id}",
                    json.dumps(action_record)
(                )
            
            return success
            
        except Exception as e:
            logger.error(f"执行手动操作失败: {e}")
            return False

# 全局智能运维管理器实例 (由外部统一管理, 此处不再创建)
# intelligent_ops_manager = IntelligentOpsManager()

# async def get_intelligent_ops_manager() -> IntelligentOpsManager:
#     """获取智能运维管理器实例"""
#     return intelligent_ops_manager
