"""
集成测试基类
提供通用的测试功能和工具方法
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock

logger: Any = logging.getLogger(__name__)


class BaseIntegrationTest:
    """集成测试基类"""
    
    @pytest.fixture(autouse=True)
    def setup_test(self, integration_test_config, test_utils) -> None:
        """自动设置测试环境"""
        self.config = integration_test_config
        self.utils = test_utils
        self.test_data = {}
        logger.info(f"Setting up integration test with config: {self.config}")
        yield
        logger.info("Tearing down integration test")
    
    async def wait_for_condition(self, condition_func, timeout: int = 10, interval: float = 0.1):
        """
        等待条件满足
        
        Args:
            condition_func: 条件检查函数
            timeout: 超时时间(秒)
            interval: 检查间隔(秒)
            
        Returns:
            bool: 条件是否满足
        """
        return await self.utils.wait_for_condition(condition_func, timeout, interval)
    
    def create_test_agent_config(self, agent_type: str = "test_agent") -> Dict[str, Any]:
        """
        创建测试代理配置
        
        Args:
            agent_type: 代理类型
            
        Returns:
            Dict: 代理配置
        """
        return self.utils.create_test_agent_config(agent_type)
    
    def create_test_hsp_message(self, message_type: str = "fact", content: str = "Test message") -> Dict[str, Any]:
        """
        创建测试HSP消息
        
        Args:
            message_type: 消息类型
            content: 消息内容
            
        Returns:
            Dict: HSP消息
        """
        return self.utils.create_test_hsp_message(message_type, content)
    
    def create_test_memory_item(self, content: str = "Test memory content") -> Dict[str, Any]:
        """
        创建测试记忆项
        
        Args:
            content: 记忆内容
            
        Returns:
            Dict: 记忆项
        """
        return self.utils.create_test_memory_item(content)
    
    async def assert_event_occurred(self, event_checker, timeout: int = 5, message: str = "Event did not occur"):
        """
        断言事件发生
        
        Args:
            event_checker: 事件检查函数
            timeout: 超时时间
            message: 断言失败时的消息
        """
        try:
            await asyncio.wait_for(event_checker(), timeout=timeout)
        except asyncio.TimeoutError:
            pytest.fail(message)
    
    def assert_mock_called_with(self, mock_obj, expected_args=None, expected_kwargs=None):
        """
        断言mock对象被调用且参数正确
        
        Args:
            mock_obj: mock对象
            expected_args: 期望的位置参数
            expected_kwargs: 期望的关键字参数
        """
        mock_obj.assert_called()
        if expected_args:
            mock_obj.assert_called_with(*expected_args)
        if expected_kwargs:
            mock_obj.assert_called_with(**expected_kwargs)
    
    async def run_with_timeout(self, coro, timeout: int = 10):
        """
        带超时的协程执行
        
        Args:
            coro: 协程对象
            timeout: 超时时间
            
        Returns:
            协程结果
        """
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            pytest.fail(f"Operation timed out after {timeout} seconds")
    
    def capture_logs(self, logger_name: str, level: int = logging.INFO):
        """
        捕获指定logger的日志
        
        Args:
            logger_name: logger名称
            level: 日志级别
            
        Returns:
            list: 日志记录列表
        """
        import io
        
        logger_instance = logging.getLogger(logger_name)
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(level)
        logger_instance.addHandler(handler)
        
        # 返回清理函数和日志流
        def cleanup():
            logger_instance.removeHandler(handler)
            handler.close()
            return log_stream.getvalue()
        
        return cleanup, log_stream


class SystemIntegrationTest(BaseIntegrationTest):
    """系统集成测试基类"""
    
    @pytest.fixture(autouse=True)
    def setup_system_test(self, setup_test, mock_external_services):
        """设置系统测试环境"""
        self.mock_services = mock_external_services
        logger.info("Setting up system integration test environment")
        yield
        logger.info("Tearing down system integration test environment")
    
    def get_mock_service(self, service_name: str) -> Mock:
        """
        获取mock服务实例
        
        Args:
            service_name: 服务名称
            
        Returns:
            Mock: mock服务实例
        """
        return self.mock_services.get(service_name)
    
    async def simulate_agent_interaction(self, agent1_config: Dict, agent2_config: Dict, message: Dict):
        """
        模拟代理间交互
        
        Args:
            agent1_config: 发送代理配置
            agent2_config: 接收代理配置
            message: 消息内容
        """
        # 模拟代理1发送消息
        hsp_connector = self.get_mock_service("hsp_connector")
        hsp_connector.return_value.publish.return_value = True
        
        # 模拟代理2接收消息
        # 这里可以根据需要添加更复杂的交互逻辑
        
        logger.info(f"Simulated interaction between {agent1_config['agent_id']} and {agent2_config['agent_id']}")