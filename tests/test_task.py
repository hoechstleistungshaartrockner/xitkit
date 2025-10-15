"""Tests for the Task class."""

import pytest
from pathlib import Path

from xitflow.task import Task


class TestTaskBasics:
    """Test basic Task functionality."""
    
    def test_task_creation(self):
        """Test creating a task with all parameters."""
        task = Task(
            file="/test/file.xit",
            line_number=10,
            description="Test task",
            status="OPEN",
            priority=2,
            tags=["#work", "#urgent"],
            due_date="2025-12-31"
        )
        
        assert task.file == "/test/file.xit"
        assert task.line_number == 10
        assert task.description == "Test task"
        assert task.status == "OPEN"
        assert task.priority == 2
        assert task.tags == ["#work", "#urgent"]
        assert task.due_date == "2025-12-31"
    
    def test_task_creation_minimal(self):
        """Test creating a task with minimal parameters."""
        task = Task(
            file="/test/file.xit",
            line_number=1,
            description="Simple task",
            status="OPEN",
            priority=0,
            tags=[],
            due_date=None
        )
        
        assert task.file == "/test/file.xit"
        assert task.line_number == 1
        assert task.description == "Simple task"
        assert task.status == "OPEN"
        assert task.priority == 0
        assert task.tags == []
        assert task.due_date is None


class TestTaskProperties:
    """Test Task property methods."""
    
    def test_location_property(self):
        """Test location getter and setter."""
        task = Task("/test/file.xit", 5, "Test", "OPEN", 0, [], None)
        
        # Test getter
        assert task.location == ("/test/file.xit", 5)
        
        # Test setter
        task.location = ("/new/file.xit", 10)
        assert task.file == "/new/file.xit"
        assert task.line_number == 10
    
    def test_filename_property(self):
        """Test filename extraction from file path."""
        task = Task("/path/to/file.xit", 1, "Test", "OPEN", 0, [], None)
        assert task.filename == "file.xit"
        
        task = Task("simple.md", 1, "Test", "OPEN", 0, [], None)
        assert task.filename == "simple.md"
    
    def test_relative_path_property(self, temp_dir):
        """Test relative path calculation."""
        import os
        # Create a test file in temp directory
        test_file = temp_dir / "test.xit"
        test_file.write_text("[ ] Test")
        
        # Change to temp directory so relative path works
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            task = Task(str(test_file), 1, "Test", "OPEN", 0, [], None)
            relative = task.relative_path
            
            # Should be relative path when working directory is the temp dir
            assert not Path(relative).is_absolute()
            assert "test.xit" in relative
        finally:
            os.chdir(original_cwd)
    
    def test_status_symbol_property(self):
        """Test status symbol mapping."""
        status_tests = [
            ("OPEN", "[ ]"),
            ("DONE", "[x]"),
            ("ONGOING", "[@]"),
            ("OBSOLETE", "[~]"),
            ("INQUESTION", "[?]"),
        ]
        
        for status, expected_symbol in status_tests:
            task = Task("/test.xit", 1, "Test", status, 0, [], None)
            assert task.status_symbol == expected_symbol
    
    def test_has_priority_property(self):
        """Test priority detection."""
        task_no_priority = Task("/test.xit", 1, "Test", "OPEN", 0, [], None)
        assert not task_no_priority.has_priority
        
        task_with_priority = Task("/test.xit", 1, "Test", "OPEN", 3, [], None)
        assert task_with_priority.has_priority
    
    def test_has_due_date_property(self):
        """Test due date detection."""
        task_no_due = Task("/test.xit", 1, "Test", "OPEN", 0, [], None)
        assert not task_no_due.has_due_date
        
        task_with_due = Task("/test.xit", 1, "Test", "OPEN", 0, [], "2025-12-31")
        assert task_with_due.has_due_date
    
    def test_has_tags_property(self):
        """Test tag detection."""
        task_no_tags = Task("/test.xit", 1, "Test", "OPEN", 0, [], None)
        assert not task_no_tags.has_tags
        
        task_with_tags = Task("/test.xit", 1, "Test", "OPEN", 0, ["#work"], None)
        assert task_with_tags.has_tags
    
    def test_priority_indicator_property(self):
        """Test priority indicator formatting."""
        task_no_priority = Task("/test.xit", 1, "Test", "OPEN", 0, [], None)
        assert task_no_priority.priority_indicator == ""
        
        task_priority_1 = Task("/test.xit", 1, "Test", "OPEN", 1, [], None)
        assert task_priority_1.priority_indicator == "!"
        
        task_priority_3 = Task("/test.xit", 1, "Test", "OPEN", 3, [], None)
        assert task_priority_3.priority_indicator == "!!!"


