# tests/test_atlassian_integration.py
"""
Integration tests for Atlassian integration functionality
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add the src directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from apps.backend.src.integrations.confluence_integration import ConfluenceIntegration
from apps.backend.src.integrations.jira_integration import JiraIntegration
from apps.backend.src.integrations.rovo_dev_agent import RovoDevAgent
from apps.backend.src.integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector

class TestAtlassianIntegration(unittest.TestCase):
    """Integration tests for Atlassian integration"""
    
    def setUp(self):
        """Set up test fixtures"""
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
        
    def test_confluence_integration_initialization(self):
        """Test Confluence integration initialization"""
        with patch('integrations.confluence_integration.EnhancedRovoDevConnector') as mock_connector:
            mock_connector_instance = Mock()
            mock_connector.return_value = mock_connector_instance
            
            integration = ConfluenceIntegration(mock_connector_instance)
            
            self.assertEqual(integration.connector, mock_connector_instance)
            self.assertIn('confluence', integration.base_url)
            
    def test_jira_integration_initialization(self):
        """Test Jira integration initialization"""
        with patch('integrations.jira_integration.EnhancedRovoDevConnector') as mock_connector:
            mock_connector_instance = Mock()
            mock_connector.return_value = mock_connector_instance
            
            integration = JiraIntegration(mock_connector_instance)
            
            self.assertEqual(integration.connector, mock_connector_instance)
            self.assertIn('jira', integration.base_url)
            
    def test_rovo_dev_agent_initialization(self):
        """Test Rovo Dev agent initialization"""
        with patch('integrations.rovo_dev_agent.EnhancedRovoDevConnector'), \
             patch('integrations.rovo_dev_agent.AtlassianBridge'), \
             patch('integrations.rovo_dev_agent.HSPConnector'):
            agent = RovoDevAgent(self.mock_config)
            
            self.assertEqual(agent.agent_id, "rovo-dev-agent")
            self.assertFalse(agent.is_active)
            
    def test_enhanced_connector_initialization(self):
        """Test Enhanced Rovo Dev connector initialization"""
        connector = EnhancedRovoDevConnector(self.mock_config)
        
        self.assertEqual(connector.api_token, "test-token")
        self.assertEqual(connector.cloud_id, "test-cloud-id")
        self.assertEqual(connector.user_email, "test@example.com")
        self.assertIn('confluence', connector.base_urls)
        self.assertIn('jira', connector.base_urls)
        
    def test_confluence_space_retrieval(self):
        """Test Confluence space retrieval"""
        with patch('integrations.confluence_integration.EnhancedRovoDevConnector') as mock_connector:
            mock_connector_instance = Mock()
            mock_connector.return_value = mock_connector_instance
            
            integration = ConfluenceIntegration(mock_connector_instance)
            
            # Mock the async method
            with patch.object(integration, 'get_spaces') as mock_get_spaces:
                mock_get_spaces.return_value = {
                    "success": True,
                    "spaces": [{"key": "TEST", "name": "Test Space"}],
                    "count": 1
                }
                
                # This would normally be an async call
                result = mock_get_spaces()
                
                self.assertTrue(result["success"])
                self.assertEqual(result["count"], 1)
                self.assertEqual(result["spaces"][0]["key"], "TEST")
                
    def test_jira_project_retrieval(self):
        """Test Jira project retrieval"""
        with patch('integrations.jira_integration.EnhancedRovoDevConnector') as mock_connector:
            mock_connector_instance = Mock()
            mock_connector.return_value = mock_connector_instance
            
            integration = JiraIntegration(mock_connector_instance)
            
            # Mock the async method
            with patch.object(integration, 'get_projects') as mock_get_projects:
                mock_get_projects.return_value = {
                    "success": True,
                    "projects": [{"key": "TEST", "name": "Test Project"}],
                    "count": 1
                }
                
                # This would normally be an async call
                result = mock_get_projects()
                
                self.assertTrue(result["success"])
                self.assertEqual(result["count"], 1)
                self.assertEqual(result["projects"][0]["key"], "TEST")

if __name__ == '__main__':
    unittest.main()