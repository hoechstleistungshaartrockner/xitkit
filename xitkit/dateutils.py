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
        self.relative_pattern = re.compile(r'(?P<years>\d+y)?(?P<months>\d+m)?(?P<weeks>\d+w)?(?P<days>\d+d)?', re.IGNORECASE)
        
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
            amount = {'years': relative_match.group('years'),
                      'months': relative_match.group('months'),
                      'weeks': relative_match.group('weeks'),
                      'days': relative_match.group('days')}
            # strip the unit letters and convert to int or None
            for key in amount:
                if amount[key]:
                    amount[key] = int(amount[key][:-1])  # remove last char (unit)
                else:
                    amount[key] = 0
            
            if not relative_match.span() == (0, 0):
                target_date = self._calculate_relative_date(**amount)
                return target_date.strftime('%Y-%m-%d')
        
        # Handle standard date formats (return as-is if valid)
        if self._is_valid_standard_date(expression):
            return expression
        
        return None

    def _calculate_relative_date(self, years: int = 0, months: int = 0, weeks: int = 0, days: int = 0) -> Optional[datetime]:
        """Calculate a date relative to the current date.
        
        Args:
            years: Number of years
            months: Number of months
            weeks: Number of weeks
            days: Number of days
            
        Returns:
            Calculated datetime or None if invalid unit
        """
        # resolve None values
        resolve_options = {None: 0,}
        intervals = [resolve_options.get(i, i) for i in [years, months, weeks, days]]
        factors = [365, 30, 7, 1]
        total_days = sum(f * int(v) for f, v in zip(factors, intervals))
        return self.current_date + timedelta(days=total_days)
        

    
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
        
        # Handle week format YYYY-W## (return Sunday of that week)
        week_match = re.match(r'^(\d{4})-W(\d{2})$', date_str)
        if week_match:
            year = int(week_match.group(1))
            week = int(week_match.group(2))
            try:
                # Use proper ISO week calculation
                # January 4th is always in week 1
                jan_4 = datetime(year, 1, 4).date()
                # Find Monday of week 1 (ISO weeks start on Monday)
                monday_week_1 = jan_4 - timedelta(days=jan_4.weekday())
                # Calculate Monday of target week
                monday_target = monday_week_1 + timedelta(weeks=week-1)
                # Sunday is 6 days later (end of week)
                sunday_target = monday_target + timedelta(days=6)
                return sunday_target.strftime('%Y-%m-%d')
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


def parse_interval_expression(interval: str) -> timedelta:
    """Parse interval expression for recurring tasks.
    
    Supports formats like:
    - 1d, 7d (days)
    - 1w, 2w (weeks)
    - 1m, 3m (months - approximated as 30 days)
    - 1y (years - approximated as 365 days)
    - 1w2d, 2m3w4d (composite intervals)
    
    Args:
        interval: Interval expression (e.g., "1w", "30d", "3m", "1w2d")
        
    Returns:
        timedelta object representing the interval
        
    Raises:
        ValueError: If interval format is invalid
    """
    if not interval or not isinstance(interval, str):
        raise ValueError("Interval must be a non-empty string")
    
    # Remove whitespace and make lowercase
    interval = interval.strip().lower()
    
    # Pattern for finding all interval components (e.g., "1w", "2d" from "1w2d")
    pattern = re.compile(r'([+-]?\d+)([dwmy])')
    matches = pattern.findall(interval)
    
    if not matches:
        raise ValueError(f"Invalid interval format: '{interval}'. Use format like '1d', '2w', '3m', '1y', or composites like '1w2d'")
    
    # Check that the entire string was consumed by matches
    # Reconstruct what the matches would produce and compare
    reconstructed = ''.join(f"{amount}{unit}" for amount, unit in matches)
    if reconstructed != interval:
        raise ValueError(f"Invalid interval format: '{interval}'. Use format like '1d', '2w', '3m', '1y', or composites like '1w2d'")
    
    total_delta = timedelta()
    
    for amount_str, unit in matches:
        amount = int(amount_str)
        
        if amount <= 0:
            raise ValueError("Interval amount must be positive")
        
        # Convert to timedelta and add to total
        if unit == 'd':  # days
            total_delta += timedelta(days=amount)
        elif unit == 'w':  # weeks
            total_delta += timedelta(weeks=amount)
        elif unit == 'm':  # months (approximate as 30 days)
            total_delta += timedelta(days=amount * 30)
        elif unit == 'y':  # years (approximate as 365 days)
            total_delta += timedelta(days=amount * 365)
        else:
            raise ValueError(f"Unsupported interval unit: '{unit}'. Use d, w, m, or y")
    
    return total_delta


def generate_recurring_dates(start_date: str, interval: str, end_date: str = None, 
                           count: int = None) -> list[str]:
    """Generate a list of recurring dates based on interval.
    
    Args:
        start_date: Starting date in YYYY-MM-DD format
        interval: Interval expression (e.g., "1w", "30d", "3m")
        end_date: Optional end date in YYYY-MM-DD format
        count: Optional maximum number of occurrences
        
    Returns:
        List of date strings in YYYY-MM-DD format
        
    Raises:
        ValueError: If parameters are invalid
    """
    if not start_date:
        # assume today if not provided
        start_date = str(datetime.now().strftime("%Y-%m-%d"))
    
    # Parse start date
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid start date format: '{start_date}'. Use YYYY-MM-DD format")
    
    # Parse interval
    interval_delta = parse_interval_expression(interval)
    
    # Parse end date if provided
    end_dt = None
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid end date format: '{end_date}'. Use YYYY-MM-DD format")
        
        if end_dt <= start_dt:
            raise ValueError("End date must be after start date")
    
    # Validate count
    if count is not None:
        if count <= 0:
            raise ValueError("Count must be positive")
        if count > 1000:  # Reasonable limit
            raise ValueError("Count cannot exceed 1000 occurrences")
    
    # Require at least one limit parameter
    if end_date is None and count is None:
        raise ValueError("Either end_date or count must be specified")
    
    # Generate dates
    dates = []
    current_dt = start_dt
    occurrence_count = 0
    
    while True:
        # Check if we've reached the end date
        if end_dt and current_dt > end_dt:
            break
        
        # Check if we've reached the max count
        if count and occurrence_count >= count:
            break
        
        # Add current date
        dates.append(current_dt.strftime("%Y-%m-%d"))
        occurrence_count += 1
        
        # Move to next occurrence
        current_dt += interval_delta
        
        # Safety check to prevent infinite loops
        if len(dates) > 1000:
            raise ValueError("Too many occurrences generated (limit: 1000)")
    
    return dates