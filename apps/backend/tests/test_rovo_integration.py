# tests/test_rovo_integration.py
"""
Unit tests for the Rovo Dev Integration
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add the src directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from apps.backend.src.integrations.rovo_dev_agent import RovoDevAgent
from apps.backend.src.integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector

class TestRovoDevIntegration(unittest.TestCase):
    """Test cases for the Rovo Dev Integration"""
    
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
                    "max_concurrent_requests": 5,
                    "capabilities": [
                        {
                            "name": "code_analysis",
                            "description": "Analyze code quality and security",
                            "enabled": True
                        },
                        {
                            "name": "documentation_generation",
                            "description": "Generate documentation from code",
                            "enabled": True
                        }
                    ]
                }
            },
            "hsp_integration": {
                "agent_id": "test-rovo-agent"
            }
        }
        
    def test_rovo_dev_agent_initialization(self):
        """Test Rovo Dev agent initialization"""
        with patch('integrations.rovo_dev_agent.EnhancedRovoDevConnector'), \
             patch('integrations.rovo_dev_agent.AtlassianBridge'), \
             patch('integrations.rovo_dev_agent.HSPConnector'):
            agent = RovoDevAgent(self.mock_config)
            
            self.assertEqual(agent.agent_id, "test-rovo-agent")
            self.assertFalse(agent.is_active)
            self.assertEqual(len(agent.capabilities), 2)
            self.assertEqual(agent.capabilities[0]['name'], 'code_analysis')
            self.assertEqual(agent.capabilities[1]['name'], 'documentation_generation')
            
    def test_enhanced_connector_initialization(self):
        """Test Enhanced Rovo Dev connector initialization"""
        connector = EnhancedRovoDevConnector(self.mock_config)
        
        self.assertEqual(connector.api_token, "test-token")
        self.assertEqual(connector.cloud_id, "test-cloud-id")
        self.assertEqual(connector.user_email, "test@example.com")
        self.assertIn('confluence', connector.base_urls)
        self.assertIn('jira', connector.base_urls)
        
    def test_capability_loading(self):
        """Test capability loading"""
        with patch('integrations.rovo_dev_agent.EnhancedRovoDevConnector'), \
             patch('integrations.rovo_dev_agent.AtlassianBridge'), \
             patch('integrations.rovo_dev_agent.HSPConnector'):
            agent = RovoDevAgent(self.mock_config)
            
            self.assertEqual(len(agent.capabilities), 2)
            self.assertIn('code_analysis', agent.capabilities_dict)
            self.assertIn('documentation_generation', agent.capabilities_dict)
            
    def test_capability_parameters(self):
        """Test capability parameters"""
        with patch('integrations.rovo_dev_agent.EnhancedRovoDevConnector'), \
             patch('integrations.rovo_dev_agent.AtlassianBridge'), \
             patch('integrations.rovo_dev_agent.HSPConnector'):
            agent = RovoDevAgent(self.mock_config)
            
            # Test code analysis parameters
            code_params = agent._get_capability_parameters('code_analysis')
            self.assertIn('repository_url', code_params)
            self.assertIn('analysis_type', code_params)
            
            # Test documentation generation parameters
            doc_params = agent._get_capability_parameters('documentation_generation')
            self.assertIn('source_path', doc_params)
            self.assertIn('doc_type', doc_params)

if __name__ == '__main__':
    unittest.main()