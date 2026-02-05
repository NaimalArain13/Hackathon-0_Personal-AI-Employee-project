# Task List: Bronze Tier - Personal AI Employee Foundation

**Feature**: Bronze Tier - Personal AI Employee Foundation
**Branch**: `001-bronze-tier`
**Spec**: [specs/001-bronze-tier/spec.md](specs/001-bronze-tier/spec.md)
**Plan**: [specs/001-bronze-tier/plan.md](specs/001-bronze-tier/plan.md)
**Input**: Feature specification and implementation plan

## Implementation Strategy

Build a Personal AI Employee foundation implementing the Bronze Tier requirements from the hackathon specification. The system will use Claude Code as the reasoning engine with Obsidian as the local knowledge base, implementing watcher scripts (Gmail, file system) to trigger AI processing of tasks, with MCP servers for external actions and human-in-the-loop approval for sensitive operations.

### Approach
1. Start with foundational setup (project structure, dependencies)
2. Implement Obsidian vault with essential documents (Dashboard.md, Company_Handbook.md)
3. Create the file system watcher to monitor for new files
4. Enable Claude Code integration with file system tools
5. Develop Agent Skills for AI functionality
6. Test the complete workflow

### MVP Scope
Focus on User Story 1 (Obsidian Vault Setup) and User Story 2 (File System Watcher) for initial working prototype.

---

## Phase 1: Project Setup and Environment Configuration

**Goal**: Set up the development environment and project structure for the Personal AI Employee.

### Independent Test Criteria
- Project directory structure is created successfully
- Dependencies can be installed without errors
- Development environment is properly configured

### Tasks
- [x] T001 Create project root directory structure with necessary subdirectories
- [x] T002 Set up virtual environment with Python 3.13+ and install required dependencies (watchdog, playwright, google-api-python-client)
- [ ] T003 Install Node.js v24+ and required packages for MCP servers
- [x] T004 Create project configuration files (.env, .gitignore, etc.)

---

## Phase 2: Foundational Infrastructure

**Goal**: Establish the foundational components that will be used by all user stories.

### Independent Test Criteria
- Basic project structure is in place
- Obsidian vault directory structure is created
- Shared utilities and base classes are available

### Tasks
- [x] T005 Create the Obsidian vault directory structure with required folders (Inbox, Needs_Action, Done, Logs, Pending_Approval, Approved, Rejected)
- [x] T006 [P] Create base watcher class (base_watcher.py) with abstract methods for check_for_updates and create_action_file
- [x] T007 [P] Create shared utility functions for file handling and logging
- [x] T008 Create orchestrator.py as the main process orchestrator

---

## Phase 3: User Story 1 - Obsidian Vault Setup with Essential Documents (Priority: P1)

**Goal**: Establish a foundation for the Personal AI Employee using Obsidian as the central knowledge base with Dashboard.md for real-time status updates and Company_Handbook.md for defining rules and engagement guidelines.

### Independent Test Criteria
- User can create an Obsidian vault with the required documents and manually update them to reflect their preferences and business rules
- Dashboard.md and Company_Handbook.md are created with proper templates and initial content
- The file properly stores and displays engagement rules when updated

### Acceptance Tests
- [x] T009 [US1] Create Dashboard.md template with placeholders for bank balance, pending messages, and active business projects
- [x] T010 [US1] Create Company_Handbook.md template with configurable "Rules of Engagement" section allowing users to define interaction guidelines

### Implementation Tasks
- [x] T011 [US1] Implement Dashboard.md creation with status placeholders (bank balance, pending messages, active projects)
- [x] T012 [US1] Implement Company_Handbook.md creation with rules configuration sections (email, WhatsApp, file processing, approval requirements)
- [x] T013 [US1] Verify templates render properly in Obsidian and are editable by users

---

## Phase 4: User Story 2 - File System Watcher Implementation (Priority: P1)

