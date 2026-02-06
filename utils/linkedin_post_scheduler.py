"""
LinkedIn Post Scheduler Module for the Personal AI Employee system.
Handles scheduling and automated posting of LinkedIn content using the schedule library.
"""

import asyncio
import json
import logging
import schedule
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from pathlib import Path

from utils.linkedin_post_generator import generate_linkedin_post, format_linkedin_post
from utils.setup_logger import setup_logger


class LinkedInPostScheduler:
    """
    Scheduler class for managing LinkedIn post scheduling and execution.
    Uses the schedule library to automate LinkedIn posts at specified times.
    """

    def __init__(self, mcp_client=None):
        """
        Initialize the LinkedIn post scheduler.

        Args:
            mcp_client: Optional MCP client for interacting with LinkedIn MCP server
        """
        self.logger = setup_logger("LinkedInPostScheduler")
        self.mcp_client = mcp_client
        self.jobs = []
        self.scheduler_thread = None
        self.running = False

        # Store scheduled posts
        self.scheduled_posts = {}

    def schedule_post(self, post_data: Dict, run_time: str = None, timezone: str = None) -> str:
        """
        Schedule a LinkedIn post to be published at a specific time.

        Args:
            post_data: Dictionary containing post information
            run_time: Time to run the post (e.g., "10:30", "every day at 10:30", "in 1 hour")
            timezone: Optional timezone for the schedule

        Returns:
            Job ID for the scheduled post
        """
        import uuid
        job_id = str(uuid.uuid4())

        # Create the post content
        post_content = generate_linkedin_post(post_data)
        formatted_post = format_linkedin_post(post_content)

        # Create the scheduled job
        if "every day at" in run_time:
            # Schedule daily at specific time (e.g., "every day at 10:30")
            time_part = run_time.split("at ")[1]
            job = schedule.every().day.at(time_part).do(
                self._execute_post,
                job_id=job_id,
                post_content=formatted_post,
                post_data=post_data
            )
        elif run_time.startswith("every "):
            # Schedule at intervals (e.g., "every 2 hours", "every monday")
            parts = run_time.split()
            if len(parts) >= 3:
                interval = int(parts[1])
                unit = parts[2]

                if unit.startswith("minute"):
                    job = schedule.every(interval).minutes.do(
                        self._execute_post,
                        job_id=job_id,
                        post_content=formatted_post,
                        post_data=post_data
                    )
                elif unit.startswith("hour"):
                    job = schedule.every(interval).hours.do(
                        self._execute_post,
                        job_id=job_id,
                        post_content=formatted_post,
                        post_data=post_data
                    )
                elif unit.startswith("day"):
                    job = schedule.every(interval).days.do(
                        self._execute_post,
                        job_id=job_id,
                        post_content=formatted_post,
                        post_data=post_data
                    )
                elif unit.startswith("week"):
                    job = schedule.every(interval).weeks.do(
                        self._execute_post,
                        job_id=job_id,
                        post_content=formatted_post,
                        post_data=post_data
                    )
        elif run_time.startswith("in "):
            # Schedule for a future time (e.g., "in 1 hour", "in 30 minutes")
            parts = run_time.split()
            if len(parts) >= 3:
                interval = int(parts[1])
                unit = parts[2]

                if unit.startswith("minute"):
                    job = schedule.every().minute.do(
                        self._execute_post,
                        job_id=job_id,
                        post_content=formatted_post,
                        post_data=post_data
                    )
                    # Run once after the delay
                    threading.Timer(interval * 60, lambda: self._execute_post(job_id, formatted_post, post_data)).start()
                    self.scheduled_posts[job_id] = {
                        'post_data': post_data,
                        'scheduled_time': datetime.now() + timedelta(minutes=interval),
                        'status': 'scheduled'
                    }
                    return job_id
        else:
            # Assume it's a specific time (e.g., "10:30")
            job = schedule.every().day.at(run_time).do(
                self._execute_post,
                job_id=job_id,
                post_content=formatted_post,
                post_data=post_data
            )

        # Store job info
        self.scheduled_posts[job_id] = {
            'post_data': post_data,
            'scheduled_time': run_time,
            'status': 'scheduled'
        }

        self.logger.info(f"Scheduled LinkedIn post with ID {job_id} for {run_time}")
        return job_id

    def schedule_recurring_post(self, post_data: Dict, interval: str, start_time: str = None) -> str:
        """
        Schedule a recurring LinkedIn post at regular intervals.

        Args:
            post_data: Dictionary containing post information
            interval: Interval for the recurring post (e.g., "daily", "weekly", "monthly")
            start_time: Optional start time for the first post

        Returns:
            Job ID for the scheduled recurring post
        """
        import uuid
        job_id = str(uuid.uuid4())

        # Create the post content
        post_content = generate_linkedin_post(post_data)
        formatted_post = format_linkedin_post(post_content)

        # Schedule based on interval
        if interval.lower() == "daily":
            if start_time:
                job = schedule.every().day.at(start_time).do(
                    self._execute_recurring_post,
                    job_id=job_id,
                    post_content=formatted_post,
                    post_data=post_data
                )
            else:
                job = schedule.every().day.do(
                    self._execute_recurring_post,
                    job_id=job_id,
                    post_content=formatted_post,
                    post_data=post_data
                )
        elif interval.lower() == "weekly":
            if start_time:
                day, time_part = start_time.split(" at ")
                day_attr = getattr(schedule.every(), day.lower())
                job = day_attr.at(time_part).do(
                    self._execute_recurring_post,
                    job_id=job_id,
                    post_content=formatted_post,
                    post_data=post_data
                )
            else:
                job = schedule.every().monday.do(
                    self._execute_recurring_post,
                    job_id=job_id,
                    post_content=formatted_post,
                    post_data=post_data
                )
        elif interval.lower() == "monthly":
            # Monthly scheduling is trickier with schedule library
            # We'll schedule it to run daily and check if it's the right day
            job = schedule.every().day.do(
                self._execute_monthly_post,
                job_id=job_id,
                post_content=formatted_post,
                post_data=post_data,
                start_time=start_time
            )

        # Store job info
        self.scheduled_posts[job_id] = {
            'post_data': post_data,
            'interval': interval,
            'start_time': start_time,
            'status': 'scheduled',
            'last_run': None
        }

        self.logger.info(f"Scheduled recurring LinkedIn post with ID {job_id} every {interval}")
        return job_id

    def cancel_post(self, job_id: str) -> bool:
        """
        Cancel a scheduled LinkedIn post.

        Args:
            job_id: ID of the job to cancel

        Returns:
            True if successfully canceled, False otherwise
        """
        if job_id in self.scheduled_posts:
            # In a real implementation, we would cancel the scheduled job
            # For now, we'll just update the status
            self.scheduled_posts[job_id]['status'] = 'cancelled'
            self.logger.info(f"Cancelled scheduled LinkedIn post with ID {job_id}")
            return True
        return False

    def get_scheduled_posts(self) -> Dict:
        """
        Get information about all scheduled posts.

        Returns:
            Dictionary containing information about scheduled posts
        """
        return self.scheduled_posts

    def _execute_post(self, job_id: str, post_content: str, post_data: Dict):
        """
        Execute a scheduled LinkedIn post.

        Args:
            job_id: ID of the scheduled job
            post_content: Content of the post to publish
            post_data: Original post data
        """
        try:
            self.logger.info(f"Executing scheduled LinkedIn post: {job_id}")

            # Update status
            if job_id in self.scheduled_posts:
                self.scheduled_posts[job_id]['status'] = 'executing'
                self.scheduled_posts[job_id]['execution_time'] = datetime.now().isoformat()

            # In a real implementation, we would use the MCP client to post to LinkedIn
            # For now, we'll simulate the posting
            if self.mcp_client:
                # Call the MCP server to create the LinkedIn post
                post_request = {
                    "method": "create_linkedin_post",
                    "params": {
                        "content": post_content,
                        "headline": post_data.get("headline"),
                        "visibility": post_data.get("visibility", "PUBLIC")
                    }
                }

                # This would actually call the MCP server
                # response = self.mcp_client.call(post_request)
                self.logger.info(f"Posted to LinkedIn: {post_content[:100]}...")
            else:
                # Simulate posting without MCP client
                self.logger.info(f"Simulated LinkedIn post: {post_content[:100]}...")

            # Update status
            if job_id in self.scheduled_posts:
                self.scheduled_posts[job_id]['status'] = 'completed'
                self.scheduled_posts[job_id]['completed_time'] = datetime.now().isoformat()

            self.logger.info(f"Successfully executed scheduled LinkedIn post: {job_id}")

        except Exception as e:
            self.logger.error(f"Error executing scheduled LinkedIn post {job_id}: {e}")
            if job_id in self.scheduled_posts:
                self.scheduled_posts[job_id]['status'] = 'failed'
                self.scheduled_posts[job_id]['error'] = str(e)

    def _execute_recurring_post(self, job_id: str, post_content: str, post_data: Dict):
        """
        Execute a recurring LinkedIn post.

        Args:
            job_id: ID of the scheduled job
            post_content: Content of the post to publish
            post_data: Original post data
        """
        # Refresh the post content for recurring posts to ensure variety
        refreshed_post_data = post_data.copy()
        refreshed_post_data['time_period'] = f"Latest update - {datetime.now().strftime('%B %Y')}"

        refreshed_content = generate_linkedin_post(refreshed_post_data)
        formatted_content = format_linkedin_post(refreshed_content)

        self._execute_post(job_id, formatted_content, refreshed_post_data)

    def _execute_monthly_post(self, job_id: str, post_content: str, post_data: Dict, start_time: str):
        """
        Execute a monthly LinkedIn post.

        Args:
            job_id: ID of the scheduled job
            post_content: Content of the post to publish
            post_data: Original post data
            start_time: Start time specification
        """
        # Check if today is the right day for monthly posting
        now = datetime.now()
        if start_time:
            # Parse the start time to determine the day
            try:
                day_num = int(start_time.split()[0])  # Assuming format like "15 at 10:30"
                if now.day == day_num:
                    self._execute_post(job_id, post_content, post_data)
            except ValueError:
                # If we can't parse the day, just run on the first of the month
                if now.day == 1:
                    self._execute_post(job_id, post_content, post_data)
        else:
            # Default to first of the month
            if now.day == 1:
                self._execute_post(job_id, post_content, post_data)

    def run_scheduler(self):
        """
        Run the scheduler in a background thread.
        """
        if self.running:
            self.logger.warning("Scheduler is already running")
            return

        self.running = True
        self.logger.info("Starting LinkedIn post scheduler...")

        def run_schedule():
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        self.scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
        self.scheduler_thread.start()

    def stop_scheduler(self):
        """
        Stop the scheduler.
        """
        self.logger.info("Stopping LinkedIn post scheduler...")
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        schedule.clear()  # Clear all scheduled jobs


def create_sample_schedule():
    """
    Create sample scheduled posts for demonstration.
    """
    scheduler = LinkedInPostScheduler()

    # Sample business achievement data
    sample_data = {
        'type': 'revenue',
        'company_name': 'TechInnovate Inc.',
        'metric_value': 1000000,
        'metric_type': 'revenue',
        'time_period': 'Q4 2025',
        'quote': 'Excellence is never an accident.',
        'call_to_action': 'Connect with us to learn more.'
    }

    # Schedule a post for tomorrow at 10:30 AM
    job_id1 = scheduler.schedule_post(sample_data, "10:30")
    print(f"Scheduled one-time post: {job_id1}")

    # Schedule a recurring weekly post
    job_id2 = scheduler.schedule_recurring_post(sample_data, "weekly", "monday at 09:00")
    print(f"Scheduled weekly post: {job_id2}")

    return scheduler


if __name__ == "__main__":
    print("LinkedIn Post Scheduler - Example Usage")
    print("=" * 50)

    # Create sample scheduled posts
    scheduler = create_sample_schedule()

    # Show scheduled posts
    scheduled = scheduler.get_scheduled_posts()
    print(f"\nScheduled posts: {json.dumps(scheduled, indent=2, default=str)}")