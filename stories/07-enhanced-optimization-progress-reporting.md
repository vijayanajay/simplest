# Story 7: Enhanced Optimization Progress Reporting and Error Handling

**Epic:** Epic 4 - Parameter Optimization Engine (Single Indicator)  
**Story ID:** MEQSAP-007  
**Story Type:** Feature Enhancement  
**Priority:** Medium  
**Effort Estimate:** 5 Story Points  

## User Story

**As a strategist, I want real-time progress reporting during parameter optimization runs and graceful error handling for individual failed backtests, so that I can monitor long-running optimizations and understand when/why certain parameter combinations fail.**

## Business Context

This story addresses the user experience gap identified in the architecture document v2.3 for optimization runs. Long-running optimization tasks (especially Grid Search with large parameter spaces) need progress indicators and robust error handling to provide a professional, reliable experience. This aligns with the architecture's emphasis on "progress reporting mechanisms (Optuna callbacks integrated with `rich` progress bars)" and "enhanced error handling strategies within the optimization loop."

## Acceptance Criteria

### AC1: Real-time Progress Reporting
- **Given** a user runs `meqsap optimize-single` with a strategy configuration
- **When** the optimization begins
- **Then** a `rich` progress bar displays showing:
  - Current trial number / total trials (for Grid Search)
  - Current trial number / target iterations (for Random Search)
  - Best objective score found so far
  - Elapsed time and estimated time remaining
  - Current parameter combination being tested (optional, space permitting)

### AC2: Optuna Callback Integration
- **Given** the optimization engine is running trials
- **When** each trial completes (successfully or with failure)
- **Then** progress updates are driven by Optuna callbacks managed by the `cli` module
- **And** the `meqsap_optimizer.engine` integrates with Optuna's callback system to report trial completions
- **And** progress bar updates occur after each successful trial completion

### AC3: Individual Backtest Error Handling
- **Given** a parameter combination is being tested
- **When** a single backtest fails within an optimization trial (e.g., insufficient data, calculation error, invalid parameter combination)
- **Then** the optimization continues without terminating
- **And** the failed trial is logged with error details using the standard `logging` module
- **And** Optuna handles the failure appropriately (e.g., assigns poor score or `TrialPruned`)
- **And** the error does not propagate to crash the entire optimization run

### AC4: Error Reporting Summary
- **Given** an optimization run completes (successfully or via user interruption)
- **When** results are displayed
- **Then** a summary includes:
  - Total trials attempted
  - Number of successful trials
  - Number of failed trials with brief error categorization (e.g., "Data Error: 2", "Calculation Error: 1")
  - This information is displayed before the best results summary

### AC5: Graceful Termination
- **Given** a user interrupts an optimization run (Ctrl+C)
- **When** the interruption signal is received
- **Then** the optimization stops gracefully
- **And** partial results are reported if any successful trials completed
- **And** the optimization state is properly cleaned up
- **And** no corrupted files or hanging processes remain

## Technical Implementation Notes

### Architecture Alignment
This story directly implements the architecture requirements from v2.3:
- "Progress is reported to the user via `rich` progress bars, driven by Optuna callbacks managed by the `cli` module"
- "handles individual backtest failures gracefully (e.g., by logging the error and allowing Optuna to prune the trial or assign a poor score)"
- "Enhanced error handling strategies within the optimization loop"

### Implementation Approach
1. **Progress Bar Integration**: Leverage Optuna's callback system with `rich.progress.Progress`
2. **Error Handling**: Implement try-catch blocks within the optimization loop in `meqsap_optimizer.engine`
3. **Logging**: Use standard Python `logging` module for error details
4. **Signal Handling**: Implement signal handlers for graceful Ctrl+C termination

### Modified Components
- `meqsap.cli` - Add progress bar initialization and callback management
- `meqsap_optimizer.engine` - Integrate Optuna callbacks and error handling
- `meqsap.exceptions` - Ensure appropriate custom exceptions exist
- `meqsap.reporting` - Include error summary in optimization results

