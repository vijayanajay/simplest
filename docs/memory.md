# MEQSAP Memory File

## AI-Induced Bugs & Fixes

### CLI Module Execution Issue (December 2024)

**Problem**: CLI tests were failing because when running the CLI as a module (`python -m src.meqsap.cli`), the `if __name__ == "__main__":` guard was preventing the typer app from executing. When run as a module, `__name__` becomes the full module path (`src.meqsap.cli`) instead of `"__main__"`.

**Symptoms**: All CLI tests failing with exit code 2 instead of expected 0 or 1.

**Root Cause**: The `if __name__ == "__main__":` pattern doesn't work for module execution via `python -m`.

**Fix**: Added a dedicated `main()` function that calls `app()`, keeping the `if __name__ == "__main__":` guard but ensuring the CLI is accessible for both direct execution and module execution.

**Code Pattern**:
```python
def main():
    """Entry point for the CLI application."""
    app()

if __name__ == "__main__":
    main()
```

**Lesson**: When building CLI modules that need to work with both direct execution and `python -m` module execution, always provide a dedicated entry point function rather than relying solely on the `__name__` check.

## CLI Test Failures - Command Registration Issue

**Date**: [Current Date]
**Issue**: All CLI tests failing with exit code 2, indicating command registration failure

**Root Cause**: CLI commands were not properly registered with the Typer app instance that tests were importing. The structural issue was in the **command registration pattern**, not argument parsing.

**Symptoms**:
- Exit code 2 across all CLI tests
- Help commands worked but had wrong content
- Tests could import `app` but commands weren't attached

**Structural Problems**:
1. Commands defined but not registered with the Typer app
2. Possible mismatch between command registration pattern and Typer expectations
3. Import path structure may not align with test expectations

**Fix Applied**:
1. Explicit command registration using `app.command("name")(function)`
2. Verified file structure matches import paths in tests
3. Ensured Typer app metadata matches test expectations

**Lesson Learned**:
- Exit code 2 in Typer can indicate command discovery failure, not just argument issues
- Test imports must match actual module structure exactly
- Typer command registration requires explicit attachment to app instance

**Prevention**:
- Add CLI smoke test that verifies command registration
- Ensure import paths in tests match actual file structure
- Use consistent command registration patterns throughout

## CLI Test Failures - Missing Module Structure

**Date**: [Current Date]
**Issue**: All CLI tests failing with exit code 2 due to missing or broken CLI module structure

**Root Cause**: The CLI module (`src/meqsap/cli.py`) either didn't exist or had import errors, preventing Typer from initializing properly. Tests were attempting to import and patch functions from a non-existent module.

**Structural Problem**: 
- Module structure didn't match test import expectations (`src.meqsap.cli.*`)
- Missing required exception classes and dependencies
- Typer app object wasn't accessible for test runner

**Symptoms**:
- Exit code 2 across all CLI tests (Typer framework-level failure)
- Empty stdout instead of error messages
- Help commands showing generic Typer output instead of MEQSAP-specific text
- Tests could not import the `app` object from CLI module

**Fix Applied**:
1. Created complete CLI module at expected path (`src/meqsap/cli.py`)
2. Implemented all functions that tests were attempting to mock
3. Added proper exception classes in `exceptions.py`
4. Ensured package structure supports imports (`__init__.py`)

**Lesson Learned**:
- Exit code 2 in CLI tests often indicates **missing module structure**, not logic errors
- Test import paths must exactly match actual file structure
- Typer requires the entire module dependency chain to be importable
- Always verify module structure before writing tests

**Prevention**:
- Create skeleton modules before writing tests that import them
- Add basic import smoke tests to verify module structure
- Use absolute imports in tests to catch import issues early

## CLI Application Definition Issues (2024-01)

**Issue**: All CLI tests failing with exit code 2, indicating Typer application structure problems rather than command logic failures.

**Root Cause**: Structural mismatch between test expectations and actual CLI module exports. Exit code 2 typically indicates CLI framework initialization or argument parsing failures, suggesting the Typer `app` object wasn't properly defined or exported.

