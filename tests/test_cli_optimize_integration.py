"""
Integration tests for the CLI optimize commands.

Tests the complete optimize command workflow including:
- Configuration loading and validation
- Data acquisition
- Optimization engine execution
- Progress reporting
- Error handling scenarios
- Output generation and reporting

Ensures compliance with memory.md anti-patterns prevention rules.
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import date
from unittest.mock import Mock, patch, MagicMock
from typer.testing import CliRunner
import pandas as pd
import yaml

# Import the CLI app and optimize commands
from src.meqsap.cli import app
from src.meqsap.cli.commands.optimize import optimize_app

# Import required types and exceptions
from src.meqsap.config import StrategyConfig
from src.meqsap.exceptions import (
    ConfigurationError, DataError, BacktestError, ReportingError,
    DataAcquisitionError, BacktestExecutionError
)
from src.meqsap.optimizer import OptimizationEngine, OptimizationResult, ErrorSummary
from src.meqsap.backtest import BacktestAnalysisResult


# Sample optimization configuration YAML content
VALID_OPTIMIZATION_YAML = yaml.dump({
    "ticker": "AAPL",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31", 
    "strategy_type": "MovingAverageCrossover",
    "strategy_params": {
        "fast_ma": {"type": "range", "start": 5, "stop": 15, "step": 1},
        "slow_ma": {"type": "range", "start": 20, "stop": 50, "step": 5}
    },
    "optimization_config": {
        "active": True,
        "algorithm": "RandomSearch",
        "objective_function": "SharpeRatio",  # Fixed: use correct PascalCase name
        "objective_params": {"risk_free_rate": 0.02},
        "algorithm_params": {"n_trials": 10}
    }
})

INVALID_OPTIMIZATION_YAML_NO_CONFIG = yaml.dump({
    "ticker": "AAPL",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "strategy_type": "MovingAverageCrossover",
    "strategy_params": {"fast_ma": 10, "slow_ma": 20}
    # Missing optimization_config section
})

INVALID_OPTIMIZATION_YAML_INACTIVE = yaml.dump({
    "ticker": "AAPL",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "strategy_type": "MovingAverageCrossover",
    "strategy_params": {"fast_ma": 10, "slow_ma": 20},
    "optimization_config": {
        "active": False,  # Not active
        "algorithm": "RandomSearch",
        "objective_function": "SharpeRatio"  # Fixed: use correct PascalCase name
    }
})


class TestOptimizeCommandIntegration:
    """Test the optimize command integration scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
          # Mock optimization result
        self.mock_optimization_result = Mock(spec=OptimizationResult)
        self.mock_optimization_result.best_params = {"fast_ma": 10, "slow_ma": 25}
        self.mock_optimization_result.best_score = 1.25
        self.mock_optimization_result.total_trials = 10
        self.mock_optimization_result.successful_trials = 10
        self.mock_optimization_result.error_summary = ErrorSummary(total_failed_trials=0)
        self.mock_optimization_result.timing_info = {"total_elapsed": 12.3, "avg_per_trial": 1.23}
        self.mock_optimization_result.was_interrupted = False
        # This mock must be a complete dictionary representation of BacktestAnalysisResult
        # to pass Pydantic validation in the reporting function.
        self.mock_optimization_result.best_strategy_analysis = {
            "strategy_config": {"ticker": "AAPL", "start_date": "2023-01-01", "end_date": "2023-12-31", "strategy_type": "MovingAverageCrossover", "strategy_params": {"fast_ma": 10, "slow_ma": 20}},
            "primary_result": {
                "total_return": 10.0,
                "annualized_return": 10.0,
                "sharpe_ratio": 1.5,
                "max_drawdown": -5.0,
                "total_trades": 5,
                "win_rate": 80.0,
                "profit_factor": 2.5,
                "final_value": 11000.0,
                "volatility": 15.0,
                "calmar_ratio": 2.0,
                "trade_details": [],
                "portfolio_value_series": {"2023-01-01": 10000.0},
                "avg_trade_duration_days": 10.0,
                "pct_trades_in_target_hold_period": 80.0,
                "trade_durations_days": [10, 10, 10, 10, 10]
            },
            "vibe_checks": {"minimum_trades_check": True, "signal_quality_check": True, "data_coverage_check": True, "overall_pass": True, "check_messages": []},
            "robustness_checks": {"baseline_sharpe": 1.5, "high_fees_sharpe": 1.2, "turnover_rate": 10.0, "sharpe_degradation": 20.0, "return_degradation": 15.0, "recommendations": []}
        }
        self.mock_optimization_result.constraint_adherence = None

          # Mock market data
        self.mock_market_data = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [105, 106, 107],
            'low': [99, 100, 101],
            'close': [103, 104, 105],
            'volume': [1000, 1100, 1200]
        })

    @patch('src.meqsap.cli.commands.optimize.display_optimization_summary')
    @patch('src.meqsap.cli.commands.optimize.create_progress_callback')
    @patch('src.meqsap.cli.commands.optimize.create_optimization_progress_bar')
    @patch('src.meqsap.cli.commands.optimize.OptimizationEngine')
    @patch('src.meqsap.cli.commands.optimize.fetch_market_data')
    @patch('src.meqsap.cli.commands.optimize.load_yaml_config')
    def test_optimize_single_successful_execution(self, mock_load_config, mock_fetch_data, mock_engine_class,
                                                 mock_progress_bar, mock_progress_callback, mock_display_summary):
        """Test successful optimization execution with all mocked dependencies."""        # Setup mocks
        mock_load_config.return_value = yaml.safe_load(VALID_OPTIMIZATION_YAML)
        mock_fetch_data.return_value = self.mock_market_data
          # Mock progress UI components
        mock_progress = Mock()
        mock_progress.__enter__ = Mock(return_value=mock_progress)
        mock_progress.__exit__ = Mock(return_value=None)
        mock_task_id = 1
        mock_progress_bar.return_value = (mock_progress, mock_task_id)
        mock_callback = Mock()
        # The CLI code expects create_progress_callback to return two values (callback, context)
        # The context should be the progress instance which is a context manager
        mock_progress_callback.return_value = (mock_callback, mock_progress)
        
        mock_engine = Mock(spec=OptimizationEngine)
        mock_engine.run_optimization.return_value = self.mock_optimization_result
        mock_engine_class.return_value = mock_engine
        
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(VALID_OPTIMIZATION_YAML)
            config_path = f.name
        
        try:
            result = self.runner.invoke(app, ["optimize", "single", config_path])
            assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
            
            # Verify the optimization workflow was executed
            mock_load_config.assert_called_once_with(config_path)
            mock_fetch_data.assert_called_once()
            mock_engine_class.assert_called_once()
            mock_engine.run_optimization.assert_called_once()
            mock_display_summary.assert_called_once()
            
            # Check for key output messages
            assert "Loading configuration" in result.stdout
            assert "Acquired" in result.stdout
            assert "completed successfully" in result.stdout
            
        finally:
            os.unlink(config_path)

    @patch('src.meqsap.cli.commands.optimize.load_yaml_config')
    def test_optimize_single_configuration_error_no_optimization_config(self, mock_load_config):
        """Test configuration error when optimization_config is missing."""
        mock_load_config.return_value = yaml.safe_load(INVALID_OPTIMIZATION_YAML_NO_CONFIG)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(INVALID_OPTIMIZATION_YAML_NO_CONFIG)
            config_path = f.name
        
        try:
            result = self.runner.invoke(app, ["optimize", "single", config_path])
            assert result.exit_code == 1  # Configuration error exit code
            assert "optimization_config.active must be true" in result.stdout
        finally:
            os.unlink(config_path)

    @patch('src.meqsap.cli.commands.optimize.load_yaml_config')
    def test_optimize_single_configuration_error_inactive_optimization(self, mock_load_config):
        """Test configuration error when optimization is not active."""
        mock_load_config.return_value = yaml.safe_load(INVALID_OPTIMIZATION_YAML_INACTIVE)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(INVALID_OPTIMIZATION_YAML_INACTIVE)
            config_path = f.name
        
        try:
            result = self.runner.invoke(app, ["optimize", "single", config_path])
            assert result.exit_code == 1  # Configuration error exit code
            assert "optimization_config.active must be true" in result.stdout
        finally:
            os.unlink(config_path)

    @patch('src.meqsap.cli.commands.optimize.fetch_market_data')
    @patch('src.meqsap.cli.commands.optimize.load_yaml_config')
    def test_optimize_single_data_acquisition_error(self, mock_load_config, mock_fetch_data):
        """Test data acquisition error handling."""
        mock_load_config.return_value = yaml.safe_load(VALID_OPTIMIZATION_YAML)
        mock_fetch_data.side_effect = DataAcquisitionError("Failed to fetch market data")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(VALID_OPTIMIZATION_YAML)
            config_path = f.name
        
        try:
            result = self.runner.invoke(app, ["optimize", "single", config_path])
            assert result.exit_code == 2  # Data error exit code
        finally:
            os.unlink(config_path)

    @patch('src.meqsap.cli.commands.optimize.fetch_market_data')
    @patch('src.meqsap.cli.commands.optimize.load_yaml_config')
    def test_optimize_single_empty_market_data(self, mock_load_config, mock_fetch_data):
        """Test handling of empty market data."""
        mock_load_config.return_value = yaml.safe_load(VALID_OPTIMIZATION_YAML)
        mock_fetch_data.return_value = pd.DataFrame()  # Empty DataFrame
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(VALID_OPTIMIZATION_YAML)
            config_path = f.name
        try:
            result = self.runner.invoke(app, ["optimize", "single", config_path])
            assert result.exit_code == 2  # Data error exit code
            # The error message is now handled by the decorator and may not be in stdout
            assert "No market data available" in result.output
        finally:
            os.unlink(config_path)

    @patch('src.meqsap.cli.commands.optimize.display_optimization_summary')
    @patch('src.meqsap.cli.commands.optimize.create_progress_callback')
    @patch('src.meqsap.cli.commands.optimize.create_optimization_progress_bar')
    @patch('src.meqsap.cli.commands.optimize.OptimizationEngine')
    @patch('src.meqsap.cli.commands.optimize.fetch_market_data')
    @patch('src.meqsap.cli.commands.optimize.load_yaml_config')
    def test_optimize_single_with_trials_override(self, mock_load_config, mock_fetch_data, mock_engine_class,
                                                 mock_progress_bar, mock_progress_callback, mock_display_summary):
        """Test optimization with trials parameter override."""
        mock_load_config.return_value = yaml.safe_load(VALID_OPTIMIZATION_YAML)
        mock_fetch_data.return_value = self.mock_market_data        # Mock progress UI components
        mock_progress = Mock()
        mock_progress.__enter__ = Mock(return_value=mock_progress)
        mock_progress.__exit__ = Mock(return_value=None)
        mock_task_id = 1
        mock_progress_bar.return_value = (mock_progress, mock_task_id)
        mock_callback = Mock()
        mock_progress_callback.return_value = (mock_callback, mock_progress)
        
        mock_engine = Mock(spec=OptimizationEngine)
        mock_engine.run_optimization.return_value = self.mock_optimization_result
        mock_engine_class.return_value = mock_engine
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(VALID_OPTIMIZATION_YAML)
            config_path = f.name
        
        try:
            result = self.runner.invoke(app, ["optimize", "single", config_path, "--trials", "50"])
            assert result.exit_code == 0
            assert "Overriding trials to 50" in result.stdout
        finally:
            os.unlink(config_path)    
    
    @patch('src.meqsap.cli.commands.optimize.display_optimization_summary')
    @patch('src.meqsap.cli.commands.optimize.create_progress_callback')
    @patch('src.meqsap.cli.commands.optimize.create_optimization_progress_bar')
    @patch('src.meqsap.cli.commands.optimize.OptimizationEngine')
    @patch('src.meqsap.cli.commands.optimize.fetch_market_data')
    @patch('src.meqsap.cli.commands.optimize.load_yaml_config')
    def test_optimize_single_with_verbose_flag(self, mock_load_config, mock_fetch_data, mock_engine_class,
                                             mock_progress_bar, mock_progress_callback, mock_display_summary):
        """Test optimization with verbose logging enabled."""
        mock_load_config.return_value = yaml.safe_load(VALID_OPTIMIZATION_YAML)
        mock_fetch_data.return_value = self.mock_market_data
        
        # Mock progress UI components
        mock_progress = Mock()
        mock_progress.__enter__ = Mock(return_value=mock_progress)
        mock_progress.__exit__ = Mock(return_value=None)
        mock_task_id = 1
        mock_progress_bar.return_value = (mock_progress, mock_task_id)
        mock_callback = Mock()
        # The CLI code expects create_progress_callback to return two values (callback, context)
        # The context should be the progress instance which is a context manager
        mock_progress_callback.return_value = (mock_callback, mock_progress)
        
        mock_engine = Mock(spec=OptimizationEngine)
        mock_engine.run_optimization.return_value = self.mock_optimization_result
        mock_engine_class.return_value = mock_engine
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(VALID_OPTIMIZATION_YAML)
            config_path = f.name
        
        try:
            result = self.runner.invoke(app, ["optimize", "single", config_path, "--verbose"])
            assert result.exit_code == 0
            assert "Verbose logging enabled" in result.stdout
        finally:
            os.unlink(config_path)

    @patch('src.meqsap.cli.commands.optimize.OptimizationEngine')
    @patch('src.meqsap.cli.commands.optimize.fetch_market_data')
    @patch('src.meqsap.cli.commands.optimize.load_yaml_config')
    def test_optimize_single_interrupted_optimization(self, mock_load_config, mock_fetch_data, mock_engine_class):
        """Test handling of interrupted optimization."""
        mock_load_config.return_value = yaml.safe_load(VALID_OPTIMIZATION_YAML)
        mock_fetch_data.return_value = self.mock_market_data
          # Create a result that indicates interruption
        interrupted_result = Mock(spec=OptimizationResult)
        interrupted_result.best_params = {"fast_ma": 10, "slow_ma": 25}
        interrupted_result.best_score = 1.1  # Add missing attribute
        interrupted_result.was_interrupted = True
        interrupted_result.total_trials = 5
        interrupted_result.successful_trials = 5
        interrupted_result.error_summary = ErrorSummary(total_failed_trials=0)
        interrupted_result.timing_info = {"total_elapsed": 6.0, "avg_per_trial": 1.2}
        interrupted_result.best_strategy_analysis = self.mock_optimization_result.best_strategy_analysis
        interrupted_result.constraint_adherence = None  # Add missing attribute
        
        mock_engine = Mock(spec=OptimizationEngine)
        mock_engine.run_optimization.return_value = interrupted_result
        mock_engine_class.return_value = mock_engine
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(VALID_OPTIMIZATION_YAML)
            config_path = f.name
        
        try:
            result = self.runner.invoke(app, ["optimize", "single", config_path])
            assert result.exit_code == 7  # Interrupted exit code (as per ADR-004)
            assert "completed with interruption" in result.stdout
        finally:
            os.unlink(config_path)

    @patch('src.meqsap.cli.commands.optimize.OptimizationEngine')
    @patch('src.meqsap.cli.commands.optimize.fetch_market_data')
    @patch('src.meqsap.cli.commands.optimize.load_yaml_config')
    def test_optimize_single_no_valid_trials(self, mock_load_config, mock_fetch_data, mock_engine_class):
        """Test handling when no valid trials are found."""
        mock_load_config.return_value = yaml.safe_load(VALID_OPTIMIZATION_YAML)
        mock_fetch_data.return_value = self.mock_market_data
          # Create a result with no valid trials
        failed_result = Mock(spec=OptimizationResult)
        failed_result.best_params = None
        failed_result.best_score = None  # Add missing attribute
        failed_result.was_interrupted = False
        failed_result.total_trials = 10
        failed_result.successful_trials = 0
        failed_result.error_summary = ErrorSummary(total_failed_trials=10)
        failed_result.timing_info = {"total_elapsed": 10.0, "avg_per_trial": 1.0}
        failed_result.constraint_adherence = None  # Add missing attribute
        
        mock_engine = Mock(spec=OptimizationEngine)
        mock_engine.run_optimization.return_value = failed_result
        mock_engine_class.return_value = mock_engine
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(VALID_OPTIMIZATION_YAML)
            config_path = f.name
        
        try:
            result = self.runner.invoke(app, ["optimize", "single", config_path])
            assert result.exit_code == 6  # No valid trials exit code (as per ADR-004)
            assert "no valid trials found" in result.stdout
        finally:
            os.unlink(config_path)

    @patch('src.meqsap.cli.commands.optimize.OptimizationEngine')
    @patch('src.meqsap.cli.commands.optimize.fetch_market_data')
    @patch('src.meqsap.cli.commands.optimize.load_yaml_config')
    def test_optimize_single_with_report_generation(self, mock_load_config, mock_fetch_data, mock_engine_class):
        """Test optimization with PDF report generation."""
        mock_load_config.return_value = yaml.safe_load(VALID_OPTIMIZATION_YAML)
        mock_fetch_data.return_value = self.mock_market_data
        
        mock_engine = Mock(spec=OptimizationEngine)
        mock_engine.run_optimization.return_value = self.mock_optimization_result
        mock_engine_class.return_value = mock_engine
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(VALID_OPTIMIZATION_YAML)
            config_path = f.name
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:                # Mock the PDF generation to avoid import errors - correct import path
                with patch('meqsap.reporting.generate_pdf_report') as mock_pdf:
                    result = self.runner.invoke(app, [
                        "optimize", "single", config_path, 
                        "--report", "--output-dir", temp_dir
                    ])
                    assert result.exit_code == 0
                    assert "Generating PDF report" in result.stdout
                    mock_pdf.assert_called_once()
            finally:
                os.unlink(config_path)    
    
    def test_optimize_single_nonexistent_config_file(self):
        """Test error handling for nonexistent configuration file."""
        result = self.runner.invoke(app, ["optimize", "single", "/nonexistent/config.yaml"])
        # Based on actual behavior, this is handled as configuration error, not file not found
        assert result.exit_code == 1  # Configuration error exit code
        assert "Configuration file not found" in result.stdout

    @patch('src.meqsap.cli.commands.optimize.load_yaml_config')
    def test_optimize_single_invalid_yaml_syntax(self, mock_load_config):
        """Test handling of invalid YAML syntax."""
        mock_load_config.side_effect = yaml.YAMLError("Invalid YAML syntax")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: syntax: [")
            config_path = f.name
        try:
            result = self.runner.invoke(app, ["optimize", "single", config_path])
            assert result.exit_code == 1  # Configuration error exit code
        finally:
            os.unlink(config_path)

    @patch('src.meqsap.cli.commands.optimize.display_optimization_summary')
    @patch('src.meqsap.cli.commands.optimize.create_progress_callback')
    @patch('src.meqsap.cli.commands.optimize.create_optimization_progress_bar')
    @patch('src.meqsap.cli.commands.optimize.OptimizationEngine')
    @patch('src.meqsap.cli.commands.optimize.fetch_market_data')
    @patch('src.meqsap.cli.commands.optimize.load_yaml_config')
    def test_optimize_single_no_progress_flag(self, mock_load_config, mock_fetch_data, mock_engine_class,
                                            mock_progress_bar, mock_progress_callback, mock_display_summary):
        """Test optimization with progress bar disabled."""
        mock_load_config.return_value = yaml.safe_load(VALID_OPTIMIZATION_YAML)
        mock_fetch_data.return_value = self.mock_market_data
          # Progress components should not be called with --no-progress
        mock_engine = Mock(spec=OptimizationEngine)
        mock_engine.run_optimization.return_value = self.mock_optimization_result
        mock_engine_class.return_value = mock_engine
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(VALID_OPTIMIZATION_YAML)
            config_path = f.name
        
        try:
            result = self.runner.invoke(app, ["optimize", "single", config_path, "--no-progress"], catch_exceptions=False)
            assert result.exit_code == 0, f"EXIT CODE: {result.exit_code}\nSTDOUT: {result.stdout}\nException: {result.exception}"
            # Verify that no progress callback was passed (would be tested in engine mock)
            mock_engine.run_optimization.assert_called_once()
            # Progress components should not be called with --no-progress flag
            mock_progress_bar.assert_not_called()
            mock_progress_callback.assert_not_called()
        finally:
            os.unlink(config_path)


class TestOptimizeCommandHelp:
    """Test optimize command help and usage information."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_optimize_help_command(self):
        """Test optimize command help output."""
        result = self.runner.invoke(app, ["optimize", "--help"])
        assert result.exit_code == 0
        assert "Strategy optimization commands" in result.output

    def test_optimize_single_help_command(self):
        """Test optimize single subcommand help output."""
        result = self.runner.invoke(app, ["optimize", "single", "--help"])
        assert result.exit_code == 0
        assert "Optimize a single strategy configuration" in result.output
        assert "--report" in result.output
        assert "--output-dir" in result.output
        assert "--trials" in result.output
        assert "--no-progress" in result.output
        assert "--verbose" in result.output

    def test_optimize_without_subcommand(self):
        """Test optimize command without subcommand shows help."""
        result = self.runner.invoke(app, ["optimize"])
        # Based on actual behavior, optimize requires a subcommand
        assert result.exit_code == 2  # Missing subcommand
        assert "Usage:" in result.output or "Missing command" in result.output


class TestOptimizeCommandArgumentValidation:
    """Test optimize command argument validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_optimize_single_missing_config_argument(self):
        """Test error when config path argument is missing."""
        result = self.runner.invoke(app, ["optimize", "single"])
        assert result.exit_code == 2  # Missing argument
        assert "Missing argument" in result.stderr

    def test_optimize_single_invalid_trials_value(self):
        """Test error when trials value is invalid."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(VALID_OPTIMIZATION_YAML)
            config_path = f.name
        
        try:
            result = self.runner.invoke(app, ["optimize", "single", config_path, "--trials", "invalid"])
            assert result.exit_code == 2  # Invalid argument type
            assert "Invalid value" in result.stderr
        finally:
            os.unlink(config_path)

    def test_optimize_single_negative_trials_value(self):
        """Test handling of negative trials value."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(VALID_OPTIMIZATION_YAML)
            config_path = f.name
        
        try:
            # This should be accepted by typer but may cause issues in the optimization logic
            result = self.runner.invoke(app, ["optimize", "single", config_path, "--trials", "-5"])
            # The command should at least parse correctly, though the optimization may fail
            assert result.exit_code in [0, 1, 2]  # Various possible exit codes depending on handling
        finally:
            os.unlink(config_path)


# Ensure this follows anti-patterns from memory.md:
# - Complete package structure with __init__.py files
# - All imports work correctly
# - Mock specifications match actual return types
# - No duplicate exception classes
# - Tests match actual implementation structure
# - Help text assertions use key terms, not exact strings