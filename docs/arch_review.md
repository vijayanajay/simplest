# MEQSAP Architectural Review - 2025-06-10

This document outlines architectural directives, new critical flaws, and strategic imperatives identified during the audit.

**Audit Date:** 2025-06-10

## Part 1A: Compliance Audit of Prior Architectural Mandates

**-- AUDIT OF PRIOR DIRECTIVE --**
**Directive Reference (from arch_review.md):** FLAW-20250601-001 (Local ConfigError in config.py)
**Current Status:** RESOLVED
**Evidence & Justification for Status:**
   Code in `src/meqsap/config.py` and `src/meqsap/cli/__init__.py` correctly imports and uses the canonical `ConfigurationError` from `src/meqsap/exceptions.py`. The local definition has been removed. This remains compliant with ADR-004.
**Required Action (If Not Fully Resolved/Regressed):** N/A

**-- AUDIT OF PRIOR DIRECTIVE --**
**Directive Reference (from arch_review.md):** FLAW-20250601-002 (Doc misalignment for CLI exceptions)
**Current Status:** RESOLVED
**Evidence & Justification for Status:**
   Documentation in `docs/adr/004-error-handling-policy.md` and `docs/policies/error-handling-policy.md` correctly reflects the CLI-specific exception hierarchy (`DataAcquisitionError`, etc.) as implemented in `src/meqsap/exceptions.py`. This remains compliant.
**Required Action (If Not Fully Resolved/Regressed):** N/A

**-- AUDIT OF PRIOR DIRECTIVE --**
**Directive Reference (from arch_review.md):** FLAW-20250601-003 (Doc inaccuracy in architecture.md project structure)
**Current Status:** UNRESOLVED
**Evidence & Justification for Status:**
   While some previous inaccuracies were fixed, a new one has been introduced by recent refactoring. The "Project Structure" diagram and component descriptions in `docs/architecture.md` still refer to `src/meqsap/cli.py` as a single file. The codebase has refactored this into a full package at `src/meqsap/cli/` with submodules (`commands/`, `utils.py`). This makes the architectural documentation misleading and out of sync with the implementation.
**Required Action (If Not Fully Resolved/Regressed):**
   1. Update the "Project Structure" diagram in `docs/architecture.md` to accurately reflect the `src/meqsap/cli/` package structure.
   2. Update the "Component View" and associated Mermaid diagrams to refer to the `cli` module/package instead of `cli.py`, and describe its new internal structure.

**-- AUDIT OF PRIOR DIRECTIVE --**
**Directive Reference (from arch_review.md):** FLAW-20250601-004 (Doc error in adr-002-date-range-handling.md validation logic)
**Current Status:** RESOLVED
**Evidence & Justification for Status:**
   The validation logic example in `docs/adr/adr-002-date-range-handling.md` remains correct and accurately reflects the inclusive `end_date` handling policy.
**Required Action (If Not Fully Resolved/Regressed):** N/A

**-- AUDIT OF PRIOR DIRECTIVE --**
**Directive Reference (from arch_review.md):** FLAW-20250602-001 (Incorrect Error Handling & Exit Code in CLI)
**Current Status:** RESOLVED
**Evidence & Justification for Status:**
   The `handle_cli_errors` decorator in `src/meqsap/cli/utils.py` correctly maps exceptions to exit codes as per ADR-004, including the catch-all `Exception` to exit code 10. The signatures for error handling utilities remain correct. This is compliant.
**Required Action (If Not Fully Resolved/Regressed):** N/A

**-- AUDIT OF PRIOR DIRECTIVE --**
**Directive Reference (from arch_review.md):** FLAW-20250602-002 (Default Pass for Data Coverage Check)
**Current Status:** RESOLVED
**Evidence & Justification for Status:**
   The `get_required_data_coverage_bars` method in `src/meqsap/config.py::BaseStrategyParams` remains an abstract method, and `perform_vibe_checks` in `src/meqsap/backtest.py` correctly fails the check if the requirement is not met. This is compliant.
**Required Action (If Not Fully Resolved/Regressed):** N/A

