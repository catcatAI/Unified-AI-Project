#!/usr/bin/env python3
"""
HSP协议高级性能优化器
负责实现更高级的性能优化机制，包括连接池、智能缓存和负载均衡
"""

import asyncio
import logging
import time
import json
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor

logger: Any = logging.getLogger(__name__)

@dataclass
class ConnectionPoolStats:
    """连接池统计信息"""
    active_connections: int
    idle_connections: int
    total_connections: int
    max_connections: int
    connection_reuse_count: int

@dataclass
class MessageRoutingStats:
    """消息路由统计信息"""
    routed_messages: int
    avg_routing_time_ms: float
    cache_hits: int
    cache_misses: int

class HSPConnectionPool:
    """HSP连接池"""
    
    def __init__(self, max_connections: int = 10, connection_timeout: int = 30) -> None:
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.active_connections = {}  # 连接ID -> 连接对象
        self.idle_connections = deque()  # 空闲连接队列
        self.connection_lock = threading.RLock()
        self.connection_counter = 0
        self.stats = ConnectionPoolStats(0, 0, 0, max_connections, 0)
        
        logger.info(f"HSP连接池初始化，最大连接数: {max_connections}")
    
    def get_connection(self) -> Optional[Any]:
        """获取连接"""
        with self.connection_lock:
            # 尝试从空闲连接中获取
            while self.idle_connections:
                connection = self.idle_connections.popleft
                # 检查连接是否仍然有效
                if self._is_connection_valid(connection):
                    self.active_connections[id(connection)] = connection
                    self.stats.active_connections += 1
                    self.stats.idle_connections -= 1
                    self.stats.connection_reuse_count += 1
                    logger.debug("从连接池获取空闲连接")
                    return connection
            
            # 创建新连接（如果未达到最大连接数）
            if len(self.active_connections) + len(self.idle_connections) < self.max_connections:
                connection = self._create_new_connection
                if connection:
                    self.active_connections[id(connection)] = connection
                    self.stats.active_connections += 1
                    self.stats.total_connections += 1
                    logger.debug("创建新连接")
                    return connection
            
            logger.warning("连接池已满，无法获取新连接")
            return None
    
    def return_connection(self, connection: Any):
        """归还连接到池中"""
        with self.connection_lock:
            conn_id = id(connection)
            if conn_id in self.active_connections:
                del self.active_connections[conn_id]
                self.stats.active_connections -= 1
                
                # 检查连接是否仍然有效
                if self._is_connection_valid(connection):
                    self.idle_connections.append(connection)
                    self.stats.idle_connections += 1
                    logger.debug("连接归还到连接池")
                else:
                    self.stats.total_connections -= 1
                    logger.debug("无效连接已丢弃")
    
    def _create_new_connection(self) -> Optional[Any]:
        """创建新连接（模拟实现）"""
        self.connection_counter += 1
        connection = {
            'id': self.connection_counter,
            'created_at': time.time,
            'last_used': time.time
        }
        return connection
    
    def _is_connection_valid(self, connection: Any) -> bool:
        """检查连接是否有效"""
        if not connection:
            return False
        
        # 检查连接是否超时
        if time.time - connection.get('last_used', 0) > self.connection_timeout:
            return False
        
        return True
    
    def get_stats(self) -> ConnectionPoolStats:
        """获取连接池统计信息"""
        with self.connection_lock:
            self.stats.idle_connections = len(self.idle_connections)
            self.stats.active_connections = len(self.active_connections)
            return self.stats.copy

