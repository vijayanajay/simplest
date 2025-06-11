# Story 8: Baseline Comparison & Advanced Reporting Framework - Pseudocode

**Generated Date:** June 12, 2025  
**Story Reference:** MEQSAP-008  
**Epic:** Epic 5 - Baseline Comparison & Advanced Reporting

## Overview

This document provides detailed pseudocode (natural language logical plans) for implementing the Baseline Comparison & Advanced Reporting Framework. The implementation follows the MEQSAP principle of minimalist orchestration, leveraging existing libraries like QuantStats for HTML reporting while maintaining clear separation of concerns.

## Component 1: Enhanced Configuration Models

### Component: `Config Module`
### Function: `BaselineConfig` Model Definition

**Inputs:**
* User-provided YAML configuration containing an optional `baseline_config` block.

**Output:**
* A validated `BaselineConfig` Pydantic model instance with proper defaults.

**Steps:**
1. **Define the Baseline Configuration Structure.**
   * Create a `BaselineConfig` Pydantic model with the following fields:
     * `active: bool = True` to enable/disable baseline comparison.
     * `strategy_type: str = "BuyAndHold"` to specify the baseline strategy type.
     * `params: Optional[Dict[str, Any]] = None` for any strategy-specific parameters.

2. **Implement Strategy Type Validation.**
   * Use a Pydantic validator to ensure `strategy_type` is one of the allowed values: `["BuyAndHold", "MovingAverageCrossover"]`.
   * Provide clear error messages if an unsupported strategy type is specified.

3. **Add Parameter Validation Logic.**
   * If `strategy_type` is "MovingAverageCrossover", validate that required parameters like `fast_ma` and `slow_ma` are present in the `params` dictionary.
   * For "BuyAndHold", ensure no parameters are required or provided.

4. **Integrate with StrategyConfig.**
   * Add `baseline_config: Optional[BaselineConfig] = None` field to the existing `StrategyConfig` model.
   * Ensure backward compatibility by making the field optional.

### Component: `Config Module`
### Function: `Default Baseline Injection`

**Inputs:**
* A parsed `StrategyConfig` that may or may not contain a `baseline_config`.
* CLI flags indicating whether baseline comparison is disabled (`--no-baseline`).

**Output:**
* A `StrategyConfig` with a properly configured baseline, either from user input or injected defaults.

**Steps:**
1. **Check for Explicit Baseline Configuration.**
   * If the `StrategyConfig` already contains a `baseline_config` block, validate it and use it as-is.

2. **Apply CLI Flag Override.**
   * If the `--no-baseline` flag is present, set `baseline_config.active = False` or set `baseline_config = None`.

3. **Inject Default Buy & Hold Baseline.**
   * If no `baseline_config` is present and `--no-baseline` is not used, create a default `BaselineConfig` instance.
   * Set `strategy_type = "BuyAndHold"`, `active = True`, and `params = None`.

4. **Return the Enhanced Configuration.**
   * Provide the complete `StrategyConfig` with baseline configuration ready for use by the workflow orchestrator.

## Component 2: Workflow Orchestration

### Component: `Workflows Module`
### Function: `AnalysisWorkflow.execute`

**Inputs:**
* A validated `StrategyConfig` containing both candidate and baseline configurations.
* CLI flags dictionary containing `report_html`, `no_baseline`, and other options.
* The market ticker and date range for the analysis.

**Output:**
* A `ComparativeAnalysisResult` containing results from both candidate and baseline backtests.

**Steps:**
1. **Initialize Workflow State.**
   * Extract the candidate strategy configuration from the main `StrategyConfig`.
   * Extract the baseline strategy configuration from `baseline_config`, if active.
   * Set up status tracking for real-time progress reporting.

2. **Display Initial Status.**
   * Use the `rich` library to show "🚀 Starting Analysis Workflow..." status message.
   * Indicate whether baseline comparison is enabled or disabled.

