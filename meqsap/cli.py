import signal
import threading
from typing import Optional, Tuple
from rich.progress import Progress, TaskID, BarColumn, TextColumn, TimeElapsedColumn, SpinnerColumn
from rich.console import Console

from meqsap import __version__
from meqsap.config import load_config
from meqsap.data import download_data
from meqsap.backtest import run_complete_backtest
from meqsap_optimizer.engine import OptimizationEngine
from meqsap_optimizer.objective_functions import get_objective_function

import typer

app = typer.Typer()

# ...existing imports and code...

class OptimizationInterruptHandler:
    """Context manager for graceful optimization interruption handling."""
    
    def __init__(self):
        self.interrupted = threading.Event()
        self._original_handler = None
        
    def __enter__(self):
        self._original_handler = signal.signal(signal.SIGINT, self._handle_interrupt)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.signal(signal.SIGINT, self._original_handler)
        
    def _handle_interrupt(self, signum, frame):
        console = Console()
        console.print("\n[yellow]Optimization interrupted. Finishing current trial...[/yellow]")
        self.interrupted.set()

def create_optimization_progress_bar(algorithm: str, total_trials: Optional[int]) -> Tuple[Progress, TaskID]:
    """Create and configure a rich progress bar for optimization."""
    if algorithm == "GridSearch" and total_trials:
        # Known total for grid search
        progress = Progress(
            TextColumn("[bold blue]Optimizing"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TextColumn("Best: {task.fields[best_score]:.4f}"),
            TimeElapsedColumn(),
            TextColumn("{task.fields[current_params]}")
        )
        task_id = progress.add_task(
            "optimization", 
            total=total_trials,
            best_score=0.0,
            current_params=""
        )
    else:
        # Indefinite progress for random search
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Optimizing"),
            TextColumn("({task.completed} trials)"),
            TextColumn("Best: {task.fields[best_score]:.4f}"),
            TimeElapsedColumn(),
            TextColumn("{task.fields[current_params]}")
        )
        task_id = progress.add_task(
            "optimization",
            total=None,
            best_score=0.0,
            current_params=""
        )
    
    return progress, task_id

def create_progress_callback(progress: Progress, task_id: TaskID) -> callable:
    """Create a progress update callback for the optimization engine."""
    
    def update_progress_display(progress_data):
        # Format current parameters with truncation
        params_str = ", ".join(f"{k}={v}" for k, v in progress_data.current_params.items())
        if len(params_str) > 40:  # Truncate if too long
            params_str = params_str[:37] + "..."
        
        # Update progress bar
        progress.update(
            task_id,
            completed=progress_data.current_trial,
            best_score=progress_data.best_score or 0.0,
            current_params=params_str
        )
    
    return update_progress_display

@app.command()
def optimize_single(
    config_path: str = typer.Argument(..., help="Path to strategy configuration YAML file"),
    report: bool = typer.Option(False, "--report", help="Generate PDF report for best strategy"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
    no_progress: bool = typer.Option(False, "--no-progress", help="Disable progress reporting")
):
    """Run parameter optimization for a single-indicator strategy."""
    
    console = Console()
    
    # Load and validate configuration
    config = load_config(config_path)
    
    # Check if optimization is enabled
    optimization_config = config.get('optimization_config')
    if not optimization_config or not optimization_config.get('active', False):
        console.print("[red]Error: optimization_config.active must be true for optimize-single command[/red]")
        raise typer.Exit(1)
    
    try:
        # Initialize optimization engine
        objective_function = get_objective_function(optimization_config['objective_function'])
        engine = OptimizationEngine(
            strategy_config=config,
            objective_function=objective_function,
            algorithm_params=optimization_config.get('algorithm_params', {})
        )
        
        # Set up progress reporting if not disabled
        progress_callback = None
        if not no_progress:
            algorithm = optimization_config['algorithm']
            total_trials = engine.get_total_trials_estimate()
            
            progress, task_id = create_optimization_progress_bar(algorithm, total_trials)
            progress_callback = create_progress_callback(progress, task_id)
        
        # Run optimization with interruption handling
        with OptimizationInterruptHandler() as interrupt_handler:
            if not no_progress:
                with progress:
                    result = engine.run_optimization(
                        market_data=market_data,
                        progress_callback=progress_callback
                    )
            else:
                result = engine.run_optimization(market_data=market_data)
            
            # Check if interrupted
            if interrupt_handler.interrupted.is_set():
                result.was_interrupted = True
        
        # Display results
        from meqsap.reporting import display_optimization_summary
        display_optimization_summary(result)
        
        # Generate PDF report if requested and we have a best strategy
        if report and result.best_params:
            console.print("[blue]Generating PDF report for best strategy...[/blue]")
            # ...PDF generation code...
            
    except Exception as e:
        logger.error(f"Optimization failed: {e}", exc_info=verbose)
        console.print(f"[red]Optimization failed: {e}[/red]")
        raise typer.Exit(1)

# ...existing code...