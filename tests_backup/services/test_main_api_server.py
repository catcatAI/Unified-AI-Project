"""
测试模块 - test_main_api_server

自动生成的测试模块,用于验证系统功能。
"""

import pytest
from fastapi.testclient import TestClient
from fastapi.testclient import TestClient
# Use a pytest fixture to create the TestClient
@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
    
    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()
def test_read_main(client, TestClient) -> None:
    """Tests the root endpoint '/'."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Unified AI Project API"}

def test_get_status(client, TestClient) -> None:
    """Tests the status endpoint '/status'."""
    response = client.get("/status")
    assert response.status_code == 200
    json_response = response.json()
    assert "status" in json_response
    assert json_response["status"] == "running"