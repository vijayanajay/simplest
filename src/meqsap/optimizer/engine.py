"""Optimization engine with progress tracking and robust error handling."""

import logging
import time
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Callable, List
from collections import defaultdict

import optuna
from optuna import Trial

from ..exceptions import DataError, BacktestError, ConfigurationError
from ..backtest import run_complete_backtest, BacktestAnalysisResult
from .models import TrialFailureType, ProgressData, ErrorSummary, OptimizationResult
from ..config import StrategyFactory, StrategyConfig

# Constants
FAILED_TRIAL_SCORE = -np.inf

logger = logging.getLogger(__name__)


class _ParameterParser:
    """Helper class to parse a single parameter definition for different samplers."""

    def __init__(self, name: str, definition: Any):
        self.name = name
        self.definition = definition

    def for_grid_search(self) -> List[Any]:
        """Returns a list of values for GridSampler."""
        if isinstance(self.definition, dict):
            param_type = self.definition.get("type")
            if param_type == "range":
                start, stop, step = self.definition['start'], self.definition['stop'], self.definition['step']
                if all(isinstance(x, int) for x in [start, stop, step]):
                    return list(range(start, stop + 1, step))
                else:
                    num_steps = int(round((stop - start) / step)) + 1
                    return np.linspace(start, stop, num=num_steps).tolist()
            elif param_type == "choices":
                return self.definition['values']
            elif param_type == "value":
                return [self.definition['value']]
            else:
                raise ConfigurationError(
                    f"Unsupported parameter definition type '{param_type}' for GridSearch on parameter '{self.name}'."
                )
        elif isinstance(self.definition, (int, float, str, bool)):
            return [self.definition]
        else:
            raise ConfigurationError(
                f"Unsupported parameter definition for GridSearch on parameter '{self.name}': {self.definition}"
            )

    def for_trial_suggestion(self, trial: Trial) -> Any:
        """Suggests a value for a trial for other samplers."""
        if isinstance(self.definition, dict):
            param_type = self.definition.get("type")
            if param_type == "range":
                start, stop, step = self.definition['start'], self.definition['stop'], self.definition['step']
                if all(float(x).is_integer() for x in [start, stop, step]):
                    return trial.suggest_int(self.name, int(start), int(stop), step=int(step))
                else:
                    return trial.suggest_float(self.name, float(start), float(stop), step=float(step))
            elif param_type == "choices":
                return trial.suggest_categorical(self.name, self.definition['values'])
            elif param_type == "value":
                return self.definition['value']
            else:
                raise ConfigurationError(
                    f"Unsupported parameter definition type '{param_type}' for trial suggestion on parameter '{self.name}'."
                )
        elif isinstance(self.definition, (int, float, str, bool)):
            return self.definition
        else:
            raise ConfigurationError(
                f"Unsupported parameter definition for trial suggestion on parameter '{self.name}': {self.definition}"
            )


