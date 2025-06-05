"""
Tests for the SimpleMovingAverageIndicator.
"""
import pytest
import pandas as pd
import numpy as np
from src.meqsap.indicators_core.indicators.moving_average import SimpleMovingAverageIndicator
from src.meqsap.indicators_core.base import ParameterDefinition

class TestSimpleMovingAverageIndicator:

    def test_get_parameter_definitions(self):
        defs = SimpleMovingAverageIndicator.get_parameter_definitions()
        assert len(defs) == 1
        assert isinstance(defs[0], ParameterDefinition)
        assert defs[0].name == "period"
        assert defs[0].param_type == int
        assert defs[0].constraints == {"gt": 0}

    def test_calculate_sma_valid(self):
        indicator = SimpleMovingAverageIndicator()
        data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        params = {"period": 3}
        result = indicator.calculate(data, **params)

        expected = pd.Series([np.nan, np.nan, 2.0, 3.0, 4.0], name="SMA_3") # pandas-ta names the series
        pd.testing.assert_series_equal(result, expected, check_dtype=False, check_names=True)

    def test_calculate_sma_invalid_period_zero(self):
        indicator = SimpleMovingAverageIndicator()
        data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        params = {"period": 0}
        with pytest.raises(ValueError, match="'period' must be a positive integer"):
            indicator.calculate(data, **params)

    def test_calculate_sma_invalid_period_negative(self):
        indicator = SimpleMovingAverageIndicator()
        data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        params = {"period": -5}
        with pytest.raises(ValueError, match="'period' must be a positive integer"):
            indicator.calculate(data, **params)

    def test_calculate_sma_missing_period(self):
        indicator = SimpleMovingAverageIndicator()
        data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        with pytest.raises(ValueError, match="'period' must be a positive integer"):
            indicator.calculate(data) # Missing period

    def test_get_required_data_coverage_bars_valid(self):
        assert SimpleMovingAverageIndicator.get_required_data_coverage_bars(period=10) == 10
        assert SimpleMovingAverageIndicator.get_required_data_coverage_bars(period=1) == 1

    def test_get_required_data_coverage_bars_invalid_period(self):
        with pytest.raises(ValueError, match="SMA 'period' for coverage calculation must be a positive integer."):
            SimpleMovingAverageIndicator.get_required_data_coverage_bars(period=0)
        with pytest.raises(ValueError, match="SMA 'period' for coverage calculation must be a positive integer."):
            SimpleMovingAverageIndicator.get_required_data_coverage_bars(period=-5)

    def test_get_required_data_coverage_bars_missing_period(self):
        with pytest.raises(ValueError, match="SMA 'period' for coverage calculation must be a positive integer."):
            SimpleMovingAverageIndicator.get_required_data_coverage_bars()
