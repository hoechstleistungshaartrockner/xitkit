"""
Description
===========

This module provides functionality to handle descriptions for tasks
in the xit framework.
"""

from dataclasses import dataclass, field
from .tags import Tag
from copy import deepcopy
import re
from typing import Optional

@dataclass
class Description:
    """Class representing a task description."""
    text: str = field(default_factory=str)
    tags: list = field(init=False)

    def __post_init__(self):
        """Post-initialization to extract tags from the text."""
        self.tags = Tag.from_line(self.text)

    def __str__(self) -> str:
        """String representation of the description."""
        return self.text

    def set_text(self, new_text: Optional[str]) -> None:
        """Set the description text.

        Args:
            new_text (Optional[str]): The new description text.
        """
        if new_text is None:
            new_text = ""
        self.text = new_text
        # Re-extract tags from the new text
        self.tags = Tag.from_line(self.text)

    def add_tag(self, tag: Tag) -> None:
        """Add a tag to the description.

        Args:
            tag (Tag): The tag to add.
        """
        # Check if tag already exists to avoid duplicates
        if tag not in self.tags:
            self.tags.append(tag)
            # Add tag to text
            if self.text:
                self.text += f" {str(tag)}"
            else:
                self.text = str(tag)

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
        
        # Clean up extra whitespace
        self.text = re.sub(r'\s+', ' ', self.text).strip()

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

    def copy(self) -> 'Description':
        """Create a deep copy of the description.

        Returns:
            Description: A deep copy of the current description.
        """
        return deepcopy(self)

    @staticmethod
    def identify_tags(text: str) -> list:
        """Identify and extract tags from a given text.

        Args:
            text (str): The text to extract tags from.
        Returns:
            list: A list of Tag objects identified in the text.
        """
        return Tag.from_line(text)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Description(text='{self.text}', tags={self.tags})"
    
    def __eq__(self, other) -> bool:
        """Check equality with another Description."""
        if not isinstance(other, Description):
            return False
        return self.text == other.text and self.tags == other.tags
    
    def __hash__(self) -> int:
        """Hash function for Description objects."""
        return hash((self.text, tuple(self.tags)))
    
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
