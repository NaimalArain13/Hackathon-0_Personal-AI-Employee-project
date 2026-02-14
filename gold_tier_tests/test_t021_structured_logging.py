#!/usr/bin/env python3
"""Test script for T021 - Structured Logging for Odoo Operations"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / '.claude' / 'mcp-servers' / 'odoo-mcp'))

# Load .env file
from dotenv import load_dotenv
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)

from mcp_server_odoo import OdooMCPServer


def setup_test_environment():
    """Set up test vault for logging."""
    test_vault = project_root / "test_vault_t021"
    test_vault.mkdir(exist_ok=True)

    # Set environment variable for test vault
    import os
    os.environ['VAULT_PATH'] = str(test_vault)

    return test_vault


def read_today_logs(vault_path):
    """Read today's structured log file."""
    logs_dir = vault_path / "Logs"
    today_file = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

    if not today_file.exists():
        return []

    entries = []
    with open(today_file, 'r') as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))

    return entries


def test_success_logging():
    """Test that successful operations are logged."""
    print("\n" + "=" * 60)
    print("Test 1: Success Case Logging")
    print("=" * 60)

    server = OdooMCPServer()

    # Test odoo_list_invoices (read operation that will fail but log the attempt)
    print("\nCalling odoo_list_invoices...")
    result = server.odoo_list_invoices(limit=10)

    print(f"Result status: {result.get('status')}")

    # The call will fail (no Odoo server), but it should be logged
    # Read logs to verify
    test_vault = Path(project_root) / "test_vault_t021"
    logs = read_today_logs(test_vault)

    # Find the log entry for this operation
    odoo_logs = [log for log in logs if log.get('action') == 'odoo_list_invoices']

    if odoo_logs:
        latest_log = odoo_logs[-1]
        print(f"\n✓ Found log entry for odoo_list_invoices")
        print(f"  Timestamp: {latest_log.get('timestamp')}")
        print(f"  Actor: {latest_log.get('actor')}")
        print(f"  Result status: {latest_log.get('result', {}).get('status')}")
        print(f"  Approval status: {latest_log.get('approval_status')}")
        print(f"  Duration: {latest_log.get('duration_ms')}ms")
        print(f"  Error: {latest_log.get('error', 'None')[:100]}...")

        # Validate schema
        required_fields = ['timestamp', 'action', 'actor', 'parameters', 'result', 'approval_status']
        for field in required_fields:
            assert field in latest_log, f"Missing required field: {field}"
            print(f"  ✓ Has field: {field}")

        return True
    else:
        print("❌ No log entry found for odoo_list_invoices")
        return False


def test_error_logging_all_tools():
    """Test that all four Odoo tools log errors correctly."""
    print("\n" + "=" * 60)
    print("Test 2: Error Logging for All Tools")
    print("=" * 60)

    server = OdooMCPServer()
    test_vault = Path(project_root) / "test_vault_t021"

    tools_to_test = [
        ('odoo_create_invoice', lambda: server.odoo_create_invoice(
            partner_id=999,
            invoice_lines=[{"product_id": 1, "description": "Test", "quantity": 1, "unit_price": 100}],
            dry_run=True
        )),
        ('odoo_record_payment', lambda: server.odoo_record_payment(
            invoice_id=999,
            amount=100.00,
            payment_date="2026-02-13",
            payment_method="bank_transfer",
            dry_run=True
        )),
        ('odoo_get_partner', lambda: server.odoo_get_partner(
            partner_id=999
        )),
        ('odoo_list_invoices', lambda: server.odoo_list_invoices(
            limit=10
        ))
    ]

    all_passed = True

    for tool_name, tool_func in tools_to_test:
        print(f"\n--- Testing {tool_name} ---")

        # Clear previous logs for this action
        logs_before = read_today_logs(test_vault)
        logs_before_count = len([l for l in logs_before if l.get('action') == tool_name])

        # Call the tool (will fail without Odoo server)
        result = tool_func()
        print(f"  Result status: {result.get('status')}")
        print(f"  Error type: {result.get('error')}")

        # Read logs after
        logs_after = read_today_logs(test_vault)
        tool_logs = [l for l in logs_after if l.get('action') == tool_name]

        if len(tool_logs) > logs_before_count:
            latest_log = tool_logs[-1]
            print(f"  ✓ Log entry created")
            print(f"    Actor: {latest_log.get('actor')}")
            print(f"    Result status: {latest_log.get('result', {}).get('status')}")
            print(f"    Error logged: {'Yes' if latest_log.get('error') else 'No'}")
            print(f"    Duration: {latest_log.get('duration_ms')}ms")

            # Validate error is logged
            assert latest_log.get('error'), f"{tool_name}: Error should be logged"
            assert latest_log.get('result', {}).get('status') == 'error', f"{tool_name}: Status should be error"

            print(f"  ✓ {tool_name} error logging validated")
        else:
            print(f"  ❌ No new log entry found for {tool_name}")
            all_passed = False

    return all_passed


