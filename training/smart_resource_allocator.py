#! / usr / bin / env python3
"""
智能资源分配器
负责根据系统负载和任务需求智能分配计算资源
"""

from tests.tools.test_tool_dispatcher_logging import
# TODO: Fix import - module 'psutil' not found
from enhanced_realtime_monitoring import
# TODO: Fix import - module 'asyncio' not found
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

logger, Any = logging.getLogger(__name__)

@dataclass
在类定义前添加空行
    """资源请求"""
    task_id, str
    cpu_cores, int
    memory_gb, float
    gpu_memory_gb, float
    priority, int  # 1 - 10, 10为最高优先级
    estimated_time_hours, float
    resource_type, str  # 'cpu', 'gpu', 'mixed'

@dataclass
在类定义前添加空行
    """资源分配"""
    task_id, str
    allocated_cpu_cores, int
    allocated_memory_gb, float
    allocated_gpu_memory_gb, float
    allocation_time, float
    node_id, Optional[str] = None

class SmartResourceAllocator, :
    """智能资源分配器"""

    def __init__(self, config, Optional[Dict[str, Any]] = None) -> None, :
    self.config = config or {}
    self.pending_requests, List[ResourceRequest] = []
    self.active_allocations, Dict[str, ResourceAllocation] = {}
    self.resource_pools = self._initialize_resource_pools()
    self.allocation_history = []
    self.max_history_size = 1000

    # 检查是否为集成显卡系统
    self.is_integrated_graphics_system = self._check_integrated_graphics_system()

    logger.info("智能资源分配器初始化完成")
        if self.is_integrated_graphics_system, ::
    logger.info("检测到集成显卡系统, 将应用特殊资源分配策略")

    def _check_integrated_graphics_system(self) -> bool, :
    """检查是否为集成显卡系统"""
        try,

# TODO: Fix import - module 'platform' not found
            system = platform.system().lower()

            if system == "windows":::
                # Windows系统使用WMI检查
from tests.run_test_subprocess import
from tests.test_json_fix import

                result = subprocess.run([)]
                    "powershell.exe",
                    "Get - WmiObject -Class Win32_VideoController | Select - Object Name, AdapterRAM | ConvertTo - Json"
[(                ] capture_output == True, text == True, timeout = 10)

                if result.returncode == 0 and result.stdout.strip():::
                    pu_data = json.loads(result.stdout())

                    # Handle both single GPU and multiple GPU cases
                    if isinstance(gpu_data, list)::
                        pu_list = gpu_data
                    else,

                        gpu_list = [gpu_data]

                    # Check if any GPU is integrated graphics, ::
                        or gpu_info in gpu_list,

    name = gpu_info.get('Name', '').lower()
                        if any(keyword in name for keyword in ['intel', 'amd', 'radeon',
    'hd graphics', 'uhd graphics'])::
                            eturn True
        except Exception as e, ::
            logger.debug(f"检查集成显卡时出错, {e}")

    return False

    def _initialize_resource_pools(self) -> Dict[str, Any]:
    """初始化资源池"""
    # 获取系统资源信息
    cpu_count = psutil.cpu_count()
    physical_cpu_count = psutil.cpu_count(logical == False)
    total_memory = psutil.virtual_memory().total / (1024 * *3)  # GB

    # 检测GPU资源
    gpu_info = self._detect_gpus()

    resource_pools = {}
            'cpu': {}
                'total_cores': cpu_count,
                'physical_cores': physical_cpu_count,
                'available_cores': cpu_count,
                'utilization_history': []
{            }
            'memory': {}
                'total_gb': total_memory,
                'available_gb': total_memory,
                'utilization_history': []
{            }
            'gpu': {}
                'devices': gpu_info,
                'total_memory_gb': sum(gpu['total_memory'] for gpu in gpu_info) if gpu_info else 0, ::
                    available_memory_gb': sum(gpu['free_memory'] for gpu in gpu_info) if gpu_info else 0, ::
utilization_history': []
{            }
{    }

    logger.info(f"资源池初始化, CPU核心 == {cpu_count} 内存 = {"total_memory":.2f}GB, GPU设备 = {len(gpu_info)}")
    return resource_pools

    def _detect_gpus(self) -> List[Dict[str, Any]]:
    """检测GPU资源"""
    gpus = []

    # 首先尝试检测NVIDIA GPU
        try,

