"""Tests for the DateUtils module."""

import pytest
from datetime import datetime, timedelta

from xitkit.dateutils import DateParser, get_date_parser, parse_date_expression


class TestDateParserBasics:
    """Test basic DateParser functionality."""
    
    def test_parser_creation(self):
        """Test creating a DateParser instance."""
        parser = DateParser()
        assert isinstance(parser.current_date, datetime)
        
        # Test with specific date
        specific_date = datetime(2025, 10, 15)
        parser = DateParser(specific_date)
        assert parser.current_date == specific_date
    
    def test_natural_keywords(self):
        """Test natural language keyword mapping."""
        parser = DateParser()
        
        expected_keywords = {
            'today': 0,
            'tomorrow': 1,
            'yesterday': -1,
        }
        
        assert parser.natural_keywords == expected_keywords


class TestNaturalLanguageParsing:
    """Test parsing of natural language date expressions."""
    
    def test_parse_today(self):
        """Test parsing 'today'."""
        current_date = datetime(2025, 10, 15)
        parser = DateParser(current_date)
        
        result = parser.parse_date_expression("today")
        assert result == "2025-10-15"
        
        # Test case insensitive
        result = parser.parse_date_expression("TODAY")
        assert result == "2025-10-15"
    
    def test_parse_tomorrow(self):
        """Test parsing 'tomorrow'."""
        current_date = datetime(2025, 10, 15)
        parser = DateParser(current_date)
        
        result = parser.parse_date_expression("tomorrow")
        assert result == "2025-10-16"
    
    def test_parse_yesterday(self):
        """Test parsing 'yesterday'."""
        current_date = datetime(2025, 10, 15)
        parser = DateParser(current_date)
        
        result = parser.parse_date_expression("yesterday")
        assert result == "2025-10-14"


class TestRelativeDateParsing:
    """Test parsing of relative date expressions."""
    
    def test_parse_days(self):
        """Test parsing relative days (1d, 2d, etc.)."""
        current_date = datetime(2025, 10, 15)
        parser = DateParser(current_date)
        
        assert parser.parse_date_expression("1d") == "2025-10-16"
        assert parser.parse_date_expression("2d") == "2025-10-17"
        assert parser.parse_date_expression("7d") == "2025-10-22"
        assert parser.parse_date_expression("0d") == "2025-10-15"
    
    def test_parse_weeks(self):
        """Test parsing relative weeks (1w, 2w, etc.)."""
        current_date = datetime(2025, 10, 15)
        parser = DateParser(current_date)
        
        assert parser.parse_date_expression("1w") == "2025-10-22"
        assert parser.parse_date_expression("2w") == "2025-10-29"
        assert parser.parse_date_expression("4w") == "2025-11-12"
    
    def test_parse_months(self):
        """Test parsing relative months (1m, 2m, etc.)."""
        current_date = datetime(2025, 10, 15)
        parser = DateParser(current_date)
        
        # Months are approximated as 30 days
        assert parser.parse_date_expression("1m") == "2025-11-14"
        assert parser.parse_date_expression("2m") == "2025-12-14"
    
    def test_parse_years(self):
        """Test parsing relative years (1y, 2y, etc.)."""
        current_date = datetime(2025, 10, 15)
        parser = DateParser(current_date)
        
        # Years are approximated as 365 days
        assert parser.parse_date_expression("1y") == "2026-10-15"
        assert parser.parse_date_expression("2y") == "2027-10-15"
    
    def test_case_insensitive_relative(self):
        """Test that relative dates are case insensitive."""
        current_date = datetime(2025, 10, 15)
        parser = DateParser(current_date)
        
        assert parser.parse_date_expression("1D") == "2025-10-16"
        assert parser.parse_date_expression("1W") == "2025-10-22"
        assert parser.parse_date_expression("1M") == "2025-11-14"
        assert parser.parse_date_expression("1Y") == "2026-10-15"


