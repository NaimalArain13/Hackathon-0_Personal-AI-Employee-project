#!/usr/bin/env python3
"""
Test script to verify MCP server functionality
"""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import signal
import sys

def test_email_server():
    """Test the email server by starting it and sending a request."""
    print("Starting email MCP server...")

    server_path = Path(".claude/mcp-servers/gmail-mcp/mcp_server_email.py")

    # Start the server in a subprocess
    proc = subprocess.Popen([
        sys.executable, str(server_path)
    ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    universal_newlines=True, bufsize=1)

    # Give the server a moment to start
    time.sleep(2)

    # Prepare a test request
    test_req = {
        "method": "send_email",
        "params": {
            "receiver": ["test@example.com"],
            "subject": "Test",
            "body": "Test message",
            "attachments": []
        }
    }

    try:
        # Send the request
        proc.stdin.write(json.dumps(test_req) + '\n')
        proc.stdin.flush()

        # Read the response
        response_line = proc.stdout.readline()
        print(f"Response: {response_line}")

        # Parse and display the response
        if response_line.strip():
            response = json.loads(response_line)
            print("Parsed response:", json.dumps(response, indent=2))
        else:
            print("No response received")

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
    except Exception as e:
        print(f"Error communicating with server: {e}")
    finally:
        # Terminate the server process
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

def test_search_attachments():
    """Test the search_attachments functionality."""
    print("\nTesting search_attachments...")

    server_path = Path(".claude/mcp-servers/gmail-mcp/mcp_server_email.py")

    # Start the server in a subprocess
    proc = subprocess.Popen([
        sys.executable, str(server_path)
    ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    universal_newlines=True, bufsize=1)

    # Give the server a moment to start
    time.sleep(2)

    # Prepare a test request for searching attachments
    test_req = {
        "method": "search_attachments",
        "params": {
            "pattern": "test"
        }
    }

    try:
        # Send the request
        proc.stdin.write(json.dumps(test_req) + '\n')
        proc.stdin.flush()

        # Read the response
        response_line = proc.stdout.readline()
        print(f"Response: {response_line}")

        # Parse and display the response
        if response_line.strip():
            response = json.loads(response_line)
            print("Parsed response:", json.dumps(response, indent=2))
        else:
            print("No response received")

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
    except Exception as e:
        print(f"Error communicating with server: {e}")
    finally:
        # Terminate the server process
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('.env')

    test_email_server()
    test_search_attachments()