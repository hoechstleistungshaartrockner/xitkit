"""Tests for the FileParser class."""

import pytest
import tempfile
from pathlib import Path

from xitkit.fileparser import FileParser, ParseContext
from xitkit.task import Task
from xitkit.status import StatusType
from xitkit.patterns import *
from tests.conftest import create_test_file, assert_task_equal


class TestFileParserBasics:
    """Test basic FileParser functionality."""
    
    def test_parser_creation(self):
        """Test creating a FileParser instance."""
        parser = FileParser()
        assert parser.tasks == []
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
class TestBasicParsing:
    """Test basic checkbox parsing."""
    
    def test_parse_simple_checkboxes(self, temp_dir, file_parser):
        """Test parsing simple checkbox formats."""
        content = """[ ] Open task
[x] Done task
[@] Ongoing task
[~] Obsolete task
[?] Question task"""
        
        test_file = create_test_file(temp_dir, "simple.xit", content)
        tasks = file_parser.parse_file(str(test_file))
        
        assert len(tasks) == 5
        assert tasks[0].status.status_type == StatusType.OPEN
        assert tasks[1].status.status_type == StatusType.CHECKED
        assert tasks[2].status.status_type == StatusType.ONGOING
        assert tasks[3].status.status_type == StatusType.OBSOLETE
        assert tasks[4].status.status_type == StatusType.IN_QUESTION
    
    def test_parse_with_descriptions(self, temp_dir, file_parser):
        """Test parsing checkboxes with descriptions."""
        content = """[ ] First task
[x] Second completed task
[@] Third ongoing task with longer description"""
        
        test_file = create_test_file(temp_dir, "desc.xit", content)
        tasks = file_parser.parse_file(str(test_file))
        
        assert len(tasks) == 3
        assert tasks[0].description.text == "First task"
        assert tasks[1].description.text == "Second completed task"
        assert tasks[2].description.text == "Third ongoing task with longer description"
    
    def test_parse_empty_descriptions(self, temp_dir, file_parser):
        """Test parsing checkboxes with empty descriptions."""
        content = """[ ] 
[x] 
[@]        
[~] Task with description"""
        
        test_file = create_test_file(temp_dir, "empty.xit", content)
        tasks = file_parser.parse_file(str(test_file))
        
        assert len(tasks) == 4
        assert tasks[0].description.text == ""
        assert tasks[1].description.text == ""
        assert tasks[2].description.text == ""  # Parser trims whitespace after checkbox
        assert tasks[3].description.text == "Task with description"


class TestInvalidFormats:
    """Test parsing of invalid checkbox formats."""
    
    def test_invalid_status_characters(self, temp_dir, file_parser):
        """Test that invalid status characters are ignored."""
        content = """[ ] Valid open task
[*] Invalid status
[o] Invalid lowercase
[X] Invalid uppercase
[a] Invalid letter
[ ] Another valid task"""
        
        test_file = create_test_file(temp_dir, "invalid.xit", content)
        tasks = file_parser.parse_file(str(test_file))
        
        # Should only parse the valid tasks
        assert len(tasks) == 2
        assert tasks[0].description.text == "Valid open task"
        assert tasks[1].description.text == "Another valid task"
    
    def test_invalid_spacing(self, temp_dir, file_parser):
        """Test that invalid spacing is ignored."""
        content = """[ ] Valid task
[] Missing space inside
[  ] Extra space inside
[ x ] Extra spaces around status
[ ]Invalid missing space after
 [x] Leading whitespace
    [x] Leading indentation
[ ] Valid task at end"""
        
        test_file = create_test_file(temp_dir, "spacing.xit", content)
        tasks = file_parser.parse_file(str(test_file))
        
        # Should only parse the valid tasks
        assert len(tasks) == 2
        assert tasks[0].description.text == "Valid task"
        assert tasks[1].description.text == "Valid task at end"


