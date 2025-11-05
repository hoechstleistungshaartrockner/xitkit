import re
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
import xitkit.task as task
from .status import Status, StatusType
from .priority import Priority
from .tags import Tag
from .duedate import DueDate
from .config import get_config
from .exceptions import FileNotSupportedError, ParseError
from .patterns import *
from .location import Location


@dataclass
class Section:
    """Represents a section header in the file.
    
    Attributes:
        name: The name of the section
        line_number: The line number where the section appears (1-based)
    """
    title: str
    line_numbers: range = None
    tasks: Optional[List[task.Task]] = None
    n_lines: int = 2 # title line + blank line
    parent_file: Optional['File'] = None

    def __post_init__(self):
        if self.tasks is None:
            self.tasks = []
    
    def extend_line_numbers(self, line_number: int):
        """Extend the line numbers to include a new line number."""
        if self.line_numbers is None:
            self.line_numbers = range(line_number, line_number + 1)
            return
        if line_number == self.line_numbers.stop:
            self.line_numbers = range(self.line_numbers.start, line_number + 1)
            return
        raise ValueError(f"line_number is not consecutive to the current line_numbers range. Current line numbers: {self.line_numbers}, line_number: {line_number}")
    
    def remove_task(self, task: task.Task):
        """
        Remove a task from this section.
        
        Args:
            task: The task to remove.
        
        Returns:
            Number of lines removed from the section.
        """
        if task not in self.tasks:
            return 0
        
        self.tasks.remove(task)
        n_task_lines = task.description.text.count('\n') + 1
        self.n_lines -= n_task_lines
        
        # Update parent file's line count for the task removal
        if self.parent_file is not None:
            self.parent_file.n_lines -= n_task_lines
        
        # Update line_numbers range to reflect the new size
        if self.line_numbers is not None:
            self.line_numbers = range(self.line_numbers.start, self.line_numbers.start + self.n_lines)
            
        # If this section is now empty and has a parent file, remove it from the file
        if len(self.tasks) == 0 and self.parent_file is not None:
            self.parent_file.remove_section(self.title)
            
        return n_task_lines  # Return lines removed for caller to handle file updates
        
    def add_task(self, task: task.Task):
        """Add a task to this section."""
        self.tasks.append(task)
        n_task_lines = task.description.text.count('\n') + 1
        self.n_lines += n_task_lines
        
        # Update parent file's task mapping if it exists
        if self.parent_file is not None:
            self.parent_file._task_to_section[task] = self
        
    def write(self, file_handle) -> None:
        """
        Write the section and its tasks to the given file handle.
        
        Args:
            file_handle: An open file handle to write to
        
        Returns:
            None
        
        """
        file_handle.write(f"{self.title}\n")
        for task in self.tasks:
            file_handle.write(f"{task.to_checkbox_format()}\n")

        file_handle.write("\n")

