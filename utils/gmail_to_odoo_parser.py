"""
Gmail to Odoo Parser - Cross-Domain Integration (Phase 6.5, T079–T086).

Detects invoice requests in Gmail emails and creates draft invoice files
in Pending_Approval/ for human review before Odoo invoice creation.

Cross-domain flow:
    Gmail Email → detect_invoice_request()
               → extract_invoice_details()
               → create_invoice_draft()  →  Pending_Approval/INVOICE_draft_*.md
               → [human moves to Approved/]
               → ApprovalWatcher → ActionExecutor._execute_odoo_invoice_from_approval()
               → OdooClient.create_invoice()

Constitutional Compliance:
    - Principle II:  Human approval required before creating any Odoo invoice
    - Principle III: dry_run=True default; only False after explicit human approval
    - Principle IX:  No log deletion; all structured logs retained
    - Principle X:   Invoice creation is a WRITE — never auto-retried
"""

import re
import logging
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

from utils.setup_logger import setup_logger, log_structured_action


# ==================== T080: Invoice Detection Keywords ====================

INVOICE_KEYWORDS = [
    r"\binvoice\b",
    r"\bquote\b",
    r"\bquotation\b",
    r"\bbill\b",
    r"\bplease\s+send\s+invoice\b",
    r"\bsend\s+me\s+an?\s+invoice\b",
    r"\bcan\s+you\s+invoice\b",
    r"\binvoic(?:e|ing)\b",
    r"\bpurchase\s+order\b",
    r"\bproforma\b",
    r"\brequest(?:ing)?\s+an?\s+invoice\b",
    r"\bneed\s+an?\s+invoice\b",
]

# ==================== T081: Detail Extraction Patterns ====================

AMOUNT_PATTERNS = [
    r'\$\s*([\d,]+(?:\.\d{2})?)',
    r'([\d,]+(?:\.\d{2})?)\s*(?:USD|dollars?)',
    r'amount\s*[:\-]\s*\$?([\d,]+(?:\.\d{2})?)',
    r'total\s*[:\-]\s*\$?([\d,]+(?:\.\d{2})?)',
    r'price\s*[:\-]\s*\$?([\d,]+(?:\.\d{2})?)',
    r'cost\s*[:\-]\s*\$?([\d,]+(?:\.\d{2})?)',
]

DUE_DATE_PATTERNS = [
    r'due\s+(?:by\s+|date\s*[:\-]\s*)?([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
    r'due\s+(?:by\s+|date\s*[:\-]\s*)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    r'payment\s+due\s*[:\-]\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
    r'net\s+(\d+)\s+days',
    r'pay\s+within\s+(\d+)\s+days',
]

CUSTOMER_NAME_PATTERNS = [
    r'(?:client|customer|company)\s*[:\-]\s*([A-Z][A-Za-z0-9\s&.,\-]+)',
    r'billing\s+to\s*[:\-]?\s*([A-Z][A-Za-z0-9\s&.,\-]+)',
    r'invoice\s+to\s*[:\-]?\s*([A-Z][A-Za-z0-9\s&.,\-]+)',
]

LINE_ITEM_PATTERN = (
    r'(?P<qty>\d+)\s*(?:[xX×]\s*)?'
    r'(?P<desc>[A-Za-z][A-Za-z0-9\s\-]+?)\s*'
    r'[@\s]+\$?(?P<price>[\d,]+(?:\.\d{2})?)'
)


# ==================== Data Classes ====================

@dataclass
class InvoiceLineItem:
    """A single line item in an invoice."""
    description: str
    quantity: int = 1
    unit_price: float = 0.0

    @property
    def subtotal(self) -> float:
        return round(self.quantity * self.unit_price, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "subtotal": self.subtotal,
        }


