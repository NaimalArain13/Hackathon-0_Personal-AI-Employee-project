# Twitter (X) MCP Server API Contract

**Version**: 1.0.0
**Service**: Twitter API v2 Integration
**Transport**: MCP stdio (command-line)
**Authentication**: OAuth 1.0a (User Context) or OAuth 2.0

---

## 💰 Cost & Free Tier

**Twitter API Essential Access: FREE (with limits)**

- ✅ **Free tier available**: Essential Access (no cost)
- ✅ **50 tweets per 24 hours** (sufficient for scheduled business posting)
- ✅ **1,500 tweets per month** (within free quota)
- ✅ Read access: 100 requests per 15 minutes (free)
- ⚠️ Requires Twitter developer account approval (typically approved within 24-48 hours)

**What's Free (Essential Access):**
- Post tweets (50/day)
- Upload media
- Read user timeline
- Get user information
- All features used in Gold Tier

**Upgrade Tiers (NOT required for Gold Tier):**
- **Basic**: $100/month - 3,000 tweets/month, 10,000 reads/month
- **Pro**: $5,000/month - Higher limits
- **Enterprise**: Custom pricing

**Recommendation for Gold Tier**:
- Use **FREE Essential Access** (50 tweets/day = ~350 tweets/week is more than enough)
- Typical usage: 5-10 tweets per week = well within free limits

---

## Tools Provided

### 1. `twitter_create_tweet`

Create a tweet on Twitter/X.

**Parameters**:
```json
{
  "text": {
    "type": "string",
    "description": "Tweet text content",
    "required": true,
    "maxLength": 280
  },
  "media_ids": {
    "type": "array",
    "description": "Media attachment IDs (up to 4 images or 1 video/GIF)",
    "items": {"type": "string"},
    "maxItems": 4,
    "required": false
  },
  "poll_options": {
    "type": "array",
    "description": "Poll options (2-4 choices)",
    "items": {"type": "string"},
    "minItems": 2,
    "maxItems": 4,
    "required": false
  },
  "poll_duration_minutes": {
    "type": "integer",
    "description": "Poll duration in minutes (5-10080 = 7 days)",
    "minimum": 5,
    "maximum": 10080,
    "required": false
  },
  "quote_tweet_id": {
    "type": "string",
    "description": "Tweet ID to quote",
    "required": false
  },
  "reply_to": {
    "type": "string",
    "description": "Tweet ID to reply to",
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
  "tweet_id": "string | null",
  "tweet_url": "string | null",
  "text": "string",
  "message": "string"
}
```

**Errors**:
- `INVALID_CREDENTIALS`: Authentication failed
- `PERMISSION_DENIED`: Missing required permissions
- `RATE_LIMIT_EXCEEDED`: Tweet creation limit exceeded (see rate limits below)
- `DUPLICATE_TWEET`: Identical tweet posted recently (within ~10 minutes)
- `TEXT_TOO_LONG`: Exceeds 280 characters
- `INVALID_MEDIA_ID`: media_id doesn't exist or expired
- `TWEET_NOT_FOUND`: reply_to or quote_tweet_id doesn't exist
- `API_ERROR`: Twitter API returned error

**Side Effects**:
- If `dry_run = false`: Creates tweet on Twitter/X
- If `reply_to` specified: Creates reply (threaded conversation)

**Idempotency**: Partially idempotent (Twitter prevents exact duplicates within ~10 minutes)

---

### 2. `twitter_upload_media`

Upload an image or video for use in a tweet.

**Parameters**:
```json
{
  "media_url": {
    "type": "string",
    "format": "uri",
    "description": "Publicly accessible media URL",
    "required": true
  },
  "media_type": {
    "type": "string",
    "enum": ["image", "video", "gif"],
    "required": true
  },
  "alt_text": {
    "type": "string",
    "description": "Alt text for accessibility",
    "maxLength": 1000,
    "required": false
  }
}
```

**Returns**:
```json
{
  "status": "success | error",
  "media_id": "string",
  "expires_after_secs": "integer",
  "message": "string"
}
```

**Errors**:
- `INVALID_CREDENTIALS`
- `MEDIA_TOO_LARGE`: Image >5MB or video >512MB
- `UNSUPPORTED_FORMAT`: Media format not supported
- `MEDIA_DOWNLOAD_FAILED`: Cannot download from media_url
- `API_ERROR`

**Side Effects**:
- Uploads media to Twitter; media_id expires after 24 hours if not used

