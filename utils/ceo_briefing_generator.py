#!/usr/bin/env python3
"""
CEO Briefing Generator
======================

Generates Monday Morning CEO Briefings with actionable insights.

Responsibilities:
- Consume AuditResult from audit_generator.py
- Detect operational bottlenecks (approval backlog, error spikes, pending tasks)
- Generate proactive suggestions (opportunities, risks, optimizations)
- Extract project status from AI_Employee/Plans/*.md files
- Generate comprehensive Markdown briefing saved to AI_Employee/CEO_Briefings/
- Structured logging and error alerting

Bottleneck Rules:
- >5 items in Pending_Approval/ → HIGH approval bottleneck
- >10 errors from same service → MEDIUM error bottleneck
- >20 items in Needs_Action/ → MEDIUM pending task bottleneck
- Same customer >3 emails → LOW opportunity

Constitutional Requirements:
- Principle IX: Comprehensive logging
- No financial data in briefings (see Odoo for accounting)
- Briefing generated within 10 minutes (SC-001)
"""

import os
import re
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Import audit types
try:
    from utils.audit_generator import AuditResult, AuditMetrics
except ImportError:
    try:
        from audit_generator import AuditResult, AuditMetrics
    except ImportError:
        AuditResult = None
        AuditMetrics = None


# ==================== Data Models ====================

@dataclass
class BriefingSummary:
    """High-level metrics for the CEO briefing."""
    tasks_completed: int = 0
    social_media_posts: int = 0
    emails_processed: int = 0
    plans_created: int = 0
    approvals_pending: int = 0


@dataclass
class Bottleneck:
    """An operational bottleneck requiring attention."""
    category: str           # "approval", "error", "pending_task"
    description: str
    severity: str           # "low", "medium", "high"
    count: int
    suggested_action: str


@dataclass
class Suggestion:
    """A proactive suggestion for the CEO."""
    type: str               # "opportunity", "risk", "optimization"
    description: str
    rationale: str
    priority: str           # "low", "medium", "high"


@dataclass
class ProjectStatus:
    """Status extracted from a Plan.md file."""
    name: str
    status: str             # "in_progress", "completed", "blocked"
    progress_percentage: int
    next_steps: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)


@dataclass
class BriefingResult:
    """Result of a CEO briefing generation."""
    success: bool
    briefing_id: str        # Format: briefing_YYYY-MM-DD
    file_path: Optional[Path]
    date: datetime
    metrics: Optional[BriefingSummary]
    bottlenecks: List[Bottleneck] = field(default_factory=list)
    suggestions: List[Suggestion] = field(default_factory=list)
    projects: List[ProjectStatus] = field(default_factory=list)
    error: Optional[str] = None


# ==================== Bottleneck Detection ====================

def detect_bottlenecks(audit_result: AuditResult, vault_path: Path) -> List[Bottleneck]:
    """
    Detect operational bottlenecks from audit data and vault state.

    Rules:
    1. >5 pending approvals → HIGH approval bottleneck
    2. >10 errors from same service → MEDIUM error bottleneck
    3. >20 items in Needs_Action → MEDIUM pending task bottleneck

    Args:
        audit_result: Completed audit result
        vault_path: Path to vault root

    Returns:
        List of Bottleneck objects, sorted by severity
    """
    bottlenecks = []
    metrics = audit_result.metrics if audit_result and audit_result.metrics else None

    # Rule 1: Approval backlog
    pending_dir = vault_path / 'Pending_Approval'
    if pending_dir.exists():
        pending_count = sum(1 for f in pending_dir.glob('*.md'))
        if pending_count > 5:
            bottlenecks.append(Bottleneck(
                category="approval",
                description=f"{pending_count} items are waiting in Pending_Approval/ and have not been reviewed.",
                severity="high",
                count=pending_count,
                suggested_action="Review and action pending approvals in AI_Employee/Pending_Approval/ to unblock automated workflows."
            ))

    # Rule 2: Error spike per service
    if metrics and metrics.errors_by_service:
        for service, count in metrics.errors_by_service.items():
            if count > 10:
                bottlenecks.append(Bottleneck(
                    category="error",
                    description=f"Service '{service}' logged {count} errors this week.",
                    severity="medium",
                    count=count,
                    suggested_action=f"Investigate {service} integration. Check credentials, API limits, and recent changes."
                ))

    # Rule 3: Pending task overload
    needs_action_dir = vault_path / 'Needs_Action'
    if needs_action_dir.exists():
        pending_tasks = sum(1 for f in needs_action_dir.glob('*.md'))
        if pending_tasks > 20:
            bottlenecks.append(Bottleneck(
                category="pending_task",
                description=f"{pending_tasks} items are waiting in Needs_Action/ without resolution.",
                severity="medium",
                count=pending_tasks,
                suggested_action="Triage AI_Employee/Needs_Action/ — archive resolved items, prioritize critical ones."
            ))

    # Sort: high → medium → low
    severity_order = {"high": 0, "medium": 1, "low": 2}
    bottlenecks.sort(key=lambda b: severity_order.get(b.severity, 3))

    return bottlenecks


