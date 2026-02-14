# Instagram MCP Server API Contract

**Version**: 1.0.0
**Service**: Instagram Graph API Integration (via Facebook)
**Transport**: MCP stdio (command-line)
**Authentication**: Facebook Page Access Token (requires Instagram Business Account)

---

## 💰 Cost & Free Tier

**IMPORTANT: Instagram Graph API is 100% FREE**

- ✅ **No usage fees** for content publishing
- ✅ **No usage fees** for insights and analytics
- ✅ **No subscription required**
- ✅ Instagram Business Account conversion: FREE
- ✅ Facebook Page creation and linking: FREE
- ✅ Free rate limits: 25 posts per 24 hours (sufficient for business needs)

**What's Free:**
- Content publishing (photos)
- Media insights and analytics
- Account information
- All features used in Gold Tier

**What You Need (All Free):**
- Instagram account (free)
- Convert to Business Account (free - no charges)
- Facebook Page (free)
- Facebook Page Access Token (free)

**Not Used (Out of Scope):**
- Instagram Ads (paid, but not in Gold Tier scope)
- Influencer partnership tools (if paid)

---

## Prerequisites

- Instagram Business Account or Instagram Creator Account (FREE conversion)
- Facebook Page connected to Instagram account (FREE)
- Facebook Page Access Token with `instagram_basic`, `instagram_content_publish` permissions (FREE)

---

## Tools Provided

### 1. `instagram_create_post`

Create a photo or video post on Instagram (container-based publishing).

**Parameters**:
```json
{
  "caption": {
    "type": "string",
    "description": "Post caption",
    "required": false,
    "maxLength": 2200
  },
  "image_url": {
    "type": "string",
    "format": "uri",
    "description": "Publicly accessible image URL (JPEG only, <8MB)",
    "required": true
  },
  "location_id": {
    "type": "string",
    "description": "Optional Instagram location ID",
    "required": false
  },
  "user_tags": {
    "type": "array",
    "description": "Tag other Instagram users",
    "items": {
      "username": "string",
      "x": "number (0.0-1.0)",
      "y": "number (0.0-1.0)"
    },
    "required": false
  },
  "dry_run": {
    "type": "boolean",
    "description": "If true, create container but don't publish",
    "default": true
  }
}
```

**Returns**:
```json
{
  "status": "success | dry_run | error",
  "container_id": "string | null",
  "media_id": "string | null",
  "permalink": "string | null",
  "message": "string"
}
```

**Errors**:
- `INVALID_TOKEN`: Access token expired or invalid
- `PERMISSION_DENIED`: Missing required permissions
- `RATE_LIMIT_EXCEEDED`: 25 API calls per 24 hours exceeded
- `INVALID_IMAGE_URL`: Image not accessible or wrong format
- `IMAGE_TOO_LARGE`: Image exceeds 8MB limit
- `CAPTION_TOO_LONG`: Caption exceeds 2,200 characters
- `ACCOUNT_NOT_BUSINESS`: Instagram account is not Business/Creator account
- `API_ERROR`: Instagram API returned error

**Side Effects**:
- If `dry_run = false`:
  1. Creates media container (step 1)
  2. Publishes container to Instagram feed (step 2)
- If `dry_run = true`: Only creates container, doesn't publish

**Idempotency**: NOT idempotent (creates duplicate posts if called multiple times)

**Publishing Flow**:
```
Step 1: Create Container → returns container_id
Step 2: Publish Container → returns media_id
```

---

### 2. `instagram_get_account_info`

Get information about the connected Instagram Business Account.

**Parameters**:
```json
{
  "fields": {
    "type": "array",
    "items": {
      "type": "string",
      "enum": ["id", "username", "name", "profile_picture_url", "followers_count", "follows_count", "media_count"]
    },
    "default": ["id", "username", "followers_count", "media_count"]
  }
}
```

