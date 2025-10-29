import pytest
from datetime import datetime
from xitkit.description import Description
from xitkit.tags import Tag
from xitkit.duedate import DueDate

class TestDescriptionBasics:

    def test_empty_initialization(self):
        desc = Description()
        assert desc.text == ""
        assert desc.tags == []

    def test_initialization_with_text(self):
        desc = Description("Initial text")
        assert desc.text == "Initial text"
        assert desc.tags == []

    def test_initialization_with_text_and_tags(self):
        desc = Description("Task with #work and #urgent tags")
        assert desc.text == "Task with #work and #urgent tags"
        assert len(desc.tags) == 2
        assert desc.tags[0] == Tag(name="work")
        assert desc.tags[1] == Tag(name="urgent")
    
    def test_initialization_with_priority(self):
        desc = Description("!! Important task")
        assert desc.text == "!! Important task"
        assert desc.priority.level == 2
        

    def test_set_text(self):
        desc = Description()
        desc.set_text("New task description")
        assert desc.text == "New task description"

    def test_set_text_overwrites_existing(self):
        desc = Description("Old text")
        desc.set_text("New task description")
        assert desc.text == "New task description"

    def test_set_text_with_tags(self):
        desc = Description()
        desc.set_text("Task with #priority=high")
        assert desc.text == "Task with #priority=high"
        assert len(desc.tags) == 1
        assert desc.tags[0] == Tag(name="priority", value="high")

    def test_set_empty_text(self):
        desc = Description("Some text with #tag")
        desc.set_text("")
        assert desc.text == ""
        assert len(desc.tags) == 0

    def test_set_text_none(self):
        desc = Description("Some text")
        desc.set_text(None)
        assert desc.text == ""

    def test_set_text_whitespace_only(self):
        desc = Description()
        desc.set_text("   ")
        assert desc.text == "   "
        assert desc.tags == []
    

class TestDescriptionTagIdentification:

    def test_tag_identification(self):
        desc = Description("This is a task with a #tag")
        tag = Tag(name="tag")
        assert desc.text == "This is a task with a #tag"
        assert len(desc.tags) == 1
        assert desc.tags[0] == tag

    def test_tag_identification_multiple(self):
        desc = Description("Task with #work #urgent #project=website")
        assert len(desc.tags) == 3
        assert desc.tags[0] == Tag(name="work")
        assert desc.tags[1] == Tag(name="urgent")
        assert desc.tags[2] == Tag(name="project", value="website")

    def test_tag_identification_with_values(self):
        desc = Description("Task #priority=high #status=done")
        assert len(desc.tags) == 2
        assert desc.tags[0] == Tag(name="priority", value="high")
        assert desc.tags[1] == Tag(name="status", value="done")

    def test_tag_identification_quoted_values(self):
        desc = Description('Task #title="My Task" #note=\'important stuff\'')
        assert len(desc.tags) == 2
        assert desc.tags[0] == Tag(name="title", value="My Task")
        assert desc.tags[1] == Tag(name="note", value="important stuff")

    def test_tag_identification_empty_values(self):
        desc = Description('Task #status= #type=""')
        assert len(desc.tags) == 2
        assert desc.tags[0] == Tag(name="status", value="")
        assert desc.tags[1] == Tag(name="type", value="")

    def test_tag_identification_unicode(self):
        desc = Description("Task #项目=网站 #språk=norsk")
        assert len(desc.tags) == 2
        assert desc.tags[0] == Tag(name="项目", value="网站")
        assert desc.tags[1] == Tag(name="språk", value="norsk")

    def test_tag_identification_at_start_and_end(self):
        desc = Description("#start some text #end")
        assert len(desc.tags) == 2
        assert desc.tags[0] == Tag(name="start")
        assert desc.tags[1] == Tag(name="end")

    def test_tag_identification_no_tags(self):
        desc = Description("Task with no tags")
        assert len(desc.tags) == 0

