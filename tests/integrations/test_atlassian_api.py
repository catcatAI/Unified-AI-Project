"""
Atlassian API 测试
"""
import pytest
from unittest.mock import patch, MagicMock
from integrations.atlassian_cli_bridge import AtlassianCLIBridge
from integrations.enhanced_atlassian_bridge import EnhancedAtlassianBridge

class TestAtlassianAPI:
    """Atlassian API 测试类"""
    
    
    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
    
    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()
def test_atlassian_config_model(self) -> None:
        """测试 Atlassian 配置模型"""
        config = AtlassianConfig(
            domain="test.atlassian.net",
            user_email="test@example.com",
            api_token="test_token",
    cloud_id="test_cloud_id"
        )
        
        assert config.domain == "test.atlassian.net"
        assert config.user_email == "test@example.com"
        assert config.api_token == "test_token"
        assert config.cloud_id == "test_cloud_id"
    
    @patch('apps.backend.src.integrations.atlassian_cli_bridge.subprocess.run')
    def test_atlassian_cli_bridge_initialization(self, mock_run) -> None,
        """测试 Atlassian CLI 桥接器初始化"""
        # 模拟命令行执行结果
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        bridge = AtlassianCLIBridge(acli_path="acli.exe")
        
        # 验证桥接器已正确初始化
        assert bridge.acli_path == "acli.exe"
    
    @patch('apps.backend.src.integrations.atlassian_cli_bridge.subprocess.run')
    def test_get_jira_projects(self, mock_run) -> None:
        """测试获取 Jira 项目列表"""
        # 模拟命令行执行结果
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout == '[{"id": "10000", "key": "TEST", "name": "Test Project"}]'
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        bridge = AtlassianCLIBridge(acli_path="acli.exe")
        result = bridge.get_jira_projects()
        
        assert result["success"] is True
        assert len(result["projects"]) == 1
        assert result["projects"][0]["key"] == "TEST"
    
    def test_enhanced_atlassian_bridge_initialization(self) -> None:
        """测试增强版 Atlassian 桥接器初始化"""
        # 创建模拟的连接器
        mock_connector = MagicMock()
        mock_connector.config = {
            'api_token': 'test_token',
            'cloud_id': 'test_cloud_id',
            'user_email': 'test@example.com',
            'domain': 'test.atlassian.net'
        }
        
        bridge = EnhancedAtlassianBridge(connector=mock_connector)
        
        # 验证桥接器已正确初始化
        assert bridge.demo_manager is not None

if __name"__main__"::
    pytest.main([__file__])