"""Tests for the FileParser class."""

import pytest
import tempfile
from pathlib import Path

from xitkit.fileparser import *
from xitkit.task import Task
from xitkit.status import StatusType
from xitkit.patterns import *
from tests.conftest import create_test_file, assert_task_equal

class ParserTestBase:
    """Base class for FileParser tests."""
    
    def parse_and_unpack(self, file_path):
        """Helper to parse a file and return its tasks."""
        file_parser = FileParser()
        file = file_parser.parse_file(str(file_path))
        return file.get_tasks()

class TestFileParserBasics:
    """Test basic FileParser functionality."""
    
    def test_parser_creation(self):
        """Test creating a FileParser instance."""
        parser = FileParser()
        assert isinstance(parser, FileParser)
        assert hasattr(parser, 'STATUS_MAP')
        # Patterns are now imported from patterns module, not parser attributes
        assert CHECKBOX_PATTERN is not None
    
    def test_status_map(self):
        """Test status character mapping."""
        parser = FileParser()

        expected_mapping = {
            ' ': StatusType.OPEN,
            'x': StatusType.CHECKED,
            '@': StatusType.ONGOING,
            '~': StatusType.OBSOLETE,
            '?': StatusType.IN_QUESTION
        }

        assert parser.STATUS_MAP == expected_mapping

