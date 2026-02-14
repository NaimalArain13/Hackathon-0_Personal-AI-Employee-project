# Odoo MCP Server API Contract

**Version**: 1.0.0
**Service**: Odoo Community Edition v19+ Integration
**Transport**: MCP stdio (command-line)
**Authentication**: Odoo XML-RPC (database, username, password)

---

## Tools Provided

### 1. `odoo_create_invoice`

Create a customer invoice in Odoo accounting system.

**Parameters**:
```json
{
  "partner_id": {
    "type": "integer",
    "description": "Odoo partner (customer) ID",
    "required": true
  },
  "invoice_lines": {
    "type": "array",
    "description": "List of invoice line items",
    "required": true,
    "items": {
      "product_id": {"type": "integer", "required": true},
      "description": {"type": "string", "required": true},
      "quantity": {"type": "number", "required": true},
      "unit_price": {"type": "number", "required": true},
      "tax_ids": {"type": "array", "items": {"type": "integer"}, "default": []}
    }
  },
  "due_date": {
    "type": "string",
    "format": "date",
    "description": "Payment due date (YYYY-MM-DD)",
    "required": false
  },
  "dry_run": {
    "type": "boolean",
    "description": "If true, validate but don't create",
    "default": true
  }
}
```

**Returns**:
```json
{
  "status": "success | dry_run | error",
  "invoice_id": "integer | null",
  "invoice_number": "string | null",
  "total_amount": "number",
  "message": "string"
}
```

**Errors**:
- `PARTNER_NOT_FOUND`: partner_id doesn't exist in Odoo
- `PRODUCT_NOT_FOUND`: product_id doesn't exist in Odoo
- `VALIDATION_ERROR`: invalid invoice data
- `ODOO_CONNECTION_ERROR`: cannot connect to Odoo server
- `AUTHENTICATION_ERROR`: invalid credentials

**Side Effects**:
- If `dry_run = false`: Creates `account.move` record in Odoo with `state = 'draft'`
- No side effects if `dry_run = true`

**Idempotency**: NOT idempotent (creates new invoice each call)

---

### 2. `odoo_record_payment`

Record a payment for an invoice in Odoo.

**Parameters**:
```json
{
  "invoice_id": {
    "type": "integer",
    "description": "Odoo invoice (account.move) ID",
    "required": true
  },
  "amount": {
    "type": "number",
    "description": "Payment amount",
    "required": true
  },
  "payment_date": {
    "type": "string",
    "format": "date",
    "description": "Payment date (YYYY-MM-DD)",
    "required": true
  },
  "payment_method": {
    "type": "string",
    "enum": ["cash", "bank_transfer", "check", "credit_card"],
    "default": "bank_transfer"
  },
  "dry_run": {
    "type": "boolean",
    "default": true
  }
}
```

**Returns**:
```json
{
  "status": "success | dry_run | error",
  "payment_id": "integer | null",
  "invoice_status": "paid | partial | open",
  "message": "string"
}
```

**Errors**:
- `INVOICE_NOT_FOUND`: invoice_id doesn't exist
- `INVALID_AMOUNT`: amount exceeds invoice total or is negative
- `INVOICE_ALREADY_PAID`: invoice is already fully paid
- `ODOO_CONNECTION_ERROR`
- `AUTHENTICATION_ERROR`

**Side Effects**:
- If `dry_run = false`: Creates `account.payment` record and reconciles with invoice
- Updates invoice `payment_state` to 'paid' or 'partial'

**Idempotency**: NOT idempotent (creates duplicate payments if called multiple times)

---

### 3. `odoo_get_partner`

Get or search for a partner (customer/vendor) in Odoo.

**Parameters**:
```json
{
  "partner_id": {
    "type": "integer",
    "description": "Odoo partner ID (if known)",
    "required": false
  },
  "search": {
    "type": "string",
    "description": "Search by name or email",
    "required": false
  }
}
```

**Returns**:
```json
{
  "status": "success | error",
  "partners": [
    {
      "id": "integer",
      "name": "string",
      "email": "string | null",
      "phone": "string | null",
      "is_company": "boolean"
    }
  ]
}
```

**Errors**:
- `NO_RESULTS`: No partners found matching criteria
- `ODOO_CONNECTION_ERROR`
- `AUTHENTICATION_ERROR`

**Side Effects**: None (read-only)

**Idempotency**: Idempotent (read-only)

---

### 4. `odoo_list_invoices`

List invoices with optional filters.

