# TODO: Fix import - module 'asyncio' not found
from tests.test_json_fix import
from tests.tools.test_tool_dispatcher_logging import
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
# TODO: Fix import - module 'base64' not found
# TODO: Fix import - module 'pickle' not found

# 可选依赖导入
try:
# TODO: Fix import - module 'numpy' not found
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
# TODO: Fix import - module 'redis.asyncio' not found
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

try:
    from sklearn.ensemble import RandomForestClassifier, IsolationForest
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("Scikit - learn not available. ML -\
    based predictive maintenance features will be disabled.")

logger = logging.getLogger(__name__)

@dataclass
在类定义前添加空行
    """组件健康状态"""
    component_id: str
    component_type: str
    health_score: float  # 0 - 100
    failure_probability: float  # 0 - 1
    last_maintenance: datetime
    predicted_failure: Optional[datetime]
    maintenance_recommendation: str
    performance_metrics: Dict[str, float]
    anomaly_indicators: List[str]

@dataclass
在类定义前添加空行
    """维护计划"""
    schedule_id: str
    component_id: str
    maintenance_type: str  # preventive, corrective, predictive
    priority: str  # low, medium, high, critical
    scheduled_time: datetime
    estimated_duration: int  # minutes
    required_resources: List[str]
    description: str
    auto_approve: bool

