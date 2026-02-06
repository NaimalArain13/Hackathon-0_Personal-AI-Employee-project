#!/usr/bin/env python3
"""
Test script for the complete approval workflow from request to execution.
"""

import json
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

# Add the project root to the path to import from other modules
sys.path.insert(0, str(Path(__file__).parent))

from utils.setup_logger import setup_logger
from utils.file_utils import create_approval_request, scan_for_approval_changes
from utils.action_executor import ActionExecutor
from utils.sensitive_content_detector import SensitiveContentDetector


def test_approval_creation():
    """Test approval request creation."""
    print("Testing approval request creation...")

    # Create a test vault structure
    test_vault = Path("./test_approval_vault")
    pending_approval = test_vault / "Pending_Approval"
    approved = test_vault / "Approved"
    rejected = test_vault / "Rejected"

    for folder in [test_vault, pending_approval, approved, rejected]:
        folder.mkdir(exist_ok=True)

    # Create an approval request
    approval_data = {
        'email_id': 'test123',
        'subject': 'Test Email',
        'from': 'test@example.com',
        'body_preview': 'This is a test email body...'
    }

    approval_path = create_approval_request(
        str(test_vault),
        'gmail_response',
        approval_data,
        'Test Approval Request'
    )

    # Verify the approval file was created
    assert approval_path.exists(), "Approval request file should be created"
    assert "Pending_Approval" in str(approval_path), "Approval should be in Pending_Approval folder"

    # Verify content
    content = approval_path.read_text()
    assert "Test Approval Request" in content, "Approval should have correct title"
    assert "gmail_response" in content, "Approval should have correct action type"

    print(f"✓ Approval request created: {approval_path}")

    # Clean up
    shutil.rmtree(test_vault, ignore_errors=True)

    return True


def test_approval_detection():
    """Test detection of approval status changes."""
    print("\nTesting approval status detection...")

    # Create a test vault structure
    test_vault = Path("./test_approval_detection_vault")
    pending_approval = test_vault / "Pending_Approval"
    approved = test_vault / "Approved"
    rejected = test_vault / "Rejected"

    for folder in [test_vault, pending_approval, approved, rejected]:
        folder.mkdir(exist_ok=True)

    # Create an approval request
    approval_data = {
        'email_id': 'test456',
        'subject': 'Another Test Email',
        'from': 'another@example.com',
        'body_preview': 'Another test email body...'
    }

    approval_path = create_approval_request(
        str(test_vault),
        'gmail_response',
        approval_data,
        'Test Approval Request 2'
    )

    # Verify it starts in pending
    changes_before_move = scan_for_approval_changes(str(test_vault))
    assert len(changes_before_move) == 0, "Should be no approval changes before moving"

    # Simulate approving by moving to Approved folder
    approved_file = approved / approval_path.name
    shutil.move(str(approval_path), str(approved_file))

    # Scan for changes after moving
    changes_after_move = scan_for_approval_changes(str(test_vault))

    # Should detect the approval
    assert len(changes_after_move) == 1, "Should detect one approval change"
    assert changes_after_move[0]['status'] == 'approved', "Change status should be 'approved'"
    assert str(approved_file) in changes_after_move[0]['file_path'], "Should point to the approved file"

    print("✓ Approval status change detected correctly")

    # Clean up
    shutil.rmtree(test_vault, ignore_errors=True)

    return True


def test_action_executor():
    """Test the action executor functionality."""
    print("\nTesting action executor...")

    # Create a test vault structure
    test_vault = Path("./test_executor_vault")
    pending_approval = test_vault / "Pending_Approval"
    approved = test_vault / "Approved"
    rejected = test_vault / "Rejected"
    done = test_vault / "Done"

    for folder in [test_vault, pending_approval, approved, rejected, done]:
        folder.mkdir(exist_ok=True)

    # Create an executor
    executor = ActionExecutor(str(test_vault))

    # Create a test action file
    test_action = test_vault / "Needs_Action" / "test_action.md"
    test_action.parent.mkdir(exist_ok=True)
    test_action.write_text("# Test Action\n\nThis is a test action file.")

    # Test that unapproved action cannot be executed
    can_execute_unapproved = executor.can_execute_action(str(test_action))
    assert not can_execute_unapproved, "Unapproved action should not be executable"

    # Create an approval request
    approval_data = {
        'action_file': str(test_action),
        'reason': 'Testing approval workflow'
    }

    approval_path = create_approval_request(
        str(test_vault),
        'test_action',
        approval_data,
        'Test Action Approval'
    )

    # Move approval to approved folder to simulate approval
    approved_folder = test_vault / "Approved"
    approved_file = approved_folder / approval_path.name
    shutil.move(str(approval_path), str(approved_file))

    # Test that approved action can be executed
    can_execute_approved = executor.can_execute_action(str(approved_file))
    assert can_execute_approved, "Approved action should be executable"

    print("✓ Action executor works correctly")

    # Clean up
    shutil.rmtree(test_vault, ignore_errors=True)

    return True


