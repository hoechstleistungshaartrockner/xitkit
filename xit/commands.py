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


class AddTaskCommand(Command):
    """Command for adding new tasks."""
    
    def execute(self, description: str, file_path: str, directory: Path = None) -> None:
        """Execute the add task command.
        
        Args:
            description: The task description text
            file_path: Path to the file where task should be added
            directory: Base directory for relative paths
        """
        try:
            # Resolve absolute file path
            if not Path(file_path).is_absolute():
                if directory:
                    file_path = str(directory / file_path)
                else:
                    file_path = str(Path.cwd() / file_path)
            
            # Add the task to the file
            self.task_service.add_task_to_file(description, file_path)
            
            # Display confirmation message
            relative_path = self._get_relative_path(file_path)
            self.formatter.display_success(
                f"✓ Added task to {relative_path}: \"{description}\""
            )
            
        except XitError as e:
            self.formatter.display_error(str(e))
        except Exception as e:
            self.formatter.display_error(f"Unexpected error: {e}")
    
    def _get_relative_path(self, file_path: str) -> str:
        """Get relative path for display purposes."""
        try:
            return str(Path(file_path).relative_to(Path.cwd()))
        except ValueError:
            return file_path


class MarkTaskCommand(Command):
    """Command for marking tasks with a specific status."""
    
    def execute(self, task_id: int, status: str, directory: Path = None, 
                specified_files: list = None) -> None:
        """Execute the mark task command.
        
        Args:
            task_id: ID of the task to mark
            status: New status for the task
            directory: Default directory to search
            specified_files: Explicitly specified files
        """
        try:
            # Resolve file paths
            file_paths = self.file_service.resolve_file_paths(
                None, directory, specified_files
            )
            
            if not file_paths:
                self.formatter.display_warning("No task files found.")
                return
            
            # Find and update the task
            updated_task = self.task_service.mark_task_by_id(task_id, status, file_paths)
            
            if updated_task:
                # Display confirmation message
                relative_path = self._get_relative_path(updated_task.file)
                status_display = status.lower()
                self.formatter.display_success(
                    f"✓ Marked task #{task_id} as {status_display} in {relative_path}: \"{updated_task.description}\""
                )
            else:
                self.formatter.display_error(f"Task with ID #{task_id} not found.")
                
        except XitError as e:
            self.formatter.display_error(str(e))
        except Exception as e:
            self.formatter.display_error(f"Unexpected error: {e}")
    
    def _get_relative_path(self, file_path: str) -> str:
        """Get relative path for display purposes."""
        try:
            return str(Path(file_path).relative_to(Path.cwd()))
        except ValueError:
            return file_path


class RescheduleTaskCommand(Command):
    """Command for rescheduling tasks to new due dates."""
    
    def execute(self, task_id: int, new_date: str, directory: Path = None, 
                specified_files: list = None) -> None:
        """Execute the reschedule task command.
        
        Args:
            task_id: ID of the task to reschedule
            new_date: New due date (can be natural language)
            directory: Default directory to search
            specified_files: Explicitly specified files
        """
        try:
            # Resolve file paths
            file_paths = self.file_service.resolve_file_paths(
                None, directory, specified_files
            )
            
            if not file_paths:
                self.formatter.display_warning("No task files found.")
                return
            
            # Parse the date expression
            from .dateutils import get_date_parser
            date_parser = get_date_parser()
            
            try:
                # Handle different relative date formats:
                # "+1w" -> "1w", "1d-" -> "-1d"
                if new_date.startswith('+'):
                    date_expression = new_date[1:]  # Remove "+" prefix
                elif new_date.endswith('-'):
                    date_expression = '-' + new_date[:-1]  # Move "-" to front
                else:
                    date_expression = new_date
                
                parsed_date = date_parser.parse_date_expression(date_expression)
                
                if parsed_date is None:
                    self.formatter.display_error(f"Invalid date format: {new_date}")
                    return
                    
            except Exception as e:
                self.formatter.display_error(f"Invalid date format: {new_date}")
                return
            
            # Find and update the task
            updated_task = self.task_service.reschedule_task_by_id(task_id, parsed_date, file_paths)
            
            if updated_task:
                # Display confirmation message
                relative_path = self._get_relative_path(updated_task.file)
                self.formatter.display_success(
                    f"✓ Rescheduled task #{task_id} to {parsed_date} in {relative_path}: \"{updated_task.description}\""
                )
            else:
                self.formatter.display_error(f"Task with ID #{task_id} not found.")
                
        except XitError as e:
            self.formatter.display_error(str(e))
        except Exception as e:
            self.formatter.display_error(f"Unexpected error: {e}")
    
    def _get_relative_path(self, file_path: str) -> str:
        """Get relative path for display purposes."""
        try:
            return str(Path(file_path).relative_to(Path.cwd()))
        except ValueError:
            return file_path


