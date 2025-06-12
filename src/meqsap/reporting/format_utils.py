"""Utility functions for formatting report data."""

import os
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Union, Tuple
from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
import warnings

from ..backtest import BacktestAnalysisResult, BacktestResult, VibeCheckResults, RobustnessResults
from ..exceptions import ReportingError
from ..config import StrategyConfig

# Flag indicating whether pyfolio is available
try:
    import pyfolio as pf
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    PYFOLIO_AVAILABLE = True
except ImportError:
    PYFOLIO_AVAILABLE = False


def format_percentage(value: float, decimal_places: int = 2, include_sign: bool = True) -> str:
    """Format a decimal value as a percentage."""
    if value is None or pd.isna(value) or not np.isfinite(value):
        return "N/A"
    
    formatted = f"{value:.{decimal_places}f}%"
    if include_sign and value > 0:
        formatted = "+" + formatted
    return formatted


def format_currency(value: float, decimal_places: int = 2) -> str:
    """Format a value as currency."""
    if value is None or pd.isna(value) or not np.isfinite(value):
        return "N/A"
    
    return f"${value:,.{decimal_places}f}"


def format_number(value: float, decimal_places: int = 2) -> str:
    """Format a numeric value with specified decimal places."""
    if value is None or pd.isna(value) or not np.isfinite(value):
        return "N/A"
    
    return f"{value:.{decimal_places}f}"


def get_performance_color(metric_name: str, value: float) -> str:
    """Get color code for performance metrics based on thresholds."""
    if value is None or pd.isna(value) or not np.isfinite(value):
        return "white"
    
    color_rules = {
        "total_return": {"good": 10.0, "bad": -5.0},  # Thresholds in percentage
        "annual_return": {"good": 15.0, "bad": 0.0},
        "sharpe_ratio": {"good": 1.0, "bad": 0.0},
        "max_drawdown": {"good": -10.0, "bad": -25.0},  # Note: negative values
        "win_rate": {"good": 55.0, "bad": 45.0},
    }
    
    if metric_name not in color_rules:
        return "white"
    
    thresholds = color_rules[metric_name]
    
    if metric_name == "max_drawdown":
        # For drawdown, less negative is better. Positive values are invalid.
        if value > 0:
            return "red"
        if value >= thresholds["good"]: # e.g. -5.0 >= -10.0
            return "green"
        elif value <= thresholds["bad"]:
            return "red"
        else:
            return "yellow"
    else:
        # For other metrics, higher is better
        if value >= thresholds["good"]:
            return "green"
        elif value <= thresholds["bad"]:
            return "red"
        else:
            return "yellow"


def format_performance_metrics(backtest_result: BacktestResult, decimal_places: int = 2) -> Dict[str, str]:
    """Format all performance metrics from a backtest result.
    
    Args:
        backtest_result: The BacktestResult object.
        decimal_places: The number of decimal places for formatting.
        
    Returns:
        A dictionary of formatted performance metrics.
    """
    return {
        "total_return": format_percentage(backtest_result.total_return, decimal_places),
        "annual_return": format_percentage(backtest_result.annualized_return, decimal_places),
        "sharpe_ratio": format_number(backtest_result.sharpe_ratio, decimal_places),
        "max_drawdown": format_percentage(backtest_result.max_drawdown, decimal_places),
        "win_rate": format_percentage(backtest_result.win_rate, decimal_places),
        "volatility": format_percentage(backtest_result.volatility, decimal_places),
        "calmar_ratio": format_number(backtest_result.calmar_ratio, decimal_places),
        "final_value": format_currency(backtest_result.final_value),
        "profit_factor": format_number(backtest_result.profit_factor, decimal_places),
        "total_trades": str(backtest_result.total_trades),
    }


