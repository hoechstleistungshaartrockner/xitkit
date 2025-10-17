"""Core service classes for task management operations.

This module provides high-level services that orchestrate the various components
of the task management system, separating business logic from CLI concerns.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass

from .fileparser import FileParser
from .task import Task
from .dateutils import DateParser
from .config import get_config
from .exceptions import FileNotSupportedError, TaskFilterError


@dataclass
class TaskFilter:
    """Configuration for filtering tasks."""
    status: Optional[str] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None
    due_on: Optional[str] = None
    due_by: Optional[str] = None


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
        # Sort file paths alphabetically to ensure consistent ID assignment
        sorted_file_paths = sorted(file_paths)
        
        # Parse all tasks from all files
        all_tasks = self.parser.parse_files(sorted_file_paths)
        
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
        filtered = tasks.copy()
        
        # Apply status filter
        if filters.status:
            status_upper = filters.status.upper()
            filtered = [t for t in filtered if t.status == status_upper]
        
        # Apply priority filter
        if filters.priority is not None:
            filtered = [t for t in filtered if t.priority >= filters.priority]
        
        # Apply tag filters
        if filters.tags:
            normalized_tags = self._normalize_tags(filters.tags)
            filtered = [t for t in filtered if self._has_all_tags(t.tags, normalized_tags)]
        
        # Apply date filters
        if filters.due_on:
            filtered = [t for t in filtered if self.date_parser.matches_date_filter_on(t.due_date, filters.due_on)]
        
        if filters.due_by:
            filtered = [t for t in filtered if self.date_parser.matches_date_filter_by(t.due_date, filters.due_by)]
        
        return filtered
    
    def _normalize_tags(self, tags: List[str]) -> List[str]:
        """Normalize tag list to include # prefix."""
        normalized = []
        for tag in tags:
            if not tag.startswith('#'):
                normalized.append(f'#{tag}')
            else:
                normalized.append(tag)
        return normalized
    
    def _has_all_tags(self, task_tags: List[str], required_tags: List[str]) -> bool:
        """Check if task has all required tags."""
        task_tag_names = []
        for task_tag in task_tags:
            if '=' in task_tag:
                task_tag_names.append(task_tag.split('=')[0])
            else:
                task_tag_names.append(task_tag)
        
        return all(req_tag in task_tag_names for req_tag in required_tags)
    
    def get_task_statistics(self, tasks: List[Task]) -> Dict[str, Any]:
        """Calculate statistics for a list of tasks.
        
        Args:
            tasks: List of tasks to analyze
            
        Returns:
            Dictionary containing various statistics
        """
        stats = {
            'total_tasks': len(tasks),
            'status_counts': {},
            'priority_counts': {},
            'files_with_tasks': set(),
            'tasks_with_due_dates': 0,
            'tasks_with_tags': 0
        }
        
        for task in tasks:
            # Count by status
            stats['status_counts'][task.status] = stats['status_counts'].get(task.status, 0) + 1
            
            # Count by priority
            stats['priority_counts'][task.priority] = stats['priority_counts'].get(task.priority, 0) + 1
            
            # Track files
            stats['files_with_tasks'].add(task.file)
            
            # Count tasks with due dates and tags
            if task.due_date:
                stats['tasks_with_due_dates'] += 1
            if task.tags:
                stats['tasks_with_tags'] += 1
        
        return stats


class FileDiscoveryService:
    """Service for discovering and validating task files."""
    
    SUPPORTED_EXTENSIONS = {'.md', '.xit'}
    
    def resolve_file_paths(self, path: Optional[str], directory: Optional[Path], 
                          specified_files: Optional[List[str]]) -> List[str]:
        """Resolve file paths based on various input options.
        
        Args:
            path: Optional path argument
            directory: Default directory to search
            specified_files: Explicitly specified files
            
        Returns:
            List of resolved file paths
            
        Raises:
            FileNotFoundError: If path doesn't exist
            ValueError: If file type is not supported
        """
        if path:
            return self._resolve_path_argument(path)
        elif specified_files:
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