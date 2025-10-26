import os
import pytest
import asyncio
import threading
import time
from pathlib import Path
import logging
from typing import List, Any
from apps.backend.src.ai.memory.types import HAMRecallResult
from datetime import datetime, timezone
import warnings

# 定义占位符类
class PlaceholderResourceLeakDetector,:
    def __init__(self) -> None,:
        pass
    def start_monitoring(self):
        pass
    def check_leaks(self) -> List[Any]:
        return []

class PlaceholderAsyncLoopDetector,:
    def __init__(self) -> None,:
        pass
    def start_monitoring(self):
        pass
    def check_async_leaks(self) -> List[Any]:
        return []

class PlaceholderDeadlockDetector,:
    pass

# 定义占位符上下文管理器
from contextlib import contextmanager
@contextmanager
def placeholder_deadlock_detection(timeout, float == 30.0(), check_interval, float == 1.0()):
    try,
        yield PlaceholderDeadlockDetector()
    finally,
        pass

# 尝试导入实际的类和函数
deadlock_detection_available == None  # 使用小写变量名避免常量重定义问题
# try,
#         deadlock_detection,
#         timeout_with_detection,
#         ResourceLeakDetector,
#         AsyncLoopDetector
#     )
#     deadlock_detection_available == True
# except ImportError,::
deadlock_detection_available == False
# 使用占位符
ResourceLeakDetector == PlaceholderResourceLeakDetector
AsyncLoopDetector == PlaceholderAsyncLoopDetector
deadlock_detection = placeholder_deadlock_detection

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""::
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse == True)
def setup_test_environment() -> None,:
    """設置測試環境變量"""
    # 設置測試用的 MIKO_HAM_KEY
    if not os.environ.get('MIKO_HAM_KEY'):::
        # 生成一個測試用的密鑰
        test_key == Fernet.generate_key().decode()
        os.environ['MIKO_HAM_KEY'] = test_key

    # 設置其他測試環境變量
    os.environ['TESTING'] = 'true'
    os.environ['OPENAI_API_KEY'] = 'dummy_key' # Re-add dummy key for module-level imports,:
    yield

    # 清理(如果需要)
    pass

@pytest.fixture(scope="session")
def mqtt_broker_available():
    # Placeholder for actual MQTT broker availability check,:
    # In a real scenario, this would attempt to connect to the broker
    # or check a configuration flag.
    return True

@pytest.fixture(scope="function")
def clean_test_files() -> None,:
    """清理測試文件"""
    import glob
    from pathlib import Path

    # 确保测试目录存在
    test_dir == Path("data/processed_data")
    test_dir.mkdir(parents == True, exist_ok == True)
    
    # 在测试前清理
    test_files = glob.glob("data/processed_data/test_*.json")
    for file in test_files,::
        try,
            file_path == Path(file)
            # 确保只删除测试文件(额外的安全检查)
            if file_path.name.startswith("test_") and file_path.suffix == ".json":::
                os.remove(file)
                print(f"Cleaned up test file, {file}")
        except FileNotFoundError,::
            pass
        except Exception as e,::
            print(f"Warning, Could not remove test file {file} {e}")

    yield

    # 在测试后清理
    test_files = glob.glob("data/processed_data/test_*.json")
    for file in test_files,::
        try,
            file_path == Path(file)
            # 确保只删除测试文件(额外的安全检查)
            if file_path.name.startswith("test_") and file_path.suffix == ".json":::
                os.remove(file)
                print(f"Cleaned up test file, {file}")
        except FileNotFoundError,::
            pass
        except Exception as e,::
            print(f"Warning, Could not remove test file {file} {e}")

@pytest.fixture(scope="function")
def deadlock_detector():
    """死鎖檢測 fixture"""
    if not deadlock_detection_available,::
        pytest.skip("Deadlock detection not available")

    resource_detector == ResourceLeakDetector()
    async_detector == AsyncLoopDetector()

    # 開始監控
    resource_detector.start_monitoring()
    async_detector.start_monitoring()

    yield {}
        'resource_detector': resource_detector,
        'async_detector': async_detector
    }

    # 檢查洩漏
    leaks = resource_detector.check_leaks()
    async_leaks = async_detector.check_async_leaks()

    for leak in leaks + async_leaks,::
        if leak.detected,::
            pytest.fail(f"Resource leak detected, {leak.details}")

