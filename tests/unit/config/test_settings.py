"""
Unit tests for the configuration settings module.
"""
import os
import tempfile
from pathlib import Path
import pytest
from pydantic import ValidationError

from adaptive_trading_system.config.settings import (
    load_config, Config, DataSourceConfig, FeatureConfig,
    GeneticAlgorithmConfig, BacktestConfig, ReportingConfig
)
from adaptive_trading_system.common.exceptions import ConfigurationError


class TestConfigModels:
    """Tests for the configuration Pydantic models."""
    
    def test_data_source_config_valid(self):
        """Test that a valid DataSourceConfig validates correctly."""
        config = DataSourceConfig(
            symbols=["RELIANCE.NS"],
            start_date="2022-01-01",
            end_date="2022-12-31"
        )
        
        assert config.provider == "yfinance"
        assert config.symbols == ["RELIANCE.NS"]
        assert config.start_date == "2022-01-01"
        assert config.end_date == "2022-12-31"
        assert config.interval == "1d"
    
    def test_data_source_config_invalid_dates(self):
        """Test that invalid date format raises validation error."""
        with pytest.raises(ValidationError):
            DataSourceConfig(
                symbols=["RELIANCE.NS"],
                start_date="01/01/2022",  # Invalid format
                end_date="2022-12-31"
            )
    
    def test_data_source_config_end_before_start(self):
        """Test that end date before start date raises validation error."""
        with pytest.raises(ValidationError) as excinfo:
            DataSourceConfig(
                symbols=["RELIANCE.NS"],
                start_date="2022-12-31",
                end_date="2022-01-01"  # Earlier than start_date
            )
        assert "start_date must be earlier than end_date" in str(excinfo.value)
    
    def test_feature_config_defaults(self):
        """Test that FeatureConfig has correct defaults."""
        config = FeatureConfig()
        
        assert 20 in config.sma_periods
        assert 50 in config.sma_periods
        assert 200 in config.sma_periods
        assert 12 in config.ema_periods
        assert 26 in config.ema_periods
        assert 14 in config.rsi_periods
        assert config.macd_parameters["fast"] == 12
        assert config.macd_parameters["slow"] == 26
        assert config.macd_parameters["signal"] == 9
        assert config.bollinger_bands_parameters["period"] == 20
        assert config.bollinger_bands_parameters["std_dev"] == 2.0
        assert config.custom_feature_scripts == []
    
    def test_feature_config_invalid_periods(self):
        """Test that negative periods raise validation error."""
        with pytest.raises(ValidationError) as excinfo:
            FeatureConfig(sma_periods=[-10, 20, 50])
        assert "Period must be positive" in str(excinfo.value)
    
    def test_genetic_algorithm_config_validation(self):
        """Test validation of GA config parameters."""
        # Test valid config
        valid_config = GeneticAlgorithmConfig(
            population_size=50,
            generations=20,
            mutation_rate=0.2,
            crossover_rate=0.8,
            min_profitable_symbols=2
        )
        assert valid_config.population_size == 50
        assert valid_config.mutation_rate == 0.2
        
        # Test invalid mutation_rate
        with pytest.raises(ValidationError):
            GeneticAlgorithmConfig(mutation_rate=1.5)  # Greater than 1.0
    
    def test_backtest_config_validation(self):
        """Test validation of backtest config parameters."""
        # Test valid config
        valid_config = BacktestConfig(
            initial_capital=50000.0,
            commission_percent=0.002
        )
        assert valid_config.initial_capital == 50000.0
        assert valid_config.commission_percent == 0.002
        
        # Test invalid initial capital
        with pytest.raises(ValidationError):
            BacktestConfig(initial_capital=-1000)  # Negative capital
    
    def test_reporting_config_validation(self):
        """Test validation of reporting config parameters."""
        # Test valid config
        valid_config = ReportingConfig(
            top_n_strategies=3,
            report_formats=["html", "csv"]
        )
        assert valid_config.top_n_strategies == 3
        assert "html" in valid_config.report_formats
        assert "csv" in valid_config.report_formats
        
        # Test invalid top_n_strategies
        with pytest.raises(ValidationError):
            ReportingConfig(top_n_strategies=0)  # Must be >= 1
    
    def test_main_config_run_id_generation(self):
        """Test that run_id is auto-generated if not provided."""
        config = Config(
            data_source=DataSourceConfig(
                symbols=["RELIANCE.NS"],
                start_date="2022-01-01",
                end_date="2022-12-31"
            )
        )
        assert config.run_id is not None
        assert len(config.run_id) > 0
    
    def test_main_config_logging_level_validation(self):
        """Test validation of logging level."""
        # Test valid logging level
        config = Config(
            data_source=DataSourceConfig(
                symbols=["RELIANCE.NS"],
                start_date="2022-01-01",
                end_date="2022-12-31"
            ),
            logging_level="debug"
        )
        assert config.logging_level == "DEBUG"  # Should be uppercase
        
        # Test invalid logging level
        with pytest.raises(ValidationError) as excinfo:
            Config(
                data_source=DataSourceConfig(
                    symbols=["RELIANCE.NS"],
                    start_date="2022-01-01",
                    end_date="2022-12-31"
                ),
                logging_level="TRACE"  # Invalid level
            )
        assert "Invalid logging level" in str(excinfo.value)


class TestConfigLoading:
    """Tests for loading configuration from files."""
    
    def test_load_config_file_not_found(self):
        """Test that loading a non-existent file raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as excinfo:
            load_config("non_existent_file.yaml")
        assert "not found" in str(excinfo.value)
    
    def test_load_config_invalid_yaml(self):
        """Test that loading invalid YAML raises ConfigurationError."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w+") as temp_file:
            # Write invalid YAML content
            temp_file.write("invalid: yaml: content: [")
            temp_file.flush()
            
            with pytest.raises(ConfigurationError) as excinfo:
                load_config(temp_file.name)
            assert "Error parsing YAML" in str(excinfo.value)
    
    def test_load_config_missing_required_field(self):
        """Test that missing required fields raise ConfigurationError."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w+") as temp_file:
            # Write config without required data_source field
            temp_file.write("logging_level: INFO")
            temp_file.flush()
            
            with pytest.raises(ConfigurationError) as excinfo:
                load_config(temp_file.name)
            assert "Invalid configuration" in str(excinfo.value)
    
    def test_load_config_valid(self):
        """Test loading a valid configuration file."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w+") as temp_file:
            # Write minimal valid config
            temp_file.write("""
data_source:
  symbols:
    - RELIANCE.NS
  start_date: 2022-01-01
  end_date: 2022-12-31
logging_level: INFO
""")
            temp_file.flush()
            
            config = load_config(temp_file.name)
            
            assert isinstance(config, Config)
            assert config.data_source.symbols == ["RELIANCE.NS"]
            assert config.data_source.start_date == "2022-01-01"
            assert config.data_source.end_date == "2022-12-31"
            assert config.logging_level == "INFO"
            assert config.run_id is not None 