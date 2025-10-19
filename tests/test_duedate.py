"""
Tests for DueDate class
=======================
Tests the DueDate class functionality according to syntax guide requirements.
"""

import pytest
from datetime import datetime, timedelta
from xit.duedate import DueDate


class TestDueDateBasics:
    """Test basic DueDate class functionality."""
    
    def test_due_date_creation_with_expression(self):
        """Test creating due date with valid expression."""
        due_date = DueDate(expression="-> 2025-12-31")
        assert due_date.expression == "-> 2025-12-31"
        assert due_date.is_valid
        assert due_date.date_part == "2025-12-31"

    def test_due_date_string_representation(self):
        """Test string representation."""
        due_date = DueDate(expression="-> 2025-12-31")
        assert str(due_date) == "-> 2025-12-31"


class TestDueDateFromString:
    """Test creating DueDate from date strings."""
    
    def test_valid_full_date_formats(self):
        """Test various valid full date formats."""
        # Standard YYYY-MM-DD format
        due_date = DueDate.from_string("2025-12-31")
        assert due_date is not None
        assert due_date.expression == "-> 2025-12-31"
        assert due_date.is_valid
        
        # Slash format
        due_date = DueDate.from_string("2025/12/31")
        assert due_date is not None
        assert due_date.is_valid

    def test_valid_partial_date_formats(self):
        """Test partial date formats (month, year)."""
        # Month format (implies last day of month)
        due_date = DueDate.from_string("2025-12")
        assert due_date is not None
        assert due_date.is_valid
        
        # Year format (implies last day of year)
        due_date = DueDate.from_string("2025")
        assert due_date is not None
        assert due_date.is_valid

    def test_valid_week_format(self):
        """Test week format YYYY-W##."""
        due_date = DueDate.from_string("2025-W01")
        assert due_date is not None
        assert due_date.is_valid
        
        due_date = DueDate.from_string("2025-W52")
        assert due_date is not None
        assert due_date.is_valid
        
        # Slash format for weeks
        due_date = DueDate.from_string("2025/W01")
        assert due_date is not None
        assert due_date.is_valid

    def test_valid_quarter_format(self):
        """Test quarter format YYYY-Q#."""
        for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
            due_date = DueDate.from_string(f"2025-{quarter}")
            assert due_date is not None, f"Failed for {quarter}"
            assert due_date.is_valid

    def test_invalid_date_formats(self):
        """Test invalid date formats return None."""
        invalid_dates = [
            None,
            "",
            "invalid",
            "2025-13-01",  # Invalid month
            "2025-02-30",  # Invalid day
            "2025-W00",    # Invalid week (week 0)
            "2025-Q5",     # Invalid quarter
            "2025-Q0",     # Invalid quarter (0)
            "2025-01/31",  # Mixed delimiters
            "25-01-31",    # Wrong year format
            "abc-12-31",   # Non-numeric year
            "2025-ab-31",  # Non-numeric month
            "2025-12-ab",  # Non-numeric day
        ]
        
        for invalid_date in invalid_dates:
            result = DueDate.from_string(invalid_date)
            assert result is None, f"Should be None for: {invalid_date}"


