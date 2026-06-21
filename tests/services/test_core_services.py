"""Test Core Services - FastAPI server tests"""

from pathlib import Path


def test_config_loader_functions():
    """Test config_loader module functions"""
    from app_config_loader import load_config, get_config
    assert load_config.__name__ == 'load_config'
    assert get_config.__name__ == 'get_config'


def test_path_config_import():
    """Test path_config module can be imported"""
    from path_config import PROJECT_ROOT, DATA_DIR, get_data_path
    assert isinstance(PROJECT_ROOT, (str, Path))
    assert isinstance(DATA_DIR, (str, Path))


def test_core_modules_exist():
    """Test core module directory structure"""
    src_path = Path(__file__).resolve().parent.parent.parent / "apps" / "backend" / "src"
    core_path = src_path / "core"
    assert core_path.exists()


def test_services_modules_exist():
    """Test services module directory structure"""
    src_path = Path(__file__).resolve().parent.parent.parent / "apps" / "backend" / "src"
    services_path = src_path / "services"
    assert services_path.exists()