## Detailed Task Breakdown

### Task 1: Implement Optuna Progress Callback System
**Module:** `meqsap_optimizer.engine`  
**Effort:** 1.5 Story Points  
**Dependencies:** Epic 4 Stories 1-6

#### Sub-tasks:
1.1. **Create OptimizationProgressCallback class**
   - Implement `optuna.study.StudyProgressCallback` interface
   - Track trial completion, best score, elapsed time
   - Expose progress data via properties for CLI consumption
   - Handle both successful and failed trials

1.2. **Integrate callback with OptimizationEngine**
   - Modify `OptimizationEngine.run_optimization()` to accept progress callback
   - Register callback with Optuna study
   - Ensure callback receives trial results and updates internal state

1.3. **Add trial failure classification**
   - Define error categories: `DataError`, `CalculationError`, `ValidationError`, `UnknownError`
   - Track failed trial counts by category within callback
   - Expose error summary data for reporting

#### Implementation Details:
```python
# meqsap_optimizer/engine.py
import optuna
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum

class TrialFailureType(Enum):
    DATA_ERROR = "Data Error"
    CALCULATION_ERROR = "Calculation Error" 
    VALIDATION_ERROR = "Validation Error"
    UNKNOWN_ERROR = "Unknown Error"

@dataclass
class ProgressData:
    current_trial: int
    total_trials: Optional[int]  # None for RandomSearch
    best_score: Optional[float]
    elapsed_seconds: float
    failed_trials: Dict[TrialFailureType, int]
    current_params: Dict[str, Any]

class OptimizationProgressCallback:
    def __call__(self, study: optuna.Study, trial: optuna.Trial) -> None:
        # Update progress data, classify failures, expose via properties
```

### Task 2: Implement CLI Progress Bar Management
**Module:** `meqsap.cli`  
**Effort:** 1.0 Story Points  
**Dependencies:** Task 1

#### Sub-tasks:
2.1. **Create progress bar factory function**
   - Initialize `rich.progress.Progress` with appropriate columns
   - Configure task for Grid Search (known total) vs Random Search (indefinite)
   - Return progress bar instance and task ID

2.2. **Integrate progress bar with optimize-single command**
   - Initialize progress bar before calling optimization engine
   - Pass progress callback that updates rich progress bar
   - Handle progress bar lifecycle (start, update, complete, cleanup)

2.3. **Implement progress update logic**
   - Create callback function that receives progress data from optimization engine
   - Update rich progress bar with current trial, best score, elapsed time
   - Handle parameter display (truncate if too long for terminal width)

#### Implementation Details:
```python
# meqsap/cli.py
from rich.progress import Progress, TaskID, BarColumn, TextColumn, TimeElapsedColumn
from typing import Callable, Optional

def create_optimization_progress_bar(algorithm: str, total_trials: Optional[int]) -> tuple[Progress, TaskID]:
    # Configure columns based on algorithm type
    # Return progress instance and task ID

def create_progress_callback(progress: Progress, task_id: TaskID) -> Callable:
    # Return callback function that updates rich progress bar
    # Handle parameter display truncation
```

### Task 3: Implement Robust Error Handling in Optimization Loop
**Module:** `meqsap_optimizer.engine`  
**Effort:** 1.5 Story Points  
**Dependencies:** Task 1, Epic 4 Stories 3-4

#### Sub-tasks:
3.1. **Enhance OptimizationEngine with error handling**
   - Wrap `run_complete_backtest` calls in try-catch blocks
   - Classify exceptions into failure types (Data, Calculation, Validation, Unknown)
   - Log detailed error information with trial parameters
   - Allow Optuna to handle failed trials appropriately

3.2. **Implement trial failure recovery strategies**
   - For data errors: log and continue (let Optuna prune or assign poor score)
   - For calculation errors: log parameters causing issue, continue
   - For validation errors: log invalid parameter combination, continue
   - For unknown errors: log full traceback, continue

