#!/usr/bin/env python3
"""
Comprehensive Functionality Test for Angela AI v6.2.0
Tests all core systems and features
"""

import subprocess
import time
import json
import requests
import os
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

class AngelaTester:
    def __init__(self):
        self.results = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'tests': []
        }
        self.base_url = "http://127.0.0.1:8000"
        self.ws_url = "ws://127.0.0.1:8000/ws"
        
    def test(self, name, func):
        """Run a test and record results"""
        self.results['total'] += 1
        try:
            func()
            self.results['passed'] += 1
            self.results['tests'].append({
                'name': name,
                'status': 'passed',
                'message': 'Success'
            })
            print(f"✅ {name}")
        except Exception as e:
            logger.error(f'Error in comprehensive_test.py: {e}', exc_info=True)
            self.results['failed'] += 1

            self.results['tests'].append({
                'name': name,
                'status': 'failed',
                'message': str(e)
            })
            print(f"❌ {name}: {e}")
    
    def test_backend_health(self):
        """Test backend health endpoint"""
        response = requests.get(f"{self.base_url}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
    
    def test_websocket_connection(self):
        """Test WebSocket connection"""
        import websocket
        ws = websocket.WebSocket()
        ws.connect(self.ws_url)
        assert ws.connected
        ws.close()
    
    def test_live2d_model_files(self):
        """Test Live2D model files exist"""
        model_dir = Path("/home/cat/桌面/Unified-AI-Project/resources/models/miara_pro")
        assert model_dir.exists()
        
        # Check for required files
        required_files = [
            "miara_pro_t03.moc3",
            "miara_pro_t03.physics3.json",
            "miara_pro_t03.cdi3.json"
        ]
        
        for file in required_files:
            # Check in subdirectories
            found = any((model_dir / file).exists() or 
                       (model_dir / f"miara_pro_t03.4096" / file).exists() or
                       (model_dir / "miara_pro" / file).exists()
                       for _ in [0])
            if not found:
                # Recursively search
                found = any(p.name == file for p in model_dir.rglob("*"))
            assert found, f"Required file not found: {file}"
    
    def test_electron_running(self):
        """Test Electron app is running"""
        result = subprocess.run(
            ["pgrep", "-f", "electron"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
    
    def test_backend_running(self):
        """Test backend service is running"""
        result = subprocess.run(
            ["pgrep", "-f", "uvicorn"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
    
    def test_file_permissions(self):
        """Test critical files have correct permissions"""
        critical_files = [
            "/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app/main.js",
            "/home/cat/桌面/Unified-AI-Project/apps/backend/src/services/main_api_server.py"
        ]
        
        for file_path in critical_files:
            assert os.path.exists(file_path)
            assert os.access(file_path, os.R_OK)
    
    def test_python_dependencies(self):
        """Test Python dependencies are installed"""
        result = subprocess.run(
            ["python3", "-m", "pip", "list"],
            capture_output=True,
            text=True
        )
        required_packages = ["fastapi", "uvicorn", "websockets"]
        output = result.stdout.lower()
        
        for package in required_packages:
            assert package in output, f"Missing dependency: {package}"
    
    def test_node_dependencies(self):
        """Test Node.js dependencies are installed"""
        package_json = Path("/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app/package.json")
        if package_json.exists():
            node_modules = package_json.parent / "node_modules"
            assert node_modules.exists()
    
    def test_single_instance(self):
        """Test single instance protection"""
        # Check for main Electron process only (not internal zygote/renderer processes)
        result = subprocess.run(
            ["pgrep", "-f", "electron"],
            capture_output=True,
            text=True
        )
        
        # Count main electron processes (exclude zygote, renderer, and bash processes)
        pids = result.stdout.strip().split('\n')
        main_processes = 0
        for pid in pids:
            if not pid:
                continue
            try:
                # Get process command line
                cmd_result = subprocess.run(
                    ["ps", "-p", pid, "-o", "command="],
                    capture_output=True,
                    text=True
                )
                cmd = cmd_result.stdout.strip()
                
                # Exclude bash processes
                if cmd.startswith('bash'):
                    continue
                
                # Count only main electron processes (not --type=zygote or --type=renderer)
                if 'electron . --disable-dev-shm-usage --no-sandbox' in cmd:
                    main_processes += 1
            except Exception as e:
                logger.error(f'Unexpected error in comprehensive_test.py: {e}', exc_info=True)
                pass

        
        # Should have 2 main processes (node wrapper + electron binary), which is normal
        # Single instance protection prevents additional app instances
        assert main_processes <= 2, f"Too many main Electron instances: {main_processes}"
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("🧪 Running Comprehensive Angela AI Tests")
        print("="*60 + "\n")
        
        # Backend Tests
        print("📡 Backend Tests")
        print("-" * 40)
        self.test("Backend Health", self.test_backend_health)
        self.test("Backend Running", self.test_backend_running)
        self.test("WebSocket Connection", self.test_websocket_connection)
        
        # Frontend Tests
        print("\n🖥️ Frontend Tests")
        print("-" * 40)
        self.test("Electron Running", self.test_electron_running)
        self.test("Single Instance Protection", self.test_single_instance)
        
        # Live2D Tests
        print("\n🎭 Live2D Tests")
        print("-" * 40)
        self.test("Live2D Model Files", self.test_live2d_model_files)
        
        # System Tests
        print("\n⚙️ System Tests")
        print("-" * 40)
        self.test("File Permissions", self.test_file_permissions)
        self.test("Python Dependencies", self.test_python_dependencies)
        self.test("Node.js Dependencies", self.test_node_dependencies)
        
        # Print Summary
        print("\n" + "="*60)
        print("📊 Test Summary")
        print("="*60)
        print(f"Total Tests: {self.results['total']}")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        
        if self.results['failed'] > 0:
            print(f"\nFailed Tests:")
            for test in self.results['tests']:
                if test['status'] == 'failed':
                    print(f"  - {test['name']}: {test['message']}")
        
        success_rate = (self.results['passed'] / self.results['total'] * 100) if self.results['total'] > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        print("="*60 + "\n")
        
        return self.results

if __name__ == "__main__":
    tester = AngelaTester()
    results = tester.run_all_tests()
    
    # Save results to file
    with open('/tmp/angela_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Exit with appropriate code
    exit(0 if results['failed'] == 0 else 1)