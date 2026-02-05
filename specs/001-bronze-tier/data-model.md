# Data Model: Bronze Tier - Personal AI Employee Foundation

## Overview
This document defines the data structures and schemas used in the Bronze Tier Personal AI Employee system, focusing on the file-based architecture that uses Obsidian markdown files as the primary data store.

## Core Data Structures

### 1. Action File Schema
Files stored in `/Needs_Action/` folder with `.md` extension

```yaml
File Name Convention: "{TYPE}_{UNIQUE_ID}.md"
Example: "EMAIL_a1b2c3d4.md", "FILE_report.pdf.md", "WHATSAPP_client_123.md"

Frontmatter Metadata:
  type: [email, file_drop, whatsapp_message, payment_request, etc.]
  created: ISO 8601 timestamp
  priority: [low, medium, high, critical]
  status: [pending, in_progress, completed, failed]
  source: [original source identifier]

Body Content:
  - Primary content (email snippet, file content, message text)
  - Suggested actions as checkboxes
  - Contextual information
```

### 2. Approval Request Schema
Files stored in `/Pending_Approval/` folder with `.md` extension

```yaml
File Name Convention: "APPROVAL_{ACTION_TYPE}_{IDENTIFIER}.md"
Example: "APPROVAL_PAYMENT_ClientA_2026-01-07.md"

Frontmatter Metadata:
  type: approval_request
  action: [payment, email_send, file_delete, etc.]
  amount: (if financial) numeric value
  recipient: target entity for action
  reason: brief description of action
  created: ISO 8601 timestamp
  expires: ISO 8601 expiration timestamp
  status: [pending, approved, rejected]

Body Content:
  - Detailed action description
  - Risk assessment
  - Instructions for approval/rejection
```

### 3. Dashboard.md Schema
Central status dashboard file

```yaml
File Name: Dashboard.md
Location: Root of vault

Structure:
  # AI Employee Dashboard

  ## Current Status
  - **Last Updated**: [Auto-generated timestamp]
  - **Active Tasks**: [Count of files in Needs_Action]
  - **Pending Approval**: [Count of files in Pending_Approval]

  ## Bank Balance
  - **Current**: [Manual entry or auto-populated]

  ## Pending Messages
  - **Unread Emails**: [Auto-populated from Gmail watcher]
  - **WhatsApp Messages**: [Auto-populated from WhatsApp watcher]

  ## Active Business Projects
  - [List of active projects]

  ## Recent Activity
  - [Log of recent AI actions]
```

### 4. Company_Handbook.md Schema
Rule configuration file

```yaml
File Name: Company_Handbook.md
Location: Root of vault

Structure:
  # Company Handbook

  ## Rules of Engagement
  - Email communication rules
  - WhatsApp communication rules
  - File processing rules
  - Approval requirements
  - Escalation procedures
```

### 5. Plan.md Schema
Task planning files stored in `/Plans/` folder

```yaml
File Name Convention: "PLAN_{DESCRIPTION}_{TIMESTAMP}.md"
Example: "PLAN_invoice_client_a_2026-01-07.md"

Frontmatter Metadata:
  created: ISO 8601 timestamp
  status: [pending_approval, in_progress, completed, failed]
  related_to: [reference to related action file]

Body Content:
  - Objective description
  - Step-by-step plan with checkboxes
  - Dependencies
  - Approval requirements
```

### 6. Log Entry Schema
Files stored in `/Logs/` folder with YYYY-MM-DD.json extension

```json
{
  "timestamp": "ISO 8601 timestamp",
  "action_type": "type of action taken",
  "actor": "claude_code, user, watcher, etc.",
  "target": "target of the action",
  "parameters": "action parameters",
  "approval_status": "approved, pending, rejected",
  "approved_by": "human, system, automated",
  "result": "success, failed, partial"
}
```

## Folder Structure

```
/Vault/
├── Dashboard.md              # Central status dashboard
├── Company_Handbook.md       # Rules configuration
├── Inbox/                    # Incoming items awaiting classification
├── Needs_Action/             # Items requiring AI processing
├── Plans/                    # Created plans for complex tasks
├── Pending_Approval/         # Items requiring human approval
├── Approved/                 # Approved items ready for execution
├── Rejected/                 # Items rejected by human
├── Done/                     # Completed items
├── Logs/                     # Audit logs (YYYY-MM-DD.json)
└── Briefings/                # Generated reports (YYYY-MM-DD_Briefing.md)
```

## File Lifecycle

1. **Incoming**: Files arrive in `/Inbox/` or `/Needs_Action/` via watchers
2. **Processing**: Claude Code reads files and creates plans in `/Plans/`
3. **Approval**: If required, approval files go to `/Pending_Approval/`
4. **Execution**: Approved actions are executed via MCP servers
5. **Completion**: Processed files move to `/Done/`
6. **Logging**: All actions are recorded in `/Logs/`

## Data Relationships

```
Dashboard.md ←→ All other files (aggregates status)
Company_Handbook.md → All processing (defines rules)
Action files ↔ Plans (bidirectional relationship)
Approval files → Action files (triggers execution)
Log files ← All actions (records everything)
```

## Validation Rules

1. All markdown files in system folders must have valid frontmatter
2. File names must follow established conventions
3. Status values must be from predefined sets
4. Timestamps must be in ISO 8601 format
5. All action files must have corresponding log entries
6. Approval files must reference existing action files