class TestDescriptionAddingTags:
    """Test adding, removing, and managing tags in Description."""

    def test_add_tag(self):
        desc = Description()
        tag = Tag(name="priority", value="high")
        desc.add_tag(tag)
        assert len(desc.tags) == 1
        assert desc.tags[0] == tag
        assert desc.text == "#priority=high"

    def test_add_tag_to_existing_text(self):
        desc = Description("Existing task")
        tag = Tag(name="urgent")
        desc.add_tag(tag)
        assert len(desc.tags) == 1
        assert desc.tags[0] == tag
        assert desc.text == "Existing task #urgent"

    def test_add_tag_duplicate(self):
        desc = Description()
        tag = Tag(name="priority", value="high")
        desc.add_tag(tag)
        desc.add_tag(tag)  # Add same tag again
        assert len(desc.tags) == 1  # Should not duplicate
        assert desc.tags[0] == tag

    def test_add_tag_multiple(self):
        desc = Description()
        tag1 = Tag(name="work")
        tag2 = Tag(name="urgent")
        desc.add_tag(tag1)
        desc.add_tag(tag2)
        assert len(desc.tags) == 2
        assert desc.tags[0] == tag1
        assert desc.tags[1] == tag2
        assert desc.text == "#work #urgent"

    def test_add_tag_with_existing_tags(self):
        desc = Description("Task with #existing")
        new_tag = Tag(name="new")
        desc.add_tag(new_tag)
        assert len(desc.tags) == 2
        assert desc.tags[0] == Tag(name="existing")
        assert desc.tags[1] == new_tag
        assert desc.text == "Task with #existing #new"

    def test_add_tag_no_value(self):
        desc = Description()
        tag = Tag(name="simple")
        desc.add_tag(tag)
        assert desc.text == "#simple"

    def test_add_tag_empty_value(self):
        desc = Description()
        tag = Tag(name="status", value="")
        desc.add_tag(tag)
        assert desc.text == "#status="

