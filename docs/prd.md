Okay, I'm John, your Product Manager. I understand the goal: to update the MEQSAP Product Requirements Document (PRD) from its current v2.0 to a new v2.1. This update will meticulously incorporate **Phase 1: Enhanced Indicator & Parameter Definition Framework** from the provided `roadmap.md`.

This phase is crucial as it lays the foundational groundwork for future automated strategy discovery and optimization by enabling a more flexible and robust way to define strategy parameters. I will ensure the updated PRD reflects these changes in detail, including modifications to existing sections and the introduction of a new Epic with corresponding user stories and acceptance criteria.

Here is the updated Product Requirements Document:

# MEQSAP Product Requirements Document (PRD) - v2.1

## Version History

* **v2.1 (June 4, 2025):** Incorporates Phase 1 of the Automated Strategy Discovery roadmap.
    * Enhanced parameter definition framework supporting ranges, choices, and steps for strategy parameters.
    * Refactored `BaseStrategyParams`, `StrategyConfig`, and `StrategySignalGenerator` to accommodate the new parameterization.
    * Introduced the design and planned integration of the `meqsap_indicators_core` library for modular indicator management.
    * Added **Epic 3: Enhanced Parameterization Framework for Optimization Readiness**.
    * Updated User Stories, Functional Requirements, Non-Functional Requirements (Modularity), and Technical Assumptions to reflect these changes.
* **v2.0 (Initial Release Date):** Initial MVP definition for core backtesting pipeline and reporting.

## 1. Goal, Objective, and Context

* **Goal:** To build a command-line tool, the Minimum Viable Quantitative Strategy Analysis Pipeline (MEQSAP), that can take a simple strategy configuration file, run a complete backtest, perform robustness checks, and present a clear, actionable verdict. The system is evolving to support more advanced strategy analysis capabilities.
* **Objective:** The core principle remains to rapidly develop an end-to-end "happy path" by orchestrating powerful, existing Python libraries (`vectorbt`, `pyfolio`, `pydantic`, etc.). This version (v2.1) expands the objective to include the creation of a flexible and extensible framework for strategy parameter definition, enabling parameter search spaces (ranges, choices, steps). This enhancement is a foundational step towards future automated parameter optimization, focusing on high-level integration and logic validation ("Vibe Checks") rather than writing low-level, boilerplate code.
* **Context:** This project is for a user who wants to quickly and reliably analyze quantitative trading strategies using a simple, configuration-driven CLI tool. The MVP (v2.0) proved the viability of the orchestration-first approach. Version 2.1 enhances the configuration capabilities to prepare for more sophisticated analysis techniques.

## 2. User Stories

1.  **As a strategist, I want to** define a trading strategy (e.g., a moving average crossover) in a simple `.yaml` file, including the ability to specify single values for parameters, **so that** I can configure a backtest without writing any Python code.
    * *Acceptance Criteria updated for v2.1 to differentiate from new parameter space story.*
2.  **As a strategist, I want the tool to** validate my `.yaml` configuration against a predefined schema, including new parameter space definitions, **so that** I am immediately alerted to typos or invalid parameter combinations (e.g., `slow_ma` < `fast_ma`, invalid range definitions).
    * *Acceptance Criteria updated for v2.1.*
3.  **As a strategist, I want the tool to** automatically download the necessary historical price data for a given ticker **so that** I don't have to manage data files manually. (No change from v2.0)
4.  **As a strategist, I want the tool to** cache downloaded data **so that** subsequent runs on the same data are fast and don't repeatedly call the data provider's API. (No change from v2.0)
5.  **As a strategist, I want the tool to** run a complete backtest on my defined strategy (using specific parameter values if ranges/choices are defined for optimization readiness) using a single command **so that** I can see its performance statistics.
    * *Note for v2.1: For a single run, if parameter spaces are defined, the system might use default values or the first choice, or this might be configurable later. The immediate focus is on supporting the definition; actual optimization is out of scope for v2.1.*
