# Research: Gold Tier - Autonomous Employee

**Date**: 2026-02-11
**Feature**: 003-gold-tier
**Purpose**: Resolve technical unknowns and establish best practices for Odoo integration, social media APIs, audit generation, and error handling.

---

## 1. Odoo JSON-RPC Integration

### Decision: Use XML-RPC (built-in) over odoorpc library
**Rationale**:
- Odoo Community Edition v19+ provides XML-RPC interface out of the box
- No additional Python dependencies required
- Standard `xmlrpc.client` in Python standard library
- Well-documented in Odoo official docs

**Integration Pattern**:
```python
import xmlrpc.client

# Authentication
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})

# API calls
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
result = models.execute_kw(db, uid, password, model, method, args, kwargs)
```

**Key Modules to Integrate**:
- `account.move`: Invoices and journal entries
- `account.payment`: Payment records
- `res.partner`: Customer/vendor information
- `product.product`: Product catalog

**Alternatives Considered**:
- OdooRPC library: More pythonic but adds dependency
- Direct PostgreSQL access: Bypasses Odoo business logic, violates encapsulation

---

## 2. Social Media API Integration

### 2.1 Facebook Graph API

**Decision**: Facebook Graph API v19.0 with facebook-sdk (FREE)
**Rationale**:
- **100% FREE**: No cost for standard Graph API usage (posting, insights, page management)
- Official Python SDK maintained by Facebook
- Supports page posting via `/{page-id}/feed` endpoint
- OAuth 2.0 with long-lived page access tokens
- Rate limits: 200 calls per hour per user (sufficient for business posting needs)

**Authentication Flow**:
1. Create Facebook App in Meta for Developers
2. Generate User Access Token with `pages_manage_posts` permission
3. Exchange for long-lived token (60 days)
4. Get Page Access Token (no expiration if page token)

**API Contract**:
```python
import facebook

graph = facebook.GraphAPI(access_token=page_token, version='19.0')
graph.put_object(
    parent_object=page_id,
    connection_name='feed',
    message='Post content',
    link='https://optional-link.com'
)
```

**Alternatives Considered**:
- Playwright browser automation: Fragile, breaks with UI changes
- Third-party scheduling tools: Adds external dependency

### 2.2 Instagram Graph API

**Decision**: Instagram Graph API (via Facebook) for business accounts (FREE)
**Rationale**:
- **100% FREE**: No cost for Instagram Business API usage (posting, insights)
- Instagram Basic Display API doesn't support posting
- Instagram Graph API requires Facebook Page + Instagram Business Account (both free)
- Same authentication as Facebook (page access token - no additional cost)
- Container-based posting: create → publish

**API Contract**:
```python
# Step 1: Create media container
container = graph.put_object(
    parent_object=instagram_account_id,
    connection_name='media',
    image_url='https://url-to-image.jpg',
    caption='Post caption'
)

# Step 2: Publish container
result = graph.put_object(
    parent_object=instagram_account_id,
    connection_name='media_publish',
    creation_id=container['id']
)
```

**Rate Limits**: 25 API calls per 24 hours per user

**Alternatives Considered**:
- Personal account API: Doesn't support posting
- Selenium automation: Against Instagram TOS, account suspension risk

### 2.3 Twitter (X) API v2

**Decision**: Tweepy library with OAuth 2.0 PKCE flow
**Rationale**:
- Twitter API v2 is the current standard
- Tweepy 4.14+ supports API v2 endpoints
- OAuth 2.0 PKCE flow for enhanced security
- Essential access: 1500 tweets/month, 50 tweets/day (free tier)

**Authentication Flow**:
1. Create Twitter App at developer.twitter.com
2. Get OAuth 2.0 Client ID and Client Secret
3. Generate Bearer Token or use OAuth 2.0 user context
4. For posting: OAuth 1.0a user context required

**API Contract**:
```python
import tweepy

client = tweepy.Client(
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_secret
)

response = client.create_tweet(text='Tweet content')
```

**Rate Limits**:
- 300 tweets per 3 hours (free tier)
- 50 tweets per 24 hours (essential access)

**Alternatives Considered**:
- Direct API calls: More code, error-prone
- Twitter API v1.1: Deprecated, sunset scheduled

---

## 3. Weekly Audit & CEO Briefing Generation

### Decision: APScheduler with CronTrigger for Sunday night execution
**Rationale**:
- Pure Python, no external daemons (cron) required
- Persistent job storage with SQLite backend
- Integrates cleanly with existing orchestrator pattern
- Graceful handling of missed runs (coalesce=True)

**Scheduling Pattern**:
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=generate_weekly_audit,
    trigger=CronTrigger(day_of_week='sun', hour=22, minute=0),
    id='weekly_audit',
    coalesce=True,
    max_instances=1
)
scheduler.start()
```

**Audit Data Sources**:
1. Obsidian vault: completed tasks, plans, needs_action counts
2. Social media metrics: post counts, engagement (if available via API)
3. Odoo: invoice counts, payment status (future)
4. Log files: action counts by type, error rates

**CEO Briefing Content Template**:
```markdown
# Monday Morning CEO Briefing - [Date]

