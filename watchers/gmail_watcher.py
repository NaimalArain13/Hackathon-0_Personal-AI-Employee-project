#!/usr/bin/env python3
"""
Gmail watcher implementation for the Personal AI Employee.
Monitors Gmail inbox for new emails and creates action files in the /Needs_Action folder.
"""

import os
import time
import logging
import pickle
import base64
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add the project root to the path to import from other modules
import sys
from pathlib import Path as PPath
sys.path.insert(0, str(PPath(__file__).parent.parent))

from watchers.base_watcher import BaseWatcher
from utils.setup_logger import setup_logger
from utils.file_utils import create_action_file as create_standard_action_file, create_approval_request
from utils.conflict_resolver import get_conflict_resolver
from watchers.utils import get_file_metadata, create_markdown_frontmatter, sanitize_filename, format_timestamp


class GmailWatcher(BaseWatcher):
    """
    Gmail watcher implementation that extends BaseWatcher.
    Uses Gmail API to monitor for new emails and create action items.
    """

    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the Gmail watcher.

        Args:
            vault_path: Path to the Obsidian vault
            check_interval: Interval in seconds to check for new emails
        """
        super().__init__(vault_path, check_interval)
        self.logger = setup_logger("GmailWatcher", level=logging.INFO)

        # Gmail API configuration
        self.client_id = os.getenv('GMAIL_CLIENT_ID')
        self.client_secret = os.getenv('GMAIL_CLIENT_SECRET')
        self.credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', './gmail-token.pickle')
        self.gmail_service = None

        # Track last checked email ID to avoid duplicates
        self.last_checked_email_id = None

        # OAuth2 scopes for Gmail
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.modify'
        ]

        # Initialize running attribute for the run loop
        self.running = True

        self.logger.info("GmailWatcher initialized")

    def authenticate_gmail(self):
        """
        Authenticate with Gmail API using OAuth2 flow.

        Returns:
            Gmail API service object if successful, None otherwise
        """
        creds = None

        # Load existing credentials
        credentials_path = Path(self.credentials_path)
        if credentials_path.exists():
            try:
                with open(credentials_path, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                self.logger.error(f"Error loading credentials: {e}")

        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    self.logger.error(f"Error refreshing credentials: {e}")
                    creds = None

            if not creds:
                # Create credentials from client ID and secret
                client_config = {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"]
                    }
                }

                try:
                    flow = Flow.from_client_config(
                        client_config,
                        scopes=self.scopes,
                        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
                    )
                    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

                    # For headless environments, you might need to handle the authorization URL differently
                    auth_url, _ = flow.authorization_url(prompt='consent')

                    print(f'Please visit this URL to authorize the application: {auth_url}')
                    code = input('Enter the authorization code: ')

                    flow.fetch_token(code=code)
                    creds = flow.credentials

                    # Save the credentials for the next run
                    with open(credentials_path, 'wb') as token:
                        pickle.dump(creds, token)

                except Exception as e:
                    self.logger.error(f"Error during OAuth flow: {e}")
                    return None

        try:
            service = build('gmail', 'v1', credentials=creds)
            return service
        except Exception as e:
            self.logger.error(f"Error building Gmail service: {e}")
            return None

    def connect(self):
        """
        Establish connection to Gmail API.

        Returns:
            True if connection successful, False otherwise
        """
        def _authenticate_operation():
            return self.authenticate_gmail()

        try:
            self.gmail_service = self.exponential_backoff_retry(_authenticate_operation)
            if self.gmail_service:
                self.logger.info("Successfully connected to Gmail API")
                return True
            else:
                self.logger.error("Failed to connect to Gmail API")
                return False
        except Exception as e:
            self.logger.error(f"Failed to connect to Gmail API after retries: {e}")
            return False

    def get_recent_emails(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve recent unread emails from Gmail inbox.

        Args:
            max_results: Maximum number of emails to retrieve

        Returns:
            List of email dictionaries containing metadata and content
        """
        if not self.gmail_service:
            self.logger.error("Gmail service not connected")
            return []

        def _fetch_emails_operation():
            # Query for unread emails
            results = self.gmail_service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            emails = []

            for message in messages:
                msg_id = message['id']

                # Get full message details
                msg = self.gmail_service.users().messages().get(
                    userId='me',
                    id=msg_id
                ).execute()

                # Extract email data
                email_data = self._parse_email_message(msg)
                emails.append(email_data)

            return emails

        try:
            return self.exponential_backoff_retry(_fetch_emails_operation)
        except Exception as e:
            self.logger.error(f"Error retrieving emails after retries: {e}")
            return []

    def _parse_email_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Gmail API message object into structured email data.

        Args:
            message: Raw message object from Gmail API

        Returns:
            Dictionary containing parsed email information
        """
        headers = {}
        for header in message.get('payload', {}).get('headers', []):
            name = header.get('name', '').lower()
            value = header.get('value', '')
            headers[name] = value

        # Extract email parts
        body = ""
        attachments = []

        payload = message.get('payload', {})
        parts = payload.get('parts', [])

        if not parts:
            # Single part message
            body_data = payload.get('body', {}).get('data', '')
            if body_data:
                body = base64.urlsafe_b64decode(body_data).decode('utf-8')
        else:
            # Multi-part message
            for part in parts:
                if part.get('mimeType', '') == 'text/plain':
                    body_data = part.get('body', {}).get('data', '')
                    if body_data:
                        body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                elif part.get('filename'):
                    # Attachment found
                    attachments.append({
                        'filename': part.get('filename'),
                        'mimeType': part.get('mimeType'),
                        'size': part.get('body', {}).get('size', 0)
                    })

        # Parse labels
        labels = message.get('labelIds', [])

        return {
            'id': message['id'],
            'thread_id': message.get('threadId'),
            'snippet': message.get('snippet', ''),
            'subject': headers.get('subject', 'No Subject'),
            'from': headers.get('from', ''),
            'to': headers.get('to', ''),
            'date': headers.get('date', ''),
            'body': body[:1000],  # Limit body length
            'labels': labels,
            'size_estimate': message.get('sizeEstimate', 0),
            'attachments': attachments,
            'timestamp': format_timestamp()
        }

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check for new emails and return them as update objects.

        Returns:
            List of email dictionaries that represent new updates
        """
        def _get_emails_operation():
            if not self.gmail_service:
                if not self.connect():
                    return []
            return self.get_recent_emails(max_results=10)

        try:
            # Use the exponential backoff retry mechanism from BaseWatcher
            return self.exponential_backoff_retry(_get_emails_operation)
        except Exception as e:
            self.logger.error(f"Failed to get emails after retries: {e}")
            return []

    def create_action_file(self, email: Dict[str, Any]) -> Path:
        """
        Create an action file for the given email in the Needs_Action folder.
        For sensitive emails, create an approval request instead.
        Uses conflict resolution to prevent duplicate action items.

        Args:
            email: Email dictionary containing email information

        Returns:
            Path to the created action file
        """
        try:
            # Get conflict resolver instance
            conflict_resolver = get_conflict_resolver(str(self.vault_path))

            # Determine if this email requires approval
            priority = self._determine_priority(email)
            requires_approval = self._requires_approval(email)

            if requires_approval:
                # Create an approval request for sensitive emails
                content = f"""# Approval Request: {email.get('subject', 'No Subject')}

## Email Information
- **Subject**: {email.get('subject', 'No Subject')}
- **From**: {email.get('from', 'Unknown')}
- **Date**: {email.get('date', 'Unknown')}
- **Priority**: {priority}
- **Has Attachments**: {len(email.get('attachments', [])) > 0}

## Email Content Preview
{email.get('body', 'No content available')[:500]}

## Attachments
{self._format_attachments(email.get('attachments', []))}

## Action Required
- Move this file to `/Approved` to approve the response
- Move this file to `/Rejected` to reject the response
"""

                approval_data = {
                    'email_id': email['id'],
                    'subject': email.get('subject', 'No Subject'),
                    'from': email.get('from', 'Unknown'),
                    'body_preview': email.get('body', '')[:200],
                    'priority': priority,
                    'has_attachments': len(email.get('attachments', [])) > 0
                }

                # Check for duplicates before creating approval request
                is_duplicate, existing_path = conflict_resolver.is_duplicate_action_item(
                    content, 'gmail', email.get('from', 'unknown')
                )

                if is_duplicate:
                    self.logger.info(f"Duplicate approval request detected for email from {email.get('from', 'unknown')}, skipping creation")
                    return Path(existing_path) if existing_path else None

                approval_path = create_approval_request(
                    str(self.vault_path),
                    'gmail_response',
                    approval_data,
                    f"Email Response Approval: {email.get('subject', 'No Subject')[:50]}"
                )

                # Register the approval request to prevent future duplicates
                conflict_resolver.register_action_item(
                    content,
                    str(approval_path),
                    'gmail',
                    email.get('from', 'unknown')
                )

                self.logger.info(f"Created approval request for sensitive email: {approval_path}")
                return approval_path
            else:
                # Create a standard action file for regular emails
                subject = email.get('subject', 'no_subject')
                sanitized_subject = sanitize_filename(subject)[:50]  # Limit length
                content = f"""# New Email: {email.get('subject', 'No Subject')}

## Sender Information
- **From**: {email.get('from', 'Unknown')}
- **To**: {email.get('to', 'Unknown')}
- **Date**: {email.get('date', 'Unknown')}

## Email Content
{email.get('body', 'No content available')}

## Attachments
{self._format_attachments(email.get('attachments', []))}

## Action Items
- [ ] Review email content
- [ ] Determine appropriate response
- [ ] Process or escalate as needed

## Suggested Next Steps
1. Analyze the content of this email
2. Determine if any action is required
3. Follow the rules defined in Company_Handbook.md
4. Flag for approval if necessary
"""

                # Check for duplicates before creating action file
                is_duplicate, existing_path = conflict_resolver.is_duplicate_action_item(
                    content, 'gmail', email.get('from', 'unknown')
                )

                if is_duplicate:
                    self.logger.info(f"Duplicate action item detected for email from {email.get('from', 'unknown')}, skipping creation")
                    return Path(existing_path) if existing_path else None

                # Create metadata for the action file
                frontmatter = {
                    'type': 'gmail_message',
                    'email_id': email['id'],
                    'thread_id': email.get('thread_id'),
                    'subject': email.get('subject'),
                    'from': email.get('from'),
                    'to': email.get('to'),
                    'date': email.get('date'),
                    'timestamp': email.get('timestamp'),
                    'size': email.get('size_estimate'),
                    'has_attachments': len(email.get('attachments', [])) > 0,
                    'labels': email.get('labels', []),
                    'status': 'pending',
                    'priority': priority
                }

                action_path = create_standard_action_file(
                    str(self.vault_path / 'Needs_Action'),
                    f"GMAIL_{sanitized_subject}",
                    content,
                    frontmatter
                )

                # Register the action item to prevent future duplicates
                conflict_resolver.register_action_item(
                    content,
                    str(action_path),
                    'gmail',
                    email.get('from', 'unknown')
                )

                self.logger.info(f"Created action file for email: {action_path}")
                return action_path

        except Exception as e:
            self.logger.error(f"Error creating action file for email {email.get('id', 'unknown')}: {e}")
            return None

    def _determine_priority(self, email: Dict[str, Any]) -> str:
        """
        Determine priority level based on email content and sender.

        Args:
            email: Email dictionary

        Returns:
            Priority level ('high', 'medium', 'low')
        """
        subject = email.get('subject', '').lower()
        body = email.get('body', '').lower()
        from_addr = email.get('from', '').lower()

        # Check for high priority indicators
        high_priority_keywords = [
            'urgent', 'asap', 'payment', 'invoice', 'money', 'transfer',
            'important', 'critical', 'emergency', 'immediate'
        ]

        medium_priority_keywords = [
            'meeting', 'schedule', 'request', 'question', 'follow up'
        ]

        # Check subject and body for priority keywords
        email_text = f"{subject} {body}"

        for keyword in high_priority_keywords:
            if keyword in email_text:
                return 'high'

        for keyword in medium_priority_keywords:
            if keyword in email_text:
                return 'medium'

        return 'low'

    def _format_attachments(self, attachments: List[Dict[str, Any]]) -> str:
        """
        Format attachment information for markdown display.

        Args:
            attachments: List of attachment dictionaries

        Returns:
            Formatted string for markdown
        """
        if not attachments:
            return "- No attachments"

        formatted = "### Attachments\n"
        for att in attachments:
            formatted += f"- **{att.get('filename', 'Unknown')}** ({att.get('mimeType', 'Unknown')}, {att.get('size', 0)} bytes)\n"

        return formatted

    def _requires_approval(self, email: Dict[str, Any]) -> bool:
        """
        Determine if an email requires human approval based on content analysis.

        Args:
            email: Email dictionary containing email information

        Returns:
            True if the email requires approval, False otherwise
        """
        subject = email.get('subject', '').lower()
        body = email.get('body', '').lower()
        sender = email.get('from', '').lower()

        # Keywords that indicate the email might need approval
        approval_keywords = [
            # Emotional/controversial content
            'complaint', 'angry', 'disappointed', 'frustrated', 'concerned',
            'unhappy', 'dissatisfied', 'terrible', 'awful', 'horrible',

            # Legal matters
            'legal', 'lawyer', 'lawsuit', 'contract', 'agreement', 'terms',
            'liability', 'responsibility', 'court', 'attorney',

            # Financial matters
            'payment', 'invoice', 'refund', 'charge', 'money', 'financial',
            'bank', 'account', 'credit', 'debit', 'expense', 'budget',

            # Medical/health
            'medical', 'health', 'doctor', 'hospital', 'medicine', 'prescription',
            'patient', 'treatment', 'condition',

            # Personal/private
            'personal', 'private', 'confidential', 'secret', 'intimate',

            # Urgent/critical
            'urgent', 'emergency', 'critical', 'immediate', 'asap',

            # Authority figures
            'manager', 'director', 'ceo', 'boss', 'supervisor', 'hr', 'human resources'
        ]

        # Check if any approval keywords are in the subject or body
        email_text = f"{subject} {body} {sender}"

        for keyword in approval_keywords:
            if keyword in email_text:
                return True

        # Check for certain sender types that might need approval
        sensitive_senders = [
            'legal@', 'lawyer@', 'ceo@', 'manager@', 'hr@', 'hrdepartment@',
            'compliance@', 'audit@', 'auditdepartment@'
        ]

        for sender_pattern in sensitive_senders:
            if sender_pattern in sender:
                return True

        # If the priority is high, it might need approval
        priority = self._determine_priority(email)
        if priority == 'high':
            return True

        return False

    def run(self):
        """
        Main execution loop for the Gmail watcher.
        Continuously monitors for new emails and creates action files.
        """
        self.logger.info("Starting GmailWatcher...")

        if not self.connect():
            self.logger.error("Cannot start GmailWatcher without valid connection")
            return

        try:
            while self.running:
                # Check for new emails
                new_emails = self.check_for_updates()

                if new_emails:
                    self.logger.info(f"Found {len(new_emails)} new emails")

                    for email in new_emails:
                        # Create action file for each new email
                        action_file_path = self.create_action_file(email)

                        if action_file_path:
                            self.logger.info(f"Created action file: {action_file_path}")

                            # Mark email as read after creating action file
                            def _mark_as_read_operation():
                                return self.gmail_service.users().messages().modify(
                                    userId='me',
                                    id=email['id'],
                                    body={'removeLabelIds': ['UNREAD']}
                                ).execute()

                            try:
                                self.exponential_backoff_retry(_mark_as_read_operation)
                                self.logger.debug(f"Marked email {email['id']} as read")
                            except Exception as e:
                                self.logger.error(f"Error marking email as read after retries: {e}")

                # Wait for the specified interval before checking again
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("GmailWatcher interrupted by user")
        except Exception as e:
            self.logger.error(f"Error in GmailWatcher execution: {e}")

    def stop(self):
        """
        Stop the Gmail watcher.
        """
        self.logger.info("Stopping GmailWatcher...")
        self.running = False


def main():
    """
    Main entry point for the Gmail watcher.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Gmail Watcher for Personal AI Employee')
    parser.add_argument('--vault-path', '-v', default='D:\\\\Obsidian Vaults\\\\AI_Employee_Vault', help='Path to the Obsidian vault')
    parser.add_argument('--check-interval', '-i', type=int, default=60, help='Check interval in seconds')

    args = parser.parse_args()

    # Set up logging
    logger = setup_logger("GmailWatcher", level=logging.INFO)

    # Create and run the watcher
    watcher = GmailWatcher(vault_path=args.vault_path, check_interval=args.check_interval)

    try:
        watcher.run()
    except KeyboardInterrupt:
        logger.info("GmailWatcher interrupted by user")
    except Exception as e:
        logger.error(f"Error running GmailWatcher: {e}")


if __name__ == "__main__":
    main()