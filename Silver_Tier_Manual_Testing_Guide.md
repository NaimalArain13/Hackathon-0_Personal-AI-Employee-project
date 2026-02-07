# Silver Tier Manual Testing Guide

Based on the Silver Tier implementation summary, I'll create a comprehensive manual testing guide to validate all features in your actual vault environment.

## Pre-Testing Setup

### Environment Configuration
1. Verify all required environment variables are set in your `.env` file:
   - Gmail credentials (OAuth2 setup)
   - LinkedIn credentials (if using browser automation)
   - WhatsApp credentials
   - SMTP settings in `email.json`

2. Ensure your actual vault directory structure exists:
   ```
   AI_Employee/
   ├── Inbox/
   ├── Needs_Action/
   ├── Pending_Approval/
   ├── Done/
   ├── Plans/
   ├── Approved/
   └── attachments/
   ```

3. Start the orchestrator and MCP servers before testing.

## Test Cases

### 1. Email Management (Gmail Watcher)

#### Test 1.1: Receiving and Processing Emails
- **Objective**: Verify Gmail watcher detects new emails and creates action files
- **Steps**:
  1. Send a test email to your monitored Gmail account
  2. Wait up to 2 minutes for processing
  3. Check `AI_Employee/Needs_Action/` for new email action files
  4. Verify action files are properly structured with email content and action items
- **Expected Result**: Email detected within 2 minutes, appropriate action files created in Needs_Action folder

