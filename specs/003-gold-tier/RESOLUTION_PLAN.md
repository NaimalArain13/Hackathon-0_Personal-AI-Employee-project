# Resolution Plan for Critical Analysis Issues

## Issue C1: FR-013 (Agent Skills)

### Decision Required
Choose ONE option:

**Option A: Remove Requirement (RECOMMENDED)**
- Update spec.md: Remove FR-013 or replace with "modular MCP architecture"
- Rationale: Already satisfied by microservices MCP pattern
- Time saved: ~4-6 hours
- Risk: Low (MCP servers provide same modularity)

**Option B: Implement Minimal Agent Skills**
- Add tasks T091-T096 for Agent Skills packaging
- Create 3 skills: gold-tier-audit, gold-tier-odoo, gold-tier-social
- Time required: ~4-6 hours additional work
- Risk: Medium (new framework to learn)

### Recommended: **Option A**

---

## Issue C2: Constitution Principle III (Default Dry Run Mode)

### Required Action (CRITICAL - Cannot skip)

Add these tasks to tasks.md after T023 (Odoo completion):

```markdown
- [ ] T024-DRY Implement dry_run parameter for all Odoo MCP tools (create_invoice, record_payment)
- [ ] T025-DRY Add dry_run validation: when true, log action without executing Odoo API calls
```

Add these tasks after T051 (Social Media completion):

```markdown
- [ ] T052-DRY Implement dry_run parameter for all social media MCP tools (create_post, etc.)
- [ ] T053-DRY Add dry_run validation: when true, log action without posting to platforms
```

Update action_executor.py:
```markdown
- [ ] T054-DRY Extend action_executor.py to check dry_run flag before executing any MCP action
- [ ] T055-DRY Add dry_run status to structured JSON logs
```

**Time required**: ~2-3 hours
**Priority**: CRITICAL (constitution violation)

---

## Issue C3: Success Criteria Without Implementation

### Decision Required
Choose ONE option:

**Option A: Add Metrics Collection Tasks (If metrics are acceptance gates)**
```markdown
- [ ] T091-METRICS Create metrics_collector.py in utils/
- [ ] T092-METRICS Track uptime percentage (SC-002: 99% uptime)
- [ ] T093-METRICS Track data loss events during Odoo outages (SC-004: <1% loss)
- [ ] T094-METRICS Track automation percentage (SC-005: 95% without human intervention)
- [ ] T095-METRICS Add metrics dashboard to Dashboard.md
```
**Time required**: ~3-4 hours

**Option B: Revise Success Criteria to Match Implementation (RECOMMENDED)**
Update spec.md success criteria:
```markdown
# Keep these (already implemented):
- SC-001: CEO briefing generation <10 min ✅ (T088 validates)
- SC-003: Social posts <5 min ✅ (T088 validates)
- SC-006: 100% logging completeness ✅ (T007 implements)
- SC-007: 90% error recovery ✅ (T067-T078 implement)

# Revise these to be qualitative:
- SC-002: System implements health monitoring and auto-restart for critical services
- SC-004: System queues operations during Odoo outages and retries when recovered
- SC-005: System automates routine operations with approval workflows for sensitive actions
```
**Time saved**: ~3-4 hours
**Risk**: Low (still delivers Gold Tier value)

### Recommended: **Option B**

---

## Issue H1: FR-014 (Cross-Domain Integration)

### Recommended Action

**Simplify and Document** - No new tasks needed!

Update spec.md FR-014:
```markdown
- FR-014: System MUST maintain unified task orchestration across personal (Gmail, WhatsApp) and business (Odoo, social media) domains via shared AI_Employee/Needs_Action/ inbox (satisfied by existing orchestrator-watcher architecture)
```

Add to plan.md Technical Context:
```markdown
**Cross-Domain Integration**: The orchestrator.py coordinates all watchers (personal: gmail_watcher, whatsapp_watcher; business: odoo actions, social media workflows) feeding into a unified Obsidian vault. This provides automatic cross-domain integration - a task from Gmail can trigger an Odoo invoice creation, and both updates appear in the same Dashboard.md. No additional implementation required.
```

**Time required**: 15 minutes (documentation only)
**Priority**: HIGH (removes ambiguity)

---

## Total Time Impact

### Minimal Path (Recommended):
- C2 (Dry Run): ~2-3 hours
- C1 (Remove Agent Skills): ~15 minutes
- C3 (Revise Success Criteria): ~15 minutes
- H1 (Document Cross-Domain): ~15 minutes

**Total: ~3-4 hours additional work**

### Maximal Path (If judge requires everything):
- C2 (Dry Run): ~2-3 hours
- C1 (Implement Agent Skills): ~4-6 hours
- C3 (Add Metrics): ~3-4 hours
- H1 (Document): ~15 minutes

**Total: ~10-14 hours additional work**

---

## Recommended Execution Order

1. **Now**: Update spec.md to remove/revise FR-013, FR-014, and success criteria (30 min)
2. **Next**: Add dry_run tasks to tasks.md (15 min)
3. **Then**: Re-run `/sp.analyze` to verify all CRITICAL issues resolved
4. **Finally**: Proceed to `/sp.implement` with confidence

---

## Approval Needed

Please confirm your choice:
- [ ] Option A paths (minimal scope, faster completion)
- [ ] Option B paths (full implementation, longer timeline)
- [ ] Mixed approach (specify which)

Once confirmed, I can update the spec, plan, and tasks files accordingly.
