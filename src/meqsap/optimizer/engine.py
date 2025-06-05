"""Main optimization engine for orchestrating parameter optimization workflows."""

import logging
from typing import Dict, Any, Optional, Callable
from pathlib import Path

from ..config import StrategyConfig
from .config import OptimizationConfig
from .parameter_space import ParameterSpace
from .objective_functions import ObjectiveFunctionFactory
from .algorithms import OptimizationFactory, OptimizationProgress
from .results import OptimizationResult

logger = logging.getLogger(__name__)


class OptimizationEngine:
    """Main orchestrator class managing optimization workflows."""
    
    def __init__(self, progress_callback: Optional[Callable[[OptimizationProgress], None]] = None):
        """
        Initialize optimization engine.
        
        Args:
            progress_callback: Optional callback for progress updates
        """
        self.progress_callback = progress_callback
        
    def run_single_indicator_optimization(
        self,
        strategy_config: StrategyConfig,
        optimization_config: OptimizationConfig
    ) -> OptimizationResult:
        """
        Orchestrate complete optimization workflow for single-indicator strategies.
        
        Args:
            strategy_config: Strategy configuration with parameter definitions
            optimization_config: Optimization algorithm and objective function settings
            
        Returns:
            OptimizationResult: Comprehensive optimization results with constraint adherence
            
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If optimization fails
        """
        logger.info("Starting single-indicator optimization workflow")
        logger.info(f"Strategy: {strategy_config.strategy_type}")
        logger.info(f"Algorithm: {optimization_config.algorithm}")
        logger.info(f"Objective: {optimization_config.objective_function}")
        
        try:
            # Create parameter space from strategy configuration
            parameter_space = self._create_parameter_space(strategy_config)
            logger.info(f"Parameter space created with {parameter_space.total_combinations} combinations")
            
            # Create objective function
            objective_function = self._create_objective_function(
                optimization_config, strategy_config
            )
            logger.info(f"Objective function created: {objective_function.__class__.__name__}")
            
            # Create optimization algorithm
            optimizer = self._create_optimizer(
                optimization_config, parameter_space, objective_function
            )
            logger.info(f"Optimizer created: {optimizer.__class__.__name__}")
            
            # Set progress callback if provided
            if self.progress_callback:
                optimizer.set_progress_callback(self.progress_callback)
                
            # Run optimization
            algorithm_params = optimization_config.algorithm_params or {}
            result = optimizer.optimize(**algorithm_params)
            
            logger.info(f"Optimization completed successfully")
            logger.info(f"Best value: {result.best_value:.6f}")
            logger.info(f"Best parameters: {result.best_parameters}")
            
            return result
            
        except Exception as e:
            logger.error(f"Optimization failed: {str(e)}")
            raise RuntimeError(f"Single-indicator optimization failed: {str(e)}") from e
    
    def _create_parameter_space(self, strategy_config: StrategyConfig) -> ParameterSpace:
        """Create parameter space from strategy configuration."""
        try:
            parameter_space = ParameterSpace()
            
            # Add parameters from strategy configuration
            if hasattr(strategy_config, 'parameters') and strategy_config.parameters:
                for param_name, param_def in strategy_config.parameters.items():
                    parameter_space.add_parameter(param_name, param_def)
                    
            if parameter_space.total_combinations == 0:
                raise ValueError("No valid parameter combinations found in strategy configuration")
                
            return parameter_space
            
        except Exception as e:
            raise ValueError(f"Failed to create parameter space: {str(e)}") from e
    
    def _create_objective_function(
        self, 
        optimization_config: OptimizationConfig,
        strategy_config: StrategyConfig
    ):
        """Create objective function from optimization configuration."""
        try:
            return ObjectiveFunctionFactory.create_objective_function(
                objective_name=optimization_config.objective_function,
                strategy_config=strategy_config,
                objective_params=optimization_config.objective_params or {}
            )
        except Exception as e:
            raise ValueError(f"Failed to create objective function: {str(e)}") from e
    
    def _create_optimizer(
        self,
        optimization_config: OptimizationConfig,
        parameter_space: ParameterSpace,
        objective_function
    ):
        """Create optimization algorithm from configuration."""
        try:
            return OptimizationFactory.create_optimizer(
                algorithm_name=optimization_config.algorithm,
                parameter_space=parameter_space,
                objective_function=objective_function
            )
        except Exception as e:
            raise ValueError(f"Failed to create optimizer: {str(e)}") from e


def evaluate_parameter_set(params: Dict[str, Any], config: StrategyConfig) -> float:
    """
    Evaluate a single parameter combination for single-indicator strategies.
    
    This is a helper function that can be used independently of the main
    optimization workflow for testing or manual parameter evaluation.
    
    Args:
        params: Parameter combination to evaluate
        config: Strategy configuration
        
    Returns:
        Objective value for the parameter combination
        
    Raises:
        ValueError: If parameters are invalid
        RuntimeError: If backtest evaluation fails
    """
    from ..backtest import run_backtest
    
    try:
        # Create modified config with new parameters
        modified_config = config.copy()
        if hasattr(modified_config, 'parameters'):
            modified_config.parameters.update(params)
        else:
            modified_config.parameters = params
            
        # Run backtest
        result = run_backtest(modified_config)
        
        # Return basic Sharpe ratio as default evaluation
        return result.sharpe_ratio if result.sharpe_ratio is not None else 0.0
        
    except Exception as e:
        logger.error(f"Failed to evaluate parameter set {params}: {str(e)}")
        raise RuntimeError(f"Parameter evaluation failed: {str(e)}") from e


def generate_optimization_report(result: OptimizationResult, output_dir: Path) -> None:
    """
    Create detailed optimization analysis report with constraint adherence metrics.
    
    Args:
        result: Optimization results to report
        output_dir: Directory to save report files
        
    Raises:
        IOError: If report generation fails
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate summary report
        summary_path = output_dir / "optimization_summary.txt"
        with open(summary_path, 'w') as f:
            f.write("MEQSAP Optimization Results Summary\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Algorithm: {result.algorithm_name}\n")
            f.write(f"Total Evaluations: {result.total_iterations}\n")
            f.write(f"Failed Evaluations: {result.failed_iterations}\n")
            f.write(f"Success Rate: {result.success_rate:.2%}\n\n")
            
            f.write("Best Result:\n")
            f.write(f"  Value: {result.best_value:.6f}\n")
            f.write(f"  Parameters: {result.best_parameters}\n\n")
            
            if result.constraint_adherence:
                f.write("Constraint Adherence:\n")
                for constraint, adherence in result.constraint_adherence.items():
                    f.write(f"  {constraint}: {adherence:.2%}\n")
        
        logger.info(f"Optimization report saved to {summary_path}")
        
        # Generate detailed CSV report
        csv_path = output_dir / "optimization_details.csv"
        result.to_csv(csv_path)
        logger.info(f"Detailed results saved to {csv_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate optimization report: {str(e)}")
        raise IOError(f"Report generation failed: {str(e)}") from e
