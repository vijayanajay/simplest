"""Tests for the optimization engine."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from meqsap.optimizer import (
    OptimizationEngine,
    ParameterSpace,
    SharpeRatioObjective,
    SharpeWithHoldPeriodConstraint,
    GridSearchOptimizer,
    RandomSearchOptimizer,
    OptimizationFactory,
    TradeDurationAnalyzer,
    ConstraintEvaluator
)
from meqsap.optimizer.config import OptimizationConfig
from meqsap.optimizer.results import OptimizationResult, ParameterEvaluation


class TestParameterSpace:
    """Test parameter space functionality."""
    
    def test_parameter_space_creation(self):
        """Test parameter space creation from definitions."""
        definitions = {
            'fast_ma': {'range': [5, 15, 2]},
            'slow_ma': {'range': [20, 30, 5]},
            'strategy_type': {'choices': ['MA', 'EMA']}
        }
        
        space = ParameterSpace(definitions)
        assert len(space.parameters) == 3
        assert space.get_grid_size() == 6 * 3 * 2  # 6 fast_ma * 3 slow_ma * 2 strategy_type
    
    def test_grid_search_iterator(self):
        """Test grid search parameter generation."""
        definitions = {
            'param1': {'range': [1, 3, 1]},
            'param2': {'choices': ['A', 'B']}
        }
        
        space = ParameterSpace(definitions)
        combinations = list(space.grid_search_iterator())
        
        assert len(combinations) == 6  # 3 * 2
        assert {'param1': 1, 'param2': 'A'} in combinations
        assert {'param1': 3, 'param2': 'B'} in combinations
    
    def test_random_sample(self):
        """Test random parameter sampling."""
        definitions = {
            'param1': {'range': [1, 10, 1]},
            'param2': {'choices': ['X', 'Y', 'Z']}
        }
        
        space = ParameterSpace(definitions)
        samples = space.random_sample(n_samples=5, random_state=42)
        
        assert len(samples) == 5
        for sample in samples:
            assert 1 <= sample['param1'] <= 10
            assert sample['param2'] in ['X', 'Y', 'Z']


class TestTradeDurationAnalyzer:
    """Test trade duration analysis."""
    
    def test_calculate_trade_durations(self):
        """Test trade duration calculation."""
        trades_df = pd.DataFrame({
            'entry_date': ['2023-01-01', '2023-01-05', '2023-01-10'],
            'exit_date': ['2023-01-03', '2023-01-10', '2023-01-15']
        })
        
        analyzer = TradeDurationAnalyzer()
        durations = analyzer.calculate_trade_durations(trades_df)
        
        assert durations == [2, 5, 5]
    
    def test_analyze_trade_durations(self):
        """Test trade duration statistics."""
        trades_df = pd.DataFrame({
            'entry_date': ['2023-01-01', '2023-01-05', '2023-01-10'],
            'exit_date': ['2023-01-03', '2023-01-10', '2023-01-15']
        })
        
        analyzer = TradeDurationAnalyzer()
        stats = analyzer.analyze_trade_durations(trades_df, target_range=[3, 7])
        
        assert stats.total_trades == 3
        assert stats.average_hold_days == 4.0
        assert stats.median_hold_days == 5.0
        assert stats.trades_within_target == 2  # 5 and 5 are within [3, 7]
        assert stats.percentage_within_target == 2/3 * 100
    
    def test_empty_trades_df(self):
        """Test handling of empty trades DataFrame."""
        trades_df = pd.DataFrame()
        
        analyzer = TradeDurationAnalyzer()
        stats = analyzer.analyze_trade_durations(trades_df)
        
        assert stats.total_trades == 0
        assert stats.average_hold_days == 0.0
        assert stats.percentage_within_target == 0.0


class TestObjectiveFunctions:
    """Test objective functions."""
    
    def test_sharpe_ratio_objective(self):
        """Test Sharpe ratio calculation."""
        # Mock backtest result
        mock_result = Mock()
        mock_result.returns = pd.Series([0.01, 0.02, -0.01, 0.015, 0.005])
        
        objective = SharpeRatioObjective(risk_free_rate=0.02)
        sharpe = objective.evaluate(mock_result)
        
        assert isinstance(sharpe, float)
        assert not np.isnan(sharpe)
    
    def test_sharpe_with_hold_period_constraint(self):
        """Test Sharpe ratio with hold period constraint."""
        # Mock backtest result
        mock_result = Mock()
        mock_result.returns = pd.Series([0.01, 0.02, -0.01, 0.015, 0.005])
        
        # Mock trades DataFrame
        trades_df = pd.DataFrame({
            'entry_date': ['2023-01-01', '2023-01-05'],
            'exit_date': ['2023-01-03', '2023-01-10']
        })
        mock_result.trades_df = trades_df
        
        constraints = {'target_hold_period_days': [3, 7]}
        
        objective = SharpeWithHoldPeriodConstraint()
        constrained_sharpe = objective.evaluate(mock_result, constraints)
        
        assert isinstance(constrained_sharpe, float)
        assert not np.isnan(constrained_sharpe)
        
        # Test constraint adherence
        adherence = objective.get_constraint_adherence(mock_result, constraints)
        assert adherence is not None
        assert adherence.total_constraint_score >= 0


class TestOptimizationAlgorithms:
    """Test optimization algorithms."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parameter_space = ParameterSpace({
            'param1': {'range': [1, 3, 1]},
            'param2': {'choices': ['A', 'B']}
        })
        
        self.objective_function = SharpeRatioObjective()
        
        def mock_evaluation_function(params):
            """Mock evaluation function."""
            mock_result = Mock()
            # Simulate different performance based on parameters
            if params['param1'] == 2 and params['param2'] == 'A':
                mock_result.returns = pd.Series([0.02, 0.01, 0.015])  # Good performance
            else:
                mock_result.returns = pd.Series([0.005, 0.002, 0.001])  # Poor performance
            return mock_result
        
        self.evaluation_function = mock_evaluation_function
    
    def test_grid_search_optimizer(self):
        """Test grid search optimization."""
        optimizer = GridSearchOptimizer(
            parameter_space=self.parameter_space,
            objective_function=self.objective_function,
            evaluation_function=self.evaluation_function,
            show_progress=False
        )
        
        result = optimizer.optimize()
        
        assert isinstance(result, OptimizationResult)
        assert result.algorithm == "grid_search"
        assert result.best_parameters == {'param1': 2, 'param2': 'A'}
        assert result.successful_evaluations > 0
    
    def test_random_search_optimizer(self):
        """Test random search optimization."""
        optimizer = RandomSearchOptimizer(
            parameter_space=self.parameter_space,
            objective_function=self.objective_function,
            evaluation_function=self.evaluation_function,
            max_iterations=10,
            random_state=42,
            show_progress=False
        )
        
        result = optimizer.optimize()
        
        assert isinstance(result, OptimizationResult)
        assert result.algorithm == "random_search"
        assert result.successful_evaluations > 0
    
    def test_optimization_factory(self):
        """Test optimization factory."""
        optimizer = OptimizationFactory.create_optimizer(
            algorithm="grid_search",
            parameter_space=self.parameter_space,
            objective_function=self.objective_function,
            evaluation_function=self.evaluation_function,
            show_progress=False
        )
        
        assert isinstance(optimizer, GridSearchOptimizer)
        
        optimizer = OptimizationFactory.create_optimizer(
            algorithm="random_search",
            parameter_space=self.parameter_space,
            objective_function=self.objective_function,
            evaluation_function=self.evaluation_function,
            algorithm_params={"max_iterations": 5},
            show_progress=False
        )
        
        assert isinstance(optimizer, RandomSearchOptimizer)
        assert optimizer.max_iterations == 5


