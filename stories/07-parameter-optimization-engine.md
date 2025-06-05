<!-- Status: ToDo -->
# Story: Parameter Optimization Engine (Single Indicator) - Phase 2

## Description
Implement an automated parameter optimization engine specifically focused on **single-indicator strategies** that can find optimal parameters based on configurable objective functions. This story builds upon the enhanced parameter definition framework from Phase 1 and introduces the capability to automatically explore parameter spaces defined in YAML configurations, evaluate strategy performance across different parameter combinations, and recommend optimal parameter sets that respect specified constraints (such as target holding periods).

The optimization engine will support Grid Search and Random Search algorithms and allow users to define objective functions including the specific "SharpeWithHoldPeriodConstraint" objective function. This represents a practical first step toward automated strategy discovery while maintaining the modularity and reliability principles of the MEQSAP architecture, with clear focus on single-indicator strategies to establish the optimization foundation.

## Epic Overview
This story implements **Phase 2** of the Automated Strategy Discovery roadmap, focusing specifically on **single-indicator strategy optimization**. It introduces:

- **Objective Function Framework**: Configurable optimization targets including the specific "SharpeWithHoldPeriodConstraint" objective function
- **Parameter Space Exploration**: Automated exploration of parameter ranges and choices defined in Phase 1 for single-indicator strategies
- **Optimization Algorithm Suite**: Grid Search and Random Search algorithms with different trade-offs
- **Constraint Handling**: Support for holding period constraints and other business rules with detailed adherence metrics
- **Results Analysis**: Comprehensive reporting of optimization results with constraint adherence metrics (especially hold period stats)
- **Progress Indicators**: Real-time progress indicators for long-running optimization processes
- **Trade Duration Statistics**: Mandatory trade duration statistics in BacktestResult to support constraint evaluation

## Acceptance Criteria

### Core Optimization Engine
1. **AC1**: `meqsap_optimizer` module provides a clean API for single-indicator strategy parameter optimization
2. **AC2**: Support for Grid Search and Random Search algorithms as the primary optimization methods
3. **AC3**: Configurable objective functions including Sharpe ratio and the specific "SharpeWithHoldPeriodConstraint" objective function
4. **AC4**: Parameter space exploration respects parameter definitions from `meqsap_indicators_core` for single-indicator strategies
5. **AC5**: Optimization process provides real-time progress indicators for long-running operations

### Objective Function Framework
6. **AC6**: `ObjectiveFunction` abstract base class allows custom optimization targets with constraint integration
7. **AC7**: Built-in "SharpeWithHoldPeriodConstraint" objective function balances risk-adjusted returns with holding period constraints
8. **AC8**: Objective functions incorporate constraints (e.g., target trade holding periods between 5 and 20 days)
9. **AC9**: Constraint adherence metrics are calculated and reported, especially for hold period statistics

### Integration and Configuration
10. **AC10**: YAML configuration supports `optimization_config` blocks with algorithm selection and objective function definitions
11. **AC11**: CLI includes `optimize-single` sub-command for running single-indicator strategy parameter optimization
12. **AC12**: Optimization respects existing configuration validation and error handling patterns with user-friendly error messages
13. **AC13**: Integration with existing `meqsap.backtest` module for strategy evaluation with enhanced trade duration statistics

### Results and Reporting
14. **AC14**: Optimization results include constraint adherence metrics with detailed hold period statistics
15. **AC15**: Results reporting shows parameter sensitivity analysis and optimization progress
16. **AC16**: Best parameter sets include validation of constraint satisfaction (especially holding periods)
17. **AC17**: Optimization history is saved with detailed constraint adherence tracking

### Performance and Error Handling
18. **AC18**: Clear error handling strategies for failures within optimization loops with user-friendly messages
19. **AC19**: Memory-efficient handling of single-indicator parameter spaces
20. **AC20**: Support for graceful interruption and resumption of optimization processes
21. **AC21**: BacktestResult includes mandatory trade duration statistics (average hold time, percentage within target range)

## Implementation Details

### meqsap_optimizer Module Architecture
Create `src/meqsap/optimizer/` as a new package containing:

#### Core Optimization Engine
- **`OptimizationEngine`**: Main orchestrator class managing optimization workflows
- **`ParameterSpace`**: Class for defining and sampling parameter search spaces
- **`ObjectiveFunction`**: Abstract base class for optimization targets
- **`OptimizationResult`**: Comprehensive results container with statistical analysis

