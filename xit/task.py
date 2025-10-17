from dataclasses import dataclass
from typing import Tuple, Optional
from pathlib import Path


@dataclass
class Task:
    """Represents a task parsed from .md or .xit files.
    
    This class encapsulates all information about a task including its location,
    content, status, priority, tags, and due date. It provides methods for
    accessing and modifying task properties as well as string representations
    for display purposes.
    
    Attributes:
        file: Path to the file containing this task
        line_number: Line number where the task appears (1-based)
        description: The task description text
        status: Task status (OPEN, ONGOING, DONE, OBSOLETE, INQUESTION)
        priority: Priority level (0 = no priority, 1+ = number of exclamation marks)
        tags: List of tags associated with the task
        due_date: Due date string if present, None otherwise
        id: Unique sequential ID assigned when reading files
    """
    file: str
    line_number: int
    description: str
    status: str  # one of ["OPEN", "ONGOING", "DONE", "OBSOLETE", "INQUESTION"]
    priority: int  # e.g., 0 (low) to open-ended (high)
    tags: list[str]  # e.g., ["#work", "#personal"]
    due_date: str | None  # e.g., "2023-12-31" or None
    id: int = 0  # Sequential ID assigned when reading files

    # Status symbols for visual representation - using square bracket format
    _STATUS_SYMBOLS = {
        'OPEN': '[ ]',
        'DONE': '[x]',
        'ONGOING': '[@]',
        'OBSOLETE': '[~]',
        'INQUESTION': '[?]'
    }

    # Valid status values
    _VALID_STATUSES = {'OPEN', 'ONGOING', 'DONE', 'OBSOLETE', 'INQUESTION'}

    @property
    def location(self) -> Tuple[str, int]:
        """Get the location of this task as a (filename, line_number) tuple.
        
        Returns:
            Tuple containing the file path and line number
        """
        return (self.file, self.line_number)

    @location.setter
    def location(self, value: Tuple[str, int]) -> None:
        """Set the location of this task.
        
        Args:
            value: Tuple containing (filename, line_number)
        """
        self.file, self.line_number = value

    @property
    def filename(self) -> str:
        """Get just the filename without the full path.
        
        Returns:
            The filename portion of the file path
        """
        return Path(self.file).name

    @property
    def relative_path(self) -> str:
        """Get the relative path from current working directory.
        
        Returns:
            Relative path if possible, otherwise absolute path
        """
        try:
            return str(Path(self.file).relative_to(Path.cwd()))
        except ValueError:
            return self.file

    @property
    def status_symbol(self) -> str:
        """Get the visual symbol for the current status.
        
        Returns:
            Unicode symbol representing the task status
        """
        return self._STATUS_SYMBOLS.get(self.status, self.status)

    @property
    def has_priority(self) -> bool:
        """Check if the task has a priority set.
        
        Returns:
            True if priority > 0, False otherwise
        """
        return self.priority > 0

    @property
    def has_due_date(self) -> bool:
        """Check if the task has a due date.
        
        Returns:
            True if due_date is not None, False otherwise
        """
        return self.due_date is not None

    @property
    def has_tags(self) -> bool:
        """Check if the task has any tags.
        
        Returns:
            True if tags list is not empty, False otherwise
        """
        return len(self.tags) > 0

    @property
    def priority_indicator(self) -> str:
        """Get the priority indicator string.
        
        Returns:
            String of exclamation marks representing priority level
        """
        return "!" * self.priority if self.priority > 0 else ""

    def set_status(self, status: str) -> None:
        """Set the task status with validation.
        
        Args:
            status: New status value
            
        Raises:
            ValueError: If status is not valid
        """
        if status not in self._VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {self._VALID_STATUSES}")
        self.status = status

    def set_priority(self, priority: int) -> None:
        """Set the task priority with validation.
        
        Args:
            priority: New priority value (must be >= 0)
            
        Raises:
            ValueError: If priority is negative
        """
        if priority < 0:
            raise ValueError("Priority must be >= 0")
        self.priority = priority

    def add_tag(self, tag: str) -> None:
        """Add a tag to the task.
        
        Args:
            tag: Tag to add (will be normalized to include # if missing)
        """
        if not tag.startswith('#'):
            tag = f'#{tag}'
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> bool:
        """Remove a tag from the task.
        
        Args:
            tag: Tag to remove (with or without # prefix)
            
        Returns:
            True if tag was removed, False if not found
        """
        # Try both with and without # prefix
        normalized_tag = tag if tag.startswith('#') else f'#{tag}'
        alt_tag = tag[1:] if tag.startswith('#') else tag
        
        for t in [tag, normalized_tag, alt_tag]:
            if t in self.tags:
                self.tags.remove(t)
                return True
        return False

    def has_tag(self, tag: str) -> bool:
        """Check if the task has a specific tag.
        
        Args:
            tag: Tag to check for (with or without # prefix)
            
        Returns:
            True if tag exists, False otherwise
        """
        # Extract tag names without values for comparison
        tag_names = []
        for task_tag in self.tags:
            if '=' in task_tag:
                tag_names.append(task_tag.split('=')[0])
            else:
                tag_names.append(task_tag)
        
        # Check both with and without # prefix
        normalized_tag = tag if tag.startswith('#') else f'#{tag}'
        return normalized_tag in tag_names or tag in tag_names

    def set_due_date(self, due_date: Optional[str]) -> None:
        """Set the due date for the task.
        
        Args:
            due_date: Due date string or None to clear
        """
        self.due_date = due_date

    def clear_due_date(self) -> None:
        """Clear the due date for the task."""
        self.due_date = None

    def is_overdue(self, current_date: str = "2025-10-15") -> bool:
        """Check if the task is overdue based on the current date.
        
        Args:
            current_date: Current date in YYYY-MM-DD format
            
        Returns:
            True if task has a due date and it's before current date
        """
        if not self.due_date:
            return False
        
        # Simple string comparison works for YYYY-MM-DD format
        # For more complex dates, this would need more sophisticated parsing
        try:
            return self.due_date < current_date
        except (TypeError, ValueError):
            return False

    def __str__(self) -> str:
        """String representation for terminal display.
        
        Returns:
            Formatted string with status symbol and description only
        """
        # Just show the status symbol and description
        # Don't duplicate metadata that's already in the description
        return f"{self.status_symbol} {self.description}"

    def __repr__(self) -> str:
        """Developer-friendly string representation.
        
        Returns:
            Detailed string representation for debugging
        """
        return (f"Task(file='{self.file}', line={self.line_number}, "
                f"status='{self.status}', priority={self.priority}, "
                f"description='{self.description[:30]}...', "
                f"tags={self.tags}, due_date='{self.due_date}')")

    def to_terminal_line(self, show_file: bool = True, show_line: bool = True) -> str:
        """Format task for terminal output with location information.
        
        Args:
            show_file: Whether to include file path in output
            show_line: Whether to include line number in output
            
        Returns:
            Formatted string ready for terminal display
        """
        # Format the main task content
        lines = self.description.split('\n')
        result_lines = []
        
        # First line gets the status symbol
        if lines:
            result_lines.append(f"{self.status_symbol} {lines[0]}")
            
            # Subsequent lines get proper indentation (4 spaces to align with description)
            for line in lines[1:]:
                result_lines.append(f"    {line}")
        else:
            result_lines.append(f"{self.status_symbol}")
        
        result = '\n'.join(result_lines)
        
        # Add location information if requested (only on the last line)
        if show_file or show_line:
            location_parts = []
            if show_file:
                location_parts.append(self.relative_path)
            if show_line:
                location_parts.append(f"L{self.line_number}")
            
            if location_parts:
                location = ":".join(location_parts)
                result += f" [{location}]"
        
        return result

    def to_checkbox_format(self) -> str:
        """Convert task back to checkbox format for writing to files.
        
        Returns:
            String in the original checkbox format
        """
        # Map status back to checkbox characters
        status_chars = {
            'OPEN': ' ',
            'DONE': 'x',
            'ONGOING': '@',
            'OBSOLETE': '~',
            'INQUESTION': '?'
        }
        
        status_char = status_chars.get(self.status, ' ')
        result = f"[{status_char}]"
        
        # Add priority if present
        if self.has_priority:
            result += f" {self.priority_indicator}"
        
        # Add description
        result += f" {self.description}"
        
        return result

    def copy(self) -> 'Task':
        """Create a copy of this task.
        
        Returns:
            New Task instance with the same properties
        """
        return Task(
            file=self.file,
            line_number=self.line_number,
            description=self.description,
            status=self.status,
            priority=self.priority,
            tags=self.tags.copy(),  # Shallow copy of tags list
            due_date=self.due_date
        )