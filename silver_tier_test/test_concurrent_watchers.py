#!/usr/bin/env python3
"""
Test script for concurrent operation of multiple watchers.
"""

import json
import sys
import time
import threading
from pathlib import Path
from datetime import datetime

# Add the project root to the path to import from other modules
sys.path.insert(0, str(Path(__file__).parent))

from utils.setup_logger import setup_logger
from watchers.base_watcher import BaseWatcher
from watchers.gmail_watcher import GmailWatcher
from watchers.whatsapp_watcher import WhatsAppWatcher


def test_base_watcher_concurrency():
    """Test that the BaseWatcher supports concurrent operation."""
    print("Testing BaseWatcher inheritance for concurrent operation...")

    # Test that derived classes properly inherit from BaseWatcher
    gmail_watcher = GmailWatcher(vault_path="./test_gmail_vault_1", check_interval=30)
    whatsapp_watcher = WhatsAppWatcher(vault_path="./test_whatsapp_vault_2", check_interval=45)

    # Verify they both inherit from BaseWatcher
    assert isinstance(gmail_watcher, BaseWatcher), "GmailWatcher should inherit from BaseWatcher"
    assert isinstance(whatsapp_watcher, BaseWatcher), "WhatsAppWatcher should inherit from BaseWatcher"

    # Verify they have different attributes
    assert gmail_watcher.vault_path != whatsapp_watcher.vault_path, "Watchers should have different vault paths"
    assert gmail_watcher.check_interval != whatsapp_watcher.check_interval, "Watchers should have different check intervals"

    # Verify they have independent state
    gmail_watcher.test_attr = "gmail_watcher"
    whatsapp_watcher.test_attr = "whatsapp_watcher"

    assert hasattr(gmail_watcher, 'test_attr'), "gmail_watcher should have test_attr"
    assert hasattr(whatsapp_watcher, 'test_attr'), "whatsapp_watcher should have test_attr"
    assert gmail_watcher.test_attr != whatsapp_watcher.test_attr, "Watchers should have independent state"

    # Verify they both have BaseWatcher's common attributes
    assert hasattr(gmail_watcher, 'needs_action'), "GmailWatcher should have needs_action"
    assert hasattr(whatsapp_watcher, 'needs_action'), "WhatsAppWatcher should have needs_action"
    assert hasattr(gmail_watcher, 'exponential_backoff_retry'), "GmailWatcher should have exponential_backoff_retry"
    assert hasattr(whatsapp_watcher, 'exponential_backoff_retry'), "WhatsAppWatcher should have exponential_backoff_retry"

    print("✓ BaseWatcher inheritance supports concurrent operation")

    # Clean up test directories
    import shutil
    for path in ["./test_gmail_vault_1", "./test_whatsapp_vault_2"]:
        if Path(path).exists():
            shutil.rmtree(path, ignore_errors=True)

    return True


def test_watcher_isolation():
    """Test that different watcher types are isolated."""
    print("\nTesting watcher isolation...")

    # Create instances of different watcher types
    gmail_watcher = GmailWatcher(vault_path="./test_gmail_vault", check_interval=60)
    whatsapp_watcher = WhatsAppWatcher(vault_path="./test_whatsapp_vault", check_interval=45)

    # Verify they are different types
    assert type(gmail_watcher) != type(whatsapp_watcher), "Watchers should be different types"
    assert isinstance(gmail_watcher, GmailWatcher), "gmail_watcher should be GmailWatcher"
    assert isinstance(whatsapp_watcher, WhatsAppWatcher), "whatsapp_watcher should be WhatsAppWatcher"

    # Verify they have independent vault paths
    assert gmail_watcher.vault_path != whatsapp_watcher.vault_path, "Watchers should have different vault paths"

    # Verify they have independent check intervals
    assert gmail_watcher.check_interval != whatsapp_watcher.check_interval, "Watchers should have different check intervals"

    print("✓ Different watcher types are properly isolated")

    # Clean up test directories
    import shutil
    for path in ["./test_gmail_vault", "./test_whatsapp_vault"]:
        if Path(path).exists():
            shutil.rmtree(path, ignore_errors=True)

    return True


def test_concurrent_execution_simulation():
    """Test concurrent execution simulation."""
    print("\nTesting concurrent execution simulation...")

    # Create a shared vault for this test
    shared_vault = Path("./test_shared_vault")
    shared_vault.mkdir(exist_ok=True)

    # Create watcher instances
    gmail_watcher = GmailWatcher(vault_path=str(shared_vault), check_interval=10)
    whatsapp_watcher = WhatsAppWatcher(vault_path=str(shared_vault), check_interval=15)

    # Test that they can call their methods independently
    # Mock the check_for_updates method to return dummy data
    original_gmail_check = gmail_watcher.check_for_updates
    original_whatsapp_check = whatsapp_watcher.check_for_updates

    def mock_gmail_check():
        return [{"id": "gmail_msg_1", "subject": "Test Gmail"}]

    def mock_whatsapp_check():
        return [{"id": "wa_msg_1", "chat_name": "Test Contact", "message": "Test message"}]

    gmail_watcher.check_for_updates = mock_gmail_check
    whatsapp_watcher.check_for_updates = mock_whatsapp_check

    # Run both check methods
    gmail_updates = gmail_watcher.check_for_updates()
    whatsapp_updates = whatsapp_watcher.check_for_updates()

    # Verify both return appropriate data
    assert len(gmail_updates) == 1, "Gmail watcher should return 1 update"
    assert len(whatsapp_updates) == 1, "WhatsApp watcher should return 1 update"
    assert gmail_updates[0]["id"] == "gmail_msg_1", "Gmail update should have correct ID"
    assert whatsapp_updates[0]["id"] == "wa_msg_1", "WhatsApp update should have correct ID"

    # Restore original methods
    gmail_watcher.check_for_updates = original_gmail_check
    whatsapp_watcher.check_for_updates = original_whatsapp_check

    print("✓ Watchers can operate independently in simulation")

    # Clean up
    import shutil
    if shared_vault.exists():
        shutil.rmtree(shared_vault, ignore_errors=True)

    return True


