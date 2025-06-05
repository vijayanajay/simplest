# MEQSAP Memory File

## What NOT To Do: Common AI-Induced Pitfalls

### Import & Package Structure

**DON'T** write tests for modules that don't exist or have incomplete package structure.
- Always create `__init__.py` files for package hierarchy
- Verify imports work before writing tests: `python -c "from src.meqsap.cli import app"`
- Mock specifications must match actual return types (`spec=pd.DataFrame`, not `spec=Path`)

**DON'T** rely on `if __name__ == "__main__":` for modules executed with `python -m`.
- Use dedicated `main()` function for CLI entry points
- Test both direct execution and module execution patterns

### CLI Testing Anti-Patterns

**DON'T** test CLI help/commands without understanding the command structure.
- Use proper subcommand syntax: `["analyze", config, "--flag"]`, not `[config, "--flag"]`
- Test subcommand help with `["analyze", "--help"]`, not just `["--help"]`
- Verify CLI structure before writing tests: `python -m src.meqsap.cli --help`

**DON'T** assume Typer API stability.
- Remove deprecated arguments like `mix_stderr` from `CliRunner()`
- Pin Typer versions or test against updates regularly

**DON'T** mock functions to raise exceptions when testing return codes.
- Mock return values: `function.return_value = code`
- Not exceptions: `function.side_effect = Exception()` (bypasses internal error handling)

### Configuration & Schema Evolution

**DON'T** update Pydantic models without updating all test fixtures.
- Search project-wide for model instantiations when changing schemas
- Use factory functions for complex models to centralize test data creation
- Example: `MovingAverageCrossoverParams` field changes require updating all test helpers

**DON'T** hardcode configuration values in tests.
- Use constants for strategy types: `STRATEGY_TYPES = Literal["MovingAverageCrossover"]`
- Keep naming conventions consistent: PascalCase for strategy types, not snake_case

### Exception Handling

**DON'T** create duplicate exception classes.
- Single source of truth: use `exceptions.py`, not local classes in modules
- Import canonical exceptions: `from meqsap.exceptions import ConfigurationError`
- Don't alias imports that create ambiguity

**DON'T** reference unimplemented methods in factory patterns.
- Implement all factory methods before creating dependent code
- Use `mypy` to catch missing method references early

## Exception Handling Anti-Patterns

### Missing Exception Definitions
**Issue**: CLI module imports `ConfigError` from `config.py` but the exception class doesn't exist, causing import failures across all CLI tests.

**Root Cause**: Interface contract violation - dependent module expects exception class that isn't defined in the target module.

**Fix**: Define missing exception classes in their expected modules or update import statements to reference the correct location.

**Prevention**: 
- Verify all custom exceptions are defined before importing them
- Use a dedicated `exceptions.py` module for shared exceptions when appropriate
- Run basic import tests: `python -c "from module import exception_class"`

### Testing Fragility

**DON'T** assert exact CLI help text that depends on library formatting.
- Check for key terms ("Error", "MEQSAP"), not exact message strings
- Update test assertions when docstrings change

**DON'T** assume test structure matches implementation without verification.
- Inspect actual implementation before writing tests
- Use `typer.testing.CliRunner` with actual command structure
- Mock at module boundaries where functions are actually called

### Debugging Pattern

When CLI tests uniformly fail with exit code 2:
1. **First** check imports: `python -c "from module import app"`
2. **Then** check CLI help: `python -m module --help`  
3. **Then** check command structure: `python -m module subcommand --help`
4. **Finally** check runtime execution with mocks

**Remember**: Exit code 2 indicates framework-level failures (imports, command registration, argument parsing), not logic errors.

## Indicator Instantiation and Parameter Handling

