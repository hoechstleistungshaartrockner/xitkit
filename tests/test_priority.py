"""
Tests for Priority class
========================
Tests the Priority class functionality according to syntax guide requirements.
"""

import pytest
from xitkit.priority import Priority


class TestPriorityBasics:
    """Test basic Priority class functionality."""
    
    def test_default_priority(self):
        """Test default priority creation."""
        priority = Priority()
        assert priority.level == 0
        assert priority.leading_dots == 0
        assert priority.trailing_dots == 0
        assert priority.is_empty
        assert str(priority) == ""
        assert priority.indicator == ""

    def test_simple_priority_creation(self):
        """Test creating priority with different levels."""
        p1 = Priority(level=1)
        assert p1.level == 1
        assert str(p1) == "!"
        assert not p1.is_empty
        
        p3 = Priority(level=3)
        assert p3.level == 3
        assert str(p3) == "!!!"
        
    def test_priority_with_leading_dots(self):
        """Test priority with dots before exclamation marks."""
        p = Priority(level=2, leading_dots=3)
        assert str(p) == "...!!"
        assert p.level == 2
        assert p.leading_dots == 3
        assert p.trailing_dots == 0

    def test_priority_with_trailing_dots(self):
        """Test priority with dots after exclamation marks."""
        p = Priority(level=1, trailing_dots=2)
        assert str(p) == "!.."
        assert p.level == 1
        assert p.leading_dots == 0
        assert p.trailing_dots == 2


class TestPriorityFromLine:
    """Test parsing priority from text after checkbox."""
    
    def test_valid_simple_priorities(self):
        """Test parsing simple priorities."""
        p1 = Priority.from_line(" ! description")
        assert p1.level == 1
        assert p1.leading_dots == 0
        assert p1.trailing_dots == 0
        assert str(p1) == "!"
        
        p3 = Priority.from_line(" !!! description")
        assert p3.level == 3
        assert str(p3) == "!!!"

    def test_valid_priorities_with_leading_dots(self):
        """Test parsing priorities with dots before exclamation marks."""
        p = Priority.from_line(" ..! description")
        assert p.level == 1
        assert p.leading_dots == 2
        assert p.trailing_dots == 0
        assert str(p) == "..!"
        
        p2 = Priority.from_line(" ...!! description")
        assert p2.level == 2
        assert p2.leading_dots == 3
        assert str(p2) == "...!!"

    def test_valid_priorities_with_trailing_dots(self):
        """Test parsing priorities with dots after exclamation marks."""
        p = Priority.from_line(" !!. description")
        assert p.level == 2
        assert p.leading_dots == 0
        assert p.trailing_dots == 1
        assert str(p) == "!!."
        
        p2 = Priority.from_line(" !... description")
        assert p2.level == 1
        assert p2.trailing_dots == 3
        assert str(p2) == "!..."

    def test_priority_with_extra_spaces_in_description(self):
        """Test that extra spaces in description are preserved."""
        p = Priority.from_line(" !   description with spaces")
        assert p.level == 1
        assert str(p) == "!"
        
        p2 = Priority.from_line(" !!.   lots of spaces")
        assert p2.level == 2
        assert p2.trailing_dots == 1

    def test_invalid_mixed_dot_positions(self):
        """Test that dots on both sides are invalid."""
        # These should be invalid according to syntax guide
        assert Priority.from_line(" .!. description") is None
        assert Priority.from_line(" !.! description") is None
        assert Priority.from_line(" ..!.. description") is None

    def test_invalid_no_exclamation_marks(self):
        """Test that priority without exclamation marks is invalid."""
        assert Priority.from_line(" . description") is None
        assert Priority.from_line(" ... description") is None

    def test_invalid_no_leading_space(self):
        """Test that priority without leading space is invalid."""
        assert Priority.from_line("! description") is None
        assert Priority.from_line("!! description") is None

    def test_invalid_no_description_separator(self):
        """Test that priority without space separator is invalid."""
        assert Priority.from_line(" !description") is None
        assert Priority.from_line(" !!description") is None

    def test_invalid_extra_leading_spaces(self):
        """Test that extra leading spaces make priority invalid."""
        assert Priority.from_line("  ! description") is None
        assert Priority.from_line("    ! description") is None

    def test_no_priority_found(self):
        """Test lines without priority."""
        assert Priority.from_line(" description") is None
        assert Priority.from_line(" regular text") is None
        assert Priority.from_line("") is None


