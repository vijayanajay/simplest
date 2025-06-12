"""MEQSAP Reporting Module - Strategy Pattern Implementation."""

from .models import ComparativeAnalysisResult, ReportConfig, ExecutiveVerdictData
from .reporters import BaseReporter, TerminalReporter, HtmlReporter, PdfReporter
from .main import ReportingOrchestrator, generate_complete_report
from .format_utils import (
    format_percentage,
    format_currency,
    format_number,
    get_performance_color,
    format_performance_metrics,
    determine_overall_verdict,
    create_strategy_summary_table,
    create_performance_table,
    create_vibe_check_table,
    create_robustness_table,
    create_recommendations_panel,
    generate_executive_verdict,
    prepare_returns_for_pyfolio,
    generate_pdf_report,
    PYFOLIO_AVAILABLE,
)
from ..exceptions import ReportingError

__all__ = [
    'ComparativeAnalysisResult',
    'ReportConfig',
    'ExecutiveVerdictData',
    'BaseReporter',
    'TerminalReporter', 
    'HtmlReporter',
    'PdfReporter',
    'ReportingOrchestrator',
    'generate_complete_report',
    'ReportingError',
    'format_percentage',
    'format_currency',
    'format_number',
    'get_performance_color',
    'format_performance_metrics',
    'determine_overall_verdict',
    'create_strategy_summary_table',
    'create_performance_table',
    'create_vibe_check_table',
    'create_robustness_table',
    'create_recommendations_panel',
    'generate_executive_verdict',
    'prepare_returns_for_pyfolio',
    'generate_pdf_report',
    'PYFOLIO_AVAILABLE',
]
