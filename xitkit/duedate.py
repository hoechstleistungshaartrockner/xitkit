"""
DueDate
-------

Module for handling task due dates in the Xit task management system.
Supports all date formats specified in the syntax guide.
"""

from dataclasses import dataclass, field
from typing import Optional, Union
from datetime import datetime, timedelta
import re
from .dateutils import DateParser, get_date_parser


@dataclass
class DueDate:
    """Class representing a task's due date as it appears in the text.
    
    Supports formats from syntax guide:
    - -> 2022-01-31 (specific date)
    - -> 2022-01 (month, implies last day)
    - -> 2022 (year, implies last day)
    - -> 2022-W01 (week, implies last day)
    - -> 2022-Q1 (quarter, implies last day)
    - -> 2022/01/31 (slash format)
    """
    
    expression: str  # Original expression like "-> 2025-12-31", "-> 2025-Q3"
    implied_date: Optional[str] = field(init=False)  # Normalized to YYYY-MM-DD
    normalized_date: Optional[str] = field(init=False)  # Same as implied_date for compatibility
    regex_pattern: str = r'(?:^|(?<=[\s\(\)\[\]:;,.!?]))-> (\d{4}(?:[-/](?:W\d{2}|Q[1-4]|\d{1,2}(?:[-/]\d{1,2})?))?)(?=\s|[^\w/-]|$)'

    
    def __post_init__(self):
        """Post-initialization to parse and normalize the date expression."""
        self.implied_date = self._parse_date_from_expression()
        self.normalized_date = self.implied_date

    def _parse_date_from_expression(self) -> Optional[str]:
        """Parse the date from the due date expression."""
        # Remove the "-> " prefix to get just the date part
        if self.expression.startswith('-> '):
            date_part = self.expression[3:]
        else:
            # Handle cases where expression might not have the prefix
            date_part = self.expression.lstrip('-> ')
        
        # Validate the date format first
        if not self._is_valid_date_format(date_part):
            return None
        
        # Use DateParser to normalize the date
        parser = get_date_parser()
        try:
            return parser._normalize_date_for_comparison(date_part)
        except (ValueError, TypeError):
            return None
    
    def _is_valid_date_format(self, date_str: str) -> bool:
        """Validate that date string has correct format and values."""
        if not date_str:
            return False
            
        # Full date format: YYYY-MM-DD or YYYY/MM/DD
        if re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}$', date_str):
            return self._validate_full_date(date_str)
        
        # Month format: YYYY-MM or YYYY/MM
        if re.match(r'^\d{4}[-/]\d{2}$', date_str):
            return self._validate_month_date(date_str)
        
        # Year format: YYYY
        if re.match(r'^\d{4}$', date_str):
            year = int(date_str)
            return 1000 <= year <= 9999
        
        # Week format: YYYY-W## or YYYY/W##
        if re.match(r'^\d{4}[-/]W\d{2}$', date_str):
            return self._validate_week_date(date_str)
        
        # Quarter format: YYYY-Q#
        if re.match(r'^\d{4}-Q[1-4]$', date_str):
            return self._validate_quarter_date(date_str)
        
        return False
    
    def _validate_full_date(self, date_str: str) -> bool:
        """Validate full date format."""
        try:
            # Extract year, month, day
            if '-' in date_str:
                parts = date_str.split('-')
            else:
                parts = date_str.split('/')
            
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            
            # Basic range checks
            if not (1000 <= year <= 9999):
                return False
            if not (1 <= month <= 12):
                return False
            if not (1 <= day <= 31):
                return False
                
            # Check if date is valid (handles leap years, month lengths)
            datetime(year, month, day)
            return True
        except (ValueError, IndexError):
            return False
    
    def _validate_month_date(self, date_str: str) -> bool:
        """Validate month format."""
        try:
            if '-' in date_str:
                parts = date_str.split('-')
            else:
                parts = date_str.split('/')
                
            year, month = int(parts[0]), int(parts[1])
            return (1000 <= year <= 9999) and (1 <= month <= 12)
        except (ValueError, IndexError):
            return False
    
    def _validate_week_date(self, date_str: str) -> bool:
        """Validate week format."""
        try:
            if '-' in date_str:
                year_part, week_part = date_str.split('-')
            else:
                year_part, week_part = date_str.split('/')
                
            year = int(year_part)
            week = int(week_part[1:])  # Remove 'W' prefix
            
            return (1000 <= year <= 9999) and (1 <= week <= 53)
        except (ValueError, IndexError):
            return False
    
    def _validate_quarter_date(self, date_str: str) -> bool:
        """Validate quarter format."""
        try:
            year_part, quarter_part = date_str.split('-Q')
            year = int(year_part)
            quarter = int(quarter_part)
            
            return (1000 <= year <= 9999) and (1 <= quarter <= 4)
        except (ValueError, IndexError):
            return False

    @classmethod
    def from_string(cls, date_str: str) -> Optional['DueDate']:
        """Create a DueDate from a date string like '2025-12-31' or natural language like 'tomorrow'.
        
        Args:
            date_str: Date string in various formats including natural language
            
        Returns:
            DueDate object or None if invalid
        """
        if not date_str or not isinstance(date_str, str):
            return None
        
        # First try to parse with natural language / date parser
        date_parser = get_date_parser()
        parsed_date = date_parser.parse_date_expression(date_str.strip())
        
        if parsed_date:
            # Use the parsed date
            expression = f"-> {parsed_date}"
        else:
            # Fall back to direct usage (for already formatted dates)
            expression = f"-> {date_str.strip()}"
        
        # Validate using the pattern
        pattern = re.compile(cls.regex_pattern)
        if not pattern.search(expression):
            return None
        
        # Create the object and check if it parsed successfully
        due_date = cls(expression=expression)
        if not due_date.is_valid:
            return None
            
        return due_date

    @classmethod
    def from_line(cls, line: str) -> Optional['DueDate']:
        """Parse due date from a complete task line.
        
        Args:
            line: Complete task line that may contain due date
            
        Returns:
            DueDate object or None if no valid due date found
        """
        pattern = re.compile(cls.regex_pattern)
        match = pattern.search(line)
        if not match:
            return None
            
        # The pattern now includes the full "-> " prefix and date
        # Extract the matched portion
        start_pos = match.start()
        end_pos = match.end()
        
        expression = line[start_pos:end_pos]
        
        # Create and validate the DueDate
        due_date = cls(expression=expression)
        if not due_date.is_valid:
            return None
            
        return due_date

    def is_overdue(self, reference_date: Optional[datetime] = None) -> bool:
        """Check if the due date is overdue.
        
        Args:
            reference_date: Date to compare against (defaults to today)
            
        Returns:
            True if overdue, False otherwise
        """
        if not self.implied_date:
            return False
            
        if reference_date is None:
            reference_date = datetime.now()
            
        try:
            due_date = datetime.strptime(self.implied_date, '%Y-%m-%d')
            return due_date.date() < reference_date.date()
        except ValueError:
            return False

    def days_until_due(self, reference_date: Optional[datetime] = None) -> Optional[int]:
        """Calculate days until due date.
        
        Args:
            reference_date: Date to compare against (defaults to today)
            
        Returns:
            Number of days (negative if overdue), None if invalid date
        """
        if not self.implied_date:
            return None
            
        if reference_date is None:
            reference_date = datetime.now()
            
        try:
            due_date = datetime.strptime(self.implied_date, '%Y-%m-%d')
            delta = due_date.date() - reference_date.date()
            return delta.days
        except ValueError:
            return None

    def get_description(self, reference_date: Optional[datetime] = None) -> str:
        """Get a human-readable description of the due date.
        
        Args:
            reference_date: Date to compare against (defaults to today)
            
        Returns:
            Human-readable description
        """
        if not self.implied_date:
            return "Invalid date"
            
        days = self.days_until_due(reference_date)
        if days is None:
            return "Invalid date"
            
        if days < 0:
            return f"Overdue by {abs(days)} day{'s' if abs(days) != 1 else ''}"
        elif days == 0:
            return "Due today"
        elif days == 1:
            return "Due tomorrow"
        else:
            return f"Due in {days} days"

    def __str__(self) -> str:
        """String representation of the due date."""
        return self.expression

    def __eq__(self, other) -> bool:
        """Check equality with another DueDate."""
        if not isinstance(other, DueDate):
            return False
        return self.implied_date == other.implied_date

    def __lt__(self, other) -> bool:
        """Compare due dates (earlier dates are "less than" later dates)."""
        if not isinstance(other, DueDate):
            return NotImplemented
        if self.implied_date is None or other.implied_date is None:
            return False
        return self.implied_date < other.implied_date

    def __hash__(self) -> int:
        """Hash function for DueDate objects."""
        return hash(self.implied_date)

    @property
    def is_valid(self) -> bool:
        """Check if the due date is valid."""
        return self.implied_date is not None

    @property 
    def date_part(self) -> Optional[str]:
        """Get just the date part without the '-> ' prefix."""
        if self.expression.startswith('-> '):
            return self.expression[3:]
        return self.expression.lstrip('-> ')
    
    