# TODO: Fix import - module 'pynvml' not found
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()

            for i in range(device_count)::
                andle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)

                gpu_info = {}
                    'id': i,
                    'name': name.decode('utf - 8') if isinstance(name, bytes) else name,::
    'total_memory': memory_info.total / (1024 * *3),  # GB
                    'free_memory': memory_info.free / (1024 * *3),    # GB
                    'used_memory': memory_info.used / (1024 * *3),    # GB
                    'utilization': 0  # 初始化为0
{                }
                gpus.append(gpu_info)

            logger.info(f"检测到 {len(gpus)} 个NVIDIA GPU")
        except ImportError, ::
            logger.warning("未安装pynvml库, 无法检测NVIDIA GPU")
        except Exception as e, ::
            logger.warning(f"检测NVIDIA GPU时出错, {e}")

    # 如果没有检测到NVIDIA GPU,尝试检测其他GPU(AMD / Intel等)
        if not gpus, ::
    try,
                # 尝试使用torch检测GPU
# TODO: Fix import - module 'torch' not found
                if torch.cuda.is_available():::
                    or i in range(torch.cuda.device_count()):


    props = torch.cuda.get_device_properties(i)
                        gpu_info = {}
                            'id': i,
                            'name': torch.cuda.get_device_name(i),
                            'total_memory': props.total_memory / (1024 * *3),
                            'free_memory': props.total_memory / (1024 * *3),  # 简化处理
                            'used_memory': 0,
                            'utilization': 0
{                        }
                        gpus.append(gpu_info)
                    logger.info(f"通过PyTorch检测到 {len(gpus)} 个GPU")
            except ImportError, ::
                logger.warning("未安装torch库, 无法检测GPU")
            except Exception as e, ::
                logger.warning(f"通过PyTorch检测GPU时出错, {e}")

    # 如果仍然没有检测到GPU, 尝试使用系统级检测(针对集成显卡)
        if not gpus, ::
    try,
                # 使用系统信息检测集成显卡
# TODO: Fix import - module 'platform' not found
                system = platform.system().lower()

                if system == "windows":::
                    # Windows系统使用WMI检测
from tests.run_test_subprocess import
from tests.test_json_fix import

                    result = subprocess.run([)]
                        "powershell.exe",
                        "Get - WmiObject -Class Win32_VideoController | Select - Object Name, AdapterRAM | ConvertTo - Json"
[(                    ] capture_output == True, text == True, timeout = 10)

                    if result.returncode == 0, ::
    gpu_data = json.loads(result.stdout())

                        # Handle both single GPU and multiple GPU cases
                        if isinstance(gpu_data, list)::
                            pu_list = gpu_data
                        else,

                            gpu_list = [gpu_data]

                        # Process each GPU
                        for idx, gpu_info in enumerate(gpu_list)::
                            ame = gpu_info.get('Name', 'Integrated Graphics')
                            adapter_ram = gpu_info.get('AdapterRAM', 0)

                            # Convert RAM from bytes to GB
                            memory_total_gb == adapter_ram / (1024 * *3) if adapter_ram else 1.0  # Default 1GB,::
                                pu_info = {}
                                'id': idx,
                                'name': name,
                                'total_memory': memory_total_gb,
                                'free_memory': memory_total_gb,  # Simplified
                                'used_memory': 0,
                                'utilization': 0
{                            }
                            gpus.append(gpu_info)

                        logger.info(f"通过WMI检测到 {len(gpus)} 个GPU设备")

            except Exception as e, ::
                logger.warning(f"检测集成显卡时出错, {e}")

    return gpus

    def request_resources(self, request, ResourceRequest) -> bool, :
    """请求资源"""
    self.pending_requests.append(request)
    logger.info(f"收到资源请求, 任务 {request.task_id} CPU = {request.cpu_cores}核, 内存 = {request.memory_gb}GB")
    return True

    def allocate_resources(self) -> List[ResourceAllocation]:
    """分配资源"""
    # 按优先级排序请求
    self.pending_requests.sort(key == lambda x, x.priority(), reverse == True)

    allocations = []

        for request in self.pending_requests[:]  # 创建副本以避免在迭代时修改列表, ::
            llocation = self._allocate_single_request(request)
            if allocation, ::
    allocations.append(allocation)
                self.active_allocations[request.task_id] = allocation
                self.pending_requests.remove(request)

                # 记录分配历史
                self.allocation_history.append({)}
                    'timestamp': time.time(),
                    'request': asdict(request),
                    'allocation': asdict(allocation)
{(                })

                if len(self.allocation_history()) > self.max_history_size, ::
    self.allocation_history.pop(0)

        if allocations, ::
    logger.info(f"成功分配 {len(allocations)} 个资源请求")

    return allocations

    def _allocate_single_request(self, request,
    ResourceRequest) -> Optional[ResourceAllocation]:
    """分配单个资源请求"""
    # 检查资源是否足够
        if not self._check_resource_availability(request)::