class TestValidFormats(ParserTestBase):
    """Test basic checkbox parsing."""
    
    def test_parse_valid_status(self, isolated_test_files):
        """Test parsing simple checkboxes with different statuses."""
        tasks = self.parse_and_unpack(isolated_test_files / "valid_status.xit")

        assert len(tasks) == 5
        assert tasks[0].status.status_type == StatusType.OPEN
        assert tasks[1].status.status_type == StatusType.ONGOING
        assert tasks[2].status.status_type == StatusType.OBSOLETE
        assert tasks[3].status.status_type == StatusType.CHECKED
        assert tasks[4].status.status_type == StatusType.IN_QUESTION
        
        assert tasks[0].description.text == "Open Task"
        assert tasks[1].description.text == "Ongoing Task"
        assert tasks[2].description.text == "Obsolete Task"
        assert tasks[3].description.text == "Done Task"
        assert tasks[4].description.text == "Questionable Task"

        assert tasks[0].location.line_numbers == range(2, 3)
        assert tasks[0].location.file_path == isolated_test_files / "valid_status.xit"
        assert tasks[0].location.section == "Tasks with valid statuses"
    
    
    def test_parse_white_space(self, isolated_test_files):
        """Test parsing checkboxes with varying white space."""
        tasks = self.parse_and_unpack(isolated_test_files / "white_space.xit")
        
        assert len(tasks) == 4
        assert tasks[0].description.text == "    Task with four leading spaces"
        assert tasks[1].description.text == "Task with four trailing spaces    "
        assert tasks[2].description.text == "    Task with both four leading and trailing spaces    "
        assert tasks[3].description.text == ""


    def test_parse_priorities(self, isolated_test_files):
        """Test parsing various priority formats."""
        tasks = self.parse_and_unpack(isolated_test_files / "valid_priority.xit")
        
        assert len(tasks) == 9
        assert tasks[0].priority.level == 1
        assert tasks[1].priority.level == 2
        assert tasks[2].priority.level == 3
        assert tasks[3].priority.level == 10
        assert tasks[4].priority.level == 0  # Dots only = no priority
        assert tasks[4].priority.leading_dots == 1
        assert tasks[5].priority.level == 0  # Multiple dots only = no priority
        assert tasks[5].priority.leading_dots == 2
        assert tasks[6].priority.level == 1  # Leading dots
        assert tasks[6].priority.leading_dots == 2
        assert tasks[7].priority.level == 2  # Trailing dots
        assert tasks[7].priority.trailing_dots == 1
        assert tasks[8].priority.level == 0  # No priority
    
    def test_parse_due_dates(self, isolated_test_files):
        """Test parsing various due date formats."""
        tasks = self.parse_and_unpack(isolated_test_files / "valid_due_dates.xit")
        
        assert len(tasks) == 12
        assert tasks[0].due_date.normalized_date == "2024-12-31"
        assert tasks[1].due_date.normalized_date == "2024-12-31"  # 2024-12 implies end of month
        assert tasks[2].due_date.normalized_date == "2024-12-31"  # 2024 implies end of year
        assert tasks[3].due_date.normalized_date == "2024-10-20"  # KW42 of 2024
        assert tasks[4].due_date.normalized_date == "2024-12-31"  # Q4 of 2024
        assert tasks[5].due_date.normalized_date == "2024-12-31"  # Slash format
        assert tasks[6].due_date.normalized_date == "2024-10-20"  # Slash week format (KW42 of 2024)
        assert tasks[7].due_date.normalized_date == "2024-12-31"
        # Additional tasks with relative dates (yesterday, today, tomorrow, next week)
        assert tasks[8].due_date.normalized_date == "2025-11-02"  # yesterday
        assert tasks[9].due_date.normalized_date == "2025-11-03"  # today  
        assert tasks[10].due_date.normalized_date == "2025-11-04"  # tomorrow
        assert tasks[11].due_date.normalized_date == "2025-11-10"  # next week

    def test_parse_basic_tags(self, isolated_test_files):
        """Test parsing basic tag formats."""
        tasks = self.parse_and_unpack(isolated_test_files / "valid_tags.xit")
        
        assert len(tasks) == 6 + 5  # 6 tasks with simple tags, 5 with tags with values

        # Simple tags
        assert tasks[0].tags[0].name == "simple"
        assert tasks[1].tags[0].name == "multiple"
        assert tasks[1].tags[1].name == "tags"
        assert tasks[2].tags[0].name == "UPPERCASE"
        assert tasks[2].tags[1].name == "lowercase"
        assert tasks[3].tags[0].name == "numbers123"
        assert tasks[3].tags[1].name == "123numbers"
        assert tasks[4].tags[0].name == "dashes-allowed"
        assert tasks[4].tags[1].name == "underscores_allowed"
        assert tasks[5].tags[0].name == "unicode_täg"
        assert tasks[5].tags[1].name == "日本語"

        # Tags with values
        assert tasks[6].tags[0].name == "tag"
        assert tasks[6].tags[0].value == "value"
        assert tasks[7].tags[0].name == "tag"
        assert tasks[7].tags[0].value == "quoted value"
        assert tasks[8].tags[0].name == "tag"
        assert tasks[8].tags[0].value == "single quoted"
        assert tasks[9].tags[0].name == "empty"
        assert tasks[9].tags[0].value == ""
        assert tasks[9].tags[1].name == "another"
        assert tasks[9].tags[1].value == ""
        assert tasks[10].tags[0].name == "mix"
        assert tasks[10].tags[0].value == "unquoted"
        assert tasks[10].tags[1].name == "quoted"
        assert tasks[10].tags[1].value == "with spaces"
        assert tasks[10].tags[2].name == "single"
        assert tasks[10].tags[2].value == "also spaces"

    def test_parse_multiline_tasks(self, isolated_test_files):
        """Test parsing tasks with continuation lines."""
        tasks = self.parse_and_unpack(isolated_test_files / "valid_multiline.xit")

        assert len(tasks) == 4
        assert tasks[0].description.text == "Multi-line task ...\nwith continuation line\n123 starts with numbers\n*&$^% starts with symbols\n  starts with two spaces\n. starts with a dot\n! starts with an exclamation that is not priority\n-> 2024-11-11 starts with a due date\n#startstag starts with a tag\nThis is still the same task."
        assert tasks[1].description.text == "finally a next task"
        assert tasks[2].description.text == "Another multi-line task\nwith only one continuation line but after that there's an empty line"
        assert tasks[3].description.text == "Task with continuation line that has only spaces\n\n       \nThis line with text is valid continuation."

        # Check that tags and due dates are correctly parsed from multiline tasks
        assert tasks[0].tags[0].name == "startstag"
        assert tasks[0].due_date.normalized_date == "2024-11-11"

    def test_parse_utf8_content(self, isolated_test_files):
        """Test parsing UTF-8 content."""
        tasks = self.parse_and_unpack(isolated_test_files / "unicode_file.xit")
        
        # Should successfully parse Unicode tasks
        assert len(tasks) > 0
        
        # Check for Unicode content
        unicode_found = False
        for task in tasks:
            if any(ord(char) > 127 for char in task.description.text):
                unicode_found = True
                break
        assert unicode_found

    def test_sectioned_file(self, isolated_test_files):
        """Test parsing tasks under different sections."""
        parser = FileParser()
        file_obj = parser.parse_file(str(isolated_test_files / "sectioned_file.xit"))
        tasks = file_obj.get_tasks()

        assert len(file_obj.sections) == 3
        assert "First Section" in file_obj.sections
        assert "Second Section" in file_obj.sections
        assert "Third Section" in file_obj.sections
        for s in file_obj.sections.values():
            assert len(s.tasks) == 1

        assert len(tasks) == 3
        assert tasks[0].description.text == "Task in first section"
        assert tasks[0].location.section == "First Section"
        
        assert tasks[1].description.text == "Task in second section"
        assert tasks[1].location.section == "Second Section"
        
        assert tasks[2].description.text == "Task in third section"
        assert tasks[2].location.section == "Third Section"