3.3. **Add error state tracking**
   - Track error counts by type within optimization session
   - Preserve error details for final reporting
   - Ensure optimization continues unless all trials fail

#### Implementation Details:
```python
# meqsap_optimizer/engine.py
def _run_single_trial(self, trial: optuna.Trial, market_data: pd.DataFrame) -> float:
    try:
        # Generate concrete parameters from trial
        concrete_params = self._generate_concrete_params(trial)
        
        # Run backtest
        result = run_complete_backtest(concrete_params, market_data)
        
        # Evaluate with objective function
        score = self.objective_function(result, self.objective_params)
        return score
        
    except DataError as e:
        logger.warning(f"Trial {trial.number} failed due to data error: {e}")
        self.progress_callback.record_failure(TrialFailureType.DATA_ERROR, trial.params)
        return float('-inf')  # Or raise optuna.TrialPruned()
        
    except CalculationError as e:
        logger.warning(f"Trial {trial.number} failed due to calculation error: {e}")
        self.progress_callback.record_failure(TrialFailureType.CALCULATION_ERROR, trial.params)
        return float('-inf')
        
    # ... handle other exception types
```

### Task 4: Implement Graceful Interruption Handling
**Module:** `meqsap.cli`, `meqsap_optimizer.engine`  
**Effort:** 0.5 Story Points  
**Dependencies:** Task 2, Task 3

#### Sub-tasks:
4.1. **Add signal handler for SIGINT (Ctrl+C)**
   - Register signal handler in CLI before starting optimization
   - Set flag to gracefully stop optimization loop
   - Ensure cleanup of progress bar and optimization state

4.2. **Implement graceful termination in optimization engine**
   - Check interruption flag during optimization loop
   - Allow current trial to complete before stopping
   - Return partial results if any successful trials completed

4.3. **Add interruption reporting**
   - Display message indicating graceful interruption
   - Show partial results summary if available
   - Clean up any temporary files or hanging processes

#### Implementation Details:
```python
# meqsap/cli.py
import signal
import threading

class OptimizationInterruptHandler:
    def __init__(self):
        self.interrupted = threading.Event()
        
    def __enter__(self):
        signal.signal(signal.SIGINT, self._handle_interrupt)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        
    def _handle_interrupt(self, signum, frame):
        print("\n[yellow]Optimization interrupted. Finishing current trial...[/yellow]")
        self.interrupted.set()
```

### Task 5: Enhance Optimization Results Reporting
**Module:** `meqsap.reporting`, `meqsap_optimizer.models`  
**Effort:** 0.5 Story Points  
**Dependencies:** Task 1, Task 3

#### Sub-tasks:
5.1. **Extend OptimizationResult model**
   - Add error summary fields (trial counts by failure type)
   - Add timing information (total elapsed, average time per trial)
   - Add interruption status flag

5.2. **Enhance optimization summary display**
   - Include error summary in terminal output
   - Show trial completion statistics
   - Display timing information
   - Indicate if optimization was interrupted

5.3. **Update PDF report generation for optimized strategies**
   - Ensure `--report` flag works with `optimize-single`
   - Include optimization metadata in PDF
   - Show parameter search space and final selected values

#### Implementation Details:
```python
# meqsap_optimizer/models.py
@dataclass
class OptimizationSummary:
    total_trials: int
    successful_trials: int
    failed_trials_by_type: Dict[TrialFailureType, int]
    total_elapsed_seconds: float
    avg_time_per_trial: float
    was_interrupted: bool
    algorithm_used: str

# meqsap/reporting.py
def display_optimization_summary(result: OptimizationResult) -> None:
    # Enhanced terminal output with error summary
    # Progress indicators and timing information
```

## Definition of Done

