"""
Unit tests for objective function registry and validation.

Tests the objective function registry directly to ensure proper validation
of objective function names and prevent runtime errors.
"""

import pytest
from unittest.mock import Mock

from src.meqsap.optimizer.objective_functions import (
    get_objective_function,
    OBJECTIVE_FUNCTION_REGISTRY,
    maximize_sharpe_ratio,
    maximize_calmar_ratio,
    maximize_profit_factor,
    sharpe_with_hold_period_constraint
)
from src.meqsap.exceptions import ConfigurationError
from src.meqsap.backtest import BacktestAnalysisResult


class TestObjectiveFunctionRegistry:
    """Test the objective function registry and validation."""

    def test_get_objective_function_valid_names(self):
        """Test that all registered objective functions can be retrieved."""
        for name in OBJECTIVE_FUNCTION_REGISTRY.keys():
            func = get_objective_function(name)
            assert callable(func)

    def test_get_objective_function_invalid_name(self):
        """Test that invalid objective function names raise ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            get_objective_function("invalid_function_name")
        
        assert "not found" in str(exc_info.value)
        assert "invalid_function_name" in str(exc_info.value)
        assert "Available functions" in str(exc_info.value)

    def test_registry_contains_expected_functions(self):
        """Test that the registry contains all expected objective functions."""
        expected_functions = {
            "SharpeRatio",
            "CalmarRatio", 
            "ProfitFactor",
            "SharpeWithHoldPeriodConstraint"
        }
        
        assert set(OBJECTIVE_FUNCTION_REGISTRY.keys()) == expected_functions

    def test_common_lowercase_names_are_invalid(self):
        """Test that common lowercase variants are properly rejected."""
        lowercase_variants = [
            "sharpe", "sharperatio", "sharpe_ratio",
            "calmar", "calmarratio", "calmar_ratio",
            "profit", "profitfactor", "profit_factor"
        ]
        
        for name in lowercase_variants:
            with pytest.raises(ConfigurationError):
                get_objective_function(name)

    @pytest.mark.parametrize("func_name,func_impl", [
        ("SharpeRatio", maximize_sharpe_ratio),
        ("CalmarRatio", maximize_calmar_ratio),
        ("ProfitFactor", maximize_profit_factor),
        ("SharpeWithHoldPeriodConstraint", sharpe_with_hold_period_constraint)
    ])
    def test_registry_mapping_correctness(self, func_name, func_impl):
        """Test that registry maps names to correct function implementations."""
        retrieved_func = get_objective_function(func_name)
        assert retrieved_func is func_impl

    def test_objective_functions_callable_with_backtest_result(self):
        """Test that all objective functions can be called with mock BacktestAnalysisResult."""
        # Create a mock backtest result
        mock_result = Mock(spec=BacktestAnalysisResult)
        mock_result.primary_result = Mock()
        mock_result.primary_result.sharpe_ratio = 1.5
        mock_result.primary_result.calmar_ratio = 0.8
        mock_result.primary_result.profit_factor = 2.0
        mock_result.primary_result.pct_trades_in_target_hold_period = 75.0
        
        params = {}
        
        # Test each objective function
        for name in OBJECTIVE_FUNCTION_REGISTRY.keys():
            func = get_objective_function(name)
            result = func(mock_result, params)
            assert isinstance(result, (int, float))
            assert not isinstance(result, bool)  # Ensure it's a numeric value

    def test_error_message_includes_available_functions(self):
        """Test that error messages include the list of available functions."""
        with pytest.raises(ConfigurationError) as exc_info:
            get_objective_function("nonexistent")
        
        error_message = str(exc_info.value)
        
        # Should include all available function names
        for func_name in OBJECTIVE_FUNCTION_REGISTRY.keys():
            assert func_name in error_message


class TestObjectiveFunctionImplementations:
    """Test individual objective function implementations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_result = Mock(spec=BacktestAnalysisResult)
        self.mock_result.primary_result = Mock()

    def test_maximize_sharpe_ratio(self):
        """Test Sharpe ratio objective function."""
        self.mock_result.primary_result.sharpe_ratio = 2.5
        
        result = maximize_sharpe_ratio(self.mock_result, {})
        assert result == 2.5

    def test_maximize_calmar_ratio(self):
        """Test Calmar ratio objective function."""
        self.mock_result.primary_result.calmar_ratio = 1.2
        
        result = maximize_calmar_ratio(self.mock_result, {})
        assert result == 1.2

    def test_maximize_profit_factor(self):
        """Test profit factor objective function."""
        self.mock_result.primary_result.profit_factor = 3.0
        
        result = maximize_profit_factor(self.mock_result, {})
        assert result == 3.0

    def test_sharpe_with_hold_period_constraint_full_compliance(self):
        """Test Sharpe with hold period constraint at 100% compliance."""
        self.mock_result.primary_result.sharpe_ratio = 2.0
        self.mock_result.primary_result.pct_trades_in_target_hold_period = 100.0
        
        result = sharpe_with_hold_period_constraint(self.mock_result, {})
        # Should return original Sharpe ratio with no penalty
        assert result == 2.0

    def test_sharpe_with_hold_period_constraint_zero_compliance(self):
        """Test Sharpe with hold period constraint at 0% compliance."""
        self.mock_result.primary_result.sharpe_ratio = 2.0
        self.mock_result.primary_result.pct_trades_in_target_hold_period = 0.0
        
        result = sharpe_with_hold_period_constraint(self.mock_result, {})
        # Should apply maximum penalty (50% of absolute Sharpe)
        expected = 2.0 - (2.0 * 0.5)  # Full penalty
        assert result == expected

    def test_sharpe_with_hold_period_constraint_missing_data(self):
        """Test Sharpe with hold period constraint when data is missing."""
        self.mock_result.primary_result.sharpe_ratio = 1.5
        self.mock_result.primary_result.pct_trades_in_target_hold_period = None
        
        result = sharpe_with_hold_period_constraint(self.mock_result, {})
        # Should return original Sharpe ratio when data is missing
        assert result == 1.5
