"""
Action Executor Module for the Personal AI Employee system.
Ensures that only approved actions are executed, preventing unauthorized actions.

Gold Tier Extensions:
    - Odoo transaction support (invoice, payment)
    - Social media posting (Facebook, Instagram, Twitter)
    - Circuit breaker integration for resilience
    - Dry-run mode for safe testing (Constitutional Principle III)
    - Structured JSON logging for all actions
    - Approval workflow integration for Odoo transactions (T020)
"""

import json
import logging
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from decimal import Decimal
from utils.setup_logger import setup_logger, log_structured_action
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

        # Pending Approval folder (Gold Tier)
        self.pending_approval_folder = self.vault_path / "Pending_Approval"
        self.pending_approval_folder.mkdir(exist_ok=True)

        # Logs folder for checking transaction history
        self.logs_folder = self.vault_path / "Logs"

    # ========== Approval Workflow Methods (T020) ==========

    def is_partner_recurring(self, partner_id: int, lookback_days: int = 90) -> bool:
        """
        Check if a partner has previous transactions (is recurring).

        A partner is considered recurring if there are any successful Odoo transactions
        with this partner_id in the past lookback_days.

        Args:
            partner_id: Odoo partner (customer) ID
            lookback_days: Number of days to look back for transaction history

        Returns:
            True if partner has previous transactions, False otherwise

        Constitutional Compliance:
            - Supports auto-approval logic per Principle II (explicit approval required)
        """
        if not self.logs_folder or not self.logs_folder.exists():
            self.logger.debug(f"Logs folder not found, treating partner {partner_id} as new")
            return False

        try:
            cutoff_date = datetime.now() - timedelta(days=lookback_days)

            # Check log files for transactions with this partner
            for log_file in self.logs_folder.glob("*.json"):
                try:
                    # Check if log file is within lookback period
                    file_date_str = log_file.stem  # e.g., "2026-02-13"
                    file_date = datetime.strptime(file_date_str, "%Y-%m-%d")

                    if file_date < cutoff_date:
                        continue  # Skip old log files

                    # Read and parse log file
                    with open(log_file, 'r') as f:
                        for line in f:
                            try:
                                log_entry = json.loads(line.strip())

                                # Check if this is an Odoo transaction with our partner
                                if (log_entry.get('action') in ['odoo_create_invoice', 'odoo_record_payment'] and
                                    log_entry.get('result', {}).get('status') == 'success' and
                                    log_entry.get('parameters', {}).get('partner_id') == partner_id):

                                    self.logger.debug(f"Found previous transaction for partner {partner_id}")
                                    return True

                            except (json.JSONDecodeError, KeyError) as e:
                                # Skip malformed log entries
                                continue

                except (ValueError, OSError) as e:
                    self.logger.warning(f"Error reading log file {log_file}: {e}")
                    continue

            self.logger.debug(f"No previous transactions found for partner {partner_id}")
            return False

        except Exception as e:
            self.logger.error(f"Error checking partner recurrence: {e}")
            # Conservative approach: treat as new partner if check fails
            return False

    def requires_odoo_approval(
        self,
        amount: float,
        partner_id: int,
        transaction_type: str = "invoice"
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if an Odoo transaction requires human approval.

        Approval Rules (from spec.md):
            - Auto-approve: amount <= $100 AND partner is recurring
            - Require approval: amount > $100 OR partner is new

        Args:
            amount: Transaction amount in USD
            partner_id: Odoo partner (customer) ID
            transaction_type: Type of transaction ('invoice' or 'payment')

        Returns:
            Tuple of (requires_approval: bool, reason: Optional[str])
            reason will be one of: None, "amount_over_threshold", "new_payee", "both"

        Constitutional Compliance:
            - Principle II: Explicit user approval required for sensitive actions
            - Auto-approval only for low-risk recurring transactions (<$100)
        """
        APPROVAL_THRESHOLD = 100.00

        reasons = []

        # Check amount threshold
        if amount > APPROVAL_THRESHOLD:
            reasons.append("amount_over_threshold")

        # Check if partner is new (not recurring)
        if not self.is_partner_recurring(partner_id):
            reasons.append("new_payee")

        if reasons:
            reason = "_and_".join(reasons) if len(reasons) > 1 else reasons[0]
            self.logger.info(
                f"Odoo transaction requires approval: amount=${amount:.2f}, "
                f"partner_id={partner_id}, reason={reason}"
            )
            return True, reason
        else:
            self.logger.info(
                f"Odoo transaction auto-approved: amount=${amount:.2f}, "
                f"partner_id={partner_id} (recurring)"
            )
            return False, None

    def create_approval_request(
        self,
        action_type: str,
        metadata: Dict[str, Any],
        description: str,
        expires_in_hours: int = 48
    ) -> str:
        """
        Create an approval request file for a sensitive action.

        The approval request file is created in Pending_Approval/ folder.
        User must move it to Approved/ folder to execute the action.

        Args:
            action_type: Type of action ('odoo_transaction', 'social_media_post', etc.)
            metadata: Action metadata (transaction details, post content, etc.)
            description: Human-readable description of the action
            expires_in_hours: Number of hours before approval request expires

        Returns:
            Path to the created approval request file

        Constitutional Compliance:
            - Principle II: Explicit user approval required
            - Creates audit trail for approval decisions
        """
        try:
            # Generate unique ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            hash_input = f"{action_type}_{timestamp}_{json.dumps(metadata, sort_keys=True)}"
            hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8]
            approval_id = f"approval_{timestamp}_{hash_value}"

            # Calculate expiration
            created_at = datetime.now()
            expires_at = created_at + timedelta(hours=expires_in_hours)

            # Build frontmatter
            frontmatter = {
                'id': approval_id,
                'type': action_type,
                'created_at': created_at.isoformat(),
                'expires_at': expires_at.isoformat(),
                'status': 'pending'
            }

            # Add metadata fields
            frontmatter.update(metadata)

            # Build approval request content
            content_lines = ["---"]
            for key, value in frontmatter.items():
                if isinstance(value, (dict, list)):
                    content_lines.append(f"{key}: {json.dumps(value)}")
                else:
                    content_lines.append(f"{key}: {value}")
            content_lines.append("---")
            content_lines.append("")
            content_lines.append(f"# Approval Request: {action_type.replace('_', ' ').title()}")
            content_lines.append("")
            content_lines.append(description)
            content_lines.append("")
            content_lines.append("## Instructions")
            content_lines.append("")
            content_lines.append("To **approve** this action:")
            content_lines.append(f"1. Move this file to `Approved/` folder")
            content_lines.append(f"2. The system will automatically execute the action")
            content_lines.append("")
            content_lines.append("To **reject** this action:")
            content_lines.append(f"1. Delete this file from `Pending_Approval/` folder")
            content_lines.append("")
            content_lines.append(f"**Note**: This request expires at {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")

            content = "\n".join(content_lines)

            # Write approval request file
            approval_file_path = self.pending_approval_folder / f"{approval_id}.md"
            with open(approval_file_path, 'w') as f:
                f.write(content)

            self.logger.info(f"Created approval request: {approval_file_path}")

            # Log the approval request
            log_structured_action(
                action="create_approval_request",
                actor="action_executor",
                parameters={
                    'approval_id': approval_id,
                    'action_type': action_type,
                    'expires_in_hours': expires_in_hours
                },
                result={'status': 'created', 'file': str(approval_file_path)},
                approval_status="pending",
                vault_path=str(self.vault_path)
            )

            return str(approval_file_path)

        except Exception as e:
            self.logger.error(f"Error creating approval request: {e}")
            raise

    def check_and_handle_odoo_approval(
        self,
        transaction_type: str,
        amount: float,
        partner_id: int,
        transaction_details: Dict[str, Any]
    ) -> Tuple[str, Optional[str]]:
        """
        Check if Odoo transaction requires approval and handle accordingly.

        Args:
            transaction_type: 'invoice' or 'payment'
            amount: Transaction amount
            partner_id: Odoo partner ID
            transaction_details: Full transaction details for approval request

        Returns:
            Tuple of (approval_status, approval_file_path)
            approval_status: 'auto_approved' | 'pending' | 'error'
            approval_file_path: Path to approval file if pending, None otherwise

        Constitutional Compliance:
            - Principle II: Explicit approval for sensitive transactions
            - Principle III: Default dry-run mode (handled by caller)
        """
        try:
            # Check if approval is required
            requires_approval, reason = self.requires_odoo_approval(
                amount=amount,
                partner_id=partner_id,
                transaction_type=transaction_type
            )

            if not requires_approval:
                # Auto-approved
                self.logger.info(
                    f"Odoo {transaction_type} auto-approved: "
                    f"amount=${amount:.2f}, partner_id={partner_id}"
                )
                return 'auto_approved', None

            # Approval required - create approval request
            self.logger.info(
                f"Odoo {transaction_type} requires approval: "
                f"amount=${amount:.2f}, partner_id={partner_id}, reason={reason}"
            )

            # Build description
            if transaction_type == 'invoice':
                description = f"""
This invoice requires approval before creation in Odoo.

**Transaction Details:**
- **Type**: Invoice
- **Partner ID**: {partner_id}
- **Amount**: ${amount:.2f}
- **Approval Reason**: {reason.replace('_', ' ').title()}

**Transaction Data:**
```json
{json.dumps(transaction_details, indent=2)}
```
"""
            elif transaction_type == 'payment':
                description = f"""
This payment requires approval before recording in Odoo.

**Transaction Details:**
- **Type**: Payment
- **Partner ID**: {partner_id}
- **Amount**: ${amount:.2f}
- **Approval Reason**: {reason.replace('_', ' ').title()}

**Transaction Data:**
```json
{json.dumps(transaction_details, indent=2)}
```
"""
            else:
                description = f"""
This Odoo transaction requires approval.

**Details:**
- **Type**: {transaction_type}
- **Amount**: ${amount:.2f}
- **Partner ID**: {partner_id}
- **Reason**: {reason.replace('_', ' ').title()}
"""

            # Create approval request
            metadata = {
                'transaction_type': transaction_type,
                'amount': amount,
                'partner_id': partner_id,
                'approval_reason': reason,
                'dry_run': True  # Default per Principle III
            }
            metadata.update(transaction_details)

            approval_file = self.create_approval_request(
                action_type='odoo_transaction',
                metadata=metadata,
                description=description,
                expires_in_hours=48
            )

            return 'pending', approval_file

        except Exception as e:
            self.logger.error(f"Error handling Odoo approval: {e}")
            return 'error', None

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
            # Gold Tier action types
            elif action_type == 'social_media_post':
                return self._execute_social_media_post(action_file_path, frontmatter, body)
            elif action_type == 'odoo_transaction':
                return self._execute_odoo_transaction(action_file_path, frontmatter, body)
            else:
                return self._execute_generic_action(action_file_path, frontmatter, body)

        except Exception as e:
            self.logger.error(f"Error executing action {action_file_path}: {e}")
            return False

    def _parse_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
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

    # ========== Gold Tier Action Handlers ==========

    def _execute_social_media_post(self, action_file_path: str, frontmatter: Dict, body: str) -> bool:
        """
        Execute a social media post action (Gold Tier).

        Posts content to Facebook, Instagram, and/or Twitter based on specified platforms.

        Args:
            action_file_path: Path to the action file
            frontmatter: Parsed frontmatter containing:
                - platforms: List of platforms to post to
                - dry_run: Whether to run in dry-run mode (default: true)
            body: Post content

        Returns:
            True if successful, False otherwise

        Constitutional Compliance:
            - Principle III: Default dry-run mode
            - Principle X: NO auto-retry for post creation (destructive)
        """
        start_time = time.time()

        try:
            platforms = frontmatter.get('platforms', [])
            dry_run = frontmatter.get('dry_run', True)  # Default to dry-run per Principle III

            if not platforms:
                self.logger.error("No platforms specified for social media post")
                return False

            self.logger.info(f"Executing social media post to platforms: {platforms} (dry_run={dry_run})")

            # Log the action execution start
            log_params = {
                'platforms': platforms,
                'dry_run': dry_run
            }
            if action_file_path:
                log_params['file'] = action_file_path

            log_structured_action(
                action="social_media_post",
                actor="action_executor",
                parameters=log_params,
                result={'status': 'initiated'},
                approval_status="human_approved",
                vault_path=str(self.vault_path)
            )

            results = {}

            # Post to each platform
            for platform in platforms:
                try:
                    # Get circuit breaker for this platform
                    from utils.retry_handler import get_circuit_breaker

                    cb = get_circuit_breaker(platform.lower())

                    # Execute post with circuit breaker protection
                    def post_action():
                        if dry_run:
                            self.logger.info(f"[DRY RUN] Would post to {platform}: {body[:100]}...")
                            return {'status': 'success', 'dry_run': True}
                        else:
                            # In real implementation, call the appropriate MCP server
                            # For now, log that we would post
                            self.logger.info(f"Posting to {platform} via MCP server")
                            return {'status': 'success', 'platform': platform}

                    result = cb.call(post_action)
                    results[platform] = result

                except Exception as e:
                    self.logger.error(f"Error posting to {platform}: {e}")
                    results[platform] = {'status': 'error', 'error': str(e)}

            # Check if all posts succeeded
            all_success = all(r.get('status') == 'success' for r in results.values())

            duration_ms = int((time.time() - start_time) * 1000)

            # Log the final result
            log_params_final = {
                'platforms': platforms,
                'dry_run': dry_run
            }
            if action_file_path:
                log_params_final['file'] = action_file_path

            log_structured_action(
                action="social_media_post",
                actor="action_executor",
                parameters=log_params_final,
                result={
                    'status': 'success' if all_success else 'partial',
                    'data': results
                },
                approval_status="human_approved",
                duration_ms=duration_ms,
                vault_path=str(self.vault_path)
            )

            if all_success and action_file_path:
                self._move_to_done(action_file_path)

            return all_success

        except Exception as e:
            self.logger.error(f"Error executing social media post: {e}")

            duration_ms = int((time.time() - start_time) * 1000)

            log_params_error = {}
            if action_file_path:
                log_params_error['file'] = action_file_path

            log_structured_action(
                action="social_media_post",
                actor="action_executor",
                parameters=log_params_error,
                result={'status': 'error'},
                approval_status="human_approved",
                duration_ms=duration_ms,
                error=str(e),
                vault_path=str(self.vault_path)
            )

            return False

    def _execute_odoo_transaction(self, action_file_path: str, frontmatter: Dict, body: str) -> bool:
        """
        Execute an Odoo transaction action (Gold Tier).

        Creates invoices or records payments in Odoo accounting system.

        Args:
            action_file_path: Path to the action file
            frontmatter: Parsed frontmatter containing:
                - transaction_type: 'invoice' or 'payment'
                - dry_run: Whether to run in dry-run mode (default: true)
                - Additional transaction-specific parameters
            body: Transaction details/description

        Returns:
            True if successful, False otherwise

        Constitutional Compliance:
            - Principle III: Default dry-run mode
            - Principle X: NO auto-retry for create/payment operations (destructive)
        """
        start_time = time.time()

        try:
            transaction_type = frontmatter.get('transaction_type')
            dry_run = frontmatter.get('dry_run', True)  # Default to dry-run per Principle III

            if not transaction_type:
                self.logger.error("No transaction_type specified for Odoo transaction")
                return False

            self.logger.info(f"Executing Odoo transaction: {transaction_type} (dry_run={dry_run})")

            # Determine approval status (T020)
            approval_status = frontmatter.get('approval_status', 'human_approved')

            # Log the action execution start
            log_params = {
                'transaction_type': transaction_type,
                'dry_run': dry_run,
                'approval_status': approval_status
            }
            if action_file_path:
                log_params['file'] = action_file_path

            log_structured_action(
                action="odoo_transaction",
                actor="action_executor",
                parameters=log_params,
                result={'status': 'initiated'},
                approval_status=approval_status,
                vault_path=str(self.vault_path)
            )

            # Get circuit breaker for Odoo
            from utils.retry_handler import get_circuit_breaker

            cb = get_circuit_breaker('odoo')

            # Execute transaction with circuit breaker protection
            def odoo_action():
                if dry_run:
                    self.logger.info(f"[DRY RUN] Would execute Odoo {transaction_type}")
                    self.logger.info(f"[DRY RUN] Transaction details: {frontmatter}")
                    return {'status': 'success', 'dry_run': True}
                else:
                    # In real implementation, call the Odoo MCP server
                    self.logger.info(f"Executing Odoo {transaction_type} via MCP server")

                    if transaction_type == 'invoice':
                        # Extract invoice parameters
                        partner_id = frontmatter.get('partner_id')
                        amount = frontmatter.get('amount')
                        # Call Odoo MCP server: odoo_create_invoice()
                        return {'status': 'success', 'transaction_type': 'invoice'}
                    elif transaction_type == 'payment':
                        # Extract payment parameters
                        invoice_id = frontmatter.get('invoice_id')
                        amount = frontmatter.get('amount')
                        # Call Odoo MCP server: odoo_record_payment()
                        return {'status': 'success', 'transaction_type': 'payment'}
                    else:
                        return {'status': 'error', 'error': f'Unknown transaction type: {transaction_type}'}

            result = cb.call(odoo_action)

            duration_ms = int((time.time() - start_time) * 1000)

            # Log the final result
            log_params_final = {
                'transaction_type': transaction_type,
                'dry_run': dry_run
            }
            if action_file_path:
                log_params_final['file'] = action_file_path

            log_structured_action(
                action="odoo_transaction",
                actor="action_executor",
                parameters=log_params_final,
                result=result,
                approval_status=approval_status,
                duration_ms=duration_ms,
                vault_path=str(self.vault_path)
            )

            success = result.get('status') == 'success'

            if success and action_file_path:
                self._move_to_done(action_file_path)

            return success

        except Exception as e:
            self.logger.error(f"Error executing Odoo transaction: {e}")

            duration_ms = int((time.time() - start_time) * 1000)

            # Get approval status if available
            approval_status_error = frontmatter.get('approval_status', 'human_approved') if frontmatter else 'unknown'

            log_params_error = {}
            if action_file_path:
                log_params_error['file'] = action_file_path

            log_structured_action(
                action="odoo_transaction",
                actor="action_executor",
                parameters=log_params_error,
                result={'status': 'error'},
                approval_status=approval_status_error,
                duration_ms=duration_ms,
                error=str(e),
                vault_path=str(self.vault_path)
            )

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

    def execute_action_from_approval(self, action_type: str, metadata: Dict, content: str) -> Dict:
        """
        Execute an action from the approval workflow (Gold Tier).

        This method is called by the approval watcher when a file is approved.

        Args:
            action_type: Type of action (e.g., 'social_media_post', 'odoo_transaction')
            metadata: Metadata from YAML frontmatter
            content: Body content of the approval file

        Returns:
            Result dictionary with 'status' key ('success' or 'error')
        """
        start_time = time.time()

        try:
            self.logger.info(f"Executing approved action: {action_type}")

            # Route to appropriate handler
            if action_type == 'social_media_post':
                success = self._execute_social_media_post_from_metadata(metadata, content)
            elif action_type == 'odoo_transaction':
                success = self._execute_odoo_transaction_from_metadata(metadata, content)
            elif action_type == 'gmail_response':
                success = self._execute_gmail_response(None, metadata, content)
            elif action_type == 'whatsapp_response':
                success = self._execute_whatsapp_response(None, metadata, content)
            elif action_type == 'linkedin_post':
                success = self._execute_linkedin_post(None, metadata, content)
            else:
                self.logger.warning(f"Unknown action type: {action_type}, treating as generic")
                success = True

            duration_ms = int((time.time() - start_time) * 1000)

            return {
                'status': 'success' if success else 'error',
                'data': {
                    'action_type': action_type,
                    'duration_ms': duration_ms
                }
            }

        except Exception as e:
            self.logger.error(f"Error executing action {action_type}: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def _execute_social_media_post_from_metadata(self, metadata: Dict, content: str) -> bool:
        """Helper to execute social media post from metadata (no file path)."""
        return self._execute_social_media_post(None, metadata, content)

    def _execute_odoo_transaction_from_metadata(self, metadata: Dict, content: str) -> bool:
        """Helper to execute Odoo transaction from metadata (no file path)."""
        return self._execute_odoo_transaction(None, metadata, content)

    def execute_odoo_transaction_with_approval(
        self,
        transaction_type: str,
        amount: float,
        partner_id: int,
        transaction_details: Dict[str, Any],
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Execute an Odoo transaction with automatic approval checking (T020).

        This method checks if approval is required and:
        - If auto-approved: executes immediately
        - If approval required: creates approval request and returns pending status

        Args:
            transaction_type: 'invoice' or 'payment'
            amount: Transaction amount
            partner_id: Odoo partner ID
            transaction_details: Full transaction details
            dry_run: Whether to run in dry-run mode (default: True per Principle III)

        Returns:
            Dictionary with:
                - status: 'success' | 'pending' | 'error'
                - approval_status: 'auto_approved' | 'pending' | 'human_approved'
                - approval_file: Path to approval file (if pending)
                - data: Transaction result (if executed)

        Constitutional Compliance:
            - Principle II: Explicit approval for sensitive transactions
            - Principle III: Default dry-run mode
            - Principle X: NO auto-retry on failures
        """
        start_time = time.time()

        try:
            self.logger.info(
                f"Processing Odoo {transaction_type}: "
                f"amount=${amount:.2f}, partner_id={partner_id}, dry_run={dry_run}"
            )

            # Check approval requirements
            approval_status, approval_file = self.check_and_handle_odoo_approval(
                transaction_type=transaction_type,
                amount=amount,
                partner_id=partner_id,
                transaction_details=transaction_details
            )

            if approval_status == 'error':
                return {
                    'status': 'error',
                    'error': 'Failed to process approval check',
                    'approval_status': 'error'
                }

            if approval_status == 'pending':
                # Approval required - return pending status
                duration_ms = int((time.time() - start_time) * 1000)

                log_structured_action(
                    action=f"odoo_{transaction_type}",
                    actor="action_executor",
                    parameters={
                        'amount': amount,
                        'partner_id': partner_id,
                        'transaction_type': transaction_type,
                        'dry_run': dry_run
                    },
                    result={'status': 'pending_approval', 'approval_file': approval_file},
                    approval_status='pending',
                    duration_ms=duration_ms,
                    vault_path=str(self.vault_path)
                )

                return {
                    'status': 'pending',
                    'approval_status': 'pending',
                    'approval_file': approval_file,
                    'message': f'Transaction requires human approval. File: {approval_file}'
                }

            # Auto-approved - execute immediately
            self.logger.info(f"Executing auto-approved Odoo {transaction_type}")

            # Build frontmatter for execution
            frontmatter = transaction_details.copy()
            frontmatter['transaction_type'] = transaction_type
            frontmatter['dry_run'] = dry_run
            frontmatter['approval_status'] = 'auto_approved'

            # Execute the transaction
            success = self._execute_odoo_transaction(
                action_file_path=None,
                frontmatter=frontmatter,
                body=f"Auto-approved {transaction_type}"
            )

            duration_ms = int((time.time() - start_time) * 1000)

            if success:
                return {
                    'status': 'success',
                    'approval_status': 'auto_approved',
                    'message': f'Transaction auto-approved and executed successfully',
                    'duration_ms': duration_ms
                }
            else:
                return {
                    'status': 'error',
                    'approval_status': 'auto_approved',
                    'error': 'Transaction execution failed',
                    'duration_ms': duration_ms
                }

        except Exception as e:
            self.logger.error(f"Error executing Odoo transaction with approval: {e}")
            duration_ms = int((time.time() - start_time) * 1000)

            log_structured_action(
                action=f"odoo_{transaction_type}",
                actor="action_executor",
                parameters={
                    'amount': amount,
                    'partner_id': partner_id,
                    'transaction_type': transaction_type
                },
                result={'status': 'error'},
                approval_status='error',
                duration_ms=duration_ms,
                error=str(e),
                vault_path=str(self.vault_path)
            )

            return {
                'status': 'error',
                'error': str(e),
                'approval_status': 'error'
            }

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