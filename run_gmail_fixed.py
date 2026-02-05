
#!/usr/bin/env python3
"""
Fixed version of Gmail Watcher runner that addresses the missing 'running' attribute issue.
"""
import os
import sys
import time
import signal
from pathlib import Path

# Add the project root to the path to import from other modules
sys.path.insert(0, str(Path(__file__).parent))

from watchers.gmail_watcher import GmailWatcher
from watchers.utils import setup_logger
import logging


class FixedGmailWatcher(GmailWatcher):
    """
    Fixed version of GmailWatcher that properly initializes the running attribute.
    """
    def __init__(self, vault_path: str, check_interval: int = 60):
        super().__init__(vault_path, check_interval)
        # Fix: Initialize the running attribute that the run() method expects
        self.running = True


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print("\nReceived interrupt signal, shutting down gracefully...")
    if 'gmail_watcher' in globals():
        gmail_watcher.running = False


def main():
    # Set up signal handling for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Use the vault path from environment or default
    vault_path = os.getenv('VAULT_PATH', 'D:\\\\Obsidian Vaults\\\\AI_Employee_Vault')

    print(f"Starting fixed Gmail watcher with vault path: {vault_path}")

    # Create Gmail watcher instance with the fix
    gmail_watcher = FixedGmailWatcher(vault_path=vault_path)

    # Connect to Gmail
    if not gmail_watcher.connect():
        print("Cannot start GmailWatcher without valid connection")
        return

    try:
        print("Starting GmailWatcher monitoring (Press Ctrl+C to stop)...")

        check_interval = gmail_watcher.check_interval

        while gmail_watcher.running:
            # Check for new emails
            new_emails = gmail_watcher.check_for_updates()

            if new_emails:
                gmail_watcher.logger.info(f"Found {len(new_emails)} new emails")

                for email in new_emails:
                    # Create action file for each new email
                    action_file_path = gmail_watcher.create_action_file(email)

                    if action_file_path:
                        gmail_watcher.logger.info(f"Created action file: {action_file_path}")

                        # Mark email as read after creating action file
                        try:
                            gmail_watcher.gmail_service.users().messages().modify(
                                userId='me',
                                id=email['id'],
                                body={'removeLabelIds': ['UNREAD']}
                            ).execute()
                            gmail_watcher.logger.debug(f"Marked email {email['id']} as read")
                        except Exception as e:
                            gmail_watcher.logger.error(f"Error marking email as read: {e}")

            # Wait for the specified interval before checking again
            if gmail_watcher.running:  # Check again before sleeping
                time.sleep(check_interval)

    except KeyboardInterrupt:
        print("\nGmailWatcher interrupted by user")
        gmail_watcher.running = False
    except Exception as e:
        print(f"Error in GmailWatcher execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
