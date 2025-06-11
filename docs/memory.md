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

## Anti-Pattern: Inconsistent API Contracts in Call Chain

### Structural Issue Discovered (2025-06-14)
- **Symptom**: Multiple tests for the `optimize single` command failed with `TypeError: cannot unpack non-iterable function object` and `AttributeError: 'str' object has no attribute 'strftime'`.
- **Root Cause**: The application had two separate logic paths for loading and validating user configuration YAMLs. The `analyze` command's path used a robust Pydantic model (`StrategyConfig`) that performed type coercion (e.g., converting date strings to `datetime.date` objects). The `optimize single` command's path used a simpler helper that loaded the YAML into a raw dictionary but failed to perform the same type coercion. This created a structural inconsistency where the same input data was treated differently depending on the CLI command used, leading to downstream errors. A secondary symptom was an API contract mismatch between a UI helper and its consumer due to incomplete refactoring.

### Lesson & Design Principle
- **Principle: Unify Core Business Logic.** Critical, cross-cutting concerns like configuration loading, validation, and data preparation should be handled by a single, canonical function or class that is used by all parts of the application. Avoid creating parallel, slightly different implementations for the same task in different modules or command paths.
- **Action**: Refactor divergent logic paths to call a single, authoritative function. In this case, the `optimize` command's configuration loader was refactored to use the same `validate_config` function as the `analyze` command, ensuring all configurations are processed identically, regardless of the entry point. This reinforces the "Don't Repeat Yourself" (DRY) principle at an architectural level.

---

## Anti-Pattern: Inconsistent API Contracts in Call Chain
 
 ### Structural Issue Discovered (2025-06-12)
- **Symptom**: `AttributeError` in `OptimizationEngine` tests due to a call to a non-existent method, and a latent bug in the `_compile_results` method where `run_complete_backtest` was called with incorrect argument types (`dict` of parameters instead of `dict` of objective settings).
- **Root Cause**: A structural refactoring was performed to simplify the `run_complete_backtest` API, requiring callers to pass a fully-formed `StrategyConfig` object containing all parameters. However, not all call sites within the `OptimizationEngine` were updated to adhere to this new contract. The optimizer's `_compile_results` method was still attempting to pass strategy parameters via a separate argument, which was now being misinterpreted as `objective_params`. Additionally, a helper method (`_is_trial_with_concrete_params`) was removed, but its call was left in place, causing test failures.

### Lesson & Design Principle
- **Principle: API refactoring requires updating all call sites.** When a function's signature or contract is changed, the refactoring is incomplete until every call site—including those in application logic, unit tests, and integration tests—is updated.
- **Action**: Use IDE tools like "Find Usages" or global search to locate every call to the refactored function. Ensure that the arguments passed in each call match the new signature in both type and meaning. This prevents latent bugs where data of one type is misinterpreted as another (e.g., `strategy_params` being passed as `objective_params`). Update or remove test mocks that target old, non-existent internal methods to keep the test suite synchronized with the implementation.

## Anti-Pattern: Incomplete Fixture Data for Pydantic Model Instantiation

### Structural Issue Discovered (2025-06-13)
- **Symptom**: A test suite for an error-handling function (`test_single_trial_error_handling`) was failing. The tests were designed to check if specific exceptions (`DataError`, `BacktestError`) were caught and classified correctly. However, all failures were being misclassified as a generic `UNKNOWN_ERROR`.
- **Root Cause**: The test fixture provided an incomplete dictionary as `strategy_config` to the `OptimizationEngine`. Inside the method under test (`_run_single_trial`), this incomplete dictionary was used to instantiate a `StrategyConfig` Pydantic model. This instantiation failed with a `pydantic.ValidationError` *before* the code path that was supposed to raise the test-specific exceptions was ever reached. The `ValidationError` was not explicitly caught, so it fell through to the generic `except Exception` block, causing the misclassification and test failure.

### Lesson & Design Principle
- **Principle: Test fixtures must provide a complete and valid data contract for downstream components.** When a component under test relies on creating objects (especially strictly-validated Pydantic models) from data passed into its constructor, the test fixtures must supply a dictionary that satisfies the model's schema.
- **Action**: Ensure that test fixtures for components that perform internal object instantiation provide a complete and valid dictionary/data structure. Do not use minimal or incomplete dictionaries in fixtures if they will be used to construct a validated model later in the call chain. This prevents tests from failing due to schema validation errors, allowing them to correctly test the intended business logic.

## Anti-Pattern: Hardcoded File Paths in Tests

