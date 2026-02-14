# Audit & CEO Briefing Internal API Contract

**Version**: 1.0.0
**Service**: Internal audit generation and CEO briefing system
**Transport**: Direct Python function calls (not MCP server)
**Purpose**: Weekly business analysis and executive briefing

---

## Overview

This contract defines the internal API for generating weekly business audits and Monday Morning CEO Briefings. These are **internal utilities**, not MCP servers, invoked by the orchestrator's scheduler.

---

## Functions Provided

### 1. `generate_weekly_audit()`

Generate comprehensive weekly business audit from logs and vault data.

**Signature**:
```python
def generate_weekly_audit(
    week_end: datetime,
    output_dir: Path = Path("AI_Employee/Audits")
) -> AuditResult
```

**Parameters**:
- `week_end` (datetime): Sunday date ending the week (required)
- `output_dir` (Path): Directory to save audit file (default: AI_Employee/Audits)

**Returns**: `AuditResult`
```python
@dataclass
class AuditResult:
    success: bool
    audit_id: str                    # Format: audit_YYYY-MM-DD
    file_path: Path
    week_start: datetime
    week_end: datetime
    metrics: AuditMetrics
    error: str | None
```

**AuditMetrics**:
```python
@dataclass
class AuditMetrics:
    # Activity metrics
    total_actions: int
    actions_by_type: dict[str, int]

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
    errors_by_service: dict[str, int]

    # System health
    uptime_percentage: float
    watchdog_restarts: int
```

**Data Sources**:
1. `/Vault/Logs/YYYY-MM-DD.json`: Parse logs for week (Monday-Sunday)
2. `AI_Employee/Completed/`: Count completed tasks
3. `AI_Employee/Pending_Approval/`: Count pending approvals
4. `AI_Employee/Plans/`: Count plans created during week
5. System metrics: Uptime from orchestrator health checks

**Output File Format** (Markdown):
```markdown
# Weekly Business Audit - [Week Start] to [Week End]

**Generated**: [Timestamp]
**Period**: [Week Start] - [Week End]

## Executive Summary

[Brief overview of the week's activities]

## Activity Metrics

- **Total Actions**: [count]
- **Emails**: [received] received, [sent] sent
- **Social Media**: [fb] Facebook, [ig] Instagram, [tw] Twitter posts
- **Tasks**: [completed] completed, [pending] pending
- **Plans Created**: [count]

## Breakdown by Action Type

| Action Type | Count | Percentage |
|-------------|-------|------------|
| email_send | [count] | [%] |
| social_media_post | [count] | [%] |
| ... | ... | ... |

## Approval Workflow

- **Approvals Requested**: [count]
- **Auto-Approved**: [count] ([%]%)
- **Human Approved**: [count] ([%]%)
- **Rejected**: [count] ([%]%)

## System Health

- **Uptime**: [%]%
- **Errors**: [count] total
- **Watchdog Restarts**: [count]

### Errors by Service

| Service | Error Count |
|---------|-------------|
| odoo | [count] |
| facebook | [count] |
| ... | ... |

## Detailed Action Log

[Optional: Link to specific log files for deep dive]

---
_Generated automatically by AI Employee - Gold Tier_
```

**Errors**:
- `LOG_FILES_NOT_FOUND`: Cannot find logs for specified week
- `VAULT_ACCESS_ERROR`: Cannot read vault directories
- `INVALID_DATE`: week_end is not a Sunday
- `GENERATION_FAILED`: Error during audit generation

**Side Effects**:
- Creates audit file in `AI_Employee/Audits/YYYY-MM-DD-audit.md`
- Logs generation to `/Vault/Logs/YYYY-MM-DD.json`

**Performance**:
- Target: <2 minutes for 7 days of logs
- Log parsing: ~10,000 entries/second
- File system scans: <10 seconds

---

### 2. `generate_ceo_briefing()`

Generate Monday Morning CEO Briefing with actionable insights.

**Signature**:
```python
def generate_ceo_briefing(
    week_end: datetime,
    audit_result: AuditResult | None = None,
    output_dir: Path = Path("AI_Employee/CEO_Briefings")
) -> BriefingResult
```

**Parameters**:
- `week_end` (datetime): Sunday date ending the week (required)
- `audit_result` (AuditResult | None): Pre-generated audit (optional; will generate if None)
- `output_dir` (Path): Directory to save briefing file

