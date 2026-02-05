#!/usr/bin/env python3
"""
File system watcher implementation for the Personal AI Employee.
Monitors a designated folder for new files and creates action files in the /Needs_Action folder.
"""

import time
import logging
import shutil
from pathlib import Path
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add the project root to the path to import from other modules
import sys
from pathlib import Path as PPath
sys.path.insert(0, str(PPath(__file__).parent.parent))

from watchers.base_watcher import BaseWatcher
from watchers.utils import setup_logger, get_file_metadata, create_markdown_frontmatter, sanitize_filename, format_timestamp


class DropFolderHandler(FileSystemEventHandler):
    """
    Event handler for the file system watcher.
    Handles file creation events and processes them appropriately.
    """

    def __init__(self, vault_path: str):
        """
        Initialize the event handler.

        Args:
            vault_path: Path to the Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.logger = setup_logger(f"{self.__class__.__name__}", level=logging.INFO)

        # Ensure Needs_Action directory exists
        self.needs_action.mkdir(parents=True, exist_ok=True)

    def on_created(self, event):
        """
        Handle file creation events.

        Args:
            event: The file system event
        """
        if event.is_directory:
            self.logger.debug(f"Ignoring directory creation: {event.src_path}")
            return

        source = Path(event.src_path)
        self.logger.info(f"New file detected: {source.name}")

        # Create a copy in the Needs_Action folder with metadata
        self.process_new_file(source)

    def process_new_file(self, source: Path):
        """
        Process a newly detected file by creating a metadata file in Needs_Action.

        Args:
            source: Path to the source file
        """
        try:
            # Create the action file with metadata
            dest = self.needs_action / f'FILE_{sanitize_filename(source.name)}.md'

            # Create metadata content
            metadata = {
                'type': 'file_drop',
                'original_name': source.name,
                'size': source.stat().st_size,
                'timestamp': format_timestamp(),
                'source_path': str(source.absolute()),
                'extension': source.suffix,
                'status': 'pending'
            }

            # Create markdown content with frontmatter
            frontmatter = create_markdown_frontmatter(metadata)

            content = f"""{frontmatter}

# New File Drop: {source.name}

## File Information
- **Original Path**: `{source}`
- **Size**: {source.stat().st_size} bytes
- **Extension**: {source.suffix}
- **Detected At**: {format_timestamp()}

## Action Items
- [ ] Review file content
- [ ] Determine appropriate response
- [ ] Process or escalate as needed

## File Preview
```
{self._get_file_preview(source)}
```

## Suggested Next Steps
1. Analyze the content of this file
2. Determine if any action is required
3. Follow the rules defined in Company_Handbook.md
"""

            # Write the content to the destination file
            with open(dest, 'w', encoding='utf-8') as f:
                f.write(content)

            self.logger.info(f"Created action file: {dest}")

        except Exception as e:
            self.logger.error(f"Error processing file {source}: {e}")

    def _get_file_preview(self, file_path: Path, max_lines: int = 10) -> str:
        """
        Get a preview of the file content.

        Args:
            file_path: Path to the file to preview
            max_lines: Maximum number of lines to read

        Returns:
            String containing the file preview
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        lines.append("... (truncated)")
                        break
                    lines.append(line.rstrip())
                return "\n".join(lines)
        except UnicodeDecodeError:
            # For binary files, return a message
            return f"[Binary file - {file_path.suffix} - {file_path.stat().st_size} bytes]"
        except Exception as e:
            return f"[Error reading file: {e}]"


class FileWatcher(BaseWatcher):
    """
    File system watcher implementation that extends BaseWatcher.
    Uses watchdog to monitor a directory for file changes.
    """

    def __init__(self, vault_path: str, watch_path: str = "./watch_folder", check_interval: int = 5):
        """
        Initialize the file watcher.

        Args:
            vault_path: Path to the Obsidian vault
            watch_path: Path to the folder to watch for new files
            check_interval: Interval in seconds to check for changes (not used for watchdog)
        """
        super().__init__(vault_path, check_interval)
        self.watch_path = Path(watch_path)
        self.observer = None

        # Ensure watch directory exists
        self.watch_path.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"FileWatcher initialized - watching: {self.watch_path}, vault: {self.vault_path}")

    def check_for_updates(self) -> list:
        """
        For the FileWatcher, this method is not actively used since we rely on watchdog events.
        This is kept for compatibility with BaseWatcher interface.

        Returns:
            Empty list (updates are handled by watchdog events)
        """
        # This is handled by the watchdog observer
        return []

    def create_action_file(self, item) -> Path:
        """
        Create an action file for the given item.

        Args:
            item: The item to create an action file for

        Returns:
            Path to the created action file
        """
        # This is handled by DropFolderHandler
        pass

    def run(self):
        """
        Start the file system watcher using watchdog.
        """
        self.logger.info(f"Starting FileWatcher to monitor: {self.watch_path}")

        # Create event handler
        event_handler = DropFolderHandler(str(self.vault_path))

        # Create observer
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.watch_path), recursive=False)

        # Start observer
        self.observer.start()
        self.logger.info(f"Watching {self.watch_path} for new files...")

        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Stopping FileWatcher...")
            self.observer.stop()

        # Wait for observer to finish
        self.observer.join()
        self.logger.info("FileWatcher stopped.")

    def stop(self):
        """
        Stop the file system watcher.
        """
        if self.observer:
            self.observer.stop()
            self.observer.join()


def main():
    """
    Main entry point for the filesystem watcher.
    """
    import argparse

    parser = argparse.ArgumentParser(description='File System Watcher for Personal AI Employee')
    parser.add_argument('--vault-path', '-v', default='D:\\Obsidian Vaults\\AI_Employee_Vault', help='Path to the Obsidian vault')
    parser.add_argument('--watch-path', '-w', default='./watch_folder', help='Path to the folder to watch')

    args = parser.parse_args()

    # Set up logging
    logger = setup_logger("FileWatcher", level=logging.INFO)

    # Create and run the watcher
    watcher = FileWatcher(vault_path=args.vault_path, watch_path=args.watch_path)

    try:
        watcher.run()
    except KeyboardInterrupt:
        logger.info("FileWatcher interrupted by user")
    except Exception as e:
        logger.error(f"Error running FileWatcher: {e}")


if __name__ == "__main__":
    main()