"""
Objective function framework for parameter optimization.

This module provides the abstract base class and concrete implementations
for optimization objectives including constraint-aware objectives.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd
from meqsap.backtest import BacktestResult
from meqsap.config import ObjectiveParams


@dataclass
class ObjectiveValue:
    """Container for objective function evaluation results."""
    
    value: float
    constraint_satisfied: bool
    constraint_details: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        """Validate objective value."""
        if not isinstance(self.value, (int, float)) or np.isnan(self.value):
            raise ValueError(f"Objective value must be a valid number, got: {self.value}")


class ObjectiveFunction(ABC):
    """Abstract base class for optimization objective functions."""
    
    def __init__(self, params: Optional[ObjectiveParams] = None):
        """Initialize objective function with parameters.
        
        Args:
            params: Configuration parameters for the objective function
        """
        self.params = params or ObjectiveParams()
        self._validate_params()
    
    @abstractmethod
    def evaluate(self, backtest_result: BacktestResult) -> ObjectiveValue:
        """Evaluate the objective function for a backtest result.
        
        Args:
            backtest_result: Results from strategy backtest
            
        Returns:
            ObjectiveValue containing the evaluation result and constraint status
        """
        pass
    
    @abstractmethod
    def _validate_params(self) -> None:
        """Validate objective function parameters."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the objective function."""
        pass
    
    @property
    @abstractmethod
    def higher_is_better(self) -> bool:
        """Return True if higher objective values are better."""
        pass


class SharpeRatioObjective(ObjectiveFunction):
    """Standard Sharpe ratio objective function."""
    
    def __init__(self, params: Optional[ObjectiveParams] = None):
        """Initialize Sharpe ratio objective.
        
        Args:
            params: Configuration parameters (risk_free_rate, etc.)
        """
        super().__init__(params)
    
    def evaluate(self, backtest_result: BacktestResult) -> ObjectiveValue:
        """Evaluate Sharpe ratio for backtest results.
        
        Args:
            backtest_result: Results from strategy backtest
            
        Returns:
            ObjectiveValue with Sharpe ratio and constraint status
        """
        if not backtest_result.portfolio_returns or len(backtest_result.portfolio_returns) == 0:
            return ObjectiveValue(
                value=-np.inf,
                constraint_satisfied=False,
                constraint_details={"error": "No portfolio returns available"},
                metadata={"insufficient_data": True}
            )
        
        # Calculate Sharpe ratio
        returns = pd.Series(backtest_result.portfolio_returns)
        risk_free_rate = getattr(self.params, 'risk_free_rate', 0.0)
        
        excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
        sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
        
        # Basic constraint check (minimum trades)
        min_trades = getattr(self.params, 'min_trades', 10)
        num_trades = len(backtest_result.trades)
        constraint_satisfied = num_trades >= min_trades
        
        return ObjectiveValue(
            value=sharpe_ratio if not np.isnan(sharpe_ratio) else -np.inf,
            constraint_satisfied=constraint_satisfied,
            constraint_details={
                "min_trades_required": min_trades,
                "actual_trades": num_trades,
                "trades_constraint_met": constraint_satisfied
            },
            metadata={
                "excess_returns_mean": excess_returns.mean(),
                "excess_returns_std": excess_returns.std(),
                "annualized_factor": np.sqrt(252)
            }
        )
    
    def _validate_params(self) -> None:
        """Validate Sharpe ratio parameters."""
        if hasattr(self.params, 'risk_free_rate'):
            if not isinstance(self.params.risk_free_rate, (int, float)):
                raise ValueError("risk_free_rate must be a number")
            if self.params.risk_free_rate < 0 or self.params.risk_free_rate > 1:
                raise ValueError("risk_free_rate must be between 0 and 1")
    
    @property
    def name(self) -> str:
        """Return the name of the objective function."""
        return "SharpeRatio"
    
    @property
    def higher_is_better(self) -> bool:
        """Return True since higher Sharpe ratios are better."""
        return True


