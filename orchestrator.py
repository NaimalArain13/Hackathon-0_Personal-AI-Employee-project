#!/usr/bin/env python3
"""
Main orchestrator for the Personal AI Employee system.
Manages the execution of various watcher processes and coordinates
between different components of the system.
"""

import os
import sys
import time
import signal
import logging
import argparse
import threading
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add the project root to the path to import from other modules
sys.path.insert(0, str(Path(__file__).parent))

from utils.setup_logger import setup_logger
from utils.file_utils import scan_for_approval_changes


def ensure_directory_exists(path: str):
    """Ensure a directory exists, creating it if necessary."""
    Path(path).mkdir(parents=True, exist_ok=True)


class Orchestrator:
    """
    Main orchestrator class that manages the Personal AI Employee system.
    Coordinates between different watchers, handles configuration,
    and manages the overall workflow.
    """

    def __init__(self, config_path: str = ".env"):
        """
        Initialize the orchestrator with configuration.

        Args:
            config_path: Path to the configuration file (default: .env)
        """
        self.logger = setup_logger("Orchestrator", level=logging.INFO)
        self.config = self.load_config(config_path)
        self.running = True
        self.watchers = []
        self.watcher_threads = []

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Ensure vault directory exists
        vault_path = self.config.get('VAULT_PATH', 'D:\\Obsidian Vaults\\AI_Employee_Vault')
        ensure_directory_exists(vault_path)

        # Initialize Silver Tier features
        self.approval_monitor_thread = None
        self.scheduled_task_thread = None

        self.logger.info("Orchestrator initialized successfully")

    def load_config(self, config_path: str) -> Dict[str, str]:
        """
        Load configuration from environment variables or .env file.

        Args:
            config_path: Path to the configuration file

        Returns:
            Dictionary containing configuration values
        """
        config = {}

        # Load from .env file if it exists
        env_file = Path(config_path)
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                config[key.strip()] = value.strip().strip('"\'')
            except Exception as e:
                self.logger.error(f"Error loading config from {config_path}: {e}")

        # Override with environment variables if they exist
        default_values = {
            'VAULT_PATH': 'D:\\Obsidian Vaults\\AI_Employee_Vault',
            'WATCH_FOLDER_PATH': './watch_folder',
            'CHECK_INTERVAL': '60',
            'LOG_LEVEL': 'INFO',
            'DEV_MODE': 'false',
            'DRY_RUN': 'false',
            'MAX_RETRY_ATTEMPTS': '5',
            'INITIAL_RETRY_DELAY': '1',
            'SCHEDULE_POST_INTERVAL': '3600',  # Default: 1 hour
            'WHATSAPP_ENABLED': 'false'
        }

        for key, default_val in default_values.items():
            env_val = os.environ.get(key)
            if env_val is not None:
                config[key] = env_val
            elif key not in config:
                config[key] = default_val

        return config

    def signal_handler(self, signum, frame):
        """
        Handle shutdown signals gracefully.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    def initialize_watchers(self) -> List[Any]:
        """
        Initialize and return the watcher instances based on configuration.

        Returns:
            List of watcher instances to run
        """
        watchers = []

        # Import watchers dynamically to avoid circular imports
        try:
            from watchers.filesystem_watcher import FileWatcher
            from watchers.gmail_watcher import GmailWatcher

            vault_path = self.config.get('VAULT_PATH', './ai-employee-vault')
            watch_path = self.config.get('WATCH_FOLDER_PATH', './watch_folder')

            # Create filesystem watcher
            file_watcher = FileWatcher(vault_path=vault_path, check_interval=int(self.config.get('CHECK_INTERVAL', 60)))
            watchers.append(file_watcher)
            self.logger.info(f"Initialized FileWatcher monitoring {watch_path}")

            # Create Gmail watcher if credentials are available
            if self.config.get('GMAIL_CLIENT_ID') and self.config.get('GMAIL_CLIENT_SECRET'):
                gmail_watcher = GmailWatcher(vault_path=vault_path, check_interval=int(self.config.get('CHECK_INTERVAL', 60)))
                watchers.append(gmail_watcher)
                self.logger.info("Initialized GmailWatcher")
            else:
                self.logger.info("Gmail credentials not found, skipping GmailWatcher initialization")

            # For Silver Tier - Initialize additional watchers if needed
            # WhatsApp watcher would be initialized here when available
            whatsapp_enabled = self.config.get('WHATSAPP_ENABLED', '').lower() == 'true'
            if whatsapp_enabled:
                try:
                    from watchers.whatsapp_watcher import WhatsAppWatcher
                    whatsapp_watcher = WhatsAppWatcher(vault_path=vault_path, check_interval=int(self.config.get('CHECK_INTERVAL', 60)))
                    watchers.append(whatsapp_watcher)
                    self.logger.info("Initialized WhatsAppWatcher")
                except ImportError:
                    self.logger.info("WhatsAppWatcher not available, skipping initialization")

        except ImportError as e:
            self.logger.error(f"Could not import watcher: {e}")
        except Exception as e:
            self.logger.error(f"Error initializing watchers: {e}")

        return watchers

    def monitor_approvals(self):
        """
        Monitor for approval status changes in Approved and Rejected folders.
        This runs in a separate thread to continuously monitor for changes.
        """
        vault_path = self.config.get('VAULT_PATH', './ai-employee-vault')

        while self.running:
            try:
                changes = scan_for_approval_changes(vault_path)

                for change in changes:
                    self.logger.info(f"Approval change detected: {change['status']} - {change['file_path']}")

                    # Process the approval change based on the status
                    if change['status'] == 'approved':
                        self.handle_approved_action(change)
                    elif change['status'] == 'rejected':
                        self.handle_rejected_action(change)

                # Sleep before next check
                time.sleep(5)  # Check every 5 seconds

            except Exception as e:
                self.logger.error(f"Error in approval monitoring: {e}")
                time.sleep(10)  # Wait longer before retry on error

    def handle_approved_action(self, change: Dict):
        """
        Handle an approved action from the approval monitoring.

        Args:
            change: Dictionary containing the approval change information
        """
        self.logger.info(f"Processing approved action: {change['file_path']}")
        # In a real implementation, this would execute the approved action
        # For now, just log that it was approved

    def handle_rejected_action(self, change: Dict):
        """
        Handle a rejected action from the approval monitoring.

        Args:
            change: Dictionary containing the rejection change information
        """
        self.logger.info(f"Processing rejected action: {change['file_path']}")
        # In a real implementation, this would handle the rejection
        # For now, just log that it was rejected

    def start_approval_monitoring(self):
        """
        Start the approval monitoring thread.
        """
        self.approval_monitor_thread = threading.Thread(target=self.monitor_approvals, daemon=True)
        self.approval_monitor_thread.start()
        self.logger.info("Started approval monitoring thread")

    def run_watchers_concurrently(self):
        """
        Run all initialized watchers concurrently using threads.
        """
        for i, watcher in enumerate(self.watchers):
            watcher_thread = threading.Thread(target=watcher.run, name=f"WatcherThread-{i}", daemon=True)
            self.watcher_threads.append(watcher_thread)
            watcher_thread.start()
            self.logger.info(f"Started watcher thread: {watcher_thread.name}")

        # Keep the main thread alive to monitor the watcher threads
        try:
            while self.running:
                # Check if any threads have died
                for i, thread in enumerate(self.watcher_threads):
                    if not thread.is_alive():
                        self.logger.error(f"Watcher thread {thread.name} died unexpectedly, attempting restart...")
                        # Restart the failed watcher
                        if i < len(self.watchers):
                            failed_watcher = self.watchers[i]
                            restart_thread = threading.Thread(target=failed_watcher.run, name=f"Restarted-{failed_watcher.__class__.__name__}", daemon=True)
                            self.watcher_threads[i] = restart_thread
                            restart_thread.start()

                time.sleep(5)  # Check every 5 seconds
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received, stopping watchers...")
        except Exception as e:
            self.logger.error(f"Error in watcher management: {e}")

    def run(self):
        """
        Main execution loop for the orchestrator.
        Initializes watchers and runs them concurrently.
        """
        self.logger.info("Starting Personal AI Employee Orchestrator...")
        self.logger.info(f"Configuration: {dict((k, '***' if 'KEY' in k or 'SECRET' in k or 'PASSWORD' in k else v) for k, v in self.config.items())}")

        # Initialize watchers
        self.watchers = self.initialize_watchers()

        if not self.watchers:
            self.logger.warning("No watchers initialized. Exiting.")
            return

        # Start approval monitoring (Silver Tier feature)
        self.start_approval_monitoring()

        # Run watchers concurrently
        self.logger.info(f"Starting {len(self.watchers)} watcher(s) concurrently...")
        self.run_watchers_concurrently()

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the orchestrator.

        Returns:
            Dictionary with health status information
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy' if self.running else 'shutdown',
            'config_loaded': bool(self.config),
            'vault_accessible': Path(self.config.get('VAULT_PATH', './ai-employee-vault')).exists(),
            'watchers_running': len([t for t in self.watcher_threads if t.is_alive()]),
            'approval_monitor_active': self.approval_monitor_thread.is_alive() if self.approval_monitor_thread else False,
            'uptime': getattr(self, '_start_time', datetime.now()).isoformat()
        }


def main():
    """
    Main entry point for the orchestrator.
    """
    parser = argparse.ArgumentParser(description='Personal AI Employee Orchestrator')
    parser.add_argument('--config', '-c', default='.env', help='Configuration file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    orchestrator = Orchestrator(config_path=args.config)

    # Store start time for health checks
    orchestrator._start_time = datetime.now()

    try:
        orchestrator.run()
    except Exception as e:
        logging.error(f"Critical error in orchestrator: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()