class TestDescriptionRemovingTags:
    """Test removing tags from Description."""

    def test_remove_tag(self):
        desc = Description()
        tag = Tag(name="priority", value="high")
        desc.add_tag(tag)
        desc.remove_tag(tag)
        assert len(desc.tags) == 0
        assert desc.text == ""
    
    def test_remove_tag_with_text(self):
        desc = Description("Task with #priority=high tag")
        tag = Tag(name="priority", value="high")
        desc.remove_tag(tag)
        assert len(desc.tags) == 0
        assert desc.text == "Task with tag"

    def test_remove_tag_from_middle(self):
        desc = Description("Start #first middle #second end")
        tag = Tag(name="first")
        desc.remove_tag(tag)
        assert len(desc.tags) == 1
        assert desc.tags[0] == Tag(name="second")
        assert desc.text == "Start middle #second end"

    def test_remove_tag_from_start(self):
        desc = Description("#first text #second")
        tag = Tag(name="first")
        desc.remove_tag(tag)
        assert len(desc.tags) == 1
        assert desc.text == "text #second"

    def test_remove_tag_from_end(self):
        desc = Description("text #first #second")
        tag = Tag(name="second")
        desc.remove_tag(tag)
        assert len(desc.tags) == 1
        assert desc.text == "text #first"

    def test_remove_tag_only_tag(self):
        desc = Description("#only")
        tag = Tag(name="only")
        desc.remove_tag(tag)
        assert len(desc.tags) == 0
        assert desc.text == ""

    def test_remove_tag_multiple_occurrences(self):
        desc = Description("#tag text #tag more #tag")
        tag = Tag(name="tag")
        desc.remove_tag(tag)
        assert len(desc.tags) == 0
        assert desc.text == "text more"  # All occurrences removed

    def test_remove_tag_nonexistent(self):
        desc = Description("Task with #existing")
        tag = Tag(name="nonexistent")
        desc.remove_tag(tag)
        assert len(desc.tags) == 1  # Existing tag remains
        assert desc.text == "Task with #existing"

    def test_remove_tag_by_name_only(self):
        desc = Description("Task with #priority=high")
        tag = Tag(name="priority")  # Different value
        desc.remove_tag(tag, soft=True)
        assert len(desc.tags) == 0
        assert desc.text == "Task with priority=high"

    def test_remove_tag_exact_match_required(self):
        desc = Description("Task with #priority=high")
        tag = Tag(name="priority", value="low")  # Different value
        desc.remove_tag(tag, soft=False)
        assert len(desc.tags) == 1  # Tag not removed because value doesn't match
        assert desc.text == "Task with #priority=high"

    def test_get_tags(self):
        desc = Description()
        tag1 = Tag(name="priority", value="high")
        tag2 = Tag(name="due", value="tomorrow")
        desc.add_tag(tag1)
        desc.add_tag(tag2)
        tags = desc.get_tags()
        assert tags == [tag1, tag2]

    def test_get_tags_empty(self):
        desc = Description()
        tags = desc.get_tags()
        assert tags == []

    def test_get_tags_from_text(self):
        desc = Description("Task with #work #urgent=high")
        tags = desc.get_tags()
        assert len(tags) == 2
        assert tags[0] == Tag(name="work")
        assert tags[1] == Tag(name="urgent", value="high")

    def test_get_tags_returns_copy(self):
        desc = Description("Task with #work")
        tags = desc.get_tags()
        tags.append(Tag(name="fake"))
        assert len(desc.tags) == 1  # Original should be unchanged

    def test_clear_tags(self):
        desc = Description()
        tag = Tag(name="priority", value="high")
        desc.add_tag(tag)
        desc.clear_tags()
        assert len(desc.tags) == 0

    def test_clear_tags_from_text(self):
        desc = Description("Task with #work #urgent")
        desc.clear_tags()
        assert len(desc.tags) == 0
        assert desc.text == "Task with"  # Tags removed from text

    def test_clear_tags_empty(self):
        desc = Description("Task without tags")
        desc.clear_tags()
        assert len(desc.tags) == 0
        assert desc.text == "Task without tags"  # Text unchanged

    def test_has_tag(self):
        desc = Description()
        assert not desc.has_tag()
        tag = Tag(name="priority", value="high")
        desc.add_tag(tag)
        assert desc.has_tag()

    def test_has_tag_from_text(self):
        desc = Description("Task with #work")
        assert desc.has_tag()

    def test_has_tag_empty_text(self):
        desc = Description("")
        assert not desc.has_tag()

    def test_has_tag_text_no_tags(self):
        desc = Description("Task without tags")
        assert not desc.has_tag()

    def test_has_specific_tag(self):
        desc = Description("Task with #work #urgent")
        work_tag = Tag(name="work")
        urgent_tag = Tag(name="urgent")
        missing_tag = Tag(name="missing")
        
        assert desc.has_specific_tag(work_tag)
        assert desc.has_specific_tag(urgent_tag)
        assert not desc.has_specific_tag(missing_tag)

    def test_has_specific_tag_soft_comparison(self):
        desc = Description("Task with #priority=high")
        priority_tag_exact = Tag(name="priority", value="high")
        priority_tag_different = Tag(name="priority", value="low")
        priority_tag_no_value = Tag(name="priority")
        
        assert desc.has_specific_tag(priority_tag_exact)
        assert not desc.has_specific_tag(priority_tag_different)
        assert desc.has_specific_tag(priority_tag_no_value, soft=True)
        assert not desc.has_specific_tag(priority_tag_no_value, soft=False)

    def test_soft_tag_removal(self):
        desc = Description("Task with #priority=high tag")
        tag = Tag(name="priority", value="high")
        desc.remove_tag(tag, soft=True)
        assert len(desc.tags) == 0
        assert desc.text == "Task with priority=high tag"

    def test_tag_removal_not_in_text(self):
        desc = Description("Task without the tag")
        tag = Tag(name="priority", value="high")
        desc.add_tag(tag)
        desc.remove_tag(tag)
        assert len(desc.tags) == 0
        assert desc.text == "Task without the tag"

    def test_tag_removal_not_in_text_soft(self):
        desc = Description("Task without the tag")
        tag = Tag(name="priority", value="high")
        desc.add_tag(tag)
        desc.remove_tag(tag, soft=True)
        assert len(desc.tags) == 0
        assert desc.text == "Task without the tag priority=high"

    def test_tag_removal_not_in_text2(self):
        desc = Description("Task with #priority=high")
        tag = Tag(name="due", value="tomorrow")
        desc.remove_tag(tag)
        assert len(desc.tags) == 1
        assert desc.text == "Task with #priority=high"

    def test_tag_removal_not_in_text2_soft(self):
        desc = Description("Task with #priority=high")
        tag = Tag(name="due", value="tomorrow")
        desc.remove_tag(tag, soft=True)
        assert len(desc.tags) == 1
        assert desc.text == "Task with #priority=high"


