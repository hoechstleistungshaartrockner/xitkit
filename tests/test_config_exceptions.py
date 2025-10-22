"""Tests for configuration and exceptions modules."""

import pytest
from pathlib import Path

from xitkit.config import (
    ParsingConfig, DisplayConfig, DateConfig, AppConfig, 
    get_config, load_config_from_file, save_config_to_file
)
from xitkit.exceptions import (
    XitError, ParseError, ValidationError, FileNotSupportedError,
    TaskFilterError, DateParseError
)


class TestParsingConfig:
    """Test ParsingConfig dataclass."""
    
    def test_parsing_config_defaults(self):
        """Test default parsing configuration."""
        config = ParsingConfig()
        
        assert config.supported_extensions == {'.md', '.xit'}
        assert config.continuation_indent == 4
        assert config.max_file_size_mb == 10
        assert config.encoding == 'utf-8'
    
    def test_parsing_config_custom(self):
        """Test custom parsing configuration."""
        config = ParsingConfig(
            supported_extensions={'.txt', '.md'},
            continuation_indent=2,
            max_file_size_mb=50,
            encoding='latin1'
        )
        
        assert config.supported_extensions == {'.txt', '.md'}
        assert config.continuation_indent == 2
        assert config.max_file_size_mb == 50
        assert config.encoding == 'latin1'


class TestDisplayConfig:
    """Test DisplayConfig dataclass."""
    
    def test_display_config_defaults(self):
        """Test default display configuration."""
        config = DisplayConfig()
        
        expected_colors = {
            'OPEN': 'white',
            'DONE': 'green',
            'ONGOING': 'yellow',
            'OBSOLETE': 'red',
            'INQUESTION': 'magenta'
        }
        
        assert config.status_colors == expected_colors
        assert config.max_description_length == 200
        assert config.show_file_headers is True
        assert config.group_by_file is True
    
    def test_display_config_custom(self):
        """Test custom display configuration."""
        custom_colors = {
            'OPEN': 'blue',
            'DONE': 'bright_green',
            'ONGOING': 'orange',
            'OBSOLETE': 'dim_red',
            'INQUESTION': 'purple'
        }
        
        config = DisplayConfig(
            status_colors=custom_colors,
            max_description_length=100,
            show_file_headers=False,
            group_by_file=False
        )
        
        assert config.status_colors == custom_colors
        assert config.max_description_length == 100
        assert config.show_file_headers is False
        assert config.group_by_file is False


class TestDateConfig:
    """Test DateConfig dataclass."""
    
    def test_date_config_defaults(self):
        """Test default date configuration."""
        config = DateConfig()
        
        expected_keywords = {
            'today': 0,
            'tomorrow': 1,
            'yesterday': -1,
        }
        
        assert config.natural_keywords == expected_keywords
        assert len(config.supported_formats) > 5
        # Check for regex pattern that matches YYYY-MM-DD format
        assert any(r'\d{4}-\d{2}-\d{2}' in fmt for fmt in config.supported_formats)
    
    def test_date_config_custom(self):
        """Test custom date configuration."""
        custom_keywords = {
            'today': 0,
            'next week': 7,
            'next month': 30,
        }
        
        custom_formats = [
            r'^\d{4}-\d{2}-\d{2}$',
            r'^\d{2}/\d{2}/\d{4}$',
        ]
        
        config = DateConfig(
            natural_keywords=custom_keywords,
            supported_formats=custom_formats
        )
        
        assert config.natural_keywords == custom_keywords
        assert config.supported_formats == custom_formats


class TestAppConfig:
    """Test main AppConfig dataclass."""
    
    def test_app_config_defaults(self):
        """Test default application configuration."""
        config = AppConfig()
        
        assert isinstance(config.parsing, ParsingConfig)
        assert isinstance(config.display, DisplayConfig)
        assert isinstance(config.date, DateConfig)
        assert config.app_name == "xit"
        assert config.version == "0.1.0"
        assert isinstance(config.config_dir, Path)
    
    def test_app_config_custom_components(self):
        """Test app config with custom component configurations."""
        custom_parsing = ParsingConfig(continuation_indent=2)
        custom_display = DisplayConfig(max_description_length=50)
        custom_date = DateConfig()
        
        config = AppConfig(
            parsing=custom_parsing,
            display=custom_display,
            date=custom_date,
            app_name="custom-xit",
            version="2.0.0"
        )
        
        assert config.parsing is custom_parsing
        assert config.display is custom_display
        assert config.date is custom_date
        assert config.app_name == "custom-xit"
        assert config.version == "2.0.0"


class TestConfigGlobalFunctions:
    """Test global configuration functions."""
    
    def test_get_config_singleton(self):
        """Test that get_config returns a singleton."""
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
        assert isinstance(config1, AppConfig)
    
    def test_load_config_from_file(self, temp_dir):
        """Test loading config from file (placeholder)."""
        config_file = temp_dir / "config.toml"
        
        # Currently returns default config
        config = load_config_from_file(config_file)
        assert isinstance(config, AppConfig)
    
    def test_save_config_to_file(self, temp_dir):
        """Test saving config to file (placeholder)."""
        config = AppConfig()
        config_file = temp_dir / "config.toml"
        
        # Currently does nothing but shouldn't crash
        save_config_to_file(config, config_file)


