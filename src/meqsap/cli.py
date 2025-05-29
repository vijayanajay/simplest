"""
Command-line interface for MEQSAP.

This module provides the CLI entry points for the application.
"""

from typing import Optional
import sys
from pathlib import Path

import typer
from rich import print as rich_print
from rich.panel import Panel
from rich.console import Console

from meqsap import __version__
from meqsap.config import load_yaml_config, validate_config, ConfigError


app = typer.Typer(
    name="meqsap",
    help="Market Equity Quantitative Strategy Analysis Platform",
    add_completion=False,
)

console = Console()


@app.command("analyze")
def analyze_config(
    config_file: Path = typer.Argument(
        ..., help="Path to the YAML configuration file", exists=True, readable=True
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """Analyze a trading strategy using the provided configuration."""
    try:
        console.print(f"Loading configuration from [bold]{config_file}[/bold]...")
        config_data = load_yaml_config(str(config_file))
        
        console.print("Validating configuration...")
        config = validate_config(config_data)
        
        # Validate the strategy-specific parameters
        strategy_params = config.validate_strategy_params()
        
        # Show success message
        rich_print(Panel(
            f"[bold green]Configuration valid![/bold green]\n\n"
            f"Strategy: [bold]{config.strategy_type}[/bold]\n"
            f"Ticker: [bold]{config.ticker}[/bold]\n"
            f"Date Range: [bold]{config.start_date}[/bold] to [bold]{config.end_date}[/bold]",
            title="MEQSAP Analysis",
            expand=False
        ))
        
        # Show additional details in verbose mode
        if verbose:
            console.print("\n[bold]Strategy Parameters:[/bold]")
            for key, value in strategy_params.model_dump().items():
                console.print(f"  [bold]{key}[/bold]: {value}")
        
    except ConfigError as e:
        rich_print(f"[bold red]Configuration Error:[/bold red] {str(e)}")
        sys.exit(1)
    except Exception as e:
        rich_print(f"[bold red]Unexpected Error:[/bold red] {str(e)}")
        sys.exit(1)


@app.command("version")
def version():
    """Show the version of MEQSAP."""
    rich_print(f"MEQSAP version: [bold]{__version__}[/bold]")


if __name__ == "__main__":
    app()