class HSPIntelligentCache:
    """HSP智能缓存"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300) -> None:
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = {}  # 键 -> (值, 过期时间, 访问计数)
        self.access_order = deque()  # 访问顺序队列（用于LRU）
        self.cache_lock = threading.RLock()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
        
        logger.info(f"HSP智能缓存初始化，最大大小: {max_size}, TTL: {ttl_seconds}秒")
    
    def get(self, key: str) -> Optional[Any]:
        """从缓存获取值"""
        with self.cache_lock:
            if key in self.cache:
                value, expire_time, access_count = self.cache[key]
                # 检查是否过期
                if time.time < expire_time:
                    # 更新访问计数和顺序
                    self.cache[key] = (value, expire_time, access_count + 1)
                    self._update_access_order(key)
                    self.stats['hits'] += 1
                    logger.debug(f"缓存命中: {key}")
                    return value
                else:
                    # 过期，删除
                    del self.cache[key]
                    self.stats['evictions'] += 1
                    logger.debug(f"缓存项过期并删除: {key}")
            
            self.stats['misses'] += 1
            logger.debug(f"缓存未命中: {key}")
            return None
    
    def put(self, key: str, value: Any):
        """将值放入缓存"""
        with self.cache_lock:
            # 如果缓存已满，执行淘汰策略
            if len(self.cache) >= self.max_size:
                self._evict
            
            expire_time = time.time + self.ttl_seconds
            self.cache[key] = (value, expire_time, 1)
            self._update_access_order(key)
            logger.debug(f"值已放入缓存: {key}")
    
    def _evict(self):
        """淘汰缓存项（LRU策略）"""
        if not self.access_order:
            return
        
        # 找到最少访问的项
        lru_key = None
        min_access_count = float('inf')
        
        # 检查访问顺序中的项
        for key in list(self.access_order):
            if key in self.cache:
                _, _, access_count = self.cache[key]
                if access_count < min_access_count:
                    min_access_count = access_count
                    lru_key = key
        
        # 如果没有找到，使用最老的项
        if not lru_key and self.access_order:
            lru_key = self.access_order[0]
        
        if lru_key and lru_key in self.cache:
            del self.cache[lru_key]
            # 从访问顺序队列中移除
            if lru_key in self.access_order:
                self.access_order.remove(lru_key)
            self.stats['evictions'] += 1
            logger.debug(f"缓存项被淘汰: {lru_key}")
    
    def _update_access_order(self, key: str):
        """更新访问顺序"""
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self.cache_lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'evictions': self.stats['evictions'],
                'hit_rate': hit_rate
            }

class HSPLoadBalancer:
    """HSP负载均衡器"""
    
    def __init__(self, strategy: str = "round_robin") -> None:
        self.strategy = strategy
        self.nodes =   # 节点ID -> 节点信息
        self.node_stats = defaultdict(lambda: {
            'request_count': 0,
            'error_count': 0,
            'response_time_sum': 0,
            'response_time_count': 0
        })
        self.current_index = 0
        self.lb_lock = threading.RLock
        
        logger.info(f"HSP负载均衡器初始化，策略: {strategy}")
    
    def add_node(self, node_id: str, node_info: Dict[str, Any]):
        """添加节点"""
        with self.lb_lock:
            self.nodes[node_id] = node_info
            logger.debug(f"节点已添加: {node_id}")
    
    def remove_node(self, node_id: str):
        """移除节点"""
        with self.lb_lock:
            if node_id in self.nodes:
                del self.nodes[node_id]
                if node_id in self.node_stats:
                    del self.node_stats[node_id]
                logger.debug(f"节点已移除: {node_id}")
    
    def select_node(self, message: Dict[str, Any]) -> Optional[str]:
        """选择节点"""
        with self.lb_lock:
            if not self.nodes:
                return None
            
            if self.strategy == "round_robin":
                return self._round_robin_selection
            elif self.strategy == "least_connections":
                return self._least_connections_selection
            elif self.strategy == "weighted_response_time":
                return self._weighted_response_time_selection
            else:
                # 默认使用轮询
                return self._round_robin_selection
    
    def _round_robin_selection(self) -> str:
        """轮询选择"""
        node_ids = list(self.nodes.keys)
        if not node_ids:
            return None
        
        selected_node = node_ids[self.current_index]
        self.current_index = (self.current_index + 1) % len(node_ids)
        return selected_node
    
    def _least_connections_selection(self) -> str:
        """最少连接数选择"""
        # 简化实现，选择请求计数最少的节点
        if not self.node_stats:
            return list(self.nodes.keys)[0] if self.nodes else None
        
        min_requests = float('inf')
        selected_node = None
        
        for node_id in self.nodes:
            stats = self.node_stats[node_id]
            if stats['request_count'] < min_requests:
                min_requests = stats['request_count']
                selected_node = node_id
        
        return selected_node
    
    def _weighted_response_time_selection(self) -> str:
        """加权响应时间选择"""
        if not self.node_stats:
            return list(self.nodes.keys)[0] if self.nodes else None
        
        best_score = float('inf')
        selected_node = None
        
        for node_id in self.nodes:
            stats = self.node_stats[node_id]
            if stats['response_time_count'] > 0:
                avg_response_time = stats['response_time_sum'] / stats['response_time_count']
                # 使用响应时间和错误率计算得分
                error_rate = stats['error_count'] / (stats['request_count'] + 1)
                score = avg_response_time * (1 + error_rate)
            else:
                score = float('inf')  # 没有统计数据的节点优先级较低
            
            if score < best_score:
                best_score = score
                selected_node = node_id
        
        # 如果所有节点都没有统计数据，使用轮询
        if selected_node is None:
            return self._round_robin_selection
        
        return selected_node
    
    def record_request(self, node_id: str):
        """记录请求"""
        with self.lb_lock:
            self.node_stats[node_id]['request_count'] += 1
    
    def record_response(self, node_id: str, response_time: float, success: bool = True):
        """记录响应"""
        with self.lb_lock:
            stats = self.node_stats[node_id]
            stats['response_time_sum'] += response_time
            stats['response_time_count'] += 1
            if not success:
                stats['error_count'] += 1

class HSPAdvancedPerformanceOptimizer:
    """HSP高级性能优化器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or 
        
        # 初始化组件
        self.connection_pool = HSPConnectionPool(
            max_connections=self.config.get('max_connections', 10),
            connection_timeout=self.config.get('connection_timeout', 30)
        )
        
        self.intelligent_cache = HSPIntelligentCache(
            max_size=self.config.get('cache_max_size', 1000),
            ttl_seconds=self.config.get('cache_ttl', 300)
        )
        
        self.load_balancer = HSPLoadBalancer(
            strategy=self.config.get('load_balancing_strategy', 'round_robin')
        )
        
        # 路由统计
        self.routing_stats = MessageRoutingStats(0, 0.0, 0, 0)
        self.routing_times = deque(maxlen=1000)  # 存储最近1000次路由时间
        
        # 线程池用于异步处理
        self.executor = ThreadPoolExecutor(max_workers=self.config.get('thread_pool_size', 4))
        
        logger.info("HSP高级性能优化器初始化完成")
    
    def optimize_message_routing(self, message: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """优化消息路由"""
        start_time = time.time
        
        # 1. 生成消息键用于缓存
        message_key = self._generate_message_key(message)
        
        # 2. 尝试从缓存获取路由结果
        cached_result = self.intelligent_cache.get(message_key)
        if cached_result:
            self.routing_stats.cache_hits += 1
            routing_time = (time.time - start_time) * 1000
            self.routing_times.append(routing_time)
            self.routing_stats.avg_routing_time_ms = sum(self.routing_times) / len(self.routing_times)
            logger.debug(f"使用缓存路由结果: {message_key}")
            return cached_result, "cached"
        
        # 3. 缓存未命中，执行路由逻辑
        self.routing_stats.cache_misses += 1
        
        # 4. 选择目标节点
        target_node = self.load_balancer.select_node(message)
        if target_node:
            self.load_balancer.record_request(target_node)
        
        # 5. 获取连接
        connection = self.connection_pool.get_connection
        
        # 6. 构建路由结果
        routing_result = {
            'message': message,
            'target_node': target_node,
            'connection': connection,
            'routing_timestamp': time.time
        }
        
        # 7. 缓存路由结果
        self.intelligent_cache.put(message_key, routing_result)
        
        # 8. 更新统计信息
        self.routing_stats.routed_messages += 1
        routing_time = (time.time - start_time) * 1000
        self.routing_times.append(routing_time)
        self.routing_stats.avg_routing_time_ms = sum(self.routing_times) / len(self.routing_times)
        
        # 9. 归还连接
        if connection:
            self.connection_pool.return_connection(connection)
        
        logger.debug(f"消息路由完成: {message_key} -> {target_node}")
        return routing_result, "routed"
    
    def _generate_message_key(self, message: Dict[str, Any]) -> str:
        """生成消息键用于缓存"""
        # 使用消息的关键属性生成键
        key_data = {
            'message_type': message.get('message_type', ''),
            'sender_ai_id': message.get('sender_ai_id', ''),
            'recipient_ai_id': message.get('recipient_ai_id', ''),
            'payload_hash': hashlib.md5(
                json.dumps(message.get('payload', ), sort_keys=True).encode
            _ = ).hexdigest
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode).hexdigest
    
    def get_connection(self) -> Optional[Any]:
        """获取连接"""
        return self.connection_pool.get_connection
    
    def return_connection(self, connection: Any):
        """归还连接"""
        self.connection_pool.return_connection(connection)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return {
            'connection_pool': asdict(self.connection_pool.get_stats),
            'cache': self.intelligent_cache.get_stats,
            'routing': asdict(self.routing_stats),
            'timestamp': datetime.now.isoformat
        }
    
    def add_node_to_load_balancer(self, node_id: str, node_info: Dict[str, Any]):
        """向负载均衡器添加节点"""
        self.load_balancer.add_node(node_id, node_info)
    
    def remove_node_from_load_balancer(self, node_id: str):
        """从负载均衡器移除节点"""
        self.load_balancer.remove_node(node_id)
    
    def record_response_stats(self, node_id: str, response_time: float, success: bool = True):
        """记录响应统计"""
        self.load_balancer.record_response(node_id, response_time, success)

# 异步装饰器用于性能增强
class HSPAdvancedPerformanceEnhancer:
    """HSP高级性能增强器"""
    
    def __init__(self, optimizer: HSPAdvancedPerformanceOptimizer) -> None:
        self.optimizer = optimizer
    
    def enhance_publish(self, original_publish_func: Callable):
        """增强发布函数"""
        async def enhanced_publish(*args, **kwargs):
            # 记录开始时间
            start_time = time.time
            
            # 执行原始发布函数
            try:
                if asyncio.iscoroutinefunction(original_publish_func):
                    result = await original_publish_func(*args, **kwargs)
                else:
                    # 对于同步函数，在线程池中执行
                    loop = asyncio.get_event_loop
                    result = await loop.run_in_executor(self.optimizer.executor, original_publish_func, *args, **kwargs)
                success = True
            except Exception as e:
                result = None
                success = False
                logger.error(f"消息发布失败: {e}")
            
            # 记录结束时间
            end_time = time.time
            processing_time = (end_time - start_time) * 1000  # 转换为毫秒
            
            # 记录性能统计（如果可以获取节点信息）
            # 这里可以根据具体实现进行调整
            
            return result
        
        return enhanced_publish
    
    def enhance_receive(self, original_receive_func: Callable):
        """增强接收函数"""
        async def enhanced_receive(*args, **kwargs):
            # 记录开始时间
            start_time = time.time
            
            # 执行原始接收函数
            try:
                if asyncio.iscoroutinefunction(original_receive_func):
                    result = await original_receive_func(*args, **kwargs)
                else:
                    # 对于同步函数，在线程池中执行
                    loop = asyncio.get_event_loop
                    result = await loop.run_in_executor(self.optimizer.executor, original_receive_func, *args, **kwargs)
                success = True
            except Exception as e:
                result = None
                success = False
                logger.error(f"消息接收失败: {e}")
            
            # 记录结束时间
            end_time = time.time
            processing_time = (end_time - start_time) * 1000  # 转换为毫秒
            
            # 记录性能统计（如果可以获取节点信息）
            # 这里可以根据具体实现进行调整
            
            return result
        
        return enhanced_receive

# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建高级性能优化器
    config = {
        'max_connections': 5,
        'connection_timeout': 60,
        'cache_max_size': 100,
        'cache_ttl': 600,
        'load_balancing_strategy': 'round_robin',
        'thread_pool_size': 2
    }
    
    optimizer = HSPAdvancedPerformanceOptimizer(config)
    enhancer = HSPAdvancedPerformanceEnhancer(optimizer)
    
    # 添加测试节点
    optimizer.add_node_to_load_balancer("node_1", {"host": "192.168.1.101", "port": 1883})
    optimizer.add_node_to_load_balancer("node_2", {"host": "192.168.1.102", "port": 1883})
    optimizer.add_node_to_load_balancer("node_3", {"host": "192.168.1.103", "port": 1883})
    
    # 测试消息路由
    test_messages = [
        {
            "message_id": "msg_001",
            "message_type": "HSP::Fact_v0.1",
            "sender_ai_id": "did:hsp:ai_001",
            "recipient_ai_id": "did:hsp:ai_002",
            "payload": {"content": "Test fact 1"}
        },
        {
            "message_id": "msg_002",
            "message_type": "HSP::Fact_v0.1",
            "sender_ai_id": "did:hsp:ai_001",
            "recipient_ai_id": "did:hsp:ai_002",
            "payload": {"content": "Test fact 1"}  # 相同内容，应该缓存命中
        },
        {
            "message_id": "msg_003",
            "message_type": "HSP::TaskRequest_v0.1",
            "sender_ai_id": "did:hsp:ai_002",
            "recipient_ai_id": "did:hsp:ai_003",
            "payload": {"task": "process_data"}
        }
    ]
    
    # 测试路由
    for i, message in enumerate(test_messages):
        print(f"\n测试消息 {i+1}:")
        routing_result, status = optimizer.optimize_message_routing(message)
        print(f"路由状态: {status}")
        print(f"目标节点: {routing_result.get('target_node')}")
        
        # 模拟响应记录
        if routing_result.get('target_node'):
            optimizer.record_response_stats(
                routing_result['target_node'], 
                response_time=10.5, 
                success=True
            )
    
    # 显示性能统计
    print("\n性能统计:")
    stats = optimizer.get_performance_stats
    print(json.dumps(stats, indent=2, ensure_ascii=False))