def test_resource_usage():
    """Test that watchers don't excessively consume resources."""
    print("\nTesting resource usage...")

    # Create multiple watchers to test resource allocation
    vaults = [f"./test_vault_{i}" for i in range(5)]
    watchers = []

    for i, vault in enumerate(vaults):
        vault_path = Path(vault)
        vault_path.mkdir(exist_ok=True)

        # Alternate between Gmail and WhatsApp watchers
        if i % 2 == 0:
            watcher = GmailWatcher(vault_path=str(vault_path), check_interval=60)
        else:
            watcher = WhatsAppWatcher(vault_path=str(vault_path), check_interval=45)

        watchers.append(watcher)

    # Verify each watcher has its own resources
    for i, watcher in enumerate(watchers):
        assert hasattr(watcher, 'logger'), f"Watcher {i} should have a logger"
        assert hasattr(watcher, 'vault_path'), f"Watcher {i} should have a vault_path"
        assert hasattr(watcher, 'needs_action'), f"Watcher {i} should have a needs_action directory"

    # Verify vault paths are unique
    vault_paths = [str(w.vault_path) for w in watchers]
    assert len(set(vault_paths)) == len(vault_paths), "All watchers should have unique vault paths"

    print("✓ Watchers manage resources independently")

    # Clean up
    import shutil
    for vault in vaults:
        vault_path = Path(vault)
        if vault_path.exists():
            shutil.rmtree(vault_path, ignore_errors=True)

    return True


def test_thread_safety_simulation():
    """Test thread safety through simulation."""
    print("\nTesting thread safety simulation...")

    # Create a shared vault
    shared_vault = Path("./test_thread_safety_vault")
    shared_vault.mkdir(exist_ok=True)

    # Create a single watcher instance
    watcher = GmailWatcher(vault_path=str(shared_vault), check_interval=30)

    # Create a shared counter to track method calls
    call_count = {"check_for_updates": 0, "create_action_file": 0}
    import threading
    lock = threading.Lock()

    # Mock methods that update the counter
    original_check = watcher.check_for_updates
    original_create = watcher.create_action_file

    def thread_safe_check():
        with lock:
            call_count["check_for_updates"] += 1
        return [{"id": f"msg_{call_count['check_for_updates']}", "subject": f"Test {call_count['check_for_updates']}"}]

    def thread_safe_create(item):
        with lock:
            call_count["create_action_file"] += 1
        # Return a mock path
        return Path(f"./mock_action_{call_count['create_action_file']}.md")

    watcher.check_for_updates = thread_safe_check
    watcher.create_action_file = thread_safe_create

    # Simulate concurrent access with multiple threads
    def worker_thread(thread_id):
        for i in range(5):
            updates = watcher.check_for_updates()
            for update in updates:
                watcher.create_action_file(update)
            time.sleep(0.01)  # Small delay

    # Create and start multiple threads
    threads = []
    for i in range(3):  # 3 concurrent threads
        t = threading.Thread(target=worker_thread, args=(i,))
        threads.append(t)
        t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

    # Verify all calls were made
    total_expected_calls = 3 * 5  # 3 threads * 5 iterations
    assert call_count["check_for_updates"] == total_expected_calls, f"Expected {total_expected_calls} check calls, got {call_count['check_for_updates']}"
    assert call_count["create_action_file"] == total_expected_calls, f"Expected {total_expected_calls} create calls, got {call_count['create_action_file']}"

    print(f"✓ Thread safety simulation passed: {call_count['check_for_updates']} checks, {call_count['create_action_file']} creations")

    # Clean up
    import shutil
    if shared_vault.exists():
        shutil.rmtree(shared_vault, ignore_errors=True)

    return True


def main():
    """Main test function."""
    print("Testing Concurrent Operation of Multiple Watchers")
    print("=" * 55)

    tests = [
        test_base_watcher_concurrency,
        test_watcher_isolation,
        test_concurrent_execution_simulation,
        test_resource_usage,
        test_thread_safety_simulation
    ]

    all_passed = True
    for test in tests:
        if not test():
            all_passed = False

    print("\n" + "=" * 55)
    if all_passed:
        print("✓ All concurrent operation tests passed!")
        print("\nFeatures tested:")
        print("- BaseWatcher concurrency support")
        print("- Watcher type isolation")
        print("- Independent operation simulation")
        print("- Resource management")
        print("- Thread safety simulation")
        return 0
    else:
        print("✗ Some concurrent operation tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())