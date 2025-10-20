"""Reorganized tests for the Task class with redundancies removed."""

import pytest
from pathlib import Path

from xit.task import Task
from xit.tags import Tag
from xit.status import Status, StatusType
from xit.description import Description
from xit.priority import Priority


class TestTaskCreation:
    """Test task creation and instantiation."""

    def test_invalid_creation(self):
        """Test creating a task with no parameters raises TypeError."""
        with pytest.raises(TypeError):
            Task()

    def test_minimal_creation(self):
        """Test creating a task with minimal parameters."""
        task = Task("Empty task")
        
        assert task.file is None
        assert task.line_number is None
        assert task.description_text == "Empty task"
        assert task.status == Status(StatusType.OPEN)
        assert task.priority == Priority()
        assert task.tags == []
        assert task.due_date is None
        assert task.id == 0
        assert str(task) == "[ ] Empty task"

    @pytest.mark.parametrize("status_input,expected_status,expected_str", [
        # String statuses
        ("OPEN", Status(StatusType.OPEN), "[ ] Test task"),
        ("DONE", Status(StatusType.CHECKED), "[x] Test task"),
        ("ONGOING", Status(StatusType.ONGOING), "[@] Test task"),
        ("OBSOLETE", Status(StatusType.OBSOLETE), "[~] Test task"),
        ("INQUESTION", Status(StatusType.IN_QUESTION), "[?] Test task"),
        # StatusType enum
        (StatusType.CHECKED, Status(StatusType.CHECKED), "[x] Test task"),
        (StatusType.IN_QUESTION, Status(StatusType.IN_QUESTION), "[?] Test task"),
        # Status objects
        (Status(StatusType.ONGOING), Status(StatusType.ONGOING), "[@] Test task"),
    ])
    def test_creation_with_status(self, status_input, expected_status, expected_str):
        """Test creating a task with various status inputs."""
        task = Task("Test task", status=status_input)
        assert task.status == expected_status
        assert str(task) == expected_str

    @pytest.mark.parametrize("priority_input,expected_level,expected_str", [
        # Integer priorities
        (0, 0, "[ ] Test task"),
        (1, 1, "[ ] ! Test task"),
        (3, 3, "[ ] !!! Test task"),
        # Priority objects
        (Priority(level=2, leading_dots=1), 2, "[ ] .!! Test task"),
        (Priority(level=1, trailing_dots=2), 1, "[ ] !.. Test task"),
    ])
    def test_creation_with_priority(self, priority_input, expected_level, expected_str):
        """Test creating a task with various priority inputs."""
        task = Task("Test task", priority=priority_input)
        assert task.priority.level == expected_level
        assert str(task) == expected_str

    def test_creation_with_tags(self):
        """Test creating a task with tags."""
        # Tag objects
        tags = [Tag("work"), Tag("urgent", "high")]
        task = Task("Task with tags", tags=tags)
        
        assert len(task.tags) == 2
        assert task.tags[0] == Tag("work")
        assert task.tags[1] == Tag("urgent", "high")
        assert str(task) == "[ ] Task with tags #work #urgent=high"

        # Mixed tag types
        mixed_tags = ["project", Tag("priority", "high"), "urgent"]
        task2 = Task("Mixed tags", tags=mixed_tags)
        assert len(task2.tags) == 3
        assert task2.tags[0] == Tag("project")
        assert task2.tags[1] == Tag("priority", "high")
        assert task2.tags[2] == Tag("urgent")

    def test_creation_with_due_date(self):
        """Test creating a task with due date."""
        task = Task("Task with due date", due_date="2025-12-31")
        assert task.has_due_date
        assert task.due_date_string == "2025-12-31"
        assert "-> 2025-12-31" in str(task)

    def test_complex_creation(self):
        """Test creating a task with all parameters."""
        task = Task(
            "Complex task",
            file="/test/file.xit",
            line_number=42,
            status=StatusType.IN_QUESTION,
            priority=Priority(level=2, leading_dots=1),
            tags=[Tag("work"), Tag("review", "needed")],
            due_date="2025-11-15",
            id=123
        )
        
        assert task.description_text == "Complex task"
        assert task.file == "/test/file.xit"
        assert task.line_number == 42
        assert task.status == Status(StatusType.IN_QUESTION)
        assert task.priority.level == 2
        assert len(task.tags) == 2
        assert task.due_date_string == "2025-11-15"
        assert task.id == 123