6.  **As a strategist, I want to** see a clean, formatted "Executive Verdict" table in my terminal **so that** I can quickly assess the strategy's performance and the results of all validation checks. (No change from v2.0)
7.  **As a strategist, I want the tool to** automatically perform "Vibe Checks" (e.g., ensuring at least one trade occurred) **so that** I can instantly spot obviously flawed or inactive strategies. (No change from v2.0)
8.  **As a strategist, I want the tool to** run automated robustness checks (e.g., re-running with high fees) **so that** I can understand how sensitive my strategy is to real-world costs. (No change from v2.0)
9.  **As a strategist, I want the option to** generate a comprehensive, institutional-grade PDF report using a command-line flag (`--report`) **so that** I can perform a deeper analysis or share the results. (No change from v2.0)
10. **As a developer, I want the tool to** provide clear, user-friendly error messages (e.g., for a bad ticker or malformed config file, including errors in parameter space definitions) **so that** users can self-diagnose and fix problems easily.
    * *Acceptance Criteria updated for v2.1.*
11. **(NEW for v2.1) As a strategist, I want to define parameter search spaces** (e.g., ranges, choices, steps) for my strategy indicators within the `.yaml` configuration file **so that** I can prepare my strategy for future automated parameter optimization.

## 3. Functional Requirements

The system must be able to:

* **Strategy Configuration:**
    1.  Load a backtest strategy from a `.yaml` configuration file using `yaml.safe_load()` for security. The configuration can include fixed parameters as well as definitions for parameter search spaces (ranges, choices, steps).
    2.  Validate the loaded configuration, including parameter search space definitions, against a predefined Pydantic schema. This includes validating types (e.g., range, choice, value) and their specific attributes (e.g., `start`, `stop`, `step` for ranges; `values` for choices).
    3.  Interpret parameter definitions within `BaseStrategyParams` and its children, supporting:
        * Fixed values (e.g., `parameter: 10`).
        * Ranges (e.g., `parameter: {"type": "range", "start": 5, "stop": 20, "step": 1}`).
        * Choices (e.g., `parameter: {"type": "choices", "values": [10, 14, 20]}`).
        * Specific single values when a search space is defined (e.g., for a non-optimizing run, a default or the first value in a choice list might be used, or the 'value' from `{"type": "value", "value": 50}`).
    4.  Ensure the `get_required_data_coverage_bars` method within `BaseStrategyParams` (and its overrides) correctly calculates the necessary historical data length by considering the maximum possible lookback required by any parameter, especially when defined as a range (e.g., using the `stop` value of a range if it dictates the longest lookback). This includes addressing FLAW-20250602-002 regarding strict enforcement and handling of dynamic parameter definitions.
* **Data Handling:**
    5.  Acquire historical OHLCV data for a specified ticker from `yfinance`.
    6.  Implement a file-based caching system for downloaded data (e.g., using Parquet or Feather format) to improve performance on subsequent runs.
    7.  Perform data integrity "Vibe Checks" post-download to validate data for completeness (no NaN values) and freshness.
* **Backtesting Core:**
    8.  Generate entry and exit signals based on the strategy's rules. The `StrategySignalGenerator` (or equivalent component) must be adaptable to accept concrete parameter sets (drawn from a defined search space or fixed values) for signal generation.
    9.  Execute a full backtest using the generated signals with a single command from the `vectorbt` library.
* **Results & Reporting:**
    10. Print the core performance statistics from the backtest result.
    11. Perform a "Vibe Check" to ensure the strategy generated at least one trade.
    12. Conduct an automated robustness "Vibe Check" by re-running the simulation with high fees and by reporting the strategy's turnover rate.
    13. Display a formatted "Executive Verdict" in the terminal using the `rich` library, presenting key metrics and the pass/fail status (e.g., ✅/❌) of all "Vibe Checks".
    14. Generate a comprehensive PDF report ("tear sheet") using `pyfolio` when the `--report` flag is used.
