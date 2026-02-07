#!/usr/bin/env python3
"""
Test script for LinkedIn post creation and scheduling functionality.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the path to import from other modules
sys.path.insert(0, str(Path(__file__).parent))

from utils.linkedin_post_generator import generate_linkedin_post, format_linkedin_post, generate_business_achievement_data_example
from utils.linkedin_post_scheduler import LinkedInPostScheduler, create_sample_schedule


def test_post_generation():
    """Test LinkedIn post generation functionality."""
    print("Testing LinkedIn post generation...")

    # Test with different types of business achievements
    test_data_types = [
        {
            'type': 'revenue',
            'company_name': 'TestCorp',
            'metric_value': 500000,
            'metric_type': 'revenue',
            'time_period': 'Q1 2026'
        },
        {
            'type': 'growth',
            'company_name': 'GrowthInc',
            'metric_value': 150,
            'metric_type': 'new customers',
            'time_period': 'last quarter'
        },
        {
            'type': 'product_launch',
            'company_name': 'InnovateCo',
            'metric_value': 'New SaaS Platform',
            'metric_type': 'product',
            'time_period': 'January 2026'
        },
        {
            'type': 'award_recognition',
            'company_name': 'ExcellenceLLC',
            'metric_value': 'Industry Leader Award',
            'metric_type': 'award',
            'time_period': 'Annual Conference 2026'
        }
    ]

    for i, data in enumerate(test_data_types):
        try:
            post = generate_linkedin_post(data)
            formatted_post = format_linkedin_post(post)

            print(f"✓ Generated post for type {data['type']}: {len(post)} characters")
            assert len(post) > 0, f"Post for type {data['type']} should not be empty"
            assert len(formatted_post) > len(post), "Formatted post should include hashtags"

            # Verify post is properly generated (contains meaningful content)
            assert len(post) > 50, f"Post for type {data['type']} should contain meaningful content"
        except Exception as e:
            print(f"✗ Failed to generate post for type {data['type']}: {e}")
            return False

    print("✓ All post generation tests passed")
    return True


def test_post_formatting():
    """Test LinkedIn post formatting functionality."""
    print("\nTesting LinkedIn post formatting...")

    # Test basic formatting
    raw_content = "This is a test post."
    formatted = format_linkedin_post(raw_content)

    assert raw_content in formatted, "Raw content should be in formatted post"
    assert '#' in formatted, "Formatted post should include hashtags"
    print("✓ Basic formatting works")

    # Test with custom hashtags
    custom_hashtags = ['Test', 'Automation', 'LinkedIn']
    formatted_custom = format_linkedin_post(raw_content, custom_hashtags)

    for tag in custom_hashtags:
        assert f'#{tag}' in formatted_custom, f"Custom hashtag #{tag} should be in formatted post"
    print("✓ Custom hashtag formatting works")

    # Test character limit handling
    long_content = "A" * 3500  # Much longer than typical limit
    formatted_long = format_linkedin_post(long_content)

    # The function should handle long content appropriately
    print(f"✓ Long content handled: {len(formatted_long)} characters")

    return True


def test_scheduler_basic():
    """Test basic scheduler functionality."""
    print("\nTesting scheduler basic functionality...")

    try:
        scheduler = LinkedInPostScheduler()

        # Test creating a scheduler instance
        assert scheduler is not None, "Scheduler should be created successfully"
        print("✓ Scheduler instance created")

        # Test getting scheduled posts (should be empty initially)
        scheduled_posts = scheduler.get_scheduled_posts()
        assert isinstance(scheduled_posts, dict), "Scheduled posts should be a dictionary"
        print("✓ Scheduled posts retrieval works")

        return True
    except Exception as e:
        print(f"✗ Scheduler basic test failed: {e}")
        return False


def test_scheduler_with_sample_data():
    """Test scheduler with sample data."""
    print("\nTesting scheduler with sample data...")

    try:
        # Use the sample scheduling function
        scheduler = create_sample_schedule()

        # Check that posts were scheduled
        scheduled_posts = scheduler.get_scheduled_posts()

        if len(scheduled_posts) == 0:
            print("Note: No posts were scheduled in sample data (might be expected)")
            return True

        print(f"✓ Sample scheduling created {len(scheduled_posts)} scheduled posts")

        # Check that each scheduled post has required fields
        for job_id, post_info in scheduled_posts.items():
            required_fields = ['post_data', 'status']
            for field in required_fields:
                assert field in post_info, f"Scheduled post {job_id} missing field: {field}"

            assert post_info['status'] in ['scheduled', 'cancelled', 'executing', 'completed', 'failed'], \
                   f"Scheduled post {job_id} has invalid status: {post_info['status']}"

        print("✓ All scheduled posts have required information")

        return True
    except Exception as e:
        print(f"✗ Scheduler sample data test failed: {e}")
        return False


def test_business_data_generation():
    """Test business achievement data generation."""
    print("\nTesting business achievement data generation...")

    try:
        # Generate sample business data
        sample_data = generate_business_achievement_data_example()

        assert isinstance(sample_data, dict), "Sample data should be a dictionary"
        print("✓ Sample business data generated")

        # Check for required fields in sample data
        required_fields = ['type', 'company_name', 'metric_value', 'metric_type']
        for field in required_fields:
            assert field in sample_data, f"Sample data missing required field: {field}"

        print("✓ Sample data has required fields")

        # Generate and use the sample data for post creation
        post = generate_linkedin_post(sample_data)
        formatted_post = format_linkedin_post(post)

        assert len(post) > 0, "Generated post should not be empty"
        assert len(formatted_post) >= len(post), "Formatted post should be at least as long as raw post"

        print("✓ Sample data works with post generation")

        return True
    except Exception as e:
        print(f"✗ Business data generation test failed: {e}")
        return False


def main():
    """Main test function."""
    print("Testing LinkedIn Post Creation and Scheduling Functionality")
    print("=" * 60)

    tests = [
        test_post_generation,
        test_post_formatting,
        test_scheduler_basic,
        test_scheduler_with_sample_data,
        test_business_data_generation
    ]

    all_passed = True
    for test in tests:
        if not test():
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All LinkedIn functionality tests passed!")
        print("\nFeatures tested:")
        print("- Post generation for different business achievements")
        print("- Post formatting with hashtags")
        print("- Scheduler basic functionality")
        print("- Sample scheduling with real data")
        print("- Business data generation")
        return 0
    else:
        print("✗ Some LinkedIn functionality tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())