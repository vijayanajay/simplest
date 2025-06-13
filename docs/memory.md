# MEQSAP Memory Bank: Concise Do's and Don'ts

## API & Package Contracts

### DO ✅
- Explicitly export all public symbols from a package's `__init__.py` file.
- Use Pydantic v2 validators: `@field_validator` for single fields and `@model_validator` for cross-field validation.

### DON'T ❌
- Assume sub-module contents are automatically part of a package's public API.
- Use deprecated Pydantic v1 `@validator` for new code.

## Package Structure & Imports

### DO ✅
- Create complete `__init__.py` files for package hierarchy
- Verify imports work: `python -c "from src.meqsap.cli import app"`
- Match mock specifications exactly to expected types: `spec=pd.DataFrame`
- Use dedicated `main()` function for CLI entry points
- Use distinct names for modules and packages
- For name collisions: re-export in `__init__.py` (`from ..mod import symbol`)

### DON'T ❌
- Write tests for incomplete package structures
- Rely on `if __name__ == "__main__":` for `python -m` execution
- Use incorrect mock types (e.g., `spec=Path` for DataFrame)
- Create ambiguous import paths without re-export management
- Create module file and directory with same name (e.g., `test_reporting.py` and `test_reporting/`)

## CLI Testing

### DO ✅
- Use proper subcommand syntax: `["analyze", config, "--flag"]`
- Test subcommand help with: `["analyze", "--help"]`
- Mock return values: `function.return_value = code`
- Verify CLI structure: `python -m src.meqsap.cli --help`

### DON'T ❌
- Use incorrect command syntax: `[config, "--flag"]`
- Mock exceptions for testing return codes - use return values
- Use deprecated Typer arguments (`mix_stderr`)
- Assert exact CLI help text - use key terms instead

## Configuration & Models

### DO ✅
- Update ALL test fixtures when changing Pydantic models
- Use factory functions for complex model creation
- Add explicit validators for Union types with constraints
- Handle both raw types and model instances in validators
- **Make configuration value lookups case-insensitive** where it improves user experience (e.g., for names of functions, algorithms).

### DON'T ❌
- Change schemas without updating dependent tests
- Assume Union type validation works automatically
- Use helper functions expecting raw types on model instances
- **Enforce strict case-sensitivity** on user-provided string configurations (like function names) when a case-insensitive match is unambiguous and more user-friendly.

## Exception Handling & Error Codes

### DO ✅
- Use canonical exceptions from `exceptions.py`
- Map specific exceptions to distinct exit codes (follow ADR-004)
- Use specific exception blocks: `except ConfigurationError`
- Handle exceptions at the appropriate layer closest to the action

### DON'T ❌
- Create duplicate exception classes in multiple modules
- Use broad `try...except Exception` in CLI commands
- Reference unimplemented methods
- Add redundant exception handling at higher abstraction layers

## Testing & Mocking

### DO ✅
- Mock at correct module boundaries
- Match external library interfaces exactly: `pd.Index` not `list`
- Mock magic methods directly: `mock_obj.__len__ = Mock(return_value=X)`
- Instantiate with mocks instead of patching `__init__`
- Ensure complete fixture setup with all required attributes
- When patching `__init__`, mock all accessed attributes

### DON'T ❌
- Mock with incorrect return types for external libraries
- Use `mock_obj.__len__.return_value = X` (causes `AttributeError`)
- Skip data validation for critical columns
- Patch `__init__` without mocking complete object state
- Copy-paste test classes without verifying fixture completeness

## Data Type Safety & Critical Metrics

### DO ✅
- Coerce external data early: `pd.to_numeric(errors='coerce')`
- Use strict error handling for critical metrics: `raise_on_type_error=True`
- Distinguish critical vs non-critical data handling

### DON'T ❌
- Silent-default critical financial metrics
- Assume external library outputs have correct types
- Skip data validation before mathematical operations

## Indicator Framework

### DO ✅
- Instantiate indicators without arguments: `indicator = IndicatorCls()`
- Pass parameters to `calculate()` method: `indicator.calculate(data, **params)`
- Verify implementation matches documentation

### DON'T ❌
- Pass parameters to indicator `__init__()` unless designed for it
- Assume documentation matches implementation

## Cross-Platform Compatibility

### DO ✅
- Use ASCII or widely supported Unicode for CLI output
- Test on Windows and check for `UnicodeEncodeError`
- Include `pytest-mock` in dev dependencies
- Use relative paths in tests: `Path(__file__).parent.parent / "file"`

### DON'T ❌
- Use high-plane Unicode emoji without fallbacks
- Assume Unicode support across all terminal environments
- Use hardcoded absolute paths in tests

## Common Debug Patterns

| Pattern | Debugging Approach |
|---------|-------------------|
| **CLI Exit Code 2** | Check imports → CLI help → subcommand structure → runtime with mocks |
| **Mass Test Failures** | Check for structural issues (incomplete refactoring, missing dependencies) |
| **Import Ambiguity** | Look for module/package name collision - fix with re-export in `__init__.py` |
| **AttributeError in Tests** | Check fixture completeness and mock object initialization |

