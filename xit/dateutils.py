"""Date utilities for parsing and handling due dates.

This module provides functions for parsing various date formats including
natural language terms like "today", "tomorrow", relative dates like "1w", "2d",
and standard date formats.
"""

from datetime import datetime, timedelta
from typing import Optional, Union
import re
from pathlib import Path


class DateParser:
    """Parser for various date formats and natural language date expressions.
    
    Supports:
    - Natural language: today, tomorrow, yesterday
    - Relative dates: 1d, 2w, 3m, 1y (days, weeks, months, years)
    - Standard formats: 2025-12-31, 2025-12, 2025
    - Week/Quarter formats: 2025-W42, 2025-Q4
    """
    
    def __init__(self, current_date: Optional[datetime] = None):
        """Initialize the date parser.
        
        Args:
            current_date: Current date to use as reference. Defaults to today.
        """
        self.current_date = current_date or datetime.now()
        
        # Natural language mappings
        self.natural_keywords = {
            'today': 0,
            'tomorrow': 1,
            'yesterday': -1,
        }
        
        # Regex patterns for relative dates
        self.relative_pattern = re.compile(r'^([+-]?\d+)([dwmy])$', re.IGNORECASE)
        
        # Standard date patterns (from syntax guide)
        self.date_patterns = [
            re.compile(r'^\d{4}-\d{2}-\d{2}$'),  # 2025-12-31
            re.compile(r'^\d{4}-\d{2}$'),        # 2025-12
            re.compile(r'^\d{4}$'),              # 2025
            re.compile(r'^\d{4}-W\d{2}$'),       # 2025-W42
            re.compile(r'^\d{4}-Q[1-4]$'),       # 2025-Q4
            re.compile(r'^\d{4}/\d{2}/\d{2}$'),  # 2025/12/31
            re.compile(r'^\d{4}/W\d{2}$'),       # 2025/W42
        ]
    
    def parse_date_expression(self, expression: str) -> Optional[str]:
        """Parse a date expression and return a standardized date string.
        
        Args:
            expression: Date expression to parse (e.g., "today", "1w", "2025-12-31")
            
        Returns:
            Standardized date string or None if parsing fails
            
        Examples:
            >>> parser = DateParser()
            >>> parser.parse_date_expression("today")
            "2025-10-15"
            >>> parser.parse_date_expression("1w")
            "2025-10-22"
            >>> parser.parse_date_expression("2025-12-31")
            "2025-12-31"
        """
        expression = expression.strip()
        
        # Handle natural language keywords (case insensitive)
        if expression.lower() in self.natural_keywords:
            days_offset = self.natural_keywords[expression.lower()]
            target_date = self.current_date + timedelta(days=days_offset)
            return target_date.strftime('%Y-%m-%d')
        
        # Handle relative dates (1d, 2w, 3m, 1y)
        relative_match = self.relative_pattern.match(expression.lower())
        if relative_match:
            amount = int(relative_match.group(1))
            unit = relative_match.group(2).lower()
            
            target_date = self._calculate_relative_date(amount, unit)
            if target_date:
                return target_date.strftime('%Y-%m-%d')
        
        # Handle standard date formats (return as-is if valid)
        if self._is_valid_standard_date(expression):
            return expression
        
        return None
    
    def _calculate_relative_date(self, amount: int, unit: str) -> Optional[datetime]:
        """Calculate a date relative to the current date.
        
        Args:
            amount: Number of units
            unit: Time unit ('d', 'w', 'm', 'y')
            
        Returns:
            Calculated datetime or None if invalid unit
        """
        if unit == 'd':  # days
            return self.current_date + timedelta(days=amount)
        elif unit == 'w':  # weeks
            return self.current_date + timedelta(weeks=amount)
        elif unit == 'm':  # months (approximate as 30 days)
            return self.current_date + timedelta(days=amount * 30)
        elif unit == 'y':  # years (approximate as 365 days)
            return self.current_date + timedelta(days=amount * 365)
        
        return None
    
    def _is_valid_standard_date(self, date_str: str) -> bool:
        """Check if a string matches any of the standard date formats.
        
        Args:
            date_str: Date string to validate
            
        Returns:
            True if the string matches a valid date format
        """
        return any(pattern.match(date_str) for pattern in self.date_patterns)
    
    def format_date_for_display(self, date_str: str) -> str:
        """Format a date string for display purposes.
        
        Args:
            date_str: Date string to format
            
        Returns:
            Formatted date string
        """
        # For now, just return as-is, but this could be enhanced
        # to show relative descriptions like "in 3 days" etc.
        return date_str
    
    def get_date_description(self, date_str: str) -> str:
        """Get a human-readable description of a date.
        
        Args:
            date_str: Date string to describe
            
        Returns:
            Human-readable description
        """
        try:
            # Try to parse the date and compare with current date
            if '-' in date_str and len(date_str) == 10:  # YYYY-MM-DD format
                target_date = datetime.strptime(date_str, '%Y-%m-%d')
                current_date = self.current_date.replace(hour=0, minute=0, second=0, microsecond=0)
                target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                
                diff = (target_date - current_date).days
                
                if diff == 0:
                    return "today"
                elif diff == 1:
                    return "tomorrow"
                elif diff == -1:
                    return "yesterday"
                elif diff > 0:
                    return f"in {diff} days"
                else:
                    return f"{abs(diff)} days ago"
        except ValueError:
            pass
        
        return date_str
    
    def matches_date_filter_on(self, task_due_date: Optional[str], filter_expression: str) -> bool:
        """Check if a task's due date matches a filter expression exactly.
        
        Args:
            task_due_date: Due date from the task (may be None)
            filter_expression: Filter expression to match against
            
        Returns:
            True if the task matches the filter exactly
        """
        if not task_due_date:
            return False
        
        # Parse the filter expression to get the target date
        target_date = self.parse_date_expression(filter_expression)
        
        if target_date:
            # Exact match for parsed expressions
            return task_due_date == target_date
        else:
            # Fallback to substring matching for unparsed expressions
            return filter_expression.lower() in task_due_date.lower()
    
    def matches_date_filter_by(self, task_due_date: Optional[str], filter_expression: str) -> bool:
        """Check if a task's due date is on or before the specified date.
        
        Args:
            task_due_date: Due date from the task (may be None)
            filter_expression: Filter expression to match against
            
        Returns:
            True if the task is due on or before the specified date
        """
        if not task_due_date:
            return False
        
        # Parse the filter expression to get the target date
        target_date = self.parse_date_expression(filter_expression)
        
        if target_date:
            # Compare dates - task due date should be <= target date
            return self._compare_dates(task_due_date, target_date) <= 0
        else:
            # Fallback to substring matching for unparsed expressions
            return filter_expression.lower() in task_due_date.lower()
    
    def _compare_dates(self, date1: str, date2: str) -> int:
        """Compare two date strings.
        
        Args:
            date1: First date string
            date2: Second date string
            
        Returns:
            -1 if date1 < date2, 0 if equal, 1 if date1 > date2
        """
        # Normalize dates for comparison
        norm_date1 = self._normalize_date_for_comparison(date1)
        norm_date2 = self._normalize_date_for_comparison(date2)
        
        if norm_date1 < norm_date2:
            return -1
        elif norm_date1 > norm_date2:
            return 1
        else:
            return 0
    
    def _normalize_date_for_comparison(self, date_str: str) -> str:
        """Normalize a date string for comparison purposes.
        
        This handles different date formats and converts them to a comparable format.
        
        Args:
            date_str: Date string to normalize
            
        Returns:
            Normalized date string for comparison
        """
        # Handle standard YYYY-MM-DD format
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str
        
        # Handle YYYY-MM format (treat as end of month for comparison)
        if re.match(r'^\d{4}-\d{2}$', date_str):
            year, month = date_str.split('-')
            # Use last day of month for comparison
            if month in ['01', '03', '05', '07', '08', '10', '12']:
                return f"{year}-{month}-31"
            elif month in ['04', '06', '09', '11']:
                return f"{year}-{month}-30"
            elif month == '02':
                # Simple leap year check
                year_int = int(year)
                if year_int % 4 == 0 and (year_int % 100 != 0 or year_int % 400 == 0):
                    return f"{year}-{month}-29"
                else:
                    return f"{year}-{month}-28"
        
        # Handle YYYY format (treat as end of year)
        if re.match(r'^\d{4}$', date_str):
            return f"{date_str}-12-31"
        
        # Handle week format YYYY-W## (approximate to middle of week)
        week_match = re.match(r'^(\d{4})-W(\d{2})$', date_str)
        if week_match:
            year = int(week_match.group(1))
            week = int(week_match.group(2))
            # Approximate: assume week 1 starts on Jan 1, each week is 7 days
            # This is a simplification but good enough for comparison
            day_of_year = (week - 1) * 7 + 4  # Middle of the week
            try:
                from datetime import datetime, timedelta
                jan_1 = datetime(year, 1, 1)
                target_date = jan_1 + timedelta(days=day_of_year - 1)
                return target_date.strftime('%Y-%m-%d')
            except:
                return f"{year}-{week:02d}-15"  # Fallback
        
        # Handle quarter format YYYY-Q# (treat as end of quarter)
        quarter_match = re.match(r'^(\d{4})-Q([1-4])$', date_str)
        if quarter_match:
            year = quarter_match.group(1)
            quarter = int(quarter_match.group(2))
            quarter_end_months = {1: "03-31", 2: "06-30", 3: "09-30", 4: "12-31"}
            return f"{year}-{quarter_end_months[quarter]}"
        
        # Handle slash format
        if '/' in date_str:
            # Convert slashes to dashes and try again
            dash_format = date_str.replace('/', '-')
            return self._normalize_date_for_comparison(dash_format)
        
        # Return as-is if we can't parse it
        return date_str

    # Keep the old method for backward compatibility but rename it
    def matches_date_filter(self, task_due_date: Optional[str], filter_expression: str) -> bool:
        """Check if a task's due date matches a filter expression (exact match).
        
        This method is kept for backward compatibility and delegates to matches_date_filter_on.
        
        Args:
            task_due_date: Due date from the task (may be None)
            filter_expression: Filter expression to match against
            
        Returns:
            True if the task matches the filter
        """
        return self.matches_date_filter_on(task_due_date, filter_expression)


# Global instance for convenience
_default_parser = None

def get_date_parser(current_date: Optional[datetime] = None) -> DateParser:
    """Get a DateParser instance.
    
    Args:
        current_date: Current date to use. If None, uses global default or creates new one.
        
    Returns:
        DateParser instance
    """
    global _default_parser
    
    if current_date is not None:
        return DateParser(current_date)
    
    if _default_parser is None:
        _default_parser = DateParser()
    
    return _default_parser


def parse_date_expression(expression: str, current_date: Optional[datetime] = None) -> Optional[str]:
    """Convenience function to parse a date expression.
    
    Args:
        expression: Date expression to parse
        current_date: Current date to use as reference
        
    Returns:
        Standardized date string or None if parsing fails
    """
    parser = get_date_parser(current_date)
    return parser.parse_date_expression(expression)