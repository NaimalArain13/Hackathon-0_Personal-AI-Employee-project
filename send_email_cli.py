#!/usr/bin/env python3
"""
Command-line interface to send emails using the MCP email server.
"""

import json
import subprocess
import sys
import os
from pathlib import Path

def send_email(receiver, subject, body, attachments=None):
    """Send an email using the MCP email server."""
    if attachments is None:
        attachments = []

    # Prepare the MCP request
    request = {
        "method": "send_email",
        "params": {
            "receiver": receiver if isinstance(receiver, list) else [receiver],
            "subject": subject,
            "body": body,
            "attachments": attachments
        }
    }

    # Start the email server process
    server_path = Path(".claude/mcp-servers/gmail-mcp/mcp_server_email.py")
    env = os.environ.copy()

    try:
        proc = subprocess.Popen([
            sys.executable, str(server_path)
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=env, cwd=os.getcwd())

        # Send the request
        input_data = json.dumps(request) + "\n"
        stdout, stderr = proc.communicate(input=input_data.encode(), timeout=30)

        # Parse the response
        response_str = stdout.decode().strip()
        if response_str:
            response = json.loads(response_str)
            return response
        else:
            return {"error": "No response from server"}

    except subprocess.TimeoutExpired:
        proc.kill()
        return {"error": "Request timed out"}
    except Exception as e:
        return {"error": f"Failed to send email: {str(e)}"}

def main():
    if len(sys.argv) < 4:
        print("Usage: python send_email_cli.py <to_email> <subject> <message> [attachment_paths...]")
        sys.exit(1)

    receiver = sys.argv[1]
    subject = sys.argv[2]
    body = sys.argv[3]
    attachments = sys.argv[4:] if len(sys.argv) > 4 else []

    print(f"Sending email to: {receiver}")
    print(f"Subject: {subject}")
    print(f"Body: {body[:50]}{'...' if len(body) > 50 else ''}")

    if attachments:
        print(f"Attachments: {attachments}")

    result = send_email(receiver, subject, body, attachments)

    if result.get("success"):
        print("✅ Email sent successfully!")
        print(f"Message ID: {result.get('message_id', 'N/A')}")
    else:
        print("❌ Failed to send email:")
        print(f"Error: {result.get('error_message', result.get('error', 'Unknown error'))}")

if __name__ == "__main__":
    main()