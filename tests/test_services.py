"""Tests for the Services module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from xit.services import TaskService, FileDiscoveryService, TaskFilter
from xit.task import Task
from xit.exceptions import XitError
from tests.conftest import create_test_file


class TestTaskFilter:
    """Test TaskFilter dataclass."""
    
    def test_task_filter_creation_empty(self):
        """Test creating an empty TaskFilter."""
        filter_obj = TaskFilter()
        
        assert filter_obj.status is None
        assert filter_obj.priority is None
        assert filter_obj.tags is None
        assert filter_obj.due_on is None
        assert filter_obj.due_by is None
    
    def test_task_filter_creation_full(self):
        """Test creating a TaskFilter with all parameters."""
        filter_obj = TaskFilter(
            status="OPEN",
            priority=2,
            tags=["work", "urgent"],
            due_on="2025-12-31",
            due_by="2025-12-31"
        )
        
        assert filter_obj.status == "OPEN"
        assert filter_obj.priority == 2
        assert filter_obj.tags == ["work", "urgent"]
        assert filter_obj.due_on == "2025-12-31"
        assert filter_obj.due_by == "2025-12-31"


class TestTaskService:
    """Test TaskService functionality."""
    
    def test_task_service_creation(self):
        """Test creating a TaskService instance."""
        service = TaskService()
        
        assert hasattr(service, 'parser')
        assert hasattr(service, 'date_parser')
    
    def test_find_task_files_empty_directory(self, temp_dir, task_service):
        """Test finding task files in empty directory."""
        files = task_service.find_task_files(temp_dir)
        assert files == []
    
    def test_find_task_files_with_task_files(self, temp_dir, task_service):
        """Test finding task files in directory with various files."""
        # Create test files
        (temp_dir / "tasks.xit").write_text("[ ] Task 1")
        (temp_dir / "notes.md").write_text("[ ] Task 2")
        (temp_dir / "readme.txt").write_text("Not a task file")
        (temp_dir / "subdir").mkdir()
        (temp_dir / "subdir" / "subtasks.xit").write_text("[ ] Subtask")
        
        files = task_service.find_task_files(temp_dir)
        
        # Should find .xit and .md files recursively
        assert len(files) >= 3
        file_names = [Path(f).name for f in files]
        assert "tasks.xit" in file_names
        assert "notes.md" in file_names
        assert "subtasks.xit" in file_names
        assert "readme.txt" not in file_names
    
    def test_find_task_files_default_directory(self, task_service):
        """Test finding task files in current directory (default)."""
        with patch('pathlib.Path.cwd') as mock_cwd:
            mock_cwd.return_value = Path("/fake/dir")
            with patch('pathlib.Path.glob') as mock_glob:
                mock_glob.return_value = []
                
                files = task_service.find_task_files()
                
                # Should have called glob on current directory
                mock_cwd.assert_called_once()
    
    def test_load_tasks_single_file(self, temp_dir, task_service):
        """Test loading tasks from a single file."""
        content = """[ ] Open task