class TestPriorityParsing:
    """Test parsing of priority indicators."""
    
    def test_parse_priorities(self, temp_dir, file_parser):
        """Test parsing various priority formats."""
        content = """[ ] ! Priority 1 task
[ ] !! Priority 2 task
[ ] !!! Priority 3 task
[ ] !!!!!!!!!! Priority 10 task
[ ] . No priority (dots only)
[ ] .. Still no priority
[ ] ..! Priority 1 with leading dots
[ ] !!. Priority 2 with trailing dots
[ ] Regular task without priority"""
        
        test_file = create_test_file(temp_dir, "priority.xit", content)
        tasks = file_parser.parse_file(str(test_file))
        
        assert len(tasks) == 9
        assert tasks[0].priority.level == 1
        assert tasks[1].priority.level == 2
        assert tasks[2].priority.level == 3
        assert tasks[3].priority.level == 10
        assert tasks[4].priority.level == 0  # Dots only = no priority
        assert tasks[5].priority.level == 0  # Multiple dots only = no priority
        assert tasks[6].priority.level == 1  # Leading dots
        assert tasks[7].priority.level == 2  # Trailing dots
        assert tasks[8].priority.level == 0  # No priority
    
    def test_invalid_priority_formats(self, temp_dir, file_parser):
        """Test invalid priority formats are treated as description."""
        content = """[ ] .!. Invalid dots on both sides
[ ] !.! Invalid mixed pattern
[ ] !This is description not priority
[ ] .This is also description
[ ]    ! Spaces before priority (invalid)
[ ]    . Spaces before dots (invalid)
[ ] ! Valid priority
[ ] !Missing space after (description)"""
        
        test_file = create_test_file(temp_dir, "invalid_priority.xit", content)
        tasks = file_parser.parse_file(str(test_file))
        
        assert len(tasks) == 8
        assert tasks[0].priority.level == 0  # Invalid format
        assert tasks[1].priority.level == 0  # Invalid format
        assert tasks[2].priority.level == 0  # No space after exclamation
        assert tasks[3].priority.level == 0  # No space after dot
        assert tasks[4].priority.level == 0  # Spaces before priority
        assert tasks[5].priority.level == 0  # Spaces before dots
        assert tasks[6].priority.level == 1  # Valid priority
        assert tasks[7].priority.level == 0  # Missing space after


class TestDueDateParsing:
    """Test parsing of due dates."""
    
    def test_parse_due_dates(self, temp_dir, file_parser):
        """Test parsing various due date formats."""
        content = """[ ] Task -> 2025-12-31
[ ] Task -> 2025-12
[ ] Task -> 2025
[ ] Task -> 2025-W42
[ ] Task -> 2025-Q4
[ ] Task -> 2025/12/31
[ ] Task -> 2025/W42
[ ] Task with description -> 2025-12-31 and more text"""
        
        test_file = create_test_file(temp_dir, "dates.xit", content)
        tasks = file_parser.parse_file(str(test_file))
        
        assert len(tasks) == 8
        assert tasks[0].due_date.normalized_date == "2025-12-31"
        assert tasks[1].due_date.normalized_date == "2025-12-31"  # 2025-12 implies end of month
        assert tasks[2].due_date.normalized_date == "2025-12-31"  # 2025 implies end of year
        assert tasks[3].due_date.normalized_date is not None  # Week format
        assert tasks[4].due_date.normalized_date is not None  # Quarter format
        assert tasks[5].due_date.normalized_date == "2025-12-31"  # Slash format
        assert tasks[6].due_date.normalized_date is not None  # Slash week format
        assert tasks[7].due_date.normalized_date == "2025-12-31"
    
    def test_invalid_due_date_formats(self, temp_dir, file_parser):
        """Test invalid due date formats are not recognized."""
        content = """[ ] Task → 2025-12-31 (wrong arrow)
[ ] Task > 2025-12-31 (missing hyphen)
[ ] Task -> 2025-12-31very (text after)
[ ] Task -> 2025-12-31T10:00 (time)"""
        
        test_file = create_test_file(temp_dir, "invalid_dates.xit", content)
        tasks = file_parser.parse_file(str(test_file))
        
        # All tasks should be parsed but none should have due dates
        assert len(tasks) == 4
        for task in tasks:
            assert task.due_date is None


