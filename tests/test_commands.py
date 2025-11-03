"""Tests for the Commands module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from xitkit.commands import (
    Command, ShowTasksCommand, ShowStatsCommand, AddTaskCommand, 
    MarkTaskCommand, RescheduleTaskCommand, RemoveTaskCommand, 
    MoveTaskCommand, RecurTaskCommand, EditTaskCommand, PriorityTaskCommand,
    TagTaskCommand, UntagTaskCommand, CommandFactory
)
from xitkit.services import TaskFilter
from xitkit.task import Task
from xitkit.priority import Priority
from xitkit.formatter import TaskFormatter
from xitkit.exceptions import XitError
from xitkit.location import Location
from tests.conftest import create_test_file
import os

class TestCommandBase:
    """Test the base Command class."""
    
    def test_command_is_abstract(self):
        """Test that Command is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            Command()
    
    def test_command_subclass_with_formatter(self):
        """Test command subclass with custom formatter."""
        class TestCommand(Command):
            def _execute(self, **kwargs):
                return "test"
        
        custom_formatter = TaskFormatter()
        cmd = TestCommand(custom_formatter)
        
        assert cmd.formatter is custom_formatter
        assert hasattr(cmd, 'task_service')
        assert hasattr(cmd, 'file_service')
    
    def test_command_subclass_default_formatter(self):
        """Test command subclass with default formatter."""
        class TestCommand(Command):
            def _execute(self, **kwargs):
                return "test"
        
        cmd = TestCommand()
        
        assert isinstance(cmd.formatter, TaskFormatter)
        assert hasattr(cmd, 'task_service')
        assert hasattr(cmd, 'file_service')

    def test_select_files(self, isolated_test_files):
        """Test the resolve_file_path helper method."""
        provided_file1 = isolated_test_files / "valid_status.xit"
        provided_file2 = isolated_test_files / "valid_priority.xit"
        class CommandReplica(Command):
            def ask_multiple_choice(self, prompt, choices):
                return [provided_file1, provided_file2]
            def _execute(self, *args, **kwargs):
                pass
            def ask_single_choice(self, prompt, choices):
                return [provided_file1]
        
        output = CommandReplica().select_files([], isolated_test_files, interactive=False, only_one=False)
        assert output == sorted([i.path for i in os.scandir(isolated_test_files)])
        
        output = CommandReplica().select_files([], isolated_test_files, interactive=False, only_one=True)
        assert output == [isolated_test_files / "todo.xit"]
        
        output = CommandReplica().select_files([], isolated_test_files, interactive=True, only_one=False)
        assert output == [provided_file1, provided_file2]

        output = CommandReplica().select_files([], isolated_test_files, interactive=True, only_one=True)
        assert output == [provided_file1]

        output = CommandReplica().select_files([provided_file1], isolated_test_files, interactive=False, only_one=False)
        assert output == [provided_file1]

        output = CommandReplica().select_files([provided_file1], isolated_test_files, interactive=False, only_one=True)
        assert output == [provided_file1]

        output = CommandReplica().select_files([provided_file1], isolated_test_files, interactive=True, only_one=False)
        assert output == [provided_file1]

        output = CommandReplica().select_files([provided_file1], isolated_test_files, interactive=True, only_one=True)
        assert output == [provided_file1]

        output = CommandReplica().select_files([provided_file1, provided_file2], isolated_test_files, interactive=False, only_one=False)
        assert output == [provided_file1, provided_file2]

        # raises error
        output = CommandReplica().select_files([provided_file1, provided_file2], isolated_test_files, interactive=False, only_one=True)
        assert output is None

        output = CommandReplica().select_files([provided_file1, provided_file2], isolated_test_files, interactive=True, only_one=False)
        assert output == [provided_file1, provided_file2]

        output = CommandReplica().select_files([provided_file1, provided_file2], isolated_test_files, interactive=True, only_one=True)
        assert output == [provided_file1]


        

class TestShowTasksCommand:
    """Test ShowTasksCommand functionality."""
    
    @pytest.fixture
    def show_command(self):
        """Create a ShowTasksCommand instance with mocked dependencies."""
        formatter = Mock(spec=TaskFormatter)
        cmd = ShowTasksCommand(formatter)
        
        # Mock the services
        cmd.task_service = Mock()
        cmd.file_service = Mock()
        
        return cmd
    
    def test_show_command_creation(self):
        """Test creating a ShowTasksCommand."""
        cmd = ShowTasksCommand()
        assert isinstance(cmd, ShowTasksCommand)
        assert isinstance(cmd.formatter, TaskFormatter)
    
    def test_execute_basic_success(self, show_command):
        """Test successful execution with basic parameters."""
        # Mock select_files to return test files
        show_command.select_files = Mock(return_value=["/test.xit"])
        
        # Create a task with proper section information
        from xitkit.location import Location
        test_task = Task("Test task", location=Location("/test.xit", 1), status="OPEN", priority=0, tags=[], due_date=None)
        test_task.location.section = "Default"  # Give the task a section
        
        # Mock task service
        show_command.task_service.load_tasks.return_value = [test_task]
        
        # Mock section selection to return the same section as the task
        show_command.select_section = Mock(return_value=["Default"])
        
        # Execute command
        show_command.execute(
            directory=Path("/test"),
            specified_files=None,
            filters=None,
            show_location=False,
            count_only=False
        )
        
        # Verify interactions
        show_command.select_files.assert_called_once()
        show_command.task_service.load_tasks.assert_called_once_with(["/test.xit"])
        show_command.formatter.display_tasks.assert_called_once()
        show_command.formatter.display_summary.assert_called_once()
    
    def test_execute_no_files_found(self, show_command):
        """Test execution when no files are found."""
        show_command.select_files = Mock(return_value=None)
        
        show_command.execute()
        
        show_command.formatter.display_warning.assert_called_once_with(
            "No files selected."
        )
    
    def test_execute_no_tasks_found(self, show_command):
        """Test execution when no tasks are found in files."""
        show_command.select_files = Mock(return_value=["/test.xit"])
        show_command.task_service.load_tasks.return_value = []
        show_command.select_section = Mock(return_value=["Default"])  # Mock section selection
        
        show_command.execute()
        
        show_command.formatter.display_warning.assert_called_once_with(
            "No tasks found in the specified files."
        )
    
    def test_execute_with_filters(self, show_command):
        """Test execution with task filters."""
        from xitkit.location import Location
        
        # Create tasks with proper sections
        task1 = Task("Open task", location=Location("/test.xit", 1), status="OPEN", priority=0, tags=[], due_date=None)
        task1.location.section = "Default"
        task2 = Task("Done task", location=Location("/test.xit", 2), status="DONE", priority=0, tags=[], due_date=None)
        task2.location.section = "Default"
        
        tasks = [task1, task2]
        filtered_tasks = [task1]  # Only open task
        
        show_command.select_files = Mock(return_value=["/test.xit"])
        show_command.task_service.load_tasks.return_value = tasks
        show_command.task_service.filter_tasks.return_value = filtered_tasks
        show_command.select_section = Mock(return_value=["Default"])
        
        filters = TaskFilter(status="OPEN")
        show_command.execute(filters=filters)
        
        show_command.task_service.filter_tasks.assert_called_once_with(tasks, filters)
        show_command.formatter.display_tasks.assert_called_once_with(
            filtered_tasks, show_location=False, no_id=False
        )
        show_command.formatter.display_summary.assert_called_once_with(1, 2)
    
    def test_execute_no_filtered_matches(self, show_command):
        """Test execution when filters match no tasks."""
        from xitkit.location import Location
        
        task = Task("Task", location=Location("/test.xit", 1), status="OPEN", priority=0, tags=[], due_date=None)
        task.location.section = "Default"
        tasks = [task]
        
        show_command.select_files = Mock(return_value=["/test.xit"])
        show_command.task_service.load_tasks.return_value = tasks
        show_command.task_service.filter_tasks.return_value = []  # No matches
        show_command.select_section = Mock(return_value=["Default"])
        
        filters = TaskFilter(status="DONE")
        show_command.execute(filters=filters)
        
        show_command.formatter.display_warning.assert_called_once_with(
            "No tasks match the specified criteria."
        )
    
    def test_execute_count_only(self, show_command):
        """Test execution with count_only=True."""
        from xitkit.location import Location
        
        task = Task("Task", location=Location("/test.xit", 1), status="OPEN", priority=0, tags=[], due_date=None)
        task.location.section = "Default"
        tasks = [task]

        show_command.select_files = Mock(return_value=["/test.xit"])
        show_command.task_service.load_tasks.return_value = tasks
        show_command.task_service.filter_tasks.return_value = tasks
        show_command.select_section = Mock(return_value=["Default"])
        
        show_command.execute(count_only=True)
        
        show_command.formatter.display_count.assert_called_once_with(1)
        show_command.formatter.display_tasks.assert_not_called()
    
    def test_execute_with_line_numbers(self, show_command):
        """Test execution with show_location=True."""
        from xitkit.location import Location
        
        task = Task("Task", location=Location("/test.xit", 1), status="OPEN", priority=0, tags=[], due_date=None)
        task.location.section = "Default"
        tasks = [task]
        
        show_command.select_files = Mock(return_value=["/test.xit"])
        show_command.task_service.load_tasks.return_value = tasks
        show_command.task_service.filter_tasks.return_value = tasks
        show_command.select_section = Mock(return_value=["Default"])
        
        show_command.execute(show_location=True)
        
        show_command.formatter.display_tasks.assert_called_once_with(
            tasks, show_location=True, no_id=False
        )
    
    def test_execute_handles_xit_error(self, show_command):
        """Test execution handles XitError properly."""
        show_command.select_files = Mock(side_effect=XitError("Test error"))
        
        show_command.execute()
        
        show_command.formatter.display_error.assert_called_once_with("Test error")
    
    def test_execute_handles_unexpected_error(self, show_command):
        """Test execution handles unexpected errors."""
        show_command.select_files = Mock(side_effect=ValueError("Unexpected"))
        
        show_command.execute()
        
        show_command.formatter.display_error.assert_called_once_with(
            "Unexpected error: Unexpected"
        )

    def test_execute_with_sort_priority_asc(self, show_command):
        """Test execution with sort by priority ascending."""
        from xitkit.location import Location
        
        task1 = Task("High priority", location=Location("/test.xit", 1), status="OPEN", priority=Priority(2), tags=[], due_date=None)
        task1.location.section = "Default"
        task2 = Task("Low priority", location=Location("/test.xit", 2), status="OPEN", priority=Priority(0), tags=[], due_date=None)
        task2.location.section = "Default"
        task3 = Task("Medium priority", location=Location("/test.xit", 3), status="OPEN", priority=Priority(1), tags=[], due_date=None)
        task3.location.section = "Default"
        
        tasks = [task1, task2, task3]
        
        show_command.select_files = Mock(return_value=["/test.xit"])
        show_command.task_service.load_tasks.return_value = tasks
        show_command.task_service.filter_tasks.return_value = tasks
        show_command.task_service.sort_tasks.return_value = [task2, task3, task1]  # Sorted by priority asc
        show_command.select_section = Mock(return_value=["Default"])
        
        show_command.execute(sort_by='priority', sort_order='asc')
        
        show_command.task_service.sort_tasks.assert_called_once_with(tasks, 'priority', 'asc')
        
    def test_execute_with_sort_priority_desc(self, show_command):
        """Test execution with sort by priority descending."""
        from xitkit.location import Location
        
        task1 = Task("High priority", location=Location("/test.xit", 1), status="OPEN", priority=Priority(2), tags=[], due_date=None)
        task1.location.section = "Default"
        task2 = Task("Low priority", location=Location("/test.xit", 2), status="OPEN", priority=Priority(0), tags=[], due_date=None)
        task2.location.section = "Default"
        task3 = Task("Medium priority", location=Location("/test.xit", 3), status="OPEN", priority=Priority(1), tags=[], due_date=None)
        task3.location.section = "Default"
        
        tasks = [task1, task2, task3]
        
        show_command.select_files = Mock(return_value=["/test.xit"])
        show_command.task_service.load_tasks.return_value = tasks
        show_command.task_service.filter_tasks.return_value = tasks
        show_command.task_service.sort_tasks.return_value = [task1, task3, task2]  # Sorted by priority desc
        show_command.select_section = Mock(return_value=["Default"])
        
        show_command.execute(sort_by='priority', sort_order='desc')
        
        show_command.task_service.sort_tasks.assert_called_once_with(tasks, 'priority', 'desc')
        
    def test_execute_with_sort_due_date_asc(self, show_command):
        """Test execution with sort by due_date ascending."""
        from xitkit.duedate import DueDate
        from xitkit.location import Location
        
        task1 = Task("Task 1", location=Location("/test.xit", 1), status="OPEN", priority=Priority(0), tags=[], due_date=DueDate.from_string("2025-10-22"))
        task1.location.section = "Default"
        task2 = Task("Task 2", location=Location("/test.xit", 2), status="OPEN", priority=Priority(0), tags=[], due_date=DueDate.from_string("2025-10-20"))
        task2.location.section = "Default"
        task3 = Task("Task 3", location=Location("/test.xit", 3), status="OPEN", priority=Priority(0), tags=[], due_date=None)
        task3.location.section = "Default"
        
        tasks = [task1, task2, task3]
        
        show_command.select_files = Mock(return_value=["/test.xit"])
        show_command.task_service.load_tasks.return_value = tasks
        show_command.task_service.filter_tasks.return_value = tasks
        show_command.task_service.sort_tasks.return_value = [task2, task1, task3]  # Sorted by due_date asc
        show_command.select_section = Mock(return_value=["Default"])
        
        show_command.execute(sort_by='due_date', sort_order='asc')
        
        show_command.task_service.sort_tasks.assert_called_once_with(tasks, 'due_date', 'asc')
        
    def test_execute_with_sort_due_date_desc(self, show_command):
        """Test execution with sort by due_date descending."""
        from xitkit.duedate import DueDate
        from xitkit.location import Location
        
        task1 = Task("Task 1", location=Location("/test.xit", 1), status="OPEN", priority=Priority(0), tags=[], due_date=DueDate.from_string("2025-10-22"))
        task1.location.section = "Default"
        task2 = Task("Task 2", location=Location("/test.xit", 2), status="OPEN", priority=Priority(0), tags=[], due_date=DueDate.from_string("2025-10-20"))
        task2.location.section = "Default"
        task3 = Task("Task 3", location=Location("/test.xit", 3), status="OPEN", priority=Priority(0), tags=[], due_date=None)
        task3.location.section = "Default"
        
        tasks = [task1, task2, task3]
        
        show_command.select_files = Mock(return_value=["/test.xit"])
        show_command.task_service.load_tasks.return_value = tasks
        show_command.task_service.filter_tasks.return_value = tasks
        show_command.task_service.sort_tasks.return_value = [task1, task2, task3]  # Sorted by due_date desc
        show_command.select_section = Mock(return_value=["Default"])
        
        show_command.execute(sort_by='due_date', sort_order='desc')
        
        show_command.task_service.sort_tasks.assert_called_once_with(tasks, 'due_date', 'desc')

    def test_execute_sort_without_order_defaults_asc(self, show_command):
        """Test that sorting without order defaults to ascending."""
        from xitkit.location import Location
        
        task = Task("Task", location=Location("/test.xit", 1), status="OPEN", priority=Priority(0), tags=[], due_date=None)
        task.location.section = "Default"
        tasks = [task]
        
        show_command.select_files = Mock(return_value=["/test.xit"])
        show_command.task_service.load_tasks.return_value = tasks
        show_command.task_service.filter_tasks.return_value = tasks
        show_command.task_service.sort_tasks.return_value = tasks
        show_command.select_section = Mock(return_value=["Default"])
        
        show_command.execute(sort_by='priority')  # No sort_order specified
        
        show_command.task_service.sort_tasks.assert_called_once_with(tasks, 'priority', 'asc')


