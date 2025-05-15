"""
Pytest fixtures for the adaptive trading system tests.
"""
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Generator, Tuple

import pytest
import yaml

from adaptive_trading_system.config.settings import Config, load_config


@pytest.fixture
def minimal_valid_config_dict() -> Dict[str, Any]:
    """Return a minimal valid configuration dictionary."""
    return {
        "data_source": {
            "symbols": ["RELIANCE.NS"],
            "start_date": "2022-01-01",
            "end_date": "2022-12-31"
        },
        "logging_level": "INFO"
    }


@pytest.fixture
def temp_config_file(minimal_valid_config_dict: Dict[str, Any]) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
    """Create a temporary config file with the given content and return its path.
    
    Returns:
        Tuple containing:
        - Path to the temporary config file
        - The configuration dictionary that was written to the file
    """
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w+", delete=False) as temp_file:
        yaml.dump(minimal_valid_config_dict, temp_file)
        temp_file.flush()
        path = temp_file.name
    
    try:
        yield path, minimal_valid_config_dict
    finally:
        # Clean up the temporary file
        if os.path.exists(path):
            os.unlink(path)


@pytest.fixture
def valid_config_instance(minimal_valid_config_dict: Dict[str, Any]) -> Config:
    """Return a valid Pydantic Config instance."""
    return Config.parse_obj(minimal_valid_config_dict) 