#### Optimization Algorithms
- **`GridSearchOptimizer`**: Exhaustive grid search implementation for single-indicator strategies
- **`RandomSearchOptimizer`**: Random sampling with configurable distribution for single-indicator strategies
- **`OptimizationFactory`**: Factory pattern for algorithm selection (Grid Search and Random Search)

#### Objective Functions
- **`SharpeRatioObjective`**: Risk-adjusted return optimization
- **`SharpeWithHoldPeriodConstraint`**: Specific objective function balancing Sharpe ratio with holding period constraints
- **`CustomObjective`**: Framework for user-defined objective functions via configuration

#### Trade Duration and Constraint Tracking
- **`TradeDurationAnalyzer`**: Component to calculate mandatory trade duration statistics
- **`ConstraintEvaluator`**: Component to assess constraint adherence, especially for holding periods
- **`ProgressTracker`**: Component to provide real-time progress indicators during optimization

### Configuration Schema Extensions
Extend YAML configuration to support optimization blocks:

```yaml
strategy_config:
  ticker: "TCS.NS"
  start_date: "2020-01-01"
  end_date: "2023-12-31"
  strategy_type: "MovingAverageCrossover"
  parameters:
    fast_ma:
      range: [5, 50, 1]
    slow_ma:
      range: [20, 200, 5]

optimization_config:
  algorithm: "grid_search"  # grid_search, random_search
  objective: "sharpe_with_hold_period_constraint"  # sharpe_ratio, sharpe_with_hold_period_constraint
  constraints:
    target_hold_period_days: [5, 20]  # Min and max holding period in days
    min_trades: 50
  algorithm_params:
    max_iterations: 100  # For random_search
    progress_update_frequency: 10  # Progress indicator frequency
  error_handling:
    max_failures: 10  # Maximum optimization failures before stopping
    continue_on_constraint_violation: true
```

### CLI Integration
Enhance `src/meqsap/cli.py` with `optimize-single` sub-command:

```python
@app.command("optimize-single")
def optimize_single(
    config_file: Path,
    algorithm: str = typer.Option("grid_search", help="Optimization algorithm (grid_search, random_search)"),
    max_iterations: int = typer.Option(100, help="Maximum optimization iterations"),
    show_progress: bool = typer.Option(True, help="Show real-time progress indicators"),
    output_dir: Path = typer.Option("optimization_results", help="Results output directory"),
    verbose: bool = typer.Option(False, help="Verbose optimization logging")
):
    """Run parameter optimization for single-indicator strategy configuration."""
```

### Core Functions

#### `run_single_indicator_optimization(config: StrategyConfig, optimization_config: OptimizationConfig) -> OptimizationResult`
- Orchestrate the complete optimization workflow for single-indicator strategies
- Handle parameter space generation from configuration
- Execute chosen optimization algorithm (Grid Search or Random Search)
- Provide real-time progress indicators for long-running processes
- Generate comprehensive optimization report with constraint adherence metrics

#### `evaluate_parameter_set(params: Dict, config: StrategyConfig) -> ObjectiveValue`
- Evaluate a single parameter combination for single-indicator strategies
- Run backtest with specified parameters including mandatory trade duration statistics
- Calculate objective function value with constraint consideration
- Handle constraint violations with clear error messages
- Support for holding period constraint evaluation

#### `generate_optimization_report(result: OptimizationResult, output_dir: Path) -> None`
- Create detailed optimization analysis report with constraint adherence metrics
- Include parameter sensitivity analysis for single-indicator strategies
- Show optimization progress and convergence information
- Display constraint adherence statistics, especially hold period metrics
- Generate recommendations for parameter selection with constraint satisfaction

### Technical Implementation Requirements

#### Optimization Algorithms
- **Grid Search**: Systematic exploration of parameter grid for single-indicator strategies with progress tracking
- **Random Search**: Efficient random sampling with configurable probability distributions

#### Trade Duration and Constraint Analysis
- **Mandatory Trade Duration Statistics**: Average hold time, median hold time, percentage of trades within target range
- **Constraint Adherence Metrics**: Detailed tracking of holding period constraint satisfaction
- **Progress Indicators**: Real-time progress reporting for optimization processes

#### Error Handling and User Experience
- **Clear Error Messages**: User-friendly error messages for optimization failures as per PRD US10
- **Graceful Failure Recovery**: Handle optimization failures without losing progress
- **Progress Tracking**: Visual progress indicators for long-running optimization processes
- **Constraint Violation Handling**: Clear reporting when constraints cannot be satisfied

## Tasks Breakdown

