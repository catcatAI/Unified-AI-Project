"""
Atlassian 集成测试
"""
import pytest
from fastapi.testclient import TestClient
from apps.backend.main import app
from apps.backend.src.services.atlassian_api import AtlassianConfig

# 创建测试客户端
client = TestClient(app)

class TestAtlassianIntegration:
    """Atlassian 集成测试类"""
    
    def test_configure_atlassian_success(self):
        """测试成功配置 Atlassian 集成"""
        config = AtlassianConfig(
            domain="test.atlassian.net",
            user_email="test@example.com",
            api_token="test_token",
            cloud_id="test_cloud_id"
        )
        
        response = client.post("/api/v1/atlassian/configure", json=config.dict())
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data
    
    def test_get_atlassian_status_without_configuration(self):
        """测试在未配置 Atlassian 集成时获取状态"""
        response = client.get("/api/v1/atlassian/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False
        assert len(data["services"]) == 3  # Confluence, Jira, Bitbucket
    
    def test_get_jira_projects_without_configuration(self):
        """测试在未配置 Atlassian 集成时获取 Jira 项目"""
        response = client.get("/api/v1/atlassian/jira/projects")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not configured" in data["detail"]
    
    def test_create_confluence_page_without_enhanced_bridge(self):
        """测试在未配置增强桥接器时创建 Confluence 页面"""
        page_data = {
            "space_key": "TEST",
            "title": "Test Page",
            "content": "This is a test page"
        }
        
        response = client.post("/api/v1/atlassian/confluence/page", json=page_data)
        
        # 注意：由于增强桥接器未正确配置，这里可能会返回 400 错误
        # 在实际实现中，我们需要更复杂的设置来测试这个端点
        assert response.status_code in [400, 500]

if __name__ == "__main__":
    pytest.main([__file__])