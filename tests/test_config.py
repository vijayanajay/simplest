"""
Tests for the configuration module.
"""

import os
import tempfile
from datetime import date
import warnings

import pytest
import yaml
from pydantic import ValidationError
from meqsap.config import BaselineConfig, StrategyConfig

from src.meqsap.config import (
    load_yaml_config,
    validate_config,
    StrategyFactory,
    StrategyConfig,
    MovingAverageCrossoverParams,
)
from src.meqsap.exceptions import ConfigurationError

# Suppress pandas_ta related warnings  
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API", category=UserWarning)


# Test fixtures
@pytest.fixture
def valid_config_data():
    """Return a valid configuration dictionary."""
    return {
        "ticker": "AAPL",
        "start_date": date(2020, 1, 1),
        "end_date": date(2021, 1, 1),
        "strategy_type": "MovingAverageCrossover",
        "strategy_params": {
            "fast_ma": 10,
            "slow_ma": 30,
        },
    }


@pytest.fixture
def valid_config_yaml(valid_config_data):
    """Create a temporary file with valid YAML configuration."""
    # Convert Python objects to serializable format
    yaml_data = valid_config_data.copy()
    yaml_data["start_date"] = yaml_data["start_date"].isoformat()
    yaml_data["end_date"] = yaml_data["end_date"].isoformat()
    
    with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".yaml") as temp:
        yaml.safe_dump(yaml_data, temp)
        temp_path = temp.name
    
    yield temp_path
    
    # Clean up the temporary file
    os.unlink(temp_path)


@pytest.fixture
def invalid_yaml():
    """Create a temporary file with invalid YAML."""
    with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".yaml") as temp:
        temp.write("this: is: invalid: yaml:")
        temp_path = temp.name
    
    yield temp_path
    
    # Clean up the temporary file
    os.unlink(temp_path)


@pytest.fixture
def empty_yaml():
    """Create a temporary empty YAML file."""
    with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".yaml") as temp:
        temp_path = temp.name
    
    yield temp_path
    
    # Clean up the temporary file
    os.unlink(temp_path)


# YAML Loading Tests
def test_load_yaml_valid(valid_config_yaml):
    """Test loading a valid YAML configuration file."""
    config = load_yaml_config(valid_config_yaml)
    assert isinstance(config, dict)
    assert config["ticker"] == "AAPL"
    assert "start_date" in config
    assert "end_date" in config
    assert config["strategy_type"] == "MovingAverageCrossover"
    assert "strategy_params" in config


def test_load_yaml_file_not_found():
    """Test handling of a non-existent YAML file."""
    with pytest.raises(ConfigurationError) as excinfo:
        load_yaml_config("non_existent_file.yaml")
    assert "not found" in str(excinfo.value)


def test_load_yaml_invalid(invalid_yaml):
    """Test handling of syntactically invalid YAML."""
    with pytest.raises(ConfigurationError) as excinfo:
        load_yaml_config(invalid_yaml)
    assert "Invalid YAML" in str(excinfo.value)


def test_load_yaml_empty(empty_yaml):
    """Test handling of an empty YAML file."""
    with pytest.raises(ConfigurationError) as excinfo:
        load_yaml_config(empty_yaml)
    assert "Empty configuration" in str(excinfo.value)


# Configuration Validation Tests
def test_validate_config_valid(valid_config_data):
    """Test validation of a valid configuration."""
    config = validate_config(valid_config_data)
    assert isinstance(config, StrategyConfig)
    assert config.ticker == "AAPL"
    assert config.start_date == date(2020, 1, 1)
    assert config.end_date == date(2021, 1, 1)
    assert config.strategy_type == "MovingAverageCrossover"


def test_validate_config_missing_fields():
    """Test validation when required fields are missing."""
    incomplete_data = {
        "ticker": "AAPL",
        # Missing start_date
        "end_date": date(2021, 1, 1),
        "strategy_type": "MovingAverageCrossover",
        "strategy_params": {
            "fast_ma": 10,
            "slow_ma": 30,
        },
    }
    
    with pytest.raises(ConfigurationError) as excinfo:
        validate_config(incomplete_data)
    assert "validation failed" in str(excinfo.value)


def test_validate_ticker_format():
    """Test ticker format validation."""
    # Test with invalid ticker format
    invalid_data = {
        "ticker": "AAPL@123",  # Invalid character
        "start_date": date(2020, 1, 1),
        "end_date": date(2021, 1, 1),
        "strategy_type": "MovingAverageCrossover",
        "strategy_params": {
            "fast_ma": 10,
            "slow_ma": 30,
        },
    }
    
    with pytest.raises(ConfigurationError) as excinfo:
        validate_config(invalid_data)
    assert "ticker must contain only" in str(excinfo.value)


