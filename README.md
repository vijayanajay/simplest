# MEQSAP - Market Equity Quantitative Strategy Analysis Platform

A comprehensive platform for backtesting quantitative trading strategies using historical market data. MEQSAP provides robust data acquisition, signal generation, backtesting, and reporting capabilities with a user-friendly command-line interface.

## Installation

### Option 1: Development Installation (Recommended)
```bash
pip install -e .
```

### Option 2: Direct Usage (No Installation Required)
You can run MEQSAP directly from the project root using the provided `run.py` script:
```bash
python run.py --help
```

## Quick Start

### 1. Create a Configuration File

Create a YAML configuration file (e.g., `my_strategy.yaml`):

```yaml
# Basic Moving Average Crossover Strategy
ticker: AAPL                    # Stock ticker symbol
start_date: 2022-01-01          # Analysis start date (inclusive)
end_date: 2022-12-31            # Analysis end date (inclusive)
strategy_type: MovingAverageCrossover
strategy_params:
  fast_ma: 10                   # Fast moving average period (days)
  slow_ma: 30                   # Slow moving average period (days)
```

### 2. Run the Analysis

#### Using the run.py script (no installation required):
```bash
# Basic analysis
python run.py analyze my_strategy.yaml

# With detailed reporting
python run.py analyze my_strategy.yaml --report --verbose

# Validate configuration only
python run.py analyze my_strategy.yaml --validate-only
```

#### Using the installed CLI:
```bash
# Basic analysis
meqsap analyze my_strategy.yaml

# With detailed reporting  
meqsap analyze my_strategy.yaml --report --verbose
```

### 3. View Results

MEQSAP will output:
- **Summary Statistics**: Key performance metrics (returns, Sharpe ratio, max drawdown)
- **Trade Analysis**: Entry/exit points and individual trade performance
- **Risk Metrics**: Volatility, drawdown analysis, and risk-adjusted returns
- **Optional PDF Report**: Comprehensive analysis with charts (when using `--report`)

### 4. Parameter Optimization (New!)

For automated parameter optimization, create a configuration with parameter ranges and run:

```bash
# Run parameter optimization with real-time progress reporting
python run.py optimize single my_strategy_with_ranges.yaml --report

# Run optimization with custom trial count
python run.py optimize single config.yaml --trials 100 --verbose
```

MEQSAP will automatically find the best parameter combinations using Grid Search or Random Search algorithms.

## Available Strategy Types

### MovingAverageCrossover
Implements a trading strategy based on the crossover of two moving averages.

**Required Parameters:**
- `fast_ma`: Fast moving average period in days (must be > 0)
- `slow_ma`: Slow moving average period in days (must be > fast_ma)

**Parameter Definition Options:**
- **Fixed Values**: Traditional approach with single values
- **Parameter Ranges**: For optimization with start, stop, and step values
- **Parameter Choices**: Discrete options to test during optimization
- **Explicit Values**: Named value definitions for clarity

**Trading Logic:**
- **Entry Signal**: When fast MA crosses above slow MA (bullish crossover)
- **Exit Signal**: When fast MA crosses below slow MA (bearish crossover)

**Example Configurations:**

*Fixed Parameters (Traditional):*
```yaml
strategy_type: MovingAverageCrossover
strategy_params:
  fast_ma: 10      # 10-day moving average
  slow_ma: 30      # 30-day moving average
```

*Parameter Ranges (For Optimization):*
```yaml
strategy_type: MovingAverageCrossover
strategy_params:
  fast_ma:
    type: "range"
    start: 5
    stop: 15
    step: 1
  slow_ma:
    type: "choices" 
    values: [20, 30, 50]
```

*Mixed Parameters:*
```yaml
strategy_type: MovingAverageCrossover
strategy_params:
  fast_ma: 10      # Fixed value
  slow_ma:         # Range for optimization
    type: "range"
    start: 20
    stop: 50
    step: 5
```

## Enhanced Parameter Definition Framework

MEQSAP now supports flexible parameter definitions that enable automated optimization while maintaining backward compatibility with fixed parameter configurations.

