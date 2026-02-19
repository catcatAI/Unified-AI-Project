"""
Angela AI Core Test Suite
完整的Angela AI核心測試套件
"""

import pytest
import sys
import os
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

# 添加項目路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestAngelaCore:
    """Angela AI核心功能測試"""
    
    def test_project_structure(self):
        """測試項目結構完整性"""
        required_dirs = [
            'apps/backend',
            'apps/desktop-app', 
            'apps/mobile-app',
            'tests',
            'configs'
        ]
        
        for dir_path in required_dirs:
            assert os.path.exists(dir_path), f"Missing directory: {dir_path}"
    
    def test_configuration_files(self):
        """測試配置文件存在性"""
        config_files = [
            'requirements.txt',
            '.env.example',
            'configs/angela_config.yaml'
        ]
        
        for config_file in config_files:
            assert os.path.exists(config_file), f"Missing config: {config_file}"
    
    def test_python_imports(self):
        """測試Python模組導入"""
        try:
            import fastapi
            import uvicorn
            import pydantic
        except ImportError as e:
            pytest.skip(f"Required dependency not installed: {e}")
    
    def test_security_middleware(self):
        """測試安全中間件"""
        try:
            sys.path.insert(0, str(project_root / 'apps/backend'))
            from src.shared.security_middleware import EncryptedCommunicationMiddleware
            assert EncryptedCommunicationMiddleware is not None
        except ImportError as e:
            pytest.skip(f"Security module not available: {e}")
    
    def test_live2d_manager(self):
        """測試Live2D管理器"""
        live2d_path = project_root / 'apps/desktop-app/electron_app/js/live2d-manager.js'
        assert live2d_path.exists(), "Live2D manager not found"
        
        # 檢查關鍵功能
        content = live2d_path.read_text()
        required_functions = [
            'initialize()',
            'loadModel(',
            'setExpression(',
            'playMotion('
        ]
        
        for func in required_functions:
            assert func in content, f"Missing function: {func}"
    
    def test_mobile_app_structure(self):
        """測試移動端應用結構"""
        mobile_files = [
            'apps/mobile-app/package.json',
            'apps/mobile-app/App.js',
            'apps/mobile-app/src/security/encryption.js'
        ]
        
        for mobile_file in mobile_files:
            assert os.path.exists(mobile_file), f"Missing mobile file: {mobile_file}"
    
    def test_api_endpoints(self):
        """測試API端點定義"""
        main_py = project_root / 'apps/backend/main.py'
        assert main_py.exists(), "Main backend file not found"
        
        content = main_py.read_text()
        required_endpoints = [
            '@app.get("/health")',
            '@app.get("/api/v1/system/status")',
            '@app.websocket("/ws")'
        ]
        
        for endpoint in required_endpoints:
            assert endpoint in content, f"Missing endpoint: {endpoint}"
    
    def test_performance_settings(self):
        """測試性能設置"""
        hardware_js = project_root / 'apps/desktop-app/electron_app/js/hardware-detection.js'
        assert hardware_js.exists(), "Hardware detection not found"
        
        content = hardware_js.read_text()
        performance_indicators = [
            'detect()',
            'optimizeForHardware',
            'frameRate',
            'resolution'
        ]
        
        for indicator in performance_indicators:
            assert indicator in content, f"Missing performance indicator: {indicator}"
    
    def test_installation_scripts(self):
        """測試安裝腳本"""
        install_files = [
            'install_angela.py',
            'setup_angela.sh'
        ]
        
        for install_file in install_files:
            assert os.path.exists(install_file), f"Missing install script: {install_file}"
    
    def test_documentation(self):
        """測試文檔文件"""
        doc_files = [
            'README.md',
            'QUICKSTART.md',
            'CONTRIBUTING.md'
        ]
        
        for doc_file in doc_files:
            assert os.path.exists(doc_file), f"Missing documentation: {doc_file}"

class TestAngelaSecurity:
    """Angela AI安全測試"""
    
    def test_environment_variables_template(self):
        """測試環境變量模板"""
        env_example = project_root / '.env.example'
        assert env_example.exists(), "Environment template missing"
        
        content = env_example.read_text()
        required_vars = [
            'ANGELA_KEY_A',
            'ANGELA_KEY_B', 
            'ANGELA_KEY_C',
            'BACKEND_HOST',
            'BACKEND_PORT'
        ]
        
        for var in required_vars:
            assert var in content, f"Missing env var: {var}"
    
    def test_security_keys_length(self):
        """測試安全密鑰長度要求"""
        env_example = project_root / '.env.example'
        content = env_example.read_text()
        
        # 檢查密鑰長度提示
        assert 'minimum_32_chars' in content, "Security key length requirement not specified"

class TestAngelaPerformance:
    """Angela AI性能測試"""
    
    def test_performance_modes(self):
        """測試性能模式定義"""
        perf_js = project_root / 'apps/desktop-app/electron_app/js/performance-manager.js'
        if perf_js.exists():
            content = perf_js.read_text()
            
            required_modes = [
                'very_low',
                'low', 
                'medium',
                'high',
                'ultra'
            ]
            
            for mode in required_modes:
                assert mode in content, f"Missing performance mode: {mode}"
    
    def test_hardware_detection(self):
        """測試硬體檢測功能"""
        hardware_js = project_root / 'apps/desktop-app/electron_app/js/hardware-detection.js'
        if hardware_js.exists():
            content = hardware_js.read_text()
            
            detection_methods = [
                '_detectGPU',
                '_detectRAM',
                '_detectPlatform',
                '_detectDeviceType'
            ]
            
            for method in detection_methods:
                assert method in content, f"Missing detection method: {method}"

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])