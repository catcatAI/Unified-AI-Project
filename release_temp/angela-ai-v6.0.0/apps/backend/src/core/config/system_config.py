from typing import Any


class SystemConfig:
    """Manages global system configurations."""

    _config: dict[str, Any] = {
        "ENVIRONMENT": "development",
        "LOG_LEVEL": "INFO",
        "API_VERSION": "v1",
        "HSP_BROKER_HOST": "localhost",
        "HSP_BROKER_PORT": 1883,
        "HSP_BROKER_KEEPALIVE": 60,
        "AGENT_MANAGER_ENABLED": True,
        "TOOL_DISPATCHER_ENABLED": True,
        "MEMORY_MANAGER_ENABLED": True,
    }

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Retrieves a configuration value by key."""
        return cls._config.get(key, default)

    @classmethod
    def set(cls, key: str, value: Any):
        """Sets a configuration value."""
        cls._config[key] = value

    @classmethod
    def load_from_file(cls, file_path: str):
        """Loads configurations from a file (e.g., JSON, YAML).
        Placeholder for actual file loading logic.
        """
        print(f"Loading config from {file_path} (placeholder).")
        # In a real implementation, parse the file and update _config


if __name__ == "__main__":
    # Example Usage
    print(f"Environment: {SystemConfig.get('ENVIRONMENT')}")
    SystemConfig.set("LOG_LEVEL", "DEBUG")
    print(f"Log Level: {SystemConfig.get('LOG_LEVEL')}")
    SystemConfig.load_from_file("config.json")