# ==================== Suggestion Generation ====================

def generate_suggestions(audit_result: AuditResult, vault_path: Path) -> List[Suggestion]:
    """
    Generate proactive suggestions from audit data and log patterns.

    Rules:
    1. Repeat customer (same sender >3 emails) → opportunity suggestion
    2. High error rate from service → risk suggestion
    3. Low/zero social media engagement → optimization suggestion

    Args:
        audit_result: Completed audit result
        vault_path: Path to vault root

    Returns:
        List of Suggestion objects
    """
    suggestions = []
    metrics = audit_result.metrics if audit_result and audit_result.metrics else None

    # Rule 1: Detect repeat customers from email log patterns
    repeat_customers = _find_repeat_customers(vault_path, audit_result)
    for customer, count in repeat_customers.items():
        suggestions.append(Suggestion(
            type="opportunity",
            description=f"Customer '{customer}' sent {count} emails this week.",
            rationale="Repeat inquiries often indicate purchase intent or unresolved needs — proactive outreach can convert or resolve.",
            priority="low"
        ))

    # Rule 2: High error rate → risk
    if metrics and metrics.total_errors > 0:
        high_error_services = [
            s for s, c in metrics.errors_by_service.items() if c > 5
        ]
        for service in high_error_services:
            suggestions.append(Suggestion(
                type="risk",
                description=f"'{service}' had elevated errors this week ({metrics.errors_by_service[service]} errors).",
                rationale="Persistent errors may indicate API credential expiry, rate limit exhaustion, or service outage.",
                priority="high" if metrics.errors_by_service[service] > 15 else "medium"
            ))

    # Rule 3: Low social media posting → optimization
    if metrics:
        total_posts = metrics.facebook_posts + metrics.instagram_posts + metrics.twitter_posts
        if total_posts == 0:
            suggestions.append(Suggestion(
                type="optimization",
                description="No social media posts were published this week.",
                rationale="Regular posting maintains audience engagement and brand visibility.",
                priority="medium"
            ))
        elif total_posts < 3:
            suggestions.append(Suggestion(
                type="optimization",
                description=f"Only {total_posts} social media post(s) were published this week.",
                rationale="Consider scheduling more frequent posts to increase reach.",
                priority="low"
            ))

    # Sort: high → medium → low
    priority_order = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda s: priority_order.get(s.priority, 3))

    return suggestions


def _find_repeat_customers(vault_path: Path, audit_result: AuditResult) -> Dict[str, int]:
    """
    Scan log entries for repeat email senders (>3 emails from same address).

    Returns:
        Dict of {sender: count} for repeat senders
    """
    # Read log files for the audit week
    if not audit_result or not audit_result.week_start:
        return {}

    log_dir = vault_path / 'Logs'
    if not log_dir.exists():
        return {}

    sender_counts: Dict[str, int] = {}
    current = audit_result.week_start
    while current <= audit_result.week_end:
        log_file = log_dir / current.strftime('%Y-%m-%d.json')
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                            if entry.get('action') in ('email_receive', 'gmail_receive'):
                                params = entry.get('parameters', {}) or {}
                                sender = params.get('from', params.get('sender', ''))
                                if sender:
                                    # Normalize: extract email address
                                    match = re.search(r'[\w.+-]+@[\w-]+\.\w+', sender)
                                    if match:
                                        email = match.group(0).lower()
                                        sender_counts[email] = sender_counts.get(email, 0) + 1
                        except json.JSONDecodeError:
                            continue
            except OSError:
                pass
        current += timedelta(days=1)

    return {k: v for k, v in sender_counts.items() if v > 3}


