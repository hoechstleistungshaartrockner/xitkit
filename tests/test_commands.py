"""Tests for the Commands module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from xit.commands import (
    Command, ShowTasksCommand, ShowStatsCommand, AddTaskCommand, 
    MarkTaskCommand, RescheduleTaskCommand, RemoveTaskCommand, 
    MoveTaskCommand, CommandFactory
)
from xit.services import TaskFilter
from xit.task import Task
from xit.formatter import TaskFormatter
from xit.exceptions import XitError
from tests.conftest import create_test_file

class TestCommandBase:
    """Test the base Command class."""
    
    def test_command_is_abstract(self):
        """Test that Command is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            Command()
    
    def test_command_subclass_with_formatter(self):
        """Test command subclass with custom formatter."""
        class TestCommand(Command):
            def execute(self, **kwargs):
                return "test"
        
        custom_formatter = TaskFormatter()
        cmd = TestCommand(custom_formatter)
        
        assert cmd.formatter is custom_formatter
        assert hasattr(cmd, 'task_service')
        assert hasattr(cmd, 'file_service')
    
    def test_command_subclass_default_formatter(self):
        """Test command subclass with default formatter."""
        class TestCommand(Command):
            def execute(self, **kwargs):
                return "test"
        
        cmd = TestCommand()
        
        assert isinstance(cmd.formatter, TaskFormatter)
        assert hasattr(cmd, 'task_service')
        assert hasattr(cmd, 'file_service')


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
        # Setup mocks
        show_command.file_service.resolve_file_paths.return_value = ["/test.xit"]
        show_command.task_service.load_tasks.return_value = [
            Task("/test.xit", 1, "Test task", "OPEN", 0, [], None)
        ]
        show_command.task_service.filter_tasks.return_value = [
            Task("/test.xit", 1, "Test task", "OPEN", 0, [], None)
        ]
        
        # Execute command
        show_command.execute(
            path=None,
            directory=Path("/test"),
            specified_files=None,
            filters=None,
            show_line=False,
            count_only=False
        )
        
        # Verify interactions
        show_command.file_service.resolve_file_paths.assert_called_once()
        show_command.task_service.load_tasks.assert_called_once_with(["/test.xit"])
        show_command.formatter.display_tasks.assert_called_once()
        show_command.formatter.display_summary.assert_called_once()
    
    def test_execute_no_files_found(self, show_command):
        """Test execution when no files are found."""
        show_command.file_service.resolve_file_paths.return_value = []
        
        show_command.execute()
        
        show_command.formatter.display_warning.assert_called_once_with(
            "No task files found."
        )
    
    def test_execute_no_tasks_found(self, show_command):
        """Test execution when no tasks are found in files."""
        show_command.file_service.resolve_file_paths.return_value = ["/test.xit"]
        show_command.task_service.load_tasks.return_value = []
        
        show_command.execute()
        
        show_command.formatter.display_warning.assert_called_once_with(
            "No tasks found in the specified files."
        )
    
    def test_execute_with_filters(self, show_command):
        """Test execution with task filters."""
        tasks = [
            Task("/test.xit", 1, "Open task", "OPEN", 0, [], None),
            Task("/test.xit", 2, "Done task", "DONE", 0, [], None)
        ]
        filtered_tasks = [tasks[0]]  # Only open task
        
        show_command.file_service.resolve_file_paths.return_value = ["/test.xit"]
        show_command.task_service.load_tasks.return_value = tasks
        show_command.task_service.filter_tasks.return_value = filtered_tasks
        
        filters = TaskFilter(status="OPEN")
        show_command.execute(filters=filters)
        
        show_command.task_service.filter_tasks.assert_called_once_with(tasks, filters)
        show_command.formatter.display_tasks.assert_called_once_with(
            filtered_tasks, show_line=False, show_id=False
        )
        show_command.formatter.display_summary.assert_called_once_with(1, 2)
    
    def test_execute_no_filtered_matches(self, show_command):
        """Test execution when filters match no tasks."""
        tasks = [Task("/test.xit", 1, "Task", "OPEN", 0, [], None)]
        
        show_command.file_service.resolve_file_paths.return_value = ["/test.xit"]
        show_command.task_service.load_tasks.return_value = tasks
        show_command.task_service.filter_tasks.return_value = []  # No matches
        
        filters = TaskFilter(status="DONE")
        show_command.execute(filters=filters)
        
        show_command.formatter.display_warning.assert_called_once_with(
            "No tasks match the specified criteria."
        )
    
    def test_execute_count_only(self, show_command):
        """Test execution with count_only=True."""
        tasks = [Task("/test.xit", 1, "Task", "OPEN", 0, [], None)]
        
        show_command.file_service.resolve_file_paths.return_value = ["/test.xit"]
        show_command.task_service.load_tasks.return_value = tasks
        show_command.task_service.filter_tasks.return_value = tasks
        
        show_command.execute(count_only=True)
        
        show_command.formatter.display_count.assert_called_once_with(1)
        show_command.formatter.display_tasks.assert_not_called()
    
    def test_execute_with_line_numbers(self, show_command):
        """Test execution with show_line=True."""
        tasks = [Task("/test.xit", 1, "Task", "OPEN", 0, [], None)]
        
        show_command.file_service.resolve_file_paths.return_value = ["/test.xit"]
        show_command.task_service.load_tasks.return_value = tasks
        show_command.task_service.filter_tasks.return_value = tasks
        
        show_command.execute(show_line=True)
        
        show_command.formatter.display_tasks.assert_called_once_with(
            tasks, show_line=True, show_id=False
        )
    
    def test_execute_handles_xit_error(self, show_command):
        """Test execution handles XitError properly."""
        show_command.file_service.resolve_file_paths.side_effect = XitError("Test error")
        
        show_command.execute()
        
        show_command.formatter.display_error.assert_called_once_with("Test error")
    
    def test_execute_handles_unexpected_error(self, show_command):
        """Test execution handles unexpected errors."""
        show_command.file_service.resolve_file_paths.side_effect = ValueError("Unexpected")
        
        show_command.execute()
        
        show_command.formatter.display_error.assert_called_once_with(
            "Unexpected error: Unexpected"
        )


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
            Task("/test.xit", 1, "Open task", "OPEN", 1, ["#work"], "2025-12-31"),
            Task("/test.xit", 2, "Done task", "DONE", 0, [], None)
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
        tasks = [Task("/test.xit", 1, "Task", "OPEN", 0, [], None)]
        stats = {'total_tasks': 1, 'status_counts': {}, 'priority_counts': {}, 
                'files_with_tasks': set(), 'tasks_with_due_dates': 0, 'tasks_with_tags': 0}
        
        stats_command.file_service.resolve_file_paths.return_value = ["/test.xit"]
        stats_command.task_service.load_tasks.return_value = tasks
        stats_command.task_service.get_task_statistics.return_value = stats
        
        # Mock the console print calls
        stats_command.formatter.console = Mock()
        
        stats_command.execute(path="/specific/path")
        
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
        # Setup
        add_command.task_service.add_task_to_file = Mock(return_value=True)
        
        # Execute
        add_command.execute("New task description", "tasks.xit", directory=Path("/test"))
        
        # Verify
        add_command.task_service.add_task_to_file.assert_called_once_with(
            "New task description", "/test/tasks.xit"
        )
        add_command.formatter.display_success.assert_called_once()
    
    def test_execute_add_task_absolute_path(self, add_command):
        """Test adding task with absolute file path."""
        # Setup  
        add_command.task_service.add_task_to_file = Mock(return_value=True)
        
        # Execute with absolute path
        add_command.execute("New task", "/absolute/path/tasks.xit")
        
        # Verify
        add_command.task_service.add_task_to_file.assert_called_once_with(
            "New task", "/absolute/path/tasks.xit"
        )
        add_command.formatter.display_success.assert_called_once()
    
    def test_execute_add_task_with_due_date(self, add_command):
        """Test adding a task with due date."""
        # Setup
        add_command.task_service.add_task_to_file = Mock(return_value=True)
        
        # Execute
        add_command.execute("Task with date -> 2025-12-31", "tasks.xit", directory=Path("/test"))
        
        # Verify task was added with proper description
        add_command.task_service.add_task_to_file.assert_called_once_with(
            "Task with date -> 2025-12-31", "/test/tasks.xit"
        )
        add_command.formatter.display_success.assert_called_once()
    
    def test_execute_add_task_relative_path_no_directory(self, add_command):
        """Test adding task with relative path and no directory specified."""
        # Setup
        add_command.task_service.add_task_to_file = Mock(return_value=True)
        
        with patch('pathlib.Path.cwd', return_value=Path("/current/working/dir")):
            # Execute with relative path and no directory
            add_command.execute("New task", "tasks.xit")
            
            # Verify absolute path was resolved using cwd
            add_command.task_service.add_task_to_file.assert_called_once_with(
                "New task", "/current/working/dir/tasks.xit"
            )
    
    def test_execute_add_task_error_handling(self, add_command):
        """Test error handling during task addition."""
        # Setup
        add_command.task_service.add_task_to_file.side_effect = XitError("Test error")
        
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
        # Setup
        test_file = Path("/test/tasks.xit")
        mark_command.file_service.resolve_file_paths.return_value = [test_file]
        
        # Create mock updated task
        updated_task = Mock()
        updated_task.description = "Test task"
        updated_task.file = "/test/tasks.xit"
        mark_command.task_service.mark_task_by_id.return_value = updated_task
        
        # Execute
        mark_command.execute([1], "X", directory=Path("/test"))
        
        # Verify
        mark_command.file_service.resolve_file_paths.assert_called_once_with(
            None, Path("/test"), None
        )
        mark_command.task_service.mark_task_by_id.assert_called_once_with(1, "X", [test_file])
        mark_command.formatter.display_success.assert_called_once()
    
    def test_execute_mark_task_no_files(self, mark_command):
        """Test marking task when no files found."""
        # Setup
        mark_command.file_service.resolve_file_paths.return_value = []
        
        # Execute
        mark_command.execute(1, "x", directory=Path("/test"))
        
        # Verify
        mark_command.formatter.display_warning.assert_called_once_with(
            "No task files found."
        )
        mark_command.task_service.mark_task_by_id.assert_not_called()
    
    def test_execute_mark_task_not_found(self, mark_command):
        """Test marking a task that doesn't exist."""
        # Setup
        test_file = Path("/test/tasks.xit")
        mark_command.file_service.resolve_file_paths.return_value = [test_file]
        mark_command.task_service.mark_task_by_id.return_value = None
        
        # Execute
        mark_command.execute([999], "X", directory=Path("/test"))
        
        # Verify
        mark_command.formatter.display_error.assert_called_once_with(
            "Task #999 not found."
        )
    
    def test_execute_mark_task_different_statuses(self, mark_command):
        """Test marking tasks with different status symbols."""
        # Setup
        test_file = Path("/test/tasks.xit")
        mark_command.file_service.resolve_file_paths.return_value = [test_file]
        
        updated_task = Mock()
        updated_task.description = "Test task"
        updated_task.file = "/test/tasks.xit"
        mark_command.task_service.mark_task_by_id.return_value = updated_task
        
        # Test different status symbols
        statuses = ["X", "ONGOING", "OBSOLETE", "INQUESTION", "OPEN"]
        for status in statuses:
            mark_command.execute([1], status, directory=Path("/test"))
            mark_command.task_service.mark_task_by_id.assert_called_with(1, status, [test_file])
    
    def test_execute_mark_task_with_specified_files(self, mark_command):
        """Test marking task in specified files."""
        # Setup
        specified_files = ["tasks.xit", "projects.md"]
        test_files = [Path("/test/tasks.xit"), Path("/test/projects.md")]
        mark_command.file_service.resolve_file_paths.return_value = test_files
        
        updated_task = Mock()
        updated_task.description = "Test task"
        updated_task.file = "/test/tasks.xit"
        mark_command.task_service.mark_task_by_id.return_value = updated_task
        
        # Execute
        mark_command.execute(1, "x", specified_files=specified_files)
        
        # Verify
        mark_command.file_service.resolve_file_paths.assert_called_once_with(
            None, None, specified_files
        )
    
    def test_execute_mark_task_error_handling(self, mark_command):
        """Test error handling during task marking."""
        # Setup
        mark_command.file_service.resolve_file_paths.side_effect = XitError("Test error")
        
        # Execute
        mark_command.execute(1, "x", directory=Path("/test"))
        
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
    
    @patch('xit.dateutils.get_date_parser')
    def test_execute_reschedule_task_success(self, mock_get_parser, reschedule_command):
        """Test successfully rescheduling a task."""
        # Setup
        test_file = Path("/test/tasks.xit")
        reschedule_command.file_service.resolve_file_paths.return_value = [test_file]
        
        # Mock date parser
        mock_parser = Mock()
        mock_parser.parse_date_expression.return_value = "2025-12-31"
        mock_get_parser.return_value = mock_parser
        
        # Mock updated task
        updated_task = Mock()
        updated_task.description = "Test task"
        updated_task.file = "/test/tasks.xit"
        reschedule_command.task_service.reschedule_task_by_id.return_value = updated_task
        
        # Execute
        reschedule_command.execute([1], "2025-12-31", directory=Path("/test"))
        
        # Verify
        reschedule_command.file_service.resolve_file_paths.assert_called_once()
        mock_parser.parse_date_expression.assert_called_once_with("2025-12-31")
        reschedule_command.task_service.reschedule_task_by_id.assert_called_once_with(
            1, "2025-12-31", [test_file]
        )
        reschedule_command.formatter.display_success.assert_called_once()
    
    @patch('xit.dateutils.get_date_parser')
    def test_execute_reschedule_natural_language_dates(self, mock_get_parser, reschedule_command):
        """Test rescheduling with natural language dates."""
        # Setup
        test_file = Path("/test/tasks.xit")
        reschedule_command.file_service.resolve_file_paths.return_value = [test_file]
        
        mock_parser = Mock()
        mock_parser.parse_date_expression.return_value = "2025-10-18"
        mock_get_parser.return_value = mock_parser
        
        updated_task = Mock()
        updated_task.description = "Test task"
        updated_task.file = "/test/tasks.xit"
        reschedule_command.task_service.reschedule_task_by_id.return_value = updated_task
        
        # Test different natural language expressions
        expressions = ["tomorrow", "today", "+1w", "1d-"]
        expected_parsed = ["tomorrow", "today", "1w", "-1d"]
        
        for expr, expected in zip(expressions, expected_parsed):
            reschedule_command.execute([1], expr, directory=Path("/test"))
            mock_parser.parse_date_expression.assert_called_with(expected)
    
    @patch('xit.dateutils.get_date_parser')
    def test_execute_reschedule_invalid_date(self, mock_get_parser, reschedule_command):
        """Test rescheduling with invalid date format."""
        # Setup
        test_file = Path("/test/tasks.xit")
        reschedule_command.file_service.resolve_file_paths.return_value = [test_file]
        
        mock_parser = Mock()
        mock_parser.parse_date_expression.side_effect = Exception("Invalid date")
        mock_get_parser.return_value = mock_parser
        
        # Execute
        reschedule_command.execute([1], "invalid-date", directory=Path("/test"))
        
        # Verify error handling
        reschedule_command.formatter.display_error.assert_called_once_with(
            "Invalid date format: invalid-date"
        )
        reschedule_command.task_service.reschedule_task_by_id.assert_not_called()
    
    def test_execute_reschedule_task_not_found(self, reschedule_command):
        """Test rescheduling a task that doesn't exist."""
        # Setup
        test_file = Path("/test/tasks.xit")
        reschedule_command.file_service.resolve_file_paths.return_value = [test_file]
        reschedule_command.task_service.reschedule_task_by_id.return_value = None
        
        with patch('xit.dateutils.get_date_parser') as mock_get_parser:
            mock_parser = Mock()
            mock_parser.parse_date_expression.return_value = "2025-12-31"
            mock_get_parser.return_value = mock_parser
            
            # Execute
            reschedule_command.execute([999], "2025-12-31", directory=Path("/test"))
            
        # Verify
        reschedule_command.formatter.display_error.assert_called_once_with(
            "Task #999 not found."
        )

    def test_execute_reschedule_no_files(self, reschedule_command):
        """Test rescheduling when no files found."""
        # Setup
        reschedule_command.file_service.resolve_file_paths.return_value = []
        
        # Execute
        reschedule_command.execute([1], "tomorrow", directory=Path("/test"))
        
        # Verify
        reschedule_command.formatter.display_warning.assert_called_once_with(
            "No task files found."
        )


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
            None, Path("/test"), None
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
            None, Path("/test"), None
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
            None, None, specified_files
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
            None, Path("/test"), None
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
            None, None, specified_files
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
            'total_tasks': 5,
            'status_counts': {'OPEN': 2, 'DONE': 2, 'ONGOING': 1},
            'priority_counts': {0: 3, 1: 1, 2: 1},
            'files_with_tasks': {"/file1.xit", "/file2.xit"},
            'tasks_with_due_dates': 2,
            'tasks_with_tags': 3
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
            'total_tasks': 1,
            'status_counts': {'OPEN': 1},
            'priority_counts': {0: 1},
            'files_with_tasks': {"/test.xit"},
            'tasks_with_due_dates': 0,
            'tasks_with_tags': 0
        }
        
        stats_command_with_console._display_statistics(stats, "/test/path")
        
        calls = stats_command_with_console.formatter.console.print.call_args_list
        call_texts = [str(call) for call in calls]
        
        # Should include the path in the header
        assert any("/test/path" in text for text in call_texts)
    
    def test_display_statistics_status_breakdown(self, stats_command_with_console):
        """Test status breakdown in statistics display."""
        stats = {
            'total_tasks': 5,
            'status_counts': {
                'OPEN': 2,
                'DONE': 1,
                'ONGOING': 1,
                'OBSOLETE': 1,
                'INQUESTION': 0  # Zero count should not be displayed
            },
            'priority_counts': {},
            'files_with_tasks': set(),
            'tasks_with_due_dates': 0,
            'tasks_with_tags': 0
        }
        
        stats_command_with_console._display_statistics(stats)
        
        calls = stats_command_with_console.formatter.console.print.call_args_list
        call_texts = [str(call) for call in calls]
        
        # Should show non-zero status counts
        assert any("OPEN: 2" in text for text in call_texts)
        assert any("DONE: 1" in text for text in call_texts)
        assert any("ONGOING: 1" in text for text in call_texts)
        assert any("OBSOLETE: 1" in text for text in call_texts)
        # Should not show zero counts
        assert not any("INQUESTION: 0" in text for text in call_texts)
    
    def test_display_statistics_priority_breakdown(self, stats_command_with_console):
        """Test priority breakdown in statistics display."""
        stats = {
            'total_tasks': 4,
            'status_counts': {},
            'priority_counts': {0: 2, 1: 1, 3: 1},
            'files_with_tasks': set(),
            'tasks_with_due_dates': 0,
            'tasks_with_tags': 0
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
            path=str(test_file),
            directory=None,
            specified_files=None,
            filters=None,
            show_line=False,
            count_only=False
        )
        
        # Verify that tasks were displayed
        cmd.formatter.display_tasks.assert_called_once()
        args, kwargs = cmd.formatter.display_tasks.call_args
        tasks = args[0]
        
        assert len(tasks) == 3
        assert tasks[0].description == "Open high priority task #work"
        assert tasks[0].priority == 1
        assert tasks[1].status == "DONE"
        assert tasks[2].status == "ONGOING"
        assert tasks[2].due_date == "2025-12-31"
    
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
            path=str(temp_dir),
            directory=None,
            specified_files=None
        )
        
        # Verify statistics were calculated and displayed
        cmd._display_statistics.assert_called_once()
        stats, path_arg = cmd._display_statistics.call_args[0]
        
        assert stats['total_tasks'] == 5
        assert stats['status_counts']['OPEN'] == 1
        assert stats['status_counts']['DONE'] == 1
        assert stats['status_counts']['ONGOING'] == 1
        assert stats['status_counts']['OBSOLETE'] == 1
        assert stats['status_counts']['INQUESTION'] == 1
        assert len(stats['files_with_tasks']) == 2
    
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
        filters = TaskFilter(status="OPEN")
        cmd.execute(
            path=str(test_file),
            filters=filters
        )
        
        args, kwargs = cmd.formatter.display_tasks.call_args
        filtered_tasks = args[0]
        
        assert len(filtered_tasks) == 2  # Two OPEN tasks
        assert all(task.status == "OPEN" for task in filtered_tasks)
        
        # Test filtering by tags
        cmd.formatter.display_tasks.reset_mock()
        filters = TaskFilter(tags=["work"])
        cmd.execute(
            path=str(test_file),
            filters=filters
        )
        
        args, kwargs = cmd.formatter.display_tasks.call_args
        filtered_tasks = args[0]
        
        assert len(filtered_tasks) == 3  # Three tasks with #work tag
        assert all("#work" in task.tags for task in filtered_tasks)


