# Story: Data Acquisition and Caching Module Implementation

## Description
Implement the data module for MEQSAP. This module will acquire historical OHLCV market data for a specified ticker using yfinance, implement a file-based caching system, and perform data integrity checks. It must be fully independent and follow the modular monolith pattern.

## Acceptance Criteria
1. Data module can download historical OHLCV data for a ticker and date range using yfinance
2. Data is cached locally (e.g., Parquet or Feather format) to avoid redundant downloads
3. On cache miss, data is fetched from yfinance and stored in the cache
4. On cache hit, data is loaded from the cache without calling yfinance
5. Data integrity checks are performed: no NaN values, correct date range, and data freshness
6. Clear error handling for bad tickers, missing data, or API issues
7. Unit tests cover all core and edge cases
8. Documentation is added for module usage and configuration

## Implementation Details

### Data Module
- Create `src/meqsap/data.py` as a new module
- Implement a function to fetch data for a given ticker, start_date, and end_date
- Use yfinance to download data if not cached
- Store and load cached data using Parquet or Feather (choose one, document rationale)
- Implement data integrity checks:
  - Ensure no missing (NaN) values in the returned DataFrame
  - Ensure the data covers the requested date range
  - Optionally, check that the most recent data is not stale (e.g., within 2 days of today for non-weekends)
- Raise clear, user-friendly errors for all failure modes
- Ensure the module is independent and does not import from other MEQSAP modules except config for the validated config object

### Caching
- Use a dedicated cache directory (e.g., `data/cache/` under project root)
- Cache key should be based on ticker and date range
- On repeated requests for the same ticker and range, load from cache
- Provide a function to clear the cache (for testing and user diagnostics)

### Unit Testing
- Add tests in `tests/test_data.py`
- Test cache hit, cache miss, data integrity failures, and error handling

### Documentation
- Add docstrings to all public functions and classes
- Update README.md with a section on data acquisition and caching

## Tasks
- [ ] Create `src/meqsap/data.py` and implement data acquisition logic
- [ ] Implement file-based caching (Parquet or Feather)
- [ ] Implement data integrity checks
- [ ] Add error handling for all failure modes
- [ ] Add unit tests in `tests/test_data.py`
- [ ] Add/Update documentation (docstrings, README)

## Definition of Done
1. Data module is implemented and fully tested
2. Caching works as specified
3. Data integrity checks are enforced
4. All tests pass
5. Documentation is complete
6. Code follows project standards and is independent
