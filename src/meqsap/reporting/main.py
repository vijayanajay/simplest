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
                # Continue with other reporters
    
    @classmethod
    def from_cli_flags(cls, flags: Dict[str, Any]) -> 'ReportingOrchestrator':
        """Create orchestrator based on CLI flags."""
        orchestrator = cls()
        
        # Always add terminal reporter
        orchestrator.add_reporter(TerminalReporter())
        
        # Add PDF reporter if requested
        if flags.get('report', False):
            orchestrator.add_reporter(PdfReporter())
        
        # Add HTML reporter if requested
        if flags.get('report_html', False):
            orchestrator.add_reporter(HtmlReporter())
            
        return orchestrator


def generate_complete_report(
    analysis_result: BacktestAnalysisResult,
    include_pdf: bool = False,
    output_directory: str = "./reports",
    no_color: bool = False,
    quiet: bool = False
) -> Optional[str]:
    """Generate complete report output with optional PDF.
    
    This function provides backward compatibility with the previous reporting system
    by wrapping the new ReportingOrchestrator-based implementation.
    
    Args:
        analysis_result: The backtest analysis result to report on
        include_pdf: Whether to include a PDF report
        output_directory: Directory for report output
        no_color: Whether to disable color in terminal output
        quiet: Whether to suppress terminal output
        
    Returns:
        Path to PDF report if generated, None otherwise
    """
    # Create flags dictionary for orchestrator
    flags = {
        'report': include_pdf,
        'report_html': False,  # PDF only for backward compatibility
    }
    
    # Create orchestrator with appropriate reporters
    orchestrator = ReportingOrchestrator.from_cli_flags(flags)
    
    # Create a wrapper ComparativeAnalysisResult for the single analysis_result
    from .models import ComparativeAnalysisResult
    result = ComparativeAnalysisResult(
        candidate_result=analysis_result,
        baseline_result=None,
        comparative_verdict=None
    )
    
    try:
        # Generate reports
        if not quiet:
            orchestrator.generate_reports(result)
        elif include_pdf:
            # In quiet mode, only generate PDF if requested
            pdf_reporter = PdfReporter(
                output_path=str(Path(output_directory) / "report.pdf")
            )
            pdf_reporter.generate_report(result)
            
        # Return path to PDF if it was generated
        if include_pdf:
            return str(Path(output_directory) / "report.pdf")
        return None
        
    except ReportingError as e:
        console = Console()
        console.print(f"[bold red]Report Generation Error:[/bold red] {str(e)}")
        return None
    except Exception as e:
        console = Console()
        console.print(f"[bold red]Unexpected Error in Report Generation:[/bold red] {str(e)}")
        return None
