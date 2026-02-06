#!/usr/bin/env python3
"""
Test script for send_email functionality with multiple recipients and attachments.
"""

import json
import sys
from pathlib import Path
from pydantic import ValidationError

# Add the MCP server path to sys.path to import the module
sys.path.insert(0, str(Path("./.claude/mcp-servers/gmail-mcp")))
from mcp_server_email import SendEmailRequest


def test_multiple_recipients():
    """Test send_email with multiple recipients."""
    print("Testing send_email with multiple recipients...")

    # Valid request with multiple recipients
    request_data = {
        "receiver": ["user1@example.com", "user2@example.com", "user3@example.com"],
        "body": "This is a test email with multiple recipients.",
        "subject": "Test: Multiple Recipients",
        "attachments": []
    }

    try:
        request = SendEmailRequest(**request_data)
        print(f"✓ Successfully created request with {len(request.receiver)} recipients")
        assert len(request.receiver) == 3
        assert request.receiver == ["user1@example.com", "user2@example.com", "user3@example.com"]
        print("✓ Multiple recipients validated correctly")
    except ValidationError as e:
        print(f"✗ Validation failed: {e}")
        return False

    return True


def test_various_attachments():
    """Test send_email with various attachment types."""
    print("\nTesting send_email with various attachment types...")

    # Test with different attachment types
    attachment_types = [
        ["document.pdf"],
        ["image.jpg", "photo.png"],
        ["spreadsheet.xlsx", "presentation.pptx", "archive.zip"],
        ["document.docx", "data.csv", "config.json", "readme.md"]
    ]

    for attachments in attachment_types:
        request_data = {
            "receiver": ["test@example.com"],
            "body": "Email with attachments.",
            "subject": "Test: Attachments",
            "attachments": attachments
        }

        try:
            request = SendEmailRequest(**request_data)
            print(f"✓ Successfully validated request with {len(request.attachments or [])} attachments: {request.attachments}")
        except ValidationError as e:
            print(f"✗ Validation failed for attachments {attachments}: {e}")
            return False

    return True


def test_no_attachments():
    """Test send_email without attachments."""
    print("\nTesting send_email without attachments...")

    request_data = {
        "receiver": ["test@example.com"],
        "body": "Email without attachments.",
        "subject": "Test: No Attachments",
        "attachments": None  # Should be optional
    }

    try:
        request = SendEmailRequest(**request_data)
        print("✓ Successfully created request without attachments")
        assert request.attachments is None
        print("✓ Attachments field correctly handled as optional")
    except ValidationError as e:
        print(f"✗ Validation failed for request without attachments: {e}")
        return False

    return True


def test_required_fields():
    """Test that required fields are enforced."""
    print("\nTesting required fields enforcement...")

    # Test missing receiver
    request_data = {
        "body": "Missing receiver",
        "subject": "Test",
        "attachments": []
    }

    try:
        request = SendEmailRequest(**request_data)
        print("✗ Should have failed validation for missing receiver")
        return False
    except ValidationError:
        print("✓ Correctly rejected request missing required 'receiver' field")

    # Test missing body
    request_data = {
        "receiver": ["test@example.com"],
        "subject": "Test",
        "attachments": []
    }

    try:
        request = SendEmailRequest(**request_data)
        print("✗ Should have failed validation for missing body")
        return False
    except ValidationError:
        print("✓ Correctly rejected request missing required 'body' field")

    # Test missing subject
    request_data = {
        "receiver": ["test@example.com"],
        "body": "Test body",
        "attachments": []
    }

    try:
        request = SendEmailRequest(**request_data)
        print("✗ Should have failed validation for missing subject")
        return False
    except ValidationError:
        print("✓ Correctly rejected request missing required 'subject' field")

    return True


def test_edge_cases():
    """Test edge cases for send_email functionality."""
    print("\nTesting edge cases...")

    # Empty receiver list
    request_data = {
        "receiver": [],
        "body": "Empty receivers",
        "subject": "Test",
        "attachments": []
    }

    try:
        request = SendEmailRequest(**request_data)
        print("✗ Should have failed validation for empty receiver list")
        return False
    except ValidationError:
        print("✓ Correctly rejected request with empty receiver list")

    # Very long subject and body
    request_data = {
        "receiver": ["test@example.com"],
        "body": "A" * 10000,  # Very long body
        "subject": "B" * 1000,  # Very long subject
        "attachments": ["test.pdf"]
    }

    try:
        request = SendEmailRequest(**request_data)
        print("✓ Handled request with very long subject and body")
    except ValidationError as e:
        print(f"✗ Failed to handle long content: {e}")
        return False

    return True


def main():
    """Main test function."""
    print("Testing send_email functionality with multiple recipients and attachments")
    print("=" * 70)

    tests = [
        test_multiple_recipients,
        test_various_attachments,
        test_no_attachments,
        test_required_fields,
        test_edge_cases
    ]

    all_passed = True
    for test in tests:
        if not test():
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("✓ All send_email functionality tests passed!")
        print("\nFeatures tested:")
        print("- Multiple recipients support")
        print("- Various attachment types")
        print("- Optional attachments")
        print("- Required field validation")
        print("- Edge cases handling")
        return 0
    else:
        print("✗ Some send_email functionality tests failed!")
        return 1


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    sys.exit(main())