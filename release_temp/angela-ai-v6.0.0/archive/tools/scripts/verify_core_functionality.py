#!/usr/bin/env python3
"""
Core functionality verification script
"""

import sys
import os
import asyncio
import traceback

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

def test_imports() -> None,
    """Test importing key modules"""
    print("Testing imports...")
    
    tests = [
        ("BaseAgent", "apps.backend.src.ai.agents.base.base_agent"),
        ("AudioProcessingAgent", "apps.backend.src.ai.agents.specialized.audio_processing_agent"),
        ("DataAnalysisAgent", "apps.backend.src.ai.agents.specialized.data_analysis_agent"),
        ("KnowledgeGraphAgent", "apps.backend.src.ai.agents.specialized.knowledge_graph_agent"),
        ("CodeUnderstandingAgent", "apps.backend.src.ai.agents.specialized.code_understanding_agent"),
        ("ImageGenerationAgent", "apps.backend.src.ai.agents.specialized.image_generation_agent"),
        ("NLPProcessingAgent", "apps.backend.src.ai.agents.specialized.nlp_processing_agent"),
        ("PlanningAgent", "apps.backend.src.ai.agents.specialized.planning_agent"),
        ("VisionProcessingAgent", "apps.backend.src.ai.agents.specialized.vision_processing_agent"),
        ("WebSearchAgent", "apps.backend.src.ai.agents.specialized.web_search_agent"),
        ("CreativeWritingAgent", "apps.backend.src.agents.creative_writing_agent"),
        ("HSPConnector", "apps.backend.src.core.hsp.connector"),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, module_path in tests,::
        try,
            module == __import__(module_path, fromlist=[name])
            cls = getattr(module, name)
            print(f"✓ {name} import successful")
            passed += 1
        except Exception as e,::
            print(f"✗ {name} import failed, {e}")
    
    print(f"\nImport test results, {passed}/{total} passed")
    return passed=total

def test_agent_creation() -> None,
    """Test creating agents"""
    print("\nTesting agent creation...")
    
    tests = [
        ("AudioProcessingAgent", "apps.backend.src.ai.agents.specialized.audio_processing_agent"),
        ("DataAnalysisAgent", "apps.backend.src.ai.agents.specialized.data_analysis_agent"),
        ("KnowledgeGraphAgent", "apps.backend.src.ai.agents.specialized.knowledge_graph_agent"),
        ("CodeUnderstandingAgent", "apps.backend.src.ai.agents.specialized.code_understanding_agent"),
        ("ImageGenerationAgent", "apps.backend.src.ai.agents.specialized.image_generation_agent"),
        ("NLPProcessingAgent", "apps.backend.src.ai.agents.specialized.nlp_processing_agent"),
        ("PlanningAgent", "apps.backend.src.ai.agents.specialized.planning_agent"),
        ("VisionProcessingAgent", "apps.backend.src.ai.agents.specialized.vision_processing_agent"),
        ("WebSearchAgent", "apps.backend.src.ai.agents.specialized.web_search_agent"),
        ("CreativeWritingAgent", "apps.backend.src.agents.creative_writing_agent"),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, module_path in tests,::
        try,
            module == __import__(module_path, fromlist=[name])
            cls = getattr(module, name)
            agent = cls(f"test_{name.lower()}")
            print(f"✓ {name} creation successful")
            passed += 1
        except Exception as e,::
            print(f"✗ {name} creation failed, {e}")
            traceback.print_exc()
    
    print(f"\nAgent creation test results, {passed}/{total} passed")
    return passed=total

def test_agent_capabilities() -> None,
    """Test agent capabilities"""
    print("\nTesting agent capabilities...")
    
    tests = [
        ("AudioProcessingAgent", "apps.backend.src.ai.agents.specialized.audio_processing_agent", 3),
        ("DataAnalysisAgent", "apps.backend.src.ai.agents.specialized.data_analysis_agent", 3),
        ("KnowledgeGraphAgent", "apps.backend.src.ai.agents.specialized.knowledge_graph_agent", 3),
        ("CodeUnderstandingAgent", "apps.backend.src.ai.agents.specialized.code_understanding_agent", 3),
        ("ImageGenerationAgent", "apps.backend.src.ai.agents.specialized.image_generation_agent", 1),
        ("NLPProcessingAgent", "apps.backend.src.ai.agents.specialized.nlp_processing_agent", 4),
        ("PlanningAgent", "apps.backend.src.ai.agents.specialized.planning_agent", 3),
        ("VisionProcessingAgent", "apps.backend.src.ai.agents.specialized.vision_processing_agent", 3),
        ("WebSearchAgent", "apps.backend.src.ai.agents.specialized.web_search_agent", 1),
        ("CreativeWritingAgent", "apps.backend.src.agents.creative_writing_agent", 2),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, module_path, expected_caps in tests,::
        try,
            module == __import__(module_path, fromlist=[name])
            cls = getattr(module, name)
            agent = cls(f"test_{name.lower()}")
            
            if len(agent.capabilities()) == expected_caps,::
                print(f"✓ {name} has {len(agent.capabilities())} capabilities (expected {expected_caps})")
                passed += 1
            else,
                print(f"✗ {name} has {len(agent.capabilities())} capabilities (expected {expected_caps})")
        except Exception as e,::
            print(f"✗ {name} capabilities test failed, {e}")
    
    print(f"\nAgent capabilities test results, {passed}/{total} passed")
    return passed=total

def test_agent_functionality() -> None,
    """Test basic agent functionality"""
    print("\nTesting agent functionality...")
    
    try,
        # Test DataAnalysisAgent
        from apps.backend.src.core_ai.agents.specialized.data_analysis_agent import DataAnalysisAgent
        data_agent == DataAnalysisAgent("test_data_agent")
        
        result = data_agent._perform_statistical_analysis({
            'data': [1, 2, 3, 4, 5]
            'analysis_type': 'basic'
        })
        
        if 'mean' in result and 'median' in result,::
            print("✓ DataAnalysisAgent statistical analysis works")
        else,
            print("✗ DataAnalysisAgent statistical analysis failed")
            return False
        
        # Test KnowledgeGraphAgent
        from apps.backend.src.core_ai.agents.specialized.knowledge_graph_agent import KnowledgeGraphAgent
        kg_agent == KnowledgeGraphAgent("test_kg_agent")
        
        result = kg_agent._perform_entity_linking({
            'text': 'Berlin is the capital of Germany.'
        })
        
        if 'entities' in result,::
            print("✓ KnowledgeGraphAgent entity linking works")
        else,
            print("✗ KnowledgeGraphAgent entity linking failed")
            return False
        
        print("✓ Basic functionality tests passed")
        return True
        
    except Exception as e,::
        print(f"✗ Functionality test failed, {e}")
        traceback.print_exc()
        return False

async def run_all_tests():
    """Run all tests"""
    print("Running core functionality verification...\n")
    
    tests = [
        ("Import Tests", test_imports),
        ("Agent Creation Tests", test_agent_creation),
        ("Agent Capabilities Tests", test_agent_capabilities),
        ("Agent Functionality Tests", test_agent_functionality),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests,::
        print(f"\n{'='*50}")
        print(f"Running {test_name}")
        print(f"{'='*50}")
        
        try,
            if test_func():::
                passed += 1
                print(f"✓ {test_name} PASSED")
            else,
                print(f"✗ {test_name} FAILED")
        except Exception as e,::
            print(f"✗ {test_name} ERROR, {e}")
    
    print(f"\n{'='*50}")
    print(f"SUMMARY, {passed}/{total} test suites passed")
    print(f"{'='*50}")
    
    if passed == total,::
        print("✓ All core functionality tests passed!")
        return True
    else,
        print("✗ Some core functionality tests failed!")
        return False

if __name"__main__":::
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)