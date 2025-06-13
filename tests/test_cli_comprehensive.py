"""
Comprehensive test suite for CLI integration and error handling.
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path
from datetime import date
from unittest.mock import Mock, patch, MagicMock
from typer.testing import CliRunner
import pandas as pd
from io import StringIO

from src.meqsap.cli import app
from src.meqsap.config import StrategyConfig
from src.meqsap.exceptions import ConfigurationError
from src.meqsap.data import DataError, fetch_market_data
from src.meqsap.backtest import BacktestError, BacktestAnalysisResult, BacktestResult
from src.meqsap.reporting import ReportingError
from src.meqsap.exceptions import MEQSAPError


class TestConfigurationErrorScenarios:
    """Test various configuration error scenarios and recovery suggestions."""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_missing_required_fields(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""ticker: "AAPL" # Missing strategy_type, start_date, end_date""")
            config_file = f.name
        try:
            result = self.runner.invoke(app, ["analyze", config_file], catch_exceptions=True)
            assert result.exit_code == 1, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}"
            assert "Configuration validation failed" in result.stdout
            assert "Field required" in result.stdout
        finally:
            os.unlink(config_file)
    
    def test_invalid_date_formats(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
strategy_type: "MovingAverageCrossover"
ticker: "AAPL"
start_date: "invalid-date-format"
end_date: "2023-12-31"
strategy_params: {"fast_ma": 10, "slow_ma": 20}""")
            config_file = f.name
        try:
            result = self.runner.invoke(app, ["analyze", config_file], catch_exceptions=True)
            assert result.exit_code == 1, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}"
            assert "Input should be a valid date" in result.stdout
        finally:
            os.unlink(config_file)
    
    def test_invalid_parameter_ranges(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
strategy_type: "MovingAverageCrossover"
ticker: "AAPL"
start_date: "2023-01-01"
end_date: "2023-12-31"
strategy_params: { "fast_ma": -5, "slow_ma": 20 }""")
            config_file = f.name
        try:
            result = self.runner.invoke(app, ["analyze", config_file], catch_exceptions=True)
            assert result.exit_code == 1, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}"
            assert "fast_ma must be positive" in result.stdout
        finally:
            os.unlink(config_file)
    
    def test_malformed_yaml_syntax(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
strategy_type: "MovingAverageCrossover"
ticker: "AAPL"
  start_date: "2023-01-01" # Malformed
end_date: "2023-12-31"
strategy_params: {"fast_ma": 10, "slow_ma": 20}""")
            config_file = f.name
        try:
            result = self.runner.invoke(app, ["analyze", config_file], catch_exceptions=True)
            assert result.exit_code == 1, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}"
            assert "Invalid YAML" in result.stdout
        finally:
            os.unlink(config_file)
    
    def test_circular_date_range(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
strategy_type: "MovingAverageCrossover"
ticker: "AAPL"
start_date: "2023-12-31"
end_date: "2023-01-01"
strategy_params: {"fast_ma": 10, "slow_ma": 20}""")
            config_file = f.name
        try:
            result = self.runner.invoke(app, ["analyze", config_file], catch_exceptions=True)
            assert result.exit_code == 1, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}"
            assert "end_date must be after start_date" in result.stdout
        finally:
            os.unlink(config_file)

class TestDataAcquisitionErrorScenarios:
    def setup_method(self):
        self.runner = CliRunner()
    
    @patch('src.meqsap.workflows.analysis.fetch_market_data')
    def test_network_connection_failure(self, mock_fetch_data):
        mock_fetch_data.side_effect = DataError("Connection timeout")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
