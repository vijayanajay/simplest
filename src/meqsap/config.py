"""
Configuration module for MEQSAP.

This module handles loading and validation of strategy configurations from YAML files.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Literal, Optional, Type, Union
from datetime import date
import re
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from pydantic_core import ValidationError # Use pydantic_core's ValidationError for Pydantic v2

from .exceptions import ConfigurationError
from .indicators_core.parameters import ParameterDefinitionType, ParameterValue, ParameterRange, ParameterChoices  # Updated import


class BaseStrategyParams(BaseModel, ABC):
    """Base class for all strategy parameters."""

    @abstractmethod
    def get_required_data_coverage_bars(self) -> int:
        """
        Returns the minimum number of data bars required by the strategy for its calculations.
        This is the raw requirement from the strategy's perspective (e.g., longest MA period).
        The vibe check framework might apply additional safety factors (e.g., 2x this value).

        This method MUST be overridden by concrete strategy parameter classes.
        """
        pass


class MovingAverageCrossoverParams(BaseStrategyParams):
    """Parameters for the Moving Average Crossover strategy."""
    
    fast_ma: ParameterDefinitionType = Field(..., description="Fast moving average period or definition.")
    slow_ma: ParameterDefinitionType = Field(..., description="Slow moving average period or definition.")
    
    @field_validator("fast_ma", "slow_ma")
    @classmethod
    def ma_period_must_be_positive(cls, v: ParameterDefinitionType, info: Any) -> ParameterDefinitionType:
        """Validate that MA periods are positive when provided as fixed numeric values."""
        actual_value: Any = None
        is_fixed_numeric = False

        if isinstance(v, (int, float)):
            actual_value = v
            is_fixed_numeric = True
        elif isinstance(v, ParameterValue): # Pydantic passes the model instance
            if isinstance(v.value, (int, float)):
                actual_value = v.value
                is_fixed_numeric = True

        if is_fixed_numeric and actual_value <= 0: # type: ignore
            raise ValueError(f"{info.field_name} must be positive when provided as a fixed numeric value")
        return v

    @field_validator("slow_ma")
    @classmethod
    def slow_ma_must_be_greater_than_fast_ma(cls, v: ParameterDefinitionType, info: Any) -> ParameterDefinitionType:
        """Validate that slow_ma is greater than fast_ma."""
        if "fast_ma" in info.data:
            fast_ma_param_def = info.data["fast_ma"]
            slow_ma_param_def = v

            fast_val_numeric = None
            slow_val_numeric = None
            if isinstance(fast_ma_param_def, (int, float)):
                fast_val_numeric = float(fast_ma_param_def)
            elif isinstance(fast_ma_param_def, ParameterValue) and isinstance(fast_ma_param_def.value, (int, float)):
                fast_val_numeric = float(fast_ma_param_def.value)
            if isinstance(slow_ma_param_def, (int, float)):
                slow_val_numeric = float(slow_ma_param_def)
            elif isinstance(slow_ma_param_def, ParameterValue) and isinstance(slow_ma_param_def.value, (int, float)):
                slow_val_numeric = float(slow_ma_param_def.value)

            if fast_val_numeric is not None and slow_val_numeric is not None and slow_val_numeric <= fast_val_numeric:
                raise ValueError("slow_ma must be greater than fast_ma when both are fixed values")
        return v

    def get_required_data_coverage_bars(self) -> int:
        """Return the slow MA period as the minimum data requirement."""
        # Consider the maximum possible value if slow_ma is a range or choice
        slow_ma_max = self._get_parameter_maximum(self.slow_ma)
        return int(slow_ma_max)

    def _get_parameter_maximum(self, param: ParameterDefinitionType) -> float:
        """Extract maximum possible value from parameter definition."""
        # Check for Pydantic model instances first
        if isinstance(param, ParameterRange):
            return float(param.stop)
        elif isinstance(param, ParameterChoices):
            if not all(isinstance(val, (int, float)) for val in param.values):
                raise ConfigurationError(f"Non-numeric value found in choices for parameter: {param}")
            return float(max(param.values))
        elif isinstance(param, ParameterValue):
            if not isinstance(param.value, (int, float)):
                raise ConfigurationError(f"Non-numeric value found in ParameterValue for parameter: {param}")
            return float(param.value)
        # Handle direct primitive types
        if isinstance(param, (int, float)):
            return float(param)
        # Fallback for dict representation (e.g. from model_dump or direct dict in tests)
        elif isinstance(param, dict):
            param_type = param.get("type")
            if param_type == "range":
                return float(param["stop"])
            elif param_type == "choices":
                if not all(isinstance(val, (int, float)) for val in param["values"]):
                    raise ConfigurationError(f"Non-numeric value found in choices for parameter: {param}")
                return float(max(param["values"]))
            elif param_type == "value":
                if not isinstance(param["value"], (int, float)):
                    raise ConfigurationError(f"Non-numeric value found in ParameterValue dict for parameter: {param}")
                return float(param["value"])        
            else:
                raise ConfigurationError(f"Unknown parameter type: {param_type}")
            raise ConfigurationError(f"Unable to determine maximum value for parameter: {param} of type {type(param)}")


class BuyAndHoldParams(BaseStrategyParams):
    """Parameters for the Buy & Hold strategy.
    
    Buy & Hold strategy requires no parameters - it simply buys on the first day
    and holds forever. This class serves as a placeholder to maintain consistency
    with the strategy parameter framework.
    """
    
    def get_required_data_coverage_bars(self) -> int:
        """Return minimum data requirement for Buy & Hold strategy.
        
        Buy & Hold only needs one day of data to execute, but we return 1
        to satisfy the abstract method requirement.
        """
        return 1


# Type alias for all possible strategy parameter types (for use in raw YAML data)
# This represents the unvalidated parameter dictionary that comes from YAML parsing,
# which gets converted to concrete BaseStrategyParams instances via validate_strategy_params()
StrategyParamsDict = Dict[str, Any]

class OptimizationConfig(BaseModel):
    """Defines the configuration for a parameter optimization run."""
    active: bool = Field(False, description="Whether optimization is active for this run.")
    algorithm: Literal["GridSearch", "RandomSearch"] = Field("RandomSearch", description="The optimization algorithm to use.")
    objective_function: str = Field(..., description="The name of the objective function to maximize or minimize.")
    objective_params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the objective function.")
    algorithm_params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the chosen algorithm (e.g., 'n_trials').")
    cache_results: bool = Field(True, description="Whether to cache intermediate backtest results during optimization.")


class BaselineConfig(BaseModel):
    """Configuration for baseline strategy comparison."""
    active: bool = True
    strategy_type: Literal["BuyAndHold", "MovingAverageCrossover"] = "BuyAndHold"
    params: Optional[Dict[str, Any]] = None
    
    @field_validator('strategy_type')
    @classmethod
    def validate_strategy_type(cls, v: str) -> str:
        """Validate that strategy_type is supported."""
        allowed_types = ["BuyAndHold", "MovingAverageCrossover"]
        if v not in allowed_types:
            raise ValueError(f"Baseline strategy_type must be one of {allowed_types}, got: {v}")
        return v
    
    @model_validator(mode='after')
    def validate_params_for_strategy(self) -> 'BaselineConfig':
        """Validate parameters based on strategy type."""
        strategy_type = self.strategy_type
        params = self.params
        
        if strategy_type == "MovingAverageCrossover":
            if not params:
                raise ValueError("MovingAverageCrossover baseline requires 'params' with 'fast_ma' and 'slow_ma'")
            if 'fast_ma' not in params or 'slow_ma' not in params:
                raise ValueError("MovingAverageCrossover baseline requires 'fast_ma' and 'slow_ma' parameters")
            if not isinstance(params['fast_ma'], int) or not isinstance(params['slow_ma'], int):
                raise ValueError("MovingAverageCrossover 'fast_ma' and 'slow_ma' must be integers")
            if params['fast_ma'] >= params['slow_ma']:
                raise ValueError("MovingAverageCrossover 'fast_ma' must be less than 'slow_ma'")
        
        elif strategy_type == "BuyAndHold":
            if params:
                raise ValueError("BuyAndHold baseline does not accept parameters")
        
        return self

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
    strategy_type: Literal["MovingAverageCrossover", "BuyAndHold"] = Field(
        ..., description="Type of trading strategy to backtest"
    )
    strategy_params: StrategyParamsDict = Field(
        ..., description="Strategy-specific parameters"    )
    optimization_config: Optional[OptimizationConfig] = Field(
        None, description="Configuration for parameter optimization."
    )
    baseline_config: Optional[BaselineConfig] = None

    model_config = ConfigDict(extra='forbid')

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

    def get_baseline_config_with_defaults(self, no_baseline: bool = False) -> Optional[BaselineConfig]:
        """Get baseline config with default injection logic."""
        if no_baseline:
            return None
        
        if self.baseline_config is not None:
            return self.baseline_config
        
        # Default to Buy & Hold baseline if not specified
        return BaselineConfig(
            active=True,
            strategy_type="BuyAndHold",
            params=None
        )


class StrategyFactory:
    """Factory for creating strategy parameter validators."""

    _strategy_validators: Dict[str, Type[BaseStrategyParams]] = {
        "MovingAverageCrossover": MovingAverageCrossoverParams,
        "BuyAndHold": BuyAndHoldParams,
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


def load_yaml_config(file_path: Union[str, Path]) -> Dict[str, Any]:
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
