"""
Logging utility module for the Personal AI Employee system.
Provides consistent logging setup across all components.
Includes structured JSON logging for audit trails (Gold Tier).
"""

import logging
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


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


def log_structured_action(
    action: str,
    actor: str,
    parameters: Dict[str, Any],
    result: Dict[str, Any],
    approval_status: str = "not_required",
    duration_ms: Optional[int] = None,
    error: Optional[str] = None,
    vault_path: str = None
) -> None:
    """
    Log an action in structured JSON format for Gold Tier audit trails.

    Schema:
        - timestamp: ISO 8601 datetime (UTC)
        - action: Action type identifier (e.g., "social_media_post", "odoo_create_invoice")
        - actor: System component performing the action (e.g., "orchestrator", "facebook_mcp")
        - parameters: Action-specific parameters (dict)
        - result: Action result with status and data (dict with 'status' key: 'success'|'error'|'partial')
        - approval_status: "auto_approved" | "human_approved" | "not_required" | "pending"
        - duration_ms: Execution time in milliseconds
        - error: Error message if failed (null if success)

    Args:
        action: Action type identifier
        actor: Component name performing the action
        parameters: Action-specific parameters
        result: Result dictionary with 'status' and optional 'data' keys
        approval_status: Approval workflow status
        duration_ms: Execution duration in milliseconds
        error: Error message if action failed
        vault_path: Override vault path (defaults to VAULT_PATH env var or ./AI_Employee)

    Constitutional Compliance:
        - Principle IX: Comprehensive logging with 90-day retention
        - All external actions must be logged
        - No auto-deletion of logs
    """
    # Get vault path
    if vault_path is None:
        vault_path = os.getenv('VAULT_PATH', './AI_Employee')

    # Create log directory if needed
    log_dir = Path(vault_path) / 'Logs'
    log_dir.mkdir(parents=True, exist_ok=True)

    # Get today's log file (YYYY-MM-DD.json)
    today = datetime.utcnow().strftime('%Y-%m-%d')
    log_file = log_dir / f'{today}.json'

    # Create log entry
    log_entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'action': action,
        'actor': actor,
        'parameters': parameters,
        'result': result,
        'approval_status': approval_status,
        'duration_ms': duration_ms,
        'error': error
    }

    # Append to log file (one JSON object per line)
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            json.dump(log_entry, f, ensure_ascii=False)
            f.write('\n')
    except Exception as e:
        # Fallback to standard logging if JSON logging fails
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to write structured log: {e}")
        logger.info(f"ACTION: {action} | ACTOR: {actor} | STATUS: {result.get('status')}")


def get_log_path(date: datetime = None, vault_path: str = None) -> Path:
    """
    Get the path to a structured log file for a specific date.

    Args:
        date: Date for the log file (defaults to today)
        vault_path: Override vault path (defaults to VAULT_PATH env var)

    Returns:
        Path to the log file (YYYY-MM-DD.json)
    """
    if vault_path is None:
        vault_path = os.getenv('VAULT_PATH', './AI_Employee')

    if date is None:
        date = datetime.utcnow()

    log_dir = Path(vault_path) / 'Logs'
    date_str = date.strftime('%Y-%m-%d')
    return log_dir / f'{date_str}.json'


def read_structured_logs(start_date: datetime, end_date: datetime, vault_path: str = None) -> list:
    """
    Read structured logs for a date range.

    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        vault_path: Override vault path

    Returns:
        List of log entries (dicts)
    """
    if vault_path is None:
        vault_path = os.getenv('VAULT_PATH', './AI_Employee')

    log_dir = Path(vault_path) / 'Logs'
    entries = []

    # Iterate through date range
    current = start_date
    while current <= end_date:
        log_file = get_log_path(current, vault_path)

        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            entries.append(json.loads(line))
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to read log file {log_file}: {e}")

        # Move to next day
        from datetime import timedelta
        current += timedelta(days=1)

    return entries


if __name__ == "__main__":
    # Example usage - Bronze/Silver Tier
    logger = setup_logger("ExampleLogger")
    logger.info("Logger setup successfully")
    log_action("test_action", "Demonstrate logging functionality", "completed", logger)

    # Example usage - Gold Tier structured logging
    log_structured_action(
        action="social_media_post",
        actor="facebook_mcp",
        parameters={
            "platforms": ["facebook"],
            "content": "Test post",
            "scheduled_for": None
        },
        result={
            "status": "success",
            "data": {
                "facebook_post_id": "123456789"
            }
        },
        approval_status="auto_approved",
        duration_ms=2345,
        error=None
    )

    print(f"Structured log written to: {get_log_path()}")