**Returns**:
```json
{
  "status": "success | error",
  "account": {
    "id": "string",
    "username": "string",
    "name": "string",
    "followers_count": "integer",
    "follows_count": "integer",
    "media_count": "integer"
  },
  "message": "string"
}
```

**Errors**:
- `INVALID_TOKEN`
- `PERMISSION_DENIED`
- `API_ERROR`

**Side Effects**: None (read-only)

**Idempotency**: Idempotent (read-only)

---

### 3. `instagram_get_media_insights`

Get insights/metrics for a specific Instagram post.

**Parameters**:
```json
{
  "media_id": {
    "type": "string",
    "description": "Instagram media ID",
    "required": true
  },
  "metrics": {
    "type": "array",
    "items": {
      "type": "string",
      "enum": ["engagement", "impressions", "reach", "saved", "likes", "comments"]
    },
    "default": ["engagement", "impressions", "reach"]
  }
}
```

**Returns**:
```json
{
  "status": "success | error",
  "insights": {
    "engagement": "integer",
    "impressions": "integer",
    "reach": "integer",
    "saved": "integer"
  },
  "message": "string"
}
```

**Errors**:
- `MEDIA_NOT_FOUND`: media_id doesn't exist
- `INSIGHTS_NOT_AVAILABLE`: Insights not yet available (requires 24h after publish)
- `INVALID_TOKEN`
- `PERMISSION_DENIED`
- `API_ERROR`

**Side Effects**: None (read-only)

**Idempotency**: Idempotent (read-only)

---

### 4. `instagram_get_recent_media`

List recent media posts from the Instagram account.

**Parameters**:
```json
{
  "limit": {
    "type": "integer",
    "description": "Number of posts to retrieve",
    "default": 10,
    "maximum": 100
  },
  "fields": {
    "type": "array",
    "items": {
      "type": "string",
      "enum": ["id", "caption", "media_type", "media_url", "permalink", "timestamp", "like_count", "comments_count"]
    },
    "default": ["id", "caption", "media_type", "permalink", "timestamp"]
  }
}
```

**Returns**:
```json
{
  "status": "success | error",
  "media": [
    {
      "id": "string",
      "caption": "string",
      "media_type": "IMAGE | VIDEO | CAROUSEL_ALBUM",
      "permalink": "string",
      "timestamp": "string (ISO 8601)"
    }
  ],
  "count": "integer",
  "message": "string"
}
```