# ==================== Project Status Extraction ====================

def extract_project_statuses(vault_path: Path) -> List[ProjectStatus]:
    """
    Parse AI_Employee/Plans/*.md files to extract project statuses.

    Parsing rules:
    - Project name: from filename (without extension) or first H1 heading
    - Status: derived from checkbox ratio (- [x] vs - [ ])
    - Progress %: completed / total checkboxes × 100
    - Blockers: lines under "Blockers:" or "## Blockers" section
    - Next steps: first 3 unchecked checkboxes found

    Args:
        vault_path: Path to vault root

    Returns:
        List of ProjectStatus objects
    """
    plans_dir = vault_path / 'Plans'
    if not plans_dir.exists():
        return []

    projects = []
    for plan_file in sorted(plans_dir.glob('*.md')):
        try:
            content = plan_file.read_text(encoding='utf-8')
            project = _parse_plan_file(plan_file.stem, content)
            projects.append(project)
        except Exception as e:
            logger.warning(f"Failed to parse plan file {plan_file}: {e}")

    return projects


def _parse_plan_file(filename: str, content: str) -> ProjectStatus:
    """Parse a single Plan.md file into a ProjectStatus."""
    lines = content.splitlines()

    # Extract name: first H1 heading or filename
    name = filename.replace('-', ' ').replace('_', ' ').title()
    for line in lines:
        if line.startswith('# '):
            name = line[2:].strip()
            break

    # Count checkboxes
    completed_boxes = len(re.findall(r'- \[x\]', content, re.IGNORECASE))
    pending_boxes = len(re.findall(r'- \[ \]', content))
    total_boxes = completed_boxes + pending_boxes

    progress = int((completed_boxes / total_boxes) * 100) if total_boxes > 0 else 0

    # Determine status
    if total_boxes == 0:
        status = "in_progress"
    elif progress == 100:
        status = "completed"
    elif _has_blockers_section(content):
        status = "blocked"
    else:
        status = "in_progress"

    # Extract next steps (first 3 unchecked)
    next_steps = []
    for line in lines:
        if re.match(r'\s*- \[ \]', line):
            step = re.sub(r'\s*- \[ \]\s*', '', line).strip()
            if step:
                next_steps.append(step)
            if len(next_steps) >= 3:
                break

    # Extract blockers
    blockers = _extract_blockers(lines)

    return ProjectStatus(
        name=name,
        status=status,
        progress_percentage=progress,
        next_steps=next_steps,
        blockers=blockers
    )


def _has_blockers_section(content: str) -> bool:
    """Return True if content has a non-empty Blockers section."""
    in_blockers = False
    for line in content.splitlines():
        if re.match(r'#+\s*[Bb]locker', line) or re.match(r'\*\*[Bb]lockers?\*\*', line):
            in_blockers = True
            continue
        if in_blockers:
            if line.startswith('#'):
                break
            if line.strip() and line.strip() not in ('None', 'N/A', '-'):
                return True
    return False


def _extract_blockers(lines: List[str]) -> List[str]:
    """Extract blocker descriptions from lines following a Blockers section."""
    blockers = []
    in_blockers = False
    for line in lines:
        if re.match(r'#+\s*[Bb]locker', line) or re.match(r'\*\*[Bb]lockers?\*\*', line):
            in_blockers = True
            continue
        if in_blockers:
            if line.startswith('#'):
                break
            stripped = line.strip().lstrip('- ').strip()
            if stripped and stripped not in ('None', 'N/A'):
                blockers.append(stripped)
    return blockers[:5]  # Cap at 5 blockers


