# MEQSAP Architecture Document - v2.3 (Final, Revised)

**Document Version:** v2.3 (Final, Revised), Updated June 12, 2025.
**Previous Version:** v2.3 (Final, Unabridged)

## Technical Summary

This document outlines the architecture for the Minimum Viable Quantitative Strategy Analysis Pipeline (MEQSAP). The system is designed as a command-line tool that orchestrates a suite of powerful, existing Python libraries to provide an end-to-end backtesting and analysis workflow.

**Version 2.2 Foundation:** This architecture incorporated the **Enhanced Indicator & Parameter Definition Framework** (`meqsap_indicators_core`) and the **Parameter Optimization Engine** (`meqsap_optimizer`) using Optuna.

**Version 2.3 Revisions (Current - Revised):** This version incorporates the requirements from **PRD v2.3 (Epic 5)**, introducing a robust comparative analysis framework. Key architectural updates include:
* **Baseline Strategy Comparison:** The core workflow is updated to run a second backtest for a user-defined baseline strategy (e.g., Buy & Hold), enabling direct performance comparison.
* **Advanced HTML Reporting:** Integration of the `QuantStats` library into the `reporting` module to generate comprehensive, comparative HTML reports via a new `--report-html` flag.
* **Enhanced Reporting Architecture:** The `reporting` module will adopt a **Strategy design pattern** to cleanly manage multiple report formats (Terminal, PDF, HTML), improving modularity and extensibility.
* **New Data Models:** Introduction of a `ComparativeAnalysisResult` to hold results for both the candidate and baseline strategies, and updates to `StrategyConfig` to include a `baseline_config` block.
* **CLI Enhancements:** Addition of `--report-html` and `--no-baseline` flags to provide users with greater control over output and performance.
* **Resilience:** The backtesting process is designed to gracefully handle failures in the baseline strategy run, ensuring the primary analysis can still complete.

The primary goal is to validate a high-level orchestration approach, prioritizing rapid development and reliability by leveraging battle-tested components.

## High-Level Overview

The MEQSAP application is built as a **Modular Monolith** contained within a **single repository**. This approach simplifies development, dependency management, and deployment for a command-line tool.

The primary data flows are:

1.  **Analysis Path (Updated for v2.3):**
    * User invokes `meqsap analyze`. The CLI's sole responsibility is to parse arguments and invoke the appropriate workflow orchestrator.
    * The `AnalysisWorkflow` orchestrator manages the process. It first loads and validates the `.yaml` configuration, including the new optional `baseline_config`. If no baseline is specified, it defaults to Buy & Hold (unless disabled).
    * The system runs a backtest for the **candidate strategy**.
    * If enabled, the system runs a second backtest for the **baseline strategy**. The workflow gracefully handles baseline failures.
    * Results from both runs are packaged into a `ComparativeAnalysisResult`.
    * The `reporting` module is called to present a side-by-side comparison in the terminal and generate a comparative HTML report (`QuantStats`) or a PDF report for the candidate (`pyfolio`).

2.  **Optimization Path (Updated for v2.3):**
    * User invokes `meqsap optimize-single`. The CLI invokes the `OptimizationWorkflow`. This path now also supports the `--report-html` and `--no-baseline` flags.
    * The `meqsap_optimizer` finds the best parameter set for the candidate strategy.
    * After optimization, the **best candidate strategy** is compared against the **baseline strategy** in the same manner as the Analysis Path.
    * The `reporting` module presents the optimization summary, a side-by-side comparison of the best candidate vs. the baseline, and can generate comparative reports.

