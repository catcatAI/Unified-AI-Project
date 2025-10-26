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
    logger.warning("Redis.asyncio not found. CapacityPlanner will run in in -\
    memory mode.")

# Scikit - learn可用性检查
SKLEARN_AVAILABLE = False
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_squared_error
    SKLEARN_AVAILABLE = True
except ImportError:
    logger.warning("Scikit -\
    learn not found. CapacityPlanner will use simpler prediction models.")

@dataclass
在类定义前添加空行
    """资源使用情况"""
    timestamp: datetime
    cpu_cores: float
    memory_gb: float
    disk_gb: float
    network_mbps: float
    gpu_count: float
    active_instances: int
    concurrent_users: int
    request_rate: float

@dataclass
在类定义前添加空行
    """容量预测"""
    prediction_id: str
    resource_type: str
    current_capacity: float
    predicted_need: float
    time_horizon: int  # 小时
    confidence: float
    recommendation: str
    urgency: str  # low, medium, high, critical

@dataclass
在类定义前添加空行
    """扩容计划"""
    plan_id: str
    resource_type: str
    action: str  # scale_up, scale_down, maintain
    target_capacity: float
    current_capacity: float
    execution_time: datetime
    estimated_cost: float
    rollback_plan: str
    auto_approve: bool

class CapacityPlanner:
    """智能容量规划引擎"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.redis_client: Optional[redis.Redis] = None
        self.usage_history: List[Dict[str, Any]] = []
        self.capacity_plans: Dict[str, ScalingPlan] = {}
        
        # 配置参数
        self.prediction_window = self.config.get('prediction_window', 24)  # 小时
        self.scaling_threshold = self.config.get('scaling_threshold', 0.8)  # 80%阈值
        self.min_data_points = self.config.get('min_data_points', 168)  # 一周数据
        self.cost_per_cpu = self.config.get('cost_per_cpu', 0.05)  # 每小时每CPU成本
        self.cost_per_gb = self.config.get('cost_per_gb', 0.01)  # 每小时每GB内存成本
        self.redis_available = REDIS_AVAILABLE
        self.sklearn_available = SKLEARN_AVAILABLE
        
        logger.info("容量规划引擎初始化完成")
    
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
            
            # 加载或初始化预测模型 (此处省略, 因为模型是动态生成的)
            
            # 加载历史数据
            await self._load_usage_data()
            
            # 启动定期容量检查
            asyncio.create_task(self._periodic_capacity_check())
            
            logger.info("容量规划引擎启动完成")
        except Exception as e:
            logger.error(f"容量规划引擎初始化失败: {e}")
            raise
    
    async def _load_usage_data(self):
        """加载使用数据"""
        try:
            if self.redis_available and self.redis_client:
                # 从Redis加载历史数据
                data = await self.redis_client.lrange("capacity_planner:usage_history",
    0, -1)
                self.usage_history = [json.loads(item) for item in data] if data else []
                logger.info(f"加载资源使用历史数据: {len(self.usage_history)} 条记录")
        except Exception as e:
            logger.warning(f"加载使用数据失败: {e}")
    
    async def collect_resource_usage(self, resource_data: Dict[str, float]):
        """收集资源使用数据"""
        try:
            timestamp = datetime.now(timezone.utc())
            
            # 创建资源使用对象
            usage = ResourceUsage()
                timestamp = timestamp,
                cpu_cores = resource_data.get('cpu_cores', 0.0),
                memory_gb = resource_data.get('memory_gb', 0.0),
                disk_gb = resource_data.get('disk_gb', 0.0),
                network_mbps = resource_data.get('network_mbps', 0.0),
                gpu_count = resource_data.get('gpu_count', 0.0),
                active_instances = resource_data.get('active_instances', 0),
                concurrent_users = resource_data.get('concurrent_users', 0),
                request_rate = resource_data.get('request_rate', 0.0)
(            )
            
            # 存储使用数据
            usage_record = {}
                'timestamp': timestamp.isoformat(),
                'usage': asdict(usage)
{            }
            
            # 添加到历史数据
            self.usage_history.append(usage_record)
            
            # 保存到Redis(如果可用)
            if self.redis_available and self.redis_client:
                await self.redis_client.lpush()
                    "capacity_planner:usage_history",
                    json.dumps(usage_record)
(                )
                
                # 限制历史数据数量
                await self.redis_client.ltrim()
                    "capacity_planner:usage_history",
                    0, 20000
(                )
            
            # 分析容量需求
            await self._analyze_capacity_needs(usage)
            
        except Exception as e:
            logger.error(f"收集资源使用数据失败: {e}")
    
    async def _analyze_capacity_needs(self, current_usage: ResourceUsage):
        """分析容量需求"""
        try:
            if len(self.usage_history) < self.min_data_points:
                return  # 数据不足
            
            # 预测各项资源需求
            resource_predictions = await self._predict_resource_needs(current_usage)
            
            # 生成扩容计划
            for prediction in resource_predictions:
                if prediction.urgency in ['high', 'critical']:
                    await self._create_scaling_plan(prediction)
            
        except Exception as e:
            logger.error(f"分析容量需求失败: {e}")
    
    async def _predict_resource_needs(self,
    current_usage: ResourceUsage) -> List[CapacityPrediction]:
        """预测资源需求"""
        predictions: List[CapacityPrediction] = []
        
        try:
            # CPU预测
            cpu_prediction = await self._predict_cpu_needs(current_usage)
            if cpu_prediction:
                predictions.append(cpu_prediction)
            
            # 内存预测
            memory_prediction = await self._predict_memory_needs(current_usage)
            if memory_prediction:
                predictions.append(memory_prediction)
            
            # 磁盘预测
            disk_prediction = await self._predict_disk_needs(current_usage)
            if disk_prediction:
                predictions.append(disk_prediction)
            
            # 网络预测
            network_prediction = await self._predict_network_needs(current_usage)
            if network_prediction:
                predictions.append(network_prediction)
            
            # GPU预测
            gpu_prediction = await self._predict_gpu_needs(current_usage)
            if gpu_prediction:
                predictions.append(gpu_prediction)
            
            return predictions
            
        except Exception as e:
            logger.error(f"预测资源需求失败: {e}")
            return []
    
    async def _predict_cpu_needs(self,
    current_usage: ResourceUsage) -> Optional[CapacityPrediction]:
        """预测CPU需求"""
        try:
            # 获取CPU使用历史
            cpu_history = []
                record['usage']['cpu_cores']
                for record in self.usage_history[ - self.min_data_points:]:
[            ]
            
            if len(cpu_history) < self.prediction_window:
                return None
            
            # 计算趋势
            if self.sklearn_available and len(cpu_history) > 1:
                x = np.arange(len(cpu_history)).reshape( - 1, 1)
                model = LinearRegression()
                model.fit(x, cpu_history)
                
                # 预测未来需求
                future_x = np.arange(len(cpu_history),
    len(cpu_history) + self.prediction_window).reshape( - 1, 1)
                predicted_cpu_values = model.predict(future_x)
                predicted_cpu = predicted_cpu_values[ - 1]
                
                # 计算置信度 (基于MSE)
                predicted_values_past = model.predict(x)
                mse = mean_squared_error(cpu_history, predicted_values_past)
                confidence = max(0.5, min(0.95,
    1.0 - mse / (np.var(cpu_history) + 1e - 6))) # 避免除以0
            else:
                # 简单预测
                predicted_cpu = np.mean(cpu_history) if cpu_history else 0.0
                confidence = 0.6

            # 确定紧急程度
            utilization_rate = current_usage.cpu_cores / max(1.0, predicted_cpu)
            if utilization_rate > 0.9:
                urgency = 'critical'
            elif utilization_rate > 0.8:
                urgency = 'high'
            elif utilization_rate > 0.6:
                urgency = 'medium'
            else:
                urgency = 'low'
            
            # 生成建议
            recommendation: str
            if utilization_rate > self.scaling_threshold:
                recommendation = f"建议增加CPU资源至 {int(predicted_cpu * 1.2)} 核"
            elif utilization_rate < 0.3:
                recommendation = f"可考虑减少CPU资源至 {int(predicted_cpu)} 核"
            else:
                recommendation = "CPU资源充足"
            
            return CapacityPrediction()
                prediction_id = f"cpu_pred_{datetime.now(timezone.utc()).strftime('%Y%m%\
    \
    \
    d_%H%M%S')}",
                resource_type = "cpu",
                current_capacity = current_usage.cpu_cores,
                predicted_need = predicted_cpu,
                time_horizon = self.prediction_window,
                confidence = confidence,
                recommendation = recommendation,
                urgency = urgency
(            )
            
        except Exception as e:
            logger.error(f"CPU需求预测失败: {e}")
            return None
    
    async def _predict_memory_needs(self,
    current_usage: ResourceUsage) -> Optional[CapacityPrediction]:
        """预测内存需求"""
        try:
            # 获取内存使用历史
            memory_history = []
                record['usage']['memory_gb']
                for record in self.usage_history[ - self.min_data_points:]:
[            ]
            
            if len(memory_history) < self.prediction_window:
                return None
            
            # 计算趋势和季节性
            if self.sklearn_available and len(memory_history) > 1:
                x = np.arange(len(memory_history)).reshape( - 1, 1)
                model = LinearRegression()
                model.fit(x, memory_history)
                
                # 预测未来需求
                future_x = np.arange(len(memory_history),
    len(memory_history) + self.prediction_window).reshape( - 1, 1)
                predicted_memory_values = model.predict(future_x)
                predicted_memory = predicted_memory_values[ - 1]
                
                # 计算置信度 (基于MSE)
                predicted_values_past = model.predict(x)
                mse = mean_squared_error(memory_history, predicted_values_past)
                confidence = max(0.5, min(0.95,
    1.0 - mse / (np.var(memory_history) + 1e - 6)))
            else:
                # 简单预测
                predicted_memory = np.mean(memory_history) if memory_history else 0.0
                confidence = 0.6

            # 考虑用户增长趋势
            user_growth_rate = self._calculate_user_growth_rate()
            predicted_memory *= (1 + user_growth_rate * self.prediction_window / 24)
            
            # 确定紧急程度
            utilization_rate = current_usage.memory_gb / max(1.0, predicted_memory)
            if utilization_rate > 0.9:
                urgency = 'critical'
            elif utilization_rate > 0.8:
                urgency = 'high'
            elif utilization_rate > 0.6:
                urgency = 'medium'
            else:
                urgency = 'low'
            
            # 生成建议
            if utilization_rate > self.scaling_threshold:
                recommendation = f"建议增加内存至 {int(predicted_memory * 1.2)} GB"
            elif utilization_rate < 0.3:
                recommendation = f"可考虑减少内存至 {int(predicted_memory)} GB"
            else:
                recommendation = "内存资源充足"
            
            return CapacityPrediction()
                prediction_id = f"mem_pred_{datetime.now(timezone.utc()).strftime('%Y%m%\
    \
    \
    d_%H%M%S')}",
                resource_type = "memory",
                current_capacity = current_usage.memory_gb,
                predicted_need = predicted_memory,
                time_horizon = self.prediction_window,
                confidence = confidence,
                recommendation = recommendation,
                urgency = urgency
(            )
            
        except Exception as e:
            logger.error(f"内存需求预测失败: {e}")
            return None
    
    async def _predict_disk_needs(self,
    current_usage: ResourceUsage) -> Optional[CapacityPrediction]:
        """预测磁盘需求"""
        try:
            # 获取磁盘使用历史
            disk_history = []
                record['usage']['disk_gb']
                for record in self.usage_history[ - self.min_data_points:]:
[            ]
            
            if len(disk_history) < self.prediction_window:
                return None
            
            # 磁盘通常是线性增长
            if self.sklearn_available and len(disk_history) > 1:
                x = np.arange(len(disk_history)).reshape( - 1, 1)
                model = LinearRegression()
                model.fit(x, disk_history)
                
                # 预测未来需求
                future_x = np.arange(len(disk_history),
    len(disk_history) + self.prediction_window).reshape( - 1, 1)
                predicted_disk_values = model.predict(future_x)
                predicted_disk = predicted_disk_values[ - 1]
            else:
                predicted_disk = np.mean(disk_history) if disk_history else 0.0

            # 磁盘预测通常更稳定
            confidence = 0.85
            # 确定紧急程度
            utilization_rate = current_usage.disk_gb / max(1.0, predicted_disk)
            if utilization_rate > 0.95:
                urgency = 'critical'
            elif utilization_rate > 0.85:
                urgency = 'high'
            elif utilization_rate > 0.7:
                urgency = 'medium'
            else:
                urgency = 'low'
            
            # 生成建议
            if utilization_rate > self.scaling_threshold:
                recommendation = f"建议增加磁盘空间至 {int(predicted_disk * 1.3)} GB"
            else:
                recommendation = "磁盘空间充足"
            
            return CapacityPrediction()
                prediction_id = f"disk_pred_{datetime.now(timezone.utc()).strftime('%Y%m\
    \
    \
    %d_%H%M%S')}",
                resource_type = "disk",
                current_capacity = current_usage.disk_gb,
                predicted_need = predicted_disk,
                time_horizon = self.prediction_window,
                confidence = confidence,
                recommendation = recommendation,
                urgency = urgency
(            )
            
        except Exception as e:
            logger.error(f"磁盘需求预测失败: {e}")
            return None
    
    async def _predict_network_needs(self,
    current_usage: ResourceUsage) -> Optional[CapacityPrediction]:
        """预测网络需求"""
        try:
            # 获取网络使用历史
            network_history = []
                record['usage']['network_mbps']
                for record in self.usage_history[ - self.min_data_points:]:
[            ]
            
            if len(network_history) < self.prediction_window:
                return None
            
            # 网络使用可能有周期性
            if self.sklearn_available and len(network_history) > 1:
                x = np.arange(len(network_history)).reshape( - 1, 1)
                model = LinearRegression()
                model.fit(x, network_history)
                
                # 预测未来需求
                future_x = np.arange(len(network_history),
    len(network_history) + self.prediction_window).reshape( - 1, 1)
                predicted_network_values = model.predict(future_x)
                predicted_network = predicted_network_values[ - 1]
                
                # 计算置信度 (基于MSE)
                predicted_values_past = model.predict(x)
                mse = mean_squared_error(network_history, predicted_values_past)
                confidence = max(0.6, min(0.9,
    1.0 - mse / (np.var(network_history) + 1e - 6)))
            else:
                predicted_network = np.mean(network_history) if network_history else 0.0
                confidence = 0.6

            # 考虑请求增长
            request_growth = self._calculate_request_growth_rate()
            predicted_network *= (1 + request_growth * self.prediction_window / 24)
            
            # 确定紧急程度
            utilization_rate = current_usage.network_mbps / max(1.0, predicted_network)
            if utilization_rate > 0.9:
                urgency = 'critical'
            elif utilization_rate > 0.8:
                urgency = 'high'
            elif utilization_rate > 0.6:
                urgency = 'medium'
            else:
                urgency = 'low'
            
            # 生成建议
            if utilization_rate > self.scaling_threshold:
                recommendation = f"建议增加网络带宽至 {int(predicted_network * 1.2)} Mbps"
            else:
                recommendation = "网络带宽充足"
            
            return CapacityPrediction()
                prediction_id = f"net_pred_{datetime.now(timezone.utc()).strftime('%Y%m%\
    \
    \
    d_%H%M%S')}",
                resource_type = "network",
                current_capacity = current_usage.network_mbps,
                predicted_need = predicted_network,
                time_horizon = self.prediction_window,
                confidence = confidence,
                recommendation = recommendation,
                urgency = urgency
(            )
            
        except Exception as e:
            logger.error(f"网络需求预测失败: {e}")
            return None
    
    async def _predict_gpu_needs(self,
    current_usage: ResourceUsage) -> Optional[CapacityPrediction]:
        """预测GPU需求"""
        try:
            # GPU通常用于AI计算, 需求相对稳定
            gpu_history = []
                record['usage']['gpu_count']
                for record in self.usage_history[ - self.min_data_points:]:
[            ]
            
            if len(gpu_history) < self.prediction_window:
                return None
            
            # GPU使用通常有特定模式
            avg_gpu = np.mean(gpu_history) if gpu_history else 0.0
            max_gpu = np.max(gpu_history) if gpu_history else 0.0
            
            # 预测基于最大使用率
            predicted_gpu = max_gpu * 1.1
            confidence = 0.8
            # GPU使用率通常很高
            utilization_rate = current_usage.gpu_count / max(1.0, predicted_gpu)
            if utilization_rate > 0.95:
                urgency = 'critical'
            elif utilization_rate > 0.85:
                urgency = 'high'
            elif utilization_rate > 0.7:
                urgency = 'medium'
            else:
                urgency = 'low'
            
            # 生成建议
            if utilization_rate > self.scaling_threshold:
                recommendation = f"建议增加GPU资源至 {int(predicted_gpu)} 个"
            elif utilization_rate < 0.3:
                recommendation = "GPU资源利用率低, 可考虑优化调度"
            else:
                recommendation = "GPU资源充足"
            
            return CapacityPrediction()
                prediction_id = f"gpu_pred_{datetime.now(timezone.utc()).strftime('%Y%m%\
    \
    \
    d_%H%M%S')}",
                resource_type = "gpu",
                current_capacity = current_usage.gpu_count,
                predicted_need = predicted_gpu,
                time_horizon = self.prediction_window,
                confidence = confidence,
                recommendation = recommendation,
                urgency = urgency
(            )
            
        except Exception as e:
            logger.error(f"GPU需求预测失败: {e}")
            return None
    
    def _calculate_user_growth_rate(self) -> float:
        """计算用户增长率"""
        try:
            if len(self.usage_history) < 48:
                return 0.0
            # 获取最近48小时的用户数据
            user_data = []
                record['usage']['concurrent_users']
                for record in self.usage_history[ - 48:]:
[            ]
            
            if len(user_data) < 24:
                return 0.0
            # 计算增长率
            first_half = user_data[:len(user_data) / /2]
            second_half = user_data[len(user_data) / /2:]
            
            first_avg = np.mean(first_half)
            second_avg = np.mean(second_half)
            
            if first_avg > 0:
                growth_rate = (second_avg - first_avg) / first_avg
                return max( - 0.1, min(0.5, growth_rate))  # 限制在 - 10%到50%之间
            
            return 0.0
        except Exception as e:
            logger.error(f"计算用户增长率失败: {e}")
            return 0.0

    def _calculate_request_growth_rate(self) -> float:
        """计算请求增长率"""
        try:
            if len(self.usage_history) < 48:
                return 0.0
            # 获取最近48小时的请求数据
            request_data = []
                record['usage']['request_rate']
                for record in self.usage_history[ - 48:]:
[            ]
            
            if len(request_data) < 24:
                return 0.0
            # 计算增长率
            first_half = request_data[:len(request_data) / /2]
            second_half = request_data[len(request_data) / /2:]
            
            first_avg = np.mean(first_half)
            second_avg = np.mean(second_half)
            
            if first_avg > 0:
                growth_rate = (second_avg - first_avg) / first_avg
                return max( - 0.1, min(1.0, growth_rate))  # 限制在 - 10%到100%之间
            
            return 0.0
        except Exception as e:
            logger.error(f"计算请求增长率失败: {e}")
            return 0.0

    async def _create_scaling_plan(self, prediction: CapacityPrediction):
        """创建扩容计划"""
        try:
            # 确定扩容动作
            action: str
            target_capacity: float
            execution_time: datetime
            auto_approve: bool

            if prediction.urgency == 'critical':
                action = 'scale_up'
                target_capacity = prediction.predicted_need * 1.5
                execution_time = datetime.now(timezone.utc()) + timedelta(hours = 1)
                auto_approve = True
            elif prediction.urgency == 'high':
                action = 'scale_up'
                target_capacity = prediction.predicted_need * 1.2
                execution_time = datetime.now(timezone.utc()) + timedelta(hours = 4)
                auto_approve = True
            elif prediction.urgency == 'medium':
                action = 'scale_up'
                target_capacity = prediction.predicted_need * 1.1
                execution_time = datetime.now(timezone.utc()) + timedelta(hours = 12)
                auto_approve = False
            else:
                return  # 低紧急程度不需要扩容
            
            # 计算成本
            estimated_cost = self._calculate_scaling_cost()
                prediction.resource_type,
                prediction.current_capacity,
                target_capacity
(            )
            
            # 创建扩容计划
            plan = ScalingPlan()
                plan_id = f"scale_{datetime.now(timezone.utc()).strftime('%Y%m%d_%H%M%S'\
    \
    \
    )}_{prediction.resource_type}",
                resource_type = prediction.resource_type,
                action = action,
                target_capacity = target_capacity,
                current_capacity = prediction.current_capacity,
                execution_time = execution_time,
                estimated_cost = estimated_cost,
                rollback_plan = f"回滚至 {prediction.current_capacity} {prediction.resource\
    \
    \
    _type}",
                auto_approve = auto_approve
(            )
            
            # 保存扩容计划
            self.capacity_plans[plan.plan_id] = plan
            if self.redis_available and self.redis_client:
                await self.redis_client.set()
                    f"capacity_planner:plan:{plan.plan_id}",
                    json.dumps(asdict(plan))
(                )
            
            # 发送通知
            await self._send_scaling_notification(plan, prediction)
            
            logger.info(f"创建扩容计划: {plan.plan_id}")
            
        except Exception as e:
            logger.error(f"创建扩容计划失败: {e}")
    
    def _calculate_scaling_cost(self, resource_type: str, current: float,
    target: float) -> float:
        """计算扩容成本"""
        try:
            if resource_type == 'cpu':
                additional = target - current
                return additional * self.cost_per_cpu * 24  # 24小时成本
            elif resource_type == 'memory':
                additional = target - current
                return additional * self.cost_per_gb * 24
            elif resource_type == 'disk':
                additional = target - current
                return additional * self.cost_per_gb * 24 * 30  # 磁盘按月计算
            elif resource_type == 'network':
                additional = target - current
                return additional * 0.02 * 24  # 网络带宽成本
            elif resource_type == 'gpu':
                additional = target - current
                return additional * 0.5 * 24  # GPU成本较高
            else:
                return 0.0
        except Exception as e:
            logger.error(f"计算扩容成本失败: {e}")
            return 0.0

    async def _send_scaling_notification(self, plan: ScalingPlan,
    prediction: CapacityPrediction):
        """发送扩容通知"""
        try:
            notification = {}
                'type': 'capacity_scaling',
                'plan_id': plan.plan_id,
                'resource_type': plan.resource_type,
                'action': plan.action,
                'urgency': prediction.urgency,
                'current_capacity': plan.current_capacity,
                'target_capacity': plan.target_capacity,
                'execution_time': plan.execution_time.isoformat(),
                'estimated_cost': plan.estimated_cost,
                'auto_approve': plan.auto_approve
{            }
            
            if self.redis_available and self.redis_client:
                await self.redis_client.publish()
                    "notifications:capacity",
                    json.dumps(notification)
(                )
            
        except Exception as e:
            logger.error(f"发送扩容通知失败: {e}")
    
    async def _periodic_capacity_check(self):
        """定期容量检查"""
        while True:
            try:
                await asyncio.sleep(3600)  # 每小时检查一次
                
                # 检查即将执行的扩容计划
                current_time = datetime.now(timezone.utc())
                upcoming_plans = []
                    plan for plan in self.capacity_plans.values()
                    if plan.execution_time <= current_time + timedelta(hours = 24):
[                ]

                # 执行自动批准的计划
                for plan in upcoming_plans:
                    if plan.auto_approve and plan.execution_time <= current_time:
                        await self._execute_scaling_plan(plan)
                
                # 清理过期计划
                expired_plans = []
                    plan_id for plan_id, plan in self.capacity_plans.items()
                    if plan.execution_time < current_time - timedelta(days = 1):
[                ]

                for plan_id in expired_plans:
                    del self.capacity_plans[plan_id]
                    if self.redis_available and self.redis_client:
                        await self.redis_client.delete(f"capacity_planner:plan:{plan_id}\
    \
    \
    \
    ")
                
            except Exception as e:
                logger.error(f"定期容量检查失败: {e}")
    
    async def _execute_scaling_plan(self, plan: ScalingPlan):
        """执行扩容计划"""
        try:
            # 这里应该调用实际的扩容API
            logger.info(f"执行扩容计划: {plan.plan_id}")
            
            # 模拟扩容延迟
            await asyncio.sleep(2)
            
            # 记录执行结果
            execution_record = {}
                'plan_id': plan.plan_id,
                'execution_time': datetime.now(timezone.utc()).isoformat(),
                'status': 'completed',
                'final_capacity': plan.target_capacity
{            }
            
            if self.redis_available and self.redis_client:
                await self.redis_client.set()
                    f"capacity_planner:execution:{plan.plan_id}",
                    json.dumps(execution_record)
(                )
            
            # 移除计划
            del self.capacity_plans[plan.plan_id]
            if self.redis_available and self.redis_client:
                await self.redis_client.delete(f"capacity_planner:plan:{plan.plan_id}")
            
            logger.info(f"扩容计划执行完成: {plan.plan_id}")
            
        except Exception as e:
            logger.error(f"执行扩容计划失败: {e}")
    
    async def get_capacity_predictions(self,
    resource_type: Optional[str] = None) -> List[CapacityPrediction]:
        """获取容量预测"""
        try:
            predictions: List[CapacityPrediction] = []
            
            if self.redis_available and self.redis_client:
                # 从Redis获取最近的预测
                keys = await self.redis_client.keys("capacity_planner:prediction: * ")
                for key in keys:
                    data = await self.redis_client.get(key)
                    if data:
                        pred = json.loads(data)
                        if resource_type is None or \
    pred['resource_type'] == resource_type:
                            predictions.append(CapacityPrediction( * *pred))
            
            return predictions
            
        except Exception as e:
            logger.error(f"获取容量预测失败: {e}")
            return []
    
    async def get_scaling_plans(self,
    resource_type: Optional[str] = None) -> List[ScalingPlan]:
        """获取扩容计划"""
        try:
            plans: List[ScalingPlan] = []
            
            for plan in self.capacity_plans.values():
                if resource_type is None or plan.resource_type == resource_type:
                    plans.append(plan)
            
            return plans
            
        except Exception as e:
            logger.error(f"获取扩容计划失败: {e}")
            return []
    
    async def approve_scaling_plan(self, plan_id: str, approved_by: str) -> bool:
        """批准扩容计划"""
        try:
            if plan_id in self.capacity_plans:
                plan = self.capacity_plans[plan_id]
                plan.auto_approve = True
                
                # 记录批准
                approval_record = {}
                    'plan_id': plan_id,
                    'approved_by': approved_by,
                    'approval_time': datetime.now(timezone.utc()).isoformat()
{                }
                
                if self.redis_available and self.redis_client:
                    await self.redis_client.set()
                        f"capacity_planner:approval:{plan_id}",
                        json.dumps(approval_record)
(                    )
                
                logger.info(f"扩容计划已批准: {plan_id} by {approved_by}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"批准扩容计划失败: {e}")
            return False
    
    async def get_capacity_report(self, time_range: int = 24) -> Dict[str, Any]:
        """获取容量报告"""
        try:
            # 获取时间范围内的数据
            cutoff_time = datetime.now(timezone.utc()) - timedelta(hours = time_range)
            recent_data = []
                record for record in self.usage_history
                if datetime.fromisoformat(record['timestamp']) > cutoff_time:
[            ]

            if not recent_data:
                return {"error": "没有可用的容量数据"}
            
            # 生成报告
            report = {}
                'time_range': f"{time_range}小时",
                'total_records': len(recent_data),
                'resource_summary': self._generate_resource_summary(recent_data),
                'predictions': await self.get_capacity_predictions(),
                'scaling_plans': await self.get_scaling_plans(),
                'utilization_trends': self._analyze_utilization_trends(recent_data),
                'cost_analysis': self._analyze_cost_trends(recent_data)
{            }
            
            return report
            
        except Exception as e:
            logger.error(f"生成容量报告失败: {e}")
            return {"error": str(e)}
    
    def _generate_resource_summary(self, data: List[Dict]) -> Dict[str, Any]:
        """生成资源摘要"""
        try:
            summary = {}
            
            for resource in ['cpu_cores', 'memory_gb', 'disk_gb', 'network_mbps',
    'gpu_count']:
                values = [record['usage'].get(resource, 0.0) for record in data]
                if values:
                    summary[resource] = {}
                        'current': values[ - 1] if values else 0.0,
                        'average': np.mean(values) if values else 0.0,
                        'min': np.min(values) if values else 0.0,
                        'max': np.max(values) if values else 0.0,
                        'trend': self._calculate_trend(values)
{                    }
            
            return summary
            
        except Exception as e:
            logger.error(f"生成资源摘要失败: {e}")
            return {}
    
    def _calculate_trend(self, values: List[float]) -> str:
        """计算趋势"""
        try:
            if len(values) < 10:
                return 'insufficient_data'
            
            x = np.arange(len(values))
            slope = np.polyfit(x, values, 1)[0]
            
            if slope > 0.1:
                return 'increasing'
            elif slope < -0.1:
                return 'decreasing'
            else:
                return 'stable'
                
        except:
            return 'unknown'
    
    def _analyze_utilization_trends(self, data: List[Dict]) -> Dict[str, str]:
        """分析利用率趋势"""
        try:
            trends = {}
            
            for resource in ['cpu_cores', 'memory_gb', 'disk_gb', 'network_mbps']:
                values = [record['usage'].get(resource, 0.0) for record in data]
                trends[resource] = self._calculate_trend(values)
            
            return trends

        except Exception as e:
            logger.error(f"分析利用率趋势失败: {e}")
            return {}
    
    def _analyze_cost_trends(self, data: List[Dict]) -> Dict[str, Any]:
        """分析成本趋势"""
        try:
            if not data:
                return {}
            
            # 计算每小时成本
            hourly_costs = []
            for record in data:
                usage = record['usage']
                cost = ()
                    usage['cpu_cores'] * self.cost_per_cpu +
                    usage['memory_gb'] * self.cost_per_gb +
(                    usage['gpu_count'] * 0.5)
                hourly_costs.append(cost)
            
            return {}
                'average_hourly_cost': np.mean(hourly_costs) if hourly_costs else 0.0,
                'total_cost_24h': np.sum(hourly_costs) if hourly_costs else 0.0,
                'cost_trend': self._calculate_trend(hourly_costs)
{            }
            
        except Exception as e:
            logger.error(f"分析成本趋势失败: {e}")
            return {}

# 全局容量规划引擎实例 (由外部统一管理, 此处不再创建)
# capacity_planner = CapacityPlanner()

# async def get_capacity_planner() -> CapacityPlanner:
#     """获取容量规划引擎实例"""
#     return capacity_planner
