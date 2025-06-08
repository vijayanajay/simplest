"""
Moving Average Indicator Implementations.
"""
from typing import List, Any
import pandas as pd
import pandas_ta as ta

from ..base import IndicatorBase, ParameterDefinition
from ..registry import get_indicator_registry


class SimpleMovingAverageIndicator(IndicatorBase):
    """Simple Moving Average (SMA) Indicator."""

    @classmethod
    def get_parameter_definitions(cls) -> List[ParameterDefinition]:
        return [
            ParameterDefinition(name="period", param_type=int, description="The time period for the SMA.", constraints={"gt": 0})
        ]

    @classmethod
    def get_required_data_coverage_bars(cls, **params: Any) -> int:
        """Return minimum required historical data bars for SMA calculation."""
        period = params.get("period")
        if period is None or not isinstance(period, int) or period <= 0:
            raise ValueError("SMA 'period' for coverage calculation must be a positive integer.")
        # SMA needs 'period' bars to produce the first value.
        # The first value is at index period-1. So, period bars are needed.
        return period

    @classmethod
    def calculate(cls, data: pd.Series, **params: Any) -> pd.Series:
        """
        Calculates the Simple Moving Average.

        Args:
            data: pd.Series of prices (e.g., close prices).
            params: Dictionary of parameters, must include 'period'.

        Returns:
            pd.Series: The SMA values.
        """
        period = params.get("period")
        if period is None or not isinstance(period, int) or period <= 0:
            raise ValueError("SMA 'period' must be a positive integer.")
        return ta.sma(data, length=period)

# Register the indicator
get_indicator_registry().register('simple_moving_average', SimpleMovingAverageIndicator)