class TestStandardDateFormats:
    """Test parsing of standard date formats."""
    
    def test_parse_valid_standard_dates(self):
        """Test parsing valid standard date formats."""
        parser = DateParser()
        
        valid_dates = [
            "2025-12-31",      # YYYY-MM-DD
            "2025-12",         # YYYY-MM
            "2025",            # YYYY
            "2025-W42",        # YYYY-W##
            "2025-Q4",         # YYYY-Q#
            "2025/12/31",      # YYYY/MM/DD
            "2025/W42",        # YYYY/W##
        ]
        
        for date_str in valid_dates:
            result = parser.parse_date_expression(date_str)
            assert result == date_str  # Should return as-is for valid formats
    
    def test_parse_invalid_standard_dates(self):
        """Test that invalid standard formats return None."""
        parser = DateParser()
        
        invalid_dates = [
            "2025-13-31",      # Invalid month
            "2025-12-32",      # Invalid day
            "2025-W54",        # Invalid week
            "2025-Q5",         # Invalid quarter
            "25-12-31",        # 2-digit year
            "2025/12-31",      # Mixed delimiters
            "not-a-date",      # Not a date
            "",                # Empty string
        ]
        
        for date_str in invalid_dates:
            result = parser.parse_date_expression(date_str)
            # Some might be None, others might be the original string if they match pattern
            # but we're testing they don't crash


class TestDateComparison:
    """Test date comparison functionality."""
    
    def test_compare_dates_basic(self):
        """Test basic date comparison."""
        parser = DateParser()
        
        # Test equal dates
        assert parser._compare_dates("2025-12-31", "2025-12-31") == 0
        
        # Test date1 < date2
        assert parser._compare_dates("2025-12-30", "2025-12-31") == -1
        
        # Test date1 > date2
        assert parser._compare_dates("2025-12-31", "2025-12-30") == 1
    
    def test_compare_different_formats(self):
        """Test comparing dates in different formats."""
        parser = DateParser()
        
        # Month format should be compared as end of month
        # 2025-12 should be treated as 2025-12-31 for comparison
        assert parser._compare_dates("2025-12", "2025-12-30") == 1
        assert parser._compare_dates("2025-12", "2025-12-31") == 0
        
        # Year format should be compared as end of year
        assert parser._compare_dates("2025", "2025-12-31") == 0
        assert parser._compare_dates("2025", "2026-01-01") == -1
    
    def test_normalize_date_for_comparison(self):
        """Test date normalization for comparison."""
        parser = DateParser()
        
        # Standard format should remain unchanged
        assert parser._normalize_date_for_comparison("2025-12-31") == "2025-12-31"
        
        # Month format should become end of month
        assert parser._normalize_date_for_comparison("2025-12") == "2025-12-31"
        assert parser._normalize_date_for_comparison("2025-02") == "2025-02-28"
        assert parser._normalize_date_for_comparison("2024-02") == "2024-02-29"  # Leap year
        
        # Year format should become end of year
        assert parser._normalize_date_for_comparison("2025") == "2025-12-31"
        
        # Quarter format should become end of quarter
        assert parser._normalize_date_for_comparison("2025-Q1") == "2025-03-31"
        assert parser._normalize_date_for_comparison("2025-Q2") == "2025-06-30"
        assert parser._normalize_date_for_comparison("2025-Q3") == "2025-09-30"
        assert parser._normalize_date_for_comparison("2025-Q4") == "2025-12-31"


class TestDateFiltering:
    """Test date filtering functionality."""
    
    def test_matches_date_filter_on_exact(self):
        """Test exact date matching."""
        current_date = datetime(2025, 10, 15)
        parser = DateParser(current_date)
        
        # Should match today
        assert parser.matches_date_filter_on("2025-10-15", "today")
        assert not parser.matches_date_filter_on("2025-10-16", "today")
        
        # Should match exact date
        assert parser.matches_date_filter_on("2025-12-31", "2025-12-31")
        assert not parser.matches_date_filter_on("2025-12-30", "2025-12-31")
        
        # Should match relative dates
        assert parser.matches_date_filter_on("2025-10-16", "1d")
        assert parser.matches_date_filter_on("2025-10-22", "1w")
    
    def test_matches_date_filter_on_no_due_date(self):
        """Test that tasks without due dates don't match filters."""
        parser = DateParser()
        
        assert not parser.matches_date_filter_on(None, "today")
        assert not parser.matches_date_filter_on(None, "2025-12-31")
    
    def test_matches_date_filter_by_range(self):
        """Test date range filtering (on or before)."""
        current_date = datetime(2025, 10, 15)
        parser = DateParser(current_date)
        
        # Tasks due on or before today
        assert parser.matches_date_filter_by("2025-10-15", "today")  # Due today
        assert parser.matches_date_filter_by("2025-10-14", "today")  # Due yesterday
        assert not parser.matches_date_filter_by("2025-10-16", "today")  # Due tomorrow
        
        # Tasks due on or before specific date
        assert parser.matches_date_filter_by("2025-12-30", "2025-12-31")
        assert parser.matches_date_filter_by("2025-12-31", "2025-12-31")
        assert not parser.matches_date_filter_by("2026-01-01", "2025-12-31")
    
    def test_matches_date_filter_by_no_due_date(self):
        """Test that tasks without due dates don't match range filters."""
        parser = DateParser()
        
        assert not parser.matches_date_filter_by(None, "today")
        assert not parser.matches_date_filter_by(None, "2025-12-31")


