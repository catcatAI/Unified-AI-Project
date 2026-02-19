"""
测试模块 - test_hsp_fixture_fix

自动生成的测试模块,用于验证系统功能。
"""

import pytest
import sys
import os
import logging
logger = logging.getLogger(__name__)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'apps', 'backend', 'src')))
from hsp.connector import HSPConnector

# 创建一个简单的异步fixture来测试我们的修复
@pytest.fixture()
async def hsp_connector_fixture():
    # 创建一个mock的MQTT客户端
    mock_mqtt_client = AsyncMock()
    mock_mqtt_client.connect = AsyncMock()
    mock_mqtt_client.disconnect = AsyncMock()
    mock_mqtt_client.subscribe = AsyncMock()
    mock_mqtt_client.publish = AsyncMock(return_value=True)
    
    # 创建HSPConnector实例
    connector = HSPConnector(
        ai_id="test_ai",
        broker_address="localhost",
        broker_port=1883,
        mock_mode=True,
        mock_mqtt_client=mock_mqtt_client
    )
    
    # 连接connector
    await connector.connect()
    
    # 返回connector而不是yield它
    return connector

@pytest.mark.asyncio
async def test_hsp_connector_fixture_fix(hsp_connector_fixture) -> None:
    """测试异步fixture修复是否有效"""
    # 获取connector实例
    connector = await hsp_connector_fixture
    
    # 验证connector是否正确初始化
    assert connector is not None
    assert connector.ai_id == "test_ai"
    assert connector.is_connected is True
    assert connector.mock_mode is True
    
    print("HSP connector fixture fix test passed!")

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])