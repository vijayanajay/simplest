# Story 7: Enhanced Optimization Progress Reporting - Complete Pseudocode (Revised)

**Story Reference:** MEQSAP-007 - Enhanced Optimization Progress Reporting and Error Handling  
**Architecture Alignment:** MEQSAP Architecture v2.3 (Revised)  
**Generation Date:** Generated based on PRD v2.2 and Architecture v2.3 (Revised)

## Directory Structure (as of implementation)

```
src/
    meqsap/
        __init__.py
        backtest.py
        cli.py
        config.py
        data.py
        exceptions.py
        reporting.py
        cli/
            optimization_ui.py
            commands/
                optimize.py
        optimizer/
            __init__.py
            engine.py
            models.py
            interruption.py

tests/
    __init__.py
    test_backtest.py
    test_cli.py
    test_config.py
    test_data.py
    test_optimization_error_handling.py
    test_reporting.py
    test_optimizer/
        ...
```

## Overview

This document provides comprehensive pseudocode for implementing real-time progress reporting, robust error handling, and graceful interruption for optimization runs. The implementation follows the architecture's emphasis on "orchestration over implementation" and leverages Optuna's callback system with `rich` progress bars.

### Key Revisions in this Version
*   **Decoupled Architecture:** The `meqsap_optimizer` module is now fully decoupled from the `rich` library. The `cli` module owns all progress display logic and passes a simple `update` function to the optimizer.
*   **Clarity on Logging:** Specified log levels (`INFO`, `WARNING`, `DEBUG`) for different events to improve diagnostics.
*   **Explicit Constants:** Replaced "magic values" like `float('-inf')` with a named constant (`FAILED_TRIAL_SCORE`) for better readability and maintainability.
*   **RDB Storage Mentioned:** Explicitly noted the integration of Optuna's RDB storage for trial history persistence, as per the architecture.
*   **Testing Strategy:** Added a dedicated section outlining a clear and effective strategy for unit testing the error handling logic.

## Component 1: Optimization Progress Callback System

**Component:** `meqsap_optimizer.engine`  
**Function:** `OptimizationEngine`'s internal state management

**Inputs:**
* An `on_trial_complete` callback function provided by the CLI (`Callable[[ProgressData], None]`).
* Optuna `Study` and `Trial` objects.

**Output:**
* Invokes the `on_trial_complete` callback with a `ProgressData` object after each trial.

**Steps:**
1. **Initialize Progress Tracking State.**
   * In the `OptimizationEngine`, create internal counters for total trials, successful trials, and failed trials by category.
   * Initialize timing trackers.

2. **Receive Trial Completion Notification.**
   * Within the optimization loop, after each trial completes, gather all relevant data.
   * This includes trial number, parameters, completion status, elapsed time, and current best score from the Optuna `study` object.

3. **Classify Trial Outcome.**
   * If the trial failed, determine the failure category (Data Error, Calculation Error, etc.).
   * Update the appropriate internal failure counter.

4. **Package and Expose Progress Data.**
   * Create an instance of the `ProgressData` data model (see Component 6).
   * Populate it with the current state: trial counts, best score, timing, error summary, and the parameters of the just-completed trial.
   * Call the `on_trial_complete` function provided by the CLI, passing the `ProgressData` object.

## Component 2: Rich Progress Bar Management

**Component:** `meqsap.cli`  
**Function:** `optimize_single` command implementation

**Inputs:**
* Optimization algorithm name (Grid Search or Random Search).
* Total number of trials (known for Grid Search, None for Random Search).

**Output:**
* A real-time `rich.Progress` display in the terminal.
* Orchestrates the optimization run.

**Steps:**
1. **Configure and Initialize `rich.Progress`.**
   * Create a `rich.Progress` instance with appropriate columns (e.g., `BarColumn`, `TextColumn`, `TimeElapsedColumn`).
   * For Grid Search, show `[progress.percentage]` and `"{task.completed}/{task.total}"`.
   * For Random Search, use a spinner and show `"{task.completed} trials"`.
   * Add a `TextColumn` for the best score found so far.

