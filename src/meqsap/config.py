"""
Configuration module for MEQSAP.

This module handles loading and validation of strategy configurations from YAML files.
"""

from typing import Any, Dict, Literal, Optional, Type
from datetime import date
import re
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class ConfigError(Exception):
    """Exception raised for configuration errors."""

    pass


class BaseStrategyParams(BaseModel):
    """Base class for all strategy parameters."""

    pass


class MovingAverageCrossoverParams(BaseStrategyParams):
    """Parameters for the Moving Average Crossover strategy."""

    fast_ma: int = Field(..., gt=0, description="Fast moving average period")
    slow_ma: int = Field(..., gt=0, description="Slow moving average period")

    @field_validator("slow_ma")
    @classmethod
    def slow_ma_must_be_greater_than_fast_ma(cls, v: int, info: Any) -> int:
        """Validate that slow_ma is greater than fast_ma."""
        if "fast_ma" in info.data and v <= info.data["fast_ma"]:
            raise ValueError("slow_ma must be greater than fast_ma")
        return v


class StrategyConfig(BaseModel):
    """Configuration for a trading strategy backtest."""

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
            raise ValueError(f"Unknown strategy type: {strategy_type}")

        return validator_class(**params)


def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """Load a YAML configuration file.

    Args:
        file_path: Path to the YAML configuration file

    Returns:
        A dictionary containing the parsed YAML configuration

    Raises:
        ConfigError: If the file can't be found or contains invalid YAML
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            config_data = yaml.safe_load(file)
            if not config_data:
                raise ConfigError("Empty configuration file")
            return config_data
    except FileNotFoundError:
        raise ConfigError(f"Configuration file not found: {file_path}")
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in configuration: {str(e)}")
    except Exception as e:
        raise ConfigError(f"Error loading configuration: {str(e)}")


def validate_config(config_data: Dict[str, Any]) -> StrategyConfig:
    """Validate a configuration dictionary against the schema.

    Args:
        config_data: A dictionary containing the configuration data

    Returns:
        A validated StrategyConfig object

    Raises:
        ConfigError: If the configuration is invalid
    """
    try:
        # Create and validate the main config
        config = StrategyConfig(**config_data)
        
        # Validate strategy-specific parameters
        config.validate_strategy_params()
        
        return config
    except ValueError as e:
        raise ConfigError(f"Configuration validation failed: {str(e)}")
    except Exception as e:
        raise ConfigError(f"Unexpected error in configuration validation: {str(e)}")
