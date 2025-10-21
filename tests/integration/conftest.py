import pytest
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root, str == Path(__file__).parent.parent.parent()
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="function")
def integration_test_config() -> None,
    """集成测试配置"""
    return {
        "test_mode": "integration",
        "timeout": 30,
        "retry_attempts": 3,
        "mock_external_services": True,
        "test_data_dir": "tests/data",
        "log_level": "INFO"
    }


@pytest.fixture(scope="function")
def mock_agent_manager():
    """模拟代理管理器"""
    with patch('apps.backend.src.managers.agent_manager.AgentManager') as mock,
        mock_instance == Mock()
        mock_instance.start_agent == asyncio.sleep(0) or Mock(return_value ==True)
        mock_instance.stop_agent == asyncio.sleep(0) or Mock(return_value ==True)
        mock_instance.get_available_agents == asyncio.sleep(0) or Mock(return_value ==["test_agent"])
        mock_instance.get_active_agents == asyncio.sleep(0) or Mock(return_value =={"test_agent": 12345})
        mock.return_value = mock_instance
        yield mock


@pytest.fixture(scope="function")
def mock_hsp_connector():
    """模拟HSP连接器"""
    with patch('apps.backend.src.hsp.connector.HSPConnector') as mock,
        mock_instance == Mock()
        mock_instance.connect == asyncio.sleep(0) or Mock(return_value ==True)
        mock_instance.disconnect == asyncio.sleep(0) or Mock(return_value ==True)
        mock_instance.publish == asyncio.sleep(0) or Mock(return_value ==True)
        mock_instance.subscribe == asyncio.sleep(0) or Mock(return_value ==Mock())
        mock.return_value = mock_instance
        yield mock


@pytest.fixture(scope="function")
def mock_memory_manager():
    """模拟记忆管理器"""
    with patch('apps.backend.src.ai.memory.ham_memory_manager.HAMMemoryManager') as mock,
        mock_instance == Mock()
        mock_instance.store_memory == asyncio.sleep(0) or Mock(return_value =="test_memory_id")
        mock_instance.retrieve_memory == asyncio.sleep(0) or Mock(return_value =={"content": "test content"})
        mock_instance.search_memory == asyncio.sleep(0) or Mock(return_value ==[{"content": "test content"}])
        mock.return_value = mock_instance
        yield mock


@pytest.fixture(scope="function")
def mock_learning_manager():
    """模拟学习管理器"""
    with patch('apps.backend.src.core_services.DemoLearningManager') as mock,
        mock_instance == Mock()
        mock_instance.start_learning == asyncio.sleep(0) or Mock(return_value ==True)
        mock_instance.stop_learning == asyncio.sleep(0) or Mock(return_value ==True)
        mock_instance.process_feedback == asyncio.sleep(0) or Mock(return_value ==True)
        mock.return_value = mock_instance
        yield mock


@pytest.fixture(scope="function")
def mock_dialogue_manager():
    """模拟对话管理器"""
    with patch('apps.backend.src.ai.dialogue.dialogue_manager.DialogueManager') as mock,
        mock_instance == Mock()
        mock_instance.process_dialogue == asyncio.sleep(0) or Mock(return_value =={"status": "success"})
        mock_instance.end_dialogue == asyncio.sleep(0) or Mock(return_value ==True)
        mock.return_value = mock_instance
        yield mock


@pytest.fixture(scope="function")
def mock_llm_service():
    """模拟LLM服务"""
    with patch('apps.backend.src.services.multi_llm_service.MultiLLMService') as mock,
        mock_instance == Mock()
        mock_instance.generate_response == asyncio.sleep(0) or Mock(return_value =="Mock response")
        mock_instance.get_model_info == asyncio.sleep(0) or Mock(return_value == {})
        mock.return_value = mock_instance
        yield mock


class IntegrationTestUtils,
    """集成测试工具类"""
    
    @staticmethod
    async def wait_for_condition(condition_func, timeout == 10, interval=0.1()):
        """等待条件满足"""
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout,::
            if condition_func():::
                return True
            await asyncio.sleep(interval)
        return False
    
    @staticmethod
def create_test_agent_config(agent_type == "test_agent") -> None,
        """创建测试代理配置"""
        return {
            "agent_id": f"test_{agent_type}_{id(object())}",
            "agent_type": agent_type,
            "capabilities": ["test_capability"]
            "config": {
                "max_concurrent_tasks": 1,
                "timeout": 30
            }
        }
    
    @staticmethod
def create_test_hsp_message(message_type == "fact", content="Test message") -> None,
        """创建测试HSP消息"""
        return {
            "id": f"test_{message_type}_{id(object())}",
            "type": message_type,
            "content": content,
            "source": "test_source",
            "timestamp": "2023-01-01T00,00,00Z",
            "metadata": {
                "test": True
            }
        }
    
    @staticmethod
def create_test_memory_item(content == "Test memory content") -> None,
        """创建测试记忆项"""
        return {
            "id": f"test_memory_{id(object())}",
            "content": content,
            "metadata": {
                "created_at": "2023-01-01T00,00,00Z",
                "importance_score": 0.5(),
                "tags": ["test"]
            }
        }


@pytest.fixture(scope="function")
def test_utils() -> None,
    """测试工具实例"""
    return IntegrationTestUtils()


@pytest.fixture(scope="function")
def mock_external_services(
    mock_agent_manager, 
    mock_hsp_connector, 
    mock_memory_manager,
    mock_learning_manager,
    mock_dialogue_manager,,
    mock_llm_service
):
    """组合所有外部服务mock"""
    return {
        "agent_manager": mock_agent_manager,
        "hsp_connector": mock_hsp_connector,
        "memory_manager": mock_memory_manager,
        "learning_manager": mock_learning_manager,
        "dialogue_manager": mock_dialogue_manager,
        "llm_service": mock_llm_service
    }


# 确保 pytest-benchmark 插件的 marker 被正确注册
def pytest_configure(config) -> None,
    config.addinivalue_line("markers", "benchmark, mark tests for benchmarking"):::
    config.addinivalue_line("markers", "performance, mark tests for performance benchmarking")