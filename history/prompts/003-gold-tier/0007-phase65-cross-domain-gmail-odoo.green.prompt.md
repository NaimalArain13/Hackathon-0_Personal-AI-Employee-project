---
id: 0007
title: Phase 6.5 Cross-Domain Gmail to Odoo Integration
stage: green
date: 2026-02-18
surface: agent
model: claude-sonnet-4-6
feature: 003-gold-tier
branch: 003-gold-tier
user: naimalarian
command: now start phase 6.5 in @specs/003-gold-tier/tasks.md
labels: ["phase6.5", "cross-domain", "gmail-to-odoo", "invoice-parser", "approval-workflow", "gold-tier", "xd"]
links:
  spec: specs/003-gold-tier/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - utils/gmail_to_odoo_parser.py (created: detect_invoice_request, extract_invoice_details, create_invoice_draft, create_clarification_request)
  - watchers/gmail_watcher.py (extended: _route_email_to_handler, run loop integration)
  - utils/action_executor.py (extended: odoo_invoice handler in execute_action_from_approval, _execute_odoo_invoice_from_approval)
  - specs/003-gold-tier/tasks.md (T079-T086 marked complete)
tests:
  - python3 -m py_compile utils/gmail_to_odoo_parser.py (pass)
  - python3 -m py_compile watchers/gmail_watcher.py (pass)
  - python3 -m py_compile utils/action_executor.py (pass)
---

## Prompt

now start phase 6.5 in @specs/003-gold-tier/tasks.md

## Response

Reviewed gmail_watcher.py, odoo_client.py, and approval_watcher.py before implementing. Implemented T079–T086 across 3 files:

### utils/gmail_to_odoo_parser.py (T079, T080, T081, T083, T085, T086) — NEW FILE
- `INVOICE_KEYWORDS`: 12 regex patterns (invoice, quote, bill, "please send invoice", purchase order, proforma, etc.) for T080
- `AMOUNT_PATTERNS`, `DUE_DATE_PATTERNS`, `CUSTOMER_NAME_PATTERNS`, `LINE_ITEM_PATTERN`: T081 extraction regexes
- `InvoiceLineItem` / `InvoiceDetails` dataclasses with `is_complete` property
- `detect_invoice_request(email)` → `Tuple[bool, float]`: keyword scan + amount boost → confidence 0.0–1.0 (T080)
- `extract_invoice_details(email)` → `InvoiceDetails`: extracts customer from sender display name, amount from 6 patterns, due date from 5 patterns (default 30 days), line items via qty×desc@price pattern (T081)
- `create_invoice_draft(email, details, vault_path)` → `Path`: YAML frontmatter with `type: odoo_invoice`, `domain_link: gmail_to_odoo`, serialised `line_items` list; file: `Pending_Approval/INVOICE_draft_YYYY-MM-DD_<id>.md` (T083); T085 structured log on success
- `create_clarification_request(email, error, vault_path)` → `Path`: T086 Needs_Action file when parsing produces incomplete details; T085 structured log with `domain_link: gmail_to_odoo`

### watchers/gmail_watcher.py (T082)
- Added imports for all 4 parser functions at top of file
- Added `_route_email_to_handler(email)` method:
  - Calls `detect_invoice_request(email)` → if invoice: calls `extract_invoice_details()`
  - `details.is_complete` → `create_invoice_draft()` → returns draft path
  - Not complete → `create_clarification_request()` with missing fields listed
  - Exception → `create_clarification_request()` with error message
  - Non-invoice email → falls through to existing `create_action_file()`
- Modified `run()` loop: replaced direct `create_action_file()` call with `_route_email_to_handler()`; email now always marked as read after any routing path

### utils/action_executor.py (T084)
- Added `elif action_type == 'odoo_invoice':` branch in `execute_action_from_approval()` dispatch
- Added `_execute_odoo_invoice_from_approval(metadata, content)`:
  - Reads: customer_name, customer_email, total_amount, due_date, line_items, domain_link from YAML metadata
  - T085: logs `odoo_invoice_approval_processing` with `domain_link` tag
  - Connects OdooClient; searches partner by email first, then name
  - Partner not found → Needs_Action alert + returns False
  - Builds invoice_lines from metadata list (or synthetic fallback)
  - T084: calls `odoo.create_invoice(partner_id, invoice_lines, due_date, dry_run=False)` — real execution since human approved
  - T085: logs `odoo_invoice_created` with `domain_link: gmail_to_odoo`, partner_id, amounts
  - Exception → T076 `_log_error_with_trace()` with domain_link context

### specs/003-gold-tier/tasks.md
- T079–T086 all marked [X]

All 8 tasks (T079–T086) complete. All files pass python3 -m py_compile.
