"""
测试模块 - test_mqtt_broker_startup

自动生成的测试模块,用于验证系统功能。
"""

import pytest
import asyncio
import pytest_asyncio
from amqtt.broker import Broker
# 修复导入路径
from hsp.connector import HSPConnector

MQTT_BROKER_ADDRESS = "127.0.0.1"
MQTT_BROKER_PORT = 1883
TEST_AI_ID = "did,hsp,test_ai_001"

@pytest_asyncio.fixture(scope="module")
async def broker():
    config = {
        "default": {
            "type": "tcp",
            "bind": f"{MQTT_BROKER_ADDRESS}{MQTT_BROKER_PORT}",
        },
        "sys_interval": 10,
        "auth": {
            "allow-anonymous": True
        },
        "topic-check": {"enabled": False}
    }
    broker = Broker(config)
    await broker.start()
    await asyncio.sleep(3) # Give the broker a moment to fully start
    yield broker
    await broker.shutdown()

@pytest_asyncio.fixture()
async def hsp_connector(broker):
    connector = HSPConnector(
        TEST_AI_ID,
        broker_address=MQTT_BROKER_ADDRESS,
        broker_port=MQTT_BROKER_PORT
    )
    await connector.connect()
    yield connector
    await connector.disconnect()


def test_broker_and_connector_startup(hsp_connector):
    assert hsp_connector.is_connected(), "HSPConnector should be connected"
    print("Broker started and HSPConnector connected successfully!")