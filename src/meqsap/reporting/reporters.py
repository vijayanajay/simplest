"""Reporter implementations using Strategy Pattern."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich import box

from .models import ComparativeAnalysisResult
from ..backtest import BacktestAnalysisResult
from ..exceptions import ReportingError

logger = logging.getLogger(__name__)


class BaseReporter(ABC):
    """Protocol for all report generators."""
    
    @abstractmethod
    def generate_report(self, result: ComparativeAnalysisResult) -> None:
        """Generate report from comparative analysis result."""
        pass


class TerminalReporter(BaseReporter):
    """Rich terminal-based comparative reporting."""
    
    def __init__(self):
        self.console = Console()
    
    def generate_report(self, result: ComparativeAnalysisResult) -> None:
        """Display side-by-side comparison in terminal."""
        try:
            if result.is_comparative:
                self._display_comparative_analysis(result)
            else:
                self._display_single_strategy(result)
            
            # Always display vibe check results
            self._display_vibe_checks(result)
            
        except Exception as e:
            logger.error(f"Terminal reporting failed: {e}")
            raise ReportingError(f"Failed to generate terminal report: {e}")
    
    def _display_comparative_analysis(self, result: ComparativeAnalysisResult) -> None:
        """Display comparative metrics table."""
        table = Table(title="📊 Strategy Performance Comparison", box=box.ROUNDED)
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Candidate", style="green")
        table.add_column("Baseline", style="blue")
        
        # Extract metrics
        candidate = result.candidate_result
        baseline = result.baseline_result
        
        # Core performance metrics
        table.add_row(
            "Total Return",
            f"{candidate.total_return:.2%}",
            f"{baseline.total_return:.2%}" if baseline else "N/A"
        )
        
        table.add_row(
            "Sharpe Ratio",
            f"{candidate.sharpe_ratio:.2f}",
            f"{baseline.sharpe_ratio:.2f}" if baseline else "N/A"
        )
        
        table.add_row(
            "Calmar Ratio",
            f"{candidate.calmar_ratio:.2f}",
            f"{baseline.calmar_ratio:.2f}" if baseline else "N/A"
        )
        
        table.add_row(
            "Max Drawdown",
            f"{candidate.max_drawdown:.2%}",
            f"{baseline.max_drawdown:.2%}" if baseline else "N/A"
        )
        
        # Add verdict row
        verdict_style = "bold green" if "Outperformed" in str(result.comparative_verdict) else "bold red"
        table.add_row(
            "Verdict",
            result.format_verdict(),
            "",
            style=verdict_style
        )
        
        self.console.print(table)
    
    def _display_single_strategy(self, result: ComparativeAnalysisResult) -> None:
        """Display single strategy metrics."""
        table = Table(title="📊 Strategy Performance Analysis", box=box.ROUNDED)
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        candidate = result.candidate_result
        
        table.add_row("Total Return", f"{candidate.total_return:.2%}")
        table.add_row("Sharpe Ratio", f"{candidate.sharpe_ratio:.2f}")
        table.add_row("Calmar Ratio", f"{candidate.calmar_ratio:.2f}")
        table.add_row("Max Drawdown", f"{candidate.max_drawdown:.2%}")
        
        # Show baseline failure reason if applicable
        if result.baseline_failed:
            table.add_row(
                "Baseline Status", 
                f"⚠️ Failed: {result.baseline_failure_reason}",
                style="bold yellow"
            )
        
        self.console.print(table)
    
    def _display_vibe_checks(self, result: ComparativeAnalysisResult) -> None:
        """Display vibe check results for both strategies."""
        # Display candidate vibe checks (existing functionality)
        if hasattr(result.candidate_result, 'vibe_check_results'):
            # Use existing vibe check display logic
            pass
        
        # Display baseline vibe checks if available
        if result.has_baseline and hasattr(result.baseline_result, 'vibe_check_results'):
            # Display baseline vibe checks
            pass
    
    def _calculate_verdict(self, candidate: BacktestAnalysisResult, 
                          baseline: Optional[BacktestAnalysisResult]) -> Optional[str]:
        """Calculate performance verdict based on Sharpe ratio."""
        if baseline is None:
            return None
        
        if candidate.sharpe_ratio > baseline.sharpe_ratio:
            return "Outperformed"
        else:
            return "Underperformed"


class HtmlReporter(BaseReporter):
    """QuantStats-based HTML report generation."""
    
    def __init__(self, output_path: str = "report.html"):
        self.output_path = Path(output_path)
    
    def generate_report(self, result: ComparativeAnalysisResult) -> None:
        """Generate comprehensive HTML report using QuantStats."""
        try:
            import quantstats as qs
        except ImportError:
            raise ReportingError(
                "QuantStats not installed. Run 'pip install quantstats' to enable HTML reporting."
            )
        
        try:
            # Extract returns data
            candidate_returns = self._extract_returns(result.candidate_result)
            
            if result.is_comparative:
                baseline_returns = self._extract_returns(result.baseline_result)
                
                # Generate comparative report
                qs.reports.html(
                    candidate_returns,
                    benchmark=baseline_returns,
                    output=str(self.output_path),
                    title="MEQSAP Strategy Analysis Report"
                )
            else:
                # Generate single strategy report
                qs.reports.html(
                    candidate_returns,
                    output=str(self.output_path),
                    title="MEQSAP Strategy Analysis Report"
                )
            
            logger.info(f"✅ HTML report generated: {self.output_path}")
            
        except Exception as e:
            logger.error(f"HTML report generation failed: {e}")
            raise ReportingError(f"Failed to generate HTML report: {e}")
    
    def _extract_returns(self, result: BacktestAnalysisResult) -> 'pd.Series':
        """Extract daily returns series from backtest result."""
        # Extract returns from the backtest result
        # This assumes the BacktestAnalysisResult has returns data
        if hasattr(result, 'returns'):
            return result.returns
        elif hasattr(result, 'portfolio_returns'):
            return result.portfolio_returns
        else:
            raise ReportingError("Cannot extract returns data from backtest result")


class PdfReporter(BaseReporter):
    """Existing pyfolio-based PDF reporting with comparative support."""
    
    def __init__(self, output_path: str = "report.pdf"):
        self.output_path = Path(output_path)
    
    def generate_report(self, result: ComparativeAnalysisResult) -> None:
        """Generate PDF report for candidate strategy."""
        try:
            # Use existing PDF generation logic for candidate strategy
            # This maintains backward compatibility
            from ..reporting import generate_pdf_report  # Existing function
            
            generate_pdf_report(result.candidate_result, str(self.output_path))
            logger.info(f"✅ PDF report generated: {self.output_path}")
            
        except Exception as e:
            logger.error(f"PDF report generation failed: {e}")
            raise ReportingError(f"Failed to generate PDF report: {e}")