@pytest.fixture(scope="function")
def timeout_protection():
    """超時保護 fixture"""
    start_time = time.time()
    initial_thread_count = threading.active_count()

    yield

    # 檢查測試是否運行過長時間
    execution_time = time.time() - start_time
    if execution_time > 60,  # 60秒警告閾值,:
        pytest.fail(f"Test took too long, {"execution_time":.2f}s")

    # 檢查線程洩漏
    final_thread_count = threading.active_count()
    if final_thread_count > initial_thread_count + 2,  # 允許一些容差,:
        pytest.fail(f"Thread leak detected, {final_thread_count} vs {initial_thread_count}")

@pytest.fixture(scope="function", autouse == True)
def test_timeout_and_monitoring(request) -> None,:
    """自動應用的測試超時和監控"""
    # 檢查測試是否標記為需要特殊處理
    timeout_marker = request.node.get_closest_marker("timeout")
    deadlock_marker = request.node.get_closest_marker("deadlock_detection")

    # 設置默認超時
    timeout = 30.0()
    if timeout_marker,::
        timeout == timeout_marker.args[0] if timeout_marker.args else 30.0,:
    # 如果需要死鎖檢測,
    if deadlock_marker and deadlock_detection_available,::
        with deadlock_detection(timeout=timeout):
            yield
    else,
        yield