class TestInvalidFormats(ParserTestBase):
    """Test parsing of invalid checkbox formats."""
    
    def test_invalid_status_characters(self, isolated_test_files):
        """Test that invalid status characters are ignored."""
        tasks = self.parse_and_unpack(isolated_test_files / "invalid_status.xit")
        
        # Should only parse the valid tasks
        assert len(tasks) == 0
    
    def test_invalid_spacing(self, isolated_test_files):
        """Test that invalid spacing is ignored."""
        tasks = self.parse_and_unpack(isolated_test_files / "invalid_spacing.xit")
        
        # Should only parse the valid tasks
        assert len(tasks) == 1
        assert tasks[0].description.text == "Valid spacing task (valid)"
    
    def test_invalid_priority_formats(self, isolated_test_files):
        """Test invalid priority formats are treated as description."""
        tasks = self.parse_and_unpack(isolated_test_files / "invalid_priority.xit")
        
        assert len(tasks) == 7
        assert tasks[0].priority.level == 0  # Invalid format
        assert tasks[0].description.text == ".!. Invalid dots on both sides"
        assert tasks[1].priority.level == 0  # Invalid format
        assert tasks[1].description.text == "!.! Invalid mixed pattern"
        assert tasks[2].priority.level == 0  # No space after exclamation
        assert tasks[2].description.text == "!This is description not priority"
        assert tasks[3].priority.level == 0  # No space after dot
        assert tasks[3].description.text == ".This is also description"
        assert tasks[4].priority.level == 0  # Spaces before priority
        assert tasks[4].description.text == "   ! Spaces before priority (invalid)"
        assert tasks[5].priority.level == 0  # Spaces before dots
        assert tasks[5].description.text == "   . Spaces before dots (invalid)"
        assert tasks[6].priority.level == 0  # Missing space after
        assert tasks[6].description.text == "!Missing space after (description)"
 
    def test_invalid_due_date_formats(self, isolated_test_files):
        """Test invalid due date formats are not recognized."""
        tasks = self.parse_and_unpack(isolated_test_files / "invalid_due_dates.xit")
                
        # All tasks should be parsed but none should have due dates
        assert len(tasks) == 11
        for task in tasks:
            assert task.due_date is None

    
    def test_invalid_tags(self, isolated_test_files):
        """Test that invalid tag formats are not recognized."""
        tasks = self.parse_and_unpack(isolated_test_files / "invalid_tags.xit")

        assert len(tasks) == 5
        for task in tasks:
            assert len(task.tags) == 0

    def test_invalid_multilines(self, isolated_test_files):
        """Test that invalid continuation lines are not included."""
        tasks = self.parse_and_unpack(isolated_test_files / "invalid_multiline.xit")
        
        assert len(tasks) == 5
        for t in tasks:
            assert t.description.text == "Task with a valid start" # continuations are cut off as they are invalid.
        for t in tasks[:4]:
            assert t.location.section == "Tasks with invalid multi-line descriptions"
        assert tasks[4].location.section == "no spaces before continuation (invalid) this will be interpreted as a section title"


