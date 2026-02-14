# Cross-Domain Integration Tasks (FR-014)

Based on clarification responses, FR-014 requires these implementations:

## Phase 9: Cross-Domain Integration Workflows (FR-014)

**Goal**: Connect personal and business systems for automated cross-domain workflows

### Task Group 1: Gmail → Odoo Integration

**User Selection**: "When a customer inquiry arrives via Gmail, create draft invoices automatically"

Add these tasks after Phase 6 (Error Handling) completion:

```markdown
- [ ] T091 [US-XD1] Create gmail_to_odoo_parser.py in utils/ to detect invoice requests in emails
- [ ] T092 [US-XD1] Implement email pattern matching for invoice triggers (keywords: "invoice", "quote", "bill", customer name patterns)
- [ ] T093 [US-XD1] Extract invoice details from email body (customer name, amount, line items, due date)
- [ ] T094 [US-XD1] Integrate gmail_watcher.py with odoo_client.py to create draft invoices
- [ ] T095 [US-XD1] Add approval workflow: draft invoice → Pending_Approval/ → user confirms → Odoo API call
- [ ] T096 [US-XD1] Add structured logging for cross-domain Gmail→Odoo actions
```

**Acceptance Criteria**:
- Given: Customer sends email with subject "Please send invoice for Project X - $500"
- When: gmail_watcher processes the email
- Then: Draft invoice created in Pending_Approval/INVOICE_draft_YYYY-MM-DD.md with extracted details
- And: User approves → invoice created in Odoo → confirmation email sent

---

### Task Group 2: Social Media → WhatsApp Status Integration

**User Selection**: "Auto-sync business content to WhatsApp status updates"

Add these tasks after Phase 4 (Social Media) completion:

```markdown
- [ ] T097 [US-XD2] Extend social_media_manager.py to support WhatsApp status as additional target
- [ ] T098 [US-XD2] Create whatsapp_status_publisher.py in utils/ using WhatsApp Business API
- [ ] T099 [US-XD2] Add configuration flag: sync_to_whatsapp_status (default: true for business posts)
- [ ] T100 [US-XD2] Implement post transformation: social media content → WhatsApp status format (text-only, max 700 chars)
- [ ] T101 [US-XD2] Add cross-posting logic: when social media post approved → also post to WhatsApp status
- [ ] T102 [US-XD2] Add structured logging for cross-domain Social→WhatsApp actions
```

**Note**: WhatsApp Status API requires WhatsApp Business API access (see: https://developers.facebook.com/docs/whatsapp/business-management-api/status)

**Acceptance Criteria**:
- Given: Social media post approved in AI_Employee/Approved/
- When: social_media_manager publishes to Facebook/Instagram/Twitter
- Then: Same content automatically posted to WhatsApp Status
- And: All posts logged with cross-domain tag

---

### Task Group 3: Shared Task Context (Answer Question 5)

**Please select**:
- Option A: All tasks unified in AI_Employee/Needs_Action/ (current architecture)
- Option B: Separate personal/business task folders
- Option C: Flag personal tasks differently in shared folder

**Recommendation**: **Option A** - Already implemented by orchestrator.py. No new tasks needed.

---

## Updated Task Dependencies

### New Prerequisites
- **T091-T096 (Gmail→Odoo)**: Depends on Phase 3 (US2 - Odoo) completion
- **T097-T102 (Social→WhatsApp)**: Depends on Phase 4 (US3 - Social Media) completion

### Execution Order
```
Phase 1-2: Setup + Foundational
  ↓
Phase 3: Odoo Integration (US2)
  ↓
Phase 4: Social Media (US3)
  ↓
Phase 5: Autonomous Management (US1)
  ↓
Phase 6: Error Handling (US4)
  ↓
Phase 9: Cross-Domain Integration (NEW - FR-014)
  ↓  T091-T096: Gmail→Odoo
  ↓  T097-T102: Social→WhatsApp
  ↓
Phase 7: Polish
```

---

## Time Impact

**Additional Implementation Time**:
- Gmail→Odoo parser and workflow: ~3-4 hours
- Social→WhatsApp status integration: ~2-3 hours (if WhatsApp Business API already configured)
- **Total: ~5-7 hours additional work**

**Note**: WhatsApp Business API setup may require additional time for:
- Business verification with Meta
- API access approval
- Webhook configuration

If WhatsApp Business API is not yet configured, consider:
- **Option 1**: Implement Gmail→Odoo only (3-4 hours)
- **Option 2**: Replace WhatsApp status with simpler notification (e.g., send message to personal WhatsApp instead of status)

---

## Updated FR-014 Definition

Update spec.md with concrete definition:

```markdown
- FR-014: System MUST implement cross-domain automation workflows:
  - Gmail invoice requests automatically create draft Odoo invoices (requires approval)
  - Social media business posts automatically sync to WhatsApp status updates
  - All cross-domain actions logged with domain linkage for audit trail
```

---

## Next Steps

1. **Complete Question 5** in CLARIFICATIONS_NEEDED.md (Shared Task Context)
2. **Decide on WhatsApp Business API** availability:
   - If available: Implement T097-T102
   - If not available: Simplify to notification-only
3. **Add T091-T102 to tasks.md** in Phase 9 section
4. **Update spec.md FR-014** with concrete definition above
5. **Re-run `/sp.analyze`** to verify all issues resolved

Would you like me to:
- A) Add these tasks directly to tasks.md now
- B) Wait for you to answer Question 5 first
- C) Simplify cross-domain to just Gmail→Odoo (skip WhatsApp status)