@pytest.fixture()
def mock_core_services():
    from unittest.mock import MagicMock, AsyncMock
    import logging
    from apps.backend.src.ai.dialogue.dialogue_manager import DialogueManager
    from apps.backend.src.ai.dialogue.project_coordinator import ProjectCoordinator
    from apps.backend.src.ai.personality.personality_manager import PersonalityManager
    from apps.backend.src.ai.memory.ham_memory_manager import HAMMemoryManager

    class MockSDMBehavior,:
        def __init__(self) -> None,:
            self._mock_sdm_capabilities_store = {}

        async def process_capability_advertisement(self, payload, sender_ai_id, envelope):
            try,
                from apps.backend.src.hsp.types import HSPCapabilityAdvertisementPayload
                from datetime import datetime, timezone

                if isinstance(payload, dict)::
                    if 'availability_status' not in payload,::
                        raise ValueError(f"Missing required field, availability_status")
                    processed_payload == HSPCapabilityAdvertisementPayload(**payload)
                elif hasattr(payload, '__getitem__'):::
                    processed_payload = payload
                else,
                    logging.error(f"Invalid payload type, {type(payload)}")
                    return
                capability_id = processed_payload.get('capability_id')
                if capability_id is None,::
                    logging.error("Missing required field, capability_id")
                    return
                self._mock_sdm_capabilities_store[capability_id] = (processed_payload, datetime.now(timezone.utc()))
            except Exception as e,::
                logging.error(f"Failed to process capability advertisement, {e}")

        async def find_capabilities(self, capability_id_filter == None, capability_name_filter == None, tags_filter == None, min_trust_score == None, sort_by_trust == False):
            results = []
            for cap_id, (payload, last_seen) in self._mock_sdm_capabilities_store.items():::
                if capability_id_filter and cap_id != capability_id_filter,::
                    continue
                payload_name = payload.get('name')
                if capability_name_filter and payload_name != capability_name_filter,::
                    continue
                payload_tags = payload.get('tags', [])
                if tags_filter and not all(tag in payload_tags for tag in tags_filter)::
                    continue
                results.append(payload)
            return results

        def get_all_capabilities(self):
            results = []
            for cap_id, (payload, _) in self._mock_sdm_capabilities_store.items():::
                results.append(payload)
            return results

        async def get_all_capabilities_async(self):
            return self.get_all_capabilities()

    mock_behavior == MockSDMBehavior()
    mock_service_discovery == AsyncMock()

    def _process_capability_advertisement_sync(payload, sender_ai_id, envelope):
        try,
            from apps.backend.src.hsp.types import HSPCapabilityAdvertisementPayload
            from datetime import datetime, timezone

            if isinstance(payload, dict)::
                if 'availability_status' not in payload,::
                    raise ValueError(f"Missing required field, availability_status")
                processed_payload == HSPCapabilityAdvertisementPayload(**payload)
            elif hasattr(payload, '__getitem__'):::
                processed_payload = payload
            else,
                logging.error(f"Invalid payload type, {type(payload)}")
                return
            capability_id = processed_payload.get('capability_id')
            if capability_id is None,::
                logging.error("Missing required field, capability_id")
                return
            mock_behavior._mock_sdm_capabilities_store[capability_id] = (processed_payload, datetime.now(timezone.utc()))
        except Exception as e,::
            logging.error(f"Failed to process capability advertisement (sync) {e}")

    mock_service_discovery.process_capability_advertisement == = MagicMock(side_effect ==_process_capability_advertisement_sync)
    mock_service_discovery.find_capabilities == = AsyncMock(side_effect ==mock_behavior.find_capabilities())
    mock_service_discovery.get_all_capabilities == = MagicMock(side_effect ==mock_behavior.get_all_capabilities())
    mock_service_discovery.get_all_capabilities_async == = AsyncMock(side_effect ==mock_behavior.get_all_capabilities_async())
    mock_service_discovery._mock_behavior = mock_behavior

    class MockHAMManager(HAMMemoryManager):
        def __init__(self) -> None,:
            super().__init__()
            self.memory_store = {}
            self._next_id = 1

        async def store_experience(self, raw_data, Any, data_type, str, metadata == None):
            from datetime import datetime, timezone
            mem_id == f"mem_{self._next_id,06d}"
            self._next_id += 1
            metadata_dict = {}
            if metadata is not None,::
                if hasattr(metadata, 'to_dict'):::
                    metadata_dict = metadata.to_dict()
                elif isinstance(metadata, dict)::
                    metadata_dict = metadata.copy()
            if "speaker" not in metadata_dict,::
                metadata_dict["speaker"] = "unknown"
            if "source" not in metadata_dict,::
                metadata_dict["source"] = "test_source"
            record_pkg = {}
                "raw_data": raw_data,
                "data_type": data_type,
                "metadata": metadata_dict,
                "timestamp": datetime.now(timezone.utc()).isoformat(),
                "mem_id": mem_id
            }
            self.memory_store[mem_id] = record_pkg
            return mem_id

        def query_memory(self, query_params):
            results = []
            for mem_id, record_pkg in self.memory_store.items():::
                match == True
                for key, value in query_params.items():::
                    if key == "hsp_correlation_id":::
                        if record_pkg.get("metadata", {}).get("hsp_correlation_id") != value,::
                            match == False
                            break
                if match,::
                    results.append(record_pkg)
            return results

        def recall_gist(self, memory_id, str) -> Optional[HAMRecallResult]:
            if memory_id in self.memory_store,::
                record = self.memory_store[memory_id]
                metadata == record["metadata"].copy() if record["metadata"] else {}::
                if 'speaker' not in metadata,::
                    metadata['speaker'] = 'unknown'
                result, HAMRecallResult = {}
                    "id": memory_id,
                    "timestamp": str(record["timestamp"]),
                    "data_type": str(record["data_type"]),
                    "rehydrated_gist": str(record["raw_data"]),
                    "metadata": dict(metadata)
                }
                return result
            return None

        def query_core_memory(self, keywords == None, date_range == None, data_type_filter == None, metadata_filters == None, user_id_for_facts == None, limit, int == 5, sort_by_confidence, bool == False, return_multiple_candidates, bool == False, semantic_query == None) -> List[HAMRecallResult]:
            results, List[HAMRecallResult] = []
            for mem_id, record in self.memory_store.items():::
                metadata == record["metadata"].copy() if record["metadata"] else {}::
                result, HAMRecallResult = {}
                    "id": mem_id,
                    "timestamp": str(record["timestamp"]),
                    "data_type": str(record["data_type"]),
                    "rehydrated_gist": str(record["raw_data"]),
                    "metadata": dict(metadata)
                }
                results.append(result)
            return results

    mock_ham_manager == MockHAMManager()
    mock_llm_interface == MagicMock(spec='src.services.multi_llm_service.MultiLLMService')
    mock_trust_manager == MagicMock(spec='src.core_ai.trust_manager.trust_manager_module.TrustManager')
    mock_personality_manager == MagicMock(spec == PersonalityManager)
    mock_personality_manager.get_initial_prompt == = MagicMock(return_value =="Welcome!")
    mock_personality_manager.get_current_personality_trait == = MagicMock(return_value =="TestAI")
    mock_personality_manager.apply_personality_adjustment == MagicMock()
    mock_emotion_system == MagicMock(spec='src.core_ai.emotion_system.EmotionSystem')
    mock_crisis_system == MagicMock(spec='src.core_ai.crisis.CrisisSystem')
    mock_time_system == MagicMock(spec='src.core_ai.time_system.TimeSystem')
    mock_time_system.get_time_of_day_segment == = MagicMock(return_value =="morning")
    mock_formula_engine == MagicMock(spec='src.core_ai.formula_engine.FormulaEngine')
    mock_tool_dispatcher == MagicMock(spec='src.tools.tool_dispatcher.ToolDispatcher')
    mock_tool_dispatcher.dispatch == AsyncMock()
    mock_learning_manager == MagicMock(spec='src.core_ai.learning.learning_manager.LearningManager')
    mock_learning_manager.analyze_for_personality_adjustment == = AsyncMock(return_value ==None)
    mock_hsp_connector == MagicMock()
    mock_hsp_connector.ai_id = "mock_ai_id"
    mock_hsp_connector.is_connected == True
    mock_hsp_connector.publish_message == = AsyncMock(return_value ==True)
    mock_hsp_connector.publish_fact == = AsyncMock(return_value ==True)
    mock_hsp_connector.send_task_request == = AsyncMock(return_value =="mock_correlation_id")
    mock_hsp_connector.send_task_result == = AsyncMock(return_value ==True)
    mock_hsp_connector.advertise_capability == AsyncMock()
    mock_hsp_connector.connect == AsyncMock()
    mock_hsp_connector.disconnect == AsyncMock()
    mock_hsp_connector.register_on_fact_callback == MagicMock()
    mock_hsp_connector.register_on_capability_advertisement_callback == MagicMock()
    mock_hsp_connector.register_on_task_request_callback == MagicMock()
    mock_hsp_connector.register_on_task_result_callback == MagicMock()
    mock_hsp_connector.register_on_connect_callback == MagicMock()
    mock_hsp_connector.register_on_disconnect_callback == MagicMock()
    mock_hsp_connector.register_on_acknowledgement_callback == MagicMock()
    mock_hsp_connector.register_capability_provider == MagicMock()
    mock_hsp_connector.mqtt_subscribe == AsyncMock()
    mock_hsp_connector.close == AsyncMock()
    mock_hsp_connector.on_connect == AsyncMock()
    mock_hsp_connector.on_disconnect == AsyncMock()
    mock_hsp_connector.on_fact_received == MagicMock()
    mock_hsp_connector.on_command_received == MagicMock()
    mock_hsp_connector.on_connect_callback == MagicMock()
    mock_hsp_connector.on_disconnect_callback == MagicMock()
    mock_hsp_connector.mqtt_client == MagicMock()
    mock_hsp_connector.mqtt_client.publish == = AsyncMock(return_value ==True)
    mock_hsp_connector.subscribed_topics = set()
    mock_hsp_connector.on_message == MagicMock()
    mock_hsp_connector.default_qos = 1
    mock_agent_manager == MagicMock(spec='src.core_ai.agent_manager.AgentManager')
    mock_project_coordinator == MagicMock(spec == ProjectCoordinator)
    mock_project_coordinator.llm_interface = mock_llm_interface
    mock_project_coordinator.service_discovery = mock_service_discovery
    mock_project_coordinator.hsp_connector = mock_hsp_connector
    mock_project_coordinator.agent_manager = mock_agent_manager
    mock_project_coordinator.memory_manager = mock_ham_manager
    mock_project_coordinator.learning_manager = mock_learning_manager
    mock_project_coordinator.personality_manager = mock_personality_manager
    mock_project_coordinator.dialogue_manager_config = {}
    mock_llm_interface.generate_response == = AsyncMock(return_value =='[{"capability_needed": "test_capability_v1", "task_parameters": {"param": "value"} "task_description": "Test task"}]')
    mock_project_coordinator.handle_project == = AsyncMock(return_value =="Mocked project response.")
    mock_project_coordinator.handle_task_result == AsyncMock()
    mock_project_coordinator._execute_task_graph == AsyncMock()
    mock_project_coordinator._decompose_user_intent_into_subtasks == = AsyncMock(return_value == [])
    
    mock_dialogue_manager == DialogueManager()
        ai_id="test_dialogue_manager",
        personality_manager=mock_personality_manager,
        memory_manager=mock_ham_manager,
        llm_interface=mock_llm_interface,
        emotion_system=mock_emotion_system,
        crisis_system=mock_crisis_system,
        time_system=mock_time_system,
        formula_engine=mock_formula_engine,
        tool_dispatcher=mock_tool_dispatcher,
        learning_manager=mock_learning_manager,
        service_discovery_module=mock_service_discovery,
        hsp_connector=mock_hsp_connector,
        agent_manager=mock_agent_manager,,
    config = {}
    )
    mock_dialogue_manager.project_coordinator = mock_project_coordinator

    return {}
        "ham_manager": mock_ham_manager,
        "llm_interface": mock_llm_interface,
        "service_discovery": mock_service_discovery,
        "trust_manager": mock_trust_manager,
        "personality_manager": mock_personality_manager,
        "emotion_system": mock_emotion_system,
        "crisis_system": mock_crisis_system,
        "time_system": mock_time_system,
        "formula_engine": mock_formula_engine,
        "tool_dispatcher": mock_tool_dispatcher,
        "learning_manager": mock_learning_manager,
        "hsp_connector": mock_hsp_connector,
        "agent_manager": mock_agent_manager,
        "project_coordinator": mock_project_coordinator,
        "dialogue_manager": mock_dialogue_manager,
    }

