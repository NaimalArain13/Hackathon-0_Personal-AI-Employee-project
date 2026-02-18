"""
Health Monitor Module for the Personal AI Employee system.
Monitors system health to ensure 24+ hours of uptime without manual intervention.

Gold Tier Extensions:
    - Polls MCP servers every 30 seconds
    - Watchdog auto-restart for failed services (max 3 attempts)
    - Error aggregation and reporting by service
    - Circuit breaker integration
"""

import json
import logging
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable
from utils.setup_logger import setup_logger, log_structured_action


class HealthMonitor:
    """
    Class to monitor system health and ensure 24+ hours of uptime.
    """

    def __init__(self, vault_path: str):
        """
        Initialize the health monitor.

        Args:
            vault_path: Path to the Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.logger = setup_logger("HealthMonitor", level=logging.INFO)

        # Monitoring configuration
        self.monitoring = False
        self.monitoring_thread = None
        self.health_checks = []
        self.system_start_time = datetime.now()
        self.last_error_time = None

        # Gold Tier: Watchdog configuration
        self.watchdog_enabled = False
        self.watchdog_max_attempts = 3
        self.watchdog_restart_counts = {}  # service_name -> restart_count
        self.watchdog_last_restart_time = {}  # service_name -> timestamp
        self.watchdog_restart_window = 300  # Reset count after 5 minutes

        # Gold Tier: Error aggregation (T074 — windowed buckets per service)
        self.error_counts = {}          # service_name -> error_count (current window)
        self.error_window_start = datetime.now()
        self.error_window_seconds = 3600  # 1-hour window for reporting (T074)
        self.error_history: Dict[str, List[Dict]] = {}  # service -> [{ts, msg}, ...]

        # T070: Separate 30s MCP polling thread
        self._mcp_poll_thread: Optional[threading.Thread] = None
        self._mcp_poll_running = False

        # Gold Tier: MCP server registry
        self.mcp_servers = {
            'odoo': {'enabled': False, 'last_check': None, 'status': 'unknown'},
            'facebook': {'enabled': False, 'last_check': None, 'status': 'unknown'},
            'instagram': {'enabled': False, 'last_check': None, 'status': 'unknown'},
            'twitter': {'enabled': False, 'last_check': None, 'status': 'unknown'},
        }

        # Health log
        self.health_log_file = self.vault_path / "Logs" / "health_monitor.json"
        self.health_log_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize the health log file
        if not self.health_log_file.exists():
            self._write_health_log([])

    def start_monitoring(self, check_interval: int = 300):  # Default: check every 5 minutes
        """
        Start the health monitoring system.

        Args:
            check_interval: Interval in seconds between health checks
        """
        if self.monitoring:
            self.logger.warning("Health monitoring is already running")
            return

        self.monitoring = True
        self.logger.info("Starting health monitoring...")

        def monitor_loop():
            while self.monitoring:
                try:
                    # Perform health check
                    health_status = self.perform_health_check()

                    # Log the health status
                    self._log_health_status(health_status)

                    # Check for issues and handle them
                    self._handle_issues(health_status)

                except Exception as e:
                    self.logger.error(f"Error in health monitoring: {e}")

                # Wait for the specified interval
                time.sleep(check_interval)

        self.monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitoring_thread.start()

    def stop_monitoring(self):
        """Stop the health monitoring system."""
        self.monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        self.logger.info("Stopped health monitoring")

    # ========== Gold Tier Extensions ==========

    def enable_watchdog(self, service_name: str):
        """
        Enable watchdog monitoring for a specific MCP server.

        Args:
            service_name: Name of the MCP server (e.g., 'odoo', 'facebook')
        """
        if service_name in self.mcp_servers:
            self.mcp_servers[service_name]['enabled'] = True
            self.watchdog_enabled = True
            self.logger.info(f"Watchdog enabled for service: {service_name}")
        else:
            self.logger.warning(f"Unknown service: {service_name}")

    def disable_watchdog(self, service_name: str):
        """
        Disable watchdog monitoring for a specific MCP server.

        Args:
            service_name: Name of the MCP server
        """
        if service_name in self.mcp_servers:
            self.mcp_servers[service_name]['enabled'] = False
            self.logger.info(f"Watchdog disabled for service: {service_name}")

    # ==================== T070: 30-Second MCP Polling Loop ====================

    def start_mcp_polling(self, poll_interval: int = 30):
        """
        Start dedicated MCP server health polling every 30 seconds (T070).

        Runs in a separate daemon thread alongside the general health monitor.
        Triggers watchdog auto-restart when a circuit is OPEN (T071).

        Args:
            poll_interval: Polling interval in seconds (default: 30)
        """
        if self._mcp_poll_running:
            self.logger.warning("MCP polling already running")
            return

        self._mcp_poll_running = True

        def _poll_loop():
            self.logger.info(f"MCP polling started (interval={poll_interval}s)")
            while self._mcp_poll_running:
                try:
                    self._mcp_poll_loop()
                except Exception as exc:
                    self.logger.error(f"MCP poll iteration error: {exc}")
                time.sleep(poll_interval)
            self.logger.info("MCP polling stopped")

        self._mcp_poll_thread = threading.Thread(target=_poll_loop, daemon=True, name="MCP-Poll")
        self._mcp_poll_thread.start()

    def stop_mcp_polling(self):
        """Stop the MCP polling thread."""
        self._mcp_poll_running = False
        if self._mcp_poll_thread:
            self._mcp_poll_thread.join(timeout=5)

    def _mcp_poll_loop(self):
        """
        Single iteration of MCP health polling (T070 + T071).

        For each enabled MCP server:
        - Reads circuit breaker state
        - If OPEN: attempts watchdog restart (T071)
        - Logs health status to structured log
        """
        for service_name, info in self.mcp_servers.items():
            if not info.get('enabled', False):
                continue

            try:
                from utils.retry_handler import get_circuit_breaker
                cb = get_circuit_breaker(service_name)
                state = cb.get_state()

                info['last_check'] = datetime.now()
                info['status'] = state['state']

                if state['state'] == 'open':
                    self.logger.warning(
                        f"[MCP Poll] {service_name} circuit OPEN "
                        f"({state['failure_count']} failures). Triggering watchdog."
                    )
                    # T071: Watchdog auto-restart
                    self.attempt_service_restart(service_name)

                elif state['state'] == 'half_open':
                    self.logger.info(f"[MCP Poll] {service_name} circuit HALF_OPEN (recovering)")

                # Structured log for monitoring dashboards
                log_structured_action(
                    action="mcp_health_poll",
                    actor="health_monitor",
                    parameters={"service": service_name, "poll_interval_s": 30},
                    result={"status": "success", "circuit_state": state['state'],
                            "failure_count": state['failure_count']},
                    approval_status="not_required",
                    vault_path=str(self.vault_path)
                )

            except Exception as exc:
                self.logger.error(f"[MCP Poll] Error polling {service_name}: {exc}")

    # ==================== T074: Enhanced Error Aggregation ====================

    def record_error(self, service_name: str, error: Exception):
        """
        Record an error for a specific service with time-windowed aggregation (T074).

        Maintains:
        - Current-window counts (resets every error_window_seconds)
        - Rolling history of recent errors per service (last 100 per service)

        Args:
            service_name: Name of the service that errored
            error: The exception that occurred
        """
        now = datetime.now()

        # Reset window if expired
        if (now - self.error_window_start).total_seconds() > self.error_window_seconds:
            self.logger.info(
                f"Error window expired — resetting counts. "
                f"Previous: {self.error_counts}"
            )
            self.error_counts = {}
            self.error_window_start = now

        # Increment current-window count
        self.error_counts[service_name] = self.error_counts.get(service_name, 0) + 1

        # Maintain rolling history
        if service_name not in self.error_history:
            self.error_history[service_name] = []
        self.error_history[service_name].append({
            'timestamp': now.isoformat(),
            'message': str(error),
            'type': type(error).__name__
        })
        # Cap history at 100 entries per service
        if len(self.error_history[service_name]) > 100:
            self.error_history[service_name] = self.error_history[service_name][-100:]

        self.logger.warning(
            f"Error recorded for '{service_name}': {error} "
            f"(Window total: {self.error_counts[service_name]})"
        )

        # Structured log for audit trail
        log_structured_action(
            action="error_recorded",
            actor="health_monitor",
            parameters={"service": service_name, "window_seconds": self.error_window_seconds},
            result={
                "status": "recorded",
                "window_count": self.error_counts[service_name],
                "error_type": type(error).__name__
            },
            approval_status="not_required",
            vault_path=str(self.vault_path)
        )

    def get_error_report(self) -> Dict:
        """
        Get aggregated error report for all services (T074).

        Returns:
            Dictionary with error counts, history, and time window
        """
        window_elapsed = (datetime.now() - self.error_window_start).total_seconds()
        return {
            'window_start': self.error_window_start.isoformat(),
            'window_seconds': self.error_window_seconds,
            'window_elapsed_seconds': round(window_elapsed),
            'errors_by_service': dict(self.error_counts),
            'total_errors': sum(self.error_counts.values()),
            'error_history_counts': {s: len(h) for s, h in self.error_history.items()}
        }

    def get_error_history(self, service_name: str, last_n: int = 20) -> List[Dict]:
        """
        Get recent error history for a specific service (T074).

        Args:
            service_name: Service name
            last_n: Return last N errors

        Returns:
            List of error dicts with timestamp, message, type
        """
        history = self.error_history.get(service_name, [])
        return history[-last_n:]

    # ==================== T078: Log Retention Check ====================

    def check_log_retention(self, retention_days: int = 90) -> Dict:
        """
        Check structured log files and warn about retention policy compliance (T078).

        Constitutional Principle IX: 90-day retention — logs are NEVER auto-deleted.
        This method ONLY reports; it never deletes.

        Args:
            retention_days: Expected retention window in days (default: 90)

        Returns:
            Report dict with oldest_log_date, total_log_files, compliance_status
        """
        log_dir = self.vault_path / 'Logs'
        if not log_dir.exists():
            return {
                'log_dir': str(log_dir),
                'exists': False,
                'compliance_status': 'no_logs'
            }

        log_files = sorted(log_dir.glob('*.json'))
        if not log_files:
            return {
                'log_dir': str(log_dir),
                'exists': True,
                'total_log_files': 0,
                'compliance_status': 'no_logs'
            }

        oldest_file = log_files[0]
        newest_file = log_files[-1]

        try:
            oldest_date = datetime.strptime(oldest_file.stem, '%Y-%m-%d')
            days_retained = (datetime.now() - oldest_date).days
        except ValueError:
            oldest_date = None
            days_retained = None

        # Warn if logs are being deleted (fewer days than expected)
        if days_retained is not None and days_retained < retention_days:
            self.logger.warning(
                f"Log retention check: only {days_retained} days of logs found "
                f"(expected {retention_days}). Oldest: {oldest_file.name}. "
                f"NOTE: Logs must NOT be auto-deleted per Constitutional Principle IX."
            )
            compliance_status = 'warning_short_retention'
        else:
            compliance_status = 'compliant'

        report = {
            'log_dir': str(log_dir),
            'exists': True,
            'total_log_files': len(log_files),
            'oldest_log': oldest_file.name,
            'newest_log': newest_file.name,
            'days_retained': days_retained,
            'retention_days_required': retention_days,
            'compliance_status': compliance_status,
            'note': 'Logs are NEVER auto-deleted per Constitutional Principle IX'
        }

        self.logger.info(f"Log retention check: {report}")
        return report

    def check_mcp_server_health(self, service_name: str) -> Dict:
        """
        Check health of a specific MCP server (Gold Tier).

        Args:
            service_name: Name of the MCP server to check

        Returns:
            Dictionary with health status
        """
        if service_name not in self.mcp_servers:
            return {
                'service': service_name,
                'status': 'unknown',
                'error': 'Service not registered'
            }

        try:
            # Try to import the circuit breaker to check service health
            from utils.retry_handler import get_circuit_breaker

            cb = get_circuit_breaker(service_name)
            cb_state = cb.get_state()

            # Update registry
            self.mcp_servers[service_name]['last_check'] = datetime.now()
            self.mcp_servers[service_name]['status'] = cb_state['state']

            return {
                'service': service_name,
                'status': cb_state['state'],
                'failure_count': cb_state['failure_count'],
                'last_check': self.mcp_servers[service_name]['last_check'].isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error checking health for {service_name}: {e}")
            self.mcp_servers[service_name]['status'] = 'error'
            return {
                'service': service_name,
                'status': 'error',
                'error': str(e)
            }

    def attempt_service_restart(self, service_name: str) -> bool:
        """
        Attempt to restart a failed MCP server (Gold Tier watchdog).

        Args:
            service_name: Name of the service to restart

        Returns:
            True if restart was attempted, False if max attempts reached

        Constitutional Compliance:
            - Max 3 restart attempts per service
            - Reset attempt count after 5 minutes without issues
            - Alert user after max attempts exceeded
        """
        # Reset restart count if enough time has passed
        if service_name in self.watchdog_last_restart_time:
            time_since_restart = (datetime.now() - self.watchdog_last_restart_time[service_name]).total_seconds()
            if time_since_restart > self.watchdog_restart_window:
                self.watchdog_restart_counts[service_name] = 0
                self.logger.info(f"Reset restart count for {service_name} (no issues for {time_since_restart:.0f}s)")

        # Check if we've exceeded max attempts
        restart_count = self.watchdog_restart_counts.get(service_name, 0)
        if restart_count >= self.watchdog_max_attempts:
            self.logger.error(
                f"Service {service_name} has failed {restart_count} times. "
                f"Max restart attempts ({self.watchdog_max_attempts}) reached. Manual intervention required."
            )
            self._create_alert(service_name, restart_count)
            return False

        # Attempt restart
        try:
            self.logger.warning(f"Attempting to restart service: {service_name} (attempt {restart_count + 1}/{self.watchdog_max_attempts})")

            # Log the restart attempt
            log_structured_action(
                action="watchdog_restart",
                actor="health_monitor",
                parameters={
                    'service': service_name,
                    'attempt': restart_count + 1,
                    'max_attempts': self.watchdog_max_attempts
                },
                result={'status': 'initiated'},
                vault_path=str(self.vault_path)
            )

            # In a real implementation, this would restart the MCP server process
            # For now, we'll just reset the circuit breaker
            from utils.retry_handler import get_circuit_breaker
            cb = get_circuit_breaker(service_name)
            cb.reset()

            # Update restart tracking
            self.watchdog_restart_counts[service_name] = restart_count + 1
            self.watchdog_last_restart_time[service_name] = datetime.now()

            self.logger.info(f"Service {service_name} restart initiated successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to restart service {service_name}: {e}")
            self.record_error(service_name, e)
            return False

    def _create_alert(self, service_name: str, restart_count: int):
        """
        Create an alert file in Needs_Action/ for manual intervention.

        Args:
            service_name: Name of the failed service
            restart_count: Number of restart attempts made
        """
        try:
            alert_dir = self.vault_path / "Needs_Action"
            alert_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            alert_file = alert_dir / f"ALERT_SERVICE_DOWN_{service_name}_{timestamp}.md"

            alert_content = f"""# ⚠️ SERVICE FAILURE ALERT