### Module Setup and Core Infrastructure
- [ ] **Create optimizer package structure** - Set up `src/meqsap/optimizer/` with proper `__init__.py` and module organization
- [ ] **Implement ParameterSpace class** - Create parameter space definition and sampling logic using Phase 1 parameter definitions
- [ ] **Create OptimizationResult class** - Implement comprehensive results container with statistical analysis methods
- [ ] **Add optimization dependencies** - Update `requirements.txt` with scikit-optimize, joblib, and statistical analysis libraries

### Objective Function Framework
- [ ] **Implement ObjectiveFunction base class** - Create abstract interface for optimization targets with constraint handling
- [ ] **Create SharpeWithHoldPeriodConstraint objective** - Implement the specific objective function that balances Sharpe ratio with holding period constraints
- [ ] **Create basic Sharpe ratio objective** - Implement standard Sharpe ratio optimization for comparison
- [ ] **Implement constraint evaluation framework** - Add support for holding period and trading frequency constraints with detailed metrics

### Optimization Algorithms
- [ ] **Implement GridSearchOptimizer** - Create exhaustive grid search for single-indicator strategies with progress indicators
- [ ] **Implement RandomSearchOptimizer** - Add random sampling algorithm with configurable distributions and progress tracking
- [ ] **Create OptimizationFactory** - Implement factory pattern for algorithm selection (Grid Search and Random Search)
- [ ] **Add progress tracking system** - Implement real-time progress indicators for long-running optimization processes

### Configuration and CLI Integration
- [ ] **Extend YAML schema for optimization_config** - Add optimization configuration blocks to existing Pydantic models
- [ ] **Implement configuration validation** - Add validation for optimization parameters and algorithm settings with clear error messages
- [ ] **Add optimize-single CLI command** - Create new sub-command with proper argument parsing and progress indicators
- [ ] **Update configuration loading** - Enhance config module to handle optimization-specific settings

### Trade Duration and Constraint Analysis
- [ ] **Implement mandatory trade duration statistics** - Add average hold time, median hold time, percentage within target range to BacktestResult
- [ ] **Create constraint adherence metrics** - Implement detailed tracking of holding period constraint satisfaction
- [ ] **Add constraint evaluation to backtest** - Enhance backtesting to calculate and report constraint adherence
- [ ] **Implement constraint violation reporting** - Create clear reporting when constraints cannot be satisfied

### Statistical Analysis and Reporting
- [ ] **Implement constraint adherence reporting** - Add constraint satisfaction metrics to optimization results
- [ ] **Create parameter sensitivity analysis** - Implement parameter importance ranking for single-indicator strategies
- [ ] **Add progress visualization** - Create optimization progress tracking and reporting
- [ ] **Implement result persistence with constraints** - Add saving and loading of optimization results with constraint data

### Integration and Validation
- [ ] **Integrate with backtest module** - Ensure seamless integration with existing backtesting functionality and trade duration statistics
- [ ] **Add error handling for optimization loops** - Implement clear error handling strategies for failures within optimization loops
- [ ] **Create single-indicator optimization workflow** - Implement end-to-end optimization pipeline focused on single-indicator strategies
- [ ] **Add progress tracking and user feedback** - Implement progress indicators and user-friendly feedback for optimization processes

### Testing and Quality Assurance
- [ ] **Create unit tests for core classes** - Test ParameterSpace, ObjectiveFunction, and optimization algorithms (Grid Search, Random Search)
- [ ] **Implement integration tests** - Test complete single-indicator optimization workflows with various configurations
- [ ] **Add constraint adherence tests** - Test holding period constraint evaluation and reporting functionality
- [ ] **Create error handling tests** - Verify user-friendly error messages and graceful failure recovery
- [ ] **Add CLI testing for optimize-single** - Test optimize-single command with various arguments and configuration scenarios

### Documentation and Examples
- [ ] **Write module documentation** - Create comprehensive docstrings for all optimization classes and functions
- [ ] **Add single-indicator optimization examples** - Create example YAML configurations demonstrating single-indicator optimization features
- [ ] **Update architecture documentation** - Update `architecture.md` to reflect meqsap_optimizer module structure and single-indicator focus
- [ ] **Create optimization guide** - Document best practices for single-indicator parameter optimization and constraint usage
- [ ] **Add troubleshooting section** - Document common optimization issues and solutions with emphasis on constraint satisfaction

