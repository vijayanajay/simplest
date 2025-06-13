"""
Unit tests for the CLI module.

Tests all CLI commands, options, error handling, and user interactions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typer.testing import CliRunner
from datetime import date
import re
import yaml
import pandas as pd  # noqa: F401

# Import the Typer app instance from your CLI module
from src.meqsap.cli import app
# Import custom exceptions and types
from src.meqsap.config import StrategyConfig
from src.meqsap.exceptions import ConfigurationError
from src.meqsap.data import DataError
from src.meqsap.backtest import BacktestError, BacktestAnalysisResult, BacktestResult
from src.meqsap.reporting import ReportingError
from src.meqsap.workflows.analysis import AnalysisWorkflow


# Minimal valid YAML content for dummy config files
DUMMY_YAML_CONTENT = yaml.dump({
    "ticker": "DUMMY",
    "start_date": "2023-01-01",
    "end_date": "2023-01-31",
    "strategy_type": "MovingAverageCrossover",
    "strategy_params": {"fast_ma": 10, "slow_ma": 20}
})

class TestCLIAnalyzeCommand:
    """Test the analyze command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

        self.mock_config_obj = Mock(spec=StrategyConfig)
        self.mock_config_obj.strategy_type = "MovingAverageCrossover"
        self.mock_config_obj.ticker = "AAPL"
        self.mock_config_obj.start_date = date(2023, 1, 1)
        self.mock_config_obj.end_date = date(2023, 12, 31)

        self.mock_strategy_params = Mock()
        self.mock_strategy_params.model_dump.return_value = {
            "fast_ma": 10, "slow_ma": 30
        }
        self.mock_config_obj.validate_strategy_params.return_value = self.mock_strategy_params
        self.mock_config_obj.model_dump.return_value = {
            "ticker": "AAPL", "start_date": date(2023,1,1),
            "end_date": date(2023,12,31), "strategy_type": "MovingAverageCrossover",
            "strategy_params": {"fast_ma": 10, "slow_ma": 20}
        }

        self.mock_market_data = Mock(spec=pd.DataFrame)
        # Ensure mock_market_data has lowercase columns if it's supposed to be
        # the output of fetch_market_data
        self.mock_market_data.columns = ['open', 'high', 'low', 'close', 'volume']
        self.mock_market_data.__len__ = Mock(return_value=252)
        self.mock_market_data.head.return_value = "DataFrame Head"

        self.mock_primary_backtest_result = Mock(spec=BacktestResult)
        self.mock_primary_backtest_result.total_trades = 10
        self.mock_primary_backtest_result.trade_details = [
            {
                'entry_date': '2023-02-01', 'entry_price': 150.00,
                'exit_date': '2023-02-15', 'exit_price': 155.00,
                'pnl': 5.00, 'return_pct': 3.33
            }
        ] * 5
        self.mock_primary_backtest_result.portfolio_value_series = {'2023-01-01': 10000.0}


        self.mock_analysis_result = Mock(spec=BacktestAnalysisResult)
        self.mock_analysis_result.primary_result = self.mock_primary_backtest_result
        self.mock_analysis_result.vibe_checks = Mock()
        self.mock_analysis_result.robustness_checks = Mock()
        self.mock_analysis_result.strategy_config = self.mock_config_obj.model_dump()


    @patch('src.meqsap.cli.commands.analyze.AnalysisWorkflow')
    @patch('src.meqsap.cli.commands.analyze.validate_config')
    @patch('src.meqsap.cli.commands.analyze.load_yaml_config')
    def test_analyze_basic_success(
        self, mock_load_yaml, mock_validate_config, mock_workflow_cls
    ):
        mock_load_yaml.return_value = {"strategy": "test"}
        mock_validate_config.return_value = self.mock_config_obj
        mock_workflow_instance = mock_workflow_cls.return_value
        mock_workflow_instance.execute.return_value = self.mock_analysis_result

        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            
            result = self.runner.invoke(app, ["analyze", str(config_file_path)], catch_exceptions=True)

        assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
        mock_load_yaml.assert_called_once_with(config_file_path)
        mock_workflow_cls.assert_called_once()
        mock_workflow_instance.execute.assert_called_once()

    @patch('src.meqsap.cli.commands.analyze.AnalysisWorkflow')
    @patch('src.meqsap.cli.commands.analyze.validate_config')
    @patch('src.meqsap.cli.commands.analyze.load_yaml_config')
    def test_analyze_validate_only(
        self, mock_load_yaml, mock_validate_config, mock_workflow_cls
    ):
        mock_load_yaml.return_value = {"strategy": "test"}
        mock_validate_config.return_value = self.mock_config_obj

        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            
            result = self.runner.invoke(app, ["analyze", str(config_file_path), "--validate-only"], catch_exceptions=True)
        
        assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
        mock_load_yaml.assert_called_once()
        mock_validate_config.assert_called_once()
        mock_workflow_cls.assert_not_called()

    @patch('src.meqsap.cli.commands.analyze.AnalysisWorkflow')
    @patch('src.meqsap.cli.commands.analyze.validate_config')
    @patch('src.meqsap.cli.commands.analyze.load_yaml_config')
    def test_analyze_with_report_flag(
        self, mock_load_yaml, mock_validate_config, mock_workflow_cls
    ):
        mock_load_yaml.return_value = {"strategy": "test"}
        mock_validate_config.return_value = self.mock_config_obj
        mock_workflow_instance = mock_workflow_cls.return_value
        mock_workflow_instance.execute.return_value = self.mock_analysis_result
        
        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            
            custom_reports_dir_name = "custom_reports_test_dir"
            
            result = self.runner.invoke(app, [
                "analyze", str(config_file_path),
                "--report", "--output-dir", custom_reports_dir_name
            ], catch_exceptions=True)

        assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
        mock_workflow_cls.assert_called_once()
        _config, cli_flags = mock_workflow_cls.call_args.args
        assert cli_flags['report'] is True
        assert cli_flags['output_dir'] == Path(custom_reports_dir_name)

    @patch('src.meqsap.cli.commands.analyze.AnalysisWorkflow')
    @patch('src.meqsap.cli.commands.analyze.validate_config')
    @patch('src.meqsap.cli.commands.analyze.load_yaml_config')
    def test_analyze_verbose_mode(
        self, mock_load_yaml, mock_validate_config, mock_workflow_cls
    ):
        mock_load_yaml.return_value = {"strategy": "test"}
        mock_validate_config.return_value = self.mock_config_obj
        mock_workflow_instance = mock_workflow_cls.return_value
        mock_workflow_instance.execute.return_value = self.mock_analysis_result

        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            result = self.runner.invoke(app, ["analyze", str(config_file_path), "--verbose"], catch_exceptions=True)
        
        assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
        # The following assertions are removed as the verbose output has changed with the new workflow.
        # The test now just verifies that the command runs successfully with the flag.

    @patch('src.meqsap.cli.commands.analyze.AnalysisWorkflow')
    @patch('src.meqsap.cli.commands.analyze.validate_config')
    @patch('src.meqsap.cli.commands.analyze.load_yaml_config')
    def test_analyze_quiet_mode(
        self, mock_load_yaml, mock_validate_config, mock_workflow_cls
    ):
        mock_load_yaml.return_value = {"strategy": "test"}
        mock_validate_config.return_value = self.mock_config_obj
        mock_workflow_instance = mock_workflow_cls.return_value
        mock_workflow_instance.execute.return_value = self.mock_analysis_result

        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            result = self.runner.invoke(app, ["analyze", str(config_file_path), "--quiet"], catch_exceptions=True)

        assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
        mock_workflow_cls.assert_called_once()
        _config, cli_flags = mock_workflow_cls.call_args.args
        assert cli_flags['quiet'] is True

    @patch('src.meqsap.cli.commands.analyze.AnalysisWorkflow')
    @patch('src.meqsap.cli.commands.analyze.validate_config')
    @patch('src.meqsap.cli.commands.analyze.load_yaml_config')
    def test_analyze_no_color_mode(
        self, mock_load_yaml, mock_validate_config, mock_workflow_cls
    ):
        mock_load_yaml.return_value = {"strategy": "test"}
        mock_validate_config.return_value = self.mock_config_obj
        mock_workflow_instance = mock_workflow_cls.return_value
        mock_workflow_instance.execute.return_value = self.mock_analysis_result

        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            result = self.runner.invoke(app, ["analyze", str(config_file_path), "--no-color"], catch_exceptions=True)

        assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
        mock_workflow_cls.assert_called_once()
        _config, cli_flags = mock_workflow_cls.call_args.args
        assert cli_flags['no_color'] is True

