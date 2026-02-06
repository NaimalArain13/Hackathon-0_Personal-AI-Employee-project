# Tasks: Silver Tier - Functional Assistant

**Feature**: Silver Tier - Functional Assistant
**Branch**: `002-silver-tier`
**Created**: 2026-02-05
**Dependencies**: spec.md, plan.md, data-model.md, contracts/

## Implementation Strategy

Build incrementally following user story priority (P1, P2, P3...). Start with US1 (Multi-Channel Email Management) as the MVP, then add subsequent features. Each user story should be independently testable with its own acceptance criteria.

## Dependencies Between User Stories

- US2 (LinkedIn Automation) requires US6 (MCP Server Integration) to be partially complete
- US3 (Multi-Watcher Coordination) requires US1 (Gmail Watcher) foundation
- US4 (Human-in-the-Loop) requires file system foundations from earlier stories
- US5 (Planning) requires file system foundations from earlier stories

## Parallel Execution Opportunities

- [US1] MCP Server Setup and [US6] MCP Server Integration can run in parallel
- [US2] LinkedIn Automation and [US3] WhatsApp Watcher implementation can run in parallel (different channels)
- [US4] Approval Workflow and [US5] Plan Generation can run in parallel (both involve file manipulation)

---

## Phase 1: Setup Tasks

### Goal
Initialize project structure and install dependencies required for Silver Tier functionality.

### Independent Test Criteria
Project structure matches plan.md and all required dependencies are installed.

### Tasks

- [x] T001 Add required new directories to existing AI_Employee structure (attachments, Plans, Pending_Approval, Approved, Logs) - leave existing Inbox, Needs_Action, Done intact
- [x] T002 Add new Python dependencies to requirements.txt: pydantic, schedule, apscheduler
- [x] T003 Create email.json configuration file for SMTP settings
- [x] T004 Update existing .env file with new environment variables for Silver Tier
- [x] T005 Create or update Dashboard.md and Company_Handbook.md files in AI_Employee directory

---

## Phase 2: Foundational Tasks

### Goal
Establish foundational components needed across all user stories (logger, base watcher, file utilities).

### Independent Test Criteria
Base components can be instantiated and perform basic functionality without error.

### Tasks

- [x] T010 [P] Update existing base_watcher.py with additional methods needed for Silver Tier if not already present
- [x] T011 [P] Create or update setup_logger.py utility for consistent logging across all components
- [x] T012 [P] Create file utilities for reading/writing markdown files in Obsidian vault
- [x] T013 [P] Update existing orchestrator.py with Silver Tier functionality
- [x] T014 Create email.json configuration file with Gmail SMTP settings

---

## Phase 3: [US1] Multi-Channel Email Management

### Goal
Implement Gmail monitoring and email sending capabilities using Email MCP server.

### Independent Test Criteria
System can monitor Gmail for new messages, create action files in Needs_Action folder, and send emails via MCP server when approved.

### Tasks

- [ ] T020 [US1] Create gmail_watcher.py extending base_watcher.py with Gmail-specific implementation
- [ ] T021 [US1] Implement Gmail authentication using Google APIs and OAuth2 credentials
- [ ] T022 [US1] Implement check_for_updates() method to fetch unread emails from Gmail
- [ ] T023 [US1] Implement create_action_file() method to create .md files in Needs_Action folder
- [ ] T024 [US1] Set up Email MCP server with proper SMTP configuration for Gmail
- [ ] T025 [US1] Test email sending functionality with subject, body, and recipients
- [ ] T026 [US1] Implement attachment handling for emails (PDF, DOCX, JPG, etc.)
- [ ] T027 [US1] Test complete email workflow from receipt to response

---

## Phase 4: [US6] MCP Server Integration

### Goal
Integrate Email MCP server with Claude Code for external email actions.

### Independent Test Criteria
Claude Code can successfully communicate with Email MCP server to send emails with attachments.

### Tasks

- [ ] T030 [US6] Configure Claude Code MCP settings to connect to email MCP server
- [ ] T031 [US6] Implement send_email tool interface per email-mcp-contract.md
- [ ] T032 [US6] Implement search_attachments tool interface per email-mcp-contract.md
- [ ] T033 [US6] Test send_email functionality with multiple recipients and attachments
- [ ] T034 [US6] Test search_attachments functionality with various file patterns
- [ ] T035 [US6] Handle authentication errors and invalid attachment types per contract
- [ ] T036 [US6] Test error handling and response formats per contract specification

---

## Phase 5: [US2] LinkedIn Business Automation

### Goal
Implement LinkedIn automation using Playwright MCP server to generate and post business content.

### Independent Test Criteria
System can generate business content and post it to LinkedIn using Playwright browser automation.

### Tasks

