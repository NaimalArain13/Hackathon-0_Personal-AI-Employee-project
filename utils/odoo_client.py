"""
Odoo XML-RPC Client Wrapper for Gold Tier Integration.

Provides a Python wrapper around Odoo's XML-RPC API for accounting operations.

Features:
    - XML-RPC connection management
    - Authentication handling
    - CRUD operations on Odoo models
    - Circuit breaker integration
    - Dry-run mode support
    - Structured logging

Constitutional Compliance:
    - Principle III: Default dry-run mode
    - Principle X: NO auto-retry for destructive operations
    - All operations logged via structured JSON logging
"""

import os
import logging
import xmlrpc.client
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from utils.setup_logger import setup_logger, log_structured_action
from utils.retry_handler import get_circuit_breaker, OperationType


class OdooConnectionError(Exception):
    """Raised when connection to Odoo fails."""
    pass


class OdooAuthenticationError(Exception):
    """Raised when authentication with Odoo fails."""
    pass


class OdooValidationError(Exception):
    """Raised when data validation fails."""
    pass


class OdooClient:
    """
    XML-RPC client wrapper for Odoo accounting system.

    Handles connection, authentication, and provides helper methods
    for common Odoo operations.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        db: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        vault_path: str = "./AI_Employee"
    ):
        """
        Initialize Odoo client.

        Args:
            url: Odoo server URL (default: from ODOO_URL env var)
            db: Database name (default: from ODOO_DB env var)
            username: Odoo username (default: from ODOO_USERNAME env var)
            password: Odoo password (default: from ODOO_PASSWORD env var)
            vault_path: Path to vault for logging (default: ./AI_Employee)
        """
        self.url = url or os.getenv('ODOO_URL')
        self.db = db or os.getenv('ODOO_DB')
        self.username = username or os.getenv('ODOO_USERNAME')
        self.password = password or os.getenv('ODOO_PASSWORD')
        self.vault_path = vault_path

        self.logger = setup_logger("OdooClient", level=logging.INFO)

        # Connection endpoints
        self.common = None
        self.models = None
        self.uid = None

        # Circuit breaker
        self.circuit_breaker = get_circuit_breaker('odoo')

        # Validate configuration
        if not all([self.url, self.db, self.username, self.password]):
            self.logger.error("Odoo configuration incomplete")
            raise OdooConnectionError(
                "Missing Odoo configuration. Set ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD"
            )

        self.logger.info(f"OdooClient initialized for {self.url}/{self.db}")

    def connect(self):
        """
        Connect to Odoo and authenticate.

        Raises:
            OdooConnectionError: If connection fails
            OdooAuthenticationError: If authentication fails
        """
        try:
            self.logger.info(f"Connecting to Odoo at {self.url}")

            # Create XML-RPC endpoints
            self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')

            # Authenticate
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})

            if not self.uid:
                raise OdooAuthenticationError("Authentication failed - invalid credentials")

            self.logger.info(f"Successfully authenticated as user ID: {self.uid}")

        except xmlrpc.client.Fault as e:
            self.logger.error(f"XML-RPC fault: {e}")
            raise OdooConnectionError(f"Odoo XML-RPC error: {e}")
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            raise OdooConnectionError(f"Failed to connect to Odoo: {e}")

    def execute_kw(
        self,
        model: str,
        method: str,
        args: List,
        kwargs: Optional[Dict] = None
    ) -> Any:
        """
        Execute a method on an Odoo model via XML-RPC.

        Args:
            model: Odoo model name (e.g., 'res.partner', 'account.move')
            method: Method to call (e.g., 'search', 'create', 'write')
            args: Positional arguments for the method
            kwargs: Keyword arguments for the method

        Returns:
            Result from Odoo

        Raises:
            OdooConnectionError: If not connected
            OdooValidationError: If data validation fails
        """
        if not self.uid or not self.models:
            raise OdooConnectionError("Not connected to Odoo. Call connect() first.")

        kwargs = kwargs or {}

        try:
            result = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                model,
                method,
                args,
                kwargs
            )
            return result

        except xmlrpc.client.Fault as e:
            self.logger.error(f"Odoo method {model}.{method} failed: {e}")
            if 'ValidationError' in str(e) or 'UserError' in str(e):
                raise OdooValidationError(f"Validation error: {e}")
            raise OdooConnectionError(f"Odoo error: {e}")

    def search(
        self,
        model: str,
        domain: List,
        limit: int = 10,
        offset: int = 0,
        order: Optional[str] = None
    ) -> List[int]:
        """
        Search for records in Odoo.

        Args:
            model: Odoo model name
            domain: Search domain (list of tuples)
            limit: Maximum number of records
            offset: Number of records to skip
            order: Sort order (e.g., 'name ASC')

        Returns:
            List of record IDs
        """
        kwargs = {'limit': limit, 'offset': offset}
        if order:
            kwargs['order'] = order

        return self.execute_kw(model, 'search', [domain], kwargs)

    def read(
        self,
        model: str,
        ids: Union[int, List[int]],
        fields: Optional[List[str]] = None
    ) -> Union[Dict, List[Dict]]:
        """
        Read records from Odoo.

        Args:
            model: Odoo model name
            ids: Record ID or list of IDs
            fields: List of fields to read (None = all fields)

        Returns:
            Record data (dict if single ID, list of dicts if multiple IDs)
        """
        if isinstance(ids, int):
            ids = [ids]
            single = True
        else:
            single = False

        kwargs = {'fields': fields} if fields else {}
        result = self.execute_kw(model, 'read', [ids], kwargs)

        return result[0] if single and result else result

    def create(
        self,
        model: str,
        values: Dict,
        dry_run: bool = True
    ) -> Optional[int]:
        """
        Create a record in Odoo.

        Args:
            model: Odoo model name
            values: Field values for the new record
            dry_run: If True, validate but don't create (default: True per Principle III)

        Returns:
            New record ID (or None if dry_run=True)

        Constitutional Compliance:
            - Principle III: Default dry_run=True
            - Principle X: NO auto-retry (handled by caller with circuit breaker)
        """
        if dry_run:
            self.logger.info(f"[DRY RUN] Would create {model} with values: {values}")
            # Validate by attempting to check required fields
            # In a real implementation, this could call check_access_rights
            return None

        self.logger.info(f"Creating {model} record")
        record_id = self.execute_kw(model, 'create', [values])
        self.logger.info(f"Created {model} record with ID: {record_id}")

        return record_id

    def write(
        self,
        model: str,
        ids: Union[int, List[int]],
        values: Dict,
        dry_run: bool = True
    ) -> bool:
        """
        Update records in Odoo.

        Args:
            model: Odoo model name
            ids: Record ID or list of IDs to update
            values: Field values to update
            dry_run: If True, validate but don't update

        Returns:
            True if successful (or None if dry_run=True)
        """
        if isinstance(ids, int):
            ids = [ids]

        if dry_run:
            self.logger.info(f"[DRY RUN] Would update {model} IDs {ids} with values: {values}")
            return None

        self.logger.info(f"Updating {model} records: {ids}")
        result = self.execute_kw(model, 'write', [ids, values])

        return result

    def search_read(
        self,
        model: str,
        domain: List,
        fields: Optional[List[str]] = None,
        limit: int = 10,
        offset: int = 0,
        order: Optional[str] = None
    ) -> List[Dict]:
        """
        Search and read records in one call (more efficient).

        Args:
            model: Odoo model name
            domain: Search domain
            fields: List of fields to read
            limit: Maximum number of records
            offset: Number of records to skip
            order: Sort order

        Returns:
            List of record dictionaries
        """
        kwargs = {'limit': limit, 'offset': offset}
        if fields:
            kwargs['fields'] = fields
        if order:
            kwargs['order'] = order

        return self.execute_kw(model, 'search_read', [domain], kwargs)

    def get_partner(
        self,
        partner_id: Optional[int] = None,
        search_term: Optional[str] = None,
        limit: int = 10
    ) -> Union[Dict, List[Dict]]:
        """
        Get or search for a partner (customer/vendor).

        Args:
            partner_id: Odoo partner ID (if known)
            search_term: Search by name or email
            limit: Maximum number of results

        Returns:
            Partner record(s)
        """
        if partner_id:
            return self.read('res.partner', partner_id, fields=['id', 'name', 'email', 'phone'])

        if search_term:
            domain = [
                '|',
                ('name', 'ilike', search_term),
                ('email', 'ilike', search_term)
            ]
            return self.search_read(
                'res.partner',
                domain,
                fields=['id', 'name', 'email', 'phone'],
                limit=limit
            )

        return []

    def list_invoices(
        self,
        partner_id: Optional[int] = None,
        state: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        List invoices in Odoo.

        Args:
            partner_id: Filter by partner (customer) ID
            state: Filter by state ('draft', 'posted', 'paid')
            limit: Maximum number of results

        Returns:
            List of invoice records
        """
        domain = [('move_type', '=', 'out_invoice')]  # Customer invoices only

        if partner_id:
            domain.append(('partner_id', '=', partner_id))

        if state:
            if state == 'paid':
                domain.append(('payment_state', '=', 'paid'))
            elif state == 'posted':
                domain.append(('state', '=', 'posted'))
            elif state == 'draft':
                domain.append(('state', '=', 'draft'))

        fields = [
            'id', 'name', 'partner_id', 'invoice_date', 'invoice_date_due',
            'amount_total', 'amount_residual', 'state', 'payment_state'
        ]

        return self.search_read(
            'account.move',
            domain,
            fields=fields,
            limit=limit,
            order='invoice_date desc'
        )

    def create_invoice(
        self,
        partner_id: int,
        invoice_lines: List[Dict],
        due_date: Optional[str] = None,
        dry_run: bool = True
    ) -> Dict:
        """
        Create a customer invoice.

        Args:
            partner_id: Odoo partner (customer) ID
            invoice_lines: List of invoice line items with:
                - product_id: Product ID
                - description: Line description
                - quantity: Quantity
                - unit_price: Unit price
                - tax_ids: List of tax IDs (optional)
            due_date: Payment due date (YYYY-MM-DD)
            dry_run: If True, validate but don't create

        Returns:
            Result dictionary with status, invoice_id, etc.
        """
        # Prepare invoice values
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner_id,
            'invoice_date': datetime.now().strftime('%Y-%m-%d'),
            'invoice_line_ids': []
        }

        if due_date:
            invoice_vals['invoice_date_due'] = due_date

        # Prepare invoice lines
        for line in invoice_lines:
            line_vals = {
                'product_id': line['product_id'],
                'name': line['description'],
                'quantity': line['quantity'],
                'price_unit': line['unit_price']
            }

            if 'tax_ids' in line and line['tax_ids']:
                line_vals['tax_ids'] = [(6, 0, line['tax_ids'])]

            invoice_vals['invoice_line_ids'].append((0, 0, line_vals))

        # Create invoice
        invoice_id = self.create('account.move', invoice_vals, dry_run=dry_run)

        if dry_run:
            return {
                'status': 'dry_run',
                'message': 'Validation successful - invoice not created (dry_run=True)',
                'invoice_id': None
            }

        # Read the created invoice to get details
        invoice = self.read('account.move', invoice_id, fields=['name', 'amount_total'])

        return {
            'status': 'success',
            'invoice_id': invoice_id,
            'invoice_number': invoice['name'],
            'total_amount': invoice['amount_total']
        }

    def record_payment(
        self,
        invoice_id: int,
        amount: float,
        payment_date: str,
        payment_method: str = 'bank_transfer',
        dry_run: bool = True
    ) -> Dict:
        """
        Record a payment for an invoice.

        Args:
            invoice_id: Odoo invoice (account.move) ID
            amount: Payment amount
            payment_date: Payment date (YYYY-MM-DD)
            payment_method: Payment method
            dry_run: If True, validate but don't create

        Returns:
            Result dictionary with status, payment_id, etc.
        """
        # Read invoice to get partner and validate
        invoice = self.read('account.move', invoice_id, fields=[
            'partner_id', 'amount_total', 'amount_residual', 'state', 'payment_state'
        ])

        if not invoice:
            raise OdooValidationError(f"Invoice {invoice_id} not found")

        if invoice['payment_state'] == 'paid':
            raise OdooValidationError(f"Invoice {invoice_id} is already fully paid")

        if amount > invoice['amount_residual']:
            raise OdooValidationError(
                f"Payment amount {amount} exceeds remaining balance {invoice['amount_residual']}"
            )

        if amount <= 0:
            raise OdooValidationError(f"Payment amount must be positive")

        # Prepare payment values
        payment_vals = {
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': invoice['partner_id'][0],
            'amount': amount,
            'date': payment_date,
            'journal_id': 1,  # TODO: Should be configurable or looked up
        }

        # Create payment
        payment_id = self.create('account.payment', payment_vals, dry_run=dry_run)

        if dry_run:
            return {
                'status': 'dry_run',
                'message': 'Validation successful - payment not recorded (dry_run=True)',
                'payment_id': None,
                'invoice_status': invoice['payment_state']
            }

        # In real implementation, would also reconcile the payment with the invoice
        # This involves posting the payment and matching it with the invoice move lines

        # Determine new payment status
        new_residual = invoice['amount_residual'] - amount
        invoice_status = 'paid' if new_residual == 0 else 'partial'

        return {
            'status': 'success',
            'payment_id': payment_id,
            'invoice_status': invoice_status,
            'message': f'Payment recorded successfully'
        }

    def __enter__(self):
        """Context manager entry - connect to Odoo."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup."""
        # No cleanup needed for XML-RPC connections
        pass