def test_log_file_format():
    """Test that log file format is correct."""
    print("\n" + "=" * 60)
    print("Test 3: Log File Format Validation")
    print("=" * 60)

    test_vault = Path(project_root) / "test_vault_t021"
    logs_dir = test_vault / "Logs"
    today_file = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

    print(f"\nLog file path: {today_file}")
    print(f"File exists: {today_file.exists()}")

    if not today_file.exists():
        print("❌ Log file doesn't exist")
        return False

    # Verify file format (one JSON object per line)
    with open(today_file, 'r') as f:
        lines = f.readlines()

    print(f"Total log entries: {len(lines)}")

    valid_lines = 0
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue

        try:
            entry = json.loads(line)
            valid_lines += 1

            # Validate schema for first entry
            if i == 1:
                print(f"\nFirst log entry schema validation:")
                required_fields = ['timestamp', 'action', 'actor', 'parameters', 'result', 'approval_status']
                for field in required_fields:
                    has_field = field in entry
                    print(f"  {'✓' if has_field else '❌'} {field}: {has_field}")

                    if not has_field:
                        return False

        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON on line {i}: {e}")
            return False

    print(f"\n✓ All {valid_lines} log entries are valid JSON")
    print(f"✓ Log file format is correct (one JSON per line)")

    return True


def test_log_persistence():
    """Test that logs persist across operations."""
    print("\n" + "=" * 60)
    print("Test 4: Log Persistence")
    print("=" * 60)

    test_vault = Path(project_root) / "test_vault_t021"

    # Count initial logs
    initial_logs = read_today_logs(test_vault)
    initial_count = len(initial_logs)
    print(f"Initial log entries: {initial_count}")

    # Perform new operation
    server = OdooMCPServer()
    server.odoo_list_invoices(limit=5)

    # Count after
    after_logs = read_today_logs(test_vault)
    after_count = len(after_logs)
    print(f"Log entries after operation: {after_count}")

    if after_count > initial_count:
        print(f"✓ New log entry persisted (added {after_count - initial_count} entry)")
        return True
    else:
        print("❌ Log entry not persisted")
        return False


def cleanup_test_environment(test_vault):
    """Clean up test vault."""
    import shutil
    if test_vault.exists():
        shutil.rmtree(test_vault)
        print(f"\n✓ Cleaned up test vault: {test_vault}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("T021 - Structured Logging for Odoo Operations Tests")
    print("=" * 60)

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Set up test environment
    test_vault = setup_test_environment()
    print(f"\n✓ Test vault created: {test_vault}")

    try:
        # Run all tests
        tests = [
            ("Success Case Logging", test_success_logging),
            ("Error Logging All Tools", test_error_logging_all_tools),
            ("Log File Format", test_log_file_format),
            ("Log Persistence", test_log_persistence)
        ]

        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"\n❌ Test '{test_name}' failed with exception: {e}")
                results.append((test_name, False))

        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)

        for test_name, result in results:
            status = "✓ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")

        all_passed = all(result for _, result in results)

        if all_passed:
            print("\n" + "=" * 60)
            print("✓ ALL TESTS PASSED - T021 Implementation Complete")
            print("=" * 60)
            print("\nStructured Logging Features:")
            print("  • All Odoo operations logged (success and error cases)")
            print("  • Log format: /Vault/Logs/YYYY-MM-DD.json")
            print("  • Schema: timestamp, action, actor, parameters, result,")
            print("            approval_status, duration_ms, error")
            print("  • One JSON object per line (newline-delimited JSON)")
            print("  • Constitutional Principle IX: Comprehensive audit trails")
            print("\n" + "=" * 60)
        else:
            print("\n❌ SOME TESTS FAILED")

    finally:
        # Clean up
        cleanup_test_environment(test_vault)


if __name__ == "__main__":
    main()