- [ ] T040 [US2] Set up Playwright MCP server configuration per specification
- [ ] T041 [US2] Create LinkedIn post generation logic based on business achievements
- [ ] T042 [US2] Implement LinkedIn login and authentication via Playwright
- [ ] T043 [US2] Create LinkedIn post creation functionality using browser automation
- [ ] T044 [US2] Implement scheduling logic for LinkedIn posts using schedule library
- [ ] T045 [US2] Test LinkedIn post creation and scheduling functionality
- [ ] T046 [US2] Handle LinkedIn rate limiting and anti-bot measures

---

## Phase 6: [US3] Multi-Watcher Coordination

### Goal
Implement multiple concurrent watcher services (Gmail, WhatsApp) that coordinate without conflicts.

### Independent Test Criteria
Multiple watcher services run concurrently, monitor their respective channels, and create coordinated action items without conflicts.

### Tasks

- [ ] T050 [US3] Create whatsapp_watcher.py extending base_watcher.py with WhatsApp-specific implementation
- [ ] T051 [US3] Implement WhatsApp message monitoring using Playwright automation
- [ ] T052 [US3] Ensure existing Gmail watcher and new WhatsApp watcher can run simultaneously without conflict
- [ ] T053 [US3] Implement conflict resolution for duplicate action items across channels
- [ ] T054 [US3] Test concurrent operation of multiple watchers
- [ ] T055 [US3] Monitor resource usage and performance impact of multiple watchers

---

## Phase 7: [US4] Human-in-the-Loop Approval Workflow

### Goal
Implement approval workflow for sensitive actions including emotional contexts, legal matters, etc.

### Independent Test Criteria
System creates approval requests for sensitive actions and waits for human approval before proceeding.

### Tasks

- [ ] T060 [US4] Create sensitive content detection logic (emotional, legal, medical contexts)
- [ ] T061 [US4] Implement creation of approval files in Pending_Approval folder
- [ ] T062 [US4] Create approval request file format with proper metadata per data-model.md
- [ ] T063 [US4] Implement file monitoring for approval status changes (move to Approved/Rejected)
- [ ] T064 [US4] Create execution logic that only proceeds with approved actions
- [ ] T065 [US4] Test complete approval workflow from request to execution
- [ ] T066 [US4] Implement expiration logic for approval requests (24-hour limit)

---

## Phase 8: [US5] Automated Planning and Documentation

### Goal
Implement generation of structured Plan.md files for complex multi-step tasks.

### Independent Test Criteria
System analyzes incoming requests and generates structured Plan.md files with clear steps and status tracking.

### Tasks

- [ ] T070 [US5] Create Plan.md template with proper frontmatter and structure
- [ ] T071 [US5] Implement plan generation logic based on complex task identification
- [ ] T072 [US5] Create structured tasks with checkboxes for progress tracking
- [ ] T073 [US5] Link plan items to related entities (emails, LinkedIn posts, etc.)
- [ ] T074 [US5] Implement plan status updates as tasks are completed
- [ ] T075 [US5] Test plan generation and tracking functionality
- [ ] T076 [US5] Create plan monitoring for tracking progress on generated tasks

---

## Phase 9: Cross-cutting & Polish

### Goal
Implement error handling, logging, and performance improvements across all components.

### Independent Test Criteria
System demonstrates robust error handling, proper logging, and meets performance goals.

### Tasks

- [ ] T080 Implement exponential backoff retry mechanism (1s, 2s, 4s, 8s, 16s) for network operations
- [ ] T081 Add comprehensive logging to all watcher services with consistent format
- [ ] T082 Implement credential security practices (environment variables, no plaintext storage)
- [ ] T083 Add validation for attachment file types per specification (PDF, DOCX, etc.)
- [ ] T084 Create monitoring for 24+ hour uptime without manual intervention
- [ ] T085 Optimize file I/O operations for performance
- [ ] T086 Conduct end-to-end testing of all user stories
- [ ] T087 Document configuration and setup procedures for deployment

---

## Acceptance Tests

- [ ] AT01 US1 Acceptance: Gmail MCP server monitors email and creates action files within 2 minutes (SC-001)
- [ ] AT02 US1 Acceptance: Email MCP server sends 95% of approved emails within 30 seconds (SC-002)
- [ ] AT03 US2 Acceptance: LinkedIn posts created with 99% reliability during business hours (SC-004)
- [ ] AT04 US3 Acceptance: At least 2 watcher services run concurrently without interference (SC-003)
- [ ] AT05 US4 Acceptance: Approval system routes 90% of sensitive actions for approval (SC-005)
- [ ] AT06 US5 Acceptance: Plan.md files generated with structured tasks and progress indicators (SC-006)
- [ ] AT07 General: System maintains stable operation for 24+ hours (SC-007)
- [ ] AT08 US1 Acceptance: Email MCP server supports common attachment types (SC-008)
- [ ] AT09 General: 80% of routine communications handled automatically (SC-009)
- [ ] AT10 General: All communications maintain professional tone per Company_Handbook.md (SC-010)