### Parameter Types

#### Fixed Values (Traditional)
Use simple numeric values for traditional single-run analysis:
```yaml
strategy_params:
  fast_ma: 10
  slow_ma: 30
```

#### Parameter Ranges
Define ranges for systematic optimization:
```yaml
strategy_params:
  fast_ma:
    type: "range"
    start: 5      # Minimum value
    stop: 15      # Maximum value (exclusive)
    step: 1       # Step size
```

#### Parameter Choices
Specify discrete options to test:
```yaml
strategy_params:
  slow_ma:
    type: "choices"
    values: [20, 30, 50, 100]
```

#### Explicit Values
Named value definitions for clarity:
```yaml
strategy_params:
  period:
    type: "value"
    value: 14
```

### Mixed Parameter Definitions
You can combine different parameter types in the same configuration:
```yaml
strategy_params:
  fast_ma: 10              # Fixed value
  slow_ma:                 # Range for optimization
    type: "range"
    start: 20
    stop: 100
    step: 5
  signal_threshold:        # Discrete choices
    type: "choices"
    values: [0.01, 0.02, 0.05]
```

### Backward Compatibility
All existing YAML configurations with fixed parameters continue to work without modification. The enhanced framework automatically detects parameter types and handles them appropriately.

## Parameter Optimization Engine

MEQSAP includes a powerful parameter optimization engine that systematically searches through parameter combinations to find optimal strategy configurations. This engine integrates seamlessly with the enhanced parameter definition framework to provide comprehensive optimization capabilities.

### Key Features

- **Multiple Search Algorithms**: Grid Search, Random Search, and future support for advanced optimization methods
- **Flexible Parameter Spaces**: Supports ranges, discrete choices, and mixed parameter types
- **Real-time Progress Tracking**: Live progress bars with ETA, completion rate, and performance metrics
- **Graceful Interruption**: Ctrl+C handling that preserves partial results and shows best findings
- **Memory Efficient**: Streams results and maintains configurable result caching
- **Comprehensive Reporting**: Detailed optimization reports with parameter sensitivity analysis

### Optimization Algorithms

**Grid Search (`GridSearch`)**
- Exhaustively searches all parameter combinations
- Guarantees finding the global optimum within the defined space
- Best for: Small parameter spaces, thorough exploration needs
- Performance: Systematic but can be time-intensive for large spaces

**Random Search (`RandomSearch`)**
- Randomly samples parameter combinations for a specified number of trials
- Often finds good solutions faster than grid search for high-dimensional spaces
- Best for: Large parameter spaces, time-constrained optimization
- Performance: Efficient exploration with configurable trial limits

### Objective Functions

The optimization engine supports multiple objective functions for strategy evaluation:

 - **`SharpeRatio`**: Sharpe ratio (risk-adjusted returns) – *default*
 - **`TotalReturn`**: Total portfolio return percentage
 - **`MaxDrawdown`**: Maximum drawdown (minimised)
 - **`ProfitFactor`**: Ratio of gross profit to gross loss
 - **`WinRate`**: Percentage of profitable trades
- **`win_rate`**: Percentage of profitable trades

### Configuration

Enable optimization by adding an `optimization_config` section to your YAML:

```yaml
optimization_config:
  active: true                     # Must be true to enable optimisation
  algorithm: "GridSearch"          # or "RandomSearch"
  objective_function: "SharpeRatio"  # Metric to optimise
  max_trials: 1000               # For RandomSearch only
  cache_results: true            # Cache intermediate results
  parallel_jobs: 1               # Future: parallel execution
```

### Optimization Workflow

1. **Parameter Discovery**: Engine analyzes configuration for optimizable parameters
2. **Space Generation**: Creates parameter combinations based on algorithm choice
3. **Parallel Execution**: Runs backtests with progress tracking and interruption handling
4. **Result Analysis**: Identifies best parameters and generates performance rankings
5. **Report Generation**: Creates comprehensive optimization reports (if `--report` enabled)

### Progress Monitoring

