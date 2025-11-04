"""Terminal formatting utilities for tasks using Rich library.

This module provides classes and functions for formatting tasks with colors,
syntax highlighting, and proper layout for terminal display.
"""

from typing import List, Dict
from collections import defaultdict
from pathlib import Path
import re

from rich.console import Console
from rich.text import Text
from rich.panel import Panel

from .task import Task
from .config import get_config
from .dateutils import get_date_parser
from itertools import pairwise

id_color = "grey39"

class TaskFormatter:
    """Formatter for displaying tasks in the terminal with Rich formatting.
    
    This class handles all the visual formatting of tasks including:
    - Colored status symbols
    - Syntax highlighting for tags, due dates, and priorities
    - Multi-line description formatting
    - File grouping and headers
    - Optional line number display
    
    The formatter uses the Rich library to provide colored output and
    professional-looking terminal display.
    """
    
    def __init__(self, console: Console = None):
        """Initialize the formatter.
        
        Args:
            console: Rich Console instance to use. If None, creates a new one.
        """
        self.console = console or Console()
        self.date_parser = get_date_parser()
        
        # Status colors for different task states
        self.status_colors = {
            'OPEN': 'white',
            'CHECKED': 'green',
            'ONGOING': 'yellow',
            'OBSOLETE': 'red',
            'IN_QUESTION': 'magenta'
        }
    
    def _normalize_date_for_display(self, date_str: str) -> str:
        """Normalize a date string to YYYY-MM-DD format for display.
        
        Args:
            date_str: Original date string from task
            
        Returns:
            Normalized date string in YYYY-MM-DD format
        """
        # Handle standard YYYY-MM-DD format (already correct)
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str
        
        # Handle YYYY-MM format (treat as last day of month for display)
        if re.match(r'^\d{4}-\d{2}$', date_str):
            year, month = date_str.split('-')
            year_int, month_int = int(year), int(month)
            
            # Calculate last day of the month
            if month_int in [1, 3, 5, 7, 8, 10, 12]:
                last_day = 31
            elif month_int in [4, 6, 9, 11]:
                last_day = 30
            elif month_int == 2:
                # Check for leap year
                if year_int % 4 == 0 and (year_int % 100 != 0 or year_int % 400 == 0):
                    last_day = 29
                else:
                    last_day = 28
            else:
                last_day = 31  # fallback
            
            return f"{year}-{month}-{last_day:02d}"
        
        # Handle YYYY format (treat as last day of year for display)
        if re.match(r'^\d{4}$', date_str):
            return f"{date_str}-12-31"
        
        # Handle week format YYYY-W## (convert to last day of that week - Sunday)
        week_match = re.match(r'^(\d{4})-W(\d{2})$', date_str)
        if week_match:
            year = int(week_match.group(1))
            week = int(week_match.group(2))
            # Calculate the last day (Sunday) of the specified week
            from datetime import datetime, timedelta
            try:
                # Find the first day of the year
                jan_1 = datetime(year, 1, 1)
                # Find what day of the week Jan 1 is (0=Monday, 6=Sunday)
                jan_1_weekday = jan_1.weekday()
                
                # Calculate the start of week 1 (Monday)
                # If Jan 1 is not Monday, find the Monday of week 1
                if jan_1_weekday == 0:  # Jan 1 is Monday
                    week_1_monday = jan_1
                else:
                    days_to_monday = 7 - jan_1_weekday
                    week_1_monday = jan_1 + timedelta(days=days_to_monday)
                
                # Calculate the target week's Monday
                target_monday = week_1_monday + timedelta(weeks=week - 1)
                # Get the Sunday (last day) of that week
                target_sunday = target_monday + timedelta(days=6)
                
                return target_sunday.strftime('%Y-%m-%d')
            except:
                # Fallback if date calculation fails
                return f"{year}-{week:02d}-07"
        
        # Handle quarter format YYYY-Q# (convert to last day of quarter)
        quarter_match = re.match(r'^(\d{4})-Q([1-4])$', date_str)
        if quarter_match:
            year = quarter_match.group(1)
            quarter = int(quarter_match.group(2))
            quarter_end_dates = {1: "03-31", 2: "06-30", 3: "09-30", 4: "12-31"}
            return f"{year}-{quarter_end_dates[quarter]}"
        
        # Handle slash format (convert to dash format and try again)
        if '/' in date_str:
            # Convert slashes to dashes and try again
            dash_format = date_str.replace('/', '-')
            return self._normalize_date_for_display(dash_format)
        
        # Return as-is if we can't normalize it
        return date_str

    def format_task(self, task: Task, show_location: bool = False, no_id: bool = False) -> Text:
        """Format a single task using Rich for colored terminal output.
        
        Args:
            task: Task object to format
            show_location: Whether to include file path and line number in output
            no_id: Whether to include task ID in output
            
        Returns:
            Rich Text object with colored formatting
        """
        # Create the main text object
        text = Text()
        
        # Add task ID if requested, with zero padding and reduced opacity
        if not no_id:
            # Calculate the number of digits needed for zero padding based on task ID
            # Use at least 3 digits for padding
            total_digits = max(3, len(str(task.id)))
            padded_id = f"#{task.id:0{total_digits}d}"
            text.append(padded_id, style=id_color)
            text.append(" ")
            indentation_continuation = " " * (len(padded_id) + 1 + 4) # ID + space + status 
            len_id_part = len(padded_id) + 1
        else:
            indentation_continuation = " " * 4  # Status
            len_id_part = 0

        # Add status symbol with color
        # Get status type name for color mapping
        status_name = task.status.status_type.name
        status_color = self.status_colors.get(status_name, 'white')
        text.append(task.status_symbol, style=f"bold {status_color}")
        text.append(" ")
        
        # Add priority indicator if task has priority
        if task.has_priority:
            priority_indicator = task.priority_indicator
            text.append(priority_indicator, style="bold red")
            text.append(" ")
        
        # Parse and format the description with highlighting
        # Use display text to avoid duplicating priority (but keep tags/dates)
        display_description = task.description.get_display_text()
        description_lines = display_description.split('\n')
        
        for i, line in enumerate(description_lines):
            if i > 0:
                # Add newline and indentation for continuation lines
                text.append("\n" + indentation_continuation)
            
            # Process the line for tags, due dates, and priority
            line_text = self._format_description_line(line)
            text.append(line_text)

        # strikethrough for completed tasks and 
        if task.status.status_type.name == 'CHECKED':
            self.strikethrough_text(text, len_id_part, len(indentation_continuation))
            # Dim the text for completed tasks
            text.stylize(id_color, len(indentation_continuation), len(text.plain))
        
        # Add line number if requested
        if show_location:
            text.append(f"    ({str(task.location)})", style="dim")
        
        return text

    def strikethrough_text(self, text: Text, id_part_length: int, indentation_length: int) -> None:
        """Apply strikethrough style to the task description in the Text object.
        
        Args:
            text: Rich Text object containing the formatted task
            id_part_length: Length of the ID part (for offset)
            indentation_length: Length of the indentation before description for the second+ lines
        """
        n_lines = text.plain.count("\n") + 1
        
        start_indices = []
        end_indices = []
        if n_lines == 1:
            start_indices.append(indentation_length)
            end_indices.append(len(text.plain))
        else:
            # get location of "\n" to file the end of the lines
            line_breaks = [0] + [i for i, char in enumerate(text.plain) if char == "\n"]
            idx = 0
            for s, e in pairwise(line_breaks + [len(text.plain)]):
                if idx == 0:
                    # First line
                    start_indices.append(indentation_length)
                    end_indices.append(e)
                else:
                    # Continuation lines
                    start_indices.append(s + 1 + indentation_length)
                    end_indices.append(e)
                idx += 1
        
        # Apply strikethrough from start_index to end of text
        for i, j in zip(start_indices, end_indices):
            text.stylize("strike", i, j)


    def _format_description_line(self, line: str) -> Text:
        """Format a single line of description with syntax highlighting.
        
        Args:
            line: Line of text to format
            
        Returns:
            Rich Text object with highlighted tags and due dates
        """
        text = Text()
        i = 0
        
        while i < len(line):
            # Check for due date pattern (-> date)
            if i < len(line) - 2 and line[i:i+2] == '->':
                # Find the end of the due date
                j = i + 2
                while j < len(line) and line[j] == ' ':
                    j += 1  # Skip spaces after ->
                
                # Find the actual date part
                date_start = j
                while j < len(line) and (line[j].isalnum() or line[j] in '-/WQ'):
                    j += 1
                
                if j > date_start:
                    # Extract and normalize the date
                    original_date = line[date_start:j]
                    normalized_date = self._normalize_date_for_display(original_date)
                    
                    # Add the -> part
                    text.append(line[i:date_start], style="cyan")
                    # Add the normalized date part
                    text.append(normalized_date, style="bold cyan")
                    i = j
                    continue
            
            # Check for tag pattern (#tag or #tag=value)
            elif line[i] == '#':
                # Find the end of the tag
                j = i + 1
                while j < len(line) and (line[j].isalnum() or line[j] in '_-'):
                    j += 1
                
                # Check for tag value
                if j < len(line) and line[j] == '=':
                    j += 1  # Skip =
                    # Handle quoted values
                    if j < len(line) and line[j] in '"\'':
                        quote = line[j]
                        j += 1
                        while j < len(line) and line[j] != quote:
                            j += 1
                        if j < len(line):
                            j += 1  # Include closing quote
                    else:
                        # Unquoted value
                        while j < len(line) and (line[j].isalnum() or line[j] in '_-'):
                            j += 1
                
                if j > i + 1:  # Valid tag found
                    text.append(line[i:j], style="bold blue")
                    i = j
                    continue
            
            # Check for priority pattern (! or . at start or after space)
            elif line[i] == '!' and (i == 0 or line[i-1] == ' '):
                # Find consecutive ! and . characters
                j = i
                while j < len(line) and line[j] in '!.':
                    j += 1
                
                # Only highlight if followed by space (valid priority)
                if j < len(line) and line[j] == ' ':
                    text.append(line[i:j], style="bold red")
                    i = j
                    continue
            
            # Regular character
            text.append(line[i])
            i += 1
        
        return text

    def display_tasks(self, tasks: List[Task], show_location: bool = False, no_id: bool = False) -> None:
        """Display a list of tasks with Rich formatting.
        
        Args:
            tasks: List of tasks to display
            show_location: Whether to show file path and line number
            no_id: Whether to hide task IDs
        """
        if not tasks:
            self.console.print("[yellow]No tasks to display.[/yellow]")
            return
        
        
        for task in tasks:
            task_text = self.format_task(task, show_location=show_location, no_id=no_id)
            self.console.print(task_text)
        
        self.console.print()  # Add a newline at the end
            
    
    def display_summary(self, filtered_count: int, total_count: int) -> None:
        """Display a summary of filtered vs total tasks.
        
        Args:
            filtered_count: Number of tasks shown after filtering
            total_count: Total number of tasks found
        """
        if filtered_count != total_count:
            self.console.print(f"[dim]Showing {filtered_count} of {total_count} total tasks.[/dim]")
    
    def display_count(self, count: int) -> None:
        """Display just the count of tasks.
        
        Args:
            count: Number of tasks
        """
        self.console.print(f"[green]{count} tasks found.[/green]")
    
    def display_error(self, message: str) -> None:
        """Display an error message.
        
        Args:
            message: Error message to display
        """
        message = message.replace("[", "\\[")
        self.console.print(f"[red]{message}[/red]")
    
    def display_warning(self, message: str) -> None:
        """Display a warning message.
        
        Args:
            message: Warning message to display
        """
        message = message.replace("[", "\\[")
        self.console.print(f"[yellow]{message}[/yellow]")
    
    def display_success(self, message: str) -> None:
        """Display a success message.
        
        Args:
            message: Success message to display
        """
        message = message.replace("[", "\\[")
        self.console.print(f"[green]{message}[/green]")


# Convenience function for backward compatibility
def format_task_rich(task: Task, show_location: bool = False, no_id: bool = False) -> Text:
    """Format a task using Rich for colored terminal output.
    
    This is a convenience function that creates a formatter and formats a single task.
    
    Args:
        task: Task object to format
        show_location: Whether to include file path and line number in output
        no_id: Whether to include task ID in output
        
    Returns:
        Rich Text object with colored formatting
    """
    formatter = TaskFormatter()
    return formatter.format_task(task, show_location=show_location, no_id=no_id)