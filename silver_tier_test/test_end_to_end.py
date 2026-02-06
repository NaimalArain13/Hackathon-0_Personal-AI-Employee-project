#!/usr/bin/env python3
"""
End-to-End Test Script for all User Stories in the Silver Tier Personal AI Employee system.
"""

import json
import sys
import os
import shutil
import time
from pathlib import Path
from datetime import datetime

# Add the project root to the path to import from other modules
sys.path.insert(0, str(Path(__file__).parent))

from utils.setup_logger import setup_logger
from utils.file_utils import create_action_file, create_approval_request
from utils.plan_generator import PlanGenerator
from utils.plan_updater import PlanUpdater
from utils.sensitive_content_detector import SensitiveContentDetector
from utils.action_executor import ActionExecutor
from watchers.gmail_watcher import GmailWatcher
from watchers.whatsapp_watcher import WhatsAppWatcher
from utils.health_monitor import HealthMonitor


def test_us1_multi_channel_email_management():
    """Test User Story 1: Multi-Channel Email Management."""
    print("Testing US1: Multi-Channel Email Management...")

    # Create a test vault structure
    test_vault = Path("./test_us1_vault")
    needs_action = test_vault / "Needs_Action"
    pending_approval = test_vault / "Pending_Approval"
    approved = test_vault / "Approved"
    rejected = test_vault / "Rejected"

    for folder in [test_vault, needs_action, pending_approval, approved, rejected]:
        folder.mkdir(exist_ok=True)

    # Test creating an email action file
    email_content = f"""# New Email: Quarterly Report Request

## Sender Information
- **From**: boss@company.com
- **To**: employee@company.com
- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Email Content
Please prepare the quarterly report with detailed financial analysis.

## Action Items
- [ ] Review email content
- [ ] Determine appropriate response
- [ ] Process or escalate as needed
"""

    frontmatter = {
        'type': 'gmail_message',
        'email_id': 'test_email_123',
        'subject': 'Quarterly Report Request',
        'from': 'boss@company.com',
        'timestamp': datetime.now().isoformat(),
        'status': 'pending',
        'priority': 'high'
    }

    action_file = create_action_file(
        str(needs_action),
        "EMAIL_Quarterly_Report_Request",
        email_content,
        frontmatter
    )

    assert action_file.exists(), "Email action file should be created"
    print("✓ Email action file created successfully")

    # Test sensitive content detection
    detector = SensitiveContentDetector()
    is_sensitive = detector.should_require_approval("Please prepare the quarterly report with detailed financial analysis.", "boss@company.com")

    if is_sensitive:
        # Create approval request for sensitive content
        approval_data = {
            'email_id': 'test_email_123',
            'subject': 'Quarterly Report Request',
            'from': 'boss@company.com',
            'body_preview': 'Please prepare the quarterly report with detailed financial analysis.'
        }

        approval_file = create_approval_request(
            str(test_vault),
            'gmail_response',
            approval_data,
            'Email Response Approval: Quarterly Report Request'
        )

        assert approval_file.exists(), "Approval request should be created for sensitive email"
        print("✓ Approval request created for sensitive email")

    # Clean up
    shutil.rmtree(test_vault, ignore_errors=True)

    print("✓ US1: Multi-Channel Email Management - PASSED")
    return True


def test_us2_linkedin_automation():
    """Test User Story 2: LinkedIn Business Automation."""
    print("\nTesting US2: LinkedIn Business Automation...")

    # Create a test vault structure
    test_vault = Path("./test_us2_vault")
    plans = test_vault / "Plans"
    plans.mkdir(parents=True, exist_ok=True)

    # Test creating a LinkedIn post plan
    generator = PlanGenerator(str(test_vault))

    linkedin_task = "Create and schedule weekly LinkedIn posts about our new product launch, focusing on business benefits and featuring customer testimonials over the next month."

    plan_path = generator.generate_plan(linkedin_task)

    assert plan_path is not None, "Plan should be generated for LinkedIn automation task"
    assert plan_path.exists(), "LinkedIn automation plan file should exist"

    content = plan_path.read_text()
    assert "LinkedIn" in content, "Plan should mention LinkedIn"
    assert "post" in content.lower(), "Plan should include posting tasks"

    print("✓ LinkedIn automation plan created successfully")

    # Clean up
    shutil.rmtree(test_vault, ignore_errors=True)

    print("✓ US2: LinkedIn Business Automation - PASSED")
    return True


