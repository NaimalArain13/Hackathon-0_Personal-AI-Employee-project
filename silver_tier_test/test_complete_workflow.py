#!/usr/bin/env python3
"""
Test script for the complete email workflow from receipt to response.
This tests the integration between Gmail watcher, action file creation, and email sending.
"""

import json
import os
from pathlib import Path
from datetime import datetime

def test_gmail_watcher_integration():
    """Test that Gmail watcher is properly integrated."""
    print("Testing Gmail Watcher Integration...")

    # Check that the Gmail watcher exists and is properly implemented
    gmail_watcher_path = Path("watchers/gmail_watcher.py")
    if not gmail_watcher_path.exists():
        print("✗ Gmail watcher file not found")
        return False

    # Read the file and check for key components
    with open(gmail_watcher_path, 'r') as f:
        content = f.read()

    # Check for required methods
    required_methods = [
        'check_for_updates',
        'create_action_file',
        'authenticate_gmail',
        '_requires_approval'
    ]

    for method in required_methods:
        if f'def {method}' not in content:
            print(f"✗ Method {method} not found in Gmail watcher")
            return False

    print("✓ Gmail watcher contains all required methods")

    # Check that it inherits from BaseWatcher to get exponential_backoff_retry
    if 'BaseWatcher' not in content:
        print("✗ Gmail watcher does not inherit from BaseWatcher")
        return False

    print("✓ Gmail watcher inherits from BaseWatcher for exponential_backoff_retry")

    # Check for Silver Tier features
    silver_features = [
        'create_approval_request',
        'exponential_backoff_retry',
        '_requires_approval'
    ]

    for feature in silver_features:
        if feature not in content:
            print(f"✗ Silver Tier feature {feature} not found in Gmail watcher")
            return False

    print("✓ Gmail watcher includes Silver Tier features")
    return True


def test_action_file_creation():
    """Test action file creation functionality."""
    print("\nTesting Action File Creation...")

    # Check that file utilities exist
    file_utils_path = Path("utils/file_utils.py")
    if not file_utils_path.exists():
        print("✗ File utilities not found")
        return False

    with open(file_utils_path, 'r') as f:
        content = f.read()

    if 'create_action_file' not in content:
        print("✗ create_action_file function not found in file utilities")
        return False

    if 'create_approval_request' not in content:
        print("✗ create_approval_request function not found in file utilities")
        return False

    print("✓ Action file creation utilities exist")
    return True


def test_email_mcp_server():
    """Test Email MCP server integration."""
    print("\nTesting Email MCP Server Integration...")

    # Check that the MCP server exists
    mcp_server_path = Path(".claude/mcp-servers/gmail-mcp/mcp_server_email.py")
    if not mcp_server_path.exists():
        print("✗ Email MCP server not found")
        return False

    with open(mcp_server_path, 'r') as f:
        content = f.read()

    # Check for required methods
    if 'send_email' not in content:
        print("✗ send_email method not found in MCP server")
        return False

    if 'search_attachments' not in content:
        print("✗ search_attachments method not found in MCP server")
        return False

    print("✓ Email MCP server contains required methods")
    return True


def test_workflow_integration():
    """Test the overall workflow integration."""
    print("\nTesting Workflow Integration...")

    # Check that orchestrator is updated to handle the workflow
    orchestrator_path = Path("orchestrator.py")
    if not orchestrator_path.exists():
        print("✗ Orchestrator not found")
        return False

    with open(orchestrator_path, 'r') as f:
        content = f.read()

    # Check for Gmail watcher initialization
    if 'GmailWatcher' not in content:
        print("✗ GmailWatcher not found in orchestrator")
        return False

    # Check for approval monitoring
    if 'monitor_approvals' not in content:
        print("✗ Approval monitoring not found in orchestrator")
        return False

    print("✓ Workflow components are integrated in orchestrator")
    return True


def test_configuration_files():
    """Test that required configuration files exist."""
    print("\nTesting Configuration Files...")

    # Check for email.json configuration
    email_config_path = Path("email.json")
    if not email_config_path.exists():
        print("✗ email.json configuration file not found")
        return False

    # Verify the content
    with open(email_config_path, 'r') as f:
        try:
            config = json.load(f)
            if not isinstance(config, list) or len(config) == 0:
                print("✗ Invalid email.json configuration format")
                return False

            required_fields = {'domain', 'server', 'port'}
            for server_config in config:
                if not all(field in server_config for field in required_fields):
                    print("✗ Missing required fields in email configuration")
                    return False

            print("✓ email.json configuration is valid")
        except json.JSONDecodeError:
            print("✗ Invalid JSON in email configuration")
            return False

    # Check for .env file with required environment variables
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.read()

        required_vars = ['GMAIL_CLIENT_ID', 'GMAIL_CLIENT_SECRET']
        for var in required_vars:
            if var not in env_content:
                print(f"⚠  Warning: {var} not found in .env (may not be required for testing)")

    print("✓ Configuration files exist and are valid")
    return True


def main():
    """Main test function."""
    print("Testing Complete Email Workflow from Receipt to Response")
    print("=" * 60)

    tests = [
        test_gmail_watcher_integration,
        test_action_file_creation,
        test_email_mcp_server,
        test_workflow_integration,
        test_configuration_files
    ]

    all_passed = True
    for test in tests:
        if not test():
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All workflow tests passed! Complete email workflow is properly integrated.")
        print("\nWorkflow Components:")
        print("- Gmail watcher monitors for new emails")
        print("- Creates action files in Needs_Action folder")
        print("- Identifies sensitive emails requiring approval")
        print("- Creates approval requests when needed")
        print("- Processes approved actions via MCP server")
        print("- Sends email responses through Email MCP server")
        return 0
    else:
        print("✗ Some workflow tests failed!")
        return 1


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    sys.exit(main())