# MEQSAP Memory File: Quick Reference Rules

## Package Structure & Imports

### DO ✅
- Create complete `__init__.py` files for package hierarchy
- Verify imports work: `python -c "from src.meqsap.cli import app"`
- Match mock specifications to actual return types (`spec=pd.DataFrame`)
- Use dedicated `main()` function for CLI entry points
- For module/package name collisions: re-export in `__init__.py` (`from ..mod import symbol`)

### DON'T ❌
- Write tests for incomplete package structures
- Rely on `if __name__ == "__main__":` for `python -m` execution
- Use incorrect mock types (e.g., `spec=Path` for DataFrame)
- Create ambiguous import paths without explicit re-export management

## CLI Testing

### DO ✅
- Use proper subcommand syntax: `["analyze", config, "--flag"]`
- Test subcommand help: `["analyze", "--help"]`
- Mock return values: `function.return_value = code`
- Check CLI structure: `python -m src.meqsap.cli --help`

### DON'T ❌
- Use wrong command syntax: `[config, "--flag"]`
- Mock exceptions when testing return codes: `function.side_effect = Exception()`
- Use deprecated Typer arguments (`mix_stderr`)
- Assert exact CLI help text (use key terms instead)

## Configuration & Models

### DO ✅
- Update ALL test fixtures when changing Pydantic models
- Use factory functions for complex model creation
- Add explicit validators for Union types with numeric constraints
- Handle Pydantic model instances in validators: `isinstance(v, ModelClass)`

### DON'T ❌
- Change schemas without updating dependent tests
- Assume Union type validation works automatically
- Use helper functions expecting raw types on model instances

## Exception Handling & Error Codes

### DO ✅
- Use canonical exceptions from `exceptions.py`
- Map specific exceptions to distinct exit codes (follow ADR-004)
- Use specific `except` blocks: `except ConfigurationError`, not `except Exception`

### DON'T ❌
- Create duplicate exception classes in multiple modules
- Use broad `try...except Exception` in CLI commands (masks error types)
- Reference unimplemented methods

## Testing & Mocking

### DO ✅
- Mock at correct module boundaries
- Match external library interfaces: `pd.Index` not `list`
- Mock magic methods directly: `mock_obj.__len__ = Mock(return_value=X)`
- Validate data types early: `pd.to_numeric(errors='coerce')`
- **Instantiate with Mocks Instead of Patching `__init__`:** When testing a class method, prefer instantiating the class with mock dependencies over patching its `__init__` method. This avoids brittle tests that break if the constructor's internal assignments change.
- **When patching `__init__`, ensure all instance attributes accessed by the method under test are initialized in the mock setup to prevent `AttributeError`.**

### DON'T ❌
- Mock with incorrect return types for external libraries
- Attempt `mock_obj.__len__.return_value = X` (causes `AttributeError`)
- Skip data type validation for critical columns
- **Patch `__init__` and fail to mock the complete object state.** This creates brittle tests that break when new attributes are added to the real `__init__`. This was the root cause of a series of `AttributeError` failures in the `OptimizationEngine` tests, where a test fixture patched `__init__` but failed to set `self.strategy_config`, causing all error-handling paths in the method under test to fail and be miscategorized.

## Data Type Safety & Critical Metrics

### DO ✅
- Coerce external library data early: `pd.to_numeric(errors='coerce')`
- Use strict error handling for critical metrics: `raise_on_type_error=True`
- Distinguish critical vs non-critical data handling

### DON'T ❌
- Silent-default critical financial metrics
- Assume external library outputs are always correct types
- Skip early data validation before mathematical operations

## Indicator Framework

### DO ✅
- Instantiate indicators without arguments: `indicator = IndicatorCls()`
- Pass parameters to `calculate()` method: `indicator.calculate(data, **params)`

### DON'T ❌
- Pass parameters to indicator `__init__()` unless explicitly designed for it
- Assume documentation matches implementation without verification

## Cross-Platform Compatibility

### DO ✅
- Use ASCII or widely supported Unicode for CLI output
- Test on Windows and check for `UnicodeEncodeError`
- Include `pytest-mock` in dev dependencies for `mocker` fixture

### DON'T ❌
- Use high-plane Unicode emoji in CLI without fallbacks
- Assume Unicode support across all terminal environments

## Common Debug Patterns

