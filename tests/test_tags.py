"""Tests for the Tag class."""

import pytest
from xit.tags import Tag


class TestTagBasics:
    """Test basic Tag functionality."""
    
    def test_tag_creation_name_only(self):
        """Test creating a tag with name only."""
        tag = Tag("work")
        
        assert tag.name == "work"
        assert tag.value is None
    
    def test_tag_creation_with_value(self):
        """Test creating a tag with name and value."""
        tag = Tag("priority", "high")
        
        assert tag.name == "priority"
        assert tag.value == "high"
    
    def test_tag_creation_empty_value(self):
        """Test creating a tag with empty value."""
        tag = Tag("status", "")
        
        assert tag.name == "status"
        assert tag.value == ""
    
    def test_tag_creation_with_spaces(self):
        """Test creating a tag with spaces in value."""
        tag = Tag("note", "important stuff")
        
        assert tag.name == "note"
        assert tag.value == "important stuff"


class TestTagStringRepresentation:
    """Test Tag string representation methods."""
    
    def test_str_name_only(self):
        """Test string representation of tag with name only."""
        tag = Tag("work")
        
        assert str(tag) == "#work"
    
    def test_str_with_value(self):
        """Test string representation of tag with value."""
        tag = Tag("priority", "high")
        
        assert str(tag) == "#priority=high"
    
    def test_str_with_empty_value(self):
        """Test string representation of tag with empty value."""
        tag = Tag("status", "")
        
        assert str(tag) == "#status="
    
    def test_str_with_special_characters(self):
        """Test string representation with special characters in name and value."""
        tag = Tag("project-name", "my-project_v1")
        
        assert str(tag) == "#project-name=my-project_v1"

    def test_str_with_unicode(self):
        """Test string representation with Unicode characters."""
        tag = Tag("项目", "网站")
        
        assert str(tag) == "#项目=网站"

    def test_str_with_spaces(self):
        """Test string representation with spaces in value."""
        tag = Tag("note", "important stuff")

        assert str(tag) == '#note="important stuff"'


class TestTagParsing:
    """Test Tag parsing from text."""
    
    def test_from_line_single_tag(self):
        """Test parsing a single tag from a line."""
        tags = Tag.from_line("This is a task #work")
        
        assert len(tags) == 1
        assert tags[0].name == "work"
        assert tags[0].value is None
    
    def test_from_line_multiple_tags(self):
        """Test parsing multiple tags from a line."""
        tags = Tag.from_line("Task with #work #urgent #project=website")
        
        assert len(tags) == 3
        assert tags[0].name == "work"
        assert tags[0].value is None
        assert tags[1].name == "urgent"
        assert tags[1].value is None
        assert tags[2].name == "project"
        assert tags[2].value == "website"
    
    def test_from_line_no_tags(self):
        """Test parsing from line with no tags."""
        tags = Tag.from_line("This is a task with no tags")
        
        assert len(tags) == 0
    
    def test_from_line_quoted_values(self):
        """Test parsing tags with quoted values."""
        tags = Tag.from_line('Task #title="My Task" #note=\'important stuff\'')
        
        assert len(tags) == 2
        assert tags[0].name == "title"
        assert tags[0].value == "My Task"
        assert tags[1].name == "note"
        assert tags[1].value == "important stuff"
    
    def test_from_line_empty_values(self):
        """Test parsing tags with empty values."""
        tags = Tag.from_line('Task #status= #type=""')
        
        assert len(tags) == 2
        assert tags[0].name == "status"
        assert tags[0].value == ""  # Empty unquoted value becomes empty string
        assert tags[1].name == "type"
        assert tags[1].value == ""  # Empty quoted value becomes empty string
    
    def test_from_line_unicode_tags(self):
        """Test parsing tags with Unicode characters."""
        tags = Tag.from_line("Task #项目=网站 #språk=norsk")
        
        assert len(tags) == 2
        assert tags[0].name == "项目"
        assert tags[0].value == "网站"
        assert tags[1].name == "språk"
        assert tags[1].value == "norsk"
    
    def test_from_line_complex_values(self):
        """Test parsing tags with complex values."""
        # URLs and special characters require quoted values for the current regex
        tags = Tag.from_line('Task #url="https://example.com" #version=1-2-3')
        
        assert len(tags) == 2
        assert tags[0].name == "url"
        assert tags[0].value == "https://example.com"
        assert tags[1].name == "version"
        assert tags[1].value == "1-2-3"


