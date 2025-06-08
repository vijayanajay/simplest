# Resolved Architectural Issues Log

This file tracks issues that have been resolved, including their re-open history.

**Last Updated:** 2025-06-10

---
**Issue ID:** FLAW-20250601-001
**Original Description (Concise):** Local ConfigError in config.py
**Initial Resolution Summary (Concise):**
The local `ConfigError` definition was removed from `src/meqsap/config.py`. The `src/meqsap/cli.py` module was verified to exclusively import and use `ConfigurationError` from `src/meqsap/exceptions.py`, adhering to `docs/adr/004-error-handling-policy.md`.
**Date First Resolved:** 2025-06-02
**Reopen Count:** 0
**Last Reopened Date:**
**Last Resolution Summary (Concise):** The local `ConfigError` definition was removed from `src/meqsap/config.py`. The `src/meqsap/cli.py` module was verified to exclusively import and use `ConfigurationError` from `src/meqsap/exceptions.py`, adhering to `docs/adr/004-error-handling-policy.md`.
**Date Last Resolved:** 2025-06-02
---
**Issue ID:** FLAW-20250601-002
**Original Description (Concise):** Doc misalignment for CLI exceptions
**Initial Resolution Summary (Concise):**
The exception hierarchy diagram in `docs/adr/004-error-handling-policy.md` and the "Exception Mapping" table in `docs/policies/error-handling-policy.md` were verified to include the CLI-specific exceptions (`DataAcquisitionError`, `BacktestExecutionError`, `ReportGenerationError`) as subclasses of `CLIError`, aligning documentation with the implemented error handling.
**Date First Resolved:** 2025-06-02
**Reopen Count:** 0
**Last Reopened Date:**
**Last Resolution Summary (Concise):** The exception hierarchy diagram in `docs/adr/004-error-handling-policy.md` and the "Exception Mapping" table in `docs/policies/error-handling-policy.md` were verified to include the CLI-specific exceptions (`DataAcquisitionError`, `BacktestExecutionError`, `ReportGenerationError`) as subclasses of `CLIError`, aligning documentation with the implemented error handling.
**Date Last Resolved:** 2025-06-02
---
**Issue ID:** FLAW-20250601-003
**Original Description (Concise):** Doc inaccuracy in architecture.md project structure
**Initial Resolution Summary (Concise):**
The "Project Structure" diagram in `docs/architecture.md` was verified to include `src/meqsap/exceptions.py`, the `examples/` directory, and details of the `docs/` subdirectories (e.g., `adr/`, `policies/`), accurately reflecting the current project structure.
**Date First Resolved:** 2025-06-02
**Reopen Count:** 0
**Last Reopened Date:**
**Last Resolution Summary (Concise):** The "Project Structure" diagram in `docs/architecture.md` was verified to include `src/meqsap/exceptions.py`, the `examples/` directory, and details of the `docs/` subdirectories (e.g., `adr/`, `policies/`), accurately reflecting the current project structure.
**Date Last Resolved:** 2025-06-02
---
**Issue ID:** FLAW-20250601-004
**Original Description (Concise):** Doc error in adr-002-date-range-handling.md validation logic
**Initial Resolution Summary (Concise):**
Corrected the example validation logic in `docs/adr/adr-002-date-range-handling.md` (section "Internal Implementation") to reflect the actual correct check, ensuring data for the inclusive `end_date` is present after yfinance fetching and adjustment.
**Date First Resolved:** 2025-06-02
**Reopen Count:** 0
**Last Reopened Date:**
**Last Resolution Summary (Concise):** Corrected the example validation logic in `docs/adr/adr-002-date-range-handling.md` (section "Internal Implementation") to reflect the actual correct check, ensuring data for the inclusive `end_date` is present after yfinance fetching and adjustment.
**Date Last Resolved:** 2025-06-02
---
**Issue ID:** FLAW-20250602-001
**Original Description (Concise):** Incorrect error handling and exit code (5 instead of 10) for unexpected exceptions in `cli.py`. Type hint violation for error handling utility functions.
**Initial Resolution Summary (Concise):**
The error handling logic in `src/meqsap/cli.py` was updated to ensure that unexpected exceptions are caught and mapped to exit code 10, and all error handling utility functions now have correct type hints. Verified by running CLI error scenarios and mypy checks.
**Date First Resolved:** 2025-06-02
**Reopen Count:** 0
**Last Reopened Date:**
**Last Resolution Summary (Concise):** The error handling logic in `src/meqsap/cli.py` was updated to ensure that unexpected exceptions are caught and mapped to exit code 10, and all error handling utility functions now have correct type hints. Verified by running CLI error scenarios and mypy checks.
**Date Last Resolved:** 2025-06-02
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
**Last Resolution Summary (Concise):** The resolution for this issue involved two key changes: 1. The `get_required_data_coverage_bars` method in `src/meqsap/config.py::BaseStrategyParams` was made an abstract method. 2. The `perform_vibe_checks` function was modified to explicitly fail the data coverage check if `get_required_data_coverage_bars` returns `None`.
**Date Last Resolved:** 2025-06-02
---