class OptimizationEngine:
    """Core optimization engine with progress tracking and error handling."""
    def __init__(self, strategy_config: StrategyConfig, objective_function: Callable, 
                 objective_params: Optional[Dict[str, Any]] = None,
                 algorithm_params: Optional[Dict[str, Any]] = None):
        """Initialize optimization engine.
        
        Args:
            strategy_config: The full strategy configuration object
            objective_function: The function to optimize
            objective_params: Parameters for the objective function
            algorithm_params: Parameters for the optimization algorithm. Supported keys:
                - n_trials: Default number of trials (overridden by run_optimization param)
                - sampler: Optuna sampler type ('tpe', 'random', 'grid', 'cmaes')
                - pruner: Optuna pruner type ('median', 'successive_halving', 'hyperband')
                - random_seed: Random seed for reproducibility
                - timeout: Timeout in seconds for optimization
                - direction: Optimization direction ('maximize' or 'minimize')
        """
        self.strategy_config = strategy_config
        self.objective_function = objective_function
        self.objective_params = objective_params or {}
        self.algorithm_params = algorithm_params or {}

        # Initialize state attributes
        self._progress_callback: Optional[Callable[[ProgressData], None]] = None
        self._total_trials: Optional[int] = None
        self._interruption_event = None
        self._market_data = None
        self._start_time: float = 0.0
        self._current_trial: int = 0
        self._successful_trials: int = 0        
        self._best_score: Optional[float] = None
        self._failed_trials_by_type: Dict[TrialFailureType, int] = defaultdict(int)
    
    def _get_grid_search_space(self) -> Dict[str, List[Any]]:
        """
        Returns a search space dictionary suitable for optuna.samplers.GridSampler.
        """
        search_space = {}
        strategy_params_dict = self.strategy_config.strategy_params

        for param_name, param_def in strategy_params_dict.items():
            parser = _ParameterParser(param_name, param_def)
            search_space[param_name] = parser.for_grid_search()

        if not search_space:
            raise ConfigurationError("GridSearch requires at least one parameter with a defined search space (range or choices).")

        return search_space

    def _get_grid_constraints_func(self) -> Optional[Callable[[optuna.trial.FrozenTrial], bool]]:
        """
        Returns a constraints function for the GridSampler based on the strategy.
        This is used to prune invalid parameter combinations from the grid.
        """
        strategy_type = self.strategy_config.strategy_type

        if strategy_type == "MovingAverageCrossover":
            def constraints(trial: optuna.trial.FrozenTrial) -> bool:
                # Prune if fast_ma is not smaller than slow_ma
                if "fast_ma" in trial.params and "slow_ma" in trial.params:
                    return trial.params["fast_ma"] < trial.params["slow_ma"]
                return True  # No constraint to apply if params are missing
            return constraints

        # Return None if no constraints for this strategy type
        return None
    
    def _get_sampler(self) -> Optional[optuna.samplers.BaseSampler]:
        """Get Optuna sampler based on algorithm parameters.
        
        Returns:
            Configured sampler or None for default
        """
        sampler_type = self.algorithm_params.get("sampler", "tpe").lower()
        random_seed = self.algorithm_params.get("random_seed")
        if sampler_type == "random":
            return optuna.samplers.RandomSampler(seed=random_seed)
        elif sampler_type == "grid":
            logger.info("Grid sampler requested. Building search space...")
            search_space = self._get_grid_search_space()
            constraints_func = self._get_grid_constraints_func()
            return optuna.samplers.GridSampler(search_space, constraints_func=constraints_func)
        elif sampler_type == "cmaes":
            return optuna.samplers.CmaEsSampler(seed=random_seed)
        elif sampler_type == "tpe":
            return optuna.samplers.TPESampler(seed=random_seed)
        else:
            logger.warning(f"Unknown sampler type: {sampler_type}, using default TPE")
            return optuna.samplers.TPESampler(seed=random_seed)
    
    def _get_pruner(self) -> Optional[optuna.pruners.BasePruner]:
        """Get Optuna pruner based on algorithm parameters.
        
        Returns:
            Configured pruner or None for no pruning
        """
        pruner_type = self.algorithm_params.get("pruner")
        if not pruner_type:
            return None
            
        pruner_type = pruner_type.lower()
        if pruner_type == "median":
            return optuna.pruners.MedianPruner()
        elif pruner_type == "successive_halving":
            return optuna.pruners.SuccessiveHalvingPruner()
        elif pruner_type == "hyperband":
            return optuna.pruners.HyperbandPruner()        
        else:
            logger.warning(f"Unknown pruner type: {pruner_type}, using no pruning")
            return None
    
    def _validate_and_normalize_direction(self, direction: str) -> str:
        """Validate and normalize optimization direction.
        
        Args:
            direction: Direction string from algorithm parameters
            
        Returns:
            Normalized direction string ("maximize" or "minimize")
            
        Raises:
            ConfigurationError: If direction is invalid
        """
        if not isinstance(direction, str):
            raise ConfigurationError(f"Direction must be a string, got {type(direction).__name__}")
        
        normalized = direction.strip().lower()
        
        if normalized not in ("maximize", "minimize"):
            raise ConfigurationError(
                f"Invalid optimization direction '{direction}'. Must be 'maximize' or 'minimize'."
            )
        
        return normalized
      
    def run_optimization(self, market_data: pd.DataFrame, progress_callback: Optional[Callable[[ProgressData], None]] = None,
                        interruption_event=None, n_trials: Optional[int] = None) -> OptimizationResult:
        """Run optimization with progress tracking and error handling.
        
        Args:
            market_data: Market data DataFrame for backtesting
            progress_callback: Callback for progress updates
            interruption_event: Event for graceful interruption
            n_trials: Number of trials for random search (overrides algorithm_params default)
            
        Returns:
            OptimizationResult with best parameters and comprehensive statistics
        """    
        self._progress_callback = progress_callback
        self._interruption_event = interruption_event
        
        # Use n_trials from parameter or fall back to algorithm_params default
        effective_n_trials = n_trials if n_trials is not None else self.algorithm_params.get("n_trials", 100)
        self._total_trials = effective_n_trials
        self._market_data = market_data

        # Reset state for the new run
        self._start_time = time.time()
        self._current_trial = 0
        self._successful_trials = 0
        self._best_score = None
        self._failed_trials_by_type = defaultdict(int)
        logger.info(f"Starting optimization with {effective_n_trials} trials")
        
        # Configure Optuna study based on algorithm parameters
        raw_direction = self.algorithm_params.get("direction", "maximize")
        direction = self._validate_and_normalize_direction(raw_direction)
        sampler = self._get_sampler()
        pruner = self._get_pruner()
        
        # Create Optuna study with configured parameters
        storage = "sqlite:///meqsap_trials.db"
        study = optuna.create_study(
            direction=direction,
            storage=storage,
            study_name=f"meqsap_optimization_{int(time.time())}",
            sampler=sampler,
            pruner=pruner
        )
        
        # Set timeout if specified
        timeout = self.algorithm_params.get("timeout")
        try:
            # Run optimization with configured parameters
            study.optimize(
                lambda trial: self._run_single_trial(trial, market_data),
                n_trials=effective_n_trials,
                timeout=timeout,
                callbacks=[self._trial_callback] if progress_callback else []
            )
                
        except KeyboardInterrupt:
            logger.info("Optimization interrupted by user")
        except Exception as e:
            logger.error(f"Optimization failed with error: {e}", exc_info=True)
        
        # Compile results
        return self._compile_results(study)
    
    def _run_single_trial(self, trial: Trial, market_data) -> float:
        """Execute a single optimization trial with error handling.
        
        Args:
            trial: Optuna trial object
            market_data: Market data for backtesting
            
        Returns:
            Objective score or FAILED_TRIAL_SCORE
        """
        # Check for interruption
        if self._interruption_event and self._interruption_event.is_set():
            raise optuna.TrialPruned("Optimization interrupted")
        self._current_trial += 1
        concrete_params = self._suggest_params_for_trial(trial)
        logger.info(f"Starting trial {trial.number} with params: {concrete_params}")
        try:
            # Create a temporary config dict for this trial by injecting concrete_params
            trial_config_dict = self.strategy_config.model_dump()
            trial_config_dict['strategy_params'] = concrete_params
            # Create a StrategyConfig object for this trial to ensure a consistent interface
            config_for_trial = StrategyConfig(**trial_config_dict)

            # Execute backtest with error handling
            backtest_result = run_complete_backtest(
                config_for_trial,
                market_data,
                objective_params=self.objective_params
            )
            # Evaluate with objective function
            score = self.objective_function(backtest_result, self.objective_params)
            # Update best score
            if self._best_score is None or score > self._best_score:
                self._best_score = score
            self._successful_trials += 1
            logger.info(f"Trial {trial.number} completed successfully with score: {score}")
            # Update progress
            self._update_progress(concrete_params)
            return score
        except DataError as e:
            logger.warning(f"Trial {trial.number} failed: [{TrialFailureType.DATA_ERROR.value}] {e}. Params: {trial.params}")
            self._record_failure(TrialFailureType.DATA_ERROR, trial.params)
            return FAILED_TRIAL_SCORE
        except BacktestError as e:
            logger.warning(f"Trial {trial.number} failed: [{TrialFailureType.CALCULATION_ERROR.value}] {e}. Params: {trial.params}")
            self._record_failure(TrialFailureType.CALCULATION_ERROR, trial.params)
            return FAILED_TRIAL_SCORE
        except ConfigurationError as e:
            logger.warning(f"Trial {trial.number} failed: [{TrialFailureType.VALIDATION_ERROR.value}] {e}. Params: {trial.params}")
            self._record_failure(TrialFailureType.VALIDATION_ERROR, trial.params)
            return FAILED_TRIAL_SCORE
        except Exception as e:
            logger.debug(f"Trial {trial.number} failed with unexpected error. Params: {trial.params}", exc_info=True)
            self._record_failure(TrialFailureType.UNKNOWN_ERROR, trial.params)
            return FAILED_TRIAL_SCORE
    
    def _suggest_params_for_trial(self, trial: Trial) -> Dict[str, Any]:
        """
        Suggests parameter values for a given trial using the parameter definitions.
        """
        params = {}
        strategy_params_dict = self.strategy_config.strategy_params

        for param_name, param_def in strategy_params_dict.items():
            parser = _ParameterParser(param_name, param_def)
            params[param_name] = parser.for_trial_suggestion(trial)

        # Add business logic validation to prune invalid trials early.
        if 'fast_ma' in params and 'slow_ma' in params:
            if params['fast_ma'] >= params['slow_ma']:
                raise optuna.TrialPruned("fast_ma must be smaller than slow_ma.")

        return params
    
    def _record_failure(self, failure_type: TrialFailureType, params: Dict[str, Any]):
        """Record a trial failure by type.
        
        Args:
            failure_type: Type of failure encountered
            params: Parameters that caused the failure
        """
        self._failed_trials_by_type[failure_type] += 1
        self._update_progress(params)
    
    def _update_progress(self, params: Dict[str, Any]):
        """Update progress tracking and call progress callback.
        
        Args:
            params: Current trial parameters
        """
        if not self._progress_callback:
            return
            
        elapsed = time.time() - self._start_time
        failed_trials_summary = {
            failure_type.value: count 
            for failure_type, count in self._failed_trials_by_type.items()
            if count > 0
        }
        
        progress_data = ProgressData(
            current_trial=self._current_trial,
            total_trials=self._total_trials,
            best_score=self._best_score,
            elapsed_seconds=elapsed,
            failed_trials_summary=failed_trials_summary,
            current_params=params
        )
        
        self._progress_callback(progress_data)
    
    def _trial_callback(self, study, trial):
        """Optuna trial callback for progress updates."""
        # This callback is called after each trial completes
        # Progress update is already handled in _update_progress
        pass
    
    def _compile_results(self, study) -> OptimizationResult:
        """Compile final optimization results.
        
        Args:
            study: Optuna study object
            
        Returns:
            OptimizationResult with comprehensive statistics
        """
        elapsed_time = time.time() - self._start_time
        total_failed = sum(self._failed_trials_by_type.values())
        
        error_summary = ErrorSummary(
            total_failed_trials=total_failed,
            failure_counts_by_type={
                failure_type.value: count 
                for failure_type, count in self._failed_trials_by_type.items()
            }
        )
        
        timing_info = {
            "total_elapsed": elapsed_time,
            "avg_per_trial": elapsed_time / max(self._current_trial, 1),
            "successful_trials_time": elapsed_time * (self._successful_trials / max(self._current_trial, 1))
        }
        
        # Get best trial results
        best_params = None
        best_score = None
        best_strategy_analysis = None
        if study.best_trial:
            best_params = study.best_trial.params
            best_score = study.best_value
            
            # Re-run backtest for the best params to get full analysis
            if self._market_data is not None and best_params is not None:
                try:
                    logger.info(f"Re-running backtest for best parameters: {best_params}")
                    # Create a new config dict for the best trial
                    best_config_dict = self.strategy_config.model_dump()
                    best_config_dict['strategy_params'] = best_params
                    config_for_best_trial = StrategyConfig(**best_config_dict)

                    analysis = run_complete_backtest(
                        config_for_best_trial,
                        self._market_data,
                        objective_params=self.objective_params
                    )
                    best_strategy_analysis = analysis.model_dump()
                except Exception as e:
                    logger.error(f"Failed to re-run backtest for best parameters: {e}", exc_info=True)
        
        was_interrupted = (self._interruption_event and self._interruption_event.is_set()) if self._interruption_event else False
        
        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            best_strategy_analysis=best_strategy_analysis,
            total_trials=self._current_trial,
            successful_trials=self._successful_trials,
            error_summary=error_summary,
            was_interrupted=was_interrupted,
            constraint_adherence=None
        )