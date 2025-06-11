# MEQSAP Product Requirements Document (PRD) - v2.3

## Version History

* **(NEW for v2.3) (June 11, 2025):** Incorporates Phase 3 of the Automated Strategy Discovery roadmap.
    * Introduced the concept of a baseline strategy (e.g., Buy & Hold) for comparative analysis.
    * Added `baseline_config` to the YAML configuration schema.
    * Updated the backtesting pipeline to run both the candidate strategy and the baseline strategy.
    * Enhanced terminal reporting to display a side-by-side comparison of the candidate strategy vs. the baseline.
    * Integrated the `QuantStats` library to generate comprehensive HTML reports via a new `--report-html` flag.
    * Updated `BacktestAnalysisResult` to accommodate comparative results.
    * Added **Epic 5: Baseline Comparison & Advanced Reporting**.
    * Updated User Stories, Functional Requirements, Non-Functional Requirements, and Technical Assumptions.
    * Refined requirements to include graceful baseline failure handling, an option to disable baseline comparison for faster runs, a more robust reporting architecture, and enhanced real-time CLI feedback.
* **v2.2 (June 5, 2025):** Incorporates Phase 2 of the Automated Strategy Discovery roadmap.
    * Introduced a Parameter Optimization Engine for single-indicator strategies.
    * Added an objective function framework, with initial support for standard metrics and a crucial focus on incorporating target trade holding period constraints.
    * Implemented initial optimization algorithms: Grid Search and Random Search.
    * New CLI command `meqsap optimize-single` to invoke the optimization.
    * Enhanced `BacktestResult` to include trade duration statistics.
    * Updated reporting to summarize optimization outcomes, including adherence to constraints.
    * Added **Epic 4: Parameter Optimization Engine (Single Indicator)**.
    * Updated User Stories, Functional Requirements, Non-Functional Requirements (Modularity for `meqsap_optimizer`), and Technical Assumptions.
* **v2.1 (June 4, 2025):** Incorporates Phase 1 of the Automated Strategy Discovery roadmap.
    * This version laid the groundwork for optimization by enhancing the parameter definition framework.
    * Enhanced parameter definition framework supporting ranges, choices, and steps for strategy parameters.
    * Refactored `BaseStrategyParams`, `StrategyConfig`, and `StrategySignalGenerator` to accommodate the new parameterization.
    * Introduced the design and planned integration of the `meqsap_indicators_core` library for modular indicator management.
    * Added **Epic 3: Enhanced Parameterization Framework for Optimization Readiness**.
* **v2.0 (Initial Release Date):** Initial MVP definition for core backtesting pipeline and reporting.

## 1. Goal, Objective, and Context

* **Goal:** To build a command-line tool, the Minimum Viable Quantitative Strategy Analysis Pipeline (MEQSAP), that can take a simple strategy configuration file, run a complete backtest, perform robustness checks, and present a clear, actionable verdict. The system is evolving to support automated strategy optimization and more advanced analysis capabilities.
* **Objective:** The core principle remains to rapidly develop an end-to-end "happy path" by orchestrating powerful, existing Python libraries. Version 2.2 introduced a parameter optimization engine. **Version 2.3 introduces baseline comparisons and advanced HTML reporting**, allowing users to quantitatively and qualitatively compare their strategies against a benchmark like "Buy & Hold" to prove their alpha.
* **Context:** This project is for a user who wants to quickly and reliably analyze and optimize quantitative trading strategies and now *prove their value* against a standard benchmark using a simple, configuration-driven CLI tool.

## 2. User Stories

