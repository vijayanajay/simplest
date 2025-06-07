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

### DO ✅
- **Delegate to a Central Pipeline:** High-level CLI commands (e.g., `analyze`) should be thin wrappers that call a single, central orchestration function (e.g., `_main_pipeline`).
- **Centralize Error Handling:** The central pipeline function must contain the comprehensive `try...except` blocks for all specific, expected exceptions (`ConfigurationError`, `DataError`, etc.), mapping them to distinct exit codes.
- **Return Exit Codes:** The pipeline function should return integer exit codes, which the CLI command then uses in `typer.Exit(code=...)`.

### DON'T ❌
- **Duplicate Pipeline Logic:** Avoid re-implementing the application's core workflow inside a CLI command function. This leads to inconsistent behavior.
- **Use Generic `except Exception` in Commands:** A broad `except Exception` in a command function will mask specific error types, preventing correct exit code mapping and making debugging difficult. This was the root cause of FLAW-20250607-001.

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
