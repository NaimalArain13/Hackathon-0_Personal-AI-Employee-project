"""
Logging utility module for the Personal AI Employee system.
Provides consistent logging setup across all components.
"""

import logging
import os
from pathlib import Path


def setup_logger(name: str, level=None, log_file: str = None):
    """
    Set up a logger with consistent formatting for the AI Employee system.

    Args:
        name: Name of the logger (typically the class/module name)
        level: Logging level (uses LOG_LEVEL from environment or defaults to INFO)
        log_file: Optional file path to write logs to (uses LOG_FILE from environment if not provided)

    Returns:
        logging.Logger: Configured logger instance
    """
    # Get logging level from environment or use provided level
    if level is None:
        level_str = os.getenv('LOG_LEVEL', 'INFO')
        level = getattr(logging, level_str.upper(), logging.INFO)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent adding multiple handlers if logger already has handlers
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if enabled)
    log_file_path = log_file or os.getenv('LOG_FILE')
    if log_file_path:
        # Create directory if it doesn't exist
        log_dir = Path(log_file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_action(action_type: str, intent: str, result: str = None, logger=None):
    """
    Log an action taken by the AI Employee system with timestamp, intent, and result.

    Args:
        action_type: Type of action being performed (e.g., "email_send", "linkedin_post")
        intent: The intended action/purpose
        result: The result of the action (can be None initially, updated later)
        logger: Optional logger instance to use
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    log_msg = f"ACTION_LOG: Type={action_type} | Intent='{intent}'"
    if result is not None:
        log_msg += f" | Result='{result}'"

    logger.info(log_msg)


if __name__ == "__main__":
    # Example usage
    logger = setup_logger("ExampleLogger")
    logger.info("Logger setup successfully")

    # Example action logging
    log_action("test_action", "Demonstrate logging functionality", "completed", logger)