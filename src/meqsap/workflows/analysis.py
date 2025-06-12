"""Analysis workflow orchestration."""

import logging
from typing import Dict, Any, Optional

from rich.console import Console
from rich.status import Status

from ..config import StrategyConfig
from ..backtest import BacktestAnalysisResult, run_complete_backtest
from ..reporting.models import ComparativeAnalysisResult
from ..reporting.main import ReportingOrchestrator
from ..exceptions import BacktestError, WorkflowError

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
        try:
            with Status("🔧 Initializing analysis workflow...", console=self.console) as status:
                # Show baseline status
                baseline_config = self.config.get_baseline_config_with_defaults(self.no_baseline)
                if baseline_config and baseline_config.active:
                    status.update("🔧 Baseline comparison enabled")
                else:
                    status.update("🔧 Baseline comparison disabled")
                
                # Execute candidate strategy
                status.update("📊 Running candidate strategy backtest...")
                candidate_result = self._run_candidate_backtest()
                
                # Execute baseline strategy if enabled
                baseline_result = None
                baseline_failed = False
                baseline_failure_reason = None
                
                if baseline_config and baseline_config.active:
                    status.update("📈 Running baseline strategy backtest...")
                    baseline_result, baseline_failed, baseline_failure_reason = self._run_baseline_safely(baseline_config)
                    
                    if baseline_failed:
                        status.update("⚠️ Baseline failed, continuing with candidate analysis...")
                
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
            
        except Exception as e:
            logger.error(f"Analysis workflow failed: {e}")
            raise WorkflowError(f"Analysis workflow execution failed: {e}")
    
    def _run_candidate_backtest(self) -> BacktestAnalysisResult:
        """Run the candidate strategy backtest."""
        try:
            return run_complete_backtest(self.config)
        except Exception as e:
            logger.error(f"Candidate backtest failed: {e}")
            raise BacktestError(f"Candidate strategy backtest failed: {e}")
    
    def _run_baseline_safely(self, baseline_config) -> tuple[Optional[BacktestAnalysisResult], bool, Optional[str]]:
        """Run baseline backtest with comprehensive error handling."""
        try:
            # Create baseline strategy config
            baseline_strategy_config = self._create_baseline_strategy_config(baseline_config)
            
            # Execute baseline backtest
            baseline_result = run_complete_backtest(baseline_strategy_config)
            return baseline_result, False, None
            
        except Exception as e:
            error_msg = f"Baseline strategy execution failed: {str(e)}"
            logger.warning(error_msg)
            return None, True, error_msg
    
    def _create_baseline_strategy_config(self, baseline_config) -> StrategyConfig:
        """Create a strategy config for the baseline strategy."""
        # Create a copy of the main config but with baseline strategy settings
        baseline_dict = self.config.dict()
        
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
            comparative_verdict=comparative_verdict
        )
    
    def _calculate_verdict(self, candidate: BacktestAnalysisResult, baseline: BacktestAnalysisResult) -> str:
        """Calculate performance verdict based on Sharpe ratio."""
        if candidate.sharpe_ratio > baseline.sharpe_ratio:
            return "Outperformed"
        else:
            return "Underperformed"
    
    def _generate_reports(self, result: ComparativeAnalysisResult) -> None:
        """Generate reports based on CLI flags."""
        try:
            orchestrator = ReportingOrchestrator.from_cli_flags(self.cli_flags)
            orchestrator.generate_reports(result)
            
            # Show completion summary
            self._show_completion_summary()
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            # Don't fail the entire workflow for reporting issues
            self.console.print("⚠️ Some reports failed to generate. Check logs for details.")
    
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
