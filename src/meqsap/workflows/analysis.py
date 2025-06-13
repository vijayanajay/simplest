"""Analysis workflow orchestration."""

import logging
from typing import Dict, Any, Optional, cast

import pandas as pd
from rich.console import Console
from rich.status import Status

from ..config import StrategyConfig
from ..data import fetch_market_data
from ..backtest import BacktestAnalysisResult, run_complete_backtest
from ..reporting.models import ComparativeAnalysisResult
from ..reporting.main import ReportingOrchestrator, TerminalReporter, HtmlReporter, PdfReporter
from ..exceptions import BacktestError, WorkflowError, DataError, ConfigurationError, ReportingError

logger = logging.getLogger(__name__)


class AnalysisWorkflow:
    """Orchestrates the complete analysis workflow including baseline comparison."""
    
    def __init__(self, config: StrategyConfig, cli_flags: Dict[str, Any]):
        self.config = config
        self.cli_flags = cli_flags
        self.console = Console()
        
        # Extract flags
        self.no_baseline = cli_flags.get('no_baseline', False)
        self.report_html = cli_flags.get('report_html', False)
        self.report_pdf = cli_flags.get('report', False)
    
    def execute(self) -> ComparativeAnalysisResult:
        """Execute the complete analysis workflow."""
        with Status("🔧 Initializing analysis workflow...", console=self.console) as status:
            try:
                # Show baseline status
                baseline_config = self.config.get_baseline_config_with_defaults(self.no_baseline)
                if baseline_config and baseline_config.active:
                    status.update("🔧 Baseline comparison enabled")
                else:
                    status.update("🔧 Baseline comparison disabled")
                
                # Fetch market data
                status.update(f"\ud83d\udce1 Fetching market data for {self.config.ticker}...")
                market_data = fetch_market_data(
                    ticker=self.config.ticker,
                    start_date=self.config.start_date,
                    end_date=self.config.end_date,
                )
                if market_data.empty:
                    raise DataError(f"No market data found for {self.config.ticker}")

                # Execute candidate strategy
                status.update("\ud83d\udcca Running candidate strategy backtest...")
                candidate_result = self._run_candidate_backtest(market_data)
                
                # Execute baseline strategy if enabled
                baseline_result = None
                baseline_failed = False
                baseline_failure_reason = None
                
                if baseline_config and baseline_config.active:
                    status.update("\ud83d\udcc8 Running baseline strategy backtest...")
                    baseline_result, baseline_failed, baseline_failure_reason = self._run_baseline_safely(baseline_config, market_data)
                    
                    if baseline_failed:
                        status.update("\u26a0\ufe0f Baseline failed, continuing with candidate analysis...")
                
                # Create comparative result
                status.update("📋 Analyzing results...")
                result = self._create_comparative_result(
                    candidate_result, baseline_result, baseline_failed, baseline_failure_reason
                )                
                # Generate reports
                status.update("📄 Generating reports...")
                self._generate_reports(result)
                
                status.update("✅ Analysis complete!")
                
                return result
            except (DataError, BacktestError, ConfigurationError, ReportingError) as e:
                # Re-raise known, specific errors so the CLI can handle them correctly
                raise
            except Exception as e:
                logger.error(f"Analysis workflow failed with an unexpected error: {e}", exc_info=True)
                raise WorkflowError(f"Analysis workflow execution failed: {e}") from e
    
    def _run_candidate_backtest(self, market_data: pd.DataFrame) -> BacktestAnalysisResult:
        """Run the candidate strategy backtest."""
        try:
            return run_complete_backtest(self.config, market_data)
        except Exception as e:
            logger.error(f"Candidate backtest failed: {e}")
            raise BacktestError(f"Candidate strategy backtest failed: {e}")

    def _run_baseline_safely(self, baseline_config, market_data: pd.DataFrame) -> tuple[Optional[BacktestAnalysisResult], bool, Optional[str]]:
        """Run baseline backtest with comprehensive error handling."""
        try:
            # Create baseline strategy config
            baseline_strategy_config = self._create_baseline_strategy_config(baseline_config)
            
            # Execute baseline backtest
            baseline_result = run_complete_backtest(baseline_strategy_config, market_data)
            return baseline_result, False, None
            
        except Exception as e:
            error_msg = f"Baseline strategy execution failed: {str(e)}"
            logger.warning(error_msg)
            return None, True, error_msg

    def _create_baseline_strategy_config(self, baseline_config) -> StrategyConfig:
        """Create a strategy config for the baseline strategy."""
        # Create a copy of the main config but with baseline strategy settings
        baseline_dict = self.config.model_dump()
        
        # Replace strategy-specific settings with baseline
        if baseline_config.strategy_type == "BuyAndHold":
            baseline_dict['strategy_type'] = "BuyAndHold"
            baseline_dict['strategy_params'] = {}
        elif baseline_config.strategy_type == "MovingAverageCrossover":
            baseline_dict['strategy_type'] = "MovingAverageCrossover"
            baseline_dict['strategy_params'] = baseline_config.params or {}
        
        # Remove baseline_config to avoid recursion
        baseline_dict['baseline_config'] = None
        
        return StrategyConfig(**baseline_dict)
    
    def _create_comparative_result(
        self, 
        candidate_result: BacktestAnalysisResult,
        baseline_result: Optional[BacktestAnalysisResult],
        baseline_failed: bool,
        baseline_failure_reason: Optional[str]
    ) -> ComparativeAnalysisResult:
        """Create the comparative analysis result."""
        
        # Calculate verdict if both results are available
        comparative_verdict = None
        if baseline_result is not None and not baseline_failed:
            comparative_verdict = self._calculate_verdict(candidate_result, baseline_result)
        
        return ComparativeAnalysisResult(
            candidate_result=candidate_result,
            baseline_result=baseline_result,
            baseline_failed=baseline_failed,
            baseline_failure_reason=baseline_failure_reason,
            comparative_verdict=comparative_verdict        )
    
    def _calculate_verdict(self, candidate: BacktestAnalysisResult, baseline: BacktestAnalysisResult) -> str:
        """Calculate performance verdict based on Sharpe ratio."""
        if candidate.primary_result.sharpe_ratio > baseline.primary_result.sharpe_ratio:
            return "Outperformed"
        else:
            return "Underperformed"

    def _generate_reports(self, result: ComparativeAnalysisResult) -> None:
        """Generate reports based on CLI flags."""
        orchestrator = ReportingOrchestrator()
        orchestrator.add_reporter(TerminalReporter())
        if self.report_html:
            orchestrator.add_reporter(HtmlReporter())
        if self.report_pdf:
            orchestrator.add_reporter(PdfReporter())
        orchestrator.generate_reports(result)
        self._show_completion_summary()
    
    def _show_completion_summary(self) -> None:
        """Show completion summary with generated files."""
        generated_files = []
        
        if self.report_pdf:
            generated_files.append("report.pdf")
        if self.report_html:
            generated_files.append("report.html")
        
        if generated_files:
            files_str = ", ".join(generated_files)
            self.console.print(f"✅ Analysis complete! Generated: {files_str}")
        else:
            self.console.print("✅ Analysis complete!")