**CLI Exit Code 2:** Check imports → CLI help → subcommand structure → runtime with mocks
**Mass Test Failures:** Often indicates structural issue in core component (incomplete refactoring, missing dependencies)
**Import Ambiguity:** Module/package name collision - fix with re-export in `__init__.py`

## Key Anti-Patterns Summary

1. **Incomplete Refactoring:** Always run full test suite, use specific exception handling
2. **Mock Type Mismatches:** Match external library interfaces exactly
3. **Silent Data Issues:** Critical metrics must "fail loudly" on type errors
4. **Union Type Validators:** Handle both raw types and Pydantic model instances
5. **Magic Method Mocking:** Direct assignment, not `.return_value` manipulation

## CLI Orchestration & Error Handling

### DO ✅ (Corrected Pattern)
- **Use Decorators for Error Handling:** Apply a single, robust error-handling decorator (e.g., `@handle_cli_errors`) to top-level CLI command functions.
- **Centralize Exception-to-Exit-Code Mapping:** The decorator should be responsible for catching specific `MEQSAPError` subclasses and mapping them to the correct integer exit codes as defined in ADR-004.
- **Raise Specific Exceptions:** Pipeline functions (e.g., `_main_pipeline` and its helpers) should raise specific, typed exceptions (`ConfigurationError`, `DataError`, etc.) and let them bubble up to the decorator.
- **CLI Commands Raise Exceptions, Not `typer.Exit`:** Inside a command function, for application logic errors (like `verbose` and `quiet` used together), raise a `ConfigurationError` instead of calling `typer.Exit` directly. This allows the decorator to handle it consistently.
- **CLI Commands Should Not Raise `typer.Exit`:** Inside a command function, application logic should either complete successfully (exiting with 0 implicitly) or raise a specific `MEQSAPError`. The error-handling decorator is solely responsible for converting these exceptions into `typer.Exit` calls with the correct code.

### DON'T ❌
- **Use Generic `except Exception` in Decorators for Specific Errors:** A decorator's `except Exception` block should only handle truly *unexpected* errors. Relying on it to catch specific application errors (like `ConfigurationError`) indicates a structural flaw in the preceding `except` blocks. This was the root cause of numerous test failures where specific errors were incorrectly assigned exit code 10.
- **Call `typer.Exit` from within Command Logic:** Bypassing the error handling decorator by calling `typer.Exit` directly makes error handling inconsistent.

## Anti-Pattern Prevention

- **Pass Validated Objects Explicitly:** When a component (e.g., `_validate_and_load_config`) produces multiple validated objects (e.g., `StrategyConfig` and `StrategyParams`), pass them explicitly down the call chain instead of having downstream functions re-derive them. This improves decoupling.

## Refactoring & Test Maintenance

### DO ✅
- When refactoring a function's signature, use "Find in all files" or IDE tools to locate and update **all** call sites, including those in unit tests.
- Ensure that mock assertions in tests are updated to match the new function signature and call arguments.

### DON'T ❌
- Assume a refactoring is complete just because the main application logic works. Unit tests are critical call sites that must be maintained.
- Leave failing tests that are caused by simple signature mismatches. They indicate an incomplete refactoring process and reduce trust in the test suite. This was the root cause of a `TypeError` in `_execute_backtest_pipeline` tests after its signature was changed to explicitly pass `strategy_params`.

## Test Fixture Integrity

### DO ✅
- **Ensure Complete Fixture Setup:** When creating or refactoring a test class, verify that its `setup_method` or `pytest` fixture initializes **all** mock objects and data attributes that will be accessed by the test methods within that class.
- **Keep Fixtures Self-Contained:** A test class should be able to run independently based on its own setup.

### DON'T ❌
- **Copy-Paste Test Classes Without Verifying Fixtures:** Avoid copy-pasting test classes and assuming the setup is correct. This is a common source of `AttributeError`s within the test suite itself.
- **Leave Incomplete Test Setups:** A test failing because an attribute is missing on the test class instance (e.g., `AttributeError: 'TestClass' object has no attribute 'mock_something'`) indicates a structural flaw in the test suite, not the application code. This was the root cause of a failure in `TestBacktestExecution` where `self.mock_strategy_params` was not initialized in `setup_method`.

## Anti-Pattern: Incomplete Code Relocation