2. **Create the Progress Update Callback Function.**
   * Define a nested function or a closure, `update_progress_display(progress_data: ProgressData)`, inside the `optimize_single` command function.
   * This function will capture the `rich.Progress` instance and the `TaskID` from its scope.
   * **Parameter Display Logic:** Inside the callback, format the `current_params` dictionary into a string (e.g., `"fast_ma=10, slow_ma=50"`). Truncate the string with an ellipsis (`...`) if it exceeds a defined character limit to prevent breaking the progress bar layout.
   * The callback's logic will update the progress bar's description and advance the task.

3. **Instantiate and Run the Optimizer.**
   * Create an instance of the `OptimizationEngine`.
   * Call its main execution method, passing the strategy config, market data, and the `update_progress_display` callback function.
   * Example: `optimizer.run(config=config, data=data, on_trial_complete=update_progress_display)`

4. **Manage Progress Bar Lifecycle.**
   * The `rich.Progress` object should be used as a context manager (`with Progress(...) as progress:`) to ensure it is properly cleaned up, even if errors occur.

## Component 3: Robust Error Handling in Optimization Engine

**Component:** `meqsap_optimizer.engine`  
**Function:** `_run_single_trial`

**Inputs:**
* Optuna `Trial` object with suggested parameter values.
* Market data DataFrame for backtesting.

**Output:**
* Objective score for successful trials.
* A classified `TrialFailureType` for failed trials.
* The appropriate return value for Optuna (score or pruned state).

**Steps:**
1. **Define Constants and Setup.**
   * At the module level: `FAILED_TRIAL_SCORE = -np.inf` (or a similar very poor score).
   * **RDB Storage Note:** The `Optuna.create_study` call (which precedes this loop) should be configured with `storage="sqlite:///meqsap_trials.db"` to enable trial history persistence as per the architecture.

2. **Execute Protected Backtest.**
   * Wrap the `run_complete_backtest` call in a `try...except` block.
   * Log the start of the trial with `logger.info(f"Starting trial {trial.number} with params: {trial.params}")`.

3. **Handle Data-Related Errors.**
   * `except DataError as e:`
   * `logger.warning(f"Trial {trial.number} failed: [DataError] {e}. Params: {trial.params}")`
   * Record this failure internally as a "Data Error".
   * `return FAILED_TRIAL_SCORE`

4. **Handle Calculation Errors.**
   * `except CalculationError as e:`
   * `logger.warning(f"Trial {trial.number} failed: [CalculationError] {e}. Params: {trial.params}")`
   * Record this failure as a "Calculation Error".
   * `return FAILED_TRIAL_SCORE`

5. **Handle Validation Errors.**
   * `except ValidationError as e:`
   * `logger.warning(f"Trial {trial.number} failed: [ValidationError] {e}. Params: {trial.params}")`
   * Record as "Validation Error".
   * `return FAILED_TRIAL_SCORE`

6. **Handle Unknown Errors.**
   * `except Exception as e:`
   * `logger.debug(f"Trial {trial.number} failed with an unexpected error. Params: {trial.params}", exc_info=True)` (exc_info=True logs the full traceback).
   * Record as "Unknown Error".
   * `return FAILED_TRIAL_SCORE`

7. **Process Successful Trials.**
   * If the backtest succeeds, evaluate the result using the configured objective function.
   * Return the calculated objective score to Optuna.

## Component 4: Graceful Interruption Handling

**Component:** `meqsap.cli`  
**Function:** `OptimizationInterruptHandler`

**Inputs:**
* An active optimization process.
* Signal handlers for interrupt detection (SIGINT/Ctrl+C).

**Output:**
* Graceful termination of optimization with partial results.

**Steps:**
1. **Register Signal Handler.**
   * Use a context manager for the signal handler to ensure it's set and restored correctly.
   * Use a `threading.Event` to communicate the interruption request to the optimization loop.

2. **Monitor for Interruption.**
   * The `OptimizationEngine` will check the `interruption_event.is_set()` flag at the start of each new trial.
   * If set, it will stop asking Optuna for new trials and exit the loop gracefully.

