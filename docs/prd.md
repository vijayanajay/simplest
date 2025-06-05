# MEQSAP Product Requirements Document (PRD) - v2.2

## Version History

*   **v2.2 (June 5, 2025):** Incorporates Phase 2 of the Automated Strategy Discovery roadmap.
    *   Introduced a Parameter Optimization Engine for single-indicator strategies.
    *   Added an objective function framework, with initial support for standard metrics and a crucial focus on incorporating target trade holding period constraints.
    *   Implemented initial optimization algorithms: Grid Search and Random Search.
    *   New CLI command `meqsap optimize-single` to invoke the optimization.
    *   Enhanced `BacktestResult` to include trade duration statistics.
    *   Updated reporting to summarize optimization outcomes, including adherence to constraints.
    *   Added **Epic 4: Parameter Optimization Engine (Single Indicator)**.
    *   Updated User Stories, Functional Requirements, Non-Functional Requirements (Modularity for `meqsap_optimizer`), and Technical Assumptions.
*   **v2.1 (June 4, 2025):** Incorporates Phase 1 of the Automated Strategy Discovery roadmap.
    *   Enhanced parameter definition framework supporting ranges, choices, and steps for strategy parameters.
    *   Refactored `BaseStrategyParams`, `StrategyConfig`, and `StrategySignalGenerator` to accommodate the new parameterization.
    *   Introduced the design and planned integration of the `meqsap_indicators_core` library for modular indicator management.
    *   Added **Epic 3: Enhanced Parameterization Framework for Optimization Readiness**.
*   **v2.0 (Initial Release Date):** Initial MVP definition for core backtesting pipeline and reporting.

## 1. Goal, Objective, and Context

*   **Goal:** To build a command-line tool, the Minimum Viable Quantitative Strategy Analysis Pipeline (MEQSAP), that can take a simple strategy configuration file, run a complete backtest, perform robustness checks, and present a clear, actionable verdict. The system is evolving to support automated strategy optimization and more advanced analysis capabilities.
*   **Objective:** The core principle remains to rapidly develop an end-to-end "happy path" by orchestrating powerful, existing Python libraries. Version 2.1 established a flexible parameter definition framework. **Version 2.2 introduces a parameter optimization engine for single-indicator strategies**, allowing users to automatically find optimal parameters based on defined objectives, including constraints like target trade holding periods. This focuses on delivering a practical first step in optimization, leveraging the modularity already built.
*   **Context:** This project is for a user who wants to quickly and reliably analyze and now *optimize* quantitative trading strategies using a simple, configuration-driven CLI tool. The v2.1 enhancements prepared for this optimization step.

## 2. User Stories

1.  As a strategist, I want to define a trading strategy (e.g., a moving average crossover) in a simple `.yaml` file, including the ability to specify single values for parameters, **so that** I can configure a backtest without writing any Python code. (No change from v2.1)
2.  As a strategist, I want the tool to validate my `.yaml` configuration against a predefined schema, including new parameter space definitions and optimization settings, **so that** I am immediately alerted to typos or invalid parameter combinations. (Acceptance Criteria updated for v2.2)
3.  As a strategist, I want the tool to automatically download the necessary historical price data for a given ticker **so that** I don't have to manage data files manually. (No change from v2.0)
4.  As a strategist, I want the tool to cache downloaded data **so that** subsequent runs on the same data are fast and don't repeatedly call the data provider's API. (No change from v2.0)
5.  As a strategist, I want the tool to run a complete backtest on my defined strategy (using specific parameter values if ranges/choices are defined, or default/first values if not optimizing via the `analyze` command) using a single command **so that** I can see its performance statistics. (Clarified for v2.2)
6.  As a strategist, I want to see a clean, formatted "Executive Verdict" table in my terminal **so that** I can quickly assess the strategy's performance and the results of all validation checks. (No change from v2.0)
7.  As a strategist, I want the tool to automatically perform "Vibe Checks" **so that** I can instantly spot obviously flawed or inactive strategies. (No change from v2.0)
8.  As a strategist, I want the tool to run automated robustness checks **so that** I can understand how sensitive my strategy is to real-world costs. (No change from v2.0)
9.  As a strategist, I want the option to generate a comprehensive, institutional-grade PDF report using a command-line flag (`--report`) **so that** I can perform a deeper analysis or share the results. (No change from v2.0)
10. As a developer, I want the tool to provide clear, user-friendly error messages (e.g., for a bad ticker, malformed config file, errors in parameter space definitions, or optimization failures) **so that** users can self-diagnose and fix problems easily. (Acceptance Criteria updated for v2.2)
11. As a strategist, I want to define parameter search spaces (e.g., ranges, choices, steps) for my strategy indicators within the `.yaml` configuration file **so that** I can prepare my strategy for automated parameter optimization. (No change from v2.1)
12. **(NEW for v2.2) As a strategist, I want to define an objective function (e.g., maximize Sharpe Ratio) and constraints (e.g., average trade hold period between 5 and 20 days) in my YAML configuration so that the system can optimize parameters towards my specific goals.**
13. **(NEW for v2.2) As a strategist, I want to run an automated parameter optimization for a single-indicator strategy using Grid Search or Random Search via a new CLI command (e.g., `meqsap optimize-single`) so that I can discover better performing parameter sets without manual trial and error.**
14. **(NEW for v2.2) As a strategist, I want to see a report of the optimization process, including the best parameters found, their performance, and how well they met constraints like hold periods, so that I can understand the outcome of the optimization.**
15. **(NEW for v2.2) As a developer, I want the `BacktestResult` to include detailed trade duration statistics (e.g., average hold time, percentage of trades within a target range) so that objective functions can use this information for optimization.**

