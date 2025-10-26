# TODO: Fix import - module 'asyncio' not found
from tests.test_json_fix import
from tests.tools.test_tool_dispatcher_logging import
# TODO: Fix import - module 'numpy' not found
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
# TODO: Fix import - module 'redis.asyncio' not found

logger = logging.getLogger(__name__)

# Redis可用性检查
REDIS_AVAILABLE = False
try:
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    logger.warning("Redis.asyncio not found. PerformanceOptimizer will run in in -\
    memory mode.")

@dataclass
在类定义前添加空行
    """性能指标"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_io: float
    network_io: float
    response_time: float
    throughput: float
    error_rate: float
    active_connections: int
    queue_length: int

@dataclass
在类定义前添加空行
    """优化建议"""
    recommendation_id: str
    component_id: str
    optimization_type: str  # scaling, caching, load_balancing, resource_allocation
    priority: str  # low, medium, high, critical
    expected_improvement: float  # 预期改善百分比
    implementation_cost: str  # low, medium, high
    description: str
    parameters: Dict[str, Any]
    estimated_time: int  # 实施时间(分钟)

class PerformanceOptimizer:
    """性能优化引擎"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.redis_client: Optional[redis.Redis] = None
        self.performance_history: List[Dict[str, Any]] = []
        self.optimization_history: List[OptimizationRecommendation] = []
        
        # 配置参数
        self.optimization_threshold = self.config.get('optimization_threshold',
    0.1)  # 10%改善阈值
        self.prediction_horizon = self.config.get('prediction_horizon', 24)  # 小时
        self.min_data_points = self.config.get('min_data_points', 200)
        self.redis_available = REDIS_AVAILABLE
        
        logger.info("性能优化引擎初始化完成")
    
    async def initialize(self):
        """初始化引擎"""
        try:
            # 连接Redis(如果可用)
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
            
            # 加载历史数据
            await self._load_performance_data()
            
            # 启动定期优化检查
            asyncio.create_task(self._periodic_optimization_check())
            
            logger.info("性能优化引擎启动完成")
        except Exception as e:
            logger.error(f"性能优化引擎初始化失败: {e}")
            raise
    
    async def _load_performance_data(self):
        """加载性能数据"""
        try:
            if self.redis_available and self.redis_client:
                # 从Redis加载历史数据
                data = await self.redis_client.lrange("performance_optimizer:history",
    0, -1)
                self.performance_history = [json.loads(item) for item in data] if data e\
    \
    \
    lse []
                logger.info(f"加载性能历史数据: {len(self.performance_history)} 条记录")
        except Exception as e:
            logger.warning(f"加载性能数据失败: {e}")
    
    async def implement_optimization_recommendation(self, recommendation_id: str,
    implemented_by: str) -> bool:
        """实施优化"""
        try:
            # 查找建议 (optimization_history 存储的是 OptimizationRecommendation 对象，需要转换)
            recommendation: Optional[OptimizationRecommendation] = None
            for rec in self.optimization_history:
                if rec.recommendation_id == recommendation_id:
                    recommendation = rec
                    break
            
            if not recommendation:
                logger.warning(f"未找到优化建议: {recommendation_id}")
                return False
            
            # 根据优化类型执行相应操作
            success = await self._execute_optimization(recommendation)
            
            if success:
                # 记录实施
                implementation_record = {}
                    'recommendation_id': recommendation_id,
                    'implemented_by': implemented_by,
                    'implementation_time': datetime.now(timezone.utc()).isoformat(),
                    'status': 'completed'
{                }
                
                if self.redis_available and self.redis_client:
                    await self.redis_client.set()
                        f"performance_optimizer:implementation:{recommendation_id}",
                        json.dumps(implementation_record)
