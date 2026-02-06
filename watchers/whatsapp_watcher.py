#!/usr/bin/env python3
"""
WhatsApp watcher implementation for the Personal AI Employee.
Monitors WhatsApp for new messages and creates action files in the /Needs_Action folder.
"""

import os
import time
import logging
import json
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError, Error as PlaywrightError

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add the project root to the path to import from other modules
import sys
from pathlib import Path as PPath
sys.path.insert(0, str(PPath(__file__).parent.parent))

from watchers.base_watcher import BaseWatcher
from utils.setup_logger import setup_logger
from utils.file_utils import create_action_file, create_approval_request
from utils.conflict_resolver import get_conflict_resolver


class WhatsAppWatcher(BaseWatcher):
    """
    WhatsApp watcher implementation that extends BaseWatcher.
    Uses Playwright to monitor WhatsApp Web for new messages and create action items.
    """

    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the WhatsApp watcher.

        Args:
            vault_path: Path to the Obsidian vault
            check_interval: Interval in seconds to check for new messages
        """
        super().__init__(vault_path, check_interval)
        self.logger = setup_logger("WhatsAppWatcher", level=logging.INFO)

        # WhatsApp Web configuration
        self.whatsapp_web_url = "https://web.whatsapp.com"

        # Playwright setup
        self.playwright = None
        self.browser = None
        self.page = None
        self.logged_in = False

        # Track processed messages to avoid duplicates
        self.processed_messages = set()

        # Initialize running attribute for the run loop
        self.running = True

        self.logger.info("WhatsAppWatcher initialized")

    def connect(self) -> bool:
        """
        Establish connection to WhatsApp Web using Playwright.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Start Playwright
            self.playwright = sync_playwright().start()

            # Launch browser with stealth options to avoid detection
            self.browser = self.playwright.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox'
                ]
            )

            # Create new page
            self.page = self.browser.new_page()

            # Add stealth script to avoid bot detection
            self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)

            # Navigate to WhatsApp Web
            self.page.goto(self.whatsapp_web_url)

            # Wait for QR code to appear and notify user
            try:
                self.page.wait_for_selector("canvas", timeout=10000)
                self.logger.info("QR code appeared. Please scan it with your phone to log in to WhatsApp Web.")
                print("Please scan the QR code with your phone to log in to WhatsApp Web.")

                # Wait for login to complete
                self.page.wait_for_url("**/chat**", timeout=60000)
                self.logged_in = True
                self.logger.info("Successfully logged into WhatsApp Web")
                return True

            except TimeoutError:
                # Check if already logged in (URL might already be chat page)
                if "chat" in self.page.url:
                    self.logged_in = True
                    self.logger.info("Already logged into WhatsApp Web")
                    return True
                else:
                    self.logger.error("Failed to log into WhatsApp Web - QR code scan timed out")
                    return False

        except Exception as e:
            self.logger.error(f"Error connecting to WhatsApp Web: {e}")
            return False

    def disconnect(self):
        """Close the connection to WhatsApp Web."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.logged_in = False
        self.logger.info("Disconnected from WhatsApp Web")

    def get_new_messages(self) -> List[Dict[str, Any]]:
        """
        Retrieve new messages from WhatsApp Web.

        Returns:
            List of message dictionaries containing metadata and content
        """
        if not self.logged_in:
            if not self.connect():
                return []

        try:
            # Wait for chats to load
            self.page.wait_for_selector('[data-testid="default-user"]', timeout=5000)

            # Get all chat items
            chat_elements = self.page.query_selector_all('div[data-tab="0"] div[tabindex="-1"]')

            messages = []

            for chat_element in chat_elements:
                try:
                    # Extract chat information
                    chat_name_elem = chat_element.query_selector('div:nth-child(2) div:nth-child(1) span[dir="auto"]')
                    if not chat_name_elem:
                        continue

                    chat_name = chat_name_elem.inner_text()

                    # Check for unread messages indicator
                    unread_indicator = chat_element.query_selector('span[data-testid="icon-unread-count"]')
                    has_unread = unread_indicator is not None

                    if not has_unread:
                        continue  # Skip chats without unread messages

                    # Click on the chat to open it and view messages
                    chat_element.click()
                    time.sleep(2)  # Wait for messages to load

                    # Get all message bubbles
                    message_elements = self.page.query_selector_all('div.message-in, div.message-out')

                    for msg_elem in message_elements:
                        # Check if this message has been processed already
                        msg_id = msg_elem.get_attribute('data-id')
                        if msg_id and msg_id in self.processed_messages:
                            continue

                        # Extract message information
                        message_text_elem = msg_elem.query_selector('span.selectable-text')
                        if not message_text_elem:
                            continue

                        message_text = message_text_elem.inner_text()

                        # Skip if message is empty
                        if not message_text.strip():
                            continue

                        # Get timestamp
                        time_elem = msg_elem.query_selector('span[data-testid="msg-time"]')
                        timestamp = time_elem.inner_text() if time_elem else datetime.now().isoformat()

                        # Determine message direction
                        is_outgoing = 'message-out' in msg_elem.get_attribute('class')

                        # Create message object
                        message_obj = {
                            'id': msg_id or f"whatsapp_{int(time.time())}",
                            'chat_name': chat_name,
                            'message': message_text,
                            'timestamp': timestamp,
                            'direction': 'outgoing' if is_outgoing else 'incoming',
                            'type': 'text',
                            'processed_at': datetime.now().isoformat()
                        }

                        # Add to processed messages to avoid duplicates
                        if msg_id:
                            self.processed_messages.add(msg_id)

                        messages.append(message_obj)

                except Exception as e:
                    self.logger.warning(f"Error processing chat: {e}")
                    continue

            return messages

        except Exception as e:
            self.logger.error(f"Error retrieving WhatsApp messages: {e}")
            return []

    def _requires_approval(self, message: Dict[str, Any]) -> bool:
        """
        Determine if a WhatsApp message requires human approval based on content analysis.

        Args:
            message: Message dictionary containing message information

        Returns:
            True if the message requires approval, False otherwise
        """
        message_text = message.get('message', '').lower()
        chat_name = message.get('chat_name', '').lower()

        # Keywords that indicate the message might need approval
        approval_keywords = [
            # Emotional/controversial content
            'complaint', 'angry', 'frustrated', 'concerned',
            'unhappy', 'dissatisfied', 'terrible', 'awful', 'horrible',

            # Business/financial matters
            'payment', 'invoice', 'refund', 'charge', 'money', 'financial',
            'bank', 'account', 'credit', 'debit', 'expense', 'budget',
            'price', 'cost', 'deal', 'offer',

            # Legal matters
            'legal', 'lawyer', 'contract', 'agreement', 'terms',
            'liability', 'responsibility', 'court', 'attorney',

            # Medical/health
            'medical', 'health', 'doctor', 'hospital', 'medicine', 'prescription',
            'patient', 'treatment', 'condition',

            # Personal/private
            'personal', 'private', 'confidential', 'secret', 'intimate',

            # Urgent/critical
            'urgent', 'emergency', 'critical', 'immediate', 'asap',

            # Sensitive topics
            'salary', 'compensation', 'salary', 'payroll', 'hr', 'human resources'
        ]

        # Check if any approval keywords are in the message
        for keyword in approval_keywords:
            if keyword in message_text:
                return True

        # Check for certain contacts that might need approval
        sensitive_contacts = [
            'boss', 'manager', 'ceo', 'hr', 'legal', 'lawyer', 'compliance'
        ]

        for contact in sensitive_contacts:
            if contact in chat_name:
                return True

        return False

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check for new WhatsApp messages and return them as update objects.

        Returns:
            List of message dictionaries that represent new updates
        """
        def _get_messages_operation():
            if not self.logged_in:
                if not self.connect():
                    return []
            return self.get_new_messages()

        try:
            # Use the exponential backoff retry mechanism from BaseWatcher
            return self.exponential_backoff_retry(_get_messages_operation)
        except Exception as e:
            self.logger.error(f"Failed to get WhatsApp messages after retries: {e}")
            return []

    def create_action_file(self, message: Dict[str, Any]) -> Path:
        """
        Create an action file for the given WhatsApp message in the Needs_Action folder.
        Uses conflict resolution to prevent duplicate action items.

        Args:
            message: Message dictionary containing message information

        Returns:
            Path to the created action file
        """
        try:
            # Get conflict resolver instance
            conflict_resolver = get_conflict_resolver(str(self.vault_path))

            # Determine if this message requires approval
            requires_approval = self._requires_approval(message)

            if requires_approval:
                # Create an approval request for sensitive messages
                content = f"""# Approval Request: {message['chat_name']}

## Message Information
- **Chat Name**: {message['chat_name']}
- **Direction**: {message['direction'].title()}
- **Timestamp**: {message['timestamp']}
- **Priority**: {self._determine_priority(message)}

## Message Content Preview
{message['message'][:500]}

## Action Required
- Move this file to `/Approved` to approve the response
- Move this file to `/Rejected` to reject the response
"""

                approval_data = {
                    'message_id': message['id'],
                    'chat_name': message['chat_name'],
                    'message_preview': message['message'][:200],
                    'timestamp': message['timestamp'],
                    'direction': message['direction']
                }

                # Check for duplicates before creating approval request
                is_duplicate, existing_path = conflict_resolver.is_duplicate_action_item(
                    content, 'whatsapp', message['chat_name']
                )

                if is_duplicate:
                    self.logger.info(f"Duplicate approval request detected for chat {message['chat_name']}, skipping creation")
                    return Path(existing_path) if existing_path else None

                approval_path = create_approval_request(
                    str(self.vault_path),
                    'whatsapp_response',
                    approval_data,
                    f"WhatsApp Response Approval: {message['chat_name'][:30]}"
                )

                # Register the approval request to prevent future duplicates
                conflict_resolver.register_action_item(
                    content,
                    str(approval_path),
                    'whatsapp',
                    message['chat_name']
                )

                self.logger.info(f"Created approval request for sensitive WhatsApp message: {approval_path}")
                return approval_path
            else:
                # Create a standard action file for regular messages
                content = f"""# New WhatsApp Message: {message['chat_name']}

## Sender Information
- **Chat Name**: {message['chat_name']}
- **Direction**: {message['direction'].title()}
- **Timestamp**: {message['timestamp']}

## Message Content
{message['message']}

## Action Items
- [ ] Review message content
- [ ] Determine appropriate response
- [ ] Process or escalate as needed

## Suggested Next Steps
1. Analyze the content of this message
2. Determine if any action is required
3. Follow the rules defined in Company_Handbook.md
4. Flag for approval if necessary
"""

                # Check for duplicates before creating action file
                is_duplicate, existing_path = conflict_resolver.is_duplicate_action_item(
                    content, 'whatsapp', message['chat_name']
                )

                if is_duplicate:
                    self.logger.info(f"Duplicate action item detected for chat {message['chat_name']}, skipping creation")
                    return Path(existing_path) if existing_path else None

                # Create metadata for the action file
                frontmatter = {
                    'type': 'whatsapp_message',
                    'message_id': message['id'],
                    'chat_name': message['chat_name'],
                    'timestamp': message['timestamp'],
                    'direction': message['direction'],
                    'status': 'pending',
                    'priority': self._determine_priority(message)
                }

                action_path = create_action_file(
                    str(self.vault_path / 'Needs_Action'),
                    f"WHATSAPP_{message['chat_name'][:20]}",
                    content,
                    frontmatter
                )

                # Register the action item to prevent future duplicates
                conflict_resolver.register_action_item(
                    content,
                    str(action_path),
                    'whatsapp',
                    message['chat_name']
                )

                self.logger.info(f"Created action file for WhatsApp message: {action_path}")
                return action_path

        except Exception as e:
            self.logger.error(f"Error creating action file for WhatsApp message {message.get('id', 'unknown')}: {e}")
            return None

    def _determine_priority(self, message: Dict[str, Any]) -> str:
        """
        Determine priority level based on message content and sender.

        Args:
            message: Message dictionary

        Returns:
            Priority level ('high', 'medium', 'low')
        """
        message_text = message.get('message', '').lower()
        chat_name = message.get('chat_name', '').lower()

        # Check for high priority indicators
        high_priority_keywords = [
            'urgent', 'asap', 'payment', 'invoice', 'money', 'transfer',
            'important', 'critical', 'emergency', 'immediate', 'now'
        ]

        medium_priority_keywords = [
            'meeting', 'schedule', 'request', 'question', 'follow up',
            'appointment', 'deal', 'offer'
        ]

        # Check message text for priority keywords
        msg_text = f"{message_text} {chat_name}"

        for keyword in high_priority_keywords:
            if keyword in msg_text:
                return 'high'

        for keyword in medium_priority_keywords:
            if keyword in msg_text:
                return 'medium'

        return 'low'

    def run(self):
        """
        Main execution loop for the WhatsApp watcher.
        Continuously monitors for new messages and creates action files.
        """
        self.logger.info("Starting WhatsAppWatcher...")

        if not self.connect():
            self.logger.error("Cannot start WhatsAppWatcher without valid connection")
            return

        try:
            while self.running:
                # Check for new messages
                new_messages = self.check_for_updates()

                if new_messages:
                    self.logger.info(f"Found {len(new_messages)} new WhatsApp messages")

                    for message in new_messages:
                        # Create action file for each new message
                        action_file_path = self.create_action_file(message)

                        if action_file_path:
                            self.logger.info(f"Created action file: {action_file_path}")

                # Wait for the specified interval before checking again
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("WhatsAppWatcher interrupted by user")
        except Exception as e:
            self.logger.error(f"Error in WhatsAppWatcher execution: {e}")

    def stop(self):
        """
        Stop the WhatsApp watcher.
        """
        self.logger.info("Stopping WhatsAppWatcher...")
        self.running = False
        self.disconnect()


def main():
    """
    Main entry point for the WhatsApp watcher.
    """
    import argparse

    parser = argparse.ArgumentParser(description='WhatsApp Watcher for Personal AI Employee')
    parser.add_argument('--vault-path', '-v', default='./ai-employee-vault', help='Path to the Obsidian vault')
    parser.add_argument('--check-interval', '-i', type=int, default=60, help='Check interval in seconds')

    args = parser.parse_args()

    # Set up logging
    logger = setup_logger("WhatsAppWatcher", level=logging.INFO)

    # Create and run the watcher
    watcher = WhatsAppWatcher(vault_path=args.vault_path, check_interval=args.check_interval)

    try:
        watcher.run()
    except KeyboardInterrupt:
        logger.info("WhatsAppWatcher interrupted by user")
    except Exception as e:
        logger.error(f"Error running WhatsAppWatcher: {e}")


if __name__ == "__main__":
    main()