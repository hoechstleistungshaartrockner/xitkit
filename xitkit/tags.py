"""
Tags
----

Module for handling task tags in the Xit task management system.
"""

from dataclasses import dataclass
from typing import List, Optional
from .patterns import TAG_PATTERN

@dataclass
class Tag:
    """Class representing a task tag."""
    name: str
    value: Optional[str] = None

    def __str__(self) -> str:
        """String representation of the tag."""
        if self.value is not None and ' ' not in self.value:
            return f"#{self.name}={self.value}"
        if self.value is not None and ' ' in self.value:
            return f'#{self.name}="{self.value}"'
        return f"#{self.name}"
    
    @staticmethod
    def from_line(line: str) -> List['Tag']:
        """Parse tags from a line of text using regular expressions.

        Args:
            line (str): The line of text containing tags.
        Returns:
            List[Tag]: A list of Tag objects parsed from the line.
        """
        tags = []
        for match in TAG_PATTERN.finditer(line):
            tag_name = match.group(1)
            # Check each group individually to preserve empty strings
            if match.group(2) is not None:  # Double-quoted value
                tag_value = match.group(2)
            elif match.group(3) is not None:  # Single-quoted value
                tag_value = match.group(3)
            elif match.group(4) is not None:  # Unquoted value
                tag_value = match.group(4)
            else:
                tag_value = None
            tags.append(Tag(name=tag_name, value=tag_value))
        return tags

    def compare(self, other: 'Tag', soft: bool = False) -> bool:
        """Compare this tag with another tag.

        Args:
            other (Tag): The other tag to compare with.
            soft (bool): If True, only compare names; if False, compare names and values.
        Returns:
            bool: True if tags are considered equal, False otherwise.
        """
        # Truth table:
        # name identical    value identical    soft    result
        #       T                  T             T       T
        #       T                  T             F       T
        #       T                  F             T       T
        #       T                  F             F       F
        #       F                  T             T       F
        #       F                  T             F       F
        #       F                  F             T       F
        #       F                  F             F       F
        name_equal = self.name == other.name
        value_equal = self.value == other.value
        return name_equal and (soft or value_equal)

    def __hash__(self) -> int:
        """Hash function for the Tag class."""
        return hash((self.name, self.value))

    def __eq__(self, other: object) -> bool:
        """Equality comparison for the Tag class."""
        if not isinstance(other, Tag):
            return NotImplemented
        return self.compare(other, soft=False)

    @staticmethod
    def tags_to_string(tags: List[Tag]) -> str:
        """Convert a list of Tag objects to a string representation.

        Args:
            tags (List[Tag]): The list of Tag objects.
        Returns:
            str: A string representation of the tags.
        """
        return ' '.join(str(tag) for tag in tags)