3. **Handle Interruption Gracefully.**
   * The `cli` will catch the early exit from the optimizer.
   * The `rich.Progress` context manager will handle its own cleanup.
   * The `cli` will then proceed to call the reporting function with the partial results collected so far.

4. **Prepare Partial Results Summary.**
   * The reporting function will check an `was_interrupted` flag in the `OptimizationResult`.
   * If true, it will clearly state that the results are partial and based on the number of trials that were completed.

## Component 5: Enhanced Optimization Results Reporting

**Component:** `meqsap.reporting`  
**Function:** `display_optimization_summary`

**Inputs:**
* `OptimizationResult` object containing best parameters, scores, and the error summary.
* Constraint adherence metrics.

**Output:**
* Comprehensive terminal display of optimization outcomes.

**Steps:**
1. **Display Optimization Run Statistics.**
   * Show total trials attempted, time elapsed, and average time per trial.
   * Clearly state if the run was interrupted.

2. **Present Error Summary by Category.**
   * Display a breakdown of failed trials: `Data Errors: 2 (5%)`, `Calculation Errors: 1 (2.5%)`, etc.
   * This data comes directly from the `OptimizationResult` object.

3. **Show Best Strategy Results.**
   * Display the best parameter combination found.
   * Present the objective score achieved.

4. **Include Constraint Adherence Details.**
   * **Crucially**, highlight hold period statistics: "Avg Hold Period: 15.2 days", "% Trades in Target Range (5-20 days): 85%".
   * Indicate if the best strategy meets all specified constraints.

5. **Generate Enhanced PDF Report for Best Strategy.**
   * If `--report` was used, generate a `pyfolio` PDF for the *best found strategy*.
   * Include optimization metadata (algorithm, trials run, best params) in a header or appendix of the report.

## Component 6: Optimization Progress Data Models

**Component:** `meqsap_optimizer.models`  
**Function:** Data structures for progress tracking

**Inputs/Outputs:** These are the data structures used for communication.

**Steps:**
1. **Define `ProgressData` Structure.**
   * This is the key data contract between the optimizer and the CLI's update function.
   ```python
   from dataclasses import dataclass
   from typing import Dict, Optional, Any

   @dataclass
   class ProgressData:
       current_trial: int
       total_trials: Optional[int]
       best_score: Optional[float]
       elapsed_seconds: float
       failed_trials_summary: Dict[str, int] # e.g., {"Data Error": 2, ...}
       current_params: Dict[str, Any]
   ```

2. **Define `ErrorSummary` Structure.**
   * This will be part of the final `OptimizationResult`.
   ```python
   @dataclass
   class ErrorSummary:
       total_failed_trials: int
       failure_counts_by_type: Dict[str, int]
   ```

3. **Enhance `OptimizationResult` Model.**
   * Extend the existing `OptimizationResult` to include:
     * `error_summary: ErrorSummary`
     * `timing_info: Dict[str, float]` (e.g., total_elapsed, avg_per_trial)
     * `was_interrupted: bool`

## Testing Strategy

A robust testing strategy is crucial for the error handling components.

**Focus:** Unit test the `_run_single_trial` method in `meqsap_optimizer.engine`.

**Methodology:**
1.  **Use `pytest.mark.parametrize`:** Create test cases for each expected failure type (`DataError`, `CalculationError`, `ValidationError`, `Exception`).
2.  **Use `pytest-mock`'s `mocker`:**
    *   In each test case, patch (`mocker.patch`) the `run_complete_backtest` function.
    *   Configure the mock to `side_effect` the desired exception (e.g., `mock_backtest.side_effect = DataError("Insufficient data")`).
3.  **Use `pytest`'s `caplog` fixture:**
    *   Assert that the correct log message was emitted at the correct level (e.g., `assert "DataError" in caplog.text` and `assert caplog.records[0].levelname == "WARNING"`).
4.  **Assert the Return Value:**
    *   Assert that the `_run_single_trial` function returns the `FAILED_TRIAL_SCORE` constant when an exception is caught.
5.  **Happy Path Test:**
    *   Include a test where the mock `run_complete_backtest` returns a valid `BacktestAnalysisResult` and assert that the objective function is called and its score is returned correctly.

