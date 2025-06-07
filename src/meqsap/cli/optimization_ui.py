"""CLI progress bar and UI components for optimization."""

import time
from typing import Optional, Callable, Dict, Any, Tuple
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, SpinnerColumn
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..optimizer.models import ProgressData, OptimizationResult

console = Console()


def create_optimization_progress_bar(algorithm: str, total_trials: Optional[int] = None) -> Tuple[Progress, int]:
    """Create a rich progress bar for optimization display.
    
    Args:
        algorithm: Optimization algorithm name (e.g., GridSearch, RandomSearch).
        total_trials: Total number of trials. If None, an indeterminate bar is shown.
        
    Returns:
        A tuple containing the configured rich Progress instance and the task ID.
    """
    # Use a determinate progress bar for ANY algorithm with a known, positive total
    if total_trials is not None and total_trials > 0:
        columns = [
            TextColumn("[bold blue]Optimizing..."),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total} trials)"),
            TextColumn("Best: [green]{task.fields[best_score]:.4f}[/green]"),
            TimeElapsedColumn(),
            TextColumn("{task.fields[current_params]}", style="dim"),
        ]
    else:
        # Use an indeterminate spinner for algorithms with an unknown or zero total
        columns = [
            SpinnerColumn(),
            TextColumn("[bold blue]Optimizing..."),
            TextColumn("({task.completed} trials)"),
            TextColumn("Best: [green]{task.fields[best_score]:.4f}[/green]"),
            TimeElapsedColumn(),
            TextColumn("{task.fields[current_params]}", style="dim"),
        ]
    
    progress = Progress(*columns, console=console)
    task_id = progress.add_task(
        "optimization", 
        total=total_trials, 
        best_score=0.0, 
        current_params="Initializing..."
    )
    
    return progress, task_id


def create_progress_callback(progress: Progress, task_id: int, 
                           max_param_length: int = 60) -> Callable[[ProgressData], None]:
    """Create a callback to update the progress bar from optimization engine."""
    def callback(progress_data: ProgressData):
        # Truncate params string if too long
        params_str = str(progress_data.current_params)
        if len(params_str) > max_param_length:
            params_str = params_str[:max_param_length-3] + "..."
        
        # Update progress bar
        best_score_value = progress_data.best_score if progress_data.best_score is not None else 0.0
        
        progress.update(
            task_id,
            completed=progress_data.current_trial,
            total=progress_data.total_trials,
            fields={
                "best_score": best_score_value,
                "current_params": params_str
            }
        )
        
        # Display error summary if there are failures
        if progress_data.failed_trials_summary:
            error_parts = [f"{error_type}: {count}" for error_type, count in progress_data.failed_trials_summary.items()]
            error_str = " | ".join(error_parts)
            console.print(f"[yellow]Failures:[/yellow] {error_str}", style="dim")
    
    return callback


def display_optimization_summary(result: OptimizationResult) -> None:
    """Display comprehensive optimization results summary.
    
    Args:
        result: OptimizationResult containing all optimization data
    """
    console.print("\n")
    console.print("[bold cyan]Optimization Complete![/bold cyan]")
    console.print("="*60)
    
    # Display run statistics
    _display_run_statistics(result)
    
    # Display error summary if there were failures
    if result.error_summary.total_failed_trials > 0:
        _display_error_summary(result.error_summary)
    
    # Display best strategy results
    if result.best_params:
        _display_best_strategy_results(result)
    else:
        console.print("[red]No successful trials completed.[/red]")
    
    # Display constraint adherence if available
    if result.constraint_adherence:
        _display_constraint_adherence(result.constraint_adherence)


def _display_run_statistics(result: OptimizationResult) -> None:
    """Display optimization run statistics.
    
    Args:
        result: OptimizationResult containing timing and trial data
    """
    table = Table(title="Optimization Statistics", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    total_elapsed = result.timing_info.get("total_elapsed", 0)
    avg_per_trial = result.timing_info.get("avg_per_trial", 0)
    
    table.add_row("Total Trials", str(result.total_trials))
    table.add_row("Successful Trials", str(result.successful_trials))
    table.add_row("Failed Trials", str(result.error_summary.total_failed_trials))
    table.add_row("Success Rate", f"{(result.successful_trials / max(result.total_trials, 1)) * 100:.1f}%")
    table.add_row("Total Time", f"{total_elapsed:.1f}s")
    table.add_row("Avg Time/Trial", f"{avg_per_trial:.2f}s")
    
    if result.was_interrupted:
        table.add_row("Status", "[yellow]INTERRUPTED[/yellow]")
    else:
        table.add_row("Status", "[green]COMPLETED[/green]")
    
    console.print(table)
    console.print()


def _display_error_summary(error_summary) -> None:
    """Display error summary by category.
    
    Args:
        error_summary: ErrorSummary object with failure statistics
    """
    table = Table(title="Error Summary", show_header=True)
    table.add_column("Error Type", style="red")
    table.add_column("Count", style="yellow")
    table.add_column("Percentage", style="yellow")
    
    total_failures = error_summary.total_failed_trials
    
    for error_type, count in error_summary.failure_counts_by_type.items():
        if count > 0:
            percentage = (count / total_failures) * 100 if total_failures > 0 else 0
            table.add_row(error_type, str(count), f"{percentage:.1f}%")
    
    console.print(table)
    console.print()


def _display_best_strategy_results(result: OptimizationResult) -> None:
    """Display best strategy parameters and performance.
    
    Args:
        result: OptimizationResult with best strategy data
    """
    # Best parameters table
    if result.best_params:
        params_table = Table(title="Best Parameters Found", show_header=True)
        params_table.add_column("Parameter", style="cyan")
        params_table.add_column("Value", style="green")
        
        for param, value in result.best_params.items():
            params_table.add_row(param, str(value))
        
        console.print(params_table)
    
    # Best score display
    if result.best_score is not None:
        score_panel = Panel(
            f"[bold green]{result.best_score:.6f}[/bold green]",
            title="Best Objective Score",
            border_style="green"
        )
        console.print(score_panel)
    
    console.print()


def _display_constraint_adherence(constraint_data: Dict[str, Any]) -> None:
    """Display constraint adherence metrics.
    
    Args:
        constraint_data: Dictionary containing constraint adherence metrics
    """
    table = Table(title="Constraint Adherence", show_header=True)
    table.add_column("Constraint", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Status", style="bold")
    
    # Display hold period statistics if available
    if "avg_hold_period" in constraint_data:
        table.add_row(
            "Avg Hold Period", 
            f"{constraint_data['avg_hold_period']:.1f} days",
            "[green]✓[/green]" if constraint_data.get("hold_period_valid", True) else "[red]✗[/red]"
        )
    
    if "pct_trades_in_target_range" in constraint_data:
        table.add_row(
            "% Trades in Target Range",
            f"{constraint_data['pct_trades_in_target_range']:.1f}%",
            "[green]✓[/green]" if constraint_data.get("target_range_valid", True) else "[red]✗[/red]"
        )
    
    console.print(table)
    console.print()