# Quickstart Guide: Gold Tier - Autonomous Employee

**Date**: 2026-02-11
**Feature**: 003-gold-tier
**Purpose**: Step-by-step guide to set up and run Gold Tier autonomous employee features.

---

## 💰 Cost Overview

**IMPORTANT: All Gold Tier integrations are 100% FREE**

| Service | Cost | Rate Limits | Notes |
|---------|------|-------------|-------|
| **Facebook Graph API** | ✅ FREE | 200 calls/hour | No usage fees for page posting |
| **Instagram Graph API** | ✅ FREE | 25 posts/24 hours | Business account (free conversion) |
| **Twitter API** | ✅ FREE | 50 tweets/24 hours | Essential Access tier |
| **Odoo** | ✅ FREE | Unlimited | Self-hosted (Docker) |
| **Python Libraries** | ✅ FREE | N/A | Open source |

**Total Monthly Cost: $0**

All rate limits are sufficient for typical business needs (5-10 posts per day across platforms).

---

## Prerequisites

### System Requirements
- **OS**: Linux/WSL2 (tested on Ubuntu 20.04+)
- **Python**: 3.13+ (as required by project)
- **Odoo**: Community Edition v19.0+ (self-hosted or cloud)
- **Git**: For version control

### Existing Setup (from Bronze/Silver Tier)
- Working orchestrator with Gmail and WhatsApp watchers
- Obsidian vault at `AI_Employee/`
- Email MCP server configured
- Browser MCP server configured (for LinkedIn)
- `.env` file with Gmail credentials

---

## Step 1: Install Dependencies

### 1.1 Update Python Packages

```bash
# Navigate to project root
cd "/mnt/e/Q4 extension/Hackathon 2k25/Hackathon 0"

# Install new dependencies
pip install --upgrade pip
pip install xmlrpc facebook-sdk tweepy apscheduler
```

### 1.2 Verify Installations

```bash
python -c "import xmlrpc.client; print('Odoo client: OK')"
python -c "import facebook; print('Facebook SDK: OK')"
python -c "import tweepy; print('Tweepy: OK')"
python -c "from apscheduler.schedulers.background import BackgroundScheduler; print('APScheduler: OK')"
```

---

## Step 2: Set Up Odoo

### 2.1 Install Odoo (Docker - Recommended)

```bash
# Start PostgreSQL database
docker run -d \
  -e POSTGRES_USER=odoo \
  -e POSTGRES_PASSWORD=odoo_password \
  -e POSTGRES_DB=postgres \
  --name odoo_db \
  postgres:15

# Start Odoo
docker run -d \
  -p 8069:8069 \
  --name odoo \
  --link odoo_db:db \
  -e POSTGRES_USER=odoo \
  -e POSTGRES_PASSWORD=odoo_password \
  odoo:19.0
```

### 2.2 Initial Odoo Configuration

1. Open browser: http://localhost:8069
2. Create new database:
   - **Master Password**: admin (change in production!)
   - **Database Name**: my_company
   - **Email**: your-email@example.com
   - **Password**: admin (change in production!)
   - **Country**: Select your country
3. Install "Accounting" module from Apps menu
4. Configure chart of accounts

### 2.3 Get Odoo Credentials

Add to `.env`:
```bash
# Odoo Configuration
ODOO_URL=http://localhost:8069
ODOO_DB=my_company
ODOO_USERNAME=admin
ODOO_PASSWORD=admin
```

---

## Step 3: Set Up Social Media Integrations

### 3.1 Facebook Page Setup

#### Create Facebook App
1. Go to https://developers.facebook.com/apps/
2. Click "Create App" → Business → Continue
3. App Name: "AI Employee Social Manager"
4. Contact Email: your-email@example.com

#### Get Page Access Token
1. Add "Facebook Login" product to your app
2. Go to Graph API Explorer: https://developers.facebook.com/tools/explorer/
3. Select your app from dropdown
4. Click "Get Token" → "Get Page Access Token"
5. Select permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `read_insights`
6. Generate token and copy it

#### Exchange for Long-Lived Token
```bash
curl -i -X GET "https://graph.facebook.com/v19.0/oauth/access_token?\
grant_type=fb_exchange_token&\
client_id={your-app-id}&\
client_secret={your-app-secret}&\
fb_exchange_token={short-lived-token}"
```

Copy the `access_token` from response.

#### Get Page Access Token (Non-Expiring)
```bash
curl -i -X GET "https://graph.facebook.com/v19.0/me/accounts?\
access_token={long-lived-user-token}"
```

Find your page in the response and copy its `access_token` and `id`.