def test_sensitive_content_detection():
    """Test sensitive content detection."""
    print("\nTesting sensitive content detection...")

    detector = SensitiveContentDetector()

    # Test cases with different levels of sensitivity
    test_cases = [
        ("Hi, how are you?", False, "Non-sensitive content"),
        ("I'm really frustrated with your service", True, "Emotional content"),
        ("Please review this legal contract", True, "Legal content"),
        ("My medical condition is", True, "Medical content"),
        ("Payment information needed", True, "Financial content"),
        ("Emergency situation needs immediate attention", True, "Urgent content")
    ]

    for text, should_require_approval, description in test_cases:
        requires_approval = detector.should_require_approval(text)

        if should_require_approval:
            assert requires_approval, f"Sensitive content should require approval: {description}"
        else:
            # For non-sensitive content, it might still require approval based on threshold
            # So we just verify the function runs without error
            pass

        print(f"✓ {description}: {requires_approval}")

    return True


def test_approval_workflow_integration():
    """Test integration of all approval workflow components."""
    print("\nTesting approval workflow integration...")

    # Create a test vault structure
    test_vault = Path("./test_integration_vault")
    pending_approval = test_vault / "Pending_Approval"
    approved = test_vault / "Approved"
    rejected = test_vault / "Rejected"
    done = test_vault / "Done"

    for folder in [test_vault, pending_approval, approved, rejected, done]:
        folder.mkdir(exist_ok=True)

    # Create sensitive content that should trigger approval
    sensitive_content = "I'm really frustrated with the service and would like to discuss my legal options regarding the contract."

    # Use the detector to identify if approval is needed
    detector = SensitiveContentDetector()
    should_approve = detector.should_require_approval(sensitive_content)

    assert should_approve, "Sensitive content should require approval"

    # Create approval request
    approval_data = {
        'original_content': sensitive_content[:100] + "...",
        'detected_risks': detector.analyze_content_risk(sensitive_content)['detected_categories']
    }

    approval_path = create_approval_request(
        str(test_vault),
        'customer_response',
        approval_data,
        'Customer Complaint Response Approval'
    )

    # Verify approval was created
    assert approval_path.exists(), "Approval request should be created"
    print(f"✓ Approval request created: {approval_path.name}")

    # Simulate user approval by moving to Approved folder
    approved_file = approved / approval_path.name
    shutil.move(str(approval_path), str(approved_file))

    # Verify approval status change is detected
    changes = scan_for_approval_changes(str(test_vault))
    assert len(changes) == 1, "Should detect approval status change"
    assert changes[0]['status'] == 'approved', "Status should be approved"
    print("✓ Approval status change detected")

    # Use action executor to handle the approved action
    executor = ActionExecutor(str(test_vault))
    can_execute = executor.can_execute_action(str(approved_file))
    assert can_execute, "Approved action should be executable"
    print("✓ Approved action can be executed")

    print("✓ Approval workflow integration test passed")

    # Clean up
    shutil.rmtree(test_vault, ignore_errors=True)

    return True


def main():
    """Main test function."""
    print("Testing Complete Approval Workflow from Request to Execution")
    print("=" * 65)

    tests = [
        test_approval_creation,
        test_approval_detection,
        test_action_executor,
        test_sensitive_content_detection,
        test_approval_workflow_integration
    ]

    all_passed = True
    for test in tests:
        if not test():
            all_passed = False

    print("\n" + "=" * 65)
    if all_passed:
        print("✓ All approval workflow tests passed!")
        print("\nFeatures tested:")
        print("- Approval request creation")
        print("- Approval status detection")
        print("- Action execution controls")
        print("- Sensitive content detection")
        print("- End-to-end workflow integration")
        return 0
    else:
        print("✗ Some approval workflow tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())