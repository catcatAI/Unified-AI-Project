"""
Atlassian 端到端工作流程测试
"""
import pytest
import requests
import time
from typing import Dict, Any

# 假设后端服务运行在本地
BASE_URL = "http://localhost:8000"

class TestAtlassianEndToEndWorkflow:
    """Atlassian 端到端工作流程测试类"""
    
    def setup_method(self):
        """测试前准备"""
        # 确保服务可用
        try:
            response = requests.get(f"{BASE_URL}/health")
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("后端服务未运行，跳过端到端测试")
    
    def test_atlassian_full_workflow(self):
        """测试完整的 Atlassian 工作流程"""
        # 1. 配置 Atlassian 集成
        config_data = {
            "domain": "test.atlassian.net",
            "user_email": "test@example.com",
            "api_token": "test_token",
            "cloud_id": "test_cloud_id"
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/atlassian/configure", json=config_data)
        assert response.status_code == 200
        
        config_result = response.json()
        assert config_result["success"] is True
        
        # 2. 检查服务状态
        time.sleep(1)  # 等待配置生效
        
        response = requests.get(f"{BASE_URL}/api/v1/atlassian/status")
        assert response.status_code == 200
        
        status_result = response.json()
        # 注意：在实际测试中，这里的结果取决于 ACLI 是否可用
        # 在测试环境中，我们可能需要模拟这个行为
        
        # 3. 获取 Jira 项目（如果服务可用）
        if status_result.get("connected", False):
            response = requests.get(f"{BASE_URL}/api/v1/atlassian/jira/projects")
            assert response.status_code == 200
            
            projects_result = response.json()
            # 验证返回的数据结构
            assert "projects" in projects_result
            assert "count" in projects_result
        
        # 4. 获取 Confluence 空间（如果服务可用）
        if status_result.get("connected", False):
            response = requests.get(f"{BASE_URL}/api/v1/atlassian/confluence/spaces")
            assert response.status_code == 200
            
            spaces_result = response.json()
            # 验证返回的数据结构
            assert "spaces" in spaces_result
            assert "count" in spaces_result
    
    def test_offline_mode_handling(self):
        """测试离线模式处理"""
        # 模拟离线状态下的配置尝试
        config_data = {
            "domain": "test.atlassian.net",
            "user_email": "test@example.com",
            "api_token": "test_token",
            "cloud_id": "test_cloud_id"
        }
        
        # 在实际测试中，我们可以模拟网络中断的情况
        # 这里我们只是测试配置端点的基本功能
        response = requests.post(f"{BASE_URL}/api/v1/atlassian/configure", json=config_data)
        assert response.status_code == 200
        
        # 检查离线状态
        response = requests.get(f"{BASE_URL}/api/v1/atlassian/status")
        assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__])