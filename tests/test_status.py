"""Tests for the Status class."""

import pytest
from xitkit.status import Status, StatusType


class TestStatusBasics:
    """Test basic Status functionality."""
    
    def test_status_creation_with_status_type(self):
        """Test creating status with StatusType enum."""
        status = Status(StatusType.CHECKED)
        assert status.status_type == StatusType.CHECKED
        assert str(status) == "[x]"
    
    def test_all_status_types(self):
        """Test all valid status types can be created."""
        test_cases = [
            (StatusType.OPEN, "[ ]"),
            (StatusType.CHECKED, "[x]"),
            (StatusType.ONGOING, "[@]"),
            (StatusType.OBSOLETE, "[~]"),
            (StatusType.IN_QUESTION, "[?]")
        ]
        
        for status_type, expected_str in test_cases:
            status = Status(status_type)
            assert status.status_type == status_type
            assert str(status) == expected_str
    
    def test_status_immutable(self):
        """Test that Status is immutable (frozen dataclass)."""
        status = Status(StatusType.OPEN)
        with pytest.raises(AttributeError):
            status.status_type = StatusType.CHECKED
    
    def test_status_repr(self):
        """Test status repr representation."""
        status = Status(StatusType.CHECKED)
        assert repr(status) == "Status(CHECKED)"
    
    def test_indicator_property(self):
        """Test indicator property returns correct character."""
        test_cases = [
            (StatusType.OPEN, " "),
            (StatusType.CHECKED, "x"),
            (StatusType.ONGOING, "@"),
            (StatusType.OBSOLETE, "~"),
            (StatusType.IN_QUESTION, "?")
        ]
        
        for status_type, expected_indicator in test_cases:
            status = Status(status_type)
            assert status.indicator == expected_indicator


class TestStatusFromString:
    """Test Status.from_string method."""
    
    def test_valid_status_strings(self):
        """Test valid status strings according to syntax guide."""
        test_cases = [
            ("[ ]", StatusType.OPEN),
            ("[x]", StatusType.CHECKED),
            ("[@]", StatusType.ONGOING),
            ("[~]", StatusType.OBSOLETE),
            ("[?]", StatusType.IN_QUESTION)
        ]
        
        for status_str, expected_type in test_cases:
            status = Status.from_string(status_str)
            assert status is not None
            assert status.status_type == expected_type
            assert str(status) == status_str
    
    def test_invalid_status_strings_from_syntax_guide(self):
        """Test invalid status strings specifically mentioned in syntax guide."""
        invalid_cases = [
            "[*]",      # Invalid character
            "[o]",      # Invalid character  
            "[X]",      # Uppercase invalid
            "[]",       # Missing character
            "[  ]",     # Multiple spaces
            "[ x ]",    # Extra spaces around character
            "[@@]",     # Extra characters
        ]
        
        for invalid_str in invalid_cases:
            status = Status.from_string(invalid_str)
            assert status is None
    
    def test_invalid_formats(self):
        """Test various invalid formats."""
        invalid_cases = [
            "",           # Empty string
            "[",          # Incomplete
            "]",          # Incomplete
            "[ ",         # Incomplete
            " ]",         # Incomplete
            "x",          # No brackets
            "(x)",        # Wrong brackets
            "[x",         # Missing closing bracket
            "x]",         # Missing opening bracket
            "[x] extra",  # Extra text
            "prefix[x]",  # Prefix text
            "[xy]",       # Too long
            "[[x]]",      # Double brackets
        ]
        
        for invalid_str in invalid_cases:
            status = Status.from_string(invalid_str)
            assert status is None
    
    def test_non_string_input(self):
        """Test non-string input to from_string."""
        invalid_inputs = [None, 123, [], {}, True]
        
        for invalid_input in invalid_inputs:
            status = Status.from_string(invalid_input)
            assert status is None


