import vectorbt as vbt
import pandas as pd
import numpy as np

# Create sample data
dates = pd.date_range('2023-01-01', periods=10, freq='D')
close = pd.Series([100, 101, 102, 101, 103, 104, 102, 105, 106, 107], index=dates)
entries = pd.Series([True, False, False, False, True, False, False, False, False, False], index=dates)
exits = pd.Series([False, False, False, True, False, False, False, False, True, False], index=dates)

# Create portfolio
pf = vbt.Portfolio.from_signals(close, entries, exits, init_cash=10000, fees=0.001)

print('=== STATS KEYS ===')
stats = pf.stats()
print('Stats type:', type(stats))
print('Stats keys:', list(stats.keys()) if hasattr(stats, 'keys') else 'No keys')
if hasattr(stats, 'keys'):
    for key in stats.keys():
        print(f"  {key}: {stats[key]}")

print('\n=== TRADE RECORDS COLUMNS ===')
trades = pf.trades.records_readable
print('Trades columns:', trades.columns.tolist())
print('Trades dtypes:')
print(trades.dtypes)

print('\n=== SAMPLE TRADE RECORD ===')
if len(trades) > 0:
    print("First trade:")
    print(trades.iloc[0])
    print("\nAll trade data:")
    print(trades.head())