- [ ] Progress bars display during `optimize-single` runs
- [ ] Individual backtest failures don't crash the optimization
- [ ] Error summary is provided at optimization completion
- [ ] Graceful interruption (Ctrl+C) works correctly
- [ ] Unit tests cover error handling scenarios
- [ ] Integration tests verify progress reporting functionality
- [ ] All existing tests continue to pass
- [ ] Code follows project style guidelines and type hints
- [ ] Documentation updated for new error handling behavior
- [ ] Progress reporting works for both Grid Search and Random Search
- [ ] Error categorization is accurate and helpful
- [ ] Signal handling doesn't interfere with normal operation
- [ ] Progress bar displays parameter information when space permits
- [ ] Optimization state is properly cleaned up on interruption

## Dependencies

**Prerequisite Stories:**
- Story 1: Enhanced BacktestResult with trade duration statistics
- Story 2: ObjectiveFunction framework 
- Story 3: Grid Search and Random Search algorithms
- Story 4: OptimizationEngine core
- Story 5: CLI command `optimize-single`

**Technical Dependencies:**
- `rich` library for progress bars
- `Optuna` callback system
- Standard Python `logging` and `signal` modules

## Test Scenarios

### Happy Path
1. **Grid Search with Progress**: Run optimization with known parameter count, verify progress bar shows correct totals
2. **Random Search with Progress**: Run optimization with iteration limit, verify indefinite progress display
3. **Complete optimization with summary**: Verify error summary shows all successful trials when no errors occur

### Error Scenarios  
1. **Data errors during optimization**: Some backtests fail due to insufficient data - optimization continues, errors are categorized
2. **Calculation errors**: Invalid parameter combination causes calculation error - logged and skipped appropriately
3. **Mixed error types**: Multiple failure types occur during single optimization run - correct categorization in summary

### Interruption Scenarios
1. **Graceful interruption mid-run**: User presses Ctrl+C - current trial completes, partial results displayed
2. **Interruption with no completed trials**: User interrupts before any trials complete - appropriate message shown
3. **Interruption cleanup**: Verify no hanging processes or corrupted files after interruption

### Edge Cases
1. **All trials fail**: Appropriate error message and empty results handling
2. **Very quick optimization**: Progress bar functions correctly for fast optimizations
3. **Long parameter names**: Parameter display truncation works correctly for terminal width
4. **Very slow trials**: Progress bar remains responsive during long individual backtests

## Future Considerations

- **Parallel Execution**: This story's error handling design will be foundation for future parallel optimization
- **Persistence**: Error logs could be enhanced to support optimization resumption in future phases
- **Advanced Progress**: Could be extended to show parameter space exploration visualization
- **Performance Monitoring**: Progress reporting could include memory usage and system resource monitoring
- **Remote Monitoring**: Progress callbacks could be extended to support remote monitoring interfaces

## Story Dependencies & Relationships

**Blocks:** None (this is a UX enhancement)  
**Blocked By:** Stories 1-6 from Epic 4  
**Related:** All Epic 4 stories (enhances their user experience)

## Risk Mitigation

**Risk 1: Progress reporting performance overhead**
- *Mitigation*: Keep progress updates lightweight, update frequency limited to once per trial
- *Fallback*: Option to disable progress reporting with `--no-progress` flag

**Risk 2: Signal handling conflicts**
- *Mitigation*: Careful signal handler registration/cleanup, use context managers
- *Fallback*: Graceful degradation if signal handling fails

**Risk 3: Error categorization accuracy**
- *Mitigation*: Conservative categorization, comprehensive exception handling tests
- *Fallback*: "Unknown Error" category for unclassified exceptions

## Validation Criteria

- [ ] Progress bars update correctly without impacting optimization performance
- [ ] Error handling maintains optimization robustness while providing useful feedback
- [ ] Interruption handling preserves data integrity and provides meaningful results
- [ ] All error categories are properly tested with representative failure scenarios
- [ ] Progress reporting adapts correctly to different terminal sizes and capabilities