class SharpeWithHoldPeriodConstraint(ObjectiveFunction):
    """Sharpe ratio objective with holding period constraints."""
    
    def __init__(self, params: Optional[ObjectiveParams] = None):
        """Initialize Sharpe ratio with holding period constraint.
        
        Args:
            params: Configuration parameters including target_hold_period_days
        """
        super().__init__(params)
    
    def evaluate(self, backtest_result: BacktestResult) -> ObjectiveValue:
        """Evaluate Sharpe ratio with holding period constraints.
        
        Args:
            backtest_result: Results from strategy backtest
            
        Returns:
            ObjectiveValue with constrained Sharpe ratio evaluation
        """
        if not backtest_result.portfolio_returns or len(backtest_result.portfolio_returns) == 0:
            return ObjectiveValue(
                value=-np.inf,
                constraint_satisfied=False,
                constraint_details={"error": "No portfolio returns available"},
                metadata={"insufficient_data": True}
            )
        
        # Calculate base Sharpe ratio
        returns = pd.Series(backtest_result.portfolio_returns)
        risk_free_rate = getattr(self.params, 'risk_free_rate', 0.0)
        
        excess_returns = returns - risk_free_rate / 252
        base_sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
        
        if np.isnan(base_sharpe):
            base_sharpe = -np.inf
        
        # Evaluate holding period constraints
        hold_period_metrics = self._evaluate_holding_period_constraints(backtest_result)
        
        # Calculate constraint-adjusted objective value
        constraint_penalty = self._calculate_constraint_penalty(hold_period_metrics)
        adjusted_sharpe = base_sharpe * (1 - constraint_penalty)
        
        # Overall constraint satisfaction
        min_trades = getattr(self.params, 'min_trades', 10)
        num_trades = len(backtest_result.trades)
        trades_constraint_met = num_trades >= min_trades
        
        overall_constraint_satisfied = (
            hold_period_metrics["constraint_satisfied"] and 
            trades_constraint_met
        )
        
        constraint_details = {
            **hold_period_metrics,
            "min_trades_required": min_trades,
            "actual_trades": num_trades,
            "trades_constraint_met": trades_constraint_met,
            "constraint_penalty": constraint_penalty,
            "base_sharpe_ratio": base_sharpe
        }
        
        return ObjectiveValue(
            value=adjusted_sharpe,
            constraint_satisfied=overall_constraint_satisfied,
            constraint_details=constraint_details,
            metadata={
                "base_sharpe_ratio": base_sharpe,
                "constraint_penalty": constraint_penalty,
                "adjustment_factor": 1 - constraint_penalty
            }
        )
    
    def _evaluate_holding_period_constraints(self, backtest_result: BacktestResult) -> Dict[str, Any]:
        """Evaluate holding period constraints for trades.
        
        Args:
            backtest_result: Results from strategy backtest
            
        Returns:
            Dictionary with holding period constraint evaluation
        """
        if not hasattr(backtest_result, 'trade_duration_stats') or not backtest_result.trade_duration_stats:
            # Calculate trade durations from trades if not available
            trade_durations = self._calculate_trade_durations(backtest_result.trades)
        else:
            trade_durations = backtest_result.trade_duration_stats.get('durations', [])
        
        if not trade_durations:
            return {
                "constraint_satisfied": False,
                "error": "No trade durations available",
                "avg_hold_period": 0,
                "median_hold_period": 0,
                "pct_within_target": 0,
                "target_range": getattr(self.params, 'target_hold_period_days', [5, 20])
            }
        
        # Get target holding period range
        target_range = getattr(self.params, 'target_hold_period_days', [5, 20])
        min_hold, max_hold = target_range
        
        # Calculate statistics
        durations_array = np.array(trade_durations)
        avg_hold_period = np.mean(durations_array)
        median_hold_period = np.median(durations_array)
        
        # Calculate percentage within target range
        within_target = (durations_array >= min_hold) & (durations_array <= max_hold)
        pct_within_target = np.mean(within_target) * 100
        
        # Constraint satisfaction threshold
        min_pct_within_target = getattr(self.params, 'min_pct_within_target', 70.0)
        constraint_satisfied = pct_within_target >= min_pct_within_target
        
        return {
            "constraint_satisfied": constraint_satisfied,
            "avg_hold_period": float(avg_hold_period),
            "median_hold_period": float(median_hold_period),
            "pct_within_target": float(pct_within_target),
            "target_range": target_range,
            "min_pct_within_target": min_pct_within_target,
            "total_trades": len(trade_durations),
            "trades_within_target": int(np.sum(within_target))
        }
    
    def _calculate_trade_durations(self, trades: List[Dict[str, Any]]) -> List[float]:
        """Calculate trade durations from trade records.
        
        Args:
            trades: List of trade dictionaries
            
        Returns:
            List of trade durations in days
        """
        durations = []
        for trade in trades:
            if 'entry_date' in trade and 'exit_date' in trade:
                entry_date = pd.to_datetime(trade['entry_date'])
                exit_date = pd.to_datetime(trade['exit_date'])
                duration = (exit_date - entry_date).days
                durations.append(duration)
        return durations
    
    def _calculate_constraint_penalty(self, hold_period_metrics: Dict[str, Any]) -> float:
        """Calculate penalty for constraint violations.
        
        Args:
            hold_period_metrics: Holding period constraint evaluation results
            
        Returns:
            Penalty factor (0.0 = no penalty, 1.0 = maximum penalty)
        """
        if hold_period_metrics.get("error"):
            return 1.0  # Maximum penalty for missing data
        
        pct_within_target = hold_period_metrics.get("pct_within_target", 0)
        min_pct_within_target = hold_period_metrics.get("min_pct_within_target", 70.0)
        
        if pct_within_target >= min_pct_within_target:
            return 0.0  # No penalty if constraint is satisfied
        
        # Linear penalty based on how far below the threshold
        penalty_factor = (min_pct_within_target - pct_within_target) / min_pct_within_target
        return min(penalty_factor * 0.5, 0.5)  # Cap penalty at 50%
    
    def _validate_params(self) -> None:
        """Validate holding period constraint parameters."""
        if hasattr(self.params, 'target_hold_period_days'):
            target_range = self.params.target_hold_period_days
            if not isinstance(target_range, list) or len(target_range) != 2:
                raise ValueError("target_hold_period_days must be a list of [min, max] values")
            if target_range[0] >= target_range[1]:
                raise ValueError("target_hold_period_days min must be less than max")
            if target_range[0] <= 0:
                raise ValueError("target_hold_period_days min must be positive")
        
        if hasattr(self.params, 'min_pct_within_target'):
            min_pct = self.params.min_pct_within_target
            if not isinstance(min_pct, (int, float)) or min_pct <= 0 or min_pct > 100:
                raise ValueError("min_pct_within_target must be between 0 and 100")
    
    @property
    def name(self) -> str:
        """Return the name of the objective function."""
        return "SharpeWithHoldPeriodConstraint"
    
    @property
    def higher_is_better(self) -> bool:
        """Return True since higher Sharpe ratios are better."""
        return True


class ObjectiveFunctionFactory:
    """Factory for creating objective function instances."""
    
    _registry = {
        "sharpe_ratio": SharpeRatioObjective,
        "sharpe_with_hold_period_constraint": SharpeWithHoldPeriodConstraint,
    }
    
    @classmethod
    def create(cls, objective_type: str, params: Optional[ObjectiveParams] = None) -> ObjectiveFunction:
        """Create an objective function instance.
        
        Args:
            objective_type: Type of objective function to create
            params: Configuration parameters for the objective function
            
        Returns:
            ObjectiveFunction instance
            
        Raises:
            ValueError: If objective_type is not supported
        """
        if objective_type not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(f"Unsupported objective function '{objective_type}'. Available: {available}")
        
        objective_class = cls._registry[objective_type]
        return objective_class(params)
    
    @classmethod
    def list_available(cls) -> List[str]:
        """List available objective function types.
        
        Returns:
            List of supported objective function type names
        """
        return list(cls._registry.keys())
