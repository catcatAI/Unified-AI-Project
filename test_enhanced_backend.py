#!/usr/bin/env python3
"""
Comprehensive test suite for Enhanced Minimal Backend
Tests all endpoints including the newly added ones
"""
import sys
import os
import json
import time
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import requests

BASE_URL = "http://localhost:8000"

class TestResult:
    def __init__(self, name, passed, message=""):
        self.name = name
        self.passed = passed
        self.message = message

    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status}: {self.name}" + (f" - {self.message}" if self.message else "")

def test_endpoint(method, path, name, data=None, expected_status=200):
    """Test a single endpoint."""
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{path}", timeout=5)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{path}", json=data, timeout=5)
        elif method == "DELETE":
            response = requests.delete(f"{BASE_URL}{path}", timeout=5)
        
        passed = response.status_code == expected_status
        return TestResult(name, passed, f"Status: {response.status_code}")
    except Exception as e:
        return TestResult(name, False, str(e))

def run_tests():
    """Run all endpoint tests."""
    results = []
    
    print("=" * 60)
    print("Enhanced Minimal Backend - Endpoint Tests")
    print("=" * 60)
    print()
    
    # Health & Status
    print("Testing Health & Status endpoints...")
    results.append(test_endpoint("GET", "/", "Root endpoint"))
    results.append(test_endpoint("GET", "/api/v1/health", "Health check"))
    results.append(test_endpoint("GET", "/api/v1/admin/status", "Admin status"))
    
    # Pet System
    print("\nTesting Pet System endpoints...")
    results.append(test_endpoint("GET", "/api/v1/pet/status", "Get pet status"))
    results.append(test_endpoint("GET", "/api/v1/pet/angelas-pet-123", "Get specific pet"))
    results.append(test_endpoint("GET", "/api/v1/pet/angelas-pet-123/needs", "Get pet needs"))
    results.append(test_endpoint("POST", "/api/v1/pet/angelas-pet-123/interact?action=feed", "Interact with pet (feed)"))
    results.append(test_endpoint("GET", "/api/v1/pet/proactive", "Get proactive suggestions"))
    
    # Economy System
    print("\nTesting Economy System endpoints...")
    results.append(test_endpoint("GET", "/api/v1/economy/angelas-pet-123", "Get economy data"))
    results.append(test_endpoint("GET", "/api/v1/economy/balance", "Get economy balance"))
    results.append(test_endpoint("GET", "/api/v1/economy/angelas-pet-123/inventory", "Get inventory"))
    results.append(test_endpoint("POST", "/api/v1/economy/angelas-pet-123/transaction", 
                                "Transaction", 
                                {"itemId": "food_bowl", "quantity": 1, "transactionType": "buy"}))
    
    # Memory System
    print("\nTesting Memory System endpoints...")
    results.append(test_endpoint("GET", "/api/v1/memory", "Get memories"))
    results.append(test_endpoint("GET", "/api/v1/memory/search?query=AI", "Search memories"))
    results.append(test_endpoint("POST", "/api/v1/memory", "Create memory",
                                {"content": "Test memory", "category": "test", "importance": 0.5}))
    
    # Conversation System
    print("\nTesting Conversation System endpoints...")
    results.append(test_endpoint("GET", "/api/v1/chat/conversations", "List conversations"))
    results.append(test_endpoint("POST", "/api/v1/chat/mscu", "MSCU chat",
                                {"message": "Hello"}))
    results.append(test_endpoint("POST", "/api/v1/chat/completions", "Chat completions",
                                {"messages": [{"role": "user", "content": "Hi"}]}))
    
    # Task System
    print("\nTesting Task System endpoints...")
    results.append(test_endpoint("GET", "/api/v1/tasks", "Get tasks"))
    results.append(test_endpoint("POST", "/api/v1/tasks", "Create task",
                                {"title": "Test Task", "description": "Testing"}))
    
    # Agent System
    print("\nTesting Agent System endpoints...")
    results.append(test_endpoint("GET", "/api/v1/agents", "List agents"))
    results.append(test_endpoint("GET", "/api/v1/agents/creative_agent", "Get specific agent"))
    results.append(test_endpoint("POST", "/api/v1/agents/creative_agent/task", "Assign task to agent",
                                {"task_description": "Write a story"}))
    results.append(test_endpoint("POST", "/api/v1/agents/creative_agent/actions", "Perform agent action",
                                {"action": "generate", "config": {"style": "creative"}}))
    
    # Image Generation
    print("\nTesting Image Generation endpoints...")
    results.append(test_endpoint("POST", "/api/v1/images/generations", "Generate image",
                                {"prompt": "A beautiful sunset"}))
    results.append(test_endpoint("GET", "/api/v1/images/history", "Get image history"))
    results.append(test_endpoint("GET", "/api/v1/images/statistics", "Get image statistics"))
    results.append(test_endpoint("POST", "/api/v1/images/batch-delete", "Batch delete images",
                                {"imageIds": ["img1", "img2", "img3"]}))
    
    # Data Pipeline
    print("\nTesting Data Pipeline endpoints...")
    results.append(test_endpoint("GET", "/api/v1/data/pipeline/status", "Get pipeline status"))
    results.append(test_endpoint("POST", "/api/v1/data/pipeline/trigger", "Trigger pipeline",
                                {"type": "full"}))
    
    # System Endpoints
    print("\nTesting System endpoints...")
    results.append(test_endpoint("GET", "/api/v1/system/status", "Get system status"))
    results.append(test_endpoint("GET", "/api/v1/system/health", "Get system health"))
    results.append(test_endpoint("GET", "/api/v1/system/metrics", "Get system metrics"))
    results.append(test_endpoint("GET", "/api/v1/system/metrics/detailed", "Get detailed metrics"))
    
    # Web Search
    print("\nTesting Web Search endpoints...")
    results.append(test_endpoint("POST", "/api/v1/search", "Perform web search",
                                {"query": "AI developments"}))
    
    # Code Analysis
    print("\nTesting Code Analysis endpoints...")
    results.append(test_endpoint("POST", "/api/v1/code/analyze", "Analyze code",
                                {"code": "def hello():\n    print('Hello')", "language": "python"}))
    
    # Training
    print("\nTesting Training endpoints...")
    results.append(test_endpoint("GET", "/api/v1/training/status", "Get training status"))
    results.append(test_endpoint("POST", "/api/v1/training/start", "Start training",
                                {"model_id": "test_model"}))
    
    # Knowledge Graph
    print("\nTesting Knowledge Graph endpoints...")
    results.append(test_endpoint("GET", "/api/v1/knowledge/graph/nodes", "Get knowledge nodes"))
    results.append(test_endpoint("GET", "/api/v1/knowledge/graph/edges", "Get knowledge edges"))
    results.append(test_endpoint("POST", "/api/v1/knowledge/graph/query", "Query knowledge graph",
                                {"query": "AI"}))
    
    # HSP Protocol
    print("\nTesting HSP Protocol endpoints...")
    results.append(test_endpoint("GET", "/api/v1/hsp/services", "Get HSP services"))
    results.append(test_endpoint("POST", "/api/v1/hsp/request", "Send HSP request",
                                {"service_id": "test", "action": "status"}))
    
    # Monitoring
    print("\nTesting Monitoring endpoints...")
    results.append(test_endpoint("GET", "/api/v1/monitoring/alerts", "Get monitoring alerts"))
    results.append(test_endpoint("GET", "/api/v1/monitoring/metrics", "Get monitoring metrics"))
    
    # Files
    print("\nTesting Files endpoints...")
    results.append(test_endpoint("GET", "/api/v1/files", "List files"))
    results.append(test_endpoint("POST", "/api/v1/files/upload", "Upload file"))
    results.append(test_endpoint("DELETE", "/api/v1/files/test-id", "Delete file"))
    
    # Models
    print("\nTesting Models endpoints...")
    results.append(test_endpoint("GET", "/api/v1/models", "Get models"))
    results.append(test_endpoint("GET", "/api/v1/models/test-model/metrics", "Get model metrics"))
    results.append(test_endpoint("GET", "/api/v1/models/test-model/training/status", "Get training status"))
    
    # Debug endpoints
    print("\nTesting Debug endpoints...")
    results.append(test_endpoint("GET", "/api/v1/debug/mock_data", "Debug mock data"))
    results.append(test_endpoint("POST", "/api/v1/debug/reset", "Reset mock data"))
    
    # Print results
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    print()
    
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    
    for result in results:
        print(result)
    
    print()
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")
    print("=" * 60)
    
    return passed, failed

if __name__ == "__main__":
    print("Waiting for backend to be ready...")
    time.sleep(2)
    
    try:
        # Quick health check
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=2)
        if response.status_code != 200:
            print("❌ Backend is not responding correctly")
            print(f"   Status: {response.status_code}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend")
        print("   Make sure the backend is running: python apps/backend/enhanced_minimal_backend.py")
        sys.exit(1)
    
    passed, failed = run_tests()
    
    if failed > 0:
        sys.exit(1)
    print("\n🎉 All tests passed!")