@dataclass
class File:
    """Represents a parsed file with its tasks and sections.
    
    Attributes:
        path: The file path
        sections: A dictionary mapping section titles to Section objects
    """
    path: str
    sections: dict[str, Section] = None
    n_lines: int = 0
    _task_to_section: dict[task.Task, Section] = None  # Cache for efficient task lookup

    def __post_init__(self):
        if self.sections is None:
            self.sections = {}
        if self._task_to_section is None:
            self._task_to_section = {}
            
    def add_task(self, task: task.Task):
        """Add a task to the file, creating a default section if necessary."""
        section_title = task.location.section or "To Do"
        
        if section_title not in self.sections:
            new_section = Section(title=section_title)
            self.add_section(new_section)
        
        section = self.sections[section_title]
        section.add_task(task)
    
    def add_section(self, section: Section):
        """Add a section to this file."""
        section.parent_file = self  # Set parent reference
        self.sections[section.title] = section
        
        # Update task-to-section mapping
        for task in section.tasks:
            self._task_to_section[task] = section
            
        for idx, task in enumerate(section.tasks):
            task.set_location(Location(self.path, 
                              self.n_lines + idx + 2, # +1 for 1-based, +1 for section title line
                              section.title))

        self.n_lines += section.n_lines
    
    def remove_section(self, section_title: str):
        """Remove a section from the file."""
        if section_title not in self.sections:
            return
        
        section = self.sections[section_title]
        
        # Remove tasks from mapping
        for task in section.tasks:
            if task in self._task_to_section:
                del self._task_to_section[task]
        
        # Update file line count
        self.n_lines -= section.n_lines
        
        # Finally, remove the section
        del self.sections[section_title]
        
        # Update task locations once at the end
        self._update_task_locations()
    
    def get_tasks(self) -> List[task.Task]:
        """Get all tasks in the file across all sections."""
        tasks = []
        for section in self.sections.values():
            tasks.extend(section.tasks)
        return tasks
    
    def remove_task(self, task: task.Task):
        """Remove a task from the file."""
        # Use efficient lookup instead of linear search
        section_to_remove_from = self._task_to_section.get(task)
        
        if section_to_remove_from:
            # Remove from mapping first
            del self._task_to_section[task]
            
            # Remove the task from the section 
            # Note: Section.remove_task() already updates file.n_lines
            section_to_remove_from.remove_task(task)
            
            # Update task locations once at the end
            self._update_task_locations()
    
    def ensure_default_section(self):
        """Ensure there's at least a default 'To Do' section if no sections exist."""
        if not self.sections:
            default_section = Section(title="To Do")
            self.sections["To Do"] = default_section
            
    def _update_task_locations(self):
        """Update location line numbers for all tasks after file structure changes."""
        current_line = 1
        
        # Clear and rebuild task mapping
        self._task_to_section.clear()
        
        for section in self.sections.values():
            # Update section line numbers
            section.line_numbers = range(current_line, current_line + section.n_lines)
            
            # Update task locations within this section
            task_line = current_line + 1  # Skip section title line
            for task in section.tasks:
                # Rebuild task mapping
                self._task_to_section[task] = section
                
                task_lines = task.description.text.count('\n') + 1
                task.set_location((
                    self.path,
                    range(task_line, task_line + task_lines),
                    section.title
                ))
                task_line += task_lines
            
            current_line += section.n_lines
            
    def write(self) -> bool:
        """Write the file back to disk"""
        
        with open(self.path, 'w', encoding='utf-8') as f:
            for section in self.sections.values():
                section.write(f)
        return True



