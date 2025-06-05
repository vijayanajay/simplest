"""Optimization results container and analysis functionality."""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
import numpy as np
from pathlib import Path

from ..backtest import BacktestResult


@dataclass
class ParameterEvaluation:
    """Single parameter set evaluation result."""
    parameters: Dict[str, Any]
    objective_value: float
    backtest_result: BacktestResult
    constraint_adherence: Dict[str, Any]
    evaluation_time: float
    error: Optional[str] = None
    
    def __post_init__(self):
        """Validate evaluation result."""
        if self.error is None and self.backtest_result is None:
            raise ValueError("Either backtest_result or error must be provided")


@dataclass
class ConstraintAdherenceMetrics:
    """Detailed constraint adherence metrics."""
    hold_period_stats: Dict[str, float] = field(default_factory=dict)
    constraint_violations: List[str] = field(default_factory=list)
    adherence_score: float = 0.0
    
    def __post_init__(self):
        """Initialize default metrics."""
        if not self.hold_period_stats:
            self.hold_period_stats = {
                'avg_hold_days': 0.0,
                'median_hold_days': 0.0,
                'pct_within_target': 0.0,
                'min_hold_days': 0.0,
                'max_hold_days': 0.0
            }


@dataclass
class OptimizationProgress:
    """Optimization progress tracking."""
    total_evaluations: int
    completed_evaluations: int
    failed_evaluations: int
    best_objective_value: float
    best_parameters: Dict[str, Any]
    start_time: datetime
    estimated_completion: Optional[datetime] = None
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_evaluations == 0:
            return 0.0
        return (self.completed_evaluations / self.total_evaluations) * 100
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total_attempts = self.completed_evaluations + self.failed_evaluations
        if total_attempts == 0:
            return 0.0
        return (self.completed_evaluations / total_attempts) * 100


