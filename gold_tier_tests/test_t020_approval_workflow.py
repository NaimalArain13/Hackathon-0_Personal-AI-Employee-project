#!/usr/bin/env python3
"""Test script for T020 - Odoo Approval Workflow Integration"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.action_executor import ActionExecutor


def setup_test_environment():
    """Set up test vault structure."""
    test_vault = project_root / "test_vault_t020"
    test_vault.mkdir(exist_ok=True)

    # Create logs folder with sample transaction
    logs_folder = test_vault / "Logs"
    logs_folder.mkdir(exist_ok=True)

    # Create sample log entry for recurring partner (partner_id=100)
    log_file = logs_folder / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "odoo_create_invoice",
        "actor": "odoo-mcp",
        "parameters": {
            "partner_id": 100,
            "amount": 50.00
        },
        "result": {
            "status": "success",
            "invoice_id": 123
        },
        "approval_status": "auto_approved"
    }

    with open(log_file, 'w') as f:
        f.write(json.dumps(log_entry) + '\n')

    return test_vault


def test_is_partner_recurring(executor):
    """Test partner recurrence detection."""
    print("\n" + "=" * 60)
    print("Test 1: Partner Recurrence Detection")
    print("=" * 60)

    # Test recurring partner (has transaction in logs)
    is_recurring_100 = executor.is_partner_recurring(partner_id=100)
    print(f"Partner 100 (has transaction): {'✓ RECURRING' if is_recurring_100 else '❌ NEW'}")
    assert is_recurring_100, "Partner 100 should be recurring"

    # Test new partner (no transaction in logs)
    is_recurring_999 = executor.is_partner_recurring(partner_id=999)
    print(f"Partner 999 (no transaction): {'✓ NEW' if not is_recurring_999 else '❌ RECURRING'}")
    assert not is_recurring_999, "Partner 999 should be new"

    print("\n✓ Partner recurrence detection working correctly")


def test_requires_approval_logic(executor):
    """Test approval requirement determination."""
    print("\n" + "=" * 60)
    print("Test 2: Approval Requirement Logic")
    print("=" * 60)

    # Test Case 1: Small amount + recurring partner → auto-approve
    requires_1, reason_1 = executor.requires_odoo_approval(
        amount=50.00,
        partner_id=100  # Recurring
    )
    print(f"\nCase 1: $50 + recurring partner")
    print(f"  Requires approval: {requires_1}")
    print(f"  Reason: {reason_1}")
    assert not requires_1, "Should auto-approve small recurring transaction"
    print("  ✓ AUTO-APPROVED (correct)")

    # Test Case 2: Large amount + recurring partner → require approval
    requires_2, reason_2 = executor.requires_odoo_approval(
        amount=150.00,
        partner_id=100  # Recurring
    )
    print(f"\nCase 2: $150 + recurring partner")
    print(f"  Requires approval: {requires_2}")
    print(f"  Reason: {reason_2}")
    assert requires_2, "Should require approval for large amount"
    assert reason_2 == "amount_over_threshold", "Reason should be amount_over_threshold"
    print("  ✓ REQUIRES APPROVAL (correct)")

    # Test Case 3: Small amount + new partner → require approval
    requires_3, reason_3 = executor.requires_odoo_approval(
        amount=50.00,
        partner_id=999  # New
    )
    print(f"\nCase 3: $50 + new partner")
    print(f"  Requires approval: {requires_3}")
    print(f"  Reason: {reason_3}")
    assert requires_3, "Should require approval for new partner"
    assert reason_3 == "new_payee", "Reason should be new_payee"
    print("  ✓ REQUIRES APPROVAL (correct)")

    # Test Case 4: Large amount + new partner → require approval
    requires_4, reason_4 = executor.requires_odoo_approval(
        amount=150.00,
        partner_id=999  # New
    )
    print(f"\nCase 4: $150 + new partner")
    print(f"  Requires approval: {requires_4}")
    print(f"  Reason: {reason_4}")
    assert requires_4, "Should require approval for large amount + new partner"
    assert "amount_over_threshold" in reason_4 and "new_payee" in reason_4, "Should have both reasons"
    print("  ✓ REQUIRES APPROVAL (correct)")

    # Test Case 5: Exactly $100 + recurring partner → auto-approve
    requires_5, reason_5 = executor.requires_odoo_approval(
        amount=100.00,
        partner_id=100  # Recurring
    )
    print(f"\nCase 5: $100 (threshold) + recurring partner")
    print(f"  Requires approval: {requires_5}")
    print(f"  Reason: {reason_5}")
    assert not requires_5, "Should auto-approve at threshold for recurring"
    print("  ✓ AUTO-APPROVED (correct)")

    # Test Case 6: $100.01 + recurring partner → require approval
    requires_6, reason_6 = executor.requires_odoo_approval(
        amount=100.01,
        partner_id=100  # Recurring
    )
    print(f"\nCase 6: $100.01 (over threshold) + recurring partner")
    print(f"  Requires approval: {requires_6}")
    print(f"  Reason: {reason_6}")
    assert requires_6, "Should require approval just over threshold"
    print("  ✓ REQUIRES APPROVAL (correct)")

    print("\n✓ All approval requirement cases working correctly")


def test_create_approval_request(executor):
    """Test approval request file creation."""
    print("\n" + "=" * 60)
    print("Test 3: Approval Request Creation")
    print("=" * 60)

    metadata = {
        'transaction_type': 'invoice',
        'amount': 150.00,
        'partner_id': 100,
        'approval_reason': 'amount_over_threshold'
    }

    description = """
This invoice requires approval before creation in Odoo.