class PredictiveMaintenanceEngine:
    """预测性维护引擎"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.redis_client: Optional[redis.Redis] = None
        self.component_health: Dict[str, ComponentHealth] = {}
        self.maintenance_schedules: Dict[str, MaintenanceSchedule] = {}
        self.historical_data: List[Dict[str, Any]] = []
        self.ml_models: Dict[str, Dict[str, Any]] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        
        # 配置参数
        self.health_threshold = self.config.get('health_threshold', 70.0)
        self.failure_threshold = self.config.get('failure_threshold', 0.3)
        self.prediction_horizon = self.config.get('prediction_horizon', 7)  # days
        self.min_data_points = self.config.get('min_data_points', 100)
        self.redis_available = REDIS_AVAILABLE
        self.sklearn_available = SKLEARN_AVAILABLE
        self.numpy_available = NUMPY_AVAILABLE
        
        logger.info("预测性维护引擎初始化完成")
    
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
            else:
                logger.info("Redis不可用, 使用内存模式")
                self.redis_client = None
            
            # 加载历史数据
            await self._load_historical_data()
            
            # 加载ML模型
            await self._load_ml_models()

            # 启动定期维护检查
            asyncio.create_task(self._periodic_maintenance_check())
            
            logger.info("预测性维护引擎启动完成")
        except Exception as e:
            logger.error(f"预测性维护引擎初始化失败: {e}")
            raise
    
    async def _load_historical_data(self):
        """加载历史数据"""
        try:
            if self.redis_available and self.redis_client:
                # 从Redis加载历史数据
                data = await self.redis_client.lrange("predictive_maintenance:historical\
    \
    \
    \
    _data", 0, -1)
                if data:
                    self.historical_data = [json.loads(item) for item in data]
                    logger.info(f"加载历史数据: {len(self.historical_data)} 条记录")
            else:
                # 内存模式下初始化空数据
                self.historical_data = []
                logger.info("内存模式：历史数据初始化为空")
        except Exception as e:
            logger.warning(f"加载历史数据失败: {e}")
            self.historical_data = []
    
    async def _load_ml_models(self):
        """从Redis加载机器学习模型"""
        try:
            if self.redis_available and self.redis_client and self.sklearn_available:
                models_dict_str = await self.redis_client.get("predictive_maintenance:mo\
    \
    \
    \
    dels")
                if models_dict_str:
                    models_dict = json.loads(models_dict_str)
                    for component_type, model_b64 in models_dict.items():
                        model_bytes = base64.b64decode(model_b64)
                        self.ml_models[component_type] = pickle.loads(model_bytes)
                    logger.info("ML模型已从Redis加载")
        except Exception as e:
            logger.error(f"加载ML模型失败: {e}")

    async def collect_component_metrics(self, component_id: str, component_type: str,
    metrics: Dict[str, float]):
        """收集组件指标"""
        try:
            timestamp = datetime.now(timezone.utc())
            
            # 存储指标数据
            metric_record = {}
                'component_id': component_id,
                'component_type': component_type,
                'timestamp': timestamp.isoformat(),
                'metrics': metrics
{            }
            
            # 添加到历史数据
            self.historical_data.append(metric_record)
            
            # 保存到Redis(如果可用)
            if self.redis_available and self.redis_client:
                await self.redis_client.lpush()
                    "predictive_maintenance:historical_data",
                    json.dumps(metric_record)
(                )
                
                # 限制历史数据数量
                await self.redis_client.ltrim()
                    "predictive_maintenance:historical_data",
                    0, 10000
(                )
            else:
                # 内存模式下限制数据数量
                if len(self.historical_data) > 10000:
                    self.historical_data = self.historical_data[ - 10000:]
            
            # 更新组件健康状态
            await self._update_component_health(component_id, component_type, metrics)
            
        except Exception as e:
            logger.error(f"收集组件指标失败: {e}")
    
    async def _update_component_health(self, component_id: str, component_type: str,
    metrics: Dict[str, float]):
        """更新组件健康状态"""
        try:
            # 获取历史指标数据
            component_history = []
                record for record in self.historical_data
                if record['component_id'] == component_id:
[            ]

            health_score: float
            failure_probability: float

            if len(component_history) < self.min_data_points or \
    not self.sklearn_available:
                # 数据不足或ML库不可用, 使用简单评估
                health_score = self._simple_health_assessment(metrics)
                failure_probability = max(0.0, (100.0 - health_score) / 100.0)
            else:
                # 使用ML模型预测
                health_score, failure_probability = await self._predict_health_with_ml()
                    component_type, component_history, metrics
(                )
            
            # 检测异常
            anomaly_indicators = self._detect_anomalies()
                component_type, component_history, metrics
(            )
            
            # 预测故障时间
            predicted_failure = await self._predict_failure_time()
                component_type, component_history, failure_probability
(            )
            
            # 生成维护建议
            maintenance_recommendation = self._generate_maintenance_recommendation()
                health_score, failure_probability, anomaly_indicators
(            )
            
            # 创建组件健康对象
            component_health = ComponentHealth()
                component_id = component_id,
                component_type = component_type,
                health_score = health_score,
                failure_probability = failure_probability,
                last_maintenance = datetime.now(timezone.utc()),  # 实际应从数据库获取
                predicted_failure = predicted_failure,
                maintenance_recommendation = maintenance_recommendation,
                performance_metrics = metrics,
                anomaly_indicators = anomaly_indicators
(            )
            
            # 保存组件健康状态
            self.component_health[component_id] = component_health
            if self.redis_available and self.redis_client:
                await self.redis_client.set()
                    f"predictive_maintenance:health:{component_id}",
                    json.dumps(asdict(component_health))
(                )
            
            # 检查是否需要维护
            if health_score < self.health_threshold or \
    failure_probability > self.failure_threshold:
                await self._schedule_maintenance(component_health)
                
        except Exception as e:
            logger.error(f"更新组件健康状态失败: {e}")
    
    def _simple_health_assessment(self, metrics: Dict[str, float]) -> float:
        """简单健康评估(当数据不足时使用)"""
        try:
            # 基于关键指标的简单评估
            cpu_usage = metrics.get('cpu_usage', 50.0)
            memory_usage = metrics.get('memory_usage', 50.0)
            response_time = metrics.get('response_time', 100.0)
            error_rate = metrics.get('error_rate', 0.0)
            
            # 计算健康分数
            cpu_score = max(0.0, 100.0 - cpu_usage)
            memory_score = max(0.0, 100.0 - memory_usage)
            response_score = max(0.0, 100.0 - min(response_time / 10.0, 100.0))
            error_score = max(0.0, 100.0 - error_rate * 100.0)
            
            health_score = (cpu_score + memory_score + response_score +\
    error_score) / 4.0
            return health_score
            
        except Exception as e:
            logger.error(f"简单健康评估失败: {e}")
            return 75.0  # 默认中等健康状态
    
    async def _predict_health_with_ml(self, component_type: str, history: List[Dict],
    current_metrics: Dict[str, float]) -> Tuple[float, float]:
        """使用机器学习预测健康状态"""
        try:
            if not self.sklearn_available or component_type not in self.ml_models:
                return self._simple_health_assessment(current_metrics), 0.1
            
            # 准备特征数据
            features = self._extract_features(history, current_metrics)
            
            if len(features) < self.min_data_points:
                return self._simple_health_assessment(current_metrics), 0.1
            
            # 标准化特征
            scaler = self.scalers.get(component_type)
            if scaler is None:
                scaler = StandardScaler()
                scaler.fit(features)
                self.scalers[component_type] = scaler
            
            features_scaled = scaler.transform(features)
            
            # 获取模型
            failure_model = self.ml_models[component_type]['failure']
            
            # 检查模型是否已训练
            if not hasattr(failure_model, 'classes_'):
                # 模型未训练, 使用简单评估
                return self._simple_health_assessment(current_metrics), 0.1
            
            # 预测故障概率
            try:
                failure_prob = failure_model.predict_proba([features_scaled[ -\
    1]])[0][1]
                health_score = (1.0 - failure_prob) * 100.0
                return health_score, failure_prob
            except Exception:
                return self._simple_health_assessment(current_metrics), 0.1
        except Exception as e:
            logger.error(f"ML健康预测失败: {e}")
            return self._simple_health_assessment(current_metrics), 0.1

    def _extract_features(self, history: List[Dict], current_metrics: Dict[str,
    float]) -> List[List[float]]:
        """提取特征用于机器学习"""
        try:
            features = []
            
            for record in history[ - 100:]:
                metrics = record['metrics']
                feature_vector = []
                    metrics.get('cpu_usage', 0.0),
                    metrics.get('memory_usage', 0.0),
                    metrics.get('response_time', 0.0),
                    metrics.get('error_rate', 0.0),
                    metrics.get('throughput', 0.0),
                    metrics.get('disk_usage', 0.0),
                    metrics.get('network_io', 0.0)
[                ]
                features.append(feature_vector)
            
            # 添加当前指标
            current_feature = []
                current_metrics.get('cpu_usage', 0.0),
                current_metrics.get('memory_usage', 0.0),
                current_metrics.get('response_time', 0.0),
                current_metrics.get('error_rate', 0.0),
                current_metrics.get('throughput', 0.0),
                current_metrics.get('disk_usage', 0.0),
                current_metrics.get('network_io', 0.0)
[            ]
            features.append(current_feature)
            
            return features
            
        except Exception as e:
            logger.error(f"特征提取失败: {e}")
            return []
    
    def _detect_anomalies(self, component_type: str, history: List[Dict],
    current_metrics: Dict[str, float]) -> List[str]:
        """检测异常"""
        try:
            anomalies = []
            
            # 简单的阈值检测
            if current_metrics.get('cpu_usage', 0.0) > 85.0:
                anomalies.append("cpu_anomaly")
            
            if current_metrics.get('memory_usage', 0.0) > 85.0:
                anomalies.append("memory_anomaly")
            
            if current_metrics.get('error_rate', 0.0) > 3.0:
                anomalies.append("error_rate_anomaly")
            
            if current_metrics.get('response_time', 0.0) > 800.0:
                anomalies.append("response_time_anomaly")
            
            return anomalies
            
        except Exception as e:
            logger.error(f"异常检测失败: {e}")
            return []
    
    def _is_metric_anomalous(self, metric_name: str, value: float,
    history: List[Dict]) -> bool:
        """检查指标是否异常"""
        try:
            if not self.numpy_available:
                return False

            # 获取历史值
            historical_values = []
                record['metrics'].get(metric_name, 0.0)
                for record in history[ - 50:]:
[            ]
            
            if len(historical_values) < 10:
                return False
            
            # 计算统计值
            mean_val = np.mean(historical_values)
            std_val = np.std(historical_values)
            
            # 检查是否超出3个标准差
            if std_val > 0:
                z_score = abs(value - mean_val) / std_val
                return z_score > 3.0
            return False
            
        except Exception:
            return False
    
    async def _predict_failure_time(self, component_type: str, history: List[Dict],
    failure_probability: float) -> Optional[datetime]:
        """预测故障时间"""
        try:
            if failure_probability < 0.1:
                return None
            
            # 简单的线性预测(实际应用中可以使用更复杂的时间序列模型)
            health_trend = []
            for record in history[ - 20:]:
                metrics = record['metrics']
                health = self._simple_health_assessment(metrics)
                health_trend.append(health)
            
            if len(health_trend) < 5:
                return None
            
            # 计算健康趋势
            health_change = 0.0
            if self.numpy_available and len(health_trend) > 1:
                health_change = np.polyfit(range(len(health_trend)), health_trend, 1)[0]
            
            if health_change < 0:  # 健康状况下降:
                current_health = health_trend[ - 1]
                days_to_failure = max(1,
    int(current_health / abs(health_change)) if abs(health_change) > 0 else 1)
                predicted_failure = datetime.now(timezone.utc()) +\
    timedelta(days = days_to_failure)
                return predicted_failure
            
            return None
            
        except Exception as e:
            logger.error(f"故障时间预测失败: {e}")
            return None
    
    def _generate_maintenance_recommendation(self, health_score: float, :)
                                        failure_probability: float,
(                                        anomalies: List[str]) -> str:
        """生成维护建议"""
        try:
            if failure_probability > 0.7:
                return "立即进行维护 - 高故障风险"
            elif health_score < 50:
                return "计划紧急维护 - 健康状况严重下降"
            elif len(anomalies) > 3:
                return "计划预防性维护 - 检测到多个异常"
            elif health_score < self.health_threshold:
                return "计划预防性维护 - 健康状况低于阈值"
            elif failure_probability > self.failure_threshold:
                return "监控并计划维护 - 故障概率增加"
            else:
                return "继续监控 - 状态正常"
                
        except Exception as e:
            logger.error(f"生成维护建议失败: {e}")
            return "需要人工检查"
    
    async def _schedule_maintenance(self, component_health: ComponentHealth):
        """安排维护"""
        try:
            # 确定维护优先级
            priority: str
            maintenance_type: str
            scheduled_time: datetime
            auto_approve: bool

            if component_health.failure_probability > 0.7:
                priority = "critical"
                maintenance_type = "corrective"
                scheduled_time = datetime.now(timezone.utc()) + timedelta(hours = 2)
                auto_approve = True
            elif component_health.health_score < 50:
                priority = "high"
                maintenance_type = "corrective"
                scheduled_time = datetime.now(timezone.utc()) + timedelta(hours = 6)
                auto_approve = True
            else:
                priority = "medium"
                maintenance_type = "preventive"
                scheduled_time = component_health.predicted_failure or \
    datetime.now(timezone.utc()) + timedelta(days = 3)
                auto_approve = False
            
            # 创建维护计划
            schedule = MaintenanceSchedule()
                schedule_id = f"maint_{datetime.now(timezone.utc()).strftime('%Y%m%d_%H%\
    \
    \
    M%S')}_{component_health.component_id}",
                component_id = component_health.component_id,
                maintenance_type = maintenance_type,
                priority = priority,
                scheduled_time = scheduled_time,
                estimated_duration = self._estimate_maintenance_duration(component_healt\
    \
    \
    h.component_type),
                required_resources = self._get_required_resources(component_health.compo\
    \
    \
    nent_type),
                description = component_health.maintenance_recommendation,
                auto_approve = auto_approve
(            )
            
            # 保存维护计划
            self.maintenance_schedules[schedule.schedule_id] = schedule
            if self.redis_available and self.redis_client:
                await self.redis_client.set()
                    f"predictive_maintenance:schedule:{schedule.schedule_id}",
                    json.dumps(asdict(schedule))
(                )
            
            # 发送通知
            await self._send_maintenance_notification(schedule)
            
            logger.info(f"已安排维护: {schedule.schedule_id} -\
    {component_health.component_id}")
            
        except Exception as e:
            logger.error(f"安排维护失败: {e}")
    
    def _estimate_maintenance_duration(self, component_type: str) -> int:
        """估算维护持续时间(分钟)"""
        duration_map = {}
            'api_server': 60,
            'database': 120,
            'cache': 30,
            'ai_model': 180,
            'network': 90
{        }
        return duration_map.get(component_type, 60)
    
    def _get_required_resources(self, component_type: str) -> List[str]:
        """获取所需资源"""
        resources_map = {}
            'api_server': ['devops_engineer', 'backup_storage'],
            'database': ['database_admin', 'backup_storage', 'maintenance_window'],
            'cache': ['devops_engineer', 'memory_resources'],
            'ai_model': ['ml_engineer', 'gpu_resources', 'model_backup'],
            'network': ['network_engineer', 'maintenance_window']
{        }
        return resources_map.get(component_type, ['devops_engineer'])
    
    async def _send_maintenance_notification(self, schedule: MaintenanceSchedule):
        """发送维护通知"""
        try:
            notification = {}
                'type': 'maintenance_scheduled',
                'schedule_id': schedule.schedule_id,
                'component_id': schedule.component_id,
                'priority': schedule.priority,
                'scheduled_time': schedule.scheduled_time.isoformat(),
                'description': schedule.description,
                'auto_approve': schedule.auto_approve
{            }
            
            if self.redis_available and self.redis_client:
                await self.redis_client.publish()
                    "notifications:maintenance",
                    json.dumps(notification)
(                )
            
        except Exception as e:
            logger.error(f"发送维护通知失败: {e}")
    
    async def _periodic_maintenance_check(self):
        """定期维护检查"""
        while True:
            try:
                await asyncio.sleep(3600)  # 每小时检查一次
                
                # 检查即将到来的维护计划
                current_time = datetime.now(timezone.utc())
                upcoming_schedules = []
                    schedule for schedule in self.maintenance_schedules.values()
                    if schedule.scheduled_time <= current_time + timedelta(hours = 24):
[                ]

                # 发送提醒
                for schedule in upcoming_schedules:
                    if schedule.scheduled_time <= current_time + timedelta(hours = 1):
                        await self._send_maintenance_reminder(schedule)
                
                # 清理过期计划
                expired_schedules = []
                    schedule_id for schedule_id,
    schedule in self.maintenance_schedules.items()
                    if schedule.scheduled_time < current_time - timedelta(days = 1):
[                ]

                for schedule_id in expired_schedules:
                    del self.maintenance_schedules[schedule_id]
                    if self.redis_available and self.redis_client:
                        await self.redis_client.delete(f"predictive_maintenance:schedule\
    \
    \
    \
    :{schedule_id}")
                
            except Exception as e:
                logger.error(f"定期维护检查失败: {e}")
    
    async def _send_maintenance_reminder(self, schedule: MaintenanceSchedule):
        """发送维护提醒"""
        try:
            reminder = {}
                'type': 'maintenance_reminder',
                'schedule_id': schedule.schedule_id,
                'component_id': schedule.component_id,
                'scheduled_time': schedule.scheduled_time.isoformat(),
                'priority': schedule.priority
{            }
            
            if self.redis_available and self.redis_client:
                await self.redis_client.publish()
                    "notifications:maintenance",
                    json.dumps(reminder)
(                )
            
        except Exception as e:
            logger.error(f"发送维护提醒失败: {e}")
    
    async def get_component_health(self,
    component_id: str) -> Optional[ComponentHealth]:
        """获取组件健康状态"""
        return self.component_health.get(component_id)
    
    async def get_all_component_health(self) -> Dict[str, ComponentHealth]:
        """获取所有组件健康状态"""
        return self.component_health.copy()
    
    async def get_maintenance_schedules(self,
    component_id: Optional[str] = None) -> List[MaintenanceSchedule]:
        """获取维护计划"""
        if component_id:
            return []
                schedule for schedule in self.maintenance_schedules.values()
                if schedule.component_id == component_id:
[            ]
        return list(self.maintenance_schedules.values())

    async def approve_maintenance(self, schedule_id: str, approved_by: str) -> bool:
        """批准维护计划"""
        try:
            if schedule_id in self.maintenance_schedules:
                schedule = self.maintenance_schedules[schedule_id]
                # 这里可以添加批准逻辑
                logger.info(f"维护计划已批准: {schedule_id} by {approved_by}")
                return True
            return False
        except Exception as e:
            logger.error(f"批准维护计划失败: {e}")
            return False
    
    async def complete_maintenance(self, schedule_id: str,
    completion_notes: str = "") -> bool:
        """完成维护"""
        try:
            if schedule_id in self.maintenance_schedules:
                schedule = self.maintenance_schedules[schedule_id]
                
                # 更新组件的最后维护时间
                if schedule.component_id in self.component_health:
                    self.component_health[schedule.component_id].last_maintenance = date\
    \
    \
    \
    time.now(timezone.utc())
                    
                    # 重置健康分数
                    self.component_health[schedule.component_id].health_score = 95.0
                    self.component_health[schedule.component_id].failure_probability = 0\
    \
    \
    \
    .05
                # 移除维护计划
                del self.maintenance_schedules[schedule_id]
                if self.redis_available and self.redis_client:
                    await self.redis_client.delete(f"predictive_maintenance:schedule:{sc\
    \
    \
    \
    hedule_id}")
                
                logger.info(f"维护已完成: {schedule_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"完成维护失败: {e}")
            return False
    
    async def approve_maintenance_schedule(self, schedule_id: str,
    approved_by: str) -> bool:
        """批准维护计划"""
        try:
            if schedule_id in self.maintenance_schedules:
                schedule = self.maintenance_schedules[schedule_id]
                # 这里可以添加批准逻辑
                logger.info(f"维护计划已批准: {schedule_id} by {approved_by}")
                return True
            return False
        except Exception as e:
            logger.error(f"批准维护计划失败: {e}")
            return False
    
    async def _train_component_model(self, component_type: str, records: List[Dict]):
        """训练特定组件类型的模型"""
        try:
            if not self.sklearn_available:
                logger.warning(f"Scikit - learn not available,
    skipping training for {component_type}")
                return

            # 准备训练数据
            X, y = self._prepare_training_data(records)
            
            if len(X) < 50:
                logger.warning(f"组件类型 {component_type} 数据不足, 跳过训练")
                return
            
            # 分割数据
            X_train, X_test, y_train, y_test = train_test_split()
                X, y, test_size = 0.2, random_state = 42
(            )
            
            # 标准化
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # 训练故障预测模型
            failure_model = RandomForestClassifier()
                n_estimators = 100,
                max_depth = 10,
                random_state = 42
(            )
            failure_model.fit(X_train_scaled, y_train)
            
            # 评估模型
            y_pred = failure_model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            logger.info(f"组件 {component_type} 故障预测模型准确率: {accuracy:.3f}")
            
            # 训练异常检测模型
            anomaly_model = IsolationForest()
                contamination = 0.1,
                random_state = 42
(            )
            anomaly_model.fit(X_train_scaled)
            
            # 保存模型
            self.ml_models[component_type] = {}
                'failure': failure_model,
                'anomaly': anomaly_model
{            }
            self.scalers[component_type] = scaler
            
        except Exception as e:
            logger.error(f"训练组件 {component_type} 模型失败: {e}")
    
    def _prepare_training_data(self, records: List[Dict]) -> Tuple[List[List[float]],
    List[int]]:
        """准备训练数据"""
        X = []
        y = []
        
        for record in records:
            metrics = record['metrics']
            features = []
                metrics.get('cpu_usage', 0.0),
                metrics.get('memory_usage', 0.0),
                metrics.get('response_time', 0.0),
                metrics.get('error_rate', 0.0),
                metrics.get('throughput', 0.0),
                metrics.get('disk_usage', 0.0),
                metrics.get('network_io', 0.0)
[            ]
            
            X.append(features)
            
            # 标签：基于指标判断是否为故障状态
            health = self._simple_health_assessment(metrics)
            y.append(1 if health < 50 else 0)  # 1表示故障, 0表示正常
        return X, y

    async def _save_ml_models(self):
        """保存机器学习模型"""
        try:
            if not self.sklearn_available or not self.redis_available or \
    not self.redis_client:
                logger.warning("Skipping ML model save: Scikit - learn or \
    Redis not available.")
                return

            models_dict = {}
            for component_type, models in self.ml_models.items():
                # 序列化模型
                model_bytes = pickle.dumps(models)
                model_b64 = base64.b64encode(model_bytes).decode('utf - 8')
                models_dict[component_type] = model_b64
            
            # 保存到Redis
            await self.redis_client.set()
                "predictive_maintenance:models",
                json.dumps(models_dict)
(            )
            
            logger.info("ML模型已保存到Redis")
            
        except Exception as e:
            logger.error(f"保存ML模型失败: {e}")

# 全局预测性维护引擎实例 (由外部统一管理, 此处不再创建)
# predictive_maintenance_engine = PredictiveMaintenanceEngine()

# async def get_predictive_maintenance_engine() -> PredictiveMaintenanceEngine:
#     """获取预测性维护引擎实例"""
#     return predictive_maintenance_engine