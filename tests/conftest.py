"""Shared test fixtures and utilities."""

import pytest
import tempfile
from pathlib import Path
from typing import Union

from xitkit.task import Task
from xitkit.services import TaskService, FileDiscoveryService
from xitkit.formatter import TaskFormatter
from xitkit.fileparser import FileParser
from xitkit.file_repository import FileRepository

@pytest.fixture(autouse=True)
def reset_file_repository():
    """Reset the FileRepository singleton before each test."""
    FileRepository().reset()
    yield

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
def sample_tasks():
    """Create a list of sample tasks for testing."""
    return [
        Task("Open task", location=("/test1.xit", 1), status="OPEN", priority=0, tags=["#work"], due_date=None),
        Task("High priority task", location=("/test1.xit", 2), status="OPEN", priority=2, tags=["#work", "#urgent"], due_date="2024-12-31"),
        Task("Done task", location=("/test1.xit", 3), status="DONE", priority=1, tags=["#personal"], due_date=None),
        Task("Ongoing task", location=("/test2.xit", 1), status="ONGOING", priority=0, tags=["#project"], due_date="2024-11-30"),
        Task("Obsolete task", location=("/test2.xit", 2), status="OBSOLETE", priority=0, tags=["#old"], due_date=None),
    ]


@pytest.fixture
def stats_sample_tasks():
    """Create a diverse list of tasks for statistics testing."""
    return [
        Task("Open task", location=("/test.xit", 1), status="OPEN", priority=0, tags=["#work"], due_date=None),
        Task("High priority", location=("/test.xit", 2), status="OPEN", priority=2, tags=["#urgent"], due_date="2024-12-31"),
        Task("Medium priority", location=("/test.xit", 3), status="OPEN", priority=1, tags=["#work"], due_date=None),
        Task("Done task", location=("/test.xit", 4), status="DONE", priority=0, tags=["#personal"], due_date=None),
        Task("Done priority", location=("/test.xit", 5), status="DONE", priority=1, tags=["#work"], due_date=None),
        Task("Ongoing task", location=("/test.xit", 6), status="ONGOING", priority=0, tags=["#project"], due_date="2024-11-30"),
        Task("Obsolete task", location=("/test.xit", 7), status="OBSOLETE", priority=0, tags=["#old"], due_date=None),
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

@pytest.fixture
def sectionized_file():
    """Create a temporary file with sections for testing."""
    content = """
First Section with 5 Tasks
[ ] Open Task 1 in Section 1 #section1
[@] Task in Progress in Section 1 #section1
[~] Obsolete Task in Section 1 #section1
[x] Done Task in Section 1 #section1
[?] Task in Question in Section 1 #section1

Second Section with 3 Tasks
[ ] Multi-line Task in Section 2
    Continuation line 1
    Continuation line 2
[x] Completed Task in Section 2 #section2
[ ] !! High Priority Task in Section 2 #section2 #priority

    """
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "todo.xit"
        file_path.write_text(content, encoding='utf-8')
        yield file_path
        
        
from datetime import datetime, timedelta

# Define date variables before they're used in f-strings
yesterday_date = (datetime.now() - timedelta(days=1)).date()
today_date = datetime.now().date()
tomorrow_date = (datetime.now() + timedelta(days=1)).date()
one_week_date = (datetime.now() + timedelta(weeks=1)).date()

files_dict = {"valid_status.xit": """Tasks with valid statuses
[ ] Open Task
[@] Ongoing Task
[~] Obsolete Task
[x] Done Task
[?] Questionable Task

""",
              "valid_no_sections.xit": """[ ] Open Task""",
              "white_space.xit": """Tasks with white space descriptions
[ ]     Task with four leading spaces
[ ] Task with four trailing spaces    
[ ]     Task with both four leading and trailing spaces    
[ ] 

""",
              "invalid_status.xit": """Tasks with invalid statuses
[!] Invalid Status Task 1
[#] Invalid Status Task 2
[+] Invalid Status Task 3
[*] Invalid Status Task 4
[X] Invalid Status Task 5
[o] Invalid Status Task 6
[a] Invalid Status Task 7

""",
                "invalid_spacing.xit": """Tasks with invalid spacing
[ ] Valid spacing task (valid)
    [ ] Leading space before bracket (invalid)
[  ] Extra space inside brackets (invalid)
[ x ] Space around status character (invalid)
    [ ] Leading tab before bracket (invalid)
[	 ] Tab inside brackets (invalid)

""",
                "valid_priority.xit": """Tasks with valid priorities
[ ] ! Priority 1 task
[ ] !! Priority 2 task
[ ] !!! Priority 3 task
[ ] !!!!!!!!!! Priority 10 task
[ ] . No priority (dots only)
[ ] .. Still no priority
[ ] ..! Priority 1 with leading dots
[ ] !!. Priority 2 with trailing dots
[ ] Regular task without priority

""",
                "invalid_priority.xit": """Tasks with invalid priorities
[ ] .!. Invalid dots on both sides
[ ] !.! Invalid mixed pattern
[ ] !This is description not priority
[ ] .This is also description
[ ]    ! Spaces before priority (invalid)
[ ]    . Spaces before dots (invalid)
[ ] !Missing space after (description)

""",
                "valid_due_dates.xit": f"""Tasks with valid due dates
[ ] Task -> 2024-12-31
[ ] Task -> 2024-12
[ ] Task -> 2024
[ ] Task -> 2024-W42
[ ] Task -> 2024-Q4
[ ] Task -> 2024/12/31
[ ] Task -> 2024/W42
[ ] Task with description -> 2024-12-31 and more text
[ ] Task due yesterday -> {yesterday_date}
[ ] Task due today -> {today_date}
[ ] Task due tomorrow -> {tomorrow_date}
[ ] Task due next week -> {one_week_date}

""",
                "invalid_due_dates.xit": """Tasks with invalid due dates
[ ] Task → 2024-12-31 (wrong arrow)
[ ] Task > 2024-12-31 (missing hyphen)
[ ] Task - 2024-12-31 (wrong separator)
[ ] Task ->2024-12-31 (missing space)
[ ] Task -> 2024-12-31very (text after)
[ ] Task -> 2024-12-31T10:00 (time)
[ ] Task -> 2024/13/01 (invalid month)
[ ] Task -> 2024/00/10 (invalid month)
[ ] Task -> 2024/12/32 (invalid day)
[ ] Task -> 2024-W54 (invalid week)
[ ] Task -> 2024-Q5 (invalid quarter)

""",
                "valid_tags.xit": """Simple valid tags
[ ] Task with #simple tag
[ ] Task with #multiple #tags here
[ ] Task with #UPPERCASE and #lowercase
[ ] Task with #numbers123 and #123numbers
[ ] Task with #dashes-allowed and #underscores_allowed
[ ] Task with #unicode_täg and #日本語

Tasks with tags having values
[ ] Task #tag=value simple
[ ] Task #tag="quoted value" with quotes
[ ] Task #tag='single quoted' value
[ ] Task #empty= and #another=""
[ ] Task #mix=unquoted #quoted="with spaces" #single='also spaces'

""",
                "valid_multiline.xit": """Tasks with valid multi-line descriptions
[ ] Multi-line task ...
    with continuation line
    123 starts with numbers
    *&$^% starts with symbols
      starts with two spaces
    . starts with a dot
    ! starts with an exclamation that is not priority
    -> 2024-11-11 starts with a due date
    #startstag starts with a tag
    This is still the same task.
[ ] finally a next task
[ ] Another multi-line task
    with only one continuation line but after that there's an empty line

    This is invalid and does not belong to the task.
[ ] Task with continuation line that has only spaces
    
           
    This line with text is valid continuation.

""",
            "invalid_tags.xit": """Tasks with invalid tags
[ ] Task with # (empty tag)
[ ] Task with #=value (no name)
[ ] Task with #="quoted" (no name)
[ ] Task with #tag='unclosed quote
[ ] Task with #tag="mismatched quote'

""",
            "invalid_multiline.xit": """Tasks with invalid multi-line descriptions
[ ] Task with a valid start
 but only one space before continuation (invalid)
[ ] Task with a valid start
  but only two spaces before continuation (invalid)
[ ] Task with a valid start
   but only three spaces before continuation (invalid)
[ ] Task with a valid start
no spaces before continuation (invalid) this will be interpreted as a section title
[ ] Task with a valid start
	but a tab before continuation (invalid)
 
""",
            "markdown_file.md": """# Markdown File with Tasks
This is a markdown file that includes some tasks.
```xit
[ ] valid task inside a code block

This is a section title inside a code block
[ ] valid task
[ ] valid multi-line task
    continuation line
```
Outside the code block, this is just text.
[ ] this seemingly valid task is outside code block and will be ignored.

""",
            "unicode_file.xit": """Unicode Tasks
[ ] 测试任务 #中文 #test
[x] ✓ Completed task with emoji #emoji #done
[@] Русская задача #русский #ongoing -> 2024-12-31
[~] Ελληνικό έργο #ελληνικά #obsolete""",
            "sectioned_file.xit": """First Section
[ ] Task in first section

Second Section
[ ] Task in second section

Third Section
[ ] Task in third section

""",
            "valid_mixed.xit": f"""11 Mixed Tasks
[ ] Open task
[x] Completed task with 3 trailing spaces   
[@] Ongoing task
[~] Obsolete task
[?] Task in question
[ ] !! High priority task #urgent
[ ] Task due tomorrow -> {tomorrow_date}
[ ] Task with #tags -> 2024-10-21
[ ] Task with #multiple #tags
[ ] Simple task
[ ] multi-line
    task description
    continues here

""",
            "valid_another_priority.xit": """To Do
[ ] ! priority 1 task
[ ] !! priority 2 task
[ ] !!! priority 3 task
[ ] !!!! priority 4 task
[ ] !!!!! priority 5 task
[ ] ....! priority 1 task with leading dots
[ ] !.... priority 1 task with trailing dots
[ ] task with no priority
[ ] ... task with no priority but dots

""",
            "valid_another_due_dates.xit": """Due Dates Galore
[ ] Task due 2024-10-20 -> 2024-10-20
[ ] Task with no due date
[ ] Task due 2024-10-21 -> 2024-10-21
[ ] Task due 2024-10-19 -> 2024-10-19

""",
}


@pytest.fixture
def isolated_test_files(temp_dir):
    """Create temporary files with valid and invalid status tasks for testing."""
    for file_name, file_content in files_dict.items():
        file_path = temp_dir / file_name
        file_path.write_text(file_content, encoding='utf-8')
    return temp_dir

