"""Tests for the Commands module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from xit.commands import (
    Command, ShowTasksCommand, ShowStatsCommand, CommandFactory
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