```mermaid
graph TD
    subgraph "User Interaction"
        A[Strategist] --invokes `analyze` or `optimize-single`--> B{MEQSAP CLI};
    end

    subgraph "MEQSAP Core"
        B --flags & config path--> WO[Workflow Orchestrator];
        WO --> C[1. Load & Validate Config];
        C --on success--> E[2. Acquire Data];
        E --provides data--> H[3. Run Candidate Backtest];
        H --Candidate Results--> K[5. Package Results];
        
        subgraph "Baseline Comparison (Conditional)"
            WO --if baseline enabled--> BL_H[4. Run Baseline Backtest];
            BL_H --Baseline Results (or failure warning)--> K;
        end
        
        K --ComparativeAnalysisResult--> J[6. Generate Reports & Verdict];
    end
    
    subgraph "Modules & Libraries"
       Optimizer((meqsap_optimizer));
       WO --for optimization path--> Optimizer;
       Optimizer --iteratively calls--> H;
       Optimizer --Best Candidate--> H;

       ReportingLib((reporting));
       J --uses--> ReportingLib;
    end

    subgraph "Output"
        ReportingLib --uses rich--> Term[Terminal: Side-by-Side Verdict];
        ReportingLib --if --report-html (uses QuantStats)--> HTML[Comparative HTML Report];
        ReportingLib --if --report (uses pyfolio)--> PDF[Candidate PDF Report];
    end
```

## Architectural / Design Patterns Adopted

The following high-level patterns guide the system's design:

* **Pattern 1: Modular Monolith:** A single deployable unit, ideal for a CLI tool. Structured into distinct modules (`config`, `data`, `backtest`, `reporting`, `indicators_core`, `optimizer`, and `workflows`).
* **Pattern 2: Orchestration & Facade:** MEQSAP acts as a simplifying facade to underlying libraries (`vectorbt`, `pyfolio`, `Optuna`, `QuantStats`) and internal modules.
* **Pattern 3: Declarative Configuration:** Users declare strategy, baseline, and optimization settings in `.yaml`. The application interprets this, separating definition from logic.
* **Pattern 4: Schema-Driven Validation:** Pydantic defines strict schemas for YAML, ensuring input integrity and clear error feedback.
* **Pattern 5: Caching:** File-based caching for market data improves performance.
* **Pattern 6: Library-based Componentization:** `meqsap_indicators_core` and `meqsap_optimizer` are dedicated internal modules promoting high cohesion and loose coupling.
* **Pattern 7: Strategy Pattern (Expanded for v2.3):**
    * Used within `meqsap_optimizer` for interchangeable algorithms (via `Optuna` samplers) and objective functions.
    * **Newly applied to the `reporting` module.** A `BaseReporter` protocol will define a common interface, with concrete implementations like `TerminalReporter`, `HtmlReporter` (using `QuantStats`), and `PdfReporter` (using `pyfolio`). This aligns with PRD v2.3 NFRs for a more maintainable and extensible reporting architecture.

## Component View

The MEQSAP application comprises the following primary modules:

* **`cli` Module:** Main entry point package using `Typer`. Its sole responsibility is to parse command-line arguments and invoke the correct workflow from the `workflows` module.
* **`workflows` Module (NEW):** Orchestrates the high-level application logic, separating it from the CLI. This improves testability and adheres to the Single Responsibility Principle.
    * Contains classes like `AnalysisWorkflow` and `OptimizationWorkflow`.
    * Manages the dual backtest workflow: triggers the candidate backtest, and conditionally triggers the baseline backtest (respecting the `--no-baseline` flag). 
    * Manages `rich`-based **real-time status updates** to inform the user of the current stage with explicit messages like "Running candidate strategy...", "Running baseline strategy...", and "Generating HTML report...". 
    * Catches failures from the baseline run, ensuring the main analysis proceeds while displaying a clear user-facing warning (e.g., `⚠️ Baseline strategy backtest failed. Displaying candidate results only.`). 
* **`config` Module:** Loads strategy `.yaml` files. Parses and validates `optimization_config` and the new `baseline_config` block against Pydantic models. During validation, it injects a default "Buy & Hold" configuration if `baseline_config` is absent and not disabled via the CLI.
* **`data` Module:** Handles market data acquisition (`yfinance`), caching, and integrity checks.
* **`meqsap_indicators_core` Module:** Standardizes definition, parameterization (fixed, range, choice), validation, and calculation logic for technical indicators.
* **`backtest` Module:** Core backtesting engine. The orchestrating logic (now in `workflows`) must gracefully handle exceptions from this module during the baseline run. `run_complete_backtest` populates `BacktestResult` with mandatory trade duration statistics.
* **`meqsap_optimizer` Module:** Responsible for automated parameter optimization using Optuna. Its output (the best strategy) is fed into the new comparative analysis workflow.
* **`reporting` Module (Enhanced for v2.3):**
    * Refactored to implement the **Strategy Pattern** for different report formats.
    * The `TerminalReporter` implementation is responsible for presenting the side-by-side terminal view using `rich` and for calculating the final "Verdict vs. Baseline" (e.g., "Outperformed") based on the primary objective function.
    * **Integrates `QuantStats`** via an `HtmlReporter` to generate comprehensive, comparative HTML reports when `--report-html` is used. 
    * Handles the new `ComparativeAnalysisResult` data model.

