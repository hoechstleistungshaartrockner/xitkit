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
from .status import Status, StatusType
from .description import Description
from .priority import Priority
from .task import Task
from .duedate import DueDate


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
                show_line: bool = False, no_id: bool = False, count_only: bool = False,
                sort_by: str = None, sort_order: str = None) -> None:
        """Execute the show tasks command.
        
        Args:
            path: Optional path argument
            directory: Default directory to search
            specified_files: Explicitly specified files
            filters: Task filters to apply
            show_line: Whether to show line numbers
            no_id: Whether to hide task IDs
            count_only: Whether to show only count
            sort_by: Sort attribute (priority, due_date)
            sort_order: Sort order (asc, desc)
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
            
            # Sort tasks if requested
            if sort_by:
                filtered_tasks = self.task_service.sort_tasks(filtered_tasks, sort_by, sort_order or 'asc')
            
            # Display results
            if count_only:
                self.formatter.display_count(len(filtered_tasks))
            elif not filtered_tasks:
                self.formatter.display_warning("No tasks match the specified criteria.")
            else:
                self.formatter.display_tasks(filtered_tasks, show_line=show_line, no_id=no_id)
                self.formatter.display_summary(len(filtered_tasks), len(all_tasks))
                
        except XitError as e:
            self.formatter.display_error(str(e))
        except Exception as e:
            self.formatter.display_error(f"Unexpected error: {e}")

    def _get_relative_path(self, file_path: str) -> str:
        """Get relative path for display."""
        try:
            return str(Path(file_path).relative_to(Path.cwd()))
        except ValueError:
            return file_path


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
        self.formatter.console.print(f"Total tasks: {stats['total']}")
        self.formatter.console.print(f"Files with tasks: {len(stats['by_file'])}")
        self.formatter.console.print()
        
        # Status breakdown
        self.formatter.console.print("[bold]By Status:[/bold]")
        status_display = {'OPEN': 'Open', 'CHECKED': 'Done', 'ONGOING': 'Ongoing', 'OBSOLETE': 'Obsolete', 'IN_QUESTION': 'In Question'}
        for status, display_name in status_display.items():
            count = stats['by_status'].get(status, 0)
            if count > 0:
                self.formatter.console.print(f"  {display_name}: {count}")
        self.formatter.console.print()
        
        # Priority breakdown
        self.formatter.console.print("[bold]By Priority:[/bold]")
        for priority in sorted(stats['by_priority'].keys()):
            count = stats['by_priority'][priority]
            if priority == 0:
                self.formatter.console.print(f"  No priority: {count}")
            else:
                self.formatter.console.print(f"  Priority {'!' * priority}: {count}")
        self.formatter.console.print()
        
        # Additional stats
        self.formatter.console.print(f"Tasks with due dates: {stats['with_due_date']}")
        self.formatter.console.print(f"Tasks with tags: {stats['with_tags']}")
        self.formatter.console.print(f"Overdue tasks: {stats['overdue']}")
        
        # File breakdown  
        if len(stats['by_file']) > 1:
            self.formatter.console.print()
            self.formatter.console.print("[bold]By File:[/bold]")
            for filename, count in sorted(stats['by_file'].items()):
                self.formatter.console.print(f"  {filename}: {count}")


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
            
            # Create a task object
            task = Task(
                description=description,
                file=file_path,
                line_number=None,  # Will be determined when added
                status=Status(StatusType.OPEN),
                priority=Priority(0),  # No priority by default
                tags=[],
                due_date=None,
                id=None  # Will be assigned when loaded
            )
            
            # Add the task to the file
            self.task_service.add_task_to_file(task, file_path)
            
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
    
    def execute(self, task_ids: list, status: str, directory: Path = None, 
                specified_files: list = None) -> None:
        """Execute the mark task command for one or more tasks.
        
        Args:
            task_ids: List of task IDs to mark
            status: New status for the tasks
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
            
            # Convert status string to Status object
            status_mapping = {
                'OPEN': StatusType.OPEN,
                'DONE': StatusType.CHECKED,  # CLI uses 'done', StatusType uses 'CHECKED'
                'ONGOING': StatusType.ONGOING,
                'OBSOLETE': StatusType.OBSOLETE,
                'INQUESTION': StatusType.IN_QUESTION
            }
            
            if status.upper() not in status_mapping:
                self.formatter.display_error(f"Invalid status: {status}")
                return
                
            status_obj = Status(status_mapping[status.upper()])
            
            # Process each task ID
            updated_count = 0
            for task_id in task_ids:
                try:
                    # Find and update the task
                    updated_task = self.task_service.update_task_by_id(
                        task_id, file_paths, new_status=status_obj
                    )
                    
                    if updated_task:
                        # Display confirmation message
                        relative_path = self._get_relative_path(updated_task.file)
                        status_display = status.lower()
                        self.formatter.display_success(
                            f"✓ Marked task #{task_id:03d} as {status_display} in {relative_path}: \"{updated_task.description.text}\""
                        )
                        updated_count += 1
                    else:
                        self.formatter.display_error(f"Task #{task_id} not found.")
                except Exception as e:
                    self.formatter.display_error(f"Error marking task #{task_id}: {e}")
            
            # Summary message for multiple tasks
            if len(task_ids) > 1:
                self.formatter.display_success(f"Processed {updated_count} of {len(task_ids)} tasks.")
                
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
    
    def execute(self, task_ids: list, new_date: str, directory: Path = None, 
                specified_files: list = None) -> None:
        """Execute the reschedule task command for one or more tasks.
        
        Args:
            task_ids: List of task IDs to reschedule
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
            
            # Parse the date expression once for all tasks
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
                
                parsed_date = DueDate.from_string(str(parsed_date))
            except Exception as e:
                self.formatter.display_error(f"Invalid date format: {new_date}")
                return
            
            # Process each task ID
            updated_count = 0
            for task_id in task_ids:
                try:
                    # Find and update the task
                    updated_task = self.task_service.update_task_by_id(task_id, file_paths, new_due_date=parsed_date)
                    
                    if updated_task:
                        # Display confirmation message
                        relative_path = self._get_relative_path(updated_task.file)
                        self.formatter.display_success(
                            f"✓ Rescheduled task #{task_id} to {parsed_date} in {relative_path}: \"{updated_task.description}\""
                        )
                        updated_count += 1
                    else:
                        self.formatter.display_error(f"Task #{task_id} not found.")
                except Exception as e:
                    self.formatter.display_error(f"Error rescheduling task #{task_id}: {e}")
            
            # Summary message for multiple tasks
            if len(task_ids) > 1:
                self.formatter.display_success(f"Processed {updated_count} of {len(task_ids)} tasks.")
                
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
    
    def execute(self, task_ids: list, directory: Path = None, 
                specified_files: list = None) -> None:
        """Execute the remove task command for one or more tasks.
        
        Args:
            task_ids: List of task IDs to remove
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
            
            # First, collect all target tasks and get confirmations before any modifications
            all_tasks = self.task_service.load_tasks(file_paths)
            target_tasks = []
            not_found_ids = []
            user_choices = {}  # Store user's choice for each task
            
            import click
            
            # Build a mapping of ID to task for quick lookup
            task_by_id = {task.id: task for task in all_tasks}
            
            # Collect tasks and get user confirmation for each in specified order
            for task_id in task_ids:
                if task_id in task_by_id:
                    task_found = task_by_id[task_id]
                    target_tasks.append(task_found)
                    # Show the task and ask for confirmation
                    relative_path = self._get_relative_path(task_found.file)
                    self.formatter.display_warning(
                        f"Task #{task_id} in {relative_path}: \"{task_found.description}\""
                    )
                    
                    user_choice = click.confirm("Are you sure you want to permanently delete this task? (n will mark as obsolete instead)")
                    user_choices[task_id] = user_choice
                else:
                    not_found_ids.append(task_id)
            
            # Report not found tasks
            for task_id in not_found_ids:
                self.formatter.display_error(f"Task #{task_id} not found.")
            
            # Process tasks in the order specified by the user  
            deleted_count = 0
            obsoleted_count = 0
            
            for task in target_tasks:
                try:
                    task_id = task.id
                    relative_path = self._get_relative_path(task.file)
                    
                    # Find current task by content since ID may have changed
                    current_tasks = self.task_service.load_tasks(file_paths)
                    current_task = None
                    
                    for curr_task in current_tasks:
                        if (curr_task.description == task.description and 
                            curr_task.file == task.file and 
                            curr_task.status == task.status and
                            curr_task.priority == task.priority and
                            curr_task.due_date == task.due_date):
                            current_task = curr_task
                            break
                    
                    if current_task:
                        if user_choices[task_id]:
                            # User chose to permanently delete
                            removed_task = self.task_service.remove_task_by_id(current_task.id, file_paths)
                            if removed_task:
                                self.formatter.display_success(
                                    f"✓ Permanently deleted task #{task_id} from {relative_path}: \"{removed_task.description}\""
                                )
                                deleted_count += 1
                            else:
                                self.formatter.display_error(f"Failed to delete task #{task_id}.")
                        else:
                            # User chose to mark as obsolete instead
                            updated_task = self.task_service.mark_task_by_id(current_task.id, "OBSOLETE", file_paths)
                            if updated_task:
                                self.formatter.display_success(
                                    f"✓ Marked task #{task_id} as obsolete in {relative_path}: \"{updated_task.description}\""
                                )
                                obsoleted_count += 1
                            else:
                                self.formatter.display_error(f"Failed to mark task #{task_id} as obsolete.")
                    else:
                        self.formatter.display_error(f"Task #{task_id} no longer found (may have been processed already).")
                except Exception as e:
                    self.formatter.display_error(f"Error processing task #{task.id}: {e}")
            
            # Summary message for multiple tasks
            if len(task_ids) > 1:
                total_processed = deleted_count + obsoleted_count
                self.formatter.display_success(
                    f"Processed {total_processed} of {len(task_ids)} tasks. "
                    f"Deleted: {deleted_count}, Marked obsolete: {obsoleted_count}"
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


class MoveTaskCommand(Command):
    """Command for moving tasks between files."""
    
    def execute(self, task_ids: list, target_file: str, directory: Path = None, 
                specified_files: list = None) -> None:
        """Execute the move task command for one or more tasks.
        
        Args:
            task_ids: List of task IDs to move
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
            
            # First, collect all target tasks before any modifications
            all_tasks = self.task_service.load_tasks(source_files)
            target_tasks = []
            not_found_ids = []
            
            # Build a mapping of ID to task for quick lookup
            task_by_id = {task.id: task for task in all_tasks}
            
            # Collect target tasks in the order specified by user
            for task_id in task_ids:
                if task_id in task_by_id:
                    target_tasks.append(task_by_id[task_id])
                else:
                    not_found_ids.append(task_id)
            
            # Report not found tasks
            for task_id in not_found_ids:
                self.formatter.display_error(f"Task #{task_id} not found.")
            
            # Process tasks in the order specified by the user
            moved_count = 0
            
            for task in target_tasks:
                try:
                    # Use the task's content and position to move it, not just ID
                    # Since IDs can change after each move, we need to find the task by content
                    current_tasks = self.task_service.load_tasks(source_files)
                    current_task = None
                    
                    # Find the task by matching content and file (since ID may have changed)
                    for curr_task in current_tasks:
                        if (curr_task.description == task.description and 
                            curr_task.file == task.file and 
                            curr_task.status == task.status and
                            curr_task.priority == task.priority and
                            curr_task.due_date == task.due_date):
                            current_task = curr_task
                            break
                    
                    if current_task:
                        moved_task = self.task_service.move_task_by_id(current_task.id, source_files, target_file)
                        if moved_task:
                            # Display confirmation message using original ID for user clarity
                            target_relative = self._get_relative_path(target_file)
                            self.formatter.display_success(
                                f"✓ Moved task #{task.id} to {target_relative}: \"{moved_task.description}\""
                            )
                            moved_count += 1
                        else:
                            self.formatter.display_error(f"Failed to move task #{task.id}.")
                    else:
                        self.formatter.display_error(f"Task #{task.id} no longer found (may have been moved already).")
                except Exception as e:
                    self.formatter.display_error(f"Error moving task #{task.id}: {e}")
            
            # Summary message for multiple tasks
            if len(task_ids) > 1:
                self.formatter.display_success(f"Moved {moved_count} of {len(task_ids)} tasks.")
                
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


class RecurTaskCommand(Command):
    """Command for creating recurring instances of a task."""
    
    def execute(self, task_id: int, interval: str, end_date: str = None, 
                count: int = None, target_file: str = None,
                directory: Path = None, specified_files: list = None) -> None:
        """Execute the recur task command.
        
        Args:
            task_id: ID of the task to make recurring
            interval: Interval expression (e.g., "1w", "30d", "3m")
            end_date: Optional end date in YYYY-MM-DD format
            count: Optional maximum number of occurrences  
            target_file: Optional target file for new tasks
            directory: Directory to search for tasks
            specified_files: Specific files to search in
        """
        try:
            # Create recurring tasks
            created_tasks = self.task_service.recur_task_by_id(
                task_id=task_id,
                interval=interval,
                end_date=end_date,
                count=count,
                target_file=target_file,
                directory=directory,
                specified_files=specified_files
            )
            
            # Display success message
            if created_tasks:
                self.formatter.display_success(
                    f"Created {len(created_tasks)} recurring instance(s) of task #{task_id:03d}"
                )
                
                # Show additional info about created tasks
                if target_file:
                    target_display = self._get_relative_path(target_file)
                    from rich.console import Console
                    console = Console()
                    console.print(f"📁 Recurring tasks added to {target_display} with {interval} interval", style="dim")
                else:
                    from rich.console import Console  
                    console = Console()
                    console.print(f"📁 Recurring tasks added to original file with {interval} interval", style="dim")
                
                # Display date range if we have dates
                if len(created_tasks) >= 1:
                    first_date = created_tasks[0].due_date
                    last_date = created_tasks[-1].due_date
                    if first_date and last_date:
                        from rich.console import Console
                        console = Console()
                        if first_date == last_date:
                            console.print(f"📅 Due date: {first_date}", style="dim")
                        else:
                            console.print(f"📅 Date range: {first_date} to {last_date}", style="dim")
            else:
                self.formatter.display_warning(f"No recurring instances created for task #{task_id:03d}")
                
        except Exception as e:
            if isinstance(e, XitError):
                self.formatter.display_error(str(e))
            else:
                self.formatter.display_error(f"Error creating recurring tasks: {e}")
    
    def _get_relative_path(self, file_path: str) -> str:
        """Get relative path for display purposes."""
        try:
            return str(Path(file_path).relative_to(Path.cwd()))
        except ValueError:
            return file_path


class EditTaskCommand(Command):
    """Command for editing task descriptions."""
    
    def execute(self, task_id: int, description: str,
                directory: Path = None, specified_files: list = None) -> None:
        """Execute the edit task command.
        
        Args:
            task_id: ID of the task to edit
            description: New description text
            directory: Directory to search for tasks
            specified_files: Specific files to search in
        """
        try:
            # Resolve file paths
            file_paths = self.file_service.resolve_file_paths(
                None, directory, specified_files
            )
            
            if not file_paths:
                self.formatter.display_warning("No task files found.")
                return
            
            # Edit the task description
            updated_task = self.task_service.update_task_description(
                task_id=task_id,
                new_description=description,
                file_paths=file_paths
            )
            
            if updated_task:
                relative_path = self._get_relative_path(updated_task.file)
                self.formatter.display_success(
                    f"✓ Updated description for task #{task_id:03d} in {relative_path}: \"{updated_task.description.text}\""
                )
            else:
                self.formatter.display_error(f"Task #{task_id:03d} not found")
                
        except Exception as e:
            if isinstance(e, XitError):
                self.formatter.display_error(str(e))
            else:
                self.formatter.display_error(f"Error editing task: {e}")

    def _get_relative_path(self, file_path: str) -> str:
        """Get relative path for display."""
        try:
            return str(Path(file_path).relative_to(Path.cwd()))
        except ValueError:
            return file_path


class PriorityTaskCommand(Command):
    """Command for setting task priority."""
    
    def execute(self, task_id: int, priority: int,
                directory: Path = None, specified_files: list = None) -> None:
        """Execute the priority task command.
        
        Args:
            task_id: ID of the task to modify
            priority: Priority level (0, 1, 2, etc.)
            directory: Directory to search for tasks
            specified_files: Specific files to search in
        """
        try:
            # Validate priority
            if priority < 0:
                self.formatter.display_error("Priority must be a non-negative integer (0, 1, 2, etc.)")
                return
            
            # Resolve file paths
            file_paths = self.file_service.resolve_file_paths(
                None, directory, specified_files
            )
            
            if not file_paths:
                self.formatter.display_warning("No task files found.")
                return
            
            # Set the task priority
            success = self.task_service.set_task_priority(
                task_id=task_id,
                priority=priority,
                directory=directory,
                specified_files=specified_files
            )
            
            if success:
                priority_display = f"({priority})" if priority > 0 else "(none)"
                self.formatter.display_success(f"Set priority {priority_display} for task #{task_id:03d}")
            else:
                self.formatter.display_error(f"Task #{task_id:03d} not found")
                
        except Exception as e:
            if isinstance(e, XitError):
                self.formatter.display_error(str(e))
            else:
                self.formatter.display_error(f"Error setting task priority: {e}")


class TagTaskCommand(Command):
    """Command for adding tags to tasks."""
    
    def execute(self, task_id: int, tag: str,
                directory: Path = None, specified_files: list = None) -> None:
        """Execute the tag task command.
        
        Args:
            task_id: ID of the task to modify
            tag: Tag to add (without # prefix)
            directory: Directory to search for tasks
            specified_files: Specific files to search in
        """
        try:
            # Clean the tag (remove # if present)
            tag = tag.lstrip('#')
            
            # Validate tag format
            if not tag or ' ' in tag:
                self.formatter.display_error("Tag must be a single word without spaces")
                return
            
            # Resolve file paths
            file_paths = self.file_service.resolve_file_paths(
                None, directory, specified_files
            )
            
            if not file_paths:
                self.formatter.display_warning("No task files found.")
                return
            
            # Add the tag
            success = self.task_service.add_task_tag(
                task_id=task_id,
                tag=tag,
                file_paths=file_paths
            )
            
            if success:
                self.formatter.display_success(f"Added tag #{tag} to task #{task_id:03d}")
            else:
                self.formatter.display_error(f"Task #{task_id:03d} not found")
                
        except Exception as e:
            if isinstance(e, XitError):
                self.formatter.display_error(str(e))
            else:
                self.formatter.display_error(f"Error adding tag: {e}")


class UntagTaskCommand(Command):
    """Command for removing tags from tasks."""
    
    def execute(self, task_id: int, tag: str,
                directory: Path = None, specified_files: list = None) -> None:
        """Execute the untag task command.
        
        Args:
            task_id: ID of the task to modify
            tag: Tag to remove (without # prefix)
            directory: Directory to search for tasks
            specified_files: Specific files to search in
        """
        try:
            # Clean the tag (remove # if present)
            tag = tag.lstrip('#')
            
            # Resolve file paths
            file_paths = self.file_service.resolve_file_paths(
                None, directory, specified_files
            )
            
            if not file_paths:
                self.formatter.display_warning("No task files found.")
                return
            
            # Remove the tag
            success = self.task_service.remove_task_tag(
                task_id=task_id,
                tag=tag,
                file_paths=file_paths
            )
            
            if success:
                self.formatter.display_success(f"Removed tag #{tag} from task #{task_id:03d}")
            else:
                self.formatter.display_error(f"Task #{task_id:03d} not found")
                
        except Exception as e:
            if isinstance(e, XitError):
                self.formatter.display_error(str(e))
            else:
                self.formatter.display_error(f"Error removing tag: {e}")


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
    
    @staticmethod
    def create_recur_command(formatter: TaskFormatter = None) -> RecurTaskCommand:
        """Create a recur task command."""
        return RecurTaskCommand(formatter)
    
    @staticmethod
    def create_edit_command(formatter: TaskFormatter = None) -> EditTaskCommand:
        """Create an edit task command."""
        return EditTaskCommand(formatter)
    
    @staticmethod
    def create_priority_command(formatter: TaskFormatter = None) -> PriorityTaskCommand:
        """Create a priority task command."""
        return PriorityTaskCommand(formatter)
    
    @staticmethod
    def create_tag_command(formatter: TaskFormatter = None) -> TagTaskCommand:
        """Create a tag task command."""
        return TagTaskCommand(formatter)
    
    @staticmethod
    def create_untag_command(formatter: TaskFormatter = None) -> UntagTaskCommand:
        """Create an untag task command."""
        return UntagTaskCommand(formatter)