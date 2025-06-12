"""Data models for comparative analysis reporting."""

from typing import Optional
from pydantic import BaseModel, validator
from ..backtest import BacktestAnalysisResult


class ComparativeAnalysisResult(BaseModel):
    """Holds results from both candidate and baseline strategy backtests."""
    
    candidate_result: BacktestAnalysisResult
    baseline_result: Optional[BacktestAnalysisResult] = None
    baseline_failed: bool = False
    baseline_failure_reason: Optional[str] = None
    comparative_verdict: Optional[str] = None  # "Outperformed" | "Underperformed"
    
    @validator('baseline_result')
    def validate_baseline_consistency(cls, v, values):
        """Ensure baseline_result consistency with baseline_failed flag."""
        baseline_failed = values.get('baseline_failed', False)
        if baseline_failed and v is not None:
            raise ValueError("baseline_result should be None when baseline_failed is True")
        return v
    
    @validator('comparative_verdict')
    def validate_verdict_requires_baseline(cls, v, values):
        """Ensure comparative_verdict is only set when baseline is available."""
        baseline_result = values.get('baseline_result')
        baseline_failed = values.get('baseline_failed', False)
        
        if v is not None and (baseline_result is None or baseline_failed):
            raise ValueError("comparative_verdict requires successful baseline_result")
        
        if v is not None and v not in ["Outperformed", "Underperformed"]:
            raise ValueError("comparative_verdict must be 'Outperformed' or 'Underperformed'")
        
        return v
    
    @property
    def has_baseline(self) -> bool:
        """Check if valid baseline results are available."""
        return self.baseline_result is not None and not self.baseline_failed
    
    @property
    def is_comparative(self) -> bool:
        """Check if meaningful comparison can be made."""
        return self.has_baseline
    
    def get_comparison_basis(self) -> str:
        """Get the metric used for comparison."""
        return "Sharpe Ratio"
    
    def format_verdict(self) -> str:
        """Format the verdict string for display."""
        if not self.is_comparative:
            return "No baseline comparison available"
        
        if self.comparative_verdict:
            return f"Strategy {self.comparative_verdict} baseline ({self.get_comparison_basis()})"
        
        return "Comparison inconclusive"