The optimization engine provides real-time feedback:

```
Optimizing AAPL MovingAverageCrossover...
Progress: 45% |████████████████████▌                    | 450/1000 trials
Best Sharpe: 1.847 | Current: 1.234 | ETA: 00:02:15
Top Parameters: fast_ma=8, slow_ma=35, signal_threshold=0.02
```

### Interruption Handling

Press `Ctrl+C` during optimization to gracefully stop and see results so far:

```
Optimization interrupted by user.
Completed 342 out of 1000 trials (34.2%).

Best result found:
├─ Sharpe Ratio: 1.847
├─ Total Return: 24.5%
├─ Max Drawdown: -8.2%
└─ Parameters: fast_ma=8, slow_ma=35, signal_threshold=0.02
```

### Memory and Performance

- **Efficient Streaming**: Results processed incrementally to minimize memory usage
- **Result Caching**: Optional caching prevents re-computation of identical parameter sets
- **Progress Persistence**: Partial results preserved on interruption
- **Configurable Batch Processing**: Future support for batch optimization workflows

## CLI Commands

### `analyze` - Run Strategy Analysis

**Syntax:**
```bash
python run.py analyze CONFIG_FILE [OPTIONS]
# or
meqsap analyze CONFIG_FILE [OPTIONS]
```

**Arguments:**
- `CONFIG_FILE`: Path to YAML configuration file (required)

**Options:**
- `--report`: Generate a comprehensive PDF report after analysis
- `--validate-only`: Only validate the configuration, don't run backtest
- `--output-dir DIR`: Directory for output reports (default: `./reports`)
- `--verbose, -v`: Enable detailed logging and diagnostics
- `--quiet, -q`: Suppress non-essential output (minimal mode)
- `--no-color`: Disable colored terminal output
- `--help, -h`: Show help message

**Examples:**
```bash
# Basic analysis
python run.py analyze config.yaml

# Generate PDF report with verbose output
python run.py analyze config.yaml --report --verbose

# Validate configuration only
python run.py analyze config.yaml --validate-only

# Custom output directory
python run.py analyze config.yaml --report --output-dir ./my_reports

# Quiet mode for scripting
python run.py analyze config.yaml --quiet
```

### `optimize single` - Parameter Optimization (New!)

**Important**: The `single` subcommand is required. Use `python run.py optimize single` (not just `python run.py optimize`).

**Syntax:**
```bash
python run.py optimize single CONFIG_FILE [OPTIONS]
# or
meqsap optimize single CONFIG_FILE [OPTIONS]
```

**Arguments:**
- `CONFIG_FILE`: Path to YAML configuration file with parameter ranges (required)

**Options:**
- `--report`: Generate PDF report for the best strategy found
- `--output-dir DIR`: Directory for output reports and results
- `--trials N`: Number of optimization trials (RandomSearch only)
- `--no-progress`: Disable real-time progress bar
- `--verbose, -v`: Enable detailed optimization logging
- `--help, -h`: Show help message

**Examples:**
```bash
# Basic optimization with progress reporting
python run.py optimize single config_with_ranges.yaml

# Optimization with PDF report for best strategy
python run.py optimize single config.yaml --report --verbose

# Random search with custom trial count
python run.py optimize single config.yaml --trials 200

# Optimization without progress bar (for scripting)
python run.py optimize single config.yaml --no-progress --quiet
```

**Progress Reporting Features:**
- Real-time progress bars with trial completion status
- Best score tracking during optimization
- Error categorization and failure reporting
- Graceful interruption with Ctrl+C
- Comprehensive optimization summary

**Supported Algorithms:**
- **Grid Search**: Systematic exploration of all parameter combinations
- **Random Search**: Random sampling within parameter ranges

### `version` - Show Version Information

**Syntax:**
```bash
python run.py version
# or  
meqsap version
```

Shows the current version of MEQSAP.

### Global Help

**Syntax:**
```bash
python run.py --help
# or
meqsap --help
```

Shows available commands and global options.

## Configuration File Format

