"""Optimization configuration models for parameter optimization engine."""

from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field, validator


class ObjectiveParams(BaseModel):
    """Configuration for objective function parameters."""
    
    target_hold_period_days: Optional[List[int]] = Field(
        None, 
        description="Min and max holding period in days [min, max]",
        min_items=2,
        max_items=2
    )
    
    min_trades: Optional[int] = Field(
        50, 
        description="Minimum number of trades required",
        ge=1
    )
    
    risk_free_rate: Optional[float] = Field(
        0.02, 
        description="Risk-free rate for Sharpe ratio calculation",
        ge=0.0
    )

    @validator('target_hold_period_days')
    def validate_hold_period_range(cls, v):
        if v is not None and len(v) == 2:
            if v[0] >= v[1]:
                raise ValueError("Min holding period must be less than max holding period")
            if v[0] < 1:
                raise ValueError("Min holding period must be at least 1 day")
        return v


class AlgorithmParams(BaseModel):
    """Configuration for optimization algorithm parameters."""
    
    max_iterations: Optional[int] = Field(
        100, 
        description="Maximum iterations for random search",
        ge=1
    )
    
    progress_update_frequency: Optional[int] = Field(
        10, 
        description="Progress update frequency (every N evaluations)",
        ge=1
    )
    
    random_seed: Optional[int] = Field(
        None, 
        description="Random seed for reproducible results"
    )


class ErrorHandlingConfig(BaseModel):
    """Configuration for error handling during optimization."""
    
    max_failures: int = Field(
        10, 
        description="Maximum optimization failures before stopping",
        ge=1
    )
    
    continue_on_constraint_violation: bool = Field(
        True, 
        description="Continue optimization when constraints are violated"
    )
    
    timeout_seconds: Optional[int] = Field(
        None, 
        description="Maximum optimization time in seconds",
        ge=1
    )


class OptimizationConfig(BaseModel):
    """Complete optimization configuration."""
    
    algorithm: Literal["grid_search", "random_search"] = Field(
        "grid_search",
        description="Optimization algorithm to use"
    )
    
    objective_function: Literal["sharpe_ratio", "sharpe_with_hold_period_constraint"] = Field(
        "sharpe_ratio",
        description="Objective function for optimization"
    )
    
    objective_params: ObjectiveParams = Field(
        default_factory=ObjectiveParams,
        description="Parameters for objective function"
    )
    
    algorithm_params: AlgorithmParams = Field(
        default_factory=AlgorithmParams,
        description="Parameters for optimization algorithm"
    )
    
    error_handling: ErrorHandlingConfig = Field(
        default_factory=ErrorHandlingConfig,
        description="Error handling configuration"
    )

    class Config:
        extra = "forbid"
        validate_assignment = True
