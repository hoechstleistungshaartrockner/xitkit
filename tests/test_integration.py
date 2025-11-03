"""Integration tests for the xit package.

These tests verify that all components work together correctly in real-world scenarios.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from xitkit.fileparser import FileParser
from xitkit.services import TaskService, FileDiscoveryService, TaskFilter
from xitkit.formatter import TaskFormatter
from xitkit.commands import ShowTasksCommand, ShowStatsCommand
from xitkit.task import Task
from xitkit.dateutils import DateParser
from tests.conftest import create_test_file
from xitkit.file_repository import FileRepository


@pytest.mark.integration
class TestFullWorkflow:
    """Test complete workflows from file discovery to output."""
    
    def test_complete_discovery_and_parsing(self, isolated_test_files):
        """Test complete file discovery and task parsing."""
        service = TaskService()
        
        # Discover all task files
        files = service.find_task_files(isolated_test_files)
        
        # Should find .xit and .md files but not .txt
        assert len(files) >= 3
        file_extensions = {Path(f).suffix for f in files}
        assert ".xit" in file_extensions
        assert ".md" in file_extensions
        assert ".txt" not in file_extensions
        
        # Parse all files
        file_objs = [FileRepository().get_file(f) for f in files]
        tasks = FileRepository()._tasks.values()
        
        # Should have parsed multiple tasks from multiple files
        assert len(tasks) > 10
        
        # Verify we have tasks from different files
        file_paths = {task.location.file_path for task in tasks}
        assert len(file_paths) >= 3
        
        # Verify different types of tasks were parsed
        statuses = {task.status.status_type.name for task in tasks}
        assert "OPEN" in statuses
        assert "CHECKED" in statuses
        assert "ONGOING" in statuses
        
        # Verify tasks with different features
        has_priority = any(task.priority.level > 0 for task in tasks)
        has_tags = any(len(task.tags) > 0 for task in tasks)
        has_due_dates = any(task.due_date is not None for task in tasks)
        has_multiline = any('\n' in str(task.description) for task in tasks)
        
        assert has_priority
        assert has_tags
        assert has_due_dates
        assert has_multiline
    
    def test_filtering_integration(self, isolated_test_files):
        """Test task filtering across multiple files."""
        service = TaskService()
        
        files = service.find_task_files(isolated_test_files)
        file_objs = [FileRepository().get_file(f) for f in files]
        tasks = FileRepository()._tasks.values()
        
        # Filter by status
        from xitkit.status import Status, StatusType
        open_filter = TaskFilter(status=[Status(StatusType.OPEN)])
        open_tasks = service.filter_tasks(tasks, open_filter)
        assert all(task.status.status_type == StatusType.OPEN for task in open_tasks)
        assert len(open_tasks) > 0
        
        # Filter by priority
        from xitkit.priority import Priority
        high_priority_filter = TaskFilter(priority=Priority(level=2))
        high_priority_tasks = service.filter_tasks(tasks, high_priority_filter)
        assert all(task.priority.level >= 2 for task in high_priority_tasks)
        assert len(high_priority_tasks) > 0
        
        # Filter by tags
        from xitkit.tags import Tag
        dev_tag_filter = TaskFilter(tags=[Tag(name="tag")])
        dev_tasks = service.filter_tasks(tasks, dev_tag_filter)
        assert all(task.has_tag_by_name("tag") for task in dev_tasks)
        assert len(dev_tasks) > 0
        
        # Combined filtering
        combined_filter = TaskFilter(status=[Status(StatusType.OPEN)], tags=[Tag(name="tag")])
        combined_tasks = service.filter_tasks(tasks, combined_filter)
        assert all(
            task.status.status_type == StatusType.OPEN and task.has_tag_by_name("tag")
            for task in combined_tasks
        )
        assert len(combined_tasks) > 0
    
    def test_statistics_integration(self, isolated_test_files):
        """Test statistics calculation across multiple files."""
        service = TaskService()
        
        files = service.find_task_files(isolated_test_files)
        file_objs = [FileRepository().get_file(f) for f in files]
        tasks = FileRepository()._tasks.values()
        stats = service.get_task_statistics(tasks)
        
        # Verify comprehensive statistics
        assert stats['total'] > 10
        assert len(stats['by_file']) >= 3
        assert stats['with_due_date'] > 0
        assert stats['with_tags'] > 0
        
        # Verify status distribution
        assert 'OPEN' in stats['by_status']
        assert 'CHECKED' in stats['by_status']
        assert stats['by_status']['OPEN'] > 0
        
        # Verify priority distribution
        assert 0 in stats['by_priority']  # Some tasks have no priority
        assert any(p > 0 for p in stats['by_priority'].keys())  # Some have priority


@pytest.mark.integration
class TestUnicodeAndSpecialContent:
    """Test handling of Unicode content and special characters."""

    def parse_and_unpack(self, file_path):
        """Helper to parse a file and return its tasks."""
        file_parser = FileParser()
        file = file_parser.parse_file(str(file_path))
        return file.get_tasks()
    
    def test_unicode_content_integration(self, isolated_test_files):
        """Test parsing and handling of Unicode content in tasks."""
        tasks = self.parse_and_unpack(isolated_test_files / 'unicode_file.xit')
        
        # Should successfully parse all tasks
        assert len(tasks) == 4
        
        # Verify Unicode content is preserved
        descriptions = [str(task.description) for task in tasks]
        unicode_found = any(
            any(ord(char) > 127 for char in desc) 
            for desc in descriptions
        )
        assert unicode_found
        
        # Test filtering with Unicode tags
        service = TaskService()
        from xitkit.tags import Tag
        unicode_filter = TaskFilter(tags=[Tag(name="文档")])
        filtered = service.filter_tasks(tasks, unicode_filter)
        
        # Should handle Unicode tag filtering
        # (Result depends on implementation, but should not crash)
        assert isinstance(filtered, list)
        
        # Test statistics with Unicode content
        stats = service.get_task_statistics(tasks)
        assert stats['total'] == 4
        assert stats['with_tags'] > 0


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Test error handling in integrated workflows."""
    
    def test_mixed_valid_invalid_files(self, temp_dir):
        """Test handling mix of valid and invalid files."""
        # Create valid file
        valid_content = """[ ] Valid task 1
[x] Valid task 2"""
        valid_file = create_test_file(temp_dir, "valid.xit", valid_content)
        
        # Create file with mixed valid/invalid content
        mixed_content = """[ ] Valid task
[*] Invalid status
[ ]Invalid spacing
 [x] Invalid leading space
[ ] Another valid task
[x] Final valid task"""
        mixed_file = create_test_file(temp_dir, "mixed.xit", mixed_content)
        
        # Create unsupported file type
        unsupported_file = create_test_file(temp_dir, "unsupported.txt", "[ ] Should be ignored")
        
        # Test file discovery (should include only supported types)
        discovery_service = FileDiscoveryService()
        files = discovery_service.resolve_file_paths(
            directory=temp_dir,
            specified_files=None
        )
        
        # Should find .xit files but not .txt
        xit_files = [f for f in files if f.endswith('.xit')]
        assert len(xit_files) == 2
        assert not any(f.endswith('.txt') for f in files)
        
        # Test parsing (should handle invalid lines gracefully)
        service = TaskService()
        tasks = service.load_tasks(files)
        
        # Should parse valid tasks and skip invalid ones
        assert len(tasks) == 5  # 2 from valid + 3 valid from mixed
        
        # All parsed tasks should be valid
        for task in tasks:
            assert task.status.status_type.name in ["OPEN", "CHECKED", "ONGOING", "OBSOLETE", "IN_QUESTION"]
            assert task.priority.level >= 0
    
    def test_empty_and_malformed_files(self, temp_dir):
        """Test handling of empty and malformed files."""
        # Create empty file
        empty_file = create_test_file(temp_dir, "empty.xit", "")
        
        # Create file with only headers and blank lines
        headers_only = create_test_file(temp_dir, "headers.xit", """
Header 1

Header 2


Another Header


""")
        
        # Create file with only invalid content
        invalid_only = create_test_file(temp_dir, "invalid.xit", """
[*] Invalid status
[] Missing space
 [x] Leading space
[x]Missing space after
""")
        
        # Test parsing all files
        service = TaskService()
        files = [str(empty_file), str(headers_only), str(invalid_only)]
        tasks = service.load_tasks(files)
        
        # Should handle gracefully without crashing
        assert isinstance(tasks, list)
        assert len(tasks) == 0  # No valid tasks
        
        # Test statistics with empty results
        stats = service.get_task_statistics(tasks)
        assert stats['total'] == 0
        assert stats['by_status'] == {}
        assert stats['by_priority'] == {}