[x] Done task
[@] Ongoing task"""
        
        test_file = create_test_file(temp_dir, "test.xit", content)
        tasks = task_service.load_tasks([str(test_file)])
        
        assert len(tasks) == 3
        assert tasks[0].status == "OPEN"
        assert tasks[1].status == "DONE"
        assert tasks[2].status == "ONGOING"
    
    def test_load_tasks_multiple_files(self, temp_dir, task_service):
        """Test loading tasks from multiple files."""
        file1 = create_test_file(temp_dir, "file1.xit", "[ ] Task 1\n[x] Task 2")
        file2 = create_test_file(temp_dir, "file2.xit", "[@] Task 3")
        
        tasks = task_service.load_tasks([str(file1), str(file2)])
        
        assert len(tasks) == 3
        assert tasks[0].description == "Task 1"
        assert tasks[1].description == "Task 2"
        assert tasks[2].description == "Task 3"
    
    def test_load_tasks_empty_file_list(self, task_service):
        """Test loading tasks from empty file list."""
        tasks = task_service.load_tasks([])
        assert tasks == []


class TestTaskFiltering:
    """Test task filtering functionality."""
    
    @pytest.fixture
    def sample_tasks(self):
        """Create sample tasks for filtering tests."""
        return [
            Task("/test.xit", 1, "Open task", "OPEN", 1, ["#work"], "2025-12-31"),
            Task("/test.xit", 2, "Done task", "DONE", 0, ["#personal"], None),
            Task("/test.xit", 3, "High priority", "OPEN", 3, ["#work", "#urgent"], "2025-11-30"),
            Task("/test.xit", 4, "Ongoing task", "ONGOING", 2, ["#project"], "2025-12-15"),
            Task("/test.xit", 5, "Question task", "INQUESTION", 0, [], "2025-12-01"),
        ]
    
    def test_filter_by_status(self, task_service, sample_tasks):
        """Test filtering tasks by status."""
        # Filter for OPEN tasks
        filter_obj = TaskFilter(status="OPEN")
        filtered = task_service.filter_tasks(sample_tasks, filter_obj)
        
        assert len(filtered) == 2
        assert all(task.status == "OPEN" for task in filtered)
        
        # Filter for DONE tasks
        filter_obj = TaskFilter(status="DONE")
        filtered = task_service.filter_tasks(sample_tasks, filter_obj)
        
        assert len(filtered) == 1
        assert filtered[0].status == "DONE"
    
    def test_filter_by_priority(self, task_service, sample_tasks):
        """Test filtering tasks by minimum priority."""
        # Filter for priority >= 2
        filter_obj = TaskFilter(priority=2)
        filtered = task_service.filter_tasks(sample_tasks, filter_obj)
        
        assert len(filtered) == 2
        assert all(task.priority >= 2 for task in filtered)
        
        # Filter for priority >= 3
        filter_obj = TaskFilter(priority=3)
        filtered = task_service.filter_tasks(sample_tasks, filter_obj)
        
        assert len(filtered) == 1
        assert filtered[0].priority == 3
    
    def test_filter_by_tags_single(self, task_service, sample_tasks):
        """Test filtering tasks by single tag."""
        filter_obj = TaskFilter(tags=["work"])
        filtered = task_service.filter_tasks(sample_tasks, filter_obj)
        
        assert len(filtered) == 2
        assert all("#work" in task.tags for task in filtered)
    
    def test_filter_by_tags_multiple(self, task_service, sample_tasks):
        """Test filtering tasks by multiple tags (AND logic)."""
        filter_obj = TaskFilter(tags=["work", "urgent"])
        filtered = task_service.filter_tasks(sample_tasks, filter_obj)
        
        assert len(filtered) == 1
        assert "#work" in filtered[0].tags
        assert "#urgent" in filtered[0].tags
    
    def test_filter_by_tags_with_hash(self, task_service, sample_tasks):
        """Test filtering with tags that include # prefix."""
        filter_obj = TaskFilter(tags=["#work"])
        filtered = task_service.filter_tasks(sample_tasks, filter_obj)
        
        assert len(filtered) == 2
        assert all("#work" in task.tags for task in filtered)
    
    def test_filter_by_due_on(self, task_service, sample_tasks):
        """Test filtering tasks due on specific date."""
        with patch.object(task_service.date_parser, 'matches_date_filter_on') as mock_filter:
            mock_filter.return_value = True
            
            filter_obj = TaskFilter(due_on="2025-12-31")
            filtered = task_service.filter_tasks(sample_tasks, filter_obj)
            
            # Should call the date parser for each task
            assert mock_filter.call_count == len(sample_tasks)
    
    def test_filter_by_due_by(self, task_service, sample_tasks):
        """Test filtering tasks due by specific date."""
        with patch.object(task_service.date_parser, 'matches_date_filter_by') as mock_filter:
            mock_filter.return_value = True
            
            filter_obj = TaskFilter(due_by="2025-12-31")
            filtered = task_service.filter_tasks(sample_tasks, filter_obj)
            
            # Should call the date parser for each task
            assert mock_filter.call_count == len(sample_tasks)
    
    def test_filter_combined(self, task_service, sample_tasks):
        """Test filtering with multiple criteria."""
        filter_obj = TaskFilter(
            status="OPEN",
            priority=1,
            tags=["work"]
        )
        filtered = task_service.filter_tasks(sample_tasks, filter_obj)
        
        # Should match tasks that meet ALL criteria
        assert len(filtered) == 2
        for task in filtered:
            assert task.status == "OPEN"
            assert task.priority >= 1
            assert "#work" in task.tags
    
    def test_filter_no_matches(self, task_service, sample_tasks):
        """Test filtering with criteria that match no tasks."""
        filter_obj = TaskFilter(
            status="OBSOLETE",  # No tasks have this status
        )
        filtered = task_service.filter_tasks(sample_tasks, filter_obj)
        
        assert len(filtered) == 0
    
    def test_filter_tags_with_values(self, task_service):
        """Test filtering tasks with tags that have values."""
        tasks_with_values = [
            Task("/test.xit", 1, "Task 1", "OPEN", 0, ["#priority=high"], None),
            Task("/test.xit", 2, "Task 2", "OPEN", 0, ["#priority=low"], None),
            Task("/test.xit", 3, "Task 3", "OPEN", 0, ["#category=work"], None),
        ]
        
        # Should match tag name without value
        filter_obj = TaskFilter(tags=["priority"])
        filtered = task_service.filter_tasks(tasks_with_values, filter_obj)
        
        assert len(filtered) == 2  # Both tasks with #priority tag


class TestTaskStatistics:
    """Test task statistics functionality."""
    
    @pytest.fixture
    def stats_sample_tasks(self):
        """Create sample tasks for statistics tests."""
        return [
            Task("/file1.xit", 1, "Task 1", "OPEN", 0, [], None),
            Task("/file1.xit", 2, "Task 2", "OPEN", 1, ["#work"], "2025-12-31"),
            Task("/file1.xit", 3, "Task 3", "DONE", 2, ["#work", "#urgent"], None),
            Task("/file2.xit", 1, "Task 4", "ONGOING", 0, [], "2025-11-30"),
            Task("/file2.xit", 2, "Task 5", "OBSOLETE", 1, ["#old"], None),
        ]
    
    def test_get_task_statistics(self, task_service, stats_sample_tasks):
        """Test calculating task statistics."""
        stats = task_service.get_task_statistics(stats_sample_tasks)
        
        # Check basic counts
        assert stats['total_tasks'] == 5
        assert stats['tasks_with_due_dates'] == 2
        assert stats['tasks_with_tags'] == 3
        assert len(stats['files_with_tasks']) == 2
        
        # Check status counts
        assert stats['status_counts']['OPEN'] == 2
        assert stats['status_counts']['DONE'] == 1
        assert stats['status_counts']['ONGOING'] == 1
        assert stats['status_counts']['OBSOLETE'] == 1
        
        # Check priority counts
        assert stats['priority_counts'][0] == 2  # Two tasks with priority 0
        assert stats['priority_counts'][1] == 2  # Two tasks with priority 1
        assert stats['priority_counts'][2] == 1  # One task with priority 2
    
    def test_get_task_statistics_empty(self, task_service):
        """Test statistics for empty task list."""
        stats = task_service.get_task_statistics([])
        
        assert stats['total_tasks'] == 0
        assert stats['tasks_with_due_dates'] == 0
        assert stats['tasks_with_tags'] == 0
        assert len(stats['files_with_tasks']) == 0
        assert stats['status_counts'] == {}
        assert stats['priority_counts'] == {}


