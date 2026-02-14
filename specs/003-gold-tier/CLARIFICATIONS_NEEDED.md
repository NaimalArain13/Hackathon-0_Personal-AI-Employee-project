# Gold Tier Clarification Questions

## FR-014: Cross-Domain Integration

**Current requirement**: "System MUST maintain cross-domain integration between personal and business affairs"

### Clarification Questions:

1. **Gmail → Odoo Integration**: When a customer inquiry arrives via Gmail, should the AI automatically create an Odoo invoice draft?
   - Option A: Yes, create draft invoices from email requests ✔
   - Option B: No, keep email and accounting separate
   - Option C: Only for specific email patterns (e.g., subject contains "invoice")

2. **WhatsApp → Social Media Integration**: Should business updates posted to social media also be sent as WhatsApp status updates?
   - Option A: Yes, auto-sync business content to WhatsApp status ✔
   - Option B: No, separate channels
   - Option C: Only for major announcements

3. **Odoo → Gmail Integration**: Should completed Odoo invoices automatically trigger thank-you emails to customers?
   - Option A: Yes, send automated receipts/confirmations 
   - Option B: No, manual email only ✔
   - Option C: Only for amounts above certain threshold

4. **CEO Briefing Data Sources**: Should the weekly CEO briefing pull data from BOTH personal (Gmail unread count, WhatsApp message volume) AND business (Odoo revenue, social media engagement)?
   - Option A: Yes, unified dashboard with all metrics
   - Option B: No, business metrics only (as currently specified) ✔
   - Option C: Separate sections for personal vs. business

5. **Shared Task Context**: Should tasks identified in personal communications (Gmail/WhatsApp) appear in business project tracking?
   - Option A: Yes, all tasks unified in AI_Employee/Needs_Action/ ✔
   - Option B: No, separate personal/business task folders
   - Option C: Flag personal tasks differently in shared folder

### Recommendation

If unsure, **Option D**: Remove FR-014 and replace with:
- "System maintains unified task inbox (AI_Employee/Needs_Action/) accepting inputs from all channels (personal and business)"
- This is ALREADY IMPLEMENTED by the existing watcher architecture from Bronze/Silver Tier

The existing orchestrator.py already provides cross-domain integration via the unified Needs_Action folder!
