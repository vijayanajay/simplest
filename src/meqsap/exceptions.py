"""Custom exceptions for MEQSAP."""


class MEQSAPError(Exception):
    """Base exception for MEQSAP errors."""
    pass


class ConfigError(MEQSAPError):
    """Configuration-related errors."""
    pass


class DataError(MEQSAPError):
    """Data fetching and processing errors."""
    pass


class BacktestError(MEQSAPError):
    """Backtest execution errors."""
    pass


class ReportingError(MEQSAPError):
    """Report generation errors."""
    pass


# CLI-specific exception hierarchy
class CLIError(MEQSAPError):
    """Base exception for CLI-specific errors."""
    pass


class ConfigurationError(CLIError):
    """Raised when configuration file has errors."""
    pass


class DataAcquisitionError(CLIError):
    """Raised when data download or processing fails."""
    pass


class BacktestExecutionError(CLIError):
    """Raised when backtest computation fails."""
    pass


class ReportGenerationError(CLIError):
    """Raised when report generation encounters errors."""
    pass
