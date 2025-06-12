"""Main reporting orchestrator."""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from rich.console import Console

from .models import ComparativeAnalysisResult
from .reporters import BaseReporter, TerminalReporter, HtmlReporter, PdfReporter
from ..exceptions import ReportingError
from ..backtest import BacktestAnalysisResult

logger = logging.getLogger(__name__)


class ReportingOrchestrator:
    """Orchestrates report generation using multiple reporters."""
    
    def __init__(self):
        self.reporters: List[BaseReporter] = []
    
    def add_reporter(self, reporter: BaseReporter) -> None:
        """Add a reporter to the orchestrator."""
        self.reporters.append(reporter)
    
    def generate_reports(self, result: ComparativeAnalysisResult) -> None:
        """Generate all configured reports."""
        if not self.reporters:
            logger.warning("No reporters configured. Adding default terminal reporter.")
            self.add_reporter(TerminalReporter())
        
        for reporter in self.reporters:
            try:
                reporter.generate_report(result)
            except Exception as e:
                logger.error(f"Reporter {type(reporter).__name__} failed: {e}")
                raise


def generate_complete_report(
    analysis_result: BacktestAnalysisResult,
    include_pdf: bool = False,
    output_directory: str = "./reports",
    quiet: bool = False
) -> Optional[str]:
    """Generate complete report output with optional PDF.
    
    This function provides backward compatibility with the previous reporting system
    by wrapping the new ReportingOrchestrator-based implementation.
    
    Args:
        analysis_result: The backtest analysis result to report on
        include_pdf: Whether to include a PDF report
        output_directory: Directory for report output
        quiet: Whether to suppress terminal output
        
    Returns:
        Path to PDF report if generated, None otherwise
    """
    pdf_path = Path(output_directory) / "report.pdf"

    orchestrator = ReportingOrchestrator()
    if not quiet:
        orchestrator.add_reporter(TerminalReporter())
    if include_pdf:
        orchestrator.add_reporter(PdfReporter(output_path=str(pdf_path)))

    # Create a wrapper ComparativeAnalysisResult for the single analysis_result
    from .models import ComparativeAnalysisResult
    result = ComparativeAnalysisResult(
        candidate_result=analysis_result,
        baseline_result=None,
        comparative_verdict=None
    )

    try:
        # Generate reports
        orchestrator.generate_reports(result)

        # Return path to PDF if it was generated
        if include_pdf:
            return str(pdf_path)
    except ReportingError as e:
        console = Console()
        console.print(f"[bold red]Report Generation Error:[/bold red] {str(e)}")
        return None
