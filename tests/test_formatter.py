"""Tests for the Formatter module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from rich.console import Console
from rich.text import Text

from xitflow.formatter import TaskFormatter, format_task_rich
from xitflow.task import Task
from tests.conftest import create_test_file


class TestTaskFormatterBasics:
    """Test basic TaskFormatter functionality."""
    
    def test_formatter_creation(self):
        """Test creating a TaskFormatter instance."""
        formatter = TaskFormatter()
        
        assert isinstance(formatter.console, Console)
        assert hasattr(formatter, 'date_parser')
        assert hasattr(formatter, 'status_colors')
    
    def test_formatter_creation_with_console(self):
        """Test creating a TaskFormatter with custom console."""
        custom_console = Console()
        formatter = TaskFormatter(custom_console)
        
        assert formatter.console is custom_console
    
    def test_status_colors(self):
        """Test status color mapping."""
        formatter = TaskFormatter()
        
        expected_colors = {
            'OPEN': 'white',
            'DONE': 'green',
            'ONGOING': 'yellow',
            'OBSOLETE': 'red',
            'INQUESTION': 'magenta'
        }
        
        assert formatter.status_colors == expected_colors


class TestDateNormalization:
    """Test date normalization for display."""
    
    def test_normalize_standard_date(self, task_formatter):
        """Test normalizing standard YYYY-MM-DD dates."""
        result = task_formatter._normalize_date_for_display("2025-12-31")
        assert result == "2025-12-31"
    
    def test_normalize_month_date(self, task_formatter):
        """Test normalizing YYYY-MM dates."""
        # December should become 2025-12-31
        result = task_formatter._normalize_date_for_display("2025-12")
        assert result == "2025-12-31"
        
        # February should become 2025-02-28 (non-leap year)
        result = task_formatter._normalize_date_for_display("2025-02")
        assert result == "2025-02-28"
        
        # February in leap year should become 2024-02-29
        result = task_formatter._normalize_date_for_display("2024-02")
        assert result == "2024-02-29"
    
    def test_normalize_year_date(self, task_formatter):
        """Test normalizing YYYY dates."""
        result = task_formatter._normalize_date_for_display("2025")
        assert result == "2025-12-31"
    
    def test_normalize_week_date(self, task_formatter):
        """Test normalizing YYYY-W## dates."""
        result = task_formatter._normalize_date_for_display("2025-W01")
        # Should convert to a specific date in that week
        assert "2025-" in result
        assert len(result) == 10  # YYYY-MM-DD format
    
    def test_normalize_quarter_date(self, task_formatter):
        """Test normalizing YYYY-Q# dates."""
        result = task_formatter._normalize_date_for_display("2025-Q1")
        assert result == "2025-03-31"
        
        result = task_formatter._normalize_date_for_display("2025-Q2")
        assert result == "2025-06-30"
        
        result = task_formatter._normalize_date_for_display("2025-Q3")
        assert result == "2025-09-30"
        
        result = task_formatter._normalize_date_for_display("2025-Q4")
        assert result == "2025-12-31"
    
    def test_normalize_slash_format(self, task_formatter):
        """Test normalizing slash-separated dates."""
        result = task_formatter._normalize_date_for_display("2025/12/31")
        assert result == "2025-12-31"
        
        result = task_formatter._normalize_date_for_display("2025/12")
        assert result == "2025-12-31"
    
    def test_normalize_invalid_date(self, task_formatter):
        """Test normalizing invalid dates returns as-is."""
        result = task_formatter._normalize_date_for_display("invalid-date")
        assert result == "invalid-date"


