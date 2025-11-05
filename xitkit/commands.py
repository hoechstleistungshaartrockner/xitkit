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
from .location import Location
import questionary as ques
from .fileparser import File, FileParser
from .file_repository import FileRepository
from .tags import Tag
import re


class Command(ABC):
    """Abstract base class for CLI commands."""
    
    def __init__(self, formatter: TaskFormatter = None):
        """Initialize command with optional formatter."""
        self.formatter = formatter or TaskFormatter()
        self.task_service = TaskService()
        self.file_service = FileDiscoveryService()
    
    @abstractmethod
    def _execute(self, **kwargs) -> Any:
        """Execute the command with given arguments."""
        pass
    
    def ask_single_choice(self, prompt: str, choices: list[str]) -> list[str]:
        """Prompt user to select a single choice from a list."""
        selection = ques.select(
            prompt,
            choices=choices
        ).ask()
        return [selection]
    
    def ask_multiple_choice(self, prompt: str, choices: list[str]) -> list[str]:
        """Prompt user to select multiple choices from a list."""
        selections = ques.checkbox(
            prompt,
            choices=choices
        ).ask()
        return selections

    def load_files(self, file_paths: list[str]) -> list[File]:
        """Load files from given paths using the FileRepository."""
        file_paths = sorted(set(file_paths))
        repo = FileRepository()
        return [repo.get_file(path) for path in file_paths]
    
    def select_files(self, 
                          file_paths: list[str], 
                          directory: Path | None, 
                          interactive: bool = False,
                          only_one: bool = False) -> list[str] | str | None:
        """
        Resolve the file path from given inputs, prompting if necessary.
        
        Behavior:
        
        | case | file_paths    | interactive | only_one | Result                          |
        |------|---------------|-------------|----------|---------------------------------|
        | 1    | None provided | False       | True     | "todo.xit"                      |      
        | 2    | One provided  | Any         | Any      | The provided file path          |
        | 3    | Multiple      | False       | True     | Error (single file expected)    |
        | 4    | Multiple      | False       | False    | All provided file paths         |
        | 5    | Multiple      | True        | False    | Prompt user, multiple choice from the provided options |
        | 6    | Multiple      | True        | True     | Prompt user, single choice       |
        | 7    | None provided | False       | False    | All discovered file paths       |
        | 8    | None provided | True        | False    | Prompt user, multiple choice from discovered files |
        | 9    | None provided | True        | True     | Prompt user, single choice      |


        Args:
            file_paths: List of specified file paths
            directory: Base directory for relative paths
            interactive: Whether to prompt for missing information
            only_one: Whether only one file is expected
            
        Returns:
            Resolved file path(s) or None if error occurred.
        """     
        
        if all(fp is None for fp in file_paths):
            file_paths = []
        
        if file_paths == []:
            assert not directory is None, "Directory must be provided"
            
        # Case 1: Default to "todo.xit" if no inputs and only_one
        if not file_paths and not interactive and only_one:
            self.formatter.display_warning("Defaulting to 'todo.xit'.")
            return [directory / "todo.xit"]
        
        # Case 2: Single specified file
        if len(file_paths) == 1:
            return file_paths
        
        # Case 3 and 10: Multiple specified files but only_one
        if only_one and not interactive:
            self.formatter.display_error("Multiple files found, but only one expected.")
            return None

        # Case 4: Multiple specified files but no directory, non-interactive, not only_one
        if len(file_paths) > 1 and not directory and not interactive and not only_one:
            return file_paths
        
        # Case 5: Multiple specified files, interactive, not only_one
        if len(file_paths) > 1 and interactive and not only_one:
            # Prompt for multiple file selection
            selected_files = self.ask_multiple_choice(
                "Select relevant files:",
                file_paths
            )
            return selected_files

        # Case 6: Multiple specified files, interactive, only_one
        if len(file_paths) > 1 and interactive and only_one:
            # Prompt for single file selection
            selected_files = self.ask_single_choice(
                "Select a file:",
                file_paths
            )
            return selected_files

        all_files = self.file_service.resolve_file_paths(directory, file_paths)
        
        if not all_files:
            self.formatter.display_warning("No task files found.")
            return None
        
        # Case 7: No specified files, directory provided, non-interactive, not only_one
        if not interactive and not only_one:
            return all_files
        
        # Case 8: No specified files, directory provided, interactive, not only_one
        if only_one:
            # Prompt for single file selection
            selected_file = self.ask_single_choice(
                "Select a file:",
                all_files
            )
            return selected_file
        
        # Case 9: No specified files, directory provided, interactive, not only_one
        # Prompt for multiple file selection
        selected_files = self.ask_multiple_choice(
            "Select relevant files:",
            all_files
        )
        return selected_files
        
    def select_section(self, sections: list, interactive: bool = False, single: bool = False) -> list[str]:
        """Interactively ask the user to select sections."""
        
        if len(sections) == 1 and interactive:
            self.formatter.display_warning(f"Only one section '{sections[0]}' available, selecting it.")
            return sections
        
        if interactive and single:
            selection = ques.select(
                "Select a section:",
                choices=sections
            ).ask()
            return [selection]
        
        if interactive and not single:
            selections = ques.checkbox(
                "Select sections:",
                choices=sections
            ).ask()
            return selections
        
        if single:
            return [sections[-1]]
        
        return sections
    
    def select_tasks(self, tasks, interactive: bool = False) -> list[int]:
        """
        Select tasks from a list, either interactively or by returning all IDs.
        
        Args:
            tasks: List of Task objects
            interactive: Whether to prompt for selection

        Returns:
            List of selected task IDs
        """
        if not interactive:
            return [task.id for task in tasks]
        
        task_choices = [str(self.formatter.format_task(t)) for t in tasks]
        selected_task_lines = self.ask_multiple_choice(
            "Select tasks to mark:",
            task_choices
        )
        task_ids = [int(l.split()[0].lstrip('#')) for l in selected_task_lines]
        
        return task_ids

    def select_status(self, status: str = "OPEN", interactive: bool = False) -> Status:
        """Select status either interactively or from provided string."""

        if status is None and interactive:
            status = self.ask_single_choice(
                "Select status to mark tasks with:",
                ['OPEN', 'DONE', 'ONGOING', 'OBSOLETE', 'INQUESTION']
            )[0]

        return Status.from_string(status)
    
    def select_duedate(self, due_date: str = None, interactive: bool = False) -> DueDate | None:
        """Select due date either interactively or from provided string."""
        
        if due_date is None and interactive:
            due_date = ques.text("Enter new due date (natural language):").ask()
        
        if due_date:
            return DueDate.from_string(due_date)
        
        return None
    
    def select_priority(self, priority: int = None, interactive: bool = False) -> Priority:
        """Select priority either interactively or from provided integer."""
        
        if priority is None and interactive:
            priority_str = ques.text("Enter priority level (0 = no priority, 1+ = number of exclamation marks):").ask()
            try:
                priority = int(priority_str)
            except ValueError:
                self.formatter.display_error("Invalid priority input. Must be a non-negative integer.")
                return None
        
        if priority is not None:
            return Priority(priority)
        
        return None

    def select_deletion_method(self, force_deletion: bool = False, interactive: bool = False) -> str:
        """Select deletion method either interactively or from provided string."""
        
        if not force_deletion and interactive:
            choice = self.ask_single_choice(
                "Select deletion method:",
                ['mark as obsolete', 'delete permanently']
            )[0]
            return choice
        
        if force_deletion:
            return 'delete permanently'
        return 'mark as obsolete'
    
    def select_recurrence_params(self, params: tuple = None, interactive: bool = False) -> tuple:
        """
        Select recurrence parameters either interactively or from provided tuple.
        
        Args:
            params: Tuple of (interval, end_date, count)
            interactive: Whether to prompt for missing information
        
        Returns:
            Tuple of (interval, end_date, count)
        """
        interval, end_date, count = params if params else (None, None, None)
        
        if (end_date and count):
            raise XitError("Cannot specify both end_date and count.")
        
        if interval is None and interactive:
            interval = ques.text("Enter recurrence interval (e.g., '1d', '2w', '3m', '1y', '7m3w'):").ask()
            
        if (end_date is None and count is None) and interactive:
            end = ques.text("Enter number of occurrences or end date (YYYY-MM-DD):").ask()
            is_count = re.compile(r'^\d{1,4}$')
            if is_count.match(end):
                count, end_date = int(end), None
            else:
                count, end_date = None, end

        return interval, end_date, count
    
    def select_existing_tags(self):
        pass
    
    def select_new_tags(self, tags: list[str] = None, interactive: bool = False) -> list[str]:
        """Select new tags either interactively or from provided list."""
        
        if (not tags or len(tags) == 0) and interactive:
            tag_input = ques.text("Enter tag names (comma-separated, without # prefix):").ask()
            tags = [tag.strip() for tag in tag_input.split(',') if tag.strip()]
        
        return tags or []

    @abstractmethod
    def check_inputs(self, *args, **kwargs) -> None:
        pass

    def execute(self, *args, **kwargs) -> None:
        """wrapper to execute command with error handling."""
        try:
            self.check_inputs(*args, **kwargs)

            self._execute(*args, **kwargs)
        except XitError as e:
            self.formatter.display_error(str(e))
            if kwargs.get("debug"):
                raise e
        except Exception as e:
            self.formatter.display_error(f"Unexpected error: {e}")
            if kwargs.get("debug"):
                raise e
       

