#!/usr/bin/env python3
"""
Simple test to check project core functionality
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_imports():
    """Test basic imports"""
    print("Testing basic imports...")
    
    imports = [
        "import numpy",
        "import pandas",
        "import sklearn",
        "import torch",
        "import tensorflow",
        "import nltk",
        "import spacy",
        "import chromadb",
        "from fastapi import FastAPI",
        "import uvicorn",
        "import requests",
        "import yaml",
        "import json",
        "import asyncio",
        "import logging"
    ]
    
    results = {}
    
    for imp in imports:
        try:
            exec(imp)
            print(f"✅ {imp}")
            results[imp] = True
        except Exception as e:
            print(f"❌ {imp} - {str(e)[:50]}...")
            results[imp] = False
    
    return results

def test_project_specific_imports():
    """Test project specific imports"""
    print("\nTesting project specific imports...")
    
    imports = [
        "from apps.backend.src.core.managers.system_manager import SystemManager",
        "from apps.backend.src.ai.agents.base_agent import BaseAgent",
        "from apps.backend.src.ai.concept_models.causal_reasoning_engine import CausalReasoningEngine",
        "from apps.backend.src.ai.memory.ham_memory_manager import HAMMemoryManager",
        "from apps.backend.src.tools.tool_dispatcher import ToolDispatcher",
        "from apps.backend.src.core.hsp.connector import HSPConnector"
    ]
    
    results = {}
    
    for imp in imports:
        try:
            exec(imp)
            print(f"✅ {imp}")
            results[imp] = True
        except Exception as e:
            print(f"❌ {imp} - {str(e)[:50]}...")
            results[imp] = False
    
    return results

def main():
    """Main test function"""
    print("Project Core Functionality Test")
    print("=" * 50)
    
    # Test basic imports
    basic_results = test_basic_imports()
    
    # Test project specific imports
    project_results = test_project_specific_imports()
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    total_basic = len(basic_results)
    successful_basic = sum(1 for v in basic_results.values() if v)
    print(f"Basic Imports: {successful_basic}/{total_basic}")
    
    total_project = len(project_results)
    successful_project = sum(1 for v in project_results.values() if v)
    print(f"Project Imports: {successful_project}/{total_project}")
    
    overall = successful_basic == total_basic and successful_project == total_project
    print(f"\nOverall Status: {'✅ PASS' if overall else '❌ FAIL'}")
    
    return 0 if overall else 1

if __name__ == "__main__":
    sys.exit(main())