class TestCommandErrorScenarios:
    """Test command error handling scenarios."""
    
    def test_show_command_file_not_found(self):
        """Test ShowTasksCommand with non-existent file."""
        cmd = ShowTasksCommand()
        cmd.formatter.display_error = Mock()
        
        cmd.execute(path="/nonexistent/file.xit")
        
        # Should display an error
        cmd.formatter.display_error.assert_called_once()
        error_message = cmd.formatter.display_error.call_args[0][0]
        assert "not found" in error_message.lower() or "does not exist" in error_message.lower()
    
    def test_stats_command_file_not_found(self):
        """Test ShowStatsCommand with non-existent file."""
        cmd = ShowStatsCommand()
        cmd.formatter.display_error = Mock()
        
        cmd.execute(path="/nonexistent/file.xit")
        
        # Should display an error
        cmd.formatter.display_error.assert_called_once()
    
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
            cmd.execute(path=str(test_file), filters=filters)
            # Command should complete successfully
            success = True
        except Exception:
            success = False
        
        assert success, "Command should not crash with invalid date filter"



class TestBatchProcessing:
    """Test batch processing functionality for commands that support multiple task IDs."""
    
    def test_mark_command_multiple_tasks_success(self):
        """Test marking multiple tasks successfully."""
        # Setup
        formatter = Mock(spec=TaskFormatter)
        file_service = Mock()
        task_service = Mock()
        mark_command = MarkTaskCommand(formatter)
        mark_command.file_service = file_service
        mark_command.task_service = task_service
        
        test_file = Path("/test/tasks.xit")
        file_service.resolve_file_paths.return_value = [test_file]
        
        # Mock successful task operations
        task1 = Mock()
        task1.description = "Task 1"
        task1.file = "/test/tasks.xit"
        task2 = Mock()
        task2.description = "Task 2"
        task2.file = "/test/tasks.xit"
        task_service.mark_task_by_id.side_effect = [task1, task2]
        
        # Execute batch operation
        mark_command.execute([1, 2], "DONE", directory=Path("/test"))
        
        # Verify both tasks were processed
        assert task_service.mark_task_by_id.call_count == 2
        task_service.mark_task_by_id.assert_any_call(1, "DONE", [test_file])
        task_service.mark_task_by_id.assert_any_call(2, "DONE", [test_file])
        
        # Verify success messages
        assert formatter.display_success.call_count == 3  # 2 individual + 1 summary

    def test_mark_command_mixed_results(self):
        """Test marking multiple tasks with some not found."""
        # Setup
        formatter = Mock(spec=TaskFormatter)
        file_service = Mock()
        task_service = Mock()
        mark_command = MarkTaskCommand(formatter)
        mark_command.file_service = file_service
        mark_command.task_service = task_service
        
        test_file = Path("/test/tasks.xit")
        file_service.resolve_file_paths.return_value = [test_file]
        
        # Mock one success, one failure
        task1 = Mock()
        task1.description = "Task 1"
        task1.file = "/test/tasks.xit"
        
        def mock_mark_task(task_id, status, files):
            if task_id == 1:
                return task1
            else:
                from xit.exceptions import XitError
                raise XitError(f"Task #{task_id} not found.")
        
        task_service.mark_task_by_id.side_effect = mock_mark_task
        
        # Execute batch operation
        mark_command.execute([1, 999], "DONE", directory=Path("/test"))
        
        # Verify both operations were attempted
        assert task_service.mark_task_by_id.call_count == 2
        
        # Verify success and error messages
        formatter.display_success.assert_any_call('✓ Marked task #1 as done in /test/tasks.xit: "Task 1"')
        formatter.display_error.assert_any_call("Error marking task #999: Task #999 not found.")

    def test_reschedule_command_multiple_tasks(self):
        """Test rescheduling multiple tasks to same date."""
        # Setup
        formatter = Mock(spec=TaskFormatter)
        file_service = Mock()
        task_service = Mock()
        reschedule_command = RescheduleTaskCommand(formatter)
        reschedule_command.file_service = file_service
        reschedule_command.task_service = task_service
        
        test_file = Path("/test/tasks.xit")
        file_service.resolve_file_paths.return_value = [test_file]
        
        # Mock successful task operations
        task1 = Mock()
        task1.description = "Task 1"
        task1.file = "/test/tasks.xit"
        task2 = Mock()
        task2.description = "Task 2"
        task2.file = "/test/tasks.xit"
        task_service.reschedule_task_by_id.side_effect = [task1, task2]
        
        # Mock date parser
        with patch('xit.dateutils.get_date_parser') as mock_get_parser:
            mock_parser = Mock()
            mock_parser.parse_date_expression.return_value = "2025-12-31"
            mock_get_parser.return_value = mock_parser
            
            # Execute batch operation
            reschedule_command.execute([1, 2], "2025-12-31", directory=Path("/test"))
        
        # Verify both tasks were processed
        assert task_service.reschedule_task_by_id.call_count == 2
        task_service.reschedule_task_by_id.assert_any_call(1, "2025-12-31", [test_file])
        task_service.reschedule_task_by_id.assert_any_call(2, "2025-12-31", [test_file])

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
        # Setup
        formatter = Mock(spec=TaskFormatter)
        file_service = Mock()
        task_service = Mock()
        mark_command = MarkTaskCommand(formatter)
        mark_command.file_service = file_service
        mark_command.task_service = task_service
        
        test_file = Path("/test/tasks.xit")
        file_service.resolve_file_paths.return_value = [test_file]
        
        # Track call order
        call_order = []
        
        def track_calls(task_id, status, files):
            call_order.append(task_id)
            task = Mock()
            task.description = f"Task {task_id}"
            task.file = "/test/tasks.xit"
            return task
        
        task_service.mark_task_by_id.side_effect = track_calls
        
        # Execute with non-sequential order
        mark_command.execute([5, 1, 3, 2], "DONE", directory=Path("/test"))
        
        # Verify order was preserved
        assert call_order == [5, 1, 3, 2]

    def test_empty_task_list_handling(self):
        """Test handling when no task IDs provided."""
        # Setup
        formatter = Mock(spec=TaskFormatter)
        file_service = Mock()
        task_service = Mock()
        mark_command = MarkTaskCommand(formatter)
        mark_command.file_service = file_service
        mark_command.task_service = task_service
        
        test_file = Path("/test/tasks.xit")
        file_service.resolve_file_paths.return_value = [test_file]
        
        # Execute with empty list
        mark_command.execute([], "DONE", directory=Path("/test"))
        
        # Verify no service calls made and no error messages
        task_service.mark_task_by_id.assert_not_called()
        formatter.display_error.assert_not_called()  # No error for empty list
        formatter.display_success.assert_not_called()  # No success messages either