class UpdateCommand(Command):
    """Abstract base class for commands that update tasks."""
    
    def __init__(self, formatter: TaskFormatter = None):
        super().__init__(formatter)
        self._confirm = lambda task: f"✓ Updated task #{task.id:03d} in {task.location.file_path}:\n{task.to_checkbox_format()}\n"
    
    def find_tasks(self, directory: Path = None, specified_files: list = None,
                   task_ids: list[int] = None,
                   interactive: bool = False) -> list[Task]:
        """Helper method to find and return tasks based on inputs."""
        
        # Resolve file paths
        file_paths = self.select_files(
            specified_files, directory, interactive=interactive, only_one=False)
        
        if not file_paths:
            raise XitError("No files selected.")
        
        self.load_files(file_paths)
        
        # Load and filter tasks
        all_tasks = FileRepository()._tasks.values()
        available_sections = set()
        
        for task in all_tasks:
            if task.location.section:
                available_sections.add(task.location.section)
        available_sections = sorted(list(available_sections))
            
        selected_sections = self.select_section(available_sections, interactive, single=False)
        if not selected_sections:
            self.formatter.display_warning("No sections selected.")
            return []
        all_tasks = [
                    task for task in all_tasks 
                    if task.location.section in selected_sections
                ]
        
        if not all_tasks:
            raise XitError("No tasks found in the specified files.")
        
        if not task_ids and interactive:
            task_ids = self.select_tasks(all_tasks, interactive=interactive)
            
        all_tasks = [task for task in all_tasks if task.id in task_ids]
        if not all_tasks:
            raise XitError("No matching tasks found for the specified IDs.")          
        
        return all_tasks
    
    @abstractmethod
    def _edit_task(self, task: Task, **kwargs) -> tuple[Task, bool]:
        """Abstract method to edit a task."""
        pass
    
    @abstractmethod
    def _select_new_attribute(self, attribute: Any = None, interactive: bool = False) -> Any:
        """Abstract method to select new attribute value."""
        pass
    
    def _execute(self, task_ids: list, new_attribute: Any = None, directory: Path = None, 
                specified_files: list = None, interactive: bool = False,
                debug: bool = False) -> None:
        """
        Execute the update task command for one or more tasks.
        Child classes should override _edit_task and _select_new_attribute methods.
        
        Args:
            task_ids: List of task IDs to update
            new_attribute: New attribute value to set
            directory: Directory to search for tasks
            specified_files: List of explicitly specified files
            interactive: Whether to run in interactive mode
            debug: Whether to enable debug mode
        """
        
        tasks_to_update = self.find_tasks(directory, specified_files, task_ids, interactive=interactive)
        
        new_attribute = self._select_new_attribute(attribute=new_attribute, interactive=interactive)
        if new_attribute is None:
            raise XitError("Attribute not specified.")
        
        update_counter = 0
        for task in tasks_to_update:
            # Find and update the task
            task, success = self._edit_task(task, new_attribute=new_attribute)
            
            if success:
                # Display confirmation message
                self.formatter.display_success(self._confirm(task))
                update_counter += 1
            else:
                self.formatter.display_error(f"Task #{task.id} not found.")
                return

        # Summary message for multiple tasks
        if len(tasks_to_update) > 1:
            self.formatter.display_success(f"Processed {update_counter} of {len(tasks_to_update)} tasks.")
            
    def select_new_location(self, location: tuple = None, interactive: bool = False) -> Location:
        """Select new location either interactively or from provided tuple."""
        
        # unpack location
        file_path, section = location if location else (None, None)
        
        if file_path is None and interactive:
            file_path = self.ask_single_choice("Select new file:", self.file_service.discover_task_files())[0]
        
        if section is None and interactive:
            # Load file to get sections
            file_obj = FileRepository().get_file(file_path)
            sections = list(file_obj.sections.keys())
            section = self.ask_single_choice("Select new section:", sections)[0]
        return Location(file_path=file_path, line_numbers=None, section=section)
    
    def check_inputs(self, *args, **kwargs) -> None:
        task_ids = kwargs.get("task_ids", [])
        interactive = kwargs.get("interactive", False)
        if not task_ids and not interactive:
            message = "Error: Must specify at least one task ID or use interactive mode"
            raise XitError(message)

        self._check_inputs(*args, **kwargs)

    def _check_inputs(self, *args, **kwargs) -> None:
        """Child classes can override this method for additional input checks."""
        pass

