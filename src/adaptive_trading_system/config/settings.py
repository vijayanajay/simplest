"""
Configuration loading and parsing using Pydantic models.
"""
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from pydantic import BaseModel, Field, field_validator, model_validator
import yaml

from adaptive_trading_system.common.exceptions import ConfigurationError


class DataSourceConfig(BaseModel):
    """Configuration for the data source."""
    provider: str = Field(default="yfinance", description="Data provider, e.g., 'yfinance', 'local_csv'")
    api_key_env_var: Optional[str] = Field(
        default=None,
        description="Environment variable name for API key if needed"
    )
    symbols: List[str] = Field(
        ...,
        description="List of stock ticker symbols",
        min_items=1
    )
    start_date: str = Field(
        ...,
        description="Start date for historical data (YYYY-MM-DD)",
        regex=r"^\d{4}-\d{2}-\d{2}$"
    )
    end_date: str = Field(
        ...,
        description="End date for historical data (YYYY-MM-DD)",
        regex=r"^\d{4}-\d{2}-\d{2}$"
    )
    interval: str = Field(
        default="1d",
        description="Data interval (e.g., '1d', '1h')"
    )
    
    @field_validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        """Validate that date strings can be parsed."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {v}. Use YYYY-MM-DD format.")
        return v
    
    @model_validator(mode='after')
    def validate_date_range(cls, model):
        """Validate that start_date is before end_date."""
        start_date = model.start_date
        end_date = model.end_date
        
        if start_date and end_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            if start >= end:
                raise ValueError("start_date must be earlier than end_date")
        
        return model


class FeatureConfig(BaseModel):
    """Configuration for feature engineering."""
    # Example parameters for common technical indicators
    sma_periods: List[int] = Field(
        default_factory=lambda: [20, 50, 200],
        description="Simple Moving Average periods"
    )
    ema_periods: List[int] = Field(
        default_factory=lambda: [12, 26],
        description="Exponential Moving Average periods"
    )
    rsi_periods: List[int] = Field(
        default_factory=lambda: [14],
        description="Relative Strength Index periods"
    )
    macd_parameters: Dict[str, int] = Field(
        default_factory=lambda: {"fast": 12, "slow": 26, "signal": 9},
        description="MACD parameters"
    )
    bollinger_bands_parameters: Dict[str, Union[int, float]] = Field(
        default_factory=lambda: {"period": 20, "std_dev": 2.0},
        description="Bollinger Bands parameters"
    )
    custom_feature_scripts: Optional[List[str]] = Field(
        default_factory=list,
        description="Paths to custom feature generation scripts"
    )
    
    @field_validator('sma_periods', 'ema_periods', 'rsi_periods')
    def validate_periods(cls, periods):
        """Validate that periods are positive integers."""
        for period in periods:
            if period <= 0:
                raise ValueError(f"Period must be positive: {period}")
        return periods


class GeneticAlgorithmConfig(BaseModel):
    """Configuration for the Genetic Algorithm."""
    population_size: int = Field(
        default=100,
        ge=10,
        description="Number of individuals in the population"
    )
    generations: int = Field(
        default=50,
        ge=1,
        description="Number of generations to evolve"
    )
    mutation_rate: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Probability of mutation"
    )
    crossover_rate: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Probability of crossover"
    )
    elitism_count: int = Field(
        default=5,
        ge=0,
        description="Number of top individuals to preserve unchanged"
    )
    min_profitable_symbols: int = Field(
        default=1,
        ge=1,
        description="Minimum number of symbols the strategy must be profitable on"
    )
    # Fitness function weights
    fitness_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "net_profit": 1.0,
            "sharpe_ratio": 1.0,
            "max_drawdown": -0.5,
            "win_rate": 0.5
        },
        description="Weights for different fitness components"
    )
    # Rule complexity limits
    max_rule_count: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of rules in a strategy"
    )
    max_conditions_per_rule: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum number of conditions per rule"
    )
    checkpoint_interval: Optional[int] = Field(
        default=10,
        ge=1,
        description="Save GA state every N generations"
    )
    checkpoint_path_template: str = Field(
        default="./state/ga_checkpoints/gen_{generation}.pkl",
        description="Path template for GA checkpoints"
    )
    evolution_log_path: str = Field(
        default="./state/ga_evolution_log.jsonl",
        description="Path for GA evolution log (JSON Lines or CSV)"
    )


class BacktestConfig(BaseModel):
    """Configuration for backtesting."""
    initial_capital: float = Field(
        default=100000.0,
        gt=0,
        description="Initial capital for backtesting"
    )
    commission_percent: float = Field(
        default=0.001,
        ge=0.0,
        description="Commission as a percentage of trade value"
    )
    slippage_percent: float = Field(
        default=0.0005,
        ge=0.0,
        description="Slippage as a percentage of price"
    )
    position_size_percent: float = Field(
        default=0.1,
        gt=0.0,
        le=1.0,
        description="Position size as a percentage of capital"
    )
    # Optional backtest date range if different from data source
    backtest_start_date: Optional[str] = Field(
        default=None,
        description="Start date for backtesting (YYYY-MM-DD)"
    )
    backtest_end_date: Optional[str] = Field(
        default=None,
        description="End date for backtesting (YYYY-MM-DD)"
    )
    
    @field_validator('backtest_start_date', 'backtest_end_date')
    def validate_date_format(cls, v):
        """Validate that date strings can be parsed."""
        if v is None:
            return v
            
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {v}. Use YYYY-MM-DD format.")
        return v
    
    @model_validator(mode='after')
    def validate_date_range(cls, model):
        """Validate that backtest_start_date is before backtest_end_date if both are provided."""
        start_date = model.backtest_start_date
        end_date = model.backtest_end_date
        
        if start_date and end_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            if start >= end:
                raise ValueError("backtest_start_date must be earlier than backtest_end_date")
        
        return model


class ReportingConfig(BaseModel):
    """Configuration for reporting."""
    output_directory: str = Field(
        default="./reports",
        description="Directory to save reports"
    )
    report_formats: List[str] = Field(
        default=["html", "markdown", "csv"],
        description="Formats for the final report"
    )
    top_n_strategies: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Number of top strategies to detail in the report"
    )
    plot_generation: bool = Field(
        default=True,
        description="Whether to generate plots"
    )


class Config(BaseModel):
    """Main configuration model for the adaptive trading system."""
    run_id: Optional[str] = Field(
        default=None,
        description="Optional unique ID for this run, auto-generated if None"
    )
    data_source: DataSourceConfig
    feature_engineering: FeatureConfig = Field(default_factory=FeatureConfig)
    genetic_algorithm: GeneticAlgorithmConfig = Field(default_factory=GeneticAlgorithmConfig)
    backtesting: BacktestConfig = Field(default_factory=BacktestConfig)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)
    logging_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    @field_validator('run_id', mode='before')
    def set_run_id_if_none(cls, v):
        """Generate a run_id if none is provided."""
        import uuid
        return v or str(uuid.uuid4())
    
    @field_validator('logging_level')
    def validate_logging_level(cls, v):
        """Validate that the logging level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid logging level: {v}. Must be one of {valid_levels}")
        return v.upper()


def load_config(config_path: str) -> Config:
    """Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file

    Returns:
        Config: Validated configuration object

    Raises:
        ConfigurationError: If the configuration file is invalid or cannot be loaded
    """
    try:
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}", config_path)
        
        with open(config_file, 'r') as f:
            try:
                config_dict = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ConfigurationError(f"Error parsing YAML: {str(e)}", config_path)
        
        try:
            # Parse and validate with Pydantic
            return Config.model_validate(config_dict)
        except Exception as e:
            raise ConfigurationError(f"Invalid configuration: {str(e)}", config_path)
            
    except Exception as e:
        if not isinstance(e, ConfigurationError):
            raise ConfigurationError(f"Error loading configuration: {str(e)}", config_path)
        raise 