3. **Execute Candidate Strategy Backtest.**
   * Display status: "📊 Running candidate strategy backtest..."
   * Call the existing `run_complete_backtest` function from the `Backtest Module`.
   * Provide the candidate strategy configuration and market data.
   * Store the resulting `BacktestAnalysisResult` for the candidate.

4. **Execute Baseline Strategy Backtest (If Enabled).**
   * Check if baseline comparison is active and not disabled by CLI flags.
   * If baseline is enabled:
     * Display status: "📈 Running baseline strategy backtest..."
     * Call `run_complete_backtest` with the baseline strategy configuration.
     * Store the resulting `BacktestAnalysisResult` for the baseline.

5. **Handle Baseline Execution Failures Gracefully.**
   * Wrap the baseline backtest execution in a try-catch block.
   * If the baseline backtest fails:
     * Log the error details for debugging purposes.
     * Display a warning: "⚠️ Baseline strategy backtest failed. Displaying candidate results only."
     * Set `baseline_result = None` and `baseline_failed = True` in the result.
     * Continue with the workflow using only candidate results.

6. **Create Comparative Analysis Result.**
   * Instantiate a `ComparativeAnalysisResult` object.
   * Populate it with:
     * `candidate_result`: The successful candidate backtest result.
     * `baseline_result`: The baseline result (if successful) or `None` (if failed/disabled).
     * `baseline_failed`: Boolean indicating if baseline execution failed.
     * `baseline_failure_reason`: Error message if baseline failed.

7. **Calculate Comparative Verdict.**
   * If both candidate and baseline results are available:
     * Compare key metrics (default: Sharpe Ratio) between candidate and baseline.
     * Set `comparative_verdict` to "Outperformed" if candidate > baseline, otherwise "Underperformed".
   * If baseline is not available, set `comparative_verdict = None`.

8. **Return the Complete Result.**
   * Provide the fully populated `ComparativeAnalysisResult` to the calling CLI command.

## Component 3: Enhanced Reporting Architecture

### Component: `Reporting Module`
### Function: `BaseReporter` Protocol Definition

**Inputs:**
* None (this is an abstract protocol definition).

**Output:**
* A protocol interface that all reporter implementations must follow.

**Steps:**
1. **Define the Common Reporter Interface.**
   * Create an abstract base class `BaseReporter` using Python's `ABC` module.
   * Define the required method: `generate_report(self, result: ComparativeAnalysisResult) -> None`.

2. **Specify Implementation Requirements.**
   * Document that all concrete reporters must implement the `generate_report` method.
   * Ensure the method accepts a `ComparativeAnalysisResult` and handles both single-strategy and comparative scenarios.

### Component: `Reporting Module`
### Function: `TerminalReporter.generate_report`

**Inputs:**
* A `ComparativeAnalysisResult` containing candidate results and optional baseline results.

**Output:**
* A formatted terminal display showing comparative analysis using `rich` tables.

**Steps:**
1. **Check for Comparative vs. Single Strategy Scenario.**
   * Determine if baseline results are available by checking `result.baseline_result is not None`.
   * Choose the appropriate display format based on data availability.

2. **Create the Executive Verdict Table Structure.**
   * Use the `rich` library to create a table with appropriate columns.
   * For comparative analysis: Create columns "Metric", "Candidate", "Baseline".
   * For single strategy: Create columns "Metric", "Value".

3. **Populate Core Performance Metrics.**
   * Extract key metrics from the candidate result: Total Return, Sharpe Ratio, Calmar Ratio, Max Drawdown.
   * If baseline results are available, extract the same metrics from baseline results.
   * Format percentages and ratios with appropriate precision (e.g., "15.23%", "1.45").

4. **Add Comparative Verdict Section.**
   * If comparative data is available:
     * Add a highlighted row showing the overall verdict ("Outperformed" or "Underperformed").
     * Use colored formatting (green for outperformed, red for underperformed).
   * Include the basis for comparison (e.g., "Based on Sharpe Ratio").

