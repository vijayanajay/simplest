import logging
from pathlib import Path
from rich.console import Console as RichConsole
import typer

from ...config import load_yaml_config, validate_config
from ...workflows import AnalysisWorkflow
from ..utils import handle_cli_errors

logger = logging.getLogger(__name__)
console = RichConsole()

@handle_cli_errors
def analyze(
    config_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to YAML configuration file",
    ),
    report: bool = typer.Option(False, "--report", help="Generate PDF report"),
    report_html: bool = typer.Option(False, "--report-html", help="Generate comprehensive HTML report using QuantStats"),
    no_baseline: bool = typer.Option(False, "--no-baseline", help="Skip baseline comparison for faster execution"),
    validate_only: bool = typer.Option(False, "--validate-only", help="Validate configuration and exit."),
    output_dir: Path = typer.Option(None, "--output-dir", help="Directory to save reports."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress non-essential output."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colored terminal output."),
):
    """
    Run strategy analysis with optional baseline comparison.
    """
    if verbose:
        logging.getLogger('meqsap').setLevel(logging.DEBUG)

    config_data = load_yaml_config(config_file)
    config = validate_config(config_data)

    if validate_only:
        console.print("[green]Configuration is valid.[/green]")
        return

    cli_flags = {'report': report, 'report_html': report_html, 'no_baseline': no_baseline, 'output_dir': output_dir, 'quiet': quiet, 'no_color': no_color}

    workflow = AnalysisWorkflow(config, cli_flags)
    workflow.execute()