class TestTaskFormatting:
    """Test individual task formatting."""
    
    def test_format_simple_task(self, task_formatter):
        """Test formatting a simple task."""
        task = Task("/test.xit", 1, "Simple task", "OPEN", 0, [], None)
        
        result = task_formatter.format_task(task)
        
        assert isinstance(result, Text)
        # Check that it contains the status symbol and description
        text_content = str(result)
        assert "[ ]" in text_content
        assert "Simple task" in text_content
    
    def test_format_task_with_priority(self, task_formatter):
        """Test formatting a task with priority."""
        task = Task("/test.xit", 1, "Important task", "OPEN", 2, [], None)
        
        result = task_formatter.format_task(task)
        
        text_content = str(result)
        assert "[ ]" in text_content
        assert "!!" in text_content  # Priority indicator
        assert "Important task" in text_content
    
    def test_format_task_different_statuses(self, task_formatter):
        """Test formatting tasks with different statuses."""
        statuses = ["OPEN", "DONE", "ONGOING", "OBSOLETE", "INQUESTION"]
        expected_symbols = ["[ ]", "[x]", "[@]", "[~]", "[?]"]
        
        for status, expected_symbol in zip(statuses, expected_symbols):
            task = Task("/test.xit", 1, "Test task", status, 0, [], None)
            result = task_formatter.format_task(task)
            
            text_content = str(result)
            assert expected_symbol in text_content
    
    def test_format_multiline_task(self, task_formatter):
        """Test formatting a task with multiline description."""
        description = "First line\nSecond line\nThird line"
        task = Task("/test.xit", 1, description, "OPEN", 0, [], None)
        
        result = task_formatter.format_task(task)
        
        # Should have proper indentation for continuation lines
        lines = str(result).split('\n')
        assert len(lines) >= 3
        assert "[ ]" in lines[0]
        assert "First line" in lines[0]
    
    def test_format_task_with_line_number(self, task_formatter):
        """Test formatting a task with line number display."""
        task = Task("/test.xit", 42, "Test task", "OPEN", 0, [], None)
        
        result = task_formatter.format_task(task, show_line=True)
        
        text_content = str(result)
        assert "L42" in text_content
    
    def test_format_task_with_tags_and_dates(self, task_formatter):
        """Test formatting a task with tags and due dates."""
        description = "Task with #tag and -> 2025-12-31"
        task = Task("/test.xit", 1, description, "OPEN", 0, ["#tag"], "2025-12-31")
        
        result = task_formatter.format_task(task)
        
        # The formatter should highlight syntax in the description
        text_content = str(result)
        assert "#tag" in text_content
        assert "2025-12-31" in text_content


class TestDescriptionLineFormatting:
    """Test description line formatting with syntax highlighting."""
    
    def test_format_line_with_due_date(self, task_formatter):
        """Test formatting line with due date."""
        line = "Complete task -> 2025-12-31 today"
        
        result = task_formatter._format_description_line(line)
        
        assert isinstance(result, Text)
        # Should highlight the due date
        text_content = str(result)
        assert "2025-12-31" in text_content
    
    def test_format_line_with_tags(self, task_formatter):
        """Test formatting line with tags."""
        line = "Task with #work and #urgent tags"
        
        result = task_formatter._format_description_line(line)
        
        text_content = str(result)
        assert "#work" in text_content
        assert "#urgent" in text_content
    
    def test_format_line_with_priority(self, task_formatter):
        """Test formatting line with priority indicators."""
        line = "!! High priority task"
        
        result = task_formatter._format_description_line(line)
        
        text_content = str(result)
        assert "!!" in text_content
    
    def test_format_line_with_tag_values(self, task_formatter):
        """Test formatting line with tag values."""
        line = "Task #priority=high #category=\"work item\""
        
        result = task_formatter._format_description_line(line)
        
        text_content = str(result)
        assert "#priority=high" in text_content
        assert "#category=\"work item\"" in text_content
    
    def test_format_line_complex(self, task_formatter):
        """Test formatting line with multiple syntax elements."""
        line = "!! Important #work task -> 2025-12-31 #urgent=true"
        
        result = task_formatter._format_description_line(line)
        
        text_content = str(result)
        assert "!!" in text_content
        assert "#work" in text_content
        assert "2025-12-31" in text_content
        assert "#urgent=true" in text_content


class TestFileGrouping:
    """Test task grouping by file."""
    
    def test_group_tasks_by_file(self, task_formatter):
        """Test grouping tasks by file path."""
        tasks = [
            Task("/file1.xit", 1, "Task 1", "OPEN", 0, [], None),
            Task("/file1.xit", 2, "Task 2", "DONE", 0, [], None),
            Task("/file2.xit", 1, "Task 3", "ONGOING", 0, [], None),
            Task("/file1.xit", 3, "Task 4", "OPEN", 0, [], None),
        ]
        
        grouped = task_formatter.group_tasks_by_file(tasks)
        
        assert len(grouped) == 2
        assert "/file1.xit" in grouped
        assert "/file2.xit" in grouped
        assert len(grouped["/file1.xit"]) == 3
        assert len(grouped["/file2.xit"]) == 1
    
    def test_group_tasks_empty_list(self, task_formatter):
        """Test grouping empty task list."""
        grouped = task_formatter.group_tasks_by_file([])
        assert grouped == {}


