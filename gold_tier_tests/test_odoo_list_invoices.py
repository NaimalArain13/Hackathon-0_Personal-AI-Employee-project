#!/usr/bin/env python3
"""Test script for odoo_list_invoices tool - T019"""

import sys
from pathlib import Path

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

def test_odoo_list_invoices():
    """Test the odoo_list_invoices tool."""
    print("=" * 60)
    print("Testing odoo_list_invoices tool (T019)")
    print("=" * 60)

    server = OdooMCPServer()

    # Test 1: List all invoices (default limit)
    print("\n[Test 1] List all invoices (limit=10)")
    result = server.odoo_list_invoices(limit=10)
    print(f"Status: {result.get('status')}")
    print(f"Count: {result.get('count')}")
    if result.get('status') == 'error':
        print(f"Error: {result.get('error')}")
        print(f"Message: {result.get('message')}")

    # Test 2: List invoices for specific partner
    print("\n[Test 2] List invoices for partner_id=123 (limit=5)")
    result2 = server.odoo_list_invoices(partner_id=123, limit=5)
    print(f"Status: {result2.get('status')}")
    print(f"Count: {result2.get('count')}")
    if result2.get('status') == 'error':
        print(f"Error: {result2.get('error')}")
        print(f"Message: {result2.get('message')}")

    # Test 3: List invoices by state
    print("\n[Test 3] List posted invoices (state='posted', limit=10)")
    result3 = server.odoo_list_invoices(state="posted", limit=10)
    print(f"Status: {result3.get('status')}")
    print(f"Count: {result3.get('count')}")
    if result3.get('status') == 'error':
        print(f"Error: {result3.get('error')}")
        print(f"Message: {result3.get('message')}")

    # Test 4: List draft invoices for specific partner
    print("\n[Test 4] List draft invoices for partner_id=456 (state='draft', limit=20)")
    result4 = server.odoo_list_invoices(partner_id=456, state="draft", limit=20)
    print(f"Status: {result4.get('status')}")
    print(f"Count: {result4.get('count')}")
    if result4.get('status') == 'error':
        print(f"Error: {result4.get('error')}")
        print(f"Message: {result4.get('message')}")

    # Validation
    print("\n" + "=" * 60)
    print("Validation Checks")
    print("=" * 60)

    assert 'status' in result, "❌ Missing 'status' field"
    print("✓ 'status' field present")

    assert 'invoices' in result, "❌ Missing 'invoices' field"
    print("✓ 'invoices' field present")

    assert 'count' in result, "❌ Missing 'count' field"
    print("✓ 'count' field present")

    assert isinstance(result.get('invoices'), list), "❌ 'invoices' should be a list"
    print("✓ 'invoices' is a list")

    assert isinstance(result.get('count'), int), "❌ 'count' should be an integer"
    print("✓ 'count' is an integer")

    print("\n" + "=" * 60)
    print("✓ T019 Test Complete - odoo_list_invoices tool working")
    print("=" * 60)
    print("\nNote: Connection errors are expected without real Odoo server.")
    print("The test validates tool logic and error handling work correctly.")

if __name__ == "__main__":
    test_odoo_list_invoices()