class TestTaskProperties:
    """Test task properties and attribute access."""

    def test_location_property(self):
        """Test location getter and setter."""
        task = Task("Test", file="/test/file.xit", line_number=5)
        
        # Test getter
        assert task.location == ("/test/file.xit", 5)
        
        # Test setter
        task.location = ("/new/file.xit", 10)
        assert task.file == "/new/file.xit"
        assert task.line_number == 10

    def test_filename_property(self):
        """Test filename extraction from file path."""
        task = Task("Test", file="/path/to/file.xit")
        assert task.filename == "file.xit"
        
        # Test with None file
        task_no_file = Task("Test", file=None)
        assert task_no_file.filename is None

    def test_has_properties(self):
        """Test boolean properties for detecting features."""
        # Task with no special features
        basic_task = Task("Basic")
        assert not basic_task.has_priority
        assert not basic_task.has_due_date
        assert not basic_task.has_tags

        # Task with all features
        full_task = Task("Full", priority=2, tags=[Tag("work")], due_date="2025-12-31")
        assert full_task.has_priority
        assert full_task.has_due_date
        assert full_task.has_tags


class TestTaskModification:
    """Test task modification methods."""

    def test_status_modification(self):
        """Test setting status with various input types."""
        task = Task("Test")
        
        # String status
        task.set_status("DONE")
        assert task.status == Status(StatusType.CHECKED)
        
        # StatusType enum
        task.set_status(StatusType.ONGOING)
        assert task.status == Status(StatusType.ONGOING)
        
        # Status object
        new_status = Status(StatusType.OBSOLETE)
        task.set_status(new_status)
        assert task.status == new_status
        
        # Checkbox string format
        task.set_status("[?]")
        assert task.status == Status(StatusType.IN_QUESTION)
        
        # Single character indicator
        task.set_status("~")
        assert task.status == Status(StatusType.OBSOLETE)

    def test_status_modification_invalid(self):
        """Test setting invalid status raises ValueError."""
        task = Task("Test")
        
        with pytest.raises(ValueError, match="Invalid status"):
            task.set_status("INVALID")
        
        with pytest.raises(ValueError, match="Invalid status type"):
            task.set_status(123)

    def test_priority_modification(self):
        """Test setting priority with various input types."""
        task = Task("Test")
        
        # Integer priority
        task.set_priority(5)
        assert task.priority.level == 5
        
        # Priority object
        priority_obj = Priority(level=3, leading_dots=2)
        task.set_priority(priority_obj)
        assert task.priority == priority_obj
        
        # Set to zero
        task.set_priority(0)
        assert not task.has_priority

    def test_priority_modification_invalid(self):
        """Test setting invalid priority raises ValueError."""
        task = Task("Test")
        
        with pytest.raises(ValueError, match="Priority must be >= 0"):
            task.set_priority(-1)
        
        with pytest.raises(ValueError, match="Invalid priority type"):
            task.set_priority("high")

    def test_tag_management(self):
        """Test comprehensive tag management."""
        task = Task("Test")
        
        # Add tags
        task.add_tag_by_name("work")
        task.add_tag_by_name("#urgent")  # With # prefix
        task.add_tag_by_name("priority", "high")  # With value
        tag_obj = Tag("project", "website")
        task.add_tag(tag_obj)
        
        assert len(task.tags) == 4
        assert task.has_tag_by_name("work")
        assert task.has_tag_by_name("urgent")
        assert task.has_tag(tag_obj)
        
        # Remove tags
        assert task.remove_tag_by_name("work")
        assert not task.has_tag_by_name("work")
        
        assert task.remove_tag(tag_obj)
        assert not task.has_tag(tag_obj)
        
        # Try to remove non-existent tag
        assert not task.remove_tag_by_name("nonexistent")

    def test_due_date_management(self):
        """Test due date setting and clearing."""
        task = Task("Test")
        
        # Set due date
        task.set_due_date("2025-12-31")
        assert task.has_due_date
        assert task.due_date_string == "2025-12-31"
        
        # Clear due date
        task.clear_due_date()
        assert not task.has_due_date
        assert task.due_date is None
        
        # Set to None
        task.set_due_date("2025-06-15")
        task.set_due_date(None)
        assert not task.has_due_date

    def test_overdue_detection(self):
        """Test overdue detection scenarios."""
        # Past due date
        overdue_task = Task("Test", due_date="2025-01-01")
        assert overdue_task.is_overdue("2025-01-02")
        
        # Future due date
        future_task = Task("Test", due_date="2025-12-31")
        assert not future_task.is_overdue("2025-12-30")
        
        # No due date
        no_due_task = Task("Test")
        assert not no_due_task.is_overdue("2025-12-31")


