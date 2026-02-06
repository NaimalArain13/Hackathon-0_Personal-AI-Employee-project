"""
Plan Generator Module for the Personal AI Employee system.
Generates structured Plan.md files for complex multi-step tasks.
"""

import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from utils.setup_logger import setup_logger
from utils.file_utils import create_action_file


class PlanGenerator:
    """
    Class to generate structured plans for complex multi-step tasks.
    """

    def __init__(self, vault_path: str):
        """
        Initialize the plan generator.

        Args:
            vault_path: Path to the Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.logger = setup_logger("PlanGenerator", level=logging.INFO)

        # Define patterns for identifying complex tasks
        self.complex_task_indicators = [
            r'project', r'initiative', r'campaign', r'strategy',
            r'launch', r'development', r'implementation', r'research',
            r'analysis', r'planning', r'coordination', r'collaboration'
        ]

        # Define common task patterns that indicate complexity
        self.complexity_indicators = [
            r'multiple steps', r'over several weeks', r'with multiple teams',
            r'involving.*research', r'requiring.*approval', r'coordinating.*with',
            r'needs to be done in phases', r'consists of.*steps'
        ]

    def is_complex_task(self, task_description: str) -> bool:
        """
        Determine if a task is complex enough to warrant a plan.

        Args:
            task_description: Description of the task to analyze

        Returns:
            True if the task is complex, False otherwise
        """
        task_lower = task_description.lower()

        # Check for complex task indicators
        for indicator in self.complex_task_indicators:
            if re.search(indicator, task_lower, re.IGNORECASE):
                return True

        # Check for complexity indicators
        for complexity_indicator in self.complexity_indicators:
            if re.search(complexity_indicator, task_lower, re.IGNORECASE):
                return True

        # Count potential subtasks (indicated by keywords like "and", "then", "after")
        subtask_words = ['and', 'then', 'after', 'followed by', 'next', 'finally']
        subtask_count = sum(1 for word in subtask_words if word in task_lower)

        # If there are multiple potential subtasks, consider it complex
        if subtask_count >= 2:
            return True

        # Check for numbered lists or sequences
        if re.search(r'\d+\.', task_lower) or re.search(r'(first|second|third|step)', task_lower):
            return True

        return False

    def generate_plan_structure(self, task_description: str) -> Dict:
        """
        Generate a structured plan based on the task description.

        Args:
            task_description: Description of the complex task

        Returns:
            Dictionary containing the plan structure
        """
        # Extract key information from the task description
        title = self._extract_title(task_description)
        description = task_description

        # Generate appropriate tasks based on the task type
        tasks = self._generate_tasks(task_description)

        # Generate goals based on the task
        goals = self._generate_goals(task_description)

        # Estimate timeline based on complexity
        estimated_duration = self._estimate_duration(len(tasks))

        # Determine priority based on urgency keywords
        priority = self._determine_priority(task_description)

        # Generate dependencies
        dependencies = self._generate_dependencies(tasks)

        # Generate success criteria
        success_criteria = self._generate_success_criteria(tasks)

        return {
            'title': title,
            'description': description,
            'tasks': tasks,
            'goals': goals,
            'estimated_duration': estimated_duration,
            'priority': priority,
            'dependencies': dependencies,
            'success_criteria': success_criteria,
            'resources_needed': self._generate_resources(tasks),
            'timeline': self._generate_timeline(len(tasks)),
            'notes': self._generate_notes(task_description)
        }

    def _extract_title(self, task_description: str) -> str:
        """
        Extract a suitable title from the task description.

        Args:
            task_description: The task description

        Returns:
            A suitable title for the plan
        """
        # Look for common patterns to extract title
        patterns = [
            r'need to ([^.!?]+)',
            r'plan to ([^.!?]+)',
            r'working on ([^.!?]+)',
            r'will ([^.!?]+)',
            r'([^.!?]+) project',
            r'([^.!?]+) initiative'
        ]

        for pattern in patterns:
            match = re.search(pattern, task_description, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # Capitalize first letter
                title = title[0].upper() + title[1:] if title else task_description[:50]
                return title

        # If no pattern matches, use the first 50 characters
        return task_description[:50].strip()

    def _generate_tasks(self, task_description: str) -> List[Dict[str, str]]:
        """
        Generate a list of tasks based on the task description.

        Args:
            task_description: Description of the complex task

        Returns:
            List of task dictionaries
        """
        # Common task patterns for different types of projects
        if 'research' in task_description.lower():
            return [
                {'name': 'Define research objectives', 'description': 'Clarify the goals and scope of the research'},
                {'name': 'Gather resources and literature', 'description': 'Collect relevant sources and materials'},
                {'name': 'Conduct research', 'description': 'Perform the actual research activities'},
                {'name': 'Analyze findings', 'description': 'Process and interpret the research data'},
                {'name': 'Compile report', 'description': 'Document the research results and conclusions'}
            ]
        elif 'marketing' in task_description.lower() or 'campaign' in task_description.lower():
            return [
                {'name': 'Define campaign objectives', 'description': 'Set clear goals and KPIs for the campaign'},
                {'name': 'Identify target audience', 'description': 'Research and define the target demographic'},
                {'name': 'Develop content strategy', 'description': 'Plan the content and messaging'},
                {'name': 'Create marketing materials', 'description': 'Design and produce campaign assets'},
                {'name': 'Launch campaign', 'description': 'Execute the marketing campaign'},
                {'name': 'Monitor and optimize', 'description': 'Track performance and make adjustments'}
            ]
        elif 'development' in task_description.lower() or 'software' in task_description.lower():
            return [
                {'name': 'Requirements analysis', 'description': 'Gather and analyze functional requirements'},
                {'name': 'System design', 'description': 'Create system architecture and design documents'},
                {'name': 'Implementation', 'description': 'Develop the software components'},
                {'name': 'Testing', 'description': 'Perform unit, integration, and system testing'},
                {'name': 'Deployment', 'description': 'Deploy the system to production environment'},
                {'name': 'Documentation', 'description': 'Create user guides and technical documentation'}
            ]
        else:
            # Generic task breakdown
            return [
                {'name': 'Planning phase', 'description': 'Define scope, objectives, and resources needed'},
                {'name': 'Preparation', 'description': 'Gather materials, tools, and set up necessary infrastructure'},
                {'name': 'Execution', 'description': 'Carry out the main activities of the task'},
                {'name': 'Review and adjustment', 'description': 'Evaluate progress and make necessary adjustments'},
                {'name': 'Finalization', 'description': 'Complete the task and deliver the final output'},
                {'name': 'Documentation', 'description': 'Record lessons learned and create documentation'}
            ]

    def _generate_goals(self, task_description: str) -> List[str]:
        """
        Generate goals for the plan based on the task description.

        Args:
            task_description: Description of the task

        Returns:
            List of goals
        """
        goals = []

        if 'research' in task_description.lower():
            goals.extend([
                'Complete comprehensive research on the topic',
                'Document findings in a structured report',
                'Identify key insights and recommendations'
            ])
        elif 'marketing' in task_description.lower() or 'campaign' in task_description.lower():
            goals.extend([
                'Increase brand awareness among target audience',
                'Generate qualified leads or conversions',
                'Achieve specified ROI targets'
            ])
        elif 'development' in task_description.lower():
            goals.extend([
                'Deliver functional software solution',
                'Meet specified performance requirements',
                'Ensure code quality and maintainability'
            ])
        else:
            # Generic goals
            goals.extend([
                'Complete the task according to specifications',
                'Deliver high-quality results',
                'Meet established deadlines and budget'
            ])

        return goals

    def _estimate_duration(self, num_tasks: int) -> str:
        """
        Estimate the duration based on the number of tasks.

        Args:
            num_tasks: Number of tasks in the plan

        Returns:
            Estimated duration string
        """
        # Rough estimate: 2-3 days per task for complex projects
        days = num_tasks * 2.5
        if days < 7:
            return f"{int(days)} days"
        elif days < 30:
            weeks = days / 7
            return f"{weeks:.1f} weeks"
        else:
            months = days / 30
            return f"{months:.1f} months"

    def _determine_priority(self, task_description: str) -> str:
        """
        Determine the priority based on keywords in the description.

        Args:
            task_description: Description of the task

        Returns:
            Priority level ('low', 'medium', 'high', 'critical')
        """
        task_lower = task_description.lower()

        high_priority_keywords = [
            'urgent', 'asap', 'immediately', 'critical', 'emergency',
            'deadline', 'time-sensitive', 'expedited'
        ]

        for keyword in high_priority_keywords:
            if keyword in task_lower:
                return 'high'

        if 'important' in task_lower or 'significant' in task_lower:
            return 'medium'

        return 'medium'

    def _generate_dependencies(self, tasks: List[Dict[str, str]]) -> List[str]:
        """
        Generate dependencies between tasks.

        Args:
            tasks: List of tasks

        Returns:
            List of dependencies
        """
        dependencies = []

        # Create sequential dependencies
        for i in range(1, len(tasks)):
            dependencies.append(f"{tasks[i-1]['name']} must be completed before {tasks[i]['name']}")

        return dependencies

    def _generate_success_criteria(self, tasks: List[Dict[str, str]]) -> List[str]:
        """
        Generate success criteria based on tasks.

        Args:
            tasks: List of tasks

        Returns:
            List of success criteria
        """
        criteria = []

        for i, task in enumerate(tasks, 1):
            criteria.append(f"Task {i} ({task['name']}) completed successfully")

        criteria.append("Overall project objectives achieved")
        criteria.append("Delivered within time and budget constraints")

        return criteria

    def _generate_resources(self, tasks: List[Dict[str, str]]) -> List[str]:
        """
        Generate required resources based on tasks.

        Args:
            tasks: List of tasks

        Returns:
            List of required resources
        """
        return [
            "Time allocation for project work",
            "Access to necessary tools and software",
            "Stakeholder availability for reviews",
            f"Approximately {len(tasks) * 2} hours of work"
        ]

    def _generate_timeline(self, num_tasks: int) -> Dict[str, str]:
        """
        Generate a basic timeline.

        Args:
            num_tasks: Number of tasks

        Returns:
            Timeline dictionary
        """
        start_date = datetime.now().strftime("%Y-%m-%d")
        # Assume 3 days per task as rough estimate
        end_date = (datetime.now() + timedelta(days=num_tasks * 3)).strftime("%Y-%m-%d")

        return {
            'start_date': start_date,
            'target_completion': end_date
        }

    def _generate_notes(self, task_description: str) -> List[str]:
        """
        Generate helpful notes based on the task.

        Args:
            task_description: Description of the task

        Returns:
            List of notes
        """
        notes = ["Remember to track progress regularly"]

        if 'research' in task_description.lower():
            notes.append("Keep detailed records of sources and findings")
        elif 'marketing' in task_description.lower():
            notes.append("Monitor campaign performance metrics closely")
        elif 'development' in task_description.lower():
            notes.append("Follow coding standards and conduct code reviews")

        return notes

    def generate_plan(self, task_description: str, related_entities: Optional[List[str]] = None) -> Optional[Path]:
        """
        Generate a complete plan and save it as a markdown file.

        Args:
            task_description: Description of the complex task
            related_entities: Optional list of related entities (emails, posts, etc.)

        Returns:
            Path to the created plan file, or None if not created
        """
        if not self.is_complex_task(task_description):
            self.logger.info("Task is not complex enough to warrant a plan")
            return None

        try:
            # Generate the plan structure
            plan_data = self.generate_plan_structure(task_description)

            # Create the plan content
            plan_content = self._create_plan_content(plan_data, related_entities or [])

            # Create frontmatter
            frontmatter = {
                'type': 'plan_document',
                'title': plan_data['title'],
                'created': datetime.now().isoformat(),
                'status': 'pending',
                'total_tasks': len(plan_data['tasks']),
                'completed_tasks': 0,
                'estimated_duration': plan_data['estimated_duration'],
                'priority': plan_data['priority'],
                'tags': self._extract_tags(task_description),
                'related_entities': related_entities or []
            }

            # Create the plan file
            plans_folder = self.vault_path / 'Plans'
            plans_folder.mkdir(exist_ok=True)

            # Create a safe filename
            safe_title = re.sub(r'[^\w\s-]', '', plan_data['title']).strip()[:50]
            safe_title = re.sub(r'[-\s]+', '-', safe_title)

            plan_path = create_action_file(
                str(plans_folder),
                f"PLAN_{safe_title}",
                plan_content,
                frontmatter
            )

            self.logger.info(f"Created plan document: {plan_path}")
            return plan_path

        except Exception as e:
            self.logger.error(f"Error generating plan: {e}")
            return None

    def _create_plan_content(self, plan_data: Dict, related_entities: List[str]) -> str:
        """
        Create the markdown content for the plan.

        Args:
            plan_data: Dictionary containing plan data
            related_entities: List of related entities

        Returns:
            Markdown content string
        """
        content = f"# {plan_data['title']}\n\n"

        content += f"## Description\n{plan_data['description']}\n\n"

        content += "## Goals\n"
        for goal in plan_data['goals']:
            content += f"- [ ] {goal}\n"
        content += "\n"

        content += "## Tasks\n"
        for i, task in enumerate(plan_data['tasks'], 1):
            content += f"- [ ] **{task['name']}** - {task['description']}\n"
        content += "\n"

        content += "## Timeline\n"
        content += f"- **Start Date**: {plan_data['timeline']['start_date']}\n"
        content += f"- **Target Completion**: {plan_data['timeline']['target_completion']}\n\n"

        content += "## Resources Needed\n"
        for resource in plan_data['resources_needed']:
            content += f"- {resource}\n"
        content += "\n"

        content += "## Dependencies\n"
        for dependency in plan_data['dependencies']:
            content += f"- {dependency}\n"
        content += "\n"

        content += "## Success Criteria\n"
        for criterion in plan_data['success_criteria']:
            content += f"- [ ] {criterion}\n"
        content += "\n"

        if related_entities:
            content += "## Related Entities\n"
            for entity in related_entities:
                content += f"- [[{entity}]]\n"
            content += "\n"

        content += "## Notes\n"
        for note in plan_data['notes']:
            content += f"- {note}\n"

        return content

    def _extract_tags(self, task_description: str) -> List[str]:
        """
        Extract relevant tags from the task description.

        Args:
            task_description: Description of the task

        Returns:
            List of relevant tags
        """
        tags = []
        task_lower = task_description.lower()

        if 'research' in task_lower:
            tags.append('research')
        if 'marketing' in task_lower or 'campaign' in task_lower:
            tags.append('marketing')
        if 'development' in task_lower or 'software' in task_lower:
            tags.append('development')
        if 'urgent' in task_lower or 'asap' in task_lower:
            tags.append('urgent')
        if 'meeting' in task_lower:
            tags.append('meeting')
        if 'report' in task_lower:
            tags.append('report')

        return tags if tags else ['project']


def get_plan_generator(vault_path: str) -> PlanGenerator:
    """
    Get a PlanGenerator instance for the specified vault.

    Args:
        vault_path: Path to the Obsidian vault

    Returns:
        PlanGenerator instance
    """
    return PlanGenerator(vault_path)


if __name__ == "__main__":
    # Example usage
    import logging

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Create a plan generator
    generator = PlanGenerator("./test_vault")

    # Example complex task
    complex_task = "Need to develop a comprehensive marketing campaign for our new product launch that will run for 3 months and target young professionals aged 25-35."

    print(f"Task: {complex_task}")
    print(f"Is complex: {generator.is_complex_task(complex_task)}")

    # Generate plan structure
    plan_structure = generator.generate_plan_structure(complex_task)
    print(f"Generated plan with {len(plan_structure['tasks'])} tasks")

    # Generate actual plan
    # Note: Skipping actual file creation in this example to avoid creating files