class TestFileParsing(ParserTestBase):
    """Test file-level parsing functionality."""
    
    def test_parse_nonexistent_file(self, file_parser):
        """Test parsing a nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            file_parser.parse_file("/nonexistent/file.xit")
    
    def test_parse_empty_file(self, isolated_test_files, file_parser):
        """Test parsing an empty file returns no tasks."""
        empty_file = isolated_test_files / "empty_file.xit"
        empty_file.touch()  # Ensure the file is empty
        file_obj = file_parser.parse_file(str(empty_file))
        
        tasks = file_obj.get_tasks()
        assert len(tasks) == 0
        
        sections = list(file_obj.sections.values())
        assert len(sections) == 1
        assert sections[0].title == "To Do"
        assert sections[-1].title == "To Do"
    
    def test_parse_unsupported_file_type(self, temp_dir, file_parser):
        """Test parsing unsupported file type raises ValueError."""
        test_file = create_test_file(temp_dir, "test.txt", "[ ] Task")
        
        with pytest.raises(ValueError, match="Unsupported file type"):
            file_parser.parse_file(str(test_file))
    
    def test_parse_markdown_file(self, isolated_test_files):
        """Test parsing a markdown file."""
        tasks = self.parse_and_unpack(isolated_test_files / "markdown_file.md")
        
        assert len(tasks) == 3
        assert tasks[0].description.text == "valid task inside a code block"
        assert tasks[1].description.text == "valid task"
        assert tasks[2].description.text == "valid multi-line task\ncontinuation line"

        # check location
        assert tasks[0].location.file_path == isolated_test_files / "markdown_file.md"
        assert tasks[0].location.line_numbers == range(4, 5)
        assert tasks[1].location.line_numbers == range(7, 8)
        assert tasks[2].location.line_numbers == range(8, 10)

        # check sections
        assert tasks[0].location.section == "# Markdown File with Tasks" # if no section occurs in the codeblock, it should inherit the last markdown header
        assert tasks[1].location.section == "This is a section title inside a code block"
        assert tasks[2].location.section == "This is a section title inside a code block"

    def test_parse_multiple_files(self, isolated_test_files):
        """Test parsing multiple files."""
        file1 = isolated_test_files / "valid_status.xit"
        file2 = isolated_test_files / "valid_priority.xit"
        file3 = isolated_test_files / "invalid_status.xit"  # Should be ignored
        
        files = [str(file1), str(file2), str(file3)]
        file_objs = FileParser().parse_files(files)
        tasks = [t for f in file_objs for t in f.get_tasks()]
        
        # Should get 3 tasks from the 2 valid files
        assert len(tasks) == 5 + 9 # 5 from valid_status, 9 from valid_priority
    
class TestWriteFile:
    """Test writing tasks back to file."""
    
    def test_write_tasks_to_file(self, tmpdir):
        """Test writing tasks to a file."""
        file_path = tmpdir / "write_test.xit"

        section1 = Section("First Section")
        section1.add_task(
            Task(description="Task one in first section")
            )
        assert section1.n_lines == 3  # 2 lines for title and blank + 1 task line
        section2 = Section("Second Section")
        section2.add_task(
            Task(description="Task one in second section")
            )
        assert section2.n_lines == 3  # 2 lines for title and blank + 1 task line
        
        # Create file and add sections
        file = File(file_path)
        file.add_section(section1)
        file.add_section(section2)
        file.write()
        
        tasks = file.get_tasks()
        assert len(tasks) == 2
        for t in tasks:
            assert t.location.file_path == file_path
        assert tasks[0].location.section == "First Section"
        assert tasks[1].location.section == "Second Section"
        assert tasks[0].location.line_numbers == range(2, 3)
        assert tasks[1].location.line_numbers == range(5, 6)
        
        # Read back the file and verify contents
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        expected_content = """First Section
[ ] Task one in first section

Second Section
[ ] Task one in second section