class OptimizationResult:
    """
    Comprehensive optimization results container with analysis capabilities.
    """
    
    def __init__(
        self,
        algorithm: str,
        objective_function: str,
        parameter_space_size: int,
        optimization_config: Dict[str, Any]
    ):
        """
        Initialize optimization result container.
        
        Args:
            algorithm: Optimization algorithm used
            objective_function: Objective function used
            parameter_space_size: Total size of parameter space
            optimization_config: Configuration used for optimization
        """
        self.algorithm = algorithm
        self.objective_function = objective_function
        self.parameter_space_size = parameter_space_size
        self.optimization_config = optimization_config
        
        self.evaluations: List[ParameterEvaluation] = []
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.total_evaluation_time = 0.0
        
        # Results tracking
        self._best_evaluation: Optional[ParameterEvaluation] = None
        self._constraint_adherence_summary: Optional[ConstraintAdherenceMetrics] = None
    
    def add_evaluation(self, evaluation: ParameterEvaluation) -> None:
        """Add a parameter evaluation result."""
        self.evaluations.append(evaluation)
        self.total_evaluation_time += evaluation.evaluation_time
        
        # Update best evaluation
        if evaluation.error is None:
            if self._best_evaluation is None or evaluation.objective_value > self._best_evaluation.objective_value:
                self._best_evaluation = evaluation
    
    def finalize(self) -> None:
        """Finalize optimization results and calculate summary statistics."""
        self.end_time = datetime.now()
        self._calculate_constraint_adherence_summary()
    
    def _calculate_constraint_adherence_summary(self) -> None:
        """Calculate overall constraint adherence metrics."""
        if not self.evaluations:
            self._constraint_adherence_summary = ConstraintAdherenceMetrics()
            return
        
        # Aggregate constraint adherence across all evaluations
        valid_evaluations = [e for e in self.evaluations if e.error is None]
        
        if not valid_evaluations:
            self._constraint_adherence_summary = ConstraintAdherenceMetrics()
            return
        
        # Calculate hold period statistics
        hold_period_stats = {}
        all_violations = []
        adherence_scores = []
        
        for eval_result in valid_evaluations:
            if eval_result.constraint_adherence:
                hold_stats = eval_result.constraint_adherence.get('hold_period_stats', {})
                for key, value in hold_stats.items():
                    if key not in hold_period_stats:
                        hold_period_stats[key] = []
                    hold_period_stats[key].append(value)
                
                violations = eval_result.constraint_adherence.get('violations', [])
                all_violations.extend(violations)
                
                adherence_score = eval_result.constraint_adherence.get('adherence_score', 0.0)
                adherence_scores.append(adherence_score)
        
        # Calculate summary statistics
        summary_stats = {}
        for key, values in hold_period_stats.items():
            if values:
                summary_stats[f'avg_{key}'] = np.mean(values)
                summary_stats[f'std_{key}'] = np.std(values)
                summary_stats[f'min_{key}'] = np.min(values)
                summary_stats[f'max_{key}'] = np.max(values)
        
        # Count unique violations
        unique_violations = list(set(all_violations))
        
        # Calculate overall adherence score
        overall_adherence = np.mean(adherence_scores) if adherence_scores else 0.0
        
        self._constraint_adherence_summary = ConstraintAdherenceMetrics(
            hold_period_stats=summary_stats,
            constraint_violations=unique_violations,
            adherence_score=overall_adherence
        )
    
    @property
    def best_parameters(self) -> Optional[Dict[str, Any]]:
        """Get best parameter set found."""
        return self._best_evaluation.parameters if self._best_evaluation else None
    
    @property
    def best_objective_value(self) -> Optional[float]:
        """Get best objective value found."""
        return self._best_evaluation.objective_value if self._best_evaluation else None
    
    @property
    def best_backtest_result(self) -> Optional[BacktestResult]:
        """Get backtest result for best parameters."""
        return self._best_evaluation.backtest_result if self._best_evaluation else None
    
    @property
    def constraint_adherence_summary(self) -> ConstraintAdherenceMetrics:
        """Get constraint adherence summary."""
        return self._constraint_adherence_summary or ConstraintAdherenceMetrics()
    
    @property
    def success_rate(self) -> float:
        """Calculate optimization success rate."""
        if not self.evaluations:
            return 0.0
        successful = len([e for e in self.evaluations if e.error is None])
        return (successful / len(self.evaluations)) * 100
    
    @property
    def total_runtime(self) -> float:
        """Get total optimization runtime in seconds."""
        if self.end_time is None:
            return (datetime.now() - self.start_time).total_seconds()
        return (self.end_time - self.start_time).total_seconds()
    
    def get_parameter_sensitivity_analysis(self) -> pd.DataFrame:
        """
        Analyze parameter sensitivity across evaluations.
        
        Returns:
            DataFrame with parameter sensitivity statistics
        """
        if not self.evaluations:
            return pd.DataFrame()
        
        # Extract successful evaluations
        successful_evals = [e for e in self.evaluations if e.error is None]
        
        if len(successful_evals) < 2:
            return pd.DataFrame()
        
        # Create DataFrame from parameter sets and objective values
        data = []
        for eval_result in successful_evals:
            row = eval_result.parameters.copy()
            row['objective_value'] = eval_result.objective_value
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Calculate sensitivity metrics
        sensitivity_stats = []
        param_cols = [col for col in df.columns if col != 'objective_value']
        
        for param in param_cols:
            try:
                correlation = df[param].corr(df['objective_value'])
                param_stats = {
                    'parameter': param,
                    'correlation_with_objective': correlation,
                    'mean_value': df[param].mean(),
                    'std_value': df[param].std(),
                    'min_value': df[param].min(),
                    'max_value': df[param].max(),
                    'unique_values': df[param].nunique()
                }
                sensitivity_stats.append(param_stats)
            except Exception:
                # Handle non-numeric parameters
                param_stats = {
                    'parameter': param,
                    'correlation_with_objective': np.nan,
                    'mean_value': np.nan,
                    'std_value': np.nan,
                    'min_value': str(df[param].min()),
                    'max_value': str(df[param].max()),
                    'unique_values': df[param].nunique()
                }
                sensitivity_stats.append(param_stats)
        
        return pd.DataFrame(sensitivity_stats)
    
    def get_top_results(self, n: int = 10) -> List[ParameterEvaluation]:
        """
        Get top N results by objective value.
        
        Args:
            n: Number of top results to return
            
        Returns:
            List of top parameter evaluations
        """
        successful_evals = [e for e in self.evaluations if e.error is None]
        return sorted(successful_evals, key=lambda x: x.objective_value, reverse=True)[:n]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert optimization result to dictionary for serialization."""
        return {
            'algorithm': self.algorithm,
            'objective_function': self.objective_function,
            'parameter_space_size': self.parameter_space_size,
            'optimization_config': self.optimization_config,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_evaluation_time': self.total_evaluation_time,
            'total_runtime': self.total_runtime,
            'num_evaluations': len(self.evaluations),
            'success_rate': self.success_rate,
            'best_parameters': self.best_parameters,
            'best_objective_value': self.best_objective_value,
            'constraint_adherence_summary': {
                'hold_period_stats': self.constraint_adherence_summary.hold_period_stats,
                'constraint_violations': self.constraint_adherence_summary.constraint_violations,
                'adherence_score': self.constraint_adherence_summary.adherence_score
            }
        }