**Idempotency**: NOT idempotent (creates new media_id each time)

---

### 3. `twitter_delete_tweet`

Delete a tweet.

**Parameters**:
```json
{
  "tweet_id": {
    "type": "string",
    "description": "Tweet ID to delete",
    "required": true
  }
}
```

**Returns**:
```json
{
  "status": "success | error",
  "deleted": "boolean",
  "message": "string"
}
```

**Errors**:
- `TWEET_NOT_FOUND`: tweet_id doesn't exist or already deleted
- `PERMISSION_DENIED`: Cannot delete tweets you don't own
- `INVALID_CREDENTIALS`
- `API_ERROR`

**Side Effects**:
- Permanently deletes the tweet

**Idempotency**: Idempotent (subsequent calls return success if already deleted)

---

### 4. `twitter_get_user_tweets`

Get recent tweets from the authenticated user.

**Parameters**:
```json
{
  "max_results": {
    "type": "integer",
    "description": "Number of tweets to retrieve",
    "minimum": 5,
    "maximum": 100,
    "default": 10
  },
  "exclude": {
    "type": "array",
    "description": "Tweet types to exclude",
    "items": {
      "type": "string",
      "enum": ["retweets", "replies"]
    },
    "required": false
  }
}
```

**Returns**:
```json
{
  "status": "success | error",
  "tweets": [
    {
      "id": "string",
      "text": "string",
      "created_at": "string (ISO 8601)",
      "public_metrics": {
        "retweet_count": "integer",
        "reply_count": "integer",
        "like_count": "integer",
        "quote_count": "integer"
      }
    }
  ],
  "count": "integer",
  "message": "string"
}
```

**Errors**:
- `INVALID_CREDENTIALS`
- `PERMISSION_DENIED`
- `API_ERROR`

**Side Effects**: None (read-only)

**Idempotency**: Idempotent (read-only)

---

### 5. `twitter_get_user_info`

Get information about the authenticated user.

**Parameters**: None

**Returns**:
```json
{
  "status": "success | error",
  "user": {
    "id": "string",
    "username": "string",
    "name": "string",
    "description": "string",
    "public_metrics": {
      "followers_count": "integer",
      "following_count": "integer",
      "tweet_count": "integer",
      "listed_count": "integer"
    }
  },
  "message": "string"
}
```

**Errors**:
- `INVALID_CREDENTIALS`
- `API_ERROR`

**Side Effects**: None (read-only)

**Idempotency**: Idempotent (read-only)

---

## Configuration (via .mcp.json)

```json
{
  "mcpServers": {
    "twitter": {
      "command": "python",
      "args": [".claude/mcp-servers/twitter-mcp/mcp_server_twitter.py"],
      "env": {
        "TWITTER_API_KEY": "${TWITTER_API_KEY}",
        "TWITTER_API_SECRET": "${TWITTER_API_SECRET}",
        "TWITTER_ACCESS_TOKEN": "${TWITTER_ACCESS_TOKEN}",
        "TWITTER_ACCESS_SECRET": "${TWITTER_ACCESS_SECRET}",
        "TWITTER_BEARER_TOKEN": "${TWITTER_BEARER_TOKEN}"
      }
    }
  }
}
```

