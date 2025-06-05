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
