"""
Custom exception classes for the adaptive trading system.
"""
from typing import Optional


class AdaptiveTradingSystemError(Exception):
    """Base exception class for all trading system related errors."""
    pass


class ConfigurationError(AdaptiveTradingSystemError):
    """Exception raised for errors in the configuration file."""
    
    def __init__(self, message: str, config_file: Optional[str] = None):
        self.config_file = config_file
        super().__init__(f"Configuration error{f' in {config_file}' if config_file else ''}: {message}") 