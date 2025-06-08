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

# Core application modules
from .. import __version__
from ..backtest import BacktestAnalysisResult, run_complete_backtest
from ..config import StrategyConfig, load_yaml_config, validate_config, BaseStrategyParams
from ..data import DataError, fetch_market_data
from ..exceptions import (BacktestError, ConfigurationError, DataAcquisitionError,
                          BacktestExecutionError, ReportingError,
                          ReportGenerationError)
from ..reporting import generate_complete_report
from .commands import optimize_app
from .optimization_ui import (create_optimization_progress_bar,
                              create_progress_callback,
                              display_optimization_summary)
from .utils import handle_cli_errors

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
@handle_cli_errors
def analyze_command(
    config_file: Path = typer.Argument(
        ...,
        help="Path to strategy configuration YAML file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    report: bool = typer.Option(False, "--report", help="Generate PDF report after analysis."),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress most output."),
    validate_only: bool = typer.Option(False, "--validate-only", help="Validate configuration only, do not run backtest."),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        help="Directory to save reports and outputs.",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colored output."),
):
    """Analyze a trading strategy with MEQSAP using a YAML configuration file."""
    if verbose and quiet:
        raise ConfigurationError("--verbose and --quiet flags cannot be used together.")
    _configure_application_context(verbose=verbose, quiet=quiet, no_color=no_color)
    _main_pipeline(
        config_file,
        report=report,
        dry_run=validate_only,
        output_dir=output_dir,
        no_color=no_color,
        verbose=verbose,
        quiet=quiet,
    )


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
    config_file: Path, report: bool, dry_run: bool, output_dir: Optional[Path], no_color: bool, verbose: bool, quiet: bool
) -> None:
    start_time = time.time()
    # verbose and quiet are now passed directly from CLI flags
    config, strategy_params = _validate_and_load_config(config_file, verbose, quiet)
    if dry_run:
        _handle_dry_run_mode(config, quiet)
        return
    market_data = _handle_data_acquisition(config, verbose, quiet)
    analysis_result = _execute_backtest_pipeline(market_data, config, strategy_params, verbose, quiet)
    _generate_output(analysis_result, config, report, output_dir, quiet, no_color, verbose)


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


def _handle_dry_run_mode(config: StrategyConfig, quiet: bool) -> None:
    if not quiet:
        console.print("\n[bold blue]Dry-run mode - Configuration validation only[/bold blue]")
        operations_table = Table(title="Planned Operations", show_header=True, header_style="bold magenta")
        operations_table.add_column("Operation")
        operations_table.add_row("Validate configuration")
        operations_table.add_row("Acquire market data")
        operations_table.add_row("Run backtest")
        operations_table.add_row("Generate report (optional)")
        console.print(operations_table)
        console.print("\n[green]OK: Configuration is valid. Ready for execution.[/green]")
        console.print("[dim]Use without --dry-run to execute the backtest.[/dim]")


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
        if output_dir:
            # Path is already resolved by Typer if provided
            output_directory_str = str(output_dir)
            output_dir_path = output_dir
        else:
            # Default to a resolved path in the current directory
            output_dir_path = Path("./reports").resolve()
            output_directory_str = str(output_dir_path)
        # Ensure the output directory exists
        output_dir_path.mkdir(parents=True, exist_ok=True)
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