class TestFileDiscoveryService:
    """Test FileDiscoveryService functionality."""
    
    @pytest.fixture
    def file_service(self):
        """Create a FileDiscoveryService instance."""
        return FileDiscoveryService()
    
    def test_supported_extensions(self, file_service):
        """Test supported file extensions."""
        assert file_service.SUPPORTED_EXTENSIONS == {'.md', '.xit'}
    
    def test_resolve_file_paths_with_path_file(self, temp_dir, file_service):
        """Test resolving file paths with a specific file path."""
        test_file = create_test_file(temp_dir, "test.xit", "[ ] Task")
        
        result = file_service.resolve_file_paths(
            path=str(test_file),
            directory=None,
            specified_files=None
        )
        
        assert result == [str(test_file)]
    
    def test_resolve_file_paths_with_path_directory(self, temp_dir, file_service):
        """Test resolving file paths with a directory path."""
        # Create test files
        (temp_dir / "task1.xit").write_text("[ ] Task 1")
        (temp_dir / "task2.md").write_text("[ ] Task 2")
        (temp_dir / "readme.txt").write_text("Not a task file")
        
        with patch('xit.services.TaskService.find_task_files') as mock_find:
            mock_find.return_value = [str(temp_dir / "task1.xit"), str(temp_dir / "task2.md")]
            
            result = file_service.resolve_file_paths(
                path=str(temp_dir),
                directory=None,
                specified_files=None
            )
            
            assert len(result) == 2
            mock_find.assert_called_once_with(Path(str(temp_dir)))
    
    def test_resolve_file_paths_with_specified_files(self, file_service):
        """Test resolving file paths with specified files."""
        specified = ["file1.xit", "file2.md"]
        
        result = file_service.resolve_file_paths(
            path=None,
            directory=None,
            specified_files=specified
        )
        
        assert result == specified
    
    def test_resolve_file_paths_with_directory_default(self, temp_dir, file_service):
        """Test resolving file paths with default directory."""
        with patch('xit.services.TaskService.find_task_files') as mock_find:
            mock_find.return_value = ["found1.xit", "found2.md"]
            
            result = file_service.resolve_file_paths(
                path=None,
                directory=temp_dir,
                specified_files=None
            )
            
            assert result == ["found1.xit", "found2.md"]
            mock_find.assert_called_once_with(temp_dir)
    
    def test_resolve_file_paths_nonexistent_path(self, file_service):
        """Test resolving nonexistent path raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            file_service.resolve_file_paths(
                path="/nonexistent/path",
                directory=None,
                specified_files=None
            )
    
    def test_resolve_file_paths_unsupported_file(self, temp_dir, file_service):
        """Test resolving unsupported file type raises ValueError."""
        unsupported_file = create_test_file(temp_dir, "test.txt", "content")
        
        with pytest.raises(ValueError, match="not a supported file type"):
            file_service.resolve_file_paths(
                path=str(unsupported_file),
                directory=None,
                specified_files=None
            )
    
    def test_resolve_path_argument_file(self, temp_dir, file_service):
        """Test resolving a single file path argument."""
        test_file = create_test_file(temp_dir, "test.xit", "[ ] Task")
        
        result = file_service._resolve_path_argument(str(test_file))
        assert result == [str(test_file)]
    
    def test_resolve_path_argument_directory(self, temp_dir, file_service):
        """Test resolving a directory path argument."""
        with patch('xit.services.TaskService.find_task_files') as mock_find:
            mock_find.return_value = ["file1.xit", "file2.md"]
            
            result = file_service._resolve_path_argument(str(temp_dir))
            
            assert result == ["file1.xit", "file2.md"]
            mock_find.assert_called_once()
    
    def test_resolve_path_argument_neither_file_nor_dir(self, file_service):
        """Test resolving path that is neither file nor directory."""
        # This is hard to test in practice, but we can mock the path
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            with patch('pathlib.Path.is_file') as mock_is_file:
                mock_is_file.return_value = False
                with patch('pathlib.Path.is_dir') as mock_is_dir:
                    mock_is_dir.return_value = False
                    
                    with pytest.raises(ValueError, match="neither a file nor a directory"):
                        file_service._resolve_path_argument("/dev/null")


class TestServiceHelperMethods:
    """Test helper methods in services."""
    
    def test_normalize_tags(self, task_service):
        """Test tag normalization."""
        # Test tags without # prefix
        tags = ["work", "urgent", "personal"]
        normalized = task_service._normalize_tags(tags)
        
        assert normalized == ["#work", "#urgent", "#personal"]
        
        # Test tags with # prefix (should remain unchanged)
        tags = ["#work", "#urgent"]
        normalized = task_service._normalize_tags(tags)
        
        assert normalized == ["#work", "#urgent"]
        
        # Test mixed tags
        tags = ["work", "#urgent", "personal"]
        normalized = task_service._normalize_tags(tags)
        
        assert normalized == ["#work", "#urgent", "#personal"]
    
    def test_has_all_tags_simple(self, task_service):
        """Test simple tag matching."""
        task_tags = ["#work", "#urgent", "#personal"]
        required_tags = ["#work", "#urgent"]
        
        result = task_service._has_all_tags(task_tags, required_tags)
        assert result is True
        
        # Test with missing tag
        required_tags = ["#work", "#missing"]
        result = task_service._has_all_tags(task_tags, required_tags)
        assert result is False
    
    def test_has_all_tags_with_values(self, task_service):
        """Test tag matching with tag values."""
        task_tags = ["#priority=high", "#category=work", "#status=active"]
        required_tags = ["#priority", "#category"]
        
        result = task_service._has_all_tags(task_tags, required_tags)
        assert result is True
        
        # Test with missing tag
        required_tags = ["#priority", "#missing"]
        result = task_service._has_all_tags(task_tags, required_tags)
        assert result is False
    
    def test_has_all_tags_empty_required(self, task_service):
        """Test tag matching with empty required tags."""
        task_tags = ["#work", "#urgent"]
        required_tags = []
        
        result = task_service._has_all_tags(task_tags, required_tags)
        assert result is True
    
    def test_has_all_tags_empty_task_tags(self, task_service):
        """Test tag matching with empty task tags."""
        task_tags = []
        required_tags = ["#work"]
        
        result = task_service._has_all_tags(task_tags, required_tags)
        assert result is False


class TestServiceIntegration:
    """Test integration between service components."""
    
    def test_full_workflow(self, temp_dir):
        """Test complete workflow from file discovery to filtering."""
        # Create test files
        file1_content = """[ ] ! Open high priority task #work #urgent -> 2025-12-31
