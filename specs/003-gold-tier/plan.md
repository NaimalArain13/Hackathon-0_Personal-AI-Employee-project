# Implementation Plan: Gold Tier - Autonomous Employee

**Branch**: `003-gold-tier` | **Date**: 2026-02-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-gold-tier/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Transform the AI from a functional assistant (Silver Tier) to an autonomous employee capable of managing business operations including accounting integration (Odoo), social media management (Facebook, Instagram, Twitter/X), weekly CEO briefings, cross-domain automation (Gmail→Odoo invoice drafts), and comprehensive error handling. The system will operate with minimal human intervention after initial setup, implementing approval workflows for sensitive operations, default dry-run mode for all MCP operations, retry mechanisms with exponential backoff, and maintaining comprehensive audit logs. Architecture follows microservices pattern with separate MCP servers per service.

**Note on Agent Skills**: Formal Agent Skills packaging deferred to Platinum Tier. Gold Tier focuses on functional implementation using MCP server modularity.

## Technical Context

**Language/Version**: Python 3.13+ (as required by project)
**Primary Dependencies**:
  - Odoo JSON-RPC client (xmlrpc.client - built-in, FREE)
  - Facebook Graph API SDK (facebook-sdk - FREE, no usage fees)
  - Instagram Graph API (via Facebook SDK - FREE, no usage fees)
  - Tweepy for Twitter/X API integration (FREE Essential Access tier)
  - APScheduler for weekly audit scheduling (FREE, open source)
  - Existing: dotenv, pathlib, logging, threading, json

**💰 Cost**: $0 - All integrations use free tiers with sufficient rate limits for business needs

**Storage**: File-based (Obsidian vault markdown files + JSON logs in /Vault/Logs/)
**Testing**: pytest with async support for integration tests
**Target Platform**: Linux/WSL2 server environment (based on current deployment)

**Project Type**: Single project with microservices-style MCP servers
**Performance Goals**:
  - CEO briefing generation: <10 minutes from trigger
  - Social media posts: <5 minutes from approval to publication
  - API retry: exponential backoff with max 5 attempts
  - Watchdog recovery: <30 seconds to restart failed services

**Constraints**:
  - No banking channel automation (only spec preparation)
  - Approval required for amounts >$100 or new payees in Odoo
  - Approval required for replies/DMs on social media
  - Auto-approval allowed for scheduled posts and recurring payments <$100
  - 90-day log retention with structured JSON format
  - Environment variables for all credentials (.gitignore)

**Scale/Scope**:
  - Single business owner with multiple communication channels
  - ~10-50 transactions per week in Odoo
  - ~5-10 social media posts per week
  - Weekly audit + CEO briefing generation
  - 3-5 concurrent watcher processes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ PASS: Assistive Role (Principle I)
- AI remains supportive; all Odoo transactions and social media posts require approval workflows
- CEO briefing is advisory; no autonomous financial decisions
- Human maintains ultimate authority

### ✅ PASS: Explicit User Approval Required (Principle II)
- Social media posts: auto-approve scheduled content, approval for replies/DMs
- Odoo transactions: auto-approve <$100 recurring, approval for >$100 or new payees
- External communications gated by Pending_Approval → Approved workflow

### ✅ PASS: Default Dry Run Mode (Principle III)
- All MCP server tools implement dry_run parameter (default: true)
- Dry run mode logs intended actions without executing API calls
- Real execution requires explicit dry_run=false flag
- Approval workflows enforce separation between planning and execution
- Users explicitly confirm via file-system approval pattern

### ✅ PASS: Authorized Data Access Only (Principle IV)
- Gmail: read-only (already authorized in Silver Tier)
- Obsidian vault: primary workspace (already authorized)
- New access: Odoo API (explicit integration), Social media APIs (explicit integration)
- All within defined boundaries per constitution

### ✅ PASS: Access Restrictions (Principle V)
- No system files, passwords, or browser data access
- Credentials stored in .env (gitignored)
- No unauthorized folder access

### ✅ PASS: Instruction Clarity Requirement (Principle VI)
- Ambiguous audit data → halt and request clarification
- Unclear social media post context → request business goals
- Research phase will resolve all NEEDS CLARIFICATION items

### ✅ PASS: Conflict Resolution (Principle VII)
- Conflicting API responses → stop and log error
- Approval workflow conflicts → escalate to human
- ConflictResolver utility already implemented (Silver Tier)

### ✅ PASS: No Assumption-Based Actions (Principle VIII)
- All integrations require explicit configuration (.env)
- No guessing Odoo invoice details or social media content
- Clear instructions required for all operations

### ✅ PASS: Comprehensive Action Logging (Principle IX)
- Structured JSON logs in /Vault/Logs/YYYY-MM-DD.json
- Schema: timestamp, action, actor, parameters, result, approval_status
- 90-day retention (no auto-deletion)
- 100% completeness requirement (SC-006)

### ✅ PASS: Destructive Action Safety (Principle X)
- Failed Odoo transactions: no auto-retry (manual intervention)
- Failed social media posts: queue for manual review
- Exponential backoff for non-destructive API calls only

