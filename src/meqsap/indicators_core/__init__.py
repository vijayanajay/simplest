"""
MEQSAP Indicators Core Library.

This package provides the foundational components for defining, managing,
and calculating technical indicators within the MEQSAP ecosystem.
"""
from .base import IndicatorBase, ParameterDefinition, ParameterSpace
from .parameters import ParameterRange, ParameterChoices, ParameterValue, ParameterDefinitionType
from .registry import IndicatorRegistry, get_indicator_registry

# Import indicators to ensure they register themselves
from . import indicators

__all__ = [
    "IndicatorBase",
    "ParameterDefinition",
    "ParameterSpace",
    "ParameterRange",
    "ParameterChoices",
    "ParameterValue",
    "ParameterDefinitionType",
    "IndicatorRegistry",
    "get_indicator_registry",
]