class TestTagParsing:
    """Test parsing of tags."""
    
    def test_parse_basic_tags(self, temp_dir, file_parser):
        """Test parsing basic tag formats."""
        content = """[ ] Task with #simple tag
[ ] Task with #multiple #tags here
[ ] Task with #UPPERCASE and #lowercase
[ ] Task with #numbers123 and #123numbers
[ ] Task with #dashes-allowed and #underscores_allowed
[ ] Task with #unicode_täg and #日本語"""
        
        test_file = create_test_file(temp_dir, "tags.xit", content)
        tasks = file_parser.parse_file(str(test_file))
        
        assert len(tasks) == 6
        assert any(tag.name == "simple" for tag in tasks[0].tags)
        assert any(tag.name == "multiple" for tag in tasks[1].tags) and any(tag.name == "tags" for tag in tasks[1].tags)
        assert any(tag.name == "UPPERCASE" for tag in tasks[2].tags) and any(tag.name == "lowercase" for tag in tasks[2].tags)
        assert any(tag.name == "numbers123" for tag in tasks[3].tags) and any(tag.name == "123numbers" for tag in tasks[3].tags)
        assert any(tag.name == "dashes-allowed" for tag in tasks[4].tags) and any(tag.name == "underscores_allowed" for tag in tasks[4].tags)
        assert any(tag.name == "unicode_täg" for tag in tasks[5].tags) and any(tag.name == "日本語" for tag in tasks[5].tags)
    
    def test_parse_tags_with_values(self, temp_dir, file_parser):
        """Test parsing tags with values."""
        content = """[ ] Task #tag=value simple
[ ] Task #tag="quoted value" with quotes
[ ] Task #tag='single quoted' value
[ ] Task #empty= and #another=""
[ ] Task #mix=unquoted #quoted="with spaces" #single='also spaces'"""
        
        test_file = create_test_file(temp_dir, "tag_values.xit", content)
        tasks = file_parser.parse_file(str(test_file))
        
        assert len(tasks) == 5
        assert any(tag.name == "tag" and tag.value == "value" for tag in tasks[0].tags)
        assert any(tag.name == "tag" and tag.value == "quoted value" for tag in tasks[1].tags)
        assert any(tag.name == "tag" and tag.value == "single quoted" for tag in tasks[2].tags)
        assert any(tag.name == "mix" and tag.value == "unquoted" for tag in tasks[4].tags)
        assert any(tag.name == "quoted" and tag.value == "with spaces" for tag in tasks[4].tags)
        assert any(tag.name == "single" and tag.value == "also spaces" for tag in tasks[4].tags)
    
    def test_invalid_tags(self, temp_dir, file_parser):
        """Test that invalid tag formats are not recognized."""
        content = """[ ] Task with # (empty tag)
[ ] Task with #=value (no name)
[ ] Task with #="quoted" (no name)
[ ] Task with #tag='unclosed quote
[ ] Task with #tag="mismatched quote'
[ ] Valid #tag after invalid ones"""

        test_file = create_test_file(temp_dir, "invalid_tags.xit", content)
        tasks = file_parser.parse_file(str(test_file))

        assert len(tasks) == 6
        assert len(tasks[0].tags) == 0  # No tags for empty tag
        assert len(tasks[1].tags) == 0  # No tags for no name
        assert len(tasks[2].tags) == 0  # No tags for no name
        assert len(tasks[3].tags) == 1  # Parser extracts tag name even with unclosed quote
        assert tasks[3].tags[0].name == "tag"
        assert len(tasks[4].tags) == 1  # Parser extracts tag name even with mismatched quote
        assert tasks[4].tags[0].name == "tag"
        assert len(tasks[5].tags) == 1  # Valid tag
        assert tasks[5].tags[0].name == "tag"