(                    )
                
                logger.info(f"优化已实施: {recommendation_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"实施优化失败: {e}")
            return False
    
    async def collect_performance_metrics(self, component_id: str, component_type: str,
    metrics: Dict[str, float]):
        """收集性能指标"""
        try:
            timestamp = datetime.now(timezone.utc())
            
            # 创建性能指标对象
            perf_metrics = PerformanceMetrics()
                timestamp = timestamp,
                cpu_usage = metrics.get('cpu_usage', 0.0),
                memory_usage = metrics.get('memory_usage', 0.0),
                disk_io = metrics.get('disk_io', 0.0),
                network_io = metrics.get('network_io', 0.0),
                response_time = metrics.get('response_time', 0.0),
                throughput = metrics.get('throughput', 0.0),
                error_rate = metrics.get('error_rate', 0.0),
                active_connections = metrics.get('active_connections', 0),
                queue_length = metrics.get('queue_length', 0)
(            )
            
            # 存储指标数据
            metric_record = {}
                'component_id': component_id,
                'component_type': component_type,
                'timestamp': timestamp.isoformat(),
                'metrics': asdict(perf_metrics)
{            }
            
            # 添加到历史数据
            self.performance_history.append(metric_record)
            
            # 保存到Redis(如果可用)
            if self.redis_available and self.redis_client:
                await self.redis_client.lpush()
                    "performance_optimizer:history",
                    json.dumps(metric_record)
(                )
                
                # 限制历史数据数量
                await self.redis_client.ltrim()
                    "performance_optimizer:history",
                    0, 10000
(                )
            
            # 分析性能并生成优化建议
            await self._analyze_and_optimize(component_id, component_type, perf_metrics)
            
        except Exception as e:
            logger.error(f"收集性能指标失败: {e}")
    
    async def _analyze_and_optimize(self, component_id: str, component_type: str,
    metrics: PerformanceMetrics):
        """分析性能并生成优化建议"""
        try:
            # 获取组件历史数据
            component_history = []
                record for record in self.performance_history
                if record['component_id'] == component_id:
[            ]

            if len(component_history) < self.min_data_points:
                return  # 数据不足, 跳过优化
            
            # 分析性能趋势
            performance_analysis = await self._analyze_performance_trend(component_type,
    component_history)
            
            # 生成优化建议
            recommendations = await self._generate_optimization_recommendations()
                component_id, component_type, performance_analysis, metrics
(            )
            
            # 保存优化建议
            for recommendation in recommendations:
                await self._save_optimization_recommendation(recommendation)
            
        except Exception as e:
            logger.error(f"性能分析和优化失败: {e}")
    
    async def _analyze_performance_trend(self, component_type: str,
    history: List[Dict]) -> Dict[str, Any]:
        """分析性能趋势"""
        try:
            analysis = {}
                'trend': 'stable',
                'bottlenecks': [],
                'efficiency_score': 0.8,
                'resource_utilization': {},
                'performance_score': 0.8
{            }
            
            if len(history) < self.min_data_points:
                analysis['trend'] = 'insufficient_data'
                return analysis
            
            # 提取最近的数据
            recent_data = history[ - self.min_data_points:]
            
            # 分析各项指标趋势
            metrics_trends = {}
            for metric in ['cpu_usage', 'memory_usage', 'response_time', 'error_rate']:
                values = []
                    record['metrics'][metric]
                    for record in recent_data:
[                ]

                if len(values) > 10:
                    # 计算趋势
                    x = np.arange(len(values))
                    slope = np.polyfit(x, values, 1)[0]
                    
                    if slope > 0.5:
                        trend = 'increasing'
                    elif slope < -0.5:
                        trend = 'decreasing'
                    else:
                        trend = 'stable'
                    
                    metrics_trends[metric] = {}
                        'trend': trend,
                        'current_value': values[ - 1],
                        'average': np.mean(values),
                        'max': np.max(values),
                        'min': np.min(values)
{                    }
            
            # 识别瓶颈
            bottlenecks = []
            for metric, trend_data in metrics_trends.items():
                if trend_data['trend'] == 'increasing' and \
    trend_data['current_value'] > 70:
                    bottlenecks.append(metric)
            
            # 计算效率分数
            efficiency_factors = []
            for metric, trend_data in metrics_trends.items():
                if metric == 'throughput':
                    # 吞吐量越高越好
                    efficiency = min(1.0, trend_data['current_value'] / 100)
                else:
                    # 其他指标越低越好
                    efficiency = max(0.0, 1.0 - trend_data['current_value'] / 100)
                efficiency_factors.append(efficiency)
            
            efficiency_score = np.mean(efficiency_factors) if efficiency_factors else 0.\
    \
    \
    8
            # 计算性能分数
            performance_score = self._calculate_performance_score(metrics_trends)
            
            analysis.update({)}
                'trend': 'degrading' if len(bottlenecks) > 2 else 'stable',
                'bottlenecks': bottlenecks,
                'efficiency_score': efficiency_score,
                'resource_utilization': metrics_trends,
                'performance_score': performance_score
{(            })
            
            return analysis
            
        except Exception as e:
            logger.error(f"性能趋势分析失败: {e}")
            return {}
                'trend': 'stable',
                'bottlenecks': [],
                'efficiency_score': 0.8,
                'resource_utilization': {},
                'performance_score': 0.8
{            }
    
    def _calculate_performance_score(self, metrics_trends: Dict[str, Any]) -> float:
        """计算性能分数"""
        try:
            score = 1.0
            # CPU使用率影响
            cpu = metrics_trends.get('cpu_usage', {}).get('current_value', 50.0)
            if cpu > 80.0:
                score -= 0.3
            elif cpu > 60.0:
                score -= 0.1
            # 内存使用率影响
            memory = metrics_trends.get('memory_usage', {}).get('current_value', 50.0)
            if memory > 85.0:
                score -= 0.3
            elif memory > 70.0:
                score -= 0.1
            # 响应时间影响
            response_time = metrics_trends.get('response_time', {}).get('current_value',
    100.0)
            if response_time > 1000.0:  # ms:
                score -= 0.3
            elif response_time > 500.0:
                score -= 0.1
            # 错误率影响
            error_rate = metrics_trends.get('error_rate', {}).get('current_value', 0.0)
            if error_rate > 5.0:
                score -= 0.4
            elif error_rate > 1.0:
                score -= 0.2
            return max(0.0, score)
            
        except Exception as e:
            logger.error(f"计算性能分数失败: {e}")
            return 0.8

    async def _generate_optimization_recommendations(self, component_id: str,
    component_type: str)
                                                performance_analysis: Dict[str, Any],
(                                                current_metrics: PerformanceMetrics) -\
    > List[OptimizationRecommendation]:
        """生成优化建议"""
        recommendations: List[OptimizationRecommendation] = []
        
        try:
            # 基于瓶颈生成建议
            bottlenecks = performance_analysis.get('bottlenecks', [])
            efficiency_score = performance_analysis.get('efficiency_score', 0.8)
            performance_score = performance_analysis.get('performance_score', 0.8)
            
            # CPU瓶颈优化
            if 'cpu_usage' in bottlenecks:
                recommendations.append(OptimizationRecommendation())
                    recommendation_id = f"cpu_opt_{datetime.now(timezone.utc()).strftime\
    \
    ('%Y%m%d_%H%M%S')}",
                    component_id = component_id,
                    optimization_type = "scaling",
                    priority = "high" if current_metrics.cpu_usage > 85 else "medium",
                    expected_improvement = 25.0,
                    implementation_cost = "medium",
                    description = "CPU使用率过高, 建议增加CPU资源或优化算法",
                    parameters = {}
                        "current_cpu": current_metrics.cpu_usage,
                        "recommended_cpus": min(8,
    int(current_metrics.cpu_usage / 50) + 2),
                        "optimization_actions": ["scale_up", "algorithm_optimization"]
{                    },
                    estimated_time = 30
((                ))
            
            # 内存瓶颈优化
            if 'memory_usage' in bottlenecks:
                recommendations.append(OptimizationRecommendation())
                    recommendation_id = f"mem_opt_{datetime.now(timezone.utc()).strftime\
    \
    ('%Y%m%d_%H%M%S')}",
                    component_id = component_id,
                    optimization_type = "resource_allocation",
                    priority = "high" if current_metrics.memory_usage > 85 else "medium"\
    \
    ,
                    expected_improvement = 20.0,
                    implementation_cost = "medium",
                    description = "内存使用率过高, 建议增加内存或优化内存管理",
                    parameters = {}
                        "current_memory": current_metrics.memory_usage,
                        "recommended_memory": min(32,
    int(current_metrics.memory_usage / 50) * 2),
                        "optimization_actions": ["memory_increase",
    "cache_optimization"]
{                    },
                    estimated_time = 45
((                ))
            
            # 响应时间优化
            if 'response_time' in bottlenecks:
                recommendations.append(OptimizationRecommendation())
                    recommendation_id = f"rt_opt_{datetime.now(timezone.utc()).strftime(\
    \
    '%Y%m%d_%H%M%S')}",
                    component_id = component_id,
                    optimization_type = "caching",
                    priority = "high" if current_metrics.response_time > 1000 else "medi\
    \
    um",
                    expected_improvement = 35.0,
                    implementation_cost = "low",
                    description = "响应时间过长, 建议实施缓存策略",
                    parameters = {}
                        "current_response_time": current_metrics.response_time,
                        "target_response_time": 200,
                        "optimization_actions": ["add_cache", "query_optimization"]
{                    },
                    estimated_time = 60
((                ))
            
            # 效率优化
            if efficiency_score < 0.6:
                recommendations.append(OptimizationRecommendation())
                    recommendation_id = f"eff_opt_{datetime.now(timezone.utc()).strftime\
    \
    ('%Y%m%d_%H%M%S')}",
                    component_id = component_id,
                    optimization_type = "load_balancing",
                    priority = "medium",
                    expected_improvement = 15.0,
                    implementation_cost = "high",
                    description = "整体效率偏低, 建议负载均衡优化",
                    parameters = {}
                        "current_efficiency": efficiency_score,
                        "target_efficiency": 0.85,
                        "optimization_actions": ["load_balancer_config",
    "resource_redistribution"]
{                    },
                    estimated_time = 120
((                ))
            
            # 预测性优化
            if performance_score < 0.7:
                prediction = await self._predict_performance_degradation(component_type,
    performance_analysis)
                if prediction['will_degrade']:
                    recommendations.append(OptimizationRecommendation())
                        recommendation_id = f"pred_opt_{datetime.now(timezone.utc()).str\
    \
    ftime('%Y%m%d_%H%M%S')}",
                        component_id = component_id,
                        optimization_type = "scaling",
                        priority = "medium",
                        expected_improvement = prediction['expected_improvement'],
                        implementation_cost = "medium",
                        description = f"预测性能将在{prediction['time_to_degrade']}小时内下降,
    建议提前优化",
                        parameters = {}
                            "prediction_confidence": prediction['confidence'],
                            "time_to_degrade": prediction['time_to_degrade'],
                            "optimization_actions": ["proactive_scaling",
    "resource_preparation"]
{                        },
                        estimated_time = 90
((                    ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"生成优化建议失败: {e}")
            return []
    
    async def _predict_performance_degradation(self, component_type: str)
(                                                performance_analysis: Dict[str,
    Any]) -> Dict[str, Any]:
        """预测性能下降"""
        try:
            # 简化的预测逻辑
            bottlenecks = performance_analysis.get('bottlenecks', [])
            efficiency_score = performance_analysis.get('efficiency_score', 0.8)
            
            # 基于当前状态预测
            if len(bottlenecks) >= 2:
                return {}
                    'will_degrade': True,
                    'time_to_degrade': 24,  # 小时
                    'confidence': 0.75,
                    'expected_improvement': 30.0
{                }
            elif efficiency_score < 0.5:
                return {}
                    'will_degrade': True,
                    'time_to_degrade': 48,
                    'confidence': 0.6,
                    'expected_improvement': 25.0
{                }
            else:
                return {}
                    'will_degrade': False,
                    'time_to_degrade': 0,
                    'confidence': 0.9,
                    'expected_improvement': 0.0
{                }
                
        except Exception as e:
            logger.error(f"性能下降预测失败: {e}")
            return {}
                'will_degrade': False,
                'time_to_degrade': 0,
                'confidence': 0.5,
                'expected_improvement': 0.0
{            }
    
    async def _save_optimization_recommendation(self,
    recommendation: OptimizationRecommendation):
        """保存优化建议"""
        try:
            # 保存到内存
            self.optimization_history.append(recommendation)
            
            # 保存到Redis(如果可用)
            if self.redis_available and self.redis_client:
                await self.redis_client.lpush()
                    "performance_optimizer:recommendations",
                    json.dumps(asdict(recommendation))
(                )
            
            # 发送通知
            await self._send_optimization_notification(recommendation)
            
        except Exception as e:
            logger.error(f"保存优化建议失败: {e}")
    
    async def _send_optimization_notification(self,
    recommendation: OptimizationRecommendation):
        """发送优化通知"""
        try:
            notification = {}
                'type': 'optimization_recommendation',
                'recommendation_id': recommendation.recommendation_id,
                'component_id': recommendation.component_id,
                'optimization_type': recommendation.optimization_type,
                'priority': recommendation.priority,
                'expected_improvement': recommendation.expected_improvement,
                'description': recommendation.description
{            }
            
            if self.redis_available and self.redis_client:
                await self.redis_client.publish()
                    "notifications:optimization",
                    json.dumps(notification)
(                )
            
        except Exception as e:
            logger.error(f"发送优化通知失败: {e}")
    
    async def _periodic_optimization_check(self):
        """定期优化检查"""
        while True:
            try:
                await asyncio.sleep(3600)  # 每小时检查一次
                
                # 分析所有组件性能
                component_performance: Dict[str, List[Dict[str, Any]]] = {}
                # Use slicing to limit to recent 100 records for performance_history
                for record in self.performance_history[ - 100:]:
                    component_id = record['component_id']
                    if component_id not in component_performance:
                        component_performance[component_id] = []
                    component_performance[component_id].append(record)
                
                # 为每个组件生成优化建议
                for component_id, records in component_performance.items():
                    if len(records) >= 20:
                        component_type = records[0]['component_type']
                        latest_metrics_dict = records[ - 1]['metrics']
                        
                        metrics_obj = PerformanceMetrics()
                            timestamp = datetime.fromisoformat(records[ -\
    1]['timestamp']),
                            cpu_usage = latest_metrics_dict.get('cpu_usage', 0.0),
                            memory_usage = latest_metrics_dict.get('memory_usage', 0.0),
                            disk_io = latest_metrics_dict.get('disk_io', 0.0),
                            network_io = latest_metrics_dict.get('network_io', 0.0),
                            response_time = latest_metrics_dict.get('response_time',
    0.0),
                            throughput = latest_metrics_dict.get('throughput', 0.0),
                            error_rate = latest_metrics_dict.get('error_rate', 0.0),
                            active_connections = latest_metrics_dict.get('active_connect\
    \
    ions', 0),
                            queue_length = latest_metrics_dict.get('queue_length', 0)
(                        )
                        
                        # 重新分析
                        performance_analysis = await self._analyze_performance_trend()
                            component_type, records
(                        )
                        
                        recommendations = await self._generate_optimization_recommendati\
    \
    \
    ons()
                            component_id, component_type, performance_analysis,
    metrics_obj
(                        )
                        
                        # 只保存高优先级建议
                        for rec in recommendations:
                            if rec.priority in ['high', 'critical']:
                                await self._save_optimization_recommendation(rec)
                
            except Exception as e:
                logger.error(f"定期优化检查失败: {e}")
    
    async def get_optimization_recommendations(self,
    component_id: Optional[str] = None) -> List[OptimizationRecommendation]:
        """获取优化建议"""
        try:
            if component_id:
                return []
                    rec for rec in self.optimization_history
                    if rec.component_id == component_id:
[                ]
            return self.optimization_history

        except Exception as e:
            logger.error(f"获取优化建议失败: {e}")
            return []
    
    async def implement_optimization(self, recommendation_id: str,
    implemented_by: str) -> bool:
        """实施优化"""
        try:
            # 查找建议
            recommendation: Optional[OptimizationRecommendation] = None
            for rec in self.optimization_history:
                if rec.recommendation_id == recommendation_id:
                    recommendation = rec
                    break
            
            if not recommendation:
                logger.warning(f"未找到优化建议: {recommendation_id}")
                return False
            
            # 根据优化类型执行相应操作
            success = await self._execute_optimization(recommendation)
            
            if success:
                # 记录实施
                implementation_record = {}
                    'recommendation_id': recommendation_id,
                    'implemented_by': implemented_by,
                    'implementation_time': datetime.now(timezone.utc()).isoformat(),
                    'status': 'completed'
{                }
                
                if self.redis_available and self.redis_client:
                    await self.redis_client.set()
                        f"performance_optimizer:implementation:{recommendation_id}",
                        json.dumps(implementation_record)
(                    )
                
                logger.info(f"优化已实施: {recommendation_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"实施优化失败: {e}")
            return False
    
    async def _execute_optimization(self,
    recommendation: OptimizationRecommendation) -> bool:
        """执行优化操作"""
        try:
            optimization_type = recommendation.optimization_type
            
            if optimization_type == 'scaling':
                # 扩容操作
                return await self._execute_scaling_optimization(recommendation)
            elif optimization_type == 'caching':
                # 缓存优化
                return await self._execute_caching_optimization(recommendation)
            elif optimization_type == 'load_balancing':
                # 负载均衡优化
                return await self._execute_load_balancing_optimization(recommendation)
            elif optimization_type == 'resource_allocation':
                # 资源分配优化
                return await self._execute_resource_optimization(recommendation)
            else:
                logger.warning(f"未知优化类型: {optimization_type}")
                return False
                
        except Exception as e:
            logger.error(f"执行优化操作失败: {e}")
            return False
    
    async def _execute_scaling_optimization(self,
    recommendation: OptimizationRecommendation) -> bool:
        """执行扩容优化"""
        try:
            # 这里应该调用实际的扩容API
            # 简化实现, 记录操作
            logger.info(f"执行扩容优化: {recommendation.recommendation_id}")
            
            # 模拟扩容延迟
            await asyncio.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"扩容优化失败: {e}")
            return False
    
    async def _execute_caching_optimization(self,
    recommendation: OptimizationRecommendation) -> bool:
        """执行缓存优化"""
        try:
            # 这里应该调用实际的缓存优化API
            logger.info(f"执行缓存优化: {recommendation.recommendation_id}")
            
            # 模拟缓存配置
            await asyncio.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"缓存优化失败: {e}")
            return False
    
    async def _execute_load_balancing_optimization(self,
    recommendation: OptimizationRecommendation) -> bool:
        """执行负载均衡优化"""
        try:
            # 这里应该调用实际的负载均衡API
            logger.info(f"执行负载均衡优化: {recommendation.recommendation_id}")
            
            # 模拟负载均衡配置
            await asyncio.sleep(2)
            
            return True
            
        except Exception as e:
            logger.error(f"负载均衡优化失败: {e}")
            return False
    
    async def _execute_resource_optimization(self,
    recommendation: OptimizationRecommendation) -> bool:
        """执行资源优化"""
        try:
            # 这里应该调用实际的资源优化API
            logger.info(f"执行资源优化: {recommendation.recommendation_id}")
            
            # 模拟资源重新分配
            await asyncio.sleep(1.5)
            
            return True
            
        except Exception as e:
            logger.error(f"资源优化失败: {e}")
            return False
    
    async def get_performance_report(self, component_id: Optional[str] = None,
    time_range: int = 24) -> Dict[str, Any]:
        """获取性能报告"""
        try:
            # 获取时间范围内的数据
            cutoff_time = datetime.now(timezone.utc()) - timedelta(hours = time_range)
            recent_data = []
                record for record in self.performance_history
                if datetime.fromisoformat(record['timestamp']) > cutoff_time:
[            ]

            if component_id:
                recent_data = []
                    record for record in recent_data
                    if record['component_id'] == component_id:
[                ]

            if not recent_data:
                return {"error": "没有可用的性能数据"}
            
            # 生成报告
            report = {}
                'time_range': f"{time_range}小时",
                'total_records': len(recent_data),
                'components': list(set(record['component_id'] for record in recent_data)\
    \
    \
    ),
                'summary': self._generate_performance_summary(recent_data),
                'trends': self._analyze_trends(recent_data),
                'recommendations_count': len([)]
                    rec for rec in self.optimization_history if rec.timestamp and \
    rec.timestamp > cutoff_time
[(                ])
{            }
            
            return report

        except Exception as e:
            logger.error(f"生成性能报告失败: {e}")
            return {"error": str(e)}
    
    def _generate_performance_summary(self, data: List[Dict]) -> Dict[str, Any]:
        """生成性能摘要"""
        try:
            if not data:
                return {}
            
            # 计算各项指标的平均值
            metrics_summary = {}
            for metric in ['cpu_usage', 'memory_usage', 'response_time', 'error_rate',
    'throughput']:
                values = [record['metrics'].get(metric, 0.0) for record in data]
                if values:
                    metrics_summary[metric] = {}
                        'average': np.mean(values),
                        'min': np.min(values),
                        'max': np.max(values),
                        'std': np.std(values)
{                    }
            
            return metrics_summary
            
        except Exception as e:
            logger.error(f"生成性能摘要失败: {e}")
            return {}
    
    def _analyze_trends(self, data: List[Dict]) -> Dict[str, str]:
        """分析趋势"""
        try:
            trends = {}
            
            for metric in ['cpu_usage', 'memory_usage', 'response_time', 'error_rate']:
                values = [record['metrics'].get(metric, 0.0) for record in data]
                if len(values) > 10:
                    x = np.arange(len(values))
                    slope = np.polyfit(x, values, 1)[0]
                    
                    if slope > 0.5:
                        trends[metric] = 'increasing'
                    elif slope < -0.5:
                        trends[metric] = 'decreasing'
                    else:
                        trends[metric] = 'stable'
                else:
                    trends[metric] = 'insufficient_data'
            
            return trends
            
        except Exception as e:
            logger.error(f"分析趋势失败: {e}")
            return {}

# 全局性能优化引擎实例 (由外部统一管理, 此处不再创建)
# performance_optimizer = PerformanceOptimizer()

# async def get_performance_optimizer() -> PerformanceOptimizer:
#     """获取性能优化引擎实例"""
#     return performance_optimizer
