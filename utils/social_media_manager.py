#!/usr/bin/env python3
"""
Social Media Manager
====================

Unified interface for managing social media posts across Facebook, Instagram, and Twitter.

Responsibilities:
- Unified posting interface across all platforms
- Approval workflow integration (auto-approve scheduled, require approval for replies/DMs)
- Content validation (character limits, media requirements) per platform
- Structured logging for all social media operations
- Error handling with retry logic for transient failures
- Dry-run mode enforcement (Constitutional Principle III)

Constitutional Requirements:
- Principle II: Explicit user approval for sensitive posts
- Principle III: Default dry-run mode (default: true)
- Principle IX: Comprehensive action logging
- Principle X: No auto-retry on destructive operations (post creation)
"""

import os
import re
import json
import logging
import hashlib
import subprocess
from typing import Any, Optional, Dict, List
from datetime import datetime
from pathlib import Path
from enum import Enum

# Import utilities
try:
    from utils.setup_logger import log_action
    from utils.sensitive_content_detector import detect_sensitive_content
    from utils.retry_handler import retry_with_backoff, CircuitBreaker
except ImportError:
    # Fallback if imports fail
    def log_action(*args, **kwargs):
        pass
    def detect_sensitive_content(content):
        return {"is_sensitive": False, "reasons": []}
    class CircuitBreaker:
        def __init__(self, *args, **kwargs):
            pass
        def call(self, func, *args, **kwargs):
            return func(*args, **kwargs)
    def retry_with_backoff(max_attempts=3, backoff_base=2):
        def decorator(func):
            return func
        return decorator


logger = logging.getLogger(__name__)


class Platform(Enum):
    """Supported social media platforms."""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"


class PostType(Enum):
    """Types of social media posts."""
    SCHEDULED = "scheduled"  # Auto-approve
    REPLY = "reply"          # Require approval
    DM = "dm"               # Require approval
    SENSITIVE = "sensitive"  # Require approval


