"""Configuration management for the xit task management tool.

This module provides centralized configuration handling, making the application
more maintainable and allowing for future customization options.
"""

from dataclasses import dataclass
from typing import Set, Dict, List
from pathlib import Path
import os


@dataclass
class ParsingConfig:
    """Configuration for file parsing behavior."""
    supported_extensions: Set[str] = None
    continuation_indent: int = 4
    max_file_size_mb: int = 10
    encoding: str = 'utf-8'
    
    def __post_init__(self):
        if self.supported_extensions is None:
            self.supported_extensions = {'.md', '.xit'}


@dataclass
class DisplayConfig:
    """Configuration for display formatting."""
    status_colors: Dict[str, str] = None
    max_description_length: int = 200
    show_file_headers: bool = True
    group_by_file: bool = True
    
    def __post_init__(self):
        if self.status_colors is None:
            self.status_colors = {
                'OPEN': 'white',
                'DONE': 'green',
                'ONGOING': 'yellow',
                'OBSOLETE': 'red',
                'INQUESTION': 'magenta'
            }


@dataclass
class DateConfig:
    """Configuration for date parsing and handling."""
    natural_keywords: Dict[str, int] = None
    supported_formats: List[str] = None
    
    def __post_init__(self):
        if self.natural_keywords is None:
            self.natural_keywords = {
                'today': 0,
                'tomorrow': 1,
                'yesterday': -1,
            }
        
        if self.supported_formats is None:
            self.supported_formats = [
                r'^\d{4}-\d{2}-\d{2}$',  # 2025-12-31
                r'^\d{4}-\d{2}$',        # 2025-12
                r'^\d{4}$',              # 2025
                r'^\d{4}-W\d{2}$',       # 2025-W42
                r'^\d{4}-Q[1-4]$',       # 2025-Q4
                r'^\d{4}/\d{2}/\d{2}$',  # 2025/12/31
                r'^\d{4}/W\d{2}$',       # 2025/W42
            ]


@dataclass
class AppConfig:
    """Main application configuration."""
    parsing: ParsingConfig = None
    display: DisplayConfig = None
    date: DateConfig = None
    
    # Application metadata
    app_name: str = "xit"
    version: str = "0.1.0"
    config_dir: Path = None
    
    def __post_init__(self):
        if self.parsing is None:
            self.parsing = ParsingConfig()
        if self.display is None:
            self.display = DisplayConfig()
        if self.date is None:
            self.date = DateConfig()
        if self.config_dir is None:
            self.config_dir = Path.home() / f".{self.app_name}"


# Global configuration instance
_config = None


def get_config() -> AppConfig:
    """Get the global configuration instance.
    
    Returns:
        Global AppConfig instance
    """
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def load_config_from_file(config_path: Path) -> AppConfig:
    """Load configuration from a file (future enhancement).
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Loaded configuration
    """
    # TODO: Implement TOML/YAML config file loading
    return AppConfig()


def save_config_to_file(config: AppConfig, config_path: Path) -> None:
    """Save configuration to a file (future enhancement).
    
    Args:
        config: Configuration to save
        config_path: Path to save configuration to
    """
    # TODO: Implement config file saving
    pass