**Transaction Details:**
- **Type**: Invoice
- **Partner ID**: 100
- **Amount**: $150.00
- **Approval Reason**: Amount Over Threshold
"""

    approval_file = executor.create_approval_request(
        action_type='odoo_transaction',
        metadata=metadata,
        description=description,
        expires_in_hours=48
    )

    print(f"Approval request created: {approval_file}")

    # Verify file exists
    approval_path = Path(approval_file)
    assert approval_path.exists(), "Approval file should exist"
    print("✓ Approval file created")

    # Verify file is in Pending_Approval folder
    assert approval_path.parent.name == "Pending_Approval", "Should be in Pending_Approval folder"
    print("✓ File in correct folder")

    # Read and verify content
    with open(approval_file, 'r') as f:
        content = f.read()

    assert '---' in content, "Should have frontmatter"
    assert 'type: odoo_transaction' in content, "Should have correct type"
    assert 'status: pending' in content, "Should have pending status"
    assert 'approval_reason' in content, "Should include approval reason"
    assert '150.0' in content or '150' in content, "Should include amount"
    print("✓ File content correct")

    print("\n✓ Approval request creation working correctly")
    return approval_file


def test_check_and_handle_odoo_approval(executor):
    """Test the integrated approval checking and handling."""
    print("\n" + "=" * 60)
    print("Test 4: Integrated Approval Handling")
    print("=" * 60)

    # Test Case 1: Auto-approved transaction
    print("\nCase 1: Auto-approved transaction ($50, recurring)")
    approval_status_1, approval_file_1 = executor.check_and_handle_odoo_approval(
        transaction_type='invoice',
        amount=50.00,
        partner_id=100,
        transaction_details={'description': 'Test invoice'}
    )
    print(f"  Status: {approval_status_1}")
    print(f"  File: {approval_file_1}")
    assert approval_status_1 == 'auto_approved', "Should be auto-approved"
    assert approval_file_1 is None, "Should not create approval file"
    print("  ✓ PASS")

    # Test Case 2: Requires approval transaction
    print("\nCase 2: Requires approval ($150, recurring)")
    approval_status_2, approval_file_2 = executor.check_and_handle_odoo_approval(
        transaction_type='invoice',
        amount=150.00,
        partner_id=100,
        transaction_details={'description': 'Large invoice'}
    )
    print(f"  Status: {approval_status_2}")
    print(f"  File: {approval_file_2}")
    assert approval_status_2 == 'pending', "Should require approval"
    assert approval_file_2 is not None, "Should create approval file"
    assert Path(approval_file_2).exists(), "Approval file should exist"
    print("  ✓ PASS")

    print("\n✓ Integrated approval handling working correctly")


def test_execute_with_approval(executor):
    """Test the execute_odoo_transaction_with_approval method."""
    print("\n" + "=" * 60)
    print("Test 5: Execute Transaction with Approval")
    print("=" * 60)

    # Test Case 1: Auto-approved execution
    print("\nCase 1: Auto-approved execution")
    result_1 = executor.execute_odoo_transaction_with_approval(
        transaction_type='invoice',
        amount=50.00,
        partner_id=100,
        transaction_details={'description': 'Small invoice'},
        dry_run=True
    )
    print(f"  Result status: {result_1.get('status')}")
    print(f"  Approval status: {result_1.get('approval_status')}")
    assert result_1.get('status') == 'success', "Should execute successfully"
    assert result_1.get('approval_status') == 'auto_approved', "Should be auto-approved"
    print("  ✓ PASS")

    # Test Case 2: Pending approval
    print("\nCase 2: Pending approval")
    result_2 = executor.execute_odoo_transaction_with_approval(
        transaction_type='invoice',
        amount=150.00,
        partner_id=100,
        transaction_details={'description': 'Large invoice'},
        dry_run=True
    )
    print(f"  Result status: {result_2.get('status')}")
    print(f"  Approval status: {result_2.get('approval_status')}")
    print(f"  Approval file: {result_2.get('approval_file')}")
    assert result_2.get('status') == 'pending', "Should be pending"
    assert result_2.get('approval_status') == 'pending', "Approval should be pending"
    assert result_2.get('approval_file') is not None, "Should have approval file"
    print("  ✓ PASS")

    print("\n✓ Execute with approval working correctly")


def cleanup_test_environment(test_vault):
    """Clean up test vault."""
    import shutil
    if test_vault.exists():
        shutil.rmtree(test_vault)
        print(f"\n✓ Cleaned up test vault: {test_vault}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("T020 - Odoo Approval Workflow Integration Tests")
    print("=" * 60)

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Set up test environment
    test_vault = setup_test_environment()
    print(f"\n✓ Test vault created: {test_vault}")

    try:
        # Create action executor with test vault
        executor = ActionExecutor(str(test_vault))
        print("✓ ActionExecutor initialized")

        # Run all tests
        test_is_partner_recurring(executor)
        test_requires_approval_logic(executor)
        test_create_approval_request(executor)
        test_check_and_handle_odoo_approval(executor)
        test_execute_with_approval(executor)

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED - T020 Implementation Complete")
        print("=" * 60)
        print("\nApproval Workflow Summary:")
        print("  • Auto-approve: amount ≤ $100 AND recurring partner")
        print("  • Require approval: amount > $100 OR new partner")
        print("  • Approval requests created in Pending_Approval/ folder")
        print("  • Proper logging with approval_status tracking")
        print("\n" + "=" * 60)

    finally:
        # Clean up
        cleanup_test_environment(test_vault)


if __name__ == "__main__":
    main()
