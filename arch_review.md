# MEQSAP Architectural Review - 2025-06-01

This document outlines architectural directives, new critical flaws, and strategic imperatives identified during the audit.

**Audit Date:** 2025-06-01

## Part 1A: Compliance Audit of Prior Architectural Mandates

No prior `arch_review.md` was provided or it was empty. This audit establishes the baseline. All new findings are documented in Part 1B.

## Part 1B: New Critical Architectural Flaws

**-- NEW CRITICAL ARCHITECTURAL FLAW --**
**Issue ID:** FLAW-20250601-001
**Category:** Architectural Degeneration (Violation of ADR-004 and memory.md)
**Location:** `src/meqsap/config.py` (local `ConfigError` definition), `src/meqsap/cli.py` (imports)
**Description:** `src/meqsap/config.py` defines a local `ConfigError` class, which is redundant with `ConfigurationError` from `src/meqsap/exceptions.py`. The `cli.py` module imports both, creating ambiguity. The local `ConfigError` in `config.py` is not actually raised by the module itself; `ConfigurationError` from `exceptions.py` is used instead. This directly violates ADR-004's established exception hierarchy and the guidance in `docs/memory.md` to use a single source of truth for exceptions (`exceptions.py`).
**Consequences:** Reduced code clarity, potential for inconsistent error handling, increased maintenance overhead, and confusion for developers. Violates established architectural decisions.
**Justification for Criticality:** Undermines the established error handling policy (ADR-004) and introduces an explicit anti-pattern documented in `memory.md`. This can lead to systemic issues in error management if not rectified.
**Root Cause Analysis:** Introduction of a duplicate exception class locally instead of reusing the centrally defined one. Likely an oversight or misunderstanding of the existing error handling framework.
**Systemic Prevention Mandate:**
1. Mandate removal of the local `ConfigError` from `src/meqsap/config.py`.
2. Update `src/meqsap/cli.py` to exclusively import and use `ConfigurationError` from `src/meqsap/exceptions.py`.
3. Reinforce during code reviews that all MEQSAP-specific exceptions must originate from `exceptions.py` as per ADR-004.
4. Add a linting rule or pre-commit hook (if feasible) to detect duplicate exception class definitions or imports that violate the established pattern.

**-- NEW CRITICAL ARCHITECTURAL FLAW --**
**Issue ID:** FLAW-20250601-002
**Category:** Documentation Misalignment (ADR/Policy vs. Implementation)
**Location:** `docs/adr/004-error-handling-policy.md`, `docs/policies/error-handling-policy.md`, `src/meqsap/cli.py`, `src/meqsap/exceptions.py`
**Description:** The CLI-specific exceptions `DataAcquisitionError`, `BacktestExecutionError`, and `ReportGenerationError` (all subclasses of `CLIError` defined in `src/meqsap/exceptions.py`) are used in `src/meqsap/cli.py` for distinct exit codes and recovery suggestions. However, these specific exceptions are not documented in the main exception hierarchy diagram in `docs/adr/004-error-handling-policy.md` nor in the "Exception Mapping" table in `docs/policies/error-handling-policy.md`. These documents only list the parent `CLIError`.
**Consequences:** Developers referencing the ADR or policy document will have an incomplete understanding of the error types they might encounter or need to handle from the CLI, potentially leading to incorrect error management or overlooked specific error cases. Documentation does not accurately reflect the implemented, more granular error handling in the CLI.
**Justification for Criticality:** Accurate documentation of the error handling framework is crucial for maintainability and developer understanding. Misalignment can lead to bugs or improper error handling strategies.
**Root Cause Analysis:** The CLI's error handling evolved to be more specific than initially documented in the ADR/policy, and the documentation was not updated to reflect this refinement.
**Systemic Prevention Mandate:**
1. Update the exception hierarchy diagram in `docs/adr/004-error-handling-policy.md` to include `DataAcquisitionError`, `BacktestExecutionError`, and `ReportGenerationError` as subclasses of `CLIError`.
2. Update the "Exception Mapping" table in `docs/policies/error-handling-policy.md` to list these specific CLI exceptions and their use cases/exit codes.
3. Establish a process where changes to core components like exception hierarchies automatically trigger a documentation review and update.

