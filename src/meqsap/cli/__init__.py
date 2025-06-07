"""Enhanced CLI module for MEQSAP with comprehensive error handling and user experience features."""

import logging
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Optional

import pandas as pd
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import (Progress, SpinnerColumn, TextColumn,
                           TimeElapsedColumn)
from rich.table import Table

# Core application modules
from .. import __version__
from ..backtest import BacktestAnalysisResult, run_complete_backtest
from ..config import StrategyConfig, load_yaml_config, validate_config, BaseStrategyParams
from ..data import fetch_market_data
from ..exceptions import (MEQSAPError, ConfigurationError, DataError,
                          DataAcquisitionError, BacktestError,
                          BacktestExecutionError, ReportingError,
                          ReportGenerationError)
from ..reporting import generate_complete_report
from .commands import optimize_app
from .optimization_ui import (
    create_optimization_progress_bar,
    create_progress_callback,
    display_optimization_summary,
)

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
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


@app.command("analyze")
def analyze_command(
    config_file: Path = typer.Argument(
        ...,
        help="Path to the YAML configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
    ),
    validate_only: bool = typer.Option(
        False,
        "--validate-only",
        help="Only validate the configuration, don't run backtest",
    ),
    report: bool = typer.Option(
        False,
        "--report",
        help="Generate PDF report after analysis",
    ),
    output_dir: Optional[Path] = typer.Option(
        "./reports",
        "--output-dir",
        help="Directory for output reports",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output with detailed logging and diagnostics",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress non-essential output (minimal output mode)",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable colored output",
    ),
) -> None:
    """
    Analyze a trading strategy with MEQSAP using a YAML configuration file.

    This command loads the configuration, fetches market data, runs a backtest,
    and generates comprehensive analysis reports for the MEQSAP platform.

    Examples:
        meqsap analyze config.yaml
        meqsap analyze config.yaml --report --verbose
        meqsap analyze config.yaml --validate-only
        meqsap analyze config.yaml --output-dir ./custom_reports --report
    """
    if verbose and quiet:
        console.print("[bold red]Error:[/bold red] --verbose and --quiet flags cannot be used together")
        raise typer.Exit(code=1)

    _configure_application_context(verbose=verbose, quiet=quiet, no_color=no_color)

    exit_code = _main_pipeline(
        config_file=config_file,
        report=report,
        verbose=verbose,
        quiet=quiet,
        dry_run=validate_only,
        output_dir=output_dir,
        no_color=no_color,
    )

    if exit_code != 0:
        # _main_pipeline already prints the error, so we just exit.
        raise typer.Exit(code=exit_code)


def _configure_application_context(verbose: bool, quiet: bool, no_color: bool) -> None:
    global console
    if no_color:
        console = Console(color_system=None)
    else:
        console = Console()

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("src.meqsap").setLevel(logging.DEBUG) # Ensure our package's logger is also DEBUG
    elif quiet:
        logging.getLogger().setLevel(logging.ERROR)
    else:
        logging.getLogger().setLevel(logging.INFO)


def _main_pipeline(
    config_file: Path, report: bool, verbose: bool, quiet: bool,
    dry_run: bool, output_dir: Optional[Path], no_color: bool,
) -> int:
    start_time = time.time()
    try:
        config, strategy_params = _validate_and_load_config(config_file, verbose, quiet)
        if dry_run:
            return _handle_dry_run_mode(config, quiet)
        market_data = _handle_data_acquisition(config, verbose, quiet)
        analysis_result = _execute_backtest_pipeline(market_data, config, strategy_params, verbose, quiet)
        _generate_output(analysis_result, config, report, output_dir, quiet, no_color, verbose)
        if not quiet:
            elapsed_time = time.time() - start_time
            console.print(f"\n[bold green]OK: MEQSAP analysis completed successfully in {elapsed_time:.2f} seconds[/bold green]")
        return 0
    except ConfigurationError as e:
        error_msg = _generate_error_message(e, verbose=verbose, no_color=no_color)
        console.print(error_msg)
        return 1
    except DataAcquisitionError as e:
        error_msg = _generate_error_message(e, verbose=verbose, no_color=no_color)
        console.print(error_msg)
        return 2
    except BacktestExecutionError as e:
        error_msg = _generate_error_message(e, verbose=verbose, no_color=no_color)
        console.print(error_msg)
        return 3
    except ReportGenerationError as e:
        error_msg = _generate_error_message(e, verbose=verbose, no_color=no_color)
        console.print(error_msg)
        return 4
    except Exception as e:
        logging.exception("An unexpected error occurred in main pipeline")
        error_msg = _generate_error_message(e, verbose=verbose, no_color=no_color)
        console.print(error_msg)
        return 10