MEQSAP uses YAML configuration files to define strategy parameters and analysis settings.

### Required Fields

```yaml
ticker: SYMBOL                  # Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)
start_date: YYYY-MM-DD         # Analysis start date (inclusive)
end_date: YYYY-MM-DD           # Analysis end date (inclusive)  
strategy_type: STRATEGY_NAME   # Strategy to backtest
strategy_params:               # Strategy-specific parameters
  param1: value1
  param2: value2

# Optional: For parameter optimization
optimization_config:           # Optimization settings (optional)
  active: true                 # Enable optimization mode
  algorithm: GridSearch        # Algorithm to use
  objective_function: SharpeRatio   # Metric to optimize
```

### Field Details

**`ticker`**: Stock symbol to analyze
- Format: Alphanumeric with dots and hyphens allowed
- Examples: `AAPL`, `BRK.B`, `BTC-USD`

**`start_date` / `end_date`**: Date range for analysis
- Format: `YYYY-MM-DD` (ISO format)
- **Important**: Both dates are INCLUSIVE
- Example: `start_date: 2022-01-01` and `end_date: 2022-12-31` includes both January 1st and December 31st
- Minimum range: Must provide enough data for the strategy (e.g., 30+ days for a 30-day moving average)

**`strategy_type`**: Currently supported strategies
- `MovingAverageCrossover`: Moving average crossover strategy

**`strategy_params`**: Strategy-specific configuration
- See "Available Strategy Types" section for required parameters per strategy
- Supports both fixed values and parameter ranges for optimization

**`optimization_config`** (Optional): Parameter optimization settings
- `active`: Set to `true` to enable optimization mode
- `algorithm`: `GridSearch` or `RandomSearch`
- `objective_function`: Metric to optimize (`sharpe`, `returns`, etc.)
- `algorithm_params`: Algorithm-specific settings (e.g., `n_trials` for RandomSearch)

### Example Configurations

#### Short-term Trading (5-day vs 15-day MA)
```yaml
ticker: TSLA
start_date: 2023-01-01
end_date: 2023-12-31
strategy_type: MovingAverageCrossover
strategy_params:
  fast_ma: 5
  slow_ma: 15
```

#### Long-term Investing (50-day vs 200-day MA)
```yaml
ticker: SPY
start_date: 2020-01-01
end_date: 2023-12-31
strategy_type: MovingAverageCrossover
strategy_params:
  fast_ma: 50
  slow_ma: 200
```

#### Parameter Optimization Configuration
```yaml
ticker: AAPL
start_date: 2023-01-01
end_date: 2024-01-01
strategy_type: MovingAverageCrossover
strategy_params:
  fast_ma:
    type: "range"
    start: 5
    stop: 15
    step: 1
  slow_ma:
    type: "choices"
    values: [20, 30, 50]

optimization_config:
  active: true
  algorithm: "GridSearch"
  objective_function: "SharpeRatio"
  objective_params:
    risk_free_rate: 0.02
```

#### Random Search Optimization
```yaml
ticker: BTC-USD
start_date: 2022-06-01
end_date: 2023-06-01
strategy_type: MovingAverageCrossover
strategy_params:
  fast_ma:
    type: "range"
    start: 5
    stop: 20
    step: 1
  slow_ma:
    type: "range"
    start: 21
    stop: 100
    step: 1

optimization_config:
  active: true  algorithm: "RandomSearch"
  algorithm_params:
    n_trials: 100
  objective_function: "SharpeRatio"
```

## Output and Reporting

### Console Output

MEQSAP provides rich, formatted output in the terminal:

#### Default Mode
- Strategy configuration summary
- Data acquisition progress
- Backtest execution status  
- Key performance metrics
- Trade summary statistics

#### Verbose Mode (`--verbose`)
- Detailed logging of all operations
- Data validation steps
- Signal generation diagnostics
- Extended performance metrics
- Error details and stack traces

#### Quiet Mode (`--quiet`)
- Minimal output for scripting
- Only essential results and errors
- No progress indicators or detailed logs

