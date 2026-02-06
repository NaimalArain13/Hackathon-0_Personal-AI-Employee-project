# AI Employee Dashboard

## Overview
This dashboard provides visibility into the AI employee's activities and status.

## Current Status
- **Email Monitoring**: Active
- **LinkedIn Automation**: {{LINKEDIN_STATUS}}
- **Active Watchers**: Gmail Watcher, WhatsApp Watcher (if enabled)
- **Last Check**: {{LAST_CHECK_TIME}}
- **Pending Actions**: {{PENDING_COUNT}}
- **Pending Approvals**: {{APPROVAL_COUNT}}
- **Today's Processed Items**: {{PROCESSED_TODAY}}
- **Today's LinkedIn Posts**: {{LINKEDIN_POSTS_TODAY}}

## Activity Log
| Time | Activity | Details |
|------|----------|---------|
| {{TIME}} | System Started | AI Employee system initialized |
| | | |

## Action Items
- Check `/Needs_Action` folder for pending tasks
- Review `/Pending_Approval` folder for items requiring human approval
- Monitor `/Plans` folder for generated task plans
- Review processed items in `/Done` folder
- Monitor `/Inbox` for incoming items
- Check `/Approved` and `/Rejected` folders for processed approvals

## Rules Reference
See `Company_Handbook.md` for processing rules and guidelines.

## Performance Metrics
- Email Response Time: {{EMAIL_RESPONSE_TIME}}
- LinkedIn Post Success Rate: {{LINKEDIN_SUCCESS_RATE}}
- Approval Processing Rate: {{APPROVAL_RATE}}
- System Uptime: {{UPTIME}}