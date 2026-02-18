# Tasks: Gold Tier - Autonomous Employee

**Input**: Design documents from `/specs/003-gold-tier/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Tests are NOT explicitly requested in the specification. Tasks focus on implementation only.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Project structure from plan.md:
- MCP servers: `.claude/mcp-servers/{service}-mcp/`
- Utilities: `utils/`
- Watchers: `watchers/`
- Vault: `AI_Employee/` and `/Vault/Logs/`
- Tests: `gold_tier_test/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Gold Tier structure

- [X] T001 Create new MCP server directories: .claude/mcp-servers/odoo-mcp/, facebook-mcp/, instagram-mcp/, twitter-mcp/
- [X] T002 Create new vault directories: AI_Employee/Audits/, AI_Employee/CEO_Briefings/
- [X] T003 Create structured log directory: AI_Employee/Logs/ with proper permissions
- [X] T004 [P] Install Python dependencies: facebook-sdk, tweepy, apscheduler (xmlrpc.client is built-in) - Added to requirements.txt
- [X] T005 [P] Update .env template with new environment variables for Odoo, Facebook, Instagram, Twitter
- [X] T006 [P] Update .mcp.json with Gold Tier MCP server configurations

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Implement structured JSON logging schema in utils/setup_logger.py (timestamp, action, actor, parameters, result, approval_status, duration_ms, error)
- [X] T008 [P] Create retry_handler.py in utils/ with exponential backoff and jitter logic
- [X] T009 [P] Create circuit breaker implementation in utils/retry_handler.py (Closed, Open, Half-Open states)
- [X] T010 Extend health_monitor.py in utils/ to support Gold Tier MCP server health checks
- [X] T011 [P] Create filesystem_watcher.py in watchers/ to monitor Pending_Approval/ → Approved/ workflow
- [X] T012 Extend action_executor.py in utils/ to support Odoo and social media actions

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 2 - Integrated Accounting System (Priority: P1)

**Goal**: Enable AI to create invoices and record payments in Odoo accounting system

**Independent Test**: Create a test invoice in Odoo via MCP server with dry_run=false after approval

### Implementation for User Story 2

- [X] T013 [P] [US2] Create mcp_server_odoo.py in .claude/mcp-servers/odoo-mcp/ with MCP server boilerplate
- [X] T014 [P] [US2] Create odoo_client.py in utils/ with XML-RPC connection wrapper
- [X] T015 [P] [US2] Create requirements.txt for odoo-mcp with no additional dependencies (uses built-in xmlrpc.client)
- [X] T016 [US2] Implement odoo_create_invoice tool in mcp_server_odoo.py per odoo-contract.md
- [X] T017 [US2] Implement odoo_record_payment tool in mcp_server_odoo.py per odoo-contract.md
- [X] T018 [US2] Implement odoo_get_partner tool (search partners) in mcp_server_odoo.py
- [X] T019 [US2] Implement odoo_list_invoices tool in mcp_server_odoo.py
- [X] T020 [US2] Add approval workflow integration for Odoo transactions in action_executor.py (auto-approve <$100 recurring, require approval >$100 or new payee)
- [X] T021 [US2] Add structured logging for all Odoo operations to /Vault/Logs/YYYY-MM-DD.json
- [X] T022 [US2] Add error handling with circuit breaker for Odoo API calls (NO auto-retry on create/payment per Constitutional Principle X)
- [X] T023 [US2] Create README.md for odoo-mcp with setup instructions and API documentation

### Dry Run Mode Implementation (Constitutional Requirement - Principle III)

- [X] T023A [US2] Implement dry_run parameter (default: true) for odoo_create_invoice tool in mcp_server_odoo.py
- [X] T023B [US2] Implement dry_run parameter (default: true) for odoo_record_payment tool in mcp_server_odoo.py
- [X] T023C [US2] Implement dry_run parameter (default: true) for odoo_get_partner tool in mcp_server_odoo.py
- [X] T023D [US2] Add dry_run validation in odoo_client.py: when true, log action without executing Odoo XML-RPC calls
- [X] T023E [US2] Add dry_run status to structured JSON logs for all Odoo operations

**Checkpoint**: At this point, Odoo integration should be fully functional and testable independently with dry-run safety

---

## Phase 4: User Story 3 - Social Media Management (Priority: P2)

**Goal**: Enable AI to post business updates to Facebook, Instagram, and Twitter with approval workflows

**Independent Test**: Draft a post, approve it via file system, and verify it publishes to all three platforms

