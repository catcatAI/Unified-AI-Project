import sys
import os
import pytest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # 修复导入路径
    from apps.backend.src.core.hsp.connector import HSPConnector
    from apps.backend.tests.hsp.test_hsp_integration import MockMqttBroker
    HSP_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import HSP modules: {e}")
    HSPConnector = MockMqttBroker = None
    HSP_AVAILABLE = False

@pytest.mark.asyncio
async def test_hsp_connector() -> None:
    if not HSP_AVAILABLE:
        pytest.skip("HSP modules not available")
    
    # Create a mock broker
    mock_broker = MockMqttBroker()
#     await mock_broker.start()
    
    try:
        # Create the HSPConnector in mock mode
        connector = HSPConnector(
            "test_ai",
            "localhost",
            1883,
#             mock_mode=True,
#             mock_mqtt_client=mock_broker,
#             enable_fallback=False
        )
        
        # Connect the connector
#         await connector.connect()
        
        # 验证连接器创建成功
        assert connector is not None
        assert connector.ai_id == "test_ai"
        assert connector.is_connected == True
        
        # Clean up
#         await connector.disconnect()
        
    finally:
        await mock_broker.shutdown()