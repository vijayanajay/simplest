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
        """Create a mock optimization engine for testing."""
        with patch('src.meqsap.optimizer.engine.OptimizationEngine.__init__', return_value=None):
            engine = OptimizationEngine(None, None, None)
            engine._failed_trials_by_type = {failure_type: 0 for failure_type in TrialFailureType}
            engine._successful_trials = 0
            engine._best_score = None
            engine._current_trial = 0
            engine._start_time = 0
            engine._progress_callback = None
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
        mocker.patch.object(mock_engine, '_generate_concrete_params', return_value={})
        mocker.patch.object(mock_engine, '_record_failure')
        mocker.patch.object(mock_engine, '_update_progress')
        
        # Execute the method - engine needs _market_data set
        mock_engine._market_data = mock_market_data
        result = mock_engine._run_single_trial(mock_trial)
        
        # Assertions
        assert result == FAILED_TRIAL_SCORE
        mock_engine._record_failure.assert_called_once_with(expected_failure_type, mock_trial.params)
        
        # Check logging
        if isinstance(exception_type, (DataError, BacktestError, ConfigurationError)):
            assert expected_failure_type.value in caplog.text
            assert caplog.records[0].levelname == "WARNING"
        else:
            assert caplog.records[0].levelname == "DEBUG"
    
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
        mocker.patch.object(mock_engine, '_generate_concrete_params', return_value={})
        mocker.patch.object(mock_engine, '_update_progress')
        
        # Execute the method
        mock_engine._market_data = mock_market_data
        result = mock_engine._run_single_trial(mock_trial)
        
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
