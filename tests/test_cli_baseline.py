import pytest
from pathlib import Path
from unittest.mock import patch, Mock
from typer.testing import CliRunner

from src.meqsap.cli import app as main_app
from src.meqsap.cli.commands.analyze import analyze as analyze_command
from src.meqsap.workflows.analysis import AnalysisWorkflow
from src.meqsap.config import StrategyConfig, BaselineConfig
from src.meqsap.exceptions import BacktestError, WorkflowError
from src.meqsap.backtest import BacktestAnalysisResult, BacktestResult, VibeCheckResults, RobustnessResults

@pytest.fixture
def runner():
    return CliRunner()

@patch('src.meqsap.cli.commands.analyze.validate_config')
@patch('src.meqsap.cli.commands.analyze.load_yaml_config')
@patch('src.meqsap.cli.commands.analyze.AnalysisWorkflow')
def test_analyze_with_report_html(mock_workflow_cls, mock_load_config, mock_validate_config, runner):
    """
    Verifies that the '--report-html' flag is correctly parsed and passed
    to the AnalysisWorkflow.
    """
    mock_workflow_instance = Mock(spec=AnalysisWorkflow)
    mock_workflow_cls.return_value = mock_workflow_instance
    mock_load_config.return_value = {}
    mock_validate_config.return_value = Mock(spec=StrategyConfig)
    with runner.isolated_filesystem():
        with open("config.yaml", "w") as f:
            f.write("ticker: AAPL")
        
        result = runner.invoke(main_app, ["analyze", "config.yaml", "--report-html"])
        
        assert result.exit_code == 0
        mock_load_config.assert_called_once_with(Path("config.yaml"))
        mock_validate_config.assert_called_once()
        mock_workflow_cls.assert_called_once()
        _config, cli_flags = mock_workflow_cls.call_args.args
        assert cli_flags['report_html'] is True
        assert cli_flags['no_baseline'] is False
        assert cli_flags['report'] is False

        mock_workflow_instance.execute.assert_called_once()

@patch('src.meqsap.cli.commands.analyze.validate_config')
@patch('src.meqsap.cli.commands.analyze.load_yaml_config')
@patch('src.meqsap.cli.commands.analyze.AnalysisWorkflow')
def test_analyze_with_no_baseline(mock_workflow_cls, mock_load_config, mock_validate_config, runner):
    """
    Verifies that the '--no-baseline' flag is correctly parsed and passed
    to the AnalysisWorkflow.
    """
    mock_workflow_instance = Mock(spec=AnalysisWorkflow)
    mock_workflow_cls.return_value = mock_workflow_instance
    mock_load_config.return_value = {}
    mock_validate_config.return_value = Mock(spec=StrategyConfig)
    with runner.isolated_filesystem():
        with open("config.yaml", "w") as f:
            f.write("ticker: AAPL")
        
        result = runner.invoke(main_app, ["analyze", "config.yaml", "--no-baseline"])
        
        assert result.exit_code == 0
        mock_load_config.assert_called_once_with(Path("config.yaml"))
        mock_validate_config.assert_called_once()
        mock_workflow_cls.assert_called_once()
        _config, cli_flags = mock_workflow_cls.call_args.args
        assert cli_flags['no_baseline'] is True
        assert cli_flags['report_html'] is False
        assert cli_flags['report'] is False

        mock_workflow_instance.execute.assert_called_once()

def test_analyze_help_includes_flags(runner):
    """
    Verifies that the help text for the 'analyze' command includes the new
    baseline-related flags.
    """
    result = runner.invoke(main_app, ["analyze", "--help"])
    
    assert result.exit_code == 0
    assert "--report-html" in result.stdout
    assert "Generate comprehensive HTML report" in result.stdout
    assert "--no-baseline" in result.stdout
    assert "Skip baseline comparison" in result.stdout