class TestShowStatsCommand:
    """Test ShowStatsCommand functionality."""
    
    @pytest.fixture
    def stats_command(self):
        """Create a ShowStatsCommand instance with mocked dependencies."""
        formatter = Mock(spec=TaskFormatter)
        cmd = ShowStatsCommand(formatter)
        
        # Mock the services
        cmd.task_service = Mock()
        cmd.file_service = Mock()
        
        return cmd
    
    def test_stats_command_creation(self):
        """Test creating a ShowStatsCommand."""
        cmd = ShowStatsCommand()
        assert isinstance(cmd, ShowStatsCommand)
        assert isinstance(cmd.formatter, TaskFormatter)
    
    def test_execute_basic_success(self, stats_command):
        """Test successful execution of stats command."""
        tasks = [
            Task("Open task", location=("/test.xit", 1), status="OPEN", priority=1, tags=["#work"], due_date="2025-12-31"),
            Task("Done task", location=("/test.xit", 2), status="DONE", priority=0, tags=[], due_date=None)
        ]
        
        stats = {
            'total_tasks': 2,
            'status_counts': {'OPEN': 1, 'DONE': 1},
            'priority_counts': {0: 1, 1: 1},
            'files_with_tasks': {"/test.xit"},
            'tasks_with_due_dates': 1,
            'tasks_with_tags': 1
        }
        
        stats_command.file_service.resolve_file_paths.return_value = ["/test.xit"]
        stats_command.task_service.load_tasks.return_value = tasks
        stats_command.task_service.get_task_statistics.return_value = stats
        
        stats_command.execute()
        
        stats_command.file_service.resolve_file_paths.assert_called_once()
        stats_command.task_service.load_tasks.assert_called_once_with(["/test.xit"])
        stats_command.task_service.get_task_statistics.assert_called_once_with(tasks)
    
    def test_execute_no_files_found(self, stats_command):
        """Test stats execution when no files are found."""
        stats_command.file_service.resolve_file_paths.return_value = []
        
        stats_command.execute()
        
        stats_command.formatter.display_warning.assert_called_once_with(
            "No task files found."
        )
    
    def test_execute_no_tasks_found(self, stats_command):
        """Test stats execution when no tasks are found."""
        stats_command.file_service.resolve_file_paths.return_value = ["/test.xit"]
        stats_command.task_service.load_tasks.return_value = []
        
        stats_command.execute()
        
        stats_command.formatter.display_warning.assert_called_once_with(
            "No tasks found in the specified files."
        )
    
    def test_execute_with_path(self, stats_command):
        """Test stats execution with specific path."""
        tasks = [Task("Task", location=("/test.xit", 1), status="OPEN", priority=0, tags=[], due_date=None)]
        stats = {'total_tasks': 1, 'status_counts': {}, 'priority_counts': {}, 
                'files_with_tasks': set(), 'tasks_with_due_dates': 0, 'tasks_with_tags': 0}
        
        stats_command.file_service.resolve_file_paths.return_value = ["/test.xit"]
        stats_command.task_service.load_tasks.return_value = tasks
        stats_command.task_service.get_task_statistics.return_value = stats
        
        # Mock the console print calls
        stats_command.formatter.console = Mock()
        
        stats_command.execute(directory="/specific/path")
        
        # Should call _display_statistics with the path
        stats_command.formatter.console.print.assert_called()
    
    def test_execute_handles_xit_error(self, stats_command):
        """Test stats execution handles XitError properly."""
        stats_command.file_service.resolve_file_paths.side_effect = XitError("Test error")
        
        stats_command.execute()
        
        stats_command.formatter.display_error.assert_called_once_with("Test error")
    
    def test_execute_handles_unexpected_error(self, stats_command):
        """Test stats execution handles unexpected errors."""
        stats_command.file_service.resolve_file_paths.side_effect = ValueError("Unexpected")
        
        stats_command.execute()
        
        stats_command.formatter.display_error.assert_called_once_with(
            "Unexpected error: Unexpected"
        )


