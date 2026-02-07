# Data Model: Silver Tier - Functional Assistant

## Core Entities

### Email Message
- **Attributes**:
  - id: Unique identifier for the email
  - sender: Email address of the sender
  - subject: Subject line of the email
  - body: Content of the email
  - received_date: Timestamp when email was received
  - priority: Priority level (high, medium, low)
  - status: Current status (pending, processed, responded)
  - attachments: List of attached file names

- **Relationships**:
  - Associated with zero or more attachment files
  - May generate zero or more action files in Needs_Action folder

### LinkedIn Post
- **Attributes**:
  - id: Unique identifier for the post
  - content: Text content of the post
  - scheduled_time: Time when the post should be published
  - status: Current status (draft, scheduled, posted, failed)
  - approval_status: Approval status (pending, approved, rejected)
  - linkedin_account: The LinkedIn account used for posting
  - engagement_metrics: Metrics after posting (likes, shares, comments)

- **Relationships**:
  - May be created from business goals or achievements documented in vault
  - Links to approval request if human approval required

### Approval Request
- **Attributes**:
  - id: Unique identifier for the approval request
  - action_type: Type of action requiring approval (email_send, payment, social_post, etc.)
  - request_data: JSON data describing the action to be approved
  - created_date: Timestamp when request was created
  - expires_date: Timestamp when approval request expires
  - status: Current status (pending, approved, rejected, expired)

- **Relationships**:
  - Associated with the specific action that requires approval
  - Links to user who will approve/reject the request

### Plan Document
- **Attributes**:
  - id: Unique identifier for the plan
  - title: Title of the plan
  - created_date: Timestamp when plan was created
  - updated_date: Timestamp when plan was last updated
  - status: Overall status (pending, in_progress, completed)
  - tasks: List of individual tasks with status (completed, in_progress, pending)

- **Relationships**:
  - Generated from complex multi-step tasks
  - May contain references to other related entities (emails, posts, etc.)

### Watcher Service
- **Attributes**:
  - id: Unique identifier for the watcher
  - name: Name of the watcher (gmail, whatsapp, linkedin, etc.)
  - active: Boolean indicating if the watcher is currently running
  - last_check: Timestamp of the last check performed
  - check_interval: Interval in seconds between checks
  - status: Current status (running, paused, error)

- **Relationships**:
  - Creates action files in Needs_Action folder
  - Monitors specific communication channel or system

### MCP Server Configuration
- **Attributes**:
  - id: Unique identifier for the configuration
  - server_name: Name of the MCP server (email, playwright, etc.)
  - command: Command to start the server
  - args: Arguments for the server command
  - environment_vars: Environment variables for authentication
  - status: Current status (configured, running, error)

- **Relationships**:
  - Connected to Claude Code for external action capabilities
  - May have associated credentials for external services

### Attachment File
- **Attributes**:
  - filename: Name of the file
  - path: Path to the file in the attachments folder
  - size: Size of the file in bytes
  - mime_type: MIME type of the file
  - upload_date: Date when file was added
  - allowed: Boolean indicating if the file type is allowed

- **Relationships**:
  - Associated with one or more email messages
  - Stored in the AI_Employee/attachments folder

## State Transitions

### Email Message States
- `received` → `needs_processing` → `processing` → `action_created` → `response_sent` → `completed`
- Alternative: `received` → `needs_approval` → `approval_pending` → `approved` → `sent`

### LinkedIn Post States
- `draft` → `needs_approval` → `approval_pending` → `scheduled` → `posted` → `completed`
- Alternative: `draft` → `auto_approved` → `posted` → `completed`

### Approval Request States
- `created` → `pending` → `approved/rejected` → `processed`
- Alternative: `created` → `pending` → `expired` → `closed`

### Plan Document States
- `created` → `in_progress` → `completed`
- Tasks within the plan have their own completion status

## Validation Rules

1. **Email Messages**: Must have a valid sender email address and non-empty subject/body
2. **LinkedIn Posts**: Content must not exceed LinkedIn's character limits
3. **Approval Requests**: Must have a defined expiration date (max 24 hours)
4. **Attachments**: Must be of allowed file types (PDF, DOCX, XLSX, PPTX, JPG, JPEG, PNG, GIF, BMP, ZIP, RAR, 7Z, TXT, CSV)
5. **Plan Documents**: Must have at least one task defined
6. **Watcher Services**: Check interval must be between 15 seconds and 3600 seconds (1 hour)
7. **MCP Configurations**: Must have valid command and required environment variables