**Returns**: `BriefingResult`
```python
@dataclass
class BriefingResult:
    success: bool
    briefing_id: str                 # Format: briefing_YYYY-MM-DD
    file_path: Path
    date: datetime
    metrics: BriefingSummary
    bottlenecks: list[Bottleneck]
    suggestions: list[Suggestion]
    projects: list[ProjectStatus]
    error: str | None
```

**BriefingSummary**:
```python
@dataclass
class BriefingSummary:
    tasks_completed: int
    social_media_posts: int
    emails_processed: int
    plans_created: int
    approvals_pending: int
```

**Bottleneck**:
```python
@dataclass
class Bottleneck:
    category: str                    # "approval", "error", "pending_task"
    description: str
    severity: str                    # "low", "medium", "high"
    count: int
    suggested_action: str
```

**Suggestion**:
```python
@dataclass
class Suggestion:
    type: str                        # "opportunity", "risk", "optimization"
    description: str
    rationale: str
    priority: str                    # "low", "medium", "high"
```

**ProjectStatus**:
```python
@dataclass
class ProjectStatus:
    name: str                        # Extracted from Plan.md files
    status: str                      # "in_progress", "completed", "blocked"
    progress_percentage: int
    next_steps: list[str]
    blockers: list[str]
```

**Data Sources**:
1. `AuditResult`: Weekly audit metrics
2. `AI_Employee/Pending_Approval/`: Detect approval bottlenecks
3. `AI_Employee/Plans/`: Extract project status from Plan.md files
4. `/Vault/Logs/`: Analyze patterns (e.g., repeat customer inquiries)
5. Social media metrics: Post counts (no financial data per spec clarification)

**Output File Format** (Markdown):
```markdown
# Monday Morning CEO Briefing - [Date]

**Week Ending**: [Sunday Date]
**Generated**: [Timestamp]

## Week at a Glance

- **Tasks Completed**: [count]
- **Social Media Posts**: [count]
- **Emails Processed**: [count]
- **Plans Created**: [count]
- **Approvals Pending**: [count]

## Bottlenecks Detected

### [Severity] - [Category]
[Description]

**Count**: [count]
**Suggested Action**: [action]

---

## Proactive Suggestions

### [Priority] - [Type]: [Description]

**Rationale**: [rationale]

---

## Project Status

### [Project Name] - [Status]

**Progress**: [%]%

**Next Steps**:
- [step 1]
- [step 2]

**Blockers**: [blockers or "None"]

---

## Social Media Performance

- **Facebook**: [count] posts
- **Instagram**: [count] posts
- **Twitter**: [count] posts

_Note: Engagement metrics available via social media MCP tools_

---

_Generated automatically by AI Employee - Gold Tier_
_This briefing excludes financial data; see Odoo for accounting details._
```

**Bottleneck Detection Rules**:
1. **Approval Bottleneck**: >5 items in Pending_Approval/ → HIGH
2. **Error Bottleneck**: >10 errors from same service → MEDIUM
3. **Pending Task Bottleneck**: >20 items in Needs_Action/ → MEDIUM
4. **Repeat Customer**: Same customer >3 emails → LOW (opportunity)

**Suggestion Generation Rules**:
1. **Opportunity**: Detect repeat customer inquiries → suggest proactive outreach
2. **Risk**: High error rate from service → suggest investigation
3. **Optimization**: Low social media engagement → suggest content review

**Project Status Extraction**:
- Parse `AI_Employee/Plans/*.md` files
- Extract project name from filename or heading
- Detect status from checkboxes: `- [x]` completed, `- [ ]` pending
- Calculate progress percentage from checkbox ratio
- Extract blockers from "Blockers:" section

**Errors**:
- `AUDIT_REQUIRED`: audit_result is None and cannot generate audit
- `VAULT_ACCESS_ERROR`: Cannot read vault directories
- `INVALID_DATE`: week_end is not a Sunday
- `GENERATION_FAILED`: Error during briefing generation

**Side Effects**:
- Creates briefing file in `AI_Employee/CEO_Briefings/YYYY-MM-DD-briefing.md`
- Logs generation to `/Vault/Logs/YYYY-MM-DD.json`

**Performance**:
- Target: <10 minutes from trigger (SC-001)
- Depends on audit generation (<2 min) + analysis (<8 min)

---

## Scheduler Integration

### APScheduler Configuration

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta

scheduler = BackgroundScheduler()

