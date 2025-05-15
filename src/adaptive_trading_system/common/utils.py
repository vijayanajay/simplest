"""
General utility functions for the adaptive trading system.
"""
import os
import uuid
import logging
from typing import Any, Dict, Optional


def generate_run_id() -> str:
    """Generate a unique run ID.
    
    Returns:
        str: A unique identifier for a system run.
    """
    return str(uuid.uuid4())


def setup_logging(
    level: str = "INFO",
    log_to_file: bool = True,
    log_file_path: Optional[str] = None,
    run_id: Optional[str] = None
) -> logging.Logger:
    """Setup structured logging for the application.
    
    Args:
        level: Logging level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to a file in addition to console
        log_file_path: Path to the log file. If None, a default path will be used
        run_id: Optional run ID to include in log context
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create a JSON-like formatter for structured logging
    log_format = '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
    if run_id:
        log_format = f'%(asctime)s [%(levelname)s] [run_id={run_id}] %(name)s:%(lineno)d - %(message)s'
    
    # Basic configuration for root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get logger for this application
    logger = logging.getLogger('adaptive_trading_system')
    
    # Add file handler if requested
    if log_to_file:
        if not log_file_path:
            # Create logs directory if it doesn't exist
            os.makedirs('logs', exist_ok=True)
            log_file_path = f'logs/app_{run_id or "main"}.log'
            
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
    
    return logger


def log_config(config: Dict[str, Any], logger: logging.Logger) -> None:
    """Log the effective configuration used for a run.
    
    Args:
        config: The configuration dictionary
        logger: Logger instance to use
    """
    logger.info(f"Using configuration: {config}") 