Add to `.env`:
```bash
# Facebook Configuration
FACEBOOK_PAGE_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FACEBOOK_PAGE_ID=123456789012345
```

---

### 3.2 Instagram Business Account Setup

#### Prerequisites
- Instagram account converted to Business or Creator account
- Facebook Page linked to Instagram account

#### Convert to Business Account
1. Open Instagram app
2. Settings → Account → Switch to Professional Account → Business
3. Complete business setup

#### Link to Facebook Page
1. Instagram app → Settings → Account → Linked Accounts → Facebook
2. Select Facebook Page to link

#### Get Instagram Account ID
```bash
curl -i -X GET "https://graph.facebook.com/v19.0/{page-id}?\
fields=instagram_business_account&\
access_token={page-token}"
```

Add to `.env`:
```bash
# Instagram Configuration (uses same Facebook Page Token)
INSTAGRAM_ACCOUNT_ID=17841400123456789
```

---

### 3.3 Twitter (X) Setup

#### Create Twitter Developer Account
1. Go to https://developer.twitter.com/
2. Sign up for developer account (may require approval)
3. Create new project: "AI Employee Social Manager"
4. Create app within project

#### Generate Keys and Tokens
1. In app settings → Keys and Tokens
2. Generate:
   - API Key and Secret
   - Access Token and Secret
   - Bearer Token (optional, for read-only)
3. Set app permissions to "Read and Write"

Add to `.env`:
```bash
# Twitter Configuration
TWITTER_API_KEY=xxxxxxxxxxxxxxxxxxxxx
TWITTER_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWITTER_ACCESS_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWITTER_ACCESS_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWITTER_BEARER_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Step 4: Configure MCP Servers

### 4.1 Update .mcp.json

Edit `.mcp.json` to add Gold Tier MCP servers:

```json
{
  "mcpServers": {
    "email": {
      "command": "python",
      "args": [".claude/mcp-servers/gmail-mcp/mcp_server_email.py"],
      "env": {
        "SENDER": "${GMAIL_ADDRESS}",
        "PASSWORD": "${GMAIL_APP_PASSWORD}"
      }
    },
    "browser": {
      "command": "python",
      "args": [".claude/mcp-servers/browser-mcp/mcp_browser_server.py"],
      "env": {
        "BROWSER_HEADLESS": "false"
      }
    },
    "odoo": {
      "command": "python",
      "args": [".claude/mcp-servers/odoo-mcp/mcp_server_odoo.py"],
      "env": {
        "ODOO_URL": "${ODOO_URL}",
        "ODOO_DB": "${ODOO_DB}",
        "ODOO_USERNAME": "${ODOO_USERNAME}",
        "ODOO_PASSWORD": "${ODOO_PASSWORD}"
      }
    },
    "facebook": {
      "command": "python",
      "args": [".claude/mcp-servers/facebook-mcp/mcp_server_facebook.py"],
      "env": {
        "FACEBOOK_PAGE_TOKEN": "${FACEBOOK_PAGE_TOKEN}",
        "FACEBOOK_PAGE_ID": "${FACEBOOK_PAGE_ID}"
      }
    },
    "instagram": {
      "command": "python",
      "args": [".claude/mcp-servers/instagram-mcp/mcp_server_instagram.py"],
      "env": {
        "FACEBOOK_PAGE_TOKEN": "${FACEBOOK_PAGE_TOKEN}",
        "INSTAGRAM_ACCOUNT_ID": "${INSTAGRAM_ACCOUNT_ID}"
      }
    },
    "twitter": {
      "command": "python",
      "args": [".claude/mcp-servers/twitter-mcp/mcp_server_twitter.py"],
      "env": {
        "TWITTER_API_KEY": "${TWITTER_API_KEY}",
        "TWITTER_API_SECRET": "${TWITTER_API_SECRET}",
        "TWITTER_ACCESS_TOKEN": "${TWITTER_ACCESS_TOKEN}",
        "TWITTER_ACCESS_SECRET": "${TWITTER_ACCESS_SECRET}",
        "TWITTER_BEARER_TOKEN": "${TWITTER_BEARER_TOKEN}"
      }
    },
    "context7": {
      "type": "http",
      "url": "https://mcp.context7.com/mcp",
      "headers": {
        "CONTEXT7_API_KEY": "ctx7sk-da97932b-86ef-492c-......"
      }
    },
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer ghp_EZGQCJxr8D9u3S8u11i......."
      }
    }
  }
}
```

---

## Step 5: Create Vault Directories

```bash
cd "AI_Employee"

# Create Gold Tier directories
mkdir -p Audits
mkdir -p CEO_Briefings