## Part 1B: New Critical Architectural Flaws

**-- NEW CRITICAL ARCHITECTURAL FLAW --**
**Category:** Critical Logic Failure
**Location:** `src/meqsap/cli/__init__.py` (in `_main_pipeline` and `_execute_backtest_pipeline`) and `src/meqsap/backtest.py` (in `run_complete_backtest`).
**Description:** A type mismatch in the call chain breaks the `analyze` command. The function `_execute_backtest_pipeline` passes a `BaseStrategyParams` object to `run_complete_backtest`. This function then passes the object to `StrategySignalGenerator.generate_signals` as the `concrete_params` argument, which expects a `dict`. This causes a `TypeError` at runtime when the signal generator attempts to access dictionary keys (e.g., `params['fast_ma']`) on the Pydantic object.
**Consequences:** The primary `analyze` workflow of the application is broken and will always fail with a `TypeError`.
**Justification for Criticality:** This is a regression that breaks a core user-facing feature.
**Root Cause Analysis:** The error was likely introduced during a refactoring of the CLI pipeline. The function signature of `_execute_backtest_pipeline` was changed to explicitly accept `strategy_params`, but the downstream consumer (`run_complete_backtest`) was not updated to handle this object correctly, breaking the contract between the functions. The redundancy of passing `strategy_params` when it's already contained within the `config` object contributed to the confusion.
**Systemic Prevention Mandate:**
1.  **Stricter Type Enforcement:** `mypy` checks must be integrated into the CI/CD pipeline to catch such type mismatches before merge.
2.  **Integration Testing:** A basic integration test for the `analyze` command's "happy path" must be created to prevent regressions of the core workflow.
3.  **Refactoring Discipline:** When refactoring function signatures, all call sites, including those in other modules, must be verified. Redundant parameter passing should be eliminated to simplify data flow and reduce the chance of such errors.

## Part 2: Strategic Architectural Imperatives

**-- STRATEGIC ARCHITECTURAL IMPERATIVE --**
**Imperative:** N/A
**Architectural Justification:** All previously identified critical architectural flaws and directives have been resolved in this audit cycle. No new systemic weaknesses requiring a strategic imperative were identified.
**Expected Impact:** N/A

## Part 3: Actionable Technical Debt Rectification

No new technical debt items were logged. The critical flaw identified in Part 1B is a bug that must be fixed immediately, not deferred as debt.
- `TD-20250601-001` (Ambiguity in `run_backtest`): Remains NOT STARTED. The fix for the new critical flaw will simplify the call chain, which is a step towards addressing this debt.
- `TD-20250601-002` (Overly Permissive `safe_float` Conversion): Confirmed as ADDRESSED.
- `TD-20250601-003` (Fragile Close Price Column Discovery): Confirmed as ADDRESSED.

## Part 4: Audit Conclusion & Next Steps Mandate

 1.  **Critical Path to Compliance:**
    *   **1. Fix Critical Logic Failure:** The `TypeError` in the `analyze` command pipeline must be fixed immediately. This involves simplifying the call chain in `src/meqsap/cli/__init__.py` to remove redundant parameter passing.
    *   **2. Fix Documentation Drift:** The `docs/architecture.md` file must be updated to reflect the current `cli` package structure.
 2.  **System Integrity Verdict:** **DEGRADED**. A critical regression bug has been introduced that breaks a core feature. While many previous issues remain resolved, the introduction of a new high-severity bug indicates a lapse in testing or review during recent refactoring.
 3.  **`arch_review.md` Update Instruction:** Confirm that the output of Part 1A (unresolved, partially resolved, regressed issues) and relevant items from Part 1B (new flaws, including re-opened ones not immediately fixed) form the basis for the next `arch_review.md`.
    * This document serves as the updated `arch_review.md`. The unresolved issue from Part 1A and the new critical flaw from Part 1B must be addressed in the next development cycle.
 4.  **`resolved_issues.md` Maintenance Confirmation:**
    * No new issues were resolved in this cycle, and no regressions of previously resolved issues occurred. The file does not require updates beyond changing the "Last Updated" date.
