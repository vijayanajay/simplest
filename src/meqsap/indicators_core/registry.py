"""
Indicator Registry for discovering and accessing available indicators.
"""
from typing import Dict, Type, Optional, List
from .base import IndicatorBase


class IndicatorRegistry:
    """Manages registration and retrieval of indicator classes."""

    def __init__(self):
        self._indicators: Dict[str, Type[IndicatorBase]] = {}

    def register(self, name: str, indicator_class: Type[IndicatorBase]):
        """Registers an indicator class."""
        if not issubclass(indicator_class, IndicatorBase):
            raise TypeError("Registered class must be a subclass of IndicatorBase.")
        if name in self._indicators:
            raise ValueError(f"Indicator '{name}' is already registered.")
        self._indicators[name] = indicator_class

    def get(self, name: str) -> Optional[Type[IndicatorBase]]:
        """Retrieves an indicator class by name."""
        return self._indicators.get(name)

    def list_available(self) -> List[str]:
        """Lists all registered indicator names."""
        return list(self._indicators.keys())

# Global registry instance
_indicator_registry = IndicatorRegistry()

def get_indicator_registry() -> IndicatorRegistry:
    """Returns the global indicator registry instance."""
    return _indicator_registry
