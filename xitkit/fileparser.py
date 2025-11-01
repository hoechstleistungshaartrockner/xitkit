import re
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from .task import Task
from .status import Status, StatusType
from .priority import Priority
from .tags import Tag
from .duedate import DueDate
from .config import get_config
from .exceptions import FileNotSupportedError, ParseError
from .patterns import *


@dataclass
class ParseContext:
    """Context for tracking parsing state across lines.
    
    This class maintains state information while parsing a file,
    including the current task being processed and line tracking.
    
    Attributes:
        current_task: The task currently being parsed (may span multiple lines)
        current_group: The name of the current group/section header
        line_number: Current line number being processed (1-based)
        file_path: Path to the file being parsed
    """
    current_task: Optional[Task] = None
    current_group: Optional[str] = None
    line_number: int = 0
    file_path: str = ""


class FileParser:
    """Efficient parser for .md and .xit files containing tasks with checkboxes.
    
    This parser implements the task format specification defined in syntax_guide.txt,
    supporting checkboxes with different statuses, priorities, due dates, tags,
    multi-line descriptions, and UTF-8 text.
    
    The parser is designed to be efficient by:
    - Using compiled regex patterns for fast matching
    - Processing files line by line without loading everything into memory
    - Maintaining minimal state during parsing
    - Skipping invalid lines rather than raising exceptions
    
    Example:
        >>> parser = FileParser()
        >>> tasks = parser.parse_file("tasks.xit")
        >>> print(f"Found {len(tasks)} tasks")
    """
    
    # Status mapping from checkbox character to StatusType enum
    # These are the only valid status characters according to the spec
    STATUS_MAP = {
        ' ': StatusType.OPEN,        # [ ] - Open/uncompleted task
        'x': StatusType.CHECKED,     # [x] - Completed task
        '@': StatusType.ONGOING,     # [@] - Currently in progress
        '~': StatusType.OBSOLETE,    # [~] - No longer relevant
        '?': StatusType.IN_QUESTION  # [?] - Needs clarification
    }
        
    def __init__(self):
        """Initialize the file parser.
        
        Creates an empty task list that will be populated during parsing.
        """
        self.tasks: List[Task] = []
        
    def parse_file(self, file_path: str) -> List[Task]:
        """Parse a single file and return list of tasks.
        
        Args:
            file_path: Path to the .md or .xit file to parse
            
        Returns:
            List of Task objects found in the file
            
        Raises:
            FileNotFoundError: If the specified file doesn't exist
            ValueError: If the file type is not supported (.md or .xit)
            
        Example:
            >>> parser = FileParser()
            >>> tasks = parser.parse_file("todo.xit")
            >>> for task in tasks:
            ...     print(f"[{task.status}] {task.description}")
        """
        # Validate file existence and type
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        if path.suffix not in ['.md', '.xit']:
            raise ValueError(f"Unsupported file type: {path.suffix}")
            
        # Reset task list for this parsing session
        self.tasks = []
        context = ParseContext(file_path=file_path)
        
        # Read all lines at once for efficiency
        # Using UTF-8 encoding to support international characters
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Process all lines in the file
        self._parse_lines(lines, context)
        return self.tasks
    
    def parse_files(self, file_paths: List[str]) -> List[Task]:
        """Parse multiple files and return combined list of tasks.
        
        Args:
            file_paths: List of file paths to parse
            
        Returns:
            Combined list of Task objects from all valid files
            
        Note:
            Invalid files are skipped with a warning message.
            This allows parsing to continue even if some files are problematic.
            
        Example:
            >>> parser = FileParser()
            >>> tasks = parser.parse_files(["todo.xit", "notes.md", "tasks.xit"])
            >>> print(f"Found {len(tasks)} total tasks across all files")
        """
        all_tasks = []
        for file_path in file_paths:
            try:
                tasks = self.parse_file(file_path)
                all_tasks.extend(tasks)
            except (FileNotFoundError, ValueError) as e:
                # Continue processing other files even if one fails
                print(f"Warning: Skipping file {file_path}: {e}")
        return all_tasks
    
    def _parse_lines(self, lines: List[str], context: ParseContext) -> None:
        """Parse all lines in a file.
        
        This is the main parsing loop that processes each line according to
        the task format specification. It maintains state for multi-line tasks
        and handles different line types (checkboxes, continuations, headers, etc.).
        
        Args:
            lines: List of all lines from the file
            context: Parsing context to maintain state
        """
        i = 0
        while i < len(lines):
            context.line_number = i + 1  # Convert to 1-based line numbering
            line = lines[i].rstrip('\n\r')  # Remove line endings
            
            # Check if this is a continuation line for the current task
            # Continuation lines must be exactly 4 spaces + content
            if context.current_task and self._is_continuation_line(line):
                self._handle_continuation_line(line, context)
                i += 1
                continue
                
            # Finalize current task if we have one and we're not continuing it
            # This happens when we encounter a non-continuation line
            if context.current_task:
                self.tasks.append(context.current_task)
                context.current_task = None
            
            # Check if this is a blank line (resets group context)
            if BLANK_LINE_PATTERN.match(line):
                context.current_group = None
                i += 1
                continue
                
            # Check if this is a checkbox line (the main content we're parsing)
            checkbox_match = CHECKBOX_PATTERN.match(line)
            if checkbox_match:
                self._parse_checkbox_line(checkbox_match, context)
                i += 1
                continue
                
            # Check if this is a group header (not starting with whitespace or '[')
            # Group headers are lines that don't start with whitespace or brackets
            if line and not line.startswith((' ', '\t', '[')):
                context.current_group = line.strip()
                
            i += 1
            
        # Don't forget to add the last task if the file doesn't end with a non-task line
        if context.current_task:
            self.tasks.append(context.current_task)
    
    def _parse_checkbox_line(self, match: re.Match, context: ParseContext) -> None:
        """Parse a line containing a checkbox.
        
        This method handles the core parsing logic for checkbox lines,
        extracting the status, priority, description, due date, and tags.
        
        Args:
            match: Regex match object from CHECKBOX_PATTERN
            context: Current parsing context
        """
        status_char = match.group(1)  # Extract the status character
        rest_of_line = match.group(2)  # Everything after the checkbox
        
        # Validate status character against allowed values
        if status_char not in self.STATUS_MAP:
            return  # Invalid status, skip this line
            
        # Must have exactly one space after checkbox (per specification)
        if not rest_of_line.startswith(' '):
            return  # Invalid format, skip this line
            
        # Parse priority using the Priority class which handles dots correctly
        priority_obj = Priority.from_line(rest_of_line) or Priority()
        
        # Remove priority from content for further parsing
        content = rest_of_line[1:]  # Remove the mandatory space
        if priority_obj.level > 0:
            # Remove the priority pattern from the content
            match = PRIORITY_PATTERN.match(rest_of_line)
            if match:
                content = match.group(2)[1:]  # Skip the space after priority
        
        due_date = self._parse_due_date(content)
        tags = self._parse_tags(content)
        
        # Create Status object
        status = Status(self.STATUS_MAP[status_char])
        
        # tags are already Tag objects from _parse_tags method
        tag_objects = tags if tags else []
        
        # Create task object with all parsed information
        task = Task(
            description=content.strip(),  # Clean up whitespace
            file=context.file_path,
            line_number=context.line_number,
            status=status,
            priority=priority_obj,
            tags=tag_objects,
            due_date=due_date
        )
        
        # Store as current task (might be continued on next lines)
        context.current_task = task
    
    def _is_continuation_line(self, line: str) -> bool:
        """Check if line is a continuation of previous task description.
        
        Continuation lines must start with exactly 4 spaces according to the spec.
        
        Args:
            line: Line to check
            
        Returns:
            True if this is a valid continuation line
        """
        return bool(CONTINUATION_PATTERN.match(line))
    
    def _handle_continuation_line(self, line: str, context: ParseContext) -> None:
        """Handle a continuation line for the current task.
        
        Continuation lines can contain additional content, tags, and due dates.
        They extend the description of the current task.
        
        Args:
            line: The continuation line to process
            context: Current parsing context
        """
        if not context.current_task:
            return  # No current task to continue
            
        # Add current line number to the task's line numbers
        context.current_task.line_numbers.append(context.line_number)
            
        match = CONTINUATION_PATTERN.match(line)
        if match:
            continuation_content = match.group(1)  # Content after the 4 spaces
            
            # Parse additional tags and due dates from continuation lines
            additional_tags = self._parse_tags(continuation_content)
            context.current_task.tags.extend(additional_tags)
            
            # Only set due date if not already set (first occurrence wins)
            if not context.current_task.due_date:
                due_date_str = self._parse_due_date(continuation_content)
                if due_date_str:
                    context.current_task.due_date = DueDate.from_string(due_date_str)
            
            # Append to description with newline separator
            if context.current_task.description.text:
                context.current_task.description.append_text('\n' + continuation_content)
            else:
                context.current_task.description.set_text(continuation_content)
    
    
    def _parse_due_date(self, content: str) -> Optional[str]:
        """Parse due date from content.
        
        Due dates follow the format: -> YYYY[-/][MM[-/]DD]
        Also supports: -> YYYY-W## (week), -> YYYY-Q# (quarter)
        
        Args:
            content: Content to search for due dates
            
        Returns:
            Due date string if found, None otherwise
            
        Example:
            >>> parser._parse_due_date("Task -> 2025-12-31 (urgent)")
            "2025-12-31"
        """
        match = DUE_DATE_PATTERN.search(content)
        if match:
            return match.group(1)  # Return the captured date string
        return None
    
    def _parse_tags(self, content: str) -> List[Tag]:
        """Parse all tags from content.
        
        Tags start with # and can have values: #tag or #tag=value
        Values can be quoted: #tag="value with spaces"
        Supports Unicode characters for international tags.
        
        Args:
            content: Content to search for tags
            
        Returns:
            List of Tag objects parsed from the content
            
        Example:
            >>> parser._parse_tags("Task #work #priority=high #tag='quoted value'")
            [Tag(name="work"), Tag(name="priority", value="high"), Tag(name="tag", value="quoted value")]
        """
        return Tag.from_line(content)


def parse_file(file_path: str) -> List[Task]:
    """Convenience function to parse a single file.
    
    Args:
        file_path: Path to the file to parse
        
    Returns:
        List of Task objects found in the file
        
    Example:
        >>> from xitkit.fileparser import parse_file
        >>> tasks = parse_file("tasks.xit")
        >>> print(f"Found {len(tasks)} tasks")
    """
    parser = FileParser()
    return parser.parse_file(file_path)


def parse_files(file_paths: List[str]) -> List[Task]:
    """Convenience function to parse multiple files.
    
    Args:
        file_paths: List of file paths to parse
        
    Returns:
        Combined list of Task objects from all files
        
    Example:
        >>> from xitkit.fileparser import parse_files
        >>> tasks = parse_files(["todo.xit", "notes.md"])
        >>> print(f"Found {len(tasks)} total tasks")
    """
    parser = FileParser()
    return parser.parse_files(file_paths)