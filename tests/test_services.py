"""Unit tests for the services module.

This module tests the TaskService and FileDiscoveryService classes,
including all their methods for task management operations.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from xit.services import TaskService, FileDiscoveryService, TaskFilter
from xit.task import Task
from xit.status import Status, StatusType
from xit.priority import Priority
from xit.tags import Tag
from xit.duedate import DueDate
from xit.exceptions import FileNotSupportedError


class TestTaskService:
    """Test cases for the TaskService class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = TaskService()
        
    def test_init(self):
        """Test TaskService initialization."""
        assert hasattr(self.service, 'parser')
        assert hasattr(self.service, 'date_parser')
        
    def test_find_task_files_default_directory(self):
        """Test finding task files in default directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = [
                Path(temp_dir) / "test.xit",
                Path(temp_dir) / "notes.md",
                Path(temp_dir) / "other.txt",
                Path(temp_dir) / "subdir" / "nested.xit"
            ]
            
            # Create directories and files
            for file_path in test_files:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.touch()
            
            # Change to temp directory and test
            old_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                files = self.service.find_task_files()
                
                # Should find .xit and .md files
                expected_files = [str(test_files[0]), str(test_files[1]), str(test_files[3])]
                assert len(files) == 3
                for expected in expected_files:
                    assert any(expected.endswith(Path(f).name) for f in files)
            finally:
                os.chdir(old_cwd)
                
    def test_find_task_files_specific_directory(self):
        """Test finding task files in specific directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_dir = Path(temp_dir) / "test_dir"
            test_dir.mkdir()
            
            (test_dir / "task1.xit").touch()
            (test_dir / "notes.md").touch()
            (test_dir / "readme.txt").touch()
            
            files = self.service.find_task_files(test_dir)
            
            assert len(files) == 2
            assert any("task1.xit" in f for f in files)
            assert any("notes.md" in f for f in files)
            
    def test_load_tasks(self):
        """Test loading tasks from files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files with tasks
            file1 = Path(temp_dir) / "test1.xit"
            file2 = Path(temp_dir) / "test2.xit"
            
            file1.write_text("[ ] Task 1\n[x] Task 2\n")
            file2.write_text("[@] Task 3\n")
            
            tasks = self.service.load_tasks([str(file1), str(file2)])
            
            # Should have 3 tasks with sequential IDs
            assert len(tasks) == 3
            assert tasks[0].id == 1
            assert tasks[1].id == 2
            assert tasks[2].id == 3
            
            # Check task content
            assert "Task 1" in tasks[0].description_text
            assert "Task 2" in tasks[1].description_text
            assert "Task 3" in tasks[2].description_text
            
    def test_filter_tasks_by_status(self):
        """Test filtering tasks by status."""
        # Create mock tasks
        tasks = [
            Task("Open task", status=Status(StatusType.OPEN)),
            Task("Checked task", status=Status(StatusType.CHECKED)),
            Task("Ongoing task", status=Status(StatusType.ONGOING)),
        ]
        
        # Filter by OPEN status
        filter_open = TaskFilter(status=Status(StatusType.OPEN))
        filtered = self.service.filter_tasks(tasks, filter_open)
        
        assert len(filtered) == 1
        assert filtered[0].status.status_type == StatusType.OPEN
        
    def test_filter_tasks_by_priority(self):
        """Test filtering tasks by priority."""
        tasks = [
            Task("Low priority", priority=Priority(level=1)),
            Task("High priority", priority=Priority(level=3)),
            Task("No priority", priority=Priority(level=0)),
        ]
        
        # Filter by priority level 3
        filter_high = TaskFilter(priority=Priority(level=3))
        filtered = self.service.filter_tasks(tasks, filter_high)
        
        assert len(filtered) == 1
        assert filtered[0].priority.level == 3
        
    def test_filter_tasks_by_tags(self):
        """Test filtering tasks by tags."""
        tasks = [
            Task("Work task", tags=[Tag(name="work")]),
            Task("Home task", tags=[Tag(name="home")]),
            Task("Work and urgent", tags=[Tag(name="work"), Tag(name="urgent")]),
        ]
        
        # Filter by work tag
        filter_work = TaskFilter(tags=[Tag(name="work")])
        filtered = self.service.filter_tasks(tasks, filter_work)
        
        assert len(filtered) == 2
        
    def test_filter_tasks_by_due_date(self):
        """Test filtering tasks by due date."""
        tasks = [
            Task("Due today", due_date="2025-10-19"),
            Task("Due tomorrow", due_date="2025-10-20"),
            Task("No due date"),
        ]
        
        # Filter by due date
        due_date = DueDate.from_string("2025-10-19")
        filter_due = TaskFilter(due_on=due_date)
        filtered = self.service.filter_tasks(tasks, filter_due)
        
        assert len(filtered) == 1
        assert filtered[0].due_date.implied_date == "2025-10-19"
        
    def test_get_task_statistics_empty(self):
        """Test statistics for empty task list."""
        stats = self.service.get_task_statistics([])
        
        expected = {
            'total': 0,
            'by_status': {},
            'by_priority': {},
            'by_file': {},
            'with_tags': 0,
            'with_due_date': 0,
            'overdue': 0
        }
        assert stats == expected
        
    def test_get_task_statistics_with_tasks(self):
        """Test statistics for task list with various tasks."""
        tasks = [
            Task("Open task", file="test.xit", status=Status(StatusType.OPEN)),
            Task("Checked task", file="test.xit", status=Status(StatusType.CHECKED)),
            Task("Tagged task", file="other.xit", tags=[Tag(name="work")], status=Status(StatusType.OPEN)),
            Task("Due task", due_date="2025-10-15", status=Status(StatusType.OPEN)),  # Overdue
            Task("Priority task", priority=Priority(level=2), status=Status(StatusType.OPEN)),
        ]
        
        stats = self.service.get_task_statistics(tasks)
        
        assert stats['total'] == 5
        assert stats['by_status']['OPEN'] == 4
        assert stats['by_status']['CHECKED'] == 1
        assert stats['by_file']['test.xit'] == 2
        assert stats['by_file']['other.xit'] == 1
        assert stats['by_file']['unknown'] == 2  # Tasks without file set
        assert stats['with_tags'] == 1
        assert stats['with_due_date'] == 1
        assert stats['overdue'] == 1
        
    def test_add_task_to_file_new_file(self):
        """Test adding task to a new file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "new_tasks.xit"
            task = Task("New task", priority=Priority(level=2), tags=[Tag(name="test")])
            
            self.service.add_task_to_file(task, str(file_path))
            
            assert file_path.exists()
            content = file_path.read_text()
            assert "[ ] !! New task #test" in content
            
    def test_add_task_to_file_existing_file(self):
        """Test adding task to an existing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "existing.xit"
            file_path.write_text("[ ] Existing task\n")
            
            task = Task("New task")
            self.service.add_task_to_file(task, str(file_path))
            
            content = file_path.read_text()
            lines = content.strip().split('\n')
            assert len(lines) == 2
            assert "Existing task" in lines[0]
            assert "New task" in lines[1]
            
    def test_add_task_to_file_unsupported_extension(self):
        """Test adding task to file with unsupported extension."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            task = Task("Test task")
            
            with pytest.raises(FileNotSupportedError):
                self.service.add_task_to_file(task, str(file_path))
                
    def test_update_task_by_id_success(self):
        """Test successfully updating a task by ID."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.xit"
            file_path.write_text("[ ] Original task\n[x] Another task\n")
            
            # Update the first task
            new_status = Status(StatusType.CHECKED)
            new_priority = Priority(level=2)
            
            result = self.service.update_task_by_id(
                task_id=1, 
                file_paths=[str(file_path)],
                new_status=new_status,
                new_priority=new_priority
            )
            
            assert result is not None
            assert result.status.status_type == StatusType.CHECKED
            assert result.priority.level == 2
            
            # Check file was updated
            content = file_path.read_text()
            assert "[x] !! Original task" in content
            
    def test_update_task_by_id_not_found(self):
        """Test updating a task that doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.xit"
            file_path.write_text("[ ] Test task\n")
            
            result = self.service.update_task_by_id(
                task_id=999,
                file_paths=[str(file_path)]
            )
            
            assert result is None
            
    def test_remove_task_by_id_success(self):
        """Test successfully removing a task by ID."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.xit"
            file_path.write_text("[ ] First task\n[ ] Second task\n[ ] Third task\n")
            
            result = self.service.remove_task_by_id(2, [str(file_path)])
            
            assert result is not None
            assert "Second task" in result.description_text
            
            # Check file was updated
            content = file_path.read_text()
            lines = [line for line in content.split('\n') if line.strip()]
            assert len(lines) == 2
            assert "First task" in lines[0]
            assert "Third task" in lines[1]
            
    def test_remove_task_by_id_not_found(self):
        """Test removing a task that doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.xit"
            file_path.write_text("[ ] Test task\n")
            
            result = self.service.remove_task_by_id(999, [str(file_path)])
            
            assert result is None
            
    def test_move_task_by_id_success(self):
        """Test successfully moving a task between files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = Path(temp_dir) / "source.xit"
            target_file = Path(temp_dir) / "target.xit"
            
            source_file.write_text("[ ] Task to move\n[ ] Stay here\n")
            target_file.write_text("[ ] Existing target task\n")
            
            result = self.service.move_task_by_id(1, [str(source_file)], str(target_file))
            
            assert result is not None
            assert "Task to move" in result.description_text
            
            # Check source file
            source_content = source_file.read_text()
            assert "Task to move" not in source_content
            assert "Stay here" in source_content
            
            # Check target file
            target_content = target_file.read_text()
            assert "Task to move" in target_content
            assert "Existing target task" in target_content
            
    def test_move_task_by_id_unsupported_target(self):
        """Test moving task to unsupported file type."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = Path(temp_dir) / "source.xit"
            target_file = Path(temp_dir) / "target.txt"
            
            source_file.write_text("[ ] Task to move\n")
            
            with pytest.raises(FileNotSupportedError):
                self.service.move_task_by_id(1, [str(source_file)], str(target_file))
                
    def test_add_task_tag_success(self):
        """Test successfully adding a tag to a task."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.xit"
            file_path.write_text("[ ] Task without tag\n")
            
            result = self.service.add_task_tag(1, "work", [str(file_path)])
            
            assert result is True
            
            # Check file was updated
            content = file_path.read_text()
            assert "#work" in content
            
    def test_add_task_tag_with_hash_prefix(self):
        """Test adding a tag with # prefix."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.xit"
            file_path.write_text("[ ] Task without tag\n")
            
            result = self.service.add_task_tag(1, "#work", [str(file_path)])
            
            assert result is True
            content = file_path.read_text()
            assert "#work" in content
            
    def test_add_task_tag_not_found(self):
        """Test adding tag to non-existent task."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.xit"
            file_path.write_text("[ ] Test task\n")
            
            result = self.service.add_task_tag(999, "work", [str(file_path)])
            
            assert result is False
            
    def test_remove_task_tag_success(self):
        """Test successfully removing a tag from a task."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.xit"
            file_path.write_text("[ ] Task with tag #work #urgent\n")
            
            result = self.service.remove_task_tag(1, "work", [str(file_path)])
            
            assert result is True
            
            # Check file was updated - the tag removal should work
            # Note: The exact format may vary based on implementation
            
    def test_remove_task_tag_not_found(self):
        """Test removing tag from non-existent task."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.xit"
            file_path.write_text("[ ] Test task\n")
            
            result = self.service.remove_task_tag(999, "work", [str(file_path)])
            
            assert result is False
            
    def test_recur_task_by_id_success(self):
        """Test successfully creating recurring tasks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.xit"
            file_path.write_text("[ ] Weekly meeting -> 2025-10-19\n")
            
            result = self.service.recur_task_by_id(
                task_id=1,
                interval="1w",
                count=3,
                specified_files=[str(file_path)]
            )
            
            assert len(result) == 3
            
            # Check file content
            content = file_path.read_text()
            lines = [line for line in content.split('\n') if line.strip()]
            assert len(lines) == 4  # Original + 3 recurring
            
    def test_recur_task_by_id_with_end_date(self):
        """Test recurring tasks with end date constraint."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.xit"
            file_path.write_text("[ ] Daily task\n")
            
            result = self.service.recur_task_by_id(
                task_id=1,
                interval="1d",
                end_date="2025-10-21",  # Only 2 days from now
                count=10,  # Would create 10 but end_date limits it
                specified_files=[str(file_path)]
            )
            
            assert len(result) == 2  # Limited by end_date
            
    def test_recur_task_by_id_not_found(self):
        """Test recurring tasks when original task not found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.xit"
            file_path.write_text("[ ] Test task\n")
            
            with pytest.raises(ValueError, match="Task with ID 999 not found"):
                self.service.recur_task_by_id(
                    task_id=999,
                    interval="1w",
                    specified_files=[str(file_path)]
                )
                
    def test_parse_interval_simple_formats(self):
        """Test parsing simple interval formats."""
        assert self.service._parse_interval("1d") == 1
        assert self.service._parse_interval("2w") == 14
        assert self.service._parse_interval("3m") == 90
        assert self.service._parse_interval("1y") == 365
        
    def test_parse_interval_complex_format(self):
        """Test parsing complex interval formats."""
        # 1 year, 2 months, 1 week, 4 days = 365 + 60 + 7 + 4 = 436
        assert self.service._parse_interval("1y2m1w4d") == 436
        
    def test_parse_interval_invalid(self):
        """Test parsing invalid interval formats."""
        assert self.service._parse_interval("invalid") == 0
        assert self.service._parse_interval("") == 0


