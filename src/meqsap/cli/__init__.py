"""Enhanced CLI module for MEQSAP with comprehensive error handling and user experience features."""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

import typer
import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel

# Fix Windows console encoding issues
if sys.platform == "win32":
    # Set environment variable to force UTF-8 encoding for Rich on Windows
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    # Try to set console code page to UTF-8 if possible
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        pass  # Fallback gracefully if reconfigure is not available

# Core application modules
from .. import __version__
from ..backtest import BacktestAnalysisResult, run_complete_backtest
from ..config import StrategyConfig, load_yaml_config, validate_config, BaseStrategyParams
from ..data import DataError, fetch_market_data
from ..exceptions import (BacktestError, ConfigurationError, DataAcquisitionError,
                          BacktestExecutionError, ReportingError,
                          ReportGenerationError)
from ..reporting import generate_complete_report
from .commands import analyze, optimize_app
from .optimization_ui import (create_optimization_progress_bar,
                              create_progress_callback,
                              display_optimization_summary)
from .utils import handle_cli_errors, _generate_error_message, _get_recovery_suggestions

# Create the main app with proper command structure
app = typer.Typer(
    name="meqsap",
    help="MEQSAP - Market Equity Quantitative Strategy Analysis Platform\n\n"
         "A comprehensive tool for backtesting and analyzing quantitative trading strategies.",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)

# Global console instance - will be reconfigured based on CLI options
# Fix Windows Unicode encoding issues with Rich console
console = Console(force_terminal=True, width=120)

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

app.command("analyze")(analyze)


@app.command("version")
def version_command():
    """Display version information."""
    console.print(f"MEQSAP version: {__version__}")


app.add_typer(optimize_app, name="optimize")


def cli_main():
    """Main entry point for the CLI application."""
    app()


# This part is for when this file itself is run as a script,
# which is not the typical entry point for a Typer app defined in a package's __init__.py.
# The primary entry point is via `pyproject.toml`'s `[project.scripts]`
# or by `run.py` calling `cli_main()`.
# However, to make `python src/meqsap/cli/__init__.py` work for direct testing,
# we can add this guard.
if __name__ == "__main__":
    cli_main()


__all__ = [
    "app",
    "cli_main",
    "create_optimization_progress_bar",
    "create_progress_callback",
    "display_optimization_summary",
    "_generate_error_message",
    "_get_recovery_suggestions",
]