[x] Completed task #personal
[@] !! Ongoing very important task #project"""
        
        file2_content = """[ ] Simple task
[~] Obsolete task #old
[?] Question task #help -> 2025-11-30"""
        
        file1 = create_test_file(temp_dir, "work.xit", file1_content)
        file2 = create_test_file(temp_dir, "personal.xit", file2_content)
        
        # Initialize services
        task_service = TaskService()
        file_service = FileDiscoveryService()
        
        # Discover files
        file_paths = file_service.resolve_file_paths(
            path=str(temp_dir),
            directory=None,
            specified_files=None
        )
        
        assert len(file_paths) >= 2
        
        # Load tasks
        tasks = task_service.load_tasks(file_paths)
        assert len(tasks) == 6
        
        # Filter tasks
        filter_obj = TaskFilter(status="OPEN")
        filtered_tasks = task_service.filter_tasks(tasks, filter_obj)
        assert len(filtered_tasks) == 2  # Two OPEN tasks
        
        # Get statistics
        stats = task_service.get_task_statistics(tasks)
        assert stats['total_tasks'] == 6
        assert len(stats['files_with_tasks']) == 2


class TestTaskModificationServices:
    """Test task modification services (add, mark, reschedule)."""
    
    @pytest.fixture
    def task_service(self):
        """Create a TaskService instance."""
        return TaskService()
    
    def test_add_task_to_file_success(self, temp_dir, task_service):
        """Test successfully adding a task to a file."""
        # Create test file
        test_file = temp_dir / "tasks.xit"
        test_file.write_text("""[ ] Existing task
[x] Completed task
""")
        
        # Add new task
        task_service.add_task_to_file("New task description", str(test_file))
        
        # Verify task was added
        content = test_file.read_text()
        assert "[ ] New task description" in content
        assert "Existing task" in content  # Original content preserved
    
    def test_add_task_to_file_with_due_date(self, temp_dir, task_service):
        """Test adding a task with due date."""
        test_file = temp_dir / "tasks.xit"
        test_file.write_text("[ ] Existing task\n")
        
        task_service.add_task_to_file("Task with date -> 2025-12-31", str(test_file))
        content = test_file.read_text()
        assert "[ ] Task with date -> 2025-12-31" in content
    
    def test_add_task_to_nonexistent_file(self, temp_dir, task_service):
        """Test adding task to a file that doesn't exist."""
        test_file = temp_dir / "new_tasks.xit"
        
        task_service.add_task_to_file("First task", str(test_file))
        assert test_file.exists()
        content = test_file.read_text()
        assert "[ ] First task" in content
    
    def test_mark_task_by_id_success(self, temp_dir, task_service):
        """Test successfully marking a task by ID."""
        # Create test file with tasks
        test_file = temp_dir / "tasks.xit"
        test_file.write_text("""[ ] Task 1
[ ] Task 2 #priority1
[x] Task 3
""")
        
        # Mark task 2 as completed
        result = task_service.mark_task_by_id(2, "DONE", [test_file])
        
        assert result is not None
        assert result.description == "Task 2 #priority1"
        assert result.status == "DONE"
        
        # Verify file was updated
        content = test_file.read_text()
        lines = content.strip().split('\n')
        assert lines[1] == "[x] Task 2 #priority1"  # Task was marked
    
    def test_mark_task_by_id_different_statuses(self, temp_dir, task_service):
        """Test marking tasks with different status symbols."""
        test_file = temp_dir / "tasks.xit"
        test_file.write_text("[ ] Test task\n")
        
        # Test different status names
        status_tests = [
            ("DONE", "x"),
            ("ONGOING", "@"), 
            ("OBSOLETE", "~"),
            ("INQUESTION", "?")
        ]
        
        for status_name, expected_symbol in status_tests:
            # Reset file
            test_file.write_text("[ ] Test task\n")
            
            result = task_service.mark_task_by_id(1, status_name, [test_file])
            assert result is not None
            assert result.status == status_name
            
            # Verify file content
            content = test_file.read_text()
            assert f"[{expected_symbol}] Test task" in content
    
    def test_mark_task_by_id_not_found(self, temp_dir, task_service):
        """Test marking a task that doesn't exist."""
        test_file = temp_dir / "tasks.xit"
        test_file.write_text("[ ] Only task\n")
        
        result = task_service.mark_task_by_id(999, "DONE", [test_file])
        assert result is None
    
    def test_mark_task_across_multiple_files(self, temp_dir, task_service):
        """Test marking a task that exists across multiple files."""
        # Create multiple files
        file1 = temp_dir / "tasks1.xit"
        file1.write_text("[ ] Task 1\n")
        
        file2 = temp_dir / "tasks2.xit"  
        file2.write_text("[ ] Task 2\n[ ] Task 3\n")
        
        # Mark task 3 (should be in file2)
        result = task_service.mark_task_by_id(3, "DONE", [file1, file2])
        
        assert result is not None
        assert result.description == "Task 3"
        
        # Verify correct file was updated
        assert "[ ] Task 1" in file1.read_text()  # file1 unchanged
        content2 = file2.read_text()
        assert "[x] Task 3" in content2
    
    def test_reschedule_task_by_id_success(self, temp_dir, task_service):
        """Test successfully rescheduling a task."""
        test_file = temp_dir / "tasks.xit"
        test_file.write_text("""[ ] Task 1
[ ] Task 2 -> 2025-10-15
[ ] Task 3
""")
        
        # Reschedule task 2 to new date
        result = task_service.reschedule_task_by_id(2, "2025-12-31", [test_file])
        
        assert result is not None
        assert "Task 2" in result.description  # Description may include due date
        assert result.due_date == "2025-12-31"
        
        # Verify file was updated
        content = test_file.read_text()
        assert "[ ] Task 2 -> 2025-12-31" in content
    
    def test_reschedule_task_without_existing_date(self, temp_dir, task_service):
        """Test rescheduling a task that doesn't have a due date."""
        test_file = temp_dir / "tasks.xit"
        test_file.write_text("[ ] Task without date\n")
        
        result = task_service.reschedule_task_by_id(1, "2025-12-31", [test_file])
        
        assert result is not None
        assert result.due_date == "2025-12-31"
        
        # Verify file was updated
        content = test_file.read_text()
        assert "[ ] Task without date -> 2025-12-31" in content
    
    def test_reschedule_task_remove_date(self, temp_dir, task_service):
        """Test removing due date from a task."""
        test_file = temp_dir / "tasks.xit"
        test_file.write_text("[ ] Task with date -> 2025-10-15\n")
        
        result = task_service.reschedule_task_by_id(1, None, [test_file])
        
        assert result is not None
        assert result.due_date is None
        
        # Verify file was updated (date removed)
        content = test_file.read_text()
        assert "[ ] Task with date" in content
        assert "2025-10-15" not in content
    
    def test_reschedule_task_not_found(self, temp_dir, task_service):
        """Test rescheduling a task that doesn't exist."""
        test_file = temp_dir / "tasks.xit"
        test_file.write_text("[ ] Only task\n")
        
        result = task_service.reschedule_task_by_id(999, "2025-12-31", [test_file])
        assert result is None
    
    def test_reschedule_task_across_files(self, temp_dir, task_service):
        """Test rescheduling a task across multiple files."""
        file1 = temp_dir / "tasks1.xit"
        file1.write_text("[ ] Task 1\n")
        
        file2 = temp_dir / "tasks2.xit"
        file2.write_text("[ ] Task 2\n[ ] Task 3 -> 2025-10-15\n")
        
        # Reschedule task 3
        result = task_service.reschedule_task_by_id(3, "2025-12-25", [file1, file2])
        
        assert result is not None
        assert "Task 3" in result.description  # Description may include due date
        assert result.due_date == "2025-12-25"
        
        # Verify correct file was updated
        assert file1.read_text() == "[ ] Task 1\n"  # file1 unchanged
        content2 = file2.read_text()
        assert "[ ] Task 3 -> 2025-12-25" in content2
    
    def test_file_update_operations_preserve_format(self, temp_dir, task_service):
        """Test that file operations preserve original formatting."""
        test_file = temp_dir / "tasks.xit"
        original_content = """# Project Tasks

[ ] Task 1 #work
  - Some details
[ ] Task 2 -> 2025-10-15

## Completed
[x] Done task
"""
        test_file.write_text(original_content)
        
        # Mark task 1
        task_service.mark_task_by_id(1, "DONE", [test_file])
        
        content = test_file.read_text()
        # Should preserve headers and structure
        assert "# Project Tasks" in content
        assert "## Completed" in content
        assert "  - Some details" in content
        assert "[x] Task 1 #work" in content
    
    @patch('pathlib.Path.write_text')
    def test_file_write_error_handling(self, mock_write, temp_dir, task_service):
        """Test error handling when file write operations fail."""
        test_file = temp_dir / "tasks.xit"
        test_file.write_text("[ ] Test task\n")
        
        # Make write_text raise an exception
        mock_write.side_effect = PermissionError("Permission denied")
        
        # Should handle the exception gracefully
        result = task_service.mark_task_by_id(1, "DONE", [test_file])
        assert result is None


