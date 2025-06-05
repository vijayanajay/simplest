"""Parameter space definition and sampling for optimization engine."""

import itertools
import random
from typing import Dict, List, Any, Iterator, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class ParameterRange:
    """Defines a parameter range for optimization."""
    min_value: float
    max_value: float
    step: float = 1.0
    
    def __post_init__(self):
        if self.min_value >= self.max_value:
            raise ValueError(f"min_value ({self.min_value}) must be less than max_value ({self.max_value})")
        if self.step <= 0:
            raise ValueError(f"step ({self.step}) must be positive")


@dataclass
class ParameterChoice:
    """Defines discrete parameter choices for optimization."""
    choices: List[Any]
    
    def __post_init__(self):
        if not self.choices:
            raise ValueError("choices cannot be empty")


class ParameterSpace:
    """
    Manages parameter space definition and sampling for single-indicator strategies.
    
    Supports both continuous ranges and discrete choices for parameters.
    """
    
    def __init__(self, parameters: Dict[str, Any]):
        """
        Initialize parameter space from configuration.
        
        Args:
            parameters: Dictionary of parameter definitions with ranges or choices
        """
        self.parameters = parameters
        self._validate_parameters()
        
    def _validate_parameters(self) -> None:
        """Validate parameter definitions."""
        if not self.parameters:
            raise ValueError("Parameter space cannot be empty")
            
        for param_name, param_def in self.parameters.items():
            if not isinstance(param_name, str):
                raise ValueError(f"Parameter name must be string, got {type(param_name)}")
                
            if isinstance(param_def, dict):
                if 'range' in param_def:
                    self._validate_range_definition(param_name, param_def['range'])
                elif 'choices' in param_def:
                    self._validate_choice_definition(param_name, param_def['choices'])
                else:
                    raise ValueError(f"Parameter {param_name} must have 'range' or 'choices'")
    
    def _validate_range_definition(self, param_name: str, range_def: List) -> None:
        """Validate range parameter definition."""
        if not isinstance(range_def, list) or len(range_def) not in [2, 3]:
            raise ValueError(f"Range for {param_name} must be [min, max] or [min, max, step]")
        
        if len(range_def) == 2:
            min_val, max_val = range_def
            step = 1.0
        else:
            min_val, max_val, step = range_def
            
        if not all(isinstance(x, (int, float)) for x in [min_val, max_val, step]):
            raise ValueError(f"Range values for {param_name} must be numeric")
            
        if min_val >= max_val:
            raise ValueError(f"Min value must be less than max value for {param_name}")
            
        if step <= 0:
            raise ValueError(f"Step must be positive for {param_name}")
    
    def _validate_choice_definition(self, param_name: str, choices: List) -> None:
        """Validate choice parameter definition."""
        if not isinstance(choices, list) or not choices:
            raise ValueError(f"Choices for {param_name} must be non-empty list")
    
    def get_grid_points(self) -> List[Dict[str, Any]]:
        """
        Generate all grid points for exhaustive grid search.
        
        Returns:
            List of parameter combinations for grid search
        """
        param_values = {}
        
        for param_name, param_def in self.parameters.items():
            if isinstance(param_def, dict):
                if 'range' in param_def:
                    param_values[param_name] = self._generate_range_values(param_def['range'])
                elif 'choices' in param_def:
                    param_values[param_name] = param_def['choices']
            else:
                # Handle direct list values
                param_values[param_name] = [param_def] if not isinstance(param_def, list) else param_def
        
        # Generate all combinations
        param_names = list(param_values.keys())
        param_combinations = list(itertools.product(*param_values.values()))
        
        return [dict(zip(param_names, combo)) for combo in param_combinations]
    
    def _generate_range_values(self, range_def: List) -> List[float]:
        """Generate values from range definition."""
        if len(range_def) == 2:
            min_val, max_val = range_def
            step = 1.0
        else:
            min_val, max_val, step = range_def
            
        # Use numpy arange for better floating point handling
        values = np.arange(min_val, max_val + step/2, step)
        return values.tolist()
    
    def sample_random_point(self, random_state: np.random.RandomState = None) -> Dict[str, Any]:
        """
        Sample a random point from the parameter space.
        
        Args:
            random_state: Random state for reproducible results
            
        Returns:
            Dictionary of randomly sampled parameter values
        """
        if random_state is None:
            random_state = np.random.RandomState()
            
        sampled_params = {}
        
        for param_name, param_def in self.parameters.items():
            if isinstance(param_def, dict):
                if 'range' in param_def:
                    sampled_params[param_name] = self._sample_range_value(param_def['range'], random_state)
                elif 'choices' in param_def:
                    sampled_params[param_name] = random_state.choice(param_def['choices'])
            else:
                # Handle direct values
                if isinstance(param_def, list):
                    sampled_params[param_name] = random_state.choice(param_def)
                else:
                    sampled_params[param_name] = param_def
                    
        return sampled_params
    
    def _sample_range_value(self, range_def: List, random_state: np.random.RandomState) -> float:
        """Sample a value from range definition."""
        if len(range_def) == 2:
            min_val, max_val = range_def
            return random_state.uniform(min_val, max_val)
        else:
            min_val, max_val, step = range_def
            # Sample from discrete steps
            num_steps = int((max_val - min_val) / step) + 1
            step_idx = random_state.randint(0, num_steps)
            return min_val + step_idx * step
    
    def get_space_size(self) -> int:
        """
        Calculate the total size of the parameter space for grid search.
        
        Returns:
            Total number of parameter combinations
        """
        total_size = 1
        
        for param_name, param_def in self.parameters.items():
            if isinstance(param_def, dict):
                if 'range' in param_def:
                    range_values = self._generate_range_values(param_def['range'])
                    total_size *= len(range_values)
                elif 'choices' in param_def:
                    total_size *= len(param_def['choices'])
            else:
                if isinstance(param_def, list):
                    total_size *= len(param_def)
                    
        return total_size
    
    def get_parameter_names(self) -> List[str]:
        """Get list of parameter names."""
        return list(self.parameters.keys())
