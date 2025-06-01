import os
import pandas as pd
import yfinance as yf
from datetime import date, datetime, timedelta
from pathlib import Path
from .exceptions import DataError

# Cache directory setup
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = PROJECT_ROOT / 'data' / 'cache'
os.makedirs(CACHE_DIR, exist_ok=True)

def cache_key(ticker: str, start_date: date, end_date: date) -> str:
    """Generate cache key from ticker and date range."""
    return f"{ticker}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.parquet"

def load_from_cache(key: str) -> pd.DataFrame:
    """Load data from cache if exists."""
    filepath = CACHE_DIR / key
    if filepath.exists():
        return pd.read_parquet(filepath)
    raise FileNotFoundError(f"Cache file not found: {filepath}")

def save_to_cache(df: pd.DataFrame, key: str) -> None:
    """Save DataFrame to cache in Parquet format."""
    filepath = CACHE_DIR / key
    df.to_parquet(filepath)

def _validate_data(data: pd.DataFrame, symbol: str, start_date: str, end_date: str) -> None:
    """
    Validate that the fetched data meets basic requirements.
    
    Args:
        data: The DataFrame containing stock data
        symbol: Stock symbol that was fetched
        start_date: Start date string (YYYY-MM-DD format)
        end_date: End date string (YYYY-MM-DD format, INCLUSIVE)
    
    Raises:
        DataError: If data validation fails
    
    Note:
        end_date is user-specified as INCLUSIVE (per ADR-002). The validation
        logic accounts for yfinance's exclusive behavior by checking that
        the maximum date in fetched data is >= (end_date - 1 day), ensuring
        data for the user-specified end_date is actually present.
    """
    # Check for NaN values
    if data.isnull().values.any():
        raise DataError("Missing data points (NaN values) detected")
    
    # Ensure we have data for the full requested range
    # Note: yfinance.download() uses exclusive end dates, so we fetch with end_date + 1 day
    # but validate that we actually got data for the user-specified (inclusive) end_date
    dates = pd.to_datetime(data.index).date
    expected_start = pd.Timestamp(start_date).date()
    expected_end = pd.Timestamp(end_date).date()
    
    if dates.min() > expected_start:
        raise DataError(f"Data starts at {dates.min()}, but {expected_start} was requested")
    
    # Check that we have data for the user-specified end_date (inclusive)
    # Since yfinance is exclusive, the latest data should be for end_date itself
    if dates.max() < expected_end:
        raise DataError(f"Data ends at {dates.max()}, but data through {expected_end} was requested")

def fetch_market_data(ticker: str, start_date: date, end_date: date) -> pd.DataFrame:
    """
    Fetch OHLCV market data for given ticker and date range.
    
    Args:
        ticker: Stock ticker symbol
        start_date: Start of date range
        end_date: End of date range
        
    Returns:
        pandas.DataFrame with OHLCV data
        
    Raises:
        DataError: For any data integrity or download issues
    """
    try:
        # Try loading from cache
        key = cache_key(ticker, start_date, end_date)
        return load_from_cache(key)
    except FileNotFoundError:
        pass  # Cache miss, proceed to download
    
    try:
        # yfinance uses exclusive end dates, so add 1 day to get data for the user-specified end_date
        # This ensures end_date is INCLUSIVE from the user's perspective (per ADR-002)
        adjusted_end = (pd.Timestamp(end_date) + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Download data from yfinance
        data = yf.download(
            ticker, 
            start=start_date, 
            end=adjusted_end,  # yfinance exclusive end, so we add 1 day
            progress=False
        )
        
        if data.empty:
            raise DataError(f"No data available for {ticker} in {start_date} to {end_date}")
        
        # Perform integrity checks
        _validate_data(data, ticker, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        
        # Save to cache
        save_to_cache(data, key)
        return data
        
    except Exception as e:
        # Wrap any download errors in DataError
        raise DataError(f"Failed to download data for {ticker}: {str(e)}") from e

def clear_cache() -> None:
    """Clear all cached data files."""
    for file in CACHE_DIR.glob("*.parquet"):
        file.unlink()