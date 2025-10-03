#!/usr/bin/env python3
"""
HSP协议性能优化器
负责优化HSP协议的消息处理效率，减少网络延迟和带宽使用
"""

import asyncio
import logging
import time
import json
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime

logger: Any = logging.getLogger(__name__)

# 定义类型别名以避免使用 Any
MessageData = Dict[str, Union[str, int, float, bool, List[Any], Dict[str, Any], None]]
ConfigDict = Dict[str, Union[int, bool, str]]
CacheEntry = Dict[str, Union[MessageData, float]]
NetworkStats = Dict[str, int]

@dataclass
class MessageMetrics:
    """消息指标"""
    message_id: str
    message_type: str
    size_bytes: int
    processing_time_ms: float
    timestamp: float
    success: bool

class HSPPerformanceOptimizer:
    """HSP协议性能优化器"""

    def __init__(self, config: Optional[ConfigDict] = None) -> None:
    self.config: ConfigDict = config or
    self.message_cache: Dict[str, CacheEntry] =   # 消息缓存
    self.cache_ttl: int = self._get_int_config('cache_ttl', 300)  # 缓存有效期（秒）
    self.batch_send_enabled: bool = self._get_bool_config('batch_send_enabled', True)  # 批量发送
    self.batch_size: int = self._get_int_config('batch_size', 10)  # 批量大小
    self.compression_enabled: bool = self._get_bool_config('compression_enabled', True)  # 压缩
    self.message_metrics: deque[MessageMetrics] = deque(maxlen=1000)  # 消息指标历史
    self.message_queue: List[Dict[str, MessageData]] =   # 消息队列
    self.last_batch_send: float = time.time
    self.network_stats: NetworkStats = {
            'messages_sent': 0,
            'messages_received': 0,
            'bytes_sent': 0,
            'bytes_received': 0,
            'compression_savings': 0
    }

    logger.info("HSP协议性能优化器初始化完成")

    def _get_int_config(self, key: str, default: int) -> int:
    """获取整数配置值"""
    value = self.config.get(key, default)
        if isinstance(value, int)

    return value
        elif isinstance(value, str)

    try:


                return int(value)
            except ValueError:

                return default
        elif isinstance(value, bool)

    return int(value)
        else:

            return default

    def _get_bool_config(self, key: str, default: bool) -> bool:
    """获取布尔配置值"""
    value = self.config.get(key, default)
        if isinstance(value, bool)

    return value
        elif isinstance(value, int)

    return bool(value)
        elif isinstance(value, str)

    return value.lower in ('true', '1', 'yes', 'on')
        else:

            return default

    def cache_message(self, message_id: str, message: MessageData, ttl: Optional[int] = None)
    """缓存消息"""
    cache_ttl = ttl or self.cache_ttl
    self.message_cache[message_id] = {
            'message': message,
            'timestamp': time.time,
            'expires_at': time.time + float(cache_ttl)
    }

    logger.debug(f"消息已缓存: {message_id}")

    def get_cached_message(self, message_id: str) -> Optional[MessageData]:
    """获取缓存的消息"""
        if message_id in self.message_cache:

    cached = self.message_cache[message_id]
            # 检查缓存是否过期
            expires_at = cached.get('expires_at')
            if isinstance(expires_at, (int, float)) and time.time < expires_at:

    message = cached.get('message')
                if isinstance(message, dict)

    logger.debug(f"从缓存获取消息: {message_id}")
                    return message
                else:
                    # 移除无效缓存
                    del self.message_cache[message_id]
                    logger.debug(f"缓存消息无效并移除: {message_id}")
            else:
                # 移除过期缓存
                del self.message_cache[message_id]
                logger.debug(f"缓存消息已过期并移除: {message_id}")

    return None

    def clean_expired_cache(self)
    """清理过期缓存"""
    current_time = time.time
    expired_keys =

        for key, value in self.message_cache.items:


    expires_at = value.get('expires_at')
            if isinstance(expires_at, (int, float)) and current_time >= expires_at:

    expired_keys.append(key)

        for key in expired_keys:


    del self.message_cache[key]

        if expired_keys:


    logger.debug(f"清理了 {len(expired_keys)} 个过期缓存")

    async def batch_send_messages(self, send_callback: Callable[[List[Dict[str, MessageData]]], Awaitable[None]])
    """批量发送消息"""
        if not self.batch_send_enabled or not self.message_queue:

    return

    # 检查是否应该发送批量消息
    current_time = time.time
        if (len(self.message_queue) >= self.batch_size or :

    current_time - self.last_batch_send >= 1.0):  # 每秒至少发送一次

            # 发送批量消息
            batch_messages = self.message_queue[:self.batch_size]
            self.message_queue = self.message_queue[self.batch_size:]

            try:


                _ = await send_callback(batch_messages)
                self.network_stats['messages_sent'] += len(batch_messages)
                self.last_batch_send = current_time
                logger.debug(f"批量发送 {len(batch_messages)} 条消息")
            except Exception as e:

                logger.error(f"批量发送消息失败: {e}")
                # 将消息重新加入队列
                self.message_queue = batch_messages + self.message_queue

    def add_message_to_batch(self, message_data: Dict[str, MessageData])
    """将消息添加到批处理队列"""
        if self.batch_send_enabled:

    self.message_queue.append(message_data)
            logger.debug(f"消息已添加到批处理队列，当前队列大小: {len(self.message_queue)}")
        else:

            logger.warning("批处理已禁用，消息未添加到队列")

    def compress_message(self, message: MessageData) -> bytes:
    """压缩消息"""
        if not self.compression_enabled:

    return json.dumps(message).encode('utf-8')

        try:


            import zlib
            json_str = json.dumps(message, ensure_ascii=False)
            compressed = zlib.compress(json_str.encode('utf-8'))

            # 计算压缩节省的字节数
            original_size = len(json_str.encode('utf-8'))
            compressed_size = len(compressed)
            savings = original_size - compressed_size
            self.network_stats['compression_savings'] += savings

            logger.debug(f"消息压缩完成: {original_size} -> {compressed_size} 字节 (节省 {savings} 字节)")
            return compressed
        except Exception as e:

            logger.error(f"消息压缩失败: {e}")
            return json.dumps(message).encode('utf-8')

    def decompress_message(self, compressed_data: bytes) -> MessageData:
    """解压缩消息"""
        try:

            import zlib
            decompressed = zlib.decompress(compressed_data)
            message: MessageData = json.loads(decompressed.decode('utf-8'))
            return message
        except Exception as e:

            logger.error(f"消息解压缩失败: {e}")
            # 如果解压缩失败，假设数据未压缩
            try:

                result: MessageData = json.loads(compressed_data.decode('utf-8'))
                return result
            except:
                raise ValueError("无法解码消息数据")

    def record_message_metrics(self, metrics: MessageMetrics)
    """记录消息指标"""
    self.message_metrics.append(metrics)
    logger.debug(f"记录消息指标: {metrics.message_id}")

    def get_performance_stats(self) -> Dict[str, Union[str, int, float, NetworkStats, Dict[str, Any]]]:
    """获取性能统计信息"""
        if not self.message_metrics:

    return

    # 计算平均处理时间
        total_time = sum(m.processing_time_ms for m in self.message_metrics)
    avg_processing_time = total_time / len(self.message_metrics)

    # 计算成功率
        successful_messages = sum(1 for m in self.message_metrics if m.success)
    success_rate = successful_messages / len(self.message_metrics)

    # 按消息类型统计
    type_stats: Dict[str, List[MessageMetrics]] = defaultdict(list)
        for m in self.message_metrics:

    _ = type_stats[m.message_type].append(m)

    type_performance: Dict[str, Dict[str, Union[float, int]]] =
        for msg_type, metrics_list in type_stats.items:

    avg_time = sum(m.processing_time_ms for m in metrics_list) / len(metrics_list)
    success_count = sum(1 for m in metrics_list if m.success)
    type_success_rate = success_count / len(metrics_list)

            type_performance[msg_type] = {
                'avg_processing_time_ms': avg_time,
                'success_rate': type_success_rate,
                'message_count': len(metrics_list)
            }

    stats: Dict[str, Union[str, int, float, NetworkStats, Dict[str, Any]]] = {
            'timestamp': datetime.now.isoformat,
            'total_messages': len(self.message_metrics),
            'avg_processing_time_ms': avg_processing_time,
            'success_rate': success_rate,
            'network_stats': self.network_stats,
            'message_type_performance': type_performance,
            'cache_stats': {
                'cached_messages': len(self.message_cache),
                'cache_hit_rate': self._calculate_cache_hit_rate
            }
    }

    return stats

    def _calculate_cache_hit_rate(self) -> float:
    """计算缓存命中率"""
    # 这里需要实现实际的缓存命中率计算逻辑
    # 为了示例，我们返回一个模拟值
    return 0.85

    async def optimize_message_routing(self, message: MessageData) -> Dict[str, Union[bytes, bool, str]]:
    """优化消息路由"""
    # 分析消息内容，优化路由路径
    message_type = message.get('message_type', 'unknown')
        if not isinstance(message_type, str)

    message_type = 'unknown'

    # 根据消息类型优化处理
        if message_type in ['HSP::Fact_v0.1', 'HSP::CapabilityAdvertisement_v0.1']:
            # 对于事实和能力广告消息，可以缓存
            message_id = message.get('message_id')
            if isinstance(message_id, str)

    self.cache_message(message_id, message)

    # 压缩消息
    compressed_message = self.compress_message(message)

    # 如果启用了批处理，将消息添加到队列
        if self.batch_send_enabled:
            # 创建符合类型要求的消息数据
            message_data_entry: MessageData = {
                'routing_info': f'optimized_for_{message_type}'
            }
            message_data: Dict[str, MessageData] = {
                'original_message': message_data_entry
            }:
    self.add_message_to_batch(message_data)

    logger.debug(f"消息路由优化完成: {message_type}")
    return {
            'compressed_data': compressed_message,
            'should_batch': self.batch_send_enabled,
            'message_type': message_type
    }

    def get_network_efficiency_report(self) -> Dict[str, Union[str, Dict[str, Union[float, List[str]]], List[str]]]:
    """获取网络效率报告"""
    stats = self.get_performance_stats

        if not stats:


    return

    # 计算网络效率指标
    network_stats = stats.get('network_stats', )
        if not isinstance(network_stats, dict)

    network_stats =

    total_messages = stats.get('total_messages', 0)
        if not isinstance(total_messages, (int, float)):

    total_messages = 0

    bottlenecks = self._identify_bottlenecks(stats)
    recommendations = self._generate_optimization_recommendations(stats)

    # 计算平均消息大小，确保返回正确的类型
    avg_message_size: float = 0.0
        if total_messages > 0:

    bytes_sent = network_stats.get('bytes_sent', 0)
            if isinstance(bytes_sent, (int, float)):

    avg_message_size = bytes_sent / total_messages

    # 确保bottlenecks是正确的类型
    typed_bottlenecks: List[str] =
        for item in bottlenecks:

    if isinstance(item, str)


    typed_bottlenecks.append(item)

    # 确保recommendations是正确的类型，转换为字符串列表
    recommendation_strings: List[str] =
        for rec in recommendations:

    if isinstance(rec, dict)
                # 将字典转换为字符串表示
                rec_str = f"{rec.get('type', 'unknown')}: {rec.get('message', 'no message')}"
                recommendation_strings.append(rec_str)

    # 修复类型声明，确保与实际返回的类型匹配
    efficiency_metrics: Dict[str, Union[float, List[str]]] = {
            'messages_per_second': total_messages / 60 if total_messages > 0 else 0,  # 假设统计周期为60秒
            'average_message_size_bytes': avg_message_size,
            'compression_ratio': self._calculate_compression_ratio,
            'cache_efficiency': self._get_cache_efficiency(stats)
    }

    report: Dict[str, Union[str, Dict[str, Union[float, List[str]]], List[str]]] = {
            'timestamp': datetime.now.isoformat,
            'efficiency_metrics': efficiency_metrics,
            'bottlenecks': typed_bottlenecks,
            'recommendations': recommendation_strings
    }

    return report

    def _get_cache_efficiency(self, stats: Dict[str, Union[str, int, float, NetworkStats, Dict[str, Any]]]) -> float:
    """获取缓存效率"""
    cache_stats = stats.get('cache_stats', )
        if isinstance(cache_stats, dict)

    cache_hit_rate = cache_stats.get('cache_hit_rate', 0)
            if isinstance(cache_hit_rate, (int, float)):

    return cache_hit_rate
    return 0.0

    def _calculate_compression_ratio(self) -> float:
    """计算压缩比率"""
    total_sent = self.network_stats.get('bytes_sent', 0)
    compression_savings = self.network_stats.get('compression_savings', 0)

        if total_sent == 0:


    return 0

    # 原始大小 = 发送字节数 + 压缩节省的字节数
    original_size = total_sent + compression_savings
        if original_size == 0:

    return 0

    return compression_savings / original_size

    def _identify_bottlenecks(self, stats: Dict[...]
    """识别性能瓶颈"""
    bottlenecks: List[str] =

    # 检查处理时间
    avg_processing_time = stats.get('avg_processing_time_ms', 0)
        if isinstance(avg_processing_time, (int, float)) and avg_processing_time > 100:  # 超过100ms
            bottlenecks.append('high_message_processing_time')

    # 检查成功率
    success_rate = stats.get('success_rate', 1.0)
        if isinstance(success_rate, (int, float)) and success_rate < 0.95:  # 成功率低于95%
            bottlenecks.append('low_success_rate')

    # 检查缓存效率
    cache_hit_rate = self._get_cache_efficiency(stats)
        if cache_hit_rate < 0.7:  # 缓存命中率低于70%
            bottlenecks.append('low_cache_efficiency')

    return bottlenecks

    def _generate_optimization_recommendations(self, stats: Dict[...]
    """生成优化建议"""
    recommendations: List[Dict[str, str]] =

    # 基于瓶颈生成建议
    bottlenecks = self._identify_bottlenecks(stats)

        if 'high_message_processing_time' in bottlenecks:


    recommendations.append({
                'type': 'processing_time',
                'severity': 'high',
                'message': '消息处理时间过长，建议优化消息处理逻辑或增加处理节点'
            })

        if 'low_success_rate' in bottlenecks:


    recommendations.append({
                'type': 'success_rate',
                'severity': 'high',
                'message': '消息成功率较低，建议检查网络连接和错误处理机制'
            })

        if 'low_cache_efficiency' in bottlenecks:


    recommendations.append({
                'type': 'cache_efficiency',
                'severity': 'medium',
                'message': '缓存效率较低，建议调整缓存策略或增加缓存大小'
            })

    # 基于一般统计生成建议
    avg_processing_time = stats.get('avg_processing_time_ms', 0)
        if isinstance(avg_processing_time, (int, float)) and avg_processing_time > 50 and avg_processing_time <= 100:

    recommendations.append({
                'type': 'processing_time',
                'severity': 'medium',
                'message': '消息处理时间中等，可以考虑进一步优化'
            })

    return recommendations

# HSP连接器性能增强装饰器
class HSPPerformanceEnhancer:
    """HSP连接器性能增强器"""

    def __init__(self, optimizer: HSPPerformanceOptimizer) -> None:
    self.optimizer: HSPPerformanceOptimizer = optimizer

    def enhance_publish(self, original_publish_func: Callable[..., Awaitable[None]])
    """增强发布函数"""
        async def enhanced_publish(*args: Any, **kwargs: Any) -> None:
            # 记录开始时间
            start_time = time.time

            # 执行原始发布函数
            try:

                result = await original_publish_func(*args, **kwargs)
                success = True
            except Exception as e:

                result = None
                success = False
                logger.error(f"消息发布失败: {e}")

            # 记录结束时间
            end_time = time.time
            processing_time = (end_time - start_time) * 1000  # 转换为毫秒

            # 记录消息指标
            if len(args) > 1:

    envelope = args[1]  # 假设第二个参数是消息信封
                if isinstance(envelope, dict)

    message_id = envelope.get('message_id', 'unknown')
                    if not isinstance(message_id, str)

    message_id = 'unknown'

                    message_type = envelope.get('message_type', 'unknown')
                    if not isinstance(message_type, str)

    message_type = 'unknown'

                    # 计算消息大小
                    message_size = len(json.dumps(envelope).encode('utf-8'))

                    metrics = MessageMetrics(
                        message_id=message_id,
                        message_type=message_type,
                        size_bytes=message_size,
                        processing_time_ms=processing_time,
                        timestamp=time.time,
                        success=success
                    )

                    self.optimizer.record_message_metrics(metrics)

            return result

    return enhanced_publish

    def enhance_receive(self, original_receive_func: Callable[..., Any])
    """增强接收函数"""
        async def enhanced_receive(*args: Any, **kwargs: Any) -> None:
            # 记录开始时间
            start_time = time.time

            # 执行原始接收函数
            try:
                # 确保参数正确传递
                if asyncio.iscoroutinefunction(original_receive_func)

    _ = await original_receive_func(*args, **kwargs)
                else:

                    original_receive_func(*args, **kwargs)
                success = True
            except Exception as e:

                success = False
                logger.error(f"消息接收失败: {e}")

            # 记录结束时间
            end_time = time.time
            processing_time = (end_time - start_time) * 1000  # 转换为毫秒

            # 记录消息指标（如果可以获取消息信息）
            # 这里可以根据实际实现进行调整

            return None  # 显式返回None以匹配类型注解

    return enhanced_receive

if __name__ == "__main__":
    # 测试HSP性能优化器
    logging.basicConfig(level=logging.INFO)

    async def test_hsp_optimizer -> None:
    optimizer = HSPPerformanceOptimizer

    # 测试消息缓存
    optimizer.cache_message('msg1', {'data': 'test'})
    cached_msg = optimizer.get_cached_message('msg1')
    print(f"缓存消息: {cached_msg}")

    # 测试消息压缩
    test_message: MessageData = {
            'message_id': 'test1',
            'message_type': 'HSP::Fact_v0.1',
            'data': 'This is a test message with some data to compress'
    }

    compressed = optimizer.compress_message(test_message)
    decompressed = optimizer.decompress_message(compressed)
    print(f"原始消息: {test_message}")
    print(f"解压消息: {decompressed}")

    # 测试性能统计
    metrics = MessageMetrics(
            message_id='test1',
            message_type='HSP::Fact_v0.1',
            size_bytes=100,
            processing_time_ms=50.0,
            timestamp=time.time,
            success=True
    )
    optimizer.record_message_metrics(metrics)

    stats = optimizer.get_performance_stats
    print(f"性能统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")

    # 测试网络效率报告
    report = optimizer.get_network_efficiency_report
    print(f"网络效率报告: {json.dumps(report, indent=2, ensure_ascii=False)}")

    # 运行测试
    asyncio.run(test_hsp_optimizer)