1.  As a strategist, I want to define a trading strategy (e.g., a moving average crossover) in a simple `.yaml` file, including the ability to specify single values for parameters, **so that** I can configure a backtest without writing any Python code.
2.  As a strategist, I want the tool to validate my `.yaml` configuration against a predefined schema, including new parameter space definitions, optimization settings, and baseline configurations, **so that** I am immediately alerted to typos or invalid parameter combinations.
3.  As a strategist, I want the tool to automatically download the necessary historical price data for a given ticker **so that** I don't have to manage data files manually.
4.  As a strategist, I want the tool to cache downloaded data **so that** subsequent runs on the same data are fast and don't repeatedly call the data provider's API.
5.  As a strategist, I want the tool to run a complete backtest on my defined strategy (using specific parameter values if ranges/choices are defined, or default/first values if not optimizing via the `analyze` command) using a single command **so that** I can see its performance statistics.
6.  As a strategist, I want to see a clean, formatted "Executive Verdict" table in my terminal **so that** I can quickly assess the strategy's performance and the results of all validation checks.
7.  As a strategist, I want the tool to automatically perform "Vibe Checks" **so that** I can instantly spot obviously flawed or inactive strategies.
8.  As a strategist, I want the tool to run automated robustness checks **so that** I can understand how sensitive my strategy is to real-world costs.
9.  As a strategist, I want the option to generate a comprehensive, institutional-grade PDF report using a command-line flag (`--report`) **so that** I can perform a deeper analysis or share the results.
10. As a developer, I want the tool to provide clear, user-friendly error messages (e.g., for a bad ticker, malformed config file, errors in parameter space definitions, or optimization failures) **so that** users can self-diagnose and fix problems easily.
11. As a strategist, I want to define parameter search spaces (e.g., ranges, choices, steps) for my strategy indicators within the `.yaml` configuration file **so that** I can prepare my strategy for automated parameter optimization.
12. As a strategist, I want to define an objective function (e.g., maximize Sharpe Ratio) and constraints (e.g., average trade hold period between 5 and 20 days) in my YAML configuration **so that** the system can optimize parameters towards my specific goals.
13. As a strategist, I want to run an automated parameter optimization for a single-indicator strategy using Grid Search or Random Search via a new CLI command (e.g., `meqsap optimize-single`) **so that** I can discover better performing parameter sets without manual trial and error.
14. As a strategist, I want to see a report of the optimization process, including the best parameters found, their performance, and how well they met constraints like hold periods, **so that** I can understand the outcome of the optimization.
15. As a developer, I want the `BacktestResult` to include detailed trade duration statistics (e.g., average hold time, percentage of trades within a target range) **so that** objective functions can use this information for optimization.
16. **(NEW for v2.3) As a strategist, I want to define a baseline strategy, such as Buy & Hold or a simple fixed-parameter strategy, in my YAML file so that I have a benchmark to compare my primary strategy against.**
17. **(NEW for v2.3) As a strategist, I want the tool to automatically run a backtest for the baseline strategy alongside my main strategy so that I can see a direct performance comparison in a single execution.**
18. **(NEW for v2.3) As a strategist, I want to see a comparative analysis in my terminal, showing my strategy's key performance metrics side-by-side with the baseline's, so that I can quickly determine if it provides a quantifiable edge.**
19. **(NEW for v2.3) As a strategist, I want the option to generate a comprehensive HTML report using a new command-line flag (`--report-html`) so that I can get advanced analytics and detailed charts comparing my strategy to the baseline for deeper analysis or sharing.**
20. **(NEW for v2.3)** As a strategist, I want the option to disable the baseline comparison for a specific run, so I can get a faster analysis when I don't need the comparison.
21. **(NEW for v2.3)** As a strategist, I want to see real-time status updates during a backtest run, so I understand what the tool is doing and why it might be taking longer.

## 3. Functional Requirements

The system must be able to:

* **Strategy Configuration (Updates for v2.3):**
    1.  Load a backtest strategy from a `.yaml` configuration file. The configuration can include fixed parameters, parameter search spaces, `optimization_config`, and a new **`baseline_config` block**.
    2.  The `optimization_config` block (optional) allows specifying optimization parameters.
    3.  **(New for v2.3)** The `baseline_config` block (optional) allows specifying:
        * `active`: boolean to enable/disable baseline comparison for a run.
        * `strategy_type`: The type of baseline to run (e.g., "BuyAndHold", "MovingAverageCrossover").
        * `params`: A block containing fixed parameters for the baseline strategy if it is not parameter-less (e.g., `fast_ma`, `slow_ma` for a baseline MA cross).
    4.  Validate the loaded configuration, including the `baseline_config` block and its parameters. If no baseline is provided, it should default to an active Buy & Hold baseline, unless disabled via the `--no-baseline` CLI flag.
    5.  Interpret parameter definitions within `BaseStrategyParams` supporting fixed values, ranges, choices.
    6.  Ensure `get_required_data_coverage_bars` correctly calculates data length considering parameter ranges.

* **Data Handling:** (No change from v2.1)
    7.  Acquire historical OHLCV data via `yfinance`.
    8.  Implement file-based caching.
    9.  Perform data integrity "Vibe Checks".

* **Backtesting Core (Updates for v2.3):**
    10. Generate entry and exit signals. `StrategySignalGenerator` accepts concrete parameter sets.
    11. Execute a full backtest using `vectorbt`.
    12. **(New for v2.3)** The backtesting process must be able to run a second backtest for the baseline strategy defined in `baseline_config`.
    13. The `BacktestResult` Pydantic model must be enhanced to include duration statistics.
    14. **(New for v2.3)** The backtesting process must gracefully handle failures in the baseline strategy backtest, allowing the candidate strategy analysis to complete.

