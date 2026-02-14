# Data Model: Gold Tier - Autonomous Employee

**Date**: 2026-02-11
**Feature**: 003-gold-tier
**Purpose**: Define entities, schemas, relationships, and state transitions for Gold Tier functionality.

---

## 1. CEO Briefing Entity

**Purpose**: Weekly business summary document with metrics, bottlenecks, and proactive suggestions.

### Schema

```python
class CEOBriefing:
    id: str                      # Format: briefing_YYYY-MM-DD
    date: datetime               # Week ending date (Sunday)
    generated_at: datetime       # Timestamp of generation

    # Metrics
    tasks_completed: int         # From Completed/ folder
    social_media_posts: int      # From logs
    emails_processed: int        # From logs
    plans_created: int           # From Plans/ folder
    approvals_pending: int       # From Pending_Approval/ folder

    # Bottlenecks (auto-detected)
    bottlenecks: list[Bottleneck]

    # Proactive suggestions
    suggestions: list[Suggestion]

    # Project status
    projects: list[ProjectStatus]

    # File reference
    file_path: str               # AI_Employee/CEO_Briefings/YYYY-MM-DD-briefing.md
```

### Relationships
- **Derived From**: Weekly audit data, action logs, vault file counts
- **Triggers**: Sunday 10pm via APScheduler CronTrigger
- **Consumers**: Business owner (human reader)

### State Transitions
```
[Scheduled] → [Generating] → [Completed] → [Reviewed by Human]
    ↓             ↓
[Failed]     [Partial]
```

### Validation Rules
- `date` must be a Sunday
- `generated_at` must be within 10 minutes of trigger time (SC-001)
- All counts must be non-negative integers
- `file_path` must exist and be readable after generation

---

## 2. Social Media Post Entity

**Purpose**: Content scheduled and published across social platforms with approval tracking.

### Schema

```python
class SocialMediaPost:
    id: str                      # Format: post_[timestamp]_[hash]
    created_at: datetime
    scheduled_for: datetime      # When to post (null = immediate)

    # Content
    content: str                 # Post text
    media_urls: list[str]        # Optional images/videos
    platforms: list[Platform]    # ['facebook', 'instagram', 'twitter']

    # Approval workflow
    approval_required: bool
    approval_status: ApprovalStatus  # pending | auto_approved | human_approved | rejected
    approved_at: datetime | None
    approved_by: str | None      # "auto" | "human"

    # Publication tracking
    publication_status: PublicationStatus  # scheduled | publishing | published | failed
    published_at: datetime | None

    # Platform-specific IDs
    facebook_post_id: str | None
    instagram_post_id: str | None
    twitter_post_id: str | None

    # Error tracking
    error: str | None
    retry_count: int
```

### Enums

```python
class Platform(Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"

class ApprovalStatus(Enum):
    PENDING = "pending"
    AUTO_APPROVED = "auto_approved"
    HUMAN_APPROVED = "human_approved"
    REJECTED = "rejected"

class PublicationStatus(Enum):
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
```

### Relationships
- **Created By**: `social_media_manager.py` or Agent Skill `/post-social-media`
- **Approved Via**: Filesystem approval workflow (Pending_Approval → Approved)
- **Published By**: Facebook/Instagram/Twitter MCP servers
- **Logged To**: `/Vault/Logs/YYYY-MM-DD.json`

### State Transitions

```
[Created] → [Approval Required?]
              ↓ No (scheduled post)
           [Auto-Approved] → [Scheduled] → [Publishing] → [Published]
              ↓ Yes (reply/DM)                ↓
           [Pending Approval] → [Human Approved]    [Failed] → [Manual Review]
              ↓
           [Rejected] → [Archived]
```

### Validation Rules
- `content` must not exceed platform limits:
  - Facebook: 63,206 characters
  - Instagram: 2,200 characters
  - Twitter: 280 characters (will be truncated with link)
- `scheduled_for` must be in the future if specified
- `approval_required = true` if post type is reply/DM
- `approval_required = false` if post type is scheduled content
- `platforms` must contain at least one valid platform
- All `platform_post_id` fields populated on successful publication

---

## 3. Odoo Transaction Entity

**Purpose**: Financial records synchronized between external transactions and Odoo accounting system.

### Schema

```python
class OdooTransaction:
    id: str                      # Format: txn_[timestamp]_[hash]
    created_at: datetime

    # Transaction details
    transaction_type: TransactionType  # invoice | payment | refund
    partner_id: int              # Odoo partner (customer/vendor) ID
    partner_name: str
    amount: Decimal              # Transaction amount
    currency: str                # Default: "USD"

    # Invoice-specific (if type = invoice)
    invoice_lines: list[InvoiceLine] | None
    due_date: datetime | None

    # Payment-specific (if type = payment)
    payment_method: str | None   # "cash" | "bank_transfer" | "check"
    payment_date: datetime | None

    # Approval workflow
    approval_required: bool
    approval_status: ApprovalStatus
    approval_reason: str | None  # "amount_over_threshold" | "new_payee"

    # Odoo sync status
    sync_status: SyncStatus      # pending | synced | failed
    odoo_record_id: int | None   # ID in Odoo (account.move or account.payment)
    synced_at: datetime | None

    # Error tracking
    error: str | None
    retry_count: int
```