class TestDescriptionStringRepresentation:
    """Test string representation and conversion methods."""

    def test_str_method(self):
        desc = Description("Task description")
        assert str(desc) == "Task description"

    def test_str_method_with_tags(self):
        desc = Description("Task #work #urgent")
        assert str(desc) == "Task #work #urgent"

    def test_str_method_empty(self):
        desc = Description()
        assert str(desc) == ""

    def test_repr_method(self):
        desc = Description("Task #work")
        repr_str = repr(desc)
        assert "Description(" in repr_str
        assert "Task #work" in repr_str

    def test_to_display_format(self):
        desc = Description("Task with #work #priority=high")
        display = desc.to_display_format()
        assert display == "Task with #work #priority=high"

    def test_to_storage_format(self):
        desc = Description("Task with #work")
        storage = desc.to_storage_format()
        assert storage == "Task with #work"


class TestDescriptionEquality:
    """Test equality and comparison methods."""

    def test_equality_identical(self):
        desc1 = Description("Task #work")
        desc2 = Description("Task #work")
        assert desc1 == desc2

    def test_equality_different_text(self):
        desc1 = Description("Task A #work")
        desc2 = Description("Task B #work")
        assert desc1 != desc2

    def test_equality_different_tags(self):
        desc1 = Description("Task #work")
        desc2 = Description("Task #urgent")
        assert desc1 != desc2

    def test_equality_same_tags_different_order(self):
        desc1 = Description("Task #work #urgent")
        desc2 = Description("Task #urgent #work")
        assert desc1 != desc2
        # This depends on implementation - tags might be reordered
        # The test assumes tags maintain their order from parsing

    def test_equality_with_non_description(self):
        desc = Description("Task")
        assert desc != "Task"
        assert desc != 42
        assert desc != None

    def test_hash_consistency(self):
        desc1 = Description("Task #work")
        desc2 = Description("Task #work")
        assert hash(desc1) == hash(desc2)

    def test_hash_usable_in_set(self):
        desc1 = Description("Task #work")
        desc2 = Description("Task #urgent")
        desc3 = Description("Task #work")  # Same as desc1
        
        desc_set = {desc1, desc2, desc3}
        assert len(desc_set) == 2  # desc1 and desc3 are the same


