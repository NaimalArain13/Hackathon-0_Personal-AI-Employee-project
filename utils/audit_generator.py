#!/usr/bin/env python3
"""
Audit Generator
===============

Generates weekly business audits from structured logs and vault data.

Responsibilities:
- Parse structured JSON logs for a week (Monday-Sunday)
- Scan vault directories for task/plan/approval counts
- Calculate audit metrics (activity, communication, social media, tasks, approvals, errors, health)
- Generate Markdown audit report saved to AI_Employee/Audits/
- Log generation with structured JSON logging
- Alert on generation failure via Needs_Action/

Data Sources:
- AI_Employee/Logs/YYYY-MM-DD.json: Structured action logs
- AI_Employee/Completed/: Completed tasks
- AI_Employee/Pending_Approval/: Pending approvals
- AI_Employee/Plans/: Plans created during week

Constitutional Requirements:
- Principle IX: Comprehensive logging with 90-day retention
- No sensitive data in audit output (aggregates only)
"""

import os
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


# ==================== Data Models ====================

@dataclass
class AuditMetrics:
    """Metrics collected for a weekly audit."""
    # Activity metrics
    total_actions: int = 0
    actions_by_type: Dict[str, int] = field(default_factory=dict)

    # Communication metrics
    emails_received: int = 0
    emails_sent: int = 0
    whatsapp_messages: int = 0

    # Social media metrics
    facebook_posts: int = 0
    instagram_posts: int = 0
    twitter_posts: int = 0

    # Task metrics
    tasks_completed: int = 0
    tasks_pending: int = 0
    plans_created: int = 0

    # Approval metrics
    approvals_requested: int = 0
    approvals_granted: int = 0
    approvals_rejected: int = 0
    auto_approvals: int = 0

    # Error metrics
    total_errors: int = 0
    errors_by_service: Dict[str, int] = field(default_factory=dict)

    # System health
    uptime_percentage: float = 100.0
    watchdog_restarts: int = 0


@dataclass
class AuditResult:
    """Result of a weekly audit generation."""
    success: bool
    audit_id: str                   # Format: audit_YYYY-MM-DD
    file_path: Optional[Path]
    week_start: datetime
    week_end: datetime
    metrics: Optional[AuditMetrics]
    error: Optional[str] = None
    partial: bool = False           # True if some log files were missing


# ==================== Log Parsing ====================

def _parse_single_log_file(log_file: Path) -> List[Dict[str, Any]]:
    """
    Parse a single JSONL log file line-by-line (streaming, memory-efficient).

    Args:
        log_file: Path to the YYYY-MM-DD.json log file

    Returns:
        List of log entry dicts (invalid lines skipped with warning)
    """
    entries = []
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for lineno, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning(f"Skipping invalid JSON at {log_file}:{lineno}")
    except OSError as e:
        logger.warning(f"Cannot read log file {log_file}: {e}")
    return entries


def parse_logs_for_week(week_start: datetime, week_end: datetime, vault_path: Path) -> tuple[List[Dict], bool]:
    """
    Parse all log files for the given week in parallel.

    Args:
        week_start: Monday of the week (inclusive)
        week_end: Sunday of the week (inclusive)
        vault_path: Path to vault root

    Returns:
        Tuple (list of all log entries, partial flag)
    """
    log_dir = vault_path / 'Logs'
    all_entries: List[Dict] = []
    partial = False
    lock = threading.Lock()

    # Collect date range
    dates = []
    current = week_start
    while current <= week_end:
        dates.append(current)
        current += timedelta(days=1)

    def load_date(date: datetime):
        log_file = log_dir / date.strftime('%Y-%m-%d.json')
        if not log_file.exists():
            return None, date  # Missing
        return _parse_single_log_file(log_file), date

    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {executor.submit(load_date, d): d for d in dates}
        for future in as_completed(futures):
            entries, date = future.result()
            if entries is None:
                logger.warning(f"Log file missing for {date.strftime('%Y-%m-%d')}")
                with lock:
                    partial = True
            else:
                with lock:
                    all_entries.extend(entries)

    return all_entries, partial


# ==================== Metrics Calculation ====================