@dataclass
class InvoiceDetails:
    """Extracted invoice details from an email."""
    customer_name: str = ""
    customer_email: str = ""
    total_amount: float = 0.0
    line_items: List[InvoiceLineItem] = field(default_factory=list)
    due_date: Optional[str] = None      # ISO YYYY-MM-DD
    description: str = ""
    confidence: float = 0.0             # 0.0–1.0
    raw_email_id: str = ""
    raw_email_subject: str = ""

    @property
    def is_complete(self) -> bool:
        """True when enough data exists to attempt a draft invoice."""
        return bool(self.customer_name or self.customer_email) and self.total_amount > 0


# ==================== T080: Invoice Request Detection ====================

def detect_invoice_request(email: Dict[str, Any]) -> Tuple[bool, float]:
    """
    Detect whether an email contains an invoice request.

    Args:
        email: Parsed email dict from GmailWatcher (subject, body, from, …)

    Returns:
        Tuple[bool, float]: (is_invoice_request, confidence_score 0.0–1.0)
    """
    subject = email.get('subject', '')
    body = email.get('body', '')
    email_text = f"{subject} {body}"

    matched = [p for p in INVOICE_KEYWORDS if re.search(p, email_text, re.IGNORECASE)]

    if not matched:
        return False, 0.0

    # Base confidence from keyword density
    confidence = min(0.4 + len(matched) * 0.1, 0.8)

    # Boost when an amount is also present
    if any(re.search(p, email_text, re.IGNORECASE) for p in AMOUNT_PATTERNS):
        confidence = min(confidence + 0.2, 1.0)

    return True, round(confidence, 2)


# ==================== T081: Invoice Detail Extraction ====================