```mermaid
graph TD
    subgraph "Entrypoint"
        CLI
    end

    subgraph "Core Logic & Libraries"
        Workflows[workflows]
        ConfigModule[config]
        IndicatorsCore[meqsap_indicators_core]
        DataModule[data]
        BacktestModule[backtest]
        OptimizerModule[meqsap_optimizer]
        ReportingModule[reporting]
    end

    subgraph "External Libraries"
        Pydantic
        PyYAML
        yfinance
        Optuna
        vectorbt
        rich
        pyfolio
        QuantStats[QuantStats]
    end

    CLI -- "analyze" / "optimize-single" --> Workflows
    Workflows --> ConfigModule
    ConfigModule --uses--> PyYAML & Pydantic
    ConfigModule --uses for indicator defs--> IndicatorsCore

    Workflows --Market Data Request--> DataModule
    DataModule --uses--> yfinance
    DataModule --Market Data--> Workflows

    Workflows --runs candidate backtest via--> BacktestModule
    Workflows --runs baseline backtest via--> BacktestModule
    BacktestModule --uses--> vectorbt & IndicatorsCore
    
    Workflows --for optimization path--> OptimizerModule
    OptimizerModule --runs backtests for param sets via--> BacktestModule
    OptimizerModule --uses--> Optuna
    
    BacktestModule --Results--> Workflows
    OptimizerModule --Best params & results--> Workflows
    
    Workflows --ComparativeAnalysisResult--> ReportingModule
    ReportingModule --uses--> rich, pyfolio, QuantStats
    ReportingModule --> TerminalOutput[Terminal Verdict] & HTMLReport((HTML Report)) & PDFReport((PDF Report))
```

## Project Structure

The project uses a standard `src` layout, updated to reflect the new workflow orchestration and reporting strategy.

```plaintext
meqsap/
├── docs/
│   ├── architecture.md         # This document
│   └── prd.md                  # Product Requirements Document
├── src/
│   └── meqsap/
│       ├── __init__.py
│       ├── backtest.py           # Core backtesting logic
│       ├── cli.py                # Main CLI entry point (using Typer)
│       ├── config.py             # Pydantic schema, YAML loading
│       ├── data.py               # Data acquisition and caching
│       ├── exceptions.py         # Custom application exceptions
│       ├── reporting/            # ENHANCED: Reporting module
│       │   ├── __init__.py
│       │   ├── main.py           # Main reporting orchestrator/facade
│       │   ├── reporters.py      # NEW: BaseReporter protocol and implementations
│       │   └── models.py         # Pydantic models for reporting
│       ├── workflows/            # NEW: Core application logic orchestration
│       │   ├── __init__.py
│       │   └── analysis.py       # e.g., AnalysisWorkflow, OptimizationWorkflow
│       ├── indicators_core/      # Indicator definitions and logic
│       └── optimizer/            # Parameter optimization module
├── tests/
│   └── ...
├── .gitignore
├── pyproject.toml
├── README.md
└── requirements.txt
```

## Testing Strategy & Key Scenarios for v2.3 (NEW)

To ensure the new features are robust, the testing plan (using `pytest`) must be updated to include:

* **Configuration Tests:** Unit tests to validate the correct parsing of `baseline_config`, including successful validation, error cases, and injection of the default baseline.
* **Workflow & CLI Flag Tests:** Integration tests to verify:
    * The `--no-baseline` flag correctly prevents the baseline execution.
    * The `--report-html` flag correctly invokes the `HtmlReporter` and generates an HTML file.
