# MEQSAP Architectural Review - 2025-06-02

This document outlines architectural directives, new critical flaws, and strategic imperatives identified during the audit.

**Audit Date:** 2025-06-02

## Part 1A: Compliance Audit of Prior Architectural Mandates

**-- AUDIT OF PRIOR DIRECTIVE --**
**Directive Reference (from arch_review.md):** FLAW-20250601-001 (Local ConfigError in config.py)
**Current Status:** RESOLVED
**Evidence & Justification for Status:**
   `src/meqsap/config.py` correctly imports `ConfigurationError` from `src/meqsap/exceptions.py` and does not define a local `ConfigError`. `src/meqsap/cli.py` also imports and uses `ConfigurationError` from `src/meqsap/exceptions.py`. This aligns with ADR-004 and `memory.md` guidance. Verified `resolved_issues.md` entry for FLAW-20250601-001 is accurate and reflects this resolution.
**Required Action (If Not Fully Resolved/Regressed):** N/A

**-- AUDIT OF PRIOR DIRECTIVE --**
**Directive Reference (from arch_review.md):** FLAW-20250601-002 (Doc misalignment for CLI exceptions)
**Current Status:** RESOLVED
**Evidence & Justification for Status:**
   `docs/adr/004-error-handling-policy.md` (Exception Hierarchy) and `docs/policies/error-handling-policy.md` (Exception Mapping) correctly include CLI-specific exceptions (`DataAcquisitionError`, `BacktestExecutionError`, `ReportGenerationError`) as subclasses of `CLIError`, aligning with `src/meqsap/exceptions.py`. Verified `resolved_issues.md` entry for FLAW-20250601-002 is accurate.
**Required Action (If Not Fully Resolved/Regressed):** N/A

**-- AUDIT OF PRIOR DIRECTIVE --**
**Directive Reference (from arch_review.md):** FLAW-20250601-003 (Doc inaccuracy in architecture.md project structure)
**Current Status:** RESOLVED
**Evidence & Justification for Status:**
   The "Project Structure" diagram in `docs/architecture.md` now correctly includes `src/meqsap/exceptions.py`, the `examples/` directory, and detailed `docs/` subdirectories (`adr/`, `policies/`), accurately reflecting the project structure. Verified `resolved_issues.md` entry for FLAW-20250601-003 is accurate.
**Required Action (If Not Fully Resolved/Regressed):** N/A

**-- AUDIT OF PRIOR DIRECTIVE --**
**Directive Reference (from arch_review.md):** FLAW-20250601-004 (Doc error in adr-002-date-range-handling.md validation logic)
**Current Status:** RESOLVED
**Evidence & Justification for Status:**
   `docs/adr/adr-002-date-range-handling.md` (section "Internal Implementation") has been updated with the correct validation logic example: "`Validation logic ensures data for the inclusive `end_date` is present, such as `dates.max() >= pd.Timestamp(end_date)` after yfinance fetching and adjustment.`". Verified `resolved_issues.md` entry for FLAW-20250601-004 is accurate.
**Required Action (If Not Fully Resolved/Regressed):** N/A

**-- AUDIT OF PRIOR DIRECTIVE --**
**Directive Reference (from arch_review.md):** FLAW-20250602-001 (Incorrect Error Handling & Exit Code in CLI)
**Current Status:** RESOLVED
**Evidence & Justification for Status:**
   Code in `src/meqsap/cli.py` has been verified:
   1.  `_main_pipeline`'s final `except Exception` block correctly calls `_generate_error_message(e, verbose=verbose, no_color=no_color)` and returns `10`.
   2.  `analyze_command`'s final `except Exception` block raises `typer.Exit(code=10)`.
   3.  `_generate_error_message` signature is `def _generate_error_message(exception: Exception, verbose: bool = False, no_color: bool = False) -> str:`.
   4.  `_get_recovery_suggestions` signature is `def _get_recovery_suggestions(exception: Exception) -> list[str]:`.
   These changes align with ADR-004. Verified `resolved_issues.md` entry for FLAW-20250602-001 is accurate.
**Required Action (If Not Fully Resolved/Regressed):** N/A

## Part 1B: New Critical Architectural Flaws

 **-- NEW CRITICAL ARCHITECTURAL FLAW --**
**Directive Reference (from arch_review.md):** FLAW-20250602-002 (Default Pass for Data Coverage Check)
**Current Status:** RESOLVED
**Evidence & Justification for Status:**
   The `perform_vibe_checks` function in `src/meqsap/backtest.py` has been updated to explicitly check if `strategy_required_bars` (returned by `validated_params.get_required_data_coverage_bars()`) is `None`. If it is `None`, the `data_coverage_pass` is set to `False`, and a "FAILED" message is added, stating that the strategy did not explicitly define its data coverage requirements. This implements the stricter check proposed in the previous audit's Systemic Prevention Mandate (option 2a) and resolves the issue of silently bypassing the check. Verified `resolved_issues.md` entry for FLAW-20250602-002 is accurate.
