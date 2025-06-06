from typing import Protocol, Any, Dict, Callable
import logging

from ..backtest import BacktestAnalysisResult
from ..exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class ObjectiveFunction(Protocol):
    """Protocol for objective functions used in optimization."""

    def __call__(self, result: BacktestAnalysisResult, objective_params: Dict[str, Any]) -> float:
        """
        Calculate the objective score from a backtest result.

        Args:
            result: The complete backtest analysis result.
            objective_params: Additional parameters for the objective function.

        Returns:
            A float representing the objective score. Higher is better.
        """
        ...


# --- Objective Function Implementations ---

def maximize_sharpe_ratio(result: BacktestAnalysisResult, params: Dict[str, Any]) -> float:
    """Objective function to maximize the Sharpe Ratio."""
    return result.primary_result.sharpe_ratio


def maximize_calmar_ratio(result: BacktestAnalysisResult, params: Dict[str, Any]) -> float:
    """Objective function to maximize the Calmar Ratio."""
    return result.primary_result.calmar_ratio


def maximize_profit_factor(result: BacktestAnalysisResult, params: Dict[str, Any]) -> float:
    """Objective function to maximize the Profit Factor."""
    return result.primary_result.profit_factor


def sharpe_with_hold_period_constraint(result: BacktestAnalysisResult, params: Dict[str, Any]) -> float:
    """
    Objective function that maximizes Sharpe Ratio while penalizing strategies
    that do not meet the target trade holding period constraints.
    """
    sharpe = result.primary_result.sharpe_ratio
    pct_in_range = result.primary_result.pct_trades_in_target_hold_period

    if pct_in_range is None:
        logger.warning("pct_trades_in_target_hold_period not found in backtest result. Returning raw Sharpe Ratio.")
        return sharpe

    # Simple linear penalty. If 100% in range, penalty is 0. If 0% in range, penalty is 1.
    penalty_factor = (100.0 - pct_in_range) / 100.0

    # Apply penalty. A full penalty (factor=1) will halve the sharpe ratio.
    penalty = abs(sharpe) * penalty_factor * 0.5

    logger.debug(f"Hold period constraint: {pct_in_range:.1f}% in range. Sharpe: {sharpe:.3f}, Penalty: {penalty:.3f}")

    return sharpe - penalty


# --- Registry ---

OBJECTIVE_FUNCTION_REGISTRY: Dict[str, ObjectiveFunction] = {
    "SharpeRatio": maximize_sharpe_ratio,
    "CalmarRatio": maximize_calmar_ratio,
    "ProfitFactor": maximize_profit_factor,
    "SharpeWithHoldPeriodConstraint": sharpe_with_hold_period_constraint,
}


def get_objective_function(name: str) -> ObjectiveFunction:
    """Retrieves an objective function from the registry by name."""
    func = OBJECTIVE_FUNCTION_REGISTRY.get(name)
    if func is None:
        raise ConfigurationError(
            f"Objective function '{name}' not found. "
            f"Available functions: {list(OBJECTIVE_FUNCTION_REGISTRY.keys())}"
        )
    return func