def test_validate_dates():
    """Test date validation."""
    # Test with end_date before start_date
    invalid_dates = {
        "ticker": "AAPL",
        "start_date": date(2021, 1, 1),
        "end_date": date(2020, 1, 1),  # End date is before start date
        "strategy_type": "MovingAverageCrossover",
        "strategy_params": {
            "fast_ma": 10,
            "slow_ma": 30,
        },
    }
    
    with pytest.raises(ConfigurationError) as excinfo:
        validate_config(invalid_dates)
    assert "end_date must be after start_date" in str(excinfo.value)


# Strategy Factory Tests
def test_strategy_factory_valid():
    """Test the strategy factory with valid parameters."""
    params = StrategyFactory.create_strategy_validator(
        "MovingAverageCrossover", {"fast_ma": 10, "slow_ma": 30}
    )
    assert isinstance(params, MovingAverageCrossoverParams)
    assert params.fast_ma == 10
    assert params.slow_ma == 30


def test_strategy_factory_unknown_type():
    """Test the strategy factory with an unknown strategy type."""
    with pytest.raises(ConfigurationError) as excinfo:  # Changed from ValueError
        StrategyFactory.create_strategy_validator(
            "UnknownStrategy", {"param1": "value1"}
        )
    assert "Unknown strategy type" in str(excinfo.value)


def test_strategy_factory_invalid_params():
    """Test the strategy factory with invalid parameters."""
    with pytest.raises(ConfigurationError) as excinfo:  # Changed from ValueError
        StrategyFactory.create_strategy_validator(
            "MovingAverageCrossover", {"fast_ma": 30, "slow_ma": 10}  # Invalid: fast > slow
        )
    assert "slow_ma must be greater than fast_ma" in str(excinfo.value)


def test_validate_strategy_params(valid_config_data):
    """Test the validation of strategy-specific parameters."""
    config = StrategyConfig(**valid_config_data)
    params = config.validate_strategy_params()
    assert isinstance(params, MovingAverageCrossoverParams)
    assert params.fast_ma == 10
    assert params.slow_ma == 30


def test_moving_average_crossover_params_positive_periods():
    """Test that MA periods must be positive when fixed numeric values."""
    # Valid
    MovingAverageCrossoverParams(fast_ma=10, slow_ma=20)
    MovingAverageCrossoverParams(fast_ma={"type": "value", "value": 10}, slow_ma={"type": "value", "value": 20})

    # Invalid fast_ma
    with pytest.raises(ConfigurationError, match="fast_ma must be positive"):
        validate_config({
            "ticker": "AAPL", "start_date": date(2020,1,1), "end_date": date(2021,1,1),
            "strategy_type": "MovingAverageCrossover",
            "strategy_params": {"fast_ma": 0, "slow_ma": 20}
        })
    with pytest.raises(ConfigurationError, match="fast_ma must be positive"):
        validate_config({
            "ticker": "AAPL", "start_date": date(2020,1,1), "end_date": date(2021,1,1),
            "strategy_type": "MovingAverageCrossover",
            "strategy_params": {"fast_ma": {"type": "value", "value": -5}, "slow_ma": 20}
        })

    # Invalid slow_ma
    with pytest.raises(ConfigurationError, match="slow_ma must be positive"):
        validate_config({
            "ticker": "AAPL", "start_date": date(2020,1,1), "end_date": date(2021,1,1),
            "strategy_type": "MovingAverageCrossover",
            "strategy_params": {"fast_ma": 10, "slow_ma": -5}
        })


