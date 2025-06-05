<!-- Status: Completed -->
# Story: Enhanced Indicator & Parameter Definition Framework (Phase 1)

## Description
As outlined in PRD v2.1 and Phase 1 of the roadmap, this story implements the foundational Enhanced Indicator & Parameter Definition Framework. This critical enhancement enables strategy configurations to define parameter search spaces (ranges, choices, steps) rather than just fixed values, laying the groundwork for future automated parameter optimization. The story introduces the new `meqsap_indicators_core` module and refactors existing components to support flexible parameter definitions while maintaining backward compatibility with existing configurations.

## Epic Overview
This story implements **Epic 3: Enhanced Parameterization Framework for Optimization Readiness** from PRD v2.1, focusing on creating a robust and extensible framework for defining indicators and their parameter spaces.

## Acceptance Criteria

### Core Parameter Definition Framework
1. **AC1**: `BaseStrategyParams` and child classes (e.g., `MovingAverageCrossoverParams`) support parameter definitions as:
   - Fixed values: `fast_ma: 10`
   - Ranges: `fast_ma: {"type": "range", "start": 5, "stop": 20, "step": 1}`
   - Choices: `rsi_period: {"type": "choices", "values": [10, 14, 20]}`
   - Explicit values: `fixed_value: {"type": "value", "value": 50}`

2. **AC2**: Pydantic models validate parameter structures with proper type checking and constraints (e.g., `start < stop` for ranges, non-empty lists for choices)

3. **AC3**: YAML configuration loading correctly parses and validates new parameter space definitions

4. **AC4**: `get_required_data_coverage_bars` method calculates maximum possible lookback by considering parameter ranges (e.g., using `stop` value for range definitions)

### meqsap_indicators_core Module Implementation
5. **AC5**: New `meqsap_indicators_core` module is created with:
   - `IndicatorBase` abstract base class defining common interface
   - `ParameterDefinition` class for parameter metadata and validation
   - `ParameterSpace` class for defining search spaces
   - Registry/factory mechanism for indicator discovery

6. **AC6**: At least two technical indicators (Simple Moving Average, RSI) are implemented as concrete `IndicatorBase` classes

7. **AC7**: Indicator implementations provide calculation logic (wrapping `pandas-ta` where appropriate) and declare required data coverage

### Integration with Existing Modules
8. **AC8**: `meqsap.config` module utilizes `meqsap_indicators_core` for parameter interpretation and validation

9. **AC9**: `StrategySignalGenerator` in `meqsap.backtest` accepts concrete parameter sets and utilizes `meqsap_indicators_core` for calculations

10. **AC10**: Backward compatibility maintained - existing YAML configurations with fixed parameters continue to work without modification

### Configuration and Validation
11. **AC11**: Enhanced validation provides clear error messages for invalid parameter space definitions

12. **AC12**: System can perform standard backtests using default values or first choice when parameter spaces are defined

13. **AC13**: Example YAML files demonstrate new parameter definition syntax alongside existing fixed parameter examples

### Documentation and Testing
14. **AC14**: `architecture.md` updated to reflect new module structure and parameter handling approach

15. **AC15**: Comprehensive unit tests cover:
    - Parameter definition validation
    - Indicator implementations
    - YAML parsing with new syntax
    - Data coverage calculations with dynamic parameters

16. **AC16**: Integration tests verify end-to-end functionality with new parameter definitions

## Implementation Details

### New Module Structure
```
src/meqsap/
├── indicators_core/
│   ├── __init__.py
│   ├── base.py              # IndicatorBase, ParameterDefinition, ParameterSpace
│   ├── registry.py          # Indicator discovery and factory
│   ├── indicators/
│   │   ├── __init__.py
│   │   ├── moving_average.py
│   │   └── rsi.py
│   └── parameters.py        # Parameter type definitions
```

### Core Parameter Types
```python
# In meqsap/indicators_core/parameters.py
from pydantic import BaseModel, Field, validator
from typing import Union, List, Any

class ParameterRange(BaseModel):
    type: str = "range"
    start: float
    stop: float
    step: float = 1.0
    
    @validator('step')
    def step_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('step must be positive')
        return v
    
    @validator('stop')
    def stop_must_be_greater_than_start(cls, v, values):
        if 'start' in values and v <= values['start']:
            raise ValueError('stop must be greater than start')
        return v

class ParameterChoices(BaseModel):
    type: str = "choices"
    values: List[Any]
    
    @validator('values')
    def values_must_not_be_empty(cls, v):
        if not v:
            raise ValueError('choices values cannot be empty')
        return v

class ParameterValue(BaseModel):
    type: str = "value"
    value: Any

# Union type for all parameter definitions
ParameterDefinitionType = Union[float, int, str, bool, ParameterRange, ParameterChoices, ParameterValue]
```

