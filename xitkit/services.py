"""Core service classes for task management operations.

This module provides high-level services that orchestrate the various components
of the task management system, separating business logic from CLI concerns.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from datetime import timedelta, datetime

import xitkit.fileparser as fp
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
from .file_repository import FileRepository

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
        self.parser = fp.FileParser()
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

        # convert file paths to relative to cwd
        task_files = [str(Path(fp).relative_to(Path.cwd())) for fp in task_files]

        return sorted(task_files)
    
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
        original_task = target_task.copy()
        target_task.description = Description(new_description)
        
        # Update using FileRepository with identity matching
        repo = FileRepository()
        
        success = repo.update_task_by_identity(original_task, target_task)
        if success:
            repo.save_file(target_task.location.file_path)
        
        return target_task if success else None


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