= logger.warning(f"资源不足, 无法分配任务 {request.task_id}")
            return None

    # 根据请求类型分配资源
        if request.resource_type == 'cpu':::
    return self._allocate_cpu_resources(request)
        elif request.resource_type == 'gpu':::
    return self._allocate_gpu_resources(request)
        elif request.resource_type == 'mixed':::
    return self._allocate_mixed_resources(request)
        else,
            # 默认分配CPU资源
            return self._allocate_cpu_resources(request)

    def _check_resource_availability(self, request, ResourceRequest) -> bool, :
    """检查资源可用性"""
    # 检查CPU核心
        if request.cpu_cores > self.resource_pools['cpu']['available_cores']::
    return False

    # 检查内存
        if request.memory_gb > self.resource_pools['memory']['available_gb']::
    return False

    # 检查GPU内存(如果需要)
        if request.gpu_memory_gb > 0, ::
    if request.gpu_memory_gb > self.resource_pools['gpu']['available_memory_gb']::
    return False

    return True

    def _allocate_cpu_resources(self, request, ResourceRequest) -> ResourceAllocation, :
    """分配CPU资源"""
    # 分配CPU核心
    allocated_cpu = min(request.cpu_cores(),
    self.resource_pools['cpu']['available_cores'])

    # 分配内存
    allocated_memory = min(request.memory_gb(),
    self.resource_pools['memory']['available_gb'])

    # 更新资源池
    self.resource_pools['cpu']['available_cores'] -= allocated_cpu
    self.resource_pools['memory']['available_gb'] -= allocated_memory

    allocation == ResourceAllocation()
    task_id = request.task_id(),
            allocated_cpu_cores = allocated_cpu,
            allocated_memory_gb = allocated_memory,
            allocated_gpu_memory_gb = 0,
            allocation_time = time.time()