def calculate_metrics(log_entries: List[Dict], vault_path: Path, week_start: datetime, week_end: datetime) -> AuditMetrics:
    """
    Calculate all audit metrics from log entries and vault state.

    Args:
        log_entries: All log entries for the week
        vault_path: Path to vault root
        week_start: Start of week (for file timestamp filtering)
        week_end: End of week

    Returns:
        Populated AuditMetrics
    """
    metrics = AuditMetrics()
    metrics.total_actions = len(log_entries)

    for entry in log_entries:
        action = entry.get('action', 'unknown')
        actor = entry.get('actor', 'unknown')
        approval_status = entry.get('approval_status', '')
        result = entry.get('result', {}) or {}
        status = result.get('status', '')

        # Actions by type
        metrics.actions_by_type[action] = metrics.actions_by_type.get(action, 0) + 1

        # Communication
        if action in ('email_send', 'gmail_send'):
            metrics.emails_sent += 1
        elif action in ('email_receive', 'gmail_receive', 'gmail_watch'):
            metrics.emails_received += 1
        elif action in ('whatsapp_message', 'whatsapp_receive'):
            metrics.whatsapp_messages += 1

        # Social media
        if action == 'facebook_create_post' and status == 'success':
            metrics.facebook_posts += 1
        elif action == 'instagram_create_post' and status == 'success':
            metrics.instagram_posts += 1
        elif action == 'twitter_create_tweet' and status == 'success':
            metrics.twitter_posts += 1

        # Approvals
        if approval_status == 'pending':
            metrics.approvals_requested += 1
        elif approval_status == 'human_approved':
            metrics.approvals_granted += 1
            metrics.approvals_requested += 1
        elif approval_status == 'rejected':
            metrics.approvals_rejected += 1
            metrics.approvals_requested += 1
        elif approval_status == 'auto_approved':
            metrics.auto_approvals += 1

        # Errors
        if status == 'error':
            metrics.total_errors += 1
            service = actor.replace('_mcp', '').replace('_client', '')
            metrics.errors_by_service[service] = metrics.errors_by_service.get(service, 0) + 1

        # Watchdog restarts
        if action == 'watchdog_restart':
            metrics.watchdog_restarts += 1

    # Vault scanning
    _scan_vault_metrics(metrics, vault_path, week_start, week_end)

    return metrics


def _scan_vault_metrics(metrics: AuditMetrics, vault_path: Path, week_start: datetime, week_end: datetime):
    """
    Scan vault directories for task/plan/approval counts.
    Only counts immediate children (no deep recursion) as per performance spec.
    """
    week_start_ts = week_start.timestamp()
    week_end_ts = (week_end + timedelta(days=1)).timestamp()

    def created_in_week(path: Path) -> bool:
        try:
            return week_start_ts <= path.stat().st_mtime <= week_end_ts
        except OSError:
            return False

    # Completed tasks
    completed_dir = vault_path / 'Completed'
    if completed_dir.exists():
        metrics.tasks_completed = sum(
            1 for f in completed_dir.glob('*.md')
            if created_in_week(f)
        )

    # Pending tasks (Needs_Action)
    needs_action_dir = vault_path / 'Needs_Action'
    if needs_action_dir.exists():
        metrics.tasks_pending = sum(1 for f in needs_action_dir.glob('*.md'))

    # Plans created this week
    plans_dir = vault_path / 'Plans'
    if plans_dir.exists():
        metrics.plans_created = sum(
            1 for f in plans_dir.glob('*.md')
            if created_in_week(f)
        )

    # Pending approvals (current count)
    pending_dir = vault_path / 'Pending_Approval'
    if pending_dir.exists():
        pending_count = sum(1 for f in pending_dir.glob('*.md'))
        # Approvals requested from vault (supplement log data)
        if metrics.approvals_requested == 0:
            metrics.approvals_requested = pending_count


# ==================== Markdown Report Generation ====================

