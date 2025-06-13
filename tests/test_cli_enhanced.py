"""
Minimal test file for CLI enhanced functionality that works with current architecture.

This file replaces test_cli_enhanced.py which was testing non-existent functions.
Following memory bank anti-pattern guidance for "Incomplete Refactoring".
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from typer.testing import CliRunner
from datetime import date

# Import current working components
from src.meqsap.cli import (
    app,
    _generate_error_message,
    _get_recovery_suggestions,
)
from src.meqsap.workflows.analysis import AnalysisWorkflow
from src.meqsap.config import load_yaml_config, validate_config, StrategyConfig
from src.meqsap.exceptions import (
    ConfigurationError, 
    DataAcquisitionError,
    BacktestExecutionError,
    ReportGenerationError
)

# Valid YAML content for testing
VALID_YAML_CONTENT = """
strategy_type: "MovingAverageCrossover"
ticker: "AAPL"
start_date: "2023-01-01"
end_date: "2023-12-31"
strategy_params:
  fast_ma: 10
  slow_ma: 20
"""

class TestConfigurationValidation:
    """Test configuration validation using current architecture."""

    def test_load_and_validate_config_success(self):
        """Test successful configuration loading using current workflow."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(VALID_YAML_CONTENT)
            config_path = Path(f.name)
        
        try:
            # Test using current architecture
            config_data = load_yaml_config(str(config_path))
            config = validate_config(config_data)
            
            assert config is not None
            assert hasattr(config, 'strategy_type')
            assert config.strategy_type == "MovingAverageCrossover"
        finally:
            os.unlink(config_path)

    def test_validate_config_file_not_found(self):
        """Test configuration validation with missing file."""
        config_path = "/nonexistent/config.yaml"
        
        with pytest.raises((FileNotFoundError, ConfigurationError)):
            load_yaml_config(config_path)

    def test_validate_config_invalid_yaml(self):
        """Test configuration validation with invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [unclosed")
            config_path = Path(f.name)
        
        try:
            with pytest.raises(Exception):  # Can be various YAML-related exceptions
                load_yaml_config(str(config_path))
        finally:
            os.unlink(config_path)


class TestWorkflowIntegration:
    """Test AnalysisWorkflow integration (current architecture)."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = Mock(spec=StrategyConfig)
        self.mock_config.strategy_type = "MovingAverageCrossover"
        self.mock_config.ticker = "AAPL"
        self.mock_config.start_date = date(2023, 1, 1)
        self.mock_config.end_date = date(2023, 12, 31)
        self.mock_config.get_baseline_config_with_defaults.return_value = None
        
        self.cli_flags = {
            'report': False,
            'report_html': False,
            'no_baseline': True
        }

    @patch('src.meqsap.workflows.analysis.fetch_market_data')
    @patch('src.meqsap.workflows.analysis.run_complete_backtest')
    def test_workflow_initialization(self, mock_backtest, mock_fetch):
        """Test that AnalysisWorkflow can be initialized."""
        workflow = AnalysisWorkflow(self.mock_config, self.cli_flags)
        
        assert workflow.config == self.mock_config
        assert workflow.cli_flags == self.cli_flags
        assert workflow.no_baseline is True


class TestErrorHandling:
    """Test enhanced error handling and recovery suggestions."""

    def test_generate_error_message_basic(self):
        """Test basic error message generation."""
        error = ConfigurationError("Invalid config")
        message = _generate_error_message(error, verbose=False, no_color=True)
        
        assert "ConfigurationError: Invalid config" in message
        assert "Suggested Solutions:" in message

    def test_generate_error_message_verbose(self):
        """Test verbose error message generation."""
        error = ConfigurationError("Invalid config")
        message = _generate_error_message(error, verbose=True, no_color=True)
        
        assert "ConfigurationError: Invalid config" in message
        assert "Debug Information:" in message

    def test_recovery_suggestions_configuration_error(self):
        """Test recovery suggestions for configuration errors."""
        error = ConfigurationError("Invalid config")
        suggestions = _get_recovery_suggestions(error)
        
        assert len(suggestions) > 0
        assert isinstance(suggestions, list)
        assert all(isinstance(s, str) for s in suggestions)

    def test_recovery_suggestions_data_error(self):
        """Test recovery suggestions for data errors."""
        error = DataAcquisitionError("Network timeout")
        suggestions = _get_recovery_suggestions(error)
        
        assert len(suggestions) > 0
        assert isinstance(suggestions, list)


class TestCLIStructure:
    """Test CLI application structure and commands."""
    
    def setup_method(self):
        self.runner = CliRunner()

    def test_app_exists(self):
        """Test that the main CLI app exists."""
        assert app is not None

    def test_commands_registered(self):
        """Test that commands are properly registered."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "analyze" in result.stdout
        assert "optimize" in result.stdout
