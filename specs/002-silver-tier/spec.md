# Feature Specification: Silver Tier - Functional Assistant

**Feature Branch**: `002-silver-tier`
**Created**: 2026-02-05
**Status**: Draft
**Input**: User description: "Create comprehensive specification for Silver Tier. make sure to mention to create new branch "002-silver-tier" in the specification and all those which we have discuss in previous messages"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Multi-Channel Email Management (Priority: P1)

A business owner receives customer inquiries via multiple channels (Gmail, WhatsApp) and needs to respond professionally while maintaining proper email communication. The AI assistant must be able to monitor Gmail, create appropriate responses, and send them via secure email functionality using the Email MCP server.

**Why this priority**: This is fundamental to Silver Tier requirements as it expands on Bronze Tier functionality and implements the required Email MCP Server integration for Gmail.

**Independent Test**: The system can monitor Gmail for new messages, generate appropriate responses in the Obsidian vault, and send emails using the MCP server when approved by the user.

**Acceptance Scenarios**:

1. **Given** user has configured Gmail MCP server with proper SMTP settings and app password, **When** new email arrives in monitored Gmail account, **Then** AI assistant creates an action file in Needs_Action folder and can send response emails via the MCP server
2. **Given** AI assistant has a response ready for sending, **When** user approves the response, **Then** email is sent via the Gmail MCP server using proper SMTP authentication (smtp.gmail.com:587)

---

### User Story 2 - LinkedIn Business Automation (Priority: P1)

A business owner wants to automatically generate and post professional content on LinkedIn to generate sales leads and maintain their business presence without manual daily intervention.

**Why this priority**: This is a key requirement of Silver Tier to automatically post on LinkedIn about business to generate sales.

**Independent Test**: The system can generate appropriate business content and schedule or post it to LinkedIn using Playwright browser automation according to predefined parameters.

**Acceptance Scenarios**:

1. **Given** LinkedIn credentials are properly configured and Playwright MCP server is running, **When** business content is ready in the Obsidian vault, **Then** AI assistant can post the content to LinkedIn via browser automation
2. **Given** business goals and recent achievements are documented in the vault, **When** scheduling conditions are met, **Then** AI creates appropriate LinkedIn posts that align with business objectives using Playwright MCP server

---

### User Story 3 - Multi-Watcher Coordination (Priority: P1)

A business owner uses multiple communication channels and needs the AI assistant to coordinate between different watchers (Gmail, WhatsApp, LinkedIn) to maintain consistent communication and task management.

**Why this priority**: This fulfills the Silver Tier requirement of having two or more watcher scripts running simultaneously.

**Independent Test**: Multiple watcher services run concurrently, monitor their respective channels, and create coordinated action items in the central Obsidian vault.

**Acceptance Scenarios**:

1. **Given** Gmail and WhatsApp watchers are running, **When** messages arrive on both channels simultaneously, **Then** both are properly processed and documented in the vault without conflict
2. **Given** multiple action items exist across different channels, **When** AI processes the queue, **Then** it maintains context and consistency across all communication channels

---

### User Story 4 - Human-in-the-Loop Approval Workflow (Priority: P2)

A business owner needs to maintain control over sensitive actions including emotional contexts, legal matters, medical decisions, financial edge cases, and irreversible actions while allowing routine tasks to be automated.

**Why this priority**: This is essential for security and compliance as specified in Silver Tier requirements.

**Independent Test**: The system creates approval requests for sensitive actions and waits for human approval before proceeding.

**Acceptance Scenarios**:

1. **Given** a sensitive action is required (emotional contexts, legal matters, medical decisions, unusual financial transactions, new recipients, large amounts, or irreversible actions), **When** AI detects the sensitivity, **Then** it creates an approval file in Pending_Approval folder instead of executing immediately
2. **Given** approval file exists in Pending_Approval folder, **When** user moves file to Approved folder, **Then** action is executed by the appropriate MCP server

---

### User Story 5 - Automated Planning and Documentation (Priority: P2)

A business owner needs the AI to generate structured plan documents based on incoming tasks and requirements to maintain visibility into ongoing activities.

**Why this priority**: This fulfills the Silver Tier requirement of Claude reasoning loops that create Plan.md files.

**Independent Test**: The system analyzes incoming requests and generates structured Plan.md files with clear steps and status tracking.

**Acceptance Scenarios**:

1. **Given** a complex multi-step task is identified, **When** AI processes the request, **Then** it creates a Plan.md file with step-by-step breakdown and tracking checkboxes

---

### User Story 6 - MCP Server Integration (Priority: P1)

A business owner needs to integrate the Email MCP server with Claude Code to enable secure email sending capabilities with proper authentication and attachment support.

**Why this priority**: This is required to fulfill the Silver Tier requirement of having one working MCP server for external action (sending emails).

**Independent Test**: The Claude Code can successfully communicate with the Email MCP server to send emails with attachments.

**Acceptance Scenarios**:

1. **Given** Email MCP server is configured and running, **When** Claude requests to send an email, **Then** the MCP server processes the request and sends the email via SMTP
2. **Given** email with attachments needs to be sent, **When** Claude calls the send_email tool, **Then** the email is sent with all specified attachments