class TestDescriptionEdgeCases:
    """Test edge cases and error conditions."""

    def test_very_long_text(self):
        long_text = "This is a very long task description " * 100 + " #tag"
        desc = Description(long_text)
        assert long_text in desc.text
        assert len(desc.tags) == 1
        assert desc.tags[0] == Tag(name="tag")

    def test_many_tags(self):
        tags_text = " ".join([f"#tag{i}" for i in range(100)])
        desc = Description(f"Task with {tags_text}")
        assert len(desc.tags) == 100
        assert all(desc.tags[i].name == f"tag{i}" for i in range(100))

    def test_malformed_tags(self):
        desc = Description("Task with # and #= and invalid#tag")
        # The exact behavior depends on regex pattern
        # This test checks that malformed tags don't crash

    def test_special_characters_in_text(self):
        desc = Description("Task with special chars: !@#$%^&*()[]{}|\\:;\"'<>,.?/")
        assert "special chars" in desc.text

    def test_unicode_text(self):
        desc = Description("Задача с #работа тегом 📋")
        assert "Задача" in desc.text
        assert len(desc.tags) == 1
        assert desc.tags[0] == Tag(name="работа")

    def test_newlines_in_text(self):
        desc = Description("Multi-line\ntask description\nwith #tag")
        assert "\n" in desc.text
        assert len(desc.tags) == 1

    def test_tabs_and_spaces(self):
        desc = Description("\t  Task with    spaces   #tag  \t")
        assert desc.text == "\t  Task with    spaces   #tag  \t"
        assert len(desc.tags) == 1

    def test_empty_tag_name(self):
        # This tests behavior with malformed tags
        desc = Description("Task with # empty tag")
        # Behavior depends on regex pattern

    def test_tag_with_numbers_only(self):
        desc = Description("Task with #123456")
        assert len(desc.tags) == 1
        assert desc.tags[0] == Tag(name="123456")

    def test_tag_case_sensitivity(self):
        desc = Description("Task with #Work #WORK #work")
        # All should be treated as different tags
        assert len(desc.tags) == 3
        tag_names = [tag.name for tag in desc.tags]
        assert "Work" in tag_names
        assert "WORK" in tag_names
        assert "work" in tag_names

    def test_adjacent_tags(self):
        desc = Description("Task #tag1#tag2 #tag3")
        # Test how adjacent tags without spaces are handled
        # Behavior depends on regex pattern

    def test_tag_in_quoted_text(self):
        desc = Description('Task with "quoted #tag" text')
        # Test if tags inside quotes are still parsed
        # Behavior depends on implementation

    def test_escaped_hash(self):
        desc = Description("Task with \\#escaped hash")
        # Test if escaped hashes are treated as regular text
        # Behavior depends on implementation


class TestDescriptionTagFiltering:
    """Test tag filtering and search functionality."""

    def test_get_tags_by_name(self):
        desc = Description("Task #work #work=urgent #personal")
        work_tags = desc.get_tags_by_name("work")
        assert len(work_tags) == 2
        assert work_tags[0] == Tag(name="work")
        assert work_tags[1] == Tag(name="work", value="urgent")

    def test_get_tags_by_name_not_found(self):
        desc = Description("Task #work")
        missing_tags = desc.get_tags_by_name("missing")
        assert len(missing_tags) == 0

    def test_get_tags_with_values(self):
        desc = Description("Task #work #priority=high #status=")
        valued_tags = desc.get_tags_with_values()
        assert len(valued_tags) == 2
        assert Tag(name="priority", value="high") in valued_tags
        assert Tag(name="status", value="") in valued_tags

    def test_get_tags_without_values(self):
        desc = Description("Task #work #priority=high #urgent")
        simple_tags = desc.get_tags_without_values()
        assert len(simple_tags) == 2
        assert Tag(name="work") in simple_tags
        assert Tag(name="urgent") in simple_tags

    def test_filter_tags_by_pattern(self):
        desc = Description("Task #work-item #work-related #personal")
        work_tags = desc.filter_tags_by_pattern("work*")
        assert len(work_tags) == 2
        # Exact implementation depends on pattern matching

    def test_replace_tag(self):
        desc = Description("Task with #old-tag")
        old_tag = Tag(name="old-tag")
        new_tag = Tag(name="new-tag", value="updated")
        desc.replace_tag(old_tag, new_tag)
        assert len(desc.tags) == 1
        assert desc.tags[0] == new_tag
        assert "#new-tag=updated" in desc.text
        assert "#old-tag" not in desc.text

    def test_replace_tag_not_found(self):
        desc = Description("Task with #existing")
        missing_tag = Tag(name="missing")
        new_tag = Tag(name="replacement")
        desc.replace_tag(missing_tag, new_tag)
        # Should not change anything
        assert len(desc.tags) == 1
        assert desc.tags[0] == Tag(name="existing")


