# MEQSAP Architectural Review - 2025-06-02

This document outlines architectural directives, new critical flaws, and strategic imperatives identified during the audit.

**Audit Date:** 2025-06-02

## Part 1A: Compliance Audit of Prior Architectural Mandates

### Previously Identified Critical Flaws - STATUS UPDATE (as of 2025-06-02)

**✅ RESOLVED:** **Issue ID:** FLAW-20250601-001
Category: Architectural Degeneration (Violation of ADR-004 and memory.md)
Location: `src/meqsap/config.py` (local `ConfigError` definition), `src/meqsap/cli.py` (imports)
Resolution Date: 2025-06-02
**Initial Resolution Summary:** The local `ConfigError` definition was removed from `src/meqsap/config.py`. The `src/meqsap/cli.py` module was verified to exclusively import and use `ConfigurationError` from `src/meqsap/exceptions.py`, adhering to ADR-004.

**✅ RESOLVED:** **Issue ID:** FLAW-20250601-002
Category: Documentation Misalignment (ADR/Policy vs. Implementation)
Location: `docs/adr/004-error-handling-policy.md`, `docs/policies/error-handling-policy.md`, `src/meqsap/cli.py`, `src/meqsap/exceptions.py`
Resolution Date: 2025-06-02
**Initial Resolution Summary:** The exception hierarchy diagram in `docs/adr/004-error-handling-policy.md` and the "Exception Mapping" table in `docs/policies/error-handling-policy.md` were verified to include the CLI-specific exceptions (`DataAcquisitionError`, `BacktestExecutionError`, `ReportGenerationError`) as subclasses of `CLIError`, aligning documentation with the implemented error handling.

**✅ RESOLVED:** **Issue ID:** FLAW-20250601-003
Category: Documentation Inaccuracy (Architectural Diagram)
Location: `docs/architecture.md` (Project Structure diagram)
Resolution Date: 2025-06-02
**Initial Resolution Summary:** The "Project Structure" diagram in `docs/architecture.md` was verified to include `src/meqsap/exceptions.py`, the `examples/` directory, and details of the `docs/` subdirectories (e.g., `adr/`, `policies/`), accurately reflecting the current project structure.

**✅ RESOLVED:** **Issue ID:** FLAW-20250601-004
Category: Documentation Error (ADR Content Incorrect)
Location: `docs/adr/adr-002-date-range-handling.md` (Validation logic description)
Resolution Date: 2025-06-02
**Initial Resolution Summary:** The file `docs/adr/adr-002-date-range-handling.md` (section "Internal Implementation") was verified to contain the corrected validation logic example: "`Validation logic ensures data for the inclusive `end_date` is present, such as `dates.max() >= pd.Timestamp(end_date)` after yfinance fetching and adjustment.`". This aligns with the required correction for FLAW-20250601-004, which had pointed out an older, incorrect example logic in the ADR. The ADR documentation now accurately reflects the intended validation.

## Part 1B: New Critical Architectural Flaws

**Issue ID:** FLAW-20250602-001
**Category:** Critical Logic Failure & Architectural Degeneration (Incorrect Error Handling & Exit Code for Unexpected Exceptions)
**Location:** `src/meqsap/cli.py` (function `analyze_command`, final `except Exception as e:` block; function `_main_pipeline`, final `except Exception as e:` block) and `_generate_error_message`, `_get_recovery_suggestions` function signatures.
**Description:**
    1.  The `analyze_command`'s final `except Exception as e:` block uses `raise typer.Exit(code=5)` for unexpected exceptions. This contradicts ADR-004 and `docs/policies/error-handling-policy.md`, which specify exit code `10` for "Unexpected/unhandled errors".
    2.  The `_main_pipeline`'s final `except Exception as e:` block incorrectly calls `_generate_error_message` with non-existent parameters (`error_type`, `suggestions`) and also returns `5` instead of `10`.
    3.  The `_generate_error_message` function and the internally called `_get_recovery_suggestions` function have a type hint `exception: MEQSAPError`. However, `_generate_error_message` is called from `analyze_command`'s generic `except Exception as e:` block (and was incorrectly called from `_main_pipeline`'s similar block), where `e` might not be a `MEQSAPError` subclass. This violates the type hint.
