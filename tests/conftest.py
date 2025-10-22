"""Shared test fixtures and utilities."""

import pytest
import tempfile
from pathlib import Path
from typing import Union

from xitkit.task import Task
from xitkit.services import TaskService, FileDiscoveryService
from xitkit.formatter import TaskFormatter
from xitkit.fileparser import FileParser


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def task_service():
    """Create a TaskService instance for testing."""
    return TaskService()


@pytest.fixture
def file_service():
    """Create a FileDiscoveryService instance for testing."""
    return FileDiscoveryService()


@pytest.fixture
def task_formatter():
    """Create a TaskFormatter instance for testing."""
    return TaskFormatter()


@pytest.fixture
def file_parser():
    """Create a FileParser instance for testing."""
    return FileParser()


@pytest.fixture
def utf8_xit_content():
    """UTF-8 content for testing file parsing."""
    return """Unicode Tasks
[ ] 测试任务 #中文 #test
[x] ✓ Completed task with emoji #emoji #done
[@] Русская задача #русский #ongoing -> 2025-12-31
[~] Ελληνικό έργο #ελληνικά #obsolete"""


@pytest.fixture
def complex_xit_content():
    """Complex content for testing file parsing."""
    return """Complex Task File

# Project Tasks
[ ] ! High priority setup #setup #priority -> 2025-12-31
    Set up development environment
    Install dependencies and tools
    
[x] Basic implementation #development
[@] !! Critical ongoing work #critical #development #ongoing
    This is a multi-line task
    with continuation lines
    
# Personal Tasks
[ ] Schedule meeting #personal #work
[~] Old requirement #obsolete

# Tags and Dates
[ ] Task with value tags #priority:high #category:work #due:urgent
[ ] Task with multiple dates -> 2025-11-30 #reminder:2025-11-15"""


@pytest.fixture
def sample_tasks():
    """Create a list of sample tasks for testing."""
    return [
        Task("/test1.xit", 1, "Open task", "OPEN", 0, ["#work"], None),
        Task("/test1.xit", 2, "High priority task", "OPEN", 2, ["#work", "#urgent"], "2025-12-31"),
        Task("/test1.xit", 3, "Done task", "DONE", 1, ["#personal"], None),
        Task("/test2.xit", 1, "Ongoing task", "ONGOING", 0, ["#project"], "2025-11-30"),
        Task("/test2.xit", 2, "Obsolete task", "OBSOLETE", 0, ["#old"], None),
    ]


@pytest.fixture
def stats_sample_tasks():
    """Create a diverse list of tasks for statistics testing."""
    return [
        Task("/test.xit", 1, "Open task", "OPEN", 0, ["#work"], None),
        Task("/test.xit", 2, "High priority", "OPEN", 2, ["#urgent"], "2025-12-31"), 
        Task("/test.xit", 3, "Medium priority", "OPEN", 1, ["#work"], None),
        Task("/test.xit", 4, "Done task", "DONE", 0, ["#personal"], None),
        Task("/test.xit", 5, "Done priority", "DONE", 1, ["#work"], None),
        Task("/test.xit", 6, "Ongoing task", "ONGOING", 0, ["#project"], "2025-11-30"),
        Task("/test.xit", 7, "Obsolete task", "OBSOLETE", 0, ["#old"], None),
    ]


def create_test_file(temp_dir: Path, filename: str, content: str) -> Path:
    """Create a test file with the given content.
    
    Args:
        temp_dir: The temporary directory to create the file in
        filename: The name of the file to create
        content: The content to write to the file
        
    Returns:
        Path to the created file
    """
    file_path = temp_dir / filename
    file_path.write_text(content, encoding='utf-8')
    return file_path


def assert_task_equal(task1: Task, task2: Task) -> None:
    """Assert that two tasks are equal in all important aspects.
    
    Args:
        task1: First task to compare
        task2: Second task to compare
    """
    assert task1.file_path == task2.file_path
    assert task1.line_number == task2.line_number
    assert task1.description == task2.description
    assert task1.status == task2.status
    assert task1.priority == task2.priority
    assert task1.tags == task2.tags
    assert task1.due_date == task2.due_date