* **Parameter Optimization Engine:** (No change from v2.2)
    15. Implement a module, `meqsap_optimizer`, for parameter optimization.
    16. Implement Grid Search and Random Search.
    17. The engine must call `run_complete_backtest` for each parameter combination.
    18. Evaluate results against the specified objective function.
    19. Identify the best-performing parameter set.

* **Objective Function Framework:** (No change from v2.2)
    20. Create a system for defining and selecting objective functions.
    21. Implement standard objective functions (Maximize Sharpe, etc.).
    22. Implement at least one objective function that incorporates trade holding period constraints.

* **Results & Reporting (Updates for v2.3):**
    23. **(New for v2.3)** The CLI must display real-time status indicators to inform the user of the current process stage (e.g., candidate backtest, baseline backtest).
    24. **(New for v2.3)** Create a new data model, `ComparativeAnalysisResult`, that can hold two `BacktestAnalysisResult` objects: one for the candidate strategy and one for the baseline.
    25. Print core performance statistics.
    26. Perform "Vibe Checks".
    27. Conduct automated robustness "Vibe Checks".
    28. **(Enhanced for v2.3)** Display a formatted "Executive Verdict" using `rich` that presents a side-by-side comparison of key metrics (e.g., Sharpe Ratio, Calmar Ratio, Total Return %) for the candidate strategy and the baseline strategy. It should include a clear "Verdict vs. Baseline" assessment (e.g., "Outperformed", "Underperformed"). The 'Verdict vs. Baseline' assessment will be based on the primary objective function defined in the `optimization_config` (from Phase 2), defaulting to a key performance metric like Sharpe Ratio if no objective function is specified.
    29. Generate PDF report via `pyfolio` with `--report`.
    30. When optimization is run, output the best parameter set and its full `BacktestAnalysisResult`.
    31. **(New for v2.3)** Implement a new command-line flag `--report-html`. When used, the system must generate a comprehensive HTML report using the `QuantStats` library. This report should compare the candidate strategy's returns against the baseline strategy's returns.

* **Modular Indicator Management:** (No change from v2.1, `meqsap_indicators_core` is foundational)
    32. Utilize `meqsap_indicators_core` for standardized indicator definition, parameter management, and calculation logic.

* **CLI & Diagnostics (Updates for v2.3):**
    33. Implement a CLI command: `meqsap optimize-single <config.yaml>`.
    34. **(New for v2.3)** Add a `--no-baseline` flag to the `analyze` and `optimize-single` commands.
    35. **(New for v2.3)** Add a `--report-html` flag to the `analyze` and `optimize-single` commands.
    36. Provide `--verbose` and `--version` flags.

## 4. Non-Functional Requirements

* **Reliability:** (No change) Consistent, reproducible results.
* **Modularity & Maintainability:** (Enhanced for v2.3)
    * The new `meqsap_optimizer` module will encapsulate all optimization-specific logic.
    * **(New for v2.3)** Logic for generating `QuantStats` reports should be cleanly integrated within the `meqsap.reporting` module.
    * **(New for v2.3)** The `meqsap.reporting` module should be refactored to use a Strategy design pattern (e.g., a `BaseReporter` with `TerminalReporter`, `HtmlReporter`, `PdfReporter` implementations) to cleanly manage multiple output formats and ensure future extensibility.
* **Code Quality:** (No change) Pydantic for validation, Python type hints.
* **Dependency Management:** (Updated for v2.3) Explicitly defined and frozen. `QuantStats` will be added as a dependency.
* **Performance:**
    * Individual backtests within the optimization loop must remain efficient.
    * Optimization runs (especially Grid Search) can be time-consuming; this is acceptable. Progress indicators should be provided. The `--no-baseline` flag is provided to mitigate the performance impact of dual backtests for users who prioritize speed.
* **Packaging:** (No change) Distributable via PyPI.

## 5. Technical Assumptions

* **Repository & Service Architecture:** (No change) Monolith, single repository.
* **Core Libraries:** (Updated for v2.3) `yfinance`, `vectorbt`, `pyyaml`, `pydantic`, `pandas`, `pandas-ta`, `rich`, `pyfolio`, `optuna`.
    * **Parameter Optimization (Phase 2 & 9):** `Optuna` is the primary library for implementing optimization algorithms.
    * **Enhanced Reporting & Analytics (Phase 3):** **`QuantStats` will be integrated** for generating comprehensive HTML reports, advanced portfolio analytics, and statistical tear sheets, complementing `pyfolio`'s PDF capabilities.
    * **Machine Learning Based Features (Future Phases):** `Mlfinlab` and `skfolio` are planned for integration in later roadmap phases.
    * **Internal Modules:** `meqsap_optimizer` will be developed, leveraging `Optuna`.
