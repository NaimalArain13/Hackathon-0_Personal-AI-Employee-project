# Facebook MCP Server API Contract

**Version**: 1.0.0
**Service**: Facebook Graph API v19.0 Integration
**Transport**: MCP stdio (command-line)
**Authentication**: Facebook Page Access Token (OAuth 2.0)

---

## 💰 Cost & Free Tier

**IMPORTANT: Facebook Graph API is 100% FREE for standard use cases**

- ✅ **No usage fees** for posting to pages
- ✅ **No usage fees** for reading insights
- ✅ **No subscription required**
- ✅ Free rate limits: 200 calls/hour (sufficient for business needs)
- ⚠️ Only Facebook Ads API and Marketing API have paid tiers (not used in Gold Tier)

**What's Free:**
- Page posting and management
- Insights and analytics
- Page access tokens (non-expiring)
- All features used in Gold Tier

**What's Paid (NOT used):**
- Facebook Ads campaigns (not in scope)
- WhatsApp Business API (large scale)
- Advanced Marketing API features

---

## Tools Provided

### 1. `facebook_create_post`

Create a post on a Facebook Page.

**Parameters**:
```json
{
  "message": {
    "type": "string",
    "description": "Post content text",
    "required": true,
    "maxLength": 63206
  },
  "link": {
    "type": "string",
    "format": "uri",
    "description": "Optional URL to attach",
    "required": false
  },
  "photo_url": {
    "type": "string",
    "format": "uri",
    "description": "Optional image URL",
    "required": false
  },
  "scheduled_publish_time": {
    "type": "integer",
    "description": "Unix timestamp for scheduled post (requires publish_pages permission)",
    "required": false
  },
  "dry_run": {
    "type": "boolean",
    "description": "If true, validate but don't post",
    "default": true
  }
}
```

**Returns**:
```json
{
  "status": "success | dry_run | error",
  "post_id": "string | null",
  "post_url": "string | null",
  "message": "string"
}
```

**Errors**:
- `INVALID_TOKEN`: Access token expired or invalid
- `PERMISSION_DENIED`: Missing required permissions (pages_manage_posts)
- `RATE_LIMIT_EXCEEDED`: Too many requests (200/hour limit)
- `INVALID_MEDIA_URL`: photo_url not accessible
- `MESSAGE_TOO_LONG`: Exceeds 63,206 character limit
- `API_ERROR`: Facebook API returned error

**Side Effects**:
- If `dry_run = false`: Creates post on Facebook Page
- If `scheduled_publish_time` set: Post scheduled for future publication

**Idempotency**: NOT idempotent (creates duplicate posts if called multiple times with same content)

---

### 2. `facebook_get_page_insights`

Get insights/metrics for the Facebook Page.

**Parameters**:
```json
{
  "metrics": {
    "type": "array",
    "items": {
      "type": "string",
      "enum": ["page_impressions", "page_engaged_users", "page_post_engagements", "page_fans"]
    },
    "default": ["page_impressions", "page_engaged_users"]
  },
  "period": {
    "type": "string",
    "enum": ["day", "week", "days_28"],
    "default": "week"
  }
}
```

**Returns**:
```json
{
  "status": "success | error",
  "insights": {
    "metric_name": {
      "value": "integer",
      "period": "string",
      "title": "string",
      "description": "string"
    }
  },
  "message": "string"
}
```

**Errors**:
- `INVALID_TOKEN`
- `PERMISSION_DENIED`: Missing read_insights permission
- `API_ERROR`

**Side Effects**: None (read-only)

**Idempotency**: Idempotent (read-only)

---

### 3. `facebook_delete_post`

Delete a post from the Facebook Page.

**Parameters**:
```json
{
  "post_id": {
    "type": "string",
    "description": "Facebook post ID",
    "required": true
  }
}
```

**Returns**:
```json
{
  "status": "success | error",
  "message": "string"
}
```

**Errors**:
- `POST_NOT_FOUND`: post_id doesn't exist or already deleted
- `PERMISSION_DENIED`: No permission to delete this post
- `INVALID_TOKEN`
- `API_ERROR`

**Side Effects**:
- Permanently deletes the post from Facebook

**Idempotency**: Idempotent (subsequent calls return success if already deleted)

---

### 4. `facebook_get_post`

Get details of a specific post.

**Parameters**:
```json
{
  "post_id": {
    "type": "string",
    "required": true
  },
  "fields": {
    "type": "array",
    "items": {
      "type": "string",
      "enum": ["message", "created_time", "permalink_url", "full_picture", "likes.summary(true)", "comments.summary(true)", "shares"]
    },
    "default": ["message", "created_time", "permalink_url"]
  }
}
```

**Returns**:
```json
{
  "status": "success | error",
  "post": {
    "id": "string",
    "message": "string",
    "created_time": "string (ISO 8601)",
    "permalink_url": "string",
    "likes_count": "integer",
    "comments_count": "integer",
    "shares_count": "integer"
  },
  "message": "string"
}
```

