#!/usr/bin/env python3
"""
Test script for plan generation and tracking functionality.
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
from utils.plan_generator import PlanGenerator
from utils.plan_updater import PlanUpdater


def test_plan_generation():
    """Test plan generation functionality."""
    print("Testing plan generation...")

    # Create a test vault structure
    test_vault = Path("./test_plan_vault")
    plans_folder = test_vault / "Plans"
    plans_folder.mkdir(parents=True, exist_ok=True)

    # Create a plan generator
    generator = PlanGenerator(str(test_vault))

    # Test complex task that should trigger plan generation
    complex_task = "Need to develop a comprehensive marketing campaign for our new product launch that will run for 3 months and target young professionals aged 25-35."

    # Verify it's identified as complex
    assert generator.is_complex_task(complex_task), "Complex task should be identified as complex"

    # Generate the plan
    plan_path = generator.generate_plan(complex_task, related_entities=["email_1", "linkedin_post_1"])

    assert plan_path is not None, "Plan should be generated for complex task"
    assert plan_path.exists(), "Plan file should exist"
    print(f"✓ Plan generated: {plan_path}")

    # Verify plan content
    content = plan_path.read_text()
    assert "# " in content, "Plan should have a title header"
    assert "## Tasks" in content, "Plan should have Tasks section"
    assert "- [ ]" in content, "Plan should have tasks with checkboxes"
    assert "## Goals" in content, "Plan should have Goals section"
    assert "## Success Criteria" in content, "Plan should have Success Criteria section"

    print("✓ Plan content is properly structured")

    # Clean up
    shutil.rmtree(test_vault, ignore_errors=True)

    return True


def test_simple_task_not_complex():
    """Test that simple tasks are not considered complex."""
    print("\nTesting simple task identification...")

    # Create a test vault structure
    test_vault = Path("./test_simple_vault")
    test_vault.mkdir(parents=True, exist_ok=True)

    # Create a plan generator
    generator = PlanGenerator(str(test_vault))

    # Test simple task that should not trigger plan generation
    simple_task = "Send an email to John about the meeting."

    # Verify it's not identified as complex
    assert not generator.is_complex_task(simple_task), "Simple task should not be identified as complex"

    # Attempt to generate plan for simple task
    plan_path = generator.generate_plan(simple_task)
    assert plan_path is None, "Plan should not be generated for simple task"

    print("✓ Simple task correctly identified as not complex")

    # Clean up
    shutil.rmtree(test_vault, ignore_errors=True)

    return True


def test_plan_updater():
    """Test plan updating functionality."""
    print("\nTesting plan updating...")

    # Create a test vault structure
    test_vault = Path("./test_update_vault")
    plans_folder = test_vault / "Plans"
    plans_folder.mkdir(parents=True, exist_ok=True)

    # Create a plan generator and updater
    generator = PlanGenerator(str(test_vault))
    updater = PlanUpdater(str(test_vault))

    # Create a test plan
    complex_task = "Develop and execute a comprehensive team building program that involves multiple departments, requires coordination with external vendors, includes multiple phases over several weeks, and requires approval from leadership."
    plan_path = generator.generate_plan(complex_task)

    assert plan_path is not None and plan_path.exists(), "Plan should be created for testing"

    # Get initial status
    initial_status = updater.get_plan_status(str(plan_path))
    print(f"Initial status: {initial_status}")

    # Verify initial state
    assert initial_status['completed_tasks'] == 0, "Initially no tasks should be completed"
    assert initial_status['completion_percentage'] == 0, "Initially completion should be 0%"
    assert initial_status['status'] == 'pending', "Initially status should be pending"

    # Update a task status
    success = updater.mark_task_completed(str(plan_path), 0)  # Mark first task as completed
    assert success, "Task update should succeed"

    # Get updated status
    updated_status = updater.get_plan_status(str(plan_path))
    print(f"Updated status: {updated_status}")

    # Verify updated state
    assert updated_status['completed_tasks'] >= 1, "At least one task should be completed"
    assert updated_status['completion_percentage'] > 0, "Completion percentage should be greater than 0"
    assert updated_status['status'] in ['in_progress', 'completed'], "Status should be in_progress or completed"

    print("✓ Plan updating works correctly")

    # Clean up
    shutil.rmtree(test_vault, ignore_errors=True)

    return True


def test_plan_structure():
    """Test the structure of generated plans."""
    print("\nTesting plan structure...")

    # Create a test vault structure
    test_vault = Path("./test_structure_vault")
    plans_folder = test_vault / "Plans"
    plans_folder.mkdir(parents=True, exist_ok=True)

    # Create a plan generator
    generator = PlanGenerator(str(test_vault))

    # Generate a plan for different types of tasks
    test_tasks = [
        "Conduct comprehensive research on new marketing strategies for Q2 that involves multiple phases, stakeholder interviews, and detailed analysis.",
        "Develop a complex software application with multiple features, user authentication, database integration, and comprehensive testing phases.",
        "Plan a large-scale corporate event with catering, entertainment, multiple venues, logistics coordination, and post-event analysis."
    ]

    for i, task in enumerate(test_tasks):
        plan_path = generator.generate_plan(task)
        assert plan_path is not None, f"Plan should be generated for task {i+1}"

        content = plan_path.read_text()

        # Verify essential sections exist
        assert "## Tasks" in content, f"Plan for task {i+1} should have Tasks section"
        assert "## Goals" in content, f"Plan for task {i+1} should have Goals section"
        assert "## Success Criteria" in content, f"Plan for task {i+1} should have Success Criteria section"

        # Verify tasks have checkboxes
        task_lines = [line for line in content.split('\n') if line.strip().startswith('- [')]
        assert len(task_lines) > 0, f"Plan for task {i+1} should have tasks with checkboxes"

        # Verify frontmatter exists
        assert content.startswith("---"), f"Plan for task {i+1} should have frontmatter"
        assert "type: \"plan_document\"" in content, f"Plan for task {i+1} should have correct type in frontmatter"

        print(f"✓ Plan structure is correct for task {i+1}")

    # Clean up
    shutil.rmtree(test_vault, ignore_errors=True)

    return True


def test_related_entities():
    """Test that related entities are properly linked."""
    print("\nTesting related entity linking...")

    # Create a test vault structure
    test_vault = Path("./test_entities_vault")
    plans_folder = test_vault / "Plans"
    plans_folder.mkdir(parents=True, exist_ok=True)

    # Create a plan generator
    generator = PlanGenerator(str(test_vault))

    # Generate a plan with related entities
    complex_task = "Prepare comprehensive quarterly report analyzing sales performance across multiple regions, requiring coordination with sales teams, integration of multiple data sources, and executive review over several weeks."
    related_entities = ["sales_data_q1", "sales_data_q2", "email_from_manager", "meeting_notes"]

    plan_path = generator.generate_plan(complex_task, related_entities=related_entities)

    assert plan_path is not None, "Plan should be generated with related entities"

    content = plan_path.read_text()

    # Verify related entities are linked
    assert "## Related Entities" in content, "Plan should have Related Entities section"

    for entity in related_entities:
        assert f"[[{entity}]]" in content, f"Related entity {entity} should be linked in plan"

    print("✓ Related entities are properly linked")

    # Clean up
    shutil.rmtree(test_vault, ignore_errors=True)

    return True


def test_priority_estimation():
    """Test priority and duration estimation."""
    print("\nTesting priority and duration estimation...")

    # Create a test vault structure
    test_vault = Path("./test_priority_vault")
    plans_folder = test_vault / "Plans"
    plans_folder.mkdir(parents=True, exist_ok=True)

    # Create a plan generator
    generator = PlanGenerator(str(test_vault))

    # Test tasks with different priorities
    test_cases = [
        ("Urgent: Need to fix critical security vulnerability that affects customer data and requires immediate patching, coordination with security teams, and communication to stakeholders ASAP", "high"),
        ("Plan comprehensive next quarter's marketing campaign that involves multiple channels, budget allocation, creative development, and performance tracking", "medium"),
        ("Research new technologies for future implementation that requires evaluation, proof of concepts, team training, and integration planning", "medium"),
    ]

    for task, expected_priority in test_cases:
        plan_path = generator.generate_plan(task)
        assert plan_path is not None, f"Plan should be generated for task: {task}"

        content = plan_path.read_text()

        # Check that priority is set in frontmatter
        assert f"priority: \"{expected_priority}\"" in content or f"priority: {expected_priority}" in content, \
               f"Plan for '{task}' should have priority '{expected_priority}'"

        # Check that duration is estimated
        assert "estimated_duration" in content, f"Plan for '{task}' should have estimated duration"

        print(f"✓ Priority correctly estimated for: {task}")

    # Clean up
    shutil.rmtree(test_vault, ignore_errors=True)

    return True


def main():
    """Main test function."""
    print("Testing Plan Generation and Tracking Functionality")
    print("=" * 60)

    tests = [
        test_plan_generation,
        test_simple_task_not_complex,
        test_plan_updater,
        test_plan_structure,
        test_related_entities,
        test_priority_estimation
    ]

    all_passed = True
    for test in tests:
        if not test():
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All plan functionality tests passed!")
        print("\nFeatures tested:")
        print("- Plan generation for complex tasks")
        print("- Identification of simple vs complex tasks")
        print("- Plan updating and status tracking")
        print("- Proper plan structure and formatting")
        print("- Related entity linking")
        print("- Priority and duration estimation")
        return 0
    else:
        print("✗ Some plan functionality tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())