class TestPriorityFromCheckboxLine:
    """Test parsing priority from complete checkbox lines."""
    
    def test_valid_checkbox_lines_with_priority(self):
        """Test parsing from complete checkbox lines."""
        p = Priority.from_checkbox_line("[ ] ! Do this")
        assert p.level == 1
        assert str(p) == "!"
        
        p2 = Priority.from_checkbox_line("[x] !!! This is done")
        assert p2.level == 3
        assert str(p2) == "!!!"
        
        p3 = Priority.from_checkbox_line("[@] ..! Ongoing task")
        assert p3.level == 1
        assert p3.leading_dots == 2
        assert str(p3) == "..!"

    def test_checkbox_lines_without_priority(self):
        """Test checkbox lines without priority."""
        assert Priority.from_checkbox_line("[ ] Do this") is None
        assert Priority.from_checkbox_line("[x] Completed task") is None

    def test_invalid_checkbox_lines(self):
        """Test invalid checkbox formats."""
        assert Priority.from_checkbox_line("! Not a checkbox") is None
        assert Priority.from_checkbox_line("Invalid line") is None
        assert Priority.from_checkbox_line("") is None


class TestPriorityComparison:
    """Test priority comparison and equality."""
    
    def test_priority_equality(self):
        """Test priority equality comparison."""
        p1 = Priority(level=2, leading_dots=1)
        p2 = Priority(level=2, leading_dots=1)
        p3 = Priority(level=2, trailing_dots=1)
        
        assert p1 == p2
        assert p1 != p3
        assert p1 != "not a priority"

    def test_priority_less_than(self):
        """Test priority level comparison."""
        p1 = Priority(level=1)
        p2 = Priority(level=2)
        p3 = Priority(level=3)
        
        assert p1 < p2
        assert p2 < p3
        assert not p2 < p1
        assert not p3 < p2

    def test_priority_comparison_with_dots(self):
        """Test that dots don't affect level comparison."""
        p1 = Priority(level=2, leading_dots=5)
        p2 = Priority(level=2, trailing_dots=10)
        p3 = Priority(level=3)
        
        assert not p1 < p2  # Same level
        assert not p2 < p1  # Same level
        assert p1 < p3      # Lower level
        assert p2 < p3      # Lower level

    def test_priority_hash(self):
        """Test priority hashing for use in sets/dicts."""
        p1 = Priority(level=2, leading_dots=1)
        p2 = Priority(level=2, leading_dots=1)
        p3 = Priority(level=2, trailing_dots=1)
        
        assert hash(p1) == hash(p2)
        assert hash(p1) != hash(p3)
        
        # Test in set
        priority_set = {p1, p2, p3}
        assert len(priority_set) == 2  # p1 and p2 are same


class TestPriorityEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_very_high_priority_levels(self):
        """Test high priority levels."""
        p = Priority.from_line(" !!!!!!!!!! description")
        assert p.level == 10
        assert str(p) == "!!!!!!!!!!"

    def test_many_dots(self):
        """Test priorities with many dots."""
        p1 = Priority.from_line(" ..........! description")
        assert p1.leading_dots == 10
        assert p1.level == 1
        
        p2 = Priority.from_line(" !.......... description")
        assert p2.trailing_dots == 10
        assert p2.level == 1

    def test_mixed_valid_combinations(self):
        """Test various valid combinations."""
        test_cases = [
            (" ! description", 1, 0, 0),
            (" !! description", 2, 0, 0),
            (" .! description", 1, 1, 0),
            (" !. description", 1, 0, 1),
            (" ...!!! description", 3, 3, 0),
            (" !!!... description", 3, 0, 3),
        ]
        
        for line, expected_level, expected_leading, expected_trailing in test_cases:
            p = Priority.from_line(line)
            assert p is not None, f"Failed to parse: {line}"
            assert p.level == expected_level
            assert p.leading_dots == expected_leading
            assert p.trailing_dots == expected_trailing

    def test_string_representations(self):
        """Test string representation for various priorities."""
        test_cases = [
            (Priority(level=0), ""),
            (Priority(level=1), "!"),
            (Priority(level=3), "!!!"),
            (Priority(level=1, leading_dots=2), "..!"),
            (Priority(level=2, trailing_dots=1), "!!."),
            (Priority(level=5, leading_dots=3), "...!!!!!"),
        ]
        
        for priority, expected_str in test_cases:
            assert str(priority) == expected_str
            assert priority.indicator == expected_str


class TestPriorityProperties:
    """Test priority properties and utility methods."""
    
    def test_is_empty_property(self):
        """Test is_empty property."""
        assert Priority().is_empty
        assert Priority(level=0).is_empty
        assert not Priority(level=1).is_empty
        assert not Priority(level=1, leading_dots=5).is_empty

    def test_indicator_property(self):
        """Test indicator property (alias for __str__)."""
        p = Priority(level=2, leading_dots=1)
        assert p.indicator == str(p)
        assert p.indicator == ".!!"