def generate_audit_markdown(
    metrics: AuditMetrics,
    week_start: datetime,
    week_end: datetime,
    audit_id: str,
    partial: bool = False
) -> str:
    """
    Generate the Markdown audit report.

    Args:
        metrics: Calculated audit metrics
        week_start: Monday of the week
        week_end: Sunday of the week
        audit_id: Audit identifier
        partial: True if some log data was missing

    Returns:
        Markdown string
    """
    now = datetime.utcnow()
    partial_banner = "\n> ⚠️ **Partial Audit**: Some log files were missing. Metrics may be incomplete.\n" if partial else ""

    # Build action breakdown table
    action_rows = ""
    total = max(metrics.total_actions, 1)
    for action_type, count in sorted(metrics.actions_by_type.items(), key=lambda x: -x[1])[:20]:
        pct = (count / total) * 100
        action_rows += f"| {action_type} | {count} | {pct:.1f}% |\n"
    if not action_rows:
        action_rows = "| (no actions recorded) | 0 | 0% |\n"

    # Error breakdown table
    error_rows = ""
    for service, count in sorted(metrics.errors_by_service.items(), key=lambda x: -x[1]):
        error_rows += f"| {service} | {count} |\n"
    if not error_rows:
        error_rows = "| (no errors) | 0 |\n"

    # Approval summary
    total_approvals = metrics.approvals_requested
    human_pct = (metrics.approvals_granted / max(total_approvals, 1)) * 100
    auto_pct = (metrics.auto_approvals / max(total_approvals, 1)) * 100
    rejected_pct = (metrics.approvals_rejected / max(total_approvals, 1)) * 100

    # Executive summary
    summary_parts = []
    if metrics.emails_sent + metrics.emails_received > 0:
        summary_parts.append(f"{metrics.emails_sent + metrics.emails_received} emails processed")
    social_posts = metrics.facebook_posts + metrics.instagram_posts + metrics.twitter_posts
    if social_posts > 0:
        summary_parts.append(f"{social_posts} social media posts published")
    if metrics.tasks_completed > 0:
        summary_parts.append(f"{metrics.tasks_completed} tasks completed")
    if metrics.total_errors > 0:
        summary_parts.append(f"{metrics.total_errors} errors detected")
    summary = "This week, the AI Employee: " + (", ".join(summary_parts) + "." if summary_parts else "ran with no recorded activity.")

    return f"""# Weekly Business Audit - {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}

**Audit ID**: {audit_id}
**Generated**: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC
**Period**: {week_start.strftime('%A, %B %d %Y')} – {week_end.strftime('%A, %B %d %Y')}
{partial_banner}
---

## Executive Summary

{summary}

---

## Activity Metrics

- **Total Actions**: {metrics.total_actions}
- **Emails**: {metrics.emails_received} received, {metrics.emails_sent} sent
- **WhatsApp Messages**: {metrics.whatsapp_messages}
- **Social Media**: {metrics.facebook_posts} Facebook, {metrics.instagram_posts} Instagram, {metrics.twitter_posts} Twitter posts
- **Tasks Completed**: {metrics.tasks_completed}
- **Tasks Pending**: {metrics.tasks_pending}
- **Plans Created**: {metrics.plans_created}

---

## Breakdown by Action Type

| Action Type | Count | Percentage |
|-------------|-------|------------|
{action_rows}
---

## Approval Workflow

- **Approvals Requested**: {metrics.approvals_requested}
- **Auto-Approved**: {metrics.auto_approvals} ({auto_pct:.1f}%)
- **Human Approved**: {metrics.approvals_granted} ({human_pct:.1f}%)
- **Rejected**: {metrics.approvals_rejected} ({rejected_pct:.1f}%)

---

## System Health

- **Uptime**: {metrics.uptime_percentage:.1f}%
- **Total Errors**: {metrics.total_errors}
- **Watchdog Restarts**: {metrics.watchdog_restarts}

### Errors by Service

| Service | Error Count |
|---------|-------------|
{error_rows}
---

## Detailed Action Log

Log files for this week are stored at:
- `AI_Employee/Logs/{week_start.strftime('%Y-%m-%d')}.json` through `AI_Employee/Logs/{week_end.strftime('%Y-%m-%d')}.json`

---
_Generated automatically by AI Employee - Gold Tier_
_Audit ID: {audit_id}_
"""


# ==================== Main Entry Point ====================

def generate_weekly_audit(
    week_end: datetime,
    output_dir: Path = Path("AI_Employee/Audits"),
    vault_path: Path = None
) -> AuditResult:
    """
    Generate a comprehensive weekly business audit.

    Args:
        week_end: Sunday date ending the week (required)
        output_dir: Directory to save audit file (default: AI_Employee/Audits)
        vault_path: Override vault path (default: VAULT_PATH env var or AI_Employee)

    Returns:
        AuditResult with success status, file path, and metrics
    """
    start_time = datetime.utcnow()

    # Resolve vault path
    if vault_path is None:
        vault_path = Path(os.getenv('VAULT_PATH', 'AI_Employee'))
    vault_path = Path(vault_path)

    # Validate week_end is a Sunday (weekday 6)
    if week_end.weekday() != 6:
        return AuditResult(
            success=False,
            audit_id="",
            file_path=None,
            week_start=week_end,
            week_end=week_end,
            metrics=None,
            error="INVALID_DATE: week_end must be a Sunday"
        )

    week_start = week_end - timedelta(days=6)  # Monday
    audit_id = f"audit_{week_end.strftime('%Y-%m-%d')}"

    logger.info(f"Starting weekly audit: {audit_id} ({week_start.date()} to {week_end.date()})")

    try:
        # Parse logs
        log_entries, partial = parse_logs_for_week(week_start, week_end, vault_path)
        logger.info(f"Parsed {len(log_entries)} log entries (partial={partial})")

        if not log_entries and not (vault_path / 'Logs').exists():
            return AuditResult(
                success=False,
                audit_id=audit_id,
                file_path=None,
                week_start=week_start,
                week_end=week_end,
                metrics=None,
                error="LOG_FILES_NOT_FOUND: No log directory found"
            )

        # Calculate metrics
        metrics = calculate_metrics(log_entries, vault_path, week_start, week_end)

        # Generate Markdown
        markdown = generate_audit_markdown(metrics, week_start, week_end, audit_id, partial)

        # Write audit file
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        audit_file = output_dir / f"{week_end.strftime('%Y-%m-%d')}-audit.md"
        audit_file.write_text(markdown, encoding='utf-8')
        logger.info(f"Audit written: {audit_file}")

        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Structured log
        _log_audit_generation(
            audit_id=audit_id,
            week_start=week_start,
            week_end=week_end,
            log_count=len(log_entries),
            metrics=metrics,
            duration_ms=duration_ms,
            success=True,
            vault_path=vault_path
        )

        return AuditResult(
            success=True,
            audit_id=audit_id,
            file_path=audit_file,
            week_start=week_start,
            week_end=week_end,
            metrics=metrics,
            error=None,
            partial=partial
        )

    except OSError as e:
        error_msg = f"VAULT_ACCESS_ERROR: {e}"
        logger.error(error_msg)
        _create_alert(vault_path, audit_id, error_msg)
        return AuditResult(
            success=False,
            audit_id=audit_id,
            file_path=None,
            week_start=week_start,
            week_end=week_end,
            metrics=None,
            error=error_msg
        )
    except Exception as e:
        error_msg = f"GENERATION_FAILED: {e}"
        logger.error(error_msg, exc_info=True)
        _create_alert(vault_path, audit_id, error_msg)
        return AuditResult(
            success=False,
            audit_id=audit_id,
            file_path=None,
            week_start=week_start,
            week_end=week_end,
            metrics=None,
            error=error_msg
        )