class TestMultilineParsing:
    """Test parsing of multi-line task descriptions."""
    
    def test_parse_continuation_lines(self, temp_dir, file_parser):
        """Test parsing tasks with continuation lines."""
        content = """[ ] Multi-line task ...
    with continuation line
    and another line
[ ] Another task with ...
    single continuation
[ ] Single line task
[ ] Final multi-line ...
    with multiple ...
    continuation lines here"""
        
        test_file = create_test_file(temp_dir, "multiline.xit", content)
        tasks = file_parser.parse_file(str(test_file))
        
        assert len(tasks) == 4
        
        # First task
        expected_desc = "Multi-line task ...\nwith continuation line\nand another line"
        assert tasks[0].description.text == expected_desc
        
        # Second task
        expected_desc = "Another task with ...\nsingle continuation"
        assert tasks[1].description.text == expected_desc
        
        # Third task (single line)
        assert tasks[2].description.text == "Single line task"
        
        # Fourth task
        expected_desc = "Final multi-line ...\nwith multiple ...\ncontinuation lines here"
        assert tasks[3].description.text == expected_desc
    
    def test_invalid_continuation_lines(self, temp_dir, file_parser):
        """Test that invalid continuation lines are not included."""
        content = """[ ] Task with valid continuation ...
    exactly 4 spaces
[ ] Task with invalid ...
 1 space (invalid)
  2 spaces (invalid)
   3 spaces (invalid)
     5 spaces (invalid)
	tab instead of spaces (invalid)
[ ] Next task should not include invalid lines"""
        
        test_file = create_test_file(temp_dir, "invalid_continuation.xit", content)
        tasks = file_parser.parse_file(str(test_file))
        
        assert len(tasks) == 3
        assert tasks[0].description.text == "Task with valid continuation ...\nexactly 4 spaces"
        assert tasks[1].description.text == "Task with invalid ..."
        assert tasks[2].description.text == "Next task should not include invalid lines"
    
    def test_continuation_with_tags_and_dates(self, temp_dir, file_parser):
        """Test that continuation lines can contain tags and dates."""
        content = """[ ] Task with continuation ...
    containing #tags and -> 2025-12-31
    and more #additional tags"""
        
        test_file = create_test_file(temp_dir, "continuation_meta.xit", content)
        tasks = file_parser.parse_file(str(test_file))
        
        assert len(tasks) == 1
        task = tasks[0]
        
        expected_desc = "Task with continuation ...\ncontaining #tags and -> 2025-12-31\nand more #additional tags"
        assert task.description.text == expected_desc
        assert task.due_date.normalized_date == "2025-12-31"
        assert any(tag.name == "tags" for tag in task.tags)
        assert any(tag.name == "additional" for tag in task.tags)