class ShowTasksCommand(Command):
    """Command for showing tasks with filtering options."""
    
    def _execute(self, directory: Path = None, 
                specified_files: list = None, 
                filters: TaskFilter = None,
                show_location: bool = False, 
                no_id: bool = False, 
                count_only: bool = False,
                sort_by: str = None, 
                sort_order: str = None, 
                interactive: bool = False,
                debug: bool = False) -> None:
        """Execute the show tasks command.
        
        Args:
            directory: Default directory to search
            specified_files: Explicitly specified files
            filters: Task filters to apply
            show_location: Whether to show location information
            no_id: Whether to hide task IDs
            count_only: Whether to show only count
            sort_by: Sort attribute (priority, due_date)
            sort_order: Sort order (asc, desc)
            interactive: Whether to interactively select files and sections
        """

        
        file_paths = self.select_files(
            specified_files, directory, interactive=interactive, only_one=False)
        
        if not file_paths:
            self.formatter.display_warning("No files selected.")
            return
        
        # Load and filter tasks
        self.load_files(file_paths)
        all_tasks = FileRepository()._tasks.values()
        available_sections = set()
        
        for task in all_tasks:
            if task.location.section:
                available_sections.add(task.location.section)
        available_sections = sorted(list(available_sections))
            
        selected_sections = self.select_section(available_sections, interactive, single=False)
        if not selected_sections:
            self.formatter.display_warning("No sections selected.")
            return
        all_tasks = [
                    task for task in all_tasks 
                    if task.location.section in selected_sections
                ]                    
        
        if not all_tasks:
            self.formatter.display_warning("No tasks found in the specified files.")
            return
        
        filtered_tasks = all_tasks
        if filters:
            filtered_tasks = self.task_service.filter_tasks(all_tasks, filters)
        
        # Sort tasks if requested
        if sort_by:
            filtered_tasks = self.task_service.sort_tasks(filtered_tasks, sort_by, sort_order or 'asc')

        # put checked tasks at the end regardless of sort order (single pass)
        non_checked_tasks = []
        checked_tasks = []
        for task in filtered_tasks:
            if task.status.status_type == StatusType.CHECKED:
                checked_tasks.append(task)
            else:
                non_checked_tasks.append(task)
        filtered_tasks = non_checked_tasks + checked_tasks
        
        # Display results
        if count_only:
            self.formatter.display_count(len(filtered_tasks))
        elif not filtered_tasks:
            self.formatter.display_warning("No tasks match the specified criteria.")
        else:
            self.formatter.display_tasks(filtered_tasks, show_location=show_location, no_id=no_id)
            self.formatter.display_summary(len(filtered_tasks), len(all_tasks))
                

    def check_inputs(self, *args, **kwargs):
        pass