5. **Handle Baseline Failure Scenarios.**
   * If `result.baseline_failed` is `True`:
     * Display the candidate metrics in single-strategy format.
     * Add a warning section: "⚠️ Baseline analysis unavailable due to: {failure_reason}".

6. **Display Vibe Check Results.**
   * Include existing vibe check results from both candidate and baseline (if available).
   * Use consistent formatting with existing reporting standards.

7. **Render the Complete Table.**
   * Use `rich.console` to display the formatted table to the terminal.
   * Ensure proper spacing and visual hierarchy for easy reading.

### Component: `Reporting Module`
### Function: `HtmlReporter.generate_report`

**Inputs:**
* A `ComparativeAnalysisResult` containing returns data for both candidate and baseline strategies.

**Output:**
* A comprehensive HTML file (`report.html`) generated using the QuantStats library.

**Steps:**
1. **Extract Returns Data from Results.**
   * From the candidate `BacktestAnalysisResult`, extract the daily returns series as a pandas Series.
   * If baseline results are available, extract the baseline daily returns series.
   * Ensure both series have matching date indices for proper comparison.

2. **Prepare QuantStats Input Data.**
   * Convert the returns data to the format expected by QuantStats (typically percentage returns).
   * Handle any data preprocessing required (e.g., filling missing values, aligning dates).

3. **Generate Comparative HTML Report.**
   * If baseline data is available:
     * Use `quantstats.reports.html(candidate_returns, benchmark=baseline_returns, output='report.html')`.
     * This creates a comprehensive comparison report with multiple sections and charts.
   * If only candidate data is available:
     * Use `quantstats.reports.html(candidate_returns, output='report.html')` for single-strategy analysis.

4. **Customize Report Metadata.**
   * Set appropriate title and metadata for the report (e.g., "MEQSAP Strategy Analysis Report").
   * Include timestamp and configuration summary in the report.

5. **Handle QuantStats Errors Gracefully.**
   * Wrap the QuantStats call in error handling to catch potential issues.
   * If HTML generation fails, log the error and inform the user that PDF reporting is still available.

6. **Confirm Report Generation.**
   * Verify that the `report.html` file was created successfully.
   * Display a success message: "✅ HTML report generated: report.html".

## Component 4: CLI Integration

### Component: `CLI Module`
### Function: `Enhanced Analyze Command`

**Inputs:**
* Command-line arguments including the configuration file path and new flags (`--report-html`, `--no-baseline`).

**Output:**
* Execution of the complete analysis workflow with appropriate reporting based on flags.

**Steps:**
1. **Define New Command-Line Flags.**
   * Add `--report-html` flag with description: "Generate comprehensive HTML report using QuantStats".
   * Add `--no-baseline` flag with description: "Skip baseline comparison for faster execution".
   * Ensure flags are available for both `analyze` and `optimize-single` commands.

2. **Parse and Validate CLI Arguments.**
   * Use Typer to parse the command-line arguments and flags.
   * Validate that the configuration file path exists and is readable.

3. **Load and Enhance Configuration.**
   * Load the YAML configuration file using the existing `Config Module`.
   * Apply baseline injection logic based on the configuration and `--no-baseline` flag.

4. **Execute the Analysis Workflow.**
   * Create an instance of `AnalysisWorkflow` with the enhanced configuration and CLI flags.
   * Call `workflow.execute()` to perform the complete analysis including baseline comparison.

5. **Generate Reports Based on Flags.**
   * Always generate terminal output using `TerminalReporter`.
   * If `--report` flag is present, generate PDF report using existing `PdfReporter`.
   * If `--report-html` flag is present, generate HTML report using new `HtmlReporter`.

6. **Handle Any Execution Errors.**
   * Wrap the entire execution in appropriate error handling.
   * Provide clear error messages for configuration issues, data problems, or reporting failures.
   * Ensure proper exit codes are returned based on success or failure status.

## Component 5: Data Models

### Component: `Reporting Models Module`
### Function: `ComparativeAnalysisResult` Definition

**Inputs:**
* Results from candidate and baseline strategy backtests.

