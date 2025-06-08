import pytest
from unittest.mock import Mock, patch
import numpy as np

from src.meqsap.exceptions import DataError, BacktestError, ConfigurationError
from src.meqsap.optimizer.engine import OptimizationEngine, FAILED_TRIAL_SCORE, TrialFailureType
from src.meqsap.optimizer.models import ProgressData


class TestOptimizationErrorHandling:
    """Test suite for optimization error handling functionality."""
    
    @pytest.fixture
    def mock_engine(self):
        """Create a properly initialized OptimizationEngine with mock dependencies."""
        # This mock config must contain all required fields for StrategyConfig
        # to prevent pydantic.ValidationError inside the method under test.
        mock_config = {
            "ticker": "DUMMY",
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",
            "strategy_type": "MovingAverageCrossover",
            "strategy_params": {
                "fast_ma": {"type": "range", "start": 5, "stop": 15, "step": 1},
                "slow_ma": {"type": "range", "start": 20, "stop": 50, "step": 5}
            }
        }
        mock_objective_fn = Mock()
        
        engine = OptimizationEngine(
            strategy_config=mock_config,
            objective_function=mock_objective_fn,
            objective_params={},
            algorithm_params={}
        )
        return engine
    
    @pytest.mark.parametrize("exception_type,expected_failure_type", [
        (DataError("Insufficient data"), TrialFailureType.DATA_ERROR),
        (BacktestError("Division by zero"), TrialFailureType.CALCULATION_ERROR),
        (ConfigurationError("Invalid parameters"), TrialFailureType.VALIDATION_ERROR),
        (Exception("Unknown error"), TrialFailureType.UNKNOWN_ERROR),
    ])
    def test_single_trial_error_handling(self, mock_engine, exception_type, expected_failure_type, caplog, mocker):
        """Test that _run_single_trial handles different exception types correctly."""
        # Mock dependencies
        mock_trial = Mock()
        mock_trial.number = 1
        mock_trial.params = {"fast_ma": 10, "slow_ma": 20}
        
        mock_market_data = Mock()
        
        # Patch the backtest function to raise the exception
        mock_backtest = mocker.patch('src.meqsap.optimizer.engine.run_complete_backtest')
        mock_backtest.side_effect = exception_type
        
        # Patch other methods
        mocker.patch.object(mock_engine, '_suggest_params_for_trial', return_value=mock_trial.params)
        mocker.patch.object(mock_engine, '_record_failure')
        mocker.patch.object(mock_engine, '_update_progress')
        
        # Execute the method - engine needs _market_data set
        mock_engine._market_data = mock_market_data
        result = mock_engine._run_single_trial(mock_trial, mock_market_data)
        
        # Assertions
        assert result == FAILED_TRIAL_SCORE
        mock_engine._record_failure.assert_called_once_with(expected_failure_type, mock_trial.params)
        
        # Set caplog level to capture DEBUG logs
        caplog.set_level("DEBUG")
        
        # Check logging
        if isinstance(exception_type, (DataError, BacktestError, ConfigurationError)):
            # The first log is INFO "Starting trial...", the second is WARNING for the error
            warning_logs = [rec for rec in caplog.records 
                          if rec.levelname == 'WARNING' and rec.name == "src.meqsap.optimizer.engine"]
            assert len(warning_logs) >= 1
            assert expected_failure_type.value in warning_logs[0].message
        else:
            # The first log is INFO, the second is DEBUG for the unexpected error
            debug_logs = [rec for rec in caplog.records 
                         if rec.levelname == 'DEBUG' and rec.name == "src.meqsap.optimizer.engine"]
            assert len(debug_logs) >= 1
            assert "failed with unexpected error" in debug_logs[0].message
    
    def test_successful_trial(self, mock_engine, mocker):
        """Test successful trial execution."""
        # Mock dependencies
        mock_trial = Mock()
        mock_trial.number = 1
        mock_trial.params = {"fast_ma": 10, "slow_ma": 20}
        
        mock_market_data = Mock()
        mock_backtest_result = Mock()
        expected_score = 1.25
        
        # Mock successful backtest
        mock_backtest = mocker.patch('src.meqsap.optimizer.engine.run_complete_backtest')
        mock_backtest.return_value = mock_backtest_result
        
        # Mock objective function
        mock_engine.objective_function = Mock(return_value=expected_score)
        mock_engine.objective_params = {}
        
        # Patch other methods
        mocker.patch.object(mock_engine, '_suggest_params_for_trial', return_value=mock_trial.params)
        mocker.patch.object(mock_engine, '_update_progress')
        
        # Execute the method
        mock_engine._market_data = mock_market_data
        result = mock_engine._run_single_trial(mock_trial, mock_market_data)
        
        # Assertions
        assert result == expected_score
        assert mock_engine._successful_trials == 1
        assert mock_engine._best_score == expected_score
        mock_engine.objective_function.assert_called_once_with(mock_backtest_result, {})
    
    def test_record_failure(self, mock_engine):
        """Test failure recording functionality."""
        params = {"fast_ma": 10, "slow_ma": 20}
        
        mock_engine._record_failure(TrialFailureType.DATA_ERROR, params)
        
        assert mock_engine._failed_trials_by_type[TrialFailureType.DATA_ERROR] == 1
        assert mock_engine._failed_trials_by_type[TrialFailureType.CALCULATION_ERROR] == 0
    
    def test_progress_callback_invocation(self, mock_engine):
        """Test that progress callback is called with correct data."""
        # Setup mock callback
        mock_callback = Mock()
        mock_engine._progress_callback = mock_callback
        mock_engine._start_time = 100
        mock_engine._best_score = 1.5
        mock_engine._total_trials = 10
        mock_engine._failed_trials_by_type[TrialFailureType.DATA_ERROR] = 2
        mock_engine._current_trial = 1  # Simulate being in the first trial
        
        # Mock time.time
        with patch('time.time', return_value=150):
            params = {"fast_ma": 15}
            mock_engine._update_progress(params)
        
        # Verify callback was called
        mock_callback.assert_called_once()
        progress_data = mock_callback.call_args[0][0]
        
        assert isinstance(progress_data, ProgressData)
        assert progress_data.current_trial == 1  # Incremented from 0
        assert progress_data.best_score == 1.5
        assert progress_data.elapsed_seconds == 50
        assert progress_data.failed_trials_summary == {"Data Error": 2}
        assert progress_data.current_params == params
