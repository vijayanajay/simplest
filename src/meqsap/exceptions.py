"""Custom exceptions for MEQSAP."""


class MEQSAPError(Exception):
    """Base exception for all MEQSAP application errors."""
    pass


class ConfigurationError(MEQSAPError):
    """Errors related to configuration loading, validation, or interpretation."""
    pass


class DataError(MEQSAPError):
    """Errors related to data acquisition, processing, or integrity."""
    pass


class BacktestError(MEQSAPError):
    """Errors related to backtest setup, signal generation, or execution."""
    pass


class ReportingError(MEQSAPError):
    """Errors related to report generation or presentation."""
    pass


class OptimizationError(MEQSAPError):
    """Errors related to the optimization process failing to find a valid result."""
    pass


class OptimizationInterrupted(MEQSAPError):
    """Raised when the optimization process is interrupted by the user."""
    pass


# CLI-specific exception hierarchy
class CLIError(MEQSAPError):
    """Base exception for CLI-specific errors."""
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