class ShowStatsCommand(Command):
    """Command for showing task statistics."""

    def _execute(self, directory: Path = None, specified_files: list = None,
                debug: bool = False) -> None:
        """Execute the show stats command.
        
        Args:
            directory: Default directory to search
            specified_files: Explicitly specified files
        """
        # Resolve file paths
        file_paths = self.file_service.resolve_file_paths(
            directory, specified_files
        )
        
        if not file_paths:
            self.formatter.display_warning("No task files found.")
            return
        
        # Load tasks and calculate statistics
        file_objs = self.load_files(file_paths)
        all_tasks = FileRepository()._tasks.values()
        
        
        if not all_tasks:
            self.formatter.display_warning("No tasks found in the specified files.")
            return
        
        stats = self.task_service.get_task_statistics(all_tasks)
        if specified_files:
            self._display_statistics(stats, "specified files")
        elif directory:
            self._display_statistics(stats, str(directory))
        else:
            directory = Path.cwd()
            self._display_statistics(stats, directory)
            
    
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
                
    def check_inputs(self, *args, **kwargs):
        pass


class AddTaskCommand(Command):
    """Command for adding new tasks."""
    
    def _execute(self, 
                description: str, 
                file_path: str, 
                priority: int = None,
                due_date: str = None,
                tags: list = None,
                directory: Path = None,
                interactive: bool = False,
                debug: bool = False) -> None:
        """Execute the add task command.
        
        Args:
            description: The task description text
            file_path: Path to the file where task should be added
            directory: Base directory for relative paths
            priority: Priority level of the task
            due_date: Due date string for the task
            tags: List of string tags for the task
            interactive: Whether to prompt for missing information

        """
        file_path = self.select_files([file_path], 
                                            directory, 
                                            interactive=interactive,
                                            only_one=True)[0]
        Path(file_path).touch()  # Ensure file exists
        
        # Parse file to get sections
        files = self.load_files([file_path])
        sections = list(files[0].sections.values())

        # Select section if interactive, else use last section
        section = self.select_section([s.title for s in sections], interactive, single=True)[0]
        
        
        # Create a task object
        task = Task(
            description=description,
            location=Location(file_path=file_path, line_numbers=None, section=section),
            status=Status(StatusType.OPEN),
            priority=priority or 0,
            tags=tags or [],
            due_date=due_date,
        )
        
        # Add the task to the file
        file_obj = files[0]
        file_obj.add_task(task)
        file_obj.write()
        
        # Display confirmation message
        relative_path = self._get_relative_path(file_path)
        self.formatter.display_success(
            f"✓ Added task to {relative_path}: \"{task.description.text}\""
        )

    
    def _get_relative_path(self, file_path: str) -> str:
        """Get relative path for display purposes."""
        try:
            return str(Path(file_path).relative_to(Path.cwd()))
        except ValueError:
            return file_path
    
    def check_inputs(self, *args, **kwargs):
        description = kwargs.get("description", "").strip()
        file_path = kwargs.get("file_path", None)
        interactive = kwargs.get("interactive", False)
        if not description:
            raise XitError("Error: Task description cannot be empty.")
        # if not file_path and not interactive:
        #     raise XitError("Error: Must specify a file path or use interactive mode.")