* **Resilience Test:** An integration test that uses a mock to simulate a failure during the baseline backtest run and asserts that the application completes the candidate analysis and prints the correct warning message to the user.
* **Reporting Logic Test:** A unit test for the `TerminalReporter` to verify that the "Outperformed" / "Underperformed" verdict is calculated correctly based on different input results.

## Definitive Tech Stack Selections

| Category | Technology | Version / Details | Justification |
| :--- | :--- | :--- | :--- |
| **Languages** | Python | 3.9+ | Specified. |
| **CLI Framework** | Typer | Latest | Integrates well with Pydantic for robust CLI building. |
| **Data Handling** | pandas | Latest | Industry standard for core data manipulation. |
| | yfinance | Latest | Meets requirements for historical OHLCV data. |
| **Technical Analysis**| pandas-ta | Latest | Comprehensive TA library, wrapped by `meqsap_indicators_core`. |
| **Backtesting** | vectorbt | Latest | Powerful and modern vectorized backtesting engine. |
| **Configuration** | PyYAML, Pydantic | Latest | Standard and secure YAML loading combined with strict schema validation. |
| **Reporting & UI** | rich | Latest | Provides polished CLI UX and progress indicators. |
| | pyfolio | Latest | Industry standard for generating PDF tear sheets. |
| | **QuantStats (NEW)** | **Latest** | **Required for generating comprehensive, comparative HTML reports as per PRD v2.3.** |
| **Internal Components**| `meqsap_indicators_core` | N/A (Internal) | Ensures modularity and readiness for optimization. |
| | `meqsap_optimizer` | N/A (Internal) | Implements Phase 2 (PRD v2.2) for automated parameter tuning. |
| **Optimization** | Optuna | Latest | A powerful, standard framework for hyperparameter optimization. |
| **Testing** | pytest | Latest | De facto standard for unit and integration testing. |
| **CI/CD** | GitHub Actions | N/A | Well-integrated for automation. |

## API Reference

### External APIs Consumed
* **`yfinance` API**: For historical market data. Consumed by the `data` module.
* **`Optuna` API**: For defining studies, trials, and samplers within `meqsap_optimizer`.
* **`QuantStats` API**: For generating HTML reports within the `reporting` module.

### Internal APIs Provided
Not applicable. MEQSAP is a self-contained command-line tool.

## Data Models

* **`StrategyConfig`** (`meqsap.config`): Updated to include `baseline_config: Optional[BaselineConfig] = None`.
* **`BaselineConfig`** (`meqsap.config`): A new Pydantic model containing `active: bool`, `strategy_type: str`, and `params: dict`.
* **`BacktestAnalysisResult`** (in `reporting.models` or `backtest`): A model holding the comprehensive results of a *single* backtest run.
* **`ComparativeAnalysisResult`** (in `reporting.models`): A new, simplified Pydantic model to hold the results of both backtests.
    ```python
    from typing import Optional
    from pydantic import BaseModel
    
    class ComparativeAnalysisResult(BaseModel):
        candidate_results: BacktestAnalysisResult
        baseline_results: Optional[BacktestAnalysisResult] = None
        # Note: If baseline_results is None, it implies the run
        # was either skipped (via --no-baseline) or it failed.
        # The workflow is responsible for logging the specific reason.
    ```
* Models like `OptimizationConfig`, `BacktestResult`, and `OptimizationResult` remain functionally the same, though their consumption is now part of the comparative workflow.

## Core Workflow / Sequence Diagrams

### Analysis Path (`meqsap analyze --report-html`)

```mermaid
sequenceDiagram
    actor User
    participant CLI as cli
    participant Workflow as AnalysisWorkflow
    participant Backtest as backtest
    participant Reporting as reporting

    User->>CLI: `meqsap analyze --config strategy.yaml --report-html`
    CLI->>Workflow: start_analysis(args)
    
    Workflow->>Workflow: Load Config, Get Data
    Workflow->>Workflow: Display "Running candidate strategy..."
    Workflow->>Backtest: run_complete_backtest(candidate_config, DataFrame)
    Backtest-->>Workflow: candidate_results: BacktestAnalysisResult
    
    alt Baseline Enabled
        Workflow->>Workflow: Display "Running baseline strategy..."
        try
            Workflow->>Backtest: run_complete_backtest(baseline_config, DataFrame)
            Backtest-->>Workflow: baseline_results: BacktestAnalysisResult
        catch Exception
            Workflow->>Workflow: Log warning: "Baseline run failed."
            Workflow-->>Workflow: baseline_results = None
        end
    end

    Workflow->>Reporting: generate_output(candidate_results, baseline_results, flags)
    Reporting-->>User: Terminal: Side-by-side verdict
    Reporting-->>User: File: report.html (Comparative report via QuantStats)
```