**-- NEW CRITICAL ARCHITECTURAL FLAW --**
**Issue ID:** FLAW-20250601-003
**Category:** Documentation Inaccuracy (Architectural Diagram)
**Location:** `docs/architecture.md` (Project Structure diagram)
**Description:** The "Project Structure" diagram in `docs/architecture.md` is outdated/incomplete. It omits `src/meqsap/exceptions.py`, which is a key file for the error handling framework (ADR-004). It also omits the `examples/` directory and doesn't detail the contents of `docs/` (like `adr/`, `policies/`, etc.), which contain critical policy and decision records.
**Consequences:** Developers relying on `architecture.md` for an overview of the project structure will get an incomplete picture, potentially leading to misunderstandings about module organization or where to find certain types of code (like custom exceptions or ADRs).
**Justification for Criticality:** Architectural documentation must accurately reflect the codebase structure for it to be a reliable reference. Outdated diagrams hinder onboarding and can lead to architectural drift.
**Root Cause Analysis:** The project structure evolved after the architectural diagram was created, and the diagram was not updated.
**Systemic Prevention Mandate:**
1. Update the "Project Structure" diagram in `docs/architecture.md` to include `src/meqsap/exceptions.py`, the `examples/` directory, and a more representative view of the `docs/` subdirectories and their key contents.
2. Implement a periodic review of core architectural diagrams against the current codebase as part of major release cycles or significant refactoring efforts.
3. Consider tools that can auto-generate parts of the project structure documentation to reduce manual effort and ensure accuracy.

**-- NEW CRITICAL ARCHITECTURAL FLAW --**
**Issue ID:** FLAW-20250601-004
**Category:** Documentation Error (ADR Content Incorrect)
**Location:** `docs/adr/adr-002-date-range-handling.md` (Validation logic description)
**Description:** ADR-002 states that `data.py`'s validation logic for `end_date` inclusiveness is: `dates.max() < pd.Timestamp(end_date - timedelta(days=1))`. This logic is incorrect. If `end_date` is '2022-12-31', this checks if `dates.max()` is less than '2022-12-30', implying the last data point is '2022-12-29' or earlier, which contradicts the inclusive `end_date` goal. The actual implementation in `src/meqsap/data.py` correctly checks `if dates.max() < expected_end:`, where `expected_end` is the user-specified inclusive end date. The ADR documentation contains erroneous example validation logic.
**Consequences:** Developers referencing the ADR for implementing or verifying date handling might replicate the incorrect validation logic or misunderstand the correct implementation. This can lead to off-by-one errors in date range handling if the ADR's incorrect example is followed.
**Justification for Criticality:** ADRs are architectural decision records and must be accurate. An error in a critical ADR concerning data handling conventions can lead to data integrity issues or regressions.
**Root Cause Analysis:** A typographical or logical error was made when documenting the example validation logic in ADR-002.
**Systemic Prevention Mandate:**
1. Correct the example validation logic in `docs/adr/adr-002-date-range-handling.md`. The sentence "Validation logic accounts for this adjustment: `dates.max() < pd.Timestamp(end_date - timedelta(days=1))` verifies the last data point is for the user-specified end_date" should be revised to accurately reflect how to verify data for the inclusive `end_date` (e.g., "Validation logic ensures data for the inclusive `end_date` is present, such as `dates.max() >= pd.Timestamp(end_date)` after yfinance fetching and adjustment.").
2. Ensure all ADRs are peer-reviewed not just for the decision but also for the accuracy of any example code or logic provided within them.
3. When code implementing an ADR changes, the ADR itself must be reviewed for continued accuracy.

## Part 2: Strategic Architectural Imperatives

No new strategic architectural imperatives are proposed at this time. Focus should be on rectifying the critical flaws identified in Part 1B.

## Part 3: Actionable Technical Debt Rectification

Refer to `technical_debt.md` for new and updated technical debt items logged during this audit.

## Part 4: Audit Conclusion & Next Steps Mandate

1.  **Critical Path to Compliance:**
    * **Highest Priority:** Resolve FLAW-20250601-001 (Duplicate ConfigError) and FLAW-20250601-004 (ADR-002 Incorrect Validation Logic). These involve direct violations of existing ADRs and potential for error propagation.
    * **Second Priority:** Resolve FLAW-20250601-002 (Documentation Misalignment for CLI Exceptions) and FLAW-20250601-003 (Architecture Diagram Inaccuracy). These are critical for documentation integrity and developer understanding.
2.  **System Integrity Verdict:** The system's architectural integrity is **STAGNATED**. While core functionality exists and some ADRs are in place, the presence of direct ADR violations (FLAW-20250601-001, FLAW-20250601-004) and significant documentation drift (FLAW-20250601-002, FLAW-20250601-003) indicates a lack of consistent adherence to established architectural principles. No re-opened issues were identified from a prior cycle as this is a baseline audit.
3.  **`arch_review.md` Update Instruction:** The content from Part 1B of this audit (New Critical Architectural Flaws) forms the basis for the `arch_review.md` for the next audit cycle. All items listed require resolution.
4.  **`resolved_issues.md` Maintenance Confirmation:** `resolved_issues.md` has been created. No issues were marked as RESOLVED in this cycle as it's a baseline audit. No issues were re-opened from a previous `resolved_issues.md` as it was not provided.