strategy_type: "MovingAverageCrossover"
ticker: "GOODTICKER"
start_date: "2023-01-01"
end_date: "2023-12-31"
strategy_params: {"fast_ma": 10, "slow_ma": 20}""")
            config_file = f.name
        try:
            result = self.runner.invoke(app, ["analyze", config_file], catch_exceptions=True)
            assert result.exit_code == 2, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
            assert "Connection timeout" in result.stdout
        finally:            os.unlink(config_file)
    
    @patch('src.meqsap.workflows.analysis.fetch_market_data')
    @patch('src.meqsap.cli.commands.analyze.validate_config')
    @patch('src.meqsap.cli.commands.analyze.load_yaml_config')
    def test_invalid_ticker_symbol(self, mock_load_yaml, mock_validate_config, mock_fetch_data):
        mock_config_obj = Mock(spec=StrategyConfig)
        mock_config_obj.strategy_type = "MovingAverageCrossover"
        mock_config_obj.ticker = "MOCKFAIL"
        mock_config_obj.start_date = date(2023,1,1)
        mock_config_obj.end_date = date(2023,12,31)

        # Fix: The returned mock must be iterable for the for-loop in _validate_and_load_config
        # by having a model_dump method that returns a dictionary.
        mock_strategy_params = Mock()
        mock_strategy_params.model_dump.return_value = {}
        mock_config_obj.validate_strategy_params.return_value = mock_strategy_params

        mock_load_yaml.return_value = {"ticker": "MOCKFAIL", "strategy_type": "MovingAverageCrossover", "start_date": "2023-01-01", "end_date": "2023-12-31"}
        mock_validate_config.return_value = mock_config_obj

        mock_fetch_data.side_effect = DataError("No data found for symbol MOCKFAIL")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
strategy_type: "MovingAverageCrossover"
ticker: "MOCKFAIL"
start_date: "2023-01-01"
end_date: "2023-12-31"
strategy_params: {"fast_ma": 10, "slow_ma": 20}""")
            config_file = f.name
        try:
            result = self.runner.invoke(app, ["analyze", config_file], catch_exceptions=True)
            assert result.exit_code == 2, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
            assert "No data found for symbol MOCKFAIL" in result.stdout
        finally:            os.unlink(config_file)
    
    @patch('src.meqsap.workflows.analysis.run_complete_backtest')
    @patch('src.meqsap.workflows.analysis.fetch_market_data')
    def test_insufficient_data_period(self, mock_fetch_data, mock_run_backtest):
        mock_fetch_data.return_value = pd.DataFrame({'open': [100], 'close': [100]})
        mock_run_backtest.side_effect = BacktestError("Insufficient data points for MA 50/100")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
strategy_type: "MovingAverageCrossover"
ticker: "AAPL"
start_date: "2023-01-01"
end_date: "2023-01-02"
strategy_params: {"fast_ma": 50, "slow_ma": 100}""")
            config_file = f.name
        try:
            result = self.runner.invoke(app, ["analyze", config_file], catch_exceptions=True)
            assert result.exit_code == 3, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
            assert "Insufficient data points" in result.stdout
        finally:            os.unlink(config_file)
    
    @patch('src.meqsap.workflows.analysis.fetch_market_data')
    def test_api_rate_limiting(self, mock_fetch_data):
        mock_fetch_data.side_effect = DataError("Rate limit exceeded")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
strategy_type: "MovingAverageCrossover"
ticker: "AAPL"
start_date: "2023-01-01"
end_date: "2023-12-31"
strategy_params: {"fast_ma": 10, "slow_ma": 20}""")
            config_file = f.name
        try:
            result = self.runner.invoke(app, ["analyze", config_file], catch_exceptions=True)
            assert result.exit_code == 2, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
            assert "Rate limit exceeded" in result.stdout
        finally:
            os.unlink(config_file)

class TestBacktestExecutionErrorScenarios:
    def setup_method(self):
        self.runner = CliRunner()
    
    @patch('src.meqsap.workflows.analysis.run_complete_backtest')
    @patch('src.meqsap.workflows.analysis.fetch_market_data')
    def test_mathematical_computation_errors(self, mock_fetch_data, mock_run_backtest):
        mock_fetch_data.return_value = pd.DataFrame({
            'open':[100],'high':[100],'low':[100],
            'close':[100],'volume':[100]
        })
        mock_run_backtest.side_effect = BacktestError("Division by zero in Sharpe calculation")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
