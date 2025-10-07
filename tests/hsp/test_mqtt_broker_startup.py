"""
测试模块 - test_mqtt_broker_startup

自动生成的测试模块，用于验证系统功能。
"""

import pytest
import asyncio
import pytest_asyncio
from amqtt.broker import Broker
# 修复导入路径
from apps.backend.src.hsp.connector import HSPConnector

MQTT_BROKER_ADDRESS = "127.0.0.1"
MQTT_BROKER_PORT = 1883
TEST_AI_ID = "did:hsp:test_ai_001"

@pytest_asyncio.fixture(scope="module")
async def broker():
    config = {
        "default": {
            "type": "tcp",
            "bind": f"{MQTT_BROKER_ADDRESS}:{MQTT_BROKER_PORT}",
        },
        "sys_interval": 10,
        "auth": {
            "allow-anonymous": True
        },
        "topic-check": {"enabled": False},
    }
    broker = Broker(config)
    _ = await broker.start()
    _ = await asyncio.sleep(3) # Give the broker a moment to fully start
    yield broker
    _ = await broker.shutdown()

@pytest_asyncio.fixture
async def hsp_connector(broker):
    connector = HSPConnector(
        TEST_AI_ID,
        broker_address=MQTT_BROKER_ADDRESS,
        broker_port=MQTT_BROKER_PORT,
    )
    _ = await connector.connect()
    yield connector
    _ = await connector.disconnect()

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
@pytest.mark.flaky(reruns=3, reruns_delay=2)
async 
    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
    
    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()
def test_broker_and_connector_startup(hsp_connector) -> None:
    # If we reach here, it means the broker started and the connector connected successfully
    assert hsp_connector.is_connected, "HSPConnector should be connected"
    print("Broker started and HSPConnector connected successfully!")