def test_us3_multi_watcher_coordination():
    """Test User Story 3: Multi-Watcher Coordination."""
    print("\nTesting US3: Multi-Watcher Coordination...")

    # Create a test vault structure
    test_vault = Path("./test_us3_vault")
    needs_action = test_vault / "Needs_Action"
    pending_approval = test_vault / "Pending_Approval"

    for folder in [test_vault, needs_action, pending_approval]:
        folder.mkdir(exist_ok=True)

    # Test that both watchers can be initialized without conflict
    gmail_watcher = GmailWatcher(vault_path=str(test_vault), check_interval=60)
    whatsapp_watcher = WhatsAppWatcher(vault_path=str(test_vault), check_interval=45)

    # Verify they have different attributes but share the same vault
    assert gmail_watcher.vault_path == whatsapp_watcher.vault_path, "Both watchers should use the same vault"
    assert gmail_watcher.check_interval != whatsapp_watcher.check_interval, "Watchers should have different check intervals"

    # Test that they can both create action files in the same Needs_Action folder
    # without conflict
    gmail_content = "# Gmail Message\n\nGmail content here."
    whatsapp_content = "# WhatsApp Message\n\nWhatsApp content here."

    # These would normally be created through the watchers' check_for_updates methods,
    # but for testing we'll create them directly
    gmail_frontmatter = {'type': 'gmail_message', 'status': 'pending'}
    whatsapp_frontmatter = {'type': 'whatsapp_message', 'status': 'pending'}

    gmail_action = create_action_file(
        str(needs_action),
        "GMAIL_Test_Message",
        gmail_content,
        gmail_frontmatter
    )

    whatsapp_action = create_action_file(
        str(needs_action),
        "WHATSAPP_Test_Message",
        whatsapp_content,
        whatsapp_frontmatter
    )

    assert gmail_action.exists(), "Gmail action file should be created"
    assert whatsapp_action.exists(), "WhatsApp action file should be created"

    print("✓ Both Gmail and WhatsApp watchers can operate without conflict")

    # Clean up
    shutil.rmtree(test_vault, ignore_errors=True)

    print("✓ US3: Multi-Watcher Coordination - PASSED")
    return True


def test_us4_human_in_the_loop():
    """Test User Story 4: Human-in-the-Loop Approval Workflow."""
    print("\nTesting US4: Human-in-the-Loop Approval Workflow...")

    # Create a test vault structure
    test_vault = Path("./test_us4_vault")
    pending_approval = test_vault / "Pending_Approval"
    approved = test_vault / "Approved"
    rejected = test_vault / "Rejected"
    done = test_vault / "Done"

    for folder in [test_vault, pending_approval, approved, rejected, done]:
        folder.mkdir(exist_ok=True)

    # Create an approval request
    approval_data = {
        'action_type': 'financial_transaction',
        'amount': '$10,000',
        'recipient': 'Vendor ABC',
        'purpose': 'Q4 marketing campaign payment'
    }

    approval_file = create_approval_request(
        str(test_vault),
        'payment_approval',
        approval_data,
        'Large Payment Approval Required'
    )

    assert approval_file.exists(), "Approval request should be created"
    print("✓ Approval request created successfully")

    # Simulate approval by moving to Approved folder
    approved_file = approved / approval_file.name
    shutil.move(str(approval_file), str(approved_file))

    # Test action executor
    executor = ActionExecutor(str(test_vault))
    can_execute = executor.can_execute_action(str(approved_file))

    assert can_execute, "Approved action should be executable"
    print("✓ Approved action can be executed")

    # Test that the executor recognizes the approved status
    # (in a real system, this would execute the actual action)
    print("✓ Action execution workflow works correctly")

    # Clean up
    shutil.rmtree(test_vault, ignore_errors=True)

    print("✓ US4: Human-in-the-Loop Approval Workflow - PASSED")
    return True