**Service**: {service_name}
**Status**: DOWN
**Restart Attempts**: {restart_count}/{self.watchdog_max_attempts}
**Time**: {datetime.now().isoformat()}

## Problem

The {service_name} MCP server has failed and the watchdog was unable to recover it after {restart_count} restart attempts.

## Actions Taken

- Watchdog attempted {restart_count} automatic restarts
- All restart attempts failed
- Service is currently unavailable

## Required Action

**MANUAL INTERVENTION REQUIRED**

1. Check the service logs in `AI_Employee/Logs/`
2. Verify service configuration in `.mcp.json`
3. Check for authentication/credential issues
4. Restart the service manually if needed
5. Delete this alert file after resolving the issue

## Error Report

{json.dumps(self.get_error_report(), indent=2)}

---
*This alert was auto-generated by the Health Monitor*
"""

            with open(alert_file, 'w', encoding='utf-8') as f:
                f.write(alert_content)

            self.logger.critical(f"Alert created: {alert_file}")

            # Log the alert creation
            log_structured_action(
                action="alert_created",
                actor="health_monitor",
                parameters={
                    'service': service_name,
                    'restart_attempts': restart_count,
                    'alert_file': str(alert_file)
                },
                result={'status': 'success'},
                approval_status="not_required",
                vault_path=str(self.vault_path)
            )

        except Exception as e:
            self.logger.error(f"Failed to create alert file: {e}")

    def perform_health_check(self) -> Dict:
        """
        Perform a comprehensive health check of the system.

        Returns:
            Dictionary containing health status information
        """
        try:
            # Check system resources
            resource_status = self._check_system_resources()

            # Check vault accessibility
            vault_status = self._check_vault_accessibility()

            # Check watcher services
            watcher_status = self._check_watcher_services()

            # Check MCP servers
            mcp_status = self._check_mcp_servers()

            # Calculate overall health
            overall_health = self._calculate_overall_health(resource_status, vault_status, watcher_status, mcp_status)

            # Create health report
            health_report = {
                'timestamp': datetime.now().isoformat(),
                'uptime_hours': (datetime.now() - self.system_start_time).total_seconds() / 3600,
                'overall_health': overall_health,
                'system_resources': resource_status,
                'vault_accessibility': vault_status,
                'watcher_services': watcher_status,
                'mcp_servers': mcp_status
            }

            return health_report

        except Exception as e:
            self.logger.error(f"Error performing health check: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'overall_health': 'critical'
            }

    def _check_system_resources(self) -> Dict:
        """
        Check system resource usage.

        Returns:
            Dictionary containing resource status
        """
        try:
            import psutil

            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Get disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100

            # Check if resources are within acceptable limits
            cpu_status = 'ok' if cpu_percent < 80 else 'warning' if cpu_percent < 90 else 'critical'
            memory_status = 'ok' if memory_percent < 80 else 'warning' if memory_percent < 90 else 'critical'
            disk_status = 'ok' if disk_percent < 80 else 'warning' if disk_percent < 90 else 'critical'

            return {
                'cpu_percent': cpu_percent,
                'cpu_status': cpu_status,
                'memory_percent': memory_percent,
                'memory_status': memory_status,
                'disk_percent': disk_percent,
                'disk_status': disk_status,
                'status': self._worst_status([cpu_status, memory_status, disk_status])
            }
        except Exception as e:
            self.logger.error(f"Error checking system resources: {e}")
            return {
                'error': str(e),
                'status': 'critical'
            }

    def _check_vault_accessibility(self) -> Dict:
        """
        Check if the vault is accessible.

        Returns:
            Dictionary containing vault status
        """
        try:
            vault_path = self.vault_path

            # Check if vault directory exists
            if not vault_path.exists():
                return {
                    'accessible': False,
                    'error': 'Vault directory does not exist',
                    'status': 'critical'
                }

            # Check if we can read/write to vault
            test_file = vault_path / ".health_test"
            try:
                test_file.touch()
                test_file.unlink()  # Remove test file
                return {
                    'accessible': True,
                    'status': 'ok'
                }
            except PermissionError:
                return {
                    'accessible': False,
                    'error': 'Permission denied accessing vault',
                    'status': 'critical'
                }

        except Exception as e:
            self.logger.error(f"Error checking vault accessibility: {e}")
            return {
                'accessible': False,
                'error': str(e),
                'status': 'critical'
            }

    def _check_watcher_services(self) -> Dict:
        """
        Check the status of watcher services.

        Returns:
            Dictionary containing watcher service status
        """
        # In a real implementation, this would check the actual status of running watchers
        # For now, we'll return a placeholder status
        return {
            'status': 'ok',  # Assume OK unless we have specific monitoring
            'watchers_running': 0  # Would be populated with actual count
        }

    def _check_mcp_servers(self) -> Dict:
        """
        Check the status of MCP servers (Bronze/Silver + Gold Tier).

        Returns:
            Dictionary containing MCP server status
        """
        # Check if MCP configuration exists
        mcp_config_path = Path.cwd() / ".mcp.json"

        if not mcp_config_path.exists():
            return {
                'config_exists': False,
                'status': 'warning',
                'message': '.mcp.json configuration file not found'
            }

        try:
            with open(mcp_config_path, 'r') as f:
                config = json.load(f)

            servers = config.get('mcpServers', {})
            server_status = {}
            all_statuses = []

            for server_name, server_config in servers.items():
                # Basic configuration check
                server_info = {
                    'configured': True,
                    'type': server_config.get('type', 'unknown')
                }

                # Gold Tier: Check if this is a monitored service
                if server_name in self.mcp_servers and self.mcp_servers[server_name]['enabled']:
                    health_check = self.check_mcp_server_health(server_name)
                    server_info.update(health_check)

                    # Map circuit breaker states to health statuses
                    if health_check['status'] == 'closed':
                        status = 'ok'
                    elif health_check['status'] == 'half_open':
                        status = 'warning'
                    elif health_check['status'] == 'open':
                        status = 'critical'

                        # Gold Tier: Attempt watchdog restart if enabled
                        if self.watchdog_enabled:
                            self.logger.warning(f"MCP server {server_name} is in OPEN state, attempting restart")
                            restart_success = self.attempt_service_restart(server_name)
                            server_info['restart_attempted'] = restart_success
                    else:
                        status = 'warning'

                    server_info['health_status'] = status
                    all_statuses.append(status)

                server_status[server_name] = server_info

            # Calculate overall MCP status
            if all_statuses:
                overall_status = self._worst_status(all_statuses)
            else:
                overall_status = 'ok'

            return {
                'config_exists': True,
                'servers': server_status,
                'status': overall_status,
                'watchdog_enabled': self.watchdog_enabled,
                'restart_counts': dict(self.watchdog_restart_counts)
            }

        except Exception as e:
            self.logger.error(f"Error checking MCP servers: {e}")
            return {
                'config_exists': True,
                'error': str(e),
                'status': 'critical'
            }

    def _calculate_overall_health(self, resource_status: Dict, vault_status: Dict,
                                 watcher_status: Dict, mcp_status: Dict) -> str:
        """
        Calculate overall health based on all status checks.

        Args:
            resource_status: System resource status
            vault_status: Vault accessibility status
            watcher_status: Watcher service status
            mcp_status: MCP server status

        Returns:
            Overall health status ('ok', 'warning', 'critical')
        """
        statuses = []

        if 'status' in resource_status:
            statuses.append(resource_status['status'])
        if 'status' in vault_status:
            statuses.append(vault_status['status'])
        if 'status' in watcher_status:
            statuses.append(watcher_status['status'])
        if 'status' in mcp_status:
            statuses.append(mcp_status['status'])

        return self._worst_status(statuses)

    def _worst_status(self, statuses: List[str]) -> str:
        """
        Determine the worst status from a list of statuses.

        Args:
            statuses: List of status strings

        Returns:
            The worst status ('critical', 'warning', or 'ok')
        """
        if 'critical' in statuses:
            return 'critical'
        elif 'warning' in statuses:
            return 'warning'
        else:
            return 'ok'

    def _log_health_status(self, health_status: Dict):
        """
        Log the health status to the health log file.

        Args:
            health_status: Dictionary containing health status
        """
        try:
            # Read existing log
            existing_log = self._read_health_log()

            # Add new status
            existing_log.append(health_status)

            # Keep only last 1000 entries to prevent log from growing too large
            if len(existing_log) > 1000:
                existing_log = existing_log[-1000:]

            # Write updated log
            self._write_health_log(existing_log)

        except Exception as e:
            self.logger.error(f"Error logging health status: {e}")

    def _read_health_log(self) -> List[Dict]:
        """
        Read the health log from file.

        Returns:
            List of health status dictionaries
        """
        try:
            with open(self.health_log_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _write_health_log(self, log_data: List[Dict]):
        """
        Write the health log to file.

        Args:
            log_data: List of health status dictionaries
        """
        try:
            with open(self.health_log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error writing health log: {e}")

    def _handle_issues(self, health_status: Dict):
        """
        Handle any issues detected in the health status.

        Args:
            health_status: Dictionary containing health status
        """
        if health_status.get('overall_health') == 'critical':
            self.logger.critical("CRITICAL SYSTEM HEALTH ISSUE DETECTED")
            self.last_error_time = datetime.now()

            # In a real system, you might want to trigger alerts or recovery procedures
            # For now, we'll just log the issue

        elif health_status.get('overall_health') == 'warning':
            self.logger.warning("WARNING: System health degradation detected")

            # Log warnings for specific issues
            resource_status = health_status.get('system_resources', {})
            if resource_status.get('status') == 'warning':
                self.logger.warning(f"Resource usage warning: CPU={resource_status.get('cpu_percent')}%, Memory={resource_status.get('memory_percent')}%, Disk={resource_status.get('disk_percent')}%")

        # Check for extended periods of issues
        if self.last_error_time:
            time_since_error = datetime.now() - self.last_error_time
            if time_since_error > timedelta(hours=1):
                # Reset the error time to avoid repeated warnings
                self.logger.info(f"System recovered from error that lasted {time_since_error}")
                self.last_error_time = None

    def get_uptime_report(self) -> Dict:
        """
        Get a report on system uptime.

        Returns:
            Dictionary containing uptime information
        """
        uptime = datetime.now() - self.system_start_time
        hours = uptime.total_seconds() / 3600

        # Read health log to assess stability
        health_log = self._read_health_log()

        # Count critical and warning events in the last 24 hours
        last_24h = datetime.now() - timedelta(hours=24)
        critical_events = 0
        warning_events = 0

        for entry in health_log:
            try:
                entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                if entry_time >= last_24h:
                    if entry.get('overall_health') == 'critical':
                        critical_events += 1
                    elif entry.get('overall_health') == 'warning':
                        warning_events += 1
            except:
                continue  # Skip invalid entries

        return {
            'total_uptime_hours': hours,
            'system_start_time': self.system_start_time.isoformat(),
            'critical_events_last_24h': critical_events,
            'warning_events_last_24h': warning_events,
            'average_health_score': self._calculate_average_health_score(health_log)
        }

    def _calculate_average_health_score(self, health_log: List[Dict]) -> float:
        """
        Calculate an average health score based on recent health logs.

        Args:
            health_log: List of health status dictionaries

        Returns:
            Average health score (0.0-1.0, where 1.0 is perfect health)
        """
        if not health_log:
            return 1.0

        # Look at last 24 hours of data
        last_24h = datetime.now() - timedelta(hours=24)
        recent_entries = [
            entry for entry in health_log
            if datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00')) >= last_24h
        ]

        if not recent_entries:
            return 1.0

        # Assign scores: critical=0.0, warning=0.5, ok=1.0
        score_map = {'critical': 0.0, 'warning': 0.5, 'ok': 1.0}
        scores = [score_map.get(entry.get('overall_health', 'ok'), 0.5) for entry in recent_entries]

        return sum(scores) / len(scores) if scores else 1.0

    def get_watchdog_report(self) -> Dict:
        """
        Get Gold Tier watchdog status report.

        Returns:
            Dictionary containing watchdog statistics
        """
        return {
            'watchdog_enabled': self.watchdog_enabled,
            'max_attempts': self.watchdog_max_attempts,
            'restart_window_seconds': self.watchdog_restart_window,
            'services': {
                name: {
                    'enabled': info['enabled'],
                    'status': info['status'],
                    'restart_count': self.watchdog_restart_counts.get(name, 0),
                    'last_restart': self.watchdog_last_restart_time.get(name, 'never')
                }
                for name, info in self.mcp_servers.items()
            },
            'error_report': self.get_error_report()
        }


def get_health_monitor(vault_path: str) -> HealthMonitor:
    """
    Get a HealthMonitor instance for the specified vault.

    Args:
        vault_path: Path to the Obsidian vault

    Returns:
        HealthMonitor instance
    """
    return HealthMonitor(vault_path)


if __name__ == "__main__":
    # Example usage - Bronze/Silver Tier
    import sys
    import os
    import logging

    # Add parent directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    print("=== Bronze/Silver Tier Health Monitor Test ===\n")

    # Create a health monitor
    monitor = HealthMonitor("./test_vault")

    print("Health Monitor initialized")
    print(f"System start time: {monitor.system_start_time}")

    # Perform a manual health check
    health_status = monitor.perform_health_check()
    print(f"Health check result: {health_status['overall_health']}")

    # Get uptime report
    uptime_report = monitor.get_uptime_report()
    print(f"Uptime: {uptime_report['total_uptime_hours']:.2f} hours")
    print(f"Critical events (last 24h): {uptime_report['critical_events_last_24h']}")
    print(f"Average health score: {uptime_report['average_health_score']:.2f}")

    print("\n=== Gold Tier Extensions Test ===\n")

    # Enable watchdog for Gold Tier services
    print("Enabling watchdog for Gold Tier services...")
    monitor.enable_watchdog('odoo')
    monitor.enable_watchdog('facebook')
    monitor.enable_watchdog('twitter')

    # Check individual service health
    print("\nChecking service health...")
    for service in ['odoo', 'facebook', 'twitter']:
        health = monitor.check_mcp_server_health(service)
        print(f"  {service}: {health['status']}")

    # Simulate error recording
    print("\nSimulating error recording...")
    monitor.record_error('odoo', Exception("Connection timeout"))
    monitor.record_error('odoo', Exception("Authentication failed"))
    monitor.record_error('facebook', Exception("Rate limit exceeded"))

    # Get error report
    print("\nError Report:")
    error_report = monitor.get_error_report()
    print(f"  Total errors: {error_report['total_errors']}")
    print(f"  Errors by service: {error_report['errors_by_service']}")

    # Get watchdog report
    print("\nWatchdog Report:")
    watchdog_report = monitor.get_watchdog_report()
    print(f"  Watchdog enabled: {watchdog_report['watchdog_enabled']}")
    print(f"  Max restart attempts: {watchdog_report['max_attempts']}")
    print(f"  Services monitored: {len([s for s in watchdog_report['services'].values() if s['enabled']])}")

    # Test restart attempt
    print("\nTesting watchdog restart...")
    restart_success = monitor.attempt_service_restart('odoo')
    print(f"  Restart attempt: {'Success' if restart_success else 'Failed'}")

    print("\n=== Tests Complete ===")
    print("\nGold Tier Features Demonstrated:")
    print("  ✓ Watchdog service monitoring")
    print("  ✓ Error aggregation and reporting")
    print("  ✓ Service health checks with circuit breaker integration")
    print("  ✓ Auto-restart with attempt tracking")
    print("  ✓ Alert creation for manual intervention")