def determine_overall_verdict(
    vibe_checks: VibeCheckResults,
    robustness_checks: RobustnessResults,
    backtest_result: BacktestResult
) -> Tuple[str, List[str]]:
    """Determine the overall verdict and recommendations based on all checks."""
    recommendations = []
    fail_reasons = []
    warn_reasons = []

    # Vibe checks
    if not vibe_checks.overall_pass:
        fail_reasons.append("Failed critical validation checks (vibe checks).")
    if backtest_result.total_trades == 0:
        fail_reasons.append("Strategy generated no trades.")

    # Performance checks
    if backtest_result.sharpe_ratio < 0.5:
        warn_reasons.append(f"Low Sharpe ratio ({backtest_result.sharpe_ratio:.2f}).")
    if backtest_result.max_drawdown < -25.0:
        warn_reasons.append(f"High maximum drawdown ({backtest_result.max_drawdown:.2f}%).")

    # Robustness checks
    if robustness_checks.sharpe_degradation > 50.0:
        warn_reasons.append(f"High sensitivity to fees (Sharpe degradation: {robustness_checks.sharpe_degradation:.1f}%).")
    if robustness_checks.turnover_rate > 20.0:
        warn_reasons.append(f"High turnover rate ({robustness_checks.turnover_rate:.1f}%).")

    # Determine verdict
    if fail_reasons:
        verdict = "FAIL"
        recommendations.extend(fail_reasons)
    elif warn_reasons:
        verdict = "WARNING"
        recommendations.extend(warn_reasons)
    else:
        verdict = "PASS"
        recommendations.append("Strategy passed all checks and shows promising results.")

    return verdict, recommendations


def create_strategy_summary_table(metrics: Dict[str, str], color_output: bool = True) -> Table:
    """Create a Rich table with strategy performance summary."""
    table = Table(title="Strategy Summary", show_header=True)
    
    table.add_column("Metric", style="dim")
    table.add_column("Value")
    
    metric_display_names = {
        "total_return": "Total Return",
        "annual_return": "Annual Return",
        "sharpe_ratio": "Sharpe Ratio",
        "max_drawdown": "Max Drawdown",
        "win_rate": "Win Rate",
        "profit_factor": "Profit Factor",
        "total_trades": "Total Trades"
    }
    
    for metric, value in metrics.items():
        if metric in metric_display_names:
            display_name = metric_display_names[metric]
            
            if color_output and metric in ("total_return", "annual_return", "sharpe_ratio", "max_drawdown", "win_rate"):
                # Extract the numeric value for color determination
                try:
                    if value == "N/A":
                        numeric_value = np.nan
                    elif "%" in value:
                        numeric_value = float(value.replace("%", "").replace("+", ""))
                    else:
                        numeric_value = float(value)
                    
                    color = get_performance_color(metric, numeric_value)
                    table.add_row(display_name, value, style=color)
                except (ValueError, TypeError):
                    table.add_row(display_name, value)
            else:
                table.add_row(display_name, value)
    
    return table


