"""
Enhanced optimization CLI commands with comprehensive progress reporting.

Implements Story 7: Enhanced Optimization Progress Reporting
- Real-time progress visualization with rich progress bars
- Comprehensive error handling and categorization
- Graceful interruption with SIGINT handling
- Detailed optimization summary reporting
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import typer
from rich.console import Console

from ...backtest import run_complete_backtest, BacktestAnalysisResult
from ...config import load_yaml_config
from ...data import fetch_market_data
from ...exceptions import ConfigurationError, DataError
from ...optimizer import OptimizationEngine, OptimizationResult
from ...optimizer.interruption import OptimizationInterruptHandler
from ...optimizer.objective_functions import get_objective_function
from ..optimization_ui import (
    create_optimization_progress_bar,
    create_progress_callback,
    display_optimization_summary
)

logger = logging.getLogger(__name__)
console = Console()

# Create optimize command group
optimize_app = typer.Typer(help="Strategy optimization commands")


@optimize_app.command("single")
def optimize_single(
    config_path: str = typer.Argument(..., help="Path to strategy configuration YAML file"),
    report: bool = typer.Option(False, "--report", help="Generate PDF report for best strategy"),
    output_dir: Optional[Path] = typer.Option(
        "./reports",
        "--output-dir",
        help="Directory for output reports",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
    no_progress: bool = typer.Option(False, "--no-progress", help="Disable progress reporting"),
    trials: Optional[int] = typer.Option(None, "--trials", help="Override number of trials (for RandomSearch)")
):
    """
    Run parameter optimization for a single-indicator strategy.
    
    This command performs hyperparameter optimization using the algorithm specified
    in the configuration file. Supports both GridSearch and RandomSearch algorithms
    with real-time progress reporting and graceful interruption handling.
    
    Examples:
        meqsap optimize single examples/ma_crossover.yaml
        meqsap optimize single examples/ma_crossover.yaml --report --verbose
        meqsap optimize single examples/ma_crossover.yaml --no-progress --trials 100
    """
    
    # Configure logging based on verbose flag
    if verbose:
        logging.getLogger('meqsap').setLevel(logging.DEBUG)
        console.print("[dim]Verbose logging enabled[/dim]")
    
    try:        # Load and validate configuration
        console.print(f"[blue]Loading configuration from {config_path}...[/blue]")
        config = load_yaml_config(config_path)
        
        # Validate optimization configuration
        optimization_config = config.get('optimization_config')
        if not optimization_config or not optimization_config.get('active', False):
            console.print("[red]Error: optimization_config.active must be true for optimize-single command[/red]")
            console.print("[yellow]Hint: Set 'active: true' in the optimization_config section of your YAML file[/yellow]")
            raise typer.Exit(1)
        
        # Override trials if specified
        if trials is not None:
            if optimization_config['algorithm'] == 'RandomSearch':
                optimization_config['algorithm_params']['n_trials'] = trials
                console.print(f"[yellow]Overriding trials to {trials} for RandomSearch[/yellow]")
            else:
                console.print("[yellow]Warning: --trials option only applies to RandomSearch algorithm[/yellow]")        # Download market data
        console.print("[blue]Acquiring market data...[/blue]")
        market_data = fetch_market_data(
            ticker=config['ticker'],
            start_date=config['start_date'],
            end_date=config['end_date']
        )
        if market_data.empty:
            raise DataError(f"No market data available for ticker {config['ticker']}")
        
        console.print(f"[green]✓[/green] Acquired {len(market_data)} data points for {config['ticker']}")
        
        # Initialize optimization engine
        console.print("[blue]Initializing optimization engine...[/blue]")
        
        # Get objective function from registry
        objective_function_name = optimization_config.get('objective_function')
        if not objective_function_name:
            raise ConfigurationError("'objective_function' must be defined in optimization_config")
        
        objective_function = get_objective_function(objective_function_name)
        objective_params = optimization_config.get('objective_params', {})
        algorithm_params = optimization_config.get('algorithm_params', {})
        
        engine = OptimizationEngine(
            strategy_config=config,
            objective_function=objective_function,
            objective_params=objective_params,
            algorithm_params=algorithm_params
        )
        
        # Set up progress reporting if not disabled
        progress_callback = None
        progress_context = None
        
        if not no_progress:
            algorithm = optimization_config['algorithm']
            total_trials = algorithm_params.get('n_trials') if algorithm == 'RandomSearch' else None
            
            console.print(f"[blue]Starting {algorithm} optimization with {total_trials or 'unlimited'} trials...[blue]")
            progress, task_id = create_optimization_progress_bar(algorithm, total_trials)
            progress_callback, progress_context = create_progress_callback(progress, task_id)
        else:
            progress_callback = None
            progress_context = None
        
        # Run optimization with interruption handling
        with OptimizationInterruptHandler() as interrupt_handler:
            if progress_context:
                with progress_context:
                    result: OptimizationResult = engine.run_optimization(
                        market_data=market_data,
                        progress_callback=progress_callback,
                        interrupt_event=interrupt_handler.interrupted,
                        n_trials=total_trials
                    )
            else:
                result: OptimizationResult = engine.run_optimization(
                    market_data=market_data,
                    interrupt_event=interrupt_handler.interrupted,
                    n_trials=total_trials
                )
            
            # Check if interrupted
            if interrupt_handler.interrupted.is_set():
                result.was_interrupted = True
                console.print("[yellow]Optimization was interrupted by user[/yellow]")
        
        # Display comprehensive results summary
        display_optimization_summary(result, config['ticker'])
        
        # Generate PDF report if requested and a best strategy was found
        if report and result.best_params and result.best_strategy_analysis:
            console.print("[blue]Generating PDF report for best strategy...[/blue]")
            try:
                # Import here to avoid circular dependencies
                from meqsap.reporting import generate_pdf_report
                
                report_filename = Path(config_path).stem + "_optimization_report.pdf"
                report_path = output_dir / report_filename
                
                best_analysis = BacktestAnalysisResult(**result.best_strategy_analysis)
                generate_pdf_report(best_analysis, output_path=str(report_path))
                console.print(f"[green]✓[/green] Report saved to {report_path}")
                
            except ImportError:
                console.print("[yellow]Warning: PDF reporting not available. Install pyfolio and matplotlib for PDF generation.[/yellow]")
            except Exception as e:
                logger.error(f"Failed to generate PDF report: {e}", exc_info=verbose)
                console.print(f"[red]Failed to generate PDF report: {e}[/red]")
        
        # Exit with appropriate code
        if result.was_interrupted:
            console.print("[yellow]Optimization completed with interruption[/yellow]")
            raise typer.Exit(2)  # Special exit code for interruption
        elif result.best_params is None:
            console.print("[red]Optimization completed but no valid trials found[/red]")
            raise typer.Exit(1)
        else:
            console.print("[green]✓ Optimization completed successfully[/green]")
            
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}", exc_info=verbose)
        console.print(f"[red]Configuration error: {e}[/red]")
        raise typer.Exit(1)
    
    except DataError as e:
        logger.error(f"Data error: {e}", exc_info=verbose)
        console.print(f"[red]Data error: {e}[/red]")
        console.print("[yellow]Hint: Check your symbol, date range, and internet connection[/yellow]")
        raise typer.Exit(1)
    
    except Exception as e:
        logger.error(f"Optimization failed: {e}", exc_info=verbose)
        console.print(f"[red]Optimization failed: {e}[/red]")
        if not verbose:
            console.print("[yellow]Use --verbose flag for detailed error information[/yellow]")
        raise typer.Exit(1)


@optimize_app.command("batch")
def optimize_batch(
    config_dir: str = typer.Argument(..., help="Directory containing strategy configuration files"),
    pattern: str = typer.Option("*.yaml", "--pattern", help="File pattern to match (default: *.yaml)"),
    parallel: int = typer.Option(1, "--parallel", help="Number of parallel optimization jobs"),
    report: bool = typer.Option(False, "--report", help="Generate PDF reports for best strategies"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
    no_progress: bool = typer.Option(False, "--no-progress", help="Disable progress reporting")
):
    """
    Run optimization for multiple strategy configurations in batch mode.
    
    This command processes all configuration files matching the specified pattern
    in the given directory, running optimization for each one. Supports parallel
    execution for improved performance.
    
    Examples:
        meqsap optimize batch examples/
        meqsap optimize batch examples/ --pattern "ma_*.yaml" --parallel 2
        meqsap optimize batch examples/ --report --verbose
    """
    
    # Configure logging
    if verbose:
        logging.getLogger('meqsap').setLevel(logging.DEBUG)
    
    try:
        config_path = Path(config_dir)
        if not config_path.exists() or not config_path.is_dir():
            console.print(f"[red]Error: Directory {config_dir} does not exist[/red]")
            raise typer.Exit(1)
        
        # Find matching configuration files
        config_files = list(config_path.glob(pattern))
        if not config_files:
            console.print(f"[red]No configuration files found matching pattern '{pattern}' in {config_dir}[/red]")
            raise typer.Exit(1)
        
        console.print(f"[blue]Found {len(config_files)} configuration files to process[/blue]")
        
        # TODO: Implement batch optimization logic
        # This would involve:
        # 1. Processing each config file
        # 2. Running optimization for each
        # 3. Collecting results
        # 4. Generating summary report
        # 5. Optional parallel execution
        
        console.print("[yellow]Batch optimization is not yet implemented[/yellow]")
        console.print("[blue]Please use 'optimize single' command for individual configurations[/blue]")
        raise typer.Exit(1)
        
    except Exception as e:
        logger.error(f"Batch optimization failed: {e}", exc_info=verbose)
        console.print(f"[red]Batch optimization failed: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    optimize_app()