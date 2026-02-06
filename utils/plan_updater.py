"""
Plan Updater Module for the Personal AI Employee system.
Updates plan status as tasks are completed and tracks overall progress.
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from utils.setup_logger import setup_logger
from utils.file_utils import read_markdown_file, write_markdown_file


class PlanUpdater:
    """
    Class to update plan status as tasks are completed.
    """

    def __init__(self, vault_path: str):
        """
        Initialize the plan updater.

        Args:
            vault_path: Path to the Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.logger = setup_logger("PlanUpdater", level=logging.INFO)

    def update_task_status(self, plan_path: str, task_index: int, completed: bool = True) -> bool:
        """
        Update the status of a specific task in a plan.

        Args:
            plan_path: Path to the plan file
            task_index: Index of the task to update (0-based)
            completed: Whether the task is completed (True) or not (False)

        Returns:
            True if successfully updated, False otherwise
        """
        try:
            # Read the current plan content
            content = read_markdown_file(plan_path)

            # Parse frontmatter and content
            frontmatter, body = self._parse_frontmatter(content)

            # Update the task status in the body
            updated_body = self._update_task_in_body(body, task_index, completed)

            # Update the frontmatter with new completion stats
            updated_frontmatter = self._update_completion_stats(frontmatter, updated_body)

            # Reconstruct the content with updated frontmatter
            updated_content = self._reconstruct_content(updated_frontmatter, updated_body)

            # Write the updated content back to the file
            write_markdown_file(plan_path, updated_content)

            self.logger.info(f"Updated task {task_index} status in plan: {plan_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating task status in plan {plan_path}: {e}")
            return False

    def mark_task_completed(self, plan_path: str, task_index: int) -> bool:
        """
        Mark a specific task as completed.

        Args:
            plan_path: Path to the plan file
            task_index: Index of the task to mark as completed

        Returns:
            True if successfully updated, False otherwise
        """
        return self.update_task_status(plan_path, task_index, completed=True)

    def mark_task_incomplete(self, plan_path: str, task_index: int) -> bool:
        """
        Mark a specific task as incomplete.

        Args:
            plan_path: Path to the plan file
            task_index: Index of the task to mark as incomplete

        Returns:
            True if successfully updated, False otherwise
        """
        return self.update_task_status(plan_path, task_index, completed=False)

    def update_goal_status(self, plan_path: str, goal_index: int, completed: bool = True) -> bool:
        """
        Update the status of a specific goal in a plan.

        Args:
            plan_path: Path to the plan file
            goal_index: Index of the goal to update (0-based)
            completed: Whether the goal is completed (True) or not (False)

        Returns:
            True if successfully updated, False otherwise
        """
        try:
            # Read the current plan content
            content = read_markdown_file(plan_path)

            # Parse frontmatter and content
            frontmatter, body = self._parse_frontmatter(content)

            # Update the goal status in the body
            updated_body = self._update_goal_in_body(body, goal_index, completed)

            # Update the frontmatter with new completion stats
            updated_frontmatter = self._update_completion_stats(frontmatter, updated_body)

            # Reconstruct the content with updated frontmatter
            updated_content = self._reconstruct_content(updated_frontmatter, updated_body)

            # Write the updated content back to the file
            write_markdown_file(plan_path, updated_content)

            self.logger.info(f"Updated goal {goal_index} status in plan: {plan_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating goal status in plan {plan_path}: {e}")
            return False

    def update_success_criterion_status(self, plan_path: str, criterion_index: int, completed: bool = True) -> bool:
        """
        Update the status of a specific success criterion in a plan.

        Args:
            plan_path: Path to the plan file
            criterion_index: Index of the success criterion to update (0-based)
            completed: Whether the criterion is completed (True) or not (False)

        Returns:
            True if successfully updated, False otherwise
        """
        try:
            # Read the current plan content
            content = read_markdown_file(plan_path)

            # Parse frontmatter and content
            frontmatter, body = self._parse_frontmatter(content)

            # Update the success criterion status in the body
            updated_body = self._update_success_criterion_in_body(body, criterion_index, completed)

            # Update the frontmatter with new completion stats
            updated_frontmatter = self._update_completion_stats(frontmatter, updated_body)

            # Reconstruct the content with updated frontmatter
            updated_content = self._reconstruct_content(updated_frontmatter, updated_body)

            # Write the updated content back to the file
            write_markdown_file(plan_path, updated_content)

            self.logger.info(f"Updated success criterion {criterion_index} status in plan: {plan_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating success criterion status in plan {plan_path}: {e}")
            return False

    def _parse_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """
        Parse YAML frontmatter from markdown content.

        Args:
            content: Markdown content with potential frontmatter

        Returns:
            Tuple of (frontmatter_dict, content_without_frontmatter)
        """
        lines = content.split('\n')

        if len(lines) >= 3 and lines[0].strip() == '---':
            # Look for closing ---
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    # Extract frontmatter
                    frontmatter_str = '\n'.join(lines[1:i])
                    frontmatter = {}

                    # Simple parsing of frontmatter (key: value format)
                    for fm_line in frontmatter_str.split('\n'):
                        if ':' in fm_line:
                            key, value = fm_line.split(':', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')  # Remove quotes

                            # Try to parse as JSON if it looks like a list or dict
                            if value.startswith('[') or value.startswith('{'):
                                try:
                                    value = json.loads(value)
                                except:
                                    pass  # Keep as string if JSON parsing fails

                            frontmatter[key] = value

                    # Return frontmatter and remaining content
                    remaining_content = '\n'.join(lines[i+1:]).strip()
                    return frontmatter, remaining_content

        # No frontmatter found
        return {}, content

    def _update_task_in_body(self, body: str, task_index: int, completed: bool) -> str:
        """
        Update the status of a specific task in the body content.

        Args:
            body: Body content of the plan
            task_index: Index of the task to update (0-based)
            completed: Whether the task is completed

        Returns:
            Updated body content
        """
        lines = body.split('\n')
        task_counter = 0
        task_pattern = r'^(\s*)-\s*\[([ xX]?)\]\s*(\*\*.*?\*\*.*?)$'

        for i, line in enumerate(lines):
            if re.match(task_pattern, line):
                if task_counter == task_index:
                    match = re.match(task_pattern, line)
                    if match:
                        indent, status, task_desc = match.groups()
                        new_status = 'x' if completed else ' '
                        lines[i] = f"{indent}- [{new_status}] {task_desc}"
                        break
                task_counter += 1

        return '\n'.join(lines)

    def _update_goal_in_body(self, body: str, goal_index: int, completed: bool) -> str:
        """
        Update the status of a specific goal in the body content.

        Args:
            body: Body content of the plan
            goal_index: Index of the goal to update (0-based)
            completed: Whether the goal is completed

        Returns:
            Updated body content
        """
        lines = body.split('\n')
        goal_counter = 0
        goal_pattern = r'^(\s*)-\s*\[([ xX]?)\]\s*(.*)$'

        in_goals_section = False

        for i, line in enumerate(lines):
            stripped_line = line.strip()

            # Check if we're in the Goals section
            if stripped_line.startswith('## Goals'):
                in_goals_section = True
                continue
            elif stripped_line.startswith('## ') and not stripped_line.startswith('## Goals'):
                in_goals_section = False
                continue

            if in_goals_section and re.match(goal_pattern, line):
                if goal_counter == goal_index:
                    match = re.match(goal_pattern, line)
                    if match:
                        indent, status, goal_desc = match.groups()
                        new_status = 'x' if completed else ' '
                        lines[i] = f"{indent}- [{new_status}] {goal_desc}"
                        break
                goal_counter += 1

        return '\n'.join(lines)

    def _update_success_criterion_in_body(self, body: str, criterion_index: int, completed: bool) -> str:
        """
        Update the status of a specific success criterion in the body content.

        Args:
            body: Body content of the plan
            criterion_index: Index of the success criterion to update (0-based)
            completed: Whether the criterion is completed

        Returns:
            Updated body content
        """
        lines = body.split('\n')
        criterion_counter = 0
        criterion_pattern = r'^(\s*)-\s*\[([ xX]?)\]\s*(.*)$'

        in_success_criteria_section = False

        for i, line in enumerate(lines):
            stripped_line = line.strip()

            # Check if we're in the Success Criteria section
            if stripped_line.startswith('## Success Criteria'):
                in_success_criteria_section = True
                continue
            elif stripped_line.startswith('## ') and not stripped_line.startswith('## Success Criteria'):
                in_success_criteria_section = False
                continue

            if in_success_criteria_section and re.match(criterion_pattern, line):
                if criterion_counter == criterion_index:
                    match = re.match(criterion_pattern, line)
                    if match:
                        indent, status, criterion_desc = match.groups()
                        new_status = 'x' if completed else ' '
                        lines[i] = f"{indent}- [{new_status}] {criterion_desc}"
                        break
                criterion_counter += 1

        return '\n'.join(lines)

    def _update_completion_stats(self, frontmatter: Dict, body: str) -> Dict:
        """
        Update completion statistics in the frontmatter based on the body content.

        Args:
            frontmatter: Current frontmatter dictionary
            body: Body content of the plan

        Returns:
            Updated frontmatter dictionary
        """
        # Count total and completed tasks
        total_tasks, completed_tasks = self._count_tasks(body)

        # Update the frontmatter
        updated_frontmatter = frontmatter.copy()
        updated_frontmatter['total_tasks'] = total_tasks
        updated_frontmatter['completed_tasks'] = completed_tasks

        # Calculate completion percentage
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Update status based on completion percentage
        if completion_percentage >= 100:
            updated_frontmatter['status'] = 'completed'
        elif completion_percentage > 0:
            updated_frontmatter['status'] = 'in_progress'
        else:
            updated_frontmatter['status'] = 'pending'

        # Update the completion percentage in frontmatter
        updated_frontmatter['completion_percentage'] = completion_percentage
        updated_frontmatter['updated'] = datetime.now().isoformat()

        return updated_frontmatter

    def _count_tasks(self, body: str) -> Tuple[int, int]:
        """
        Count total and completed tasks in the body content.

        Args:
            body: Body content of the plan

        Returns:
            Tuple of (total_tasks, completed_tasks)
        """
        lines = body.split('\n')
        total_tasks = 0
        completed_tasks = 0

        # Pattern to match task lines: - [x] or - [ ] followed by content
        task_pattern = r'^\s*-\s*\[([ xX]?)\]\s*(\*\*.*?\*\*.*?)$'

        for line in lines:
            if re.match(task_pattern, line):
                total_tasks += 1
                match = re.match(task_pattern, line)
                if match:
                    status = match.group(1)
                    if status.lower() in ['x']:
                        completed_tasks += 1

        return total_tasks, completed_tasks

    def _reconstruct_content(self, frontmatter: Dict, body: str) -> str:
        """
        Reconstruct the full content from frontmatter and body.

        Args:
            frontmatter: Frontmatter dictionary
            body: Body content

        Returns:
            Full markdown content
        """
        # Build frontmatter string
        frontmatter_str = "---\n"
        for key, value in frontmatter.items():
            if isinstance(value, list):
                # Format list values
                frontmatter_str += f"{key}: {json.dumps(value)}\n"
            elif isinstance(value, (dict, bool, int, float)):
                # Format other types appropriately
                if isinstance(value, bool):
                    value_str = str(value).lower()
                else:
                    value_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
                frontmatter_str += f"{key}: {value_str}\n"
            else:
                # String values
                frontmatter_str += f"{key}: \"{value}\"\n"
        frontmatter_str += "---\n\n"

        return frontmatter_str + body

    def get_plan_status(self, plan_path: str) -> Dict:
        """
        Get the current status of a plan including completion statistics.

        Args:
            plan_path: Path to the plan file

        Returns:
            Dictionary with plan status information
        """
        try:
            content = read_markdown_file(plan_path)
            frontmatter, body = self._parse_frontmatter(content)

            total_tasks, completed_tasks = self._count_tasks(body)

            completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

            return {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'pending_tasks': total_tasks - completed_tasks,
                'completion_percentage': completion_percentage,
                'status': frontmatter.get('status', 'unknown'),
                'title': frontmatter.get('title', 'Unknown'),
                'created': frontmatter.get('created', 'Unknown'),
                'updated': frontmatter.get('updated', 'Never')
            }
        except Exception as e:
            self.logger.error(f"Error getting plan status for {plan_path}: {e}")
            return {}


def get_plan_updater(vault_path: str) -> PlanUpdater:
    """
    Get a PlanUpdater instance for the specified vault.

    Args:
        vault_path: Path to the Obsidian vault

    Returns:
        PlanUpdater instance
    """
    return PlanUpdater(vault_path)


if __name__ == "__main__":
    # Example usage
    import logging

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Create a plan updater
    updater = PlanUpdater("./test_vault")

    print("Plan Updater initialized")
    print("Use mark_task_completed(plan_path, task_index) to update task status")
    print("Use get_plan_status(plan_path) to get current plan status")