**Goal**: Implement a watcher script that monitors the file system for new files dropped into a designated folder, creating actionable files in the /Needs_Action folder for the AI employee to process.

### Independent Test Criteria
- User can drop files into a monitored folder and see corresponding .md files appear in /Needs_Action with appropriate metadata
- The system delivers value by enabling file-based automation triggers
- Multiple files are handled properly

### Acceptance Tests
- [ ] T014 [US2] Test that when file watcher is running and user places a new file in the monitored folder, a corresponding .md file appears in the /Needs_Action folder with metadata about the original file
- [ ] T015 [US2] Test that when file watcher is running and multiple files are added simultaneously, each file gets its own metadata file in the /Needs_Action folder

### Implementation Tasks
- [x] T016 [US2] Create filesystem_watcher.py with DropFolderHandler extending FileSystemEventHandler
- [x] T017 [US2] Implement file monitoring using watchdog library to detect new files in designated folder
- [x] T018 [US2] Implement creation of metadata files in /Needs_Action folder when new files are detected
- [x] T019 [US2] Add appropriate metadata to created files (file type, original name, size, timestamp)
- [x] T020 [US2] Add continuous monitoring with error handling and logging capabilities

---

## Phase 5: User Story 3 - Claude Code File System Integration (Priority: P1)

**Goal**: Enable Claude Code to read from and write to the Obsidian vault, allowing the AI to process files in /Needs_Action and create plans or completed work in other folders.

### Independent Test Criteria
- User can observe Claude Code reading files from the vault and writing new files or updating existing ones
- The AI demonstrates its ability to process information and take action
- Claude Code can update Dashboard.md successfully while maintaining format and structure

### Acceptance Tests
- [ ] T021 [US3] Test that when files exist in /Needs_Action folder and Claude Code processes the vault, it reads these files and creates appropriate output files in the appropriate locations
- [ ] T022 [US3] Test that when Claude Code is operating on the vault and needs to update Dashboard.md, it successfully writes to the file maintaining its format and structure

### Implementation Tasks
- [ ] T023 [US3] Configure Claude Code to have access to the Obsidian vault directory for reading files
- [ ] T024 [US3] Implement Claude Code configuration to write files to appropriate vault locations
- [ ] T025 [US3] Create sample prompts and workflows for Claude to process files from /Needs_Action
- [ ] T026 [US3] Verify Claude Code can update Dashboard.md and other vault files appropriately

---

## Phase 6: User Story 4 - Basic Folder Structure Setup (Priority: P2)

**Goal**: Establish a standardized folder structure (/Inbox, /Needs_Action, /Done) to organize tasks and work in progress for the AI employee.

### Independent Test Criteria
- User can manually place files in different folders and see that the organization makes sense
- The system provides clear separation of work states
- Work items move appropriately through the folder system (Inbox → Needs_Action → Done)

### Acceptance Tests
- [ ] T027 [US4] Test that when user needs to set up the AI employee and the system creates the basic folder structure, /Inbox, /Needs_Action, and /Done folders exist and are properly accessible
- [ ] T028 [US4] Test that when work items exist and they are processed, they move appropriately through the folder system (Inbox → Needs_Action → Done)

### Implementation Tasks
- [ ] T029 [US4] Ensure all required folders are created in the Obsidian vault (Inbox, Needs_Action, Done, Logs, Pending_Approval, Approved, Rejected)
- [ ] T030 [US4] Verify proper permissions and accessibility of each folder
- [ ] T031 [US4] Document the folder workflow for users and AI processing

---

## Phase 7: User Story 5 - Agent Skills Implementation for AI Functionality (Priority: P1)

**Goal**: Implement AI functionality as Agent Skills according to the Bronze Tier requirement that "All AI functionality should be implemented as Agent Skills".

### Independent Test Criteria
- User can see that AI behaviors are encapsulated as Agent Skills and can be invoked as modular components
- New AI capabilities can be integrated cleanly with the existing system following the same pattern
- The system provides reusable and maintainable AI capabilities

