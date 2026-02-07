#!/usr/bin/env python3
"""
Quick test to verify Gmail watcher can authenticate with the provided credentials.
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add the project root to the path to import from other modules
sys.path.insert(0, str(Path(__file__).parent))

from watchers.gmail_watcher import GmailWatcher
from watchers.utils import setup_logger
import logging

def main():
    # Set up logging
    logger = setup_logger("GmailAuthTest", level=logging.INFO)

    # Get vault path from environment
    vault_path = os.getenv('VAULT_PATH', 'D:\\\\Obsidian Vaults\\\\AI_Employee_Vault')

    print("Testing Gmail Authentication...")
    print(f"Using vault path: {vault_path}")
    print(f"GMAIL_CLIENT_ID: {os.getenv('GMAIL_CLIENT_ID', 'Not set')[:20]}...")
    print(f"GMAIL_CLIENT_SECRET: {os.getenv('GMAIL_CLIENT_SECRET', 'Not set')[:10]}...")
    print(f"GMAIL_CREDENTIALS_PATH: {os.getenv('GMAIL_CREDENTIALS_PATH', 'Not set')}")

    # Create Gmail watcher
    gmail_watcher = GmailWatcher(vault_path=vault_path)

    # Try to authenticate
    service = gmail_watcher.authenticate_gmail()

    if service:
        print("\n✓ Gmail authentication successful!")

        # Test fetching basic profile info
        try:
            profile = service.users().getProfile(userId='me').execute()
            print(f"✓ Connected as: {profile.get('emailAddress', 'Unknown')}")

            # Test fetching a few recent messages
            results = service.users().messages().list(
                userId='me',
                maxResults=1
            ).execute()

            messages = results.get('messages', [])
            print(f"✓ Successfully accessed mailbox, found {len(messages)} recent messages")

            if messages:
                # Get details of the first message to verify read access
                msg = service.users().messages().get(
                    userId='me',
                    id=messages[0]['id']
                ).execute()

                # Extract subject
                headers = msg.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                print(f"✓ Successfully read message with subject: {subject[:50]}...")

        except Exception as e:
            print(f"✗ Error testing Gmail functionality: {e}")
    else:
        print("\n✗ Gmail authentication failed!")
        print("Please check:")
        print("- GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in .env")
        print("- Whether the credentials have proper Gmail API permissions")
        print("- Whether the GMAIL_CREDENTIALS_PATH file exists and is valid")

if __name__ == "__main__":
    main()