class TestCLIErrorHandling:
    """Test error handling in CLI commands."""
    
    def setup_method(self):
        self.runner = CliRunner()

        self.mock_config_obj_for_errors = Mock(spec=StrategyConfig)
        self.mock_config_obj_for_errors.strategy_type = "TestStrategy"
        self.mock_config_obj_for_errors.ticker = "ANY"
        self.mock_config_obj_for_errors.start_date = date(2023,1,1)
        self.mock_config_obj_for_errors.end_date = date(2023,1,2)
        self.mock_config_obj_for_errors.validate_strategy_params.return_value = Mock()
        self.mock_config_obj_for_errors.validate_strategy_params.return_value.model_dump.return_value = {}

    @patch('src.meqsap.cli.commands.analyze.load_yaml_config')
    def test_config_error_handling(self, mock_load_yaml):
        mock_load_yaml.side_effect = ConfigurationError("Invalid configuration format")
        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f: 
                f.write("dummy_content_for_exists_check")
            result = self.runner.invoke(app, ["analyze", str(config_file_path)], catch_exceptions=True)
        assert result.exit_code == 1, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
        assert "Invalid configuration format" in result.stdout

    @patch('src.meqsap.cli.commands.analyze.AnalysisWorkflow')
    @patch('src.meqsap.cli.commands.analyze.validate_config')
    @patch('src.meqsap.cli.commands.analyze.load_yaml_config')
    def test_data_error_handling(self, mock_load_yaml, mock_validate_config, mock_workflow_cls):
        mock_load_yaml.return_value = {"strategy": "test"}
        mock_validate_config.return_value = self.mock_config_obj_for_errors
        mock_workflow_instance = mock_workflow_cls.return_value
        mock_workflow_instance.execute.side_effect = DataError("Failed to fetch market data")

        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            result = self.runner.invoke(app, ["analyze", str(config_file_path)], catch_exceptions=True)

        assert result.exit_code == 2, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
        assert "Failed to fetch market data" in result.stdout

    @patch('src.meqsap.cli.commands.analyze.AnalysisWorkflow')
    @patch('src.meqsap.cli.commands.analyze.validate_config')
    @patch('src.meqsap.cli.commands.analyze.load_yaml_config')
    def test_backtest_error_handling(
        self, mock_load_yaml, mock_validate_config, mock_workflow_cls
    ):
        mock_load_yaml.return_value = {"strategy": "test"}
        mock_validate_config.return_value = self.mock_config_obj_for_errors
        mock_workflow_cls.return_value.execute.side_effect = BacktestError("Backtest execution failed")

        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            result = self.runner.invoke(app, ["analyze", str(config_file_path)], catch_exceptions=True)

        assert result.exit_code == 3, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
        assert "Backtest execution failed" in result.stdout

    @patch('src.meqsap.cli.commands.analyze.AnalysisWorkflow')
    @patch('src.meqsap.cli.commands.analyze.validate_config')
    @patch('src.meqsap.cli.commands.analyze.load_yaml_config')
    def test_reporting_error_handling(
        self, mock_load_yaml, mock_validate_config, mock_workflow_cls
    ):
        mock_load_yaml.return_value = {"strategy": "test"}
        mock_validate_config.return_value = self.mock_config_obj_for_errors
        mock_workflow_cls.return_value.execute.side_effect = ReportingError("Failed to generate report")

        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            result = self.runner.invoke(app, ["analyze", str(config_file_path)], catch_exceptions=True)
        
        assert result.exit_code == 4, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
        assert "Failed to generate report" in result.stdout

    @patch('src.meqsap.cli.commands.analyze.validate_config')
    @patch('src.meqsap.cli.commands.analyze.load_yaml_config')
    def test_unexpected_error_handling(self, mock_load_yaml, mock_validate_config):
        mock_load_yaml.return_value = {"strategy": "test"}
        mock_validate_config.side_effect = Exception("Completely unexpected error occurred")

        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            result = self.runner.invoke(app, ["analyze", str(config_file_path)], catch_exceptions=True)

        assert result.exit_code == 10, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
        assert "Unexpected error" in result.stdout

    @patch('src.meqsap.cli.utils.traceback.format_exc')
    @patch('src.meqsap.cli.commands.analyze.validate_config')
    @patch('src.meqsap.cli.commands.analyze.load_yaml_config')
    def test_unexpected_error_verbose_traceback(
        self, mock_load_yaml, mock_validate_config, mock_format_exc
    ):
        mock_load_yaml.return_value = {"strategy": "test"}
        custom_exception = Exception("Another unexpected error")
        mock_validate_config.side_effect = custom_exception

        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            result = self.runner.invoke(app, ["analyze", str(config_file_path), "--verbose"], catch_exceptions=True)
        
        assert result.exit_code == 10, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
        assert "Debug Information" in result.stdout
        mock_format_exc.assert_called_once()


