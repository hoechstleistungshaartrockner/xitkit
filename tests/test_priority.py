"""
Tests for Priority class
========================
Tests the Priority class functionality according to syntax guide requirements.
"""

import pytest
from xitkit.priority import Priority


class TestPriorityInitialization:
    """Test Priority class initialization and basic properties."""

    @pytest.mark.parametrize(
        "level, leading_dots, trailing_dots, expected_str",
        [(0, 0, 0, ""),
         (1, 0, 0, "!"),
         (3, 0, 0, "!!!"),
         (2, 2, 0, "..!!"),
         (1, 0, 3, "!..."),
        ]
    )
    def test_priority_initialization(self, level, leading_dots, trailing_dots, expected_str):
        """Test initialization of Priority with various parameters."""
        priority = Priority(level=level, leading_dots=leading_dots, trailing_dots=trailing_dots)
        assert priority.level == level
        assert priority.leading_dots == leading_dots
        assert priority.trailing_dots == trailing_dots
        assert str(priority) == expected_str
    
    @pytest.mark.parametrize(
        "level, leading_dots, trailing_dots",
        [(0, 1, 1),
         (-1, 0, 0),
         (1, 3, 3),
        ]
    )
    def test_invalid_priority_instantiation(self, level, leading_dots, trailing_dots):
        """Test that invalid priority combinations raise errors."""
        with pytest.raises(ValueError):
            Priority(level=level, leading_dots=leading_dots, trailing_dots=trailing_dots)

class TestPriorityRegexDetection:
    """Test regex pattern for priority detection."""
    
    @pytest.mark.parametrize(
        "line, level, leading_dots, trailing_dots",
        [
            (None, 0, 0, 0),
            ("", 0, 0, 0),
            ("...", 0, 3, 0),
            ("!!!", 3, 0, 0),
            (".!!", 2, 1, 0),
            ("!!.", 2, 0, 1),
            ("..!!!..", 0, 0, 0),  # invalid: leading and trailing dots
            ("!.!", 0, 0, 0),      # invalid: dots in the middle
            # with descriptions and leading space
            (" description", 0, 0, 0),
            (" ... description", 0, 3, 0),
            (" !!! description", 3, 0, 0),
            (" .!! description", 2, 1, 0),
            (" !!. description", 2, 0, 1),
            (" ..!!!.. description", 0, 0, 0),  # invalid
            (" !.! description", 0, 0, 0),      # invalid
            # with description but no space separator (invalid)
            ("description", 0, 0, 0),
            ("...description", 0, 0, 0),
            ("!!!description", 0, 0, 0),
            (".!!description", 0, 0, 0),
            ("!!.description", 0, 0, 0),
            ("..!!!..description", 0, 0, 0),
            ("!.!description", 0, 0, 0),
            # with descriptions and no leading space
            ("description", 0, 0, 0),
            ("... description", 0, 3, 0),
            ("!!! description", 3, 0, 0),
            (".!! description", 2, 1, 0),
            ("!!. description", 2, 0, 1),
            ("..!!!.. description", 0, 0, 0),  # invalid
            ("!.! description", 0, 0, 0),      # invalid
            # with checkbox-like prefix
            ("[ ] description", 0, 0, 0),
            ("[ ] ... description", 0, 3, 0),
            ("[ ] !!! description", 3, 0, 0),
            ("[ ] .!! description", 2, 1, 0),
            ("[ ] !!. description", 2, 0, 1),
            ("[ ] ..!!!.. description", 0, 0, 0),  # invalid
            ("[ ] !.! description", 0, 0, 0),      # invalid
            # with checkbox-like prefix and no space separator (invalid)
            ("[ ] description", 0, 0, 0),
            ("[ ]... description", 0, 0, 0),
            ("[ ]!!! description", 0, 0, 0),
            ("[ ].!! description", 0, 0, 0),
            ("[ ]!!. description", 0, 0, 0),
            ("[ ]..!!!.. description", 0, 0, 0),  # invalid
            ("[ ]!.! description", 0, 0, 0),      # invalid
            # wrong positions in line
            ("[ ] description", 0, 0, 0),
            ("[ ] description ...", 0, 0, 0),
            ("[ ] description !!!", 0, 0, 0),
            ("[ ] description .!!", 0, 0, 0),
            ("[ ] description !!.", 0, 0, 0),
            ("[ ] description !.!", 0, 0, 0),
            ("[ ] description !.!!", 0, 0, 0),
            # double definitions (should pick first)
            ("[ ] description", 0, 0, 0),
            ("[ ] ... description !! ", 0, 3, 0),
            ("[ ] !!! description !.. ", 3, 0, 0),
            ("[ ] .!! description ..! ", 2, 1, 0),
            ("[ ] !!. description !.. ", 2, 0, 1),
            ("[ ] ..!!!.. description ! ", 0, 0, 0),  # invalid
            ("[ ] !.! description ! ", 0, 0, 0),      # invalid
        ]
    )
    def test_priority_regex(self, line, level, leading_dots, trailing_dots):
        """Test regex pattern for detecting priority in lines."""
        p = Priority.from_line(line)
        assert p.level == level
        assert p.leading_dots == leading_dots
        assert p.trailing_dots == trailing_dots


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
        
        assert p1 != p2  # Different due to dots
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
    
    def test_comparison_with_int(self):
        """Test comparison of Priority with integers."""
        p1, p2, p3 = Priority(level=1), Priority(level=2), Priority(level=3)

        assert p1 == 1
        assert p2 == 2
        assert p3 == 3
    
    def test_comparison_with_float(self):
        """Test comparison of Priority with floats."""
        p1, p2, p3 = Priority(level=1), Priority(level=2), Priority(level=3)

        assert p1 == 1.0
        assert p2 == 2.0
        assert p3 == 3.0

    def test_tuple_comparison(self):
        """Test comparison of Priority with tuples."""
        p1 = Priority(level=2, leading_dots=1, trailing_dots=0)
        p2 = Priority(level=2, leading_dots=0, trailing_dots=1)

        assert p1 == (2, 1, 0)
        assert p2 == (2, 0, 1)
    
    def test_to_tuple_and_dict(self):
        """Test conversion of Priority to tuple and dict."""
        p = Priority(level=2, leading_dots=0, trailing_dots=3)
        
        assert p.to_tuple() == (2, 0, 3)
        assert p.to_dict() == {'level': 2, 'leading_dots': 0, 'trailing_dots': 3}

    def test_dict_comparison(self):
        """Test comparison of Priority with dicts."""
        p = Priority(level=2, leading_dots=0, trailing_dots=3)

        assert p == {'level': 2, 'leading_dots': 0, 'trailing_dots': 3}

