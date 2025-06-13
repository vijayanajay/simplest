import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from meqsap.reporting.reporters import TerminalReporter, HtmlReporter, PdfReporter
from meqsap.reporting.models import ComparativeAnalysisResult
from meqsap.exceptions import ReportingError

@pytest.fixture
def mock_comparative_result():
    # A simplified mock for testing reporters
    candidate_result = Mock()
    candidate_result.primary_result.total_return = 0.15
    candidate_result.primary_result.sharpe_ratio = 1.2
    candidate_result.primary_result.calmar_ratio = 0.8
    candidate_result.primary_result.max_drawdown = -0.10
    
    baseline_result = Mock()
    baseline_result.primary_result.total_return = 0.10
    baseline_result.primary_result.sharpe_ratio = 0.9
    baseline_result.primary_result.calmar_ratio = 0.6
    baseline_result.primary_result.max_drawdown = -0.15

    result = Mock(spec=ComparativeAnalysisResult)
    result.candidate_result = candidate_result
    result.baseline_result = baseline_result
    result.is_comparative = True
    result.has_baseline = True
    result.baseline_failed = False
    result.comparative_verdict = "Outperformed"
    result.format_verdict.return_value = "Strategy Outperformed baseline (Sharpe Ratio)"
    return result

@pytest.fixture
def mock_single_result():
    candidate_result = Mock()
    candidate_result.primary_result.total_return = 0.15
    candidate_result.primary_result.sharpe_ratio = 1.2
    candidate_result.primary_result.calmar_ratio = 0.8
    candidate_result.primary_result.max_drawdown = -0.10

    result = Mock(spec=ComparativeAnalysisResult)
    result.candidate_result = candidate_result
    result.baseline_result = None
    result.is_comparative = False
    result.has_baseline = False
    result.baseline_failed = False
    return result

class TestTerminalReporter:
    @patch('rich.console.Console.print')
    def test_generate_report_comparative(self, mock_print, mock_comparative_result):
        reporter = TerminalReporter()
        reporter.generate_report(mock_comparative_result)
        mock_print.assert_called()
        # Check if table title is in the printed output
        args, kwargs = mock_print.call_args
        assert "Strategy Performance Comparison" in str(args[0].title)

    @patch('rich.console.Console.print')
    def test_generate_report_single(self, mock_print, mock_single_result):
        reporter = TerminalReporter()
        reporter.generate_report(mock_single_result)
        mock_print.assert_called()
        args, kwargs = mock_print.call_args
        assert "Strategy Performance Analysis" in str(args[0].title)

class TestHtmlReporter:
    @patch('quantstats.reports.html')
    def test_generate_report_comparative(self, mock_qs_html, mock_comparative_result):
        # Mock returns extraction
        mock_comparative_result.candidate_result.returns = "candidate_returns_series"
        mock_comparative_result.baseline_result.returns = "baseline_returns_series"
        
        reporter = HtmlReporter(output_path="test_report.html")
        with patch.object(reporter, '_extract_returns', side_effect=["candidate_returns_series", "baseline_returns_series"]):
            reporter.generate_report(mock_comparative_result)
        
        mock_qs_html.assert_called_once_with(
            "candidate_returns_series",
            benchmark="baseline_returns_series",
            output=str(Path("test_report.html")),
            title="MEQSAP Strategy Analysis Report"
        )

    @patch('quantstats.reports.html')
    def test_generate_report_single(self, mock_qs_html, mock_single_result):
        mock_single_result.candidate_result.returns = "candidate_returns_series"
        
        reporter = HtmlReporter(output_path="test_report.html")
        with patch.object(reporter, '_extract_returns', return_value="candidate_returns_series"):
            reporter.generate_report(mock_single_result)
        
        mock_qs_html.assert_called_once_with(
            "candidate_returns_series",
            output=str(Path("test_report.html")),
            title="MEQSAP Strategy Analysis Report"
        )

    def test_import_error(self, mock_comparative_result):
        with patch.dict('sys.modules', {'quantstats': None}):
            reporter = HtmlReporter()
            with pytest.raises(ReportingError, match="QuantStats not installed"):
                reporter.generate_report(mock_comparative_result)

class TestPdfReporter:
    @patch('meqsap.reporting.reporters.generate_pdf_report')
    def test_generate_report(self, mock_pdf_gen, mock_comparative_result):
        reporter = PdfReporter(output_path="test_report.pdf")
        reporter.generate_report(mock_comparative_result)
        mock_pdf_gen.assert_called_once_with(
            mock_comparative_result.candidate_result,
            str(Path("test_report.pdf"))
        )
