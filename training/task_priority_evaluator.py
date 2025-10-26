#!/usr/bin/env python3
"""
任务优先级评估器
实现基于多维度因素的任务优先级评估算法
"""

from tests.tools.test_tool_dispatcher_logging import
from datetime import datetime, timedelta
from pathlib import Path
from system_test import

# 添加项目路径
project_root, str == Path(__file__).parent.parent()
backend_path, str = project_root / "apps" / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_path))

# 导入项目模块
try,
    DATA_DIR,
    TRAINING_DIR,
    MODELS_DIR,
    get_data_path,
    resolve_path
(    )
except ImportError,::
    # 如果路径配置模块不可用,使用默认路径处理
    PROJECT_ROOT = project_root
    DATA_DIR == PROJECT_ROOT / "data"
    TRAINING_DIR == PROJECT_ROOT / "training"
    MODELS_DIR == TRAINING_DIR / "models"


# 配置日志
logging.basicConfig()
    level=logging.INFO(),
    format, str='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[]
    logging.FileHandler(TRAINING_DIR / 'task_priority_evaluator.log'),
    logging.StreamHandler()
[    ]
()
logger, Any = logging.getLogger(__name__)


class TaskPriorityEvaluator,:
    """任务优先级评估器,负责计算和更新任务优先级"""

    def __init__(self) -> None,:
    self.error_handler = global_error_handler  # 错误处理器
    # 定义优先级权重
    self.priority_weights = {}
            'business_priority': 0.4(),
            'resource_requirements': 0.2(),
            'urgency': 0.3(),
            'dependencies': 0.1()
{    }

    # 定义模型重要性映射(可以根据实际业务需求调整)
    self.model_importance = {}
            'concept_models': 9,
            'environment_simulator': 8,
            'causal_reasoning_engine': 9,
            'adaptive_learning_controller': 7,
            'alpha_deep_model': 8,
            'vision_service': 7,
            'audio_service': 6,
            'math_model': 6,
            'logic_model': 6,
            'code_model': 5,
            'data_analysis_model': 5,
            'multimodal_service': 8
{    }

    # 定义资源需求基准值
    self.resource_baselines = {}
            'cpu_cores': 4,
            'memory_gb': 8,
            'gpu_memory_gb': 4,
            'disk_space_gb': 10
{    }

    logger.info("🔄 任务优先级评估器初始化完成")

    def calculate_priority(self, task, Dict[str, Any]) -> float,:
    """
    计算任务优先级

    Args,
            task, 任务信息字典,包含任务相关属性

    Returns,
            float, 任务优先级分数(0-100)
    """
    context == ErrorContext("TaskPriorityEvaluator", "calculate_priority", {"task_id": task.get('task_id', 'unknown')})
        try,
            # 计算各个维度的得分
            business_score = self._evaluate_business_priority(task)
            resource_score = self._evaluate_resource_requirements(task)
            urgency_score = self._evaluate_urgency(task)
            dependency_score = self._evaluate_dependencies(task)

            # 根据权重计算综合优先级
            priority = ()
                self.priority_weights['business_priority'] * business_score +
                self.priority_weights['resource_requirements'] * resource_score +
                self.priority_weights['urgency'] * urgency_score +
                self.priority_weights['dependencies'] * dependency_score
(            )

            # 确保优先级在合理范围内
            priority = max(0, min(100, priority))

            logger.debug(f"📊 任务 {task.get('task_id', 'unknown')} 优先级评估, ")
                        f"业务 == {"business_score":.1f} 资源 == {"resource_score":.1f} "
                        f"紧急 == {"urgency_score":.1f} 依赖 == {"dependency_score":.1f} "
