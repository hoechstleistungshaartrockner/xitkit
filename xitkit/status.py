"""Status module for task status handling.

This module provides the Status class for managing task status according to
the syntax guide specifications.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union
import re

from xitkit.exceptions import XitError

class StatusType(Enum):
    """Enumeration of valid status types."""
    OPEN = " "
    CHECKED = "x"
    ONGOING = "@"
    OBSOLETE = "~"
    IN_QUESTION = "?"

@dataclass(frozen=True)
class Status:
    """Represents a task status with validation according to syntax guide.
    
    A status consists of square brackets with a single character inside:
    - [ ] Open (space character)
    - [x] Checked
    - [@] Ongoing  
    - [~] Obsolete
    - [?] In Question
    
    Any other character or format is considered invalid.
    """
    
    status_type: StatusType
    
    def __post_init__(self):
        """Validate status type after initialization."""
        if not isinstance(self.status_type, StatusType):
            raise ValueError(f"Invalid status type: {self.status_type}. Maybe use Status.from_string()?")
    
    def __str__(self) -> str:
        """Return string representation of the status."""
        return f"[{self.status_type.value}]"
    
    def __repr__(self) -> str:
        """Return repr representation of the status."""
        return f"Status({self.status_type.name})"
    
    @property
    def indicator(self) -> str:
        """Get the status indicator character."""
        return self.status_type.value
    
    @property
    def is_open(self) -> bool:
        """Check if status is open."""
        return self.status_type == StatusType.OPEN
    
    @property
    def is_checked(self) -> bool:
        """Check if status is checked."""
        return self.status_type == StatusType.CHECKED
    
    @property
    def is_ongoing(self) -> bool:
        """Check if status is ongoing."""
        return self.status_type == StatusType.ONGOING
    
    @property
    def is_obsolete(self) -> bool:
        """Check if status is obsolete."""
        return self.status_type == StatusType.OBSOLETE
    
    @property
    def is_in_question(self) -> bool:
        """Check if status is in question."""
        return self.status_type == StatusType.IN_QUESTION
    
    @property
    def is_complete(self) -> bool:
        """Check if status represents a completed task (checked or obsolete)."""
        return self.status_type in (StatusType.CHECKED, StatusType.OBSOLETE)
    
    @property
    def is_active(self) -> bool:
        """Check if status represents an active task (open, ongoing, or in question)."""
        return self.status_type in (StatusType.OPEN, StatusType.ONGOING, StatusType.IN_QUESTION)
    
    @classmethod
    def from_string(cls, status_str: str) -> Optional['Status']:
        """Create Status from string representation.
        
        Args:
            status_str (str): String like '[x]', '[ ]', '[@]', etc.
            
        Returns:
            Optional[Status]: Status object if valid, None if invalid.
            
        Examples:
            >>> Status.from_string('[x]')
            Status(CHECKED)
            >>> Status.from_string('[ ]')
            Status(OPEN)
            >>> Status.from_string('[invalid]')
            None
        """
        if not isinstance(status_str, str):
            return None
            
        allowed_values = {"open": StatusType.OPEN,
                              "checked": StatusType.CHECKED,
                              "ongoing": StatusType.ONGOING,
                              "obsolete": StatusType.OBSOLETE,
                              "in_question": StatusType.IN_QUESTION,
                              "inquestion": StatusType.IN_QUESTION,
                              "done": StatusType.CHECKED,
                              "complete": StatusType.CHECKED,
                              "active": StatusType.OPEN,
                              "OPEN": StatusType.OPEN,
                              "CHECKED": StatusType.CHECKED,
                              "ONGOING": StatusType.ONGOING,
                              "OBSOLETE": StatusType.OBSOLETE,
                              "IN_QUESTION": StatusType.IN_QUESTION,
                              "INQUESTION": StatusType.IN_QUESTION,
                              "DONE": StatusType.CHECKED,
                              "COMPLETE": StatusType.CHECKED,
                              "ACTIVE": StatusType.OPEN,
                              # checkbox formats
                              "[ ]": StatusType.OPEN,
                              "[x]": StatusType.CHECKED,
                              "[@]": StatusType.ONGOING,
                              "[~]": StatusType.OBSOLETE,
                              "[?]": StatusType.IN_QUESTION,
                              # single character indicators
                              " ": StatusType.OPEN,
                              "x": StatusType.CHECKED,
                              "@": StatusType.ONGOING,
                              "~": StatusType.OBSOLETE,
                              "?": StatusType.IN_QUESTION,
                              }
        status_type = allowed_values.get(status_str, None)
        if status_type is None:
            raise XitError(f"Invalid status string: {status_str}")
        
        return cls(status_type)
    
    @property
    def name(self) -> str:
        """Get the name of the status type."""
        return self.status_type.name
    
    @classmethod
    def from_line(cls, line: str) -> Optional['Status']:
        """Extract status from a line of text.
        
        According to syntax guide, status must be at the beginning of the line
        with no preceding whitespace.
        
        Args:
            line (str): Line of text to parse.
            
        Returns:
            Optional[Status]: Status object if found and valid, None otherwise.
            
        Examples:
            >>> Status.from_line('[x] Do something')
            Status(CHECKED)
            >>> Status.from_line('  [x] Invalid due to whitespace')
            None
        """
        if not isinstance(line, str) or len(line) < 3:
            return None
            
        # Status cannot be preceded by whitespace
        if line.startswith((' ', '\t')):
            return None
            
        # Extract potential status (first 3 characters)
        potential_status = line[:3]
        
        return cls.from_string(potential_status)
    
    @classmethod 
    def from_indicator(cls, indicator: Union[str, StatusType]) -> Optional['Status']:
        """Create Status from indicator character or StatusType.
        
        Args:
            indicator (Union[str, StatusType]): Status indicator (' ', 'x', '@', '~', '?') 
                                               or StatusType enum value.
            
        Returns:
            Optional[Status]: Status object if valid, None if invalid.
            
        Examples:
            >>> Status.from_indicator('x')
            Status(CHECKED)
            >>> Status.from_indicator(' ')
            Status(OPEN)
            >>> Status.from_indicator(StatusType.ONGOING)
            Status(ONGOING)
        """
        if isinstance(indicator, StatusType):
            return cls(indicator)
        
        if not isinstance(indicator, str) or len(indicator) != 1:
            return None
            
        try:
            status_type = StatusType(indicator)
            return cls(status_type)
        except ValueError:
            return None
    
    def to_checkbox(self) -> str:
        """Convert status to checkbox format.
        
        Returns:
            str: Status in checkbox format like '[x]', '[ ]', etc.
        """
        return str(self)
    
    def is_valid_format(self, status_str: str) -> bool:
        """Check if a string represents a valid status format.
        
        Args:
            status_str (str): String to validate.
            
        Returns:
            bool: True if valid status format, False otherwise.
        """
        return self.from_string(status_str) is not None
    
    @staticmethod
    def get_valid_indicators() -> list[str]:
        """Get list of all valid status indicators.
        
        Returns:
            list[str]: List of valid indicator characters.
        """
        return [status_type.value for status_type in StatusType]
    
    @staticmethod
    def get_valid_statuses() -> list[str]:
        """Get list of all valid status strings.
        
        Returns:
            list[str]: List of valid status strings like '[x]', '[ ]', etc.
        """
        return [f"[{status_type.value}]" for status_type in StatusType]
