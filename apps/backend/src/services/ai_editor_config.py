"""
Configuration for the AI Editor Service.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class DataProcessingConfig:
    """Configuration for data processing"""

    text_summarization_enabled: bool = True
    text_keyword_extraction_enabled: bool = True
    max_summary_length: int = 200
    max_keywords: int = 10

    code_function_extraction_enabled: bool = True
    code_class_extraction_enabled: bool = True
    code_comment_extraction_enabled: bool = True
    code_docstring_extraction_enabled: bool = True
    code_complexity_analysis_enabled: bool = True

    structured_data_flattening_enabled: bool = True
    max_nesting_depth: int = 10

    app_element_filtering_enabled: bool = True
    max_ui_elements: int = 1000


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution"""

    timeout_seconds: int = 60
    use_execution_monitoring: bool = True
    max_memory_mb: int = 512
    max_cpu_percent: int = 80
    allowed_modules: List[str] = field(
        default_factory=lambda: ["json", "re", "datetime", "collections", "itertools"]
    )
    restricted_modules: List[str] = field(
        default_factory=lambda: ["os", "sys", "subprocess", "socket"]
    )


@dataclass
class AIEditorConfig:
    """Main configuration for AI Editor Service"""

    enabled: bool = True
    log_level: str = "INFO"

    data_processing: DataProcessingConfig = field(default_factory=DataProcessingConfig)
    sandbox: SandboxConfig = field(default_factory=SandboxConfig)

    memory_storage_enabled: bool = True
    max_memory_entries: int = 10000

    max_concurrent_processes: int = 5
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300

    input_validation_enabled: bool = True
    output_sanitization_enabled: bool = True


# Default configuration
DEFAULT_CONFIG = AIEditorConfig()

# Configuration presets for different use cases
CONFIG_PRESETS: Dict[str, AIEditorConfig] = {
    "development": AIEditorConfig(
        log_level="DEBUG",
        data_processing=DataProcessingConfig(
            text_summarization_enabled=True,
            text_keyword_extraction_enabled=True,
            code_complexity_analysis_enabled=True,
        ),
        sandbox=SandboxConfig(timeout_seconds=120, max_memory_mb=1024),
    ),
    "production": AIEditorConfig(
        log_level="INFO",
        data_processing=DataProcessingConfig(
            text_summarization_enabled=True, code_complexity_analysis_enabled=False
        ),
        sandbox=SandboxConfig(timeout_seconds=30, max_memory_mb=256),
    ),
    "high_performance": AIEditorConfig(
        log_level="WARNING",
        data_processing=DataProcessingConfig(
            text_summarization_enabled=False, code_complexity_analysis_enabled=False
        ),
        sandbox=SandboxConfig(timeout_seconds=15, max_memory_mb=128),
        max_concurrent_processes=10,
        cache_enabled=False,
    ),
}


def get_config(preset: str = "development") -> AIEditorConfig:
    """
    Get configuration for the AI Editor Service.

    Args:
        preset: Configuration preset to use ('development', 'production', 'high_performance')

    Returns:
        AIEditorConfig instance
    """
    if preset in CONFIG_PRESETS:
        return CONFIG_PRESETS[preset]
    return DEFAULT_CONFIG


def update_config(config: AIEditorConfig, updates: Dict[str, Any]) -> AIEditorConfig:
    """
    Update configuration with new values.

    Args:
        config: Current configuration
        updates: Dictionary of updates to apply

    Returns:
        Updated configuration
    """
    for key, value in updates.items():
        if hasattr(config, key):
            setattr(config, key, value)
    return config