### Enums

```python
class TransactionType(Enum):
    INVOICE = "invoice"
    PAYMENT = "payment"
    REFUND = "refund"

class SyncStatus(Enum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"

class InvoiceLine:
    product_id: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    tax_ids: list[int]
```

### Relationships
- **Created By**: Business event triggers (future: email parsing, receipt scanning)
- **Approved Via**: Filesystem approval workflow
- **Synced By**: Odoo MCP server
- **Logged To**: `/Vault/Logs/YYYY-MM-DD.json`

### State Transitions

```
[Created] → [Approval Required?]
              ↓ No (<$100 recurring)
           [Auto-Approved] → [Pending Sync] → [Syncing] → [Synced]
              ↓ Yes (>$100 or new payee)         ↓
           [Pending Approval] → [Human Approved]    [Failed] → [Manual Intervention]
              ↓
           [Rejected] → [Archived]
```

### Validation Rules
- `amount` must be positive (refunds are negative)
- `approval_required = true` if:
  - `amount > 100.00` (threshold from spec)
  - `partner_id` is new (first transaction with this partner)
- `approval_required = false` if:
  - `amount <= 100.00` AND
  - `partner_id` exists in previous transactions (recurring)
- `invoice_lines` required if `transaction_type = invoice`
- `payment_method` and `payment_date` required if `transaction_type = payment`
- NO auto-retry on sync failure (constitutional principle X - destructive actions)

---

## 4. Business Audit Entity

**Purpose**: Weekly comprehensive analysis of business operations, activities, and metrics.

### Schema

```python
class BusinessAudit:
    id: str                      # Format: audit_YYYY-MM-DD
    week_start: datetime         # Monday
    week_end: datetime           # Sunday
    generated_at: datetime

    # Activity metrics
    total_actions: int           # From logs
    actions_by_type: dict[str, int]  # {"email": 45, "social_media": 12, ...}

    # Communication metrics
    emails_received: int
    emails_sent: int
    whatsapp_messages: int

    # Social media metrics
    facebook_posts: int
    instagram_posts: int
    twitter_posts: int

    # Task metrics
    tasks_completed: int
    tasks_pending: int
    plans_created: int

    # Approval metrics
    approvals_requested: int
    approvals_granted: int
    approvals_rejected: int
    auto_approvals: int

    # Error metrics
    total_errors: int
    errors_by_service: dict[str, int]  # {"odoo": 2, "facebook": 1, ...}

    # System health
    uptime_percentage: float
    watchdog_restarts: int

    # File reference
    file_path: str               # AI_Employee/Audits/YYYY-MM-DD-audit.md
```

### Relationships
- **Derived From**: Action logs, vault file counts, system metrics
- **Triggers**: Sunday 10pm via APScheduler (before CEO briefing)
- **Used By**: CEO briefing generation
- **Consumers**: Business owner (human reader), AI for trend analysis

### State Transitions
```
[Scheduled] → [Collecting Data] → [Analyzing] → [Generating Report] → [Completed]
                   ↓                                     ↓
               [Failed]                            [Partial Data]
```

### Validation Rules
- `week_end` must be a Sunday
- `week_start` must be 7 days before `week_end`
- All counts must be non-negative integers
- `uptime_percentage` must be 0.0-100.0
- `file_path` must exist after generation

---

## 5. Audit Log Entry

**Purpose**: Immutable record of every system action for accountability and compliance.

### Schema (JSON format in /Vault/Logs/YYYY-MM-DD.json)

```json
{
  "timestamp": "ISO 8601 datetime",
  "action": "string (action type identifier)",
  "actor": "string (system component)",
  "parameters": {
    "key": "value (action-specific parameters)"
  },
  "result": {
    "status": "success | error | partial",
    "data": "any (action-specific result data)"
  },
  "approval_status": "auto_approved | human_approved | not_required | pending",
  "duration_ms": "integer (execution time)",
  "error": "string | null (error message if failed)"
}
```

### Common Action Types

```python
class ActionType(Enum):
    # Social media
    SOCIAL_MEDIA_POST = "social_media_post"
    SOCIAL_MEDIA_SCHEDULE = "social_media_schedule"

    # Odoo
    ODOO_CREATE_INVOICE = "odoo_create_invoice"
    ODOO_RECORD_PAYMENT = "odoo_record_payment"

    # Communication
    EMAIL_SEND = "email_send"
    EMAIL_RECEIVE = "email_receive"
    WHATSAPP_RECEIVE = "whatsapp_receive"

    # Planning
    PLAN_CREATE = "plan_create"
    PLAN_UPDATE = "plan_update"

    # Audit
    AUDIT_GENERATE = "audit_generate"
    CEO_BRIEFING_GENERATE = "ceo_briefing_generate"

    # System
    WATCHDOG_RESTART = "watchdog_restart"
    MCP_SERVER_START = "mcp_server_start"
    APPROVAL_REQUEST = "approval_request"
    APPROVAL_GRANT = "approval_grant"
```

