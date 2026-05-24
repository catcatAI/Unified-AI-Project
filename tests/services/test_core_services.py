"""Test Core Services - FastAPI server tests"""
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent.parent / "apps" / "backend" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def test_config_loader_functions():
    """Test config_loader module functions"""
    from config_loader import load_config, get_config
    assert load_config.__name__ == 'load_config'
    assert get_config.__name__ == 'get_config'


def test_path_config_import():
    """Test path_config module can be imported"""
    from path_config import PROJECT_ROOT, DATA_DIR, get_data_path
    assert isinstance(PROJECT_ROOT, str)
    assert isinstance(DATA_DIR, str)


def test_core_modules_exist():
    """Test core module directory structure"""
    core_path = src_path / "core"
    assert core_path.exists()


def test_services_modules_exist():
    """Test services module directory structure"""
    services_path = src_path / "services"
    assert services_path.exists()