### Implementation for User Story 3 - Facebook

- [X] T024 [P] [US3] Create mcp_server_facebook.py in .claude/mcp-servers/facebook-mcp/ with MCP server boilerplate
- [X] T025 [P] [US3] Create requirements.txt for facebook-mcp with facebook-sdk dependency
- [X] T026 [US3] Implement facebook_create_post tool in mcp_server_facebook.py per facebook-contract.md
- [X] T027 [US3] Implement facebook_get_page_insights tool in mcp_server_facebook.py
- [X] T028 [US3] Implement facebook_delete_post tool in mcp_server_facebook.py
- [X] T029 [US3] Implement facebook_get_post tool in mcp_server_facebook.py
- [X] T030 [US3] Create README.md for facebook-mcp with token setup instructions

### Implementation for User Story 3 - Instagram

- [X] T031 [P] [US3] Create mcp_server_instagram.py in .claude/mcp-servers/instagram-mcp/ with MCP server boilerplate
- [X] T032 [P] [US3] Create requirements.txt for instagram-mcp with facebook-sdk dependency (Instagram uses Facebook Graph API)
- [X] T033 [US3] Implement instagram_create_post tool (container-based publishing) in mcp_server_instagram.py per instagram-contract.md
- [X] T034 [US3] Implement instagram_get_account_info tool in mcp_server_instagram.py
- [X] T035 [US3] Implement instagram_get_media_insights tool in mcp_server_instagram.py
- [X] T036 [US3] Implement instagram_get_recent_media tool in mcp_server_instagram.py
- [X] T037 [US3] Create README.md for instagram-mcp with Business Account setup instructions

### Implementation for User Story 3 - Twitter

- [X] T038 [P] [US3] Create mcp_server_twitter.py in .claude/mcp-servers/twitter-mcp/ with MCP server boilerplate
- [X] T039 [P] [US3] Create requirements.txt for twitter-mcp with tweepy dependency
- [X] T040 [US3] Implement twitter_create_tweet tool in mcp_server_twitter.py per twitter-contract.md
- [X] T041 [US3] Implement twitter_upload_media tool in mcp_server_twitter.py
- [X] T042 [US3] Implement twitter_delete_tweet tool in mcp_server_twitter.py
- [X] T043 [US3] Implement twitter_get_user_tweets tool in mcp_server_twitter.py
- [X] T044 [US3] Implement twitter_get_user_info tool in mcp_server_twitter.py
- [X] T045 [US3] Create README.md for twitter-mcp with API key setup instructions

### Implementation for User Story 3 - Unified Social Media Manager

- [X] T046 [US3] Create social_media_manager.py in utils/ with unified posting interface across all platforms
- [X] T047 [US3] Implement approval workflow for social media posts (auto-approve scheduled, require approval for replies/DMs) in social_media_manager.py
- [X] T048 [US3] Add content validation (character limits, media requirements) per platform in social_media_manager.py
- [X] T049 [US3] Integrate social media posting with filesystem_watcher.py for approval detection
- [X] T050 [US3] Add structured logging for all social media operations to /Vault/Logs/YYYY-MM-DD.json
- [X] T051 [US3] Add error handling with retry logic for transient failures (but NO retry on post creation per Principle X)

### Dry Run Mode Implementation (Constitutional Requirement - Principle III)

- [X] T051A [US3] Implement dry_run parameter (default: true) for facebook_create_post tool in mcp_server_facebook.py
- [X] T051B [US3] Implement dry_run parameter (default: true) for instagram_create_post tool in mcp_server_instagram.py
- [X] T051C [US3] Implement dry_run parameter (default: true) for twitter_create_tweet tool in mcp_server_twitter.py
- [X] T051D [US3] Add dry_run validation in social_media_manager.py: when true, log action without posting to platforms
- [X] T051E [US3] Add dry_run status to structured JSON logs for all social media operations

**Checkpoint**: At this point, all social media platforms should be independently postable with approval workflows and dry-run safety

---

## Phase 5: User Story 1 - Autonomous Business Management (Priority: P1)

**Goal**: Generate weekly business audits and Monday Morning CEO Briefings automatically

**Independent Test**: Manually trigger audit generation and verify comprehensive briefing is created with metrics from all systems

### Implementation for User Story 1