class TestTaskIdAssignment:
    """Test task ID assignment functionality."""
    
    @pytest.fixture
    def task_service(self):
        """Create a TaskService instance."""
        return TaskService()
    
    def test_load_tasks_assigns_sequential_ids(self, temp_dir, task_service):
        """Test that tasks get sequential IDs assigned."""
        # Create multiple files with tasks
        file1 = temp_dir / "a_first.xit"
        file1.write_text("""[ ] Task A1
[ ] Task A2
""")
        
        file2 = temp_dir / "b_second.xit"
        file2.write_text("""[ ] Task B1
[x] Task B2
""")
        
        # Load tasks (should assign IDs alphabetically by file path)
        tasks = task_service.load_tasks([file1, file2])
        
        # Verify ID assignment
        assert len(tasks) == 4
        
        # Should be ordered by file path then by position in file
        assert tasks[0].id == 1
        assert tasks[0].description == "Task A1"
        assert tasks[1].id == 2  
        assert tasks[1].description == "Task A2"
        assert tasks[2].id == 3
        assert tasks[2].description == "Task B1"
        assert tasks[3].id == 4
        assert tasks[3].description == "Task B2"
    
    def test_load_tasks_with_mixed_file_types(self, temp_dir, task_service):
        """Test ID assignment with mixed .xit and .md files."""
        md_file = temp_dir / "notes.md"
        md_file.write_text("# Notes\n[ ] MD Task 1\n[x] MD Task 2\n")
        
        xit_file = temp_dir / "tasks.xit"
        xit_file.write_text("[ ] XIT Task 1\n[ ] XIT Task 2\n")
        
        tasks = task_service.load_tasks([md_file, xit_file])
        
        # Should be 4 tasks total with sequential IDs
        assert len(tasks) == 4
        
        # Verify alphabetical ordering (notes.md comes before tasks.xit)
        md_tasks = [t for t in tasks if Path(t.file) == md_file]
        xit_tasks = [t for t in tasks if Path(t.file) == xit_file]
        
        assert md_tasks[0].id == 1
        assert md_tasks[1].id == 2
        assert xit_tasks[0].id == 3
        assert xit_tasks[1].id == 4
    
    def test_id_consistency_across_reloads(self, temp_dir, task_service):
        """Test that IDs remain consistent across multiple loads."""
        test_file = temp_dir / "consistent.xit"
        test_file.write_text("""[ ] Task 1
[ ] Task 2
[ ] Task 3
""")
        
        # Load tasks multiple times
        tasks1 = task_service.load_tasks([test_file])
        tasks2 = task_service.load_tasks([test_file])
        
        # IDs should be the same
        for t1, t2 in zip(tasks1, tasks2):
            assert t1.id == t2.id
            assert t1.description == t2.description


