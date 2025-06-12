"""Data models for comparative analysis reporting."""

from typing import Optional
from pydantic import BaseModel, model_validator, Field
from ..backtest import BacktestAnalysisResult


class ReportConfig(BaseModel):
    """Configuration for report generation."""
    
    include_pdf: bool = Field(False, description="Whether to generate PDF report")
    output_directory: str = Field("./reports", description="Directory for report output")
    filename_prefix: str = Field("meqsap_report", description="Prefix for report filenames")
    include_plots: bool = Field(True, description="Whether to include plots in PDF")
    decimal_places: int = Field(2, ge=0, le=6, description="Decimal places for formatting")
    color_output: bool = Field(True, description="Whether to use colored terminal output")


class ExecutiveVerdictData(BaseModel):
    """Formatted data for executive verdict display."""
    
    strategy_name: str = Field(..., description="Name of the strategy")
    ticker: str = Field(..., description="Stock ticker symbol")
    date_range: str = Field(..., description="Formatted date range")
    total_return: str = Field(..., description="Formatted total return")
    annual_return: str = Field(..., description="Formatted annualized return")
    sharpe_ratio: str = Field(..., description="Formatted Sharpe ratio")
    max_drawdown: str = Field(..., description="Formatted maximum drawdown")
    win_rate: str = Field(..., description="Formatted win rate")
    total_trades: int = Field(..., description="Total number of trades")
    vibe_check_status: str = Field(..., description="Overall vibe check status")
    robustness_score: str = Field(..., description="Formatted robustness assessment")
    overall_verdict: str = Field(..., description="Overall strategy verdict")


class ComparativeAnalysisResult(BaseModel):
    """Holds results from both candidate and baseline strategy backtests."""
    
    candidate_result: BacktestAnalysisResult
    baseline_result: Optional[BacktestAnalysisResult] = None
    baseline_failed: bool = False
    baseline_failure_reason: Optional[str] = None
    comparative_verdict: Optional[str] = None  # "Outperformed" | "Underperformed"
    
    @model_validator(mode='after')
    def check_consistency(self) -> 'ComparativeAnalysisResult':
        """Validate consistency between baseline status and other fields."""
        # Check baseline consistency
        if self.baseline_failed and self.baseline_result is not None:
            raise ValueError("baseline_result should be None when baseline_failed is True")
        # Check verdict consistency
        if self.comparative_verdict is not None:
            if self.baseline_result is None or self.baseline_failed:
                raise ValueError("comparative_verdict requires a successful baseline_result")
            if self.comparative_verdict not in ["Outperformed", "Underperformed"]:
                raise ValueError("comparative_verdict must be 'Outperformed' or 'Underperformed'")
        return self
    
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
