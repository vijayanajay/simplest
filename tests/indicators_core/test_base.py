"""
Tests for the base classes in meqsap.indicators_core.base.
"""
import pytest
import re
import pandas as pd
from typing import List, Any
import numpy as np # Added import
from src.meqsap.indicators_core.base import IndicatorBase, ParameterDefinition, ParameterSpace

class TestParameterDefinition:
    def test_creation(self):
        pd_def = ParameterDefinition(name="period", param_type=int, description="Lookback period", default=14, constraints={"gt": 0})
        assert pd_def.name == "period"
        assert pd_def.param_type == int
        assert pd_def.description == "Lookback period"
        assert pd_def.default == 14
        assert pd_def.constraints == {"gt": 0}

class TestParameterSpace:
    def test_creation_and_validation_success(self):
        p_period = ParameterDefinition(name="period", param_type=int, description="Period", default=14, constraints={"gt": 0})
        p_source = ParameterDefinition(name="source", param_type=str, description="Data source", default="close", constraints={"choices": ["open", "high", "low", "close"]})
        space = ParameterSpace(parameters=[p_period, p_source])

        # Valid parameters
        space.validate_values({"period": 20, "source": "open"})
        # Valid with defaults
        space.validate_values({})
        space.validate_values({"period": 10})

    def test_validation_missing_required(self):
        p_period = ParameterDefinition(name="period", param_type=int, description="Period", constraints={"gt": 0}) # No default
        space = ParameterSpace(parameters=[p_period])
        with pytest.raises(ValueError, match=re.escape("Missing required parameter: period")):
            space.validate_values({})

    def test_validation_wrong_type(self):
        p_period = ParameterDefinition(name="period", param_type=int, description="Period")
        space = ParameterSpace(parameters=[p_period])
        with pytest.raises(TypeError, match=re.escape("Parameter 'period' expected type int, got str")):
            space.validate_values({"period": "not_an_int"})

    def test_validation_constraint_gt_fail(self):
        p_period = ParameterDefinition(name="period", param_type=int, description="Period", constraints={"gt": 0})
        space = ParameterSpace(parameters=[p_period])
        with pytest.raises(ValueError, match=re.escape("Parameter 'period' (value: 0) must be greater than 0")):
            space.validate_values({"period": 0})

    def test_validation_constraint_choices_fail(self):
        p_source = ParameterDefinition(name="source", param_type=str, description="Data source", constraints={"choices": ["open", "close"]})
        space = ParameterSpace(parameters=[p_source])
        with pytest.raises(ValueError, match=re.escape("Parameter 'source' (value: high) must be one of ['open', 'close']")):
            space.validate_values({"source": "high"})

class MockIndicator(IndicatorBase):
    @classmethod
    def get_parameter_definitions(cls) -> List[ParameterDefinition]:
        return [
            ParameterDefinition(name="length", param_type=int, description="Lookback length.", constraints={"gt": 0})
        ]

    @classmethod
    def calculate(cls, data: pd.Series, **params: Any) -> pd.Series:
        length = params.get("length")
        if length is None or not isinstance(length, int) or length <= 0:
            raise ValueError("'length' must be a positive integer.")
        return data.rolling(length).mean()

    @classmethod
    def get_required_data_coverage_bars(cls, **params: Any) -> int:
        length = params.get("length")
        if length is None or not isinstance(length, int) or length <= 0:
            raise ValueError("'length' for coverage calculation must be a positive integer.")
        return length

class TestIndicatorBase:
    def test_mock_indicator_instantiation_and_calculation(self):
        # This indirectly tests IndicatorBase's structure if MockIndicator is used
        indicator_instance = MockIndicator() # Assuming no params needed for __init__ or default handling
        data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        result = indicator_instance.calculate(data, length=3)
        expected = pd.Series([np.nan, np.nan, 2.0, 3.0, 4.0])
        pd.testing.assert_series_equal(result, expected, check_dtype=False)

    def test_mock_indicator_get_required_data_coverage_bars(self):
        assert MockIndicator.get_required_data_coverage_bars(length=10) == 10
        with pytest.raises(ValueError, match="'length' for coverage calculation must be a positive integer."):
            MockIndicator.get_required_data_coverage_bars(length=0)
        with pytest.raises(ValueError, match="'length' for coverage calculation must be a positive integer."):
            MockIndicator.get_required_data_coverage_bars()
