"""
测试模块 - test_hsp_fixture

自动生成的测试模块，用于验证系统功能。
"""

import sys
import os
import pytest
import pytest_asyncio

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 修复导入路径
from apps.backend.tests.hsp.mock_mqtt_broker import MockMqttBroker
from apps.backend.src.core.hsp.internal.internal_bus import InternalBus
from apps.backend.src.core.hsp.bridge.data_aligner import DataAligner

# 修复hsp_connector导入路径
from apps.backend.src.core.hsp.connector import HSPConnector

@pytest_asyncio.fixture
async def mock_broker():
    broker = MockMqttBroker()
    _ = await broker.start()
    try:
        yield broker
    finally:
        _ = await broker.shutdown()

@pytest.mark.asyncio
async 
    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
    
    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()
def test_fixture() -> None:
    # Create the fixtures manually
    mock_broker = MockMqttBroker()
    _ = await mock_broker.start()
    
    try:
        # Create the other fixtures manually
        ib = InternalBus()
        da = DataAligner()
        
        # Create the hsp_connector manually (not using fixture)
        connector = HSPConnector(
            "test_ai",
            "localhost",
            1883,
            mock_mode=True,
            mock_mqtt_client=mock_broker,
            internal_bus=ib,
            message_bridge=None,
            enable_fallback=False
        )
        
        # 验证连接器创建成功
        assert connector is not None
        assert connector.ai_id == "test_ai"
        
        # Connect the connector
        _ = await connector.connect()
        assert connector.is_connected == True
        
        # Clean up
        _ = await connector.disconnect()
        
    finally:
        _ = await mock_broker.shutdown()