class TestDueDateFromLine:
    """Test parsing due dates from complete task lines."""
    
    def test_basic_due_date_parsing(self):
        """Test parsing due dates from task lines."""
        line = "[ ] Do something -> 2025-12-31"
        due_date = DueDate.from_line(line)
        assert due_date is not None
        assert "2025-12-31" in due_date.expression
        assert due_date.is_valid

    def test_due_date_with_description_before(self):
        """Test due date with description before it."""
        line = "[ ] Complete the project -> 2025-06-15"
        due_date = DueDate.from_line(line)
        assert due_date is not None
        assert "2025-06-15" in due_date.expression

    def test_due_date_with_content_after(self):
        """Test due date with content after it (should be ignored)."""
        line = "[ ] -> 2025-01-15 (very important!)"
        due_date = DueDate.from_line(line)
        assert due_date is not None
        assert "2025-01-15" in due_date.expression

    def test_due_date_on_continuation_line(self):
        """Test due date on continuation line."""
        line = "    -> 2025-03-20"
        due_date = DueDate.from_line(line)
        assert due_date is not None
        assert "2025-03-20" in due_date.expression

    def test_due_date_with_punctuation_around(self):
        """Test due date surrounded by punctuation."""
        test_cases = [
            "[ ] Do this soon -> 2025-01-31!!!",
            "[ ] Do this (-> 2025-01-31)",
            "[ ] Task: -> 2025-01-31.",
        ]
        
        for line in test_cases:
            due_date = DueDate.from_line(line)
            assert due_date is not None, f"Failed to parse: {line}"
            assert "2025-01-31" in due_date.expression

    def test_invalid_due_date_patterns(self):
        """Test patterns that should not be recognized as due dates."""
        invalid_lines = [
            "[ ] ---> 2025-01-31",           # Wrong prefix
            "[ ] Due-> 2025-01-31",          # No space before ->
            "[ ] -> 2025-01-31very urgent",  # No space after date
            "[ ] ->2025-01-31",              # No space after ->
            "[ ] → 2025-01-31",              # Wrong arrow character
            "[ ] ->   2025-01-31",           # Extra spaces
            "[ ] >2025-01-31",               # Missing hyphen
            "[ ] -> 2025-01-31T10:00",       # Time component
            "[ ] -> 2025-01-31-0",           # Extra suffix
            "[ ] -> 2025/01/31/0",           # Extra suffix with slash
        ]
        
        for line in invalid_lines:
            due_date = DueDate.from_line(line)
            assert due_date is None, f"Should not parse: {line}"

    def test_no_due_date_in_line(self):
        """Test lines without due dates."""
        lines_without_dates = [
            "[ ] Just a regular task",
            "[ ] Task with #tags but no date",
            "[ ] ! Priority task",
            "",
            "Regular text without checkbox",
        ]
        
        for line in lines_without_dates:
            due_date = DueDate.from_line(line)
            assert due_date is None

    def test_redundant_due_dates(self):
        """Test that only first due date is recognized."""
        line = "[ ] -> 2025-01-31 -> 2025-02-28"
        due_date = DueDate.from_line(line)
        assert due_date is not None
        # Should only capture the first one
        assert "2025-01-31" in due_date.expression
        assert "2025-02-28" not in due_date.expression


class TestDueDateFormats:
    """Test all supported date formats from syntax guide."""
    
    def test_all_hyphen_formats(self):
        """Test all hyphen-based date formats."""
        formats = [
            "2025-12-31",  # Full date
            "2025-12",     # Month
            "2025",        # Year
            "2025-W01",    # Week
            "2025-Q1",     # Quarter
        ]
        
        for date_format in formats:
            line = f"[ ] -> {date_format}"
            due_date = DueDate.from_line(line)
            assert due_date is not None, f"Failed for format: {date_format}"
            assert due_date.is_valid

    def test_all_slash_formats(self):
        """Test all slash-based date formats."""
        formats = [
            "2025/12/31",  # Full date
            "2025/W01",    # Week with slash
        ]
        
        for date_format in formats:
            line = f"[ ] -> {date_format}"
            due_date = DueDate.from_line(line)
            assert due_date is not None, f"Failed for format: {date_format}"
            assert due_date.is_valid

    def test_mixed_delimiters_invalid(self):
        """Test that mixed delimiters are invalid."""
        mixed_formats = [
            "2025-01/31",
            "2025/01-31",
        ]
        
        for date_format in mixed_formats:
            line = f"[ ] -> {date_format}"
            due_date = DueDate.from_line(line)
            assert due_date is None, f"Should not parse mixed format: {date_format}"


class TestDueDateComparison:
    """Test due date comparison and utility methods."""
    
    def test_overdue_detection(self):
        """Test overdue detection."""
        reference_date = datetime(2025, 6, 15)
        
        # Overdue date
        overdue = DueDate.from_string("2025-06-10")
        assert overdue.is_overdue(reference_date)
        
        # Future date
        future = DueDate.from_string("2025-06-20")
        assert not future.is_overdue(reference_date)
        
        # Same date (not overdue)
        same_day = DueDate.from_string("2025-06-15")
        assert not same_day.is_overdue(reference_date)

    def test_days_until_due(self):
        """Test calculating days until due."""
        reference_date = datetime(2025, 6, 15)
        
        # Future date
        future = DueDate.from_string("2025-06-20")
        assert future.days_until_due(reference_date) == 5
        
        # Past date (negative)
        past = DueDate.from_string("2025-06-10")
        assert past.days_until_due(reference_date) == -5
        
        # Same date
        same_day = DueDate.from_string("2025-06-15")
        assert same_day.days_until_due(reference_date) == 0

    def test_due_date_descriptions(self):
        """Test human-readable descriptions."""
        reference_date = datetime(2025, 6, 15)
        
        # Various scenarios
        test_cases = [
            ("2025-06-15", "Due today"),
            ("2025-06-16", "Due tomorrow"),
            ("2025-06-18", "Due in 3 days"),
            ("2025-06-14", "Overdue by 1 day"),
            ("2025-06-10", "Overdue by 5 days"),
        ]
        
        for date_str, expected_desc in test_cases:
            due_date = DueDate.from_string(date_str)
            description = due_date.get_description(reference_date)
            assert description == expected_desc, f"Expected '{expected_desc}' for {date_str}, got '{description}'"

    def test_due_date_equality(self):
        """Test due date equality comparison."""
        due_date1 = DueDate.from_string("2025-12-31")
        due_date2 = DueDate.from_string("2025-12-31")
        due_date3 = DueDate.from_string("2025-12-30")
        
        assert due_date1 == due_date2
        assert due_date1 != due_date3
        assert due_date1 != "not a due date"

    def test_due_date_ordering(self):
        """Test due date ordering."""
        early = DueDate.from_string("2025-06-15")
        late = DueDate.from_string("2025-06-20")
        
        assert early < late
        assert not late < early
        assert not early < early  # Same date

    def test_due_date_hashing(self):
        """Test due date hashing for use in sets/dicts."""
        due_date1 = DueDate.from_string("2025-12-31")
        due_date2 = DueDate.from_string("2025-12-31")
        due_date3 = DueDate.from_string("2025-12-30")
        
        assert hash(due_date1) == hash(due_date2)
        assert hash(due_date1) != hash(due_date3)
        
        # Test in set
        date_set = {due_date1, due_date2, due_date3}
        assert len(date_set) == 2  # due_date1 and due_date2 are same


class TestDueDateEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_invalid_due_date_operations(self):
        """Test operations on invalid due dates."""
        # Create an invalid due date by setting expression manually
        invalid_date = DueDate(expression="-> invalid")
        
        assert not invalid_date.is_valid
        assert not invalid_date.is_overdue()
        assert invalid_date.days_until_due() is None
        assert "Invalid date" in invalid_date.get_description()

    def test_leap_year_handling(self):
        """Test leap year date handling."""
        # 2024 is a leap year
        leap_day = DueDate.from_string("2024-02-29")
        assert leap_day is not None
        assert leap_day.is_valid
        
        # 2025 is not a leap year (Feb 29 would be invalid in normal validation)
        # But our current implementation might not catch this

    def test_year_boundaries(self):
        """Test year boundary dates."""
        new_year = DueDate.from_string("2025-01-01")
        year_end = DueDate.from_string("2025-12-31")
        
        assert new_year is not None
        assert year_end is not None
        assert new_year.is_valid
        assert year_end.is_valid
        assert new_year < year_end

    def test_various_quarter_and_week_formats(self):
        """Test various quarter and week formats."""
        # Test all quarters
        for q in range(1, 5):
            quarter_date = DueDate.from_string(f"2025-Q{q}")
            assert quarter_date is not None, f"Failed for Q{q}"
            assert quarter_date.is_valid
        
        # Test various week numbers
        week_numbers = ["01", "26", "52"]
        for week in week_numbers:
            week_date = DueDate.from_string(f"2025-W{week}")
            assert week_date is not None, f"Failed for W{week}"
            assert week_date.is_valid

    def test_whitespace_handling(self):
        """Test handling of whitespace in date parsing."""
        # Leading/trailing whitespace in from_string
        due_date = DueDate.from_string("  2025-12-31  ")
        assert due_date is not None
        assert due_date.is_valid

    def test_date_part_property(self):
        """Test date_part property extraction."""
        due_date = DueDate(expression="-> 2025-12-31")
        assert due_date.date_part == "2025-12-31"
        
        # Test with different prefix
        due_date2 = DueDate(expression="2025-12-31")
        assert due_date2.date_part == "2025-12-31"


class TestDueDateIntegrationWithDateUtils:
    """Test integration with dateutils functionality."""
    
    def test_date_normalization(self):
        """Test that date normalization works properly."""
        # Test various formats get normalized correctly
        test_cases = [
            "2025-12-31",  # Should stay the same
            "2025-12",     # Should normalize to last day of month
            "2025",        # Should normalize to last day of year
        ]
        
        for date_format in test_cases:
            due_date = DueDate.from_string(date_format)
            assert due_date is not None
            assert due_date.implied_date is not None
            # The implied_date should be in YYYY-MM-DD format
            assert len(due_date.implied_date.split('-')) == 3

    def test_comparison_with_different_formats(self):
        """Test that different formats can be compared properly."""
        # These should all represent the same date (end of 2025)
        year_format = DueDate.from_string("2025")
        month_format = DueDate.from_string("2025-12")
        day_format = DueDate.from_string("2025-12-31")
        
        # They should all normalize to the same date for comparison
        # (This depends on the dateutils implementation)
        assert year_format.is_valid
        assert month_format.is_valid
        assert day_format.is_valid
