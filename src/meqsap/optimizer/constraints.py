"""Constraint evaluation and trade duration analysis."""

from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from dataclasses import dataclass


@dataclass
class TradeDurationStats:
    """Statistics for trade duration analysis."""
    average_hold_days: float
    median_hold_days: float
    percentage_within_target: float
    total_trades: int
    trades_within_target: int
    min_hold_days: float
    max_hold_days: float
    std_hold_days: float


@dataclass
class ConstraintAdherenceMetrics:
    """Metrics for constraint adherence evaluation."""
    hold_period_satisfied: bool
    hold_period_score: float  # 0-1 score for hold period adherence
    min_trades_satisfied: bool
    total_constraint_score: float  # Overall constraint satisfaction score
    trade_duration_stats: TradeDurationStats
    violation_details: List[str]


class TradeDurationAnalyzer:
    """Analyzes trade duration from backtest results."""
    
    def calculate_trade_durations(self, trades_df: pd.DataFrame) -> List[float]:
        """Calculate duration in days for each trade.
        
        Args:
            trades_df: DataFrame with trade entry/exit information
            
        Returns:
            List of trade durations in days
        """
        if trades_df.empty:
            return []
        
        # Ensure we have required columns
        required_cols = ['entry_date', 'exit_date']
        if not all(col in trades_df.columns for col in required_cols):
            raise ValueError(f"Missing required columns: {required_cols}")
        
        # Calculate durations
        durations = []
        for _, trade in trades_df.iterrows():
            entry_date = pd.to_datetime(trade['entry_date'])
            exit_date = pd.to_datetime(trade['exit_date'])
            duration_days = (exit_date - entry_date).days
            durations.append(duration_days)
        
        return durations
    
    def analyze_trade_durations(
        self, 
        trades_df: pd.DataFrame,
        target_range: Optional[List[int]] = None
    ) -> TradeDurationStats:
        """Analyze trade duration statistics.
        
        Args:
            trades_df: DataFrame with trade information
            target_range: [min, max] target holding period in days
            
        Returns:
            TradeDurationStats object
        """
        durations = self.calculate_trade_durations(trades_df)
        
        if not durations:
            return TradeDurationStats(
                average_hold_days=0.0,
                median_hold_days=0.0,
                percentage_within_target=0.0,
                total_trades=0,
                trades_within_target=0,
                min_hold_days=0.0,
                max_hold_days=0.0,
                std_hold_days=0.0
            )
        
        # Calculate basic statistics
        durations_array = np.array(durations)
        average_hold = float(np.mean(durations_array))
        median_hold = float(np.median(durations_array))
        min_hold = float(np.min(durations_array))
        max_hold = float(np.max(durations_array))
        std_hold = float(np.std(durations_array))
        
        # Calculate target range adherence
        percentage_within_target = 0.0
        trades_within_target = 0
        
        if target_range:
            min_target, max_target = target_range
            trades_within_target = sum(
                1 for d in durations 
                if min_target <= d <= max_target
            )
            percentage_within_target = (trades_within_target / len(durations)) * 100
        
        return TradeDurationStats(
            average_hold_days=average_hold,
            median_hold_days=median_hold,
            percentage_within_target=percentage_within_target,
            total_trades=len(durations),
            trades_within_target=trades_within_target,
            min_hold_days=min_hold,
            max_hold_days=max_hold,
            std_hold_days=std_hold
        )


class ConstraintEvaluator:
    """Evaluates constraint adherence for optimization results."""
    
    def __init__(self):
        self.duration_analyzer = TradeDurationAnalyzer()
    
    def evaluate_constraints(
        self,
        backtest_result: Any,  # BacktestResult object
        constraints: Dict[str, Any]
    ) -> ConstraintAdherenceMetrics:
        """Evaluate constraint adherence for a backtest result.
        
        Args:
            backtest_result: BacktestResult with trade information
            constraints: Constraint definitions
            
        Returns:
            ConstraintAdherenceMetrics object
        """
        violations = []
        
        # Get trades DataFrame from backtest result
        trades_df = getattr(backtest_result, 'trades_df', pd.DataFrame())
        
        # Analyze trade durations
        target_hold_period = constraints.get('target_hold_period_days')
        duration_stats = self.duration_analyzer.analyze_trade_durations(
            trades_df, target_hold_period
        )
        
        # Evaluate hold period constraint
        hold_period_satisfied = True
        hold_period_score = 1.0
        
        if target_hold_period:
            if duration_stats.total_trades == 0:
                hold_period_satisfied = False
                hold_period_score = 0.0
                violations.append("No trades generated to evaluate hold period")
            else:
                hold_period_score = duration_stats.percentage_within_target / 100.0
                # Consider constraint satisfied if at least 70% of trades are within target
                hold_period_satisfied = hold_period_score >= 0.7
                
                if not hold_period_satisfied:
                    violations.append(
                        f"Only {duration_stats.percentage_within_target:.1f}% of trades "
                        f"within target hold period {target_hold_period}"
                    )
        
        # Evaluate minimum trades constraint
        min_trades_satisfied = True
        min_trades_required = constraints.get('min_trades')
        
        if min_trades_required:
            if duration_stats.total_trades < min_trades_required:
                min_trades_satisfied = False
                violations.append(
                    f"Only {duration_stats.total_trades} trades generated, "
                    f"minimum {min_trades_required} required"
                )
        
        # Calculate overall constraint score
        constraint_scores = []
        if target_hold_period:
            constraint_scores.append(hold_period_score)
        if min_trades_required:
            constraint_scores.append(1.0 if min_trades_satisfied else 0.0)
        
        total_constraint_score = np.mean(constraint_scores) if constraint_scores else 1.0
        
        return ConstraintAdherenceMetrics(
            hold_period_satisfied=hold_period_satisfied,
            hold_period_score=hold_period_score,
            min_trades_satisfied=min_trades_satisfied,
            total_constraint_score=total_constraint_score,
            trade_duration_stats=duration_stats,
            violation_details=violations
        )