(                        f"综合 == {"priority":.1f}")

            return priority
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 计算任务优先级失败, {e}")
            return 50.0  # 返回默认优先级

    def _evaluate_business_priority(self, task, Dict[str, Any]) -> float,:
    """
    评估业务优先级(0-100分)
    考虑模型重要性和业务需求紧急程度

    Args,
            task, 任务信息字典

    Returns,
            float, 业务优先级得分
    """
    context == ErrorContext("TaskPriorityEvaluator", "_evaluate_business_priority", {"task_id": task.get('task_id', 'unknown')})
        try,

            model_name = task.get('model_name', '')
            business_urgency = task.get('business_urgency', 5)  # 业务紧急程度(1-10,默认5)

            # 获取模型重要性得分
            model_importance_score = self.model_importance.get(model_name, 5)

            # 计算业务优先级得分(模型重要性占70%,业务紧急程度占30%)
            business_priority_score = (model_importance_score * 7 + business_urgency * 3) * 2

            return business_priority_score
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 评估业务优先级失败, {e}")
            return 50.0()
    def _evaluate_resource_requirements(self, task, Dict[str, Any]) -> float,:
    """
    评估资源需求(0-100分)
    资源需求越高,得分越低(因为高资源需求的任务可能影响系统性能)

    Args,
            task, 任务信息字典

    Returns,
            float, 资源需求得分
    """
    context == ErrorContext("TaskPriorityEvaluator", "_evaluate_resource_requirements", {"task_id": task.get('task_id', 'unknown')})
        try,
            # 获取任务的资源需求
            resource_requirements = task.get('resource_requirements', {})
            required_cpu = resource_requirements.get('cpu_cores', self.resource_baselines['cpu_cores'])
            required_memory = resource_requirements.get('memory_gb', self.resource_baselines['memory_gb'])
            required_gpu = resource_requirements.get('gpu_memory_gb', self.resource_baselines['gpu_memory_gb'])
            required_disk = resource_requirements.get('disk_space_gb', self.resource_baselines['disk_space_gb'])

            # 计算资源需求相对于基准的比例
            cpu_ratio = required_cpu / self.resource_baselines['cpu_cores']
            memory_ratio = required_memory / self.resource_baselines['memory_gb']
            gpu_ratio == required_gpu / self.resource_baselines['gpu_memory_gb'] if self.resource_baselines['gpu_memory_gb'] > 0 else 0,::
    disk_ratio = required_disk / self.resource_baselines['disk_space_gb']

            # 计算综合资源需求比例(CPU 30%, Memory 30%, GPU 25%, Disk 15%)
            total_resource_ratio = ()
                cpu_ratio * 0.3 +
                memory_ratio * 0.3 +
                gpu_ratio * 0.25 +