## Week at a Glance
- **Tasks Completed**: X
- **Social Media Posts**: Y
- **Emails Processed**: Z

## Bottlenecks Detected
- [Auto-detected from pending approvals or failed actions]

## Proactive Suggestions
- [Based on patterns: e.g., "3 emails from customer X waiting response"]

## Project Status
- [From Plans/ directory: in-progress, completed]

_Generated automatically by AI Employee_
```

**Alternatives Considered**:
- Cron jobs: Requires system access, not portable
- Manual scheduling: Defeats automation purpose
- Cloud schedulers (AWS EventBridge): External dependency

---

## 4. Error Handling & Retry Mechanisms

### Decision: Exponential backoff with jitter and circuit breaker pattern
**Rationale**:
- Prevents cascading failures in dependent services
- Jitter reduces thundering herd problem
- Circuit breaker stops wasting resources on dead services
- Industry standard for microservices (Netflix, AWS)

**Retry Logic**:
```python
import time
import random

def exponential_backoff_with_jitter(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0):
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = random.uniform(0, delay * 0.1)  # 10% jitter
    return delay + jitter

def retry_with_backoff(func, max_attempts=5, exceptions=(Exception,)):
    for attempt in range(max_attempts):
        try:
            return func()
        except exceptions as e:
            if attempt == max_attempts - 1:
                raise
            delay = exponential_backoff_with_jitter(attempt)
            time.sleep(delay)
```

**Circuit Breaker States**:
1. **Closed**: Normal operation, requests pass through
2. **Open**: Too many failures, reject requests immediately
3. **Half-Open**: Test if service recovered, allow one request

**Thresholds**:
- Failure threshold: 5 failures in 60 seconds → Open
- Timeout: 30 seconds in Open state → Half-Open
- Success threshold: 2 successes → Closed

**Destructive Action Policy**:
- Odoo invoice creation: NO retry (could duplicate)
- Social media posts: NO retry (could duplicate)
- API reads: YES retry with backoff
- Status checks: YES retry with backoff

**Alternatives Considered**:
- Fixed delay retry: Wastes time, may hit rate limits
- Infinite retry: Can cause resource exhaustion
- No circuit breaker: Continues hitting dead services

---

## 5. Agent Skills Implementation

### Decision: Claude Desktop Agent Skills pattern
**Rationale**:
- Agent Skills are reusable, composable units of functionality
- Can be invoked via slash commands (e.g., `/post-to-social-media`)
- Maintain conversation context and approval workflows
- Integrate with MCP servers seamlessly

**Skill Structure**:
```
.claude/skills/
├── post-social-media.skill/
│   ├── skill.json          # Metadata, parameters, description
│   └── execute.py          # Main skill logic
├── generate-audit.skill/
│   ├── skill.json
│   └── execute.py
└── sync-odoo.skill/
    ├── skill.json
    └── execute.py
```

**skill.json Example**:
```json
{
  "name": "post-social-media",
  "description": "Post content to Facebook, Instagram, and Twitter with approval workflow",
  "parameters": {
    "content": {
      "type": "string",
      "description": "Content to post"
    },
    "platforms": {
      "type": "array",
      "items": {"type": "string", "enum": ["facebook", "instagram", "twitter"]},
      "default": ["facebook", "instagram", "twitter"]
    }
  },
  "approval_required": true
}
```

**Skill Execution Flow**:
1. User invokes: `/post-social-media "New product launch!"`
2. Skill creates approval file in Pending_Approval/
3. User reviews and moves to Approved/
4. Filesystem watcher detects approval
5. Skill executes via appropriate MCP servers
6. Results logged to /Vault/Logs/

**Alternatives Considered**:
- Hardcoded functions in orchestrator: Not reusable, tightly coupled
- External webhook system: Adds complexity, latency
- CLI commands: Less integrated with Claude's conversational context

---

## 6. MCP Server Architecture

### Decision: Separate MCP server per external service (microservices pattern)
**Rationale**:
- Isolation: Failure in one service doesn't affect others
- Independent scaling and deployment
- Clear separation of concerns
- Follows existing pattern (email-mcp, browser-mcp)

**MCP Server Template Structure**:
```python
# mcp_server_odoo.py
from mcp.server import Server, Tool
import xmlrpc.client

server = Server("odoo")

@server.tool()
async def create_invoice(
    partner_id: int,
    lines: list[dict],
    dry_run: bool = True
) -> dict:
    """Create an invoice in Odoo accounting system"""
    if dry_run:
        return {"status": "dry_run", "message": "Would create invoice"}

    # Real implementation
    models = get_odoo_connection()
    invoice_id = models.execute_kw(...)
    return {"status": "success", "invoice_id": invoice_id}

if __name__ == "__main__":
    server.run()