* **Modular Indicator Management (New for v2.1):**
    15. Implement or integrate a dedicated module/library (conceptually `meqsap_indicators_core`) responsible for:
        * Standardized definition of technical indicators.
        * Management of indicator parameters, including their types (fixed, range, choice) and validation.
        * Providing calculation logic for indicators, potentially wrapping libraries like `pandas-ta` or offering custom implementations.
        * A registry or mechanism for discovering and accessing available indicators.
    16. The main `meqsap.config` module should utilize this indicator management system to interpret and validate indicator parameters from the YAML configuration.
    17. The main `meqsap.backtest` module (specifically the signal generation part) should utilize this indicator management system to fetch indicator calculation logic.
* **CLI & Diagnostics:**
    18. Provide a `--verbose` flag to print detailed logs for debugging user-reported issues.
    19. Provide a `--version` flag that outputs the tool's version and the versions of its key dependencies.

## 4. Non-Functional Requirements

* **Reliability:** The pipeline must be reliable and produce consistent, reproducible results, achieved by leveraging battle-tested libraries for core operations.
* **Modularity & Maintainability:** The codebase will be highly maintainable by adhering to the "orchestration-first" principle and being structured into distinct modules with clear separation of concerns (e.g., `cli`, `config`, `data`, `backtest`, `reporting`).
    * **(Enhanced for v2.1)**: The introduction of the `meqsap_indicators_core` library/module is a key step in enhancing modularity for indicator definitions and parameter handling, separating this logic from the core configuration parsing and backtesting execution flow.
* **Code Quality:** Pydantic must be used heavily for all data validation, including the new parameter search space definitions. The entire codebase must use Python's native type hints.
* **Dependency Management:** Project dependencies **must** be explicitly defined and frozen in `requirements.txt` to ensure a completely reproducible environment.
* **Performance:** The backtesting process should be fast enough for iterative testing, aided by the required data caching mechanism.
* **Packaging:** The application should be packaged for distribution via PyPI to ensure easy installation for end-users (`pip install meqsap`).

## 5. Technical Assumptions

* **Repository & Service Architecture:** The application will be a **Monolith** contained within a **single repository (Monorepo)**.
* **Core Libraries:** The project is an orchestration of the following key Python libraries: `yfinance`, `vectorbt`, `pyyaml`, `pydantic`, `pandas`, `pandas-ta`, `rich`, and `pyfolio`.
    * **(New for v2.1)**: A new internal library/module, `meqsap_indicators_core`, will be developed to handle standardized indicator definitions, parameter types (including search spaces), and calculation logic. Initially, this may reside within the main `meqsap` package structure but is designed for potential future separation.
* **Language:** Python 3.9+.
* **Platform:** A command-line tool for standard terminal environments (Linux, macOS, Windows).

## 6. Epic Overview

**Epic 1: Core Backtesting Pipeline (MVP Foundation)**
* **Goal:** Build a functional, end-to-end pipeline runnable from the command line. This involves setting up the reproducible Python environment, creating the logic to load and validate a strategy from YAML (initially with fixed parameters), implementing data acquisition with caching, and executing a backtest using `vectorbt`. The epic is complete when the pipeline can output basic performance results to the terminal.
    * *Note for v2.1: Parts of this epic, specifically strategy loading, validation, and signal generation, will be enhanced by Epic 3.*

**Epic 2: Analysis, Reporting & UX (MVP Enhancement)**
* **Goal:** Enhance the core pipeline with an analysis and presentation layer. This includes implementing the automated "Vibe Checks" (e.g., for fees, turnover, and trade count). The key deliverable is the formatted "Executive Verdict" table using the `rich` library. This epic is complete when the `pyfolio` report generation is functional via the `--report` flag and user-friendly error handling is in place.
    * *Note for v2.1: Error handling will be extended to cover new parameter definitions.*