### Enhanced Strategy Parameters
```python
# Updated MovingAverageCrossoverParams in config.py
class MovingAverageCrossoverParams(BaseStrategyParams):
    fast_ma: ParameterDefinitionType = Field(..., description="Fast moving average period")
    slow_ma: ParameterDefinitionType = Field(..., description="Slow moving average period")
    
    @validator('slow_ma')
    def validate_ma_relationship(cls, v, values):
        """Ensure slow_ma > fast_ma when both are fixed values"""
        if 'fast_ma' in values:
            fast_val = cls._extract_numeric_value(values['fast_ma'])
            slow_val = cls._extract_numeric_value(v)
            if fast_val is not None and slow_val is not None and slow_val <= fast_val:
                raise ValueError('slow_ma must be greater than fast_ma')
        return v
    
    def get_required_data_coverage_bars(self) -> int:
        """Calculate maximum possible lookback considering parameter ranges"""
        slow_ma_max = self._get_parameter_maximum(self.slow_ma)
        return slow_ma_max + 50  # Add buffer for calculation stability
    
    def _get_parameter_maximum(self, param: ParameterDefinitionType) -> int:
        """Extract maximum possible value from parameter definition"""
        if isinstance(param, (int, float)):
            return int(param)
        elif isinstance(param, dict):
            if param.get('type') == 'range':
                return int(param['stop'])
            elif param.get('type') == 'choices':
                return int(max(param['values']))
            elif param.get('type') == 'value':
                return int(param['value'])
        raise ValueError(f"Unable to determine maximum value for parameter: {param}")
```

### Indicator Base Classes
```python
# In meqsap/indicators_core/base.py
from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, List

class ParameterDefinition:
    """Defines metadata for a single indicator parameter"""
    def __init__(self, name: str, param_type: type, description: str, 
                 default: Any = None, constraints: Dict[str, Any] = None):
        self.name = name
        self.param_type = param_type
        self.description = description
        self.default = default
        self.constraints = constraints or {}

class ParameterSpace:
    """Defines the search space for a set of parameters"""
    def __init__(self, parameters: List[ParameterDefinition]):
        self.parameters = {p.name: p for p in parameters}
    
    def validate_values(self, values: Dict[str, Any]) -> bool:
        """Validate that provided values meet parameter constraints"""
        # Implementation details for validation logic
        pass

class IndicatorBase(ABC):
    """Abstract base class for all technical indicators"""
    
    def __init__(self, **params):
        self.params = params
        self._validate_parameters()
    
    @classmethod
    @abstractmethod
    def get_parameter_space(cls) -> ParameterSpace:
        """Return the parameter space definition for this indicator"""
        pass
    
    @classmethod
    @abstractmethod
    def get_required_data_coverage_bars(cls, **params) -> int:
        """Return minimum required historical data bars for calculation"""
        pass
    
    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """Calculate the indicator values"""
        pass
    
    def _validate_parameters(self):
        """Validate that provided parameters are valid for this indicator"""
        param_space = self.get_parameter_space()
        param_space.validate_values(self.params)
```

### Enhanced Signal Generation
```python
# Updates to StrategySignalGenerator in backtest.py
class StrategySignalGenerator:
    def __init__(self, indicator_registry=None):
        from .indicators_core.registry import get_indicator_registry
        self.indicator_registry = indicator_registry or get_indicator_registry()
    
    def generate_signals(self, data: pd.DataFrame, strategy_config: StrategyConfig,
                        concrete_params: Dict[str, Any] = None) -> pd.DataFrame:
        """Generate signals using concrete parameter values"""
        if concrete_params is None:
            concrete_params = self._extract_concrete_params(strategy_config.strategy_params)
        
        # Use strategy type to route to appropriate signal generation
        if strategy_config.strategy_name == "MovingAverageCrossover":
            return self._generate_ma_crossover_signals(data, concrete_params)
        else:
            raise ValueError(f"Unknown strategy: {strategy_config.strategy_name}")
    
    def _extract_concrete_params(self, strategy_params) -> Dict[str, Any]:
        """Extract concrete parameter values from parameter definitions"""
        concrete = {}
        for param_name, param_def in strategy_params.__dict__.items():
            if isinstance(param_def, (int, float, str, bool)):
                concrete[param_name] = param_def
            elif isinstance(param_def, dict):
                if param_def.get('type') == 'value':
                    concrete[param_name] = param_def['value']
                elif param_def.get('type') == 'choices':
                    # Use first choice as default for single runs
                    concrete[param_name] = param_def['values'][0]
                elif param_def.get('type') == 'range':
                    # Use start value as default for single runs
                    concrete[param_name] = param_def['start']
        return concrete
    
    def _generate_ma_crossover_signals(self, data: pd.DataFrame, 
                                      params: Dict[str, Any]) -> pd.DataFrame:
        """Generate MA crossover signals using concrete parameters"""
        # Get MA indicators from registry
        ma_indicator = self.indicator_registry.get('simple_moving_average')
        
        # Calculate MAs with concrete parameters
        fast_ma = ma_indicator(period=params['fast_ma']).calculate(data)
        slow_ma = ma_indicator(period=params['slow_ma']).calculate(data)
        
        # Generate entry/exit signals
        signals = pd.DataFrame(index=data.index)
        signals['entry'] = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))
        signals['exit'] = (fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))
        
        return signals.fillna(False)
```