**Consequences:**
    1.  Incorrect exit codes mislead users and automation scripts.
    2.  The incorrect call to `_generate_error_message` from `_main_pipeline` would lead to a runtime error if that path was taken.
    3.  Violating the type hint for `_generate_error_message` and `_get_recovery_suggestions` can lead to runtime errors if `MEQSAPError`-specific attributes were accessed (though current internal logic appears safe, the contract is violated).
**Justification for Criticality:** Accurate exit codes and robust, type-safe error handling are fundamental for CLI tools. Deviations from documented policy and type violations can lead to incorrect behavior, obscure root causes, and hinder maintainability.
**Root Cause Analysis:**
    1.  Exit code implementation in `cli.py` diverged from documented policy (ADR-004).
    2.  An incorrect call to `_generate_error_message` was present in `_main_pipeline`.
    3.  Type hints for error handling utility functions did not accurately reflect their usage with generic exceptions.
**Systemic Prevention Mandate:**
1.  In `src/meqsap/cli.py`:
    * In the `_main_pipeline` function, modify the final `except Exception as e:` block:
        * Correct the call to `_generate_error_message` to `_generate_error_message(e, verbose=verbose, no_color=no_color)`.
        * Change `return 5` to `return 10`.
    * In the `analyze_command` function, modify the final `except Exception as e:` block:
        * Change `raise typer.Exit(code=5)` to `raise typer.Exit(code=10)`.
    * Modify the function signature of `_generate_error_message` from `exception: MEQSAPError` to `exception: Exception`.
    * Modify the function signature of `_get_recovery_suggestions` from `exception: MEQSAPError` to `exception: Exception`.
2.  Mandate that code reviews for CLI modules specifically verify adherence to documented exit code policies (ADR-004) and type consistency in error handlers.
3.  Utilize static type checking tools (e.g., MyPy) in the CI pipeline to proactively catch type inconsistencies in error handling paths.

## Part 2: Strategic Architectural Imperatives

No new strategic architectural imperatives are proposed at this time. Focus should be on rectifying the new critical flaw identified in Part 1B (FLAW-20250602-001).

## Part 3: Actionable Technical Debt Rectification

Refer to `technical_debt.md` for new and updated technical debt items logged during this audit.

## Part 4: Audit Conclusion & Next Steps Mandate

1.  **Critical Path to Compliance:**
    * **Priority:** Resolve **FLAW-20250602-001 (Incorrect Error Handling & Exit Code for Unexpected Exceptions)**. This flaw affects CLI reliability and adherence to documented error handling policies.
    * **Progress Update from Prior Cycle:** Successfully resolved FLAW-20250601-004 (ADR-002 Incorrect Validation Logic Documentation). All previously identified flaws (FLAW-20250601-001, FLAW-20250601-002, FLAW-20250601-003, FLAW-20250601-004) are now RESOLVED.
2.  **System Integrity Verdict:** The system's architectural integrity has been **MAINTAINED**. While all previously identified architectural flaws have been resolved, a new critical flaw (FLAW-20250602-001) related to CLI error handling and exit codes has been identified. This new flaw requires immediate attention to ensure adherence to architectural policies and maintain system robustness.
3.  **`arch_review.md` Update Instruction:** Confirm that the output of Part 1A (unresolved, partially resolved, regressed issues) and relevant items from Part 1B (new flaws, including re-opened ones not immediately fixed) form the basis for the next `arch_review.md`.
    * FLAW-20250601-004 is now marked as RESOLVED in Part 1A.
    * FLAW-20250602-001 is documented in Part 1B and is the primary outstanding issue for the next cycle.
4.  **`resolved_issues.md` Maintenance Confirmation:** `resolved_issues.md` has been updated: FLAW-20250601-004 has been added as resolved. No issues were re-opened from the previous cycle.