# ==================== Markdown Briefing Generation ====================

def generate_briefing_markdown(
    briefing_id: str,
    week_end: datetime,
    summary: BriefingSummary,
    bottlenecks: List[Bottleneck],
    suggestions: List[Suggestion],
    projects: List[ProjectStatus],
    audit_result: AuditResult = None
) -> str:
    """
    Generate the Monday Morning CEO Briefing Markdown.

    Args:
        briefing_id: Unique briefing identifier
        week_end: Sunday date ending the week
        summary: Week at a glance metrics
        bottlenecks: Detected operational bottlenecks
        suggestions: Proactive suggestions
        projects: Project statuses from Plans/
        audit_result: Optional audit result for additional context

    Returns:
        Complete Markdown string
    """
    now = datetime.utcnow()
    metrics = audit_result.metrics if audit_result and audit_result.metrics else None

    # Bottlenecks section
    bottleneck_section = ""
    if bottlenecks:
        for b in bottlenecks:
            severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(b.severity, "⚪")
            bottleneck_section += f"""
### {severity_emoji} {b.severity.upper()} - {b.category.replace('_', ' ').title()}

{b.description}

**Count**: {b.count}
**Suggested Action**: {b.suggested_action}

---
"""
    else:
        bottleneck_section = "\n_No bottlenecks detected this week. System operating normally._\n"

    # Suggestions section
    suggestions_section = ""
    if suggestions:
        for s in suggestions:
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(s.priority, "⚪")
            suggestions_section += f"""
### {priority_emoji} {s.priority.upper()} - {s.type.title()}: {s.description}

**Rationale**: {s.rationale}

---
"""
    else:
        suggestions_section = "\n_No proactive suggestions this week._\n"

    # Projects section
    projects_section = ""
    if projects:
        for p in projects:
            status_emoji = {"completed": "✅", "in_progress": "🔄", "blocked": "🚫"}.get(p.status, "❓")
            next_steps_list = "\n".join(f"- {s}" for s in p.next_steps) if p.next_steps else "- No pending steps"
            blockers_str = "\n".join(f"- {b}" for b in p.blockers) if p.blockers else "None"
            projects_section += f"""
### {status_emoji} {p.name} - {p.status.replace('_', ' ').title()}

**Progress**: {p.progress_percentage}%

**Next Steps**:
{next_steps_list}

**Blockers**: {blockers_str}

---
"""
    else:
        projects_section = "\n_No project plans found in AI_Employee/Plans/_\n"

    # Social media performance
    social_section = ""
    if metrics:
        social_section = f"""
## Social Media Performance

- **Facebook**: {metrics.facebook_posts} posts
- **Instagram**: {metrics.instagram_posts} posts
- **Twitter**: {metrics.twitter_posts} posts

_Note: Engagement metrics available via social media MCP tools_
"""

    return f"""# Monday Morning CEO Briefing - {week_end.strftime('%Y-%m-%d')}

**Week Ending**: {week_end.strftime('%A, %B %d %Y')}
**Generated**: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC
**Briefing ID**: {briefing_id}

---

## Week at a Glance

- **Tasks Completed**: {summary.tasks_completed}
- **Social Media Posts**: {summary.social_media_posts}
- **Emails Processed**: {summary.emails_processed}
- **Plans Created**: {summary.plans_created}
- **Approvals Pending**: {summary.approvals_pending}

---

## Bottlenecks Detected
{bottleneck_section}

## Proactive Suggestions
{suggestions_section}

## Project Status
{projects_section}
{social_section}
---

_Generated automatically by AI Employee - Gold Tier_
_This briefing excludes financial data; see Odoo for accounting details._
_Briefing ID: {briefing_id}_
"""


# ==================== Main Entry Point ====================

