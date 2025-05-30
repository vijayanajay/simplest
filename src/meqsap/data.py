import os
import pandas as pd
import yfinance as yf
from datetime import date, datetime, timedelta
from pathlib import Path

class DataError(Exception):
    """Custom exception for data-related errors."""

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

def _validate_data(df: pd.DataFrame, start_date: date, end_date: date) -> None:
    """Perform data integrity checks."""
    # Check for NaN values
    if df.isnull().values.any():
        raise DataError("Missing data points (NaN values) detected")
    
    # Check date range coverage - yfinance returns data from start_date to end_date-1
    dates = pd.to_datetime(df.index)
    if dates.min() > pd.Timestamp(start_date) or dates.max() < pd.Timestamp(end_date - timedelta(days=1)):
        raise DataError(f"Data does not cover full range: {start_date} to {end_date}")
    
    # Check data freshness: last available date should be within 2 days of today
    last_data_date = dates.max().date()
    today = date.today()
    if end_date >= today - timedelta(days=2):  # Only check for recent data
        # Account for weekends - allow up to 4 days for Fri-Mon gap
        max_days = 4 if last_data_date.weekday() == 4 else 2  # 4=Friday
        if (today - last_data_date).days > max_days:
            raise DataError(f"Stale data: Last available date is {last_data_date}")

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
        # Download data from yfinance
        data = yf.download(
            ticker, 
            start=start_date, 
            end=end_date + timedelta(days=1),  # Include end date
            progress=False
        )
        
        if data.empty:
            raise DataError(f"No data available for {ticker} in {start_date} to {end_date}")
        
        # Perform integrity checks
        _validate_data(data, start_date, end_date)
        
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