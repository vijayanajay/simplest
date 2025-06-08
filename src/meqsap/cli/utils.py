"""
CLI utility functions, including a reusable error handling decorator.
"""

import functools
import logging
import traceback
from typing import Any

import typer
from rich.console import Console

from ..exceptions import (
    BacktestError,
    BacktestExecutionError,
    ConfigurationError,
    DataAcquisitionError,
    DataError,
    ReportGenerationError,
    ReportingError,
)

logger = logging.getLogger(__name__)


def _get_recovery_suggestions(exception: Exception) -> list[str]:
    suggestions = []
    if isinstance(exception, ConfigurationError):
        suggestions.extend(["Verify the YAML file syntax is correct", "Check that all required fields are present", "Ensure date ranges are valid (start < end, not in future)", "Validate ticker symbol format", "Try using --validate-only to validate configuration without execution", "Check examples in documentation for proper YAML structure"])
    elif isinstance(exception, (DataError, DataAcquisitionError)):
        suggestions.extend(["Check your internet connection", "Verify the ticker symbol exists and is correctly spelled", "Try a different date range (some tickers have limited historical data)", "Wait a moment and try again (rate limiting)", "Check if yfinance service is experiencing issues", "Try using a more common ticker symbol to test connectivity"])
    elif isinstance(exception, (BacktestError, BacktestExecutionError)):
        suggestions.extend(["Verify your strategy parameters are reasonable", "Check that your data has sufficient history for the strategy", "Ensure moving average periods are less than data length", "Try reducing the complexity of your strategy parameters", "Check for data quality issues in your date range", "Consider using --verbose for more detailed error information"])
    elif isinstance(exception, (ReportingError, ReportGenerationError)):
        suggestions.extend(["Check that the output directory exists and is writable", "Ensure you have sufficient disk space", "Try running without --report flag to skip PDF generation", "Verify all required dependencies for PDF generation are installed", "Check file permissions in the output directory", "Try specifying a different output directory with --output-dir"])
    else:
        suggestions.extend(["Try running with --verbose for more details", "Check the documentation for troubleshooting guides", "Verify all dependencies are properly installed", "Try running --version to check dependency status", "Consider using --dry-run to isolate configuration issues", "Check if this is a known issue in the project documentation"])
    return suggestions


def _generate_error_message(exception: Exception, verbose: bool = False, no_color: bool = False) -> str:
    error_type = type(exception).__name__
    error_msg = str(exception)
    if no_color:
        message_parts = [f"{error_type}: {error_msg}"]
    else:
        message_parts = [f"[bold red]{error_type}:[/bold red] {error_msg}"]
    suggestions = _get_recovery_suggestions(exception)
    if suggestions:
        if no_color:
            message_parts.append("\nSuggested Solutions:")
        else:
            message_parts.append("\n[bold yellow]Suggested Solutions:[/bold yellow]")
        for suggestion in suggestions:
            message_parts.append(f"  • {suggestion}")
    if verbose:
        if no_color:
            message_parts.append("\nDebug Information:")
            message_parts.append(traceback.format_exc())
        else:
            message_parts.append("\n[bold underline]Debug Information:[/bold underline]")
            message_parts.append(f"[dim]{traceback.format_exc()}[/dim]")
    return "\n".join(message_parts)


def handle_cli_errors(func: Any) -> Any:
    """
    A decorator to wrap CLI commands with standard error handling.

    This decorator catches MEQSAPError subclasses and other exceptions,
    logs them, prints a user-friendly error message, and exits with the
    appropriate error code as defined in ADR-004.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        verbose = kwargs.get("verbose", False)
        no_color = kwargs.get("no_color", False)
        
        console = Console(color_system=None if no_color else "auto")

        try:
            return func(*args, **kwargs)
        except ConfigurationError as e:
            exit_code = 1
            logger.error(f"{type(e).__name__}: {e}", exc_info=verbose)
            error_msg = _generate_error_message(e, verbose=verbose, no_color=no_color)
            console.print(error_msg)
            raise typer.Exit(code=exit_code)
        except (DataError, DataAcquisitionError) as e:
            exit_code = 2
            logger.error(f"{type(e).__name__}: {e}", exc_info=verbose)
            error_msg = _generate_error_message(e, verbose=verbose, no_color=no_color)
            console.print(error_msg)
            raise typer.Exit(code=exit_code)
        except (BacktestError, BacktestExecutionError) as e:
            exit_code = 3
            logger.error(f"{type(e).__name__}: {e}", exc_info=verbose)
            error_msg = _generate_error_message(e, verbose=verbose, no_color=no_color)
            console.print(error_msg)
            raise typer.Exit(code=exit_code)
        except (ReportingError, ReportGenerationError) as e:
            exit_code = 4
            logger.error(f"{type(e).__name__}: {e}", exc_info=verbose)
            error_msg = _generate_error_message(e, verbose=verbose, no_color=no_color)
            console.print(error_msg)
            raise typer.Exit(code=exit_code)
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=verbose)
            error_msg = _generate_error_message(e, verbose=verbose, no_color=no_color)
            console.print(error_msg)
            raise typer.Exit(code=10)

    return wrapper