### Structural Issue Discovered (2025-06-08)
- **Symptom:** `ImportError` during `pytest` collection, where a test file (`tests/test_cli_enhanced.py`) failed to import a function (`_generate_error_message`) from its old location (`src.meqsap.cli`).
- **Root Cause:** A structural refactoring moved utility functions from a main package `__init__.py` to a dedicated `utils.py` submodule to improve organization. However, the corresponding unit test file that imported and used these functions was not updated to reflect their new location. This is a classic "incomplete refactoring" error.

### Lesson & Design Principle
- **Principle: Refactoring must include all dependents.** When moving code (functions, classes) between modules, the refactoring task is not complete until all call sites, including unit tests, are updated.
- **Action:** Use IDE features like "Find Usages" or "Find in all files" to locate every reference to the moved symbol. Update all import statements accordingly. A failing test suite, especially during collection, is a strong signal of an incomplete structural change.

## Anti-Pattern: Stale Test Mocks After Refactoring

### Structural Issue Discovered (2025-06-09)
- **Symptom:** `AttributeError` during `pytest` execution, where a test (`tests/test_optimizer/test_optimization_error_handling.py`) failed because it tried to patch a method (`_generate_concrete_params`) that no longer exists on the `OptimizationEngine` class.
- **Root Cause:** A structural refactoring in `src/meqsap/optimizer/engine.py` renamed or removed the `_generate_concrete_params` method, likely replacing it with `_suggest_params_for_trial`. The unit test, which directly mocks this internal method, was not updated to reflect the change. This created a stale mock that targeted a non-existent attribute.

### Lesson & Design Principle
- **Principle: Test mocks are part of the contract.** When refactoring a class's internal methods, any tests that mock those methods must be updated in lockstep. Stale mocks are a form of technical debt that breaks the test suite's reliability.
- **Action:** When renaming or removing a method, immediately use "Find Usages" or a global search to locate all call sites, including test mocks (`mocker.patch`, `patch.object`, etc.). Update the test to mock the new method name or adjust the test logic if the method was removed. This prevents the test suite from reporting `AttributeError`s, which are test setup failures, not application logic failures.

## Test Suite Integrity

### DO ✅
- **Model Application Behavior Accurately:** When testing decorated functions or complex control flows (like exception-to-exit-code mapping), ensure tests mock the *inputs* that trigger the desired behavior (e.g., raising an exception) rather than mocking the *output* of the entire flow (e.g., mocking a return value that never occurs).
- **Test the Integration Point:** For CLI error handling, mock the function that *raises* the specific exception (e.g., `_validate_and_load_config` raising `ConfigurationError`). Then, use the `CliRunner` to invoke the top-level command and assert that the final `result.exit_code` matches the one assigned by the error-handling decorator.
- **Respect Function Signatures:** Ensure tests honor the return type hints of the functions they call. If a function is hinted to return `None`, tests should assert `result is None`, not `result == 0`.

### DON'T ❌
- **Write Tests Based on Incorrect Assumptions:** Avoid writing tests that expect a function to return a value (like an exit code) when its actual implementation raises exceptions or returns `None`. This creates false negatives and technical debt in the test suite.
- **Mock High-Level Wrappers for Low-Level Errors:** Don't mock a high-level pipeline function to test a specific error condition. Instead, mock the specific, lower-level function that is responsible for that error condition to create a more precise and stable test. This was the root cause of multiple failures in `test_cli_enhanced.py` where `_main_pipeline` was mocked to return an integer, which it never does.

## Anti-Pattern: Brittle Path Assertions in Tests

### Structural Issue Discovered (2025-06-11)
- **Symptom**: Multiple CLI tests failed with `AssertionError: expected call not found` when running on Windows. The mock assertion expected a `pathlib.WindowsPath` object but the code was called with a `str` representation of the path (e.g., `C:\path\to\file`).
- **Root Cause**: A core function (`_validate_and_load_config`) was unnecessarily converting a `pathlib.Path` object to a `str` before passing it to a downstream function (`load_yaml_config`). While the downstream function worked with the string, the unit test's mock assertion was written to expect the more robust `Path` object, making the test brittle and platform-dependent.

### Lesson & Design Principle
- **Principle: Pass `pathlib.Path` objects directly.** Avoid premature conversion of `Path` objects to strings. Most modern Python I/O functions (like `open()`) and many libraries accept `Path` objects directly. This makes code more robust, readable, and less prone to platform-specific path representation issues (e.g., `/` vs `\\`).
- **Action**: When writing mock assertions for functions that receive file paths, prefer asserting against `Path` objects. Refactor code to pass `Path` objects down the call chain until they are consumed by a function that strictly requires a string.