@pytest.mark.integration
class TestPerformanceIntegration:
    """Test performance with larger datasets."""
    
    @pytest.mark.slow
    def test_large_file_handling(self, temp_dir):
        """Test handling of files with many tasks."""
        # Generate a large file with many tasks
        lines = ["Large Task File", ""]
        
        for i in range(1000):
            status_chars = [' ', 'x', '@', '~', '?']
            status = status_chars[i % len(status_chars)]
            priority = "!" * (i % 4)  # 0-3 priority levels
            tags = f"#tag{i % 10} #category{i % 5}"
            due_date = f"-> 2025-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}"
            
            task_line = f"[{status}] {priority} Task {i} {tags} {due_date}".strip()
            lines.append(task_line)
            
            # Add some multi-line tasks
            if i % 100 == 0:
                lines.append("    This is a continuation line")
                lines.append("    With more details")
        
        large_content = "\n".join(lines)
        large_file = create_test_file(temp_dir, "large.xit", large_content)
        
        # Test parsing performance
        import time
        start_time = time.time()
        
        service = TaskService()
        tasks = service.load_tasks([str(large_file)])
        
        parse_time = time.time() - start_time
        
        # Should parse successfully
        assert len(tasks) == 1000
        
        # Should complete in reasonable time (adjust threshold as needed)
        assert parse_time < 5.0  # 5 seconds max for 1000 tasks
        
        # Test filtering performance
        start_time = time.time()
        
        from xitkit.status import Status, StatusType
        filters = TaskFilter(status=[Status(StatusType.OPEN)])
        filtered_tasks = service.filter_tasks(tasks, filters)
        
        filter_time = time.time() - start_time
        
        # Should filter successfully
        assert len(filtered_tasks) > 0
        assert filter_time < 1.0  # 1 second max for filtering
        
        # Test statistics performance
        start_time = time.time()
        
        stats = service.get_task_statistics(tasks)
        
        stats_time = time.time() - start_time
        
        # Should calculate stats successfully
        assert stats['total'] == 1000
        assert stats_time < 1.0  # 1 second max for stats
    
    @pytest.mark.slow
    def test_many_files_handling(self, temp_dir):
        """Test handling of many small files."""
        # Create many small files
        files = []
        for i in range(100):
            content = f"""File {i} Tasks
[ ] Task {i}.1 #file{i}
[x] Task {i}.2 #file{i}
[@] Task {i}.3 #file{i} -> 2025-12-{(i % 30) + 1:02d}"""
            
            file_path = create_test_file(temp_dir, f"tasks_{i:03d}.xit", content)
            files.append(str(file_path))
        
        # Test discovery performance
        import time
        start_time = time.time()
        
        service = TaskService()
        discovered_files = service.find_task_files(temp_dir)
        
        discovery_time = time.time() - start_time
        
        # Should discover all files
        assert len(discovered_files) == 100
        assert discovery_time < 2.0  # 2 seconds max for discovery
        
        # Test batch parsing performance
        start_time = time.time()
        
        tasks = service.load_tasks(discovered_files)
        
        parse_time = time.time() - start_time
        
        # Should parse all tasks
        assert len(tasks) == 300  # 3 tasks per file * 100 files
        assert parse_time < 10.0  # 10 seconds max for 100 files