**Structural Issue Discovered (2025-06-05):**
The `IndicatorBase` class and its concrete implementations (e.g., `SimpleMovingAverageIndicator`) were missing an `__init__` method to accept parameters at instantiation time, as potentially implied by some design documents (e.g., story 06). Instead, parameters are designed to be passed to the `calculate(self, data, **params)` method. Attempts in `backtest.py` to instantiate indicators like `IndicatorCls(param=value)` resulted in `TypeError` because the default `__init__` takes no arguments.

**Nature of Fix / Design Principle Reinforced:**
*   **Fix:** Modified `backtest.py` to instantiate indicators without arguments (e.g., `indicator_instance = IndicatorCls()`) and pass all necessary parameters to the `indicator_instance.calculate(data, **params)` method.
*   **Principle Reinforced:** Ensure strict adherence to class interface contracts. If parameters are intended for a specific method (like `calculate`), they should be passed there, not assumed by `__init__` unless `__init__` is explicitly designed to handle them. Discrepancies between design documentation (stories) and actual implementation of base class interfaces can lead to integration errors.

**Lesson Learned:**
*   Always verify that the instantiation and method calling patterns for classes (especially base/derived classes in a framework like `indicators_core`) match their defined interfaces.
*   When a base class (like `IndicatorBase`) defines how parameters are consumed (e.g., via `calculate(**params)`), ensure all client code adheres to this, rather than attempting to pass parameters during instantiation if the `__init__` method is not designed for it.
*   Keep implementation strictly aligned with the defined interfaces in `base.py` files, or update the base interface and all implementations if a design change (like parameterizing `__init__`) is intended.

## Pydantic Validation for Union Types with Direct Numeric Inputs

**Structural Issue Discovered (2025-06-05):**
Strategy parameter models (e.g., `MovingAverageCrossoverParams` in `config.py`) using Pydantic's `Union` type for fields (e.g., `fast_ma: ParameterDefinitionType`, where `ParameterDefinitionType` includes `int`, `float`, `ParameterRange`, etc.) did not automatically apply basic numeric constraints (like `value > 0`) when a direct numeric value (e.g., `fast_ma: -5`) was provided. Constraints defined in `IndicatorBase.get_parameter_definitions` were not inherently part of the Pydantic model's validation for `StrategyConfig`. This allowed invalid numeric parameters to pass initial config validation, leading to errors in later stages (e.g., `DataError` or `BacktestError`).