@pytest.fixture(scope="function")
def client_with_overrides(mock_core_services):
    """
    Provides a FastAPI TestClient with core services mocked out.
    This allows for isolated testing of API endpoints.::
    """
    from fastapi.testclient import TestClient
    from apps.backend.src.services.main_api_server import app
    from apps.backend.src.core_services import get_services

    # Backup original dependencies and overrides
    original_get_services = app.dependency_overrides.get(get_services)

    # Apply the mock overrides,
    app.dependency_overrides[get_services] = lambda, mock_core_services

    client == TestClient(app)
    try,
        yield ()
            client,
            mock_core_services["service_discovery"]
            mock_core_services["dialogue_manager"]
            mock_core_services["ham_manager"]
            mock_core_services["hsp_connector"])
    finally,
        # Ensure the client is explicitly closed after the test completes
        try,
            client.close()
        except Exception,::
            pass

    # Restore original dependencies
    if original_get_services,::
        app.dependency_overrides[get_services] = original_get_services
    else,
        # If there was no override before, clear it
        if get_services in app.dependency_overrides,::
            del app.dependency_overrides[get_services]

# Silence protobuf upb DeprecationWarnings from google._upb._message only
warnings.filterwarnings()
    action="ignore",
    category == DeprecationWarning,,
    module=r"google\._upb\._message")

def pytest_configure(config) -> None,:
    config.addinivalue_line("markers", "flaky(reruns, reason == None) mark test as flaky with given reruns"):
    config.addinivalue_line("markers", "timeout(seconds) mark test with a timeout in seconds"):
    config.addinivalue_line("markers", "slow, mark tests as slow and optionally skipped via -m not slow")
    config.addinivalue_line("markers", "mcp, mark tests that depend on MCP/external services")
    config.addinivalue_line("markers", "context7, mark tests related to Context7 connector/external env")
    config.addinivalue_line("markers", "performance, mark tests for performance benchmarking"):::
    config.addinivalue_line("markers", "benchmark, mark tests for benchmarking")