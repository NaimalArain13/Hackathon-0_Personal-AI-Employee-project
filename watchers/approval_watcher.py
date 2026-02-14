"""
Approval Workflow Watcher for Gold Tier.

Monitors the Pending_Approval/ and Approved/ directories to detect human approval actions.
When a file is moved from Pending_Approval/ to Approved/, the watcher triggers the
appropriate action (social media post, Odoo transaction, etc.).

Constitutional Compliance:
    - Principle II: Explicit user approval required for sensitive operations
    - Human moves file to Approved/ folder = explicit approval
"""

import os
import time
import yaml
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.setup_logger import setup_logger, log_structured_action


class ApprovalFileHandler(FileSystemEventHandler):
    """
    Handler for file system events in the Approved/ directory.
    Triggers actions when approval files are detected.
    """

    def __init__(self, callback: Callable[[Path], None]):
        """
        Initialize the approval file handler.

        Args:
            callback: Function to call when a file is approved (receives file path)
        """
        super().__init__()
        self.callback = callback
        self.logger = logging.getLogger(self.__class__.__name__)

    def on_created(self, event: FileSystemEvent):
        """
        Handle file creation events in Approved/ directory.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process markdown files
        if file_path.suffix.lower() in ['.md', '.markdown']:
            self.logger.info(f"Approval detected: {file_path.name}")
            try:
                self.callback(file_path)
            except Exception as e:
                self.logger.error(f"Error processing approved file {file_path.name}: {e}")

    def on_moved(self, event: FileSystemEvent):
        """
        Handle file move events (file moved into Approved/ directory).

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        dest_path = Path(event.dest_path)

        # Check if file was moved into Approved/ directory
        if dest_path.suffix.lower() in ['.md', '.markdown']:
            self.logger.info(f"File moved to Approved/: {dest_path.name}")
            try:
                self.callback(dest_path)
            except Exception as e:
                self.logger.error(f"Error processing moved file {dest_path.name}: {e}")