class TestXitError:
    """Test base XitError exception."""
    
    def test_xit_error_basic(self):
        """Test basic XitError creation."""
        error = XitError("Test error message")
        
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_xit_error_inheritance(self):
        """Test XitError inheritance."""
        error = XitError("Test")
        
        assert isinstance(error, Exception)
        assert isinstance(error, XitError)


class TestParseError:
    """Test ParseError exception."""
    
    def test_parse_error_basic(self):
        """Test basic ParseError creation."""
        error = ParseError("Parse failed")
        
        assert str(error) == "Parse failed"
        assert isinstance(error, XitError)
    
    def test_parse_error_with_file(self):
        """Test ParseError with file path."""
        error = ParseError("Parse failed", file_path="/test/file.xit")
        
        assert "Parse failed" in str(error)
        assert "/test/file.xit" in str(error)
    
    def test_parse_error_with_line(self):
        """Test ParseError with line number."""
        error = ParseError("Parse failed", file_path="/test/file.xit", line_number=42)
        
        error_str = str(error)
        assert "Parse failed" in error_str
        assert "/test/file.xit" in error_str
        assert "42" in error_str
    
    def test_parse_error_line_only(self):
        """Test ParseError with only line number."""
        error = ParseError("Parse failed", line_number=42)
        
        # Should include line number but handle missing file gracefully
        assert "Parse failed" in str(error)


class TestValidationError:
    """Test ValidationError exception."""
    
    def test_validation_error_basic(self):
        """Test basic ValidationError creation."""
        error = ValidationError("Validation failed")
        
        assert str(error) == "Validation failed"
        assert isinstance(error, XitError)


class TestFileNotSupportedError:
    """Test FileNotSupportedError exception."""
    
    def test_file_not_supported_error(self):
        """Test FileNotSupportedError creation."""
        supported = {'.xit', '.md'}
        error = FileNotSupportedError("/test/file.txt", supported)
        
        error_str = str(error)
        assert "/test/file.txt" in error_str
        assert "not supported" in error_str
        assert ".xit" in error_str
        assert ".md" in error_str
        assert isinstance(error, XitError)


class TestTaskFilterError:
    """Test TaskFilterError exception."""
    
    def test_task_filter_error_basic(self):
        """Test basic TaskFilterError creation."""
        error = TaskFilterError("Filter failed")
        
        assert str(error) == "Filter failed"
        assert isinstance(error, XitError)


class TestDateParseError:
    """Test DateParseError exception."""
    
    def test_date_parse_error_basic(self):
        """Test basic DateParseError creation."""
        error = DateParseError("invalid-date")
        
        error_str = str(error)
        assert "invalid-date" in error_str
        assert "Cannot parse date expression" in error_str
        assert isinstance(error, XitError)
    
    def test_date_parse_error_with_formats(self):
        """Test DateParseError with supported formats."""
        supported_formats = ["YYYY-MM-DD", "YYYY-MM", "YYYY"]
        error = DateParseError("invalid-date", supported_formats)
        
        error_str = str(error)
        assert "invalid-date" in error_str
        assert "YYYY-MM-DD" in error_str
        assert "Supported formats" in error_str
    
    def test_date_parse_error_many_formats(self):
        """Test DateParseError with many supported formats."""
        supported_formats = [f"format_{i}" for i in range(10)]
        error = DateParseError("invalid-date", supported_formats)
        
        error_str = str(error)
        assert "invalid-date" in error_str
        assert "..." in error_str  # Should truncate long lists


class TestExceptionIntegration:
    """Test exception integration with other components."""
    
    def test_exceptions_in_error_hierarchy(self):
        """Test that all exceptions inherit properly."""
        exceptions_to_test = [
            ParseError("test"),
            ValidationError("test"),
            FileNotSupportedError("/test.txt", {".xit"}),
            TaskFilterError("test"),
            DateParseError("test"),
        ]
        
        for exc in exceptions_to_test:
            assert isinstance(exc, XitError)
            assert isinstance(exc, Exception)
            assert str(exc)  # Should have string representation
    
    def test_exceptions_with_real_scenarios(self):
        """Test exceptions in realistic error scenarios."""
        # File not supported scenario
        try:
            raise FileNotSupportedError("data.csv", {".xit", ".md"})
        except XitError as e:
            assert "data.csv" in str(e)
            assert "xit" in str(e)
        
        # Parse error scenario
        try:
            raise ParseError("Invalid checkbox format", "tasks.xit", 15)
        except XitError as e:
            error_str = str(e)
            assert "Invalid checkbox format" in error_str
            assert "tasks.xit" in error_str
            assert "15" in error_str
        
        # Date parse error scenario
        try:
            raise DateParseError("32nd of January", ["YYYY-MM-DD", "MM/DD/YYYY"])
        except XitError as e:
            error_str = str(e)
            assert "32nd of January" in error_str
            assert "YYYY-MM-DD" in error_str