class TestOptimizationEngine:
    """Test the main optimization engine."""
    
    def test_run_optimization(self):
        """Test complete optimization workflow."""
        # Mock strategy config
        mock_config = Mock()
        mock_config.parameters = {
            'param1': {'range': [1, 3, 1]},
            'param2': {'choices': ['A', 'B']}
        }
        
        # Optimization config
        opt_config = OptimizationConfig(
            algorithm="grid_search",
            objective="sharpe_ratio"
        )
        
        def mock_evaluation_function(params):
            """Mock evaluation function."""
            mock_result = Mock()
            mock_result.returns = pd.Series([0.01, 0.02, 0.005])
            return mock_result
        
        engine = OptimizationEngine()
        
        with patch.object(engine, '_create_objective_function') as mock_obj_func:
            mock_obj_func.return_value = SharpeRatioObjective()
            
            result = engine.run_optimization(
                strategy_config=mock_config,
                optimization_config=opt_config,
                evaluation_function=mock_evaluation_function
            )
        
        assert isinstance(result, OptimizationResult)
        assert result.algorithm == "grid_search"
        assert result.successful_evaluations > 0
    
    def test_create_objective_function(self):
        """Test objective function creation."""
        engine = OptimizationEngine()
        
        # Test Sharpe ratio objective
        obj_func = engine._create_objective_function("sharpe_ratio", {})
        assert isinstance(obj_func, SharpeRatioObjective)
        
        # Test Sharpe with constraint objective
        obj_func = engine._create_objective_function(
            "sharpe_with_hold_period_constraint", 
            {"target_hold_period_days": [5, 15]}
        )
        assert isinstance(obj_func, SharpeWithHoldPeriodConstraint)
        
        # Test unknown objective
        with pytest.raises(ValueError):
            engine._create_objective_function("unknown_objective", {})


class TestOptimizationConfig:
    """Test optimization configuration."""
    
    def test_valid_config(self):
        """Test valid optimization configuration."""
        config = OptimizationConfig(
            algorithm="grid_search",
            objective="sharpe_ratio",
            constraints={
                "target_hold_period_days": [5, 15],
                "min_trades": 20
            }
        )
        
        assert config.algorithm == "grid_search"
        assert config.objective == "sharpe_ratio"
        assert config.constraints["target_hold_period_days"] == [5, 15]
    
    def test_invalid_hold_period(self):
        """Test invalid hold period constraint."""
        with pytest.raises(ValueError):
            OptimizationConfig(
                constraints={"target_hold_period_days": [15, 5]}  # Invalid: min > max
            )
    
    def test_algorithm_params_validation(self):
        """Test algorithm parameters validation."""
        # Valid random search config
        config = OptimizationConfig(
            algorithm="random_search",
            algorithm_params={"max_iterations": 50}
        )
        assert config.algorithm_params["max_iterations"] == 50
        
        # Invalid max_iterations
        with pytest.raises(ValueError):
            OptimizationConfig(
                algorithm="random_search",
                algorithm_params={"max_iterations": 0}
            )


if __name__ == "__main__":
    pytest.main([__file__])