# ==================== Helpers ====================

def _log_audit_generation(
    audit_id: str,
    week_start: datetime,
    week_end: datetime,
    log_count: int,
    metrics: AuditMetrics,
    duration_ms: int,
    success: bool,
    vault_path: Path
):
    """Write structured JSON log entry for audit generation."""
    try:
        from utils.setup_logger import log_structured_action
    except ImportError:
        try:
            from setup_logger import log_structured_action
        except ImportError:
            logger.warning("Could not import log_structured_action")
            return

    log_structured_action(
        action="audit_generate",
        actor="audit_generator",
        parameters={
            "week_start": week_start.strftime('%Y-%m-%d'),
            "week_end": week_end.strftime('%Y-%m-%d'),
            "log_files_count": (week_end - week_start).days + 1,
            "total_entries_parsed": log_count
        },
        result={
            "status": "success" if success else "error",
            "audit_id": audit_id,
            "metrics": {
                "total_actions": metrics.total_actions if metrics else 0,
                "total_errors": metrics.total_errors if metrics else 0
            }
        },
        approval_status="not_required",
        duration_ms=duration_ms,
        vault_path=str(vault_path)
    )


def _create_alert(vault_path: Path, audit_id: str, error_msg: str):
    """Create alert file in Needs_Action/ for failed audit generation."""
    try:
        needs_action_dir = vault_path / 'Needs_Action'
        needs_action_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        alert_file = needs_action_dir / f"AUDIT_FAILURE_{timestamp}.md"
        alert_file.write_text(
            f"""# Audit Generation Failed

**Audit ID**: {audit_id}
**Timestamp**: {datetime.utcnow().isoformat()}Z
**Error**: {error_msg}

## Action Required

The weekly audit generation failed. Please investigate and re-run manually:

```python
from utils.audit_generator import generate_weekly_audit
from datetime import datetime
result = generate_weekly_audit(datetime.now())
```

---
_Auto-generated alert by AI Employee - Gold Tier_
""",
            encoding='utf-8'
        )
        logger.info(f"Alert created: {alert_file}")
    except Exception as e:
        logger.error(f"Failed to create alert file: {e}")


# ==================== CLI ====================

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Generate weekly business audit")
    parser.add_argument(
        "--week-end",
        help="Sunday date (YYYY-MM-DD). Defaults to last Sunday.",
        default=None
    )
    parser.add_argument(
        "--output-dir",
        default="AI_Employee/Audits",
        help="Output directory for audit file"
    )
    args = parser.parse_args()

    if args.week_end:
        week_end = datetime.strptime(args.week_end, '%Y-%m-%d')
    else:
        today = datetime.utcnow()
        # Go back to last Sunday
        days_back = (today.weekday() + 1) % 7
        week_end = today - timedelta(days=days_back)
        week_end = week_end.replace(hour=0, minute=0, second=0, microsecond=0)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    result = generate_weekly_audit(week_end, Path(args.output_dir))

    if result.success:
        print(f"Audit generated: {result.file_path}")
        print(f"Total actions: {result.metrics.total_actions}")
        print(f"Errors: {result.metrics.total_errors}")
        sys.exit(0)
    else:
        print(f"Audit failed: {result.error}", file=sys.stderr)
        sys.exit(1)