### Configuration Examples
```yaml
# Example YAML with new parameter definitions
ticker: "AAPL"
start_date: "2023-01-01"
end_date: "2024-01-01"
strategy_name: "MovingAverageCrossover"
strategy_params:
  # Range definition for optimization readiness
  fast_ma:
    type: "range"
    start: 5
    stop: 15
    step: 1
  
  # Choice definition
  slow_ma:
    type: "choices"
    values: [20, 30, 50]

# Alternative: Mixed fixed and flexible parameters
strategy_params:
  fast_ma: 10  # Fixed value (backward compatible)
  slow_ma:     # Range for future optimization
    type: "range"
    start: 20
    stop: 50
    step: 5
```

### Testing Strategy
1. **Unit Tests**:
   - Parameter validation for all new types
   - Indicator implementations and calculations
   - Registry functionality
   - Data coverage calculations

2. **Integration Tests**:
   - YAML parsing with new syntax
   - End-to-end backtest execution
   - Concrete parameter extraction

3. **Backward Compatibility Tests**:
   - Existing configurations continue to work
   - No breaking changes to CLI interface

### Error Handling Enhancement
```python
class ParameterValidationError(ConfigurationError):
    """Raised when parameter definitions are invalid"""
    pass

class IndicatorCalculationError(BacktestError):
    """Raised when indicator calculation fails"""
    pass

# Enhanced error messages
def validate_parameter_range(param_def: dict) -> None:
    """Validate range parameter definition with clear error messages"""
    if param_def.get('start') >= param_def.get('stop'):
        raise ParameterValidationError(
            f"Range parameter 'start' ({param_def['start']}) must be less than "
            f"'stop' ({param_def['stop']})"
        )
    
    if param_def.get('step', 1) <= 0:
        raise ParameterValidationError(
            f"Range parameter 'step' must be positive, got {param_def['step']}"
        )
```

## Dependencies and Prerequisites
- **Depends on**: Stories 1-5 (completed MVP functionality)
- **Enables**: Future stories for parameter optimization engines
- **New Dependencies**: None (uses existing pandas-ta, pydantic)

## Definition of Done (All items verified as completed)
- [x] All acceptance criteria met and tested
- [x] `meqsap_indicators_core` module implemented and integrated
- [x] Enhanced parameter definitions work in YAML configurations
- [x] Backward compatibility maintained for existing configurations
- [x] Data coverage calculations handle dynamic parameters correctly
- [x] Comprehensive test coverage (unit + integration)
- [x] Documentation updated (architecture.md, example YAMLs)
- [x] Error handling provides clear, actionable messages
- [x] Code follows project standards (type hints, naming conventions)
- [x] Integration with existing CLI and reporting functionality verified

## Notes
This story represents a critical architectural enhancement that enables future automated optimization capabilities while maintaining the simplicity and reliability that characterizes MEQSAP. The modular design of `meqsap_indicators_core` follows the project's "orchestration-first" principle and prepares the system for the sophisticated features outlined in the remaining phases of the roadmap.

The implementation prioritizes:
1. **Backward Compatibility**: Existing users can continue using fixed parameter definitions
2. **Clear Interface**: New parameter syntax is intuitive and well-documented
3. **Robust Validation**: Comprehensive error checking with helpful messages
4. **Extensibility**: Easy to add new indicators and parameter types
5. **Performance**: Efficient parameter extraction and indicator calculations

This foundation enables the automated strategy discovery and optimization features planned for subsequent phases while maintaining MEQSAP's core philosophy of simplicity and reliability.

**Update (YYYY-MM-DD - Based on current review):** All acceptance criteria and definition of done items have been verified as completed. The implementation aligns with the story's goals and the project's architectural principles.