class TestDescriptionTextManipulation:
    """Test text manipulation methods."""

    def test_extract_text_without_tags(self):
        desc = Description("Task with #work and #priority=high tags")
        clean_text = desc.get_text_without_tags()
        assert clean_text == "Task with and tags"
        assert "#work" not in clean_text
        assert "#priority=high" not in clean_text

    def test_extract_text_without_tags_empty(self):
        desc = Description("#only #tags")
        clean_text = desc.get_text_without_tags()
        assert clean_text.strip() == ""

    def test_extract_text_without_tags_no_tags(self):
        desc = Description("Task without tags")
        clean_text = desc.get_text_without_tags()
        assert clean_text == "Task without tags"

    def test_insert_text_at_position(self):
        desc = Description("Task description")
        desc.insert_text_at_position(4, " new")
        assert desc.text == "Task new description"

    def test_append_text(self):
        desc = Description("Task")
        desc.append_text(" additional info")
        assert desc.text == "Task additional info"

    def test_prepend_text(self):
        desc = Description("task")
        desc.prepend_text("Important ")
        assert desc.text == "Important task"

    def test_replace_text_segment(self):
        desc = Description("Old task description")
        desc.replace_text_segment("Old", "New")
        assert desc.text == "New task description"

    def test_normalize_whitespace(self):
        desc = Description("Task   with    extra    spaces")
        desc.normalize_whitespace()
        assert desc.text == "Task with extra spaces"

    def test_normalize_whitespace_with_tags(self):
        desc = Description("Task   #tag1    #tag2   description")
        desc.normalize_whitespace()
        # Should normalize spaces while preserving tags
        assert "   " not in desc.text
        assert "#tag1" in desc.text
        assert "#tag2" in desc.text


class TestDescriptionDueDate:
    """Test due date functionality in Description."""
    
    def test_description_with_due_date_initialization(self):
        """Test creating description with due date in text."""
        desc = Description("Task with due date -> 2025-12-31")
        assert desc.text == "Task with due date -> 2025-12-31"
        assert desc.has_due_date()
        assert desc.due_date is not None
        assert desc.due_date.date_part == "2025-12-31"
    
    def test_description_without_due_date_initialization(self):
        """Test creating description without due date."""
        desc = Description("Task without due date")
        assert desc.text == "Task without due date"
        assert not desc.has_due_date()
        assert desc.due_date is None
    
    def test_get_due_date(self):
        """Test getting due date from description."""
        desc = Description("Task -> 2025-06-15")
        due_date = desc.get_due_date()
        assert due_date is not None
        assert due_date.date_part == "2025-06-15"
        
        desc2 = Description("Task without date")
        assert desc2.get_due_date() is None
    
    def test_set_due_date_to_empty_description(self):
        """Test setting due date on empty description."""
        desc = Description()
        due_date = DueDate.from_string("2025-12-31")
        desc.set_due_date(due_date)
        
        assert desc.has_due_date()
        assert desc.due_date == due_date
        assert desc.text == "-> 2025-12-31"
    
    def test_set_due_date_to_existing_description(self):
        """Test setting due date on description with existing text."""
        desc = Description("Important task")
        due_date = DueDate.from_string("2025-12-31")
        desc.set_due_date(due_date)
        
        assert desc.has_due_date()
        assert desc.due_date == due_date
        assert desc.text == "Important task -> 2025-12-31"
    
    def test_replace_existing_due_date(self):
        """Test replacing an existing due date."""
        desc = Description("Task -> 2025-06-15")
        assert desc.has_due_date()
        
        new_due_date = DueDate.from_string("2025-12-31")
        desc.set_due_date(new_due_date)
        
        assert desc.due_date == new_due_date
        assert "-> 2025-06-15" not in desc.text
        assert "-> 2025-12-31" in desc.text
    
    def test_clear_due_date(self):
        """Test clearing due date from description."""
        desc = Description("Task -> 2025-06-15")
        assert desc.has_due_date()
        
        desc.clear_due_date()
        
        assert not desc.has_due_date()
        assert desc.due_date is None
        assert "-> 2025-06-15" not in desc.text
        assert desc.text == "Task"
    
    def test_set_due_date_none(self):
        """Test setting due date to None."""
        desc = Description("Task -> 2025-06-15")
        desc.set_due_date(None)
        
        assert not desc.has_due_date()
        assert desc.due_date is None
        assert "-> 2025-06-15" not in desc.text
    
    def test_add_due_date_from_string_valid(self):
        """Test adding due date from string."""
        desc = Description("Important task")
        success = desc.add_due_date_from_string("2025-12-31")
        
        assert success
        assert desc.has_due_date()
        assert desc.due_date.date_part == "2025-12-31"
        assert "-> 2025-12-31" in desc.text
    
    def test_add_due_date_from_string_invalid(self):
        """Test adding invalid due date from string."""
        desc = Description("Task")
        success = desc.add_due_date_from_string("invalid-date")
        
        assert not success
        assert not desc.has_due_date()
        assert desc.due_date is None
        assert desc.text == "Task"
    
    def test_set_text_updates_due_date(self):
        """Test that setting new text updates due date."""
        desc = Description("Old task -> 2025-06-15")
        assert desc.has_due_date()
        
        desc.set_text("New task -> 2025-12-31")
        
        assert desc.has_due_date()
        assert desc.due_date.date_part == "2025-12-31"
    
    def test_set_text_removes_due_date(self):
        """Test that setting text without due date removes it."""
        desc = Description("Task -> 2025-06-15")
        assert desc.has_due_date()
        
        desc.set_text("Task without date")
        
        assert not desc.has_due_date()
        assert desc.due_date is None