class TestTaskRemovalServices:
    """Test task removal services."""
    
    @pytest.fixture
    def task_service(self):
        """Create a TaskService instance."""
        return TaskService()
    
    def test_remove_task_by_id_success(self, temp_dir, task_service):
        """Test successfully removing a task by ID."""
        # Create test file with tasks
        test_file = temp_dir / "tasks.xit"
        test_file.write_text("[ ] Task 1\n[ ] Task 2\n[ ] Task 3\n")
        
        # Remove task 2
        result = task_service.remove_task_by_id(2, [test_file])
        
        assert result is not None
        assert "Task 2" in result.description
        
        # Verify file was updated - task 2 should be gone
        content = test_file.read_text()
        lines = content.strip().split('\n')
        assert len(lines) == 2
        assert "Task 1" in lines[0]
        assert "Task 3" in lines[1]
        assert "Task 2" not in content
    
    def test_remove_task_by_id_with_continuation_lines(self, temp_dir, task_service):
        """Test removing a task with continuation lines."""
        test_file = temp_dir / "tasks.xit"
        test_file.write_text("""[ ] Task 1
[ ] Task 2 with details
    Additional details line 1
    Additional details line 2
[ ] Task 3
""")
        
        # Remove task 2 (which has continuation lines)
        result = task_service.remove_task_by_id(2, [test_file])
        
        assert result is not None
        
        # Verify task and continuation lines are removed
        content = test_file.read_text()
        lines = content.strip().split('\n')
        assert len(lines) == 2  # Only Task 1 and Task 3 should remain
        assert "Task 1" in lines[0]
        assert "Task 3" in lines[1]
        assert "Task 2" not in content
        assert "Additional details" not in content
    
    def test_remove_task_by_id_not_found(self, temp_dir, task_service):
        """Test removing a task that doesn't exist."""
        test_file = temp_dir / "tasks.xit"
        test_file.write_text("[ ] Only task\n")
        
        result = task_service.remove_task_by_id(999, [test_file])
        assert result is None
    
    def test_remove_task_across_multiple_files(self, temp_dir, task_service):
        """Test removing a task from multiple files."""
        # Create multiple files
        file1 = temp_dir / "tasks1.xit"
        file1.write_text("[ ] Task 1\n")
        
        file2 = temp_dir / "tasks2.xit"  
        file2.write_text("[ ] Task 2\n[ ] Task 3\n")
        
        # Remove task 3 (should be in file2)
        result = task_service.remove_task_by_id(3, [file1, file2])
        
        assert result is not None
        assert "Task 3" in result.description
        
        # Verify correct file was updated
        assert "[ ] Task 1" in file1.read_text()  # file1 unchanged
        content2 = file2.read_text()
        assert "Task 2" in content2
        assert "Task 3" not in content2
    
    def test_remove_task_preserves_file_structure(self, temp_dir, task_service):
        """Test that removing tasks preserves file structure."""
        test_file = temp_dir / "tasks.xit"
        original_content = """# Project Tasks

[ ] Task 1 #work
[ ] Task 2 -> 2025-10-15

## Completed
[x] Done task
"""
        test_file.write_text(original_content)
        
        # Remove task 1
        task_service.remove_task_by_id(1, [test_file])
        
        content = test_file.read_text()
        # Should preserve headers and other structure
        assert "# Project Tasks" in content
        assert "## Completed" in content
        assert "[x] Done task" in content
        assert "Task 1" not in content
        assert "Task 2" in content