def weekly_audit_job():
    """Run weekly audit and CEO briefing."""
    week_end = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Ensure it's Sunday
    while week_end.weekday() != 6:  # 6 = Sunday
        week_end -= timedelta(days=1)

    # Generate audit
    audit_result = generate_weekly_audit(week_end)
    if not audit_result.success:
        logger.error(f"Audit generation failed: {audit_result.error}")
        return

    # Generate CEO briefing
    briefing_result = generate_ceo_briefing(week_end, audit_result)
    if not briefing_result.success:
        logger.error(f"Briefing generation failed: {briefing_result.error}")
        return

    logger.info(f"Weekly audit and briefing generated: {briefing_result.file_path}")

# Schedule for Sunday at 10pm
scheduler.add_job(
    func=weekly_audit_job,
    trigger=CronTrigger(day_of_week='sun', hour=22, minute=0),
    id='weekly_audit_job',
    coalesce=True,          # Run once if multiple triggers missed
    max_instances=1,         # Prevent concurrent runs
    replace_existing=True
)

scheduler.start()
```

**Scheduler Behaviors**:
- **Coalesce**: If system was down and multiple triggers missed, run once
- **Max Instances**: Prevent concurrent audit generation
- **Timezone**: UTC (convert to local in orchestrator if needed)

---

## Error Handling

### Retry Policy
- **Log File Missing**: Retry once after 30 seconds (may be in progress)
- **Vault Access**: Retry with exponential backoff (max 3 attempts)
- **Generation Failure**: NO retry (log error, alert human)

### Partial Data Handling
- **Missing Logs**: Use available logs; mark audit as "partial"
- **Empty Vault**: Generate empty audit; note in summary
- **Parse Errors**: Skip invalid entries; log warning

### Alerting
- **Generation Failure**: Create alert file in `AI_Employee/Needs_Action/`
- **Partial Data**: Note in audit/briefing header
- **Performance Degradation**: Log warning if >10 min (SC-001 violation)

---

## Testing

### Unit Tests
- Test metrics calculation with mock logs
- Test bottleneck detection rules
- Test suggestion generation
- Test project status extraction from Plan.md

### Integration Tests
- Generate audit from real log files
- Generate briefing from audit
- Test scheduler trigger (advance time)
- Validate output file format

### Test Data
```python
# Create test log files
test_logs = {
    "timestamp": "2026-02-05T10:00:00Z",
    "action": "email_send",
    "actor": "orchestrator",
    "result": {"status": "success"},
    "approval_status": "auto_approved"
}
# Write to /Vault/Logs/2026-02-05.json
```

---

## Logging Schema

All audit and briefing generations logged:
```json
{
  "timestamp": "2026-02-11T22:00:00.123Z",
  "action": "audit_generate",
  "actor": "audit_generator",
  "parameters": {
    "week_start": "2026-02-03",
    "week_end": "2026-02-09",
    "log_files_count": 7,
    "total_entries_parsed": 1234
  },
  "result": {
    "status": "success",
    "audit_id": "audit_2026-02-09",
    "file_path": "AI_Employee/Audits/2026-02-09-audit.md",
    "metrics": {
      "total_actions": 456,
      "total_errors": 12
    }
  },
  "approval_status": "not_required",
  "duration_ms": 87654
}
```

---

## Performance Optimization

### Log Parsing
- **Streaming**: Parse logs line-by-line (don't load entire file)
- **Caching**: Cache parsed logs if regenerating (rare)
- **Parallelism**: Parse multiple log files concurrently (threading)

### Vault Scanning
- **Depth Limit**: Only scan immediate children (no deep recursion)
- **Glob Patterns**: Use efficient glob patterns (*.md)
- **Caching**: Cache file counts for 5 minutes

### Bottleneck Detection
- **Early Exit**: Stop scanning when threshold reached
- **Sampling**: For large datasets, sample representative subset

---

## Security Considerations

1. **No Sensitive Data**: Audit/briefing contain aggregates, not sensitive content
2. **File Permissions**: Audit files readable only by user
3. **Log Sanitization**: Never include passwords, tokens in audit text
4. **Error Messages**: Sanitize error messages (remove paths, credentials)

---

## Versioning

**Current**: 1.0.0
**Breaking Changes**: Function signature changes increment major version

---

## Future Enhancements (Out of Scope for Gold Tier)

- Financial metrics (revenue, expenses) when banking automation added
- Trend analysis (week-over-week comparison)
- Predictive insights (ML-based suggestions)
- Interactive dashboards (web UI)
- Email delivery of briefing
- Custom metric definitions (user-configurable)
- Multi-language support
