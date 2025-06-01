# MEQSAP - Market Equity Quantitative Strategy Analysis Platform

A platform for backtesting quantitative trading strategies using historical market data.

## Installation

```bash
pip install -e .
```

## Quick Start

1. Create a configuration YAML file:

```yaml
ticker: AAPL
start_date: 2020-01-01
end_date: 2022-01-01
strategy_type: MovingAverageCrossover
strategy_params:
  fast_ma: 10
  slow_ma: 30
```

2. Run the analysis:

```bash
meqsap analyze path/to/your/config.yaml
```

## Available Strategy Types

- **MovingAverageCrossover**: Implements a trading strategy based on the crossover of two moving averages
  - Required parameters:
    - `fast_ma`: The period for the fast moving average (must be > 0)
    - `slow_ma`: The period for the slow moving average (must be > fast_ma)

## Configuration

### Date Range Specification

**Important**: All date ranges in MEQSAP use **INCLUSIVE** end dates.

When you specify:
```yaml
start_date: 2022-01-01
end_date: 2022-12-31
```

The system will fetch and analyze data from January 1, 2022 **through and including** December 31, 2022.

This inclusive behavior is maintained automatically - the system handles the necessary adjustments when interfacing with data providers that use exclusive date ranges.

## Data Acquisition & Caching

The data module handles acquisition of historical OHLCV market data using yfinance, with local caching to avoid redundant downloads.

### Features
- Automatically caches downloaded data in Parquet format
- On subsequent requests for the same data, loads from cache
- Performs data integrity checks:
  - No NaN values in returned data
  - Full coverage of requested date range
  - Data freshness (within 2 days for recent data)
- Clear error handling for bad tickers, missing data, and API issues

### Usage

```python
from datetime import date
from src.meqsap.data import fetch_market_data

# Fetch data for Apple Inc. from 2023-01-01 to 2023-12-31
data = fetch_market_data("AAPL", date(2023,1,1), date(2023,12,31))

# Clear cache (for testing or diagnostics)
from src.meqsap.data import clear_cache
clear_cache()
```

## Development

Make sure to install the development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```