# Verify structure
ls -la
# Should see: Dashboard.md, Company_Handbook.md, Needs_Action/, Pending_Approval/,
#             Approved/, Completed/, Plans/, Audits/, CEO_Briefings/
```

---

## Step 6: Initialize Log Directory

```bash
# Create log directory (outside Obsidian for performance)
mkdir -p "/Vault/Logs"

# Set permissions
chmod 755 "/Vault/Logs"

# Verify
ls -la "/Vault/Logs"
```

---

## Step 7: Test MCP Servers

### 7.1 Test Odoo MCP

```bash
# Test Odoo connection
python .claude/mcp-servers/odoo-mcp/mcp_server_odoo.py --test

# Expected output: "Odoo connection successful. User: admin"
```

### 7.2 Test Facebook MCP

```bash
# Test Facebook connection
python .claude/mcp-servers/facebook-mcp/mcp_server_facebook.py --test

# Expected output: "Facebook connection successful. Page: [Your Page Name]"
```

### 7.3 Test Instagram MCP

```bash
# Test Instagram connection
python .claude/mcp-servers/instagram-mcp/mcp_server_instagram.py --test

# Expected output: "Instagram connection successful. Account: @[your-username]"
```

### 7.4 Test Twitter MCP

```bash
# Test Twitter connection
python .claude/mcp-servers/twitter-mcp/mcp_server_twitter.py --test

# Expected output: "Twitter connection successful. User: @[your-username]"
```

---

## Step 8: Run the Orchestrator

### 8.1 Start Orchestrator with Gold Tier

```bash
# Dry run mode (recommended for first run)
python orchestrator.py --tier gold --dry-run

# Real mode (after verifying dry run)
python orchestrator.py --tier gold
```

### 8.2 Verify Services Started

Check orchestrator logs:
```bash
tail -f orchestrator.log
```

Expected output:
```
[2026-02-11 10:00:00] INFO: Starting orchestrator (Gold Tier)
[2026-02-11 10:00:01] INFO: Gmail watcher started
[2026-02-11 10:00:02] INFO: WhatsApp watcher started
[2026-02-11 10:00:03] INFO: Filesystem watcher started
[2026-02-11 10:00:04] INFO: Weekly audit scheduler started (cron: Sun 22:00)
[2026-02-11 10:00:05] INFO: Health monitor started
[2026-02-11 10:00:06] INFO: Watchdog started
[2026-02-11 10:00:07] INFO: All services running. Press Ctrl+C to stop.
```

---

## Step 9: Test Gold Tier Features

### 9.1 Test Social Media Posting

Create approval file:
```bash
cat > AI_Employee/Pending_Approval/post_test_001.md << 'EOF'
---
type: social_media_post
platforms: [facebook, instagram, twitter]
timestamp: 2026-02-11T10:30:00Z
requires_approval: false
auto_approve_reason: "scheduled_post"
---

# Social Media Post Approval

**Content**:
Testing Gold Tier autonomous posting! 🚀

**Platforms**: Facebook, Instagram, Twitter

**Action**: Move to Approved/ folder to post, or delete to cancel.
EOF
```

Move to approved:
```bash
mv AI_Employee/Pending_Approval/post_test_001.md AI_Employee/Approved/
```

Check logs:
```bash
tail -f /Vault/Logs/$(date +%Y-%m-%d).json | jq 'select(.action == "social_media_post")'
```

### 9.2 Test Odoo Integration (Dry Run)

Create approval file:
```bash
cat > AI_Employee/Pending_Approval/invoice_test_001.md << 'EOF'
---
type: odoo_transaction
transaction_type: invoice
timestamp: 2026-02-11T10:30:00Z
requires_approval: true
approval_reason: "new_payee"
---

# Odoo Invoice Approval

**Customer**: Test Customer
**Amount**: $150.00
**Items**:
- Product Demo x 1 @ $150.00

**Action**: Move to Approved/ folder to create invoice (DRY RUN), or delete to cancel.
EOF
```

### 9.3 Test Weekly Audit (Manual Trigger)

```bash
# Manually trigger audit generation
python -c "
from utils.audit_generator import generate_weekly_audit
from datetime import datetime, timedelta

# Get last Sunday
today = datetime.now()
days_since_sunday = (today.weekday() + 1) % 7
last_sunday = today - timedelta(days=days_since_sunday)

result = generate_weekly_audit(last_sunday)
print(f'Audit generated: {result.file_path}')
"
```

Check output:
```bash
cat AI_Employee/Audits/$(date +%Y-%m-%d -d 'last sunday')-audit.md
```

---

## Step 10: Monitor System Health

### 10.1 View Real-Time Logs

```bash
# All actions
tail -f /Vault/Logs/$(date +%Y-%m-%d).json

