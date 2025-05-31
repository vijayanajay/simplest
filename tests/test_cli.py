"""
Unit tests for the CLI module.

Tests all CLI commands, options, error handling, and user interactions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock # Added MagicMock
from pathlib import Path
from typer.testing import CliRunner
from datetime import date
import yaml # For writing dummy config content

# Import the Typer app instance from your CLI module
from src.meqsap.cli import app
# Import custom exceptions and types
from src.meqsap.config import ConfigError, StrategyConfig
from src.meqsap.data import DataError
from src.meqsap.backtest import BacktestError, BacktestAnalysisResult, BacktestResult
from src.meqsap.reporting import ReportingError
from src.meqsap.exceptions import MEQSAPError


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
        # self.config_file = Path("test_config.yaml") # Will be created inside isolated_filesystem

        self.mock_config_obj = Mock(spec=StrategyConfig) # Use spec for better mocking
        self.mock_config_obj.strategy_type = "MovingAverageCrossover"
        self.mock_config_obj.ticker = "AAPL"
        self.mock_config_obj.start_date = date(2023, 1, 1)
        self.mock_config_obj.end_date = date(2023, 12, 31)

        self.mock_strategy_params = Mock()
        self.mock_strategy_params.model_dump.return_value = {
            "short_window": 10, "long_window": 30
        }
        self.mock_config_obj.validate_strategy_params.return_value = self.mock_strategy_params
        # Add model_dump to mock_config_obj if reporting needs it directly from config
        self.mock_config_obj.model_dump.return_value = {
            "ticker": "AAPL", "start_date": date(2023,1,1),
            "end_date": date(2023,12,31), "strategy_type": "MovingAverageCrossover",
            "strategy_params": {"fast_ma": 10, "slow_ma": 20}
        }


        self.mock_market_data = Mock(spec=Path) # Mocking as Path for simplicity
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


    @patch('src.meqsap.cli.generate_complete_report')
    @patch('src.meqsap.cli.run_complete_backtest')
    @patch('src.meqsap.cli.fetch_market_data')
    @patch('src.meqsap.cli.validate_config')
    @patch('src.meqsap.cli.load_yaml_config')
    def test_analyze_basic_success(
        self, mock_cli_load_yaml, mock_cli_validate_config, mock_cli_fetch_market_data,
        mock_cli_run_complete_backtest, mock_cli_generate_complete_report
    ):
        mock_cli_load_yaml.return_value = {"strategy": "test"}
        mock_cli_validate_config.return_value = self.mock_config_obj
        mock_cli_fetch_market_data.return_value = self.mock_market_data
        mock_cli_run_complete_backtest.return_value = self.mock_analysis_result
        mock_cli_generate_complete_report.return_value = None

        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            
            result = self.runner.invoke(app, ["analyze", str(config_file_path)])

        assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}\nException: {result.exception}"
        mock_cli_load_yaml.assert_called_once_with(str(config_file_path))
        mock_cli_validate_config.assert_called_once_with({"strategy": "test"})
        mock_cli_fetch_market_data.assert_called_once_with("AAPL", date(2023, 1, 1), date(2023, 12, 31))
        mock_cli_run_complete_backtest.assert_called_once_with(self.mock_config_obj, self.mock_market_data)
        mock_cli_generate_complete_report.assert_called_once_with(
            analysis_result=self.mock_analysis_result,
            include_pdf=False, output_directory="./reports",
            no_color=False, quiet=False
        )

    @patch('src.meqsap.cli.generate_complete_report') # Keep all mocks for consistency
    @patch('src.meqsap.cli.run_complete_backtest')
    @patch('src.meqsap.cli.fetch_market_data')
    @patch('src.meqsap.cli.validate_config')
    @patch('src.meqsap.cli.load_yaml_config')
    def test_analyze_validate_only(
        self, mock_cli_load_yaml, mock_cli_validate_config, mock_cli_fetch_market_data,
        mock_cli_run_complete_backtest, mock_cli_generate_complete_report
    ):
        mock_cli_load_yaml.return_value = {"strategy": "test"}
        mock_cli_validate_config.return_value = self.mock_config_obj

        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            
            result = self.runner.invoke(app, ["analyze", str(config_file_path), "--validate-only"])
        
        assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}\nException: {result.exception}"
        mock_cli_load_yaml.assert_called_once()
        mock_cli_validate_config.assert_called_once()
        mock_cli_fetch_market_data.assert_not_called()
        mock_cli_run_complete_backtest.assert_not_called()
        mock_cli_generate_complete_report.assert_not_called()


    @patch('src.meqsap.cli.generate_complete_report')
    @patch('src.meqsap.cli.run_complete_backtest')
    @patch('src.meqsap.cli.fetch_market_data')
    @patch('src.meqsap.cli.validate_config')
    @patch('src.meqsap.cli.load_yaml_config')
    def test_analyze_with_report_flag(
        self, mock_cli_load_yaml, mock_cli_validate_config, mock_cli_fetch_market_data,
        mock_cli_run_complete_backtest, mock_cli_generate_complete_report
    ):
        mock_cli_load_yaml.return_value = {"strategy": "test"}
        mock_cli_validate_config.return_value = self.mock_config_obj
        mock_cli_fetch_market_data.return_value = self.mock_market_data
        mock_cli_run_complete_backtest.return_value = self.mock_analysis_result
        mock_cli_generate_complete_report.return_value = "/path/to/report.pdf"
        
        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            
            custom_reports_dir_name = "custom_reports_test_dir"
            # The actual directory will be inside temp_dir
            
            result = self.runner.invoke(app, [
                "analyze", str(config_file_path),
                "--report", "--output-dir", custom_reports_dir_name
            ])

        assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}\nException: {result.exception}"
        # Typer resolves the path, so it will be absolute inside the temp_dir
        expected_output_dir = str((Path(temp_dir) / custom_reports_dir_name).resolve())

        mock_cli_generate_complete_report.assert_called_once_with(
            analysis_result=self.mock_analysis_result,
            include_pdf=True,
            output_directory=expected_output_dir,
            no_color=False, quiet=False
        )

    @patch('src.meqsap.cli.generate_complete_report')
    @patch('src.meqsap.cli.run_complete_backtest')
    @patch('src.meqsap.cli.fetch_market_data')
    @patch('src.meqsap.cli.validate_config')
    @patch('src.meqsap.cli.load_yaml_config')
    def test_analyze_verbose_mode(
        self, mock_cli_load_yaml, mock_cli_validate_config, mock_cli_fetch_market_data,
        mock_cli_run_complete_backtest, mock_cli_generate_complete_report
    ):
        mock_cli_load_yaml.return_value = {"strategy": "test"}
        mock_cli_validate_config.return_value = self.mock_config_obj
        mock_cli_fetch_market_data.return_value = self.mock_market_data
        mock_cli_run_complete_backtest.return_value = self.mock_analysis_result
        mock_cli_generate_complete_report.return_value = None

        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            result = self.runner.invoke(app, ["analyze", str(config_file_path), "--verbose"])
        
        assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}\nException: {result.exception}"
        assert "Strategy Parameters:" in result.stdout
        assert "Short Window" in result.stdout 
        assert "Data Sample (first 3 rows):" in result.stdout
        assert "Trade Details (first 5):" in result.stdout

    @patch('src.meqsap.cli.generate_complete_report')
    @patch('src.meqsap.cli.run_complete_backtest')
    @patch('src.meqsap.cli.fetch_market_data')
    @patch('src.meqsap.cli.validate_config')
    @patch('src.meqsap.cli.load_yaml_config')
    def test_analyze_quiet_mode(
        self, mock_cli_load_yaml, mock_cli_validate_config, mock_cli_fetch_market_data,
        mock_cli_run_complete_backtest, mock_cli_generate_complete_report
    ):
        mock_cli_load_yaml.return_value = {"strategy": "test"}
        mock_cli_validate_config.return_value = self.mock_config_obj
        mock_cli_fetch_market_data.return_value = self.mock_market_data
        mock_cli_run_complete_backtest.return_value = self.mock_analysis_result
        mock_cli_generate_complete_report.return_value = None

        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            result = self.runner.invoke(app, ["analyze", str(config_file_path), "--quiet"])

        assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}\nException: {result.exception}"
        mock_cli_generate_complete_report.assert_called_once_with(
            analysis_result=self.mock_analysis_result,
            include_pdf=False, output_directory="./reports",
            no_color=False, quiet=True
        )
        assert "Loading configuration from:" not in result.stdout
        assert "MEQSAP Analysis Configuration" not in result.stdout

    @patch('src.meqsap.cli.generate_complete_report')
    @patch('src.meqsap.cli.run_complete_backtest')
    @patch('src.meqsap.cli.fetch_market_data')
    @patch('src.meqsap.cli.validate_config')
    @patch('src.meqsap.cli.load_yaml_config')
    def test_analyze_no_color_mode(
        self, mock_cli_load_yaml, mock_cli_validate_config, mock_cli_fetch_market_data,
        mock_cli_run_complete_backtest, mock_cli_generate_complete_report
    ):
        mock_cli_load_yaml.return_value = {"strategy": "test"}
        mock_cli_validate_config.return_value = self.mock_config_obj
        mock_cli_fetch_market_data.return_value = self.mock_market_data
        mock_cli_run_complete_backtest.return_value = self.mock_analysis_result
        mock_cli_generate_complete_report.return_value = None

        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            result = self.runner.invoke(app, ["analyze", str(config_file_path), "--no-color"])

        assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}\nException: {result.exception}"
        mock_cli_generate_complete_report.assert_called_once_with(
            analysis_result=self.mock_analysis_result,
            include_pdf=False, output_directory="./reports",
            no_color=True, quiet=False
        )

class TestCLIErrorHandling:
    """Test error handling in CLI commands."""
    def setup_method(self):
        self.runner = CliRunner()
        # Config file will be created inside isolated_filesystem for each test

        self.mock_config_obj_for_errors = Mock(spec=StrategyConfig)
        self.mock_config_obj_for_errors.strategy_type = "TestStrategy"
        self.mock_config_obj_for_errors.ticker = "ANY"
        self.mock_config_obj_for_errors.start_date = date(2023,1,1)
        self.mock_config_obj_for_errors.end_date = date(2023,1,2)
        self.mock_config_obj_for_errors.validate_strategy_params.return_value = Mock()
        self.mock_config_obj_for_errors.validate_strategy_params.return_value.model_dump.return_value = {}


    @patch('src.meqsap.cli.load_yaml_config')
    def test_config_error_handling(self, mock_cli_load_yaml):
        mock_cli_load_yaml.side_effect = ConfigError("Invalid configuration format")
        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            # File needs to exist for Typer's 'exists=True' check, even if load_yaml_config is mocked
            with open(config_file_path, "w") as f: 
                f.write("dummy_content_for_exists_check")

            result = self.runner.invoke(app, ["analyze", str(config_file_path)])
        
        assert result.exit_code == 1, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}\nException: {result.exception}"
        assert "ConfigError:" in result.stdout # Changed from "Configuration Error:"
        assert "Invalid configuration format" in result.stdout

    @patch('src.meqsap.cli.fetch_market_data')
    @patch('src.meqsap.cli.validate_config')
    @patch('src.meqsap.cli.load_yaml_config')
    def test_data_error_handling(self, mock_cli_load_yaml, mock_cli_validate_config, mock_cli_fetch_market_data):
        mock_cli_load_yaml.return_value = {"strategy": "test"}
        mock_cli_validate_config.return_value = self.mock_config_obj_for_errors
        mock_cli_fetch_market_data.side_effect = DataError("Failed to fetch market data")

        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            result = self.runner.invoke(app, ["analyze", str(config_file_path)])

        assert result.exit_code == 1, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}\nException: {result.exception}"
        assert "DataError:" in result.stdout
        assert "Failed to fetch market data" in result.stdout

    @patch('src.meqsap.cli.run_complete_backtest')
    @patch('src.meqsap.cli.fetch_market_data')
    @patch('src.meqsap.cli.validate_config')
    @patch('src.meqsap.cli.load_yaml_config')
    def test_backtest_error_handling(
        self, mock_cli_load_yaml, mock_cli_validate_config, mock_cli_fetch_market_data, mock_cli_run_complete_backtest
    ):
        mock_cli_load_yaml.return_value = {"strategy": "test"}
        mock_cli_validate_config.return_value = self.mock_config_obj_for_errors
        mock_cli_fetch_market_data.return_value = Mock()
        mock_cli_run_complete_backtest.side_effect = BacktestError("Backtest execution failed")

        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            result = self.runner.invoke(app, ["analyze", str(config_file_path)])

        assert result.exit_code == 1, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}\nException: {result.exception}"
        assert "BacktestError:" in result.stdout
        assert "Backtest execution failed" in result.stdout

    @patch('src.meqsap.cli.generate_complete_report')
    @patch('src.meqsap.cli.run_complete_backtest')
    @patch('src.meqsap.cli.fetch_market_data')
    @patch('src.meqsap.cli.validate_config')
    @patch('src.meqsap.cli.load_yaml_config')
    def test_reporting_error_handling(
        self, mock_cli_load_yaml, mock_cli_validate_config, mock_cli_fetch_market_data,
        mock_cli_run_complete_backtest, mock_cli_generate_complete_report
    ):
        mock_cli_load_yaml.return_value = {"strategy": "test"}
        mock_cli_validate_config.return_value = self.mock_config_obj_for_errors
        mock_cli_fetch_market_data.return_value = Mock()
        mock_cli_run_complete_backtest.return_value = Mock(spec=BacktestAnalysisResult)
        mock_cli_generate_complete_report.side_effect = ReportingError("Failed to generate report")

        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            result = self.runner.invoke(app, ["analyze", str(config_file_path)])
        
        assert result.exit_code == 1, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}\nException: {result.exception}"
        assert "ReportingError:" in result.stdout
        assert "Failed to generate report" in result.stdout

    @patch('src.meqsap.cli.validate_config')
    @patch('src.meqsap.cli.load_yaml_config')
    def test_unexpected_error_handling(self, mock_cli_load_yaml, mock_cli_validate_config):
        mock_cli_load_yaml.return_value = {"strategy": "test"}
        mock_cli_validate_config.side_effect = Exception("Completely unexpected error occurred")

        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            result = self.runner.invoke(app, ["analyze", str(config_file_path)])

        assert result.exit_code == 1, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}\nException: {result.exception}"
        assert "An unexpected error occurred:" in result.stdout
        assert "Completely unexpected error occurred" in result.stdout

    @patch('src.meqsap.cli.traceback.print_exception')
    @patch('src.meqsap.cli.validate_config')
    @patch('src.meqsap.cli.load_yaml_config')
    def test_unexpected_error_verbose_traceback(
        self, mock_cli_load_yaml, mock_cli_validate_config, mock_cli_traceback_print_exception
    ):
        mock_cli_load_yaml.return_value = {"strategy": "test"}
        mock_cli_validate_config.side_effect = Exception("Another unexpected error")

        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            result = self.runner.invoke(app, ["analyze", str(config_file_path), "--verbose"])
        
        assert result.exit_code == 1, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}\nException: {result.exception}"
        assert "An unexpected error occurred:" in result.stdout
        assert "Another unexpected error" in result.stdout
        mock_cli_traceback_print_exception.assert_called_once()

class TestCLIVersionCommand:
    """Test the version command."""
    def setup_method(self):
        self.runner = CliRunner()

    @patch('src.meqsap.cli.__version__', "1.2.3")
    def test_version_command(self):
        result = self.runner.invoke(app, ["version"])
        assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}\nException: {result.exception}"
        assert "MEQSAP version: 1.2.3" in result.stdout

class TestCLIArgumentValidation:
    """Test CLI argument validation and parsing."""
    def setup_method(self):
        self.runner = CliRunner()

    def test_missing_config_file_argument(self):
        """Test error when config file argument is missing."""
        result = self.runner.invoke(app, ["analyze"])
        assert result.exit_code == 2, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}\nException: {result.exception}"
        assert "Missing argument 'CONFIG_FILE'" in result.stderr

    def test_nonexistent_config_file(self):
        """Test error when config file does not exist (Typer's exists=True)."""
        # No need for isolated_filesystem here as we are testing non-existence
        result = self.runner.invoke(app, ["analyze", "nonexistent_config.yaml"])
        assert result.exit_code == 2, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}\nException: {result.exception}"
        assert "Invalid value for 'CONFIG_FILE'" in result.stderr
        assert "'nonexistent_config.yaml' does not exist" in result.stderr # More specific check

    def test_help_command(self):
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}\nException: {result.exception}"
        assert "MEQSAP - Market Equity Quantitative Strategy Analysis Platform" in result.stdout
        assert "analyze" in result.stdout
        assert "version" in result.stdout

    def test_analyze_help(self):
        # For --help, Typer does not typically enforce `exists=True` for arguments.
        result = self.runner.invoke(app, ["analyze", "--help"])
        assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}\nException: {result.exception}"
        assert "Analyze a trading strategy using a YAML configuration file." in result.stdout
        assert "--validate-only" in result.stdout
        assert "--report" in result.stdout