### PDF Reports (`--report`)

When using the `--report` option, MEQSAP generates comprehensive PDF reports including:

- **Executive Summary**: Key performance metrics and conclusions
- **Strategy Details**: Configuration and parameters used
- **Performance Charts**: Price charts with entry/exit signals
- **Risk Analysis**: Drawdown charts and risk metrics
- **Trade Analysis**: Detailed trade-by-trade breakdown
- **Statistical Summary**: Complete performance statistics

Reports are saved to the output directory (default: `./reports/`) with timestamps.

### Output Directory Structure

```
reports/
├── AAPL_MovingAverageCrossover_20231215_143022.pdf
├── AAPL_MovingAverageCrossover_20231215_143022_trades.csv
└── summary_stats.json
```

## Data Acquisition & Caching

MEQSAP handles market data acquisition automatically with intelligent caching.

### Features
- **Automatic Data Fetching**: Uses Yahoo Finance (yfinance) for market data
- **Local Caching**: Stores data in Parquet format to avoid redundant downloads
- **Data Integrity Checks**:
  - Validates no missing/NaN values
  - Ensures complete date range coverage
  - Checks data freshness (within 2 days for recent data)
- **Error Handling**: Clear messages for invalid tickers, missing data, or API issues

### Cache Location
Data is cached in: `data/cache/` directory

### Manual Cache Management
```python
from meqsap.data import clear_cache
clear_cache()  # Clear all cached data
```

## Error Handling and Troubleshooting

MEQSAP provides comprehensive error handling with helpful recovery suggestions.

### Common Issues and Solutions

#### Configuration Errors
```bash
Error: Invalid parameters for strategy MovingAverageCrossover: slow_ma must be greater than fast_ma
```
**Solution**: Ensure `slow_ma > fast_ma` in your configuration

#### Data Issues
```bash
Error: No data found for ticker 'INVALID_SYMBOL'
```
**Solution**: Check ticker symbol spelling and ensure it exists on Yahoo Finance

#### Insufficient Data
```bash
Error: Insufficient data: need at least 30 bars, got 20
```
**Solution**: Extend your date range or reduce the moving average periods

### Debug Mode
Use `--verbose` flag for detailed error information and troubleshooting steps.

## Examples and Use Cases

### 1. Quick Strategy Test
```bash
# Test a simple strategy with minimal output
python run.py analyze examples/ma_crossover.yaml --quiet
```

### 2. Comprehensive Analysis
```bash
# Full analysis with PDF report and detailed logging
python run.py analyze my_config.yaml --report --verbose --output-dir ./analysis_results
```

### 3. Configuration Validation
```bash
# Check if your configuration is valid before running
python run.py analyze my_config.yaml --validate-only
```

### 4. Parameter Optimization
```bash
# Find optimal parameters using Grid Search
python run.py optimize single examples/ma_crossover_dynamic_params.yaml --report

# Random search with custom trial count
python run.py optimize single config.yaml --trials 200 --verbose

# Optimization without progress bar (for automation)
python run.py optimize single config.yaml --no-progress --quiet
```

### 5. Batch Analysis (Scripting)
```bash
# Run multiple analyses in quiet mode for automation
foreach ($config in Get-ChildItem configs/*.yaml) {
    python run.py analyze $config.FullName --quiet --report
}
```

### 6. Mixed Workflows
```bash
# First validate, then optimize, then generate final report
python run.py analyze config.yaml --validate-only
python run.py optimize single config_with_ranges.yaml --trials 50
python run.py analyze best_config.yaml --report --verbose
```

## Development

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Setup Development Environment

1. **Clone the repository** (if applicable):
```bash
git clone <repository-url>
cd meqsap
```

2. **Install in development mode**:
```bash
pip install -e .
```

3. **Install development dependencies**:
```bash
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/test_config.py
pytest tests/test_backtest.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src/meqsap
```

### Code Quality

The project uses:
- **Type Hints**: All code includes comprehensive type annotations
- **Pydantic**: For configuration validation and data models
- **Error Handling**: Comprehensive exception handling with custom error types
- **Documentation**: Extensive docstrings and inline comments

