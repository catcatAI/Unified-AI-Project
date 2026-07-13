"""
Angela AI Core Test Suite — smoke tests for project structure and key files.
"""

import logging
import os
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent.parent


class TestAngelaCore:
    """Angela AI core structure smoke tests."""

    def test_project_structure(self):
        required_dirs = ["apps/backend", "apps/desktop-app", "tests", "configs"]
        for dir_path in required_dirs:
            assert os.path.isdir(dir_path), f"Missing directory: {dir_path}"

    def test_configuration_files(self):
        config_files = ["requirements.txt", ".env.example", "configs/angela_config.yaml"]
        for config_file in config_files:
            assert os.path.isfile(config_file), f"Missing config: {config_file}"

    def test_live2d_manager_has_key_functions(self):
        live2d_path = project_root / "apps/desktop-app/CubismSdkForWeb-5-r.5/Samples/TypeScript/Demo/src/lapplive2dmanager.ts"
        assert live2d_path.exists(), "Live2D manager not found"
        content = live2d_path.read_text()
        for func in ["public initialize(", "addModel(", "onTap(", "onUpdate("]:
            assert func in content, f"Missing function: {func}"

    def test_api_endpoints_defined(self):
        main_py = project_root / "apps/backend/main.py"
        assert main_py.exists(), "Main backend file not found"
        content = main_py.read_text()
        for endpoint in ['@app.get("/health")', '@app.get("/api/v1/system/status")']:
            assert endpoint in content, f"Missing endpoint: {endpoint}"

    def test_hardware_detection_has_methods(self):
        hardware_js = project_root / "apps/web-live2d-viewer/js/hardware-detection.js"
        assert hardware_js.exists(), "Hardware detection not found"
        content = hardware_js.read_text()
        for method in ["detect()", "_optimizeForHardware", "getOptimalFrameRate("]:
            assert method in content, f"Missing method: {method}"


class TestAngelaSecurity:
    """Security configuration smoke tests."""

    def test_env_template_has_required_vars(self):
        env_example = project_root / ".env.example"
        assert env_example.exists(), "Environment template missing"
        content = env_example.read_text()
        for var in ["ANGELA_KEY_A", "ANGELA_KEY_B", "BACKEND_HOST"]:
            assert var in content, f"Missing env var: {var}"


class TestAngelaPerformance:
    """Performance configuration smoke tests."""

    def test_performance_modes_defined(self):
        perf_js = project_root / "apps/desktop-app/electron_app/js/system-profile.js"
        if perf_js.exists():
            content = perf_js.read_text()
            for method in ["initialize()", "_detectHardware()", "getRecommendedSettings()"]:
                assert method in content, f"Missing method: {method}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