class ApprovalWatcher:
    """
    Approval workflow watcher for Gold Tier.

    Monitors:
        - Pending_Approval/: Files awaiting human approval
        - Approved/: Files that have been approved for execution
    """

    def __init__(self, vault_path: str, action_callback: Optional[Callable] = None):
        """
        Initialize the approval watcher.

        Args:
            vault_path: Path to the Obsidian vault
            action_callback: Optional callback(action_type, params, content) for executing actions
        """
        self.vault_path = Path(vault_path)
        self.logger = setup_logger("ApprovalWatcher", level=logging.INFO)

        # Directory paths
        self.pending_approval_dir = self.vault_path / "Pending_Approval"
        self.approved_dir = self.vault_path / "Approved"
        self.completed_dir = self.vault_path / "Completed"

        # Create directories if they don't exist
        self.pending_approval_dir.mkdir(parents=True, exist_ok=True)
        self.approved_dir.mkdir(parents=True, exist_ok=True)
        self.completed_dir.mkdir(parents=True, exist_ok=True)

        # Watchdog observer
        self.observer = None
        self.action_callback = action_callback

        # Track processed files to avoid duplicates
        self.processed_files = set()

        self.logger.info(f"ApprovalWatcher initialized for vault: {vault_path}")

    def parse_approval_file(self, file_path: Path) -> Optional[Dict]:
        """
        Parse an approval file to extract YAML frontmatter and content.

        Args:
            file_path: Path to the approval file

        Returns:
            Dictionary with 'metadata' and 'content' keys, or None if parsing fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split frontmatter and body
            if not content.startswith('---'):
                self.logger.warning(f"File {file_path.name} has no YAML frontmatter")
                return None

            parts = content.split('---', 2)
            if len(parts) < 3:
                self.logger.warning(f"Invalid frontmatter format in {file_path.name}")
                return None

            # Parse YAML frontmatter
            frontmatter_text = parts[1].strip()
            body_text = parts[2].strip()

            metadata = yaml.safe_load(frontmatter_text)

            return {
                'metadata': metadata,
                'content': body_text,
                'file_path': file_path
            }

        except Exception as e:
            self.logger.error(f"Error parsing approval file {file_path.name}: {e}")
            return None

    def process_approved_file(self, file_path: Path):
        """
        Process a file that has been approved by moving to Approved/ directory.

        Args:
            file_path: Path to the approved file
        """
        # Check if already processed
        if str(file_path) in self.processed_files:
            self.logger.debug(f"File {file_path.name} already processed, skipping")
            return

        # Parse the approval file
        parsed = self.parse_approval_file(file_path)
        if not parsed:
            self.logger.error(f"Failed to parse approved file: {file_path.name}")
            return

        metadata = parsed['metadata']
        content = parsed['content']
        action_type = metadata.get('type')

        self.logger.info(f"Processing approved action: {action_type} from {file_path.name}")

        # Log the approval
        log_structured_action(
            action="approval_detected",
            actor="approval_watcher",
            parameters={
                'file': str(file_path),
                'action_type': action_type,
                'metadata': metadata
            },
            result={'status': 'detected'},
            approval_status="human_approved",
            vault_path=str(self.vault_path)
        )

        # Execute the action if callback is provided
        if self.action_callback:
            try:
                start_time = time.time()

                # Call the action executor
                result = self.action_callback(action_type, metadata, content)

                duration_ms = int((time.time() - start_time) * 1000)

                # Log the execution result
                log_structured_action(
                    action=f"execute_{action_type}",
                    actor="approval_watcher",
                    parameters={
                        'file': file_path.name,
                        'metadata': metadata
                    },
                    result=result,
                    approval_status="human_approved",
                    duration_ms=duration_ms,
                    vault_path=str(self.vault_path)
                )

                # Move to Completed/ on success
                if result.get('status') == 'success':
                    self._move_to_completed(file_path)
                else:
                    self.logger.warning(f"Action execution returned non-success status: {result}")

            except Exception as e:
                self.logger.error(f"Error executing action for {file_path.name}: {e}")

                # Log the error
                log_structured_action(
                    action=f"execute_{action_type}",
                    actor="approval_watcher",
                    parameters={
                        'file': file_path.name,
                        'metadata': metadata
                    },
                    result={'status': 'error'},
                    approval_status="human_approved",
                    error=str(e),
                    vault_path=str(self.vault_path)
                )
        else:
            self.logger.warning("No action callback configured, approval logged but not executed")
            # Still move to completed even without execution (for testing)
            self._move_to_completed(file_path)

        # Mark as processed
        self.processed_files.add(str(file_path))

    def _move_to_completed(self, file_path: Path):
        """
        Move a processed file to the Completed/ directory.

        Args:
            file_path: Path to the file to move
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename_without_ext = file_path.stem
            completed_filename = f"{filename_without_ext}_{timestamp}{file_path.suffix}"
            completed_path = self.completed_dir / completed_filename

            file_path.rename(completed_path)
            self.logger.info(f"Moved {file_path.name} to Completed/ as {completed_filename}")

        except Exception as e:
            self.logger.error(f"Error moving file to Completed/: {e}")

    def scan_approved_directory(self):
        """
        Scan the Approved/ directory for any existing files that need processing.
        This handles files that were approved while the watcher was not running.
        """
        self.logger.info("Scanning Approved/ directory for existing files...")

        try:
            approved_files = list(self.approved_dir.glob('*.md')) + list(self.approved_dir.glob('*.markdown'))

            if approved_files:
                self.logger.info(f"Found {len(approved_files)} existing approved files")
                for file_path in approved_files:
                    self.process_approved_file(file_path)
            else:
                self.logger.info("No existing approved files found")

        except Exception as e:
            self.logger.error(f"Error scanning Approved/ directory: {e}")

    def start(self):
        """
        Start watching the Approved/ directory for new approvals.
        Uses watchdog library for real-time filesystem monitoring.
        """
        self.logger.info("Starting approval watcher...")

        # First, scan for any existing approved files
        self.scan_approved_directory()

        # Set up watchdog observer
        event_handler = ApprovalFileHandler(callback=self.process_approved_file)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.approved_dir), recursive=False)
        self.observer.start()

        self.logger.info(f"Watching directory: {self.approved_dir}")

    def stop(self):
        """Stop watching the filesystem."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.logger.info("Approval watcher stopped")

    def get_pending_approvals(self) -> List[Dict]:
        """
        Get a list of pending approval files.

        Returns:
            List of dictionaries containing pending approval information
        """
        pending = []

        try:
            pending_files = list(self.pending_approval_dir.glob('*.md')) + \
                          list(self.pending_approval_dir.glob('*.markdown'))

            for file_path in pending_files:
                parsed = self.parse_approval_file(file_path)
                if parsed:
                    pending.append({
                        'file': file_path.name,
                        'path': str(file_path),
                        'type': parsed['metadata'].get('type'),
                        'created_at': parsed['metadata'].get('created_at'),
                        'expires_at': parsed['metadata'].get('expires_at')
                    })

        except Exception as e:
            self.logger.error(f"Error getting pending approvals: {e}")

        return pending

    def get_statistics(self) -> Dict:
        """
        Get statistics about the approval workflow.

        Returns:
            Dictionary with approval workflow statistics
        """
        try:
            pending_count = len(list(self.pending_approval_dir.glob('*.md')))
            approved_count = len(list(self.approved_dir.glob('*.md')))
            completed_count = len(list(self.completed_dir.glob('*.md')))

            return {
                'pending_approvals': pending_count,
                'in_approved': approved_count,
                'completed': completed_count,
                'total_processed': len(self.processed_files)
            }

        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}


# Example action executor (to be replaced with real implementation)
def example_action_executor(action_type: str, metadata: Dict, content: str) -> Dict:
    """
    Example action executor for testing.

    Args:
        action_type: Type of action (e.g., 'social_media_post', 'odoo_transaction')
        metadata: Metadata from YAML frontmatter
        content: Body content of the approval file

    Returns:
        Result dictionary with 'status' key
    """
    logger = logging.getLogger("ExampleActionExecutor")
    logger.info(f"Executing action: {action_type}")
    logger.info(f"Metadata: {metadata}")
    logger.info(f"Content preview: {content[:100]}...")

    # Simulate action execution
    time.sleep(0.5)

    return {
        'status': 'success',
        'data': {
            'action_type': action_type,
            'executed_at': datetime.now().isoformat()
        }
    }


if __name__ == "__main__":
    # Example usage and testing
    import signal

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== Approval Watcher Test ===\n")

    # Use AI_Employee vault
    vault_path = Path("./AI_Employee")

    # Initialize approval watcher
    watcher = ApprovalWatcher(
        vault_path=str(vault_path),
        action_callback=example_action_executor
    )

    # Create a test approval file in Pending_Approval/
    print("Creating test approval file in Pending_Approval/...")
    test_file_content = """---
type: social_media_post
platforms: [facebook, instagram, twitter]
created_at: 2026-02-12T14:00:00Z
requires_approval: true
---

# Test Social Media Post

This is a test post for the approval workflow.

**Platforms**: Facebook, Instagram, Twitter
**Action**: Move to Approved/ folder to post, or delete to cancel.
"""

    test_file = vault_path / "Pending_Approval" / "test_post_001.md"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_file_content)

    print(f"Created: {test_file}")
    print("\nTo test the approval workflow:")
    print(f"  1. Move the file to Approved/: mv {test_file} {vault_path}/Approved/")
    print("  2. Watch the watcher process the approval")
    print("\nStarting approval watcher...")
    print("Press Ctrl+C to stop\n")

    # Start watching
    watcher.start()

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n\nStopping approval watcher...")
        watcher.stop()

        # Print statistics
        stats = watcher.get_statistics()
        print("\n=== Statistics ===")
        print(f"Pending approvals: {stats['pending_approvals']}")
        print(f"In Approved/: {stats['in_approved']}")
        print(f"Completed: {stats['completed']}")
        print(f"Total processed: {stats['total_processed']}")

        print("\n=== Test Complete ===")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Keep the watcher running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)