class TestTagComparison:
    """Test Tag comparison methods."""
    
    def test_compare_identical_tags(self):
        """Test comparing identical tags."""
        tag1 = Tag("work", "urgent")
        tag2 = Tag("work", "urgent")
        
        assert tag1.compare(tag2, soft=False)
        assert tag1.compare(tag2, soft=True)
    
    def test_compare_same_name_different_value(self):
        """Test comparing tags with same name but different values."""
        tag1 = Tag("priority", "high")
        tag2 = Tag("priority", "low")
        
        assert not tag1.compare(tag2, soft=False)
        assert tag1.compare(tag2, soft=True)
    
    def test_compare_different_name_same_value(self):
        """Test comparing tags with different names but same values."""
        tag1 = Tag("status", "done")
        tag2 = Tag("state", "done")
        
        assert not tag1.compare(tag2, soft=False)
        assert not tag1.compare(tag2, soft=True)
    
    def test_compare_one_with_value_one_without(self):
        """Test comparing tag with value against tag without value."""
        tag1 = Tag("work")
        tag2 = Tag("work", "urgent")
        
        assert not tag1.compare(tag2, soft=False)
        assert tag1.compare(tag2, soft=True)
    
    def test_compare_both_without_values(self):
        """Test comparing tags without values."""
        tag1 = Tag("work")
        tag2 = Tag("work")
        
        assert tag1.compare(tag2, soft=False)
        assert tag1.compare(tag2, soft=True)


class TestTagEquality:
    """Test Tag equality and hashing."""
    
    def test_equality_identical_tags(self):
        """Test equality of identical tags."""
        tag1 = Tag("work", "urgent")
        tag2 = Tag("work", "urgent")
        
        assert tag1 == tag2
    
    def test_equality_different_values(self):
        """Test equality of tags with different values."""
        tag1 = Tag("priority", "high")
        tag2 = Tag("priority", "low")
        
        assert tag1 != tag2
    
    def test_equality_one_with_value_one_without(self):
        """Test equality when one tag has value and other doesn't."""
        tag1 = Tag("work")
        tag2 = Tag("work", "urgent")
        
        assert tag1 != tag2
    
    def test_equality_with_non_tag(self):
        """Test equality comparison with non-Tag objects."""
        tag = Tag("work")
        
        assert tag != "work"
        assert tag != 42
        assert tag != None
    
    def test_hash_identical_tags(self):
        """Test that identical tags have the same hash."""
        tag1 = Tag("work", "urgent")
        tag2 = Tag("work", "urgent")
        
        assert hash(tag1) == hash(tag2)
    
    def test_hash_different_tags(self):
        """Test that different tags have different hashes."""
        tag1 = Tag("work", "urgent")
        tag2 = Tag("work", "normal")
        
        assert hash(tag1) != hash(tag2)
    
    def test_hash_usable_in_set(self):
        """Test that tags can be used in sets and as dict keys."""
        tag1 = Tag("work")
        tag2 = Tag("work", "urgent")
        tag3 = Tag("work")  # Same as tag1
        
        tag_set = {tag1, tag2, tag3}
        assert len(tag_set) == 2  # tag1 and tag3 are the same
        
        tag_dict = {tag1: "value1", tag2: "value2"}
        assert len(tag_dict) == 2


class TestTagUtilities:
    """Test Tag utility methods."""
    
    def test_tags_to_string_empty_list(self):
        """Test converting empty tag list to string."""
        result = Tag.tags_to_string([])
        
        assert result == ""
    
    def test_tags_to_string_single_tag(self):
        """Test converting single tag to string."""
        tags = [Tag("work")]
        result = Tag.tags_to_string(tags)
        
        assert result == "#work"
    
    def test_tags_to_string_multiple_tags(self):
        """Test converting multiple tags to string."""
        tags = [Tag("work"), Tag("priority", "high"), Tag("project", "website")]
        result = Tag.tags_to_string(tags)
        
        assert result == "#work #priority=high #project=website"
    
    def test_tags_to_string_with_special_characters(self):
        """Test converting tags with special characters to string."""
        tags = [Tag("project-name", "my_project"), Tag("status")]
        result = Tag.tags_to_string(tags)
        
        assert result == "#project-name=my_project #status"


class TestTagEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_tag_with_empty_name(self):
        """Test creating tag with empty name."""
        tag = Tag("", "value")
        
        assert tag.name == ""
        assert tag.value == "value"
        assert str(tag) == "#=value"
    
    def test_tag_with_none_value_explicit(self):
        """Test creating tag with explicitly None value."""
        tag = Tag("work", None)
        
        assert tag.name == "work"
        assert tag.value is None
        assert str(tag) == "#work"
    
    def test_from_line_malformed_tags(self):
        """Test parsing malformed tags (should be handled gracefully)."""
        # These should not match the regex pattern
        tags = Tag.from_line("Task with # and #= and #123invalid")
        
        # Only #123invalid should be parsed (if it matches the pattern)
        # The exact behavior depends on the regex pattern
        assert isinstance(tags, list)
    
    def test_from_line_tags_at_start_and_end(self):
        """Test parsing tags at the beginning and end of lines."""
        tags = Tag.from_line("#start some text #end")
        
        assert len(tags) == 2
        assert tags[0].name == "start"
        assert tags[1].name == "end"
    
    def test_compare_with_none_values(self):
        """Test comparing tags where one or both have None values."""
        tag1 = Tag("work", None)
        tag2 = Tag("work", None)
        tag3 = Tag("work", "urgent")
        
        assert tag1.compare(tag2, soft=False)
        assert tag1.compare(tag2, soft=True)
        assert not tag1.compare(tag3, soft=False)
        assert tag1.compare(tag3, soft=True)