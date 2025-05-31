from typing import Optional
from pathlib import Path
import traceback # Import traceback for verbose error reporting

import typer
from rich import print as rich_print
from rich.panel import Panel
from rich.console import Console

# Core application modules - import actual functions
from src.meqsap import __version__
from src.meqsap.config import (
    load_yaml_config,
    validate_config,
    ConfigError,
    StrategyConfig, # Import for type hinting if needed, though validate_config returns it
)
from src.meqsap.data import fetch_market_data, DataError
from src.meqsap.backtest import run_complete_backtest, BacktestError, BacktestAnalysisResult
from src.meqsap.reporting import generate_complete_report, ReportingError
from src.meqsap.exceptions import MEQSAPError # Generic MEQSAP Error


# Create the main Typer app
app = typer.Typer(
    name="meqsap",
    help="MEQSAP - Market Equity Quantitative Strategy Analysis Platform",
    no_args_is_help=True,
    add_completion=False, # Typically disabled for simpler CLIs or testing
)

# Global console instance
console = Console()


@app.command("analyze")
def analyze_command(
    config_file: Path = typer.Argument(
        ...,
        help="Path to the YAML configuration file.",
        exists=True, # Typer checks if this file exists
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True, # Resolves to absolute path, good practice
    ),
    validate_only: bool = typer.Option(
        False, "--validate-only", help="Only validate configuration without running backtest."
    ),
    report: bool = typer.Option(False, "--report", help="Generate PDF report."),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        help="Directory for output files. Defaults to './reports'.",
        file_okay=False, # Must be a directory
        dir_okay=True,
        # writable=True, # Removed: check writability in reporting module or when creating dir
        resolve_path=True, # Resolve path if provided
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress non-essential output."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colored output."),
) -> None:
    """
    Analyze a trading strategy using a YAML configuration file.
    This command loads the configuration, fetches market data,
    runs a backtest, and generates a report.
    """
    # Configure console based on no_color flag
    # This affects the global `console` instance if it's used by other modules implicitly,
    # or we'd need to pass a configured Console object around.
    # For now, generate_complete_report takes no_color.
    # If other prints here need to respect it, they should check `no_color`.
    global console
    if no_color:
        console = Console(color_system=None)


    try:
        # Step 1: Load and validate configuration
        if not quiet:
            console.print(f"Loading configuration from: [cyan]{config_file}[/cyan]")
        
        config_data = load_yaml_config(str(config_file)) 
        config: StrategyConfig = validate_config(config_data) 
        strategy_params = config.validate_strategy_params()

        if not quiet:
            rich_print(
                Panel(
                    f"[bold green]Configuration valid![/bold green]\n\n"
                    f"Strategy: [bold]{config.strategy_type}[/bold]\n"
                    f"Ticker: [bold]{config.ticker}[/bold]\n"
                    f"Date Range: [bold]{config.start_date}[/bold] to [bold]{config.end_date}[/bold]",
                    title="📊 MEQSAP Analysis Configuration",
                    expand=False,
                    border_style="blue"
                )
            )

        if verbose and not quiet:
            console.print("\n[bold underline]Strategy Parameters:[/bold underline]")
            for key, value in strategy_params.model_dump().items(): # Use model_dump for Pydantic v2
                console.print(f"  [bold cyan]{key.replace('_', ' ').title()}[/bold cyan]: {value}")
            console.print("-" * 30)

        if validate_only:
            if not quiet:
                console.print("[green]Configuration validation successful. Exiting as --validate-only was specified.[/green]")
            # For validate_only, a successful validation should be exit code 0.
            # No explicit typer.Exit(0) is needed if the function completes normally.
            return 

        # Step 2: Fetch market data
        if not quiet:
            console.print(f"\nFetching market data for [bold cyan]{config.ticker}[/bold cyan] from [bold]{config.start_date}[/bold] to [bold]{config.end_date}[/bold]...")
        
        market_data = fetch_market_data(config.ticker, config.start_date, config.end_date)
        
        if not quiet:
            console.print(f"[green]✓[/green] Market data received: {len(market_data)} bars.")
            if verbose:
                console.print("[bold underline]Data Sample (first 3 rows):[/bold underline]")
                console.print(market_data.head(3))
                console.print("-" * 30)

        # Step 3: Run complete backtest analysis
        if not quiet:
            console.print("\nRunning backtest analysis...")
            with console.status("[bold blue]Executing backtest and analysis...[/bold blue]", spinner="dots"):
                analysis_result: BacktestAnalysisResult = run_complete_backtest(config, market_data)
            console.print("[green]✓[/green] Backtest analysis complete.")
        else:
            analysis_result: BacktestAnalysisResult = run_complete_backtest(config, market_data)
        
        # Step 4: Generate reports
        output_directory_str = str(output_dir) if output_dir else "./reports"

        if not quiet:
            console.print(f"\nGenerating report (PDF: {'Yes' if report else 'No'}, Output Dir: [cyan]{output_directory_str}[/cyan])...")
        
        pdf_path = generate_complete_report(
            analysis_result=analysis_result,
            include_pdf=report,
            output_directory=output_directory_str,
            no_color=no_color,
            quiet=quiet, 
        )

        if report and pdf_path and not quiet:
            resolved_pdf_path = Path(pdf_path).resolve()
            console.print(f"[green]✓[/green] PDF report generated: [link=file://{resolved_pdf_path}]{resolved_pdf_path}[/link]")
        elif report and not pdf_path and not quiet:
            console.print("[yellow]PDF report generation was requested but no path was returned (check logs).[/yellow]")

        # Step 5: Show trade details in verbose mode (if not quiet)
        if verbose and not quiet:
            primary_result = analysis_result.primary_result
            if primary_result and primary_result.total_trades > 0 and hasattr(primary_result, 'trade_details') and primary_result.trade_details:
                console.print("\n[bold underline]Trade Details (first 5):[/bold underline]")
                for i, trade_detail in enumerate(primary_result.trade_details[:5]):
                    console.print(
                        f"  [bold]Trade {i+1}:[/bold] "
                        f"Entry: {trade_detail.get('entry_date', 'N/A')} @ ${trade_detail.get('entry_price', 0.0):.2f}, "
                        f"Exit: {trade_detail.get('exit_date', 'N/A')} @ ${trade_detail.get('exit_price', 0.0):.2f}, "
                        f"PnL: ${trade_detail.get('pnl', 0.0):.2f} ({trade_detail.get('return_pct', 0.0):.2f}%)"
                    )
                if len(primary_result.trade_details) > 5:
                    console.print(f"  ... and {len(primary_result.trade_details) - 5} more trades not shown.")
                console.print("-" * 30)
            elif primary_result and primary_result.total_trades == 0 and not quiet:
                console.print("\n[yellow]No trades were executed during the backtest.[/yellow]")

    except MEQSAPError as e: # Catch specific MEQSAP errors first
        console.print(f"[bold red]{type(e).__name__}:[/bold red] {e}")
        if verbose:
            console.print_exception(show_locals=True)
        raise typer.Exit(code=1) # All MEQSAP specific errors result in exit code 1
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")
        if verbose:
            console.print_exception(show_locals=True) 
        else:
            console.print("Run with --verbose for more details.")
        raise typer.Exit(code=1) # Unexpected errors also exit with 1

    if not quiet:
        console.print("\n[bold green]MEQSAP analysis finished successfully.[/bold green]")
    # If successful and not validate_only, implicit exit code 0


@app.command()
def version():
    """
    Show the version of MEQSAP and its key dependencies.
    """
    rich_print(f"MEQSAP version: [bold cyan]{__version__}[/bold cyan]")
    # Example of showing other versions:
    # try:
    #     import pandas as pd
    #     import vectorbt as vbt
    #     rich_print(f"  Pandas version: {pd.__version__}")
    #     rich_print(f"  VectorBT version: {vbt.__version__}")
    # except ImportError:
    #     pass


def main():
    """
    Main entry point for the CLI application.
    This function is called when the script is executed.
    """
    app()


if __name__ == "__main__":
    main()