class TestStatusFromLine:
    """Test Status.from_line method."""
    
    def test_valid_status_at_line_start(self):
        """Test valid status at the beginning of lines."""
        test_cases = [
            ("[ ] Open task", StatusType.OPEN),
            ("[x] Completed task", StatusType.CHECKED),
            ("[@] Ongoing task", StatusType.ONGOING),
            ("[~] Obsolete task", StatusType.OBSOLETE),
            ("[?] Questionable task", StatusType.IN_QUESTION),
            ("[ ]", StatusType.OPEN),  # Status only
            ("[x]", StatusType.CHECKED),  # Status only
        ]
        
        for line, expected_type in test_cases:
            status = Status.from_line(line)
            assert status is not None
            assert status.status_type == expected_type
    
    def test_invalid_whitespace_prefix_from_syntax_guide(self):
        """Test that status cannot be preceded by whitespace (from syntax guide)."""
        invalid_cases = [
            " [x] Invalid",      # Single space prefix
            "    [x] Invalid",   # Multiple spaces prefix
            "\t[x] Invalid",     # Tab prefix
            "  [ ] Invalid",     # Space prefix with open status
        ]
        
        for invalid_line in invalid_cases:
            status = Status.from_line(invalid_line)
            assert status is None
    
    def test_valid_status_with_description_spacing(self):
        """Test status with various description spacing."""
        # According to syntax guide, space after status is part of description
        test_cases = [
            "[ ] Do this",           # Normal spacing
            "[ ]   Do this",         # Extra spaces (part of description)  
            "[x] ",                  # Status with space only
            "[x]       ",            # Status with multiple spaces
        ]
        
        for line in test_cases:
            status = Status.from_line(line)
            assert status is not None
            assert status.status_type in [StatusType.OPEN, StatusType.CHECKED]
    
    def test_line_too_short(self):
        """Test lines too short to contain status."""
        invalid_cases = ["", "x", "[]", "[ "]
        
        for short_line in invalid_cases:
            if len(short_line) < 3:
                status = Status.from_line(short_line)
                assert status is None
    
    def test_non_string_line(self):
        """Test non-string input to from_line."""
        invalid_inputs = [None, 123, [], {}]
        
        for invalid_input in invalid_inputs:
            status = Status.from_line(invalid_input)
            assert status is None


class TestStatusFromIndicator:
    """Test Status.from_indicator method."""
    
    def test_valid_indicator_characters(self):
        """Test creating status from valid indicator characters."""
        test_cases = [
            (" ", StatusType.OPEN),
            ("x", StatusType.CHECKED),
            ("@", StatusType.ONGOING),
            ("~", StatusType.OBSOLETE),
            ("?", StatusType.IN_QUESTION),
        ]
        
        for indicator, expected_type in test_cases:
            status = Status.from_indicator(indicator)
            assert status is not None
            assert status.status_type == expected_type
    
    def test_status_type_enum_input(self):
        """Test creating status from StatusType enum."""
        for status_type in StatusType:
            status = Status.from_indicator(status_type)
            assert status is not None
            assert status.status_type == status_type
    
    def test_invalid_indicator_characters(self):
        """Test invalid indicator characters."""
        invalid_indicators = ["*", "o", "X", "", "xx", "123", "!"]
        
        for invalid_indicator in invalid_indicators:
            status = Status.from_indicator(invalid_indicator)
            assert status is None
    
    def test_non_string_non_enum_input(self):
        """Test non-string, non-enum input."""
        invalid_inputs = [None, 123, [], {}]
        
        for invalid_input in invalid_inputs:
            status = Status.from_indicator(invalid_input)
            assert status is None


class TestStatusProperties:
    """Test status property methods."""
    
    def test_is_open(self):
        """Test is_open property."""
        open_status = Status(StatusType.OPEN)
        assert open_status.is_open is True
        
        other_statuses = [StatusType.CHECKED, StatusType.ONGOING, StatusType.OBSOLETE, StatusType.IN_QUESTION]
        for status_type in other_statuses:
            status = Status(status_type)
            assert status.is_open is False
    
    def test_is_checked(self):
        """Test is_checked property."""
        checked_status = Status(StatusType.CHECKED)
        assert checked_status.is_checked is True
        
        other_statuses = [StatusType.OPEN, StatusType.ONGOING, StatusType.OBSOLETE, StatusType.IN_QUESTION]
        for status_type in other_statuses:
            status = Status(status_type)
            assert status.is_checked is False
    
    def test_is_ongoing(self):
        """Test is_ongoing property."""
        ongoing_status = Status(StatusType.ONGOING)
        assert ongoing_status.is_ongoing is True
        
        other_statuses = [StatusType.OPEN, StatusType.CHECKED, StatusType.OBSOLETE, StatusType.IN_QUESTION]
        for status_type in other_statuses:
            status = Status(status_type)
            assert status.is_ongoing is False
    
    def test_is_obsolete(self):
        """Test is_obsolete property.""" 
        obsolete_status = Status(StatusType.OBSOLETE)
        assert obsolete_status.is_obsolete is True
        
        other_statuses = [StatusType.OPEN, StatusType.CHECKED, StatusType.ONGOING, StatusType.IN_QUESTION]
        for status_type in other_statuses:
            status = Status(status_type)
            assert status.is_obsolete is False
    
    def test_is_in_question(self):
        """Test is_in_question property."""
        question_status = Status(StatusType.IN_QUESTION)
        assert question_status.is_in_question is True
        
        other_statuses = [StatusType.OPEN, StatusType.CHECKED, StatusType.ONGOING, StatusType.OBSOLETE]
        for status_type in other_statuses:
            status = Status(status_type)
            assert status.is_in_question is False
    
    def test_is_complete(self):
        """Test is_complete property (checked or obsolete)."""
        complete_statuses = [StatusType.CHECKED, StatusType.OBSOLETE]
        for status_type in complete_statuses:
            status = Status(status_type)
            assert status.is_complete is True
        
        incomplete_statuses = [StatusType.OPEN, StatusType.ONGOING, StatusType.IN_QUESTION]
        for status_type in incomplete_statuses:
            status = Status(status_type)
            assert status.is_complete is False
    
    def test_is_active(self):
        """Test is_active property (open, ongoing, or in question)."""
        active_statuses = [StatusType.OPEN, StatusType.ONGOING, StatusType.IN_QUESTION]
        for status_type in active_statuses:
            status = Status(status_type)
            assert status.is_active is True
        
        inactive_statuses = [StatusType.CHECKED, StatusType.OBSOLETE]
        for status_type in inactive_statuses:
            status = Status(status_type)
            assert status.is_active is False