class TestAddTaskCommand:
    """Test AddTaskCommand functionality."""
    
    @pytest.fixture
    def add_command(self):
        """Create an AddTaskCommand instance with mocked dependencies."""
        formatter = Mock(spec=TaskFormatter)
        cmd = AddTaskCommand(formatter)
        
        # Mock the services
        cmd.task_service = Mock()
        cmd.file_service = Mock()
        
        return cmd
    
    def test_add_command_creation(self):
        """Test creating an AddTaskCommand."""
        cmd = AddTaskCommand()
        assert isinstance(cmd, AddTaskCommand)
        assert isinstance(cmd.formatter, TaskFormatter)
    
    def test_add_command_with_custom_formatter(self):
        """Test creating AddTaskCommand with custom formatter."""
        formatter = Mock(spec=TaskFormatter)
        cmd = AddTaskCommand(formatter)
        assert cmd.formatter is formatter
    
    def test_execute_add_task_success(self, add_command):
        """Test successfully adding a task."""
        # Setup - mock all the required dependencies
        mock_file_path = "/test/tasks.xit"
        mock_section = Mock()
        mock_section.title = "To Do"
        
        with patch.object(add_command, 'select_files', return_value=[mock_file_path]):
            with patch.object(add_command, 'select_section', return_value=[mock_section]):
                with patch('pathlib.Path.touch'):  # Mock file creation
                    with patch('xitkit.fileparser.FileParser.parse_file') as mock_parse:
                        # Mock file parsing
                        mock_file = Mock()
                        mock_file.sections = {"To Do": mock_section}
                        mock_parse.return_value = mock_file
                        
                        # Mock TaskService class constructor to return a mock instance
                        with patch('xitkit.commands.TaskService') as mock_task_service_class:
                            mock_task_service = Mock()
                            mock_task_service_class.return_value = mock_task_service
                            
                            # Execute
                            add_command.execute("New task description", "tasks.xit", directory=Path("/test"))
        
        # Verify the formatter was called with success message
        add_command.formatter.display_success.assert_called_once()
    
    def test_execute_add_task_absolute_path(self, add_command):
        """Test adding task with absolute file path."""
        from xitkit.fileparser import FileParser, File, Section
        
        # Mock file operations and dependencies
        add_command.select_files = Mock(return_value=["/absolute/path/tasks.xit"])
        
        # Mock section selection
        mock_section = Section("Default", 1)
        add_command.select_section = Mock(return_value=[mock_section])
        
        # Mock FileParser
        mock_file = File("/absolute/path/tasks.xit")
        mock_file.sections = {"Default": mock_section}
        
        with patch('xitkit.commands.FileParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser.parse_file.return_value = mock_file
            mock_parser_class.return_value = mock_parser
            
            with patch('xitkit.commands.TaskService') as mock_service_class:
                mock_service = Mock()
                mock_service_class.return_value = mock_service
                
                with patch('pathlib.Path.touch'):
                    # Execute with absolute path
                    add_command.execute("New task", "/absolute/path/tasks.xit")
        
        # Verify the formatter was called with success message
        add_command.formatter.display_success.assert_called_once()
    
    def test_execute_add_task_with_due_date(self, add_command):
        """Test adding a task with due date."""
        # Setup - mock all the required dependencies
        mock_file_path = "/test/tasks.xit"
        mock_section = Mock()
        mock_section.title = "To Do"
        
        with patch.object(add_command, 'select_files', return_value=[mock_file_path]):
            with patch.object(add_command, 'select_section', return_value=[mock_section]):
                with patch('pathlib.Path.touch'):  # Mock file creation
                    with patch('xitkit.fileparser.FileParser.parse_file') as mock_parse:
                        # Mock file parsing
                        mock_file = Mock()
                        mock_file.sections = {"To Do": mock_section}
                        mock_parse.return_value = mock_file
                        
                        # Mock TaskService class constructor to return a mock instance
                        with patch('xitkit.commands.TaskService') as mock_task_service_class:
                            mock_task_service = Mock()
                            mock_task_service_class.return_value = mock_task_service
                            
                            # Execute
                            add_command.execute("Task with date -> 2025-12-31", "tasks.xit", directory=Path("/test"))
        
        # Verify the formatter was called with success message
        add_command.formatter.display_success.assert_called_once()
    
    def test_execute_add_task_relative_path_no_directory(self, add_command):
        """Test adding task with relative path and no directory specified."""
        # Setup - mock all the required dependencies
        mock_file_path = "tasks.xit"
        mock_section = Mock()
        mock_section.title = "To Do"
        
        with patch('pathlib.Path.cwd', return_value=Path("/current/working/dir")):
            with patch.object(add_command, 'select_files', return_value=[mock_file_path]):
                with patch.object(add_command, 'select_section', return_value=[mock_section]):
                    with patch('pathlib.Path.touch'):  # Mock file creation
                        with patch('xitkit.fileparser.FileParser.parse_file') as mock_parse:
                            # Mock file parsing
                            mock_file = Mock()
                            mock_file.sections = {"To Do": mock_section}
                            mock_parse.return_value = mock_file
                            
                            # Mock TaskService class constructor to return a mock instance
                            with patch('xitkit.commands.TaskService') as mock_task_service_class:
                                mock_task_service = Mock()
                                mock_task_service_class.return_value = mock_task_service
                                
                                # Execute with relative path and no directory
                                add_command.execute("New task", "tasks.xit")
        
        # Verify the formatter was called with success message
        add_command.formatter.display_success.assert_called_once()
                
        # Verify the formatter was called with success message
        add_command.formatter.display_success.assert_called_once()
    
    def test_execute_add_task_error_handling(self, add_command):
        """Test error handling during task addition."""
        # Setup - mock select_files and select_section
        mock_file_path = "/test/tasks.xit"
        mock_section = Mock()
        mock_section.title = "Test Section"
        
        with patch.object(add_command, 'select_files', return_value=[mock_file_path]):
            with patch.object(add_command, 'select_section', return_value=[mock_section]):
                with patch('pathlib.Path.touch'):  # Mock file creation
                    with patch('xitkit.fileparser.FileParser.parse_file') as mock_parse:
                        # Mock file parsing
                        mock_file = Mock()
                        mock_file.sections = {"Test Section": mock_section}
                        mock_parse.return_value = mock_file
                        
                        # Mock TaskService.add_task_to_section to raise an error
                        with patch('xitkit.services.TaskService.add_task_to_section', 
                                 side_effect=XitError("Test error")):
                            # Execute
                            add_command.execute("New task", "tasks.xit", directory=Path("/test"))
        
        # Verify
        add_command.formatter.display_error.assert_called_once_with("Test error")


class TestMarkTaskCommand:
    """Test MarkTaskCommand functionality."""
    
    @pytest.fixture
    def mark_command(self):
        """Create a MarkTaskCommand instance with mocked dependencies."""
        formatter = Mock(spec=TaskFormatter)
        cmd = MarkTaskCommand(formatter)
        
        # Mock the services
        cmd.task_service = Mock()
        cmd.file_service = Mock()
        
        return cmd
    
    def test_mark_command_creation(self):
        """Test creating a MarkTaskCommand."""
        cmd = MarkTaskCommand()
        assert isinstance(cmd, MarkTaskCommand)
        assert isinstance(cmd.formatter, TaskFormatter)
    
    def test_mark_command_with_custom_formatter(self):
        """Test creating MarkTaskCommand with custom formatter."""
        formatter = Mock(spec=TaskFormatter)
        cmd = MarkTaskCommand(formatter)
        assert cmd.formatter is formatter
    
    def test_execute_mark_task_success(self, mark_command):
        """Test successfully marking a task."""
        from xitkit.task import Task
        from xitkit.location import Location
        
        # Setup - mock find_tasks to return a test task
        test_task = Task("Test task", location=Location("/test/tasks.xit", 1), status="OPEN", priority=0, tags=[], due_date=None)
        test_task.id = 1
        mark_command.find_tasks = Mock(return_value=[test_task])
        
        # Create mock updated task
        updated_task = Task("Test task", location=Location("/test/tasks.xit", 1), status="DONE", priority=0, tags=[], due_date=None)
        updated_task.id = 1
        mark_command.task_service.update_task.return_value = updated_task
        
        # Execute  
        mark_command.execute([1], "DONE", directory=Path("/test"))
        
        # Verify
        mark_command.find_tasks.assert_called_once_with(
            Path("/test"), None, [1], interactive=False
        )
        mark_command.task_service.update_task.assert_called_once()
        mark_command.formatter.display_success.assert_called()
    
    def test_execute_mark_task_no_files(self, mark_command):
        """Test marking task when no files found."""
        # Setup - mock select_files to return empty list
        with patch.object(mark_command, 'select_files', return_value=[]):
            # Execute
            mark_command.execute(1, "x", directory=Path("/test"))
        
        # Verify error is displayed
        mark_command.formatter.display_error.assert_called_once_with("No files selected.")
        
        # Verify that task service was not called
        mark_command.task_service.update_task_by_id.assert_not_called()
    
    def test_execute_mark_task_not_found(self, mark_command):
        """Test marking a task that doesn't exist."""
        # Setup - create a mock task
        test_file = Path("/test/tasks.xit")
        mock_task = Mock()
        mock_task.id = 999
        
        # Mock find_tasks to return the mock task
        with patch.object(mark_command, 'find_tasks', return_value=[mock_task]):
            # Mock select_status to return a status object
            mock_status = Mock()
            mock_status.name = "DONE"
            with patch.object(mark_command, 'select_status', return_value=mock_status):
                # Mock update_task to return None (task not found)
                mark_command.task_service.update_task.return_value = None
                
                # Execute
                mark_command.execute([999], "DONE", directory=Path("/test"))
        
        # Verify
        mark_command.formatter.display_error.assert_called_once_with(
            "Task #999 not found."
        )
    
    def test_execute_mark_task_different_statuses(self, mark_command):
        """Test marking tasks with different status symbols."""
        # Setup
        mock_task = Mock()
        mock_task.id = 1
        mock_task.description = Mock()
        mock_task.description.text = "Test task"
        mock_task.location = Mock()
        mock_task.location.file_path = "/test/tasks.xit"
        
        updated_task = Mock()
        updated_task.id = 1
        updated_task.description = Mock()
        updated_task.description.text = "Test task"
        updated_task.location = Mock()
        updated_task.location.file_path = "/test/tasks.xit"
        
        # Test different status symbols  
        statuses = ["DONE", "ONGOING", "OBSOLETE", "INQUESTION", "OPEN"]
        
        with patch.object(mark_command, 'find_tasks', return_value=[mock_task]):
            with patch.object(mark_command, 'select_status') as mock_select_status:
                mark_command.task_service.update_task.return_value = updated_task
                
                for status in statuses:
                    # Mock select_status to return different status objects
                    mock_status = Mock()
                    mock_status.name = status
                    mock_select_status.return_value = mock_status
                    
                    mark_command.execute([1], status, directory=Path("/test"))
                    
        # Verify update_task was called for each status
        assert mark_command.task_service.update_task.call_count == len(statuses)
    
    def test_execute_mark_task_with_specified_files(self, mark_command):
        """Test marking task in specified files."""
        # Setup
        specified_files = ["tasks.xit", "projects.md"]
        test_files = [Path("/test/tasks.xit"), Path("/test/projects.md")]
        
        mock_task = Mock()
        mock_task.id = 1
        mock_task.description = Mock()
        mock_task.description.text = "Test task" 
        mock_task.location = Mock()
        mock_task.location.file_path = "/test/tasks.xit"
        
        updated_task = Mock()
        updated_task.id = 1
        updated_task.description = Mock()
        updated_task.description.text = "Test task"
        updated_task.location = Mock() 
        updated_task.location.file_path = "/test/tasks.xit"
        
        # Mock find_tasks and select_status to simulate the flow
        with patch.object(mark_command, 'find_tasks', return_value=[mock_task]) as mock_find_tasks:
            mock_status = Mock()
            mock_status.name = "DONE"
            with patch.object(mark_command, 'select_status', return_value=mock_status):
                mark_command.task_service.update_task.return_value = updated_task
                
                # Execute
                mark_command.execute([1], "DONE", specified_files=specified_files)
        
        # Verify find_tasks was called with the specified files
        mock_find_tasks.assert_called_once_with(None, specified_files, [1], interactive=False)
    
    def test_execute_mark_task_error_handling(self, mark_command):
        """Test error handling during task marking."""
        # Setup - mock find_tasks to raise an error
        with patch.object(mark_command, 'find_tasks', side_effect=XitError("Test error")):
            # Execute
            mark_command.execute([1], "x", directory=Path("/test"))
        
        # Verify
        mark_command.formatter.display_error.assert_called_once_with("Test error")
    
    def test_get_relative_path(self, mark_command):
        """Test the _get_relative_path helper method."""
        with patch('pathlib.Path.cwd', return_value=Path("/current")):
            # Test relative path
            result = mark_command._get_relative_path("/current/subdir/file.xit")
            assert result == "subdir/file.xit"
            
            # Test absolute path that can't be made relative
            result = mark_command._get_relative_path("/other/path/file.xit")
            assert result == "/other/path/file.xit"


class TestRescheduleTaskCommand:
    """Test RescheduleTaskCommand functionality."""
    
    @pytest.fixture
    def reschedule_command(self):
        """Create a RescheduleTaskCommand instance with mocked dependencies."""
        formatter = Mock(spec=TaskFormatter)
        cmd = RescheduleTaskCommand(formatter)
        
        # Mock the services
        cmd.task_service = Mock()
        cmd.file_service = Mock()
        
        return cmd
    
    def test_reschedule_command_creation(self):
        """Test creating a RescheduleTaskCommand."""
        cmd = RescheduleTaskCommand()
        assert isinstance(cmd, RescheduleTaskCommand)
        assert isinstance(cmd.formatter, TaskFormatter)
    
    @patch('xitkit.duedate.DueDate.from_string')
    def test_execute_reschedule_task_success(self, mock_from_string, reschedule_command):
        """Test successfully rescheduling a task."""
        # Setup
        mock_task = Mock()
        mock_task.id = 1
        
        mock_due_date = Mock()
        mock_from_string.return_value = mock_due_date
        
        # Mock updated task
        updated_task = Mock()
        updated_task.id = 1
        updated_task.description = "Test task"
        updated_task.location = Mock()
        updated_task.location.file_path = "/test/tasks.xit"
        
        # Mock find_tasks and task service
        with patch.object(reschedule_command, 'find_tasks', return_value=[mock_task]):
            reschedule_command.task_service.update_task.return_value = updated_task
            
            # Execute
            reschedule_command.execute([1], "2025-12-31", directory=Path("/test"))
        
        # Verify
        mock_from_string.assert_called_once_with("2025-12-31")
        # Verify update_task was called with new_due_date parameter
        reschedule_command.task_service.update_task.assert_called_once_with(mock_task, new_due_date=mock_due_date)
        reschedule_command.formatter.display_success.assert_called_once()
    
    @patch('xitkit.duedate.DueDate.from_string')
    def test_execute_reschedule_natural_language_dates(self, mock_from_string, reschedule_command):
        """Test rescheduling with natural language dates."""
        # Setup
        mock_task = Mock()
        mock_task.id = 1
        
        mock_due_date = Mock()
        mock_from_string.return_value = mock_due_date
        
        updated_task = Mock()
        updated_task.id = 1
        updated_task.description = "Test task"
        updated_task.location = Mock()
        updated_task.location.file_path = "/test/tasks.xit"
        
        # Test different natural language expressions
        expressions = ["tomorrow", "today", "+1w", "1d-"]
        
        with patch.object(reschedule_command, 'find_tasks', return_value=[mock_task]):
            reschedule_command.task_service.update_task.return_value = updated_task
            
            for expr in expressions:
                reschedule_command.execute([1], expr, directory=Path("/test"))
                
        # Verify DueDate.from_string was called for each expression
        assert mock_from_string.call_count == len(expressions)
        # Verify each expression was passed correctly
        for i, expr in enumerate(expressions):
            assert mock_from_string.call_args_list[i] == ((expr,),)
    
    @patch('xitkit.duedate.DueDate.from_string')
    def test_execute_reschedule_invalid_date(self, mock_from_string, reschedule_command):
        """Test rescheduling with invalid date format."""
        # Setup
        mock_task = Mock()
        mock_task.id = 1
        
        # Mock DueDate.from_string to raise an exception for invalid date
        mock_from_string.side_effect = Exception("Invalid date format")
        
        # Mock find_tasks to return a task
        with patch.object(reschedule_command, 'find_tasks', return_value=[mock_task]):
            # Execute
            reschedule_command.execute([1], "invalid-date", directory=Path("/test"))
        
        # Verify error handling - should show "Unexpected error:" for general exceptions
        reschedule_command.formatter.display_error.assert_called_once_with(
            "Unexpected error: Invalid date format"
        )
        reschedule_command.task_service.update_task_by_id.assert_not_called()
    
    def test_execute_reschedule_task_not_found(self, reschedule_command):
        """Test rescheduling a task that doesn't exist."""
        # Setup - create a mock task
        mock_task = Mock()
        mock_task.id = 999
        
        mock_due_date = Mock()
        
        # Mock find_tasks to return the mock task
        with patch.object(reschedule_command, 'find_tasks', return_value=[mock_task]):
            with patch('xitkit.duedate.DueDate.from_string', return_value=mock_due_date):
                # Mock update_task to return None (task not found)
                reschedule_command.task_service.update_task.return_value = None
                
                # Execute
                reschedule_command.execute([999], "2025-12-31", directory=Path("/test"))
            
        # Verify
        reschedule_command.formatter.display_error.assert_called_once_with(
            "Task #999 not found."
        )

    def test_execute_reschedule_no_files(self, reschedule_command):
        """Test rescheduling when no files found."""
        # Setup - mock select_files to return empty list
        with patch.object(reschedule_command, 'select_files', return_value=[]):
            # Execute and verify error is displayed
            reschedule_command.execute([1], "tomorrow", directory=Path("/test"))
        
        # Verify error is displayed
        reschedule_command.formatter.display_error.assert_called_once_with("No files selected.")


class TestRemoveTaskCommand:
    """Test RemoveTaskCommand functionality."""
    
    @pytest.fixture
    def remove_command(self):
        """Create a RemoveTaskCommand instance with mocked dependencies."""
        formatter = Mock(spec=TaskFormatter)
        cmd = RemoveTaskCommand(formatter)
        
        # Mock the services
        cmd.task_service = Mock()
        cmd.file_service = Mock()
        
        return cmd
    
    def test_remove_command_creation(self):
        """Test creating a RemoveTaskCommand."""
        cmd = RemoveTaskCommand()
        assert isinstance(cmd, RemoveTaskCommand)
        assert isinstance(cmd.formatter, TaskFormatter)
    
    def test_remove_command_with_custom_formatter(self):
        """Test creating RemoveTaskCommand with custom formatter."""
        formatter = Mock(spec=TaskFormatter)
        cmd = RemoveTaskCommand(formatter)
        assert cmd.formatter is formatter
    
    @patch('click.confirm')
    def test_execute_remove_task_success_delete(self, mock_confirm, remove_command):
        """Test successfully removing a task with confirmation (delete)."""
        # Setup
        test_file = Path("/test/tasks.xit")
        remove_command.file_service.resolve_file_paths.return_value = [test_file]
        
        # Mock task loading
        target_task = Mock()
        target_task.id = 1
        target_task.description = "Task to remove"
        target_task.file = "/test/tasks.xit"
        target_task.status = "open"
        target_task.priority = None
        target_task.due_date = None
        remove_command.task_service.load_tasks.return_value = [target_task]
        
        # Mock confirmation as Yes (delete)
        mock_confirm.return_value = True
        
        # Mock removal
        removed_task = Mock()
        removed_task.description = "Task to remove"
        removed_task.file = "/test/tasks.xit"
        remove_command.task_service.remove_task_by_id.return_value = removed_task
        
        # Execute
        remove_command.execute([1], directory=Path("/test"))
        
        # Verify
        remove_command.file_service.resolve_file_paths.assert_called_once_with(
            Path("/test"), None
        )
        # Should load tasks twice - once for collection, once for processing
        assert remove_command.task_service.load_tasks.call_count >= 1
        mock_confirm.assert_called_once()
        remove_command.task_service.remove_task_by_id.assert_called_once_with(1, [test_file])
        remove_command.formatter.display_success.assert_called()
    
    @patch('click.confirm')
    def test_execute_remove_task_success_obsolete(self, mock_confirm, remove_command):
        """Test successfully marking a task as obsolete with confirmation (no delete)."""
        # Setup
        test_file = Path("/test/tasks.xit")
        remove_command.file_service.resolve_file_paths.return_value = [test_file]
        
        # Mock task loading
        target_task = Mock()
        target_task.id = 1
        target_task.description = "Task to mark obsolete"
        target_task.file = "/test/tasks.xit"
        target_task.status = "open"
        target_task.priority = None
        target_task.due_date = None
        remove_command.task_service.load_tasks.return_value = [target_task]
        
        # Mock confirmation as No (mark obsolete)
        mock_confirm.return_value = False
        
        # Mock marking as obsolete
        updated_task = Mock()
        updated_task.description = "Task to mark obsolete"
        updated_task.file = "/test/tasks.xit"
        remove_command.task_service.mark_task_by_id.return_value = updated_task
        
        # Execute
        remove_command.execute([1], directory=Path("/test"))
        
        # Verify
        remove_command.file_service.resolve_file_paths.assert_called_once_with(
            Path("/test"), None
        )
        # Should load tasks at least once for collection
        assert remove_command.task_service.load_tasks.call_count >= 1
        mock_confirm.assert_called_once()
        remove_command.task_service.mark_task_by_id.assert_called_once_with(1, "OBSOLETE", [test_file])
        remove_command.formatter.display_success.assert_called()
    
    def test_execute_remove_task_no_files(self, remove_command):
        """Test removing task when no files found."""
        # Setup
        remove_command.file_service.resolve_file_paths.return_value = []
        
        # Execute
        remove_command.execute([1], directory=Path("/test"))
        
        # Verify
        remove_command.formatter.display_warning.assert_called_once_with(
            "No task files found."
        )
        remove_command.task_service.remove_task_by_id.assert_not_called()
    
    def test_execute_remove_task_not_found(self, remove_command):
        """Test removing a task that doesn't exist."""
        # Setup
        test_file = Path("/test/tasks.xit")
        remove_command.file_service.resolve_file_paths.return_value = [test_file]
        
        # Mock task loading - return empty list (no tasks found)
        remove_command.task_service.load_tasks.return_value = []
        
        # Execute
        remove_command.execute([999], directory=Path("/test"))
        
        # Verify
        remove_command.formatter.display_error.assert_called_once_with(
            "Task #999 not found."
        )
    
    @patch('click.confirm')
    def test_execute_remove_task_with_specified_files(self, mock_confirm, remove_command):
        """Test removing task from specified files."""
        # Setup
        specified_files = ["tasks.xit", "projects.md"]
        test_files = [Path("/test/tasks.xit"), Path("/test/projects.md")]
        remove_command.file_service.resolve_file_paths.return_value = test_files
        
        # Mock task loading
        target_task = Mock()
        target_task.id = 1
        target_task.description = "Test task"
        target_task.file = "/test/tasks.xit"
        remove_command.task_service.load_tasks.return_value = [target_task]
        
        # Mock confirmation as Yes (delete)
        mock_confirm.return_value = True
        
        removed_task = Mock()
        removed_task.description = "Test task"
        removed_task.file = "/test/tasks.xit"
        remove_command.task_service.remove_task_by_id.return_value = removed_task
        
        # Execute
        remove_command.execute([1], specified_files=specified_files)
        
        # Verify
        remove_command.file_service.resolve_file_paths.assert_called_once_with(
            None, specified_files
        )
    
    def test_execute_remove_task_error_handling(self, remove_command):
        """Test error handling during task removal."""
        # Setup
        remove_command.file_service.resolve_file_paths.side_effect = XitError("Test error")
        
        # Execute
        remove_command.execute([1], directory=Path("/test"))
        
        # Verify
        remove_command.formatter.display_error.assert_called_once_with("Test error")
    
    def test_get_relative_path(self, remove_command):
        """Test the _get_relative_path helper method."""
        with patch('pathlib.Path.cwd', return_value=Path("/current")):
            # Test relative path
            result = remove_command._get_relative_path("/current/subdir/file.xit")
            assert result == "subdir/file.xit"
            
            # Test absolute path that can't be made relative
            result = remove_command._get_relative_path("/other/path/file.xit")
            assert result == "/other/path/file.xit"


class TestMoveTaskCommand:
    """Test MoveTaskCommand functionality."""
    
    @pytest.fixture
    def move_command(self):
        """Create a MoveTaskCommand instance with mocked dependencies."""
        formatter = Mock(spec=TaskFormatter)
        cmd = MoveTaskCommand(formatter)
        
        # Mock the services
        cmd.task_service = Mock()
        cmd.file_service = Mock()
        
        return cmd
    
    def test_move_command_creation(self):
        """Test creating a MoveTaskCommand."""
        cmd = MoveTaskCommand()
        assert isinstance(cmd, MoveTaskCommand)
        assert isinstance(cmd.formatter, TaskFormatter)
    
    def test_move_command_with_custom_formatter(self):
        """Test creating MoveTaskCommand with custom formatter."""
        formatter = Mock(spec=TaskFormatter)
        cmd = MoveTaskCommand(formatter)
        assert cmd.formatter is formatter
    
    def test_execute_move_task_success(self, move_command):
        """Test successfully moving a task."""
        # Setup
        test_file = Path("/test/tasks.xit")
        move_command.file_service.resolve_file_paths.return_value = [test_file]
        
        # Mock task loading for batch processing
        source_task = Mock()
        source_task.id = 1
        source_task.description = "Task to move"
        source_task.file = "/test/tasks.xit"
        source_task.status = "open"
        source_task.priority = None
        source_task.due_date = None
        move_command.task_service.load_tasks.return_value = [source_task]
        
        # Create mock moved task
        moved_task = Mock()
        moved_task.description = "Task to move"
        moved_task.file = "/test/target.xit"
        move_command.task_service.move_task_by_id.return_value = moved_task
        
        # Execute
        move_command.execute([1], "target.xit", directory=Path("/test"))
        
        # Verify
        move_command.file_service.resolve_file_paths.assert_called_once_with(
            Path("/test"), None
        )
        # With new batch processing, load_tasks is called twice (collection + processing)
        assert move_command.task_service.load_tasks.call_count == 2
        move_command.task_service.move_task_by_id.assert_called_once_with(
            1, [test_file], "/test/target.xit"
        )
        move_command.formatter.display_success.assert_called_once()
    
    def test_execute_move_task_absolute_target(self, move_command):
        """Test moving task with absolute target path."""
        # Setup
        test_file = Path("/test/tasks.xit")
        move_command.file_service.resolve_file_paths.return_value = [test_file]
        
        # Mock task loading for batch processing  
        source_task = Mock()
        source_task.id = 1
        source_task.description = "Task to move"
        source_task.file = "/test/tasks.xit"
        source_task.status = "open"
        source_task.priority = None
        source_task.due_date = None
        move_command.task_service.load_tasks.return_value = [source_task]
        
        moved_task = Mock()
        moved_task.description = "Task to move"
        moved_task.file = "/absolute/target.xit"
        move_command.task_service.move_task_by_id.return_value = moved_task
        
        # Execute with absolute target path
        move_command.execute([1], "/absolute/target.xit", directory=Path("/test"))
        
        # Verify
        move_command.task_service.move_task_by_id.assert_called_once_with(
            1, [test_file], "/absolute/target.xit"
        )
        move_command.formatter.display_success.assert_called_once()
    
    def test_execute_move_task_no_files(self, move_command):
        """Test moving task when no files found."""
        # Setup
        move_command.file_service.resolve_file_paths.return_value = []
        
        # Execute
        move_command.execute([1], "target.xit", directory=Path("/test"))
        
        # Verify
        move_command.formatter.display_warning.assert_called_once_with(
            "No task files found."
        )
        move_command.task_service.move_task_by_id.assert_not_called()
    
    def test_execute_move_task_not_found(self, move_command):
        """Test moving a task that doesn't exist."""
        # Setup
        test_file = Path("/test/tasks.xit")
        move_command.file_service.resolve_file_paths.return_value = [test_file]
        move_command.task_service.load_tasks.return_value = []  # No tasks found
        
        # Execute
        move_command.execute([999], "target.xit", directory=Path("/test"))
        
        # Verify
        move_command.formatter.display_error.assert_called_once_with(
            "Task #999 not found."
        )
    
    def test_execute_move_task_with_specified_files(self, move_command):
        """Test moving task from specified files."""
        # Setup
        specified_files = ["tasks.xit", "projects.md"]
        test_files = [Path("/test/tasks.xit"), Path("/test/projects.md")]
        move_command.file_service.resolve_file_paths.return_value = test_files
        
        moved_task = Mock()
        moved_task.description = "Test task"
        moved_task.file = "/test/target.xit"
        move_command.task_service.move_task_by_id.return_value = moved_task
        
        # Execute
        move_command.execute([1], "target.xit", specified_files=specified_files)
        
        # Verify
        move_command.file_service.resolve_file_paths.assert_called_once_with(
            None, specified_files
        )
    
    def test_execute_move_task_error_handling(self, move_command):
        """Test error handling during task moving."""
        # Setup
        move_command.file_service.resolve_file_paths.side_effect = XitError("Test error")
        
        # Execute
        move_command.execute([1], "target.xit", directory=Path("/test"))
        
        # Verify
        move_command.formatter.display_error.assert_called_once_with("Test error")
    
    def test_get_relative_path(self, move_command):
        """Test the _get_relative_path helper method."""
        with patch('pathlib.Path.cwd', return_value=Path("/current")):
            # Test relative path
            result = move_command._get_relative_path("/current/subdir/file.xit")
            assert result == "subdir/file.xit"
            
            # Test absolute path that can't be made relative
            result = move_command._get_relative_path("/other/path/file.xit")
            assert result == "/other/path/file.xit"


class TestStatisticsDisplay:
    """Test statistics display functionality."""
    
    @pytest.fixture
    def stats_command_with_console(self):
        """Create stats command with real console for display testing."""
        cmd = ShowStatsCommand()
        cmd.formatter.console = Mock()
        return cmd
    
    def test_display_statistics_without_path(self, stats_command_with_console):
        """Test displaying statistics without specific path."""
        stats = {
            'total': 5,
            'by_status': {'OPEN': 2, 'DONE': 2, 'ONGOING': 1},
            'by_priority': {0: 3, 1: 1, 2: 1},
            'by_file': {"/file1.xit": 3, "/file2.xit": 2},
            'with_due_date': 2,
            'with_tags': 3,
            'overdue': 1
        }
        
        stats_command_with_console._display_statistics(stats)
        
        # Check that console.print was called multiple times
        assert stats_command_with_console.formatter.console.print.call_count > 5
        
        # Check some specific content was printed
        calls = stats_command_with_console.formatter.console.print.call_args_list
        call_texts = [str(call) for call in calls]
        
        # Should contain the basic statistics
        assert any("Total tasks: 5" in text for text in call_texts)
        assert any("Files with tasks: 2" in text for text in call_texts)
        assert any("Tasks with due dates: 2" in text for text in call_texts)
        assert any("Tasks with tags: 3" in text for text in call_texts)
    
    def test_display_statistics_with_path(self, stats_command_with_console):
        """Test displaying statistics with specific path."""
        stats = {
            'total': 1,
            'by_status': {'OPEN': 1},
            'by_priority': {0: 1},
            'by_file': {"/test.xit": 1},
            'with_due_date': 0,
            'with_tags': 0,
            'overdue': 0
        }
        
        stats_command_with_console._display_statistics(stats, "/test/path")
        
        calls = stats_command_with_console.formatter.console.print.call_args_list
        call_texts = [str(call) for call in calls]
        
        # Should include the path in the header
        assert any("/test/path" in text for text in call_texts)
    
    def test_display_statistics_status_breakdown(self, stats_command_with_console):
        """Test status breakdown in statistics display."""
        stats = {
            'total': 5,
            'by_status': {
                'OPEN': 2,
                'CHECKED': 1,
                'ONGOING': 1,
                'OBSOLETE': 1,
                'IN_QUESTION': 0  # Zero count should not be displayed
            },
            'by_priority': {},
            'by_file': {},
            'with_due_date': 0,
            'with_tags': 0,
            'overdue': 0
        }
        
        stats_command_with_console._display_statistics(stats)
        
        calls = stats_command_with_console.formatter.console.print.call_args_list
        call_texts = [str(call) for call in calls]
        
        # Should show non-zero status counts (using display names from status_display mapping)
        assert any("Open: 2" in text for text in call_texts)
        assert any("Done: 1" in text for text in call_texts)
        assert any("Ongoing: 1" in text for text in call_texts)
        assert any("Obsolete: 1" in text for text in call_texts)
        # Should not show zero counts
        assert not any("In Question: 0" in text for text in call_texts)
    
    def test_display_statistics_priority_breakdown(self, stats_command_with_console):
        """Test priority breakdown in statistics display."""
        stats = {
            'total': 4,
            'by_status': {},
            'by_priority': {0: 2, 1: 1, 3: 1},
            'by_file': {},
            'with_due_date': 0,
            'with_tags': 0,
            'overdue': 0
        }
        
        stats_command_with_console._display_statistics(stats)
        
        calls = stats_command_with_console.formatter.console.print.call_args_list
        call_texts = [str(call) for call in calls]
        
        # Should show priority breakdown
        assert any("No priority: 2" in text for text in call_texts)
        assert any("Priority !: 1" in text for text in call_texts)
        assert any("Priority !!!: 1" in text for text in call_texts)


class TestCommandFactory:
    """Test CommandFactory functionality."""
    
    def test_create_show_command_default(self):
        """Test creating show command with default formatter."""
        cmd = CommandFactory.create_show_command()
        
        assert isinstance(cmd, ShowTasksCommand)
        assert isinstance(cmd.formatter, TaskFormatter)
    
    def test_create_show_command_with_formatter(self):
        """Test creating show command with custom formatter."""
        custom_formatter = Mock(spec=TaskFormatter)
        cmd = CommandFactory.create_show_command(custom_formatter)
        
        assert isinstance(cmd, ShowTasksCommand)
        assert cmd.formatter is custom_formatter
    
    def test_create_stats_command_default(self):
        """Test creating stats command with default formatter."""
        cmd = CommandFactory.create_stats_command()
        
        assert isinstance(cmd, ShowStatsCommand)
        assert isinstance(cmd.formatter, TaskFormatter)
    
    def test_create_stats_command_with_formatter(self):
        """Test creating stats command with custom formatter."""
        custom_formatter = Mock(spec=TaskFormatter)
        cmd = CommandFactory.create_stats_command(custom_formatter)
        
        assert isinstance(cmd, ShowStatsCommand)
        assert cmd.formatter is custom_formatter
    
    def test_create_add_command_default(self):
        """Test creating add command with default formatter."""
        cmd = CommandFactory.create_add_command()
        
        assert isinstance(cmd, AddTaskCommand)
        assert isinstance(cmd.formatter, TaskFormatter)
    
    def test_create_add_command_with_formatter(self):
        """Test creating add command with custom formatter."""
        custom_formatter = Mock(spec=TaskFormatter)
        cmd = CommandFactory.create_add_command(custom_formatter)
        
        assert isinstance(cmd, AddTaskCommand)
        assert cmd.formatter is custom_formatter
    
    def test_create_mark_command_default(self):
        """Test creating mark command with default formatter."""
        cmd = CommandFactory.create_mark_command()
        
        assert isinstance(cmd, MarkTaskCommand)
        assert isinstance(cmd.formatter, TaskFormatter)
    
    def test_create_mark_command_with_formatter(self):
        """Test creating mark command with custom formatter."""
        custom_formatter = Mock(spec=TaskFormatter)
        cmd = CommandFactory.create_mark_command(custom_formatter)
        
        assert isinstance(cmd, MarkTaskCommand)
        assert cmd.formatter is custom_formatter
    
    def test_create_reschedule_command_default(self):
        """Test creating reschedule command with default formatter."""
        cmd = CommandFactory.create_reschedule_command()
        
        assert isinstance(cmd, RescheduleTaskCommand)
        assert isinstance(cmd.formatter, TaskFormatter)
    
    def test_create_reschedule_command_with_formatter(self):
        """Test creating reschedule command with custom formatter."""
        custom_formatter = Mock(spec=TaskFormatter)
        cmd = CommandFactory.create_reschedule_command(custom_formatter)
        
        assert isinstance(cmd, RescheduleTaskCommand)
        assert cmd.formatter is custom_formatter
    
    def test_create_remove_command_default(self):
        """Test creating remove command with default formatter."""
        cmd = CommandFactory.create_remove_command()
        
        assert isinstance(cmd, RemoveTaskCommand)
        assert isinstance(cmd.formatter, TaskFormatter)
    
    def test_create_remove_command_with_formatter(self):
        """Test creating remove command with custom formatter."""
        custom_formatter = Mock(spec=TaskFormatter)
        cmd = CommandFactory.create_remove_command(custom_formatter)
        
        assert isinstance(cmd, RemoveTaskCommand)
        assert cmd.formatter is custom_formatter
    
    def test_create_move_command_default(self):
        """Test creating move command with default formatter."""
        cmd = CommandFactory.create_move_command()
        
        assert isinstance(cmd, MoveTaskCommand)
        assert isinstance(cmd.formatter, TaskFormatter)
    
    def test_create_move_command_with_formatter(self):
        """Test creating move command with custom formatter."""
        custom_formatter = Mock(spec=TaskFormatter)
        cmd = CommandFactory.create_move_command(custom_formatter)
        
        assert isinstance(cmd, MoveTaskCommand)
        assert cmd.formatter is custom_formatter
    
    def test_create_recur_command_default(self):
        """Test creating recur command with default formatter."""
        cmd = CommandFactory.create_recur_command()
        
        assert isinstance(cmd, RecurTaskCommand)
        assert isinstance(cmd.formatter, TaskFormatter)
    
    def test_create_recur_command_with_formatter(self):
        """Test creating recur command with custom formatter."""
        custom_formatter = Mock(spec=TaskFormatter)
        cmd = CommandFactory.create_recur_command(custom_formatter)
        
        assert isinstance(cmd, RecurTaskCommand)
        assert cmd.formatter is custom_formatter


class TestCommandIntegration:
    """Test command integration with real components."""
    
    def test_show_command_real_integration(self, temp_dir):
        """Test ShowTasksCommand with real file system and components."""
        # Create test file
        content = """[ ] ! Open high priority task #work
[x] Completed task #personal
[@] Ongoing task #project -> 2025-12-31"""
        
        test_file = create_test_file(temp_dir, "test.xit", content)
        
        # Create command with real components
        cmd = ShowTasksCommand()
        
        # Mock only the display methods to avoid actual console output
        cmd.formatter.display_tasks = Mock()
        cmd.formatter.display_summary = Mock()
        cmd.formatter.display_warning = Mock()
        
        # Execute command
        cmd.execute(
            directory=temp_dir,
            specified_files=[str(test_file)],
            filters=None,
            show_location=False,
            count_only=False
        )
        
        # Verify that tasks were displayed
        cmd.formatter.display_tasks.assert_called_once()
        args, kwargs = cmd.formatter.display_tasks.call_args
        tasks = args[0]
        
        assert len(tasks) == 3
        assert str(tasks[0].description) == "! Open high priority task #work"
        assert tasks[0].priority.level == 1
        assert tasks[1].status.status_type.name == "ONGOING"
        assert tasks[2].status.status_type.name == "CHECKED" # checked task is put last
        assert tasks[1].due_date_string == "2025-12-31"
    
    def test_stats_command_real_integration(self, temp_dir):
        """Test ShowStatsCommand with real file system and components."""
        # Create test files
        file1_content = """[ ] Open task #work
[x] ! Done task #work
[@] Ongoing task #project"""
        
        file2_content = """[~] Obsolete task
[?] Question task #help -> 2025-12-31"""
        
        file1 = create_test_file(temp_dir, "work.xit", file1_content)
        file2 = create_test_file(temp_dir, "personal.xit", file2_content)
        
        # Create command
        cmd = ShowStatsCommand()
        
        # Mock display method
        cmd._display_statistics = Mock()
        
        # Execute command
        cmd.execute(
            directory=Path(temp_dir),
            specified_files=None
        )
        
        # Verify statistics were calculated and displayed
        cmd._display_statistics.assert_called_once()
        stats, path_arg = cmd._display_statistics.call_args[0]
        
        assert stats['total'] == 5
        assert stats['by_status']['OPEN'] == 1
        assert stats['by_status']['CHECKED'] == 1
        assert stats['by_status']['ONGOING'] == 1
        assert stats['by_status']['OBSOLETE'] == 1
        assert stats['by_status']['IN_QUESTION'] == 1
        assert len(stats['by_file']) == 2
    
    def test_command_with_filters_integration(self, temp_dir):
        """Test command with filters using real components."""
        # Create test file
        content = """[ ] Open task #work
[x] Done task #work
[@] ! Ongoing important task #work #urgent
[~] Obsolete task #old
[ ] Another open task #personal"""
        
        test_file = create_test_file(temp_dir, "test.xit", content)
        
        # Create command
        cmd = ShowTasksCommand()
        cmd.formatter.display_tasks = Mock()
        cmd.formatter.display_summary = Mock()
        
        # Test filtering by status
        from xitkit.status import Status, StatusType
        filters = TaskFilter(status=[Status(StatusType.OPEN)])
        cmd.execute(
            specified_files=[str(test_file)],
            filters=filters
        )
        
        args, kwargs = cmd.formatter.display_tasks.call_args
        filtered_tasks = args[0]
        
        assert len(filtered_tasks) == 2  # Two OPEN tasks
        assert all(task.status.status_type == StatusType.OPEN for task in filtered_tasks)
        
        # Test filtering by tags
        cmd.formatter.display_tasks.reset_mock()
        from xitkit.tags import Tag
        filters = TaskFilter(tags=[Tag(name="work")])
        cmd.execute(
            specified_files=[str(test_file)],
            filters=filters
        )
        
        args, kwargs = cmd.formatter.display_tasks.call_args
        filtered_tasks = args[0]
        
        assert len(filtered_tasks) == 3  # Three tasks with #work tag
        assert all(task.has_tag_by_name("work") for task in filtered_tasks)


class TestCommandErrorScenarios:
    """Test command error handling scenarios."""
        
    def test_command_with_invalid_filter_date(self, temp_dir):
        """Test command with invalid date filter."""
        # Create test file
        content = "[ ] Task -> 2025-12-31"
        test_file = create_test_file(temp_dir, "test.xit", content)
        
        cmd = ShowTasksCommand()
        cmd.formatter.display_tasks = Mock()
        cmd.formatter.display_summary = Mock()
        
        # Use filter with date (should not crash even if date parsing fails)
        filters = TaskFilter(due_on="invalid-date")
        
        # Should complete without error (main test goal)
        try:
            cmd.execute(specified_files=[str(test_file)], filters=filters)
            # Command should complete successfully
            success = True
        except Exception:
            success = False
        
        assert success, "Command should not crash with invalid date filter"



class TestBatchProcessing:
    """Test batch processing functionality for commands that support multiple task IDs."""
    
    def test_mark_command_multiple_tasks_success(self):
        """Test marking multiple tasks successfully."""
        from xitkit.task import Task
        from xitkit.location import Location
        
        # Setup
        formatter = Mock(spec=TaskFormatter)
        mark_command = MarkTaskCommand(formatter)
        
        # Mock find_tasks to return test tasks
        task1 = Task("Task 1", location=Location("/test/tasks.xit", 1), status="OPEN", priority=0, tags=[], due_date=None)
        task1.id = 1
        task2 = Task("Task 2", location=Location("/test/tasks.xit", 2), status="OPEN", priority=0, tags=[], due_date=None)
        task2.id = 2
        
        mark_command.find_tasks = Mock(return_value=[task1, task2])
        
        # Mock update_task to return updated tasks
        updated_task1 = Task("Task 1", location=Location("/test/tasks.xit", 1), status="DONE", priority=0, tags=[], due_date=None)
        updated_task1.id = 1
        updated_task2 = Task("Task 2", location=Location("/test/tasks.xit", 2), status="DONE", priority=0, tags=[], due_date=None)
        updated_task2.id = 2
        
        mark_command.task_service = Mock()
        mark_command.task_service.update_task.side_effect = [updated_task1, updated_task2]
        
        # Execute batch operation
        mark_command.execute([1, 2], "DONE", directory=Path("/test"))
        
        # Verify both tasks were processed
        assert mark_command.task_service.update_task.call_count == 2
        
        # Verify success messages - expect 2 individual plus 1 summary when processing multiple tasks
        assert formatter.display_success.call_count == 3  # 2 individual + 1 summary

    def test_mark_command_mixed_results(self):
        """Test marking multiple tasks with some not found."""
        from xitkit.task import Task
        from xitkit.location import Location
        
        # Setup
        formatter = Mock(spec=TaskFormatter)
        mark_command = MarkTaskCommand(formatter)
        
        # Mock find_tasks to return only one task (first one found, second not found)
        task1 = Task("Task 1", location=Location("/test/tasks.xit", 1), status="OPEN", priority=0, tags=[], due_date=None)
        task1.id = 1
        
        mark_command.find_tasks = Mock(return_value=[task1])  # Only task 1 found
        
        # Mock update_task to return updated task
        updated_task1 = Task("Task 1", location=Location("/test/tasks.xit", 1), status="DONE", priority=0, tags=[], due_date=None)
        updated_task1.id = 1
        
        mark_command.task_service = Mock()
        mark_command.task_service.update_task.return_value = updated_task1
        
        # Execute batch operation (task 999 won't be found)
        mark_command.execute([1, 999], "DONE", directory=Path("/test"))
        
        # Verify only one task was processed (find_tasks filtered out task 999)
        assert mark_command.task_service.update_task.call_count == 1
        
        # Verify success message for found task
        assert formatter.display_success.call_count >= 1

    def test_reschedule_command_multiple_tasks(self):
        """Test rescheduling multiple tasks to same date."""
        from xitkit.task import Task
        from xitkit.location import Location
        
        # Setup
        formatter = Mock(spec=TaskFormatter)
        reschedule_command = RescheduleTaskCommand(formatter)
        
        # Mock find_tasks to return test tasks
        task1 = Task("Task 1", location=Location("/test/tasks.xit", 1), status="OPEN", priority=0, tags=[], due_date=None)
        task1.id = 1
        task2 = Task("Task 2", location=Location("/test/tasks.xit", 2), status="OPEN", priority=0, tags=[], due_date=None)
        task2.id = 2
        
        reschedule_command.find_tasks = Mock(return_value=[task1, task2])
        
        # Mock update_task to return updated tasks
        updated_task1 = Task("Task 1", location=Location("/test/tasks.xit", 1), status="OPEN", priority=0, tags=[], due_date="2025-12-31")
        updated_task1.id = 1
        updated_task2 = Task("Task 2", location=Location("/test/tasks.xit", 2), status="OPEN", priority=0, tags=[], due_date="2025-12-31")
        updated_task2.id = 2
        
        reschedule_command.task_service = Mock()
        reschedule_command.task_service.update_task.side_effect = [updated_task1, updated_task2]
        
        # Execute batch operation
        reschedule_command.execute([1, 2], "2025-12-31", directory=Path("/test"))
        
        # Verify both tasks were processed
        assert reschedule_command.task_service.update_task.call_count == 2

    @patch('click.confirm')
    def test_remove_command_mixed_confirmations(self, mock_confirm):
        """Test removing multiple tasks with different confirmation responses."""
        # Setup
        formatter = Mock(spec=TaskFormatter)
        file_service = Mock()
        task_service = Mock()
        remove_command = RemoveTaskCommand(formatter)
        remove_command.file_service = file_service
        remove_command.task_service = task_service
        
        test_file = Path("/test/tasks.xit")
        file_service.resolve_file_paths.return_value = [test_file]
        
        # Mock tasks for initial collection
        task1 = Mock()
        task1.id = 1
        task1.description = "Task 1"
        task1.file = "/test/tasks.xit"
        task1.status = "open"
        task1.priority = None
        task1.due_date = None
        
        task2 = Mock()
        task2.id = 2
        task2.description = "Task 2"
        task2.file = "/test/tasks.xit"
        task2.status = "open"
        task2.priority = None
        task2.due_date = None
        
        # Mock task loading for different phases
        task_service.load_tasks.side_effect = [
            [task1, task2],  # Initial collection
            [task1, task2],  # Processing task1
            [task2],         # Processing task2 (task1 removed)
        ]
        
        # Mock confirmation responses (yes for task1, no for task2)
        mock_confirm.side_effect = [True, False]
        
        # Mock operations
        removed_task = Mock()
        removed_task.description = "Task 1"
        removed_task.file = "/test/tasks.xit"
        task_service.remove_task_by_id.return_value = removed_task
        
        marked_task = Mock()
        marked_task.description = "Task 2"
        marked_task.file = "/test/tasks.xit"
        task_service.mark_task_by_id.return_value = marked_task
        
        # Execute batch operation
        remove_command.execute([1, 2], directory=Path("/test"))
        
        # Verify confirmations
        assert mock_confirm.call_count == 2
        
        # Verify operations
        task_service.remove_task_by_id.assert_called_once_with(1, [test_file])
        task_service.mark_task_by_id.assert_called_once_with(2, "OBSOLETE", [test_file])

    def test_move_command_multiple_tasks(self):
        """Test moving multiple tasks to same target file."""
        # Setup
        formatter = Mock(spec=TaskFormatter)
        file_service = Mock()
        task_service = Mock()
        move_command = MoveTaskCommand(formatter)
        move_command.file_service = file_service
        move_command.task_service = task_service
        
        test_file = Path("/test/tasks.xit")
        file_service.resolve_file_paths.return_value = [test_file]
        
        # Mock tasks for initial collection
        task1 = Mock()
        task1.id = 1
        task1.description = "Task 1"
        task1.file = "/test/tasks.xit"
        task1.status = "open"
        task1.priority = None
        task1.due_date = None
        
        task2 = Mock()
        task2.id = 2
        task2.description = "Task 2"
        task2.file = "/test/tasks.xit"
        task2.status = "open" 
        task2.priority = None
        task2.due_date = None
        
        # Mock task loading for different phases
        task_service.load_tasks.side_effect = [
            [task1, task2],  # Initial collection
            [task1, task2],  # Processing task1
            [task2],         # Processing task2 (task1 moved)
        ]
        
        # Mock move operations
        moved_task1 = Mock()
        moved_task1.description = "Task 1"
        moved_task1.file = "/test/target.xit"
        
        moved_task2 = Mock()
        moved_task2.description = "Task 2"
        moved_task2.file = "/test/target.xit"
        
        task_service.move_task_by_id.side_effect = [moved_task1, moved_task2]
        
        # Execute batch operation
        move_command.execute([1, 2], "target.xit", directory=Path("/test"))
        
        # Verify both tasks were processed
        assert task_service.move_task_by_id.call_count == 2
        task_service.move_task_by_id.assert_any_call(1, [test_file], "/test/target.xit")
        task_service.move_task_by_id.assert_any_call(2, [test_file], "/test/target.xit")

    def test_batch_processing_preserves_order(self):
        """Test that batch operations preserve user-specified order."""
        from xitkit.task import Task
        from xitkit.location import Location
        
        # Setup
        formatter = Mock(spec=TaskFormatter)
        mark_command = MarkTaskCommand(formatter)
        
        # Track call order by creating tasks with IDs in the expected order
        call_order = []
        
        def create_task_with_id(task_id):
            task = Task(f"Task {task_id}", location=Location("/test/tasks.xit", task_id), status="OPEN", priority=0, tags=[], due_date=None)
            task.id = task_id
            return task
        
        # Create tasks in the order they should be processed
        tasks = [create_task_with_id(5), create_task_with_id(1), create_task_with_id(3), create_task_with_id(2)]
        mark_command.find_tasks = Mock(return_value=tasks)
        
        def track_calls(task, **kwargs):
            call_order.append(task.id)
            updated_task = Task(f"Task {task.id}", location=Location("/test/tasks.xit", task.id), status="DONE", priority=0, tags=[], due_date=None)
            updated_task.id = task.id
            return updated_task
        
        mark_command.task_service = Mock()
        mark_command.task_service.update_task.side_effect = track_calls
        
        # Execute with non-sequential order
        mark_command.execute([5, 1, 3, 2], "DONE", directory=Path("/test"))
        
        # Verify order was preserved
        assert call_order == [5, 1, 3, 2]

    def test_empty_task_list_handling(self):
        """Test handling when no task IDs provided."""
        # Setup
        formatter = Mock(spec=TaskFormatter)
        mark_command = MarkTaskCommand(formatter)
        
        # Mock find_tasks to raise XitError for empty task list
        mark_command.find_tasks = Mock(side_effect=Exception("'NoneType' object is not iterable"))
        
        # Execute with empty list
        mark_command.execute([], "DONE", directory=Path("/test"))
        
        # Verify error message is displayed (caught by execute wrapper)
        formatter.display_error.assert_called_once()
        formatter.display_success.assert_not_called()  # No success messages


class TestRecurTaskCommand:
    """Test the RecurTaskCommand functionality."""
    
    def test_recur_command_creation(self):
        """Test creating a RecurTaskCommand."""
        from xitkit.commands import RecurTaskCommand
        
        command = RecurTaskCommand()
        
        assert isinstance(command.formatter, TaskFormatter)
        assert hasattr(command, 'task_service')
        assert hasattr(command, 'file_service')
    
    def test_recur_command_with_custom_formatter(self):
        """Test RecurTaskCommand with custom formatter."""
        from xitkit.commands import RecurTaskCommand
        
        custom_formatter = TaskFormatter()
        command = RecurTaskCommand(custom_formatter)
        
        assert command.formatter is custom_formatter
    
    @patch('xitkit.commands.RecurTaskCommand._get_relative_path')
    def test_execute_recur_task_success(self, mock_relative_path):
        """Test successful task recurrence creation."""
        from xitkit.commands import RecurTaskCommand
        
        # Setup mocks
        mock_relative_path.return_value = "test.xit"
        mock_formatter = Mock()
        recur_command = RecurTaskCommand(mock_formatter)
        
        # Mock created tasks
        mock_task1 = Mock()
        mock_task1.due_date = "2025-10-27"
        mock_task2 = Mock()
        mock_task2.due_date = "2025-11-03"
        created_tasks = [mock_task1, mock_task2]
        
        recur_command.task_service = Mock()
        recur_command.task_service.recur_task_by_id.return_value = created_tasks
        
        # Execute command
        recur_command.execute(
            task_id=1,
            interval="1w",
            count=3,
            target_file="test.xit",
            directory=Path("/test"),
            specified_files=[]
        )
        
        # Verify service call
        recur_command.task_service.recur_task_by_id.assert_called_once_with(
            task_id=1,
            interval="1w",
            end_date=None,
            count=3,
            target_file="test.xit",
            directory=Path("/test"),
            specified_files=[]
        )
        
        # Verify success message
        mock_formatter.display_success.assert_called_once_with(
            "Created 2 recurring instance(s) of task #001"
        )
    
    def test_execute_recur_task_no_instances_created(self):
        """Test when no recurring instances are created."""
        from xitkit.commands import RecurTaskCommand
        
        mock_formatter = Mock()
        recur_command = RecurTaskCommand(mock_formatter)
        recur_command.task_service = Mock()
        recur_command.task_service.recur_task_by_id.return_value = []
        
        # Execute command
        recur_command.execute(
            task_id=1,
            interval="1w",
            count=1,
            directory=Path("/test"),
            specified_files=[]
        )
        
        # Verify warning message
        mock_formatter.display_warning.assert_called_once_with(
            "No recurring instances created for task #001"
        )
    
    def test_execute_recur_task_with_end_date(self):
        """Test recur command with end date instead of count."""
        from xitkit.commands import RecurTaskCommand
        
        mock_formatter = Mock()
        recur_command = RecurTaskCommand(mock_formatter)
        
        mock_task = Mock()
        mock_task.due_date = "2025-11-01"
        recur_command.task_service = Mock()
        recur_command.task_service.recur_task_by_id.return_value = [mock_task]
        
        # Execute command
        recur_command.execute(
            task_id=5,
            interval="1m",
            end_date="2025-12-31",
            directory=Path("/test"),
            specified_files=["test.xit"]
        )
        
        # Verify service call
        recur_command.task_service.recur_task_by_id.assert_called_once_with(
            task_id=5,
            interval="1m",
            end_date="2025-12-31",
            count=None,
            target_file=None,
            directory=Path("/test"),
            specified_files=["test.xit"]
        )
    
    def test_execute_recur_task_xit_error(self):
        """Test handling XitError during recurrence creation."""
        from xitkit.commands import RecurTaskCommand
        from xitkit.exceptions import XitError
        
        mock_formatter = Mock()
        recur_command = RecurTaskCommand(mock_formatter)
        recur_command.task_service = Mock()
        recur_command.task_service.recur_task_by_id.side_effect = XitError("Task not found")
        
        # Execute command
        recur_command.execute(
            task_id=999,
            interval="1w",
            count=2,
            directory=Path("/test"),
            specified_files=[]
        )
        
        # Verify error message
        mock_formatter.display_error.assert_called_once_with("Task not found")
    
    def test_execute_recur_task_unexpected_error(self):
        """Test handling unexpected errors during recurrence creation."""
        from xitkit.commands import RecurTaskCommand
        
        mock_formatter = Mock()
        recur_command = RecurTaskCommand(mock_formatter)
        recur_command.task_service = Mock()
        recur_command.task_service.recur_task_by_id.side_effect = Exception("Database error")
        
        # Execute command
        recur_command.execute(
            task_id=1,
            interval="1w",
            count=2,
            directory=Path("/test"),
            specified_files=[]
        )
        
        # Verify error message (caught by execute wrapper and displayed as unexpected error)
        mock_formatter.display_error.assert_called_once_with(
            "Unexpected error: Database error"
        )
    
    def test_get_relative_path(self):
        """Test _get_relative_path helper method."""
        from xitkit.commands import RecurTaskCommand
        
        command = RecurTaskCommand()
        
        # Test relative path within current directory
        with patch('pathlib.Path.cwd', return_value=Path("/home/user/project")):
            result = command._get_relative_path("/home/user/project/tasks.xit")
            assert result == "tasks.xit"
        
        # Test absolute path outside current directory
        with patch('pathlib.Path.cwd', return_value=Path("/home/user/project")):
            result = command._get_relative_path("/etc/config.txt")
            assert result == "/etc/config.txt"


class TestEditTaskCommand:
    """Test the EditTaskCommand functionality."""
    
    def test_edit_command_creation(self):
        """Test creating an EditTaskCommand."""
        from xitkit.commands import EditTaskCommand
        
        command = EditTaskCommand()
        
        assert isinstance(command.formatter, TaskFormatter)
        assert hasattr(command, 'task_service')
        assert hasattr(command, 'file_service')
    
    def test_edit_command_with_custom_formatter(self):
        """Test EditTaskCommand with custom formatter."""
        from xitkit.commands import EditTaskCommand
        
        custom_formatter = TaskFormatter()
        command = EditTaskCommand(custom_formatter)
        
        assert command.formatter is custom_formatter
    
    def test_execute_edit_task_success(self):
        """Test successful task description editing."""
        from xitkit.commands import EditTaskCommand
        
        mock_formatter = Mock()
        edit_command = EditTaskCommand(mock_formatter)
        edit_command.task_service = Mock()
        # Mock successful update returning a task object
        updated_task = Mock()
        updated_task.description.text = "Updated description"
        updated_task.file = "/test/file.xit"
        edit_command.task_service.update_task_description.return_value = updated_task
        edit_command.file_service = Mock()
        edit_command.file_service.resolve_file_paths.return_value = ["/test/file.xit"]
        
        # Execute command
        edit_command.execute(
            task_id=1,
            description="Updated description",
            directory=Path("/test"),
            specified_files=[]
        )
        
        # Verify service call
        edit_command.task_service.update_task_description.assert_called_once_with(
            task_id=1,
            new_description="Updated description",
            file_paths=["/test/file.xit"]
        )
        
        # Verify success message was called
        mock_formatter.display_success.assert_called_once()
    
    def test_execute_edit_task_not_found(self):
        """Test editing a task that doesn't exist."""
        from xitkit.commands import EditTaskCommand
        
        mock_formatter = Mock()
        edit_command = EditTaskCommand(mock_formatter)
        edit_command.task_service = Mock()
        edit_command.task_service.update_task_description.return_value = None  # Task not found
        edit_command.file_service = Mock()
        edit_command.file_service.resolve_file_paths.return_value = ["/test/file.xit"]
        
        # Execute command
        edit_command.execute(
            task_id=999,
            description="Updated description",
            directory=Path("/test"),
            specified_files=[]
        )
        
        # Verify error message
        mock_formatter.display_error.assert_called_once_with(
            "Task #999 not found"
        )
    
    def test_execute_edit_task_exception(self):
        """Test edit task with exception handling."""
        from xitkit.commands import EditTaskCommand
        
        mock_formatter = Mock()
        edit_command = EditTaskCommand(mock_formatter)
        edit_command.task_service = Mock()
        edit_command.task_service.update_task_description.side_effect = XitError("Test error")
        edit_command.file_service = Mock()
        edit_command.file_service.resolve_file_paths.return_value = ["/test/file.xit"]
        
        # Execute command
        edit_command.execute(
            task_id=1,
            description="Updated description",
            directory=Path("/test"),
            specified_files=[]
        )
        
        # Verify error message
        mock_formatter.display_error.assert_called_once_with("Test error")


class TestPriorityTaskCommand:
    """Test the PriorityTaskCommand functionality."""
    
    def test_priority_command_creation(self):
        """Test creating a PriorityTaskCommand."""
        from xitkit.commands import PriorityTaskCommand
        
        command = PriorityTaskCommand()
        
        assert isinstance(command.formatter, TaskFormatter)
        assert hasattr(command, 'task_service')
        assert hasattr(command, 'file_service')
    
    def test_execute_priority_task_success(self):
        """Test successful task priority setting."""
        from xitkit.commands import PriorityTaskCommand
        from xitkit.task import Task
        from xitkit.location import Location
        from xitkit.priority import Priority
        
        mock_formatter = Mock()
        priority_command = PriorityTaskCommand(mock_formatter)
        
        # Mock find_tasks to return a test task
        test_task = Task("Test task", location=Location("/test/file.xit", 1), status="OPEN", priority=0, tags=[], due_date=None)
        test_task.id = 1
        priority_command.find_tasks = Mock(return_value=[test_task])
        
        # Mock update_task to return updated task
        updated_task = Task("Test task", location=Location("/test/file.xit", 1), status="OPEN", priority=1, tags=[], due_date=None)
        updated_task.id = 1
        priority_command.task_service = Mock()
        priority_command.task_service.update_task.return_value = updated_task
        
        # Execute command
        priority_command.execute(
            task_ids=[1],
            priority=1,
            directory=Path("/test"),
            specified_files=[]
        )
        
        # Verify find_tasks was called
        priority_command.find_tasks.assert_called_once_with(
            Path("/test"), [], [1], interactive=False
        )
        
        # Verify task was updated
        priority_command.task_service.update_task.assert_called_once()
        
        # Verify success message
        mock_formatter.display_success.assert_called_once()
    
    def test_execute_priority_task_valid_integer(self):
        """Test priority setting with valid integer input."""
        from xitkit.commands import PriorityTaskCommand
        from xitkit.task import Task
        from xitkit.location import Location
        
        mock_formatter = Mock()
        priority_command = PriorityTaskCommand(mock_formatter)
        
        # Mock find_tasks to return a test task
        test_task = Task("Test task", location=Location("/test/file.xit", 1), status="OPEN", priority=0, tags=[], due_date=None)
        test_task.id = 1
        priority_command.find_tasks = Mock(return_value=[test_task])
        
        # Mock update_task to return updated task
        updated_task = Task("Test task", location=Location("/test/file.xit", 1), status="OPEN", priority=2, tags=[], due_date=None)
        updated_task.id = 1
        priority_command.task_service = Mock()
        priority_command.task_service.update_task.return_value = updated_task
        
        # Execute command with integer priority
        priority_command.execute(
            task_ids=[1],
            priority=2,
            directory=Path("/test"),
            specified_files=[]
        )
        
        # Verify task was updated
        priority_command.task_service.update_task.assert_called_once()
    
    def test_execute_priority_task_invalid_format(self):
        """Test priority setting with invalid format."""
        from xitkit.commands import PriorityTaskCommand
        
        mock_formatter = Mock()
        priority_command = PriorityTaskCommand(mock_formatter)
        
        # Execute command with negative priority (invalid)
        priority_command.execute(
            task_ids=[1],
            priority=-1,  # Invalid negative priority
            directory=Path("/test"),
            specified_files=[]
        )
        
        # Verify error message (caught by execute wrapper and displayed as unexpected error)
        mock_formatter.display_error.assert_called_once()
        # The exact error message will be "Unexpected error: Priority level cannot be negative"
    
    def test_execute_priority_task_not_found(self):
        """Test setting priority for a task that doesn't exist."""
        from xitkit.commands import PriorityTaskCommand
        from xitkit.exceptions import XitError
        
        mock_formatter = Mock()
        priority_command = PriorityTaskCommand(mock_formatter)
        
        # Mock find_tasks to raise XitError (task not found)
        priority_command.find_tasks = Mock(side_effect=XitError("No matching tasks found for the specified IDs."))
        
        # Execute command - this should raise XitError from find_tasks
        priority_command.execute(
            task_ids=[999],
            priority=1,
            directory=Path("/test"),
            specified_files=[]
        )
        
        # Verify error message (XitError caught by execute wrapper)
        mock_formatter.display_error.assert_called_once_with("No matching tasks found for the specified IDs.")


class TestTagTaskCommand:
    """Test the TagTaskCommand functionality."""
    
    def test_tag_command_creation(self):
        """Test creating a TagTaskCommand."""
        from xitkit.commands import TagTaskCommand
        
        command = TagTaskCommand()
        
        assert isinstance(command.formatter, TaskFormatter)
        assert hasattr(command, 'task_service')
        assert hasattr(command, 'file_service')
    
    def test_execute_tag_task_success(self):
        """Test successful tag addition."""
        from xitkit.commands import TagTaskCommand
        
        mock_formatter = Mock()
        tag_command = TagTaskCommand(mock_formatter)
        tag_command.task_service = Mock()
        tag_command.task_service.add_task_tag.return_value = True
        tag_command.file_service = Mock()
        tag_command.file_service.resolve_file_paths.return_value = ["/test/file.xit"]
        
        # Execute command
        tag_command.execute(
            task_id=1,
            tag="urgent",
            directory=Path("/test"),
            specified_files=[]
        )
        
        # Verify service call
        tag_command.task_service.add_task_tag.assert_called_once_with(
            task_id=1,
            tag="urgent",
            file_paths=["/test/file.xit"]
        )
        
        # Verify success message
        mock_formatter.display_success.assert_called_once_with(
            "Added tag #urgent to task #001"
        )
    
    def test_execute_tag_task_with_hash_prefix(self):
        """Test tag addition with hash prefix."""
        from xitkit.commands import TagTaskCommand
        
        mock_formatter = Mock()
        tag_command = TagTaskCommand(mock_formatter)
        tag_command.task_service = Mock()
        tag_command.task_service.add_task_tag.return_value = True
        tag_command.file_service = Mock()
        tag_command.file_service.resolve_file_paths.return_value = ["/test/file.xit"]
        
        # Execute command with # prefix
        tag_command.execute(
            task_id=1,
            tag="#urgent",
            directory=Path("/test"),
            specified_files=[]
        )
        
        # Verify # was stripped from service call
        tag_command.task_service.add_task_tag.assert_called_once_with(
            task_id=1,
            tag="urgent",
            file_paths=["/test/file.xit"]
        )
    
    def test_execute_tag_task_invalid_format(self):
        """Test tag addition with invalid format."""
        from xitkit.commands import TagTaskCommand
        
        mock_formatter = Mock()
        tag_command = TagTaskCommand(mock_formatter)
        tag_command.task_service = Mock()
        
        # Execute command with invalid tag (contains space)
        tag_command.execute(
            task_id=1,
            tag="urgent task",
            directory=Path("/test"),
            specified_files=[]
        )
        
        # Verify error message and no service call
        mock_formatter.display_error.assert_called_once_with(
            "Tag must be a single word without spaces"
        )
        tag_command.task_service.add_task_tag.assert_not_called()
    
    def test_execute_tag_task_not_found(self):
        """Test adding tag to a task that doesn't exist."""
        from xitkit.commands import TagTaskCommand
        
        mock_formatter = Mock()
        tag_command = TagTaskCommand(mock_formatter)
        tag_command.task_service = Mock()
        tag_command.file_service = Mock()
        tag_command.file_service.resolve_file_paths.return_value = ["/test/file.xit"]
        tag_command.task_service.add_task_tag.return_value = False
        
        # Execute command
        tag_command.execute(
            task_id=999,
            tag="urgent",
            directory=Path("/test"),
            specified_files=[]
        )
        
        # Verify error message and service call
        mock_formatter.display_error.assert_called_once_with(
            "Task #999 not found"
        )
        tag_command.task_service.add_task_tag.assert_called_once_with(
            task_id=999, tag="urgent", file_paths=["/test/file.xit"]
        )


class TestUntagTaskCommand:
    """Test the UntagTaskCommand functionality."""
    
    def test_untag_command_creation(self):
        """Test creating an UntagTaskCommand."""
        from xitkit.commands import UntagTaskCommand
        
        command = UntagTaskCommand()
        
        assert isinstance(command.formatter, TaskFormatter)
        assert hasattr(command, 'task_service')
        assert hasattr(command, 'file_service')
    
    def test_execute_untag_task_success(self):
        """Test successful tag removal."""
        from xitkit.commands import UntagTaskCommand
        
        mock_formatter = Mock()
        untag_command = UntagTaskCommand(mock_formatter)
        untag_command.task_service = Mock()
        untag_command.file_service = Mock()
        untag_command.file_service.resolve_file_paths.return_value = ["/test/file.xit"]
        untag_command.task_service.remove_task_tag.return_value = True
        
        # Execute command
        untag_command.execute(
            task_id=1,
            tag="urgent",
            directory=Path("/test"),
            specified_files=[]
        )
        
        # Verify service call
        untag_command.task_service.remove_task_tag.assert_called_once_with(
            task_id=1,
            tag="urgent",
            file_paths=["/test/file.xit"]
        )
        
        # Verify success message
        mock_formatter.display_success.assert_called_once_with(
            "Removed tag #urgent from task #001"
        )
    
    def test_execute_untag_task_with_hash_prefix(self):
        """Test tag removal with hash prefix."""
        from xitkit.commands import UntagTaskCommand
        
        mock_formatter = Mock()
        untag_command = UntagTaskCommand(mock_formatter)
        untag_command.task_service = Mock()
        untag_command.file_service = Mock()
        untag_command.file_service.resolve_file_paths.return_value = ["/test/file.xit"]
        untag_command.task_service.remove_task_tag.return_value = True
        
        # Execute command with # prefix
        untag_command.execute(
            task_id=1,
            tag="#urgent",
            directory=Path("/test"),
            specified_files=[]
        )
        
        # Verify # was stripped from service call
        untag_command.task_service.remove_task_tag.assert_called_once_with(
            task_id=1,
            tag="urgent",
            file_paths=["/test/file.xit"]
        )
    
    def test_execute_untag_task_not_found(self):
        """Test removing tag from a task that doesn't exist."""
        from xitkit.commands import UntagTaskCommand
        
        mock_formatter = Mock()
        untag_command = UntagTaskCommand(mock_formatter)
        untag_command.task_service = Mock()
        untag_command.file_service = Mock()
        untag_command.file_service.resolve_file_paths.return_value = ["/test/file.xit"]
        untag_command.task_service.remove_task_tag.return_value = False
        
        # Execute command
        untag_command.execute(
            task_id=999,
            tag="urgent",
            directory=Path("/test"),
            specified_files=[]
        )
        
        # Verify error message and service call
        mock_formatter.display_error.assert_called_once_with(
            "Task #999 not found"
        )
        untag_command.task_service.remove_task_tag.assert_called_once_with(
            task_id=999, tag="urgent", file_paths=["/test/file.xit"]
        )


class TestCommandFactoryNew:
    """Test the CommandFactory for new commands."""
    
    def test_create_edit_command(self):
        """Test creating EditTaskCommand through factory."""
        from xitkit.commands import CommandFactory, EditTaskCommand
        
        command = CommandFactory.create_edit_command()
        
        assert isinstance(command, EditTaskCommand)
        assert isinstance(command.formatter, TaskFormatter)
    
    def test_create_edit_command_with_formatter(self):
        """Test creating EditTaskCommand with custom formatter."""
        from xitkit.commands import CommandFactory, EditTaskCommand
        
        custom_formatter = TaskFormatter()
        command = CommandFactory.create_edit_command(custom_formatter)
        
        assert isinstance(command, EditTaskCommand)
        assert command.formatter is custom_formatter
    
    def test_create_priority_command(self):
        """Test creating PriorityTaskCommand through factory."""
        from xitkit.commands import CommandFactory, PriorityTaskCommand
        
        command = CommandFactory.create_priority_command()
        
        assert isinstance(command, PriorityTaskCommand)
        assert isinstance(command.formatter, TaskFormatter)
    
    def test_create_tag_command(self):
        """Test creating TagTaskCommand through factory."""
        from xitkit.commands import CommandFactory, TagTaskCommand
        
        command = CommandFactory.create_tag_command()
        
        assert isinstance(command, TagTaskCommand)
        assert isinstance(command.formatter, TaskFormatter)
    
    def test_create_untag_command(self):
        """Test creating UntagTaskCommand through factory."""
        from xitkit.commands import CommandFactory, UntagTaskCommand
        
        command = CommandFactory.create_untag_command()
        
        assert isinstance(command, UntagTaskCommand)
        assert isinstance(command.formatter, TaskFormatter)