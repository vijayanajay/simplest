import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from pathlib import Path
import warnings

# Suppress pandas_ta related warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API", category=UserWarning)

from src.meqsap.data import fetch_market_data, clear_cache
from src.meqsap.exceptions import DataError

# Mock data for testing
def create_mock_data(start_date, end_date):
    """
    Create mock OHLCV data for testing.
    
    Args:
        start_date: First date to include (inclusive)
        end_date: Last date to include (INCLUSIVE)
    
    Returns:
        DataFrame with mock OHLCV data spanning the full date range
    """
    # Generate date range that includes both start_date and end_date
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Create mock OHLCV data
    np.random.seed(42)  # For reproducible test data
    data = {
        'Open': np.random.random(len(date_range)),
        'High': np.random.random(len(date_range)),
        'Low': np.random.random(len(date_range)),
        'Close': np.random.random(len(date_range)),
        'Volume': np.random.randint(1000, 10000, len(date_range))
    }
    
    df = pd.DataFrame(data, index=date_range)
    return df

@pytest.fixture
def mock_yfinance_download():
    with patch('src.meqsap.data.yf.download') as mock_download:  # Adjusted path for consistency
        yield mock_download

@pytest.fixture
def mock_cache():
    with patch('src.meqsap.data.load_from_cache') as mock_load, \
         patch('src.meqsap.data.save_to_cache') as mock_save:  # Adjusted path for consistency
        yield mock_load, mock_save

@pytest.fixture(autouse=True)
def cleanup_cache():
    yield
    # Clear cache after each test
    clear_cache()

def test_cache_miss(mock_yfinance_download, mock_cache):
    mock_load, mock_save = mock_cache
    mock_load.side_effect = FileNotFoundError
    # Create mock data that includes the full requested range (inclusive end_date)
    mock_data = create_mock_data(date(2023, 1, 1), date(2023, 1, 10))  # Include end_date
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

    # Test for date range error - update pattern to match actual error messages
    with pytest.raises(DataError, match="Data starts at .*, but .* was requested"):
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
    with patch('src.meqsap.data.date') as mock_date: # Adjusted path for consistency
        mock_date.today.return_value = stale_date + timedelta(days=3)
        mock_yfinance_download.return_value = mock_data

        # Use a recent end_date (today) to trigger freshness check
        end_date = mock_date.today.return_value

        # Test for stale data error - update pattern to match actual error messages
        with pytest.raises(DataError, match="Data ends at .*, but data through .* was requested"):
            fetch_market_data('AAPL', start_date, end_date)

def test_invalid_ticker(mock_yfinance_download, mock_cache):
    mock_load, _ = mock_cache
    mock_load.side_effect = FileNotFoundError
    mock_yfinance_download.return_value = pd.DataFrame()  # Empty data
    
    # Test for invalid ticker
    with pytest.raises(DataError, match="No data available"):
        fetch_market_data('INVALID_TICKER', date(2023, 1, 1), date(2023, 1, 10))

def test_clear_cache():
    from src.meqsap.data import CACHE_DIR # Adjusted import for consistency
    
    # Create dummy cache file
    test_file = CACHE_DIR / 'test_cache.parquet'
    test_file.touch()
    
    # Clear cache
    clear_cache()
    
    # Verify the test file was removed
    assert not test_file.exists()

def test_end_date_inclusive_behavior():
    """
    Test that end_date is truly inclusive - data for the specified end_date is present.
    
    This is a mandatory test case per the resolution of RI-20250310-001 (reopen #2)
    to prevent regression of date handling ambiguity.
    """
    # Use a short date range to make verification precise
    start_date = "2022-01-03"  # Monday to avoid weekend issues
    end_date = "2022-01-04"    # Tuesday - should be included in results
    
    # Mock yfinance to return data that includes both days
    with patch('src.meqsap.data.yf.download') as mock_download, \
         patch('src.meqsap.data.load_from_cache') as mock_load, \
         patch('src.meqsap.data.save_to_cache') as mock_save:
        
        # Cache miss
        mock_load.side_effect = FileNotFoundError
        
        # Create mock data that includes both start and end dates
        mock_data = create_mock_data(date(2022, 1, 3), date(2022, 1, 4))
        mock_download.return_value = mock_data
        
        # Call the correct function name
        data = fetch_market_data("AAPL", date(2022, 1, 3), date(2022, 1, 4))
        
        # Verify we have data for both days
        dates = pd.to_datetime(data.index).date
        expected_start = date(2022, 1, 3)
        expected_end = date(2022, 1, 4)
        
        # Check that we have the start date
        assert expected_start in dates, f"Missing data for start_date {expected_start}"
        
        # Check that we have the end date (this is the critical inclusive behavior)
        assert expected_end in dates, f"Missing data for end_date {expected_end} - end_date should be INCLUSIVE"
        
        # Verify the date range is exactly what we requested
        assert dates.min() == expected_start, f"Data starts at {dates.min()}, expected {expected_start}"
        assert dates.max() == expected_end, f"Data ends at {dates.max()}, expected {expected_end}"
        
        # Verify yfinance was called with adjusted end date (exclusive behavior)
        mock_download.assert_called_once_with(
            "AAPL",
            start=date(2022, 1, 3),
            end="2022-01-05",  # end_date + 1 day for yfinance exclusive behavior
            progress=False
        )