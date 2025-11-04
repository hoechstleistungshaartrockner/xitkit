"""Tests for the Status class."""

import pytest
from xitkit.exceptions import XitError
from xitkit.status import Status, StatusType


class TestStatusBasics:
    """Test basic Status functionality."""
    
    @pytest.mark.parametrize("status_type,expected_str,expected_indicator", [
        (StatusType.OPEN, "[ ]", " "),
        (StatusType.CHECKED, "[x]", "x"),
        (StatusType.ONGOING, "[@]", "@"),
        (StatusType.OBSOLETE, "[~]", "~"),
        (StatusType.IN_QUESTION, "[?]", "?")
    ])
    def test_status_creation_and_properties(self, status_type, expected_str, expected_indicator):
        """Test creating status with StatusType enum and basic properties."""
        status = Status(status_type)
        assert status.status_type == status_type
        assert str(status) == expected_str
        assert status.indicator == expected_indicator
        assert repr(status) == f"Status({status_type.name})"
        assert status.to_checkbox() == expected_str
    
    def test_status_immutable(self):
        """Test that Status is immutable (frozen dataclass)."""
        status = Status(StatusType.OPEN)
        with pytest.raises(AttributeError):
            status.status_type = StatusType.CHECKED


class TestStatusFromString:
    """Test Status.from_string method."""
    
    @pytest.mark.parametrize("status_str,expected_type", [
        # Checkbox formats
        ("[ ]", StatusType.OPEN),
        ("[x]", StatusType.CHECKED),
        ("[@]", StatusType.ONGOING),
        ("[~]", StatusType.OBSOLETE),
        ("[?]", StatusType.IN_QUESTION),
        # String formats (lowercase)
        ("open", StatusType.OPEN),
        ("checked", StatusType.CHECKED),
        ("ongoing", StatusType.ONGOING),
        ("obsolete", StatusType.OBSOLETE),
        ("in_question", StatusType.IN_QUESTION),
        # String formats (uppercase)
        ("OPEN", StatusType.OPEN),
        ("CHECKED", StatusType.CHECKED),
        ("ONGOING", StatusType.ONGOING),
        ("OBSOLETE", StatusType.OBSOLETE),
        ("IN_QUESTION", StatusType.IN_QUESTION),
        # Aliases
        ("INQUESTION", StatusType.IN_QUESTION),
        ("DONE", StatusType.CHECKED)
    ])
    def test_valid_status_strings(self, status_str, expected_type):
        """Test valid status strings according to syntax guide."""
        status = Status.from_string(status_str)
        assert status is not None
        assert status.status_type == expected_type
    
    @pytest.mark.parametrize("invalid_status", [
        "[", "]", "[]", "[  ]", "[xx]", "[ x ]","[!]", "[@#]", "[%]", "[$]", "[&]", "[*]",
        "[\t]",    # Tab
        "[\n]",    # Newline  
        "[\r]",    # Carriage return
        "[\u00A0]", # Non-breaking space (mentioned in syntax guide)
        "[*]",      # Invalid character
        "[o]",      # Invalid character  
        "[X]",      # Uppercase invalid
        "[]",       # Missing character
        "[  ]",     # Multiple spaces
        "[ x ]",    # Extra spaces around character
        "[@@]",     # Extra characters
        "",           # Empty string
        "[",          # Incomplete
        "]",          # Incomplete
        "[ ",         # Incomplete
        " ]",         # Incomplete
        "(x)",        # Wrong brackets
        "[x",         # Missing closing bracket
        "x]",         # Missing opening bracket
        "[x] extra",  # Extra text
        "prefix[x]",  # Prefix text
        "[xy]",       # Too long
        "[[x]]",      # Double brackets
    ])
    def test_invalid_status_strings(self, invalid_status):
        """Test that invalid strings raise XitError."""
        with pytest.raises(XitError):
            Status.from_string(invalid_status)
    
    @pytest.mark.parametrize("invalid_input", [None, 123, [], {}, True])
    def test_non_string_input(self, invalid_input):
        """Test non-string input to from_string returns None."""
        status = Status.from_string(invalid_input)
        assert status is None


class TestStatusFromLine:
    """Test Status.from_line method."""
    
    @pytest.mark.parametrize("line,expected_type", [
        ("[ ] Open task", StatusType.OPEN),
        ("[x] Completed task", StatusType.CHECKED),
        ("[@] Ongoing task", StatusType.ONGOING),
        ("[~] Obsolete task", StatusType.OBSOLETE),
        ("[?] Questionable task", StatusType.IN_QUESTION),
        ("[ ]", StatusType.OPEN),  # Status only
        ("[x]", StatusType.CHECKED),  # Status only
        # Valid spacing variations
        ("[ ] Do this", StatusType.OPEN),           # Normal spacing
        ("[ ]   Do this", StatusType.OPEN),         # Extra spaces (part of description)  
        ("[x] ", StatusType.CHECKED),                  # Status with space only
        ("[x]       ", StatusType.CHECKED),            # Status with multiple spaces
    ])
    def test_valid_lines(self, line, expected_type):
        """Test valid status at the beginning of lines with various spacing."""
        status = Status.from_line(line)
        assert status is not None
        assert status.status_type == expected_type
    
    @pytest.mark.parametrize("invalid_line", [
        " [x] Invalid",      # Single space prefix
        "    [x] Invalid",   # Multiple spaces prefix
        "\t[x] Invalid",     # Tab prefix
        "  [ ] Invalid",     # Space prefix with open status
        "",                  # Empty string
        "[]",                # Too short
        "[ ",                # Too short
    ])
    def test_invalid_lines(self, invalid_line):
        """Test invalid lines that should return None."""
        status = Status.from_line(invalid_line)
        assert status is None
    
    @pytest.mark.parametrize("invalid_input", [None, 123, [], {}])
    def test_non_string_input(self, invalid_input):
        """Test non-string input to from_line returns None."""
        status = Status.from_line(invalid_input)
        assert status is None


