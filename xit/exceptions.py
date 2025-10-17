"""Custom exceptions for the xit task management tool.

This module defines specific exception types to provide better error handling
and more informative error messages throughout the application.
"""


class XitError(Exception):
    """Base exception for all xit-related errors."""
    pass


class ParseError(XitError):
    """Raised when parsing fails."""
    
    def __init__(self, message: str, file_path: str = None, line_number: int = None):
        """Initialize parse error.
        
        Args:
            message: Error description
            file_path: Path to the file where error occurred
            line_number: Line number where error occurred
        """
        self.file_path = file_path
        self.line_number = line_number
        
        if file_path and line_number:
            super().__init__(f"{message} (in {file_path}:{line_number})")
        elif file_path:
            super().__init__(f"{message} (in {file_path})")
        else:
            super().__init__(message)


class ValidationError(XitError):
    """Raised when data validation fails."""
    pass


class FileNotSupportedError(XitError):
    """Raised when trying to parse an unsupported file type."""
    
    def __init__(self, file_path: str, supported_extensions: set):
        """Initialize file not supported error.
        
        Args:
            file_path: Path to the unsupported file
            supported_extensions: Set of supported file extensions
        """
        super().__init__(
            f"File '{file_path}' is not supported. "
            f"Supported extensions: {', '.join(supported_extensions)}"
        )


class TaskFilterError(XitError):
    """Raised when task filtering fails."""
    pass


class DateParseError(XitError):
    """Raised when date parsing fails."""
    
    def __init__(self, date_expression: str, supported_formats: list = None):
        """Initialize date parse error.
        
        Args:
            date_expression: The expression that failed to parse
            supported_formats: List of supported formats (optional)
        """
        message = f"Cannot parse date expression: '{date_expression}'"
        if supported_formats:
            message += f". Supported formats: {', '.join(supported_formats[:5])}{'...' if len(supported_formats) > 5 else ''}"
        super().__init__(message)