class MarkTaskCommand(UpdateCommand):
    """Command for marking tasks with a specific status."""
    
    def _select_new_attribute(self, attribute = None, interactive = False):
        return self.select_status(status=attribute, interactive=interactive)
    
    def _edit_task(self, task: Task, new_attribute = None) -> tuple[Task, bool]:
        task.set_status(new_attribute)
        return task, task.save()
    
    def _check_inputs(self, *args, **kwargs):
        status = kwargs.get("new_attribute", None)
        interactive = kwargs.get("interactive", False)
        if not status and not interactive:
            raise XitError("Error: Must specify a status flag (--done, --open, --ongoing, --obsolete, --inquestion)")

  
class RescheduleTaskCommand(UpdateCommand):
    """Command for rescheduling tasks to new due dates."""
    
    def _select_new_attribute(self, attribute = None, interactive = False):
        return self.select_duedate(due_date=attribute, interactive=interactive)
    
    def _edit_task(self, task: Task, new_attribute = None) -> tuple[Task, bool]:
        task.set_due_date(new_attribute)
        return task, task.save()


class RemoveTaskCommand(UpdateCommand):
    """Command for removing tasks from files."""
    
    def _select_new_attribute(self, attribute = None, interactive = False):
        return self.select_deletion_method(force_deletion=attribute, interactive=interactive)
    
    def _edit_task(self, task: Task, new_attribute = None) -> tuple[Task, bool]:
        # This method is not used in RemoveTaskCommand
        file = FileRepository().get_file(task.location.file_path)
        if new_attribute == 'delete permanently':
            task.delete()
            self._confirm = lambda t: f"✓ Deleted task #{t.id:03d} from {t.location.file_path}."
            return task, file.write()
        elif new_attribute == 'mark as obsolete':
            task.set_status(Status(StatusType.OBSOLETE))
            return task, task.save()
        else:
            raise XitError("Invalid deletion method specified.")


class MoveTaskCommand(UpdateCommand):
    """Command for moving tasks between files."""
    
    def __init__(self, formatter: TaskFormatter = None):
        super().__init__(formatter)
        self._confirm = lambda task: f"✓ Moved task #{task.id:03d} to {task.location.file_path} (section: {task.location.section}):\n{task.to_checkbox_format()}\n"
    
    def _select_new_attribute(self, attribute = None, interactive = False):
        # Not used in MoveTaskCommand
        return self.select_new_location(location=attribute, interactive=interactive)
    
    def _edit_task(self, task: Task, new_attribute = None) -> tuple[Task, bool]:
        return task, task.move(new_attribute.file_path, new_attribute.section)
    
    def _check_inputs(self, *args, **kwargs):
        target_file, section = kwargs.get("new_attribute", (None, None))
        interactive = kwargs.get("interactive", False)
        if not target_file and not interactive:
            raise XitError("Error: Must specify new file path and section or use interactive mode.")
    