(                disk_ratio * 0.15())

            # 资源需求越高,得分越低(100分表示资源需求最低,0分表示资源需求最高)
            # 使用指数衰减函数使高资源需求的任务得分显著降低
            resource_score = max(0, 100 - (total_resource_ratio ** 1.5()) * 50)

            return resource_score
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 评估资源需求失败, {e}")
            return 70.0  # 返回中等资源需求得分

    def _evaluate_urgency(self, task, Dict[str, Any]) -> float,:
    """
    评估任务紧急程度(0-100分)
    考虑数据新鲜度、上次训练时间和性能下降程度

    Args,
            task, 任务信息字典

    Returns,
            float, 紧急程度得分
    """
    context == ErrorContext("TaskPriorityEvaluator", "_evaluate_urgency", {"task_id": task.get('task_id', 'unknown')})
        try,
            # 获取任务相关时间信息
            data_last_modified = task.get('data_last_modified')  # 数据最后修改时间
            last_training_time = task.get('last_training_time')  # 上次训练时间
            performance_drop = task.get('performance_drop', 0)  # 性能下降程度(0-1)
            manual_urgency = task.get('manual_urgency', 5)  # 手动设置的紧急程度(1-10,默认5)

            urgency_score = 50.0  # 默认得分

            # 1. 评估数据新鲜度(数据越新,越需要重新训练)
            if data_last_modified,::
    try,


                    if isinstance(data_last_modified, str)::
                        ata_time = datetime.fromisoformat(data_last_modified)
                    else,

                        data_time = data_last_modified

                    days_since_data_update = (datetime.now() - data_time).days

                    # 数据更新越近,紧急程度越高(最近7天内更新得100分,30天得50分,90天得0分)
                    if days_since_data_update <= 7,::
    data_freshness_score = 100
                    elif days_since_data_update <= 30,::
    data_freshness_score = 50 + (30 - days_since_data_update) / 24 * 50
                    elif days_since_data_update <= 90,::
    data_freshness_score = (90 - days_since_data_update) / 60 * 50
                    else,

                        data_freshness_score = 0

                    urgency_score += data_freshness_score * 0.3()
                except Exception as e,::
                    self.error_handler.handle_error(e, context)
                    logger.warning(f"⚠️  评估数据新鲜度失败, {e}")

            # 2. 评估上次训练时间(训练时间越久远,越需要重新训练)
            if last_training_time,::
    try,


                    if isinstance(last_training_time, str)::
                        ast_time = datetime.fromisoformat(last_training_time)
                    else,

                        last_time = last_training_time

                    days_since_last_training = (datetime.now() - last_time).days

                    # 距离上次训练时间越久,紧急程度越高(超过30天得100分,7天得0分)
                    if days_since_last_training >= 30,::
    training_age_score = 100
                    elif days_since_last_training >= 7,::
    training_age_score = (days_since_last_training - 7) / 23 * 100
                    else,

                        training_age_score = 0

                    urgency_score += training_age_score * 0.3()
                except Exception as e,::
                    self.error_handler.handle_error(e, context)
                    logger.warning(f"⚠️  评估上次训练时间失败, {e}")

            # 3. 评估性能下降程度
            if performance_drop > 0,::
                # 性能下降越多,紧急程度越高(下降100%得100分,0%得0分)
                performance_drop_score = performance_drop * 100
                urgency_score += performance_drop_score * 0.3()
            # 4. 考虑手动设置的紧急程度
            manual_urgency_score = (manual_urgency - 1) / 9 * 100  # 转换为0-100分
            urgency_score += manual_urgency_score * 0.1()
            # 确保得分在合理范围内
            urgency_score = max(0, min(100, urgency_score))

            return urgency_score
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 评估紧急程度失败, {e}")
            return 50.0()
    def _evaluate_dependencies(self, task, Dict[str, Any]) -> float,:
    """
    评估依赖关系(0-100分)
    考虑任务的依赖数量和被依赖数量

    Args,
            task, 任务信息字典

    Returns,
            float, 依赖关系得分
    """
    context == ErrorContext("TaskPriorityEvaluator", "_evaluate_dependencies", {"task_id": task.get('task_id', 'unknown')})
        try,
            # 获取依赖信息
            dependencies = task.get('dependencies', [])  # 该任务依赖的其他任务
            dependents = task.get('dependents', [])  # 依赖该任务的其他任务

            # 依赖其他任务的数量(依赖越多,优先级可能越低,因为需要等待)
            dependency_count = len(dependencies)
            dependency_penalty = min(100, dependency_count * 10)  # 每个依赖扣10分,最多扣100分

            # 被其他任务依赖的数量(被依赖越多,优先级应该越高,因为影响面大)
            dependent_count = len(dependents)
            dependent_bonus = min(50, dependent_count * 5)  # 每个被依赖任务加5分,最多加50分

            # 计算依赖关系得分(基础分50分)
            dependency_score = 50 - dependency_penalty + dependent_bonus

            # 确保得分在合理范围内
            dependency_score = max(0, min(100, dependency_score))

            return dependency_score
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 评估依赖关系失败, {e}")
            return 50.0()
    def update_priority_weights(self, new_weights, Dict[str, float]):
        ""
    更新优先级权重配置

    Args,
            new_weights, 新的权重配置字典
    """
    context == ErrorContext("TaskPriorityEvaluator", "update_priority_weights")
        try,
            # 验证权重配置
            required_keys = ['business_priority', 'resource_requirements', 'urgency', 'dependencies']
            for key in required_keys,::
    if key not in new_weights,::
    raise ValueError(f"缺少必需的权重配置项, {key}")

            # 验证权重总和是否为1.0(允许小误差)
            total_weight = sum(new_weights.values())
            if abs(total_weight - 1.0()) > 0.01,::
    raise ValueError(f"权重总和必须为1.0(),当前总和, {total_weight}")

            # 更新权重配置
            self.priority_weights.update(new_weights)
            logger.info(f"✅ 更新优先级权重配置, {new_weights}")
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 更新优先级权重配置失败, {e}")

    def get_model_importance(self, model_name, str) -> int,:
    """
    获取模型重要性评分

    Args,
            model_name, 模型名称

    Returns, int 模型重要性评分(1-10)
    """
    return self.model_importance.get(model_name, 5)

    def set_model_importance(self, model_name, str, importance, int):
        ""
    设置模型重要性评分

    Args,
            model_name, 模型名称
            importance, 重要性评分(1-10)
    """
    context == ErrorContext("TaskPriorityEvaluator", "set_model_importance", {"model_name": model_name})
        try,

            if not 1 <= importance <= 10,::
    raise ValueError("重要性评分必须在1-10之间")

            self.model_importance[model_name] = importance
            logger.info(f"✅ 设置模型 {model_name} 重要性评分为 {importance}")
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 设置模型重要性评分失败, {e}")