"""
        assert content == expected_content
        
class TestTaskRemoval:
    """Test removing tasks from file."""
    
    def test_remove_task_from_file(self, isolated_test_files):
        """Test removing a task from a file."""
        file_path = isolated_test_files / "valid_status.xit"
        
        # read the file
        file_parser = FileParser()
        file_obj = file_parser.parse_file(str(file_path))
        tasks = file_obj.get_tasks()
        assert len(tasks) == 5
        
        # Remove the second task
        task_to_remove = tasks[1]
        file_obj.remove_task(task_to_remove)
        
        # get section
        section = file_obj.sections["Tasks with valid statuses"]
        assert len(section.tasks) == 4
        assert section.n_lines == 6  # 1 title + 1 blank + 4 tasks
        assert task_to_remove not in section.tasks
        assert section.line_numbers == range(1, 7)
        file_obj.write()
        
        # verify remaining tasks have correct line numbers
        updated_tasks = file_obj.get_tasks()
        
        assert len(updated_tasks) == 4
        assert updated_tasks[0].description.text == "Open Task"
        assert updated_tasks[0].location.line_numbers == range(2, 3)  # Updated line number
        assert updated_tasks[1].location.line_numbers == range(3, 4)
        assert updated_tasks[2].location.line_numbers == range(4, 5)
        assert updated_tasks[3].location.line_numbers == range(5, 6)
        
        # read back the file and verify the task is removed
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        expected_content = """Tasks with valid statuses
[ ] Open Task
[~] Obsolete Task
[x] Done Task
[?] Questionable Task

"""
        assert content == expected_content
        
    def test_remove_nonexistent_task(self, isolated_test_files):
        """Test removing a task that does not exist in the file."""
        file_path = isolated_test_files / "valid_status.xit"
        
        content_before = file_path.read_text(encoding='utf-8')
        
        # read the file
        file_parser = FileParser()
        file_obj = file_parser.parse_file(str(file_path))
        tasks = file_obj.get_tasks()
        assert len(tasks) == 5
        
        # Create a task that is not in the file
        non_existent_task = Task(description="Non-existent task")
        
        # Attempt to remove it and verify no error occurs and file remains unchanged
        file_obj.remove_task(non_existent_task)
        file_obj.write()
        
        # read back the file and verify contents are unchanged
        content_after = file_path.read_text(encoding='utf-8')

        assert content_after == content_before
        
    def test_remove_task_from_section(self, isolated_test_files):
        """Test removing a task from a section with only one task."""
        file_path = isolated_test_files / "sectioned_file.xit"

        # read the file
        file_parser = FileParser()
        file_obj = file_parser.parse_file(str(file_path))
        tasks = file_obj.get_tasks()
        assert len(tasks) == 3
        n_lines_before = file_obj.n_lines
        
        # Remove the task from the second section
        task_to_remove = tasks[1]
        file_obj.remove_task(task_to_remove)
        n_lines_after = file_obj.n_lines
        assert n_lines_after == n_lines_before - 3  # 3 lines removed (title, task, blank)
        
        assert len(file_obj.sections) == 2  # One section should be removed if empty
        assert "Second Section" not in file_obj.sections
        
        file_obj.write()
        
        # read back the file and verify the task is removed
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        expected_content = """First Section
[ ] Task in first section

Third Section
[ ] Task in third section

"""
        assert content == expected_content
        
    def test_remove_task_by_section(self, isolated_test_files):
        """Test removing a task from a specific section."""
        file_path = isolated_test_files / "sectioned_file.xit"

        # read the file
        file_parser = FileParser()
        file_obj = file_parser.parse_file(str(file_path))
        tasks = file_obj.get_tasks()
        assert len(tasks) == 3
        n_lines_before = file_obj.n_lines
        
        # Remove the task from the second section
        task_to_remove = tasks[1]
        section2 = file_obj.sections["Second Section"]
        section2.remove_task(task_to_remove)
        
        assert len(file_obj.sections) == 2  # One section should be removed if empty
        assert "Second Section" not in file_obj.sections
        n_lines_after = file_obj.n_lines
        assert n_lines_after == n_lines_before - 3  # 3 lines removed (title, task, blank)
        
        file_obj.write()
        
        # read back the file and verify the task is removed
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        expected_content = """First Section
[ ] Task in first section

Third Section
[ ] Task in third section

"""
        assert content == expected_content
        
    