## 3. Functional Requirements

The system must be able to:

*   **Strategy Configuration (Updates for v2.2):**
    1.  Load a backtest strategy from a `.yaml` configuration file. The configuration can include fixed parameters, parameter search spaces (from v2.1), and a new **`optimization_config` block**.
    2.  The `optimization_config` block (optional) allows specifying:
        *   `active`: boolean to enable/disable optimization for a run.
        *   `algorithm`: Choice of optimization algorithm (e.g., "GridSearch", "RandomSearch").
        *   `objective_function`: Name of the objective function to use (e.g., "SharpeRatio", "CalmarRatio", or custom ones like "SharpeWithHoldPeriodConstraint").
        *   `objective_params`: Parameters for the objective function, such as `min_hold_days`, `max_hold_days`.
        *   `algorithm_params`: Parameters specific to the chosen algorithm (e.g., `random_search_iterations`).
    3.  Validate the loaded configuration, including the `optimization_config` block and its parameters.
    4.  (No change from v2.1) Interpret parameter definitions within `BaseStrategyParams` supporting fixed values, ranges, choices.
    5.  (No change from v2.1) Ensure `get_required_data_coverage_bars` correctly calculates data length considering parameter ranges.

*   **Data Handling:** (No change from v2.1)
    6.  Acquire historical OHLCV data via `yfinance`.
    7.  Implement file-based caching.
    8.  Perform data integrity "Vibe Checks".

*   **Backtesting Core (Updates for v2.2):**
    9.  (No change from v2.1) Generate entry and exit signals. `StrategySignalGenerator` accepts concrete parameter sets.
    10. (No change from v2.1) Execute a full backtest using `vectorbt`.
    11. **(New for v2.2)** The `BacktestResult` Pydantic model (in `meqsap.backtest`) must be enhanced to include:
        *   `avg_trade_duration_days: Optional[float]`
        *   `pct_trades_in_target_hold_period: Optional[float]` (if target hold period is defined)
        *   Other relevant trade duration statistics as needed by objective functions.
        *   These statistics are to be calculated from the `trade_details` list within the `run_backtest` function or a helper.

*   **Parameter Optimization Engine (New for v2.2):**
    12. Implement a new module, `meqsap_optimizer`, responsible for parameter optimization.
    13. The engine must take a `StrategyConfig` (with parameter search spaces from `meqsap_indicators_core` and `optimization_config`), an objective function, and a chosen algorithm.
    14. Implement **Grid Search**: Systematically iterate through all combinations in the defined parameter space.
    15. Implement **Random Search**: Randomly sample a specified number of combinations from the parameter space.
    16. For each parameter combination, the engine must call `run_complete_backtest` to get a full `BacktestAnalysisResult`.
    17. Evaluate the `BacktestAnalysisResult` against the specified objective function.
    18. Track and identify the best-performing parameter set according to the objective function.

*   **Objective Function Framework (New for v2.2):**
    19. Create a system within `meqsap_optimizer` for defining and selecting objective functions.
    20. Implement standard objective functions: Maximize Sharpe Ratio, Maximize Calmar Ratio, Maximize Profit Factor.
    21. Implement at least one objective function that incorporates trade holding period constraints. This function will use the new trade duration statistics from `BacktestResult` and penalize or filter out parameter sets where trades predominantly fall outside the user-defined `min_hold_days` and `max_hold_days`.