- [X] T052 [P] [US1] Create audit_generator.py in utils/ with generate_weekly_audit() function per audit-contract.md
- [X] T053 [P] [US1] Create ceo_briefing_generator.py in utils/ with generate_ceo_briefing() function per audit-contract.md
- [X] T054 [US1] Implement log parsing logic in audit_generator.py to extract metrics from /Vault/Logs/YYYY-MM-DD.json
- [X] T055 [US1] Implement vault scanning logic in audit_generator.py (count tasks, plans, approvals from AI_Employee/)
- [X] T056 [US1] Implement audit metrics calculation (activity, communication, social media, tasks, approvals, errors, system health) in audit_generator.py
- [X] T057 [US1] Implement Markdown audit report generation in audit_generator.py
- [X] T058 [US1] Implement bottleneck detection rules in ceo_briefing_generator.py (>5 pending approvals, >10 errors from service, >20 pending tasks)
- [X] T059 [US1] Implement proactive suggestion generation in ceo_briefing_generator.py (repeat customer inquiries, high error rates, low engagement)
- [X] T060 [US1] Implement project status extraction from AI_Employee/Plans/*.md files in ceo_briefing_generator.py
- [X] T061 [US1] Implement Markdown briefing report generation in ceo_briefing_generator.py
- [X] T062 [US1] Integrate APScheduler in orchestrator.py with CronTrigger for Sunday 10pm execution
- [X] T063 [US1] Configure scheduler with coalesce=True and max_instances=1 to prevent concurrent runs
- [X] T064 [US1] Create weekly_audit_job() function in orchestrator.py to trigger audit then briefing generation
- [X] T065 [US1] Add structured logging for audit and briefing generation to /Vault/Logs/
- [X] T066 [US1] Add error alerting for failed audit/briefing generation (create alert file in Needs_Action/)

**Checkpoint**: At this point, weekly audits and CEO briefings should generate automatically every Sunday night

---

## Phase 6: User Story 4 - Comprehensive Error Handling and Monitoring (Priority: P2)

**Goal**: Ensure system handles failures gracefully with retry mechanisms and automatic recovery

**Independent Test**: Simulate MCP server failure and verify watchdog restarts the service, queues pending actions, and processes them after recovery

### Implementation for User Story 4

- [X] T067 [US4] Extend retry_handler.py to support service-specific retry policies (read operations: YES retry, write operations: NO retry per Principle X)
- [X] T068 [US4] Implement rate limit detection and backoff for each MCP server in retry_handler.py
- [X] T069 [US4] Add circuit breaker integration to all MCP server calls in action_executor.py
- [X] T070 [US4] Extend health_monitor.py to poll MCP servers every 30 seconds via health check endpoints
- [X] T071 [US4] Implement watchdog auto-restart logic in health_monitor.py (max 3 attempts, then alert)
- [X] T072 [US4] Create operation queue in action_executor.py for pending actions during MCP failures
- [X] T073 [US4] Implement queue processing logic to retry queued operations when service recovers
- [X] T074 [US4] Add error aggregation and reporting in health_monitor.py (track errors by service, time window)
- [X] T075 [US4] Implement graceful degradation strategy (continue other operations when one service fails)
- [X] T076 [US4] Add comprehensive error logging with stack traces and context to /Vault/Logs/
- [X] T077 [US4] Update orchestrator.py to start health_monitor and watchdog on Gold Tier mode
- [X] T078 [US4] Configure 90-day log retention policy (no auto-deletion per Principle IX)

### Global Dry Run Enforcement (Constitutional Requirement - Principle III)

- [X] T078A [US4] Extend action_executor.py to check dry_run flag before executing ANY MCP action
- [X] T078B [US4] Add dry_run parameter validation: reject actions with dry_run=false unless explicitly approved
- [X] T078C [US4] Update all action execution logs to include dry_run status field

**Checkpoint**: All services should now have robust error handling, auto-recovery, graceful degradation, and constitutional dry-run compliance

---

## Phase 6.5: Cross-Domain Integration (FR-014)

**Goal**: Implement automated workflows connecting personal (Gmail) and business (Odoo) domains

**Independent Test**: Send test email with invoice request keywords, verify draft invoice created in Pending_Approval/, approve it, verify Odoo invoice created

### Gmail → Odoo Invoice Automation

- [X] T079 [P] [XD] Create gmail_to_odoo_parser.py in utils/ to extract invoice details from email bodies
- [X] T080 [XD] Implement email pattern matching in gmail_to_odoo_parser.py (keywords: "invoice", "quote", "bill", "please send invoice")
- [X] T081 [XD] Implement invoice detail extraction (customer name, amount, line items, due date, description) using regex and NLP patterns
- [X] T082 [XD] Extend gmail_watcher.py to integrate with gmail_to_odoo_parser for invoice request detection
- [X] T083 [XD] Implement draft invoice creation workflow: parse email → create INVOICE_draft_YYYY-MM-DD.md → save to Pending_Approval/
- [X] T084 [XD] Add approval detection: when user moves draft from Pending_Approval/ to Approved/, trigger odoo_client.py to create invoice
- [X] T085 [XD] Add structured logging for all cross-domain Gmail→Odoo actions with domain linkage tags
- [X] T086 [XD] Add error handling: if parsing fails, create clarification request in Needs_Action/ for human review

**Checkpoint**: Gmail invoice requests automatically create draft invoices with full approval workflow and error handling

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and finalization

- [ ] T087 [P] Update quickstart.md with complete setup instructions for all Gold Tier services
- [ ] T088 [P] Create or update DEPLOYMENT.md with production deployment checklist
- [ ] T089 [P] Verify all environment variables are documented and in .env.example
- [ ] T090 [P] Add .gitignore entries for /Vault/Logs/*.json and ensure .env is ignored
- [ ] T091 Test complete end-to-end workflow: Odoo transaction → approval → sync
- [ ] T092 Test complete end-to-end workflow: Social media post → approval → publish to all platforms
- [ ] T093 Test complete end-to-end workflow: Gmail invoice request → draft creation → approval → Odoo invoice
- [ ] T094 Test complete end-to-end workflow: Wait for Sunday night → audit → briefing generation
- [ ] T095 Test error recovery: Stop Odoo → create transaction → restart Odoo → verify retry
- [ ] T096 Test dry-run mode: Execute Odoo and social media operations with dry_run=true, verify no real API calls
- [ ] T097 Verify all constitutional principles are satisfied (approval workflows, dry-run mode, logging, no auto-retry on destructive actions)
- [ ] T098 Performance optimization: Ensure CEO briefing generation completes within 10 minutes (SC-001)
- [ ] T099 Security audit: Verify no credentials are logged, all tokens in .env, file permissions correct
- [ ] T100 Run validation from quickstart.md to verify all setup steps work

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-6)**: All depend on Foundational phase completion
  - US2 (Odoo - Phase 3): Can start immediately after Foundational, includes dry-run tasks (T023A-T023E)
  - US3 (Social Media - Phase 4): Can start immediately after Foundational (parallel with US2), includes dry-run tasks (T051A-T051E)
  - US1 (Autonomous Management - Phase 5): Can start immediately after Foundational (parallel with US2/US3, but benefits from their data)
  - US4 (Error Handling - Phase 6): Should start after US2/US3/US1 have initial implementations, includes global dry-run enforcement (T078A-T078C)
- **Cross-Domain Integration (Phase 6.5)**: Depends on Phase 3 (Odoo) completion for Gmail→Odoo workflow (T079-T086)
- **Polish (Phase 7)**: Depends on all desired user stories and cross-domain integration being complete (T087-T100)

### User Story Dependencies

- **User Story 2 (P1 - Odoo)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P2 - Social Media)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 1 (P1 - Autonomous Management)**: Can start after Foundational (Phase 2) - Benefits from US2/US3 data but doesn't require them
- **User Story 4 (P2 - Error Handling)**: Should start after US2/US3/US1 have implementations - Wraps error handling around all services

### Within Each User Story

**User Story 2 (Odoo):**
- T013-T015 (MCP server setup) can run in parallel
- T016-T019 (tool implementations) must run sequentially (build on server)
- T020-T023 (integration) must come after tools
- T023A-T023E (dry-run mode) must come after T023 - CONSTITUTIONAL REQUIREMENT

**User Story 3 (Social Media):**
- T024-T030 (Facebook), T031-T037 (Instagram), T038-T045 (Twitter) can all run in parallel
- T046-T051 (unified manager) must come after all MCP servers
- T051A-T051E (dry-run mode) must come after T051 - CONSTITUTIONAL REQUIREMENT

**User Story 1 (Audit/Briefing):**
- T052-T053 (create files) can run in parallel
- T054-T061 (implementation) builds sequentially
- T062-T066 (scheduler integration) comes last

**User Story 4 (Error Handling):**
- T067-T069 (retry logic) can be done first
- T070-T074 (health monitoring) can run in parallel with retry
- T075-T078 (integration) comes last
- T078A-T078C (global dry-run enforcement) must come after T078 - CONSTITUTIONAL REQUIREMENT

**Cross-Domain Integration (Phase 6.5):**
- T079-T080 (parser creation) can run in parallel
- T081-T086 (integration workflow) must run sequentially
- Depends on Phase 3 (Odoo) completion - needs odoo_client.py

### Parallel Opportunities

- All Setup tasks (T001-T006) can run in parallel
- Within Foundational: T008-T009 (retry/circuit breaker), T011-T012 (watcher/executor) can run in parallel after T007 (logging)
- US2 and US3 can be developed completely in parallel after Foundational
- Within US3: Facebook (T024-T030), Instagram (T031-T037), Twitter (T038-T045) can all proceed in parallel
- Cross-domain tasks T079-T080 (parser creation) can run in parallel
- Polish tasks (T087-T090) can run in parallel

---

## Parallel Example: User Story 3 (Social Media)

```bash
# Launch all three MCP server implementations together:
Task: "Create mcp_server_facebook.py in .claude/mcp-servers/facebook-mcp/"
Task: "Create mcp_server_instagram.py in .claude/mcp-servers/instagram-mcp/"
Task: "Create mcp_server_twitter.py in .claude/mcp-servers/twitter-mcp/"

# After MCP servers complete, implement unified manager:
Task: "Create social_media_manager.py in utils/ with unified posting interface"
```

---

## Implementation Strategy

### MVP First (Odoo + Basic Audit)

1. Complete Phase 1: Setup → ~30 minutes
2. Complete Phase 2: Foundational → ~2 hours
3. Complete Phase 3: US2 (Odoo Integration + Dry-Run) → ~5 hours (includes T023A-T023E)
4. Complete Phase 5 (partial): US1 (Just audit/briefing generation, without social data) → ~3 hours
5. **STOP and VALIDATE**: Test Odoo invoice creation with dry-run mode and audit generation independently
6. Deploy/demo if ready

**MVP Delivers**: Accounting automation with constitutional dry-run safety + weekly business insights

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (~2.5 hours)
2. Add US2 (Odoo + Dry-Run) → Test independently → Deploy/Demo (~5 hours) - **Accounting automation live with dry-run safety!**
3. Add US3 (Social Media + Dry-Run) → Test independently → Deploy/Demo (~7 hours) - **Social media automation live with dry-run safety!**
4. Add US1 (Autonomous Management) → Test independently → Deploy/Demo (~3 hours) - **CEO briefings with full data live!**
5. Add US4 (Error Handling + Global Dry-Run) → Test independently → Deploy/Demo (~3.5 hours) - **Production-ready reliability!**
6. Add Phase 6.5 (Cross-Domain Gmail→Odoo) → Test independently → Deploy/Demo (~3 hours) - **Automated invoice drafts from email!**
7. Polish → Final validation → Production deployment (~2 hours)

**Total Estimated Time**: ~26-28 hours for complete Gold Tier implementation (includes dry-run mode + cross-domain integration)

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (~2.5 hours)
2. Once Foundational is done:
   - **Developer A**: US2 (Odoo + Dry-Run) → 5 hours
   - **Developer B**: US3 (Social Media + Dry-Run) → 7 hours
   - **Developer C**: US1 (Audit/Briefing) → 3 hours
3. After initial implementations:
   - **Developer A**: US4 (Error Handling + Global Dry-Run) → 3.5 hours
   - **Developer B or C**: Phase 6.5 (Cross-Domain) → 3 hours
4. All developers: Polish together → 2 hours

**Parallel Completion Time**: ~16-18 hours with 3 developers

---

## Notes

- [P] tasks = different files, no dependencies, safe to run in parallel
- [US#] label maps task to specific user story for traceability
- [XD] label indicates cross-domain integration tasks (Phase 6.5)
- Each user story should be independently completable and testable
- Commit after each task or logical group of related tasks
- Stop at any checkpoint to validate story independently
- All MCP servers follow the same pattern: boilerplate → tools → dry-run integration
- **CRITICAL**: Dry-run mode tasks (T023A-E, T051A-E, T078A-C) are CONSTITUTIONAL REQUIREMENTS - cannot be skipped
- Constitutional principles enforced: **default dry-run mode**, approval workflows, no destructive auto-retry, comprehensive logging, 90-day retention
- Cross-domain integration: Gmail→Odoo invoice drafts (Phase 6.5, T079-T086)
- 💰 Total Cost: $0 - All integrations use free tiers
- ⏱️ Performance targets: CEO briefing <10 min (SC-001), social posts <5 min (SC-003)
- 📊 Revised time estimate: ~26-28 hours solo, ~16-18 hours with 3 developers (includes dry-run + cross-domain)