**Nature of Fix / Design Principle Reinforced:**
*   **Fix:** Added explicit Pydantic `field_validator`s within `MovingAverageCrossoverParams` for fields like `fast_ma` and `slow_ma`. These validators check if the input is a direct numeric type and then apply necessary constraints (e.g., positivity).
*   **Principle Reinforced:** When using Pydantic `Union` types that include simple scalar types (like `int`, `float`) alongside complex model types, ensure that validators are in place for the scalar types if they have specific constraints not covered by the complex types or the `Field` definition itself for the Union. Pydantic validation is per-model; constraints from other systems (like an indicator's internal parameter definition) are not automatically inherited.

**Lesson Learned:**
*   For Pydantic fields defined as a `Union` (e.g., `ParameterDefinitionType`), if direct scalar inputs (like `int` or `float`) need specific validation (e.g., `>0`), these must be explicitly handled by validators in the Pydantic model itself. Do not assume constraints from other parts of the system (like an indicator's own parameter definition metadata) will be automatically applied by Pydantic at the configuration model level.
*   Ensure that Pydantic models responsible for configuration parsing (`StrategyConfig` and its nested parameter models) are self-contained in their validation logic for all permissible input types and structures for their fields.

## Pydantic Field Validators on Union Types Containing Models

**Structural Issue Discovered (YYYY-MM-DD - Based on current task):**
When a Pydantic `field_validator` is applied to a field whose type is a `Union` that includes other Pydantic models (e.g., `my_field: Union[int, MyModel]`), and the input data for that field matches one of the models in the Union (e.g., `my_field={"some_key": "some_value"}` which Pydantic parses into a `MyModel` instance), the validator function receives the *Pydantic model instance* (e.g., an instance of `MyModel`) as its `v` argument, not the raw input (e.g., the dictionary). If helper functions used within the validator expect raw input types (like `int` or `dict`), they might fail or return unexpected results (e.g., `None`) when passed a model instance. This can lead to validation logic being silently skipped.

**Nature of Fix / Design Principle Reinforced:**
*   **Fix:** Modified the affected `field_validator`s (e.g., `ma_period_must_be_positive` and `slow_ma_must_be_greater_than_fast_ma` in `MovingAverageCrossoverParams`) to explicitly check if the input argument `v` is an instance of the Pydantic models included in the `Union` type (e.g., `ParameterValue`). If it is, the validator now accesses the relevant attributes of the model instance (e.g., `v.value`) to get the actual data for validation, instead of relying on helper functions designed for raw types. The problematic helper function (`_static_extract_numeric_value`) was removed as its logic was incorporated directly and correctly into the validators.
*   **Principle Reinforced:** Pydantic `field_validator`s must be robust to the actual type of the value they receive, especially for `Union` types. If a `Union` includes Pydantic models, the validator might receive an instance of one of those models. Internal logic or helpers within the validator must correctly handle these model instances to extract the data needed for validation.

**Lesson Learned:**
*   When writing Pydantic `field_validator`s for fields typed as `Union` which include other Pydantic models (e.g., `field: Union[int, MyModelA, MyModelB]`), always anticipate that the validator might receive an instance of `MyModelA` or `MyModelB` if the input data successfully parses into one of them.
*   Ensure that any logic or helper functions within such validators correctly introspect or handle these Pydantic model instances to access the underlying values needed for validation, rather than assuming the input will always be a primitive type or a raw dictionary.
*   Test validators with all possible input structures that Pydantic might parse into the `Union` type, including inputs that resolve to each of the Pydantic models within the `Union`.

**Structural Issue Discovered (2025-06-06):** Overly Permissive Float Conversion in Backtest Metrics
The `safe_float` utility in `src/meqsap/backtest.py` previously defaulted to 0.0 for various conversion errors (e.g., `ValueError`, `TypeError` when converting a string like "N/A" to float) and for `None`, `NaN`, or `inf` values. While intended for robustness, this behavior masked underlying data integrity issues, especially when parsing critical financial metrics from `vectorbt`'s output or trade logs. Incorrect or missing data for key metrics could be silently converted to 0.0, leading to misleading backtest analysis results and a false sense of validity. This was highlighted by technical debt item TD-20250601-002 and a skipped test `test_mock_stats_with_non_numeric`.

**Nature of Fix / Design Principle Reinforced:**
*   **Fix:** The `safe_float` function was enhanced with a `raise_on_type_error: bool` parameter and a `metric_name: Optional[str]` parameter. When `raise_on_type_error` is `True` (used for critical metrics), `safe_float` now raises a `BacktestError` if a `ValueError` or `TypeError` occurs during float conversion, instead of returning the default. Logging was also improved using `metric_name`. Calls to `safe_float` within `run_backtest` for critical statistics (e.g., Total Return, Sharpe Ratio, Final Value, PnL of individual trades) were updated to set `raise_on_type_error=True`. `None`, `NaN`, and `inf` values continue to be logged and defaulted, as these can be legitimate (though often undesirable) outputs from numerical libraries for certain scenarios. The skipped test `test_mock_stats_with_non_numeric` was implemented to verify this stricter error handling.
*   **Principle Reinforced:** Critical data points and metrics must "fail loudly" if they are malformed or of an unexpected type. Silent defaulting for critical information can erode trust in system outputs and lead to flawed decision-making. Robustness should not come at the cost of obscuring potentially serious data issues for key analytical results.

**Lesson Learned:**
*   Distinguish between critical and non-critical data when designing error handling for data parsing and conversion utilities.
*   For critical metrics, prefer raising an error for unexpected types or conversion failures over silent defaulting. This ensures data integrity issues are surfaced early.
*   Use specific logging for data conversion issues, including the metric name, to aid debugging.
*   Ensure test suites cover scenarios with malformed or unexpected data types for critical metrics, verifying that the system handles them by raising appropriate errors.

## Inaccurate Mocking of External Library Interfaces

**Structural Issue Discovered (2025-06-06):**
The test `test_mock_stats_with_non_numeric` in `tests/test_float_handling.py` failed because a mock for `vectorbt.Portfolio.wrapper.columns` was incorrectly set to a plain Python `list` (`['asset']`) instead of a `pandas.Index` object (`pd.Index(['asset'])`). This caused an `AttributeError` (`'list' object has no attribute 'empty'`) in `src/meqsap/backtest.py` when the application code attempted to access the `.empty` attribute, which is only present on `pandas.Index` objects. This highlighted a mismatch between the test's mock behavior and the expected interface contract of the external `vectorbt` library.

**Nature of Fix / Design Principle Reinforced:**
*   **Fix:** The mock in `tests/test_float_handling.py` was updated to correctly return a `pandas.Index` object for `portfolio.wrapper.columns`, aligning the test's behavior with the actual `vectorbt` API contract.
*   **Principle Reinforced:** Strict adherence to the interface contracts of external libraries, even when mocking. Mocks should accurately mimic the behavior and return types of the real objects they replace to ensure tests are valid and catch actual application logic errors, not just mock-induced type mismatches.

**Lesson Learned:**
*   When mocking external library objects, especially complex ones like `vectorbt`'s internal structures, always ensure that the mocked attributes and methods return types and behave in a manner consistent with the actual library's API.
*   A mismatch in mock implementation can lead to misleading test failures that obscure the true root cause or falsely indicate issues in the application code.
*   Verify the exact types and attributes of the objects being mocked, potentially by inspecting the actual library's behavior or documentation.

## Data Type Enforcement for Intermediate Calculations

**Structural Issue Discovered (2025-06-06):**
The `run_backtest` function in `src/meqsap/backtest.py` assumed that the `PnL` and `Return [%]` columns within the `vectorbt` `trades.records_readable` DataFrame would always be numeric. This assumption was violated when these columns contained non-numeric data (e.g., strings), leading to `TypeError` during intermediate pandas operations (e.g., `trades[pnl_col] > 0` or `.sum()`) before `safe_float` could process individual trade details. This highlighted a gap in data type enforcement early in the trade processing pipeline.

**Nature of Fix / Design Principle Reinforced:**
*   **Fix:** Explicitly converted the `PnL` and `Return [%]` columns of the `trades` DataFrame to numeric types using `pd.to_numeric(errors='coerce')` immediately after retrieval from `vectorbt`. This ensures that subsequent pandas operations (comparisons, sums) work correctly, converting non-numeric values to `NaN`. The `safe_float` utility then correctly handles these `NaN`s when populating `trade_details`, defaulting them to 0.0 as per policy for `NaN`/`None`/`inf`.
*   **Principle Reinforced:** Proactive data type enforcement and validation at the earliest possible stage for critical data structures. Assumptions about data types from external library outputs should be explicitly validated or coerced to prevent downstream `TypeError`s. The "fail loudly" principle for critical metrics applies to the *final extraction* via `safe_float` for unexpected types, but intermediate data processing requires robust handling of potentially non-numeric values.

**Lesson Learned:**
*   Always validate or coerce data types of critical columns immediately upon receiving them from external libraries, especially before performing mathematical operations or comparisons.
*   Distinguish between data integrity checks that should "fail loudly" (e.g., `safe_float` for final metric extraction) and robust data preparation steps (e.g., `pd.to_numeric(errors='coerce')`) that ensure intermediate calculations proceed without type errors.
*   Ensure test cases accurately reflect the intended error handling and data flow, especially when mocking external library outputs. If a utility function (like `safe_float`) is designed to default for certain values (`NaN`), tests should assert the default, not an error.
