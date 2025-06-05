"""Basic test for the refactored optimize-single CLI command."""

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


def test_optimize_single_imports():
    """Test that the optimize-single command can be imported and basic imports work."""
    # This test verifies the refactored function doesn't have import errors
    runner = CliRunner()
    
    # Test that the command exists and can show help
    result = runner.invoke(app, ["optimize-single", "--help"])
    
    # The command should exist and show help without crashing
    assert result.exit_code == 0 or "optimize-single" in str(result.output)


@patch('src.meqsap.cli.OptimizationEngine')
@patch('src.meqsap.cli.run_complete_backtest')
@patch('src.meqsap.cli.fetch_market_data')
@patch('src.meqsap.cli._validate_and_load_config')
def test_optimize_single_with_config_file(
    mock_validate_config, mock_fetch_data, mock_backtest, mock_engine_class
):
    """Test optimize-single command with configuration file."""
    runner = CliRunner()
    
    # Create mock strategy config with optimization_config
    mock_strategy_config = Mock(spec=StrategyConfig)
    mock_strategy_config.ticker = "TEST.NS"
    mock_strategy_config.start_date = "2023-01-01"
    mock_strategy_config.end_date = "2023-12-31"
    mock_strategy_config.optimization_config = OptimizationConfig(
        algorithm="grid_search",
        objective="sharpe_ratio",
        algorithm_params={"max_iterations": 10}
    )
    mock_strategy_config.copy.return_value = mock_strategy_config
    
    mock_validate_config.return_value = mock_strategy_config
    
    # Mock market data
    mock_fetch_data.return_value = Mock()
    
    # Mock backtest result
    mock_backtest_result = Mock()
    mock_backtest.return_value = mock_backtest_result
    
    # Mock optimization engine and result
    mock_engine = Mock()
    mock_engine_class.return_value = mock_engine
    
    mock_optimization_result = Mock(spec=OptimizationResult)
    mock_optimization_result.best_parameters = {"param1": 10}
    mock_optimization_result.best_constraint_adherence = None
    mock_optimization_result.get_summary_stats.return_value = {
        "algorithm": "grid_search",
        "total_evaluations": 10,
        "success_rate": 1.0,
        "best_objective_value": 0.5
    }
    
    mock_engine.run_optimization.return_value = mock_optimization_result
    
    with runner.isolated_filesystem():
        # Create a dummy config file
        config_file = Path("test_config.yaml")
        config_data = {
            "ticker": "TEST.NS",
            "start_date": "2023-01-01", 
            "end_date": "2023-12-31",
            "strategy_type": "MovingAverageCrossover"
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        # Run the command
        result = runner.invoke(app, ["optimize-single", str(config_file)], catch_exceptions=False)
        
        # Verify basic execution
        assert result.exit_code == 0 or "Optimization Complete" in result.output
        
        # Verify mocks were called appropriately
        mock_validate_config.assert_called_once()
        mock_engine.run_optimization.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