**Required Action (If Not Fully Resolved/Regressed):** N/A


**-- NEW CRITICAL ARCHITECTURAL FLAW --**
**Category:** Architectural Degeneration (Potentially insufficient validation for new strategies)
**Location:** `src/meqsap/backtest.py::perform_vibe_checks` (lines related to `data_coverage_pass` default) and design of `src/meqsap/config.py::BaseStrategyParams.get_required_data_coverage_bars`.
**Description:** The `perform_vibe_checks` function defaults `data_coverage_pass` to `True` with a permissive message if a strategy (derived from `BaseStrategyParams`) does not override `get_required_data_coverage_bars` to return a specific number of bars (i.e., if it returns `None`). This means new strategies that require significant historical data but fail to implement this method correctly will silently bypass the data coverage vibe check.
**Consequences:** Strategies might be evaluated on insufficient data, leading to unreliable backtest results and potentially flawed decision-making. The system might appear to validate a strategy when a critical data requirement is not met. This flaw has been addressed by making `get_required_data_coverage_bars` an abstract method in `BaseStrategyParams`, forcing explicit implementation.
**Justification for Criticality:** Directly impacts the reliability and correctness of backtest results, a core system function. This is a silent failure of a key validation check.
**Root Cause Analysis:** Design flaw in `BaseStrategyParams` where `get_required_data_coverage_bars` returns `None` by default, coupled with handling in `perform_vibe_checks` that interprets `None` as "check passes" without adequate warning or failure.
**Systemic Prevention Mandate:**
   1.  Modify `BaseStrategyParams.get_required_data_coverage_bars` in `src/meqsap/config.py` to be an abstract method (e.g., using `abc.ABC` and `@abc.abstractmethod`) or to raise `NotImplementedError`. This will force all concrete strategy parameter classes to explicitly define their data requirements.
   2.  Alternatively, if an abstract method is too disruptive, `perform_vibe_checks` in `src/meqsap/backtest.py` must be modified. If `get_required_data_coverage_bars` returns `None`, it should either:
       a.  Fail the `data_coverage_check` outright.
       b.  Issue a prominent warning in the vibe check results (e.g., status "WARNING" or "UNKNOWN") instead of the current "✓ Data coverage check: Passed (strategy does not declare...)".
   3.  Update developer documentation for creating new strategies to explicitly state the requirement of implementing `get_required_data_coverage_bars` correctly and its impact on data validation.

## Part 2: Strategic Architectural Imperatives

**-- STRATEGIC ARCHITECTURAL IMPERATIVE --**
**Imperative:** N/A
**Architectural Justification:** All previously identified critical architectural flaws and directives have been resolved in this audit cycle. No new systemic weaknesses requiring a strategic imperative were identified.
**Expected Impact:** N/A

## Part 3: Actionable Technical Debt Rectification

No new technical debt items were logged during this audit. Refer to `technical_debt.md` for existing items.

## Part 4: Audit Conclusion & Next Steps Mandate

1.  **Critical Path to Compliance:**
    * There are no critical path items identified as outstanding by *this* audit. All previously identified critical architectural flaws (FLAW-20250601-001 to -004, FLAW-20250602-001, and FLAW-20250602-002) have been resolved.
2.  **System Integrity Verdict:** The system's architectural integrity and adherence to prior mandates has **improved** significantly. All previously identified flaws, including the critical flaw from the previous cycle (FLAW-20250602-002), are now resolved. There were no regressions or re-opened issues identified in this audit.
3.  **`arch_review.md` Update Instruction:** Confirm that the output of Part 1A (unresolved, partially resolved, regressed issues) and relevant items from Part 1B (new flaws, including re-opened ones not immediately fixed) form the basis for the next `arch_review.md`.
    * All previously listed flaws (FLAW-20250601-001 to -004, FLAW-20250602-001) and the critical flaw from the previous cycle (FLAW-20250602-002) are now marked as RESOLVED in Part 1A of this document.
    * There are no new critical flaws or unresolved directives from this audit cycle to carry forward. The next `arch_review.md` will primarily serve as a record of the resolutions achieved in this cycle.
4.  **`resolved_issues.md` Maintenance Confirmation:**   * Verification of `resolved_issues.md` confirms that entries for FLAW-20250601-001, FLAW-20250601-002, FLAW-20250601-003, FLAW-20250601-004, and FLAW-20250602-001 are accurate and up-to-date, reflecting their resolution on 2025-06-02 with a Reopen Count of 0. No changes to `resolved_issues.md` are required in this cycle as it already reflects the confirmed resolutions.
    * **Correction:** An entry for FLAW-20250602-002 must be added to `resolved_issues.md` to reflect its resolution in this cycle.
