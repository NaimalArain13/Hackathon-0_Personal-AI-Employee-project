"""
Resource Monitoring Module for the Personal AI Employee system.
Monitors resource usage and performance impact of multiple concurrent watchers.
"""

import logging
import psutil
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from utils.setup_logger import setup_logger


class ResourceMonitor:
    """
    Class to monitor resource usage and performance impact of watchers.
    """

    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize the resource monitor.

        Args:
            log_file: Optional file to log resource usage data
        """
        self.logger = setup_logger("ResourceMonitor", level=logging.INFO)
        self.log_file = log_file
        self.monitoring = False
        self.monitoring_thread = None
        self.resource_data = []
        self.process = psutil.Process()

        # Performance thresholds
        self.cpu_threshold = 80.0  # percentage
        self.memory_threshold = 80.0  # percentage
        self.thread_threshold = 100  # number of threads

    def start_monitoring(self, interval: float = 5.0):
        """
        Start monitoring resource usage.

        Args:
            interval: Interval in seconds between measurements
        """
        if self.monitoring:
            self.logger.warning("Resource monitoring is already running")
            return

        self.monitoring = True
        self.logger.info("Starting resource monitoring...")

        def monitor_loop():
            while self.monitoring:
                data_point = self.get_current_resources()
                self.resource_data.append(data_point)

                # Log to file if specified
                if self.log_file:
                    self._log_to_file(data_point)

                # Check for threshold violations
                self._check_thresholds(data_point)

                time.sleep(interval)

        self.monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitoring_thread.start()

    def stop_monitoring(self):
        """Stop monitoring resource usage."""
        self.monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        self.logger.info("Stopped resource monitoring")

    def get_current_resources(self) -> Dict:
        """
        Get current resource usage statistics.

        Returns:
            Dictionary containing current resource usage data
        """
        try:
            # CPU usage
            cpu_percent = self.process.cpu_percent()

            # Memory usage
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()

            # Thread count
            thread_count = self.process.num_threads()

            # Disk I/O
            io_counters = self.process.io_counters() if hasattr(self.process, 'io_counters') else None

            # Network I/O (for the whole system since process-level is not always available)
            net_io = psutil.net_io_counters()

            # Timestamp
            timestamp = datetime.now().isoformat()

            return {
                'timestamp': timestamp,
                'cpu_percent': cpu_percent,
                'memory_rss_mb': memory_info.rss / 1024 / 1024 if memory_info else 0,
                'memory_vms_mb': memory_info.vms / 1024 / 1024 if memory_info else 0,
                'memory_percent': memory_percent,
                'thread_count': thread_count,
                'disk_read_bytes': io_counters.read_bytes if io_counters else 0,
                'disk_write_bytes': io_counters.write_bytes if io_counters else 0,
                'net_bytes_sent': net_io.bytes_sent,
                'net_bytes_recv': net_io.bytes_recv
            }
        except Exception as e:
            self.logger.error(f"Error getting resource data: {e}")
            return {}

    def _log_to_file(self, data_point: Dict):
        """
        Log resource data to file.

        Args:
            data_point: Resource data to log
        """
        try:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            with open(log_path, 'a') as f:
                f.write(f"{data_point['timestamp']},")
                f.write(f"CPU:{data_point['cpu_percent']:.2f}%,")
                f.write(f"MEM:{data_point['memory_percent']:.2f}%,")
                f.write(f"THREADS:{data_point['thread_count']},")
                f.write(f"RSS:{data_point['memory_rss_mb']:.2f}MB\n")
        except Exception as e:
            self.logger.error(f"Error writing to log file: {e}")

    def _check_thresholds(self, data_point: Dict):
        """
        Check if resource usage exceeds thresholds.

        Args:
            data_point: Resource data to check
        """
        alerts = []

        if data_point.get('cpu_percent', 0) > self.cpu_threshold:
            alerts.append(f"High CPU usage: {data_point['cpu_percent']:.2f}%")

        if data_point.get('memory_percent', 0) > self.memory_threshold:
            alerts.append(f"High memory usage: {data_point['memory_percent']:.2f}%")

        if data_point.get('thread_count', 0) > self.thread_threshold:
            alerts.append(f"High thread count: {data_point['thread_count']}")

        if alerts:
            alert_msg = f"Resource threshold exceeded: {', '.join(alerts)}"
            self.logger.warning(alert_msg)

    def get_average_resources(self) -> Dict:
        """
        Calculate average resource usage from collected data.

        Returns:
            Dictionary containing average resource usage
        """
        if not self.resource_data:
            return {}

        avg_data = {}
        keys = self.resource_data[0].keys()

        for key in keys:
            if key != 'timestamp':
                values = [point.get(key, 0) for point in self.resource_data if key in point]
                if values:
                    avg_data[f'avg_{key}'] = sum(values) / len(values)
                else:
                    avg_data[f'avg_{key}'] = 0

        return avg_data

    def get_peak_resources(self) -> Dict:
        """
        Get peak resource usage from collected data.

        Returns:
            Dictionary containing peak resource usage
        """
        if not self.resource_data:
            return {}

        peak_data = {}
        keys = [k for k in self.resource_data[0].keys() if k != 'timestamp']

        for key in keys:
            values = [point.get(key, 0) for point in self.resource_data if key in point]
            if values:
                peak_data[f'peak_{key}'] = max(values)
            else:
                peak_data[f'peak_{key}'] = 0

        return peak_data

    def get_summary_report(self) -> str:
        """
        Generate a summary report of resource usage.

        Returns:
            Formatted string with resource usage summary
        """
        if not self.resource_data:
            return "No resource data collected."

        avg_data = self.get_average_resources()
        peak_data = self.get_peak_resources()

        report = []
        report.append("Resource Usage Summary")
        report.append("=" * 30)
        report.append(f"Data Points Collected: {len(self.resource_data)}")

        if avg_data:
            report.append("\nAverage Usage:")
            for key, value in avg_data.items():
                if 'percent' in key or 'count' in key or 'bytes' in key or 'mb' in key:
                    if isinstance(value, float):
                        report.append(f"  {key}: {value:.2f}")
                    else:
                        report.append(f"  {key}: {value}")

        if peak_data:
            report.append("\nPeak Usage:")
            for key, value in peak_data.items():
                if 'percent' in key or 'count' in key or 'bytes' in key or 'mb' in key:
                    if isinstance(value, float):
                        report.append(f"  {key}: {value:.2f}")
                    else:
                        report.append(f"  {key}: {value}")

        return "\n".join(report)

    def reset_data(self):
        """Reset collected resource data."""
        self.resource_data = []


def monitor_multiple_watchers(watchers: List, duration: int = 60, interval: float = 5.0) -> ResourceMonitor:
    """
    Monitor resource usage while multiple watchers are running.

    Args:
        watchers: List of watcher instances to monitor
        duration: Duration in seconds to monitor
        interval: Interval in seconds between measurements

    Returns:
        ResourceMonitor instance with collected data
    """
    monitor = ResourceMonitor(log_file="./logs/resource_usage.log")

    # Start monitoring
    monitor.start_monitoring(interval=interval)

    # Let watchers run for the specified duration
    time.sleep(duration)

    # Stop monitoring
    monitor.stop_monitoring()

    return monitor


if __name__ == "__main__":
    # Example usage
    import logging

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Create a resource monitor
    monitor = ResourceMonitor(log_file="./test_resource_log.csv")

    print("Starting resource monitoring...")
    monitor.start_monitoring(interval=2.0)  # Sample every 2 seconds

    # Simulate some activity
    print("Performing simulated work...")
    for i in range(10):
        # Do some work to consume resources
        data = [j for j in range(10000)]
        time.sleep(0.5)

    # Stop monitoring
    monitor.stop_monitoring()

    # Print summary
    print("\n" + monitor.get_summary_report())

    # Clean up test file
    import os
    if os.path.exists("./test_resource_log.csv"):
        os.remove("./test_resource_log.csv")