*   **Results & Reporting (Updates for v2.2):**
    22. (No change from v2.1) Print core performance statistics.
    23. (No change from v2.1) Perform "Vibe Checks".
    24. (No change from v2.1) Conduct automated robustness "Vibe Checks".
    25. (No change from v2.1) Display formatted "Executive Verdict" using `rich`.
    26. (No change from v2.1) Generate PDF report via `pyfolio` with `--report`.
    27. **(New for v2.2)** When optimization is run:
        *   Output the best parameter set found.
        *   Output the full `BacktestAnalysisResult` (including Executive Verdict) for this best parameter set.
        *   Provide a summary of the optimization process (e.g., algorithm used, number of iterations, best objective score).
        *   Clearly report on how well the best parameter set met the specified constraints, especially the target hold period.

*   **Modular Indicator Management:** (No change from v2.1, `meqsap_indicators_core` is foundational)
    28. Utilize `meqsap_indicators_core` for standardized indicator definition, parameter management, and calculation logic.

*   **CLI & Diagnostics (Updates for v2.2):**
    29. **(New for v2.2)** Implement a new CLI command: `meqsap optimize-single <config.yaml>`.
        *   This command reads the `optimization_config` block from the YAML.
        *   It invokes the `OptimizationEngine`.
    30. (No change from v2.1) Provide `--verbose` and `--version` flags.

## 4. Non-Functional Requirements

*   **Reliability:** (No change) Consistent, reproducible results.
*   **Modularity & Maintainability:** (Enhanced for v2.2)
    *   The new `meqsap_optimizer` module will encapsulate all optimization-specific logic, maintaining separation from core backtesting, data, and config modules.
*   **Code Quality:** (No change) Pydantic for validation, Python type hints.
*   **Dependency Management:** (No change) Explicitly defined and frozen.
*   **Performance:**
    *   Individual backtests within the optimization loop must remain efficient.
    *   Optimization runs (especially Grid Search) can be time-consuming; this is acceptable for v2.2. Progress indicators should be provided for long-running optimization tasks.
*   **Packaging:** (No change) Distributable via PyPI.

## 5. Technical Assumptions

*   **Repository & Service Architecture:** (No change) Monolith, single repository.
*   **Core Libraries:** (Updated for v2.2) `yfinance`, `vectorbt`, `pyyaml`, `pydantic`, `pandas`, `pandas-ta`, `rich`, `pyfolio`. The `meqsap_indicators_core` module is established.
    *   **New for v2.2:** A new internal library/module, `meqsap_optimizer`, will be developed. It will house algorithms (Grid Search, Random Search), objective function definitions, and the main optimization engine logic.
*   **Language:** (No change) Python 3.9+.
*   **Platform:** (No change) Command-line tool.

## 6. Epic Overview

**Epic 1: Core Backtesting Pipeline (MVP Foundation)** (Completed in v2.0)
**Epic 2: Analysis, Reporting & UX (MVP Enhancement)** (Completed in v2.0)
**Epic 3: Enhanced Parameterization Framework for Optimization Readiness** (Completed in v2.1)