class TestFormatRecreation:
    """" Test if Tasks, that are read from a file are formatted recreating the input."""

    @pytest.mark.parametrize("task_line", [
        "[ ] Open task",
        "[x] Completed task with 3 trailing spaces   ",
        "[@] Ongoing task",
        "[~] Obsolete task",
        "[?] Task in question",
        "[ ] !! High priority task #urgent",
        "[ ] Task due tomorrow -> 2025-10-20",
        "[ ] Task with #tags -> 2025-10-21",
        "[ ] Task with #multiple #tags",
        "[ ] Simple task\n    task description\n    continues here",
        "[ ] ..!!! Task with a lot of leading dots.",
        "[ ] !..... Task with a lot of trailing dots."
    ])
    def test_recreation(self, task_line):
        """Test that tasks can be recreated correctly after being written to file.
        
        This test verifies the complete roundtrip: parse task → create Task object → 
        write to file → parse again → verify equality.
        """
        import tempfile
        import os
        from pathlib import Path
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xit', delete=False) as temp_file:
            temp_file.write(task_line + '\n')
            temp_file_path = temp_file.name
        
        try:
            # Parse the original task
            parser = FileParser()
            files = parser.parse_files([temp_file_path])
            original_tasks = [t for f in files for t in f.get_tasks()]
            
            assert len(original_tasks) == 1
            original_task = original_tasks[0]
            
            # Convert the task back to checkbox format
            recreated_line = original_task.to_checkbox_format()
            
            # Write the recreated line to a new temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xit', delete=False) as temp_file2:
                temp_file2.write(recreated_line + '\n')
                temp_file2_path = temp_file2.name
            
            try:
                # Parse the recreated task
                files = parser.parse_files([temp_file2_path])
                recreated_tasks = [t for f in files for t in f.get_tasks()]
                
                assert len(recreated_tasks) == 1
                recreated_task = recreated_tasks[0]
                
                # Compare key properties (ignoring file path and line number)
                assert original_task.status.status_type == recreated_task.status.status_type
                assert original_task.priority.level == recreated_task.priority.level
                
                # For description, normalize whitespace to handle multiline -> single line conversion
                original_desc_normalized = ' '.join(original_task.description.text.split())
                recreated_desc_normalized = ' '.join(recreated_task.description.text.split())
                assert original_desc_normalized == recreated_desc_normalized
                
                # Compare tags
                original_tag_names = {tag.name for tag in original_task.tags}
                recreated_tag_names = {tag.name for tag in recreated_task.tags}
                assert original_tag_names == recreated_tag_names
                
                # Compare tag values if any
                for orig_tag in original_task.tags:
                    matching_recreated = next(
                        (tag for tag in recreated_task.tags if tag.name == orig_tag.name), 
                        None
                    )
                    assert matching_recreated is not None
                    assert orig_tag.value == matching_recreated.value
                
                # Compare due dates
                if original_task.due_date and recreated_task.due_date:
                    assert original_task.due_date.implied_date == recreated_task.due_date.implied_date
                elif original_task.due_date is None:
                    assert recreated_task.due_date is None
                else:
                    # One has due date, other doesn't - this is a failure
                    assert False, f"Due date mismatch: original={original_task.due_date}, recreated={recreated_task.due_date}"
                
                # Verify the recreated line matches the expected format structure
                # (Allow for minor formatting differences but ensure core elements are preserved)
                if original_task.has_priority:
                    assert '!' in recreated_line
                if original_task.has_tags:
                    assert '#' in recreated_line
                if original_task.has_due_date:
                    assert '->' in recreated_line
                    
            finally:
                # Clean up second temporary file
                os.unlink(temp_file2_path)
                
        finally:
            # Clean up first temporary file
            os.unlink(temp_file_path)