def generate_ceo_briefing(
    week_end: datetime,
    audit_result=None,
    output_dir: Path = Path("AI_Employee/CEO_Briefings"),
    vault_path: Path = None
):
    """
    Generate Monday Morning CEO Briefing with actionable insights.

    Args:
        week_end: Sunday date ending the week (required)
        audit_result: Pre-generated AuditResult (will generate one if None)
        output_dir: Directory to save briefing file
        vault_path: Override vault path (defaults to VAULT_PATH env var or AI_Employee)

    Returns:
        BriefingResult with success status, file path, and insights
    """
    start_time = datetime.utcnow()

    if vault_path is None:
        vault_path = Path(os.getenv('VAULT_PATH', 'AI_Employee'))
    vault_path = Path(vault_path)

    # Validate week_end
    if week_end.weekday() != 6:
        return BriefingResult(
            success=False,
            briefing_id="",
            file_path=None,
            date=week_end,
            metrics=None,
            error="INVALID_DATE: week_end must be a Sunday"
        )

    briefing_id = f"briefing_{week_end.strftime('%Y-%m-%d')}"
    logger.info(f"Starting CEO briefing: {briefing_id}")

    try:
        # Generate audit if not provided
        if audit_result is None:
            try:
                from utils.audit_generator import generate_weekly_audit
            except ImportError:
                from audit_generator import generate_weekly_audit

            logger.info("No audit_result provided — generating audit first")
            audit_result = generate_weekly_audit(week_end, vault_path=vault_path)
            if not audit_result.success:
                return BriefingResult(
                    success=False,
                    briefing_id=briefing_id,
                    file_path=None,
                    date=week_end,
                    metrics=None,
                    error=f"AUDIT_REQUIRED: {audit_result.error}"
                )

        metrics = audit_result.metrics

        # Build summary
        total_social = (
            (metrics.facebook_posts + metrics.instagram_posts + metrics.twitter_posts)
            if metrics else 0
        )
        pending_dir = vault_path / 'Pending_Approval'
        pending_count = sum(1 for f in pending_dir.glob('*.md')) if pending_dir.exists() else 0

        summary = BriefingSummary(
            tasks_completed=metrics.tasks_completed if metrics else 0,
            social_media_posts=total_social,
            emails_processed=(metrics.emails_received + metrics.emails_sent) if metrics else 0,
            plans_created=metrics.plans_created if metrics else 0,
            approvals_pending=pending_count
        )

        # Detect bottlenecks
        bottlenecks = detect_bottlenecks(audit_result, vault_path)
        logger.info(f"Detected {len(bottlenecks)} bottleneck(s)")

        # Generate suggestions
        suggestions = generate_suggestions(audit_result, vault_path)
        logger.info(f"Generated {len(suggestions)} suggestion(s)")

        # Extract project statuses
        projects = extract_project_statuses(vault_path)
        logger.info(f"Extracted {len(projects)} project status(es)")

        # Generate Markdown
        markdown = generate_briefing_markdown(
            briefing_id=briefing_id,
            week_end=week_end,
            summary=summary,
            bottlenecks=bottlenecks,
            suggestions=suggestions,
            projects=projects,
            audit_result=audit_result
        )

        # Write briefing file
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        briefing_file = output_dir / f"{week_end.strftime('%Y-%m-%d')}-briefing.md"
        briefing_file.write_text(markdown, encoding='utf-8')
        logger.info(f"Briefing written: {briefing_file}")

        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Performance check (SC-001: <10 minutes)
        if duration_ms > 600_000:
            logger.warning(f"Briefing generation exceeded SC-001 target: {duration_ms}ms (limit: 600000ms)")

        # Structured log
        _log_briefing_generation(
            briefing_id=briefing_id,
            week_end=week_end,
            summary=summary,
            bottleneck_count=len(bottlenecks),
            suggestion_count=len(suggestions),
            duration_ms=duration_ms,
            success=True,
            vault_path=vault_path
        )

        return BriefingResult(
            success=True,
            briefing_id=briefing_id,
            file_path=briefing_file,
            date=week_end,
            metrics=summary,
            bottlenecks=bottlenecks,
            suggestions=suggestions,
            projects=projects,
            error=None
        )

    except OSError as e:
        error_msg = f"VAULT_ACCESS_ERROR: {e}"
        logger.error(error_msg)
        _create_briefing_alert(vault_path, briefing_id, error_msg)
        return BriefingResult(
            success=False,
            briefing_id=briefing_id,
            file_path=None,
            date=week_end,
            metrics=None,
            error=error_msg
        )
    except Exception as e:
        error_msg = f"GENERATION_FAILED: {e}"
        logger.error(error_msg, exc_info=True)
        _create_briefing_alert(vault_path, briefing_id, error_msg)
        return BriefingResult(
            success=False,
            briefing_id=briefing_id,
            file_path=None,
            date=week_end,
            metrics=None,
            error=error_msg
        )


