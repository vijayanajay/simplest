"""MEQSAP Parameter Optimization Engine

This module provides automated parameter optimization capabilities for single-indicator
trading strategies. It supports various optimization algorithms and objective functions
with constraint handling.

Key Components:
- ParameterSpace: Define and sample parameter search spaces
- OptimizationResult: Comprehensive results container with statistical analysis
- ObjectiveFunction: Framework for optimization targets with constraint support
- ObjectiveFunctionFactory: Factory for creating objective function instances

Usage:
    from meqsap.optimizer import ParameterSpace, OptimizationResult, ObjectiveFunctionFactory
    
    # Create parameter space
    param_space = ParameterSpace({
        'fast_ma': {'type': 'range', 'min': 5, 'max': 50, 'step': 1},
        'slow_ma': {'type': 'range', 'min': 20, 'max': 200, 'step': 5}
    })
    
    # Create objective function
    objective = ObjectiveFunctionFactory.create(
        'sharpe_with_hold_period_constraint',
        params=ObjectiveParams(target_hold_period_days=[5, 20])
    )
"""

from .parameter_space import ParameterSpace
from .objective_functions import (
    ObjectiveFunction,
    ObjectiveValue,
    SharpeRatioObjective,
    SharpeWithHoldPeriodConstraint,
    ObjectiveFunctionFactory
)
from .algorithms import (
    OptimizationAlgorithm,
    GridSearchOptimizer,
    RandomSearchOptimizer,
    OptimizationFactory,
    OptimizationProgress
)
from .engine import (
    OptimizationEngine,
    evaluate_parameter_set,
    generate_optimization_report
)
from .results import OptimizationResult
from .config import OptimizationConfig

__all__ = [
    "OptimizationEngine",
    "ParameterSpace",
    "OptimizationResult",
    "ObjectiveFunction",
    "ObjectiveValue",
    "SharpeRatioObjective",
    "SharpeWithHoldPeriodConstraint",
    "ObjectiveFunctionFactory",
    "OptimizationAlgorithm",
    "GridSearchOptimizer",
    "RandomSearchOptimizer",
    "OptimizationFactory",
    "OptimizationProgress",
    "evaluate_parameter_set",
    "generate_optimization_report",
]

__version__ = "0.1.0"
