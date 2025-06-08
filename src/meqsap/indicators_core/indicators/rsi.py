"""
Relative Strength Index (RSI) Indicator Implementation.
"""
from typing import List, Any
import pandas as pd
import pandas_ta as ta

from ..base import IndicatorBase, ParameterDefinition
from ..registry import get_indicator_registry


class RSIIndicator(IndicatorBase):
    """Relative Strength Index (RSI) Indicator."""

    @classmethod
    def get_parameter_definitions(cls) -> List[ParameterDefinition]:
        return [
            ParameterDefinition(name="period", param_type=int, description="The time period for RSI calculation.", constraints={"gt": 0})
        ]

    @classmethod
    def get_required_data_coverage_bars(cls, **params: Any) -> int:
        """Return minimum required historical data bars for RSI calculation."""
        period = params.get("period")
        if period is None or not isinstance(period, int) or period <= 0:
            raise ValueError("RSI 'period' for coverage calculation must be a positive integer.")
        # RSI typically needs 'period' bars for the initial smoothing.
        return period

    @classmethod
    def calculate(cls, data: pd.Series, **params: Any) -> pd.Series:
        """
        Calculates the Relative Strength Index.

        Args:
            data: pd.Series of prices (e.g., close prices).
            params: Dictionary of parameters, must include 'period'.

        Returns:
            pd.Series: The RSI values.
        """
        period = params.get("period")
        if period is None or not isinstance(period, int) or period <= 0:
            raise ValueError("RSI 'period' must be a positive integer.")
        return ta.rsi(data, length=period)

# Register the indicator
get_indicator_registry().register('rsi', RSIIndicator)
