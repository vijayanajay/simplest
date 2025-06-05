"""
Pydantic models for defining parameter types and search spaces in configurations.
These models are used by strategy parameter classes (e.g., MovingAverageCrossoverParams).
"""
from typing import Union, List, Any, Literal

from pydantic import BaseModel, Field, field_validator


class ParameterRange(BaseModel):
    """Defines a range for a parameter search space."""
    type: Literal["range"] = "range"
    start: float = Field(..., description="Start of the range (inclusive).")
    stop: float = Field(..., description="End of the range (inclusive).")
    step: float = Field(1.0, gt=0, description="Step size for the range.")

    @field_validator('stop')
    @classmethod
    def stop_must_be_greater_than_or_equal_to_start(cls, v: float, info: Any) -> float:
        if 'start' in info.data and v < info.data['start']:
            raise ValueError('stop must be greater than or equal to start')
        return v


class ParameterChoices(BaseModel):
    """Defines a list of discrete choices for a parameter."""
    type: Literal["choices"] = "choices"
    values: List[Any] = Field(..., min_length=1, description="List of possible values.")


class ParameterValue(BaseModel):
    """Defines an explicit single value for a parameter, often used alongside search space definitions."""
    type: Literal["value"] = "value"
    value: Any = Field(..., description="The fixed value for the parameter.")


# Union type representing all possible ways a parameter can be defined in the configuration.
# It can be a simple Python type (for a fixed value) or one of the structured Pydantic models.
ParameterDefinitionType = Union[
    float,
    int,
    str,
    bool,
    ParameterRange,
    ParameterChoices,
    ParameterValue
]
