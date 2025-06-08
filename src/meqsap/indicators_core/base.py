"""
Base classes for indicator definitions, parameter spaces, and metadata.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type, Union

import pandas as pd


class ParameterDefinition:
    """
    Describes the metadata for a single indicator parameter.
    This is used by indicators to define what parameters they accept.
    """
    def __init__(self, name: str, param_type: Type, description: str,
                 default: Any = None, constraints: Dict[str, Any] = None):
        self.name = name
        self.param_type = param_type  # Expected Python type (e.g., int, float)
        self.description = description
        self.default = default
        self.constraints = constraints or {} # e.g., {"gt": 0, "choices": [10, 20]}


class ParameterSpace:
    """
    Defines the collective parameter space for an indicator,
    composed of multiple ParameterDefinition objects.
    """
    def __init__(self, parameters: List[ParameterDefinition]):
        self.parameters: Dict[str, ParameterDefinition] = {p.name: p for p in parameters}

    def validate_values(self, provided_params: Dict[str, Any]) -> None:
        """
        Validates if the provided parameter values conform to the defined space.
        This is a basic validation; Pydantic models handle more complex structure validation.
        """
        for name, definition in self.parameters.items():
            if name not in provided_params and definition.default is None:
                raise ValueError(f"Missing required parameter: {name}")

            value = provided_params.get(name, definition.default)
            if value is None and definition.default is None: # Still missing if default is also None
                continue # Allow if parameter is truly optional

            if not isinstance(value, definition.param_type):
                # Allow int to be float if param_type is float
                if not (definition.param_type is float and isinstance(value, int)):
                    raise TypeError(f"Parameter '{name}' expected type {definition.param_type.__name__}, got {type(value).__name__}")
            # Basic constraint checking (can be expanded)
            if "gt" in definition.constraints and not value > definition.constraints["gt"]:
                raise ValueError(f"Parameter '{name}' (value: {value}) must be greater than {definition.constraints['gt']}")
            if "choices" in definition.constraints and value not in definition.constraints["choices"]:
                raise ValueError(f"Parameter '{name}' (value: {value}) must be one of {definition.constraints['choices']}")


class IndicatorBase(ABC):
    """Abstract base class for all technical indicators.
    
    This class uses classmethods to promote a stateless design. Indicators should not
    store state between calculations.
    """

    @classmethod
    @abstractmethod
    def get_parameter_definitions(cls) -> List[ParameterDefinition]:
        """Return a list of ParameterDefinition objects for this indicator."""
        pass

    @classmethod
    @abstractmethod
    def get_required_data_coverage_bars(cls, **params: Any) -> int:
        """Return minimum required historical data bars for calculation based on provided parameters."""
        pass

    @classmethod
    @abstractmethod
    def calculate(cls, data: pd.Series, **params: Any) -> pd.Series:
        """Calculate the indicator values on the provided data series (e.g., close prices)."""
        pass
