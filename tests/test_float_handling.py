import unittest
import warnings
import pandas as pd
import numpy as np
import datetime
from datetime import date
from src.meqsap.backtest import run_backtest, BacktestError, safe_float, StrategySignalGenerator
from src.meqsap.config import StrategyConfig, MovingAverageCrossoverParams
from unittest.mock import patch, MagicMock

# Suppress pandas_ta pkg_resources deprecation warning
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API", category=UserWarning)

class TestFloatConversions(unittest.TestCase):
    """Test float conversion handling in backtest module."""
    
    def setUp(self):
        """Set up test data."""
        # Create sample test data
        dates = pd.date_range(start='2022-01-01', periods=100)
        self.test_data = pd.DataFrame({
            'open': np.random.normal(100, 5, 100),      # lowercase
            'high': np.random.normal(105, 5, 100),     # lowercase
            'low': np.random.normal(95, 5, 100),       # lowercase
            'close': np.random.normal(100, 5, 100),    # lowercase
            'volume': np.random.normal(1000, 200, 100) # lowercase
        }, index=dates)
        
        # Create signals data for testing
        self.signals = pd.DataFrame({
            'entry': np.random.choice([True, False], size=100),
            'exit': np.random.choice([True, False], size=100)
        }, index=dates)
        
        # Create a valid strategy config
        self.valid_params = MovingAverageCrossoverParams(
            fast_ma=5,
            slow_ma=20,
            stop_loss=0.05,
            take_profit=0.1,
            trailing_stop=0.02,
            position_size=1.0
        )
        
        self.valid_strategy = StrategyConfig(
            ticker="AAPL",
            start_date=date(2020, 1, 1),
            end_date=date(2021, 1, 1),
            strategy_type="MovingAverageCrossover",
            strategy_params=self.valid_params.model_dump()
        )
    
    def test_none_values(self):
        """Test handling of None values in parameters."""
        # Create params with None values
        params = MovingAverageCrossoverParams(
            fast_ma=5,
            slow_ma=20,
            stop_loss=0.05,
            take_profit=None,  # None value
            trailing_stop=0.02,
            position_size=1.0
        )
        
        strategy = StrategyConfig(
            ticker="AAPL",
            start_date=date(2020, 1, 1),
            end_date=date(2021, 1, 1),
            strategy_type="MovingAverageCrossover",
            strategy_params=params.model_dump()
        )
        
        # Prepare data and signals for backtesting
        prices_series = self.test_data['close']
        signals_df = pd.DataFrame({
            'entry': np.random.choice([True, False], size=len(self.test_data)),
            'exit': np.random.choice([True, False], size=len(self.test_data))
        }, index=self.test_data.index)
        
        # Should not raise an exception
        result = run_backtest(prices_data=prices_series, signals_data=signals_df)
        self.assertIsNotNone(result)
        
    def test_string_values(self):
        """Test handling of string values in parameters."""
        # Create params with string values that should convert to float
        params = MovingAverageCrossoverParams(
            fast_ma=5,
            slow_ma=20,
            stop_loss="0.05",  # String value
            take_profit=0.1,
            trailing_stop="0.02",  # String value
            position_size=1.0
        )
        
        strategy = StrategyConfig(
            ticker="AAPL",
            start_date=date(2020, 1, 1),
            end_date=date(2021, 1, 1),
            strategy_type="MovingAverageCrossover",
            strategy_params=params.model_dump()
        )
        
        # Prepare data and signals for backtesting
        prices_series = self.test_data['close']
        signals_df = pd.DataFrame({
            'entry': np.random.choice([True, False], size=len(self.test_data)),
            'exit': np.random.choice([True, False], size=len(self.test_data))
        }, index=self.test_data.index)
        result = run_backtest(prices_data=prices_series, signals_data=signals_df)
        self.assertIsNotNone(result)
        
    @patch('src.meqsap.backtest.vbt.Portfolio')
    def test_mock_stats_with_non_numeric(self, mock_portfolio):
        """Test handling of non-numeric values in stats dictionary."""
        # Mock the Portfolio.from_signals call and its subsequent .stats() and .trades calls
        mock_portfolio_instance = MagicMock()

        # Scenario 1: Critical stat is a non-convertible string
        mock_stats_invalid_str = pd.Series({
            'Total Return [%]': "SHOULD_BE_FLOAT", # Invalid string
            'Annualized Return [%]': 10.0,
            'Sharpe Ratio': 1.0,
            'Max Drawdown [%]': -5.0,
            'End Value': 11000.0,
            'Total Trades': 1
        })
        mock_portfolio_instance.stats.return_value = mock_stats_invalid_str
        mock_portfolio_instance.trades.records_readable = pd.DataFrame({ # Dummy trade
            'Entry Time': [pd.Timestamp('2022-01-05')], 'Exit Time': [pd.Timestamp('2022-01-10')],
            'Entry Price': [100.0], 'Exit Price': [105.0], 'PnL': [50.0], 'Return [%]': [5.0]
        })
        mock_portfolio_instance.returns.return_value = pd.Series([0.01, 0.02]) # Dummy returns
        mock_portfolio_instance.value.return_value = pd.Series({pd.Timestamp('2022-01-01'): 10000.0})
        mock_portfolio_instance.wrapper.columns = pd.Index(['asset'])

        with patch('src.meqsap.backtest.vbt.Portfolio.from_signals', return_value=mock_portfolio_instance):
            with self.assertRaisesRegex(BacktestError, "Could not convert 'SHOULD_BE_FLOAT'.*for metric 'Total Return'"):
                run_backtest(prices_data=self.test_data['close'], signals_data=self.signals)

        # Scenario 2: Critical stat from trades is non-convertible string
        mock_stats_valid = pd.Series({
            'Total Return [%]': 10.0, 'Annualized Return [%]': 10.0, 'Sharpe Ratio': 1.0,
            'Max Drawdown [%]': -5.0, 'End Value': 11000.0, 'Total Trades': 1
        })
        mock_portfolio_instance.stats.return_value = mock_stats_valid
        mock_portfolio_instance.trades.records_readable = pd.DataFrame({
            'Entry Time': [pd.Timestamp('2022-01-05')], 'Exit Time': [pd.Timestamp('2022-01-10')],
            'Entry Price': [100.0], 'Exit Price': [105.0], 'PnL': ["NOT_A_PNL"], 'Return [%]': [5.0]
        })

        with patch('src.meqsap.backtest.vbt.Portfolio.from_signals', return_value=mock_portfolio_instance):
            # The test should now pass without raising an error for the PnL column,
            # as it will be coerced to NaN and then defaulted by safe_float.
            result = run_backtest(prices_data=self.test_data['close'], signals_data=self.signals)
            self.assertIsNotNone(result)
            self.assertEqual(result.trade_details[0]['pnl'], 0.0) # Assert it defaulted to 0.0