## Definition of Done
- [ ] All acceptance criteria are met and tested
- [ ] `meqsap_optimizer` module implemented with clean API focused on single-indicator strategy optimization
- [ ] Grid Search and Random Search algorithms working effectively for single-indicator strategies
- [ ] Objective function framework supports "SharpeWithHoldPeriodConstraint" and basic Sharpe ratio optimization
- [ ] YAML configuration supports `optimization_config` blocks with full validation and clear error messages
- [ ] CLI `optimize-single` command provides user-friendly parameter optimization interface with progress indicators
- [ ] Trade duration statistics are mandatory in BacktestResult and support constraint evaluation
- [ ] Constraint adherence metrics are calculated and reported, especially for holding period constraints
- [ ] Error handling provides clear, actionable messages for optimization failures within loops
- [ ] Integration with existing modules maintains architectural consistency
- [ ] Comprehensive test coverage (unit + integration + constraint adherence tests)
- [ ] Documentation updated (architecture.md, example configurations, single-indicator optimization guide)
- [ ] Progress indicators provide real-time feedback for long-running optimization processes
- [ ] Code follows project standards (type hints, naming conventions, error handling policy)
- [ ] Cross-platform compatibility verified for single-indicator optimization workflows

## Dependencies and Prerequisites
- **Depends on**: Stories 1-6 (completed foundation and enhanced parameter framework)
- **Enables**: Future stories for multi-objective optimization and automated strategy discovery
- **New Dependencies**: 
  - `scipy` for statistical analysis and constraint evaluation
  - `tqdm` for progress indicators during optimization
  - Enhanced trade duration calculation libraries if needed

## Technical Notes

### Algorithm Selection Guidelines
- **Grid Search**: Best for small parameter spaces and exhaustive exploration needs for single-indicator strategies
- **Random Search**: Efficient for larger parameter spaces with good general performance for single-indicator strategies

### Single-Indicator Strategy Focus
- Parameter optimization specifically designed for strategies with single indicators (e.g., MovingAverageCrossover)
- Parameter spaces are typically smaller and more manageable than multi-indicator strategies
- Constraint evaluation is simplified with focus on holding period and basic trading frequency metrics
- Clear foundation for future expansion to multi-indicator optimization

### Performance Considerations
- Parameter evaluation is the computational bottleneck - optimize backtest execution for single-indicator strategies
- Progress indicators should provide meaningful feedback without impacting performance
- Trade duration statistics calculation should be optimized for repeated evaluation
- Error handling should be robust for optimization loops with clear user feedback

### Constraint Implementation
- Holding period constraints are the primary constraint type supported in Phase 2
- Trade duration statistics must be calculated for every backtest to support constraint evaluation
- Constraint adherence metrics must be prominently featured in optimization results
- Clear reporting when constraints cannot be satisfied with suggested parameter adjustments

## Integration Points

### With Existing Modules
- **`meqsap.config`**: Extended to handle `optimization_config` blocks with validation for single-indicator strategies
- **`meqsap.backtest`**: Core backtesting functionality used for parameter evaluation with mandatory trade duration statistics
- **`meqsap.indicators_core`**: Parameter definitions drive optimization space generation for single-indicator strategies
- **`meqsap.cli`**: New `optimize-single` sub-command integrated with existing CLI structure and progress indicators
- **`meqsap.reporting`**: Optimization results integrated with existing reporting framework, emphasizing constraint adherence metrics

### Future Roadmap Preparation
This story prepares the foundation for:
- **Phase 3**: Baseline Definition and Comparative Analysis with single-indicator optimization results
- **Phase 4**: Multi-strategy optimization building on single-indicator optimization patterns
- **Phase 5**: Automated strategy discovery expanding from single-indicator foundations

## Notes
This story represents the first practical step in MEQSAP's evolution from manual strategy testing to automated parameter optimization, focusing specifically on single-indicator strategies to establish a solid foundation. The implementation maintains the project's core principles of modularity, reliability, and user-friendliness while introducing optimization capabilities that prepare for more sophisticated multi-indicator optimization in future phases.

The focus on single-indicator strategies allows for:
- **Simplified Parameter Spaces**: Easier to visualize and understand optimization results
- **Clear Constraint Evaluation**: Holding period constraints are straightforward to implement and validate
- **Robust Foundation**: Proven optimization patterns that can be extended to multi-indicator strategies
- **User-Friendly Experience**: Less complex optimization results that users can easily interpret

**Key Success Metrics:**
- Single-indicator optimization can find parameter sets that outperform manual parameter selection
- Constraint adherence metrics provide clear feedback on holding period satisfaction
- User workflow remains simple despite added optimization sophistication
- Progress indicators provide meaningful feedback during long-running optimization processes
- Error handling provides clear guidance when optimization fails or constraints cannot be satisfied
