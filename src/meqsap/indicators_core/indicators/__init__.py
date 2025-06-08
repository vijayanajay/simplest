"""
MEQSAP Indicators Collection.

Import all indicator modules to ensure they register themselves.
"""
# Import all indicator modules to trigger registration
from . import moving_average
from . import rsi

# Export the specific indicator classes for convenience
from .moving_average import SimpleMovingAverageIndicator
from .rsi import RSIIndicator

__all__ = [
    "SimpleMovingAverageIndicator",
    "RSIIndicator",
]