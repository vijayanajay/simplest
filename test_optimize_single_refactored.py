"""Test for the refactored optimize-single CLI command functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typer.testing import CliRunner
import yaml

# Import the Typer app instance from your CLI module
from src.meqsap.cli import app
from src.meqsap.config import StrategyConfig
from src.meqsap.optimizer.config import OptimizationConfig
from src.meqsap.optimizer.results import OptimizationResult
from src.meqsap.exceptions import ConfigurationError


class TestOptimizeSingleRefactored:
    """Test the refactored optimize-single CLI command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch('src.meqsap.cli.OptimizationEngine')
    @patch('src.meqsap.cli.run_complete_backtest')
    @patch('src.meqsap.cli.fetch_market_data')
    @patch('src.meqsap.cli._validate_and_load_config')
    def test_optimize_single_with_embedded_optimization_config(
        self, mock_validate_config, mock_fetch_data, mock_backtest, mock_engine_class
    ):
        """Test optimize-single command with optimization config embedded in strategy config."""
        
        # Create mock strategy config with embedded optimization_config
        mock_strategy_config = Mock(spec=StrategyConfig)
        mock_strategy_config.ticker = "TCS.NS"
        mock_strategy_config.start_date = "2023-01-01"
        mock_strategy_config.end_date = "2023-12-31"
        mock_strategy_config.optimization_config = OptimizationConfig(
            algorithm="grid_search",
            objective="sharpe_ratio",
            algorithm_params={"max_iterations": 10}
        )
        mock_strategy_config.copy.return_value = mock_strategy_config
        mock_strategy_config.strategy_params = {"fast_ma": 5, "slow_ma": 20}
        
        mock_validate_config.return_value = mock_strategy_config
        
        # Mock market data and backtest result
        mock_fetch_data.return_value = Mock()
        mock_backtest_result = Mock()
        mock_backtest.return_value = mock_backtest_result
        
        # Mock optimization engine and result
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        
        mock_optimization_result = Mock(spec=OptimizationResult)
        mock_optimization_result.best_parameters = {"fast_ma": 10, "slow_ma": 30}
        mock_optimization_result.best_constraint_adherence = None
        mock_optimization_result.get_summary_stats.return_value = {
            "algorithm": "grid_search",
            "total_evaluations": 10,
            "success_rate": 1.0,
            "best_objective_value": 0.75
        }
        
        mock_engine.run_optimization.return_value = mock_optimization_result
        mock_engine.save_results.return_value = None
        
        with self.runner.isolated_filesystem():
            # Create a dummy config file
            config_file = Path("test_config.yaml")
            config_data = {
                "ticker": "TCS.NS",
                "start_date": "2023-01-01", 
                "end_date": "2023-12-31",
                "strategy_type": "MovingAverageCrossover",
                "strategy_params": {"fast_ma": 5, "slow_ma": 20},
                "optimization_config": {
                    "algorithm": "grid_search",
                    "objective": "sharpe_ratio",
                    "algorithm_params": {"max_iterations": 10}
                }
            }
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)
            
            # Run the command
            result = self.runner.invoke(app, ["optimize-single", str(config_file)], catch_exceptions=False)
            
            # Verify execution
            assert result.exit_code == 0, f"Command failed with output: {result.output}"
            assert "Optimization Complete" in result.output
            
            # Verify mocks were called appropriately
            mock_validate_config.assert_called_once()
            mock_engine.run_optimization.assert_called_once()
            mock_engine.save_results.assert_called_once()

    @patch('src.meqsap.cli.OptimizationEngine')
    @patch('src.meqsap.cli.run_complete_backtest')
    @patch('src.meqsap.cli.fetch_market_data')
    @patch('src.meqsap.cli._validate_and_load_config')
    @patch('src.meqsap.cli.load_yaml_config')
    def test_optimize_single_with_separate_optimization_config_file(
        self, mock_load_yaml, mock_validate_config, mock_fetch_data, mock_backtest, mock_engine_class
    ):
        """Test optimize-single command with separate optimization config file."""
        
        # Create mock strategy config without optimization_config
        mock_strategy_config = Mock(spec=StrategyConfig)
        mock_strategy_config.ticker = "TCS.NS"
        mock_strategy_config.start_date = "2023-01-01"
        mock_strategy_config.end_date = "2023-12-31"
        mock_strategy_config.optimization_config = None  # No embedded optimization config
        mock_strategy_config.copy.return_value = mock_strategy_config
        mock_strategy_config.strategy_params = {"fast_ma": 5, "slow_ma": 20}
        
        mock_validate_config.return_value = mock_strategy_config
        
        # Mock loading optimization config from separate file
        mock_load_yaml.return_value = {
            "algorithm": "random_search",
            "objective": "sharpe_with_hold_period_constraint",
            "constraints": {"target_hold_period_days": [5, 15]},
            "algorithm_params": {"max_iterations": 50}
        }
        
        # Mock market data and backtest result
        mock_fetch_data.return_value = Mock()
        mock_backtest_result = Mock()
        mock_backtest.return_value = mock_backtest_result
        
        # Mock optimization engine and result
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        
        mock_optimization_result = Mock(spec=OptimizationResult)
        mock_optimization_result.best_parameters = {"fast_ma": 12, "slow_ma": 25}
        mock_optimization_result.best_constraint_adherence = None
        mock_optimization_result.get_summary_stats.return_value = {
            "algorithm": "random_search",
            "total_evaluations": 50,
            "success_rate": 0.95,
            "best_objective_value": 0.85
        }
        
        mock_engine.run_optimization.return_value = mock_optimization_result
        mock_engine.save_results.return_value = None
        
        with self.runner.isolated_filesystem():
            # Create strategy config file without optimization config
            config_file = Path("strategy_config.yaml")
            config_data = {
                "ticker": "TCS.NS",
                "start_date": "2023-01-01", 
                "end_date": "2023-12-31",
                "strategy_type": "MovingAverageCrossover",
                "strategy_params": {"fast_ma": 5, "slow_ma": 20}
            }
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)
            
            # Create separate optimization config file
            opt_config_file = Path("optimization_config.yaml")
            opt_config_data = {
                "algorithm": "random_search",
                "objective": "sharpe_with_hold_period_constraint",
                "constraints": {"target_hold_period_days": [5, 15]},
                "algorithm_params": {"max_iterations": 50}
            }
            with open(opt_config_file, "w") as f:
                yaml.dump(opt_config_data, f)
            
            # Run the command with separate optimization config file
            result = self.runner.invoke(app, [
                "optimize-single", str(config_file),
                "--optimization-config-file", str(opt_config_file)
            ], catch_exceptions=False)
            
            # Verify execution
            assert result.exit_code == 0, f"Command failed with output: {result.output}"
            assert "Optimization Complete" in result.output
            
            # Verify mocks were called appropriately
            mock_validate_config.assert_called_once()
            mock_load_yaml.assert_called_once_with(str(opt_config_file))
            mock_engine.run_optimization.assert_called_once()
            mock_engine.save_results.assert_called_once()

    @patch('src.meqsap.cli.OptimizationEngine')
    @patch('src.meqsap.cli.run_complete_backtest')
    @patch('src.meqsap.cli.fetch_market_data')
    @patch('src.meqsap.cli._validate_and_load_config')
    def test_optimize_single_with_default_optimization_config(
        self, mock_validate_config, mock_fetch_data, mock_backtest, mock_engine_class
    ):
        """Test optimize-single command creates default optimization config when none provided."""
        
        # Create mock strategy config without optimization_config
        mock_strategy_config = Mock(spec=StrategyConfig)
        mock_strategy_config.ticker = "TCS.NS"
        mock_strategy_config.start_date = "2023-01-01"
        mock_strategy_config.end_date = "2023-12-31"
        mock_strategy_config.optimization_config = None  # No optimization config
        mock_strategy_config.copy.return_value = mock_strategy_config
        mock_strategy_config.strategy_params = {"fast_ma": 5, "slow_ma": 20}
        
        mock_validate_config.return_value = mock_strategy_config
        
        # Mock market data and backtest result
        mock_fetch_data.return_value = Mock()
        mock_backtest_result = Mock()
        mock_backtest.return_value = mock_backtest_result
        
        # Mock optimization engine and result
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        
        mock_optimization_result = Mock(spec=OptimizationResult)
        mock_optimization_result.best_parameters = {"fast_ma": 8, "slow_ma": 22}
        mock_optimization_result.best_constraint_adherence = None
        mock_optimization_result.get_summary_stats.return_value = {
            "algorithm": "grid_search",
            "total_evaluations": 100,
            "success_rate": 1.0,
            "best_objective_value": 0.65
        }
        
        mock_engine.run_optimization.return_value = mock_optimization_result
        mock_engine.save_results.return_value = None
        
        with self.runner.isolated_filesystem():
            # Create strategy config file without optimization config
            config_file = Path("strategy_config.yaml")
            config_data = {
                "ticker": "TCS.NS",
                "start_date": "2023-01-01", 
                "end_date": "2023-12-31",
                "strategy_type": "MovingAverageCrossover",
                "strategy_params": {"fast_ma": 5, "slow_ma": 20}
            }
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)
            
            # Run the command with verbose flag to see default config message
            result = self.runner.invoke(app, [
                "optimize-single", str(config_file), "--verbose"
            ], catch_exceptions=False)
            
            # Verify execution
            assert result.exit_code == 0, f"Command failed with output: {result.output}"
            assert "Optimization Complete" in result.output
            assert "Using default optimization configuration" in result.output
            
            # Verify mocks were called appropriately
            mock_validate_config.assert_called_once()
            mock_engine.run_optimization.assert_called_once()
            mock_engine.save_results.assert_called_once()

    @patch('src.meqsap.cli._validate_and_load_config')
    def test_optimize_single_configuration_error_handling(self, mock_validate_config):
        """Test optimize-single command handles configuration errors properly."""
        
        # Mock configuration error
        mock_validate_config.side_effect = ConfigurationError("Invalid ticker symbol")
        
        with self.runner.isolated_filesystem():
            # Create a dummy config file
            config_file = Path("invalid_config.yaml")
            config_data = {"invalid": "config"}
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)
            
            # Run the command
            result = self.runner.invoke(app, ["optimize-single", str(config_file)], catch_exceptions=False)
            
            # Verify error handling
            assert result.exit_code == 1
            assert "Configuration Error" in result.output
            assert "Invalid ticker symbol" in result.output

    def test_optimize_single_missing_config_file(self):
        """Test optimize-single command handles missing config file."""
        
        with self.runner.isolated_filesystem():
            # Run the command with non-existent file
            result = self.runner.invoke(app, ["optimize-single", "nonexistent.yaml"], catch_exceptions=False)
            
            # Verify error handling
            assert result.exit_code == 1
            assert "Configuration Error" in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
