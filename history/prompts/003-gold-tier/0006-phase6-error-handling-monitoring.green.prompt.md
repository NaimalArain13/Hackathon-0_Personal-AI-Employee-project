---
id: 0006
title: Phase 6 Error Handling and Monitoring Implementation
stage: green
date: 2026-02-18
surface: agent
model: claude-sonnet-4-6
feature: 003-gold-tier
branch: 003-gold-tier
user: naimalarian
command: implement phase 6 - error handling and monitoring
labels: ["phase6", "retry-handler", "action-executor", "health-monitor", "orchestrator", "circuit-breaker", "dry-run", "gold-tier", "us4"]
links:
  spec: specs/003-gold-tier/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - utils/retry_handler.py (extended: ServiceRetryPolicy, retry_with_service_policy)
  - utils/action_executor.py (extended: OperationQueue, _dry_run_gate, _log_error_with_trace, graceful degradation)
  - utils/health_monitor.py (extended: 30s MCP poll, enhanced error aggregation, log retention check)
  - orchestrator.py (extended: _init_gold_tier_health_monitor, start_mcp_polling)
  - specs/003-gold-tier/tasks.md (T067-T078C marked complete)
tests:
  - python3 -m py_compile utils/retry_handler.py (pass)
  - python3 -m py_compile utils/action_executor.py (pass)
  - python3 -m py_compile utils/health_monitor.py (pass)
  - python3 -m py_compile orchestrator.py (pass)
---

## Prompt

now start phase 6

## Response

Reviewed all Phase 6 target files before implementing. Implemented T067–T078C across 4 files:

### utils/retry_handler.py (T067, T068)
- `ServiceRetryPolicy` dataclass: per-service read_max_attempts, write_allowed=False (Principle X), idempotent_max_attempts, base/max delays, rate_limit_base/max_delay
- Registered policies for odoo, facebook, instagram, twitter, gmail with service-appropriate rate limit windows
- `get_service_policy(service_name)`: returns registered policy or conservative default
- `retry_with_service_policy()`: combines service policy lookup + Constitutional Principle X enforcement (WRITE → max_attempts=1) + T068 rate-limit detection (detect_rate_limit() → extended backoff via handle_rate_limit()) in a single unified retry function

### utils/action_executor.py (T069, T072, T073, T075, T076, T078A–C)
- `OperationQueue`: thread-safe deque with 500-cap; `enqueue()`, `drain()`, `size()`, `clear()`; module-level singleton via `get_operation_queue()`
- `_dry_run_gate()` (T078A–B): must be called before ANY MCP write; allows dry_run=True always; allows dry_run=False only with auto_approved/human_approved; structured log on every gate check (T078C)
- `_log_error_with_trace()` (T076): captures `traceback.format_exc()` and writes to structured log with exception_type field
- `_mark_degraded()` / `_mark_recovered()` / `is_service_degraded()` (T075): service-level degradation set; degraded services skipped, other platforms continue
- `process_queued_operations()` (T073): drains queue in FIFO; skips WRITE ops (creates Needs_Action alert per Principle X); replays read/idempotent ops via execute_action_from_approval()
- `_execute_social_media_post()`: dry_run gate added; circuit breaker (T069) via get_circuit_breaker() wraps each platform call; CircuitBreakerOpenError → mark degraded + enqueue write + continue other platforms; Exception → log with trace + mark degraded
- `_execute_odoo_transaction()`: dry_run gate added; degraded check → queue + return; Exception → log with trace + mark Odoo degraded

### utils/health_monitor.py (T070, T071, T074, T078)
- `start_mcp_polling(poll_interval=30)` / `stop_mcp_polling()`: dedicated daemon thread at 30s interval (T070)
- `_mcp_poll_loop()`: checks circuit breaker state for each enabled service; OPEN → calls attempt_service_restart() (T071); structured log every poll
- `record_error()` enhanced (T074): 1-hour window (was 60s); maintains per-service rolling history (last 100 entries) with timestamp/message/type; structured log on every error
- `get_error_report()`: returns window_start, elapsed, counts, history_counts
- `get_error_history(service, last_n=20)`: returns recent errors for a service
- `check_log_retention(retention_days=90)` (T078): scans Logs/*.json, reports oldest/newest/days_retained; warns if <90 days found; NEVER deletes (Principle IX)

### orchestrator.py (T077)
- `_init_gold_tier_health_monitor()`: creates HealthMonitor, enables watchdog for all 4 Gold Tier services
- `run()`: starts general monitoring (300s) + MCP polling (30s) + initial retention check
- `signal_handler()`: gracefully stops MCP polling and monitoring on SIGINT/SIGTERM

All 16 tasks (T067–T078C) marked [X] in tasks.md. All files pass python3 -m py_compile.
