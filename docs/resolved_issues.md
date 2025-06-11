# Resolved Architectural Issues Log

This file tracks issues that have been resolved, including their re-open history.

**Last Updated:** 2025-06-18

---
**Issue ID:** FLAW-20250617-001
**Original Description (Concise):** The comment in `examples/indian_stock_sample.yaml` incorrectly stated that `objective_function` names are case-insensitive, contradicting the case-sensitive implementation.
**Initial Resolution Summary (Concise):** Corrected the comment in `examples/indian_stock_sample.yaml` to state that `objective_function` names are case-sensitive, aligning documentation with the implementation.
**Date First Resolved:** 2025-06-18
**Reopen Count:** 0
**Last Reopened Date:** 
**Last Resolution Summary (Concise):** Corrected the comment in `examples/indian_stock_sample.yaml` to state that `objective_function` names are case-sensitive, aligning documentation with the implementation.
**Date Last Resolved:** 2025-06-18
---
**Issue ID:** FLAW-20250617-002
**Original Description (Concise):** The CLI `optimize` command violated exit code policy and had broken `KeyboardInterrupt` handling, causing loss of optimization progress.
**Initial Resolution Summary (Concise):** The `OptimizationEngine` was verified to correctly handle `KeyboardInterrupt` and set an interruption flag. The CLI command was verified to correctly inspect this flag. The `handle_cli_errors` decorator was verified to map `OptimizationError` and `OptimizationInterrupted` exceptions to the correct exit codes (6 and 7 respectively), resolving the issue.
**Date First Resolved:** 2025-06-18
**Reopen Count:** 0
**Last Reopened Date:** 
**Last Resolution Summary (Concise):** The `OptimizationEngine` was verified to correctly handle `KeyboardInterrupt` and set an interruption flag. The CLI command was verified to correctly inspect this flag. The `handle_cli_errors` decorator was verified to map `OptimizationError` and `OptimizationInterrupted` exceptions to the correct exit codes (6 and 7 respectively), resolving the issue.
**Date Last Resolved:** 2025-06-18
---
**Issue ID:** FLAW-20250601-001
**Original Description (Concise):** Local ConfigError in config.py
**Initial Resolution Summary (Concise):**
The local `ConfigError` definition was removed from `src/meqsap/config.py`. The `src/meqsap/cli.py` module was verified to exclusively import and use `ConfigurationError` from `src/meqsap/exceptions.py`, adhering to `docs/adr/004-error-handling-policy.md`.
**Date First Resolved:** 2025-06-02
**Reopen Count:** 0
**Last Reopened Date:**
**Last Resolution Summary (Concise):** Still compliant. The canonical `ConfigurationError` from `src/meqsap/exceptions.py` is used correctly.
**Date Last Resolved:** 2025-06-17
---
**Issue ID:** FLAW-20250601-002
**Original Description (Concise):** Doc misalignment for CLI exceptions
**Initial Resolution Summary (Concise):**
The exception hierarchy diagram in `docs/adr/004-error-handling-policy.md` and the "Exception Mapping" table in `docs/policies/error-handling-policy.md` were verified to include the CLI-specific exceptions (`DataAcquisitionError`, `BacktestExecutionError`, `ReportGenerationError`) as subclasses of `CLIError`, aligning documentation with the implemented error handling.
**Date First Resolved:** 2025-06-02
**Reopen Count:** 0
**Last Reopened Date:**
**Last Resolution Summary (Concise):** Still compliant. Documentation correctly reflects the CLI exception hierarchy.
**Date Last Resolved:** 2025-06-17
---
**Issue ID:** FLAW-20250601-003
**Original Description (Concise):** Doc inaccuracy in architecture.md project structure
**Initial Resolution Summary (Concise):** Initial fixes added `exceptions.py` and other files to the diagram.
**Date First Resolved:** 2025-06-02
**Reopen Count:** 0
**Last Reopened Date:**
**Last Resolution Summary (Concise):** Still compliant. `docs/architecture.md` now correctly represents the `src/meqsap/cli/` as a package with its submodules.
**Date Last Resolved:** 2025-06-17
---
**Issue ID:** FLAW-20250601-004
**Original Description (Concise):** Doc error in adr-002-date-range-handling.md validation logic
**Initial Resolution Summary (Concise):**
Corrected the example validation logic in `docs/adr/adr-002-date-range-handling.md` (section "Internal Implementation") to reflect the actual correct check, ensuring data for the inclusive `end_date` is present after yfinance fetching and adjustment.
**Date First Resolved:** 2025-06-02
**Reopen Count:** 0
**Last Reopened Date:**
**Last Resolution Summary (Concise):** Still compliant. The validation logic example in the ADR is correct.
**Date Last Resolved:** 2025-06-17
---
**Issue ID:** FLAW-20250602-001
**Original Description (Concise):** Incorrect error handling and exit code (5 instead of 10) for unexpected exceptions in `cli.py`. Type hint violation for error handling utility functions.
**Initial Resolution Summary (Concise):**
The error handling logic in `src/meqsap/cli.py` was updated to ensure that unexpected exceptions are caught and mapped to exit code 10, and all error handling utility functions now have correct type hints. Verified by running CLI error scenarios and mypy checks.
**Date First Resolved:** 2025-06-02
**Reopen Count:** 0
**Last Reopened Date:**
**Last Resolution Summary (Concise):** Still compliant. The `handle_cli_errors` decorator correctly maps exceptions to exit codes.
**Date Last Resolved:** 2025-06-17
---
**Issue ID:** FLAW-20250602-002
**Original Description (Concise):** Default Pass for Data Coverage Check. The `perform_vibe_checks` function defaults `data_coverage_pass` to `True` with a permissive message if a strategy (derived from `BaseStrategyParams`) does not override `get_required_data_coverage_bars` to return a specific number of bars (i.e., if it returns `None`). This means new strategies that require significant historical data but fail to implement this method correctly will silently bypass the data coverage vibe check.
**Initial Resolution Summary (Concise):**
The resolution for this issue involved two key changes:
1. The `get_required_data_coverage_bars` method in `src/meqsap/config.py::BaseStrategyParams` was made an abstract method, forcing all concrete strategy parameter classes to explicitly define their data coverage requirements. This prevents silent bypass of the data coverage vibe check.
2. The `perform_vibe_checks` function was modified to explicitly fail the data coverage check if `get_required_data_coverage_bars` returns `None`, adding a clear "FAILED" message. This ensures that strategies cannot pass the vibe check without declaring their minimum data requirements.
**Date First Resolved:** 2025-06-02
**Reopen Count:** 0
**Last Reopened Date:**
**Last Resolution Summary (Concise):** Still compliant. `get_required_data_coverage_bars` is an abstract method, and `perform_vibe_checks` correctly handles its absence.
**Date Last Resolved:** 2025-06-17
---
**Issue ID:** FLAW-20250610-001
**Original Description (Concise):** Critical Logic Failure: A type mismatch in the call chain for the `analyze` and `optimize` commands. `run_complete_backtest` was called with inconsistent types for its `strategy_config` parameter (a `StrategyConfig` object from the CLI path, and a `dict` from the optimizer path), breaking the API contract.
**Initial Resolution Summary (Concise):** Refactored the call chain. The optimizer engine now creates a `StrategyConfig` object for each trial, injecting the trial's specific parameters. The `run_complete_backtest` and `generate_signals` function signatures were simplified to remove the redundant `concrete_params` argument, creating a consistent and robust API.
**Date First Resolved:** 2025-06-11
**Reopen Count:** 0
**Last Reopened Date:** 
**Last Resolution Summary (Concise):** Still compliant. The API contract between the optimizer and backtesting engine has been strengthened, improving overall system integrity.
**Date Last Resolved:** 2025-06-17
---