class TestStatusFromIndicator:
    """Test Status.from_indicator method."""
    
    @pytest.mark.parametrize("indicator,expected_type", [
        (" ", StatusType.OPEN),
        ("x", StatusType.CHECKED),
        ("@", StatusType.ONGOING),
        ("~", StatusType.OBSOLETE),
        ("?", StatusType.IN_QUESTION),
    ])
    def test_valid_indicator_characters(self, indicator, expected_type):
        """Test creating status from valid indicator characters."""
        status = Status.from_indicator(indicator)
        assert status is not None
        assert status.status_type == expected_type
    
    @pytest.mark.parametrize("status_type", list(StatusType))
    def test_status_type_enum_input(self, status_type):
        """Test creating status from StatusType enum."""
        status = Status.from_indicator(status_type)
        assert status is not None
        assert status.status_type == status_type
    
    @pytest.mark.parametrize("invalid_input", [
        "*", "o", "X", "", "xx", "123", "!",  # Invalid strings
        None, 123, [], {}  # Non-string, non-enum inputs
    ])
    def test_invalid_inputs(self, invalid_input):
        """Test invalid indicator characters and non-string/non-enum inputs."""
        status = Status.from_indicator(invalid_input)
        assert status is None


class TestStatusProperties:
    """Test status property methods."""
    
    @pytest.mark.parametrize("status_type,property_name,expected", [
        # Individual status properties
        (StatusType.OPEN, "is_open", True),
        (StatusType.CHECKED, "is_open", False),
        (StatusType.ONGOING, "is_open", False),
        (StatusType.OBSOLETE, "is_open", False),
        (StatusType.IN_QUESTION, "is_open", False),
        (StatusType.CHECKED, "is_checked", True),
        (StatusType.OPEN, "is_checked", False),
        (StatusType.ONGOING, "is_checked", False),
        (StatusType.OBSOLETE, "is_checked", False),
        (StatusType.IN_QUESTION, "is_checked", False),
        (StatusType.ONGOING, "is_ongoing", True),
        (StatusType.OPEN, "is_ongoing", False),
        (StatusType.CHECKED, "is_ongoing", False),
        (StatusType.OBSOLETE, "is_ongoing", False),
        (StatusType.IN_QUESTION, "is_ongoing", False),
        (StatusType.OBSOLETE, "is_obsolete", True),
        (StatusType.OPEN, "is_obsolete", False),
        (StatusType.CHECKED, "is_obsolete", False),
        (StatusType.ONGOING, "is_obsolete", False),
        (StatusType.IN_QUESTION, "is_obsolete", False),
        (StatusType.IN_QUESTION, "is_in_question", True),
        (StatusType.OPEN, "is_in_question", False),
        (StatusType.CHECKED, "is_in_question", False),
        (StatusType.ONGOING, "is_in_question", False),
        (StatusType.OBSOLETE, "is_in_question", False),
        # Composite properties
        (StatusType.CHECKED, "is_complete", True),
        (StatusType.OBSOLETE, "is_complete", True),
        (StatusType.OPEN, "is_complete", False),
        (StatusType.ONGOING, "is_complete", False),
        (StatusType.IN_QUESTION, "is_complete", False),
        (StatusType.OPEN, "is_active", True),
        (StatusType.ONGOING, "is_active", True),
        (StatusType.IN_QUESTION, "is_active", True),
        (StatusType.CHECKED, "is_active", False),
        (StatusType.OBSOLETE, "is_active", False),
    ])
    def test_status_properties(self, status_type, property_name, expected):
        """Test all status property methods."""
        status = Status(status_type)
        assert getattr(status, property_name) == expected


class TestStatusUtilityMethods:
    """Test utility methods."""
    
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
    
    def test_status_equality_and_hashing(self):
        """Test status equality comparison and use as dictionary keys."""
        status1 = Status(StatusType.CHECKED)
        status2 = Status(StatusType.CHECKED)
        status3 = Status(StatusType.OPEN)
        
        # Test equality
        assert status1 == status2
        assert status1 != status3
        assert status2 != status3
        
        # Test hashing by using as dictionary keys
        statuses = {
            Status(StatusType.OPEN): "open",
            Status(StatusType.CHECKED): "checked",
            Status(StatusType.ONGOING): "ongoing",
        }
        
        assert len(statuses) == 3
        assert statuses[Status(StatusType.OPEN)] == "open"
        assert statuses[Status(StatusType.CHECKED)] == "checked"
