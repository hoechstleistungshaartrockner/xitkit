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


import re

class Priority:
    """Class representing task priority according to syntax guide.
    
    Priority format: dots + exclamation marks OR exclamation marks + dots
    Examples: !, !!, !!!, .!, !!., ...!, !!!...
    Invalid: .!., !.!, mixed dot positions
    """
    # Updated regex pattern for parsing priority
    regex_pattern: str = r'^(?:\[.\] | )?(?P<leading_dots>\.*)(?P<level>!*)(?P<trailing_dots>\.*)(?= |$)'

    def __init__(self, level: int = 0, leading_dots: int = 0, trailing_dots: int = 0):
        """Initialize Priority object.

        Args:
            level (int): Number of exclamation marks indicating priority level.
            leading_dots (int): Number of leading dots before exclamation marks.
            trailing_dots (int): Number of trailing dots after exclamation marks.
        """
        # Validate inputs
        if level < 0:
            raise ValueError("Priority level cannot be negative")
        if leading_dots > 0 and trailing_dots > 0:
            raise ValueError("Priority cannot have both leading and trailing dots")
        
        self.level = level
        self.leading_dots = leading_dots
        self.trailing_dots = trailing_dots

    @classmethod
    def from_line(cls, line: str) -> Priority:
        """Parse priority from text after checkbox.

        Args:
            line (str): The text after checkbox (should start with space + priority)
        Returns:
            Optional[Priority]: A Priority object if valid priority found, else None.
        """
        if line is None or line.strip() == "":
            return Priority()  # No priority, return level 0
        
        # Match the line against the regex pattern
        pattern = re.compile(cls.regex_pattern)
        match = pattern.match(line)
        
        if not match:
            return Priority()  # No valid priority found, return priority level 0
            
        leading_dots_chars = match.group("leading_dots")
        level_chars = match.group("level")
        trailing_dots_chars = match.group("trailing_dots")

        leading_dots = len(leading_dots_chars) if leading_dots_chars else 0
        level = len(level_chars) if level_chars else 0
        trailing_dots = len(trailing_dots_chars) if trailing_dots_chars else 0

        # Account for invalid cases
        # 1. Dots on both sides
        # 2. No dots and no exclamation marks (empty match)
        # 3. Mixed dots (dots in the middle - detected by having both leading and trailing)
        if leading_dots > 0 and trailing_dots > 0:
            return Priority()  # invalid: dots on both sides
        
        # If we have neither dots nor exclamation marks, it's not a priority
        if leading_dots == 0 and level == 0 and trailing_dots == 0:
            return Priority()
        
        return cls(level=level, leading_dots=leading_dots, trailing_dots=trailing_dots)

    def __str__(self) -> str:
        """String representation of the priority for display."""
        # if self.level == 0:
        #     return ""
        return '.' * self.leading_dots + '!' * self.level + '.' * self.trailing_dots

    def __eq__(self, other) -> bool:
        """Check equality with another Priority object."""
        if isinstance(other, Priority):
            return (self.level == other.level and 
                    self.leading_dots == other.leading_dots and 
                    self.trailing_dots == other.trailing_dots)
        elif isinstance(other, str):
            return str(self) == other
        elif isinstance(other, int):
            return self.level == other
        elif isinstance(other, float):
            return float(self.level) == other
        elif isinstance(other, tuple) and len(other) == 3:
            return (self.level, self.leading_dots, self.trailing_dots) == other
        elif isinstance(other, dict):
            return (self.level == other.get('level', 0) and
                    self.leading_dots == other.get('leading_dots', 0) and
                    self.trailing_dots == other.get('trailing_dots', 0))
        else:
            return NotImplemented

    def __lt__(self, other) -> bool:
        """Compare priority levels (higher level = higher priority)."""
        if isinstance(other, Priority):
            return self.level < other.level
        elif isinstance(other, int):
            return self.level < other
        elif isinstance(other, float):
            return float(self.level) < other
        else:
            return NotImplemented

    def __gt__(self, other) -> bool:
        """Compare priority levels (higher level = higher priority)."""
        if isinstance(other, Priority):
            return self.level > other.level
        elif isinstance(other, int):
            return self.level > other
        elif isinstance(other, float):
            return float(self.level) > other
        else:
            return NotImplemented

    def __hash__(self) -> int:
        """Hash function for Priority objects."""
        return hash((self.level, self.leading_dots, self.trailing_dots))

    def to_tuple(self) -> tuple:
        """Convert Priority to a tuple representation."""
        return (self.level, self.leading_dots, self.trailing_dots)
    
    def to_dict(self) -> dict:
        """Convert Priority to a dictionary representation."""
        return {
            'level': self.level,
            'leading_dots': self.leading_dots,
            'trailing_dots': self.trailing_dots
        }
    
    def __repr__(self) -> str:
        """Official string representation of Priority object."""
        return f"Priority(level={self.level}, leading_dots={self.leading_dots}, trailing_dots={self.trailing_dots})"
    