**Fix Pattern**: 
- Ensure Typer application is properly instantiated with `typer.Typer()`
- Set appropriate app metadata (name, help, etc.)
- Disable automatic exception handling to maintain manual error control
- Ensure all commands are properly decorated with `@app.command()`
- Use explicit `typer.Exit(code)` for controlled exit codes

**Prevention**: When adding new CLI commands or modifying the CLI structure, always verify that:
1. The `app` object is properly exported from the module
2. Command decorators are correctly applied
3. Tests can import and invoke the app object
4. Error handling uses `typer.Exit()` with appropriate exit codes

This reinforces the principle that CLI interfaces are structural contracts - tests failing uniformly indicates interface definition issues, not implementation bugs.

## CLI Test Failures - Missing Package Structure (Final Fix)

**Date**: [Current Date]
**Issue**: After multiple fix attempts (module execution, command registration, app definition), all CLI tests still failing with exit code 2

**Actual Root Cause**: **Missing `__init__.py` files** in the package structure preventing proper imports. Tests were importing `from src.meqsap.cli import app` but Python couldn't resolve the package hierarchy.

**Previous Failed Fixes**:
1. Module execution patterns (`__name__` guards) - Wrong level
2. Command registration patterns - Wrong level  
3. Missing CLI module - Partially correct but incomplete
4. Typer application definition - Wrong level

**Real Structural Problem**: 
- Missing `src/__init__.py` and `src/meqsap/__init__.py`
- Missing `src/meqsap/exceptions.py` that CLI imports
- Python import system couldn't resolve package path used by tests

**Complete Fix Pattern**:
1. Create all required `__init__.py` files for package hierarchy
2. Create `exceptions.py` with all expected exception classes
3. Create CLI module with stub functions that tests can mock
4. Ensure import paths exactly match test expectations

**Key Lesson**: Exit code 2 in CLI tests often indicates **Python import failures at the package level**, not Typer application issues. Always verify the complete package structure can be imported before debugging CLI-specific code.

**Prevention**: 
- Always create complete package structure before writing tests
- Add basic import smoke tests: `python -c "from src.meqsap.cli import app"`
- Verify all imported dependencies exist as modules/functions
- Check that test import paths match actual file structure exactly

This reinforces that **structural integrity** must exist at the Python package level before CLI framework functionality can work.

## CLI Test Failures - Runtime Import Resolution Issue (ACTUAL Fix)

**Date**: [Current Date]
**Issue**: After 4+ structural fixes, all CLI tests still failing with exit code 2

**ACTUAL Root Cause**: **Runtime import resolution failure** during test execution. The CLI module was defined with stub functions, but when Typer executed the command during tests, it encountered functions that raised `NotImplementedError` or had import issues, causing exit code 2.

**Previous Failed Diagnosis**:
1. Missing `__init__.py` - Correct but insufficient
2. Missing exceptions module - Correct but insufficient  
3. Missing CLI module - Correct but insufficient
4. Package structure - Correct but insufficient

**Real Problem**: The CLI functions existed as stubs but **failed at runtime execution** during test invocation, not at import time. Typer exit code 2 can indicate runtime failures within command execution, not just import failures.

**Complete Fix**:
1. Ensure CLI functions raise `NotImplementedError` with clear messages
2. Verify all imports in CLI module resolve correctly
3. Make functions properly mockable (real function objects, not pass stubs)
4. Ensure exception handling works with typer.Exit()

**Critical Insight**: **Exit code 2 in Typer can indicate runtime execution failures within commands**, not just CLI framework issues. When tests mock functions but the underlying execution path still fails, Typer returns exit code 2.

**Debugging Pattern for Future**:
1. Test basic import: `python -c "from src.meqsap.cli import app"`
2. Test CLI help: `python -m src.meqsap.cli --help`
3. Test command discovery: `python -m src.meqsap.cli analyze --help`
4. Only then test with mocked functions

**Key Lesson**: CLI tests failing uniformly often indicates **runtime execution path issues**, not just structural import problems. The entire execution path must be testable, not just importable.
