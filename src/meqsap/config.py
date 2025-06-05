"""
Configuration module for MEQSAP.

This module handles loading and validation of strategy configurations from YAML files.
"""

from typing import Any, Dict, Literal, Optional, Type
from datetime import date
import re
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError

from .exceptions import ConfigurationError
from .indicators_core.parameters import ParameterDefinitionType, ParameterValue  # Updated import


class BaseStrategyParams(BaseModel):
    """Base class for all strategy parameters."""

    def get_required_data_coverage_bars(self) -> int:
        """
        Returns the minimum number of data bars required by the strategy for its calculations.
        This is the raw requirement from the strategy's perspective (e.g., longest MA period).
        The vibe check framework might apply additional safety factors (e.g., 2x this value).

        This method MUST be overridden by concrete strategy parameter classes.
        """
        raise NotImplementedError(
            "Strategy parameter classes must implement 'get_required_data_coverage_bars'."
        )


class MovingAverageCrossoverParams(BaseStrategyParams):
    """Parameters for the Moving Average Crossover strategy."""
    
    fast_ma: ParameterDefinitionType = Field(..., description="Fast moving average period or definition.")
    slow_ma: ParameterDefinitionType = Field(..., description="Slow moving average period or definition.")
    
    @field_validator("fast_ma", "slow_ma")
    @classmethod
    def ma_period_must_be_positive(cls, v: ParameterDefinitionType, info: Any) -> ParameterDefinitionType:
        """Validate that MA periods are positive when provided as fixed numeric values."""
        print(f"DEBUG: ma_period_must_be_positive validator called with v={v}, field_name={info.field_name}")
        actual_value: Any = None
        is_fixed_numeric = False

        if isinstance(v, (int, float)):
            actual_value = v
            is_fixed_numeric = True
        elif isinstance(v, ParameterValue): # Pydantic passes the model instance
            if isinstance(v.value, (int, float)):
                actual_value = v.value
                is_fixed_numeric = True

        print(f"DEBUG: actual_value={actual_value}, is_fixed_numeric={is_fixed_numeric}")
        if is_fixed_numeric and actual_value <= 0: # type: ignore
            print(f"DEBUG: Raising 'must be positive' error because {actual_value} <= 0")
            raise ValueError(f"{info.field_name} must be positive when provided as a fixed numeric value")
        return v
    
    @field_validator("slow_ma")
    @classmethod
    def slow_ma_must_be_greater_than_fast_ma(cls, v: ParameterDefinitionType, info: Any) -> ParameterDefinitionType:
        """Validate that slow_ma is greater than fast_ma."""
        print(f"DEBUG: slow_ma_must_be_greater_than_fast_ma validator called with v={v}, info.data={info.data}")
        if "fast_ma" in info.data:
            fast_ma_param_def = info.data["fast_ma"]
            slow_ma_param_def = v

            fast_val_numeric: Optional[float] = None
            if isinstance(fast_ma_param_def, (int, float)):
                fast_val_numeric = float(fast_ma_param_def)
            elif isinstance(fast_ma_param_def, ParameterValue) and isinstance(fast_ma_param_def.value, (int, float)):
                fast_val_numeric = float(fast_ma_param_def.value)

            slow_val_numeric: Optional[float] = None
            if isinstance(slow_ma_param_def, (int, float)):
                slow_val_numeric = float(slow_ma_param_def)
            elif isinstance(slow_ma_param_def, ParameterValue) and isinstance(slow_ma_param_def.value, (int, float)):
                slow_val_numeric = float(slow_ma_param_def.value)

            print(f"DEBUG: fast_val_numeric={fast_val_numeric}, slow_val_numeric={slow_val_numeric}")
            if fast_val_numeric is not None and slow_val_numeric is not None and slow_val_numeric <= fast_val_numeric:
                print(f"DEBUG: Raising 'greater than' error because {slow_val_numeric} <= {fast_val_numeric}")
                raise ValueError("slow_ma must be greater than fast_ma when both are fixed values")
        return v

    def get_required_data_coverage_bars(self) -> int:
        """Return the slow MA period as the minimum data requirement."""
        # Consider the maximum possible value if slow_ma is a range or choice
        slow_ma_max = self._get_parameter_maximum(self.slow_ma)
        return int(slow_ma_max)

    def _get_parameter_maximum(self, param: ParameterDefinitionType) -> float:
        """Extract maximum possible value from parameter definition."""
        if isinstance(param, (int, float)):
            return float(param)
        elif isinstance(param, dict):
            param_type = param.get("type")
            if param_type == "range":
                return float(param["stop"])
            elif param_type == "choices":
                # Ensure all choices are numeric before taking max
                if not all(isinstance(val, (int, float)) for val in param["values"]):
                    raise ConfigurationError(f"Non-numeric value found in choices for parameter: {param}")
                return float(max(param["values"]))
            elif param_type == "value":
                return float(param["value"])
        raise ConfigurationError(f"Unable to determine maximum value for parameter: {param}")


