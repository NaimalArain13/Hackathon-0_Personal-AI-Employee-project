#!/usr/bin/env python3
"""
Simple CLI interface for LinkedIn automation using MCP tools in the background.
"""

import json
import subprocess
import sys
import os
from pathlib import Path
import time

def run_mcp_command(method, params):
    """Run an MCP command by starting the appropriate server temporarily."""

    # Determine which server to use based on the method
    if method in ['linkedin_login', 'create_linkedin_post', 'navigate_to_url', 'click_element', 'fill_input', 'take_screenshot']:
        # Use the browser server for LinkedIn and browser operations
        server_path = Path(".claude/mcp-servers/browser-mcp/mcp_browser_server.py")
    elif method in ['send_email', 'search_attachments']:
        # Use the email server for email operations
        server_path = Path(".claude/mcp-servers/gmail-mcp/mcp_server_email.py")
    else:
        print(f"Unknown method: {method}")
        return {"error": "Unknown method"}

    env = os.environ.copy()

    try:
        proc = subprocess.Popen([
            sys.executable, str(server_path)
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True, env=env)

        # Give the server a moment to start
        time.sleep(1)

        # Prepare the request
        request = {
            "method": method,
            "params": params
        }

        # Send the request
        proc.stdin.write(json.dumps(request) + '\n')
        proc.stdin.flush()

        # Read the response
        response_line = proc.stdout.readline()

        # Clean up
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()

        if response_line.strip():
            return json.loads(response_line)
        else:
            return {"error": "No response from server"}

    except Exception as e:
        return {"error": f"Failed to execute command: {str(e)}"}

def linkedin_menu():
    """Display LinkedIn automation menu."""
    print("\n=== LinkedIn Automation Menu ===")
    print("1. Login to LinkedIn")
    print("2. Create LinkedIn Post")
    print("3. Back to Main Menu")
    print("===============================")

    choice = input("Select an option (1-3): ").strip()

    if choice == "1":
        username = input("Enter LinkedIn username: ").strip()
        password = input("Enter LinkedIn password: ").strip()

        print("Logging in to LinkedIn...")
        result = run_mcp_command("linkedin_login", {
            "username": username,
            "password": password
        })

        print("Login Result:")
        print(json.dumps(result, indent=2))

    elif choice == "2":
        content = input("Enter post content: ").strip()
        headline = input("Enter headline (optional, press Enter to skip): ").strip() or None
        visibility = input("Enter visibility [PUBLIC/CONNECTIONS_ONLY/PRIVATE, default PUBLIC]: ").strip() or "PUBLIC"

        print("Creating LinkedIn post...")
        params = {
            "content": content,
            "visibility": visibility
        }
        if headline:
            params["headline"] = headline

        result = run_mcp_command("create_linkedin_post", params)

        print("Post Result:")
        print(json.dumps(result, indent=2))

    elif choice == "3":
        return  # Go back to main menu
    else:
        print("Invalid choice!")

    input("\nPress Enter to continue...")

def email_menu():
    """Display email menu."""
    print("\n=== Email Menu ===")
    print("1. Send Email")
    print("2. Search Attachments")
    print("3. Back to Main Menu")
    print("==================")

    choice = input("Select an option (1-3): ").strip()

    if choice == "1":
        receiver = input("Enter recipient email (comma-separated for multiple): ").strip()
        receivers = [r.strip() for r in receiver.split(',')]
        subject = input("Enter subject: ").strip()
        body = input("Enter body: ").strip()
        attachments = input("Enter attachment paths (comma-separated, press Enter to skip): ").strip()

        attachments_list = [a.strip() for a in attachments.split(',')] if attachments else []

        print("Sending email...")
        result = run_mcp_command("send_email", {
            "receiver": receivers,
            "subject": subject,
            "body": body,
            "attachments": attachments_list
        })

        print("Email Result:")
        print(json.dumps(result, indent=2))

    elif choice == "2":
        pattern = input("Enter search pattern: ").strip()

        print("Searching for attachments...")
        result = run_mcp_command("search_attachments", {
            "pattern": pattern
        })

        print("Search Result:")
        print(json.dumps(result, indent=2))

    elif choice == "3":
        return  # Go back to main menu
    else:
        print("Invalid choice!")

    input("\nPress Enter to continue...")

def main_menu():
    """Display main menu."""
    while True:
        print("\n" + "="*40)
        print("    MCP Tools Command Line Interface")
        print("="*40)
        print("1. LinkedIn Automation")
        print("2. Email Tools")
        print("3. Exit")
        print("="*40)

        choice = input("Select an option (1-3): ").strip()

        if choice == "1":
            linkedin_menu()
        elif choice == "2":
            email_menu()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice! Please select 1, 2, or 3.")

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('.env')

    print("Loading MCP Tools CLI Interface...")
    print("Note: This runs MCP tools in the background even though Claude Code shows them as disconnected.")

    main_menu()