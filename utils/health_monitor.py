"""
Health Monitor Module for the Personal AI Employee system.
Monitors system health to ensure 24+ hours of uptime without manual intervention.
"""

import json
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from utils.setup_logger import setup_logger


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

        # Health log
        self.health_log_file = self.vault_path / "Logs" / "health_monitor.json"
        self.health_log_file.parent.mkdir(exist_ok=True)

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
        Check the status of MCP servers.

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

            for server_name, server_config in servers.items():
                # For now, just check that the configuration is valid
                server_status[server_name] = {
                    'configured': True,
                    'type': server_config.get('type', 'unknown')
                }

            return {
                'config_exists': True,
                'servers': server_status,
                'status': 'ok'
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
    # Example usage
    import logging

    # Set up logging
    logging.basicConfig(level=logging.INFO)

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