## Key Anti-Patterns

1. **Incomplete Refactoring:** Always update ALL call sites and tests
2. **Mock Type Mismatches:** Match external library interfaces exactly
3. **Silent Data Issues:** Make critical metrics fail loudly on type errors
4. **Union Type Validators:** Handle both raw types and Pydantic model instances
5. **Magic Method Mocking:** Use direct assignment, not `.return_value`
6. **API Contract Inconsistency:** Use single canonical implementation for core logic
7. **Brittle Path Handling:** Use `Path` objects, not strings, until absolutely needed
8. **Exception Layer Confusion:** Handle exceptions at appropriate layer
9. **Incomplete Package API Exposure:** When refactoring code into submodules (e.g., `utils.py`), failing to export the necessary functions from the package's `__init__.py`. This breaks the public API contract, leading to `ImportError` in consuming modules. **Fix:** Always review and update the package's `__init__.py` and `__all__` list to explicitly export all symbols intended for public use.
10. **Module/Package Name Collision:** Avoid creating a `.py` file and a directory with the same name (e.g., `reporting.py` and `reporting/`) in the same package. This leads to ambiguous `ImportError`s. If refactoring a module into a package, delete the original `.py` file.
11. **Missing Type Hint Imports:** A function signature in one module uses a type hint for a class defined in another module, but the `import` statement is missing. This leads to a `NameError` during static analysis or test collection. **Fix:** Ensure all external types used in function signatures are explicitly imported.
12. **Nested Data Access Assumptions:** When consuming a data model from another module (e.g., `BacktestAnalysisResult`), accessing its attributes based on assumptions of a flat structure (e.g., `result.ticker`) instead of its explicit definition (e.g., `result.strategy_config['ticker']`). This can lead to `AttributeError` or `KeyError` if the assumed attribute path doesn't exist. **Fix:** Always access nested data explicitly according to the model's definition.
13. **Circular Package Imports:** A package's `__init__.py` imports a symbol from a submodule (e.g., `reporters.py`), while that submodule imports another symbol from the package's `__init__.py` (e.g., `from ..reporting import ...`). This creates a circular dependency that can lead to `ImportError` and makes mocking in tests complex and brittle. **Fix:** Submodules should import directly from other specific submodules (e.g., `from .format_utils import ...`) instead of relying on the package's `__init__.py` to be an intermediary. Keep the dependency graph acyclic.
14. **Mocking Pydantic Models Incorrectly**: Using a generic `unittest.mock.Mock` as a return value for a function that should return a Pydantic model instance. This will cause `ValidationError` in downstream consumers under Pydantic v2+. **Fix:** The mock must return a valid instance of the Pydantic model, e.g., `mock_function.return_value = MyPydanticModel(field=mock_value)`.
15. **Invalid Stub Implementation during Refactoring**: Creating a new module or function as a placeholder during a large refactoring, but leaving it in a syntactically invalid state (e.g., with incorrect imports or calls to non-existent functions). This can break the entire application or test suite at import time, even if the new code is not yet actively called. **Fix:** All new modules and functions, even if incomplete, must be syntactically valid and importable. Use `pass` or `raise NotImplementedError` in function bodies, but ensure all imports and top-level statements are correct.
16. **Inconsistent Dependency Declaration within a Package:** A module (`cli/commands/analyze.py`) attempted to import from a non-existent shared utility module (`...logging`), while its sibling module (`cli/commands/optimize.py`) declared its own dependencies locally. This inconsistency, likely from an incomplete refactoring, caused an `ImportError` that broke the entire test suite at collection time. **Fix:** Ensure modules within a package follow a consistent dependency strategy. Either create the shared utility and use it everywhere, or make each module self-contained by declaring its own dependencies (e.g., `import logging`). The latter was chosen for simplicity and to resolve the immediate break.
17. **Incomplete Workflow Implementation / Data Flow Orchestration:** An orchestration layer (e.g., `AnalysisWorkflow`) was implemented to manage a multi-step process but failed to handle the complete data flow. Specifically, it did not fetch the required market data before calling a backtesting function that depended on it, causing a `TypeError` for a missing argument. **Fix:** The orchestrator must be responsible for acquiring all necessary data (e.g., from a `data` module) and explicitly passing it to the processing components (e.g., a `backtest` module). The function signatures of the orchestrated functions (e.g., `run_complete_backtest(config, data)`) serve as a contract that the orchestrator must fulfill.
18. **Inaccurate Mock State:** A unit test provides a mock object (e.g., `Mock(spec=MyModel)`) that correctly mimics the class of a real object, but its attributes are set to incorrect data types (e.g., a `str` for a date field that should be a `datetime.date` object after Pydantic validation). This violates the data contract of the component under test, causing failures in downstream functions and making the root cause (the incorrect test setup) difficult to diagnose. **Fix:** Ensure that mock object attributes have the same type and format as they would in the real, post-validation object. For a `StrategyConfig` mock, `start_date` must be a `datetime.date` object, not a string.
19. **Outdated Mock Patching After Refactoring:** When a function is moved from `module_a` to `module_b`, and `module_c` calls it from `module_b`, tests for `module_c` must patch the function at `module_b` (`@patch('module_c.module_b.function_name')`), not its original location. Failure to update mock targets after refactoring is a common source of mass test failures.
20. **Suppressing Exceptions in Orchestration Layers:** An orchestration layer (e.g., a `Workflow` class) uses a broad `except Exception:` block to catch and suppress specific, meaningful exceptions (like `ReportingError`) from a component it calls. Instead of propagating the specific error, it logs a warning and continues, effectively hiding the failure from higher-level error handlers. This leads to incorrect success exit codes (e.g., 0) and misleads users. **Fix:** Let specific, domain-related exceptions propagate upwards to be handled at the appropriate policy-setting layer (e.g., the main CLI application entry point). A `try...except` block in a workflow should be specific about the exceptions it can handle and recover from.

