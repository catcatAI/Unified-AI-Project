import logging

from apps.backend.src.core.config.path_config import PathConfig
from apps.backend.src.core.config.system_config import SystemConfig


def setup_logging():
    """Sets up the logging configuration for the application."""
    log_level_str = SystemConfig.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Ensure logs directory exists
    PathConfig.ensure_dirs_exist()  # Ensure all configured dirs exist, including LOGS_DIR
    log_file_path = PathConfig.LOGS_DIR / "app.log"

    # Create a logger
    logger = logging.getLogger("unified_ai_backend")
    logger.setLevel(log_level)

    # Create handlers
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    # File handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(log_level)

    # Create formatters and add them to handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to the logger
    if (
        not logger.handlers
    ):  # Avoid adding duplicate handlers if setup_logging is called multiple times
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    logger.info("Logging setup complete.")
    return logger


# Initialize logger when module is imported
logger = setup_logging()

if __name__ == "__main__":
    # Example Usage
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")

    # Test with different log level
    SystemConfig.set("LOG_LEVEL", "DEBUG")
    logger = setup_logging()  # Re-setup logging with new level
    logger.debug("This debug message should now appear.")