@dataclass
class ParseContext:
    """Context for tracking parsing state across lines.
    
    This class maintains state information while parsing a file,
    including the current task being processed and line tracking.
    
    Attributes:
        current_task: The task currently being parsed (may span multiple lines)
        line_number: Current line number being processed (1-based)
        file_path: Path to the file being parsed
        current_section: The name of the current section header
        in_code_block: Whether we're inside a code block (for markdown files)
        last_markdown_header: The last markdown header encountered (for section inheritance)
    """
    current_task: Optional[task.Task] = None
    line_number: int = 0
    file_path: str = ""
    current_section: Optional[str] = None
    in_code_block: bool = False
    last_markdown_header: Optional[str] = None


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
        """Initialize the file parser."""
        pass
        
    def parse_file(self, file_path: str) -> File:
        """Parse a single file and return a File object with sections and tasks.
        
        Args:
            file_path: Path to the .md or .xit file to parse
            
        Returns:
            File object containing sections and tasks found in the file
            
        Raises:
            FileNotFoundError: If the specified file doesn't exist
            ValueError: If the file type is not supported (.md or .xit)
            
        Example:
            >>> parser = FileParser()
            >>> file_obj = parser.parse_file("todo.xit")
            >>> print(f"Found {len(file_obj.get_tasks())} tasks in {len(file_obj.sections)} sections")
        """
        # Validate file existence and type
        path = Path(file_path)
        if not path.exists():
            path.touch()
            
        if path.suffix not in ['.md', '.xit']:
            raise ValueError(f"Unsupported file type: {path.suffix}")
            
        # Create File object
        file_obj = File(path=file_path)
        context = ParseContext(file_path=file_path)
        
        # For markdown files, we need to track code blocks
        is_markdown = path.suffix == '.md'
        if is_markdown:
            context.in_code_block = False
        
        # Read all lines at once for efficiency
        # Using UTF-8 encoding to support international characters
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Process all lines in the file
        self._parse_lines(lines, context, file_obj)
        
        # Ensure there's at least a default section if no sections were found
        file_obj.ensure_default_section()
        
        return file_obj
    
    def parse_files(self, file_paths: List[str]) -> List[File]:
        """Parse multiple files and return list of File objects.
        
        Args:
            file_paths: List of file paths to parse
            
        Returns:
            List of File objects from all valid files
            
        Note:
            Invalid files are skipped with a warning message.
            This allows parsing to continue even if some files are problematic.
            
        Example:
            >>> parser = FileParser()
            >>> files = parser.parse_files(["todo.xit", "notes.md", "tasks.xit"])
            >>> total_tasks = sum(len(f.get_tasks()) for f in files)
            >>> print(f"Found {total_tasks} total tasks across {len(files)} files")
        """
        all_files = []
        for file_path in file_paths:
            try:
                file_obj = self.parse_file(file_path)
                all_files.append(file_obj)
            except (FileNotFoundError, ValueError) as e:
                # Continue processing other files even if one fails
                print(f"Warning: Skipping file {file_path}: {e}")
        return all_files
    
    def _parse_lines(self, lines: List[str], context: ParseContext, file_obj: File) -> None:
        """Parse all lines in a file and organize tasks into sections.
        
        This is the main parsing loop that processes each line according to
        the task format specification. It maintains state for multi-line tasks
        and handles different line types (checkboxes, continuations, headers, etc.).
        
        Args:
            lines: List of all lines from the file
            context: Parsing context to maintain state
            file_obj: File object to populate with sections and tasks
        """
        i = 0
        context.current_section = None
        current_section_obj = None
        
        while i < len(lines):
            context.line_number = i + 1  # Convert to 1-based line numbering
            line = lines[i].rstrip('\n\r')  # Remove line endings

            # Handle markdown files - track code blocks and headers
            if str(context.file_path).endswith('.md'):
                # Check for code block markers
                if line.strip().startswith('```'):
                    if not context.in_code_block:
                        context.in_code_block = True
                    else:
                        context.in_code_block = False
                    i += 1
                    continue
                
                # Track markdown headers when outside code blocks
                if not context.in_code_block and line.strip().startswith('#'):
                    context.last_markdown_header = line.strip()
                    i += 1
                    continue
                
                # Skip parsing tasks outside code blocks in markdown files
                if not context.in_code_block:
                    i += 1
                    continue

            # Check if this is a section header
            if SECTION_HEADER_PATTERN.match(line):
                # Finalize current task before switching sections
                if context.current_task and current_section_obj:
                    current_section_obj.add_task(context.current_task)
                    context.current_task = None
                
                section_title = line.strip()
                context.current_section = section_title
                
                # Create or get existing section
                if section_title not in file_obj.sections:
                    current_section_obj = Section(title=section_title, line_numbers=range(context.line_number, context.line_number + 1))
                    file_obj.add_section(current_section_obj)
                else:
                    current_section_obj = file_obj.sections[section_title]
                    current_section_obj.extend_line_numbers(context.line_number)
                
                i += 1
                continue

            # Check if this is a continuation line for the current task
            # Continuation lines must be exactly 4 spaces + content
            if context.current_task and self._is_continuation_line(line):
                self._handle_continuation_line(line, context)
                i += 1
                continue
                
            # Finalize current task if we have one and we're not continuing it
            # This happens when we encounter a non-continuation line
            if context.current_task:
                # Add task to current section or create default section
                if current_section_obj is None:
                    # No section header found yet, create default section
                    if "To Do" not in file_obj.sections:
                        current_section_obj = Section(title="To Do")
                        file_obj.add_section(current_section_obj)
                        context.current_section = "To Do"
                    else:
                        current_section_obj = file_obj.sections["To Do"]
                
                # Set the task's location if it doesn't have one
                if context.current_task.location.section is None:
                    context.current_task.set_location(Location(
                        file_path=file_obj.path,
                        line_numbers=context.current_task.location.line_numbers,
                        section=current_section_obj.title
                    ))
                
                current_section_obj.add_task(context.current_task)
                context.current_task = None
            
            # Check if this is a blank line (resets section context but not the current section object)
            if BLANK_LINE_PATTERN.match(line):
                i += 1
                continue
                
            # Check if this is a checkbox line (the main content we're parsing)
            checkbox_match = CHECKBOX_PATTERN.match(line)
            if checkbox_match:
                self._parse_checkbox_line(checkbox_match, context)
                i += 1
                continue
                
            i += 1
            
        # Don't forget to add the last task if the file doesn't end with a non-task line
        if context.current_task:
            # Add task to current section or create default section
            if current_section_obj is None:
                if "To Do" not in file_obj.sections:
                    current_section_obj = Section(title="To Do")
                    file_obj.add_section(current_section_obj)
                else:
                    current_section_obj = file_obj.sections["To Do"]
            
            # Set the task's location if it doesn't have one
            if context.current_task.location.section is None:
                context.current_task.set_location(Location(
                    file_path=file_obj.path,
                    line_numbers=context.current_task.location.line_numbers,
                    section=current_section_obj.title
                ))
            
            current_section_obj.add_task(context.current_task)
    
    def _parse_checkbox_line(self, match: re.Match, context: ParseContext) -> None:
        """Parse a the first line of a checkbox task.
        
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
        
        # Determine the section for this task
        task_section = context.current_section
        if str(context.file_path).endswith('.md') and task_section is None:
            # In markdown files, if no section is set in code block, inherit from last markdown header
            task_section = context.last_markdown_header
        
        # Create task object with all parsed information
        t = task.Task(
            description=content,  # Preserve whitespace in descriptions
            location=(context.file_path, context.line_number, task_section),
            status=status,
            priority=priority_obj,
            tags=tag_objects,
            due_date=due_date
        )
        
        # Store as current task (might be continued on next lines)
        context.current_task = t
    
    def _is_continuation_line(self, line: str) -> bool:
        """Check if line is a continuation of previous task description.
        
        Continuation lines must start with exactly 4 spaces according to the spec.
        However, lines that look like checkboxes (even with leading spaces) should
        not be treated as continuations.
        
        Args:
            line: Line to check
            
        Returns:
            True if this is a valid continuation line
        """
        if not CONTINUATION_PATTERN.match(line):
            return False
            
        # If the content after 4 spaces looks like a checkbox, it's not a continuation
        content = line[4:]  # Remove the 4 spaces
        if re.match(r'^\[.\]', content):
            return False
            
        return True
    
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
        context.current_task.location.extend_line_numbers(context.line_number)
            
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
            >>> parser._parse_due_date("task.Task -> 2025-12-31 (urgent)")
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
            >>> parser._parse_tags("task.Task #work #priority=high #tag='quoted value'")
            [Tag(name="work"), Tag(name="priority", value="high"), Tag(name="tag", value="quoted value")]
        """
        return Tag.from_line(content)
    
    def get_sections(self, file_path: str) -> List[str]:
        """Extract all section headers from a file.
        
        Args:
            file_path: Path to the file to parse

        Returns:
            List of section header strings
        """
        with open(file_path, 'r') as file:
            lines = file.readlines()
        sections = []
        for line in lines:
            if SECTION_HEADER_PATTERN.match(line):
                sections.append(line.strip())
        return sections