**(NEW for v2.1) Epic 3: Enhanced Parameterization Framework for Optimization Readiness**
* **Goal:** To refactor the strategy configuration and signal generation mechanisms to support definable parameter search spaces (ranges, choices, steps), laying the critical groundwork for future automated strategy optimization. This involves creating a robust and extensible framework for defining indicators and their parameter spaces, including the introduction of `meqsap_indicators_core`.
* **User Stories for Epic 3:**
    1.  **As a developer, I want to refactor `BaseStrategyParams` and its children** to support defining indicator parameters as ranges (with start, stop, step), choices (a list of valid values), or specific single values **so that** strategy configurations can comprehensively express parameter search spaces for individual indicators.
        * **Acceptance Criteria:**
            * AC1: `BaseStrategyParams` and relevant child classes (e.g., `MovingAverageCrossoverParams`) are modified to allow parameter definitions such as `fast_ma: {"type": "range", "start": 5, "stop": 20, "step": 1}`, `rsi_period: {"type": "choices", "values": [10, 14, 20]}`, or `fixed_value: {"type": "value", "value": 50}`.
            * AC2: Pydantic models are implemented and utilized for the strict validation of these new parameter structures, ensuring correct types and attributes (e.g., `start` < `stop` for ranges).
            * AC3: The `get_required_data_coverage_bars` method in `BaseStrategyParams` (and any overriding methods in child classes) is updated to accurately calculate the maximum lookback period. This calculation must consider the full extent of any defined parameter ranges (e.g., using the `stop` value of a range if it defines the longest indicator period requiring historical data).
            * AC4: The enforcement of `get_required_data_coverage_bars` (addressing FLAW-20250602-002) is implemented, ensuring that an error is raised or sufficient data is requested if the historical data provided does not meet the calculated coverage requirements based on dynamic parameters.
    2.  **As a strategist, I want to update the strategy `.yaml` configuration (processed by `StrategyConfig`)** to allow the specification of parameter search spaces (ranges, choices, steps) for indicators **so that** I can define strategies that are ready for subsequent automated tuning or scenario analysis.
        * **Acceptance Criteria:**
            * AC1: The YAML schema that `StrategyConfig` (and its underlying Pydantic models) parses is extended to accept parameter definitions using the new range, choice, or fixed value structures for each relevant indicator parameter.
            * AC2: Pydantic validation within `StrategyConfig` correctly parses, validates, and makes accessible these new parameter space definitions from the loaded YAML file.
            * AC3: Example `.yaml` configuration files are created or updated to clearly demonstrate how to define fixed parameters, parameter ranges, and parameter choices.
    3.  **As a developer, I want to adapt the `StrategySignalGenerator` (or equivalent logic within `src/meqsap/backtest.py`)** to accept and utilize concrete parameter sets, which could be drawn from defined search spaces or be fixed values, for generating trading signals **so that** the backtesting engine can operate with specific parameter instances, facilitating both single backtests and future parameter optimization loops.
        * **Acceptance Criteria:**
            * AC1: The `StrategySignalGenerator`'s methods (or their equivalents responsible for calculating indicator values and producing trading signals) are refactored to accept a dictionary or a structured object of concrete parameter values as an input argument for a given strategy.
            * AC2: The signal generation logic correctly uses these dynamically provided concrete parameters during its calculations, rather than assuming parameters are statically defined within the strategy configuration object itself.
            * AC3: The system can still perform a standard backtest if the YAML provides fixed values or if defaults are chosen from defined search spaces (exact mechanism for choosing defaults from spaces in a single run to be defined, could be first value, or mean, or require explicit single value definition alongside range for non-optimizing runs).
    4.  **As a developer, I want to design and implement the initial version of the `meqsap_indicators_core` library/module** to standardize indicator definitions, parameter types (including fixed values, ranges, and choices), and their search space descriptions **so that** indicator logic becomes modular, extensible, easier to maintain, and directly supports the goal of automated tuning.
        * **Acceptance Criteria:**
            * AC1: Base classes such as `IndicatorBase` (defining a common interface for all indicators), `ParameterDefinition` (describing a single parameter, its type, and constraints), and `ParameterSpace` (defining the search space for a set of parameters) are designed and implemented within `meqsap_indicators_core`.
            * AC2: At least two common technical indicators (e.g., Simple Moving Average, Relative Strength Index) are implemented as concrete classes adhering to `IndicatorBase`, demonstrating how to define their specific parameters and calculation logic (potentially by wrapping `pandas-ta` functions and linking them to `ParameterDefinition` objects).
            * AC3: A registry, factory, or similar mechanism is established within `meqsap_indicators_core` to allow for the discovery and instantiation of available indicators by name or type.
            * AC4: The `meqsap.config` module (specifically `BaseStrategyParams` and `StrategyConfig`) is updated to utilize the `meqsap_indicators_core` library/module for understanding, defining, and validating indicator parameter definitions sourced from the YAML configuration.
            * AC5: The `meqsap.backtest` module (specifically `StrategySignalGenerator`) is updated to utilize `meqsap_indicators_core` to dynamically obtain indicator calculation logic based on the strategy configuration.
            * AC6: The modularization achieved through `meqsap_indicators_core` demonstrably improves the separation of concerns, making the indicator definition and strategy configuration logic more maintainable and testable, aligning with NFRs.
    5.  **As a maintainer, I want to update relevant project documentation**, including `architecture.md`, example YAML files, and any developer guides, **so that** these documents accurately reflect the new parameter definition framework, the architectural changes related to parameter handling, and the introduction and usage of the `meqsap_indicators_core` concept.
        * **Acceptance Criteria:**
            * AC1: The `architecture.md` document is updated to reflect changes in the `config.py` (Pydantic models for new parameter structures) and `backtest.py` (adaptations in `StrategySignalGenerator`) modules. It should also describe the role and structure of the new (or planned) `meqsap_indicators_core` library/module.
            * AC2: Example `.yaml` configuration files provided with the project are updated to showcase how to define parameter ranges, choices, and fixed values using the new syntax.
            * AC3: Any internal developer documentation or README sections discussing strategy configuration or backtest execution are updated to include information about the enhanced parameterization capabilities.

