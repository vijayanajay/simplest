"""
Command Line Interface (CLI) for the adaptive trading system.
"""
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler

from adaptive_trading_system.common.exceptions import ConfigurationError
from adaptive_trading_system.common.utils import setup_logging, log_config
from adaptive_trading_system.config.settings import load_config
from adaptive_trading_system.main import run_discovery_pipeline

# Initialize Typer app
app = typer.Typer(
    name="tradefinder",
    help="Adaptive Automated Trading Strategy Discovery System",
    add_completion=False,
)

# Initialize Rich console for better formatted output
console = Console()


@app.command(name="discover")
def discover_command(
    config_file: Path = typer.Option(
        ...,
        "--config-file", "-c",
        help="Path to the configuration file (YAML)",
        exists=True,
        dir_okay=False,
        file_okay=True,
        readable=True,
    ),
    log_level: Optional[str] = typer.Option(
        None,
        "--log-level", "-l",
        help="Override logging level from config (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        case_sensitive=False,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose output",
    ),
):
    """
    Discover trading strategies using genetic algorithms based on the given configuration.
    """
    try:
        # Load and validate configuration
        config = load_config(str(config_file))
        
        # Override log level if specified in command
        if log_level:
            config.logging_level = log_level
            
        # Set up logging with more verbose output if requested
        if verbose:
            logging.basicConfig(
                level=getattr(logging, config.logging_level),
                format="%(asctime)s [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d] - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                handlers=[RichHandler(rich_tracebacks=True)]
            )
            logger = logging.getLogger("adaptive_trading_system")
        else:
            logger = setup_logging(
                level=config.logging_level,
                run_id=config.run_id
            )
        
        # Log the effective configuration
        log_config(config.dict(), logger)
        
        # Run the main pipeline
        logger.info(f"Starting discovery run with ID: {config.run_id}")
        run_discovery_pipeline(config, logger)
        
        # Log successful completion
        logger.info(f"Discovery run {config.run_id} completed successfully")
        console.print(f"[green]Discovery run completed successfully. Run ID: {config.run_id}[/green]")
        
    except ConfigurationError as e:
        console.print(f"[bold red]Configuration Error: {str(e)}[/bold red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1)


@app.command(name="version")
def version_command():
    """
    Show the version of the application.
    """
    from adaptive_trading_system import __version__
    console.print(f"[bold]tradefinder[/bold] version [bold blue]{__version__}[/bold blue]")


# Main entry point for the CLI
def run():
    """Entry point for the CLI."""
    app() 