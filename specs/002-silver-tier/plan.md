# Implementation Plan: Silver Tier - Functional Assistant

**Branch**: `002-silver-tier` | **Date**: 2026-02-05 | **Spec**: [link to spec.md](spec.md)
**Input**: Feature specification from `/specs/002-silver-tier/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implementation of Silver Tier functionality to create a functional assistant that includes: Email MCP server integration with Gmail using SMTP authentication, LinkedIn automation via Playwright browser automation, multiple concurrent watcher services (Gmail, WhatsApp), human-in-the-loop approval workflows for sensitive actions, automated plan generation, and scheduling capabilities using cross-platform Python libraries.

## Technical Context

**Language/Version**: Python 3.13+ (as required by the project)
**Primary Dependencies**:
- Claude Code (primary reasoning engine)
- Obsidian (knowledge base/dashboard)
- MCP servers (email-mcp, playwright-mcp)
- Google APIs (for Gmail integration)
- Playwright (for LinkedIn automation)
- Schedule or APScheduler (for cross-platform scheduling)
- pydantic (for email MCP server)
- python-dotenv (for environment management)
**Storage**: File-based storage using Obsidian vault markdown files and local directories
**Testing**: pytest for unit and integration testing
**Target Platform**: Cross-platform (Windows, macOS, Linux) - local-first architecture
**Project Type**: Single project with multiple integrated components (local-first automation system)
**Performance Goals**: Respond to email triggers within 2 minutes, send approved emails within 30 seconds, maintain 24+ hour uptime without manual intervention
**Constraints**: Local-first architecture (data stays on user's machine), secure credential handling, human-in-the-loop for sensitive actions, proper error handling with exponential backoff (1s, 2s, 4s, 8s, 16s), attachment size/type limitations
**Scale/Scope**: Personal AI employee for individual/small business use, single-user system with multiple communication channels

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Based on the project constitution, the following checks have been validated:
- ✓ Code quality standards are maintained per constitution
- ✓ Security practices align with constitutional requirements (credential handling, human-in-the-loop)
- ✓ Local-first architecture is preserved (file-based storage, Obsidian vault)
- ✓ Human-in-the-loop principles are properly implemented (approval workflows)
- ✓ Proper error handling and observability are planned (exponential backoff, logging)

## Project Structure

### Documentation (this feature)

```text
specs/002-silver-tier/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
# Single project with multiple integrated components
AI_Employee/
├── attachments/                    # Email attachments folder
├── Inbox/                        # Incoming action items
├── Needs_Action/                 # Items requiring processing
├── Done/                         # Completed items
├── Plans/                        # Generated plan files
├── Pending_Approval/             # Items awaiting human approval
├── Approved/                     # Approved items ready for execution
├── Logs/                         # System logs
├── watchers/                     # Watcher service implementations
│   ├── gmail_watcher.py          # Gmail monitoring service
│   ├── whatsapp_watcher.py       # WhatsApp monitoring service
│   └── base_watcher.py           # Base watcher class
├── mcp_servers/                  # MCP server implementations
│   ├── email_mcp_server/         # Email MCP server module
│   └── playwright_mcp_server/    # Playwright MCP server configuration
├── orchestrator.py               # Main orchestrator process
├── utils/                        # Utility functions and helpers
│   └── setup_logger.py           # Logging utilities
├── Dashboard.md                  # Real-time status dashboard
├── Company_Handbook.md           # Business rules and engagement policies
└── requirements.txt              # Python dependencies
```

**Structure Decision**: Selected single project structure with modular components to implement the local-first AI assistant. The structure separates concerns between watchers, MCP servers, and orchestration while maintaining the Obsidian vault structure for the knowledge base.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Multiple concurrent services | Silver Tier requirement for 2+ simultaneous watchers | Single-threaded processing insufficient for multi-channel monitoring |
| MCP server integrations | Required by Silver Tier to have working MCP server for external actions | Direct API calls would bypass Claude Code's reasoning capabilities |