**(NEW for v2.2) Epic 4: Parameter Optimization Engine (Single Indicator)**
*   **Goal:** To implement an automated parameter optimization engine for single-indicator strategies, enabling users to find optimal parameters based on defined objectives and constraints, particularly target trade holding periods.
*   **User Stories for Epic 4:**
    1.  **As a developer, I want to enhance `BacktestResult` to include detailed trade duration statistics** (e.g., average hold time, percentage of trades within a target range) **so that** this data is available for objective functions.
        *   **Acceptance Criteria:**
            *   AC1: `BacktestResult` Pydantic model in `meqsap.backtest.py` includes new fields like `avg_trade_duration_days: Optional[float]` and `pct_trades_in_target_hold_period: Optional[float]`.
            *   AC2: The `run_backtest` function calculates and populates these new duration statistics from `vectorbt`'s trade records.
            *   AC3: Unit tests verify the correct calculation of these duration statistics.
    2.  **As a developer, I want to create an `ObjectiveFunction` framework within `meqsap_optimizer`** that allows defining various optimization goals (e.g., Sharpe Ratio, Calmar Ratio) and can incorporate constraints like target trade hold periods, **so that** the optimization process can be guided by specific criteria.
        *   **Acceptance Criteria:**
            *   AC1: An `ObjectiveFunction` base class or protocol is defined in `meqsap_optimizer.objective_functions`.
            *   AC2: Implementations for standard objectives like "Maximize Sharpe Ratio" and "Maximize Calmar Ratio" are provided.
            *   AC3: At least one objective function (e.g., "SharpeWithHoldPeriodConstraint") is implemented that uses the new trade duration statistics from `BacktestResult` to penalize or filter strategies not meeting hold period criteria specified in `optimization_config.objective_params`.
            *   AC4: The framework allows for easy addition of new objective functions.
    3.  **As a developer, I want to implement Grid Search and Random Search algorithms** within the `meqsap_optimizer.algorithms` submodule, **so that** users have basic methods to explore parameter spaces defined via `meqsap_indicators_core`.
        *   **Acceptance Criteria:**
            *   AC1: `GridSearchOptimizer` class/function correctly generates all parameter combinations from the defined space.
            *   AC2: `RandomSearchOptimizer` class/function correctly samples a specified number of combinations.
            *   AC3: Both optimizers can correctly interpret parameter spaces (ranges, choices) from `StrategyConfig` (which uses `meqsap_indicators_core` definitions).
    4.  **As a developer, I want to build an `OptimizationEngine` core within `meqsap_optimizer.engine`** that orchestrates the optimization process. It should take a strategy configuration, an objective function, and an algorithm, then run backtests for parameter combinations and identify the best set, **so that** the optimization workflow is managed.
        *   **Acceptance Criteria:**
            *   AC1: `OptimizationEngine` can be initialized with a `StrategyConfig` (containing parameter spaces and `optimization_config`), a selected objective function instance, and a selected algorithm instance.
            *   AC2: The engine correctly iterates/samples parameter sets using the chosen algorithm.
            *   AC3: For each parameter set, the engine calls `run_complete_backtest` (from `meqsap.backtest`) to get `BacktestAnalysisResult`.
            *   AC4: The engine evaluates each `BacktestAnalysisResult` using the provided objective function.
            *   AC5: The engine tracks and returns the parameter set that yielded the best objective score.
    5.  **As a strategist, I want a new CLI command `meqsap optimize-single <config.yaml>`** to initiate the parameter optimization for a single-indicator strategy, using settings from the YAML's `optimization_config` block, **so that** I can easily run optimizations.
        *   **Acceptance Criteria:**
            *   AC1: A new command `optimize-single` is added to `meqsap.cli.py`.
            *   AC2: The command accepts a path to a YAML configuration file.
            *   AC3: The command loads the YAML, extracts `StrategyConfig` and the `optimization_config` block.
            *   AC4: It initializes and runs the `OptimizationEngine` based on these configurations.
            *   AC5: Appropriate error handling for invalid or missing `optimization_config`.
    6.  **As a strategist, I want the `optimize-single` command to report** the best parameters found, their full backtest performance (Executive Verdict), a summary of the optimization run, and how well constraints (especially hold period) were met, **so that** I can understand and use the optimization results.
        *   **Acceptance Criteria:**
            *   AC1: CLI output for `optimize-single` clearly states the best parameter set found.
            *   AC2: The full "Executive Verdict" (from `meqsap.reporting`) for the best parameter set is displayed.
            *   AC3: A summary of the optimization is provided (e.g., "GridSearch tested 100 combinations. Best Sharpe: 1.25").
            *   AC4: If hold period constraints were active, the report explicitly states the average hold period and % trades in range for the best strategy.
            *   AC5: If `--report` flag is used with `optimize-single`, a PDF report for the *best found strategy* is generated.

## 7. Explicitly Out of Scope for v2.2

To ensure focus, the following are **not** part of the v2.2 update:

*   **Advanced Optimization Algorithms:** Bayesian optimization, Genetic Algorithms, PSO (these are planned for later phases as per roadmap). v2.2 focuses on Grid and Random Search.
*   **Optimization for Multi-Signal/Indicator Strategies:** Phase 2 is strictly for single-indicator strategies where parameters are directly tied to one indicator's definition (e.g., optimizing `fast_ma` and `slow_ma` for `MovingAverageCrossover`). Combined strategy optimization is Phase 6.
*   **Automated Strategy Discovery/Modification:** The "Strategy Doctor" concept (Phase 8) is out of scope. This phase only finds optimal parameters for a *given* strategy structure.
*   **Sophisticated UI for Optimization:** All interactions are CLI-driven.
*   **Distributed/Parallel Execution of Optimization:** While desirable for performance, implementing robust parallel execution for optimization runs is a separate effort, deferred to keep v2.2 focused. The underlying `run_complete_backtest` should remain efficient.
*   **Optimization State Persistence & Resumption:** The ability to interrupt and resume long optimization runs is out of scope for this phase. Each `optimize-single` run is self-contained.
*   **Out-of-Sample/Walk-Forward Validation within Optimization Loop:** While important, integrating these complex validation schemes directly into the v2.2 optimization loop is deferred. The focus is on in-sample optimization first. Standard robustness checks will still apply to the *best found* strategy.