class RemoveTaskCommand(Command):
    """Command for removing tasks from files."""
    
    def execute(self, task_id: int, directory: Path = None, 
                specified_files: list = None) -> None:
        """Execute the remove task command.
        
        Args:
            task_id: ID of the task to remove
            directory: Default directory to search
            specified_files: Explicitly specified files
        """
        try:
            # Resolve file paths
            file_paths = self.file_service.resolve_file_paths(
                None, directory, specified_files
            )
            
            if not file_paths:
                self.formatter.display_warning("No task files found.")
                return
            
            # First, find the task to get its details for confirmation
            all_tasks = self.task_service.load_tasks(file_paths)
            target_task = None
            for task in all_tasks:
                if task.id == task_id:
                    target_task = task
                    break
            
            if not target_task:
                self.formatter.display_error(f"Task with ID #{task_id} not found.")
                return
            
            # Show the task and ask for confirmation
            relative_path = self._get_relative_path(target_task.file)
            import click
            self.formatter.display_warning(
                f"Task #{task_id} in {relative_path}: \"{target_task.description}\""
            )
            
            if click.confirm("Are you sure you want to permanently delete this task? (n will mark as obsolete instead)"):
                # User chose to permanently delete
                removed_task = self.task_service.remove_task_by_id(task_id, file_paths)
                if removed_task:
                    self.formatter.display_success(
                        f"✓ Permanently deleted task #{task_id} from {relative_path}: \"{removed_task.description}\""
                    )
                else:
                    self.formatter.display_error(f"Failed to delete task #{task_id}.")
            else:
                # User chose to mark as obsolete instead
                updated_task = self.task_service.mark_task_by_id(task_id, "OBSOLETE", file_paths)
                if updated_task:
                    self.formatter.display_success(
                        f"✓ Marked task #{task_id} as obsolete in {relative_path}: \"{updated_task.description}\""
                    )
                else:
                    self.formatter.display_error(f"Failed to mark task #{task_id} as obsolete.")
                
        except XitError as e:
            self.formatter.display_error(str(e))
        except Exception as e:
            self.formatter.display_error(f"Unexpected error: {e}")
    
    def _get_relative_path(self, file_path: str) -> str:
        """Get relative path for display purposes."""
        try:
            return str(Path(file_path).relative_to(Path.cwd()))
        except ValueError:
            return file_path


class MoveTaskCommand(Command):
    """Command for moving tasks between files."""
    
    def execute(self, task_id: int, target_file: str, directory: Path = None, 
                specified_files: list = None) -> None:
        """Execute the move task command.
        
        Args:
            task_id: ID of the task to move
            target_file: Path to the target file
            directory: Default directory to search
            specified_files: Explicitly specified files
        """
        try:
            # Resolve file paths for source files
            source_files = self.file_service.resolve_file_paths(
                None, directory, specified_files
            )
            
            if not source_files:
                self.formatter.display_warning("No task files found.")
                return
            
            # Resolve target file path
            if not Path(target_file).is_absolute():
                if directory:
                    target_file = str(directory / target_file)
                else:
                    target_file = str(Path.cwd() / target_file)
            
            # Find and move the task
            moved_task = self.task_service.move_task_by_id(task_id, source_files, target_file)
            
            if moved_task:
                # Display confirmation message
                target_relative = self._get_relative_path(target_file)
                self.formatter.display_success(
                    f"✓ Moved task #{task_id} to {target_relative}: \"{moved_task.description}\""
                )
            else:
                self.formatter.display_error(f"Task with ID #{task_id} not found.")
                
        except XitError as e:
            self.formatter.display_error(str(e))
        except Exception as e:
            self.formatter.display_error(f"Unexpected error: {e}")
    
    def _get_relative_path(self, file_path: str) -> str:
        """Get relative path for display purposes."""
        try:
            return str(Path(file_path).relative_to(Path.cwd()))
        except ValueError:
            return file_path


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
    
    @staticmethod
    def create_add_command(formatter: TaskFormatter = None) -> AddTaskCommand:
        """Create an add task command."""
        return AddTaskCommand(formatter)
    
    @staticmethod
    def create_mark_command(formatter: TaskFormatter = None) -> MarkTaskCommand:
        """Create a mark task command."""
        return MarkTaskCommand(formatter)
    
    @staticmethod
    def create_reschedule_command(formatter: TaskFormatter = None) -> RescheduleTaskCommand:
        """Create a reschedule task command."""
        return RescheduleTaskCommand(formatter)
    
    @staticmethod
    def create_remove_command(formatter: TaskFormatter = None) -> RemoveTaskCommand:
        """Create a remove task command."""
        return RemoveTaskCommand(formatter)
    
    @staticmethod
    def create_move_command(formatter: TaskFormatter = None) -> MoveTaskCommand:
        """Create a move task command."""
        return MoveTaskCommand(formatter)