### Relationships
- **Written By**: All system components (orchestrator, watchers, MCP servers, utilities)
- **Read By**: Audit generation, CEO briefing, error analysis, compliance reporting
- **Retention**: 90 days (principle IX - no auto-deletion)

### Validation Rules
- `timestamp` must be UTC ISO 8601 format
- `action` must be from valid ActionType enum
- `actor` must identify the component (not empty)
- `result.status` must be "success", "error", or "partial"
- `approval_status` required if action involves external communication or financial transaction
- `error` must be null if `result.status = "success"`

---

## 6. Approval Request Entity

**Purpose**: Human-in-the-loop approval workflow for sensitive operations.

### Schema (Markdown frontmatter + body)

```yaml
---
id: "approval_[timestamp]_[hash]"
type: "social_media_post | odoo_transaction"
created_at: "ISO 8601 datetime"
expires_at: "ISO 8601 datetime"  # Optional expiration
status: "pending | approved | rejected | expired"
---
```

**Body**: Human-readable description of the action requiring approval.

### Relationships
- **Created By**: Action executor when `approval_required = true`
- **Location**: `AI_Employee/Pending_Approval/[id].md`
- **Approved**: Moved to `AI_Employee/Approved/[id].md`
- **Rejected**: Deleted from `Pending_Approval/`
- **Monitored By**: Filesystem watcher

### State Transitions

```
[Created in Pending_Approval/] → [Human Review]
                                      ↓
                            [Approved (moved to Approved/)]
                                      ↓
                            [Executed] → [Logged] → [Moved to Completed/]

                            [Rejected (deleted)]
                                      ↓
                            [Logged] → [Archived]

                            [Expired (timeout reached)]
                                      ↓
                            [Moved to Expired/] → [Manual Review]
```

### Validation Rules
- `id` must be unique
- `type` must match one of the supported approval types
- `status = pending` on creation
- File must exist in `Pending_Approval/` if `status = pending`
- `expires_at` optional; if set, must be future datetime
- Action executes only after file moved to `Approved/` folder

---

## Entity Relationship Diagram

```
┌─────────────────┐
│ Business Audit  │ (weekly, automated)
└────────┬────────┘
         │ triggers
         ↓
┌─────────────────┐
│ CEO Briefing    │ (weekly, automated)
└─────────────────┘
         │ reads
         ↓
┌─────────────────┐       ┌──────────────────┐
│ Audit Log Entry │←──────│ Approval Request │
└────────┬────────┘       └────────┬─────────┘
         │ logs                     │ creates
         ↓                          ↓
┌──────────────────┐       ┌──────────────────┐
│ Social Media Post│       │ Odoo Transaction │
└──────────────────┘       └──────────────────┘
         │                          │
         └──────────┬───────────────┘
                    │ published via
                    ↓
         ┌────────────────────┐
         │ MCP Servers        │
         │ (Facebook, IG,     │
         │  Twitter, Odoo)    │
         └────────────────────┘
```

---

## Data Storage Locations

| Entity | Storage Format | Location |
|--------|---------------|----------|
| CEO Briefing | Markdown | `AI_Employee/CEO_Briefings/YYYY-MM-DD-briefing.md` |
| Social Media Post | JSON (transient) | In-memory during processing |
| Social Media Post (approved) | Markdown | `AI_Employee/Approved/post_[id].md` |
| Odoo Transaction | JSON (transient) | In-memory during processing |
| Odoo Transaction (approved) | Markdown | `AI_Employee/Approved/txn_[id].md` |
| Business Audit | Markdown | `AI_Employee/Audits/YYYY-MM-DD-audit.md` |
| Audit Log Entry | JSON (array) | `/Vault/Logs/YYYY-MM-DD.json` |
| Approval Request | Markdown | `AI_Employee/Pending_Approval/[id].md` |

---

## Data Migration & Versioning

**Current Version**: 1.0.0 (Gold Tier initial release)

**Future Considerations**:
- Schema versioning in JSON logs (`"schema_version": "1.0.0"`)
- Backward compatibility for audit queries
- Migration scripts for schema changes

**No migration required** for Gold Tier as this is net-new functionality building on Silver Tier infrastructure.

---

## Data Integrity Constraints

### Global Constraints
1. All timestamps in UTC ISO 8601 format
2. All monetary amounts as Decimal (not float) to prevent rounding errors
3. All IDs must be unique within their entity type
4. All file paths must use forward slashes and be absolute or vault-relative

### Cross-Entity Constraints
1. Approval Request `id` must match corresponding Social Media Post or Odoo Transaction `id`
2. Audit Log Entry `timestamp` must match action execution time (±1 second tolerance)
3. CEO Briefing metrics must sum to total from Audit Log queries (within 1% variance)

### Audit Trail Requirements (Principle IX)
- Every entity state transition logged to Audit Log
- Approval grants and rejections logged with human identifier
- Errors logged with full context (parameters, stack trace)
- No logs auto-deleted before 90-day retention period