class TestTaskMovingServices:
    """Test task moving services."""
    
    @pytest.fixture
    def task_service(self):
        """Create a TaskService instance."""
        return TaskService()
    
    def test_move_task_by_id_success(self, temp_dir, task_service):
        """Test successfully moving a task."""
        # Create source and target files
        source_file = temp_dir / "source.xit"
        source_file.write_text("[ ] Task 1\n[ ] Task to move -> 2025-12-31\n[ ] Task 3\n")
        
        target_file = temp_dir / "target.xit"
        target_file.write_text("[ ] Existing target task\n")
        
        # Move task 2
        result = task_service.move_task_by_id(2, [source_file], str(target_file))
        
        assert result is not None
        assert "Task to move" in result.description
        assert str(target_file) == result.file
        
        # Verify task was removed from source
        source_content = source_file.read_text()
        assert "Task 1" in source_content
        assert "Task 3" in source_content
        assert "Task to move" not in source_content
        
        # Verify task was added to target (preserving due date)
        target_content = target_file.read_text()
        assert "Existing target task" in target_content
        assert "Task to move -> 2025-12-31" in target_content
    
    def test_move_task_to_new_file(self, temp_dir, task_service):
        """Test moving a task to a new file that doesn't exist."""
        # Create source file
        source_file = temp_dir / "source.xit"
        source_file.write_text("[ ] Task to move #important\n")
        
        target_file = temp_dir / "new_target.xit"
        
        # Move task 1 to new file
        result = task_service.move_task_by_id(1, [source_file], str(target_file))
        
        assert result is not None
        
        # Verify task was removed from source
        source_content = source_file.read_text()
        assert "Task to move" not in source_content
        
        # Verify new target file was created with the task
        assert target_file.exists()
        target_content = target_file.read_text()
        assert "Task to move #important" in target_content
    
    def test_move_task_invalid_target_extension(self, temp_dir, task_service):
        """Test moving task to file with invalid extension."""
        source_file = temp_dir / "source.xit"
        source_file.write_text("[ ] Task to move\n")
        
        target_file = temp_dir / "target.txt"  # Invalid extension
        
        with pytest.raises(Exception):  # Should raise FileNotSupportedError
            task_service.move_task_by_id(1, [source_file], str(target_file))
    
    def test_move_task_not_found(self, temp_dir, task_service):
        """Test moving a task that doesn't exist."""
        source_file = temp_dir / "source.xit"
        source_file.write_text("[ ] Only task\n")
        
        target_file = temp_dir / "target.xit"
        
        result = task_service.move_task_by_id(999, [source_file], str(target_file))
        assert result is None
    
    def test_move_task_with_complex_description(self, temp_dir, task_service):
        """Test moving a task with priority, tags, and due date."""
        source_file = temp_dir / "source.xit"
        source_file.write_text("[ ] ! High priority task #work #urgent -> 2025-12-31\n")
        
        target_file = temp_dir / "target.xit"
        
        # Move the complex task
        result = task_service.move_task_by_id(1, [source_file], str(target_file))
        
        assert result is not None
        
        # Verify complete task format is preserved in target
        target_content = target_file.read_text()
        assert "! High priority task #work #urgent -> 2025-12-31" in target_content
    
    def test_extract_task_description(self, temp_dir, task_service):
        """Test the _extract_task_description helper method."""
        source_file = temp_dir / "test.xit"
        source_file.write_text("[ ] Task with details #tag -> 2025-12-31\n")
        
        # Load the task
        tasks = task_service.load_tasks([source_file])
        task = tasks[0]
        
        # Extract description
        description = task_service._extract_task_description(task)
        
        # Should preserve everything except the checkbox
        assert description == "Task with details #tag -> 2025-12-31"