class TestFileHeaderFormatting:
    """Test file header formatting."""
    
    def test_format_file_header(self, task_formatter):
        """Test formatting file header."""
        with patch('pathlib.Path.cwd') as mock_cwd:
            mock_cwd.return_value = Path("/current")
            
            # Test relative path
            result = task_formatter.format_file_header("/current/subdir/file.xit")
            assert isinstance(result, Text)
            # Should show relative path
            text_content = str(result)
            assert "subdir/file.xit" in text_content or "file.xit" in text_content
    
    def test_format_file_header_absolute_path(self, task_formatter):
        """Test formatting file header with absolute path."""
        # When relative path calculation fails, should show absolute path
        result = task_formatter.format_file_header("/absolute/path/file.xit")
        assert isinstance(result, Text)


class TestDisplayMethods:
    """Test display methods that use console output."""
    
    def test_display_tasks_empty(self, task_formatter):
        """Test displaying empty task list."""
        with patch.object(task_formatter.console, 'print') as mock_print:
            task_formatter.display_tasks([])
            
            # Should print a warning message
            mock_print.assert_called()
            call_args = str(mock_print.call_args)
            assert "No tasks to display" in call_args
    
    def test_display_tasks_with_tasks(self, task_formatter):
        """Test displaying tasks."""
        tasks = [
            Task("/file1.xit", 1, "Task 1", "OPEN", 0, [], None),
            Task("/file1.xit", 2, "Task 2", "DONE", 0, [], None),
        ]
        
        with patch.object(task_formatter.console, 'print') as mock_print:
            task_formatter.display_tasks(tasks)
            
            # Should print file header and tasks
            assert mock_print.call_count > 0
    
    def test_display_tasks_with_line_numbers(self, task_formatter):
        """Test displaying tasks with line numbers."""
        tasks = [Task("/file1.xit", 1, "Task 1", "OPEN", 0, [], None)]
        
        with patch.object(task_formatter.console, 'print') as mock_print:
            task_formatter.display_tasks(tasks, show_line=True)
            
            assert mock_print.call_count > 0
    
    def test_display_summary(self, task_formatter):
        """Test displaying summary."""
        with patch.object(task_formatter.console, 'print') as mock_print:
            task_formatter.display_summary(5, 10)
            
            mock_print.assert_called()
            call_args = str(mock_print.call_args)
            assert "5 of 10" in call_args
    
    def test_display_summary_no_filtering(self, task_formatter):
        """Test displaying summary when no filtering occurred."""
        with patch.object(task_formatter.console, 'print') as mock_print:
            task_formatter.display_summary(10, 10)
            
            # Should not print anything when counts are equal
            mock_print.assert_not_called()
    
    def test_display_count(self, task_formatter):
        """Test displaying task count."""
        with patch.object(task_formatter.console, 'print') as mock_print:
            task_formatter.display_count(42)
            
            mock_print.assert_called()
            call_args = str(mock_print.call_args)
            assert "42 tasks found" in call_args
    
    def test_display_error(self, task_formatter):
        """Test displaying error message."""
        with patch.object(task_formatter.console, 'print') as mock_print:
            task_formatter.display_error("Something went wrong")
            
            mock_print.assert_called()
            call_args = str(mock_print.call_args)
            assert "Something went wrong" in call_args
    
    def test_display_warning(self, task_formatter):
        """Test displaying warning message."""
        with patch.object(task_formatter.console, 'print') as mock_print:
            task_formatter.display_warning("This is a warning")
            
            mock_print.assert_called()
            call_args = str(mock_print.call_args)
            assert "This is a warning" in call_args
    
    def test_display_success(self, task_formatter):
        """Test displaying success message."""
        with patch.object(task_formatter.console, 'print') as mock_print:
            task_formatter.display_success("Operation successful")
            
            mock_print.assert_called()
            call_args = str(mock_print.call_args)
            assert "Operation successful" in call_args


class TestConvenienceFunction:
    """Test the convenience function for backward compatibility."""
    
    def test_format_task_rich_function(self):
        """Test the global format_task_rich function."""
        task = Task("/test.xit", 1, "Test task", "OPEN", 0, [], None)
        
        result = format_task_rich(task)
        
        assert isinstance(result, Text)
        text_content = str(result)
        assert "[ ]" in text_content
        assert "Test task" in text_content
    
    def test_format_task_rich_with_line_number(self):
        """Test the global format_task_rich function with line numbers."""
        task = Task("/test.xit", 42, "Test task", "OPEN", 0, [], None)
        
        result = format_task_rich(task, show_line=True)
        
        text_content = str(result)
        assert "L42" in text_content


class TestFormatterEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_format_task_empty_description(self, task_formatter):
        """Test formatting task with empty description."""
        task = Task("/test.xit", 1, "", "OPEN", 0, [], None)
        
        result = task_formatter.format_task(task)
        
        text_content = str(result)
        assert "[ ]" in text_content
    
    def test_format_task_unicode_description(self, task_formatter):
        """Test formatting task with Unicode characters."""
        task = Task("/test.xit", 1, "📋 Unicode task 🚀", "OPEN", 0, [], None)
        
        result = task_formatter.format_task(task)
        
        text_content = str(result)
        assert "📋" in text_content
        assert "🚀" in text_content
    
    def test_format_task_very_long_description(self, task_formatter):
        """Test formatting task with very long description."""
        long_description = "Very " * 100 + "long task description"
        task = Task("/test.xit", 1, long_description, "OPEN", 0, [], None)
        
        # Should not crash
        result = task_formatter.format_task(task)
        assert isinstance(result, Text)
    
    def test_format_line_with_malformed_tags(self, task_formatter):
        """Test formatting line with malformed tags."""
        line = "Task with #incomplete-tag= and #=no-name"
        
        # Should not crash
        result = task_formatter._format_description_line(line)
        assert isinstance(result, Text)
    
    def test_format_line_with_malformed_dates(self, task_formatter):
        """Test formatting line with malformed dates."""
        line = "Task with -> invalid-date and ->no-space"
        
        # Should not crash
        result = task_formatter._format_description_line(line)
        assert isinstance(result, Text)


class TestFormatterWithRealContent:
    """Test formatter with realistic content."""
    
    def test_format_complex_task(self, task_formatter):
        """Test formatting a complex task with all features."""
        description = """Complex multi-line task ...
    with continuation lines
    containing #tags and #priority=high
    and due date -> 2025-12-31"""
        
        task = Task(
            "/project/tasks.xit", 
            15, 
            description, 
            "ONGOING", 
            3, 
            ["#work", "#project", "#priority=high"], 
            "2025-12-31"
        )
        
        result = task_formatter.format_task(task, show_line=True)
        
        text_content = str(result)
        assert "[@]" in text_content  # ONGOING status
        assert "!!!" in text_content  # Priority 3
        assert "Complex multi-line task" in text_content
        assert "L15" in text_content  # Line number
    
    def test_format_tasks_mixed_files(self, task_formatter):
        """Test formatting tasks from multiple files."""
        tasks = [
            Task("/work/tasks.xit", 1, "Work task", "OPEN", 1, ["#work"], None),
            Task("/work/tasks.xit", 5, "Another work task", "DONE", 0, [], None),
            Task("/personal/todo.md", 3, "Personal task", "ONGOING", 2, ["#personal"], "2025-12-31"),
        ]
        
        with patch.object(task_formatter.console, 'print') as mock_print:
            task_formatter.display_tasks(tasks, show_line=True)
            
            # Should have printed multiple times (headers + tasks)
            assert mock_print.call_count > 3


class TestFormatterIntegration:
    """Test formatter integration with other components."""
    
    def test_formatter_with_date_parser_integration(self, task_formatter):
        """Test that formatter properly integrates with date parser."""
        # The formatter should use its date_parser for date normalization
        assert hasattr(task_formatter, 'date_parser')
        assert hasattr(task_formatter.date_parser, 'current_date')
    
    def test_formatter_preserves_task_data(self, task_formatter):
        """Test that formatting doesn't modify original task data."""
        original_task = Task("/test.xit", 1, "Original task", "OPEN", 1, ["#tag"], "2025-12-31")
        
        # Store original values
        original_desc = original_task.description
        original_status = original_task.status
        original_priority = original_task.priority
        original_tags = original_task.tags.copy()
        original_due_date = original_task.due_date
        
        # Format the task
        task_formatter.format_task(original_task)
        
        # Verify original data is unchanged
        assert original_task.description == original_desc
        assert original_task.status == original_status
        assert original_task.priority == original_priority
        assert original_task.tags == original_tags
        assert original_task.due_date == original_due_date