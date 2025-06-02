import yfinance as yf
import pandas as pd

def check_yfinance_for_indian_ticker(ticker_symbol: str = "RELIANCE.NS"):
    """
    Attempts to download historical data for a given Indian ticker symbol
    using yfinance and prints the outcome.

    Args:
        ticker_symbol (str): The ticker symbol to test (e.g., "RELIANCE.NS").
    """
    print(f"Attempting to download data for {ticker_symbol} using yfinance...")
    
    try:
        # Create a Ticker object
        ticker = yf.Ticker(ticker_symbol)
        
        # Get historical market data for the last 1 month
        # You can adjust the period (e.g., "1d", "5d", "1mo", "3mo", "1y", "max")
        # or use start/end dates: history(start="YYYY-MM-DD", end="YYYY-MM-DD")
        hist_data = ticker.history(period="1mo")
        
        if hist_data.empty:
            print(f"No data returned for {ticker_symbol}. This could mean:")
            print("- The ticker symbol is incorrect or delisted for the given period.")
            print("- yfinance might be having trouble accessing data for this specific ticker or exchange right now.")
            print("- There might be no trading data for the requested period (e.g., very new listing, holidays).")
        else:
            print(f"\nSuccessfully downloaded data for {ticker_symbol}!")
            print("Here are the first 5 rows:")
            print(hist_data.head())
            print("\nAnd the last 5 rows:")
            print(hist_data.tail())
            print(f"\nData dimensions: {hist_data.shape[0]} rows, {hist_data.shape[1]} columns")
            print("\nyfinance seems to be working for this Indian ticker.")
            
    except Exception as e:
        print(f"\nAn error occurred while trying to fetch data for {ticker_symbol}:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")
        print("\nThis could be due to various reasons, including:")
        print("- Temporary yfinance/Yahoo Finance API issues.")
        print("- Network connectivity problems (even if general internet works, specific routes might be blocked).")
        print("- Incorrect ticker symbol format (though RELIANCE.NS is standard for NSE).")
        print("- yfinance library issues or outdated version (try `pip install --upgrade yfinance`).")

if __name__ == "__main__":
    # You can change the ticker symbol here if you want to test another one.
    # Make sure to use the '.NS' suffix for National Stock Exchange (NSE) listed stocks
    # or '.BO' for Bombay Stock Exchange (BSE) listed stocks.
    # For example: "INFY.NS", "TCS.NS", "SBIN.BO"
    test_ticker = "RELIANCE.NS" 
    check_yfinance_for_indian_ticker(test_ticker)

    # Example for a BSE ticker:
    # test_ticker_bse = "SBIN.BO"
    # check_yfinance_for_indian_ticker(test_ticker_bse)