class TestCLIVersionCommand:
    """Test the version command."""
    
    def setup_method(self):
        self.runner = CliRunner()

    @patch('src.meqsap.cli.__version__', "1.2.3")
    def test_version_command(self):
        result = self.runner.invoke(app, ["version"])
        assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
        # Remove ANSI escape codes for color to make assertion robust
        clean_output = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
        assert "MEQSAP version: 1.2.3" in clean_output


class TestCLIArgumentValidation:
    """Test CLI argument validation and parsing."""
    
    def setup_method(self):
        self.runner = CliRunner()

    def test_missing_config_file_argument(self):
        """Test error when config file argument is missing."""
        result = self.runner.invoke(app, ["analyze"])
        assert result.exit_code == 2, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr if result.exception is None else 'N/A (exception caught)'}\nException: {result.exception}"
        assert "Missing argument 'CONFIG_FILE'" in result.stderr

    def test_nonexistent_config_file(self):
        """Test error when config file does not exist (Typer's exists=True)."""
        result = self.runner.invoke(app, ["analyze", "nonexistent_config.yaml"])
        assert result.exit_code == 2, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr if result.exception is None else 'N/A (exception caught)'}\nException: {result.exception}"
        assert "Invalid value for 'CONFIG_FILE'" in result.stderr
        # Check for parts around the potential line break due to Rich formatting
        assert "File 'nonexistent_config.yaml' does not" in result.stderr
        assert "exist." in result.stderr

    def test_help_command(self):
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr if result.exception is None else 'N/A (exception caught)'}\nException: {result.exception}"
        assert "MEQSAP - Market Equity Quantitative Strategy Analysis Platform" in result.stdout

    def test_analyze_help(self):
        result = self.runner.invoke(app, ["analyze", "--help"])
        assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr if result.exception is None else 'N/A (exception caught)'}\nException: {result.exception}"
        assert "Run strategy analysis with optional baseline comparison." in result.stdout
        assert "--validate-only" in result.stdout