**Errors**:
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
    "instagram": {
      "command": "python",
      "args": [".claude/mcp-servers/instagram-mcp/mcp_server_instagram.py"],
      "env": {
        "FACEBOOK_PAGE_TOKEN": "${FACEBOOK_PAGE_TOKEN}",
        "INSTAGRAM_ACCOUNT_ID": "${INSTAGRAM_ACCOUNT_ID}"
      }
    }
  }
}
```

**Environment Variables** (.env):
```bash
# Same Facebook Page Token as Facebook MCP (if page is connected to IG)
FACEBOOK_PAGE_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Instagram Business Account ID (not username)
# Get via: GET https://graph.facebook.com/v19.0/me/accounts?fields=instagram_business_account
INSTAGRAM_ACCOUNT_ID=17841400123456789
```

---

## Authentication Setup

### Step 1: Convert to Business Account
1. Instagram app → Settings → Account → Switch to Professional Account → Business
2. Or link existing business account to Facebook Page

### Step 2: Link to Facebook Page
1. Instagram app → Settings → Account → Linked Accounts → Facebook
2. Select Facebook Page to connect

### Step 3: Get Instagram Account ID
```bash
# Using Facebook Page Access Token
curl -i -X GET "https://graph.facebook.com/v19.0/{page-id}?fields=instagram_business_account&access_token={page-token}"
```

Returns:
```json
{
  "instagram_business_account": {
    "id": "17841400123456789"
  },
  "id": "123456789012345"
}
```

---

## Error Handling

### Retry Policy
- **Rate Limit Errors**: NO retry; respect 25 posts/24h limit
- **Token Errors**: NO retry (requires re-authentication)
- **Network Errors**: Retry with exponential backoff (max 5 attempts)
- **Post Creation**: NO auto-retry (destructive operation)

### Circuit Breaker
- **Threshold**: 5 failures in 60 seconds
- **Open Duration**: 30 seconds
- **Half-Open Test**: 1 request

### Rate Limits
- **Content Publishing**: 25 API calls per 24 hours per user
- **Read Operations**: Standard Graph API limits (200 calls/hour)

**Note**: Publishing limit is strict; track daily post count to avoid hitting limit.

---

## Image Requirements

### Supported Formats
- **Image**: JPEG only (PNG not supported)
- **Aspect Ratio**:
  - Square: 1:1 (recommended: 1080x1080)
  - Landscape: 1.91:1 (recommended: 1080x566)
  - Portrait: 4:5 (recommended: 1080x1350)
- **File Size**: <8MB
- **Resolution**: Minimum 320px width

### Image Hosting
- Must be publicly accessible via HTTPS
- Must remain accessible until publishing completes
- Consider using temporary URL with expiration after 24h

---

## Logging

All operations logged to `/Vault/Logs/YYYY-MM-DD.json`:
```json
{
  "timestamp": "2026-02-11T10:30:00.123Z",
  "action": "instagram_create_post",
  "actor": "instagram-mcp",
  "parameters": {
    "caption_hash": "sha256:abc123...",
    "image_url_hash": "sha256:def456...",
    "has_location": false,
    "has_tags": false,
    "dry_run": false
  },
  "result": {
    "status": "success",
    "container_id": "17912345678901234",
    "media_id": "17923456789012345",
    "permalink": "https://www.instagram.com/p/ABC123/"
  },
  "approval_status": "auto_approved",
  "duration_ms": 3456
}
```

---

## Testing

### Unit Tests
- Mock Instagram Graph API responses
- Test parameter validation (image format, caption length)
- Test two-step publishing flow

### Integration Tests
- Requires test Instagram Business account
- Test image posting (dry_run and real)
- Test insights retrieval
- Clean up test posts after test runs

### Test Setup
1. Create test Facebook Page
2. Create test Instagram account and convert to Business
3. Link Instagram to Facebook Page
4. Use test credentials for integration tests

---

## Security Considerations

1. **Token Security**: Never log full tokens; use env vars only
2. **Image URLs**: Ensure images don't contain sensitive information
3. **Caption Sanitization**: Validate and sanitize captions before posting
4. **Approval Workflow**: Scheduled posts auto-approved; replies require human approval (not implemented in Gold Tier)
5. **Rate Limit Tracking**: Monitor daily post count to avoid suspension

---

## Approval Workflow Integration

### Auto-Approve (Principle II)
- Scheduled posts (business content)
- Feed posts without direct engagement

### Require Approval
- Comments and replies (not implemented in Gold Tier)
- Direct messages (not implemented in Gold Tier)
- Posts with sensitive content

---

## Limitations

### Not Supported in Gold Tier
- Video posts (future enhancement)
- Carousel/album posts (future enhancement)
- Instagram Stories (requires different API)
- Instagram Reels (requires different API)
- Comment management
- Direct messaging

### API Limitations
- 25 posts per 24 hours (strict limit)
- Insights available 24h after publish
- Cannot edit published posts (Instagram limitation)
- Cannot schedule posts (must publish immediately or use third-party scheduler)

---

## Versioning

**Current**: 1.0.0
**Graph API Version**: v19.0
**Breaking Changes**: Major version increment

---

## Future Enhancements (Out of Scope for Gold Tier)

- Video and carousel posts
- Story posting
- Reel creation
- Comment and reply management
- Direct message handling
- Hashtag research and optimization
- Post scheduling (publish at specific time)
