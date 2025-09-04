#!/usr/bin/env python3
"""
Test script for Rovo Dev integration functionality
"""

import sys
import json
from pathlib import Path
from unittest.mock import patch

# Add the backend src directory to the path
backend_src = Path(__file__).parent.parent / "apps" / "backend" / "src"
sys.path.insert(0, str(backend_src))

# Mock the HSPConnector import since it's not available in this context
class MockHSPConnector:
    def __init__(self, *args, **kwargs):
        pass

import integrations.rovo_dev_agent
integrations.rovo_dev_agent.HSPConnector = MockHSPConnector

from integrations.rovo_dev_agent import RovoDevAgent
from integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector

def test_rovo_dev_initialization():
    """Test Rovo Dev agent initialization"""
    print("Testing Rovo Dev agent initialization...")
    
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
    
    try:
        # Mock the dependencies
        with patch('integrations.rovo_dev_agent.EnhancedRovoDevConnector'), \
             patch('integrations.rovo_dev_agent.AtlassianBridge'), \
             patch('integrations.rovo_dev_agent.HSPConnector', MockHSPConnector):
            # Create the Rovo Dev agent
            agent = RovoDevAgent(config)
            
            # Check that the agent was created correctly
            assert agent.agent_id == "test-rovo-agent"
            # Note: capabilities loading might not work in this mock setup
            print("Rovo Dev agent initialization test passed!")
            return True
    except Exception as e:
        print(f"Error during Rovo Dev agent initialization test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_connector_initialization():
    """Test Enhanced Rovo Dev connector initialization"""
    print("Testing Enhanced Rovo Dev connector initialization...")
    
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
        }
    }
    
    try:
        # Create the enhanced connector
        connector = EnhancedRovoDevConnector(config)
        
        # Check that the connector was created correctly
        assert connector.api_token == "test-token"
        assert connector.cloud_id == "test-cloud-id"
        assert connector.user_email == "test@example.com"
        print("Enhanced Rovo Dev connector initialization test passed!")
        return True
    except Exception as e:
        print(f"Error during Enhanced Rovo Dev connector initialization test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_capability_loading():
    """Test capability loading"""
    print("Testing capability loading...")
    
    # Create a mock configuration with capabilities
    config = {
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
    
    try:
        # Mock the dependencies
        with patch('integrations.rovo_dev_agent.EnhancedRovoDevConnector'), \
             patch('integrations.rovo_dev_agent.AtlassianBridge'), \
             patch('integrations.rovo_dev_agent.HSPConnector', MockHSPConnector):
            # Create the Rovo Dev agent
            agent = RovoDevAgent(config)
            
            # Check that capabilities were loaded correctly
            assert len(agent.capabilities) == 2
            assert agent.capabilities[0]['name'] == "code_analysis"
            assert agent.capabilities[1]['name'] == "documentation_generation"
            print("Capability loading test passed!")
            return True
    except Exception as e:
        print(f"Error during capability loading test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Rovo Dev Integration Functionality Test")
    print("=" * 40)
    print()
    
    # Run all tests
    try:
        test1 = test_rovo_dev_initialization()
        test2 = test_enhanced_connector_initialization()
        test3 = test_capability_loading()
        
        if test1 and test2 and test3:
            print("\nAll tests completed successfully!")
            return True
        else:
            print("\nSome tests failed!")
            return False
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)