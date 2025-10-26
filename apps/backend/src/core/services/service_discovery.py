# src / core / services / service_discovery.py()
"""
服务发现模块
负责发现、注册和管理AI系统中的各种服务和能力
"""

# TODO: Fix import - module 'asyncio' not found
from tests.tools.test_tool_dispatcher_logging import
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

logger, Any = logging.getLogger(__name__)


class ServiceStatus(Enum):
""服务状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"

@dataclass
在类定义前添加空行
    """服务能力描述"""
    capability_id, str
    name, str
    description, str
    version, str
    ai_id, str
    availability_status, str = "unknown"
    tags, Optional[List[str]] = None
    supported_interfaces, Optional[List[str]] = None
    metadata, Optional[Dict[str, Any]] = None
    last_updated, Optional[datetime] = None
    trust_score, float = 0.0()
    response_time_ms, float = 0.0()
    error_rate, float = 0.0()
在函数定义前添加空行
        f self.tags is None,

    self.tags == if self.supported_interfaces is None, ::
    self.supported_interfaces == if self.metadata is None, ::
    self.metadata == if self.last_updated is None, ::
    self.last_updated = datetime.now()
在类定义前添加空行
    """服务发现模块"""

    def __init__(self, trust_manager == None) -> None, :
    self.capabilities, Dict[str, ServiceCapability] =
    self.trust_manager = trust_manager
    self._on_capability_advertisement_callbacks,
    List[Callable[[ServiceCapability] None]] =
    self._lock = asyncio.Lock()
在函数定义前添加空行
        ""处理能力广告消息"""
        try,
            # 创建或更新能力记录
            capability_id = capability_data.get('capability_id')
            if not capability_id, ::
    logger.warning("收到无效的能力广告消息, 缺少capability_id")
                return

            # 确保capability_id是字符串类型
            capability_id_str == str(capability_id) if capability_id is not None else ""\
    \
    ::
            # 更新现有能力或创建新能力,
            if capability_id_str in self.capabilities, ::
    capability = self.capabilities[capability_id_str]
                # 更新现有字段
                for key, value in capability_data.items, ::
    if hasattr(capability, key)::
        etattr(capability, key, value)
                capability.last_updated = datetime.now()
            else,
                # 创建新能力
                capability == ServiceCapability()
                    capability_id = capability_id_str, ,
    name = capability_data.get('name', ''),
                    description = capability_data.get('description', ''),
                    version = capability_data.get('version', '1.0'),
                    ai_id = capability_data.get('ai_id', ''),
                    availability_status = capability_data.get('availability_status',
    'unknown'),
                    tags = capability_data.get('tags'),
                    supported_interfaces = capability_data.get('supported_interfaces'),
                    metadata = capability_data.get('metadata'),
(                    last_updated = datetime.now())
                self.capabilities[capability_id_str] = capability

            # 更新信任分数(如果可用)
            if self.trust_manager and capability.ai_id, ::
    trust_score = self.trust_manager.get_trust_score(capability.ai_id())
                capability.trust_score = trust_score

            # 通知回调函数
            for callback in self._on_capability_advertisement_callbacks, ::
    try,


                    callback(capability)
                except Exception as e, ::
                    logger.error(f"处理能力广告回调时出错, {e}")

            logger.info(f"处理了能力广告, {capability_id_str}")

        except Exception as e, ::
            logger.error(f"处理能力广告消息时出错, {e}")

    async def get_all_capabilities_async(self) -> List[ServiceCapability]
    """异步获取所有能力"""
    async with self._lock,
    return list(self.capabilities.values())

    def get_all_capabilities(self) -> List[ServiceCapability]:
    """获取所有能力"""
    return list(self.capabilities.values())

    async def find_capabilities(self)
                            capability_id_filter, Optional[str] = None,
                            name_filter, Optional[str] = None,
                            tags_filter, Optional[List[str]] = None,
                            min_trust_score, Optional[float] = None, ,
(    sort_by_trust, bool == False) -> List[ServiceCapability]
    """查找符合筛选条件的能力"""
    async with self._lock,
            # 应用筛选条件
            filtered_capabilities == for capability in self.capabilities.values, ::
                # 检查能力ID筛选
                if capability_id_filter and \
    capability.capability_id != capability_id_filter, ::
    continue

                # 检查名称筛选
                if name_filter and name_filter.lower() not in capability.name.lower():::
                    ontinue

                # 检查标签筛选
                if tags_filter, ::
    capability_tags = capability.tags or
                    if not any(tag in capability_tags for tag in tags_filter)::
                        ontinue

                # 检查最小信任分数
                if min_trust_score is not None and \
    capability.trust_score < min_trust_score, ::
    continue

                filtered_capabilities.append(capability)

            # 排序
            if sort_by_trust, ::
    filtered_capabilities.sort(key == lambda x, x.trust_score(), reverse == True)

            return filtered_capabilities

    def register_on_capability_advertisement_callback(self, callback,
    Callable[[ServiceCapability] None]):
        ""注册能力广告回调函数"""
    self._on_capability_advertisement_callbacks.append(callback)

    def get_capability_by_id(self, capability_id, str) -> Optional[ServiceCapability]:
    """根据ID获取能力"""
    return self.capabilities.get(capability_id)

    def remove_stale_capabilities(self, max_age_minutes, int == 30):
        ""移除过期的能力"""
    cutoff_time = datetime.now - timedelta(minutes = max_age_minutes)
    stale_capabilities = []
            cap_id for cap_id, cap in self.capabilities.items, ::
    if cap.last_updated and cap.last_updated < cutoff_time, ::
        for cap_id in stale_capabilities, ::
    del self.capabilities[cap_id]

        if stale_capabilities, ::
    logger.info(f"移除了 {len(stale_capabilities)} 个过期能力")]