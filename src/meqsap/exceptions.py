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