* **Language:** (No change) Python 3.9+.
* **Platform:** (No change) Command-line tool.

## 6. Epic Overview

**Epic 1: Core Backtesting Pipeline (MVP Foundation)** (Completed in v2.0)
**Epic 2: Analysis, Reporting & UX (MVP Enhancement)** (Completed in v2.0)
**Epic 3: Enhanced Parameterization Framework for Optimization Readiness** (Completed in v2.1)
**Epic 4: Parameter Optimization Engine (Single Indicator)** (Completed in v2.2)

**(NEW for v2.3) Epic 5: Baseline Comparison & Advanced Reporting**
* **Goal:** To integrate baseline strategy comparisons and advanced HTML reporting to provide users with a clear, quantitative measure of their strategy's performance against a standard benchmark.
* **User Stories for Epic 5:**
    1.  **As a strategist, I want to define a baseline strategy in my YAML file so that I have a benchmark to compare my primary strategy against.**
        * **Acceptance Criteria:**
            * AC1: `StrategyConfig` Pydantic model is updated to include an optional `baseline_config` block.
            * AC2: The YAML validation schema is updated to support `baseline_config`, which can define a `strategy_type` (e.g., "BuyAndHold") and optional fixed `params`.
            * AC3: If `baseline_config` is omitted or disabled in the config, the system defaults to using "BuyAndHold" as the baseline, unless the `--no-baseline` flag is used.
            * AC4: The system correctly parses the baseline strategy definition.
    2.  **As a strategist, I want to see a comparative analysis in my terminal, showing my strategy's key performance metrics side-by-side with the baseline's.**
        * **Acceptance Criteria:**
            * AC1: The main backtest runner is updated to execute a backtest for both the candidate strategy and the defined baseline strategy (if not disabled).
            * AC2: A `ComparativeAnalysisResult` data model is created to hold the results of both backtests.
            * AC3: The "Executive Verdict" `rich` table in the terminal output is modified to include two columns of metrics: "Candidate" and "Baseline".
            * AC4: The table includes a summary row or field indicating if the candidate "Outperformed" or "Underperformed" the baseline on a key metric (e.g., Sharpe Ratio).
            * AC5: If the baseline strategy backtest fails, the tool completes the candidate analysis and prints a warning to the terminal indicating the baseline could not be run.
    3.  **As a strategist, I want the option to generate a comprehensive HTML report using a new command-line flag (`--report-html`).**
        * **Acceptance Criteria:**
            * AC1: A new flag, `--report-html`, is added to the `analyze` and `optimize-single` CLI commands.
            * AC2: When the flag is used, the system generates a file named `report.html`.
            * AC3: The HTML report is generated using the `QuantStats` library.
            * AC4: The report correctly compares the returns of the **best-found candidate strategy** against the returns of the baseline strategy.
            * AC5: The `QuantStats` library is added as a project dependency.
    4.  **As a strategist, I want the option to disable the baseline comparison for a specific run.**
        * **Acceptance Criteria:**
            * AC1: A new flag, `--no-baseline`, is added to the `analyze` and `optimize-single` commands.
            * AC2: When `--no-baseline` is used, the baseline backtest is skipped, and all reports (terminal, HTML) only show results for the candidate strategy.
    5.  **As a strategist, I want to see real-time status updates during a backtest run.**
        * **Acceptance Criteria:**
            * AC1: The CLI provides feedback via status indicators for key stages, such as "Running candidate strategy...", "Running baseline strategy...", and "Generating HTML report...".

## 7. Explicitly Out of Scope for v2.3

To ensure focus, the following are **not** part of the v2.3 update:

* **Advanced Baseline Strategies:** The initial implementation will focus on simple baselines like Buy & Hold and strategies with fixed parameters. Complex or dynamic baselines are out of scope.
* **Advanced `QuantStats` Features:** The primary goal is to generate the comparative HTML report. Other advanced features of `QuantStats` (e.g., portfolio-level analysis, custom tear sheets) are deferred.
* **Expanding Indicator Suite (Phase 4):** No new indicators will be added in this phase.
* **Multi-Signal/Indicator Strategies (Phase 5 & 6):** All optimization and comparison work remains focused on single-indicator strategies.
* **Automated Strategy Discovery/Modification & ML Features (Phase 8+):** The "Strategy Doctor" concept and `Mlfinlab`/`skfolio` integrations are out of scope.s