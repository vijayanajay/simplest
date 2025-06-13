import pytest
from unittest.mock import Mock, patch
import pandas as pd
from datetime import date

from src.meqsap.workflows.analysis import AnalysisWorkflow
from src.meqsap.config import StrategyConfig, BaselineConfig
from src.meqsap.exceptions import BacktestError, WorkflowError
from src.meqsap.backtest import BacktestAnalysisResult, BacktestResult, VibeCheckResults, RobustnessResults

@pytest.fixture
def mock_backtest_analysis_result_factory():
    def _factory(sharpe_ratio=1.5):
        mock_primary_result = Mock(spec=BacktestResult)
        mock_primary_result.sharpe_ratio = sharpe_ratio
        return BacktestAnalysisResult(
            primary_result=mock_primary_result,
            vibe_checks=Mock(spec=VibeCheckResults),
            robustness_checks=Mock(spec=RobustnessResults),
            strategy_config={'ticker': 'DUMMY'}
        )
    return _factory

@pytest.fixture
def mock_config():
    # A mock that behaves like a Pydantic model for .dict()
    config_mock = Mock(spec=StrategyConfig)
    config_mock.ticker = "AAPL"
    config_mock.start_date = date(2023, 1, 1)
    config_mock.end_date = date(2023, 12, 31)
    config_mock.model_dump.return_value = {
        "ticker": "AAPL",
        "start_date": date(2023, 1, 1),
        "end_date": date(2023, 12, 31),
    }
    return config_mock

@pytest.fixture
def mock_cli_flags():
    return {'no_baseline': False, 'report_html': False, 'report': False}

@pytest.fixture
def mock_market_data():
    return pd.DataFrame({'close': [100, 101, 102]})

class TestAnalysisWorkflow:
    @patch('src.meqsap.workflows.analysis.fetch_market_data')
    @patch('src.meqsap.workflows.analysis.run_complete_backtest')
    @patch('src.meqsap.workflows.analysis.ReportingOrchestrator')
    def test_execute_candidate_only(self, mock_orchestrator_cls, mock_run_backtest, mock_fetch_data, mock_config, mock_backtest_analysis_result_factory, mock_market_data):
        cli_flags = {'no_baseline': True, 'report_html': False, 'report': False}
        mock_config.get_baseline_config_with_defaults.return_value = None
        mock_run_backtest.return_value = mock_backtest_analysis_result_factory()
        mock_fetch_data.return_value = mock_market_data

        workflow = AnalysisWorkflow(mock_config, cli_flags)
        workflow.execute()

        mock_fetch_data.assert_called_once()
        mock_run_backtest.assert_called_once_with(mock_config, mock_market_data)
        mock_orchestrator_cls.return_value.add_reporter.assert_called()
        mock_orchestrator_cls.return_value.generate_reports.assert_called_once()

    @patch('src.meqsap.workflows.analysis.fetch_market_data')
    @patch('src.meqsap.workflows.analysis.run_complete_backtest')
    @patch('src.meqsap.workflows.analysis.ReportingOrchestrator')
    def test_execute_with_baseline(self, mock_orchestrator_cls, mock_run_backtest, mock_fetch_data, mock_config, mock_backtest_analysis_result_factory, mock_market_data):
        cli_flags = {'no_baseline': False, 'report_html': False, 'report': False}
        baseline_config = BaselineConfig(strategy_type="BuyAndHold", active=True)
        mock_config.get_baseline_config_with_defaults.return_value = baseline_config
        candidate_result = mock_backtest_analysis_result_factory(sharpe_ratio=1.5)
        baseline_result = mock_backtest_analysis_result_factory(sharpe_ratio=1.0)
        mock_run_backtest.side_effect = [candidate_result, baseline_result]
        mock_fetch_data.return_value = mock_market_data

        workflow = AnalysisWorkflow(mock_config, cli_flags)
        workflow.execute()

        mock_fetch_data.assert_called_once()
        assert mock_run_backtest.call_count == 2
        mock_orchestrator_cls.return_value.add_reporter.assert_called()

    @patch('src.meqsap.workflows.analysis.fetch_market_data')
    @patch('src.meqsap.workflows.analysis.run_complete_backtest')
    @patch('src.meqsap.workflows.analysis.ReportingOrchestrator')
    def test_execute_baseline_fails_gracefully(self, mock_orchestrator_cls, mock_run_backtest, mock_fetch_data, mock_config, mock_backtest_analysis_result_factory, mock_market_data):
        cli_flags = {'no_baseline': False, 'report_html': False, 'report': False}
        baseline_config = BaselineConfig(strategy_type="BuyAndHold", active=True)
        mock_config.get_baseline_config_with_defaults.return_value = baseline_config
        candidate_result = mock_backtest_analysis_result_factory()
        mock_run_backtest.side_effect = [candidate_result, BacktestError("Baseline failed")]
        mock_fetch_data.return_value = mock_market_data

        workflow = AnalysisWorkflow(mock_config, cli_flags)
        result = workflow.execute()

        mock_fetch_data.assert_called_once()
        assert mock_run_backtest.call_count == 2
        assert result.baseline_failed is True
        assert "Baseline strategy execution failed" in result.baseline_failure_reason
        assert result.comparative_verdict is None
        mock_orchestrator_cls.return_value.generate_reports.assert_called_once()

    @patch('src.meqsap.workflows.analysis.fetch_market_data')
    @patch('src.meqsap.workflows.analysis.run_complete_backtest')
    def test_execute_candidate_fails(self, mock_run_backtest, mock_fetch_data, mock_config, mock_cli_flags, mock_market_data):  # noqa
        mock_fetch_data.return_value = mock_market_data
        mock_run_backtest.side_effect = BacktestError("Candidate failed")
        
        workflow = AnalysisWorkflow(mock_config, mock_cli_flags)
        
        with pytest.raises(BacktestError, match="Candidate strategy backtest failed"):
            workflow.execute()