```

**Configuration in .mcp.json**:
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
    },
    "facebook": {
      "command": "python",
      "args": [".claude/mcp-servers/facebook-mcp/mcp_server_facebook.py"],
      "env": {
        "FACEBOOK_PAGE_TOKEN": "${FACEBOOK_PAGE_TOKEN}",
        "FACEBOOK_PAGE_ID": "${FACEBOOK_PAGE_ID}"
      }
    }
  }
}
```

**Watchdog Monitoring**:
- Health check endpoint per MCP server (HTTP or file-based)
- Orchestrator polls every 30 seconds
- Auto-restart on failure (max 3 attempts)
- Alert to user after 3 failed restarts

**Alternatives Considered**:
- Monolithic MCP server: Single point of failure
- Direct API calls from orchestrator: Tight coupling, hard to test
- Event bus (Redis): Over-engineering for single-user system

---

## 7. Approval Workflow Implementation

### Decision: File-system based approval with filesystem watcher
**Rationale**:
- Already proven in Silver Tier
- Human-readable (Markdown files)
- Git-friendly for audit trail
- No database required
- Simple to implement and understand

**Approval File Schema**:
```markdown
---
type: social_media_post
platforms: [facebook, instagram, twitter]
timestamp: 2026-02-11T10:30:00Z
requires_approval: true
auto_approve_reason: null
---

# Social Media Post Approval

**Content**:
Excited to announce our Q1 product launch! 🚀

**Platforms**: Facebook, Instagram, Twitter

**Scheduled For**: 2026-02-12T09:00:00Z

**Action**: Move to Approved/ folder to post, or delete to cancel.
```

**Approval Decision Matrix** (from spec clarifications):

| Action Type | Auto-Approve | Approval Required |
|-------------|--------------|-------------------|
| Scheduled social media post | ✅ Yes | ❌ No |
| Social media reply/DM | ❌ No | ✅ Yes |
| Odoo transaction <$100 (recurring) | ✅ Yes | ❌ No |
| Odoo transaction >$100 | ❌ No | ✅ Yes |
| Odoo new payee | ❌ No | ✅ Yes |

**Alternatives Considered**:
- Web UI for approvals: Requires web server, adds complexity
- Slack/email approvals: External dependency
- CLI approval tool: Less discoverable than file-based

---

## 8. Logging Schema

### Decision: Structured JSON logs with daily rotation
**Rationale**:
- Machine-readable for audit queries
- Daily files prevent unbounded growth
- 90-day retention meets compliance needs
- Easy to parse with standard tools (jq, Python json module)

**Log Entry Schema**:
```json
{
  "timestamp": "2026-02-11T10:30:00.123Z",
  "action": "social_media_post",
  "actor": "orchestrator",
  "parameters": {
    "platforms": ["facebook", "instagram"],
    "content_hash": "sha256:abc123...",
    "scheduled_for": "2026-02-12T09:00:00Z"
  },
  "result": {
    "status": "success",
    "facebook_post_id": "123456789",
    "instagram_post_id": "987654321"
  },
  "approval_status": "auto_approved",
  "duration_ms": 2345,
  "error": null
}
```

**Log Rotation**:
- File: `/Vault/Logs/YYYY-MM-DD.json`
- New file created at midnight UTC
- Retention: Delete files older than 90 days
- No auto-deletion of logs (principle IX)

**Query Examples**:
```bash
# Count actions by type
jq -s 'map(.action) | group_by(.) | map({action: .[0], count: length})' Vault/Logs/2026-02-*.json

# Find failed actions
jq 'select(.result.status == "error")' Vault/Logs/2026-02-11.json

# Audit trail for specific approval
jq 'select(.approval_status == "human_approved")' Vault/Logs/2026-02-*.json
```

**Alternatives Considered**:
- Plain text logs: Hard to parse programmatically
- Database (SQLite): Overkill, adds lock contention
- Cloud logging (CloudWatch): External dependency, cost

---

## Summary of Decisions

| Area | Technology/Pattern | Cost | Rationale |
|------|-------------------|------|-----------|
| Odoo Integration | XML-RPC (built-in) | FREE (self-hosted) | Standard, no dependencies |
| Facebook | Graph API v19.0 + facebook-sdk | **100% FREE** | Official, stable, no usage fees |
| Instagram | Graph API (business accounts) | **100% FREE** | Only option for posting, no fees |
| Twitter | API v2 + Tweepy | FREE (Essential tier) | Current standard, 50 tweets/day limit |
| Scheduling | APScheduler + CronTrigger | FREE | Pure Python, portable |
| Error Handling | Exponential backoff + circuit breaker | FREE | Industry standard |
| Agent Skills | Claude Desktop Skills pattern | FREE | Native integration |
| MCP Architecture | Microservices (one per service) | FREE | Isolation, scalability |
| Approval Workflow | File-system + watcher | FREE | Proven in Silver Tier |
| Logging | Structured JSON, daily files | FREE | Machine-readable, auditable |

**💰 TOTAL COST: $0 - All integrations use free tiers**

**All NEEDS CLARIFICATION items resolved. Ready for Phase 1 design.**
