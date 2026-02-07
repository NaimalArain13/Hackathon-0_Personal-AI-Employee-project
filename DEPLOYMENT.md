# Deployment Guide: Silver Tier Personal AI Employee

This document provides configuration and setup procedures for deploying the Silver Tier Personal AI Employee system in a production environment.

## Prerequisites

### System Requirements
- Python 3.13+ (as required by the project)
- Linux, macOS, or Windows with WSL2
- At least 2GB RAM (recommended 4GB+ for optimal performance)
- At least 500MB free disk space
- Internet connectivity for external services (Gmail, LinkedIn, etc.)

### Required Software
- Python 3.13+
- Pip package manager
- Git (for version control)

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Linux/macOS
# OR
.venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Configuration

### 1. Environment Variables Setup

Copy the example environment file:
```bash
cp .env.example .env
```

Then edit `.env` with your specific configuration values:

```env
# Gmail API Configuration
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
GMAIL_CREDENTIALS_PATH=./gmail-token.pickle

# LinkedIn/MCP Server Configuration
LINKEDIN_USERNAME=your_linkedin_username
LINKEDIN_PASSWORD=your_linkedin_password

# Vault Configuration
VAULT_PATH=/path/to/your/obsidian/vault
WATCH_FOLDER_PATH=./watch_folder
CHECK_INTERVAL=60

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=./logs/ai_employee.log

# Development Mode
DEV_MODE=false
DRY_RUN=false
MAX_RETRY_ATTEMPTS=5
INITIAL_RETRY_DELAY=1

# Scheduling Configuration
SCHEDULE_POST_INTERVAL=3600
WHATSAPP_ENABLED=false
```

### 2. MCP Server Configuration

The system uses Model Context Protocol (MCP) servers for external services. Update `.mcp.json`:

```json
{
  "mcpServers": {
    "context7": {
      "type": "http",
      "url": "https://mcp.context7.com/mcp",
      "headers": {
        "CONTEXT7_API_KEY": "your_context7_api_key"
      }
    },
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer your_github_token"
      }
    },
    "email": {
      "command": "python",
      "args": [
        "/path/to/your/project/.claude/mcp-servers/gmail-mcp/mcp_server_email.py"
      ],
      "env": {
        "SENDER": "${GMAIL_ADDRESS}",
        "PASSWORD": "${GMAIL_APP_PASSWORD}"
      }
    },
    "browser": {
      "command": "python",
      "args": [
        "/path/to/your/project/.claude/mcp-servers/browser-mcp/mcp_browser_server.py"
      ],
      "env": {
        "BROWSER_HEADLESS": "false"
      }
    }
  }
}
```

### 3. Email Configuration

Create/update `email.json` with SMTP server configurations:

```json
[
  {
    "domain": "@gmail.com",
    "server": "smtp.gmail.com",
    "port": 587
  },
  {
    "domain": "@outlook.com",
    "server": "smtp.office365.com",
    "port": 587
  },
  {
    "domain": "@yahoo.com",
    "server": "smtp.mail.yahoo.com",
    "port": 587
  }
]
```

## Directory Structure Setup

The system expects the following directory structure:

```
AI_Employee_Vault/
├── Inbox/
├── Needs_Action/
├── Done/
├── Pending_Approval/
├── Approved/
├── Rejected/
├── Plans/
├── attachments/
└── Logs/
```

Create this structure in your Obsidian vault directory.

## Service Authorization

### Gmail API Setup
1. Go to Google Cloud Console
2. Create a new project or select existing one
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download credentials JSON and update environment variables
6. Run the Gmail watcher once to complete OAuth flow

### LinkedIn Setup
1. Create a LinkedIn account for the AI employee
2. Update the LinkedIn credentials in environment variables
3. Note: LinkedIn has strict anti-bot policies, use responsibly

## Running the System

### 1. Manual Start
```bash
python orchestrator.py --config .env --verbose
```

### 2. Using Process Manager (PM2)
```bash
npm install -g pm2
pm2 start orchestrator.py --name ai-employee --interpreter python -- --config .env
pm2 startup
pm2 save
```

### 3. Using Systemd (Linux)
Create `/etc/systemd/system/ai-employee.service`:

```ini
[Unit]
Description=Personal AI Employee
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/your/project
Environment=PATH=/path/to/your/venv/bin
ExecStart=/path/to/your/venv/bin/python orchestrator.py --config .env
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-employee
sudo systemctl start ai-employee
```

## Monitoring and Maintenance

### Health Checks
The system includes a health monitor that tracks:
- Uptime statistics
- Resource usage (CPU, memory, disk)
- Service availability
- Error rates

Access health information through the HealthMonitor utility.

### Log Management
- Logs are stored in the configured log directory
- Rotate logs daily to prevent disk space issues
- Monitor logs for errors and warnings

### Backup Procedures
Regularly backup:
- Obsidian vault directory
- Configuration files (.env, .mcp.json, email.json)
- MCP server configurations

## Security Considerations

### Credential Security
- Store credentials in environment variables, not in code
- Use app passwords for Gmail instead of account passwords
- Regularly rotate credentials
- Restrict file permissions on config files

### Rate Limiting
- The system implements exponential backoff for API calls
- Respect service rate limits to avoid being blocked
- Monitor for rate limit errors in logs

### Data Privacy
- The system processes personal data; ensure compliance with privacy regulations
- Encrypt sensitive data in transit and at rest
- Regular security audits recommended

## Troubleshooting

### Common Issues
1. **Authentication failures**: Check credentials and OAuth tokens
2. **Rate limiting**: Implement backoff strategies and respect limits
3. **Network timeouts**: Adjust timeout settings in configuration
4. **File permission errors**: Verify proper file permissions

### Debugging
- Enable verbose logging for detailed diagnostics
- Check MCP server logs for external service issues
- Monitor system resources for performance issues

## Updates and Maintenance

### Updating Code
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### Updating Dependencies
Regularly update dependencies to patch security vulnerabilities:
```bash
pip list --outdated
pip install --upgrade <package-name>
```

## Production Checklist

- [ ] Environment variables configured securely
- [ ] MCP servers properly configured and tested
- [ ] Logging configured with appropriate retention
- [ ] Backup procedures established
- [ ] Monitoring and alerting configured
- [ ] Security hardening applied
- [ ] Rate limits respected
- [ ] Credentials rotated regularly
- [ ] Health checks functioning
- [ ] Rollback procedures documented

## Support

For support issues, check:
- System logs for error messages
- MCP server status
- Network connectivity to external services
- Resource availability (CPU, memory, disk space)