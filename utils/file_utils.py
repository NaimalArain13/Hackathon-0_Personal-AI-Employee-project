"""
File utilities module for the Personal AI Employee system.
Provides functions for reading/writing markdown files in the Obsidian vault.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re


def read_markdown_file(file_path: str) -> str:
    """
    Read content from a markdown file.

    Args:
        file_path: Path to the markdown file

    Returns:
        Content of the markdown file as a string
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_markdown_file(file_path: str, content: str, append: bool = False):
    """
    Write content to a markdown file.

    Args:
        file_path: Path to the markdown file
        content: Content to write
        append: Whether to append to the file or overwrite (default: False)
    """
    path = Path(file_path)
    mode = 'a' if append else 'w'

    # Create parent directories if they don't exist
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, mode, encoding='utf-8') as f:
        f.write(content)


def create_action_file(
    base_path: str,
    prefix: str,
    content: str,
    frontmatter: Optional[Dict] = None
) -> Path:
    """
    Create a standardized action file in the vault with optional frontmatter.

    Args:
        base_path: Base directory for the action file
        prefix: Prefix for the file name
        content: Main content of the file
        frontmatter: Optional dictionary of frontmatter properties

    Returns:
        Path to the created file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_prefix = re.sub(r'[^a-zA-Z0-9_-]', '_', prefix)
    filename = f"{safe_prefix}_{timestamp}.md"
    file_path = Path(base_path) / filename

    full_content = ""
    if frontmatter:
        # Add YAML frontmatter
        full_content += "---\n"
        for key, value in frontmatter.items():
            if isinstance(value, str):
                full_content += f"{key}: \"{value}\"\n"
            else:
                full_content += f"{key}: {json.dumps(value) if isinstance(value, (list, dict)) else value}\n"
        full_content += "---\n\n"

    full_content += content

    write_markdown_file(file_path, full_content)
    return file_path


def create_approval_request(
    vault_path: str,
    action_type: str,
    request_data: Dict,
    title: str = "Approval Request"
) -> Path:
    """
    Create a standardized approval request file.

    Args:
        vault_path: Path to the Obsidian vault
        action_type: Type of action requiring approval
        request_data: Data describing the action to be approved
        title: Title for the approval request

    Returns:
        Path to the created approval request file
    """
    approval_path = Path(vault_path) / "Pending_Approval"
    approval_path.mkdir(exist_ok=True)

    from datetime import timedelta
    expiry_time = datetime.now() + timedelta(hours=24)

    frontmatter = {
        "type": "approval_request",
        "action_type": action_type,
        "created": datetime.now().isoformat(),
        "status": "pending",
        "expires": expiry_time.isoformat(),  # Expires in 24 hours
    }

    content = f"# {title}\n\n"
    content += f"## Action Details\n"
    content += f"**Action Type:** {action_type}\n\n"
    content += f"**Request Data:**\n"
    for key, value in request_data.items():
        content += f"- **{key}:** {value}\n"
    content += "\n"
    content += f"## Instructions\n"
    content += f"- Move this file to `/Approved` to approve the action\n"
    content += f"- Move this file to `/Rejected` to reject the action\n\n"

    return create_action_file(
        str(approval_path),
        f"APPROVAL_{action_type.upper()}",
        content,
        frontmatter
    )


def create_plan_document(
    vault_path: str,
    title: str,
    tasks: List[Dict],
    description: str = ""
) -> Path:
    """
    Create a standardized plan document.

    Args:
        vault_path: Path to the Obsidian vault
        title: Title for the plan
        tasks: List of task dictionaries with 'name' and 'description' keys
        description: Optional description for the plan

    Returns:
        Path to the created plan document
    """
    plans_path = Path(vault_path) / "Plans"
    plans_path.mkdir(exist_ok=True)

    frontmatter = {
        "type": "plan_document",
        "title": title,
        "created": datetime.now().isoformat(),
        "status": "pending",
        "total_tasks": len(tasks),
        "completed_tasks": 0,
    }

    content = f"# {title}\n\n"
    if description:
        content += f"## Description\n{description}\n\n"

    content += f"## Tasks\n"
    for i, task in enumerate(tasks, 1):
        task_name = task.get('name', f'Task {i}')
        task_desc = task.get('description', '')
        content += f"- [ ] **{task_name}** - {task_desc}\n"

    return create_action_file(
        str(plans_path),
        f"PLAN_{re.sub(r'[^a-zA-Z0-9_-]', '_', title.upper())}",
        content,
        frontmatter
    )


def scan_for_approval_changes(vault_path: str) -> List[Dict]:
    """
    Scan vault directories for approval status changes.

    Args:
        vault_path: Path to the Obsidian vault

    Returns:
        List of dictionaries representing approval status changes
    """
    changes = []

    vault_path = Path(vault_path)

    # Check Approved and Rejected directories for newly moved files
    for dir_name in ["Approved", "Rejected"]:
        approval_dir = vault_path / dir_name
        if approval_dir.exists():
            for file_path in approval_dir.glob("*.md"):
                # Check if this is a recent change (within last minute)
                if (datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)).seconds < 60:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    changes.append({
                        "file_path": str(file_path),
                        "status": dir_name.lower(),
                        "content": content,
                        "timestamp": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })

    return changes


def get_files_by_pattern(directory: str, pattern: str) -> List[Path]:
    """
    Get files from a directory that match a given pattern.

    Args:
        directory: Directory to search in
        pattern: Pattern to match (substring to search for in filenames)

    Returns:
        List of Paths to matching files
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        return []

    matches = []
    for file_path in dir_path.rglob(f"*{pattern}*"):
        if file_path.is_file():
            matches.append(file_path)

    return matches


if __name__ == "__main__":
    # Example usage
    # This would be used by various components of the AI Employee system
    pass