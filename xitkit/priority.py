"""
Priority
========
Module for handling task priority levels.
Provides functions to parse priority indicators and format them for display.
According to syntax guide:
- Priority must follow checkbox with exactly one space
- Priority can be padded with dots on either side (but not both)
- Additional spaces to the right belong to description
- No additional spaces to the left are allowed
"""

from typing import Optional
from dataclasses import dataclass
import re

@dataclass
class Priority:
    """Class representing task priority according to syntax guide.
    
    Priority format: dots + exclamation marks OR exclamation marks + dots
    Examples: !, !!, !!!, .!, !!., ...!, !!!...
    Invalid: .!., !.!, mixed dot positions
    """
    level: int = 0  # number of exclamation marks (priority level)
    leading_dots: int = 0  # dots before exclamation marks
    trailing_dots: int = 0  # dots after exclamation marks

    @classmethod
    def from_line(cls, line: str) -> Optional['Priority']:
        """Parse priority from text after checkbox.

        Args:
            line (str): The text after checkbox (should start with space + priority)
        Returns:
            Optional[Priority]: A Priority object if valid priority found, else None.
        """
        # Pattern for priority: space + priority_chars + space + description
        # Priority chars: dots + exclamation marks OR exclamation marks + dots
        pattern = re.compile(r'^ ((?:[.]*[!]+|[!]+[.]*))( .*)$')
        match = pattern.match(line)
        
        if not match:
            return None
            
        priority_chars = match.group(1)
        
        # Check for invalid mixed patterns (dots on both sides)
        if '.' in priority_chars and priority_chars.find('.') < priority_chars.rfind('!') and priority_chars.rfind('.') > priority_chars.find('!'):
            return None
            
        level = priority_chars.count('!')
        if level == 0:  # Must have at least one exclamation mark
            return None
            
        # Determine dot positions
        leading_dots = 0
        trailing_dots = 0
        
        if priority_chars.startswith('.'):
            # Dots before exclamation marks
            leading_dots = len(priority_chars) - len(priority_chars.lstrip('.'))
        elif priority_chars.endswith('.'):
            # Dots after exclamation marks  
            trailing_dots = len(priority_chars) - len(priority_chars.rstrip('.'))
            
        return cls(level=level, leading_dots=leading_dots, trailing_dots=trailing_dots)

    @classmethod
    def from_checkbox_line(cls, line: str) -> Optional['Priority']:
        """Parse priority from a complete checkbox line.
        
        Args:
            line (str): Complete line starting with checkbox like '[ ] ! description'
        Returns:
            Optional[Priority]: A Priority object if valid priority found, else None.
        """
        # Extract content after checkbox
        checkbox_pattern = re.compile(r'^\[(.)\](.*)$')
        match = checkbox_pattern.match(line)
        
        if not match:
            return None
            
        after_checkbox = match.group(2)
        return cls.from_line(after_checkbox)

    def __str__(self) -> str:
        """String representation of the priority for display."""
        if self.level == 0:
            return ""
        return '.' * self.leading_dots + '!' * self.level + '.' * self.trailing_dots

    def __eq__(self, other) -> bool:
        """Check equality with another Priority object."""
        if not isinstance(other, Priority):
            return False
        return (self.level == other.level and 
                self.leading_dots == other.leading_dots and 
                self.trailing_dots == other.trailing_dots)

    def __lt__(self, other) -> bool:
        """Compare priority levels (higher level = higher priority)."""
        if not isinstance(other, Priority):
            return NotImplemented
        return self.level < other.level

    def __hash__(self) -> int:
        """Hash function for Priority objects."""
        return hash((self.level, self.leading_dots, self.trailing_dots))

    @property
    def is_empty(self) -> bool:
        """Check if priority is empty (no exclamation marks)."""
        return self.level == 0

    @property
    def indicator(self) -> str:
        """Get priority indicator string (same as __str__ but clearer intent)."""
        return str(self)
    