**Output:**
* A structured data model containing all comparative analysis information.

**Steps:**
1. **Define the Core Data Structure.**
   * Create a Pydantic model `ComparativeAnalysisResult` with the following fields:
     * `candidate_result: BacktestAnalysisResult` - Always present, contains candidate strategy results.
     * `baseline_result: Optional[BacktestAnalysisResult] = None` - Present only if baseline succeeded.
     * `baseline_failed: bool = False` - Indicates if baseline execution failed.
     * `baseline_failure_reason: Optional[str] = None` - Error message if baseline failed.
     * `comparative_verdict: Optional[str] = None` - "Outperformed" or "Underperformed" or None.

2. **Add Computed Properties.**
   * Create a property `has_baseline` that returns `True` if baseline_result is not None and baseline_failed is False.
   * Create a property `is_comparative` that indicates if meaningful comparison can be made.

3. **Implement Validation Logic.**
   * Add a Pydantic validator to ensure that if `baseline_failed` is True, then `baseline_result` should be None.
   * Validate that `comparative_verdict` is only set when valid baseline results are available.

4. **Provide Helper Methods.**
   * Add method `get_comparison_basis() -> str` that returns the metric used for comparison (e.g., "Sharpe Ratio").
   * Add method `format_verdict() -> str` that returns a formatted verdict string for display.

## Component 6: Status Reporting Enhancement

### Component: `CLI Module`
### Function: `Real-time Status Updates`

**Inputs:**
* Current workflow execution stage and progress information.

**Output:**
* Real-time status displays in the terminal using `rich` status indicators.

**Steps:**
1. **Create Status Context Manager.**
   * Use `rich.status.Status` to create a context manager for displaying ongoing operations.
   * Define status messages for each major workflow stage.

2. **Display Workflow Initialization Status.**
   * Show "🔧 Initializing analysis workflow..." when the workflow starts.
   * Include information about whether baseline comparison is enabled.

3. **Show Data Acquisition Progress.**
   * Display "📡 Fetching market data for {ticker}..." during data download.
   * Show "💾 Using cached data for {ticker}" if cache is used.

4. **Indicate Backtest Execution Stages.**
   * Show "📊 Running candidate strategy backtest..." during candidate execution.
   * Show "📈 Running baseline strategy backtest..." during baseline execution (if enabled).
   * Include approximate timing information if available.

5. **Display Report Generation Progress.**
   * Show "📋 Generating terminal report..." during terminal output creation.
   * Show "🌐 Generating HTML report..." when `--report-html` flag is used.
   * Show "📄 Generating PDF report..." when `--report` flag is used.

6. **Handle Status Updates During Errors.**
   * If baseline fails, update status to "⚠️ Baseline failed, continuing with candidate analysis..."
   * Ensure status indicators are properly cleared even if errors occur.

7. **Provide Completion Summary.**
   * Show "✅ Analysis complete!" with summary of generated outputs.
   * List all generated files (e.g., "Generated: report.html, report.pdf").

## Implementation Notes

### Integration with Existing Systems
- All new components must integrate seamlessly with the existing `meqsap.backtest`, `meqsap.config`, and `meqsap.cli` modules.
- The enhanced reporting architecture maintains backward compatibility with existing PDF reporting functionality.
- Error handling follows existing patterns using custom exceptions from `meqsap.exceptions`.

### Performance Considerations
- The `--no-baseline` flag provides an escape hatch for users who prioritize speed over comparison.
- Baseline execution is designed to fail gracefully without impacting candidate analysis.
- HTML report generation is optional and only executes when explicitly requested.

### Testing Requirements
- Each component requires comprehensive unit tests covering both success and failure scenarios.
- Integration tests must verify end-to-end functionality with various CLI flag combinations.
- Resilience tests must confirm graceful handling of baseline failures.

This pseudocode provides a comprehensive blueprint for implementing Epic 5: Baseline Comparison & Advanced Reporting while maintaining MEQSAP's architectural principles of minimal orchestration and robust error handling.