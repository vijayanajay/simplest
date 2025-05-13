# Data Models for Adaptive Automated Trading Strategy Discovery System

## Overview

This document defines the key data structures and models used in the system to represent financial data, strategies, and performance metrics.

## Core Data Models

- **OHLCV Data Model**: A Pandas DataFrame with columns for Open, High, Low, Close, and Volume, indexed by date.
  - Example:
    ```python
    # ... existing code ...
    df = pd.DataFrame({
        'Open': [float],
        'High': [float],
        'Low': [float],
        'Close': [float],
        'Volume': [int]
    }, index=pd.DatetimeIndex([]))
    # ... existing code ...
    ```

- **Technical Indicators Model**: A DataFrame extension adding columns for indicators like RSI, MACD, etc.
  - Example:
    ```python
    # ... existing code ...
    indicators_df = df.copy()
    indicators_df['RSI'] = calculate_rsi(df['Close'])
    indicators_df['MACD'] = calculate_macd(df['Close'])
    # ... existing code ...
    ```

- **Strategy Model**: A class or dictionary representing a trading strategy, including rules, parameters, and fitness scores.
  - Example:
    ```python
    # ... existing code ...
    class TradingStrategy:
        def __init__(self, buy_rule, sell_rule, parameters):
            self.buy_rule = buy_rule  # e.g., lambda df: df['RSI'] < 30
            self.sell_rule = sell_rule  # e.g., lambda df: df['RSI'] > 70
            self.parameters = parameters  # dict of GA-evolved params
    # ... existing code ...
    ```

- **Backtest Results Model**: A structure holding metrics like Sharpe Ratio, Total Return, and Drawdown.
  - Example:
    ```python
    # ... existing code ...
    results = {
        'sharpe_ratio': float,
        'total_return': float,
        'max_drawdown': float,
        'trades': list  # List of trade dicts
    }
    # ... existing code ...
    ```

## Rationale

- Models are designed for ease of integration with Pandas and NumPy to leverage vectorized operations.
- Ensures data consistency and facilitates GA optimization.

## Change Log

| Change        | Date       | Version | Description                  | Author         |
| ------------- | ---------- | ------- | ---------------------------- | -------------- |
| Initial draft | 2025-05-15 | 0.1     | Initial data models outline  | AI Architect   |