## CLI Orchestration & Error Handling

### DO ✅
- Use a single error-handling decorator for top-level CLI commands
- Centralize exception-to-exit-code mapping in the decorator
- Raise specific typed exceptions from pipeline functions
- Let exceptions bubble up to the decorator
- Respect framework control flow by handling `typer.Exit` separately
- Use domain-specific exceptions for application errors

### DON'T ❌
- Use generic `except Exception` for specific errors in decorators
- Call `typer.Exit` directly from command logic
- Allow control-flow exceptions to fall into generic handlers
- Swallow specific exceptions in an orchestration layer and re-raise them as a generic one. This breaks the error handling contract of higher-level consumers (like a CLI decorator) that expect to act on specific exception types.
- Redundantly handle the same exception at multiple layers

## Object & Data Flow

### DO ✅
- Pass validated objects explicitly throughout call chain
- Use IDE tools to update ALL call sites when refactoring signatures
- Update mock assertions to match new function signatures
- Ensure complete data contracts for Pydantic model instantiation
- Pass consistent object types across command paths
- **Access nested data explicitly.** When consuming a data model from another module (e.g., `BacktestAnalysisResult`), access its attributes according to its explicit definition (`result.strategy_config['ticker']`), not based on assumptions.

### DON'T ❌
- Have downstream functions re-derive objects
- Assume refactoring is complete without updating tests
- Leave failing tests due to signature mismatches
- Provide incomplete fixture data for model instantiation
- Create parallel, inconsistent implementations for the same task
- **Assume a flat data structure.** Don't assume a data model's attributes are at the top level (`result.ticker`) when they might be nested within other objects or dictionaries. This creates brittle coupling that breaks when the producing module's implementation changes.

## Test Suite Integrity

### DO ✅
- Initialize ALL mock objects in setup_method or fixtures
- Keep test fixtures self-contained and independent
- Model application behavior accurately in tests
- Test at appropriate integration points
- Respect function signatures and return types
- Use `Path` objects for file paths in tests
- Make tests fail for missing critical files
- Update tests when architectural policies change

### DON'T ❌
- Copy-paste test classes without verifying fixtures
- Leave incomplete test setups causing AttributeError
- Mock high-level wrappers for testing low-level errors
- Write tests based on incorrect assumptions
- Use hardcoded absolute paths in tests
- Skip tests for missing critical files

## Refactoring & Code Change Procedures

### DO ✅
- Use "Find Usages" to update all code references when moving or renaming
- Update ALL test mocks when changing method names or signatures
- Update package `__init__.py` files to maintain import structure
- Update all call sites when refactoring function signatures
- Ensure test fixtures provide complete data for Pydantic models
- Use relative paths for file references in tests
- Apply unified core logic across all command paths
- Handle exceptions at appropriate layers (closest to action)
- Update tests when architectural policies (like error codes) change

### DON'T ❌
- Assume IDE refactoring caught all references
- Leave stale test mocks targeting old methods
- Skip updating `__init__.py` files after code relocation
- Ignore failing tests after signature changes
- Use incomplete fixture data for Pydantic models
- Use hardcoded absolute paths in tests
- Create parallel implementations for the same logic
- Handle the same exception at multiple abstraction layers

## Quick Troubleshooting Guide

| Error Type | First Steps to Check |
|------------|----------------------|
| ImportError | Check `__init__.py` exports, module naming conflicts, package structure |
| AttributeError | Check fixture completeness, mock initialization, correct patching |
| TypeError | Check function signatures, argument types, parameter order |
| CLI Exit Code 2 | Check imports → CLI structure → subcommands → mocks |
| Mass Test Failures | Look for structural issues across the codebase |
| Path-related errors | Use `Path` objects with relative references |

### Remember
- **Outdated Mock Patching After Refactoring:** When a function is moved from `module_a` to `module_b`, and `module_c` calls it from `module_b`, tests for `module_c` must patch the function at `module_b` (`@patch('module_c.module_b.function_name')`), not its original location. Failure to update mock targets after refactoring is a common source of mass test failures.

- When multiple tests fail simultaneously, check for structural issues first
- For import errors, inspect the complete package hierarchy
- For attribute errors, verify all mocked attributes are correctly initialized
- For type errors, ensure consistency between function signatures and call sites
- For structural issues, perform a full-stack trace of the data flow and update all consuming functions and tests