class TestTaskRecurringServices:
    """Test recurring task functionality in TaskService."""
    
    def test_recur_task_by_id_success(self, temp_dir):
        """Test creating recurring instances of a task."""
        task_service = TaskService()
        
        # Create test file with a task
        test_file = temp_dir / "test.xit"
        test_file.write_text("[ ] Weekly meeting -> 2025-10-20\n")
        
        # Execute recur with count
        created_tasks = task_service.recur_task_by_id(
            task_id=1,
            interval="1w",
            count=3,
            directory=temp_dir,
            specified_files=[]
        )
        
        # Verify correct number of tasks created
        assert len(created_tasks) == 2  # 3 total - 1 original = 2 new
        
        # Verify task properties
        for i, task in enumerate(created_tasks):
            assert task.description == "Weekly meeting"
            assert task.status == "OPEN"
            assert task.file == str(test_file)
        
        # Verify dates are correct (weekly intervals starting from 2025-10-20)
        assert created_tasks[0].due_date == "2025-10-27"
        assert created_tasks[1].due_date == "2025-11-03"
        
        # Verify tasks were actually written to file
        file_content = test_file.read_text()
        lines = file_content.strip().split('\n')
        assert len(lines) == 3  # Original + 2 new tasks
        assert "-> 2025-10-27" in file_content
        assert "-> 2025-11-03" in file_content
    
    def test_recur_task_by_id_with_end_date(self, temp_dir):
        """Test creating recurring instances with end date limit."""
        task_service = TaskService()
        
        # Create test file with a task
        test_file = temp_dir / "test.xit"  
        test_file.write_text("[ ] Monthly report -> 2025-01-01\n")
        
        # Execute recur with end date
        created_tasks = task_service.recur_task_by_id(
            task_id=1,
            interval="1m",
            end_date="2025-03-31",
            directory=temp_dir,
            specified_files=[]
        )
        
        # Should create tasks until end date
        assert len(created_tasks) >= 2
        
        # Verify all dates are within the range
        for task in created_tasks:
            assert "2025-" in task.due_date
    
    def test_recur_task_by_id_task_not_found(self, temp_dir):
        """Test recur with non-existent task ID."""
        task_service = TaskService()
        
        # Create empty test file
        test_file = temp_dir / "test.xit"
        test_file.write_text("[ ] Some task\n")
        
        # Try to recur non-existent task
        with pytest.raises(ValueError, match="Task with ID 999 not found"):
            task_service.recur_task_by_id(
                task_id=999,
                interval="1w",
                count=2,
                directory=temp_dir,
                specified_files=[]
            )
    
    def test_recur_task_by_id_with_target_file(self, temp_dir):
        """Test creating recurring instances in a different target file."""
        task_service = TaskService()
        
        # Create source file with task
        source_file = temp_dir / "source.xit"
        source_file.write_text("[ ] Team standup -> 2025-10-21\n")
        
        # Create target file
        target_file = temp_dir / "recurring.xit"
        target_file.write_text("")  # Empty initially
        
        # Execute recur with target file
        created_tasks = task_service.recur_task_by_id(
            task_id=1,
            interval="1d",
            count=3,
            target_file=str(target_file),
            directory=temp_dir,
            specified_files=[]
        )
        
        # Verify tasks created
        assert len(created_tasks) == 2  # 3 total - 1 original = 2 new
        
        # Verify target file contains the new tasks
        target_content = target_file.read_text()
        assert "Team standup -> 2025-10-22" in target_content
        assert "Team standup -> 2025-10-23" in target_content
        
        # Source file should remain unchanged
        source_content = source_file.read_text()
        assert source_content == "[ ] Team standup -> 2025-10-21\n"
    
    def test_recur_task_by_id_with_priority_and_tags(self, temp_dir):
        """Test recurring task preserves priority and tags."""
        task_service = TaskService()
        
        # Create test file with priority and tags
        test_file = temp_dir / "test.xit"
        test_file.write_text("[ ] !! High priority task #work #urgent -> 2025-10-15\n")
        
        # Execute recur
        created_tasks = task_service.recur_task_by_id(
            task_id=1,
            interval="1w",
            count=2,
            directory=temp_dir,
            specified_files=[]
        )
        
        # Verify tasks have correct properties
        assert len(created_tasks) == 1  # 2 total - 1 original = 1 new
        
        task = created_tasks[0]
        assert task.priority == 2  # Two exclamation marks
        assert task.tags == ["#work", "#urgent"]  # Tags include # prefix
        assert task.due_date == "2025-10-22"
        
        # Verify file content includes priority and tags
        file_content = test_file.read_text()
        assert "!! High priority task #work #urgent -> 2025-10-22" in file_content
    
    def test_recur_task_by_id_no_due_date(self, temp_dir):
        """Test recurring task without due date uses tomorrow as start."""
        task_service = TaskService()
        
        # Create test file with task without due date
        test_file = temp_dir / "test.xit"
        test_file.write_text("[ ] Task without due date\n")
        
        # Mock datetime to control "tomorrow"
        from datetime import datetime, timedelta
        mock_now = datetime(2025, 10, 17)  # Fixed date for testing
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            
            # Execute recur
            created_tasks = task_service.recur_task_by_id(
                task_id=1,
                interval="1d",
                count=2,
                directory=temp_dir,
                specified_files=[]
            )
        
        # Should use tomorrow (2025-10-18) as start date
        # When there's no original due date, we generate count=2 tasks starting from tomorrow
        assert len(created_tasks) == 2  
        assert created_tasks[0].due_date == "2025-10-18"  # Tomorrow
        assert created_tasks[1].due_date == "2025-10-19"  # Tomorrow + 1 day interval
    
    def test_recur_task_by_id_invalid_interval(self, temp_dir):
        """Test recur with invalid interval format."""
        task_service = TaskService()
        
        # Create test file
        test_file = temp_dir / "test.xit"
        test_file.write_text("[ ] Test task -> 2025-10-20\n")
        
        # Try with invalid interval
        with pytest.raises(ValueError, match="Error generating recurring dates"):
            task_service.recur_task_by_id(
                task_id=1,
                interval="invalid",
                count=2,
                directory=temp_dir,
                specified_files=[]
            )
    
    def test_recur_task_by_id_invalid_target_file(self, temp_dir):
        """Test recur with invalid target file extension."""
        task_service = TaskService()
        
        # Create test file
        test_file = temp_dir / "test.xit"
        test_file.write_text("[ ] Test task -> 2025-10-20\n")
        
        # Try with invalid target file extension
        with pytest.raises(ValueError, match="Target file .* must have .md or .xit extension"):
            task_service.recur_task_by_id(
                task_id=1,
                interval="1w",
                count=2,
                target_file="invalid.txt",
                directory=temp_dir,
                specified_files=[]
            )