def create_performance_table(candidate_metrics: Dict[str, str], 
                             baseline_metrics: Optional[Dict[str, str]] = None,
                             color_output: bool = True) -> Table:
    """Create a performance comparison table between candidate and baseline."""
    table = Table(title="Performance Metrics", show_header=True)
    
    table.add_column("Metric", style="dim")
    table.add_column("Candidate Strategy")
    if baseline_metrics:
        table.add_column("Baseline")
    
    metric_display_names = {
        "total_return": "Total Return",
        "annual_return": "Annual Return",
        "sharpe_ratio": "Sharpe Ratio",
        "max_drawdown": "Max Drawdown",
        "win_rate": "Win Rate",
        "profit_factor": "Profit Factor",
        "total_trades": "Total Trades"
    }
    
    candidate_metrics_dict = candidate_metrics.model_dump() if isinstance(candidate_metrics, BaseModel) else candidate_metrics
    for metric, candidate_value in candidate_metrics_dict.items():
        if metric in metric_display_names:
            display_name = metric_display_names[metric]
            
            if baseline_metrics and metric in baseline_metrics:
                baseline_value = baseline_metrics[metric]
                
                # Calculate difference for percentage metrics
                if metric in ("total_return", "annual_return", "win_rate", "max_drawdown"):
                    try:
                        if candidate_value == "N/A" or baseline_value == "N/A":
                            diff_value = "N/A"
                        else:
                            candidate_num = float(candidate_value.replace("%", "").replace("+", ""))
                            baseline_num = float(baseline_value.replace("%", "").replace("+", ""))
                            diff = candidate_num - baseline_num
                            diff_value = format_percentage(diff, include_sign=True)
                    except (ValueError, AttributeError):
                        diff_value = "N/A"
                # Calculate difference for numeric metrics
                elif metric in ("sharpe_ratio", "profit_factor"):
                    try:
                        if candidate_value == "N/A" or baseline_value == "N/A":
                            diff_value = "N/A"
                        else:
                            candidate_num = float(candidate_value)
                            baseline_num = float(baseline_value)
                            diff = candidate_num - baseline_num
                            diff_value = format_number(diff, include_sign=True)
                    except (ValueError, AttributeError):
                        diff_value = "N/A"
                # Calculate difference for count metrics
                elif metric == "total_trades":
                    try:
                        candidate_num = int(candidate_value)
                        baseline_num = int(baseline_value)
                        diff = candidate_num - baseline_num
                        diff_value = f"{diff:+d}"
                    except (ValueError, TypeError):
                        diff_value = "N/A"
                else:
                    diff_value = "N/A"
                
                table.add_row(display_name, candidate_value, baseline_value, diff_value)
            else:
                if baseline_metrics:
                    table.add_row(display_name, candidate_value, "N/A", "N/A")
                else:
                    table.add_row(display_name, candidate_value)
    
    return table


def create_vibe_check_table(vibe_check_results: Dict[str, Any],
                           color_output: bool = True) -> Table:
    """Create a table for vibe check results."""
    table = Table(title="Strategy Vibe Check", show_header=True)
    
    table.add_column("Check", style="dim", no_wrap=True)
    table.add_column("Status", justify="center")
    
    vibe_check_dict = vibe_check_results.model_dump() if isinstance(vibe_check_results, BaseModel) else vibe_check_results
    if not vibe_check_dict:
         table.add_row("No Data", "No vibe check results available")
         return table
    
    check_display_names = {
         "minimum_trades_check": "Minimum Trades",
         "signal_quality_check": "Signal Quality",
         "data_coverage_check": "Data Coverage",
         "overall_pass": "Overall Status",
     }
    
    for check, passed in vibe_check_dict.items():
        if check in check_display_names:
            display_name = check_display_names[check]
            if isinstance(passed, bool):
                status_text = "PASS" if passed else "FAIL"
                if color_output:
                    status_color = "green" if passed else "red"
                    table.add_row(display_name, f"[{status_color}]{status_text}[/{status_color}]")
                else:
                    table.add_row(display_name, status_text)
    
    return table


def create_robustness_table(robustness_results: Dict[str, Any],
                           color_output: bool = True) -> Table:
    """Create a table for robustness check results."""
    table = Table(title="Strategy Robustness Analysis", show_header=True)
    
    table.add_column("Check", style="dim", no_wrap=True)
    table.add_column("Value")
    
    robustness_dict = robustness_results.model_dump() if isinstance(robustness_results, BaseModel) else robustness_results
    if not robustness_dict:
         table.add_row("No Data", "No robustness results available")
         return table
    
    check_display_names = {
         "baseline_sharpe": "Baseline Sharpe",
         "high_fees_sharpe": "High Fees Sharpe",
         "turnover_rate": "Turnover Rate",
         "sharpe_degradation": "Sharpe Degradation",
         "return_degradation": "Return Degradation",
     }
     
    for check, value in robustness_dict.items():
        if check in check_display_names:
             display_name = check_display_names[check]
             if isinstance(value, (float, int)):
                 formatted_value = f"{value:.2f}"
                 if "degradation" in check or "turnover" in check:
                     formatted_value += "%"
                 table.add_row(display_name, formatted_value)
             elif isinstance(value, list):
                 pass  # Recommendations are handled separately
             else:
                 table.add_row(display_name, str(value))
    
    return table


