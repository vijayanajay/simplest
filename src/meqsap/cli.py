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

from src.meqsap import __version__
from src.meqsap.config import load_yaml_config, validate_config, ConfigError
from src.meqsap.data import fetch_market_data, DataError
from src.meqsap.backtest import run_complete_backtest, BacktestError


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
    skip_backtest: bool = typer.Option(False, "--validate-only", help="Only validate the configuration without running backtest"),
):
    """Analyze a trading strategy using the provided configuration."""
    try:
        console.print(f"Loading configuration from [bold]{config_file}[/bold]...")
        config_data = load_yaml_config(str(config_file))
        
        console.print("Validating configuration...")
        config = validate_config(config_data)
        
        # Validate the strategy-specific parameters
        strategy_params = config.validate_strategy_params()
        
        # Show configuration summary
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
        
        if skip_backtest:
            return
        
        # Fetch market data
        console.print(f"\nFetching market data for [bold]{config.ticker}[/bold]...")
        market_data = fetch_market_data(config.ticker, config.start_date, config.end_date)
        console.print(f"[green]✓[/green] Data received: {len(market_data)} bars")
          # Run backtest
        with console.status("[bold blue]Running backtest analysis...[/bold blue]"):
            backtest_result = run_complete_backtest(config, market_data)
        
        # Display primary results
        primary = backtest_result.primary_result
        
        rich_print(Panel(
            f"[bold green]Backtest Results for {config.ticker}[/bold green]\n\n"
            f"Total Return: [bold]{primary.total_return:.2f}%[/bold]\n"
            f"Annualized Return: [bold]{primary.annualized_return:.2f}%[/bold]\n"
            f"Sharpe Ratio: [bold]{primary.sharpe_ratio:.2f}[/bold]\n"
            f"Max Drawdown: [bold]{primary.max_drawdown:.2f}%[/bold]\n"
            f"Total Trades: [bold]{primary.total_trades}[/bold]\n"
            f"Win Rate: [bold]{primary.win_rate:.2f}%[/bold]\n",
            title="Performance Metrics",
            expand=False
        ))
        
        # Display vibe check results
        vibe = backtest_result.vibe_checks
        vibe_status = "[green]PASS[/green]" if vibe.overall_pass else "[red]FAIL[/red]"
        
        rich_print(Panel(
            f"Strategy Vibe Check: {vibe_status}\n\n" +
            "\n".join(vibe.check_messages),
            title="Vibe Check",
            expand=False
        ))
        
        # Display robustness results
        robust = backtest_result.robustness_checks
        
        rich_print(Panel(
            f"Sharpe Ratio Degradation with High Fees: [bold]{robust.sharpe_degradation:.2f}%[/bold]\n"
            f"Turnover Rate: [bold]{robust.turnover_rate:.2f}%[/bold]\n\n"
            "[bold]Recommendations:[/bold]\n" +
            "\n".join([f"  • {rec}" for rec in robust.recommendations]),
            title="Robustness Analysis",
            expand=False
        ))
        
        # Show trade details in verbose mode
        if verbose and primary.total_trades > 0:
            console.print("\n[bold]Trade Details:[/bold]")
            for i, trade in enumerate(primary.trade_details[:5]):  # Show only first 5 trades
                console.print(
                    f"  [bold]Trade {i+1}:[/bold] Entry: {trade['entry_date']} @ ${trade['entry_price']:.2f}, "
                    f"Exit: {trade['exit_date']} @ ${trade['exit_price']:.2f}, "
                    f"PnL: ${trade['pnl']:.2f} ({trade['return_pct']:.2f}%)"                )
            if len(primary.trade_details) > 5:
                console.print(f"  ... {len(primary.trade_details) - 5} more trades not shown")
    
    except ConfigError as e:
        rich_print(f"[bold red]Configuration Error:[/bold red] {str(e)}")
        sys.exit(1)
    except DataError as e:
        rich_print(f"[bold red]Data Error:[/bold red] {str(e)}")
        sys.exit(1)
    except BacktestError as e:
        rich_print(f"[bold red]Backtest Error:[/bold red] {str(e)}")
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