**Environment Variables** (.env):
```bash
# OAuth 1.0a credentials (for posting tweets)
TWITTER_API_KEY=xxxxxxxxxxxxxxxxxxxxx
TWITTER_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWITTER_ACCESS_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWITTER_ACCESS_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OAuth 2.0 Bearer Token (for read-only operations)
TWITTER_BEARER_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Authentication Setup

### Step 1: Create Twitter App
1. Go to https://developer.twitter.com/en/portal/dashboard
2. Create new project and app
3. Note your API Key and API Secret

### Step 2: Generate Access Token
1. In app settings → Keys and Tokens
2. Generate Access Token and Secret
3. Set app permissions to "Read and Write" (or "Read, Write, and Direct Messages")

### Step 3: Get Bearer Token (Optional)
1. In app settings → Keys and Tokens
2. Generate Bearer Token (for read-only operations)

---

## Error Handling

### Retry Policy
- **Rate Limit Errors**: Wait until rate limit resets (use `x-rate-limit-reset` header)
- **Auth Errors**: NO retry (requires credential fix)
- **Network Errors**: Retry with exponential backoff (max 5 attempts)
- **Tweet Creation**: NO auto-retry (could create duplicates)

### Circuit Breaker
- **Threshold**: 5 failures in 60 seconds
- **Open Duration**: 30 seconds
- **Half-Open Test**: 1 request

### Rate Limits (Free Tier - Essential Access)

| Endpoint | Limit | Window |
|----------|-------|--------|
| Tweet creation | 50 tweets | 24 hours |
| Tweet reads | 100 requests | 15 minutes |
| User lookup | 300 requests | 15 minutes |
| Media upload | 300 requests | 15 minutes |

**Note**: Limits vary by access level (Essential, Elevated, Academic). Check current tier limits.

**Rate Limit Headers**:
- `x-rate-limit-limit`: Total requests allowed
- `x-rate-limit-remaining`: Remaining requests
- `x-rate-limit-reset`: Unix timestamp when limit resets

---

## Media Requirements

### Images
- **Formats**: JPEG, PNG, GIF (non-animated)
- **Max Size**: 5MB
- **Max Dimensions**: 8192x8192 pixels
- **Max per Tweet**: 4 images

### Videos
- **Formats**: MP4, MOV
- **Max Size**: 512MB
- **Max Duration**: 2 minutes 20 seconds (140 seconds)
- **Max per Tweet**: 1 video

### GIFs (Animated)
- **Formats**: GIF
- **Max Size**: 15MB
- **Max per Tweet**: 1 GIF

---

## Logging

All operations logged to `/Vault/Logs/YYYY-MM-DD.json`:
```json
{
  "timestamp": "2026-02-11T10:30:00.123Z",
  "action": "twitter_create_tweet",
  "actor": "twitter-mcp",
  "parameters": {
    "text_hash": "sha256:abc123...",
    "has_media": false,
    "is_reply": false,
    "dry_run": false
  },
  "result": {
    "status": "success",
    "tweet_id": "1234567890123456789",
    "tweet_url": "https://twitter.com/user/status/1234567890123456789"
  },
  "approval_status": "auto_approved",
  "duration_ms": 1456
}
```

---

## Testing

### Unit Tests
- Mock Twitter API v2 responses
- Test parameter validation (character limits, media count)
- Test error handling (rate limits, duplicates)

### Integration Tests
- Requires test Twitter account
- Test tweet creation (dry_run and real)
- Test media upload
- Test rate limit handling
- Clean up test tweets after test runs

### Test Setup
1. Create Twitter developer account: https://developer.twitter.com/
2. Create test app with "Read and Write" permissions
3. Use test credentials for integration tests
4. Implement cleanup to delete test tweets

---

## Security Considerations

1. **Credential Security**: Never log API keys/tokens; use env vars only
2. **Content Validation**: Sanitize tweet text before posting
3. **Rate Limit Monitoring**: Track daily tweet count to avoid suspension
4. **Duplicate Prevention**: Check recent tweets before posting
5. **Audit Trail**: All tweets logged with approval status

---

## Approval Workflow Integration

### Auto-Approve (Principle II)
- Scheduled tweets (business content)
- Original posts without replies

### Require Approval
- Replies to other users (not implemented in Gold Tier)
- Direct messages (not implemented in Gold Tier)
- Tweets with sensitive content

---

## Character Count Calculation

Twitter's character counting is complex:
- URLs: Always count as 23 characters (regardless of length)
- Mentions (@username): Count as username length + 1
- Hashtags (#tag): Count as tag length + 1
- Emojis: Count as 2 characters
- Media attachments: Don't count toward character limit

**Implementation**: Use Tweepy's built-in character counting to avoid errors.

---

## Limitations

### Not Supported in Gold Tier
- Direct messages
- Replies to other users (can reply to own tweets for threading)
- Retweets and quote tweets (quote_tweet_id supported but not actively used)
- Likes and bookmarks
- Twitter Spaces
- Twitter Lists

### API Limitations
- 50 tweets per 24 hours (Essential access)
- Media IDs expire after 24 hours
- Cannot edit published tweets (API limitation)
- Duplicate detection window: ~10 minutes

---

## Versioning

**Current**: 1.0.0
**Twitter API Version**: v2
**Breaking Changes**: Major version increment

---

## Future Enhancements (Out of Scope for Gold Tier)

- Thread creation (connected tweets)
- Reply management
- Direct message handling
- Retweet and like functionality
- Advanced search and filtering
- Twitter Analytics integration
- Scheduled tweets (publish at specific time)
- Tweet editing (if Twitter adds API support)