def create_recommendations_panel(recommendations: List[str]) -> Panel:
    """Create a Rich panel with recommendations."""
    if not recommendations:
        recommendations = ["No specific recommendations available."]
    
    content = "\n".join([f"• {rec}" for rec in recommendations])
    return Panel(content, title="Strategy Recommendations", border_style="blue")


def generate_executive_verdict(backtest_result: BacktestAnalysisResult, decimal_places: int = 2) -> Dict[str, str]:
    """Generate an executive verdict with formatted data for reporting."""
    # Format basic metrics
    metrics = format_performance_metrics(backtest_result.primary_result, decimal_places=decimal_places)
    
    # Determine vibe check status
    vibe_check_status = "Unknown"
    if backtest_result.vibe_checks:
        if backtest_result.vibe_checks.overall_pass:
            vibe_check_status = "All Checks Passed"
        else:
            vibe_check_status = "Major Concerns"
    
    # Determine robustness score
    robustness_score = "Unknown"
    if backtest_result.robustness_checks:
        degradation = backtest_result.robustness_checks.sharpe_degradation
        if degradation < 25.0:
            robustness_score = "Highly Robust"
        elif degradation < 50.0:
            robustness_score = "Moderately Robust"
        else:
            robustness_score = "Poorly Robust"
    
    # Format date range
    start_date = backtest_result.strategy_config['start_date'].strftime("%Y-%m-%d")
    end_date = backtest_result.strategy_config['end_date'].strftime("%Y-%m-%d")
    date_range = f"{start_date} to {end_date}"
    
    # Overall verdict based on metrics
    overall_verdict, _ = determine_overall_verdict(
        backtest_result.vibe_checks, backtest_result.robustness_checks, backtest_result.primary_result
    )
    
    # Create executive verdict data
    return {
        "strategy_name": backtest_result.strategy_config['strategy_type'],
        "ticker": backtest_result.strategy_config['ticker'],
        "date_range": date_range,
        "total_return": metrics["total_return"],
        "annual_return": metrics["annual_return"],
        "sharpe_ratio": metrics["sharpe_ratio"],
        "max_drawdown": metrics["max_drawdown"],
        "win_rate": metrics["win_rate"],
        "total_trades": int(metrics["total_trades"]),
        "vibe_check_status": vibe_check_status,
        "robustness_score": robustness_score,
        "overall_verdict": overall_verdict
    }


def prepare_returns_for_pyfolio(backtest_result: BacktestResult) -> pd.Series:
    """Convert backtest results to pyfolio-compatible returns series."""
    
    if not backtest_result.portfolio_value_series:
        raise ReportingError("No portfolio value series available for pyfolio conversion")
    
    # Convert portfolio values to returns
    portfolio_values = pd.Series(backtest_result.portfolio_value_series)
    portfolio_values.index = pd.to_datetime(portfolio_values.index)
    
    # Calculate daily returns
    returns = portfolio_values.pct_change().dropna()
    
    if returns.empty:
        raise ReportingError("Unable to calculate returns from portfolio values")
    
    # Check for degenerate cases where returns are meaningless for analysis
    if (returns.abs() < 1e-10).all():
        raise ReportingError("Unable to calculate returns: portfolio values are constant (zero returns)")
    
    return returns


def generate_pdf_report(
    backtest_result: BacktestAnalysisResult,
    output_path: Union[str, Path],
    include_plots: bool = True  # This param is not used by pyfolio tear sheet
) -> Path:
    """Generate a comprehensive PDF report using pyfolio."""
    if not PYFOLIO_AVAILABLE:
        raise ReportingError(
            "PDF report generation requires pyfolio. Install with: pip install pyfolio"
        )
    
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        returns = prepare_returns_for_pyfolio(backtest_result.primary_result)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with plt.style.context('seaborn-v0_8'):
                fig = pf.create_full_tear_sheet(
                    returns,
                    live_start_date=None,
                    return_fig=True
                )
                fig.savefig(str(output_path_obj), format='pdf', bbox_inches='tight', dpi=300)
                plt.close(fig)
        
        return output_path_obj
        
    except Exception as e:
        raise ReportingError(f"PDF report generation failed: {str(e)}") from e
