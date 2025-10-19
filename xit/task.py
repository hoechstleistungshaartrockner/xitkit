from dataclasses import dataclass
from typing import Tuple, Optional
from pathlib import Path
from .patterns import *
from copy import deepcopy
from .tags import *
from .status import *
from .duedate import *
from .priority import *
from .description import *


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

    def __init__(self,
                 description: str,
                 file=None,
                 line_number=None,
                 status=None,
                 priority=None,
                 tags=None,
                 due_date=None,
                 id=None):
        """Initialize a Task instance.

        Args:
            description (str): Task description text.
            file (Optional[str]): File path where the task is located.
            line_number (Optional[int]): Line number of the task in the file.
            status (Optional[Status]): Task status object.
            priority (Optional[Priority]): Priority object or integer level.
            tags (Optional[List[Tag]]): List of Tag objects associated with the task.
            due_date (Optional[str]): Due date string if any.
            id (Optional[int]): Unique ID for the task.
        """
        
        self.description = Description(description)
        self.file = file
        self.line_number = line_number
        
        # Handle status - can be Status object, StatusType, string, or None
        if isinstance(status, Status):
            self.status = status
        elif isinstance(status, StatusType):
            self.status = Status(status)
        elif isinstance(status, str):
            # Map legacy status strings to StatusType
            status_mapping = {
                "OPEN": StatusType.OPEN,
                "DONE": StatusType.CHECKED,
                "ONGOING": StatusType.ONGOING,
                "OBSOLETE": StatusType.OBSOLETE,
                "INQUESTION": StatusType.IN_QUESTION
            }
            if status in status_mapping:
                self.status = Status(status_mapping[status])
            else:
                # Try to parse as status string or indicator
                parsed_status = Status.from_string(status) or Status.from_indicator(status)
                if parsed_status:
                    self.status = parsed_status
                else:
                    self.status = Status(StatusType.OPEN)
        else:
            self.status = Status(StatusType.OPEN)
        
        # Handle priority - can be Priority object, integer, or None
        if isinstance(priority, Priority):
            self.priority = priority
        elif isinstance(priority, int):
            self.priority = Priority(level=priority)
        else:
            self.priority = Priority()
            
        self.id = id if id is not None else 0
        
        # Handle tags - can be Tag objects or strings
        # Keep a separate list for easier management
        self.tags = []
        tags = tags if tags is not None else []
        for tag in tags:
            if isinstance(tag, Tag):
                self.tags.append(tag)
            else:
                # Assume it's a string, create Tag object
                self.tags.append(Tag(name=str(tag)))
        
        # Handle due date
        if due_date is not None:
            self.due_date = DueDate.from_string(due_date)
        else:
            self.due_date = None


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
            The filename portion of the file path, or None if no file is set
        """
        if self.file is None:
            return None
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
        return self.status.to_checkbox()

    @property
    def has_priority(self) -> bool:
        """Check if the task has a priority set.
        
        Returns:
            True if priority level > 0, False otherwise
        """
        return self.priority.level > 0
    
    @property
    def description_text(self) -> str:
        """Get the description text for backward compatibility.
        
        Returns:
            The description text as a string
        """
        return str(self.description)
    
    @property
    def due_date_string(self) -> Optional[str]:
        """Get the due date as a string for backward compatibility.
        
        Returns:
            The due date as a string or None if no due date
        """
        if self.due_date:
            return self.due_date.implied_date
        return None

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
            String of dots and exclamation marks representing priority level
        """
        return str(self.priority) if self.priority.level > 0 else "" 

    def set_status(self, status) -> None:
        """Set the task status with validation.
        
        Args:
            status: New status value (Status object, StatusType, or status string)
            
        Raises:
            ValueError: If status is not valid
        """
        if isinstance(status, Status):
            self.status = status
        elif isinstance(status, StatusType):
            self.status = Status(status)
        elif isinstance(status, str):
            # Map legacy status strings to StatusType
            status_mapping = {
                "OPEN": StatusType.OPEN,
                "DONE": StatusType.CHECKED,
                "ONGOING": StatusType.ONGOING,
                "OBSOLETE": StatusType.OBSOLETE,
                "INQUESTION": StatusType.IN_QUESTION
            }
            if status in status_mapping:
                self.status = Status(status_mapping[status])
            else:
                # Try to parse as status string like '[x]' or as indicator like 'x'
                parsed_status = Status.from_string(status)
                if parsed_status is None:
                    parsed_status = Status.from_indicator(status)
                if parsed_status is None:
                    raise ValueError(f"Invalid status: {status}")
                self.status = parsed_status
        else:
            raise ValueError(f"Invalid status type: {type(status)}")

    def set_priority(self, priority) -> None:
        """Set the task priority with validation.
        
        Args:
            priority: New priority value (Priority object or integer >= 0)
            
        Raises:
            ValueError: If priority is invalid
        """
        if isinstance(priority, Priority):
            self.priority = priority
        elif isinstance(priority, int):
            if priority < 0:
                raise ValueError("Priority must be >= 0")
            self.priority = Priority(level=priority)
        else:
            raise ValueError(f"Invalid priority type: {type(priority)}")

    def add_tag(self, tag: Tag) -> None:
        """Add a tag to the task.
        
        Args:
            tag: Tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)

    def add_tag_by_name(self, name: str, value: Optional[str] = None) -> None:
        """Add a tag by name and optional value.
        
        Args:
            name: Tag name (without # prefix)
            value: Optional tag value
        """
        # Remove # prefix if present
        name = name.lstrip('#')
        tag = Tag(name=name, value=value)
        self.add_tag(tag)

    def remove_tag(self, tag: Tag) -> bool:
        """Remove a tag from the task.
        
        Args:
            tag: Tag to remove

        Returns:
            True if tag was removed, False if not found
        """
        if tag in self.tags:
            self.tags.remove(tag)
            return True
        return False

    def remove_tag_by_name(self, name: str, soft: bool = True) -> bool:
        """Remove a tag by name.
        
        Args:
            name: Tag name to remove (with or without # prefix)
            soft: If True, remove by name only; if False, require exact match including value
            
        Returns:
            True if tag was removed, False if not found
        """
        # Remove # prefix if present
        name = name.lstrip('#')
        search_tag = Tag(name=name)
        
        for existing_tag in self.tags[:]:  # Create a copy to iterate over
            if existing_tag.compare(search_tag, soft=soft):
                self.tags.remove(existing_tag)
                return True
        return False

    def has_tag(self, tag: Tag, soft: bool = False) -> bool:
        """Check if the task has a specific tag.
        
        Args:
            tag: Tag to check for
            soft: If True, compare only tag names; if False, compare names and values
            
        Returns:
            True if tag exists, False otherwise
        """
        return any(existing_tag.compare(tag, soft=soft) for existing_tag in self.tags)

    def has_tag_by_name(self, name: str, soft: bool = True) -> bool:
        """Check if the task has a tag with the specified name.
        
        Args:
            name: Tag name to check for (with or without # prefix)
            soft: If True, check by name only; if False, require exact match including value
            
        Returns:
            True if tag exists, False otherwise
        """
        # Remove # prefix if present
        name = name.lstrip('#')
        search_tag = Tag(name=name)
        return self.has_tag(search_tag, soft=soft)

    def get_description_with_tags(self) -> str:
        """Get the full description including tags and due date.
        
        Returns:
            Description string with tags and due date appended
        """
        parts = [self.description_text]
        
        # Add tags if present
        if self.has_tags:
            tag_strings = [str(tag) for tag in self.tags]
            parts.extend(tag_strings)
        
        # Add due date if present
        if self.has_due_date:
            if hasattr(self.due_date, 'implied_date'):
                parts.append(f"-> {self.due_date.implied_date}")
            else:
                parts.append(f"-> {self.due_date}")
        
        return ' '.join(parts)

    def set_due_date(self, due_date: Optional[str]) -> None:
        """Set the due date for the task.
        
        Args:
            due_date: Due date string or None to clear
        """
        if due_date is not None:
            self.due_date = DueDate.from_string(due_date)
        else:
            self.due_date = None

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
        try:
            if hasattr(self.due_date, 'implied_date'):
                return self.due_date.implied_date < current_date
            else:
                return str(self.due_date) < current_date
        except (TypeError, ValueError):
            return False

    def __str__(self) -> str:
        """String representation for terminal display.
        
        Returns:
            Formatted string for terminal output
        """
        return self.to_checkbox_format()

    def __repr__(self) -> str:
        """Developer-friendly string representation.
        
        Returns:
            Detailed string representation for debugging
        """
        desc_text = str(self.description)
        desc_preview = desc_text[:30] + "..." if len(desc_text) > 30 else desc_text
        return (f"Task(file='{self.file}', line={self.line_number}, "
                f"status='{self.status}', priority={self.priority}, "
                f"description='{desc_preview}', "
                f"tags={self.tags}, due_date='{self.due_date}')")

    def copy(self) -> 'Task':
        """Create a copy of this task.
        
        Returns:
            New Task instance with the same properties
        """
        return deepcopy(self)

    def to_terminal_line(self, show_file: bool = True, show_line: bool = True, show_id: bool = False) -> str:
        """Convert task to terminal line format for display.
        
        Args:
            show_file: Whether to include file path in output
            show_line: Whether to include line number in output
            show_id: Whether to include task ID in output
            
        Returns:
            Formatted string suitable for terminal display
        """
        # Start with status symbol
        line_parts = [self.status_symbol]
        
        # Add priority if present
        if self.has_priority:
            line_parts.append(self.priority_indicator)
        
        # Add description, handling multi-line descriptions
        description_lines = str(self.description).split('\n')
        line_parts.append(description_lines[0])
        
        # Build first line
        result = ' '.join(line_parts)
        
        # Add continuation lines with proper indentation
        for continuation_line in description_lines[1:]:
            result += '\n    ' + continuation_line
        
        # Add location info if requested
        if (show_file or show_line) and (self.file is not None or self.line_number is not None):
            location_parts = []
            if show_file and self.file is not None:
                try:
                    relative_path = str(Path(self.file).relative_to(Path.cwd()))
                except ValueError:
                    relative_path = self.file
                location_parts.append(relative_path)
            
            if show_line and self.line_number is not None:
                location_parts.append(f"L{self.line_number}")
            
            if location_parts:
                location_str = ':'.join(location_parts)
                result += f" [{location_str}]"
        
        return result

    def to_checkbox_format(self) -> str:
        """Convert task back to checkbox format suitable for .xit files.
        
        Returns:
            String in checkbox format that can be written to file
        """
        # Start with status symbol
        line_parts = [self.status_symbol]
        
        # Add priority if present
        if self.has_priority:
            line_parts.append(self.priority_indicator)
        
        # Add description with tags and due date
        line_parts.append(self.get_description_with_tags())
        
        return ' '.join(line_parts)

