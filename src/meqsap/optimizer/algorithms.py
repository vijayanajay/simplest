"""Optimization algorithms for parameter search."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional, Iterator
import itertools
import random
from dataclasses import dataclass
from tqdm import tqdm

from .parameter_space import ParameterSpace
from .objective_functions import ObjectiveFunction
from .results import OptimizationResult

logger = logging.getLogger(__name__)


@dataclass
class OptimizationProgress:
    """Progress tracking for optimization algorithms."""
    current_iteration: int
    total_iterations: int
    best_value: Optional[float]
    current_params: Dict[str, Any]
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress as percentage."""
        if self.total_iterations == 0:
            return 0.0
        return (self.current_iteration / self.total_iterations) * 100


class OptimizationAlgorithm(ABC):
    """Base class for optimization algorithms."""
    
    def __init__(self, parameter_space: ParameterSpace, objective_function: ObjectiveFunction):
        self.parameter_space = parameter_space
        self.objective_function = objective_function
        self.progress_callback: Optional[callable] = None
        
    def set_progress_callback(self, callback: callable) -> None:
        """Set callback for progress updates."""
        self.progress_callback = callback
        
    @abstractmethod
    def optimize(self, **kwargs) -> OptimizationResult:
        """Run the optimization algorithm."""
        pass
        
    def _update_progress(self, progress: OptimizationProgress) -> None:
        """Update progress if callback is set."""
        if self.progress_callback:
            self.progress_callback(progress)


class GridSearchOptimizer(OptimizationAlgorithm):
    """Exhaustive grid search optimization for single-indicator strategies."""
    
    def optimize(self, **kwargs) -> OptimizationResult:
        """
        Run exhaustive grid search optimization.
        
        Returns:
            OptimizationResult: Complete optimization results with constraint adherence
        """
        logger.info("Starting grid search optimization")
        
        # Generate all parameter combinations
        param_combinations = list(self.parameter_space.generate_grid())
        total_combinations = len(param_combinations)
        
        logger.info(f"Grid search will evaluate {total_combinations} parameter combinations")
        
        if total_combinations == 0:
            raise ValueError("Parameter space contains no valid combinations")
            
        results = []
        failures = 0
        max_failures = kwargs.get('max_failures', 10)
        
        # Progress tracking
        progress_bar = tqdm(
            param_combinations, 
            desc="Grid Search Optimization",
            unit="combination"
        )
        
        for i, params in enumerate(progress_bar):
            try:
                # Evaluate parameter combination
                objective_value = self.objective_function.evaluate(params)
                results.append((params, objective_value))
                
                # Update progress
                current_best = max(results, key=lambda x: x[1].value)[1].value if results else None
                progress = OptimizationProgress(
                    current_iteration=i + 1,
                    total_iterations=total_combinations,
                    best_value=current_best,
                    current_params=params
                )
                self._update_progress(progress)
                
                # Update progress bar
                if current_best is not None:
                    progress_bar.set_postfix({
                        'Best': f"{current_best:.4f}",
                        'Current': f"{objective_value.value:.4f}"
                    })
                
            except Exception as e:
                failures += 1
                logger.warning(f"Failed to evaluate parameters {params}: {str(e)}")
                
                if failures >= max_failures:
                    logger.error(f"Maximum failures ({max_failures}) reached, stopping optimization")
                    break
        
        progress_bar.close()
        
        if not results:
            raise RuntimeError("Grid search failed to evaluate any parameter combinations")
            
        logger.info(f"Grid search completed with {len(results)} successful evaluations and {failures} failures")
        
        return OptimizationResult.from_evaluations(
            evaluations=results,
            algorithm_name="grid_search",
            parameter_space=self.parameter_space,
            total_iterations=len(results),
            failed_iterations=failures
        )


class RandomSearchOptimizer(OptimizationAlgorithm):
    """Random sampling optimization with configurable distributions."""
    
    def optimize(self, max_iterations: int = 100, seed: Optional[int] = None, **kwargs) -> OptimizationResult:
        """
        Run random search optimization.
        
        Args:
            max_iterations: Maximum number of parameter combinations to evaluate
            seed: Random seed for reproducibility
            
        Returns:
            OptimizationResult: Complete optimization results with constraint adherence
        """
        logger.info(f"Starting random search optimization with {max_iterations} iterations")
        
        if seed is not None:
            random.seed(seed)
            logger.info(f"Random seed set to {seed}")
            
        results = []
        failures = 0
        max_failures = kwargs.get('max_failures', 10)
        
        # Progress tracking
        progress_bar = tqdm(
            range(max_iterations),
            desc="Random Search Optimization", 
            unit="iteration"
        )
        
        for i in progress_bar:
            try:
                # Sample random parameter combination
                params = self.parameter_space.sample_random()
                
                # Evaluate parameter combination
                objective_value = self.objective_function.evaluate(params)
                results.append((params, objective_value))
                
                # Update progress
                current_best = max(results, key=lambda x: x[1].value)[1].value if results else None
                progress = OptimizationProgress(
                    current_iteration=i + 1,
                    total_iterations=max_iterations,
                    best_value=current_best,
                    current_params=params
                )
                self._update_progress(progress)
                
                # Update progress bar
                if current_best is not None:
                    progress_bar.set_postfix({
                        'Best': f"{current_best:.4f}",
                        'Current': f"{objective_value.value:.4f}"
                    })
                
            except Exception as e:
                failures += 1
                logger.warning(f"Failed to evaluate parameters {params}: {str(e)}")
                
                if failures >= max_failures:
                    logger.error(f"Maximum failures ({max_failures}) reached, stopping optimization")
                    break
        
        progress_bar.close()
        
        if not results:
            raise RuntimeError("Random search failed to evaluate any parameter combinations")
            
        logger.info(f"Random search completed with {len(results)} successful evaluations and {failures} failures")
        
        return OptimizationResult.from_evaluations(
            evaluations=results,
            algorithm_name="random_search",
            parameter_space=self.parameter_space,
            total_iterations=len(results),
            failed_iterations=failures
        )


class OptimizationFactory:
    """Factory for creating optimization algorithms."""
    
    _algorithms = {
        'grid_search': GridSearchOptimizer,
        'random_search': RandomSearchOptimizer,
    }
    
    @classmethod
    def create_optimizer(
        self,
        algorithm_name: str,
        parameter_space: ParameterSpace,
        objective_function: ObjectiveFunction
    ) -> OptimizationAlgorithm:
        """
        Create optimization algorithm instance.
        
        Args:
            algorithm_name: Name of algorithm ('grid_search' or 'random_search')
            parameter_space: Parameter space to optimize over
            objective_function: Objective function to optimize
            
        Returns:
            OptimizationAlgorithm: Configured optimization algorithm
            
        Raises:
            ValueError: If algorithm_name is not supported
        """
        if algorithm_name not in self._algorithms:
            supported = ', '.join(self._algorithms.keys())
            raise ValueError(f"Unsupported algorithm '{algorithm_name}'. Supported: {supported}")
            
        algorithm_class = self._algorithms[algorithm_name]
        return algorithm_class(parameter_space, objective_function)
    
    @classmethod
    def list_algorithms(cls) -> List[str]:
        """List available optimization algorithms."""
        return list(cls._algorithms.keys())