class TestTaskMethods:
    """Test Task methods."""
    
    def test_set_status_valid(self):
        """Test setting valid statuses."""
        task = Task("/test.xit", 1, "Test", "OPEN", 0, [], None)
        
        valid_statuses = ["OPEN", "DONE", "ONGOING", "OBSOLETE", "INQUESTION"]
        for status in valid_statuses:
            task.set_status(status)
            assert task.status == status
    
    def test_set_status_invalid(self):
        """Test setting invalid status raises ValueError."""
        task = Task("/test.xit", 1, "Test", "OPEN", 0, [], None)
        
        with pytest.raises(ValueError, match="Invalid status"):
            task.set_status("INVALID")
        
        with pytest.raises(ValueError, match="Invalid status"):
            task.set_status("done")  # Case sensitive
    
    def test_set_priority_valid(self):
        """Test setting valid priorities."""
        task = Task("/test.xit", 1, "Test", "OPEN", 0, [], None)
        
        valid_priorities = [0, 1, 5, 10]
        for priority in valid_priorities:
            task.set_priority(priority)
            assert task.priority == priority
    
    def test_set_priority_invalid(self):
        """Test setting invalid priority raises ValueError."""
        task = Task("/test.xit", 1, "Test", "OPEN", 0, [], None)
        
        with pytest.raises(ValueError, match="Priority must be >= 0"):
            task.set_priority(-1)
    
    def test_add_tag(self):
        """Test adding tags."""
        task = Task("/test.xit", 1, "Test", "OPEN", 0, [], None)
        
        # Add tag without # prefix
        task.add_tag("work")
        assert "#work" in task.tags
        
        # Add tag with # prefix
        task.add_tag("#urgent")
        assert "#urgent" in task.tags
        
        # Adding duplicate tag should not create duplicates
        task.add_tag("work")
        assert task.tags.count("#work") == 1
    
    def test_remove_tag(self):
        """Test removing tags."""
        task = Task("/test.xit", 1, "Test", "OPEN", 0, ["#work", "#urgent"], None)
        
        # Remove tag with # prefix
        result = task.remove_tag("#work")
        assert result is True
        assert "#work" not in task.tags
        
        # Remove tag without # prefix
        result = task.remove_tag("urgent")
        assert result is True
        assert "#urgent" not in task.tags
        
        # Try to remove non-existent tag
        result = task.remove_tag("nonexistent")
        assert result is False
    
    def test_has_tag(self):
        """Test checking for tag existence."""
        task = Task("/test.xit", 1, "Test", "OPEN", 0, ["#work", "#urgent=high"], None)
        
        # Check existing tags
        assert task.has_tag("work")
        assert task.has_tag("#work")
        assert task.has_tag("urgent")  # Should match tag with value
        assert task.has_tag("#urgent")
        
        # Check non-existing tags
        assert not task.has_tag("personal")
        assert not task.has_tag("#personal")
    
    def test_set_due_date(self):
        """Test setting due date."""
        task = Task("/test.xit", 1, "Test", "OPEN", 0, [], None)
        
        task.set_due_date("2025-12-31")
        assert task.due_date == "2025-12-31"
        
        task.set_due_date(None)
        assert task.due_date is None
    
    def test_clear_due_date(self):
        """Test clearing due date."""
        task = Task("/test.xit", 1, "Test", "OPEN", 0, [], "2025-12-31")
        
        task.clear_due_date()
        assert task.due_date is None
    
    def test_is_overdue(self):
        """Test overdue detection."""
        # Task with past due date
        overdue_task = Task("/test.xit", 1, "Test", "OPEN", 0, [], "2025-01-01")
        assert overdue_task.is_overdue("2025-12-31")
        
        # Task with future due date
        future_task = Task("/test.xit", 1, "Test", "OPEN", 0, [], "2025-12-31")
        assert not future_task.is_overdue("2025-01-01")
        
        # Task with no due date
        no_due_task = Task("/test.xit", 1, "Test", "OPEN", 0, [], None)
        assert not no_due_task.is_overdue("2025-12-31")
    
    def test_copy(self):
        """Test creating a copy of a task."""
        original = Task(
            "/test.xit", 1, "Test", "OPEN", 2, ["#work"], "2025-12-31"
        )
        
        copy_task = original.copy()
        
        # Should be equal but not the same object
        assert copy_task is not original
        assert copy_task.file == original.file
        assert copy_task.line_number == original.line_number
        assert copy_task.description == original.description
        assert copy_task.status == original.status
        assert copy_task.priority == original.priority
        assert copy_task.tags == original.tags
        assert copy_task.due_date == original.due_date
        
        # Modifying copy should not affect original
        copy_task.tags.append("#new")
        assert "#new" not in original.tags