def _validate_and_load_config(config_file: Path, verbose: bool, quiet: bool) -> tuple[StrategyConfig, BaseStrategyParams]:
    if not quiet:
        console.print(f"Loading configuration from: [cyan]{config_file}[/cyan]")
    try:
        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_file}")
        if config_file.suffix.lower() not in [".yaml", ".yml"]:
            raise ConfigurationError(f"Configuration file must have a .yaml or .yml extension, but got: {config_file.suffix}")
        config = load_yaml_config(config_file)
        config = validate_config(config)
        strategy_params = config.validate_strategy_params()
        
        if not quiet:
            console.print(Panel(f"[bold green]OK: Configuration valid![/bold green]\n\nStrategy: [bold]{config.strategy_type}[/bold]\nTicker: [bold]{config.ticker}[/bold]\nDate Range: [bold]{config.start_date}[/bold] to [bold]{config.end_date}[/bold]", title="MEQSAP Configuration", expand=False, border_style="green"))
        if verbose and not quiet:
            console.print("\n[bold underline]Strategy Parameters:[/bold underline]")
            for key, value in strategy_params.model_dump().items():
                console.print(f"  [cyan]{key.replace('_', ' ').title()}[/cyan]: {value}")
        return config, strategy_params
    except Exception as e:
        raise ConfigurationError(f"Failed to load or validate configuration: {e}")


def _handle_dry_run_mode(config: StrategyConfig, quiet: bool) -> int:
    if not quiet:
        console.print("\n[bold blue]Dry-run mode - Configuration validation only[/bold blue]")
        operations_table = Table(title="Planned Operations", show_header=True, header_style="bold magenta")
        operations_table.add_column("Operation", style="cyan")
        operations_table.add_column("Details", style="white")
        operations_table.add_row("Data Acquisition", "Fetch market data for ticker")
        operations_table.add_row("Backtesting", "Run complete backtest with vibe checks")
        operations_table.add_row("Output", "Generate terminal report")
        console.print(operations_table)
        console.print("\n[green]OK: Configuration is valid. Ready for execution.[/green]")
        console.print("[dim]Use without --dry-run to execute the backtest.[/dim]")
    return 0


def _handle_data_acquisition(config: StrategyConfig, verbose: bool, quiet: bool) -> pd.DataFrame:
    try:
        if not quiet:
            console.print(f"\nFetching market data for [bold cyan]{config.ticker}[/bold cyan] from [bold]{config.start_date}[/bold] to [bold]{config.end_date}[/bold]...")
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, disable=quiet) as progress:
            task = progress.add_task("Downloading market data...", total=None)
            market_data = fetch_market_data(config.ticker, config.start_date, config.end_date)
            progress.update(task, completed=100)
        if not quiet:
            console.print(f"[green]OK:[/green] Market data received: [bold]{len(market_data)}[/bold] bars")
            if verbose:
                console.print("\n[bold underline]Data Sample (first 3 rows):[/bold underline]")
                console.print(market_data.head(3))
        return market_data
    except DataError as e:
        raise DataAcquisitionError(f"Failed to acquire market data: {e}")
    except Exception as e:
        raise DataAcquisitionError(f"Unexpected error during data acquisition: {e}")


def _execute_backtest_pipeline(data: pd.DataFrame, config: StrategyConfig, strategy_params: BaseStrategyParams, verbose: bool, quiet: bool) -> BacktestAnalysisResult:
    try:
        if not quiet:
            console.print("\nRunning backtest analysis...")
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), TimeElapsedColumn(), console=console, disable=quiet) as progress:
            task = progress.add_task("Executing backtest and analysis...", total=None)
            analysis_result = run_complete_backtest(config, data, strategy_params)
            progress.update(task, completed=100)
        if not quiet:
            console.print("[green]OK:[/green] Backtest analysis complete")
        return analysis_result
    except BacktestError as e:
        raise BacktestExecutionError(f"Backtest execution failed: {e}")
    except Exception as e:
        raise BacktestExecutionError(f"Unexpected error during backtest execution: {e}")


