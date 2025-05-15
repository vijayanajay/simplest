"""
Main application entry point for the adaptive trading system.
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from adaptive_trading_system.config.settings import Config


def run_discovery_pipeline(config: Config, logger: logging.Logger) -> Dict[str, Any]:
    """
    Run the main trading strategy discovery pipeline.
    
    Args:
        config: Validated configuration object
        logger: Logger instance
        
    Returns:
        Dict[str, Any]: Results and metrics from the discovery process
    """
    # Create required directories if they don't exist
    _ensure_directories(config, logger)
    
    # In a full implementation, this would call the various pipeline components:
    # 1. Data fetching
    # 2. Feature engineering
    # 3. Genetic algorithm for strategy discovery
    # 4. Backtesting
    # 5. Analysis
    # 6. Reporting
    
    # For this MVP implementation, we just return a placeholder result
    # showing that the pipeline executed successfully
    logger.info("Discovery pipeline completed")
    return {
        "run_id": config.run_id,
        "status": "completed",
        "message": "Pipeline executed successfully"
    }


def _ensure_directories(config: Config, logger: logging.Logger) -> None:
    """
    Ensure all required directories exist.
    
    Args:
        config: Validated configuration object
        logger: Logger instance
    """
    # Extract directory paths from config
    dirs_to_create = [
        # Reports directory
        Path(config.reporting.output_directory),
        
        # State directory for GA checkpoints
        Path(os.path.dirname(config.genetic_algorithm.checkpoint_path_template.format(generation=0))),
        
        # Directory for GA evolution logs
        Path(os.path.dirname(config.genetic_algorithm.evolution_log_path)),
        
        # Create data/cache directory for market data
        Path("data/cache"),
    ]
    
    # Create each directory if it doesn't exist
    for directory in dirs_to_create:
        if not directory.exists():
            logger.debug(f"Creating directory: {directory}")
            directory.mkdir(parents=True, exist_ok=True) 