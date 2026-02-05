import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with the specified name and configuration.

    Args:
        name: Name of the logger
        log_file: Optional file path to write logs to
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding multiple handlers if logger already exists
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def ensure_directory_exists(path: str) -> bool:
    """
    Ensure that a directory exists, creating it if necessary.

    Args:
        path: Path to the directory

    Returns:
        True if directory exists or was created successfully
    """
    dir_path = Path(path)
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}")
        return False


def read_file_safely(file_path: str) -> str:
    """
    Safely read a file, returning empty string if file doesn't exist.

    Args:
        file_path: Path to the file to read

    Returns:
        File contents as string, or empty string if file doesn't exist
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""


def write_file_safely(file_path: str, content: str) -> bool:
    """
    Safely write content to a file.

    Args:
        file_path: Path to the file to write
        content: Content to write to the file

    Returns:
        True if write was successful, False otherwise
    """
    try:
        # Ensure parent directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing file {file_path}: {e}")
        return False


def get_file_metadata(file_path: str) -> Dict[str, Any]:
    """
    Get metadata for a file.

    Args:
        file_path: Path to the file

    Returns:
        Dictionary containing file metadata
    """
    path = Path(file_path)
    stat = path.stat()

    return {
        'name': path.name,
        'size': stat.st_size,
        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'extension': path.suffix,
        'absolute_path': str(path.absolute())
    }


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing potentially problematic characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove or replace problematic characters
    sanitized = filename.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_')
    sanitized = sanitized.replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
    return sanitized


def format_timestamp(timestamp: float = None) -> str:
    """
    Format a timestamp as an ISO 8601 string.

    Args:
        timestamp: Unix timestamp (uses current time if None)

    Returns:
        ISO 8601 formatted timestamp
    """
    if timestamp is None:
        timestamp = datetime.now().timestamp()
    return datetime.fromtimestamp(timestamp).isoformat()


def create_markdown_frontmatter(metadata: Dict[str, Any]) -> str:
    """
    Create YAML frontmatter for a markdown file.

    Args:
        metadata: Dictionary of metadata to include

    Returns:
        Formatted YAML frontmatter string
    """
    frontmatter_lines = ['---']
    for key, value in metadata.items():
        if isinstance(value, str) and (' ' in value or ':' in value):
            frontmatter_lines.append(f"{key}: '{value}'")
        else:
            frontmatter_lines.append(f"{key}: {value}")
    frontmatter_lines.append('---')
    return '\n'.join(frontmatter_lines)


def get_environment_variable(var_name: str, default_value: str = None) -> str:
    """
    Get an environment variable with an optional default value.

    Args:
        var_name: Name of the environment variable
        default_value: Default value if variable is not set

    Returns:
        Value of the environment variable or default value
    """
    return os.environ.get(var_name, default_value)