### Acceptance Tests
- [ ] T032 [US5] Test that when AI needs to perform a specific function and the corresponding Agent Skill is invoked, it performs the function appropriately without tight coupling to the core system
- [ ] T033 [US5] Test that when new AI capabilities are needed and a new Agent Skill is created, it integrates cleanly with the existing system following the same pattern

### Implementation Tasks
- [ ] T034 [US5] Set up Claude Code Agent Skills framework and configuration
- [ ] T035 [US5] Create obsidian-connector Agent Skill for interacting with Obsidian vault
- [ ] T036 [US5] Create vault-manager Agent Skill for managing vault operations
- [ ] T037 [US5] Document how to create additional Agent Skills following the same pattern

---

## Phase 8: Integration and Testing

**Goal**: Integrate all components and verify the complete workflow functions as expected.

### Independent Test Criteria
- All components work together in a cohesive system
- End-to-end file processing workflow is functional
- The system behaves according to the functional requirements

### Acceptance Tests
- [ ] T038 [P] Verify FR-001: Dashboard.md is created with bank balance, pending messages, and business projects placeholders
- [ ] T039 [P] Verify FR-002: Company_Handbook.md is created with configurable "Rules of Engagement" section
- [ ] T040 [P] Verify FR-004: File system watcher monitors folder and copies files to /Needs_Action with metadata
- [ ] T041 [P] Verify FR-005: Folder structure (Inbox, Needs_Action, Done) is properly created and maintained
- [ ] T042 [P] Verify FR-006: AI functionality is implemented as Agent Skills
- [ ] T043 [P] Verify FR-007: Claude Code can read from /Needs_Action and write to other vault locations
- [ ] T044 [P] Verify FR-009: New markdown files follow expected schema for Claude Code processing
- [ ] T045 [P] Verify FR-011: File watcher uses watchdog library with specified functionality

### Implementation Tasks
- [ ] T046 Set up complete end-to-end workflow from file drop to action completion
- [ ] T047 Verify all functional requirements are met (FR-001 through FR-011)
- [ ] T048 Create test scenarios to validate the complete workflow
- [ ] T049 Verify human-in-the-loop approval workflows function correctly

---

## Phase 9: Polish & Cross-Cutting Concerns

**Goal**: Final touches, documentation, and quality improvements across the entire system.

### Implementation Tasks
- [ ] T050 [P] Add comprehensive error handling and logging throughout the system
- [ ] T051 [P] Create detailed setup and usage documentation
- [ ] T052 [P] Add configuration options for customization
- [ ] T053 [P] Implement watchdog process to monitor and restart critical components
- [ ] T054 [P] Add performance monitoring and metrics
- [ ] T055 Create troubleshooting guide based on common issues
- [ ] T056 Verify all success criteria (SC-001 through SC-005) are met

---

## Dependencies

### User Story Dependency Graph
- US1 (Obsidian Vault) → US2 (File System Watcher) → US3 (Claude Integration) → US4 (Folder Structure) → US5 (Agent Skills)
- US4 can technically run in parallel with US2 and US3, but for workflow clarity, US4 comes after US2

### Parallel Execution Opportunities
- T006, T007: Base watcher and utilities can be created in parallel
- T009, T010: Dashboard and Company Handbook templates can be created in parallel
- T032, T033: Agent skill tests can run in parallel
- T038-T045: Most verification tasks can run in parallel

## Success Criteria Verification

- [ ] SC-001: User can complete setup of the foundational Obsidian vault structure within 30 minutes
- [ ] SC-002: File system watcher successfully detects and processes 100% of new files during 24-hour test
- [ ] SC-003: Claude Code successfully reads/writes to the Obsidian vault 95% of the time
- [ ] SC-004: All AI functionality operates through Agent Skills with 100% compliance
- [ ] SC-005: Basic folder structure is properly maintained and accessible for entire duration