# Social media posts only
tail -f /Vault/Logs/$(date +%Y-%m-%d).json | jq 'select(.action | contains("social_media"))'

# Errors only
tail -f /Vault/Logs/$(date +%Y-%m-%d).json | jq 'select(.result.status == "error")'
```

### 10.2 Check System Uptime

```bash
# View health monitor status
python -c "
from utils.health_monitor import HealthMonitor
monitor = HealthMonitor()
print(monitor.get_status())
"
```

### 10.3 Check Pending Approvals

```bash
ls -la AI_Employee/Pending_Approval/
```

---

## Troubleshooting

### Issue: MCP Server Won't Start

**Symptoms**: "Connection refused" or "Server not responding"

**Solutions**:
1. Check environment variables are set: `env | grep ODOO`
2. Verify credentials are correct
3. Check server logs: `journalctl -u odoo -f` (if systemd service)
4. Test direct connection: `curl http://localhost:8069`

### Issue: Social Media Post Fails

**Symptoms**: Error in logs about invalid token or permission denied

**Solutions**:
1. Check token expiration: Regenerate long-lived token if needed
2. Verify permissions: Ensure `pages_manage_posts` is granted
3. Check rate limits: Wait if limit exceeded
4. Validate image URL: Ensure publicly accessible

### Issue: Audit Generation Slow

**Symptoms**: Takes >10 minutes (violates SC-001)

**Solutions**:
1. Check log file sizes: `du -sh /Vault/Logs/*.json`
2. Optimize log parsing: Increase `workers` parameter
3. Reduce log retention: Delete logs older than 90 days
4. Check disk I/O: `iostat -x 1`

### Issue: Watchdog Keeps Restarting Service

**Symptoms**: "Watchdog restart" log entries frequent

**Solutions**:
1. Check service logs for crashes
2. Verify memory usage: `free -h`
3. Check for resource exhaustion: `top`
4. Review circuit breaker status

---

## Configuration Reference

### Environment Variables (.env)

```bash
# Gmail (from Bronze/Silver Tier)
GMAIL_ADDRESS=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password

# Odoo
ODOO_URL=http://localhost:8069
ODOO_DB=my_company
ODOO_USERNAME=admin
ODOO_PASSWORD=admin

# Facebook
FACEBOOK_PAGE_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FACEBOOK_PAGE_ID=123456789012345

# Instagram (uses Facebook Page Token)
INSTAGRAM_ACCOUNT_ID=17841400123456789

# Twitter
TWITTER_API_KEY=xxxxxxxxxxxxxxxxxxxxx
TWITTER_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWITTER_ACCESS_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWITTER_ACCESS_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWITTER_BEARER_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# System
LOG_LEVEL=INFO
DRY_RUN=false
```

### Orchestrator Command-Line Options

```bash
python orchestrator.py [OPTIONS]

Options:
  --tier gold             Enable Gold Tier features
  --dry-run               Run in simulation mode (no real actions)
  --log-level DEBUG       Set log verbosity (DEBUG, INFO, WARNING, ERROR)
  --config .env           Path to configuration file
  --no-scheduler          Disable weekly audit scheduler
  --help                  Show help message
```

---

## Next Steps

1. **Monitor for 1 week**: Let the system run and observe patterns
2. **Review CEO Briefing**: Check Monday Morning briefing quality
3. **Adjust approval thresholds**: Tune auto-approval rules based on comfort level
4. **Add custom Agent Skills**: Create reusable skills for common tasks
5. **Expand integrations**: Add more social platforms or Odoo modules

---

## Security Checklist

- [ ] `.env` file is in `.gitignore`
- [ ] All API tokens are long-lived and secure
- [ ] Odoo admin password changed from default
- [ ] File permissions set correctly (755 for dirs, 644 for files)
- [ ] Log files readable only by user
- [ ] MCP servers run with least privilege
- [ ] Approval workflows tested and understood
- [ ] Circuit breakers configured and tested

---

## Resources

- **Odoo Docs**: https://www.odoo.com/documentation/19.0/
- **Facebook Graph API**: https://developers.facebook.com/docs/graph-api/
- **Instagram Graph API**: https://developers.facebook.com/docs/instagram-api/
- **Twitter API v2**: https://developer.twitter.com/en/docs/twitter-api
- **APScheduler Docs**: https://apscheduler.readthedocs.io/

---

## Support

- **Issues**: Create issue in GitHub repo
- **Questions**: See CLAUDE.md for project instructions
- **Logs**: Always include relevant log excerpts when reporting issues

---

_Last Updated: 2026-02-11_