### Structural Issue Discovered (2025-06-10)
- **Symptom**: Tests using hardcoded file paths like `Path("d:/Code/simplest/run.py")` were not portable across different development environments and machines. Some tests would skip instead of failing when critical files didn't exist, masking potential issues.
- **Root Cause**: Inconsistent path handling across test methods, with some using relative paths while others used hardcoded absolute paths. Critical entry point files like `run.py` were being treated as optional (using `pytest.skip()`) when they should be required for the project to function.

### Lesson & Design Principle
- **Principle: Use relative paths for test portability and appropriate error handling for critical files.** Tests should work regardless of where the project is cloned. Critical project files should cause test failures, not skips, when missing.
- **Action**: 
  - Use `Path(__file__).parent.parent / "filename"` for consistent relative path calculation
  - Use `pytest.fail()` for missing critical files like entry points, configuration files, etc.
  - Use `pytest.skip()` only for truly optional features or files
  - Provide descriptive error messages with resolved paths and context
  - Add proper exception handling for file I/O operations with meaningful error messages

### DO ✅
- Use relative path calculation: `Path(__file__).parent.parent / "run.py"`
- Fail tests for missing critical files: `pytest.fail(f"run.py not found at {path.resolve()}")`
- Add file I/O exception handling: `try/except (OSError, IOError)`
- Provide descriptive error messages with expected patterns and context

### DON'T ❌
- Use hardcoded absolute paths in tests: `Path("d:/Code/project/file")`
- Skip tests for missing critical project files
- Ignore file I/O errors without proper exception handling
- Use inconsistent path handling across test methods

## Anti-Pattern: Brittle Data Contracts and Overly-Specific Exception Handling

### Structural Issue Discovered (2025-06-15)
- **Symptom**: Multiple `optimize single` command tests failed with `AttributeError: 'Mock' object has no attribute 'timing_info'` and incorrect exit codes for `YAMLError`.
- **Root Cause**:
    1.  The `OptimizationResult` Pydantic model defines several fields (`total_trials`, `error_summary`, `timing_info`) that are populated during a real run. However, the test mocks for this object were incomplete and did not define these attributes. This led to `AttributeError` in downstream UI components that expected them to exist, making the tests brittle to model changes.
    2.  The central CLI error handler in `utils.py` was too specific, only catching the custom `ConfigurationError` but not the underlying `yaml.YAMLError` that could be raised by a mock or during file parsing. This led to incorrect error classification and exit codes in tests.

### Lesson & Design Principle
- **Principle: Test mocks must honor the data contract.** When mocking a data model object (like a Pydantic model), the mock must be as complete as the consumer of that object expects it to be. Incomplete mocks lead to brittle tests that fail on implementation details, not on logic errors.
- **Principle: Central error handlers should be robust.** While core logic should wrap third-party exceptions, the top-level error handler can be made more resilient by also catching key raw exceptions that are conceptually equivalent to a custom error type (e.g., treating `yaml.YAMLError` as a `ConfigurationError`). This ensures consistent error classification and user experience (e.g., exit codes).

### DO ✅
- **Keep Mocks Complete:** Ensure test mocks for data models include all attributes that downstream functions will access.
- **Broaden `except` Blocks:** Broaden top-level `except` blocks to include key raw third-party exceptions alongside custom-wrapped ones: `except (ConfigurationError, yaml.YAMLError) as e:`.

## Anti-Pattern: Overly Broad Exception Handling in Decorators

### Structural Issue Discovered (2025-06-15)
- **Symptom**: CLI commands using `typer.Exit` for controlled exits (e.g., success with code 0, interruption with code 2) were failing with a generic exit code 10.
- **Root Cause**: A global error-handling decorator (`@handle_cli_errors`) was implemented with a broad `except Exception as e:` block. This block was catching `typer.Exit` (which can inherit from `Exception` via `click.Exit`), misinterpreting it as an unhandled application error, and then re-raising it as a generic failure with exit code 10. This broke the intended exit code semantics of the command.

### Lesson & Design Principle
- **Principle: Decorators for cross-cutting concerns must not interfere with the underlying framework's control flow.** An error-handling decorator should be specific about the application exceptions it translates into exit codes. It should explicitly ignore or re-raise framework-specific control-flow exceptions like `typer.Exit` or `SystemExit`.
- **Action**: When implementing a generic error handler as a decorator:
  - **Be Specific**: Catch specific, custom application exceptions (`MEQSAPError` subclasses) first.
  - **Ignore Control Flow**: Explicitly catch and re-raise framework exceptions like `typer.Exit` *before* the generic `except Exception:` block to allow the framework to handle its own control flow.
  - **Alternative (Stricter Design)**: Adhere to a stricter pattern where command logic *never* calls `typer.Exit` directly, but instead raises specific, typed exceptions that the decorator is designed to map to exit codes. The immediate fix was to make the decorator more robust, but the long-term solution is to enforce the stricter pattern.