class TestFloatHandling(unittest.TestCase):
    """Test safe float handling in backtesting operations."""
    
    def test_safe_float_with_valid_numbers(self):
        """Test safe_float with valid numeric inputs."""
        self.assertEqual(safe_float(1.5), 1.5)
        self.assertEqual(safe_float(10), 10.0)
        self.assertEqual(safe_float("3.14"), 3.14)
        self.assertEqual(safe_float(0), 0.0)
        
    def test_safe_float_with_invalid_inputs(self):
        """Test safe_float with invalid inputs."""
        self.assertEqual(safe_float(None), 0.0)
        self.assertEqual(safe_float("invalid"), 0.0)
        self.assertEqual(safe_float([1, 2, 3]), 0.0)
        self.assertEqual(safe_float({"key": "value"}), 0.0)
        
    def test_safe_float_with_custom_default(self):
        """Test safe_float with custom default values."""
        self.assertEqual(safe_float(None, default=100.0), 100.0)
        self.assertEqual(safe_float("invalid", default=-1.0), -1.0)
        
    def test_safe_float_with_nan_and_inf(self):
        """Test safe_float with NaN and infinite values."""
        self.assertEqual(safe_float(np.nan, default=0.0), 0.0)
        self.assertEqual(safe_float(np.inf, default=0.0), 0.0) # inf should also default
        self.assertEqual(safe_float(-np.inf, default=0.0), 0.0) # -inf should also default

    def test_safe_float_raise_on_type_error(self):
        """Test safe_float with raise_on_type_error=True."""
        with self.assertRaisesRegex(BacktestError, "Could not convert 'invalid_str'.*Invalid value for float conversion"):
            safe_float("invalid_str", metric_name="CriticalMetric1", raise_on_type_error=True)
        
        with self.assertRaisesRegex(BacktestError, "Could not convert '\\['list'\\]'.*Incorrect type for float conversion"):
            safe_float(['list'], metric_name="CriticalMetric2", raise_on_type_error=True)

        # NaN/inf/None should still default even if raise_on_type_error is True
        self.assertEqual(safe_float(np.nan, metric_name="NanTest", raise_on_type_error=True), 0.0)
        self.assertEqual(safe_float(None, metric_name="NoneTest", raise_on_type_error=True), 0.0)

if __name__ == '__main__':
    unittest.main()
