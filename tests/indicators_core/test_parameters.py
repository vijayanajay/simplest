"""
Tests for Pydantic models in meqsap.indicators_core.parameters.
"""
import pytest
from pydantic import ValidationError
from src.meqsap.indicators_core.parameters import ParameterRange, ParameterChoices, ParameterValue, ParameterDefinitionType

class TestParameterRange:
    def test_valid_range(self):
        pr = ParameterRange(start=5, stop=10, step=1)
        assert pr.type == "range"
        assert pr.start == 5
        assert pr.stop == 10
        assert pr.step == 1

    def test_default_step(self):
        pr = ParameterRange(start=1, stop=5)
        assert pr.step == 1.0

    def test_invalid_step_zero(self):
        with pytest.raises(ValidationError, match="Input should be greater than 0"):
            ParameterRange(start=1, stop=5, step=0)

    def test_invalid_step_negative(self):
        with pytest.raises(ValidationError, match="Input should be greater than 0"):
            ParameterRange(start=1, stop=5, step=-1)

    def test_stop_less_than_start(self):
        with pytest.raises(ValidationError, match="stop must be greater than or equal to start"):
            ParameterRange(start=10, stop=5, step=1)

    def test_stop_equal_to_start(self):
        pr = ParameterRange(start=5, stop=5, step=1)
        assert pr.start == 5
        assert pr.stop == 5

class TestParameterChoices:
    def test_valid_choices_numeric(self):
        pc = ParameterChoices(values=[10, 14, 20])
        assert pc.type == "choices"
        assert pc.values == [10, 14, 20]

    def test_valid_choices_string(self):
        pc = ParameterChoices(values=["sma", "ema"])
        assert pc.values == ["sma", "ema"]

    def test_empty_choices_list(self):
        with pytest.raises(ValidationError, match="List should have at least 1 item"):
            ParameterChoices(values=[])

class TestParameterValue:
    def test_valid_value_numeric(self):
        pv = ParameterValue(value=50)
        assert pv.type == "value"
        assert pv.value == 50

    def test_valid_value_string(self):
        pv = ParameterValue(value="fixed_string")
        assert pv.value == "fixed_string"

class TestParameterDefinitionType:
    # ParameterDefinitionType is a Union, its usage is tested implicitly
    # when used in other models like MovingAverageCrossoverParams.
    # Direct testing here would involve checking if Pydantic can parse
    # various valid inputs into this Union type.
    def test_type_assignment(self):
        # This is more of a conceptual check
        my_param: ParameterDefinitionType
        my_param = 10 # Valid
        my_param = {"type": "range", "start": 1, "stop": 5, "step": 1} # Valid
        assert True # If Pydantic model using this type validates, it's working