class TestFileParsing:
    """Test file-level parsing functionality."""
    
    def test_parse_nonexistent_file(self, file_parser):
        """Test parsing a nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            file_parser.parse_file("/nonexistent/file.xit")
    
    def test_parse_unsupported_file_type(self, temp_dir, file_parser):
        """Test parsing unsupported file type raises ValueError."""
        test_file = create_test_file(temp_dir, "test.txt", "[ ] Task")
        
        with pytest.raises(ValueError, match="Unsupported file type"):
            file_parser.parse_file(str(test_file))
    
    def test_parse_supported_file_types(self, temp_dir, file_parser):
        """Test parsing both .xit and .md files."""
        content = "[ ] Test task"
        
        xit_file = create_test_file(temp_dir, "test.xit", content)
        md_file = create_test_file(temp_dir, "test.md", content)
        
        xit_tasks = file_parser.parse_file(str(xit_file))
        md_tasks = file_parser.parse_file(str(md_file))
        
        assert len(xit_tasks) == 1
        assert len(md_tasks) == 1
    
    def test_parse_multiple_files(self, temp_dir, file_parser):
        """Test parsing multiple files."""
        file1 = create_test_file(temp_dir, "file1.xit", "[ ] Task 1\n[x] Task 2")
        file2 = create_test_file(temp_dir, "file2.xit", "[@] Task 3")
        file3 = create_test_file(temp_dir, "invalid.txt", "[ ] Task 4")  # Invalid type
        
        files = [str(file1), str(file2), str(file3)]
        tasks = file_parser.parse_files(files)
        
        # Should get 3 tasks from the 2 valid files
        assert len(tasks) == 3
        assert tasks[0].description.text == "Task 1"
        assert tasks[1].description.text == "Task 2"
        assert tasks[2].description.text == "Task 3"
    
    def test_parse_utf8_content(self, temp_dir, file_parser, utf8_xit_content):
        """Test parsing UTF-8 content."""
        test_file = create_test_file(temp_dir, "utf8.xit", utf8_xit_content)
        tasks = file_parser.parse_file(str(test_file))
        
        # Should successfully parse Unicode tasks
        assert len(tasks) > 0
        
        # Check for Unicode content
        unicode_found = False
        for task in tasks:
            if any(ord(char) > 127 for char in task.description.text):
                unicode_found = True
                break
        assert unicode_found


class TestGroupsAndHeaders:
    """Test parsing of groups and headers."""
    
    def test_parse_with_headers(self, temp_dir, file_parser):
        """Test parsing tasks with group headers."""
        content = """Work Tasks
[ ] Complete project
[x] Review code

Personal Tasks
[ ] Buy groceries
[ ] Call dentist

[ ] Task without header"""
        
        test_file = create_test_file(temp_dir, "headers.xit", content)
        tasks = file_parser.parse_file(str(test_file))
        
        # Headers should not affect task parsing
        assert len(tasks) == 5
        assert tasks[0].description.text == "Complete project"
        assert tasks[1].description.text == "Review code"
        assert tasks[2].description.text == "Buy groceries"
        assert tasks[3].description.text == "Call dentist"
        assert tasks[4].description.text == "Task without header"
    
    def test_parse_with_blank_lines(self, temp_dir, file_parser):
        """Test parsing with blank lines between groups."""
        content = """[ ] Task 1
[ ] Task 2

[ ] Task 3 after blank

[ ] Task 4

           
[ ] Task 5 after whitespace-only line"""
        
        test_file = create_test_file(temp_dir, "blanks.xit", content)
        tasks = file_parser.parse_file(str(test_file))
        
        assert len(tasks) == 5
        for i in range(5):
            task_num = i + 1
            expected_base = f"Task {task_num}"
            actual_desc = tasks[i].description.text
            assert actual_desc == expected_base or expected_base in actual_desc


class TestComplexScenarios:
    """Test complex parsing scenarios."""
    
    def test_parse_complex_mixed_content(self, temp_dir, file_parser, complex_xit_content):
        """Test parsing complex content with all features."""
        test_file = create_test_file(temp_dir, "complex.xit", complex_xit_content)
        tasks = file_parser.parse_file(str(test_file))
        
        # Should parse valid tasks and skip invalid ones
        assert len(tasks) > 0
        
        # Check that we have tasks with various features
        has_priority = any(task.priority.level > 0 for task in tasks)
        has_tags = any(len(task.tags) > 0 for task in tasks)
        has_due_date = any(task.due_date is not None for task in tasks)
        has_multiline = any('\n' in task.description.text for task in tasks)
        
        assert has_priority
        assert has_tags
        assert has_due_date
        assert has_multiline
    
    def test_line_number_tracking(self, temp_dir, file_parser):
        """Test that line numbers are correctly tracked."""
        content = """[ ] Task 1 on line 1

[ ] Task 2 on line 3
Invalid line
[ ] Task 3 on line 5
[ ] Task 4 is Multi-line on line 6 ...
    continuation on line 7