class TestDescriptionDueDateFormats:
    """Test various due date formats in Description."""
    
    def test_various_date_formats(self):
        """Test description with various due date formats."""
        test_cases = [
            ("Task -> 2025-12-31", "2025-12-31"),
            ("Task -> 2025-12", "2025-12"),  
            ("Task -> 2025", "2025"),
            ("Task -> 2025-W01", "2025-W01"),
            ("Task -> 2025-Q1", "2025-Q1"),
            ("Task -> 2025/12/31", "2025/12/31"),
        ]
        
        for text, expected_date_part in test_cases:
            desc = Description(text)
            assert desc.has_due_date(), f"Failed for: {text}"
            assert desc.due_date.date_part == expected_date_part
    
    def test_due_date_with_tags(self):
        """Test description with both tags and due date."""
        desc = Description("Task #work #priority=high -> 2025-12-31")
        
        assert len(desc.tags) == 2
        assert desc.has_due_date()
        assert desc.due_date.date_part == "2025-12-31"
        
        # Check that both tags and due date are parsed correctly
        assert any(tag.name == "work" for tag in desc.tags)
        assert any(tag.name == "priority" and tag.value == "high" for tag in desc.tags)
    
    def test_due_date_in_middle_of_text(self):
        """Test due date in middle of description."""
        desc = Description("Complete project -> 2025-12-31 before holidays")
        
        assert desc.has_due_date()
        assert desc.due_date.date_part == "2025-12-31"
        assert "before holidays" in desc.text
    
    def test_multiple_due_dates_only_first_recognized(self):
        """Test that only first due date is recognized."""
        desc = Description("Task -> 2025-06-15 and also -> 2025-12-31")
        
        assert desc.has_due_date()
        # Should only capture the first one
        assert desc.due_date.date_part == "2025-06-15"