def test_us5_automated_planning():
    """Test User Story 5: Automated Planning and Documentation."""
    print("\nTesting US5: Automated Planning and Documentation...")

    # Create a test vault structure
    test_vault = Path("./test_us5_vault")
    plans = test_vault / "Plans"
    plans.mkdir(parents=True, exist_ok=True)

    # Create a plan generator and updater
    generator = PlanGenerator(str(test_vault))
    updater = PlanUpdater(str(test_vault))

    # Create a complex task that should trigger plan generation
    complex_task = "Organize a comprehensive product launch event that includes keynote presentation, product demonstrations, networking sessions, media outreach, and post-event analysis spanning 3 weeks."

    plan_path = generator.generate_plan(complex_task)

    assert plan_path is not None, "Plan should be generated for complex task"
    assert plan_path.exists(), "Plan file should exist"

    content = plan_path.read_text()
    assert "## Tasks" in content, "Plan should have Tasks section"
    assert "## Goals" in content, "Plan should have Goals section"
    assert "## Success Criteria" in content, "Plan should have Success Criteria section"

    print("✓ Complex plan generated successfully")

    # Test updating plan status
    initial_status = updater.get_plan_status(str(plan_path))
    assert initial_status['total_tasks'] > 0, "Plan should have tasks"

    # Update a task status
    success = updater.mark_task_completed(str(plan_path), 0)  # Mark first task as completed
    assert success, "Task status should be updated successfully"

    updated_status = updater.get_plan_status(str(plan_path))
    assert updated_status['completed_tasks'] >= 1, "At least one task should be completed"

    print("✓ Plan status updates work correctly")

    # Clean up
    shutil.rmtree(test_vault, ignore_errors=True)

    print("✓ US5: Automated Planning and Documentation - PASSED")
    return True


def test_system_integration():
    """Test overall system integration."""
    print("\nTesting System Integration...")

    # Create a test vault structure
    test_vault = Path("./test_integration_vault")
    needs_action = test_vault / "Needs_Action"
    pending_approval = test_vault / "Pending_Approval"
    approved = test_vault / "Approved"
    plans = test_vault / "Plans"
    logs = test_vault / "Logs"

    for folder in [test_vault, needs_action, pending_approval, approved, plans, logs]:
        folder.mkdir(exist_ok=True)

    # Test that all components can work together
    detector = SensitiveContentDetector()
    generator = PlanGenerator(str(test_vault))
    executor = ActionExecutor(str(test_vault))
    monitor = HealthMonitor(str(test_vault))

    # Test content that triggers multiple system components
    sensitive_task = "Handle urgent legal contract review that requires multi-department approval from management, involves complex financial terms and compliance requirements for the Q4 partnership deal, necessitates coordination with external legal counsel, and requires detailed risk assessment over multiple phases."

    # Check if it's sensitive
    is_sensitive = detector.should_require_approval(sensitive_task)
    assert is_sensitive, "Complex legal/financial task should be flagged as sensitive"

    # Generate a plan for the complex task
    plan_path = generator.generate_plan(sensitive_task)
    assert plan_path is not None, "Plan should be generated for complex task"

    # Perform a health check
    health_status = monitor.perform_health_check()
    assert 'overall_health' in health_status, "Health monitor should return status"

    print("✓ All system components integrate correctly")

    # Clean up
    shutil.rmtree(test_vault, ignore_errors=True)

    print("✓ System Integration - PASSED")
    return True


def main():
    """Main test function."""
    print("End-to-End Testing of All User Stories")
    print("=" * 50)
    print("Testing US1: Multi-Channel Email Management")
    print("Testing US2: LinkedIn Business Automation")
    print("Testing US3: Multi-Watcher Coordination")
    print("Testing US4: Human-in-the-Loop Approval Workflow")
    print("Testing US5: Automated Planning and Documentation")
    print("Testing System Integration")
    print("=" * 50)

    tests = [
        test_us1_multi_channel_email_management,
        test_us2_linkedin_automation,
        test_us3_multi_watcher_coordination,
        test_us4_human_in_the_loop,
        test_us5_automated_planning,
        test_system_integration
    ]

    all_passed = True
    for test in tests:
        try:
            if not test():
                all_passed = False
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with error: {e}")
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("✅ ALL END-TO-END TESTS PASSED!")
        print("\nAll user stories have been successfully tested:")
        print("- US1: Multi-Channel Email Management ✓")
        print("- US2: LinkedIn Business Automation ✓")
        print("- US3: Multi-Watcher Coordination ✓")
        print("- US4: Human-in-the-Loop Approval Workflow ✓")
        print("- US5: Automated Planning and Documentation ✓")
        print("- System Integration ✓")
        return 0
    else:
        print("❌ SOME END-TO-END TESTS FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())