class SocialMediaManager:
    """
    Unified social media manager for all platforms.

    Implements approval workflows, content validation, logging, and error handling.
    """

    def __init__(self, vault_path: str = "AI_Employee"):
        """
        Initialize Social Media Manager.

        Args:
            vault_path: Path to Obsidian vault for approval workflows
        """
        self.vault_path = Path(vault_path)
        self.pending_approval_dir = self.vault_path / "Pending_Approval"
        self.approved_dir = self.vault_path / "Approved"
        self.completed_dir = self.vault_path / "Completed"

        # Ensure directories exist
        self.pending_approval_dir.mkdir(parents=True, exist_ok=True)
        self.approved_dir.mkdir(parents=True, exist_ok=True)
        self.completed_dir.mkdir(parents=True, exist_ok=True)

        # Circuit breakers for each platform (read operations only)
        self.circuit_breakers = {
            Platform.FACEBOOK: CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=30,
                name="facebook"
            ),
            Platform.INSTAGRAM: CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=30,
                name="instagram"
            ),
            Platform.TWITTER: CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=30,
                name="twitter"
            )
        }

        logger.info("Social Media Manager initialized")

    # ==================== Content Validation ====================

    def validate_facebook_content(
        self,
        message: str,
        photo_url: Optional[str] = None,
        link: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate Facebook post content.

        Args:
            message: Post text
            photo_url: Optional photo URL
            link: Optional link URL

        Returns:
            {"valid": bool, "errors": List[str]}
        """
        errors = []

        if not message:
            errors.append("Message text is required for Facebook posts")
        elif len(message) > 63206:
            errors.append(f"Message too long: {len(message)}/63206 characters")

        if photo_url and not photo_url.startswith("https://"):
            errors.append("Photo URL must use HTTPS")

        if link and not link.startswith(("http://", "https://")):
            errors.append("Link must be a valid URL")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def validate_instagram_content(
        self,
        image_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate Instagram post content.

        Args:
            image_url: Image URL (JPEG only, <8MB)
            caption: Post caption

        Returns:
            {"valid": bool, "errors": List[str]}
        """
        errors = []

        if not image_url:
            errors.append("Image URL is required for Instagram posts")
        elif not image_url.startswith("https://"):
            errors.append("Image URL must use HTTPS")
        elif not image_url.lower().endswith((".jpg", ".jpeg")):
            errors.append("Instagram only supports JPEG images (not PNG or other formats)")

        if caption and len(caption) > 2200:
            errors.append(f"Caption too long: {len(caption)}/2200 characters")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def validate_twitter_content(
        self,
        text: str,
        media_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate Twitter tweet content.

        Args:
            text: Tweet text
            media_ids: Optional media attachment IDs

        Returns:
            {"valid": bool, "errors": List[str]}
        """
        errors = []

        if not text:
            errors.append("Tweet text is required")
        elif len(text) > 280:
            errors.append(f"Tweet too long: {len(text)}/280 characters")

        if media_ids and len(media_ids) > 4:
            errors.append(f"Too many media attachments: {len(media_ids)}/4 maximum")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    # ==================== Approval Workflow ====================

    def determine_post_type(
        self,
        platform: Platform,
        content: str,
        is_reply: bool = False,
        is_dm: bool = False
    ) -> PostType:
        """
        Determine post type for approval workflow.

        Args:
            platform: Target platform
            content: Post content
            is_reply: Is this a reply to another post?
            is_dm: Is this a direct message?

        Returns:
            PostType (SCHEDULED, REPLY, DM, or SENSITIVE)
        """
        # Check if content is sensitive
        sensitivity = detect_sensitive_content(content)
        if sensitivity.get("is_sensitive", False):
            return PostType.SENSITIVE

        # Check if it's a DM or reply (require approval)
        if is_dm:
            return PostType.DM
        if is_reply:
            return PostType.REPLY

        # Default: scheduled post (auto-approve)
        return PostType.SCHEDULED

    def requires_approval(self, post_type: PostType) -> bool:
        """
        Check if post type requires human approval.

        Args:
            post_type: Type of post

        Returns:
            True if approval required, False if auto-approve
        """
        # Auto-approve scheduled posts, require approval for replies/DMs/sensitive
        return post_type in [PostType.REPLY, PostType.DM, PostType.SENSITIVE]

    def create_approval_file(
        self,
        platform: Platform,
        content: Dict[str, Any],
        post_type: PostType
    ) -> Path:
        """
        Create approval file in Pending_Approval directory.

        Args:
            platform: Target platform
            content: Post content and metadata
            post_type: Type of post

        Returns:
            Path to approval file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"SOCIAL_MEDIA_{platform.value}_{timestamp}.md"
        filepath = self.pending_approval_dir / filename

        # Create approval file content
        approval_content = f"""---
type: social_media_post
platform: {platform.value}
post_type: {post_type.value}
created: {datetime.now().isoformat()}
status: pending_approval
---

# Social Media Post Approval - {platform.value.title()}

**Post Type**: {post_type.value}
**Requires Approval**: {'YES' if self.requires_approval(post_type) else 'NO'}

## Content

```json
{json.dumps(content, indent=2)}
```

## Instructions

1. Review the content above
2. If approved, move this file to: `Approved/`
3. If rejected, delete this file or move to a rejected folder
4. The system will detect the approval and execute the post

## Approval Status

- [ ] Approved
- [ ] Rejected

---
"""

        filepath.write_text(approval_content)
        logger.info(f"Created approval file: {filepath}")

        return filepath

    # ==================== MCP Integration ====================

    def call_mcp_tool(
        self,
        platform: Platform,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call MCP server tool via stdio protocol.

        Args:
            platform: Target platform
            tool_name: MCP tool name
            arguments: Tool arguments

        Returns:
            Tool result
        """
        # Construct MCP server path
        mcp_server_map = {
            Platform.FACEBOOK: ".claude/mcp-servers/facebook-mcp/mcp_server_facebook.py",
            Platform.INSTAGRAM: ".claude/mcp-servers/instagram-mcp/mcp_server_instagram.py",
            Platform.TWITTER: ".claude/mcp-servers/twitter-mcp/mcp_server_twitter.py"
        }

        mcp_server_path = Path(mcp_server_map[platform])

        if not mcp_server_path.exists():
            return {
                "status": "error",
                "message": f"MCP server not found: {mcp_server_path}"
            }

        # Create MCP request
        request = {
            "tool": tool_name,
            "arguments": arguments
        }

        try:
            # Call MCP server via subprocess
            result = subprocess.run(
                ["python", str(mcp_server_path)],
                input=json.dumps(request) + "\n",
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"MCP server error: {result.stderr}")
                return {
                    "status": "error",
                    "message": f"MCP server failed: {result.stderr}"
                }

            # Parse response
            response = json.loads(result.stdout.strip())
            return response

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "MCP server timed out (30s)"
            }
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Invalid JSON response: {e}"
            }
        except Exception as e:
            logger.error(f"MCP call failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    # ==================== Dry-Run Enforcement ====================

    def validate_dry_run(self, dry_run: bool, approval_status: str) -> Dict[str, Any]:
        """
        Validate dry-run parameter (Constitutional Principle III).

        Args:
            dry_run: Dry-run flag
            approval_status: Approval status ("approved", "auto_approved", "pending")

        Returns:
            {"valid": bool, "message": str}
        """
        # CRITICAL: Reject dry_run=false unless explicitly approved
        if not dry_run and approval_status not in ["approved", "auto_approved"]:
            return {
                "valid": False,
                "message": "dry_run=false requires explicit approval (Constitutional Principle III)"
            }

        return {"valid": True, "message": "Dry-run validation passed"}

    # ==================== Unified Posting Interface ====================

    def post_to_facebook(
        self,
        message: str,
        link: Optional[str] = None,
        photo_url: Optional[str] = None,
        scheduled_publish_time: Optional[int] = None,
        dry_run: bool = True,
        post_type: PostType = PostType.SCHEDULED
    ) -> Dict[str, Any]:
        """
        Post to Facebook with validation and approval workflow.

        Args:
            message: Post content text
            link: Optional URL to attach
            photo_url: Optional image URL
            scheduled_publish_time: Unix timestamp for scheduled post
            dry_run: If True, validate but don't post (default: True)
            post_type: Type of post (for approval workflow)

        Returns:
            Result dict with status, post_id, post_url, message
        """
        start_time = datetime.now()

        # Validate content
        validation = self.validate_facebook_content(message, photo_url, link)
        if not validation["valid"]:
            return {
                "status": "error",
                "post_id": None,
                "post_url": None,
                "message": f"Validation failed: {', '.join(validation['errors'])}"
            }

        # Determine approval status
        approval_status = "auto_approved" if not self.requires_approval(post_type) else "pending"

        # Validate dry-run
        dry_run_check = self.validate_dry_run(dry_run, approval_status)
        if not dry_run_check["valid"]:
            return {
                "status": "error",
                "post_id": None,
                "post_url": None,
                "message": dry_run_check["message"]
            }

        # Call Facebook MCP tool
        arguments = {
            "message": message,
            "link": link,
            "photo_url": photo_url,
            "scheduled_publish_time": scheduled_publish_time,
            "dry_run": dry_run
        }

        result = self.call_mcp_tool(Platform.FACEBOOK, "facebook_create_post", arguments)

        # Log action
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        log_action(
            action="facebook_create_post",
            actor="social_media_manager",
            parameters={
                "message_hash": hashlib.sha256(message.encode()).hexdigest()[:16],
                "has_photo": photo_url is not None,
                "has_link": link is not None,
                "scheduled": scheduled_publish_time is not None,
                "dry_run": dry_run
            },
            result=result,
            approval_status=approval_status,
            duration_ms=duration_ms
        )

        return result

    def post_to_instagram(
        self,
        image_url: str,
        caption: Optional[str] = None,
        location_id: Optional[str] = None,
        user_tags: Optional[List[Dict]] = None,
        dry_run: bool = True,
        post_type: PostType = PostType.SCHEDULED
    ) -> Dict[str, Any]:
        """
        Post to Instagram with validation and approval workflow.

        Args:
            image_url: Publicly accessible image URL (JPEG only, <8MB)
            caption: Post caption
            location_id: Optional Instagram location ID
            user_tags: Tag other Instagram users
            dry_run: If True, create container but don't publish (default: True)
            post_type: Type of post (for approval workflow)

        Returns:
            Result dict with status, container_id, media_id, permalink, message
        """
        start_time = datetime.now()

        # Validate content
        validation = self.validate_instagram_content(image_url, caption)
        if not validation["valid"]:
            return {
                "status": "error",
                "container_id": None,
                "media_id": None,
                "permalink": None,
                "message": f"Validation failed: {', '.join(validation['errors'])}"
            }

        # Determine approval status
        approval_status = "auto_approved" if not self.requires_approval(post_type) else "pending"

        # Validate dry-run
        dry_run_check = self.validate_dry_run(dry_run, approval_status)
        if not dry_run_check["valid"]:
            return {
                "status": "error",
                "container_id": None,
                "media_id": None,
                "permalink": None,
                "message": dry_run_check["message"]
            }

        # Call Instagram MCP tool
        arguments = {
            "image_url": image_url,
            "caption": caption,
            "location_id": location_id,
            "user_tags": user_tags,
            "dry_run": dry_run
        }

        result = self.call_mcp_tool(Platform.INSTAGRAM, "instagram_create_post", arguments)

        # Log action
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        log_action(
            action="instagram_create_post",
            actor="social_media_manager",
            parameters={
                "caption_hash": hashlib.sha256((caption or "").encode()).hexdigest()[:16],
                "image_url_hash": hashlib.sha256(image_url.encode()).hexdigest()[:16],
                "has_location": location_id is not None,
                "has_tags": user_tags is not None,
                "dry_run": dry_run
            },
            result=result,
            approval_status=approval_status,
            duration_ms=duration_ms
        )

        return result

    def post_to_twitter(
        self,
        text: str,
        media_ids: Optional[List[str]] = None,
        poll_options: Optional[List[str]] = None,
        poll_duration_minutes: Optional[int] = None,
        quote_tweet_id: Optional[str] = None,
        reply_to: Optional[str] = None,
        dry_run: bool = True,
        post_type: PostType = PostType.SCHEDULED
    ) -> Dict[str, Any]:
        """
        Post to Twitter with validation and approval workflow.

        Args:
            text: Tweet text content
            media_ids: Media attachment IDs
            poll_options: Poll options
            poll_duration_minutes: Poll duration in minutes
            quote_tweet_id: Tweet ID to quote
            reply_to: Tweet ID to reply to
            dry_run: If True, validate but don't post (default: True)
            post_type: Type of post (for approval workflow)

        Returns:
            Result dict with status, tweet_id, tweet_url, text, message
        """
        start_time = datetime.now()

        # Validate content
        validation = self.validate_twitter_content(text, media_ids)
        if not validation["valid"]:
            return {
                "status": "error",
                "tweet_id": None,
                "tweet_url": None,
                "message": f"Validation failed: {', '.join(validation['errors'])}"
            }

        # Determine approval status (replies require approval)
        if reply_to:
            post_type = PostType.REPLY
        approval_status = "auto_approved" if not self.requires_approval(post_type) else "pending"

        # Validate dry-run
        dry_run_check = self.validate_dry_run(dry_run, approval_status)
        if not dry_run_check["valid"]:
            return {
                "status": "error",
                "tweet_id": None,
                "tweet_url": None,
                "message": dry_run_check["message"]
            }

        # Call Twitter MCP tool
        arguments = {
            "text": text,
            "media_ids": media_ids,
            "poll_options": poll_options,
            "poll_duration_minutes": poll_duration_minutes,
            "quote_tweet_id": quote_tweet_id,
            "reply_to": reply_to,
            "dry_run": dry_run
        }

        result = self.call_mcp_tool(Platform.TWITTER, "twitter_create_tweet", arguments)

        # Log action
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        log_action(
            action="twitter_create_tweet",
            actor="social_media_manager",
            parameters={
                "text_hash": hashlib.sha256(text.encode()).hexdigest()[:16],
                "has_media": media_ids is not None,
                "is_reply": reply_to is not None,
                "is_poll": poll_options is not None,
                "dry_run": dry_run
            },
            result=result,
            approval_status=approval_status,
            duration_ms=duration_ms
        )

        return result

    # ==================== Read Operations (with retry) ====================

    @retry_with_backoff(max_attempts=5, backoff_base=2)
    def get_facebook_insights(
        self,
        metrics: Optional[List[str]] = None,
        period: str = "week"
    ) -> Dict[str, Any]:
        """
        Get Facebook page insights (read operation - can retry).

        Args:
            metrics: Metrics to retrieve
            period: Time period ("day", "week", "days_28")

        Returns:
            Insights data
        """
        cb = self.circuit_breakers[Platform.FACEBOOK]
        return cb.call(
            self.call_mcp_tool,
            Platform.FACEBOOK,
            "facebook_get_page_insights",
            {"metrics": metrics or ["page_impressions", "page_engaged_users"], "period": period}
        )

    @retry_with_backoff(max_attempts=5, backoff_base=2)
    def get_instagram_account_info(
        self,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get Instagram account information (read operation - can retry).

        Args:
            fields: Account fields to retrieve

        Returns:
            Account information
        """
        cb = self.circuit_breakers[Platform.INSTAGRAM]
        return cb.call(
            self.call_mcp_tool,
            Platform.INSTAGRAM,
            "instagram_get_account_info",
            {"fields": fields or ["id", "username", "followers_count", "media_count"]}
        )

    @retry_with_backoff(max_attempts=5, backoff_base=2)
    def get_twitter_user_info(self) -> Dict[str, Any]:
        """
        Get Twitter user information (read operation - can retry).

        Returns:
            User information
        """
        cb = self.circuit_breakers[Platform.TWITTER]
        return cb.call(
            self.call_mcp_tool,
            Platform.TWITTER,
            "twitter_get_user_info",
            {}
        )


# ==================== CLI Interface ====================

def main():
    """CLI interface for testing Social Media Manager."""
    import argparse

    parser = argparse.ArgumentParser(description="Social Media Manager CLI")
    parser.add_argument("--platform", choices=["facebook", "instagram", "twitter"], required=True)
    parser.add_argument("--action", choices=["post", "insights"], required=True)
    parser.add_argument("--text", help="Post text/message/caption")
    parser.add_argument("--image-url", help="Image URL (Instagram)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Dry-run mode (default: true)")

    args = parser.parse_args()

    manager = SocialMediaManager()

    if args.action == "post":
        if args.platform == "facebook":
            result = manager.post_to_facebook(
                message=args.text or "Test post from Social Media Manager",
                dry_run=args.dry_run
            )
        elif args.platform == "instagram":
            if not args.image_url:
                print("Error: --image-url required for Instagram")
                return 1
            result = manager.post_to_instagram(
                image_url=args.image_url,
                caption=args.text,
                dry_run=args.dry_run
            )
        elif args.platform == "twitter":
            result = manager.post_to_twitter(
                text=args.text or "Test tweet from Social Media Manager",
                dry_run=args.dry_run
            )

        print(json.dumps(result, indent=2))

    elif args.action == "insights":
        if args.platform == "facebook":
            result = manager.get_facebook_insights()
        elif args.platform == "instagram":
            result = manager.get_instagram_account_info()
        elif args.platform == "twitter":
            result = manager.get_twitter_user_info()

        print(json.dumps(result, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