strategy_type: "MovingAverageCrossover"
ticker: "AAPL"
start_date: "2023-01-01"
end_date: "2023-12-31"
strategy_params: {"fast_ma": 10, "slow_ma": 20}""")
            config_file = f.name
        try:
            result = self.runner.invoke(app, ["analyze", config_file], catch_exceptions=True)
            assert result.exit_code == 3, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
            assert "Division by zero" in result.stdout
        finally:            os.unlink(config_file)
    
    @patch('src.meqsap.workflows.analysis.run_complete_backtest')
    @patch('src.meqsap.workflows.analysis.fetch_market_data')
    def test_memory_exhaustion_errors(self, mock_fetch_data, mock_run_backtest):
        mock_fetch_data.return_value = pd.DataFrame({
            'open':[100,101,102],'high':[100,101,102],'low':[100,101,102],
            'close':[100,101,102],'volume':[100,101,102]
        })
        mock_run_backtest.side_effect = MemoryError("Not enough memory")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
strategy_type: "MovingAverageCrossover"
ticker: "AAPL"
start_date: "2023-01-01"
end_date: "2023-12-31"
strategy_params: {"fast_ma": 10, "slow_ma": 20}""")
            config_file = f.name
        try:
            result = self.runner.invoke(app, ["analyze", config_file], catch_exceptions=True)
            assert result.exit_code == 3, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
            assert "Not enough memory" in result.stdout
        finally:            os.unlink(config_file)
    
    @patch('src.meqsap.cli.commands.analyze.validate_config')
    @patch('src.meqsap.cli.commands.analyze.load_yaml_config')
    def test_invalid_strategy_parameters(self, mock_load_yaml_config, mock_validate_config):
        mock_load_yaml_config.return_value = {
            "strategy_type": "MovingAverageCrossover", "ticker": "AAPL",
            "start_date": "2023-01-01", "end_date": "2023-12-31",
            "strategy_params": {"fast_ma": 50, "slow_ma": 10}        }
        mock_validate_config.side_effect = ConfigurationError("Fast MA (50) must be less than Slow MA (10).")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
strategy_type: "MovingAverageCrossover"
ticker: "AAPL"
start_date: "2023-01-01"
end_date: "2023-12-31"
strategy_params: { "fast_ma": 50, "slow_ma": 10 } """)
            config_file = f.name
        try:
            result = self.runner.invoke(app, ["analyze", config_file], catch_exceptions=True)
            assert result.exit_code == 1, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
            assert "Fast MA (50) must be less than Slow MA (10)" in result.stdout
        finally:
            os.unlink(config_file)

class TestReportGenerationErrorScenarios:
    def setup_method(self):
        self.runner = CliRunner()
    
    @patch('src.meqsap.workflows.analysis.ReportingOrchestrator')
    @patch('src.meqsap.workflows.analysis.run_complete_backtest')
    @patch('src.meqsap.workflows.analysis.fetch_market_data')
    def test_pdf_generation_permission_error(self, mock_fetch_data, mock_run_backtest, mock_orchestrator_cls):
        mock_fetch_data.return_value = pd.DataFrame({'close': [100]})
        # Fix: Provide a more complete mock to avoid AttributeError downstream
        mock_analysis_result = Mock(spec=BacktestAnalysisResult)
        mock_primary_result = Mock(spec=BacktestResult)
        mock_primary_result.sharpe_ratio = 1.0
        mock_analysis_result.primary_result = mock_primary_result
        mock_run_backtest.return_value = mock_analysis_result
        mock_orchestrator_cls.return_value.generate_reports.side_effect = ReportingError("Permission denied for PDF")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
strategy_type: "MovingAverageCrossover"
ticker: "AAPL"
start_date: "2023-01-01"
end_date: "2023-12-31"
strategy_params: {"fast_ma": 10, "slow_ma": 20}""")
            config_file = f.name
        try:
            result = self.runner.invoke(app, ["analyze", config_file, "--report"], catch_exceptions=True)
            assert result.exit_code == 4, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
            assert "Permission denied for PDF" in result.stdout
        finally:
            os.unlink(config_file)

