import time
import logging
import random
from pathlib import Path
from abc import ABC, abstractmethod


class BaseWatcher(ABC):
    """
    Abstract base class for all watcher implementations.
    Defines the common interface and structure for watcher components.
    """

    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the base watcher.

        Args:
            vault_path: Path to the Obsidian vault
            check_interval: Time in seconds between checks for updates
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)

        # Create Needs_Action directory if it doesn't exist
        self.needs_action.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def check_for_updates(self) -> list:
        """
        Check for new items that need processing.

        Returns:
            List of new items to process
        """
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        """
        Create an action file in the Needs_Action folder.

        Args:
            item: The item to create an action file for

        Returns:
            Path to the created action file
        """
        pass

    def exponential_backoff_retry(self, operation, max_retries=5, initial_delay=1):
        """
        Execute an operation with exponential backoff retry strategy.

        Args:
            operation: Callable to execute
            max_retries: Maximum number of retry attempts (default 5)
            initial_delay: Initial delay in seconds (default 1)

        Returns:
            Result of the operation if successful
        """
        delay = initial_delay
        for attempt in range(max_retries):
            try:
                return operation()
            except Exception as e:
                if attempt == max_retries - 1:  # Last attempt
                    self.logger.error(f"Operation failed after {max_retries} attempts: {e}")
                    raise
                else:
                    self.logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2  # Double the delay for next attempt (plus some jitter)
                    delay += random.uniform(0, 1)  # Add jitter to prevent thundering herd

        # This should not be reached, but included for completeness
        raise RuntimeError(f"Failed to execute operation after {max_retries} attempts")

    def run(self):
        """
        Main execution loop for the watcher.
        Continuously checks for updates at the specified interval.
        """
        self.logger.info(f'Starting {self.__class__.__name__}')
        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    self.create_action_file(item)
            except Exception as e:
                self.logger.error(f'Error in {self.__class__.__name__}: {e}')
            time.sleep(self.check_interval)


if __name__ == "__main__":
    # Example usage - this would be overridden by subclasses
    pass