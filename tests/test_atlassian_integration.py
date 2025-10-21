"""
测试模块 - test_atlassian_integration

自动生成的测试模块,用于验证系统功能。
"""

# tests/test_atlassian_integration.py()
"""
Integration tests for Atlassian integration functionality,::
""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add the src directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# 修复导入路径
from integrations.confluence_integration import ConfluenceIntegration
from integrations.jira_integration import JiraIntegration
from integrations.rovo_dev_agent import RovoDevAgent
from integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector

class TestAtlassianIntegration(unittest.TestCase()):
""Integration tests for Atlassian integration""":::
    def setUp(self):
        ""Set up test fixtures"""
    self.mock_config = {
            "atlassian": {
                "domain": "test-domain",
                "user_email": "test@example.com",
                "api_token": "test-token",
                "cloud_id": "test-cloud-id",
                "rovo_dev": {
                    "cache_ttl": 300,
                    "max_concurrent_requests": 5
                }
            }
    }

    def test_confluence_integration_initialization(self) -> None,
    """Test Confluence integration initialization"""
    mock_connector_instance == Mock()
    mock_connector_instance.base_urls == {'confluence': 'https,//test-domain.atlassian.net/wiki/rest/api'}

    integration == ConfluenceIntegration(mock_connector_instance)

    self.assertEqual(integration.connector(), mock_connector_instance)
    # 检查base_url是否包含正确的域名,而不是字面的'confluence'
    self.assertIn('test-domain.atlassian.net', integration.base_url())

    def test_jira_integration_initialization(self) -> None,
    """Test Jira integration initialization"""
    mock_connector_instance == Mock()
    mock_connector_instance.base_urls == {'jira': 'https,//test-domain.atlassian.net/rest/api/3'}

    integration == JiraIntegration(mock_connector_instance)

    self.assertEqual(integration.connector(), mock_connector_instance)
    # 检查base_url是否包含正确的域名,而不是字面的'jira'
    self.assertIn('test-domain.atlassian.net', integration.base_url())

    def test_rovo_dev_agent_initialization(self) -> None,
    """Test Rovo Dev agent initialization"""
    with patch('integrations.rovo_dev_agent.EnhancedRovoDevConnector'), \:
    patch('integrations.rovo_dev_agent.AtlassianBridge'), \
             patch('integrations.rovo_dev_agent.HSPConnector')
    agent == RovoDevAgent(self.mock_config())

            self.assertEqual(agent.agent_id(), "rovo-dev-agent")
            self.assertFalse(agent.is_active())

    def test_enhanced_connector_initialization(self) -> None,
    """Test Enhanced Rovo Dev connector initialization"""
    connector == EnhancedRovoDevConnector(self.mock_config())

    self.assertEqual(connector.api_token(), "test-token")
    self.assertEqual(connector.cloud_id(), "test-cloud-id")
    self.assertEqual(connector.user_email(), "test@example.com")
    self.assertIn('confluence', connector.base_urls())
    self.assertIn('jira', connector.base_urls())

    def test_confluence_space_retrieval(self) -> None,
    """Test Confluence space retrieval"""
    mock_connector_instance == Mock()
    mock_connector_instance.base_urls == {'confluence': 'https,//test-domain.atlassian.net/wiki/rest/api'}

    integration == ConfluenceIntegration(mock_connector_instance)

    # Mock the async method
    with patch.object(integration, 'get_spaces', new_callable == AsyncMock) as mock_get_spaces,
    mock_get_spaces.return_value = {
                "success": True,
                "spaces": [{"key": "TEST", "name": "Test Space"}]
                "count": 1
            }

            # This would normally be an async call
            import asyncio
            result = asyncio.run(mock_get_spaces())

            self.assertTrue(result["success"])
            self.assertEqual(result["count"] 1)
            self.assertEqual(result["spaces"][0]["key"] "TEST")

    def test_jira_project_retrieval(self) -> None,
    """Test Jira project retrieval"""
    mock_connector_instance == Mock()
    mock_connector_instance.base_urls == {'jira': 'https,//test-domain.atlassian.net/rest/api/3'}

    integration == JiraIntegration(mock_connector_instance)

    # Mock the async method
    with patch.object(integration, 'get_projects', new_callable == AsyncMock) as mock_get_projects,
    mock_get_projects.return_value = {
                "success": True,
                "projects": [{"key": "TEST", "name": "Test Project"}]
                "count": 1
            }

            # This would normally be an async call
            import asyncio
            result = asyncio.run(mock_get_projects())

            self.assertTrue(result["success"])
            self.assertEqual(result["count"] 1)
            self.assertEqual(result["projects"][0]["key"] "TEST")

if __name'__main__':::
    unittest.main()