class TestProgressAndUserExperience:
    def setup_method(self):
        self.runner = CliRunner()
    
    @patch('src.meqsap.workflows.analysis.Status')
    @patch('src.meqsap.workflows.analysis.fetch_market_data')
    def test_progress_indicators_data_download(self, mock_fetch_data, mock_status_constructor):
        mock_fetch_data.return_value = pd.DataFrame({'close': [100, 101, 102]})
        mock_status_instance = MagicMock()
        mock_status_constructor.return_value.__enter__.return_value = mock_status_instance
        # Fix: Provide a more complete mock to avoid AttributeError downstream
        mock_analysis_result = Mock(spec=BacktestAnalysisResult)
        mock_primary_result = Mock(spec=BacktestResult)
        mock_primary_result.sharpe_ratio = 1.0
        mock_analysis_result.primary_result = mock_primary_result

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
strategy_type: "MovingAverageCrossover"
ticker: "AAPL"
start_date: "2023-01-01"
end_date: "2023-01-03"
strategy_params: {"fast_ma": 1, "slow_ma": 2}""")
            config_file = f.name
        try:
            with patch('src.meqsap.workflows.analysis.run_complete_backtest', return_value=mock_analysis_result), \
                 patch('src.meqsap.workflows.analysis.ReportingOrchestrator', return_value=Mock()):
                self.runner.invoke(app, ["analyze", config_file], catch_exceptions=True)
            mock_status_constructor.assert_called()
            mock_status_instance.update.assert_any_call("✅ Analysis complete!")
        finally:
            os.unlink(config_file)
    
    def test_colored_output_generation(self):
        from rich.console import Console
        console = Console(force_terminal=True, color_system="truecolor")
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            console.print("Test message", style="green")
            output = mock_stdout.getvalue()
            assert '\x1b[' in output
    
    def test_terminal_capability_detection(self):
        from rich.console import Console
        console_with_color = Console(force_terminal=True)
        assert console_with_color.is_terminal is True
        console_without_color = Console(force_terminal=False, color_system=None)
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            console_without_color.print("No color", style="red")
            output = mock_stdout.getvalue()
            assert '\x1b[' not in output

class TestVersionAndDiagnostics:
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_version_information_display(self):
        result = self.runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "MEQSAP version:" in result.stdout

class TestCrossPlatformCompatibility:
    def test_file_path_handling(self):
        from pathlib import Path
        if sys.platform == "win32": test_path = r"C:\path\to\config.yaml"
        else: test_path = "/path/to/config.yaml"
        path_obj = Path(test_path)
        assert isinstance(path_obj, Path) and str(path_obj) == test_path
    
    def test_console_output_compatibility(self):
        from rich.console import Console
        console = Console(); assert console is not None
        with patch('sys.stdout', new_callable=StringIO): console.print("Test message with unicode: ✓")
    
    def test_permission_handling(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content"); test_file = f.name
        try:
            assert os.path.exists(test_file)
            if sys.platform != "win32": os.chmod(test_file, 0o644); assert os.access(test_file, os.R_OK)
        finally: os.unlink(test_file)
    
    def test_terminal_detection(self):
        is_terminal = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty(); assert isinstance(is_terminal, bool)

class TestPerformanceAndOptimization:
    def setup_method(self): self.runner = CliRunner()
    def test_startup_time_optimization(self): # FIXME: mix_stderr issue likely here too if not fixed by parent
        import time; start_time = time.time(); result = self.runner.invoke(app, ["--help"]); end_time = time.time()
        assert (end_time - start_time) < 2.0 and result.exit_code == 0
    
    def test_operation_timing(self):
        import time; start_time = time.time(); time.sleep(0.01); end_time = time.time()
        elapsed = end_time - start_time; assert elapsed >= 0.01 and elapsed < 0.1
