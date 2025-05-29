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

## Development

Make sure to install the development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```
