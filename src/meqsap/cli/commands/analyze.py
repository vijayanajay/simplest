import typer

from ...config import Config
from ...workflows import AnalysisWorkflow
from ...logging import logger, console

def analyze(
    config_file: str = typer.Argument(..., help="Path to YAML configuration file"),
    report: bool = typer.Option(False, "--report", help="Generate PDF report"),
    report_html: bool = typer.Option(False, "--report-html", help="Generate comprehensive HTML report using QuantStats"),
    no_baseline: bool = typer.Option(False, "--no-baseline", help="Skip baseline comparison for faster execution"),
):
    """
    Run strategy analysis with optional baseline comparison.
    
    Supports both single-strategy analysis and comparative analysis against
    baseline strategies like Buy & Hold.
    """
    try:
        # Load configuration
        config = Config.load(config_file)
        
        # Create CLI flags dictionary
        cli_flags = {
            'report': report,
            'report_html': report_html,
            'no_baseline': no_baseline
        }
        
        # Execute workflow
        workflow = AnalysisWorkflow(config, cli_flags)
        result = workflow.execute()
        
        return 0
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        console.print(f"❌ Analysis failed: {e}")
        return 1