class TestDescriptionDueDateTextManipulation:
    """Test text manipulation with due dates."""
    
    def test_get_text_without_tags_and_dates(self):
        """Test extracting clean text without tags or dates."""
        desc = Description("Important task #work -> 2025-12-31 #urgent")
        clean_text = desc.get_text_without_tags_and_dates()
        
        assert clean_text == "Important task"
        assert "#work" not in clean_text
        assert "#urgent" not in clean_text
        assert "-> 2025-12-31" not in clean_text
    
    def test_get_text_without_tags_and_dates_empty_result(self):
        """Test clean text extraction when only tags and dates remain."""
        desc = Description("#tag1 -> 2025-12-31 #tag2")
        clean_text = desc.get_text_without_tags_and_dates()
        
        assert clean_text == ""
    
    def test_get_text_without_tags_preserves_date(self):
        """Test that get_text_without_tags preserves due date."""
        desc = Description("Task #work -> 2025-12-31")
        text_without_tags = desc.get_text_without_tags()
        
        assert "#work" not in text_without_tags
        assert "-> 2025-12-31" in text_without_tags
        assert text_without_tags.strip() == "Task -> 2025-12-31"


class TestDescriptionDueDateEquality:
    """Test equality and comparison with due dates."""
    
    def test_equality_with_same_due_date(self):
        """Test equality of descriptions with same due date."""
        desc1 = Description("Task -> 2025-12-31")
        desc2 = Description("Task -> 2025-12-31")
        
        assert desc1 == desc2
    
    def test_equality_with_different_due_date(self):
        """Test inequality of descriptions with different due dates."""
        desc1 = Description("Task -> 2025-12-31")
        desc2 = Description("Task -> 2025-06-15")
        
        assert desc1 != desc2
    
    def test_equality_one_with_due_date_one_without(self):
        """Test inequality when one has due date and other doesn't."""
        desc1 = Description("Task -> 2025-12-31")
        desc2 = Description("Task")
        
        assert desc1 != desc2
    
    def test_hash_with_due_date(self):
        """Test hashing with due dates."""
        desc1 = Description("Task -> 2025-12-31")
        desc2 = Description("Task -> 2025-12-31")
        desc3 = Description("Task -> 2025-06-15")
        
        assert hash(desc1) == hash(desc2)
        assert hash(desc1) != hash(desc3)
        
        # Test in set
        desc_set = {desc1, desc2, desc3}
        assert len(desc_set) == 2


class TestDescriptionDueDateEdgeCases:
    """Test edge cases with due dates."""
    
    def test_invalid_due_date_in_text(self):
        """Test description with invalid due date pattern."""
        desc = Description("Task -> invalid-date")
        
        assert not desc.has_due_date()
        assert desc.due_date is None
    
    def test_due_date_with_continuation_lines(self):
        """Test due date on continuation lines.""" 
        desc = Description("Task with\n    -> 2025-12-31")
        
        # This may or may not work depending on how DueDate.from_line handles newlines
        # The test documents the expected behavior
    
    def test_set_invalid_due_date(self):
        """Test setting an invalid due date object."""
        desc = Description("Task")
        invalid_due_date = DueDate(expression="-> invalid")
        
        desc.set_due_date(invalid_due_date)
        
        # Should still set it even if invalid
        assert desc.due_date == invalid_due_date
        assert not desc.has_due_date()  # has_due_date checks is_valid
    
    def test_copy_with_due_date(self):
        """Test copying description with due date."""
        desc = Description("Task #work -> 2025-12-31")
        copied = desc.copy()
        
        assert copied == desc
        assert copied.due_date == desc.due_date
        assert copied.due_date is not desc.due_date  # Different objects
        assert copied.tags == desc.tags
    
    def test_repr_with_due_date(self):
        """Test string representation with due date."""
        desc = Description("Task -> 2025-12-31")
        repr_str = repr(desc)
        
        assert "Description(" in repr_str
        assert "Task -> 2025-12-31" in repr_str
        assert "due_date=" in repr_str
    
    def test_due_date_spacing_removal(self):
        """Test proper spacing when removing due dates."""
        test_cases = [
            ("Task -> 2025-12-31", "Task"),
            ("Task -> 2025-12-31 extra", "Task extra"),  
            ("Start -> 2025-12-31 end", "Start end"),
        ]
        
        for original, expected in test_cases:
            desc = Description(original)
            desc.clear_due_date()
            assert desc.text == expected, f"Expected '{expected}' but got '{desc.text}' for '{original}'"

    