#### Test 1.2: Sending Emails with Attachments
- **Objective**: Test email MCP server functionality
- **Steps**:
  1. Open Claude Code's MCP tool panel or use the Claude interface
  2. Look for the `send_email` tool in the available tools list
  3. Prepare test data for the tool:
     - `to`: Recipient email address (string or list of strings)
     - `subject`: Email subject line
     - `body`: Email body content
     - `cc`: CC recipients (optional, string or list of strings)
     - `bcc`: BCC recipients (optional, string or list of strings)
     - `attachments`: List of file paths for attachments (optional)
  4. Example tool call:
     ```json
     {
       "to": ["recipient@example.com"],
       "subject": "Test Email with Attachments",
       "body": "This is a test email sent using the send_email tool.",
       "attachments": ["/path/to/file1.pdf", "/path/to/file2.docx"]
     }
     ```
  5. Execute the `send_email` tool call
  6. Verify email is sent successfully (check Claude's response for success/failure)
  7. Check recipient inbox for delivery
- **Expected Result**: 95% of emails delivered within 30 seconds, attachments preserved

#### Test 1.3: Attachment Handling
- **Objective**: Validate attachment support and security
- **Steps**:
  1. Send emails with various attachment types to your Gmail
  2. Use the `search_attachments` tool to locate specific attachments:
     - Look for the `search_attachments` tool in the available tools
     - Prepare parameters:
       - `pattern`: Search pattern for attachments (e.g., "*.pdf", "report*")
       - `date_range`: Optional date range for search
  3. Example tool call:
     ```json
     {
       "pattern": "*.pdf"
     }
     ```
  4. Execute the tool and verify results
  5. Verify unsupported file types are rejected by attempting to send malicious file types
- **Expected Result**: Common attachment types supported, malicious types rejected

### 2. LinkedIn Business Automation

#### Test 2.1: Direct LinkedIn Post Creation
- **Objective**: Create a LinkedIn post using browser automation
- **Steps**:
  1. Prepare a post content (text and optional image path)
  2. Look for LinkedIn posting tools in the MCP interface
  3. Execute the LinkedIn post creation tool with your content
  4. Monitor the Claude interface for progress updates
  5. Log in to your actual LinkedIn account and verify the post appeared
- **Expected Result**: Post created successfully, anti-bot measures handled

#### Test 2.2: LinkedIn Post Scheduling
- **Objective**: Schedule a LinkedIn post for future publication
- **Steps**:
  1. Create a post with a future scheduled time
  2. Use the LinkedIn scheduling tool (look for scheduling functions in MCP)
  3. Provide post content and scheduled datetime
  4. Monitor for actual posting at scheduled time
  5. Check LinkedIn account for successful publication
- **Expected Result**: Posts published at scheduled times with 99% reliability

#### Test 2.3: Rate Limiting and Anti-Detection
- **Objective**: Test system handles LinkedIn's rate limits
- **Steps**:
  1. Attempt to create multiple posts rapidly using the LinkedIn tools
  2. Monitor for appropriate delays being implemented by the system
  3. Check that your LinkedIn account remains in good standing
  4. Observe Claude's behavior for rate-limiting indicators
- **Expected Result**: Rate limits respected, no account restrictions

### 3. Multi-Watcher Coordination

#### Test 3.1: Concurrent Gmail and WhatsApp Watchers
- **Objective**: Run both watchers simultaneously without conflicts
- **Steps**:
  1. Verify the orchestrator is configured to start both watchers
  2. Start the orchestrator (this should start both watchers)
  3. Send test messages/emails to both channels simultaneously
  4. Monitor Claude's interface and logs for any error messages
  5. Check the AI_Employee vault directories for proper file handling
- **Expected Result**: Both watchers operate independently without interference

#### Test 3.2: Three-Watcher Operation
- **Objective**: Run all three watchers concurrently
- **Steps**:
  1. Ensure orchestrator is configured for all three watchers (Gmail, WhatsApp, LinkedIn scheduler)
  2. Start the orchestrator
  3. Simulate activity across all channels
  4. Monitor resource usage via system tools or Claude's resource indicators
  5. Check for performance degradation
- **Expected Result**: All watchers run concurrently, resource usage optimized

#### Test 3.3: Conflict Resolution
- **Objective**: Handle duplicate action items across channels
- **Steps**:
  1. Create identical requests in both Gmail and WhatsApp simultaneously
  2. Monitor the system to see if conflict resolver activates
  3. Check the AI_Employee directories to verify only one action is processed
  4. Look for conflict resolution logs in the system output
- **Expected Result**: Duplicate actions detected and resolved appropriately

### 4. Human-in-the-Loop Approval Workflow

#### Test 4.1: Sensitive Content Detection
- **Objective**: Verify system identifies content requiring approval
- **Steps**:
  1. Send an email with sensitive content (financial, legal, personal data, etc.)
  2. Monitor the system to see if sensitive content detector flags it
  3. Check `AI_Employee/Pending_Approval/` directory for approval file creation
  4. Verify the approval file contains proper metadata
- **Expected Result**: 90% of sensitive content routed for approval

#### Test 4.2: Approval Request Creation
- **Objective**: Test creation and format of approval requests
- **Steps**:
  1. Trigger sensitive action by sending sensitive content
  2. Verify approval file created with proper metadata in `Pending_Approval/`
  3. Open the created file and check it contains all necessary information
  4. Verify the file follows the expected approval request format
- **Expected Result**: Well-formatted approval requests with complete context

#### Test 4.3: Approval Monitoring and Execution
- **Objective**: Test approval workflow from request to execution
- **Steps**:
  1. Locate an approval request file in `Pending_Approval/`
  2. Manually update the file to indicate approval (follow the format in Company_Handbook.md)
  3. Save the file and monitor the system
  4. Verify system detects approval and executes the associated action
  5. Try creating a request and rejecting it to ensure it's not executed
- **Expected Result**: Approved actions executed, rejected actions skipped

#### Test 4.4: Approval Expiration
- **Objective**: Verify 24-hour expiration for approval requests
- **Steps**:
  1. Create an approval request
  2. Do not approve the request within 24 hours
  3. Monitor the system to see if it expires the request
  4. Check that expired requests are not executed when later approved
- **Expected Result**: Requests expire after 24 hours

### 5. Automated Planning and Documentation

#### Test 5.1: Plan.md Generation
- **Objective**: Create structured plans for complex tasks
- **Steps**:
  1. Identify a complex multi-step task that would trigger plan generation
  2. Trigger the plan generation (this might happen automatically or via a specific command)
  3. Check `AI_Employee/Plans/` directory for Plan.md file creation
  4. Verify the file has proper structure with tasks as checkboxes
  5. Check that tasks are broken down into actionable items
- **Expected Result**: Structured plans with actionable tasks and progress tracking

#### Test 5.2: Plan Status Updates
- **Objective**: Update plan status as tasks are completed
- **Steps**:
  1. Execute tasks from a generated plan
  2. Monitor the system to see if plan status updates automatically
  3. Check the Plan.md file to see if progress indicators reflect actual completion
  4. Verify completed tasks are marked as done
- **Expected Result**: Real-time plan status updates

#### Test 5.3: Entity Linking
- **Objective**: Link plan items to related entities
- **Steps**:
  1. Generate a plan that references emails, LinkedIn posts, or other entities
  2. Check the generated Plan.md for proper cross-references
  3. Verify links point to the correct related files
  4. Test clicking/verifying the links if possible
- **Expected Result**: Proper cross-references maintained

### 6. System Reliability Features

#### Test 6.1: Retry Mechanism
- **Objective**: Verify exponential backoff works correctly
- **Steps**:
  1. Introduce temporary network failures (temporarily disconnect internet or mock failures)
  2. Observe the system logs to see if it retries with increasing intervals
  3. Look for retry patterns: 1s, 2s, 4s, 8s, 16s intervals
  4. Restore connectivity and verify operations eventually succeed
- **Expected Result**: Operations recover from transient failures

#### Test 6.2: Resource Usage Monitoring
- **Objective**: Monitor system performance during operation
- **Steps**:
  1. Run watchers continuously for an extended period
  2. Use system monitoring tools (htop, task manager) to monitor CPU and memory
  3. Check Claude's resource indicators if available
  4. Record baseline and peak usage
- **Expected Result**: Stable resource usage under normal operating conditions

#### Test 6.3: 24+ Hour Uptime Test
- **Objective**: Validate system stability over extended periods
- **Steps**:
  1. Start all watchers and leave running for 24+ hours
  2. Periodically check Claude interface and system logs
  3. Verify all functions continue to work properly
  4. Monitor for memory leaks or performance degradation
  5. Check logs for any errors that occurred during the period
- **Expected Result**: Stable operation for 24+ hours without manual intervention

### 7. End-to-End Flow Testing

#### Test 7.1: Complete Email-to-Action Flow
- **Objective**: Test complete workflow from email receipt to action completion
- **Steps**:
  1. Send an email requesting a LinkedIn post
  2. Monitor to verify email is detected by Gmail watcher
  3. Check that appropriate action file is created in the correct directory
  4. Verify LinkedIn post is scheduled/generated by checking logs
  5. Log into LinkedIn to confirm post appears on your feed
- **Expected Result**: Seamless flow from email to completed action

#### Test 7.2: Approval-Required End-to-End Flow
- **Objective**: Test workflow with human approval step
- **Steps**:
  1. Send sensitive content requiring approval via email
  2. Verify it goes through approval process (appears in Pending_Approval)
  3. Manually approve the request by updating the file
  4. Monitor the system to confirm action is executed after approval
- **Expected Result**: Proper approval workflow followed, action executed when approved

#### Test 7.3: Multi-Channel Coordination
- **Objective**: Test coordination between different communication channels
- **Steps**:
  1. Receive related requests via email and WhatsApp simultaneously
  2. Monitor the system to verify conflict resolution works
  3. Check that appropriate actions are taken without duplication
  4. Verify only one response is generated for the same request across channels
- **Expected Result**: Coordinated response across channels without duplication

## Monitoring and Validation

### Performance Metrics to Track
- Email processing time (should be <2 minutes)
- LinkedIn post success rate (should be >99%)
- System uptime percentage
- Resource utilization (CPU, memory)
- Error rates and recovery times

### Logging Verification
- Check that comprehensive logs are created for all operations
- Verify error conditions are properly logged
- Confirm audit trail for all actions taken

## Post-Testing Actions

1. **Document Issues**: Record any problems encountered during testing
2. **Performance Analysis**: Review resource usage and optimize if needed
3. **Security Review**: Verify no credentials were exposed during testing
4. **Cleanup**: Remove test data and reset any test states

## Success Criteria

- [ ] 80% of routine communications handled automatically
- [ ] All communications maintain professional tone per Company_Handbook.md
- [ ] System operates stably for 24+ hours
- [ ] At least 2 watcher services run concurrently without interference
- [ ] Email MCP server sends 95% of approved emails within 30 seconds
- [ ] LinkedIn posts created with 99% reliability during business hours
- [ ] Gmail monitoring creates action files within 2 minutes
- [ ] Approval system routes 90% of sensitive actions for approval
- [ ] Plan.md files generated with structured tasks and progress indicators
- [ ] Email MCP server supports common attachment types