**GATE STATUS**: ✅ ALL GATES PASSED - Proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/003-gold-tier/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output: Odoo/social media API research
├── data-model.md        # Phase 1 output: entities and schemas
├── quickstart.md        # Phase 1 output: setup guide
├── contracts/           # Phase 1 output: API contracts
│   ├── odoo-contract.md
│   ├── facebook-contract.md
│   ├── instagram-contract.md
│   ├── twitter-contract.md
│   └── audit-contract.md
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
# Existing structure (Bronze/Silver Tier)
orchestrator.py              # Main coordinator
watchers/
├── base_watcher.py
├── gmail_watcher.py
├── whatsapp_watcher.py
└── filesystem_watcher.py    # NEW: monitors approval workflows

utils/
├── setup_logger.py
├── file_utils.py
├── conflict_resolver.py
├── action_executor.py       # EXTEND: add Odoo/social media actions
├── health_monitor.py        # EXTEND: watchdog for Gold Tier
├── resource_monitor.py
├── io_optimizer.py
├── sensitive_content_detector.py
├── plan_generator.py
├── plan_updater.py
├── linkedin_post_generator.py
├── linkedin_post_scheduler.py
# NEW utilities for Gold Tier:
├── odoo_client.py          # Odoo JSON-RPC wrapper
├── social_media_manager.py # Unified social media posting
├── audit_generator.py      # Weekly business audit
├── ceo_briefing_generator.py # Monday Morning CEO Briefing
└── retry_handler.py        # Exponential backoff logic

# NEW: MCP servers (microservices architecture)
.claude/mcp-servers/
├── odoo-mcp/
│   ├── mcp_server_odoo.py   # Odoo MCP server
│   ├── requirements.txt
│   └── README.md
├── facebook-mcp/
│   ├── mcp_server_facebook.py
│   ├── requirements.txt
│   └── README.md
├── instagram-mcp/
│   ├── mcp_server_instagram.py
│   ├── requirements.txt
│   └── README.md
├── twitter-mcp/
│   ├── mcp_server_twitter.py
│   ├── requirements.txt
│   └── README.md
└── gmail-mcp/              # Existing from Silver Tier
    └── mcp_server_email.py

# Obsidian Vault structure
AI_Employee/
├── Dashboard.md
├── Company_Handbook.md
├── Needs_Action/           # Incoming tasks
├── Pending_Approval/       # Awaiting human approval
├── Approved/               # Human-approved actions
├── Completed/              # Archived actions
├── Plans/                  # Plan.md files
├── Audits/                 # NEW: Weekly business audits
│   └── YYYY-MM-DD-audit.md
└── CEO_Briefings/          # NEW: Monday Morning briefings
    └── YYYY-MM-DD-briefing.md

# Vault logs (outside Obsidian for performance)
/Vault/Logs/
└── YYYY-MM-DD.json         # Structured action logs

# Tests
gold_tier_test/
├── test_odoo_integration.py
├── test_social_media.py
├── test_audit_generation.py
├── test_ceo_briefing.py
├── test_error_handling.py
└── test_retry_mechanisms.py

# Configuration
.env                         # EXTEND: add Odoo, FB, IG, Twitter credentials
.mcp.json                    # EXTEND: add Gold Tier MCP servers
```

**Structure Decision**: Single project with microservices-style MCP servers. The existing orchestrator-watcher-utils pattern from Bronze/Silver Tier is extended with:
1. New MCP servers per service (Odoo, Facebook, Instagram, Twitter) following the email-mcp pattern
2. New utility modules for Odoo client, social media management, audit/briefing generation
3. New vault directories for audits and CEO briefings
4. New test suite for Gold Tier acceptance criteria

## Cross-Domain Integration

**Unified Task Orchestration**: The existing orchestrator.py already provides cross-domain integration by coordinating all watchers (personal: gmail_watcher, whatsapp_watcher; business: Odoo actions, social media workflows) through a shared AI_Employee/Needs_Action/ inbox. This enables natural cross-domain workflows without architectural changes.

**Automated Cross-Domain Workflows** (FR-014):
1. **Gmail → Odoo**: Email pattern matching detects invoice requests ("invoice", "quote", customer patterns) and creates draft invoices in Pending_Approval/ for user confirmation before Odoo API execution
2. **Social Media → Notifications**: When business content is posted to social platforms, system logs cross-channel action for awareness (simplified approach without WhatsApp Business API dependency)

**Implementation Approach**:
- Create `gmail_to_odoo_parser.py` to extract invoice details from email bodies
- Extend `gmail_watcher.py` to integrate with `odoo_client.py` for draft creation
- Maintain approval boundary: draft → Pending_Approval/ → user confirms → Odoo API call
- All cross-domain actions logged with domain linkage for audit trail

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations detected**. All constitutional principles are satisfied by the design:
- Approval workflows maintain human control
- Credentials stored securely in .env
- Comprehensive logging without auto-deletion
- No autonomous decision-making beyond approved thresholds