class TestTaskStringRepresentation:
    """Test Task string representation methods."""
    
    def test_str_method(self):
        """Test __str__ method."""
        task = Task("/test.xit", 1, "Test task", "OPEN", 0, [], None)
        assert str(task) == "[ ] Test task"
        
        task_done = Task("/test.xit", 1, "Done task", "DONE", 0, [], None)
        assert str(task_done) == "[x] Done task"
    
    def test_repr_method(self):
        """Test __repr__ method."""
        task = Task("/test.xit", 1, "Test task description", "OPEN", 1, ["#work"], "2025-12-31")
        repr_str = repr(task)
        
        assert "Task(" in repr_str
        assert "file='/test.xit'" in repr_str
        assert "line=1" in repr_str
        assert "status='OPEN'" in repr_str
        assert "priority=1" in repr_str
        assert "tags=['#work']" in repr_str
        assert "due_date='2025-12-31'" in repr_str
    
    def test_to_terminal_line_basic(self):
        """Test basic terminal line formatting."""
        task = Task("/test.xit", 1, "Simple task", "OPEN", 0, [], None)
        
        # With location info
        line = task.to_terminal_line(show_file=True, show_line=True)
        assert "[ ] Simple task" in line
        assert "[/test.xit:L1]" in line  # Expect full path since it can't be made relative
        
        # Without location info
        line = task.to_terminal_line(show_file=False, show_line=False)
        assert line == "[ ] Simple task"
    
    def test_to_terminal_line_multiline(self):
        """Test multiline task terminal formatting."""
        task = Task("/test.xit", 1, "First line\nSecond line\nThird line", "OPEN", 0, [], None)
        
        line = task.to_terminal_line(show_file=False, show_line=False)
        lines = line.split('\n')
        
        assert lines[0] == "[ ] First line"
        assert lines[1] == "    Second line"
        assert lines[2] == "    Third line"
    
    def test_to_checkbox_format(self):
        """Test converting back to checkbox format."""
        # Basic task
        task = Task("/test.xit", 1, "Simple task", "OPEN", 0, [], None)
        assert task.to_checkbox_format() == "[ ] Simple task"
        
        # Task with priority
        task_priority = Task("/test.xit", 1, "Important task", "OPEN", 2, [], None)
        assert task_priority.to_checkbox_format() == "[ ] !! Important task"
        
        # Different statuses
        status_tests = [
            ("OPEN", "[ ]"),
            ("DONE", "[x]"),
            ("ONGOING", "[@]"),
            ("OBSOLETE", "[~]"),
            ("INQUESTION", "[?]"),
        ]
        
        for status, expected_prefix in status_tests:
            task = Task("/test.xit", 1, "Test task", status, 0, [], None)
            assert task.to_checkbox_format() == f"{expected_prefix} Test task"


class TestTaskEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_description(self):
        """Test task with empty description."""
        task = Task("/test.xit", 1, "", "OPEN", 0, [], None)
        assert task.description == ""
        assert str(task) == "[ ] "
    
    def test_whitespace_description(self):
        """Test task with whitespace-only description."""
        task = Task("/test.xit", 1, "   ", "OPEN", 0, [], None)
        assert task.description == "   "
        assert str(task) == "[ ]    "
    
    def test_unicode_description(self):
        """Test task with Unicode characters."""
        task = Task("/test.xit", 1, "📋 Unicode task 🚀", "OPEN", 0, [], None)
        assert task.description == "📋 Unicode task 🚀"
        assert str(task) == "[ ] 📋 Unicode task 🚀"
    
    def test_high_priority(self):
        """Test task with very high priority."""
        task = Task("/test.xit", 1, "Very important", "OPEN", 10, [], None)
        assert task.priority == 10
        assert task.priority_indicator == "!" * 10
    
    def test_complex_tags(self):
        """Test task with complex tag scenarios."""
        task = Task("/test.xit", 1, "Test", "OPEN", 0, [
            "#simple",
            "#with-dashes",
            "#with_underscores",
            "#with=value",
            "#quoted='value with spaces'",
            "#unicode=日本語"
        ], None)
        
        assert task.has_tag("simple")
        assert task.has_tag("with-dashes")
        assert task.has_tag("with_underscores")
        assert task.has_tag("with")  # Should match tag with value
        assert task.has_tag("quoted")
        assert task.has_tag("unicode")
    
    def test_invalid_date_comparison(self):
        """Test overdue check with invalid date formats."""
        task = Task("/test.xit", 1, "Test", "OPEN", 0, [], "invalid-date")
        
        # Should not crash, should return False for invalid dates
        assert not task.is_overdue("2025-12-31")