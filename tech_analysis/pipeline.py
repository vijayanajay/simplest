import yfinance as yf
import pandas as pd
from pathlib import Path
from datetime import datetime

def fetch_data(ticker: str, period: str = "2y") -> pd.DataFrame:
    """
    Fetches historical stock data using yfinance.

    Args:
        ticker: The stock ticker symbol (e.g., "RELIANCE").
                Appends ".NS" for NSE stocks automatically.
        period: The period for which to fetch data (e.g., "1y", "2y", "max").

    Returns:
        A pandas DataFrame containing OHLCV data with lowercase column names.
    """
    data = yf.download(f"{ticker}.NS", period=period)
    data.columns = data.columns.str.lower() # Ensure lowercase columns
    return data

def cache_data(data: pd.DataFrame, ticker: str) -> str:
    """
    Caches the DataFrame to a Parquet file in the 'data/' directory.

    Args:
        data: The pandas DataFrame to cache.
        ticker: The stock ticker symbol, used for naming the file.

    Returns:
        The path to the saved Parquet file.
    """
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True) # Ensure data directory exists
    timestamp = datetime.now().strftime("%Y%m%d")
    file_path = data_dir / f"{ticker}_{timestamp}.parquet"
    data.to_parquet(file_path)
    print(f"Data for {ticker} cached to {file_path}")
    return str(file_path)

# Placeholder for main execution flow (Task 5.1)
if __name__ == "__main__":
    pass