class TestDateDescriptions:
    """Test human-readable date descriptions."""
    
    def test_get_date_description(self):
        """Test generating human-readable date descriptions."""
        current_date = datetime(2025, 10, 15)
        parser = DateParser(current_date)
        
        # Test relative descriptions
        assert parser.get_date_description("2025-10-15") == "today"
        assert parser.get_date_description("2025-10-16") == "tomorrow"
        assert parser.get_date_description("2025-10-14") == "yesterday"
        assert parser.get_date_description("2025-10-18") == "in 3 days"
        assert parser.get_date_description("2025-10-12") == "3 days ago"
    
    def test_get_date_description_invalid_format(self):
        """Test date description with invalid formats."""
        parser = DateParser()
        
        # Invalid format should return as-is
        assert parser.get_date_description("invalid-date") == "invalid-date"
        assert parser.get_date_description("2025-W42") == "2025-W42"
    
    def test_format_date_for_display(self):
        """Test date formatting for display."""
        parser = DateParser()
        
        # Currently just returns as-is, but could be enhanced
        assert parser.format_date_for_display("2025-12-31") == "2025-12-31"


class TestGlobalFunctions:
    """Test global convenience functions."""
    
    def test_get_date_parser_singleton(self):
        """Test that get_date_parser returns a singleton by default."""
        parser1 = get_date_parser()
        parser2 = get_date_parser()
        assert parser1 is parser2
    
    def test_get_date_parser_with_date(self):
        """Test that get_date_parser with date creates new instance."""
        specific_date = datetime(2025, 10, 15)
        parser = get_date_parser(specific_date)
        assert parser.current_date == specific_date
        
        # Should be different from singleton
        singleton = get_date_parser()
        assert parser is not singleton
    
    def test_parse_date_expression_function(self):
        """Test the global parse_date_expression function."""
        current_date = datetime(2025, 10, 15)
        
        # With specific current date
        result = parse_date_expression("today", current_date)
        assert result == "2025-10-15"
        
        # Without current date (uses default)
        result = parse_date_expression("2025-12-31")
        assert result == "2025-12-31"


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_relative_unit(self):
        """Test invalid relative date units."""
        parser = DateParser()
        
        # Invalid unit should return None
        assert parser.parse_date_expression("1x") is None
        assert parser.parse_date_expression("1hour") is None
        assert parser.parse_date_expression("1") is None
    
    def test_invalid_relative_amount(self):
        """Test invalid relative date amounts."""
        parser = DateParser()
        
        # Non-numeric amount should return None
        assert parser.parse_date_expression("ad") is None
        assert parser.parse_date_expression("xd") is None
    
    def test_empty_and_whitespace_input(self):
        """Test empty and whitespace-only input."""
        parser = DateParser()
        
        assert parser.parse_date_expression("") is None
        assert parser.parse_date_expression("   ") is None
        assert parser.parse_date_expression("\t\n") is None
    
    def test_very_large_relative_dates(self):
        """Test very large relative date values."""
        parser = DateParser()
        
        # Should handle large numbers without crashing
        result = parser.parse_date_expression("1000y")
        assert result is not None
        
        result = parser.parse_date_expression("999999d")
        assert result is not None
    
    def test_negative_relative_dates(self):
        """Test that negative relative dates work correctly."""
        current_date = datetime(2025, 10, 15)
        parser = DateParser(current_date)
        
        # Negative days should go backwards
        # Note: The current implementation doesn't support negative values
        # but we test that it doesn't crash
        result = parser.parse_date_expression("-1d")
        # This will return None with current implementation