class TestMovingAverageCrossoverParamsCoverage:
    def test_get_required_data_coverage_bars_fixed_values(self):
        params = MovingAverageCrossoverParams(fast_ma=10, slow_ma=50)
        assert params.get_required_data_coverage_bars() == 50

    def test_get_required_data_coverage_bars_range_type(self):
        params = MovingAverageCrossoverParams(
            fast_ma={"type": "range", "start": 5, "stop": 15, "step": 1},
            slow_ma={"type": "range", "start": 20, "stop": 60, "step": 5} # Max slow_ma is 60
        )
        assert params.get_required_data_coverage_bars() == 60

    def test_get_required_data_coverage_bars_choices_type(self):
        params = MovingAverageCrossoverParams(
            fast_ma={"type": "choices", "values": [8, 10, 12]},
            slow_ma={"type": "choices", "values": [25, 30, 70]} # Max slow_ma is 70
        )
        assert params.get_required_data_coverage_bars() == 70

    def test_get_required_data_coverage_bars_value_type(self):
        params = MovingAverageCrossoverParams(
            fast_ma={"type": "value", "value": 7},
            slow_ma={"type": "value", "value": 23} # Max slow_ma is 23
        )
        assert params.get_required_data_coverage_bars() == 23

    def test_get_required_data_coverage_bars_mixed_types(self):
        params = MovingAverageCrossoverParams(
            fast_ma=5, # Fixed primitive
            slow_ma={"type": "range", "start": 15, "stop": 35, "step": 1} # Max slow_ma is 35
        )
        assert params.get_required_data_coverage_bars() == 35

    def test_get_required_data_coverage_bars_error_non_numeric_choice(self):
        with pytest.raises(ConfigurationError, match="Non-numeric value found in choices"):
            params = MovingAverageCrossoverParams(
                fast_ma=5,
                slow_ma={"type": "choices", "values": [20, "thirty", 40]}
            )
            # The error is raised when get_required_data_coverage_bars calls _get_parameter_maximum
            params.get_required_data_coverage_bars()

class TestBaselineConfig:
    """Test baseline configuration functionality."""
    
    def test_baseline_config_defaults(self):
        """Test default baseline configuration."""
        config = BaselineConfig()
        assert config.active is True
        assert config.strategy_type == "BuyAndHold"
        assert config.params is None
    
    def test_baseline_config_buy_and_hold(self):
        """Test Buy & Hold baseline configuration."""
        config = BaselineConfig(
            active=True,
            strategy_type="BuyAndHold"
        )
        assert config.strategy_type == "BuyAndHold"
        assert config.params is None
    
    def test_baseline_config_ma_crossover_valid(self):
        """Test valid MovingAverageCrossover baseline configuration."""
        config = BaselineConfig(
            strategy_type="MovingAverageCrossover",
            params={"fast_ma": 20, "slow_ma": 50}
        )
        assert config.strategy_type == "MovingAverageCrossover"
        assert config.params["fast_ma"] == 20
        assert config.params["slow_ma"] == 50
    
    def test_baseline_config_ma_crossover_missing_params(self):
        """Test MovingAverageCrossover without required parameters."""
        with pytest.raises(ValueError, match="requires 'params' with 'fast_ma' and 'slow_ma'"):
            BaselineConfig(
                strategy_type="MovingAverageCrossover"
            )
    
    def test_baseline_config_ma_crossover_invalid_params(self):
        """Test MovingAverageCrossover with invalid parameters."""
        with pytest.raises(ValueError, match="'fast_ma' must be less than 'slow_ma'"):
            BaselineConfig(
                strategy_type="MovingAverageCrossover",
                params={"fast_ma": 50, "slow_ma": 20}
            )
    
    def test_baseline_config_buy_and_hold_with_params(self):
        """Test Buy & Hold with parameters (should fail)."""
        with pytest.raises(ValueError, match="BuyAndHold baseline does not accept parameters"):
            BaselineConfig(
                strategy_type="BuyAndHold",
                params={"some_param": "value"}
            )
    
    def test_baseline_config_invalid_strategy_type(self):
        """Test invalid strategy type."""
        with pytest.raises(ValidationError, match="Input should be 'BuyAndHold' or 'MovingAverageCrossover'"):
            BaselineConfig(strategy_type="InvalidStrategy")

class TestStrategyConfigWithBaseline:
    """Test StrategyConfig integration with baseline functionality."""
    
    def test_strategy_config_with_baseline(self):
        """Test StrategyConfig with baseline configuration."""
        config = StrategyConfig(
            ticker="AAPL",
            start_date="2023-01-01",
            end_date="2023-12-31",
            strategy_type="MovingAverageCrossover",
            strategy_params={"fast_ma": 10, "slow_ma": 30},
            baseline_config={}
        )
        assert config.baseline_config is not None
        assert config.baseline_config.strategy_type == "BuyAndHold"
    
    def test_get_baseline_config_with_defaults_no_baseline_flag(self):
        """Test baseline config with no_baseline flag."""
        config = StrategyConfig(
            ticker="AAPL",
            start_date="2023-01-01", 
            end_date="2023-12-31",
            strategy_type="MovingAverageCrossover",
            strategy_params={"fast_ma": 10, "slow_ma": 30}
        )
        
        # With no_baseline=True, should return None
        baseline_config = config.get_baseline_config_with_defaults(no_baseline=True)
        assert baseline_config is None
        
        # With no_baseline=False, should inject default
        baseline_config = config.get_baseline_config_with_defaults(no_baseline=False)
        assert baseline_config is not None
        assert baseline_config.strategy_type == "BuyAndHold"