# ==================== Helpers ====================

def _log_briefing_generation(
    briefing_id: str,
    week_end: datetime,
    summary: BriefingSummary,
    bottleneck_count: int,
    suggestion_count: int,
    duration_ms: int,
    success: bool,
    vault_path: Path
):
    """Write structured JSON log entry for briefing generation."""
    try:
        from utils.setup_logger import log_structured_action
    except ImportError:
        try:
            from setup_logger import log_structured_action
        except ImportError:
            logger.warning("Could not import log_structured_action")
            return

    log_structured_action(
        action="briefing_generate",
        actor="ceo_briefing_generator",
        parameters={
            "week_end": week_end.strftime('%Y-%m-%d'),
            "briefing_id": briefing_id
        },
        result={
            "status": "success" if success else "error",
            "briefing_id": briefing_id,
            "summary": {
                "tasks_completed": summary.tasks_completed,
                "social_media_posts": summary.social_media_posts,
                "emails_processed": summary.emails_processed,
                "approvals_pending": summary.approvals_pending,
                "bottlenecks": bottleneck_count,
                "suggestions": suggestion_count
            }
        },
        approval_status="not_required",
        duration_ms=duration_ms,
        vault_path=str(vault_path)
    )


def _create_briefing_alert(vault_path: Path, briefing_id: str, error_msg: str):
    """Create alert file in Needs_Action/ for failed briefing generation."""
    try:
        needs_action_dir = vault_path / 'Needs_Action'
        needs_action_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        alert_file = needs_action_dir / f"BRIEFING_FAILURE_{timestamp}.md"
        alert_file.write_text(
            f"""# CEO Briefing Generation Failed

**Briefing ID**: {briefing_id}
**Timestamp**: {datetime.utcnow().isoformat()}Z
**Error**: {error_msg}

## Action Required

The CEO briefing generation failed. Please re-run manually:

```python
from utils.ceo_briefing_generator import generate_ceo_briefing
from datetime import datetime
result = generate_ceo_briefing(datetime.now())
```

---
_Auto-generated alert by AI Employee - Gold Tier_
""",
            encoding='utf-8'
        )
        logger.info(f"Briefing alert created: {alert_file}")
    except Exception as e:
        logger.error(f"Failed to create briefing alert file: {e}")


# ==================== CLI ====================

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Generate Monday Morning CEO Briefing")
    parser.add_argument(
        "--week-end",
        help="Sunday date (YYYY-MM-DD). Defaults to last Sunday.",
        default=None
    )
    parser.add_argument(
        "--output-dir",
        default="AI_Employee/CEO_Briefings",
        help="Output directory for briefing file"
    )
    parser.add_argument(
        "--audit-file",
        help="Path to pre-generated audit file (optional)",
        default=None
    )
    args = parser.parse_args()

    if args.week_end:
        week_end = datetime.strptime(args.week_end, '%Y-%m-%d')
    else:
        today = datetime.utcnow()
        days_back = (today.weekday() + 1) % 7
        week_end = today - timedelta(days=days_back)
        week_end = week_end.replace(hour=0, minute=0, second=0, microsecond=0)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    result = generate_ceo_briefing(week_end, output_dir=Path(args.output_dir))

    if result.success:
        print(f"Briefing generated: {result.file_path}")
        print(f"Bottlenecks: {len(result.bottlenecks)}")
        print(f"Suggestions: {len(result.suggestions)}")
        print(f"Projects tracked: {len(result.projects)}")
        sys.exit(0)
    else:
        print(f"Briefing failed: {result.error}", file=sys.stderr)
        sys.exit(1)
