#!/usr/bin/env python3
"""Test script for T023 - README.md Validation"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent

def validate_readme():
    """Validate README.md completeness."""
    print("=" * 60)
    print("T023 - README.md Validation")
    print("=" * 60)

    readme_path = project_root / ".claude" / "mcp-servers" / "odoo-mcp" / "README.md"

    if not readme_path.exists():
        print(f"\n❌ README.md not found at {readme_path}")
        return False

    print(f"\n✓ README.md found: {readme_path}")

    with open(readme_path, 'r') as f:
        content = f.read()

    # Count lines
    lines = content.split('\n')
    print(f"✓ Total lines: {len(lines)}")

    # Required sections
    required_sections = [
        "# Odoo MCP Server",
        "## Features",
        "## Prerequisites",
        "## Installation",
        "## Configuration",
        "## API Reference",
        "### 1. `odoo_create_invoice`",
        "### 2. `odoo_record_payment`",
        "### 3. `odoo_get_partner`",
        "### 4. `odoo_list_invoices`",
        "## Error Handling",
        "## Usage Examples",
        "## Logging and Monitoring",
        "## Testing",
        "## Constitutional Compliance",
        "## Troubleshooting",
        "## Development",
        "## Support",
        "## Changelog"
    ]

    print("\n--- Required Sections ---")
    all_sections_found = True

    for section in required_sections:
        if section in content:
            print(f"✓ {section}")
        else:
            print(f"❌ Missing: {section}")
            all_sections_found = False

    # Check for key content
    print("\n--- Key Content Checks ---")
    key_content = {
        "Circuit Breaker": "Circuit breaker" in content or "circuit breaker" in content,
        "Dry-run mode": "dry_run" in content or "dry-run" in content,
        "Constitutional Compliance": "Constitutional" in content and "Principle" in content,
        "Environment variables": "ODOO_URL" in content and "ODOO_DB" in content,
        "Error codes": "ODOO_CONNECTION_ERROR" in content,
        "Examples": "Example:" in content or "```python" in content,
        "Installation steps": "docker run" in content or "Installation" in content,
        "Log format": "Logs" in content and "YYYY-MM-DD" in content,
        "Version info": "Version" in content and "1.0.0" in content,
        "All 4 tools documented": all([
            "odoo_create_invoice" in content,
            "odoo_record_payment" in content,
            "odoo_get_partner" in content,
            "odoo_list_invoices" in content
        ])
    }

    all_content_found = True
    for check, found in key_content.items():
        if found:
            print(f"✓ {check}")
        else:
            print(f"❌ Missing: {check}")
            all_content_found = False

    # Check for code examples
    code_blocks = content.count("```")
    print(f"\n✓ Code blocks: {code_blocks // 2} (pairs)")

    # Summary
    print("\n" + "=" * 60)

    if all_sections_found and all_content_found:
        print("✓ ALL CHECKS PASSED - T023 Complete")
        print("=" * 60)
        print("\nREADME.md Contents:")
        print(f"  • {len(lines)} lines of comprehensive documentation")
        print(f"  • {len(required_sections)} major sections")
        print(f"  • {code_blocks // 2} code examples")
        print("  • Complete API reference for all 4 tools")
        print("  • Installation and configuration guide")
        print("  • Error handling and troubleshooting")
        print("  • Usage examples and best practices")
        print("  • Constitutional compliance documentation")
        print("  • Testing and monitoring guidance")
        print("\n" + "=" * 60)
        return True
    else:
        print("❌ VALIDATION FAILED - Missing content")
        return False


if __name__ == "__main__":
    success = validate_readme()
    sys.exit(0 if success else 1)