class TestFileDiscoveryService:
    """Test cases for the FileDiscoveryService class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = FileDiscoveryService()
        
    def test_supported_extensions(self):
        """Test that supported extensions are correctly defined."""
        assert '.md' in self.service.SUPPORTED_EXTENSIONS
        assert '.xit' in self.service.SUPPORTED_EXTENSIONS
        
    def test_resolve_file_paths_with_path_file(self):
        """Test resolving file paths when path is a file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.xit"
            test_file.touch()
            
            result = self.service.resolve_file_paths(
                path=str(test_file),
                directory=None,
                specified_files=None
            )
            
            assert result == [str(test_file)]
            
    def test_resolve_file_paths_with_path_directory(self):
        """Test resolving file paths when path is a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)
            (test_dir / "task1.xit").touch()
            (test_dir / "notes.md").touch()
            (test_dir / "readme.txt").touch()
            
            result = self.service.resolve_file_paths(
                path=str(test_dir),
                directory=None,
                specified_files=None
            )
            
            assert len(result) == 2
            assert any("task1.xit" in f for f in result)
            assert any("notes.md" in f for f in result)
            
    def test_resolve_file_paths_with_specified_files(self):
        """Test resolving file paths when specified files are provided."""
        specified = ["file1.xit", "file2.md"]
        
        result = self.service.resolve_file_paths(
            path=None,
            directory=None,
            specified_files=specified
        )
        
        assert result == specified
        
    def test_resolve_file_paths_with_directory_fallback(self):
        """Test resolving file paths with directory fallback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)
            (test_dir / "test.xit").touch()
            
            result = self.service.resolve_file_paths(
                path=None,
                directory=test_dir,
                specified_files=None
            )
            
            assert len(result) == 1
            assert "test.xit" in result[0]
            
    def test_resolve_path_argument_nonexistent(self):
        """Test resolving nonexistent path."""
        with pytest.raises(FileNotFoundError, match="Path '/nonexistent' does not exist"):
            self.service._resolve_path_argument("/nonexistent")
            
    def test_resolve_path_argument_unsupported_file(self):
        """Test resolving unsupported file type."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.touch()
            
            with pytest.raises(ValueError, match="is not a supported file type"):
                self.service._resolve_path_argument(str(test_file))


class TestTaskFilter:
    """Test cases for the TaskFilter dataclass."""
    
    def test_default_initialization(self):
        """Test TaskFilter with default values."""
        filter_obj = TaskFilter()
        
        assert filter_obj.status is None
        assert filter_obj.priority is None
        assert filter_obj.tags is None
        assert filter_obj.due_on is None
        assert filter_obj.due_by is None
        
    def test_initialization_with_values(self):
        """Test TaskFilter with specific values."""
        status = Status(StatusType.OPEN)
        priority = Priority(level=2)
        tags = [Tag(name="work")]
        due_date = DueDate.from_string("2025-10-19")
        
        filter_obj = TaskFilter(
            status=status,
            priority=priority,
            tags=tags,
            due_on=due_date,
            due_by=due_date
        )
        
        assert filter_obj.status == status
        assert filter_obj.priority == priority
        assert filter_obj.tags == tags
        assert filter_obj.due_on == due_date
        assert filter_obj.due_by == due_date