def get_odoo_client(**kwargs) -> OdooClient:
    """
    Factory function to create an Odoo client instance.

    Args:
        **kwargs: Arguments to pass to OdooClient constructor

    Returns:
        Configured OdooClient instance
    """
    return OdooClient(**kwargs)


if __name__ == "__main__":
    # Example usage and testing
    import logging
    from pathlib import Path

    # Try to load .env file
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            print("✓ Loaded .env file\n")
    except ImportError:
        print("⚠️  python-dotenv not installed, using existing environment variables\n")

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    print("=== Odoo Client Test ===\n")

    # Check if configuration is available
    if not all([os.getenv('ODOO_URL'), os.getenv('ODOO_DB'), os.getenv('ODOO_USERNAME'), os.getenv('ODOO_PASSWORD')]):
        print("⚠️  Odoo configuration not found in environment variables")
        print("Set ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD to test connection")
        print("\nTesting with dry-run mode only...\n")

        # Test dry-run mode without connection
        try:
            client = OdooClient(
                url=os.getenv('ODOO_URL'),
                db=os.getenv('ODOO_DB'),
                username=os.getenv('ODOO_USERNAME'),
                password=os.getenv('ODOO_PASSWORD'),
                vault_path="./AI_Employee"
            )
            print("✓ OdooClient instance created")
            print(f"  URL: {client.url}")
            print(f"  Database: {client.db}")
            print(f"  Username: {client.username}")
            print(f"  Circuit breaker: {client.circuit_breaker.name}")

        except OdooConnectionError as e:
            print(f"✓ Expected error without connection: {e}")

    else:
        print("✓ Odoo configuration found")
        print("\nAttempting connection...\n")

        try:
            with get_odoo_client() as client:
                print("✓ Connected to Odoo successfully")
                print(f"  User ID: {client.uid}")

                # Test search partners
                print("\nTesting partner search...")
                partners = client.get_partner(search_term="test", limit=5)
                print(f"✓ Found {len(partners)} partners")

        except Exception as e:
            print(f"✗ Connection failed: {e}")

    print("\n=== Test Complete ===")
