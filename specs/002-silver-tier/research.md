# Research Summary: Silver Tier - Functional Assistant

## MCP Server Integrations

### Email MCP Server
- **Decision**: Integrate with Shy2593666979/mcp-server-email for Gmail SMTP functionality
- **Rationale**: Provides secure email sending capabilities with attachment support and proper authentication (app password)
- **Configuration**: Will use SMTP settings for Gmail (smtp.gmail.com:587) with app password authentication
- **Integration**: Claude Code will communicate with this MCP server to send emails via send_email tool

### Playwright MCP Server
- **Decision**: Use @executeautomation/playwright-mcp-server for LinkedIn automation
- **Rationale**: Provides browser automation capabilities for LinkedIn without requiring official API access
- **Configuration**: Will be added via Claude MCP command: `claude mcp add --transport stdio playwright npx @executeautomation/playwright-mcp-server`
- **Integration**: Claude Code will use this to automate LinkedIn posting via browser interactions

## Attachment Handling

### Decision: Create AI_Employee/attachments folder
- **Rationale**: Centralized location for managing email attachments as specified in requirements
- **Location**: Directly under the AI_Employee vault directory
- **Security**: Only safe file types will be supported (PDF, DOCX, JPG, PNG, ZIP, etc.)

## Human-in-the-Loop Approval Workflow

### Sensitive Actions Identification
- **Decision**: Actions requiring approval include:
  - Emotional contexts (condolences, conflict resolution, sensitive negotiations)
  - Legal matters (contract signing, legal advice, regulatory filings)
  - Medical decisions (health-related actions)
  - Financial edge cases (unusual transactions, new recipients, large amounts)
  - Irreversible actions (anything that cannot be easily undone)
- **Rationale**: Protects against inappropriate autonomous actions while allowing routine tasks to proceed automatically

## Scheduling Implementation

### Decision: Cross-platform Python scheduler
- **Technology**: Using the `schedule` library (preferred) or APScheduler as backup
- **Rationale**: Provides cross-platform compatibility and integrates well with Python automation systems
- **Usage**: For automated LinkedIn posting, periodic audit tasks, and scheduled communications

## Retry Mechanism

### Decision: Exponential Backoff Strategy
- **Parameters**: Max 5 retries with intervals of 1s, 2s, 4s, 8s, 16s
- **Rationale**: Standard approach that prevents overwhelming servers while ensuring reliability
- **Application**: Network-dependent operations like email sending, LinkedIn posting, and API calls

## Architecture Patterns

### Watcher Services
- **Pattern**: Extends base_watcher.py with specific implementations for each channel
- **Coordination**: Multiple watchers will run concurrently, depositing action items in Needs_Action folder
- **Monitoring**: Continuous monitoring with configurable intervals to balance responsiveness and resource usage

### File-Based State Management
- **Pattern**: Uses Obsidian vault structure with dedicated folders for different states (Needs_Action, Pending_Approval, Done)
- **Rationale**: Maintains local-first architecture while enabling complex workflow management
- **Audit Trail**: All actions are recorded in files for transparency and accountability