---

### Edge Cases

- What happens when Gmail credentials expire or become invalid?
- How does the system handle failed email sending attempts due to network issues?
- What occurs when multiple watchers detect the same business event across different channels?
- How does the system handle rate limits from email or social media APIs?
- What happens when the Obsidian vault becomes inaccessible while watchers are running?
- How does the system handle invalid email addresses or delivery failures?
- What occurs when the attachment directory becomes full or inaccessible?
- How does the system handle retries for failed operations using exponential backoff?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support Gmail MCP server integration with proper SMTP configuration using smtp.gmail.com:587 and app password authentication
- **FR-002**: System MUST monitor Gmail for new messages and create action files in the Needs_Action folder
- **FR-003**: System MUST support sending emails through the Email MCP server with subject, body, multiple recipients, and attachments
- **FR-004**: System MUST automatically post business-related content to LinkedIn using Playwright browser automation according to scheduling parameters
- **FR-005**: System MUST operate at least two simultaneous watcher services (Gmail and one other channel like WhatsApp or file system)
- **FR-006**: System MUST create Plan.md files when processing complex multi-step tasks with structured steps and progress tracking
- **FR-007**: System MUST implement human-in-the-loop approval workflow for sensitive actions including emotional contexts, legal matters, medical decisions, financial edge cases (unusual transactions, new recipients, large amounts), and irreversible actions by creating files in Pending_Approval folder
- **FR-008**: System MUST support basic scheduling functionality for automated operations using a cross-platform Python scheduler library (such as Schedule or APScheduler)
- **FR-009**: System MUST implement proper error handling and retry mechanisms for network-dependent operations using exponential backoff with max 5 retries, starting at 1 second and doubling each time (1s, 2s, 4s, 8s, 16s)
- **FR-010**: System MUST maintain proper security practices by storing credentials securely and limiting attachment types to safe formats (documents, images, archives)
- **FR-011**: System MUST create an attachments folder at AI_Employee/attachments for managing email attachments
- **FR-012**: System MUST configure Claude Code with proper MCP server settings pointing to the email MCP server module
- **FR-013**: System MUST implement the Ralph Wiggum loop pattern to ensure Claude continues working until tasks are complete
- **FR-014**: System MUST log all email sending activities for audit purposes
- **FR-015**: System MUST configure Playwright MCP server for LinkedIn automation using either 'claude mcp add --transport stdio playwright npx @executeautomation/playwright-mcp-server' or the appropriate MCP configuration

### Key Entities

- **Email Message**: Represents an incoming or outgoing email with metadata (sender, subject, body, attachments) processed by the Gmail watcher
- **LinkedIn Post**: Represents a social media post to be published on LinkedIn with content, timing, and approval status
- **Approval Request**: Represents a pending action that requires human approval before execution, stored in the Pending_Approval folder
- **Plan Document**: Structured markdown file containing step-by-step breakdown of tasks with progress tracking
- **Watcher Service**: Background process that monitors specific channels (Gmail, WhatsApp, etc.) and creates action files in the Obsidian vault
- **MCP Server Configuration**: Settings that allow Claude Code to communicate with external services like email servers
- **Attachment File**: Files that can be included with outgoing emails, stored in the designated attachments folder

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System successfully monitors Gmail and creates action files within 2 minutes of message arrival
- **SC-002**: Email MCP server successfully sends at least 95% of approved outbound emails within 30 seconds of approval
- **SC-003**: At least 2 watcher services run concurrently without interfering with each other's operations
- **SC-004**: LinkedIn posting functionality creates and schedules posts with 99% reliability during business hours
- **SC-005**: Human-in-the-loop approval system correctly identifies and routes at least 90% of sensitive actions for approval
- **SC-006**: Plan.md files are generated with structured tasks and progress indicators for complex requests
- **SC-007**: System maintains stable operation for 24+ hours without manual intervention or crashes
- **SC-008**: Email MCP server supports sending emails with attachments of common file types (PDF, DOCX, JPG, PNG, ZIP)
- **SC-009**: At least 80% of routine business communications are handled automatically without human intervention
- **SC-010**: All email communications maintain professional tone and follow company branding guidelines as specified in Company_Handbook.md

## Clarifications

### Session 2026-02-05

- Q: What method should be used for LinkedIn automation (Direct API vs Browser Automation)? → A: Browser Automation using Playwright MCP server
- Q: Where exactly should the attachments folder be created within the AI_Employee directory? → A: AI_Employee/attachments
- Q: Which specific types of actions should require human approval in the approval workflow? → A: Actions involving emotional contexts, legal matters, medical decisions, financial edge cases (unusual transactions, new recipients, large amounts), and irreversible actions
- Q: Which scheduling method should be implemented for cross-platform compatibility? → A: Cross-platform Python scheduler library (such as Schedule or APScheduler)
- Q: What should be the retry strategy for failed operations? → A: Exponential backoff with max 5 retries, starting at 1 sec and doubling each time (1s, 2s, 4s, 8s, 16s)
