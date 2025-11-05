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
from .location import Location
from .file_repository import FileRepository
from .dateutils import generate_recurring_dates


class Task:
    """Represents a task parsed from .md or .xit files.
    
    This class encapsulates all information about a task including its location,
    content, status, priority, tags, and due date. It provides methods for
    accessing and modifying task properties as well as string representations
    for display purposes.

    """

    def __init__(self,
                 description: str,
                 location=None,
                 status=None,
                 priority=None,
                 tags=None,
                 due_date=None):
        """Initialize a Task instance.

        Args:
            description (str): Task description text.
            location (Optional[Location]): Location object representing file and line numbers.
            status (Optional[Status]): status object, StatusType, or status string.
            priority (Optional[Priority]): Priority object or integer level.
            tags (Optional[List[Tag]]): List of Tag objects associated with the task.
            due_date (Optional[str]): Due date string if any.
        """
        self.description = Description(description)

        # Handle location
        self.set_location(location)

        # Handle status - can be Status object, StatusType, string, or None
        if isinstance(status, Status):
            self.status = status
        elif isinstance(status, StatusType):
            self.status = Status(status)
        elif isinstance(status, str):
            # Map legacy and current status strings to StatusType
            status_mapping = {
                "OPEN": StatusType.OPEN,
                "DONE": StatusType.CHECKED,      # legacy name
                "CHECKED": StatusType.CHECKED,   # current name
                "ONGOING": StatusType.ONGOING,
                "OBSOLETE": StatusType.OBSOLETE,
                "INQUESTION": StatusType.IN_QUESTION,  # legacy name
                "IN_QUESTION": StatusType.IN_QUESTION  # current name
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
        
        # Handle priority
        # will be inferred by the Description
        # or, if provided, can be Priority object, integer, or None and will overpower the Description

        self.priority = self.description.priority
        if isinstance(priority, Priority):
            self.set_priority(priority)
        elif isinstance(priority, int):
            self.set_priority(Priority(level=priority))
        elif priority is None:
            pass  # keep from description
        else:
            raise ValueError(f"Invalid priority type: {type(priority)}")
        
        # Handle ID
        self.id = FileRepository().assign_id()
        FileRepository()._tasks[self.id] = self
        
        # Handle tags - can be Tag objects or strings
        # Keep a separate list for easier management
        self.tags = self.description.tags
        tags = tags if tags is not None else []
        for tag in tags:
            if isinstance(tag, Tag):
                self.add_tag(tag)
            else:
                # Assume it's a string, create Tag object
                self.add_tag_by_name(tag)
        
        # Handle due date
        self.due_date = self.description.due_date
        if due_date is not None:
            if isinstance(due_date, str) or isinstance(due_date, DueDate):
                self.set_due_date(due_date)
            else:
                # Unsupported type, ignore
                pass

    def set_location(self, location) -> None:
        """Set the task's location.

        Args:
            location: Location object or tuple (file_path, line_number, section) or None for default
        """
        if isinstance(location, Location):
            self.location = location
        elif isinstance(location, tuple) and len(location) == 2:
            file_path, line_number = location
            self.location = Location(file_path=file_path, line_numbers=line_number)
        elif isinstance(location, tuple) and len(location) == 3:
            file_path, line_number, section = location
            self.location = Location(file_path=file_path, line_numbers=line_number, section=section)
        else:
            # Default location
            self.location = Location()

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
            self.description.set_priority(priority)
        elif isinstance(priority, int):
            if priority < 0:
                raise ValueError("Priority must be >= 0")
            self.description.set_priority(Priority(level=priority))
        else:
            raise ValueError(f"Invalid priority type: {type(priority)}")
        
        # Update the task's priority reference to point to the description's priority
        self.priority = self.description.priority

    def add_tag(self, tag: Tag) -> None:
        """Add a tag to the task.
        
        Args:
            tag: Tag to add
        
        Returns:
            bool: True if the tag was added, False if it was already present.
        """
        return self.description.add_tag(tag)
        

    def add_tag_by_name(self, name: str, value: Optional[str] = None) -> bool:
        """Add a tag by name and optional value.
        
        Args:
            name: Tag name (without # prefix)
            value: Optional tag value
        Returns:
            bool: True if the tag was added, False if it was already present.
        """
        # Remove # prefix if present
        name = name.lstrip('#')
        tag = Tag(name=name, value=value)
        return self.add_tag(tag)

    def remove_tag(self, tag: Tag, soft: bool =False) -> bool:
        """Remove a tag from the task.
        
        Args:
            tag: Tag to remove

        Returns:
            True if tag was removed, False if not found
        """
        return self.description.remove_tag(tag, soft=soft)
        

    def remove_tag_by_name(self, name: str, soft: bool = False) -> bool:
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
        
        return self.remove_tag(search_tag, soft=soft)

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
        parts = [self.description.get_clean_text()]
        
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
        if isinstance(due_date, str):
            self.description.set_due_date(DueDate.from_string(due_date))
        elif isinstance(due_date, DueDate):
            self.description.set_due_date(due_date)
        elif due_date is None:
            self.description.set_due_date(None)
        
        self.due_date = self.description.due_date

    def clear_due_date(self) -> None:
        """Clear the due date for the task."""
        self.description.clear_due_date()
        self.due_date = self.description.due_date

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
        return (f"Task(status='{self.status.status_type.name}', priority={self.priority.level}, "
                f"description='{desc_preview}', "
                f"tags={[str(tag) for tag in self.tags]}, due_date='{self.due_date}', "
                f"location={self.location})")

    def copy(self) -> 'Task':
        """Create a copy of this task.
        
        Returns:
            New Task instance with the same properties
        """
        return Task(
            description=str(self.description),
            location=deepcopy(self.location),
            status=deepcopy(self.status),
            priority=deepcopy(self.priority),
            tags=deepcopy(self.tags),
            due_date=deepcopy(self.due_date)
        )

    def to_terminal_line(self, 
                         show_file: bool = True, 
                         show_line: bool = True, 
                         show_id: bool = False) -> str:
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
        
        # Add description, handling multi-line descriptions
        description_lines = str(self.description).split('\n')
        line_parts.append(description_lines[0])
        
        # Build first line
        result = ' '.join(line_parts)
        
        # Add continuation lines with proper indentation
        for continuation_line in description_lines[1:]:
            result += '\n    ' + continuation_line
        
        # Add location info if requested
        if (show_file and not show_line):
            result += f"    ({self.location.relative_path})"
        elif (show_file and show_line):
            result += f"    ({str(self.location)})"
        elif (not show_file and show_line):
            result += f"    ({self.location.resolve_line_numbers()})"
        
        return result

    def to_checkbox_format(self) -> str:
        """Convert task back to checkbox format suitable for .xit files.
        
        Returns:
            String in checkbox format that can be written to file
        """
        # Handle multi-line descriptions by indenting continuation lines
        description_text = str(self.description)
        lines = description_text.split('\n')

        prefix = {0: self.status_symbol + ' '}
        
        # Multi-line - indent continuation lines with 4 spaces
        formatted_lines = [prefix.get(idx, "    ") + line for idx, line in enumerate(lines)]
        return '\n'.join(formatted_lines)

    def save(self) -> bool:
        """Save the task to its file using the FileRepository.
        
        Returns:
            True if the task was saved successfully, False otherwise
        """
        if not self.location or not self.location.file_path:
            return False
        return FileRepository().update_task(self)

    def recur(self, interval: str, count: int = None, end_date: str = None) -> list:
        """Create recurring tasks based on this task.
        
        Args:
            interval: Recurrence interval string (e.g., '1w' for one week)
            count: Number of occurrences to create
            end_date: Optional end date string in YYYY-MM-DD format
            
        Returns:
            List of newly created Task instances
        """
        # throw error if both count and end_date are provided
        if count is not None and end_date is not None:
            raise ValueError("Specify either count or end_date, not both.")
        
        dates = generate_recurring_dates(
            start_date=self.due_date.implied_date if self.due_date else None,
            interval=interval,
            count=count +1 if count is not None else None,
            end_date=end_date
        )
        
        # get the according file and rewrite
        file = FileRepository().get_file(self.location.file_path)
        
        for date in dates[1:]:  # skip the first date as it's the original task
            new_task = self.copy()
            new_task.set_due_date(date)
            file.add_task(new_task)
        
        # Save the file with new tasks
        file.write()
        return dates[1:]  # return only the newly created tasks
    
    def unlink(self) -> bool:
        """Unlink the task from its file without deleting it.
        
        Returns:
            True if the task was unlinked successfully, False otherwise
        """
        if not self.location or not self.location.file_path:
            return False
        return FileRepository().unlink_task(self)
    
    def delete(self) -> bool:
        """Delete the task from its file.
        
        Returns:
            True if the task was deleted successfully, False otherwise
        """
        if not self.location or not self.location.file_path:
            return False
        file = FileRepository().get_file(self.location.file_path)
        if file:
            file.remove_task(self)
            file.write()
            return True
        return False
    
    def move(self, new_file_path: str, section_name: Optional[str] = None) -> bool:
        """Move the task to a different file and optional section.
        
        Args:
            new_file_path: Path of the target file
            section_name: Optional section name in the target file
            
        Returns:
            True if the task was moved successfully, False otherwise
        """
        # Unlink from current file
        if not self.unlink():
            return False
        
        # write old file
        old_file = FileRepository().get_file(self.location.file_path)
        old_file.write()
        
        # Update location
        self.location.file_path = new_file_path
        self.location.section = section_name
        
        # save to new file
        return self.save()