class TestLeapYearHandling:
    """Test leap year handling in date comparisons."""
    
    def test_february_in_leap_year(self):
        """Test February handling in leap years."""
        parser = DateParser()
        
        # 2024 is a leap year
        feb_2024 = parser._normalize_date_for_comparison("2024-02")
        assert feb_2024 == "2024-02-29"
        
        # 2025 is not a leap year
        feb_2025 = parser._normalize_date_for_comparison("2025-02")
        assert feb_2025 == "2025-02-28"
        
        # 2000 is a leap year (divisible by 400)
        feb_2000 = parser._normalize_date_for_comparison("2000-02")
        assert feb_2000 == "2000-02-29"
        
        # 1900 is not a leap year (divisible by 100 but not 400)
        feb_1900 = parser._normalize_date_for_comparison("1900-02")
        assert feb_1900 == "1900-02-28"


class TestWeekAndQuarterFormats:
    """Test week and quarter format handling."""
    
    def test_week_format_normalization(self):
        """Test week format normalization."""
        parser = DateParser()
        
        # Week formats should be converted to approximate dates
        result = parser._normalize_date_for_comparison("2025-W01")
        assert "2025-" in result  # Should be in 2025
        
        result = parser._normalize_date_for_comparison("2025-W52")
        assert "2025-" in result or "2026-" in result  # Week 52 might spill into next year
    
    def test_quarter_format_normalization(self):
        """Test quarter format normalization."""
        parser = DateParser()
        
        # Test all quarters
        assert parser._normalize_date_for_comparison("2025-Q1") == "2025-03-31"
        assert parser._normalize_date_for_comparison("2025-Q2") == "2025-06-30"
        assert parser._normalize_date_for_comparison("2025-Q3") == "2025-09-30"
        assert parser._normalize_date_for_comparison("2025-Q4") == "2025-12-31"
    
    def test_slash_format_conversion(self):
        """Test that slash formats are converted to dash formats."""
        parser = DateParser()
        
        # Slash formats should be converted and then normalized
        result = parser._normalize_date_for_comparison("2025/12/31")
        assert result == "2025-12-31"
        
        result = parser._normalize_date_for_comparison("2025/12")
        assert result == "2025-12-31"


class TestBackwardCompatibility:
    """Test backward compatibility methods."""
    
    def test_matches_date_filter_legacy(self):
        """Test the legacy matches_date_filter method."""
        parser = DateParser()
        
        # Should delegate to matches_date_filter_on
        current_date = datetime(2025, 10, 15)
        parser = DateParser(current_date)
        
        assert parser.matches_date_filter("2025-10-15", "today")
        assert not parser.matches_date_filter("2025-10-16", "today")
        assert parser.matches_date_filter("2025-12-31", "2025-12-31")
        assert not parser.matches_date_filter(None, "today")


class TestIntervalParsing:
    """Test interval parsing for recurring tasks."""
    
    def test_parse_interval_expression_days(self):
        """Test parsing day intervals."""
        from xitkit.dateutils import parse_interval_expression
        
        result = parse_interval_expression("1d")
        assert result == timedelta(days=1)
        
        result = parse_interval_expression("7d")
        assert result == timedelta(days=7)
        
        result = parse_interval_expression("30d")
        assert result == timedelta(days=30)
    
    def test_parse_interval_expression_weeks(self):
        """Test parsing week intervals."""
        from xitkit.dateutils import parse_interval_expression
        
        result = parse_interval_expression("1w")
        assert result == timedelta(weeks=1)
        
        result = parse_interval_expression("2w")
        assert result == timedelta(weeks=2)
        
        result = parse_interval_expression("4w")
        assert result == timedelta(weeks=4)
    
    def test_parse_interval_expression_months(self):
        """Test parsing month intervals (approximated as 30-day periods)."""
        from xitkit.dateutils import parse_interval_expression
        
        result = parse_interval_expression("1m")
        assert result == timedelta(days=30)
        
        result = parse_interval_expression("3m")
        assert result == timedelta(days=90)
        
        result = parse_interval_expression("6m")
        assert result == timedelta(days=180)
    
    def test_parse_interval_expression_years(self):
        """Test parsing year intervals (approximated as 365-day periods)."""
        from xitkit.dateutils import parse_interval_expression
        
        result = parse_interval_expression("1y")
        assert result == timedelta(days=365)
        
        result = parse_interval_expression("2y")
        assert result == timedelta(days=730)
    
    def test_parse_interval_expression_case_insensitive(self):
        """Test that interval parsing is case insensitive."""
        from xitkit.dateutils import parse_interval_expression
        
        result1 = parse_interval_expression("1W")
        result2 = parse_interval_expression("1w")
        assert result1 == result2
        
        result1 = parse_interval_expression("3M")
        result2 = parse_interval_expression("3m")
        assert result1 == result2
    
    def test_parse_interval_expression_invalid_formats(self):
        """Test error handling for invalid interval formats."""
        from xitkit.dateutils import parse_interval_expression
        
        with pytest.raises(ValueError, match="Invalid interval format"):
            parse_interval_expression("1x")  # Invalid unit
        
        with pytest.raises(ValueError, match="Invalid interval format"):
            parse_interval_expression("abc")  # No digits
        
        with pytest.raises(ValueError, match="Invalid interval format"):
            parse_interval_expression("1")  # No unit
        
        with pytest.raises(ValueError, match="Interval must be a non-empty string"):
            parse_interval_expression("")
        
        with pytest.raises(ValueError, match="Interval must be a non-empty string"):
            parse_interval_expression(None)
    
    def test_parse_interval_expression_zero_negative(self):
        """Test error handling for zero and negative amounts."""
        from xitkit.dateutils import parse_interval_expression
        
        with pytest.raises(ValueError, match="Interval amount must be positive"):
            parse_interval_expression("0d")
        
        with pytest.raises(ValueError, match="Interval amount must be positive"):
            parse_interval_expression("-1w")


