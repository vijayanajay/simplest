import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from pathlib import Path
import warnings

# Suppress pandas_ta related warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API", category=UserWarning)

from meqsap.data import fetch_market_data, clear_cache, DataError

# Mock data for testing
def create_mock_data(start_date, end_date):
    dates = pd.date_range(start_date, end_date - timedelta(days=1))
    return pd.DataFrame({
        'Open': np.random.rand(len(dates)),
        'High': np.random.rand(len(dates)),
        'Low': np.random.rand(len(dates)),
        'Close': np.random.rand(len(dates)),
        'Volume': np.random.randint(1000, 10000, len(dates))
    }, index=dates)

@pytest.fixture
def mock_yfinance_download():
    with patch('meqsap.data.yf.download') as mock_download:
        yield mock_download

@pytest.fixture
def mock_cache():
    with patch('meqsap.data.load_from_cache') as mock_load, \
         patch('meqsap.data.save_to_cache') as mock_save:
        yield mock_load, mock_save

@pytest.fixture(autouse=True)
def cleanup_cache():
    yield
    # Clear cache after each test
    clear_cache()

def test_cache_miss(mock_yfinance_download, mock_cache):
    mock_load, mock_save = mock_cache
    mock_load.side_effect = FileNotFoundError
    mock_data = create_mock_data(date(2023, 1, 1), date(2023, 1, 10))
    mock_yfinance_download.return_value = mock_data
    
    # Call function
    result = fetch_market_data('AAPL', date(2023, 1, 1), date(2023, 1, 10))
    
    # Verify
    mock_load.assert_called_once()
    mock_yfinance_download.assert_called_once()
    mock_save.assert_called_once()
    pd.testing.assert_frame_equal(result, mock_data)

def test_cache_hit(mock_yfinance_download, mock_cache):
    mock_load, mock_save = mock_cache
    mock_data = create_mock_data(date(2023, 1, 1), date(2023, 1, 10))
    mock_load.return_value = mock_data
    
    # Call function
    result = fetch_market_data('AAPL', date(2023, 1, 1), date(2023, 1, 10))
    
    # Verify
    mock_load.assert_called_once()
    mock_yfinance_download.assert_not_called()
    mock_save.assert_not_called()
    pd.testing.assert_frame_equal(result, mock_data)

def test_nan_values_validation(mock_yfinance_download, mock_cache):
    mock_load, _ = mock_cache
    mock_load.side_effect = FileNotFoundError
    mock_data = create_mock_data(date(2023, 1, 1), date(2023, 1, 10))
    mock_data.iloc[2, 3] = np.nan  # Introduce NaN value
    
    mock_yfinance_download.return_value = mock_data
    
    # Test for NaN error
    with pytest.raises(DataError, match="Missing data points"):
        fetch_market_data('AAPL', date(2023, 1, 1), date(2023, 1, 10))

def test_incomplete_date_range(mock_yfinance_download, mock_cache):
    mock_load, _ = mock_cache
    mock_load.side_effect = FileNotFoundError
    mock_data = create_mock_data(date(2023, 1, 2), date(2023, 1, 9))  # Missing first and last day
    
    mock_yfinance_download.return_value = mock_data
    
    # Test for date range error
    with pytest.raises(DataError, match="Data does not cover full range"):
        fetch_market_data('AAPL', date(2023, 1, 1), date(2023, 1, 10))

def test_stale_data_validation(mock_yfinance_download, mock_cache):
    mock_load, _ = mock_cache
    mock_load.side_effect = FileNotFoundError
    
    # Create data that ends 3 days ago (stale) on a non-Friday
    stale_date = date.today() - timedelta(days=3)
    # Ensure it's not a Friday (weekday 4)
    if stale_date.weekday() == 4:  # Friday
        stale_date -= timedelta(days=1)
    
    # Create data that ends at stale_date
    start_date = stale_date - timedelta(days=5)
    mock_data = create_mock_data(start_date, stale_date)
      # Mock today's date to be 3 days after stale_date
    with patch('meqsap.data.date') as mock_date:
        mock_date.today.return_value = stale_date + timedelta(days=3)
        mock_yfinance_download.return_value = mock_data
        
        # Use a recent end_date (today) to trigger freshness check
        end_date = mock_date.today.return_value
        
        # Test for stale data error
        with pytest.raises(DataError, match="Data does not cover full range"):
            fetch_market_data('AAPL', start_date, end_date)

def test_invalid_ticker(mock_yfinance_download, mock_cache):
    mock_load, _ = mock_cache
    mock_load.side_effect = FileNotFoundError
    mock_yfinance_download.return_value = pd.DataFrame()  # Empty data
    
    # Test for invalid ticker
    with pytest.raises(DataError, match="No data available"):
        fetch_market_data('INVALID_TICKER', date(2023, 1, 1), date(2023, 1, 10))

def test_clear_cache():
    from meqsap.data import CACHE_DIR
    
    # Create dummy cache file
    test_file = CACHE_DIR / 'test_cache.parquet'
    test_file.touch()
    
    # Clear cache
    clear_cache()
    
    # Verify the test file was removed
    assert not test_file.exists()