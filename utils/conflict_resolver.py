"""
Conflict Resolution Module for the Personal AI Employee system.
Handles detection and resolution of duplicate action items across different channels.
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from utils.setup_logger import setup_logger


class ConflictResolver:
    """
    Class to handle conflict resolution for duplicate action items across channels.
    """

    def __init__(self, vault_path: str):
        """
        Initialize the conflict resolver.

        Args:
            vault_path: Path to the Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.logger = setup_logger("ConflictResolver", level=logging.INFO)

        # Directory to store conflict tracking data
        self.conflict_tracking_dir = self.vault_path / ".tracking"
        self.conflict_tracking_dir.mkdir(exist_ok=True)

        # File to store duplicate tracking
        self.duplicate_tracker_file = self.conflict_tracking_dir / "duplicate_tracker.json"

        # Load existing duplicate tracker
        self.duplicate_tracker = self._load_duplicate_tracker()

    def _load_duplicate_tracker(self) -> Dict:
        """
        Load the duplicate tracker from file.

        Returns:
            Dictionary containing duplicate tracking information
        """
        if self.duplicate_tracker_file.exists():
            try:
                with open(self.duplicate_tracker_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                self.logger.warning(f"Could not load duplicate tracker from {self.duplicate_tracker_file}")
                return {}
        return {}

    def _save_duplicate_tracker(self):
        """Save the duplicate tracker to file."""
        try:
            with open(self.duplicate_tracker_file, 'w', encoding='utf-8') as f:
                json.dump(self.duplicate_tracker, f, indent=2, default=str)
        except IOError as e:
            self.logger.error(f"Could not save duplicate tracker: {e}")

    def _generate_content_hash(self, content: str) -> str:
        """
        Generate a hash of the content for comparison purposes.

        Args:
            content: Content to hash

        Returns:
            Hash of the content
        """
        # Normalize content by removing whitespace and converting to lowercase
        normalized = ' '.join(content.lower().split())
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def _extract_key_content(self, content: str) -> str:
        """
        Extract key content from an action file for duplicate comparison.

        Args:
            content: Full content of the action file

        Returns:
            Key content for comparison
        """
        # Remove frontmatter if present
        lines = content.split('\n')
        if lines and lines[0].strip() == '---':
            # Look for the end of frontmatter
            try:
                end_fm_idx = lines.index('---', 1)
                content = '\n'.join(lines[end_fm_idx + 1:])
            except ValueError:
                pass  # No closing frontmatter

        # Extract key sections for comparison
        key_parts = []

        # Look for common sections in action files
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('# ') or line.startswith('## '):
                # Skip heading lines
                continue
            elif line.startswith('- ') or line.startswith('* '):
                # Include list items (action items)
                key_parts.append(line)
            elif ':' in line and not line.startswith('http'):
                # Include key-value pairs like sender information
                key_parts.append(line)
            elif len(line) > 20:  # Likely body content
                key_parts.append(line)

        return ' '.join(key_parts)

    def is_duplicate_action_item(self, content: str, channel: str, sender_id: str = None) -> Tuple[bool, Optional[str]]:
        """
        Check if an action item is a duplicate of an existing one.

        Args:
            content: Content of the action item
            channel: Channel where the action item originated (e.g., 'gmail', 'whatsapp')
            sender_id: Optional ID of the sender for additional context

        Returns:
            Tuple of (is_duplicate, existing_file_path) where is_duplicate is a boolean
            and existing_file_path is the path to the existing duplicate file (or None)
        """
        # Extract key content for comparison
        key_content = self._extract_key_content(content)
        content_hash = self._generate_content_hash(key_content)

        # Check if we've seen this content hash before
        for existing_hash, record in self.duplicate_tracker.items():
            if existing_hash == content_hash:
                # Same content, check if it's from the same or different channel
                existing_channel = record.get('channel', 'unknown')

                # If it's from the same channel, it's definitely a duplicate
                # If it's from a different channel but same content, it's likely a duplicate
                if existing_channel == channel or self._is_cross_channel_duplicate(record, {'channel': channel, 'sender_id': sender_id}):
                    return True, record.get('file_path')

        return False, None

    def _is_cross_channel_duplicate(self, existing_record: Dict, new_record: Dict) -> bool:
        """
        Determine if a record from one channel is a duplicate of a record from another channel.

        Args:
            existing_record: Existing record information
            new_record: New record information

        Returns:
            True if records are considered duplicates, False otherwise
        """
        existing_channel = existing_record.get('channel', 'unknown')
        new_channel = new_record.get('channel', 'unknown')

        # If both are from the same channel, we shouldn't reach here (handled elsewhere)
        if existing_channel == new_channel:
            return True

        # For cross-channel duplicates, we're more lenient
        # Consider it a duplicate if it's the same content within a reasonable timeframe
        existing_timestamp = existing_record.get('timestamp')
        if existing_timestamp:
            try:
                existing_dt = datetime.fromisoformat(existing_timestamp.replace('Z', '+00:00'))
                time_diff = abs((datetime.now() - existing_dt).total_seconds())

                # If the same content appeared in different channels within 10 minutes, consider it a duplicate
                return time_diff < 600  # 10 minutes in seconds
            except ValueError:
                # If timestamp parsing fails, assume it's not a duplicate
                pass

        return False

    def register_action_item(self, content: str, file_path: str, channel: str, sender_id: str = None) -> bool:
        """
        Register a new action item to track for potential duplicates.

        Args:
            content: Content of the action item
            file_path: Path where the action item file is stored
            channel: Channel where the action item originated
            sender_id: Optional ID of the sender

        Returns:
            True if successfully registered, False otherwise
        """
        try:
            # Extract key content for comparison
            key_content = self._extract_key_content(content)
            content_hash = self._generate_content_hash(key_content)

            # Create record for this action item
            record = {
                'file_path': file_path,
                'channel': channel,
                'sender_id': sender_id,
                'timestamp': datetime.now().isoformat(),
                'content_hash': content_hash
            }

            # Add to duplicate tracker
            self.duplicate_tracker[content_hash] = record

            # Save the updated tracker
            self._save_duplicate_tracker()

            self.logger.debug(f"Registered action item: {file_path} (hash: {content_hash[:8]})")
            return True

        except Exception as e:
            self.logger.error(f"Error registering action item {file_path}: {e}")
            return False

    def resolve_conflicts(self, action_items: List[Dict]) -> List[Dict]:
        """
        Resolve conflicts among a list of action items by identifying and filtering duplicates.

        Args:
            action_items: List of action items to check for conflicts

        Returns:
            List of action items with duplicates filtered out
        """
        unique_items = []
        processed_hashes = set()

        for item in action_items:
            content = item.get('content', '')
            channel = item.get('channel', 'unknown')
            sender_id = item.get('sender_id')

            # Extract key content for comparison
            key_content = self._extract_key_content(content)
            content_hash = self._generate_content_hash(key_content)

            # Check if this is a duplicate
            is_duplicate, existing_path = self.is_duplicate_action_item(content, channel, sender_id)

            if not is_duplicate and content_hash not in processed_hashes:
                # This is a unique item, add it to the list
                unique_items.append(item)
                processed_hashes.add(content_hash)

                # Register it so future duplicates can be detected
                self.register_action_item(content, item.get('file_path', 'unknown'), channel, sender_id)
            else:
                self.logger.info(f"Skipping duplicate action item from {channel} (similar to {existing_path or 'existing item'})")

        return unique_items

    def cleanup_old_records(self, days_to_keep: int = 30):
        """
        Clean up old duplicate tracking records that are no longer needed.

        Args:
            days_to_keep: Number of days to keep records (default: 30)
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days_to_keep)
            old_hashes = []

            for content_hash, record in self.duplicate_tracker.items():
                timestamp_str = record.get('timestamp')
                if timestamp_str:
                    try:
                        record_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        if record_time < cutoff_time:
                            old_hashes.append(content_hash)
                    except ValueError:
                        # If timestamp parsing fails, remove the record
                        old_hashes.append(content_hash)

            # Remove old records
            for hash_val in old_hashes:
                del self.duplicate_tracker[hash_val]

            if old_hashes:
                self.logger.info(f"Cleaned up {len(old_hashes)} old duplicate tracking records")
                self._save_duplicate_tracker()

        except Exception as e:
            self.logger.error(f"Error cleaning up old duplicate records: {e}")


# Global instance for easy access
_resolver_instance = None


def get_conflict_resolver(vault_path: str) -> ConflictResolver:
    """
    Get a singleton instance of the conflict resolver for the given vault path.

    Args:
        vault_path: Path to the Obsidian vault

    Returns:
        ConflictResolver instance
    """
    global _resolver_instance
    if _resolver_instance is None or str(_resolver_instance.vault_path) != str(vault_path):
        _resolver_instance = ConflictResolver(vault_path)
    return _resolver_instance


if __name__ == "__main__":
    # Example usage
    import logging

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Create a temporary vault for testing
    test_vault = Path("./test_vault")
    test_vault.mkdir(exist_ok=True)

    # Create conflict resolver
    resolver = ConflictResolver(str(test_vault))

    # Example action items
    action1 = {
        'content': "# New Email: Meeting Reminder\n\n## Sender Information\n- **From**: boss@company.com\n\n## Email Content\nDon't forget the meeting tomorrow at 10am.\n\n## Action Items\n- [ ] Prepare meeting materials",
        'file_path': "./Needs_Action/email_meeting_reminder.md",
        'channel': 'gmail',
        'sender_id': 'boss@company.com'
    }

    action2 = {
        'content': "# New WhatsApp Message: Boss\n\n## Sender Information\n- **Chat Name**: Boss\n\n## Message Content\nDon't forget the meeting tomorrow at 10am.\n\n## Action Items\n- [ ] Prepare meeting materials",
        'file_path': "./Needs_Action/whatsapp_meeting_reminder.md",
        'channel': 'whatsapp',
        'sender_id': 'boss'
    }

    # Test conflict resolution
    print("Testing conflict resolution...")
    resolved_items = resolver.resolve_conflicts([action1, action2])
    print(f"Original items: 2, Resolved items: {len(resolved_items)}")
    print(f"Is second item a duplicate: {len(resolved_items) == 1}")

    # Clean up
    import shutil
    shutil.rmtree(test_vault, ignore_errors=True)