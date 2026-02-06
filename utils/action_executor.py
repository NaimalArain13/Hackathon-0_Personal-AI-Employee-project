"""
Action Executor Module for the Personal AI Employee system.
Ensures that only approved actions are executed, preventing unauthorized actions.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from utils.setup_logger import setup_logger
from utils.file_utils import read_markdown_file


class ActionExecutor:
    """
    Class to handle execution of actions that have been approved.
    Ensures that only properly approved actions are executed.
    """

    def __init__(self, vault_path: str):
        """
        Initialize the action executor.

        Args:
            vault_path: Path to the Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.logger = setup_logger("ActionExecutor", level=logging.INFO)

        # Approved and Rejected folders
        self.approved_folder = self.vault_path / "Approved"
        self.rejected_folder = self.vault_path / "Rejected"

        # Ensure folders exist
        self.approved_folder.mkdir(exist_ok=True)
        self.rejected_folder.mkdir(exist_ok=True)

    def is_action_approved(self, action_file_path: str) -> bool:
        """
        Check if an action file has been approved by verifying its location.

        Args:
            action_file_path: Path to the action file to check

        Returns:
            True if the action is approved, False otherwise
        """
        file_path = Path(action_file_path)

        # Check if the file exists in the Approved folder
        approved_file = self.approved_folder / file_path.name
        return approved_file.exists()

    def is_action_rejected(self, action_file_path: str) -> bool:
        """
        Check if an action file has been rejected by verifying its location.

        Args:
            action_file_path: Path to the action file to check

        Returns:
            True if the action is rejected, False otherwise
        """
        file_path = Path(action_file_path)

        # Check if the file exists in the Rejected folder
        rejected_file = self.rejected_folder / file_path.name
        return rejected_file.exists()

    def can_execute_action(self, action_file_path: str) -> bool:
        """
        Determine if an action can be executed based on its approval status.

        Args:
            action_file_path: Path to the action file to check

        Returns:
            True if the action can be executed (is approved), False otherwise
        """
        if self.is_action_rejected(action_file_path):
            self.logger.info(f"Action {action_file_path} was rejected - cannot execute")
            return False

        if self.is_action_approved(action_file_path):
            self.logger.info(f"Action {action_file_path} is approved - can execute")
            return True

        self.logger.warning(f"Action {action_file_path} is neither approved nor rejected - cannot execute")
        return False

    def execute_approved_action(self, action_file_path: str) -> bool:
        """
        Execute an action if it has been approved.

        Args:
            action_file_path: Path to the action file to execute

        Returns:
            True if the action was successfully executed, False otherwise
        """
        if not self.can_execute_action(action_file_path):
            self.logger.error(f"Cannot execute action {action_file_path} - not approved")
            return False

        try:
            # Read the action file content
            content = read_markdown_file(action_file_path)

            # Parse frontmatter if present
            frontmatter, body = self._parse_frontmatter(content)

            # Determine action type and execute accordingly
            action_type = frontmatter.get('type', 'generic')
            action_subtype = frontmatter.get('action_type', frontmatter.get('type', 'generic'))

            self.logger.info(f"Executing approved action: {action_type}/{action_subtype}")

            # Execute based on action type
            if action_subtype == 'gmail_response':
                return self._execute_gmail_response(action_file_path, frontmatter, body)
            elif action_subtype == 'whatsapp_response':
                return self._execute_whatsapp_response(action_file_path, frontmatter, body)
            elif action_subtype == 'linkedin_post':
                return self._execute_linkedin_post(action_file_path, frontmatter, body)
            else:
                return self._execute_generic_action(action_file_path, frontmatter, body)

        except Exception as e:
            self.logger.error(f"Error executing action {action_file_path}: {e}")
            return False

    def _parse_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """
        Parse YAML frontmatter from markdown content.

        Args:
            content: Markdown content with potential frontmatter

        Returns:
            Tuple of (frontmatter_dict, content_without_frontmatter)
        """
        lines = content.split('\n')

        if len(lines) >= 3 and lines[0].strip() == '---':
            # Look for closing ---
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    # Extract frontmatter
                    frontmatter_str = '\n'.join(lines[1:i])
                    frontmatter = {}

                    # Simple parsing of frontmatter (key: value format)
                    for fm_line in frontmatter_str.split('\n'):
                        if ':' in fm_line:
                            key, value = fm_line.split(':', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')  # Remove quotes

                            # Try to parse as JSON if it looks like a list or dict
                            if value.startswith('[') or value.startswith('{'):
                                try:
                                    value = json.loads(value)
                                except:
                                    pass  # Keep as string if JSON parsing fails

                            frontmatter[key] = value

                    # Return frontmatter and remaining content
                    remaining_content = '\n'.join(lines[i+1:]).strip()
                    return frontmatter, remaining_content

        # No frontmatter found
        return {}, content

    def _execute_gmail_response(self, action_file_path: str, frontmatter: Dict, body: str) -> bool:
        """
        Execute a Gmail response action.

        Args:
            action_file_path: Path to the action file
            frontmatter: Parsed frontmatter
            body: Content body

        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract email information from frontmatter and body
            email_id = frontmatter.get('email_id')
            subject = frontmatter.get('subject', 'Re: Auto-response')
            to_address = frontmatter.get('from')  # Reply to sender

            if not to_address:
                # Try to extract from body
                import re
                match = re.search(r'- \*\*From\*\*: ([^\n]+)', body)
                if match:
                    to_address = match.group(1)

            if not to_address:
                self.logger.error("Cannot determine recipient for Gmail response")
                return False

            # For now, log that we would send the email
            # In a real implementation, this would call the email MCP server
            self.logger.info(f"Would send Gmail response to {to_address}")

            # Move the action file to Done after execution
            self._move_to_done(action_file_path)

            return True

        except Exception as e:
            self.logger.error(f"Error executing Gmail response: {e}")
            return False

    def _execute_whatsapp_response(self, action_file_path: str, frontmatter: Dict, body: str) -> bool:
        """
        Execute a WhatsApp response action.

        Args:
            action_file_path: Path to the action file
            frontmatter: Parsed frontmatter
            body: Content body

        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract WhatsApp information from frontmatter and body
            chat_name = frontmatter.get('chat_name')

            if not chat_name:
                # Try to extract from body
                import re
                match = re.search(r'- \*\*Chat Name\*\*: ([^\n]+)', body)
                if match:
                    chat_name = match.group(1)

            if not chat_name:
                self.logger.error("Cannot determine chat name for WhatsApp response")
                return False

            # For now, log that we would send the WhatsApp message
            # In a real implementation, this would call the browser MCP server
            self.logger.info(f"Would send WhatsApp response to {chat_name}")

            # Move the action file to Done after execution
            self._move_to_done(action_file_path)

            return True

        except Exception as e:
            self.logger.error(f"Error executing WhatsApp response: {e}")
            return False

    def _execute_linkedin_post(self, action_file_path: str, frontmatter: Dict, body: str) -> bool:
        """
        Execute a LinkedIn post action.

        Args:
            action_file_path: Path to the action file
            frontmatter: Parsed frontmatter
            body: Content body

        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract LinkedIn post information
            content = body

            # For now, log that we would create the LinkedIn post
            # In a real implementation, this would call the browser MCP server
            self.logger.info("Would create LinkedIn post with content")

            # Move the action file to Done after execution
            self._move_to_done(action_file_path)

            return True

        except Exception as e:
            self.logger.error(f"Error executing LinkedIn post: {e}")
            return False

    def _execute_generic_action(self, action_file_path: str, frontmatter: Dict, body: str) -> bool:
        """
        Execute a generic action.

        Args:
            action_file_path: Path to the action file
            frontmatter: Parsed frontmatter
            body: Content body

        Returns:
            True if successful, False otherwise
        """
        try:
            action_type = frontmatter.get('type', 'generic')
            self.logger.info(f"Executing generic action of type: {action_type}")

            # Move the action file to Done after execution
            self._move_to_done(action_file_path)

            return True

        except Exception as e:
            self.logger.error(f"Error executing generic action: {e}")
            return False

    def _move_to_done(self, action_file_path: str) -> bool:
        """
        Move an executed action file to the Done folder.

        Args:
            action_file_path: Path to the action file to move

        Returns:
            True if successful, False otherwise
        """
        try:
            source_path = Path(action_file_path)
            done_folder = self.vault_path / "Done"
            done_folder.mkdir(exist_ok=True)

            destination_path = done_folder / source_path.name

            # Move the file
            source_path.rename(destination_path)
            self.logger.info(f"Moved executed action to Done folder: {destination_path}")

            return True

        except Exception as e:
            self.logger.error(f"Error moving action to Done folder: {e}")
            return False

    def cleanup_expired_approvals(self, days_to_keep: int = 7) -> int:
        """
        Clean up approval request files that have expired.

        Args:
            days_to_keep: Number of days to keep approval requests

        Returns:
            Number of files cleaned up
        """
        import shutil
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleaned_count = 0

        # Check pending approval folder for old files
        pending_folder = self.vault_path / "Pending_Approval"
        if pending_folder.exists():
            for file_path in pending_folder.iterdir():
                if file_path.is_file() and file_path.suffix == '.md':
                    # Check file modification time
                    mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mod_time < cutoff_date:
                        # Move to expired folder
                        expired_folder = self.vault_path / "Expired"
                        expired_folder.mkdir(exist_ok=True)

                        destination = expired_folder / file_path.name
                        file_path.rename(destination)

                        self.logger.info(f"Moved expired approval request: {file_path.name}")
                        cleaned_count += 1

        return cleaned_count


def get_action_executor(vault_path: str) -> ActionExecutor:
    """
    Get a singleton instance of the action executor.

    Args:
        vault_path: Path to the Obsidian vault

    Returns:
        ActionExecutor instance
    """
    return ActionExecutor(vault_path)


if __name__ == "__main__":
    # Example usage
    import logging

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Create an executor instance
    executor = ActionExecutor("./test_vault")

    print("Action Executor initialized")
    print(f"Approved folder: {executor.approved_folder}")
    print(f"Rejected folder: {executor.rejected_folder}")