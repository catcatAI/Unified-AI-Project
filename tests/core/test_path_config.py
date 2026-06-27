"""
测试模块 - test_path_config

自动生成的测试模块,用于验证系统功能。
"""

import os
from pathlib import Path

from path_config import (  # noqa: E402
    CHECKPOINTS_DIR,
    CONFIGS_DIR,
    DATA_DIR,
    MODELS_DIR,
    PROJECT_ROOT,
    TRAINING_DIR,
    get_data_path,
    get_training_config_path,
    resolve_path,
)


def test_project_root_exists() -> None:
    """Test that PROJECT_ROOT is defined and exists."""
    assert isinstance(PROJECT_ROOT, Path)
    assert PROJECT_ROOT.exists()


def test_directory_paths_defined() -> None:
    """Test that all directory paths are defined."""
    assert isinstance(DATA_DIR, Path)
    assert isinstance(TRAINING_DIR, Path)
    assert isinstance(MODELS_DIR, Path)
    assert isinstance(CHECKPOINTS_DIR, Path)
    assert isinstance(CONFIGS_DIR, Path)


def test_directory_hierarchy() -> None:
    """Test that directory hierarchy is correct."""
    assert str(TRAINING_DIR).startswith(str(PROJECT_ROOT))

    assert str(MODELS_DIR).startswith(str(TRAINING_DIR))
    assert str(CHECKPOINTS_DIR).startswith(str(TRAINING_DIR))
    assert str(CONFIGS_DIR).startswith(str(TRAINING_DIR))

    assert str(DATA_DIR).startswith(str(PROJECT_ROOT))


def test_get_data_path() -> None:
    """Test get_data_path function."""
    dataset_name = "test_dataset"
    path = get_data_path(dataset_name)

    assert isinstance(path, Path)
    assert str(path).startswith(str(DATA_DIR))
    assert path.name == dataset_name


def test_get_training_config_path() -> None:
    """Test get_training_config_path function."""
    config_name = "test_config.yaml"
    path = get_training_config_path(config_name)

    assert isinstance(path, Path)
    assert str(path).startswith(str(CONFIGS_DIR))
    assert path.name == config_name


def test_resolve_path_absolute() -> None:
    """Test resolve_path with absolute path."""
    if os.name == "nt":
        abs_path = Path("C:/absolute/test/path")
    else:
        abs_path = Path("/absolute/test/path")
    resolved = resolve_path(str(abs_path))

    assert resolved == abs_path


def test_resolve_path_relative() -> None:
    """Test resolve_path with relative path."""
    rel_path = "relative/test/path"
    resolved = resolve_path(rel_path)

    expected = PROJECT_ROOT / rel_path
    assert resolved == expected


def test_directories_exist() -> None:
    """Test that necessary directories exist."""
    directories = [DATA_DIR, TRAINING_DIR, MODELS_DIR, CHECKPOINTS_DIR, CONFIGS_DIR]
    for directory in directories:
        assert directory.exists(), f"Directory {directory} does not exist"
