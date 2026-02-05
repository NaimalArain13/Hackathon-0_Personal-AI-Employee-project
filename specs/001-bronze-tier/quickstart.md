# Quickstart Guide: Bronze Tier - Personal AI Employee Foundation

## Overview
This guide provides step-by-step instructions to set up the Bronze Tier Personal AI Employee foundation, including Obsidian vault setup, watcher implementation, and Claude Code integration.

## Prerequisites
- Python 3.13 or higher
- Node.js v24+ LTS
- Claude Code (active subscription)
- Obsidian v1.10.6+ (free)
- Git and GitHub Desktop (latest stable)

## Installation Steps

### 1. Environment Setup
```bash
# Install Python dependencies
pip install watchdog playwright google-api-python-client

# Install Node.js dependencies
npm install -g @anthropic/claude-code

# Set up project directory
mkdir ai-employee-vault
cd ai-employee-vault
```

### 2. Obsidian Vault Setup
```bash
# Create Obsidian vault structure
mkdir -p ai-employee-vault/{Inbox,Needs_Action,Done,Logs,Pending_Approval,Approved,Rejected}

# Create essential documents
touch ai-employee-vault/Dashboard.md
touch ai-employee-vault/Company_Handbook.md
```

### 3. Dashboard.md Template
Create the following content in `ai-employee-vault/Dashboard.md`:
```markdown
# AI Employee Dashboard

## Current Status
- **Last Updated**: [Auto-generated timestamp]
- **Active Tasks**: [Count of files in Needs_Action]
- **Pending Approval**: [Count of files in Pending_Approval]

## Bank Balance
- **Current**: [Manual entry or auto-populated]

## Pending Messages
- **Unread Emails**: [Auto-populated from Gmail watcher]
- **WhatsApp Messages**: [Auto-populated from WhatsApp watcher]

## Active Business Projects
- [List of active projects]

## Recent Activity
- [Log of recent AI actions]
```

### 4. Company_Handbook.md Template
Create the following content in `ai-employee-vault/Company_Handbook.md`:
```markdown
# Company Handbook

## Rules of Engagement

### Email Communication
- Always be polite and professional
- Flag any payment requests over $500 for approval
- Respond to urgent emails within 2 hours

### WhatsApp Communication
- Always be polite on WhatsApp
- Flag any financial requests for approval
- Escalate urgent messages immediately

### File Processing
- Process files in /Inbox automatically
- Flag suspicious files for review
- Maintain audit trail for all actions

### Approval Requirements
- All payments require human approval
- New contact communications require approval
- Files with sensitive keywords require review
```

### 5. File System Watcher Implementation
Create `watchers/filesystem_watcher.py`:
```python
# filesystem_watcher.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import shutil
import time
import logging

class DropFolderHandler(FileSystemEventHandler):
    def __init__(self, vault_path: str):
        self.needs_action = Path(vault_path) / 'Needs_Action'
        self.logger = logging.getLogger(self.__class__.__name__)

    def on_created(self, event):
        if event.is_directory:
            return
        source = Path(event.src_path)
        dest = self.needs_action / f'FILE_{source.name}'
        shutil.copy2(source, dest)
        self.create_metadata(source, dest)
        self.logger.info(f'File {source.name} copied to Needs_Action')

    def create_metadata(self, source: Path, dest: Path):
        meta_path = dest.with_suffix('.md')
        meta_content = f'''---
type: file_drop
original_name: {source.name}
size: {source.stat().st_size}
timestamp: {time.time()}
---

New file dropped for processing.

## Action Items
- [ ] Review file content
- [ ] Determine appropriate response
- [ ] Process or escalate as needed
'''
        meta_path.write_text(meta_content)

def start_filesystem_watcher(watch_path: str, vault_path: str):
    """Start the filesystem watcher"""
    event_handler = DropFolderHandler(vault_path)
    observer = Observer()
    observer.schedule(event_handler, watch_path, recursive=False)

    observer.start()
    print(f"Watching {watch_path} for new files...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("File watcher stopped.")
    observer.join()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python filesystem_watcher.py <watch_path> <vault_path>")
        sys.exit(1)

    watch_path = sys.argv[1]
    vault_path = sys.argv[2]
    start_filesystem_watcher(watch_path, vault_path)
```

### 6. Claude Code Configuration
Create or update `~/.config/claude-code/mcp.json`:
```json
{
  "servers": [
    {
      "name": "filesystem",
      "command": "node",
      "args": ["/path/to/filesystem-mcp/index.js"]
    }
  ]
}
```

### 7. Running the System
```bash
# 1. Start the file system watcher in one terminal
python watchers/filesystem_watcher.py /path/to/watch/directory ./ai-employee-vault

# 2. In another terminal, run Claude Code pointing to the vault
cd ai-employee-vault
claude
```

### 8. Testing the System
1. Place a file in the watched directory
2. Verify a corresponding .md file appears in the Needs_Action folder
3. Check that Claude Code can read and process files from the vault
4. Verify that processed files can be moved through the workflow (Inbox → Needs_Action → Done)

## Troubleshooting

### Common Issues
- **Permission errors**: Ensure Claude Code has read/write access to the vault directory
- **Watcher not detecting files**: Check that the watched directory exists and is writable
- **File processing errors**: Verify the file format matches expected templates

### Logs Location
- System logs: `./ai-employee-vault/Logs/`
- Watcher logs: Console output or redirect to file as needed

## Next Steps
After successful Bronze Tier setup:
1. Implement Gmail watcher for email integration
2. Add WhatsApp watcher for messaging integration
3. Set up MCP servers for external actions
4. Implement the Ralph Wiggum loop for persistent processing