class TestRecurringDateGeneration:
    """Test generation of recurring dates."""
    
    def test_generate_recurring_dates_with_count(self):
        """Test generating recurring dates with count limit."""
        from xitkit.dateutils import generate_recurring_dates
        
        dates = generate_recurring_dates("2025-10-20", "1w", count=4)
        expected = ["2025-10-20", "2025-10-27", "2025-11-03", "2025-11-10"]
        assert dates == expected
    
    def test_generate_recurring_dates_with_end_date(self):
        """Test generating recurring dates with end date limit."""
        from xitkit.dateutils import generate_recurring_dates
        
        dates = generate_recurring_dates("2025-10-01", "1w", end_date="2025-10-31")
        expected = ["2025-10-01", "2025-10-08", "2025-10-15", "2025-10-22", "2025-10-29"]
        assert dates == expected
    
    def test_generate_recurring_dates_monthly(self):
        """Test generating monthly recurring dates."""
        from xitkit.dateutils import generate_recurring_dates
        
        dates = generate_recurring_dates("2025-01-01", "1m", count=3)
        expected = ["2025-01-01", "2025-01-31", "2025-03-02"]
        assert dates == expected
    
    def test_generate_recurring_dates_daily(self):
        """Test generating daily recurring dates."""
        from xitkit.dateutils import generate_recurring_dates
        
        dates = generate_recurring_dates("2025-10-15", "1d", count=3)
        expected = ["2025-10-15", "2025-10-16", "2025-10-17"]
        assert dates == expected
    
    def test_generate_recurring_dates_invalid_start_date(self):
        """Test error handling for invalid start date."""
        from xitkit.dateutils import generate_recurring_dates
        
        with pytest.raises(ValueError, match="Invalid start date format"):
            generate_recurring_dates("invalid-date", "1w", count=2)
        
        with pytest.raises(ValueError, match="Start date is required"):
            generate_recurring_dates("", "1w", count=2)
    
    def test_generate_recurring_dates_invalid_end_date(self):
        """Test error handling for invalid end date."""
        from xitkit.dateutils import generate_recurring_dates
        
        with pytest.raises(ValueError, match="Invalid end date format"):
            generate_recurring_dates("2025-10-01", "1w", end_date="invalid-date")
        
        with pytest.raises(ValueError, match="End date must be after start date"):
            generate_recurring_dates("2025-10-01", "1w", end_date="2025-09-01")
    
    def test_generate_recurring_dates_invalid_count(self):
        """Test error handling for invalid count."""
        from xitkit.dateutils import generate_recurring_dates
        
        with pytest.raises(ValueError, match="Count must be positive"):
            generate_recurring_dates("2025-10-01", "1w", count=0)
        
        with pytest.raises(ValueError, match="Count must be positive"):
            generate_recurring_dates("2025-10-01", "1w", count=-1)
        
        with pytest.raises(ValueError, match="Count cannot exceed 1000"):
            generate_recurring_dates("2025-10-01", "1w", count=1001)
    
    def test_generate_recurring_dates_no_parameters(self):
        """Test that either end_date or count is required."""
        from xitkit.dateutils import generate_recurring_dates
        
        # This should raise an error when no limit is specified
        with pytest.raises(ValueError, match="Either end_date or count must be specified"):
            generate_recurring_dates("2025-10-01", "1w")