**Errors**:
- `POST_NOT_FOUND`
- `INVALID_TOKEN`
- `PERMISSION_DENIED`
- `API_ERROR`

**Side Effects**: None (read-only)

**Idempotency**: Idempotent (read-only)

---

## Configuration (via .mcp.json)

```json
{
  "mcpServers": {
    "facebook": {
      "command": "python",
      "args": [".claude/mcp-servers/facebook-mcp/mcp_server_facebook.py"],
      "env": {
        "FACEBOOK_PAGE_TOKEN": "${FACEBOOK_PAGE_TOKEN}",
        "FACEBOOK_PAGE_ID": "${FACEBOOK_PAGE_ID}"
      }
    }
  }
}
```

**Environment Variables** (.env):
```bash
# Obtain from Meta for Developers: https://developers.facebook.com/apps/
FACEBOOK_PAGE_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Long-lived page access token
FACEBOOK_PAGE_ID=123456789012345                     # Facebook Page ID
```

---

## Authentication Setup

### Step 1: Create Facebook App
1. Go to https://developers.facebook.com/apps/
2. Create new app → Business → App Name
3. Add "Facebook Login" product

### Step 2: Get User Access Token
1. Use Graph API Explorer: https://developers.facebook.com/tools/explorer/
2. Select your app
3. Request permissions: `pages_manage_posts`, `pages_read_engagement`, `read_insights`
4. Generate token

### Step 3: Exchange for Long-Lived Token
```bash
curl -i -X GET "https://graph.facebook.com/v19.0/oauth/access_token?
  grant_type=fb_exchange_token&
  client_id={app-id}&
  client_secret={app-secret}&
  fb_exchange_token={short-lived-token}"
```

### Step 4: Get Page Access Token
```bash
curl -i -X GET "https://graph.facebook.com/v19.0/me/accounts?
  access_token={long-lived-user-token}"
```

Use the `access_token` from the desired page (this token doesn't expire).

---

## Error Handling

### Retry Policy
- **Rate Limit Errors**: Wait and retry after cooldown period (exponential backoff)
- **Token Errors**: NO retry (requires re-authentication)
- **Network Errors**: Retry with exponential backoff (max 5 attempts)
- **Post Creation**: NO auto-retry (destructive operation per Principle X)

### Circuit Breaker
- **Threshold**: 5 failures in 60 seconds
- **Open Duration**: 30 seconds
- **Half-Open Test**: 1 request

### Rate Limits
- **Page Posts**: 200 calls per hour per user
- **Insight Requests**: 200 calls per hour per user
- **Post Reads**: No specific limit (standard Graph API limits apply)

**Rate Limit Handling**: Respect `X-Business-Use-Case-Usage` header; back off when approaching limits.

---

## Logging

All operations logged to `/Vault/Logs/YYYY-MM-DD.json`:
```json
{
  "timestamp": "2026-02-11T10:30:00.123Z",
  "action": "facebook_create_post",
  "actor": "facebook-mcp",
  "parameters": {
    "message_hash": "sha256:abc123...",
    "has_photo": true,
    "scheduled": false,
    "dry_run": false
  },
  "result": {
    "status": "success",
    "post_id": "123456789_987654321",
    "post_url": "https://facebook.com/..."
  },
  "approval_status": "auto_approved",
  "duration_ms": 1823
}
```

**Note**: Log message hash, not full content (privacy).

---

## Testing

### Unit Tests
- Mock Facebook Graph API responses
- Test parameter validation
- Test error handling (rate limits, token expiration)

### Integration Tests
- Requires test Facebook Page and app
- Test post creation (dry_run and real)
- Test scheduled posts
- Test insights retrieval

### Test Account Setup
1. Create Facebook test app: https://developers.facebook.com/apps/
2. Create test page for posting
3. Use test page token for integration tests
4. Clean up test posts after test runs

---

## Security Considerations

1. **Token Security**: Never log full tokens; use env vars only
2. **Content Validation**: Sanitize user input before posting
3. **Approval Workflow**: Scheduled posts auto-approved; replies require human approval
4. **Rate Limiting**: Respect Facebook limits to avoid account suspension
5. **Audit Trail**: All posts logged with approval status

---

## Approval Workflow Integration

### Auto-Approve (Principle II)
- Scheduled posts (business content)
- Posts without replies or direct engagement

### Require Approval
- Reply to comments (not implemented in Gold Tier)
- Direct messages (not implemented in Gold Tier)
- Posts with sensitive content (detected by `sensitive_content_detector.py`)

---

## Versioning

**Current**: 1.0.0
**Graph API Version**: v19.0 (will upgrade as Facebook releases new versions)
**Breaking Changes**: Major version increment

---

## Future Enhancements (Out of Scope for Gold Tier)

- Comment and reply management
- Story posting
- Video uploads
- Live video streaming
- Ad campaign management
- Audience insights and demographics
