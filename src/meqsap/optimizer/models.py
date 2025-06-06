"""Data models for optimization progress tracking and results."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Any, List
from pydantic import BaseModel, Field


class TrialFailureType(Enum):
    """Enumeration of trial failure types for error classification."""
    DATA_ERROR = "Data Error"
    CALCULATION_ERROR = "Calculation Error"
    VALIDATION_ERROR = "Validation Error"
    UNKNOWN_ERROR = "Unknown Error"


@dataclass
class ProgressData:
    """Progress data for real-time optimization updates."""
    current_trial: int
    total_trials: Optional[int]
    best_score: Optional[float]
    elapsed_seconds: float
    failed_trials_summary: Dict[str, int]  # e.g., {"Data Error": 2, ...}
    current_params: Dict[str, Any]


@dataclass
class ErrorSummary:
    """Summary of optimization errors and failures."""
    total_failed_trials: int
    failure_counts_by_type: Dict[str, int]


class OptimizationResult(BaseModel):
    """Enhanced optimization result with error tracking and timing info."""
    
    # Core optimization results
    best_params: Optional[Dict[str, Any]] = Field(None, description="Best parameter set found")
    best_score: Optional[float] = Field(None, description="Best objective score achieved")
    
    # Trial statistics
    total_trials: int = Field(..., description="Total trials executed")
    successful_trials: int = Field(..., description="Number of successful trials")
    
    # Error tracking
    error_summary: ErrorSummary = Field(..., description="Summary of trial failures")
    
    # Timing information
    timing_info: Dict[str, float] = Field(default_factory=dict, description="Timing statistics")
    
    # Interruption status
    was_interrupted: bool = Field(False, description="Whether optimization was interrupted")
    
    # Best strategy analysis (optional, populated if available)
    best_strategy_analysis: Optional[Dict[str, Any]] = Field(None, description="Full analysis of best strategy, as a dict")
    
    # Constraint adherence metrics
    constraint_adherence: Optional[Dict[str, Any]] = Field(None, description="Constraint adherence metrics")
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True