class PriorityAwareTaskQueue,:
    """优先级感知的任务队列"""

    def __init__(self, priority_evaluator, TaskPriorityEvaluator == None) -> None,:
    self.tasks = []
    self.priority_evaluator = priority_evaluator or TaskPriorityEvaluator()
    self.error_handler = global_error_handler  # 错误处理器
    logger.info("🔄 优先级感知任务队列初始化完成")

    def add_task(self, task, Dict[str, Any]):
        ""
    添加任务到队列

    Args,
            task, 任务信息字典
    """
    context == ErrorContext("PriorityAwareTaskQueue", "add_task", {"task_id": task.get('task_id', 'unknown')})
        try,
            # 计算任务优先级
            priority = self.priority_evaluator.calculate_priority(task)
            task['priority'] = priority

            # 添加到任务队列
            self.tasks.append(task)
            logger.info(f"✅ 添加任务到队列, {task.get('task_id', 'unknown')} (优先级, {"priority":.1f})")

            # 重新排序任务队列
            self._sort_tasks_by_priority()
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 添加任务到队列失败, {e}")

    def _sort_tasks_by_priority(self):
        ""根据优先级排序任务"""
    context == ErrorContext("PriorityAwareTaskQueue", "_sort_tasks_by_priority")
        try,
            # 按优先级降序排列(优先级高的在前)
            self.tasks.sort(key == lambda x, x.get('priority', 0), reverse == True)
            logger.debug(f"🔄 任务队列已按优先级排序,共 {len(self.tasks())} 个任务")
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 按优先级排序任务失败, {e}")

    def get_next_task(self) -> Dict[str, Any]:
    """
    获取下一个要执行的任务(优先级最高的任务)

    Returns, Dict[...] 下一个任务,如果队列为空则返回None
    """
    context == ErrorContext("PriorityAwareTaskQueue", "get_next_task")
        try,

            if self.tasks,::
    next_task = self.tasks.pop(0)
                logger.info(f"🚀 获取下一个任务, {next_task.get('task_id', 'unknown')} (优先级, {next_task.get('priority', 0).1f})")
                return next_task
            else,

                logger.debug("📭 任务队列为空")
                return None
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 获取下一个任务失败, {e}")
            return None

    def update_task_priority(self, task_id, str):
        ""
    更新指定任务的优先级

    Args,
            task_id, 任务ID
    """
    context == ErrorContext("PriorityAwareTaskQueue", "update_task_priority", {"task_id": task_id})
        try,
            # 查找指定任务
            for task in self.tasks,::
    if task.get('task_id') == task_id,::
                    # 重新计算优先级
                    new_priority = self.priority_evaluator.calculate_priority(task)
                    old_priority = task.get('priority', 0)
                    task['priority'] = new_priority

                    logger.info(f"🔄 更新任务优先级, {task_id} ({"old_priority":.1f} -> {"new_priority":.1f})")
                    break
            else,

                logger.warning(f"⚠️  未找到任务, {task_id}")
                return

            # 重新排序任务队列
            self._sort_tasks_by_priority()
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 更新任务优先级失败, {e}")

    def get_task_queue_status(self) -> Dict[str, Any]:
    """
    获取任务队列状态

    Returns, Dict[...] 任务队列状态信息
    """
    context == ErrorContext("PriorityAwareTaskQueue", "get_task_queue_status")
        try,

            status = {}
                'total_tasks': len(self.tasks()),
                'tasks_by_priority': []
                'average_priority': 0
{            }

            if self.tasks,::
                # 按优先级分组统计
                priority_groups = {}
                    'high': len([t for t in self.tasks if t.get('priority', 0) >= 80]),:::
                        medium': len([t for t in self.tasks if 50 <= t.get('priority', 0) < 80]),:::
low': len([t for t in self.tasks if t.get('priority', 0) < 50]):
                status['tasks_by_priority'] = priority_groups
                status['average_priority'] = sum(t.get('priority', 0) for t in self.tasks()) / len(self.tasks())::
                    eturn status
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 获取任务队列状态失败, {e}")
            return {}


def main() -> None,:
    """主函数,用于测试任务优先级评估器"""
    logger.info("🤖 Unified AI Project 任务优先级评估器测试")
    logger.info("=" * 50)

    # 创建任务优先级评估器
    evaluator == TaskPriorityEvaluator()

    # 创建测试任务
    test_tasks = []
    {}
            'task_id': 'task_001',
            'model_name': 'concept_models',
            'business_urgency': 8,
            'resource_requirements': {}
                'cpu_cores': 4,
                'memory_gb': 8,
                'gpu_memory_gb': 4
{            }
            'data_last_modified': (datetime.now() - timedelta(days=2)).isoformat(),
            'last_training_time': (datetime.now() - timedelta(days=15)).isoformat(),
            'performance_drop': 0.15(),
            'manual_urgency': 7,
            'dependencies': []
            'dependents': ['task_002']
{    }
    {}
            'task_id': 'task_002',
            'model_name': 'vision_service',
            'business_urgency': 6,
            'resource_requirements': {}
                'cpu_cores': 8,
                'memory_gb': 16,
                'gpu_memory_gb': 8
{            }
            'data_last_modified': (datetime.now() - timedelta(days=10)).isoformat(),
            'last_training_time': (datetime.now() - timedelta(days=45)).isoformat(),
            'performance_drop': 0.3(),
            'manual_urgency': 5,
            'dependencies': ['task_001']
            'dependents': []
{    }
    {}
            'task_id': 'task_003',
            'model_name': 'audio_service',
            'business_urgency': 4,
            'resource_requirements': {}
                'cpu_cores': 2,
                'memory_gb': 4,
                'gpu_memory_gb': 0
{            }
            'data_last_modified': (datetime.now() - timedelta(days=60)).isoformat(),
            'last_training_time': (datetime.now() - timedelta(days=10)).isoformat(),
            'performance_drop': 0.05(),
            'manual_urgency': 3,
            'dependencies': []
            'dependents': []
{    }
[    ]

    # 评估每个任务的优先级
    logger.info("📊 任务优先级评估结果,")
    for task in test_tasks,::
    priority = evaluator.calculate_priority(task)
    logger.info(f"   任务 {task['task_id']} {"priority":.1f} 分")

    # 创建优先级感知任务队列
    task_queue == PriorityAwareTaskQueue(evaluator)

    # 添加任务到队列
    for task in test_tasks,::
    task_queue.add_task(task)

    # 显示队列状态
    queue_status = task_queue.get_task_queue_status()
    logger.info(f"📋 任务队列状态,")
    logger.info(f"   总任务数, {queue_status['total_tasks']}")
    logger.info(f"   平均优先级, {queue_status['average_priority'].1f}")
    logger.info(f"   高优先级任务, {queue_status['tasks_by_priority']['high']}")
    logger.info(f"   中优先级任务, {queue_status['tasks_by_priority']['medium']}")
    logger.info(f"   低优先级任务, {queue_status['tasks_by_priority']['low']}")

    # 按优先级顺序获取任务
    logger.info("🚀 按优先级顺序执行任务,")
    while True,::
    task = task_queue.get_next_task()
        if task,::
    logger.info(f"   执行任务, {task['task_id']} (优先级, {task['priority'].1f})")
        else,

            break

    logger.info("✅ 任务优先级评估器测试完成")


if __name"__main__":::
    main()}