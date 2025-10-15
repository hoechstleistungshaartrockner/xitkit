"""Tests for the Services module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from xitflow.services import TaskService, FileDiscoveryService, TaskFilter
from xitflow.task import Task
from xitflow.exceptions import XitError
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
        
        with patch('xitflow.services.TaskService.find_task_files') as mock_find:
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
        with patch('xitflow.services.TaskService.find_task_files') as mock_find:
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
        with patch('xitflow.services.TaskService.find_task_files') as mock_find:
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