[ ] Task 5 on line 8
[ ] Task 6 is on line 9 with a full line of whitespace following ...
                                                                        
[ ] Task 7 on line 11 with a line of whitespace in between
    
    this is still part of task 7 in line 13
"""
        
        test_file = create_test_file(temp_dir, "lines.xit", content)
        tasks = file_parser.parse_file(str(test_file))
        
        assert len(tasks) == 7
        assert tasks[0].location.line_numbers == range(1, 2)
        assert tasks[1].location.line_numbers == range(3, 4)
        assert tasks[2].location.line_numbers == range(5, 6)
        assert tasks[3].location.line_numbers == range(6, 8)  # Multi-line task
        assert tasks[4].location.line_numbers == range(8, 9)
        assert tasks[5].location.line_numbers == range(9, 11)
        assert tasks[6].location.line_numbers == range(11, 14)
    
    def test_file_path_tracking(self, temp_dir, file_parser):
        """Test that file paths are correctly tracked."""
        content = "[ ] Test task"
        test_file = create_test_file(temp_dir, "tracked.xit", content)
        
        tasks = file_parser.parse_file(str(test_file))
        
        assert len(tasks) == 1
        assert tasks[0].location.file_path == Path(str(test_file))
        assert tasks[0].location.line_numbers == range(1, 2)


class TestRegexPatterns:
    """Test the regex patterns used by the parser."""
    
    def test_checkbox_pattern(self, file_parser):
        """Test the checkbox regex pattern."""
        pattern = CHECKBOX_PATTERN
        
        # Valid matches
        assert pattern.match("[ ] Task")
        assert pattern.match("[x] Task")
        assert pattern.match("[@] Task")
        assert pattern.match("[~] Task")
        assert pattern.match("[?] Task")
        
        # Invalid matches
        assert not pattern.match("[] Task")
        assert not pattern.match("[ Task")
        assert not pattern.match(" [ ] Task")
    
    def test_priority_pattern(self, file_parser):
        """Test the priority regex pattern."""
        pattern = PRIORITY_PATTERN
        
        # Valid matches - note the pattern expects space at start
        assert pattern.match(" ! Task")
        assert pattern.match(" !! Task")
        assert pattern.match(" !!! Task")
        assert pattern.match(" .! Task")
        assert pattern.match(" !!. Task")
        
        # Invalid matches
        assert not pattern.match(" !Task")  # No space after priority markers
    
    def test_due_date_pattern(self, file_parser):
        """Test the due date regex pattern."""
        pattern = DUE_DATE_PATTERN
        
        test_cases = [
            "Task -> 2025-12-31",
            "Task -> 2025-12",
            "Task -> 2025",
            "Task -> 2025-W42",
            "Task -> 2025-Q4",
            "Task -> 2025/12/31",
        ]
        
        for case in test_cases:
            match = pattern.search(case)
            assert match is not None
    
    def test_tag_pattern(self, file_parser):
        """Test the tag regex pattern."""
        pattern = TAG_PATTERN
        
        test_cases = [
            "#simple",
            "#with-dashes",
            "#with_underscores",
            "#123numbers",
            "#tag=value",
            "#tag='quoted value'",
            "#tag=\"double quoted\"",
        ]
        
        for case in test_cases:
            match = pattern.search(case)
            assert match is not None
    
    def test_continuation_pattern(self, file_parser):
        """Test the continuation line pattern."""
        pattern = CONTINUATION_PATTERN
        
        # Valid continuations (exactly 4 spaces)
        assert pattern.match("    content")
        assert pattern.match("    ")
        
        # Invalid continuations
        assert not pattern.match("   content")   # 3 spaces
        assert not pattern.match("\tcontent")    # Tab
        assert not pattern.match("content")      # No indentation
        # Note: "     content" (5 spaces) matches because the pattern is ^    (.*)$
        # and the extra space becomes part of the captured content