class RecurTaskCommand(UpdateCommand):
    """Command for creating recurring instances of a task."""
        
    def _select_new_attribute(self, attribute = None, interactive = False):
        return self.select_recurrence_params(params=attribute, interactive=interactive)
    
    def _edit_task(self, task: Task, new_attribute = None) -> tuple[Task, bool]:
        interval, end_date, count = new_attribute
        dates = task.recur(interval, end_date=end_date, count=count)
        due_date_original = task.due_date.implied_date
        new_tasks_checkbox_formats = [task.to_checkbox_format().replace(str(due_date_original), str(due_date)) for due_date in dates]
        self._confirm = lambda task: f"✓ Created {len(dates)} new instance(s) of task #{task.id:03d} in file {task.location.file_path} (section: {task.location.section}):\n" + "\n".join(new_tasks_checkbox_formats)
        return task, True
    
    def _check_inputs(self, *args, **kwargs):
            # Validate mutual exclusivity
        interval, end_date, count = kwargs.get("new_attribute", (None, None, None))
        interactive = kwargs.get("interactive", False)
            
        if end_date and count:
            raise XitError("Error: Cannot specify both --end-date and --count. Choose one.")

        
        if (not end_date and not count) and not interactive:
            raise XitError("Error: Must specify either --end-date or --count for recurrence limit or use interactive mode.")
        
        if not interval and not interactive:
            raise XitError("Error: Must specify --interval for recurrence or use interactive mode.")


class EditTaskCommand(Command):
    """Command for editing task descriptions."""
    
    def _execute(self, task_id: int, description: str,
                directory: Path = None, specified_files: list = None,
                debug: bool = False) -> None:
        """Execute the edit task command.
        
        Args:
            task_id: ID of the task to edit
            description: New description text
            directory: Directory to search for tasks
            specified_files: Specific files to search in
        """
        # Resolve file paths
        file_paths = self.file_service.resolve_file_paths(
            directory, specified_files
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
            relative_path = updated_task.location.file_path
            self.formatter.display_success(
                f"✓ Updated description for task #{task_id:03d} in {relative_path}: \"{updated_task.description.text}\""
            )
        else:
            self.formatter.display_error(f"Task #{task_id:03d} not found")
                


class PriorityTaskCommand(UpdateCommand):
    """Command for setting task priority."""
    
    def _select_new_attribute(self, attribute = None, interactive = False):
        return self.select_priority(priority=attribute, interactive=interactive)
    
    def _edit_task(self, task: Task, new_attribute = None):
        task.set_priority(new_attribute)
        return task, task.save()
    
    def _check_inputs(self, *args, **kwargs):
        priority = kwargs.get("new_attribute", None)
        interactive = kwargs.get("interactive", False)
        if priority is None and not interactive:
            raise XitError("Error: Must specify a priority level or use interactive mode")



class TagTaskCommand(UpdateCommand):
    """Command for adding tags to tasks."""
    
    def _select_new_attribute(self, attribute = None, interactive = False):
        return self.select_new_tags(tags=attribute, interactive=interactive)
    
    def _edit_task(self, task: Task, new_attribute = None):
        for tag in new_attribute:
            task.add_tag_by_name(tag)
        return task, task.save()
    
    def _check_inputs(self, *args, **kwargs):
        tags = kwargs.get("new_attribute", None)
        interactive = kwargs.get("interactive", False)
        if (not tags or len(tags) == 0) and not interactive:
            raise XitError("Error: Must specify at least one tag to add or use interactive mode")

class UntagTaskCommand(UpdateCommand):
    """Command for removing tags from tasks."""
    
    def _select_new_attribute(self, attribute = None, interactive = False):
        return self.select_new_tags(tags=attribute, interactive=interactive)
    
    def _edit_task(self, task: Task, new_attribute = None):
        for tag in new_attribute:
            task.remove_tag_by_name(tag)
        return task, task.save()
    
    def _check_inputs(self, *args, **kwargs):
        tags = kwargs.get("new_attribute", None)
        interactive = kwargs.get("interactive", False)
        if (not tags or len(tags) == 0) and not interactive:
            raise XitError("Error: Must specify at least one tag to remove or use interactive mode")
    
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