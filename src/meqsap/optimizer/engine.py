"""Optimization engine with progress tracking and robust error handling."""

import logging
import time
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Callable
from collections import defaultdict

import optuna
from optuna import Trial

from ..exceptions import DataError, BacktestError, ConfigurationError
from ..backtest import run_complete_backtest, BacktestAnalysisResult
from .models import TrialFailureType, ProgressData, ErrorSummary, OptimizationResult

# Constants
FAILED_TRIAL_SCORE = -np.inf

logger = logging.getLogger(__name__)


class OptimizationEngine:
    """Core optimization engine with progress tracking and error handling."""
    def __init__(self, strategy_config: Dict[str, Any], objective_function: Callable, 
                 objective_params: Optional[Dict[str, Any]] = None,
                 algorithm_params: Optional[Dict[str, Any]] = None):
        """Initialize optimization engine.
        
        Args:
            strategy_config: Strategy configuration including parameter spaces
            objective_function: Function to evaluate backtest results
            objective_params: Additional parameters for objective function
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
            # Grid sampler requires search space definition
            # For now, return None and let Optuna use default
            logger.info("Grid sampler requested but not yet implemented with parameter spaces")
            return None
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
        effective_n_trials = n_trials or self.algorithm_params.get("n_trials", 100)
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
        direction = self.algorithm_params.get("direction", "maximize")
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
                callbacks=[self._trial_callback] if progress_callback else None
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
        trial_params = trial.params.copy()
        
        logger.info(f"Starting trial {trial.number} with params: {trial_params}")
        
        try:
            # Generate concrete parameters from trial suggestions
            concrete_params = self._generate_concrete_params(trial)
            
            # Execute backtest with error handling
            backtest_result = run_complete_backtest(
                self.strategy_config,
                market_data,
                concrete_params,
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
            self._update_progress(trial_params)
            
            return score
            
        except DataError as e:
            logger.warning(f"Trial {trial.number} failed: [{TrialFailureType.DATA_ERROR.value}] {e}. Params: {trial_params}")
            self._record_failure(TrialFailureType.DATA_ERROR, trial_params)
            return FAILED_TRIAL_SCORE
            
        except BacktestError as e:
            logger.warning(f"Trial {trial.number} failed: [{TrialFailureType.CALCULATION_ERROR.value}] {e}. Params: {trial_params}")
            self._record_failure(TrialFailureType.CALCULATION_ERROR, trial_params)
            return FAILED_TRIAL_SCORE
            
        except ConfigurationError as e:
            logger.warning(f"Trial {trial.number} failed: [{TrialFailureType.VALIDATION_ERROR.value}] {e}. Params: {trial_params}")
            self._record_failure(TrialFailureType.VALIDATION_ERROR, trial_params)
            return FAILED_TRIAL_SCORE
            
        except Exception as e:
            logger.debug(f"Trial {trial.number} failed with unexpected error. Params: {trial_params}", exc_info=True)
            self._record_failure(TrialFailureType.UNKNOWN_ERROR, trial_params)
            return FAILED_TRIAL_SCORE
    
    def _generate_concrete_params(self, trial: Trial) -> Dict[str, Any]:
        """Generate concrete parameters from trial suggestions.
        
        Args:
            trial: Optuna trial object
            
        Returns:
            Dictionary of concrete parameter values
        """
        # This is a simplified implementation
        # Real implementation would use parameter spaces from strategy config
        params = {}
        
        # Example parameter suggestions - this would be dynamic based on strategy
        if "fast_ma" in self.strategy_config.get("parameter_spaces", {}):
            params["fast_ma"] = trial.suggest_int("fast_ma", 5, 20)
        if "slow_ma" in self.strategy_config.get("parameter_spaces", {}):
            params["slow_ma"] = trial.suggest_int("slow_ma", 20, 50)
            
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
                    analysis = run_complete_backtest(
                        self.strategy_config,
                        self._market_data,
                        best_params
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