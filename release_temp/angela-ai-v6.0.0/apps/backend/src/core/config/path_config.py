from pathlib import Path

# Dynamically find the project root by looking for the 'apps' directory
current_dir = Path(__file__).resolve().parent
project_root = current_dir
while not (Path(project_root) / "apps").exists():
    parent_dir = Path(project_root).parent
    if parent_dir == project_root:  # Reached filesystem root or infinite loop
        raise RuntimeError("Could not find project root containing 'apps' directory.")
    project_root = parent_dir


class PathConfig:
    """Manages important project paths."""

    PROJECT_ROOT: str = project_root

    # Example paths, extend as needed
    LOGS_DIR: Path = Path(PROJECT_ROOT) / "logs"
    DATA_DIR: Path = Path(PROJECT_ROOT) / "data"
    MODEL_CACHE_DIR: Path = Path(PROJECT_ROOT) / "model_cache"
    CONFIGS_DIR: Path = Path(PROJECT_ROOT) / "configs"  # Global configs

    @classmethod
    def get_path(cls, key: str) -> str:
        """Retrieves a configured path by key."""
        if hasattr(cls, key):
            return getattr(cls, key)
        raise AttributeError(f"Path '{key}' not found in PathConfig.")

    @classmethod
    def ensure_dirs_exist(cls):
        """Ensures that all configured directories exist."""
        for attr_name in dir(cls):
            if attr_name.endswith("_DIR") and not attr_name.startswith("__"):
                path = getattr(cls, attr_name)
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
                    print(f"Created directory: {path}")


if __name__ == "__main__":
    # Example Usage
    print(f"Project Root: {PathConfig.PROJECT_ROOT}")
    print(f"Logs Directory: {PathConfig.LOGS_DIR}")

    # Ensure directories exist (will create if they don't)
    PathConfig.ensure_dirs_exist()

    try:
        print(f"Data Directory: {PathConfig.get_path('DATA_DIR')}")
        print(f"Non-existent Path: {PathConfig.get_path('NON_EXISTENT_DIR')}")
    except AttributeError as e:
        print(e)
