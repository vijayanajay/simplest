"""Graceful interruption handling for optimization processes."""

import signal
import threading
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class OptimizationInterruptHandler:
    """Context manager for graceful optimization interruption handling."""
    
    def __init__(self):
        """Initialize the interrupt handler."""
        self.interrupted = threading.Event()
        self._original_handler: Optional[signal.Handlers] = None
        
    def __enter__(self):
        """Enter context manager and register signal handler."""
        logger.debug("Setting up optimization interrupt handler")
        self._original_handler = signal.signal(signal.SIGINT, self._signal_handler)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and restore original signal handler."""
        logger.debug("Restoring original signal handler")
        if self._original_handler is not None:
            signal.signal(signal.SIGINT, self._original_handler)
            
    def _signal_handler(self, signum, frame):
        """Handle interrupt signal (SIGINT/Ctrl+C).
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info("Optimization interruption requested (Ctrl+C)")
        self.interrupted.set()
        
    def check_interrupted(self) -> bool:
        """Check if interruption has been requested.
        
        Returns:
            True if interruption requested, False otherwise
        """
        return self.interrupted.is_set()
        
    def wait_for_interruption(self, timeout: Optional[float] = None) -> bool:
        """Wait for interruption signal.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if interrupted within timeout, False otherwise
        """
        return self.interrupted.wait(timeout)