"""
Tests for the RSIIndicator.
"""
import pytest
import pandas as pd
import numpy as np
import pandas_ta as ta # For comparing results
from src.meqsap.indicators_core.indicators.rsi import RSIIndicator
from src.meqsap.indicators_core.base import ParameterDefinition

class TestRSIIndicator:

    def test_get_parameter_definitions(self):
        defs = RSIIndicator.get_parameter_definitions()
        assert len(defs) == 1
        assert isinstance(defs[0], ParameterDefinition)
        assert defs[0].name == "period"
        assert defs[0].param_type == int
        assert defs[0].constraints == {"gt": 0}

    def test_calculate_rsi_valid(self):
        # Data from pandas_ta documentation example
        data = pd.Series([10, 12, 15, 14, 13, 16, 18, 20, 19, 17, 15, 16, 14, 12, 10])
        params = {"period": 14} # Standard RSI period
        result = RSIIndicator.calculate(data, **params)

        # Calculate expected RSI using pandas_ta directly for comparison
        expected = ta.rsi(data, length=14)
        pd.testing.assert_series_equal(result, expected, check_dtype=False)

    def test_calculate_rsi_invalid_period_zero(self):
        data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        params = {"period": 0}
        with pytest.raises(ValueError, match="'period' must be a positive integer"):
            RSIIndicator.calculate(data, **params)

    def test_calculate_rsi_invalid_period_negative(self):
        data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        params = {"period": -5}
        with pytest.raises(ValueError, match="'period' must be a positive integer"):
            RSIIndicator.calculate(data, **params)

    def test_calculate_rsi_missing_period(self):
        data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        with pytest.raises(ValueError, match="'period' must be a positive integer"):
            RSIIndicator.calculate(data) # Missing period

    def test_get_required_data_coverage_bars_valid(self):
        assert RSIIndicator.get_required_data_coverage_bars(period=14) == 14
        assert RSIIndicator.get_required_data_coverage_bars(period=1) == 1

    def test_get_required_data_coverage_bars_invalid_period(self):
        with pytest.raises(ValueError, match="RSI 'period' for coverage calculation must be a positive integer."):
            RSIIndicator.get_required_data_coverage_bars(period=0)
        with pytest.raises(ValueError, match="RSI 'period' for coverage calculation must be a positive integer."):
            RSIIndicator.get_required_data_coverage_bars(period=-5)

    def test_get_required_data_coverage_bars_missing_period(self):
        with pytest.raises(ValueError, match="RSI 'period' for coverage calculation must be a positive integer."):
            RSIIndicator.get_required_data_coverage_bars()
