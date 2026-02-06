# Quickstart Guide: Silver Tier - Functional Assistant

## Prerequisites

Before starting the Silver Tier implementation, ensure you have:

- Python 3.13 or higher installed
- Claude Code (Pro subscription or free alternative with Claude Code Router)
- Obsidian (v1.10.6+)
- Node.js (v24+ LTS)
- Git
- Gmail account with app password enabled
- LinkedIn account (for automation via Playwright)

## Setup Steps

### 1. Clone and Prepare Environment

```bash
# If you haven't already, clone the repository
git clone <your-repo-url>
cd <your-repo-name>

# Checkout the Silver Tier branch
git checkout 002-silver-tier

# Install Python dependencies
pip install -r requirements.txt
# Or if using uv:
uv pip install -r requirements.txt
```

### 2. Set Up the Obsidian Vault Structure

The system will use your AI_Employee vault with the following folder structure:

```
AI_Employee/
├── attachments/          # For email attachments
├── Inbox/
├── Needs_Action/
├── Done/
├── Plans/
├── Pending_Approval/
├── Approved/
├── Logs/
├── Dashboard.md
└── Company_Handbook.md
```

### 3. Configure Email MCP Server

1. **Install Email MCP Server Dependencies**:
```bash
pip install pydantic python-dotenv
```

2. **Set up the email.json configuration** in the root of your project:
```json
[
  {
    "domain": "@gmail.com",
    "server": "smtp.gmail.com",
    "port": 587
  }
]
```

3. **Configure Claude Code with MCP settings** in your Claude configuration:
```json
{
  "mcpServers": {
    "email": {
      "command": "python",
      "args": [
        "-m",
        "mcp_email_server",
        "--dir",
        "/path/to/your/AI_Employee/attachments"
      ],
      "env": {
        "SENDER": "your-gmail-address@gmail.com",
        "PASSWORD": "your-16-digit-app-password"
      }
    }
  }
}
```

### 4. Set Up Playwright MCP Server for LinkedIn

```bash
# Add the Playwright MCP server to Claude
claude mcp add --transport stdio playwright npx @executeautomation/playwright-mcp-server
```

Or configure it directly in Claude settings:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@executeautomation/playwright-mcp-server"]
    }
  }
}
```

### 5. Create Required Directories

```bash
# Create the attachments directory
mkdir -p AI_Employee/attachments

# Create other necessary directories
mkdir -p AI_Employee/Inbox
mkdir -p AI_Employee/Needs_Action
mkdir -p AI_Employee/Done
mkdir -p AI_Employee/Plans
mkdir -p AI_Employee/Pending_Approval
mkdir -p AI_Employee/Approved
mkdir -p AI_Employee/Logs
```

### 6. Configure Basic Files

1. **Create Dashboard.md**:
```markdown
# AI Employee Dashboard

## Status
- Gmail Watcher: [status]
- LinkedIn Automation: [status]
- Last Processed: [timestamp]

## Today's Activities
- Emails Processed: [count]
- LinkedIn Posts: [count]
- Pending Approvals: [count]

## Recent Notifications
- [dynamic notifications appear here]
```

2. **Create Company_Handbook.md** with your business rules:
```markdown
# Company Handbook

## Rules of Engagement

### Email Responses
- Always be polite and professional
- Follow up within 24 hours for high-priority emails
- Escalate emails containing certain keywords (e.g., "urgent", "emergency")

### LinkedIn Posts
- Maintain professional tone
- Share business updates twice per week
- Include company hashtags in all posts

### Approval Requirements
- All payments over $100 require approval
- New vendor contacts require approval
- Sensitive topics require approval
```

### 7. Start the Watcher Services

Run the Gmail watcher to start monitoring emails:
```bash
cd watchers
python gmail_watcher.py
```

For WhatsApp or other watchers:
```bash
python whatsapp_watcher.py
```

### 8. Configure Scheduling

Using the `schedule` library, create a scheduler script that runs automated tasks:

```python
# scheduler.py
import schedule
import time
from pathlib import Path

def post_linkedin_update():
    # Logic to create LinkedIn post
    pass

def audit_daily_activities():
    # Logic to create daily audit
    pass

# Schedule tasks
schedule.every().day.at("09:00").do(post_linkedin_update)
schedule.every().day.at("18:00").do(audit_daily_activities)

while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute
```

### 9. Run the Orchestrator

Start the main orchestrator to coordinate all services:
```bash
python orchestrator.py
```

## Basic Operations

### Processing Incoming Emails
1. Email MCP server detects new emails
2. Gmail watcher creates action files in Needs_Action/
3. Claude processes the action files
4. Responses are created and await approval if needed
5. Approved responses are sent via Email MCP server

### Creating LinkedIn Posts
1. System analyzes business activities in the vault
2. Generates content based on Company_Handbook.md
3. Creates approval request if needed
4. Posts to LinkedIn via Playwright MCP server

### Approval Workflow
1. For sensitive actions, system creates files in Pending_Approval/
2. User reviews and moves to Approved/ or Rejected/
3. System executes approved actions or cancels rejected ones

## Troubleshooting

### Gmail MCP Server Issues
- Check if app password is correctly configured
- Verify SMTP settings (smtp.gmail.com:587)
- Ensure the email.json configuration is valid

### LinkedIn Automation Issues
- Make sure LinkedIn credentials are still valid
- Check if Playwright MCP server is running
- Verify Claude can communicate with the MCP server

### Watcher Service Issues
- Ensure proper permissions for file system access
- Check that Claude Code has access to read/write vault files
- Verify network connectivity for API calls

## Next Steps

After successful setup:
1. Customize Company_Handbook.md with your specific rules
2. Fine-tune the approval requirements based on your needs
3. Adjust scheduling frequency for optimal performance
4. Monitor logs and adjust as needed