def parse_file(file_path: str) -> File:
    """Convenience function to parse a single file.
    
    Args:
        file_path: Path to the file to parse
        
    Returns:
        File object containing sections and tasks found in the file
        
    Example:
        >>> from xitkit.fileparser import parse_file
        >>> file_obj = parse_file("tasks.xit")
        >>> print(f"Found {len(file_obj.get_tasks())} tasks in {len(file_obj.sections)} sections")
    """
    parser = FileParser()
    return parser.parse_file(file_path)


def parse_files(file_paths: List[str]) -> List[File]:
    """Convenience function to parse multiple files.
    
    Args:
        file_paths: List of file paths to parse
        
    Returns:
        List of File objects from all files
        
    Example:
        >>> from xitkit.fileparser import parse_files
        >>> files = parse_files(["todo.xit", "notes.md"])
        >>> total_tasks = sum(len(f.get_tasks()) for f in files)
        >>> print(f"Found {total_tasks} total tasks across {len(files)} files")
    """
    parser = FileParser()
    return parser.parse_files(file_paths)


def parse_file_tasks(file_path: str) -> List[task.Task]:
    """Convenience function to parse a single file and return just the tasks.
    
    This function maintains backward compatibility for code that expects a list of tasks.
    
    Args:
        file_path: Path to the file to parse
        
    Returns:
        List of task.Task objects found in the file
        
    Example:
        >>> from xitkit.fileparser import parse_file_tasks
        >>> tasks = parse_file_tasks("tasks.xit")
        >>> print(f"Found {len(tasks)} tasks")
    """
    file_obj = parse_file(file_path)
    return file_obj.get_tasks()