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
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add the project root to the path to import from other modules
sys.path.insert(0, str(Path(__file__).parent))

from watchers.utils import setup_logger, ensure_directory_exists


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

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Ensure vault directory exists
        vault_path = self.config.get('VAULT_PATH', 'D:\\Obsidian Vaults\\AI_Employee_Vault')
        ensure_directory_exists(vault_path)

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
            'DRY_RUN': 'false'
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
            file_watcher = FileWatcher(vault_path=vault_path, watch_path=watch_path)
            watchers.append(file_watcher)
            self.logger.info(f"Initialized FileWatcher monitoring {watch_path}")

            # Create Gmail watcher if credentials are available
            if self.config.get('GMAIL_CLIENT_ID') and self.config.get('GMAIL_CLIENT_SECRET'):
                gmail_watcher = GmailWatcher(vault_path=vault_path)
                watchers.append(gmail_watcher)
                self.logger.info("Initialized GmailWatcher")
            else:
                self.logger.info("Gmail credentials not found, skipping GmailWatcher initialization")

        except ImportError as e:
            self.logger.error(f"Could not import watcher: {e}")
        except Exception as e:
            self.logger.error(f"Error initializing watchers: {e}")

        return watchers

    def run(self):
        """
        Main execution loop for the orchestrator.
        Initializes watchers and runs them in sequence.
        """
        self.logger.info("Starting Personal AI Employee Orchestrator...")
        self.logger.info(f"Configuration: {dict((k, '***' if 'KEY' in k or 'SECRET' in k or 'PASSWORD' in k else v) for k, v in self.config.items())}")

        # Initialize watchers
        watchers = self.initialize_watchers()

        if not watchers:
            self.logger.warning("No watchers initialized. Exiting.")
            return

        # Run watchers (in a real implementation, this might run them in separate threads/processes)
        self.logger.info(f"Starting {len(watchers)} watcher(s)...")

        # For now, we'll run the first watcher in a loop
        # In a production implementation, you'd want to run multiple watchers concurrently
        if watchers:
            primary_watcher = watchers[0]
            self.logger.info(f"Running primary watcher: {primary_watcher.__class__.__name__}")

            try:
                # This would typically run in a thread, but for simplicity we'll run directly
                # In a real implementation, each watcher would run in its own thread/process
                primary_watcher.run()
            except KeyboardInterrupt:
                self.logger.info("Interrupt received, shutting down...")
            except Exception as e:
                self.logger.error(f"Error running watcher: {e}")
        else:
            self.logger.error("No watchers available to run")

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