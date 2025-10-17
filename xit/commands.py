"""Command pattern implementation for CLI operations.

This module implements the command pattern to better organize and structure
CLI operations, making them more testable and maintainable.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from pathlib import Path

from .services import TaskService, FileDiscoveryService, TaskFilter
from .formatter import TaskFormatter
from .exceptions import XitError


class Command(ABC):
    """Abstract base class for CLI commands."""
    
    def __init__(self, formatter: TaskFormatter = None):
        """Initialize command with optional formatter."""
        self.formatter = formatter or TaskFormatter()
        self.task_service = TaskService()
        self.file_service = FileDiscoveryService()
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the command with given arguments."""
        pass


class ShowTasksCommand(Command):
    """Command for showing tasks with filtering options."""
    
    def execute(self, path: str = None, directory: Path = None, 
                specified_files: list = None, filters: TaskFilter = None,
                show_line: bool = False, show_id: bool = False, count_only: bool = False) -> None:
        """Execute the show tasks command.
        
        Args:
            path: Optional path argument
            directory: Default directory to search
            specified_files: Explicitly specified files
            filters: Task filters to apply
            show_line: Whether to show line numbers
            show_id: Whether to show task IDs
            count_only: Whether to show only count
        """
        try:
            # Resolve file paths
            file_paths = self.file_service.resolve_file_paths(
                path, directory, specified_files
            )
            
            if not file_paths:
                self.formatter.display_warning("No task files found.")
                return
            
            # Load and filter tasks
            all_tasks = self.task_service.load_tasks(file_paths)
            
            if not all_tasks:
                self.formatter.display_warning("No tasks found in the specified files.")
                return
            
            filtered_tasks = all_tasks
            if filters:
                filtered_tasks = self.task_service.filter_tasks(all_tasks, filters)
            
            # Display results
            if count_only:
                self.formatter.display_count(len(filtered_tasks))
            elif not filtered_tasks:
                self.formatter.display_warning("No tasks match the specified criteria.")
            else:
                self.formatter.display_tasks(filtered_tasks, show_line=show_line, show_id=show_id)
                self.formatter.display_summary(len(filtered_tasks), len(all_tasks))
                
        except XitError as e:
            self.formatter.display_error(str(e))
        except Exception as e:
            self.formatter.display_error(f"Unexpected error: {e}")


class ShowStatsCommand(Command):
    """Command for showing task statistics."""
    
    def execute(self, path: str = None, directory: Path = None,
                specified_files: list = None) -> None:
        """Execute the show stats command.
        
        Args:
            path: Optional path argument
            directory: Default directory to search
            specified_files: Explicitly specified files
        """
        try:
            # Resolve file paths
            file_paths = self.file_service.resolve_file_paths(
                path, directory, specified_files
            )
            
            if not file_paths:
                self.formatter.display_warning("No task files found.")
                return
            
            # Load tasks and calculate statistics
            all_tasks = self.task_service.load_tasks(file_paths)
            
            if not all_tasks:
                self.formatter.display_warning("No tasks found in the specified files.")
                return
            
            stats = self.task_service.get_task_statistics(all_tasks)
            self._display_statistics(stats, path)
            
        except XitError as e:
            self.formatter.display_error(str(e))
        except Exception as e:
            self.formatter.display_error(f"Unexpected error: {e}")
    
    def _display_statistics(self, stats: Dict[str, Any], path: str = None) -> None:
        """Display formatted statistics."""
        # Header
        if path:
            self.formatter.console.print(f"[bold]Task Statistics for '{path}'[/bold]")
        else:
            self.formatter.console.print("[bold]Task Statistics[/bold]")
        
        self.formatter.console.print("=" * 40)
        self.formatter.console.print(f"Total tasks: {stats['total_tasks']}")
        self.formatter.console.print(f"Files with tasks: {len(stats['files_with_tasks'])}")
        self.formatter.console.print()
        
        # Status breakdown
        self.formatter.console.print("[bold]By Status:[/bold]")
        for status in ['OPEN', 'ONGOING', 'DONE', 'OBSOLETE', 'INQUESTION']:
            count = stats['status_counts'].get(status, 0)
            if count > 0:
                self.formatter.console.print(f"  {status}: {count}")
        self.formatter.console.print()
        
        # Priority breakdown
        self.formatter.console.print("[bold]By Priority:[/bold]")
        for priority in sorted(stats['priority_counts'].keys()):
            count = stats['priority_counts'][priority]
            if priority == 0:
                self.formatter.console.print(f"  No priority: {count}")
            else:
                self.formatter.console.print(f"  Priority {'!' * priority}: {count}")
        self.formatter.console.print()
        
        # Additional stats
        self.formatter.console.print(f"Tasks with due dates: {stats['tasks_with_due_dates']}")
        self.formatter.console.print(f"Tasks with tags: {stats['tasks_with_tags']}")


class CommandFactory:
    """Factory for creating command instances."""
    
    @staticmethod
    def create_show_command(formatter: TaskFormatter = None) -> ShowTasksCommand:
        """Create a show tasks command."""
        return ShowTasksCommand(formatter)
    
    @staticmethod
    def create_stats_command(formatter: TaskFormatter = None) -> ShowStatsCommand:
        """Create a show stats command."""
        return ShowStatsCommand(formatter)