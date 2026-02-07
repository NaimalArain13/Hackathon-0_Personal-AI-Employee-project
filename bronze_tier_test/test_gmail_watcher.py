#!/usr/bin/env python3
"""
Test script for Gmail watcher functionality.
This script tests the Gmail watcher without running the full orchestrator.
"""

import os
import sys
from pathlib import Path

# Add the project root to the path to import from other modules
sys.path.insert(0, str(Path(__file__).parent))

from watchers.gmail_watcher import GmailWatcher
from watchers.utils import setup_logger


def test_gmail_connection():
    """
    Test Gmail API connection and basic functionality.
    """
    logger = setup_logger("GmailTest", level=os.getenv('LOG_LEVEL', 'INFO'))

    # Use the vault path from environment or default
    vault_path = os.getenv('VAULT_PATH', 'D:\\\\Obsidian Vaults\\\\AI_Employee_Vault')

    logger.info(f"Testing Gmail watcher with vault path: {vault_path}")

    # Create Gmail watcher instance
    gmail_watcher = GmailWatcher(vault_path=vault_path)

    # Test authentication
    logger.info("Testing Gmail authentication...")
    if gmail_watcher.connect():
        logger.info("✓ Gmail authentication successful")

        # Test email retrieval
        logger.info("Testing email retrieval...")
        emails = gmail_watcher.get_recent_emails(max_results=5)

        if emails:
            logger.info(f"✓ Retrieved {len(emails)} emails")

            # Display basic info about the first email
            first_email = emails[0]
            logger.info(f"First email subject: {first_email.get('subject', 'No subject')}")
            logger.info(f"From: {first_email.get('from', 'Unknown')}")
            logger.info(f"Date: {first_email.get('date', 'Unknown')}")

            # Test action file creation
            logger.info("Testing action file creation...")
            action_file_path = gmail_watcher.create_action_file(first_email)

            if action_file_path:
                logger.info(f"✓ Created action file: {action_file_path}")

                # Verify the file exists
                if action_file_path.exists():
                    logger.info("✓ Action file verified to exist")

                    # Show the beginning of the file
                    with open(action_file_path, 'r', encoding='utf-8') as f:
                        content_preview = f.read(500)  # First 500 chars
                        logger.info(f"Action file preview: {content_preview}...")
                else:
                    logger.error("✗ Action file does not exist")
            else:
                logger.error("✗ Failed to create action file")
        else:
            logger.warning("⚠ No recent emails found to test with")
    else:
        logger.error("✗ Gmail authentication failed")
        logger.error("Please check your Gmail credentials in the .env file")


def main():
    """
    Main test function.
    """
    print("Testing Gmail Watcher...")
    print("=" * 50)

    test_gmail_connection()

    print("=" * 50)
    print("Gmail watcher test completed.")


if __name__ == "__main__":
    main()