class TestCLIIntegration:
    """Integration tests for CLI commands."""
    def setup_method(self):
        self.runner = CliRunner()
        # Config file will be created in isolated_filesystem

        self.mock_config_obj_integ = Mock(spec=StrategyConfig)
        self.mock_config_obj_integ.strategy_type = "MovingAverageCrossover"
        self.mock_config_obj_integ.ticker = "AAPL"
        self.mock_config_obj_integ.start_date = date(2023, 1, 1)
        self.mock_config_obj_integ.end_date = date(2023, 12, 31)
        
        mock_strat_params_integ = Mock()
        mock_strat_params_integ.model_dump.return_value = {"short_window": 10, "long_window": 30}
        self.mock_config_obj_integ.validate_strategy_params.return_value = mock_strat_params_integ
        self.mock_config_obj_integ.model_dump.return_value = {
            "ticker": "AAPL", "start_date": date(2023,1,1),
            "end_date": date(2023,12,31), "strategy_type": "MovingAverageCrossover",
            "strategy_params": {"fast_ma": 10, "slow_ma": 20}
        }


        self.mock_market_data_integ = Mock()
        self.mock_market_data_integ.__len__ = Mock(return_value=252)
        self.mock_market_data_integ.head.return_value = "DataFrame Head Integ"
        
        mock_primary_result_integ = Mock(spec=BacktestResult)
        mock_primary_result_integ.total_trades = 0 
        mock_primary_result_integ.trade_details = []
        mock_primary_result_integ.portfolio_value_series = {'2023-01-01': 10000.0}

        self.mock_analysis_result_integ = Mock(spec=BacktestAnalysisResult)
        self.mock_analysis_result_integ.primary_result = mock_primary_result_integ
        self.mock_analysis_result_integ.vibe_checks = Mock()
        self.mock_analysis_result_integ.robustness_checks = Mock()
        self.mock_analysis_result_integ.strategy_config = self.mock_config_obj_integ.model_dump()


    @patch('src.meqsap.cli.generate_complete_report')
    @patch('src.meqsap.cli.run_complete_backtest')
    @patch('src.meqsap.cli.fetch_market_data')
    @patch('src.meqsap.cli.validate_config')
    @patch('src.meqsap.cli.load_yaml_config')
    def test_full_workflow_integration(
        self, mock_cli_load_yaml, mock_cli_validate_config, mock_cli_fetch_market_data,
        mock_cli_run_complete_backtest, mock_cli_generate_complete_report
    ):
        mock_cli_load_yaml.return_value = {"strategy": "MovingAverageCrossover"}
        mock_cli_validate_config.return_value = self.mock_config_obj_integ
        mock_cli_fetch_market_data.return_value = self.mock_market_data_integ
        mock_cli_run_complete_backtest.return_value = self.mock_analysis_result_integ
        mock_cli_generate_complete_report.return_value = "/path/to/report.pdf"
        
        with self.runner.isolated_filesystem() as temp_dir:
            config_file_path = Path(temp_dir) / "test_integration_config.yaml"
            with open(config_file_path, "w") as f:
                f.write(DUMMY_YAML_CONTENT)
            
            custom_reports_dir_name = "test_reports_integration"
            # output_dir for invoke will be relative to temp_dir
            
            result = self.runner.invoke(app, [
                "analyze", str(config_file_path),
                "--verbose", "--report",
                "--output-dir", custom_reports_dir_name,
                "--no-color"
            ])

        assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}\nException: {result.exception}"
        expected_output_dir = str((Path(temp_dir) / custom_reports_dir_name).resolve())
        
        mock_cli_load_yaml.assert_called_once_with(str(config_file_path))
        mock_cli_validate_config.assert_called_once_with({"strategy": "MovingAverageCrossover"})
        mock_cli_fetch_market_data.assert_called_once_with("AAPL", date(2023, 1, 1), date(2023, 12, 31))
        mock_cli_run_complete_backtest.assert_called_once_with(self.mock_config_obj_integ, self.mock_market_data_integ)
        mock_cli_generate_complete_report.assert_called_once_with(
            analysis_result=self.mock_analysis_result_integ,
            include_pdf=True,
            output_directory=expected_output_dir,
            no_color=True,
            quiet=False
        )