### Optimization Path (`meqsap optimize-single --report-html`)

```mermaid
sequenceDiagram
    actor User
    participant CLI as cli
    participant Workflow as OptimizationWorkflow
    participant Optimizer as meqsap_optimizer
    participant Backtest as backtest_engine
    participant Reporting as reporting

    User->>CLI: `meqsap optimize-single --config optimizable.yaml --report-html`
    CLI->>Workflow: start_optimization(args)
    Workflow->>Optimizer: run_optimization(Config, DataFrame)
    
    loop For each Optuna trial
        Optimizer->>Backtest: run_complete_backtest(params, DataFrame)
        Backtest-->>Optimizer: BacktestAnalysisResult
    end
    
    Optimizer-->>Workflow: OptimizationResult (incl. best_found_candidate_results)
    
    alt Baseline Enabled
        Workflow->>Workflow: Display "Running baseline strategy..."
        try
            Workflow->>Backtest: run_complete_backtest(baseline_config, DataFrame)
            Backtest-->>Workflow: baseline_results: BacktestAnalysisResult
        catch Exception
            Workflow->>Workflow: Log warning: "Baseline run failed."
        end
    end
    
    Workflow->>Reporting: generate_optimization_output(OptimizationResult, baseline_results, flags)
    Reporting-->>User: Terminal: Opt. Summary & Side-by-Side Verdict
    Reporting-->>User: File: report.html (Comparative report for Best vs. Baseline)
```

## Future Considerations & Technical Debt

* **Parallel Execution for Optimization:** The current design is single-threaded. For larger parameter spaces, parallel execution will be necessary. `Optuna`'s support for distributed optimization can be explored in a future phase. This is considered **technical debt (TD-ARCH-20250605-001)**.
* **Deferred Technologies:** To adhere to YAGNI principles for this version, the following libraries are considered out of scope for the definitive tech stack but are noted for future phases:
    * **`Mlfinlab` & `skfolio`:** Identified for **Future ML Phases** for advanced features like financial ML, bet sizing, and modern portfolio optimization.
* **Advanced Optimization Algorithms:** While the Strategy Pattern supports new algorithms, implementing more advanced ones (Bayesian, Genetic via `Optuna`'s advanced samplers) is deferred to **Roadmap Phase 9**.
* **Optimization State Persistence & Resumption:** The current architecture supports logging trial history to an RDB (e.g., SQLite) via Optuna. Full, robust interrupt/resume functionality for long optimization runs would require further specific implementation and is deferred.

## Roadmap Alignment & Extension Points

This architecture is designed to implement PRD v2.3 requirements (Phase 3 of the roadmap) and provide a solid foundation for future phases:

* **Phase 3 (Baseline & Comparative Analysis): COMPLETE**. This architecture directly implements this phase.
* **Phase 4 (Expanding Indicator Suite):** `meqsap_indicators_core` is designed for easy addition of new indicators.
* **Phase 5 (Multi-Signal/Indicator Combination):** The `meqsap.backtest.StrategySignalGenerator` will be the integration point for a new `meqsap_signal_combiner` module.
* **Phase 7 (Market Regime Detection):** The `run_complete_backtest` function in `meqsap.backtest` is designed to be extensible with an optional `regime_data` parameter.
* **Phase 8 (Automated Strategy Improvement - Strategy Doctor):** `BacktestAnalysisResult` can be augmented with diagnostic data from a future `meqsap_strategy_doctor` module.
* **Phase 10 (Analyst-in-the-Loop & Portfolio Construction):** Integration of `skfolio` would likely occur as a new CLI command or an extension to the reporting/analysis phase.