class StrategyConfig(BaseModel):
    """
    Configuration for a trading strategy backtest.
    
    Date Range Convention (per ADR-002):
    - start_date: First day to include in analysis (inclusive)
    - end_date: Last day to include in analysis (INCLUSIVE)
    
    Example: start_date="2022-01-01", end_date="2022-12-31" 
    will analyze data from Jan 1 through Dec 31, 2022 (both days included).
    """

    ticker: str = Field(..., description="Stock ticker symbol")
    start_date: date = Field(..., description="Backtest start date")
    end_date: date = Field(..., description="Backtest end date")
    strategy_type: Literal["MovingAverageCrossover"] = Field(
        ..., description="Type of trading strategy to backtest"
    )
    strategy_params: Dict[str, Any] = Field(
        ..., description="Strategy-specific parameters"
    )

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Validate ticker symbol format."""
        if not re.match(r"^[A-Za-z0-9.\-]+$", v):
            raise ValueError("ticker must contain only letters, numbers, dots, and hyphens")
        return v

    @model_validator(mode="after")
    def end_date_must_be_after_start_date(self) -> "StrategyConfig":
        """Validate that end_date is after start_date."""
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self

    def validate_strategy_params(self) -> BaseStrategyParams:
        """Validate strategy parameters based on strategy_type."""
        return StrategyFactory.create_strategy_validator(
            self.strategy_type, self.strategy_params
        )


class StrategyFactory:
    """Factory for creating strategy parameter validators."""

    _strategy_validators: Dict[str, Type[BaseStrategyParams]] = {
        "MovingAverageCrossover": MovingAverageCrossoverParams,
    }

    @classmethod
    def create_strategy_validator(
        cls, strategy_type: str, params: Dict[str, Any]
    ) -> BaseStrategyParams:
        """Create and return the appropriate strategy validator based on strategy_type.

        Args:
            strategy_type: The type of strategy to validate
            params: Strategy-specific parameters

        Returns:
            A validated strategy parameters object

        Raises:
            ValueError: If the strategy type is unknown
        """
        validator_class = cls._strategy_validators.get(strategy_type)
        if not validator_class:
            raise ConfigurationError(f"Unknown strategy type: {strategy_type}")

        try:
            return validator_class(**params)
        except ValueError as e: # Pydantic validation errors are ValueErrors
            raise ConfigurationError(f"Invalid parameters for strategy {strategy_type}: {e}")

    @classmethod
    def validate_strategy_params(
        cls, strategy_type: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate strategy parameters and return validated dict.
        
        Args:
            strategy_type: The type of strategy to validate
            params: Strategy-specific parameters
            
        Returns:
            A dictionary of validated parameters
            
        Raises:
            ConfigurationError: If validation fails
        """
        try:
            validated_params = cls.create_strategy_validator(strategy_type, params)
            return validated_params.model_dump()
        except (ValidationError, ConfigurationError) as e:
            raise ConfigurationError(f"Invalid parameters for strategy {strategy_type}: {e}")


def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """Load a YAML configuration file.

    Args:
        file_path: Path to the YAML configuration file

    Returns:
        A dictionary containing the parsed YAML configuration

    Raises:
        ConfigurationError: If the file can't be found or contains invalid YAML
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            config_data = yaml.safe_load(file)
            if not config_data:
                raise ConfigurationError("Empty configuration file")
            return config_data
    except FileNotFoundError:
        raise ConfigurationError(f"Configuration file not found: {file_path}")
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in configuration: {str(e)}")
    except Exception as e:
        raise ConfigurationError(f"Error loading configuration: {str(e)}")


def validate_config(config_data: Dict[str, Any]) -> StrategyConfig:
    """Validate a configuration dictionary against the schema.

    Args:
        config_data: A dictionary containing the configuration data

    Returns:
        A validated StrategyConfig object

    Raises:
        ConfigurationError: If the configuration is invalid
    """
    try:
        # Create and validate the main config
        config = StrategyConfig(**config_data)
        # Validate strategy params
        config.strategy_params = StrategyFactory.validate_strategy_params(
            config.strategy_type, config.strategy_params
        )
        return config
    except ConfigurationError as e:
        # Re-raise ConfigurationError as-is
        raise e
    except ValueError as e:
        raise ConfigurationError(f"Configuration validation failed: {str(e)}")
    except Exception as e:
        raise ConfigurationError(f"Unexpected error in configuration validation: {str(e)}")
