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

from xitkit.services import TaskService, TaskFilter
from xitkit.task import Task
from xitkit.status import Status, StatusType
from xitkit.priority import Priority
from xitkit.tags import Tag
from xitkit.duedate import DueDate
from xitkit.exceptions import FileNotSupportedError
from xitkit.location import Location


class TestTaskService:
    """Test cases for the TaskService class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = TaskService()
        
    def test_init(self):
        """Test TaskService initialization."""
        assert hasattr(self.service, 'parser')
        assert hasattr(self.service, 'date_parser')
        
    def test_find_task_files_default_directory(self, isolated_test_files):
        """Test finding task files in default directory."""
        
        os.chdir(isolated_test_files)
        files = self.service.find_task_files()
        
        # Should find .xit and .md files
        assert len(files) > 10
        assert all(f.endswith(('.xit', '.md')) for f in files)
        assert any("valid_status.xit" in f for f in files)
                
    def test_find_task_files_specific_directory(self, isolated_test_files):
        """Test finding task files in specific directory."""
        
        files = self.service.find_task_files(isolated_test_files)
        
        assert len(files) > 10
        assert all(f.endswith(('.xit', '.md')) for f in files)
        assert any("valid_tags.xit" in f for f in files)
            
            
    def test_filter_tasks_by_status(self, sample_tasks):
        """Test filtering tasks by status."""
        # Create mock tasks
        tasks = sample_tasks

        # Filter by ONGOING status
        filter_ongoing = TaskFilter(status=[Status(StatusType.ONGOING)])
        filtered = self.service.filter_tasks(tasks, filter_ongoing)

        assert len(filtered) == 1
        assert filtered[0].status.status_type == StatusType.ONGOING

    def test_filter_tasks_by_priority(self, sample_tasks):
        """Test filtering tasks by priority."""
        tasks = sample_tasks

        # Filter by priority level 2
        filter_high = TaskFilter(priority=Priority(level=2))
        filtered = self.service.filter_tasks(tasks, filter_high)

        assert len(filtered) == 1
        assert filtered[0].priority.level == 2
        
        # Filter by priority level 1
        filter_high = TaskFilter(priority=Priority(level=1))
        filtered = self.service.filter_tasks(tasks, filter_high)
        
        assert len(filtered) == 3
        found_levels = set(t.priority.level for t in filtered)
        assert found_levels == {1, 2}

    def test_filter_tasks_by_tags(self, sample_tasks):
        """Test filtering tasks by tags."""
        tasks = sample_tasks
        
        # Filter by work tag
        filter_work = TaskFilter(tags=[Tag(name="work")])
        filtered = self.service.filter_tasks(tasks, filter_work)
        
        assert len(filtered) == 3

    def test_filter_tasks_by_due_date(self, sample_tasks):
        """Test filtering tasks by due date."""
        tasks = sample_tasks

        # Filter by due date
        due_date = DueDate.from_string("2024-11-30")
        filter_due = TaskFilter(due_on=due_date)
        filtered = self.service.filter_tasks(tasks, filter_due)

        assert len(filtered) == 1
        assert filtered[0].due_date.implied_date == "2024-11-30"
        
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
        
    def test_get_task_statistics_with_tasks(self, sample_tasks):
        """Test statistics for a list of tasks."""
        tasks = sample_tasks
        
        stats = self.service.get_task_statistics(tasks)
        
        assert stats['total'] == 7
        assert stats['by_status']['OPEN'] == 3
        assert stats['by_status']['CHECKED'] == 2
        assert stats['by_file']['/test.xit'] == 5
        assert stats['by_file']['/other.xit'] == 1
        assert stats['by_file']['todo.xit'] == 1  # Tasks without file set
        assert stats['with_tags'] == 7
        assert stats['with_due_date'] == 2
        assert stats['overdue'] == 2
            


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