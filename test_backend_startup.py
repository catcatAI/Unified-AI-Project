#!/usr/bin/env python3
"""
Test backend startup and API endpoints functionality
"""

import sys
import os
import subprocess
import time
import requests
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_backend_imports():
    """Test if backend modules can be imported successfully"""
    print("=" * 60)
    print("Testing Backend Module Imports")
    print("=" * 60)
    
    results = {}
    
    # Test critical imports
    import_tests = [
        ("FastAPI", "from fastapi import FastAPI"),
        ("System Manager", "from apps.backend.src.core.managers.system_manager import SystemManager"),
        ("Config", "from apps.backend.src.core.config.level5_config import Level5Config"),
        ("Knowledge Graph", "from apps.backend.src.core.knowledge.unified_knowledge_graph_impl import UnifiedKnowledgeGraphImpl"),
        ("API Routes", "from apps.backend.src.api.routes import app"),
    ]
    
    for name, import_stmt in import_tests:
        try:
            exec(import_stmt)
            print(f"✅ {name}: Import successful")
            results[name] = True
        except Exception as e:
            print(f"❌ {name}: Import failed - {e}")
            results[name] = False
    
    return results

def test_backend_startup():
    """Test if backend can start up successfully"""
    print("\n" + "=" * 60)
    print("Testing Backend Startup")
    print("=" * 60)
    
    backend_dir = os.path.join(os.getcwd(), "apps", "backend")
    
    try:
        # Check if main.py exists
        main_file = os.path.join(backend_dir, "main.py")
        if not os.path.exists(main_file):
            print(f"❌ main.py not found at {main_file}")
            return False
        
        # Try to start backend in background
        print("Starting backend server...")
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for startup
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Backend server started successfully")
            
            # Test basic API endpoints
            try:
                response = requests.get("http://localhost:8000/api/v1/agents", timeout=5)
                if response.status_code == 200:
                    print("✅ /api/v1/agents endpoint responding")
                else:
                    print(f"⚠️ /api/v1/agents returned status {response.status_code}")
                
                response = requests.get("http://localhost:8000/api/v1/models", timeout=5)
                if response.status_code == 200:
                    print("✅ /api/v1/models endpoint responding")
                else:
                    print(f"⚠️ /api/v1/models returned status {response.status_code}")
                
                response = requests.get("http://localhost:8000/api/v1/system/health", timeout=5)
                if response.status_code == 200:
                    print("✅ /api/v1/system/health endpoint responding")
                else:
                    print(f"⚠️ /api/v1/system/health returned status {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Could not connect to API endpoints: {e}")
            
            # Terminate the backend
            process.terminate()
            process.wait(timeout=5)
            print("Backend server stopped")
            return True
        else:
            # Process exited, check error
            stdout, stderr = process.communicate()
            print(f"❌ Backend failed to start")
            if stderr:
                print(f"Error output:\n{stderr}")
            if stdout:
                print(f"Output:\n{stdout}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing backend startup: {e}")
        return False

def test_critical_components():
    """Test critical backend components"""
    print("\n" + "=" * 60)
    print("Testing Critical Components")
    print("=" * 60)
    
    results = {}
    
    # Test Level 5 AGI Config
    try:
        from apps.backend.src.core.config.level5_config import Level5Config
        config = Level5Config()
        print("✅ Level5Config: Initialization successful")
        results["Level5Config"] = True
    except Exception as e:
        print(f"❌ Level5Config: {e}")
        results["Level5Config"] = False
    
    # Test System Manager
    try:
        from apps.backend.src.core.managers.system_manager import SystemManager
        manager = SystemManager()
        print("✅ SystemManager: Initialization successful")
        results["SystemManager"] = True
    except Exception as e:
        print(f"❌ SystemManager: {e}")
        results["SystemManager"] = False
    
    # Test Knowledge Graph
    try:
        from apps.backend.src.core.knowledge.unified_knowledge_graph_impl import UnifiedKnowledgeGraphImpl
        kg = UnifiedKnowledgeGraphImpl()
        print("✅ KnowledgeGraph: Initialization successful")
        results["KnowledgeGraph"] = True
    except Exception as e:
        print(f"❌ KnowledgeGraph: {e}")
        results["KnowledgeGraph"] = False
    
    return results

def main():
    """Run all backend tests"""
    print(f"Backend Test Suite - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    
    # Run all tests
    import_results = test_backend_imports()
    startup_result = test_backend_startup()
    component_results = test_critical_components()
    
    # Summary
    print("\n" + "=" * 60)
    print("BACKEND TEST SUMMARY")
    print("=" * 60)
    
    total_imports = len(import_results)
    successful_imports = sum(1 for v in import_results.values() if v)
    print(f"Module Imports: {successful_imports}/{total_imports} successful")
    
    print(f"Backend Startup: {'✅ Successful' if startup_result else '❌ Failed'}")
    
    total_components = len(component_results)
    successful_components = sum(1 for v in component_results.values() if v)
    print(f"Critical Components: {successful_components}/{total_components} successful")
    
    # Overall status
    all_good = startup_result and successful_imports == total_imports and successful_components == total_components
    print(f"\nOverall Backend Status: {'✅ PASS' if all_good else '❌ FAIL'}")
    
    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "imports": import_results,
        "startup": startup_result,
        "components": component_results,
        "overall": all_good
    }
    
    with open("backend_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\nDetailed results saved to: backend_test_results.json")
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())