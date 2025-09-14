#!/usr/bin/env python3
"""
Full integration test for Atlassian functionality
"""

import sys
import json
from pathlib import Path

# Add the backend src directory to the path
backend_src = Path(__file__).parent.parent / "apps" / "backend" / "src"
sys.path.insert(0, str(backend_src))

def test_confluence_integration():
    """Test Confluence integration"""
    print("Testing Confluence integration...")
    
    try:
        from integrations.confluence_integration import ConfluenceIntegration
        from integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector
        
        # Create a mock configuration
        config = {
            "atlassian": {
                "domain": "test-domain",
                "user_email": "test@example.com",
                "api_token": "test-token",
                "cloud_id": "test-cloud-id"
            }
        }
        
        # Create the connector and integration
        connector = EnhancedRovoDevConnector(config)
        integration = ConfluenceIntegration(connector)
        
        print("Confluence integration test passed!")
        return True
    except Exception as e:
        print(f"Error during Confluence integration test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_jira_integration():
    """Test Jira integration"""
    print("Testing Jira integration...")
    
    try:
        from integrations.jira_integration import JiraIntegration
        from integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector
        
        # Create a mock configuration
        config = {
            "atlassian": {
                "domain": "test-domain",
                "user_email": "test@example.com",
                "api_token": "test-token",
                "cloud_id": "test-cloud-id"
            }
        }
        
        # Create the connector and integration
        connector = EnhancedRovoDevConnector(config)
        integration = JiraIntegration(connector)
        
        print("Jira integration test passed!")
        return True
    except Exception as e:
        print(f"Error during Jira integration test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rovo_dev_agent():
    """Test Rovo Dev agent"""
    print("Testing Rovo Dev agent...")
    
    try:
        # Mock the HSPConnector import since it's not available in this context
        class MockHSPConnector:
            def __init__(self, *args, **kwargs):
                pass
        
        import integrations.rovo_dev_agent
        integrations.rovo_dev_agent.HSPConnector = MockHSPConnector
        
        from integrations.rovo_dev_agent import RovoDevAgent
        from unittest.mock import patch
        
        # Create a mock configuration
        config = {
            "atlassian": {
                "domain": "test-domain",
                "user_email": "test@example.com",
                "api_token": "test-token",
                "cloud_id": "test-cloud-id",
                "rovo_dev": {
                    "cache_ttl": 300,
                    "max_concurrent_requests": 5
                }
            },
            "hsp_integration": {
                "agent_id": "test-rovo-agent"
            }
        }
        
        # Mock the dependencies
        with patch('integrations.rovo_dev_agent.EnhancedRovoDevConnector'), \
             patch('integrations.rovo_dev_agent.AtlassianBridge'), \
             patch('integrations.rovo_dev_agent.HSPConnector', MockHSPConnector):
            # Create the Rovo Dev agent
            agent = RovoDevAgent(config)
            
            # Check that the agent was created correctly
            assert agent.agent_id == "test-rovo-agent"
            print("Rovo Dev agent test passed!")
            return True
    except Exception as e:
        print(f"Error during Rovo Dev agent test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Atlassian Full Integration Test")
    print("=" * 35)
    print()
    
    # Run all tests
    try:
        test1 = test_confluence_integration()
        test2 = test_jira_integration()
        test3 = test_rovo_dev_agent()
        
        if test1 and test2 and test3:
            print("\nAll Atlassian integration tests completed successfully!")
            return True
        else:
            print("\nSome Atlassian integration tests failed!")
            return False
    except Exception as e:
        print(f"Error during Atlassian integration testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)