class TestTaskFormatting:
    """Test task formatting and string representations."""

    def test_string_representation(self):
        """Test __str__ method produces checkbox format."""
        # Basic task
        task = Task("Simple task")
        assert str(task) == "[ ] Simple task"
        
        # Task with all features
        complex_task = Task(
            "Complex task",
            status=StatusType.IN_QUESTION,
            priority=Priority(level=2, leading_dots=1),
            tags=[Tag("work"), Tag("priority", "high")],
            due_date="2025-12-31"
        )
        expected = "[?] .!! Complex task #work #priority=high -> 2025-12-31"
        assert str(complex_task) == expected

    def test_repr_representation(self):
        """Test __repr__ method for debugging."""
        task = Task("Test task", file="/test.xit", line_number=1, priority=1, tags=[Tag("work")])
        repr_str = repr(task)
        
        assert "Task(" in repr_str
        assert "file='/test.xit'" in repr_str
        assert "line=1" in repr_str
        assert "priority=!" in repr_str

    def test_terminal_line_formatting(self):
        """Test terminal line formatting with options."""
        task = Task("Test task", file="/test.xit", line_number=10, priority=2)
        
        # With location info
        with_location = task.to_terminal_line(show_file=True, show_line=True)
        assert "[ ] !! Test task" in with_location
        assert "[/test.xit:L10]" in with_location
        
        # Without location info
        without_location = task.to_terminal_line(show_file=False, show_line=False)
        assert without_location == "[ ] !! Test task"

    def test_multiline_description_formatting(self):
        """Test formatting of multiline descriptions."""
        multiline_desc = "First line\nSecond line\nThird line"
        task = Task(multiline_desc)
        
        terminal_line = task.to_terminal_line(show_file=False, show_line=False)
        lines = terminal_line.split('\n')
        
        assert len(lines) == 3
        assert lines[0] == "[ ] First line"
        assert lines[1] == "    Second line"
        assert lines[2] == "    Third line"

    def test_checkbox_format(self):
        """Test converting back to checkbox format."""
        task = Task("Task", status=StatusType.CHECKED, priority=2, tags=[Tag("work")], due_date="2025-12-31")
        
        checkbox = task.to_checkbox_format()
        str_repr = str(task)
        
        # Should be identical
        assert checkbox == str_repr
        assert "[x] !! Task #work -> 2025-12-31" == checkbox


class TestTaskCopyAndEquality:
    """Test task copying and comparison."""

    def test_deep_copy(self):
        """Test that copied tasks are independent."""
        original = Task(
            "Original",
            file="/test.xit",
            line_number=5,
            status=StatusType.ONGOING,
            priority=Priority(level=2, leading_dots=1),
            tags=[Tag("work"), Tag("urgent", "high")],
            due_date="2025-12-31",
            id=42
        )
        
        copy_task = original.copy()
        
        # Verify copy is identical but separate
        assert copy_task is not original
        assert copy_task.description_text == original.description_text
        assert copy_task.status == original.status
        assert copy_task.priority == original.priority
        assert copy_task.tags == original.tags
        assert copy_task.due_date_string == original.due_date_string
        
        # Modify copy - original should remain unchanged
        copy_task.set_status(StatusType.CHECKED)
        copy_task.add_tag_by_name("new_tag")
        
        assert original.status == Status(StatusType.ONGOING)
        assert not original.has_tag_by_name("new_tag")


class TestTaskEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.parametrize("description,expected_str", [
        ("", "[ ] "),
        # ("   ", "[ ]    "),
        ("📋 Unicode task 🚀", "[ ] 📋 Unicode task 🚀"),
    ])
    def test_description_edge_cases(self, description, expected_str):
        """Test tasks with various description edge cases."""
        task = Task(description)
        assert task.description_text == description
        assert str(task) == expected_str

    def test_high_priority(self):
        """Test task with very high priority."""
        task = Task("Important", priority=10)
        assert task.priority.level == 10
        assert task.priority_indicator == "!" * 10

    def test_complex_tags(self):
        """Test task with complex tag scenarios."""
        tags = [
            Tag("simple"),
            Tag("with-dashes"),
            Tag("with_underscores"),
            Tag("with", "value"),
            Tag("quoted", "value with spaces"),
            Tag("unicode", "日本語")
        ]
        task = Task("Test", tags=tags)
        
        for tag in tags:
            assert task.has_tag_by_name(tag.name)

    def test_error_recovery(self):
        """Test that tasks can recover from invalid operations."""
        task = Task("Test")
        
        # Try invalid status - should not crash
        try:
            task.set_status("invalid")
        except ValueError:
            pass
        
        # Task should still be functional
        assert task.status == Status(StatusType.OPEN)
        task.set_status(StatusType.CHECKED)
        assert task.status == Status(StatusType.CHECKED)

    def test_invalid_date_comparison(self):
        """Test overdue check with invalid date formats."""
        task = Task("Test", due_date="invalid-date")
        # Should not crash, should return False for invalid dates
        assert not task.is_overdue("2025-12-31")

    def test_none_file_handling(self):
        """Test handling of None file paths."""
        task = Task("Test", file=None)
        assert task.filename is None
        assert task.location == (None, None)
        
        # Should not crash when formatting
        terminal_output = task.to_terminal_line()
        assert "Test" in terminal_output

    def test_repr_with_long_description(self):
        """Test repr method with very long descriptions."""
        long_desc = "This is a very long description " * 10
        task = Task(long_desc)
        
        repr_str = repr(task)
        assert "Task(" in repr_str
        assert "..." in repr_str  # Should be truncated
        assert len(repr_str) < len(long_desc) + 100


class TestTaskIntegration:
    """Test integration scenarios and real-world usage."""

    def test_task_lifecycle(self):
        """Test a complete task lifecycle."""
        # Create task
        task = Task("Implement feature")
        assert task.status.is_open
        
        # Add metadata
        task.add_tag_by_name("development")
        task.add_tag_by_name("priority", "high")
        task.set_due_date("2025-12-31")
        task.set_priority(2)
        
        # Start work
        task.set_status(StatusType.ONGOING)
        assert task.status.is_ongoing
        
        # Complete work
        task.set_status(StatusType.CHECKED)
        assert task.status.is_complete
        
        # Verify final state
        assert task.has_priority
        assert task.has_tags
        assert task.has_due_date
        assert len(task.tags) == 2

    def test_file_location_workflow(self):
        """Test workflow with file locations."""
        # Create task with location
        task = Task("Fix bug", file="/project/todo.xit", line_number=15)
        
        # Move to different file
        task.location = ("/project/backlog.xit", 5)
        assert task.filename == "backlog.xit"
        
        # Format for display
        display = task.to_terminal_line()
        assert "backlog.xit" in display
        assert "L5" in display

    def test_tag_filtering_workflow(self):
        """Test tag-based filtering workflow."""
        tasks = [
            Task("Task 1", tags=[Tag("work"), Tag("urgent")]),
            Task("Task 2", tags=[Tag("personal")]),
            Task("Task 3", tags=[Tag("work"), Tag("priority", "low")]),
        ]
        
        # Filter work tasks
        work_tasks = [t for t in tasks if t.has_tag_by_name("work")]
        assert len(work_tasks) == 2
        
        # Filter urgent tasks
        urgent_tasks = [t for t in tasks if t.has_tag_by_name("urgent")]
        assert len(urgent_tasks) == 1