"""Core service classes for task management operations.

This module provides high-level services that orchestrate the various components
of the task management system, separating business logic from CLI concerns.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from datetime import timedelta

from .fileparser import FileParser
from .task import Task
from .dateutils import DateParser
from .config import get_config
from .description import Description
from .exceptions import FileNotSupportedError, TaskFilterError
from .status import *
from .tags import Tag
from .duedate import DueDate
from .priority import Priority
from .location import Location

@dataclass
class TaskFilter:
    """Configuration for filtering tasks."""
    status: Optional[Status] = None
    priority: Optional[Priority] = None
    tags: Optional[List[Tag]] = None
    due_on: Optional[DueDate] = None
    due_by: Optional[DueDate] = None


class TaskService:
    """High-level service for task operations.
    
    This service orchestrates parsing, filtering, and data operations
    while keeping the CLI layer focused on user interaction.
    """
    
    def __init__(self):
        """Initialize the task service."""
        self.parser = FileParser()
        self.date_parser = DateParser()
    
    def find_task_files(self, directory: Path = None) -> List[str]:
        """Find all .md and .xit files in the specified directory.
        
        Args:
            directory: Directory to search (defaults to current directory)
            
        Returns:
            List of task file paths
        """
        if directory is None:
            directory = Path.cwd()
        
        task_files = []
        for pattern in ['**/*.xit', '**/*.md']:
            task_files.extend(str(p) for p in directory.glob(pattern))
        
        return sorted(task_files)
    
    def load_tasks(self, file_paths: List[str]) -> List[Task]:
        """Load tasks from the specified files.
        
        Files are processed in alphabetical order, and tasks are assigned
        sequential IDs starting from 1.
        
        Args:
            file_paths: List of file paths to parse
            
        Returns:
            List of parsed tasks with assigned IDs
            
        Raises:
            FileNotFoundError: If a file doesn't exist
            ValueError: If a file has an unsupported format
        """
        # Sort file paths to ensure consistent ordering
        sorted_paths = sorted(file_paths)
        
        # Parse all tasks from all files
        all_tasks = self.parser.parse_files(sorted_paths)
        
        # Assign sequential IDs starting from 1
        for i, task in enumerate(all_tasks, start=1):
            task.id = i
            
        return all_tasks

    
    def filter_tasks(self, tasks: List[Task], filters: TaskFilter) -> List[Task]:
        """Apply filters to a list of tasks.
        
        Args:
            tasks: List of tasks to filter
            filters: Filter configuration
            
        Returns:
            Filtered list of tasks
        """
        filtered_tasks = tasks
        
        # Filter by status
        if filters.status:
            filtered_tasks = [task for task in filtered_tasks 
                            if task.status.status_type in [s.status_type for s in filters.status]]
        
        # Filter by priority (minimum level)
        if filters.priority:
            filtered_tasks = [task for task in filtered_tasks 
                            if task.priority.level >= filters.priority.level]
        
        # Filter by tags
        if filters.tags:
            for filter_tag in filters.tags:
                filtered_tasks = [task for task in filtered_tasks 
                                if task.has_tag(filter_tag, soft=True)]
        
        # Filter by due_on (exact date match)
        if filters.due_on:
            filtered_tasks = [task for task in filtered_tasks 
                            if task.due_date and task.due_date.implied_date == filters.due_on.implied_date]
        
        # Filter by due_by (tasks due on or before this date)
        if filters.due_by:
            filtered_tasks = [task for task in filtered_tasks 
                            if task.due_date and task.due_date.implied_date <= filters.due_by.implied_date]
        
        return filtered_tasks

    
    
    def get_task_statistics(self, tasks: List[Task]) -> Dict[str, Any]:
        """Calculate statistics for a list of tasks.
        
        Args:
            tasks: List of tasks to analyze
            
        Returns:
            Dictionary containing various statistics
        """
        if not tasks:
            return {
                'total': 0,
                'by_status': {},
                'by_priority': {},
                'by_file': {},
                'with_tags': 0,
                'with_due_date': 0,
                'overdue': 0
            }
        
        # Status counts
        status_counts = {}
        for task in tasks:
            status_name = task.status.status_type.name
            status_counts[status_name] = status_counts.get(status_name, 0) + 1
        
        # Priority counts
        priority_counts = {}
        for task in tasks:
            priority_level = task.priority.level
            priority_counts[priority_level] = priority_counts.get(priority_level, 0) + 1
        
        # File counts
        file_counts = {}
        for task in tasks:
            file_name = str(task.location.file_path) if task.location.file_path else 'unknown'
            file_counts[file_name] = file_counts.get(file_name, 0) + 1
        
        # Count tasks with tags and due dates
        tasks_with_tags = sum(1 for task in tasks if task.has_tags)
        tasks_with_due_date = sum(1 for task in tasks if task.has_due_date)
        
        # Count overdue tasks (using a reasonable current date)
        from datetime import datetime
        current_date = datetime.now().strftime('%Y-%m-%d')
        overdue_tasks = sum(1 for task in tasks if task.is_overdue(current_date))
        
        return {
            'total': len(tasks),
            'by_status': status_counts,
            'by_priority': priority_counts,
            'by_file': file_counts,
            'with_tags': tasks_with_tags,
            'with_due_date': tasks_with_due_date,
            'overdue': overdue_tasks
        }

    def sort_tasks(self, tasks: List[Task], sort_by: str, sort_order: str = 'asc') -> List[Task]:
        """Sort tasks by the specified attribute and order.
        
        Args:
            tasks: List of tasks to sort
            sort_by: Attribute to sort by ('priority', 'due_date')
            sort_order: Sort order ('asc' or 'desc')
            
        Returns:
            Sorted list of tasks
            
        Raises:
            ValueError: If sort_by or sort_order are invalid
        """
        if sort_by not in ['priority', 'due_date']:
            raise ValueError(f"Invalid sort attribute: {sort_by}")
        
        if sort_order not in ['asc', 'desc']:
            raise ValueError(f"Invalid sort order: {sort_order}")
        
        reverse = (sort_order == 'desc')
        
        if sort_by == 'priority':
            # Sort by priority level (higher priority first for desc)
            return sorted(tasks, key=lambda task: task.priority.level, reverse=reverse)
        
        elif sort_by == 'due_date':
            # Sort by due date, with tasks without due dates at the end for asc, beginning for desc
            def due_date_key(task):
                if task.due_date is None:
                    # Use a very late date for asc (puts None at end), very early for desc (puts None at beginning)
                    return '9999-12-31' if not reverse else '0000-01-01'
                # Use implied_date for proper chronological comparison
                return task.due_date.implied_date or '9999-12-31'
            
            return sorted(tasks, key=due_date_key, reverse=reverse)

    def update_task_by_id(self, task_id: int,
        file_paths: List[str], 
        new_status: Status=None, 
        new_priority: Priority=None, 
        new_due_date: DueDate=None) -> Optional[Task]:
        """Find and update a task's status, priority and/or due date by its ID.
        
        Args:
            task_id: The ID of the task to update
            file_paths: List of file paths to search
            new_status: New status to set
            new_priority: New priority to set
            new_due_date: New due date to set
            
        Returns:
            The updated Task object if found, None otherwise
            
        Raises:
            ValueError: If the new status is invalid
        """
        # Load all tasks to find the one with matching ID
        all_tasks = self.load_tasks(file_paths)
        
        # Find the task with the specified ID
        target_task = None
        for task in all_tasks:
            if task.id == task_id:
                target_task = task
                break
        
        if not target_task:
            return None
        
        # Update task properties
        if new_status:
            target_task.set_status(new_status)
        if new_priority:
            target_task.set_priority(new_priority)
        if new_due_date:
            target_task.set_due_date(new_due_date.implied_date if new_due_date else None)
        
        # Update the task in the file using the new method
        target_task.save_to_location(target_task.location, mode='update')
        
        return target_task

    def update_task_description(self, task_id: int, new_description: str, file_paths: List[str]) -> Optional[Task]:
        """Update a task's description by its ID.
        
        Args:
            task_id: The ID of the task to update
            new_description: New description text
            file_paths: List of file paths to search
            
        Returns:
            The updated Task object if found, None otherwise
        """
        # Load all tasks to find the one with matching ID
        all_tasks = self.load_tasks(file_paths)
        
        # Find the task with the specified ID
        target_task = None
        for task in all_tasks:
            if task.id == task_id:
                target_task = task
                break
        
        if not target_task:
            return None
        
        # Update task description
        target_task.description = Description(new_description)
        
        # Update the task in the file using the new method
        target_task.save_to_location(target_task.location, mode='update')
        
        return target_task

    def remove_task_by_id(self, task_id: int, file_paths: List[str]) -> Optional[Task]:
        """Remove a task by its ID from the files.
        
        Args:
            task_id: The ID of the task to remove
            file_paths: List of file paths to search
            
        Returns:
            The removed Task object if found, None otherwise
        """
        # Load all tasks to find the one with matching ID
        all_tasks = self.load_tasks(file_paths)
        
        # Find the task with the specified ID
        target_task = None
        for task in all_tasks:
            if task.id == task_id:
                target_task = task
                break
        
        if not target_task:
            return None
        
        # Remove the task from the file using the new method
        return target_task.remove_from_file()

    def move_task_by_id(self, task_id: int, source_files: List[str], target_file: str) -> Optional[Task]:
        """Move a task by its ID from source files to a target file.
        
        Args:
            task_id: The ID of the task to move
            source_files: List of source file paths to search
            target_file: Path to the target file
            
        Returns:
            The moved Task object if found, None otherwise
            
        Raises:
            FileNotSupportedError: If target file extension is not supported
        """
        # Validate target file extension
        target_path = Path(target_file)
        if target_path.suffix not in ['.md', '.xit']:
            raise FileNotSupportedError(str(target_path), {'.md', '.xit'})
        
        # Find and remove the task from source files
        removed_task = self.remove_task_by_id(task_id, source_files)
        
        if not removed_task:
            return None
        
        # Update task's file reference
        removed_task.set_location(Location(file_path=target_file))
        
        # Add task to target file
        removed_task.save_to_location(removed_task.location, mode='append')
        
        return removed_task
    
    def add_task_tag(self, task_id: int, tag: str, file_paths: List[str]) -> bool:
        """Add a tag to a task.
        
        Args:
            task_id: ID of the task to modify
            tag: Tag to add (without # prefix)
            file_paths: List of file paths to search
            
        Returns:
            True if task was found and tag was added, False otherwise
        """
        # Load all tasks to find the one with matching ID
        all_tasks = self.load_tasks(file_paths)
        
        # Find the task with the specified ID
        target_task = None
        for task in all_tasks:
            if task.id == task_id:
                target_task = task
                break
        
        if not target_task:
            return False
        
        # Add the tag (remove # prefix if present)
        clean_tag = tag.lstrip('#')
        target_task.add_tag_by_name(clean_tag)
        
        # Update the task in the file using the new method
        target_task.save_to_location(target_task.location, mode='update')
        
        return True

    
    def remove_task_tag(self, task_id: int, tag: str, file_paths: List[str]) -> bool:
        """Remove a tag from a task.
        
        Args:
            task_id: ID of the task to modify
            tag: Tag to remove (without # prefix)
            file_paths: List of file paths to search
            
        Returns:
            True if task was found and tag was removed (or didn't exist), False otherwise
        """
        # Load all tasks to find the one with matching ID
        all_tasks = self.load_tasks(file_paths)
        
        # Find the task with the specified ID
        target_task = None
        for task in all_tasks:
            if task.id == task_id:
                target_task = task
                break
        
        if not target_task:
            return False
        
        # Remove the tag (remove # prefix if present)
        clean_tag = tag.lstrip('#')
        target_task.remove_tag_by_name(clean_tag)
        
        # Update the task in the file using the new method
        target_task.save_to_location(target_task.location, mode='update')
        
        return True
    
    def recur_task_by_id(self, task_id: int, interval: str, end_date: str = None, 
                        count: int = None, target_file: str = None,
                        directory: Path = None, specified_files: list = None) -> List[Task]:
        """Create recurring instances of a task.
        
        Args:
            task_id: ID of the task to make recurring
            interval: Interval expression (e.g., "1w", "30d", "3m", "1y2m1w4d")
            end_date: Optional end date in YYYY-MM-DD format
            count: Optional maximum number of occurrences
            target_file: Optional target file for new tasks (default: same as original)
            directory: Directory to search for tasks
            specified_files: Specific files to search in
            
        Returns:
            List of newly created recurring tasks
            
        Raises:
            ValueError: If task not found or parameters invalid
        """
        # Determine which files to search
        if specified_files:
            file_paths = specified_files
        elif directory:
            file_paths = self.find_task_files(directory)
        else:
            file_paths = self.find_task_files()
        
        # Find the original task
        all_tasks = self.load_tasks(file_paths)
        original_task = None
        for task in all_tasks:
            if task.id == task_id:
                original_task = task
                break
        
        if not original_task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        # Use target file or original task's file
        output_file = target_file or original_task.location.file_path
        
        # Parse interval to calculate days
        interval_days = self._parse_interval(interval)
        if interval_days <= 0:
            raise ValueError(f"Invalid interval: {interval}")
        
        # Create recurring tasks
        recurring_tasks = []
        current_date = self.date_parser.current_date
        
        # Determine max occurrences
        max_occurrences = count or 10  # Default to 10 if no count specified
        
        for i in range(max_occurrences):
            # Calculate next occurrence date
            next_date = current_date + timedelta(days=interval_days * (i + 1))
            next_date_str = next_date.strftime('%Y-%m-%d')
            
            # Check end date constraint
            if end_date and next_date_str > end_date:
                break
            
            # Create new task based on original
            new_task = original_task.copy()
            new_task.id = None  # Will be assigned when saved
            new_task.set_location(Location(file_path=output_file))
            
            # Update due date to the new occurrence
            new_task.set_due_date(next_date_str)
            
            # Reset status to OPEN for recurring tasks
            from .status import StatusType, Status
            new_task.status = Status(StatusType.OPEN)
            
            # Add the task to file
            new_task.save_to_location(new_task.location, mode='append')
            recurring_tasks.append(new_task)
        
        return recurring_tasks
    
    def set_task_priority(self, task_id: int, priority: int, 
                         directory: Path = None, specified_files: list = None) -> bool:
        """Set the priority of a task by its ID.
        
        Args:
            task_id: ID of the task to modify
            priority: Priority level (integer >= 0)
            directory: Directory to search for tasks
            specified_files: Specific files to search in
            
        Returns:
            True if task was found and priority was set, False otherwise
        """
        # Determine which files to search
        if specified_files:
            file_paths = specified_files
        elif directory:
            file_paths = self.find_task_files(directory)
        else:
            file_paths = self.find_task_files()
        
        # Create Priority object and update task
        from .priority import Priority
        new_priority = Priority(level=priority)
        
        updated_task = self.update_task_by_id(
            task_id=task_id,
            file_paths=file_paths,
            new_priority=new_priority
        )
        
        return updated_task is not None
    
    def _parse_interval(self, interval: str) -> int:
        """Parse interval string and return total days.
        
        Args:
            interval: Interval string like "1w", "30d", "3m", "1y2m1w4d"
            
        Returns:
            Total number of days
        """
        import re
        
        # Parse complex intervals like "1y2m1w4d"
        pattern = r'(?:(\d+)y)?(?:(\d+)m)?(?:(\d+)w)?(?:(\d+)d)?'
        match = re.match(pattern, interval.lower())
        
        if not match:
            # Try simple formats
            simple_pattern = r'(\d+)([dwmy])'
            simple_match = re.match(simple_pattern, interval.lower())
            if simple_match:
                amount = int(simple_match.group(1))
                unit = simple_match.group(2)
                
                if unit == 'd':
                    return amount
                elif unit == 'w':
                    return amount * 7
                elif unit == 'm':
                    return amount * 30  # Approximate
                elif unit == 'y':
                    return amount * 365  # Approximate
            return 0
        
        years = int(match.group(1) or 0)
        months = int(match.group(2) or 0)
        weeks = int(match.group(3) or 0)
        days = int(match.group(4) or 0)
        
        # Convert to total days (approximations for months/years)
        total_days = days + weeks * 7 + months * 30 + years * 365
        return total_days
        


class FileDiscoveryService:
    """Service for discovering and validating task files."""
    
    SUPPORTED_EXTENSIONS = {'.md', '.xit'}
    
    def resolve_file_paths(self, directory: Optional[Path], 
                          specified_files: Optional[List[str]]) -> List[str]:
        """Resolve file paths based on various input options.
        
        Args:
            directory: Default directory to search
            specified_files: Explicitly specified files
            
        Returns:
            List of resolved file paths
            
        Raises:
            FileNotFoundError: If path doesn't exist
            ValueError: If file type is not supported
        """
        if specified_files:
            return list(specified_files)
        else:
            service = TaskService()
            return service.find_task_files(directory)
    
    def _resolve_path_argument(self, path: str) -> List[str]:
        """Resolve a single path argument to a list of files."""
        path_obj = Path(path)
        
        if not path_obj.exists():
            raise FileNotFoundError(f"Path '{path}' does not exist.")
        
        if path_obj.is_file():
            if path_obj.suffix not in self.SUPPORTED_EXTENSIONS:
                raise ValueError(f"File '{path}' is not a supported file type. "
                               f"Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}")
            return [str(path_obj)]
        elif path_obj.is_dir():
            service = TaskService()
            return service.find_task_files(path_obj)
        else:
            raise ValueError(f"Path '{path}' is neither a file nor a directory.")