def extract_invoice_details(email: Dict[str, Any]) -> InvoiceDetails:
    """
    Extract invoice details from an email body using regex patterns.

    Args:
        email: Parsed email dict

    Returns:
        InvoiceDetails dataclass with extracted fields and confidence score
    """
    subject = email.get('subject', '')
    body = email.get('body', '')
    from_addr = email.get('from', '')
    email_text = f"{subject}\n{body}"

    details = InvoiceDetails(
        raw_email_id=email.get('id', ''),
        raw_email_subject=subject,
        description=f"Invoice request via email: {subject}",
    )

    # --- Customer email: parse from sender address ---
    email_match = re.search(r'[\w.+\-]+@[\w.\-]+\.\w+', from_addr)
    if email_match:
        details.customer_email = email_match.group(0)

    # --- Customer name: parse display name from sender (e.g. "John Doe <john@...>") ---
    name_match = re.match(r'^([^<@]+?)\s*<', from_addr.strip())
    if name_match:
        details.customer_name = name_match.group(1).strip().strip('"\'')

    # Override with explicit customer patterns found in the email body
    for pattern in CUSTOMER_NAME_PATTERNS:
        m = re.search(pattern, email_text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip().rstrip('.,')
            if len(candidate) > 2:
                details.customer_name = candidate
            break

    # --- Total amount ---
    for pattern in AMOUNT_PATTERNS:
        m = re.search(pattern, email_text, re.IGNORECASE)
        if m:
            try:
                details.total_amount = float(m.group(1).replace(',', ''))
                break
            except (ValueError, IndexError):
                continue

    # --- Due date ---
    for pattern in DUE_DATE_PATTERNS:
        m = re.search(pattern, email_text, re.IGNORECASE)
        if m:
            raw_date = m.group(1).strip()
            if raw_date.isdigit():
                # "net N days" or "pay within N days"
                details.due_date = (date.today() + timedelta(days=int(raw_date))).isoformat()
            else:
                details.due_date = raw_date
            break

    # Default due date: 30 days from today
    if not details.due_date:
        details.due_date = (date.today() + timedelta(days=30)).isoformat()

    # --- Line items ---
    line_items: List[InvoiceLineItem] = []
    for m in re.finditer(LINE_ITEM_PATTERN, email_text, re.IGNORECASE):
        try:
            line_items.append(InvoiceLineItem(
                description=m.group('desc').strip(),
                quantity=int(m.group('qty')),
                unit_price=float(m.group('price').replace(',', '')),
            ))
        except (ValueError, AttributeError):
            continue

    if line_items:
        details.line_items = line_items
        if details.total_amount == 0:
            details.total_amount = round(sum(i.subtotal for i in line_items), 2)
    elif details.total_amount > 0:
        # Synthetic single line item from the extracted total
        details.line_items = [InvoiceLineItem(
            description=details.description,
            quantity=1,
            unit_price=details.total_amount,
        )]

    # --- Confidence score ---
    score = 0.0
    if details.customer_name or details.customer_email:
        score += 0.3
    if details.total_amount > 0:
        score += 0.4
    if details.line_items:
        score += 0.2
    if details.due_date:
        score += 0.1
    details.confidence = round(score, 2)

    return details


# ==================== T083: Draft Invoice File Creation ====================

def create_invoice_draft(
    email: Dict[str, Any],
    details: InvoiceDetails,
    vault_path: str = "./AI_Employee",
) -> Optional[Path]:
    """
    Create a draft invoice markdown file in Pending_Approval/.

    File name: INVOICE_draft_YYYY-MM-DD_<email_id_prefix>.md
    YAML frontmatter type=odoo_invoice routes this through:
        ApprovalWatcher → ActionExecutor._execute_odoo_invoice_from_approval()
        → OdooClient.create_invoice()

    Args:
        email: Source email dict
        details: Extracted invoice details
        vault_path: Path to AI_Employee vault

    Returns:
        Path to created draft, or None on failure
    """
    logger = setup_logger("GmailToOdooParser")
    vault = Path(vault_path)
    pending_dir = vault / "Pending_Approval"
    pending_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.utcnow().strftime('%Y-%m-%d')
    safe_id = re.sub(r'[^a-zA-Z0-9]', '_', email.get('id', 'unknown'))[:16]
    filename = f"INVOICE_draft_{today}_{safe_id}.md"
    draft_path = pending_dir / filename

    # Serialise line items as YAML block (approval_watcher reads these back as list)
    line_items_yaml_block = "\n".join(
        f"  - description: \"{item.description.replace(chr(34), chr(39))}\"\n"
        f"    quantity: {item.quantity}\n"
        f"    unit_price: {item.unit_price:.2f}"
        for item in details.line_items
    ) or (
        f"  - description: \"{details.description}\"\n"
        f"    quantity: 1\n"
        f"    unit_price: {details.total_amount:.2f}"
    )

    # Markdown line-items table
    li_rows = ""
    for i, item in enumerate(details.line_items, 1):
        li_rows += (
            f"| {i} | {item.description} | {item.quantity} | "
            f"${item.unit_price:.2f} | ${item.subtotal:.2f} |\n"
        )
    if not li_rows:
        li_rows = f"| 1 | {details.description} | 1 | ${details.total_amount:.2f} | ${details.total_amount:.2f} |\n"

    safe_subject = email.get('subject', '').replace('"', "'")
    safe_from = email.get('from', '').replace('"', "'")
    safe_customer_name = details.customer_name.replace('"', "'")
    safe_customer_email = details.customer_email.replace('"', "'")

    content = f"""---
type: odoo_invoice
created_at: {datetime.utcnow().isoformat()}Z
requires_approval: true
domain_link: gmail_to_odoo
source_email_id: {email.get('id', '')}
source_email_subject: "{safe_subject}"
source_email_from: "{safe_from}"
customer_name: "{safe_customer_name}"
customer_email: "{safe_customer_email}"
total_amount: {details.total_amount:.2f}
due_date: "{details.due_date}"
extraction_confidence: {details.confidence:.2f}
approval_status: pending
line_items:
{line_items_yaml_block}
---

# Invoice Draft: {details.customer_name or details.customer_email or 'Unknown Customer'}

> **Action Required**: Move this file to `Approved/` to create the Odoo invoice,
> or **delete** to cancel. This was auto-extracted from an email — verify before approving.

## Source Email

| Field | Value |
|-------|-------|
| Subject | {email.get('subject', 'N/A')} |
| From | {email.get('from', 'N/A')} |
| Date | {email.get('date', 'N/A')} |
| Extraction Confidence | {details.confidence * 100:.0f}% |

## Extracted Invoice Details

| Field | Value |
|-------|-------|
| Customer | {details.customer_name or '⚠️ Not detected'} |
| Customer Email | {details.customer_email or '⚠️ Not detected'} |
| Total Amount | ${details.total_amount:.2f} |
| Due Date | {details.due_date or 'Not specified'} |

## Line Items

| # | Description | Qty | Unit Price | Subtotal |
|---|-------------|-----|------------|----------|
{li_rows}

## Original Email Preview

```
{email.get('body', 'No body available')[:600]}
```

## How to Approve

1. **Review** all extracted details above for accuracy
2. **Verify** the customer exists in Odoo (searched by email/name on approval)
3. **Move this file** to `Approved/` to trigger invoice creation
4. **Delete** this file to cancel

> ⚠️ Approval triggers `OdooClient.create_invoice()` with `dry_run=False`.
"""

    try:
        draft_path.write_text(content, encoding='utf-8')

        # T085: Structured log with domain_link tag
        log_structured_action(
            action="invoice_draft_created",
            actor="gmail_to_odoo_parser",
            parameters={
                'email_id': email.get('id'),
                'customer_name': details.customer_name,
                'customer_email': details.customer_email,
                'total_amount': details.total_amount,
                'confidence': details.confidence,
                'domain_link': 'gmail_to_odoo',
            },
            result={'status': 'success', 'draft_path': str(draft_path)},
            approval_status="pending",
            vault_path=vault_path,
        )

        logger.info(f"Invoice draft created: {draft_path}")
        return draft_path

    except Exception as e:
        logger.error(f"Failed to write invoice draft: {e}")
        return None


# ==================== T086: Clarification Request ====================

def create_clarification_request(
    email: Dict[str, Any],
    error: str,
    vault_path: str = "./AI_Employee",
) -> Optional[Path]:
    """
    Create a human-review file in Needs_Action/ when invoice parsing fails.

    Called when detect_invoice_request() fired but extract_invoice_details()
    did not produce actionable data (e.g. missing amount or customer).

    Args:
        email: Source email dict
        error: Description of why parsing failed / what's missing
        vault_path: Path to AI_Employee vault

    Returns:
        Path to created clarification file, or None on failure
    """
    logger = setup_logger("GmailToOdooParser")
    vault = Path(vault_path)
    needs_dir = vault / "Needs_Action"
    needs_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    clarif_path = needs_dir / f"INVOICE_CLARIFICATION_{ts}.md"

    safe_from = email.get('from', '').replace('"', "'")
    safe_error = error.replace('"', "'")

    content = f"""---
type: invoice_clarification_needed
created_at: {datetime.utcnow().isoformat()}Z
domain_link: gmail_to_odoo
source_email_id: {email.get('id', '')}
source_email_from: "{safe_from}"
parse_error: "{safe_error}"
---

# Invoice Clarification Needed

The AI detected an invoice request in the email below but could **not extract
sufficient details** to create a draft invoice automatically.

**Parse Error**: {error}

## Source Email

- **Subject**: {email.get('subject', 'N/A')}
- **From**: {email.get('from', 'N/A')}
- **Date**: {email.get('date', 'N/A')}

## Email Body

```
{email.get('body', 'No body available')[:800]}
```

## Action Required

Please manually:
1. Reply to the sender requesting missing details (customer name, line items, amounts, due date)
2. Or create the invoice directly in Odoo once details are confirmed
3. Delete this file when resolved
"""

    try:
        clarif_path.write_text(content, encoding='utf-8')

        # T085: Structured log with domain_link tag
        log_structured_action(
            action="invoice_clarification_created",
            actor="gmail_to_odoo_parser",
            parameters={
                'email_id': email.get('id'),
                'error': error,
                'domain_link': 'gmail_to_odoo',
            },
            result={'status': 'clarification_needed', 'file': str(clarif_path)},
            approval_status="pending",
            vault_path=vault_path,
        )

        logger.warning(f"Invoice clarification needed: {clarif_path}")
        return clarif_path

    except Exception as e:
        logger.error(f"Failed to create clarification request: {e}")
        return None