class TestStatusUtilityMethods:
    """Test utility methods."""
    
    def test_to_checkbox(self):
        """Test to_checkbox method."""
        test_cases = [
            (StatusType.OPEN, "[ ]"),
            (StatusType.CHECKED, "[x]"),
            (StatusType.ONGOING, "[@]"),
            (StatusType.OBSOLETE, "[~]"),
            (StatusType.IN_QUESTION, "[?]"),
        ]
        
        for status_type, expected_checkbox in test_cases:
            status = Status(status_type)
            assert status.to_checkbox() == expected_checkbox
            assert status.to_checkbox() == str(status)
    
    def test_get_valid_indicators(self):
        """Test get_valid_indicators static method."""
        indicators = Status.get_valid_indicators()
        expected_indicators = [" ", "x", "@", "~", "?"]
        assert indicators == expected_indicators
        assert len(indicators) == 5
    
    def test_get_valid_statuses(self):
        """Test get_valid_statuses static method."""
        statuses = Status.get_valid_statuses()
        expected_statuses = ["[ ]", "[x]", "[@]", "[~]", "[?]"]
        assert statuses == expected_statuses
        assert len(statuses) == 5


class TestStatusEquality:
    """Test status equality and hashing."""
    
    def test_status_equality(self):
        """Test status equality comparison."""
        status1 = Status(StatusType.CHECKED)
        status2 = Status(StatusType.CHECKED)
        status3 = Status(StatusType.OPEN)
        
        assert status1 == status2
        assert status1 != status3
        assert status2 != status3
    
    def test_status_hashing(self):
        """Test status can be used as dictionary keys."""
        statuses = {
            Status(StatusType.OPEN): "open",
            Status(StatusType.CHECKED): "checked",
            Status(StatusType.ONGOING): "ongoing",
        }
        
        assert len(statuses) == 3
        assert statuses[Status(StatusType.OPEN)] == "open"
        assert statuses[Status(StatusType.CHECKED)] == "checked"


class TestStatusEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_unicode_characters_invalid(self):
        """Test that unicode characters are invalid in status."""
        unicode_cases = ["[α]", "[β]", "[γ]", "[ñ]", "[é]"]
        
        for unicode_status in unicode_cases:
            status = Status.from_string(unicode_status)
            assert status is None
    
    def test_special_characters_invalid(self):
        """Test special characters are invalid."""
        special_cases = ["[!]", "[@#]", "[%]", "[$]", "[&]", "[*]"]
        
        for special_status in special_cases:
            status = Status.from_string(special_status)
            # Note: [@] is valid (ongoing), so we need to be more specific
            if special_status != "[@]":
                assert status is None
    
    def test_whitespace_variations_invalid(self):
        """Test different types of whitespace are invalid (except regular space)."""
        # Note: Regular space " " is valid for OPEN status
        whitespace_cases = [
            "[\t]",    # Tab
            "[\n]",    # Newline  
            "[\r]",    # Carriage return
            "[\u00A0]" # Non-breaking space (mentioned in syntax guide)
        ]
        
        for whitespace_status in whitespace_cases:
            status = Status.from_string(whitespace_status)
            assert status is None