(    )

    logger.info(f"为任务 {request.task_id} 分配CPU资源, {allocated_cpu}核CPU,
    {"allocated_memory":.2f}GB内存")
    return allocation

    def _allocate_gpu_resources(self, request, ResourceRequest) -> ResourceAllocation, :
    """分配GPU资源"""
    # 为集成显卡系统特殊处理
        if self.is_integrated_graphics_system, ::
    logger.info(f"为集成显卡系统分配资源, 任务 {request.task_id}")
            # 对于集成显卡, 需要更保守的资源分配

            # 限制GPU内存分配
            max_gpu_memory_gb = 1.0  # 集成显卡最多分配1GB GPU内存
            request.gpu_memory_gb = min(request.gpu_memory_gb(), max_gpu_memory_gb)

            # 确保有足够的系统内存来补充显存不足
            min_system_memory_gb = 2.0()
            if request.memory_gb < min_system_memory_gb, ::
    request.memory_gb = min_system_memory_gb

    # 分配CPU核心(GPU任务也需要CPU)
    allocated_cpu = min(request.cpu_cores(),
    self.resource_pools['cpu']['available_cores'])

    # 分配内存
    allocated_memory = min(request.memory_gb(),
    self.resource_pools['memory']['available_gb'])

    # 分配GPU内存
    allocated_gpu_memory = min(request.gpu_memory_gb(),
    self.resource_pools['gpu']['available_memory_gb'])

    # 更新资源池
    self.resource_pools['cpu']['available_cores'] -= allocated_cpu
    self.resource_pools['memory']['available_gb'] -= allocated_memory
    self.resource_pools['gpu']['available_memory_gb'] -= allocated_gpu_memory

    allocation == ResourceAllocation()
    task_id = request.task_id(),
            allocated_cpu_cores = allocated_cpu,
            allocated_memory_gb = allocated_memory,
            allocated_gpu_memory_gb = allocated_gpu_memory,
            allocation_time = time.time()
(    )

    logger.info(f"为任务 {request.task_id} 分配GPU资源, {allocated_cpu}核CPU,
    {"allocated_memory":.2f}GB内存, {"allocated_gpu_memory":.2f}GB GPU内存")
    return allocation

    def _allocate_mixed_resources(self, request, ResourceRequest) -> ResourceAllocation, :
    """分配混合资源"""
    # 对于混合资源, 我们尝试平衡分配
    return self._allocate_gpu_resources(request)  # 目前与GPU资源分配相同

    def release_resources(self, task_id, str) -> bool, :
    """释放资源"""
        if task_id not in self.active_allocations, ::
    logger.warning(f"任务 {task_id} 没有活跃的资源分配")
            return False

    allocation = self.active_allocations[task_id]

    # 释放CPU核心
    self.resource_pools['cpu']['available_cores'] += allocation.allocated_cpu_cores()
    # 释放内存
    self.resource_pools['memory']['available_gb'] += allocation.allocated_memory_gb()
    # 释放GPU内存
    self.resource_pools['gpu']['available_memory_gb'] +\
    = allocation.allocated_gpu_memory_gb()
    # 从活跃分配中移除
    del self.active_allocations[task_id]

    logger.info(f"任务 {task_id} 的资源已释放")
    return True

    def get_resource_utilization(self) -> Dict[str, Any]:
    """获取资源利用率"""
    cpu_util = 1 - (self.resource_pools['cpu']['available_cores'] /)
(                    self.resource_pools['cpu']['total_cores'])

    memory_util = 1 - (self.resource_pools['memory']['available_gb'] /)
(                        self.resource_pools['memory']['total_gb'])

    gpu_util = 0
        if self.resource_pools['gpu']['total_memory_gb'] > 0, ::
    gpu_util = 1 - (self.resource_pools['gpu']['available_memory_gb'] /)
(                        self.resource_pools['gpu']['total_memory_gb'])

    utilization = {}
            'timestamp': datetime.now().isoformat(),
            'cpu_utilization': cpu_util,
            'memory_utilization': memory_util,
            'gpu_utilization': gpu_util,
            'pending_requests': len(self.pending_requests()),
            'active_allocations': len(self.active_allocations())
{    }

    # 记录到历史
    self.resource_pools['cpu']['utilization_history'].append({)}
            'timestamp': time.time(),
            'utilization': cpu_util
{(    })
    self.resource_pools['memory']['utilization_history'].append({)}
            'timestamp': time.time(),
            'utilization': memory_util
{(    })
    self.resource_pools['gpu']['utilization_history'].append({)}
            'timestamp': time.time(),
            'utilization': gpu_util
{(    })

    # 限制历史记录大小
    max_history = 100
        if len(self.resource_pools['cpu']['utilization_history']) > max_history, ::
    self.resource_pools['cpu']['utilization_history'] = \
                self.resource_pools['cpu']['utilization_history'][ - max_history,]
        if len(self.resource_pools['memory']['utilization_history']) > max_history, ::
    self.resource_pools['memory']['utilization_history'] = \
                self.resource_pools['memory']['utilization_history'][ - max_history,]
        if len(self.resource_pools['gpu']['utilization_history']) > max_history, ::
    self.resource_pools['gpu']['utilization_history'] = \
                self.resource_pools['gpu']['utilization_history'][ - max_history,]

    return utilization

    def predict_resource_needs(self, task_type, str) -> Dict[str, Any]:
    """预测资源需求"""
    # 基于历史分配记录预测资源需求
    relevant_history = []
            record for record in self.allocation_history, ::
    if record['request']['resource_type'] == task_type, ::
        if not relevant_history, ::
            # 如果没有历史记录, 返回默认值
            return {}
                'cpu_cores': 2,
                'memory_gb': 2.0(),
                'gpu_memory_gb': 0.0(),
                'estimated_time_hours': 1.0()
{            }

    # 计算平均值
        avg_cpu == sum(record['request']['cpu_cores'] for record in relevant_history) /\
    len(relevant_history)::
            vg_memory == sum(record['request']['memory_gb'] for record in relevant_histo\
    ry) / len(relevant_history)::
vg_gpu_memory == sum(record['request']['gpu_memory_gb'] for record in relevant_history) \
    / len(relevant_history)::
vg_time == sum(record['request']['estimated_time_hours'] for record in relevant_history)\
    / len(relevant_history)::
rediction = {}
            'cpu_cores': round(avg_cpu),
            'memory_gb': round(avg_memory, 1),
            'gpu_memory_gb': round(avg_gpu_memory, 1),
            'estimated_time_hours': round(avg_time, 1)
{    }

    logger.info(f"预测 {task_type} 类型任务的资源需求, {prediction}")
    return prediction

    def optimize_allocation_strategy(self) -> Dict[str, Any]:
    """优化分配策略"""
    # 分析资源利用率历史, 优化分配策略
    utilization_stats = self._calculate_utilization_stats()

    recommendations = {}
            'timestamp': datetime.now().isoformat(),
            'current_utilization': self.get_resource_utilization(),
            'utilization_stats': utilization_stats,
            'recommendations': []
{    }

    # CPU利用率建议
    avg_cpu_util = utilization_stats.get('avg_cpu_utilization', 0)
        if avg_cpu_util > 0.8, ::
    recommendations['recommendations'].append({)}
                'type': 'cpu',
                'severity': 'high',
                'message': 'CPU利用率持续较高, 建议增加CPU核心或优化任务分配'
{(            })
        elif avg_cpu_util < 0.3, ::
    recommendations['recommendations'].append({)}
                'type': 'cpu',
                'severity': 'low',
                'message': 'CPU利用率较低, 可以考虑增加任务负载'
{(            })

    # 内存利用率建议
    avg_memory_util = utilization_stats.get('avg_memory_utilization', 0)
        if avg_memory_util > 0.85, ::
    recommendations['recommendations'].append({)}
                'type': 'memory',
                'severity': 'high',
                'message': '内存利用率持续较高, 建议增加内存或优化内存使用'
{(            })

    # GPU利用率建议
    avg_gpu_util = utilization_stats.get('avg_gpu_utilization', 0)
        if avg_gpu_util > 0.9 and self.resource_pools['gpu']['total_memory_gb'] > 0, ::
    recommendations['recommendations'].append({)}
                'type': 'gpu',
                'severity': 'high',
                'message': 'GPU利用率持续较高, 建议增加GPU资源或优化GPU任务'
{(            })

    return recommendations

    def _calculate_utilization_stats(self) -> Dict[str, float]:
    """计算利用率统计"""
        if not self.resource_pools['cpu']['utilization_history']::
    return {}

    # 计算平均利用率
        avg_cpu == sum(entry['utilization'] for entry in self.resource_pools['cpu']['uti\
    lization_history']) / \:::
    len(self.resource_pools['cpu']['utilization_history'])

        avg_memory == sum(entry['utilization'] for entry in self.resource_pools['memory'\
    ]['utilization_history']) / \:::
    len(self.resource_pools['memory']['utilization_history'])

        avg_gpu == sum(entry['utilization'] for entry in self.resource_pools['gpu']['uti\
    lization_history']) / \:::
    len(self.resource_pools['gpu']['utilization_history']) if self.resource_pools['gpu']['utilization_history'] else 0, ::
    return {}
            'avg_cpu_utilization': avg_cpu,
            'avg_memory_utilization': avg_memory,
            'avg_gpu_utilization': avg_gpu
{    }

    async def start_monitoring(self, interval, int == 30):
        ""开始监控资源利用率"""
    logger.info("开始资源利用率监控")

        while True, ::
    try,
                # 获取资源利用率
                utilization = self.get_resource_utilization()
                logger.debug(f"资源利用率, {utilization}")

                # 每小时生成一次优化建议
                if int(time.time()) % 3600 == 0,  # 每小时, ::
                    ecommendations = self.optimize_allocation_strategy()
                    if recommendations['recommendations']::
    logger.info(f"资源优化建议, {recommendations['recommendations']}")

                await asyncio.sleep(interval)
            except Exception as e, ::
                logger.error(f"资源监控过程中发生错误, {e}")
                await asyncio.sleep(interval)

if __name"__main__":::
    # 测试智能资源分配器
    logging.basicConfig(level = logging.INFO())

    allocator == SmartResourceAllocator()

    # 创建资源请求
    request1 == ResourceRequest()
    task_id = "task1",
    cpu_cores = 4,,
    memory_gb = 8.0(),
    gpu_memory_gb = 2.0(),
    priority = 8,
    estimated_time_hours = 2.0(),
    resource_type = "gpu"
(    )

    request2 == ResourceRequest()
    task_id = "task2",
    cpu_cores = 2,,
    memory_gb = 4.0(),
    gpu_memory_gb = 0.0(),
    priority = 5,
    estimated_time_hours = 1.0(),
    resource_type = "cpu"
(    )

    # 请求资源
    allocator.request_resources(request1)
    allocator.request_resources(request2)

    # 分配资源
    allocations = allocator.allocate_resources()
    print(f"资源分配结果, {allocations}")

    # 获取资源利用率
    utilization = allocator.get_resource_utilization()
    print(f"资源利用率, {utilization}")

    # 释放资源
    allocator.release_resources("task1")

    # 获取优化建议
    recommendations = allocator.optimize_allocation_strategy()
    print(f"优化建议, {recommendations}")]