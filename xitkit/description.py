"""
Description
===========

This module provides functionality to handle descriptions for tasks
in the xit framework.
"""

from dataclasses import dataclass, field
from .tags import Tag
from .duedate import DueDate
from .priority import Priority
from copy import deepcopy
import re
from typing import Optional

@dataclass
class Description:
    """Class representing a task description with optional due date."""
    text: str = field(default_factory=str)
    priority: Optional[Priority] = field(init=False)
    tags: list = field(init=False)
    due_date: Optional[DueDate] = field(init=False)

    def __post_init__(self):
        """Post-initialization to extract tags and due date from the text."""
        self.text = self.text.replace('\\n', '\n')  # Convert escaped newlines to actual newlines
        self.priority = Priority.from_line(self.text)
        self.tags = Tag.from_line(self.text)
        self.due_date = DueDate.from_line(self.text)

    def __str__(self) -> str:
        """String representation of the description."""
        return self.text

    # Methods for manipulating and accessing the text.

    def update(self, new_text=None, new_priority=None, new_due_date=None, new_tags=None) -> None:
        """Update the description text and optionally priority, due date, and tags. Needs to be called before setting new attributes.

        Args:
            new_text (str): The new description text.
            new_priority (Optional[Priority]): New priority to set.
            new_due_date (Optional[DueDate]): New due date to set.
            new_tags (Optional[list]): New list of tags to set.
        """
        if new_text is not None:
            self.text = new_text
        
        # Update priority if provided
        if new_priority is not None:
            self.text.replace(str(self.priority), str(new_priority), 1)
            self.priority = new_priority

    def get_clean_text(self) -> str:
        """Get description text without tags, due dates, and priority indicators.
        
        Returns:
            str: The description text with tags, due dates, and priority indicators removed.
        """
        text = self.text
        
        # Remove priority indicators including dots (..!!, !!, !.., etc.)
        # This should match the same pattern as PRIORITY_PATTERN but remove it from start of text
        text = re.sub(Priority.regex_pattern, '', text).strip()
        
        # Remove due date patterns (-> YYYY-MM-DD)
        text = re.sub(DueDate.regex_pattern, '', text).strip()
        
        # Remove tags (#tagname)
        text = re.sub(Tag.regex_pattern, "", text).strip()
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def get_display_text(self) -> str:
        """Get description text suitable for display (removes priority but keeps tags/dates).
        
        Returns:
            str: The description text with only priority indicators removed.
        """
        text = self.text
        
        # Remove priority indicators using a pattern that only matches when exclamation marks are present
        # This handles patterns like !, !!, ....!, !!!, etc.
        lines = text.split('\n')
        if lines:
            # Remove priority from the first line only, but only if there are actual exclamation marks
            match = re.search(Priority.regex_pattern, lines[0])
            if match and match.groupdict().get('level', ''):
                # Only remove if the match contains exclamation marks
                lines[0] = re.sub(Priority.regex_pattern, '', lines[0]).lstrip()
        
        return '\n'.join(lines)

    def set_text(self, new_text: Optional[str]) -> None:
        """Set the description text.

        Args:
            new_text (Optional[str]): The new description text.
        """
        if new_text is None:
            new_text = ""
        self.text = new_text
        # Re-extract tags and due date from the new text
        self.tags = Tag.from_line(self.text)
        self.due_date = DueDate.from_line(self.text)

    # Methods for manipulating tags.

    def add_tag(self, tag: Tag) -> bool:
        """Add a tag to the description.

        Args:
            tag (Tag): The tag to add.
            
        Returns:
            bool: True if the tag was added, False if it was already present.
        """
        # Check if tag already exists to avoid duplicates
        if tag not in self.tags:
            self.tags.append(tag)
            
            # Add tag to text
            if not self.text:
                self.text = str(tag)
                return True
            
            pattern = re.compile(r'(\s|^)' + re.escape(str(tag)) + r'(\s|$)')
            if not pattern.search(self.text):
                self.text += " " + str(tag)
            return True
        return False

    def remove_tag(self, tag: Tag, soft: bool = False) -> None:
        """Remove a tag from the description.

        Args:
            tag (Tag): The tag to remove.
            soft (bool): If True, remove from list of tags and remove the pound sign only from text;
                         if False, remove from both tags and text completely.
        """
        # Find matching tags (exact or by name for soft removal)
        tags_to_remove = []
        for existing_tag in self.tags[:]:  # Make a copy to iterate
            if tag.compare(existing_tag, soft=soft):
                tags_to_remove.append(existing_tag)
        
        # Remove from tags list
        for tag_to_remove in tags_to_remove:
            if tag_to_remove in self.tags:
                self.tags.remove(tag_to_remove)
        
        # Handle text removal only if tag was actually in the tags list
        for tag_to_remove in tags_to_remove:
            tag_str = str(tag_to_remove)
            if not soft:
                # Remove all occurrences of the tag from text
                while tag_str in self.text:
                    # Handle various spacing scenarios
                    patterns_to_try = [
                        f"{tag_str} ",  # Tag with trailing space  
                        f" {tag_str}",  # Tag with leading space
                        tag_str,        # Just the tag
                    ]
                    
                    for pattern in patterns_to_try:
                        if pattern in self.text:
                            self.text = self.text.replace(pattern, "", 1)
                            break
            else:
                # Soft removal: remove only the '#' from the text
                tag_without_hash = tag_str[1:]  # Remove the '#'
                self.text = self.text.replace(tag_str, tag_without_hash)
        
        # Clean up extra whitespace but preserve line breaks
        self.text = re.sub(r'[ \t]+', ' ', self.text).strip()

    def get_tags(self) -> list:
        """Get the list of tags associated with the description.

        Returns:
            list: A copy of the list of tags.
        """
        return self.tags.copy()
    
    def clear_tags(self) -> None:
        """Clear all tags from the description."""
        # Remove all tags from text first
        for tag in self.tags[:]:  # Make a copy to iterate over
            self.remove_tag(tag)
        self.tags.clear()

    def has_tag(self) -> bool:
        """Check if the description has any tags.

        Returns:
            bool: True if there are tags, False otherwise.
        """
        return len(self.tags) > 0
    
    def has_specific_tag(self, tag: Tag, soft: bool = False) -> bool:
        """Check if the description has a specific tag.
        
        Args:
            tag (Tag): The tag to check for.
            soft (bool): If True, only compare tag names; if False, compare names and values.
        Returns:
            bool: True if the tag is present, False otherwise.
        """
        for existing_tag in self.tags:
            if existing_tag.compare(tag, soft=soft):
                return True
        return False

    def compare_tags(self, other: 'Description', soft: bool = False) -> bool:
            """Compare tags of this description with another description.

            Args:
                other (Description): The other description to compare with.
                soft (bool): If True, only compare tag names; if False, compare names and values.
            Returns:
                bool: True if tags are considered equal, False otherwise.
            """
            if len(self.tags) != len(other.tags):
                return False
            
            for tag in self.tags:
                matched = False
                for other_tag in other.tags:
                    if tag.compare(other_tag, soft=soft):
                        matched = True
                        break
                if not matched:
                    return False
            return True
            
    @staticmethod
    def identify_tags(text: str) -> list:
        """Identify and extract tags from a given text.

        Args:
            text (str): The text to extract tags from.
        Returns:
            list: A list of Tag objects identified in the text.
        """
        return Tag.from_line(text)


    # Methods for manipulating due dates.
    
    def has_due_date(self) -> bool:
        """Check if the description has a due date.
        
        Returns:
            bool: True if there is a valid due date, False otherwise.
        """
        return self.due_date is not None and self.due_date.is_valid
    
    def get_due_date(self) -> Optional[DueDate]:
        """Get the due date associated with the description.
        
        Returns:
            Optional[DueDate]: The due date or None if no valid due date exists.
        """
        return self.due_date
    
    def set_due_date(self, due_date: Optional[DueDate]) -> None:
        """Set or clear the due date for the description.
        
        Args:
            due_date (Optional[DueDate]): The due date to set, or None to clear.
        """
        # Remove existing due date from text if present
        if self.due_date is not None:
            due_date_str = str(self.due_date)
            if due_date_str in self.text:
                # Handle various spacing scenarios
                patterns_to_try = [
                    f"{due_date_str} ",  # Due date with trailing space  
                    f" {due_date_str}",  # Due date with leading space
                    due_date_str,        # Just the due date
                ]
                
                for pattern in patterns_to_try:
                    if pattern in self.text:
                        self.text = self.text.replace(pattern, "", 1)
                        break
                
                # Clean up extra whitespace
                self.text = re.sub(r'[ \t]+', ' ', self.text).strip()
        
        # Set new due date
        self.due_date = due_date
        
        # Add new due date to text if provided
        if due_date is not None and due_date.is_valid:
            if self.text:
                self.text += f" {str(due_date)}"
            else:
                self.text = str(due_date)
    
    def clear_due_date(self) -> None:
        """Remove the due date from the description."""
        self.set_due_date(None)
    
    def add_due_date_from_string(self, date_str: str) -> bool:
        """Add a due date from a date string.
        
        Args:
            date_str (str): Date string like "2025-12-31" or "2025-Q1"
            
        Returns:
            bool: True if due date was successfully added, False otherwise.
        """
        due_date = DueDate.from_string(date_str)
        if due_date is not None:
            self.set_due_date(due_date)
            return True
        return False

    # Methods for Priority handling.

    def get_priority(self) -> Optional[Priority]:
        """Get the priority associated with the description.

        Returns:
            Optional[Priority]: The priority or None if no valid priority exists.
        """
        return self.priority

    def has_priority(self) -> bool:
        """Check if the description has a priority.

        Returns:
            bool: True if there is a valid priority, False otherwise.
        """
        return self.priority.level > 0

    def set_priority(self, priority: Optional[Priority]) -> None:
        """Set or clear the priority for the description.

        Args:
            priority (Optional[Priority]): The priority to set, or None to clear.
        """
        # Remove existing priority from text if present
        if self.priority is not None and self.priority.level > 0:
            priority_str = str(self.priority)
            if priority_str in self.text:
                # Handle various spacing scenarios
                patterns_to_try = [
                    f"{priority_str} ",  # Priority with trailing space  
                    f" {priority_str}",  # Priority with leading space
                    priority_str,        # Just the priority
                ]
                
                for pattern in patterns_to_try:
                    if pattern in self.text:
                        self.text = self.text.replace(pattern, "", 1)
                        break
                
                # Clean up extra whitespace
                self.text = re.sub(r'\s+', ' ', self.text).strip()
        
        # Set new priority
        if priority is None:
            self.priority = Priority()
        else:
            self.priority = priority
        
        # Add new priority to text if provided
        if self.priority.level > 0:
            if self.text:
                self.text = f"{str(self.priority)} {self.text}"
            else:
                self.text = str(self.priority)

    def copy(self) -> 'Description':
        """Create a deep copy of the description.

        Returns:
            Description: A deep copy of the current description.
        """
        return deepcopy(self)

    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Description(text='{self.text}', priority={self.priority}, tags={self.tags}, due_date={self.due_date})"
    
    def __eq__(self, other) -> bool:
        """Check equality with another Description."""
        if isinstance(other, Description):
            return (self.text == other.text and 
                self.priority == other.priority and
                self.tags == other.tags and 
                self.due_date == other.due_date)
        elif isinstance(other, str):
            return self.text == other
        else:
            return NotImplemented
    
    def __hash__(self) -> int:
        """Hash function for Description objects."""
        return hash((self.text, tuple(self.tags), self.due_date))
    
    def to_display_format(self) -> str:
        """Get display format (same as text for now)."""
        return self.text
    
    def to_storage_format(self) -> str:
        """Get storage format (same as text for now)."""
        return self.text
    
    def get_tags_by_name(self, name: str) -> list:
        """Get all tags with a specific name.
        
        Args:
            name (str): The tag name to search for.
        Returns:
            list: List of tags with the specified name.
        """
        return [tag for tag in self.tags if tag.name == name]
    
    def get_tags_with_values(self) -> list:
        """Get all tags that have values (including empty string values).
        
        Returns:
            list: List of tags with non-None values.
        """
        return [tag for tag in self.tags if tag.value is not None]
    
    def get_tags_without_values(self) -> list:
        """Get all tags that don't have values.
        
        Returns:
            list: List of tags with None values.
        """
        return [tag for tag in self.tags if tag.value is None]
    
    def filter_tags_by_pattern(self, pattern: str) -> list:
        """Filter tags by pattern (simplified implementation).
        
        Args:
            pattern (str): Pattern to match against tag names.
        Returns:
            list: List of matching tags.
        """
        # Simple pattern matching - just check if pattern (without *) is in tag name
        pattern_clean = pattern.replace('*', '')
        return [tag for tag in self.tags if pattern_clean in tag.name]
    
    def replace_tag(self, old_tag: Tag, new_tag: Tag) -> None:
        """Replace an old tag with a new tag.
        
        Args:
            old_tag (Tag): The tag to replace.
            new_tag (Tag): The new tag to add.
        """
        if old_tag in self.tags:
            # Replace in tags list
            index = self.tags.index(old_tag)
            self.tags[index] = new_tag
            
            # Replace in text
            old_str = str(old_tag)
            new_str = str(new_tag)
            self.text = self.text.replace(old_str, new_str)
    
    def get_text_without_tags(self) -> str:
        """Get text with all tags removed.
        
        Returns:
            str: Text without any tags.
        """
        text = self.text
        for tag in self.tags:
            tag_str = str(tag)
            text = text.replace(tag_str, '')
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def get_text_without_tags_and_dates(self) -> str:
        """Get text with all tags and due dates removed.
        
        Returns:
            str: Text without any tags or due dates.
        """
        text = self.text
        
        # Remove tags
        for tag in self.tags:
            tag_str = str(tag)
            text = text.replace(tag_str, '')
        
        # Remove due date
        if self.due_date is not None:
            due_date_str = str(self.due_date)
            text = text.replace(due_date_str, '')
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def insert_text_at_position(self, position: int, text: str) -> None:
        """Insert text at a specific position.
        
        Args:
            position (int): Position to insert at.
            text (str): Text to insert.
        """
        self.text = self.text[:position] + text + self.text[position:]
    
    def append_text(self, text: str) -> None:
        """Append text to the end.
        
        Args:
            text (str): Text to append.
        """
        self.text += text
    
    def prepend_text(self, text: str) -> None:
        """Prepend text to the beginning.
        
        Args:
            text (str): Text to prepend.
        """
        self.text = text + self.text
    
    def replace_text_segment(self, old: str, new: str) -> None:
        """Replace a text segment.
        
        Args:
            old (str): Text to replace.
            new (str): Replacement text.
        """
        self.text = self.text.replace(old, new)
    
    def normalize_whitespace(self) -> None:
        """Normalize whitespace in the text."""
        self.text = re.sub(r'\s+', ' ', self.text).strip()
