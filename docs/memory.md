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
- When multiple tests fail simultaneously, check for structural issues first
- For import errors, inspect the complete package hierarchy
- For attribute errors, verify all mocked attributes are correctly initialized
- For type errors, ensure consistency between function signatures and call sites
- For structural issues, perform a full-stack trace of the data flow and update all consuming functions and tests