### Project Structure

```
meqsap/
├── src/meqsap/           # Main package
│   ├── __init__.py       # Package initialization
│   ├── backtest.py       # Strategy backtesting engine
│   ├── config.py         # Configuration handling
│   ├── data.py           # Data acquisition and caching
│   ├── exceptions.py     # Custom exception classes
│   ├── reporting.py      # Report generation
│   ├── cli/              # Command-line interface
│   │   ├── __init__.py   # Main CLI entry point
│   │   ├── optimization_ui.py  # Progress bars and UI
│   │   ├── utils.py      # CLI utilities and decorators
│   │   └── commands/     # Sub-command implementations
│   │       └── optimize.py    # Optimization commands
│   ├── indicators_core/  # Enhanced parameter framework
│   │   ├── __init__.py   # Core indicator functionality
│   │   ├── base.py       # Base classes and abstractions
│   │   ├── parameters.py # Parameter type definitions
│   │   └── registry.py   # Indicator discovery system
│   └── optimizer/        # Parameter optimization engine
│       ├── __init__.py   # Optimizer public interface
│       ├── engine.py     # Core optimization engine
│       ├── models.py     # Data models and enums
│       ├── interruption.py  # Signal handling
│       └── objective_functions.py  # Optimization metrics
├── tests/               # Test suite
├── examples/            # Example configurations
├── docs/               # Documentation
├── run.py              # Convenient entry point
└── README.md           # This file
```

## API Reference

For detailed API documentation, see the docstrings in the source code:

- `config.py`: Configuration loading and validation
- `data.py`: Market data acquisition and caching
- `backtest.py`: Strategy implementation and backtesting
- `reporting.py`: Report generation and formatting
- `cli.py`: Command-line interface

## Support and Contributing

### Getting Help

1. **Check the examples**: Look at `examples/` directory for sample configurations
2. **Use verbose mode**: Run with `--verbose` for detailed diagnostics
3. **Check documentation**: Review this README and inline code documentation

### Reporting Issues

When reporting issues, please include:
- Your configuration file
- Complete error messages (use `--verbose`)
- Python version and operating system
- Steps to reproduce the issue

### Contributing

1. Follow the existing code style and patterns
2. Add tests for new features
3. Update documentation as needed
4. Ensure all tests pass before submitting

## License

MIT License - see LICENSE file for details.

---

## Quick Reference Card

### Essential Commands
```bash
# Basic usage
python run.py analyze config.yaml

# With reporting
python run.py analyze config.yaml --report --verbose

# Parameter optimization
python run.py optimize single config_with_ranges.yaml --report

# Validation only  
python run.py analyze config.yaml --validate-only

# Get help
python run.py --help
python run.py analyze --help
python run.py optimize --help
python run.py optimize single --help
```

### Sample Configuration
```yaml
ticker: AAPL
start_date: 2022-01-01
end_date: 2022-12-31
strategy_type: MovingAverageCrossover
strategy_params:
  fast_ma: 10
  slow_ma: 30
```

### Sample Optimization Configuration
```yaml
ticker: AAPL
start_date: 2022-01-01
end_date: 2022-12-31
strategy_type: MovingAverageCrossover
strategy_params:
  fast_ma:
    type: "range"
    start: 5
    stop: 15
    step: 1
  slow_ma:
    type: "choices"
    values: [20, 30, 50]
optimization_config:
  active: true
  algorithm: "GridSearch"
  objective_function: "sharpe"
```

### Common Issues
- **slow_ma must be greater than fast_ma**: Fix parameter ordering
- **Insufficient data**: Extend date range or reduce MA periods
- **No data found**: Check ticker symbol validity
- **Import errors**: Ensure you're in project root directory
- **optimization_config.active must be true**: Enable optimization in YAML config
- **Invalid parameter range**: Check start < stop for range definitions
- **No valid trials found**: Verify parameter ranges allow valid combinations

For more help: `python run.py --help` or `python run.py optimize single --help`