def _generate_output(analysis_result: BacktestAnalysisResult, config: StrategyConfig, report: bool, output_dir: Optional[Path], quiet: bool, no_color: bool, verbose: bool = False) -> None:
    try:
        output_directory_str = str(output_dir) if output_dir else "./reports"
        if not quiet:
            if report:
                console.print(f"\nGenerating reports (PDF: Yes, Output Dir: [cyan]{output_directory_str}[/cyan])...")
            else:
                console.print("\nGenerating terminal report...")
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, disable=quiet) as progress:
            task = progress.add_task("Generating reports...", total=None)
            pdf_path = generate_complete_report(analysis_result=analysis_result, include_pdf=report, output_directory=output_directory_str, no_color=no_color, quiet=quiet)
            progress.update(task, completed=100)
        if report and pdf_path and not quiet:
            resolved_pdf_path = Path(pdf_path).resolve()
            console.print(f"[green]OK:[/green] PDF report generated: [link=file://{resolved_pdf_path}]{resolved_pdf_path}[/link]")
        elif report and not pdf_path and not quiet:
            console.print("[yellow]WARN:[/yellow] PDF report was requested but generation failed (check logs)")
        if verbose and not quiet:
            console.print("\n[bold underline]Trade Details (first 5):[/bold underline]")
            _display_trade_details(analysis_result)
    except ReportingError as e:
        raise ReportGenerationError(f"Report generation failed: {e}")
    except Exception as e:
        raise ReportGenerationError(f"Unexpected error during report generation: {e}")


def _display_trade_details(analysis_result: BacktestAnalysisResult) -> None:
    primary_result = analysis_result.primary_result
    if primary_result and primary_result.total_trades > 0:
        for i, trade in enumerate(primary_result.trade_details[:5]):
            console.print(f"  Trade {i+1}: {trade}")
        if len(primary_result.trade_details) > 5:
            console.print(f"  ... and {len(primary_result.trade_details) - 5} more trades not shown.")
        console.print()
    elif primary_result and primary_result.total_trades == 0: # noqa: E721
        console.print("\n[yellow]WARN: No trades were executed during the backtest.[/yellow]")


def _generate_error_message(exception: Exception, verbose: bool = False, no_color: bool = False) -> str:
    error_type = type(exception).__name__
    error_msg = str(exception)
    if no_color:
        message_parts = [f"{error_type}: {error_msg}"]
    else:
        message_parts = [f"[bold red]{error_type}:[/bold red] {error_msg}"]
    suggestions = _get_recovery_suggestions(exception)
    if suggestions:
        message_parts.append("\n[bold yellow]Suggested Solutions:[/bold yellow]")
        for suggestion in suggestions:
            message_parts.append(f"  • {suggestion}")
    if verbose:
        message_parts.append("\n[bold underline]Debug Information:[/bold underline]")
        if no_color:
            message_parts.append(traceback.format_exc())
        else:
            message_parts.append(f"[dim]{traceback.format_exc()}[/dim]")
    return "\n".join(message_parts)


def _get_recovery_suggestions(exception: Exception) -> list[str]:
    suggestions = []
    if isinstance(exception, ConfigurationError):
        suggestions.extend(["Verify the YAML file syntax is correct", "Check that all required fields are present", "Ensure date ranges are valid (start < end, not in future)", "Validate ticker symbol format", "Try using --dry-run to validate configuration without execution", "Check examples in documentation for proper YAML structure"])
    elif isinstance(exception, DataAcquisitionError):
        suggestions.extend(["Check your internet connection", "Verify the ticker symbol exists and is correctly spelled", "Try a different date range (some tickers have limited historical data)", "Wait a moment and try again (rate limiting)", "Check if yfinance service is experiencing issues", "Try using a more common ticker symbol to test connectivity"])
    elif isinstance(exception, BacktestExecutionError):
        suggestions.extend(["Verify your strategy parameters are reasonable", "Check that your data has sufficient history for the strategy", "Ensure moving average periods are less than data length", "Try reducing the complexity of your strategy parameters", "Check for data quality issues in your date range", "Consider using --verbose for more detailed error information"])
    elif isinstance(exception, ReportGenerationError):
        suggestions.extend(["Check that the output directory exists and is writable", "Ensure you have sufficient disk space", "Try running without --report flag to skip PDF generation", "Verify all required dependencies for PDF generation are installed", "Check file permissions in the output directory", "Try specifying a different output directory with --output-dir"])
    else:
        suggestions.extend(["Try running with --verbose for more details", "Check the documentation for troubleshooting guides", "Verify all dependencies are properly installed", "Try running --version to check dependency status", "Consider using --dry-run to isolate configuration issues", "Check if this is a known issue in the project documentation"])
    return suggestions


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
]
