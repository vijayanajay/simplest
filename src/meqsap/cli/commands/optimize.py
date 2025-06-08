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
from typing import Optional, Dict, Any

import pandas as pd
import typer
from rich.console import Console

from ...backtest import BacktestAnalysisResult
from ...config import load_yaml_config
from ...data import fetch_market_data
from ...exceptions import ConfigurationError, DataError, BacktestError, ReportingError
from ...optimizer import OptimizationEngine, OptimizationResult
from ...optimizer.interruption import OptimizationInterruptHandler
from ...optimizer.objective_functions import get_objective_function
from ..optimization_ui import (
    create_optimization_progress_bar,
    create_progress_callback,
    display_optimization_summary
)
from ..utils import handle_cli_errors

logger = logging.getLogger(__name__)
console = Console()

# Create optimize command group
optimize_app = typer.Typer(help="Strategy optimization commands")


@optimize_app.command("single")
@handle_cli_errors
def optimize_single(
    config_path: str = typer.Argument(..., help="Path to strategy configuration YAML file"),
    report: bool = typer.Option(False, "--report", help="Generate PDF report for best strategy"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", help="Directory to save reports and results"),
    trials: Optional[int] = typer.Option(None, "--trials", help="Number of optimization trials (RandomSearch only)"),
    no_progress: bool = typer.Option(False, "--no-progress", help="Disable progress bar"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
):
    """Optimize a single strategy configuration using the specified optimization algorithm."""
    if verbose:
        logging.getLogger('meqsap').setLevel(logging.DEBUG)
        console.print("[dim]Verbose logging enabled[/dim]")
    
    def _load_and_validate_config(config_path: str, trials: Optional[int]) -> Dict[str, Any]:
        """Load and validate the optimization configuration."""
        console.print(f"[blue]Loading configuration from {config_path}...[\/blue]")
        config = load_yaml_config(config_path)

        optimization_config = config.get('optimization_config')
        if not optimization_config or not optimization_config.get('active', False):
            raise ConfigurationError(
                "optimization_config.active must be true for optimize-single command. "
                "Hint: Set 'active: true' in the optimization_config section of your YAML file."
            )

        # Override trials if specified via CLI
        if trials is not None:
            if optimization_config.get('algorithm') == 'RandomSearch':
                if 'algorithm_params' not in optimization_config:
                    optimization_config['algorithm_params'] = {}
                optimization_config['algorithm_params']['n_trials'] = trials
                console.print(f"[yellow]Overriding trials to {trials} for RandomSearch[\/yellow]")
            else:
                console.print("[yellow]Warning: --trials option only applies to RandomSearch algorithm[\/yellow]")

        return config

    def _setup_optimization_engine(config: Dict[str, Any]) -> OptimizationEngine:
        """Initialize the optimization engine from the configuration."""
        console.print("[blue]Initializing optimization engine...[\/blue]")
        optimization_config = config['optimization_config']

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
            algorithm_params=algorithm_params,
        )
        return engine

    def _run_optimization_with_progress(
        engine: OptimizationEngine, market_data: pd.DataFrame, no_progress: bool, config: Dict[str, Any]
    ) -> OptimizationResult:
        """Run optimization loop with progress reporting and interruption handling."""
        optimization_config = config['optimization_config']
        algorithm = optimization_config.get('algorithm', 'Unknown')
        algorithm_params = optimization_config.get('algorithm_params', {})
        total_trials = algorithm_params.get('n_trials') if algorithm == 'RandomSearch' else None

        progress_callback, progress_context = (None, None)
        if not no_progress:
            console.print(f"[blue]Starting {algorithm} optimization with {total_trials or 'unlimited'} trials...[\/blue]")
            progress, task_id = create_optimization_progress_bar(algorithm, total_trials)
            progress_callback, progress_context = create_progress_callback(progress, task_id)

        with OptimizationInterruptHandler() as interrupt_handler:
            run_kwargs = {
                "market_data": market_data,
                "progress_callback": progress_callback,
                "interrupt_event": interrupt_handler.interrupted,
                "n_trials": total_trials,
            }
            if progress_context:
                with progress_context:
                    result: OptimizationResult = engine.run_optimization(**run_kwargs)
            else:
                result: OptimizationResult = engine.run_optimization(**run_kwargs)

            if interrupt_handler.interrupted.is_set():
                result.was_interrupted = True
                console.print("[yellow]Optimization was interrupted by user[\/yellow]")

        return result

    def _handle_reporting_and_exit(
        result: OptimizationResult, config: Dict[str, Any], config_path: str, report: bool, output_dir: Optional[Path], verbose: bool
    ):
        """Display results, generate reports, and determine exit code."""
        display_optimization_summary(result, config['ticker'])

        if report and result.best_params and result.best_strategy_analysis:
            console.print("[blue]Generating PDF report for best strategy...[\/blue]")
            try:
                from meqsap.reporting import generate_pdf_report

                report_filename = Path(config_path).stem + "_optimization_report.pdf"
                report_path = output_dir / report_filename

                best_analysis = BacktestAnalysisResult(**result.best_strategy_analysis)
                generate_pdf_report(best_analysis, output_path=str(report_path))
                console.print(f"[green]✓[\/green] Report saved to {report_path}")

            except ImportError:
                console.print("[yellow]Warning: PDF reporting not available. Install pyfolio and matplotlib for PDF generation.[\/yellow]")
            except Exception as e:
                raise ReportingError(f"Failed to generate PDF report: {e}") from e

        if result.was_interrupted:
            console.print("[yellow]Optimization completed with interruption[\/yellow]")
            raise typer.Exit(2)
        elif result.best_params is None:
            console.print("[red]Optimization completed but no valid trials found[\/red]")
            raise typer.Exit(1)
        else:
            console.print("[green]✓ Optimization completed successfully[\/green]")
    
    config = _load_and_validate_config(config_path, trials)

    console.print("[blue]Acquiring market data...[\/blue]")
    market_data = fetch_market_data(
        ticker=config['ticker'], start_date=config['start_date'], end_date=config['end_date']
    )
    if market_data.empty:
        raise DataError(f"No market data available for ticker {config['ticker']}")
    console.print(f"[green]✓[\/green] Acquired {len(market_data)} data points for {config['ticker']}")

    engine = _setup_optimization_engine(config)

    result = _run_optimization_with_progress(engine, market_data, no_progress, config)

    _handle_reporting_and_exit(result, config, config_path, report, output_dir, verbose)


if __name__ == "__main__":
    optimize_app()