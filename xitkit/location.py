"""
Location
--------

This module provides the Location class, which represents a specific location within a file.

"""

from pathlib import Path
from itertools import pairwise



class Location:
    """Represents a specific location within a file."""
    
    def __init__(self, file_path=None, line_numbers=None, section=None):
        """
        Initialize a Location instance.

        Args:
            file_path: the path to the file.
            line_numbers: the line numbers within the file.
        """

        if file_path is None:
            self.file_path = Path("todo.xit")
        else:
            self.file_path = Path(file_path)

        self.set_line_numbers(line_numbers)
        self.set_section(section)

    def __repr__(self):
        return f"Location(file_path={self.file_path}, line_numbers={list(self.line_numbers) if self.line_numbers is not None else None})"
    
    def __eq__(self, other):
        if not isinstance(other, Location):
            return False
        return self.file_path == other.file_path and self.line_numbers == other.line_numbers
    
    def __hash__(self):
        return hash((self.file_path, tuple(self.line_numbers)))
    
    def set_file_path(self, new_file_path):
        """Set a new file path for the location."""
        self.file_path = Path(new_file_path)

    def set_line_numbers(self, new_line_numbers):
        """Set new line numbers for the location."""
        if new_line_numbers is None:
            self.line_numbers = None
        elif isinstance(new_line_numbers, int):
            self.line_numbers = range(new_line_numbers, new_line_numbers + 1)
        elif isinstance(new_line_numbers, range):
            self.line_numbers = new_line_numbers
        elif isinstance(new_line_numbers, list):
            if all(isinstance(num, int) for num in new_line_numbers):
                sorted_lines = sorted(new_line_numbers)
                for a, b in pairwise(sorted_lines):
                    if b != a + 1:
                        raise ValueError("line_numbers list must contain consecutive integers.")
                self.line_numbers = range(sorted_lines[0], sorted_lines[-1] + 1)
            else:
                raise TypeError("All elements in line_numbers list must be integers.")
        else:
            raise TypeError("new_line_numbers must be an int or a range.")
        
    @property
    def relative_path(self):
        """Get the relative file path as a string."""
        return str(self.file_path)
    
    def resolve_line_numbers(self):
        """Gets a string representation of the line numbers."""
        if self.line_numbers is None:
            return ""
        if self.line_numbers.start == self.line_numbers.stop - 1:
            return str(self.line_numbers.start)
        else:
            return f"{self.line_numbers.start}-{self.line_numbers.stop - 1}"
    
    def __str__(self):
        return f"{self.relative_path}:{self.resolve_line_numbers()}"

    @property
    def filename(self):
        """Get the filename from the file path."""
        return self.file_path.name
    
    def extend_line_numbers(self, new_line_number):
        """Extend the line numbers to include a new line number."""
        if self.line_numbers is None:
            self.line_numbers = range(new_line_number, new_line_number + 1)
            return
        if new_line_number == self.line_numbers.stop:
            self.line_numbers = range(self.line_numbers.start, new_line_number + 1)
            return
        raise ValueError(f"new_line_number is not consecutive to the current line_numbers range. Current line numbers: {self.line_numbers}, new_line_number: {new_line_number}")
    
    def set_section(self, section):
        """Set the section for the location."""
        self.section = section

    