**Parameters**:
```json
{
  "partner_id": {
    "type": "integer",
    "description": "Filter by partner",
    "required": false
  },
  "state": {
    "type": "string",
    "enum": ["draft", "posted", "paid", "cancel"],
    "description": "Filter by invoice state",
    "required": false
  },
  "date_from": {
    "type": "string",
    "format": "date",
    "required": false
  },
  "date_to": {
    "type": "string",
    "format": "date",
    "required": false
  },
  "limit": {
    "type": "integer",
    "default": 50,
    "maximum": 500
  }
}
```

**Returns**:
```json
{
  "status": "success | error",
  "invoices": [
    {
      "id": "integer",
      "name": "string (invoice number)",
      "partner_name": "string",
      "date": "string (date)",
      "amount_total": "number",
      "amount_residual": "number",
      "state": "string",
      "payment_state": "paid | partial | not_paid"
    }
  ],
  "count": "integer"
}
```

**Errors**:
- `ODOO_CONNECTION_ERROR`
- `AUTHENTICATION_ERROR`

**Side Effects**: None (read-only)

**Idempotency**: Idempotent (read-only)

---

## Configuration (via .mcp.json)

```json
{
  "mcpServers": {
    "odoo": {
      "command": "python",
      "args": [".claude/mcp-servers/odoo-mcp/mcp_server_odoo.py"],
      "env": {
        "ODOO_URL": "${ODOO_URL}",
        "ODOO_DB": "${ODOO_DB}",
        "ODOO_USERNAME": "${ODOO_USERNAME}",
        "ODOO_PASSWORD": "${ODOO_PASSWORD}"
      }
    }
  }
}
```

**Environment Variables** (.env):
```bash
ODOO_URL=http://localhost:8069         # Odoo server URL
ODOO_DB=my_company                     # Database name
ODOO_USERNAME=admin                    # Odoo user
ODOO_PASSWORD=admin_password           # Odoo password
```

---

## Error Handling

### Retry Policy
- **Connection Errors**: Retry with exponential backoff (max 5 attempts)
- **Authentication Errors**: NO retry (requires configuration fix)
- **Validation Errors**: NO retry (requires parameter fix)
- **Destructive Operations** (create_invoice, record_payment): NO auto-retry per Constitutional Principle X

### Circuit Breaker
- **Threshold**: 5 failures in 60 seconds
- **Open Duration**: 30 seconds
- **Half-Open Test**: 1 request after timeout

### Logging
All operations logged to `/Vault/Logs/YYYY-MM-DD.json`:
```json
{
  "timestamp": "2026-02-11T10:30:00.123Z",
  "action": "odoo_create_invoice",
  "actor": "odoo-mcp",
  "parameters": {
    "partner_id": 123,
    "total_amount": 1500.00,
    "dry_run": false
  },
  "result": {
    "status": "success",
    "invoice_id": 456,
    "invoice_number": "INV/2026/0042"
  },
  "approval_status": "human_approved",
  "duration_ms": 1234
}
```

---

## Testing

### Unit Tests
- Mock Odoo XML-RPC responses
- Test parameter validation
- Test error handling

### Integration Tests
- Requires local Odoo instance (Docker recommended)
- Test full workflow: create invoice → record payment
- Test dry_run mode
- Test error scenarios (invalid partner, etc.)

### Test Data
```bash
# Odoo Docker setup for testing
docker run -d -e POSTGRES_USER=odoo -e POSTGRES_PASSWORD=odoo -e POSTGRES_DB=postgres --name db postgres:15
docker run -p 8069:8069 --name odoo --link db:db -t odoo:19.0
```

---

## Security Considerations

1. **Credentials**: Never log passwords; use env vars only
2. **SQL Injection**: Not applicable (Odoo API handles queries)
3. **Authorization**: Rely on Odoo's built-in access control
4. **Audit Trail**: All operations logged with approval status
5. **Dry Run Default**: `dry_run = true` prevents accidental operations

---

## Rate Limits

Odoo XML-RPC has no built-in rate limits, but we impose:
- **Max 100 requests/minute** per MCP server instance
- **Max 10 concurrent requests** to prevent overload

---

## Versioning

**Current**: 1.0.0
**Breaking Changes**: Will increment major version
**Odoo Compatibility**: Designed for Odoo 19.0+; may work with 17.0-18.0 with minor adjustments

---

## Future Enhancements (Out of Scope for Gold Tier)

- Banking channel automation (automatic transaction import)
- Expense tracking and categorization
- Multi-currency support
- Advanced reporting and analytics
- Inventory management integration