---

## 7. Explicitly Out of Scope for MVP (and v2.1 Update)

To ensure a focused and rapid development cycle, the following are **not** part of the MVP, nor are they introduced by the v2.1 update. The v2.1 update focuses *solely* on the framework for defining parameters with search spaces; the actual utilization of these spaces for optimization is a future phase.

* **Automated Strategy Optimization Engine:** The v2.1 enhancements enable parameter search space *definition*. The engine to *use* these definitions for automated parameter tuning (e.g., grid search, random search, Bayesian optimization) is **out of scope** for v2.1.
* **Automated Intelligence:**
    * No Automated Feature Engineering: The system will not automatically generate or select trading features (`tsfresh`, `scikit-learn`). Strategies must use a small, pre-defined set of indicators (e.g., SMA, EMA, RSI).
    * No Automated Strategy Suggestions: The tool will not diagnose strategy weaknesses or automatically generate a modified `.yaml` file. It only reports the metrics.
    * No A/B Testing: The tool will not perform comparative tests between different strategies.
* **Advanced Backtesting Features:**
    * No Walk-Forward Optimization: All backtests are simple in-sample runs.
    * No Advanced `vectorbt` Features: Use of custom event handlers, parameter optimization grids (`run_combs` in the context of `vectorbt`'s own optimization capabilities, which is distinct from MEQSAP's planned optimizer), or other advanced `vectorbt` functionalities is not included.
    * No Complex Fee Models: The tool will only support a simple, fixed percentage fee model.
* **Scope of Analysis:**
    * No Batch Testing: The tool will process one strategy at a time. It will not support running a directory of strategies to produce a leaderboard.
    * Single-Instrument Only: The tool will only analyze a single ticker at a time. Multi-asset backtesting is not supported.
* **User Interface:**
    * No Interactive Prompts: The tool is non-interactive. All control is through the YAML file and command-line flags.
    * No Interactive Plots: The tool will not serve or display interactive plots in a browser.
* **Data Sources:**
    * `yfinance` Only: The only supported data source is `yfinance`. Support for other data providers or local CSV files is not included.