### Structural Issue Discovered (2025-06-16)
- **Symptom**: Tests for objective function validation failed, as they expected strict case-sensitive matching for function names (e.g., "SharpeRatio"), but the implementation allowed some case-insensitive variants (e.g., "sharperatio").
- **Root Cause**: A lookup function (`get_objective_function`) was implemented with case-normalization logic (`name.lower()`, `key.lower()`), creating a discrepancy between the strict contract defined in example configurations and tests, and the more lenient behavior in the code. This led to inconsistent and unpredictable configuration validation.

### Lesson & Design Principle
- **Principle: Enforce Strict Configuration Contracts.** Configuration lookups, especially for string-based keys like function or strategy names, should be explicit and case-sensitive by default. Avoid "helpful" normalization (like case-insensitivity) in core logic, as it can hide user typos, create ambiguity, and lead to inconsistent behavior. If flexibility is needed, it should be an explicit design decision documented in an ADR, not an implicit implementation detail.
- **Action**: When implementing registry or factory patterns that use string keys from user configuration, perform a direct key lookup. Ensure that error messages for failed lookups are clear and list the exact, case-sensitive names of available options.

## Anti-Pattern: Desynchronized Tests After Policy Changes

### Structural Issue Discovered (2025-06-18)
- **Symptom**: Multiple integration tests for CLI commands (`test_cli_optimize_integration.py`) failed with exit code mismatches (e.g., `assert 7 == 2`). A separate test (`test_cli_enhanced.py`) failed due to an `UnboundLocalError` in the error handling decorator.
- **Root Cause**: A core architectural policy for CLI exit codes was updated (as per `docs/arch_review.md`), and the implementation in `src/meqsap/cli/utils.py` was correctly modified to assign new, specific exit codes (6 for `OptimizationError`, 7 for `OptimizationInterrupted`). However, the integration tests were not updated to reflect this new contract and continued to assert against old, incorrect exit codes. This created a desynchronization between the implementation, the tests, and the documented architecture. The `UnboundLocalError` was a separate bug in the same error-handling decorator, where a variable was used out of scope.

### Lesson & Design Principle
- **Principle: Tests are part of the contract and must evolve with it.** When a cross-cutting concern like an error handling policy or exit code strategy is refactored, the change is not complete until all dependent components, including unit and integration tests, are updated. Stale tests give false negatives and erode trust in the test suite.
- **Action**: When updating a core policy documented in an ADR or architectural review:
  1.  Update the implementation to match the new policy.
  2.  Immediately use "Find Usages" or a global search to locate all tests that assert against the old behavior.
  3.  Update the test assertions to match the new contract. This ensures the entire system (code, docs, tests) remains consistent and that the test suite accurately validates the current architecture.
  4.  Ensure all code paths in shared utilities like decorators are tested, including generic exception handlers, to prevent scope-related bugs like `UnboundLocalError`.

## Anti-Pattern: Redundant Exception Handling at Wrong Abstraction Layer

### Structural Issue Discovered (2025-06-19)
- **Symptom**: A `KeyboardInterrupt` during an optimization run caused all partial progress to be lost. The CLI would report an interruption, but the final results would be empty, rather than showing the best parameters found before the interruption.
- **Root Cause**: A structural flaw where a `KeyboardInterrupt` was being handled at two different layers of the application with conflicting logic.
  1.  The `OptimizationEngine` correctly implemented a `try/except` block to catch the interrupt, set a `was_interrupted` flag, and then proceed to compile partial results from the `optuna` study object. This is the correct behavior.
  2.  The `cli/commands/optimize.py` module, which *calls* the `OptimizationEngine`, had its own redundant `try/except KeyboardInterrupt` block. This outer block would catch the interrupt, discard whatever the engine was trying to return, and create a new, empty `OptimizationResult` object. This incorrect, higher-level handler shadowed the correct, lower-level one, leading to data loss.

### Lesson & Design Principle
- **Principle: Handle exceptions at the appropriate layer.** The component responsible for managing a long-running, stateful process (the `OptimizationEngine`) is the correct place to handle exceptions related to that process, like an interruption. It has the context (the `optuna` study) needed to recover gracefully (compile partial results).
- **Principle: Higher-level callers should trust, not shadow.** The calling layer (the CLI command) should not re-implement exception handling for events that the callee is designed to manage. Instead, it should trust the callee to handle the event and return a result object with a status flag (e.g., `was_interrupted=True`). The caller's job is then to inspect the result object and react to the flag, not to intercept the exception itself.
- **Action**: Remove redundant, higher-level exception handlers that shadow more specific, lower-level ones. Ensure that the component closest to the work is responsible for its state management during exceptions.
