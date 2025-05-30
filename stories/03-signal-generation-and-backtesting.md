<!-- Status: Draft -->
# Story: Signal Generation and Backtesting Module Implementation

## Description
As the core engine of MEQSAP, we need to implement the signal generation and backtesting module that will take strategy configurations and historical market data to generate trading signals and execute comprehensive backtests. This module will leverage `pandas-ta` for technical indicators and `vectorbt` for high-performance backtesting operations.

## Acceptance Criteria
1. Signal generation module can create trading signals based on strategy configurations
2. Moving Average Crossover strategy is fully implemented with entry/exit signal generation
3. Backtesting engine can execute complete backtests using `vectorbt` with the generated signals
4. Performance metrics are calculated and returned in a structured format
5. "Vibe Checks" are implemented to validate strategy reasonableness (minimum trade count, etc.)
6. Robustness checks are implemented (high fees simulation, turnover analysis)
7. Unit tests cover all signal generation and backtesting logic
8. Module is independent and follows the modular monolith pattern
9. Clear error handling for edge cases (no signals generated, insufficient data, etc.)

## Implementation Details

### Backtesting Module Architecture
Create `src/meqsap/backtest.py` as the core backtesting engine with the following components:

#### Signal Generation
- **Strategy Factory Pattern**: Implement a pluggable strategy system that can be easily extended
- **Moving Average Crossover Implementation**: 
  - Use `pandas-ta` to calculate fast and slow moving averages
  - Generate long signals when fast MA crosses above slow MA
  - Generate short/exit signals when fast MA crosses below slow MA
- **Signal Validation**: Ensure signals are properly aligned with price data and contain no forward-looking bias

#### Backtesting Engine
- **vectorbt Integration**: Use `vectorbt.Portfolio` for high-performance backtesting
- **Trade Execution Logic**: Implement realistic trade execution with configurable fees
- **Position Management**: Handle position sizing, entry/exit timing, and cash management
- **Performance Calculation**: Extract comprehensive performance metrics from vectorbt results

#### Vibe Checks Implementation
1. **Minimum Trade Check**: Ensure at least one trade was executed during the backtest period
2. **Signal Quality Check**: Validate that signals are reasonable (not too frequent/infrequent)
3. **Data Coverage Check**: Ensure sufficient data for strategy parameters (e.g., slow MA period)

#### Robustness Checks
1. **High Fees Simulation**: Re-run backtest with elevated transaction costs (e.g., 1% vs 0.1%)
2. **Turnover Analysis**: Calculate portfolio turnover rate and flag high-frequency strategies
3. **Sensitivity Analysis**: Test strategy performance across different parameter ranges

### Core Functions

#### `generate_signals(data: pd.DataFrame, strategy_config: StrategyConfig) -> pd.DataFrame`
- Takes OHLCV data and strategy configuration
- Returns DataFrame with 'entry' and 'exit' boolean columns
- Handles different strategy types via factory pattern

#### `run_backtest(data: pd.DataFrame, signals: pd.DataFrame, initial_cash: float = 10000, fees: float = 0.001) -> BacktestResult`
- Executes backtest using vectorbt
- Returns structured results with performance metrics
- Includes trade-level details and portfolio statistics

#### `perform_vibe_checks(result: BacktestResult, data: pd.DataFrame, strategy_config: StrategyConfig) -> VibeCheckResults`
- Runs all validation checks on backtest results
- Returns pass/fail status for each check with explanatory messages

#### `perform_robustness_checks(data: pd.DataFrame, signals: pd.DataFrame, strategy_config: StrategyConfig) -> RobustnessResults`
- Executes robustness analysis
- Compares baseline vs stress-test scenarios
- Returns sensitivity metrics and recommendations

### Data Models

#### `BacktestResult` (Pydantic Model)
```python
class BacktestResult(BaseModel):
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    avg_trade_duration: float
    portfolio_value: pd.Series
    trades: pd.DataFrame
    # Additional vectorbt metrics
```

#### `VibeCheckResults` (Pydantic Model)
```python
class VibeCheckResults(BaseModel):
    minimum_trades_check: bool
    signal_quality_check: bool
    data_coverage_check: bool
    messages: List[str]
    overall_pass: bool
```

#### `RobustnessResults` (Pydantic Model)
```python
class RobustnessResults(BaseModel):
    baseline_sharpe: float
    high_fees_sharpe: float
    sharpe_degradation: float
    turnover_rate: float
    robustness_score: float
    recommendations: List[str]
```

### Technical Implementation Requirements

#### Dependencies
- Add `vectorbt`, `pandas-ta` to requirements.txt
- Ensure compatibility with existing pandas/numpy versions

#### Performance Considerations
- Use vectorbt's optimized operations for large datasets
- Implement efficient signal generation to avoid N+1 loops
- Cache intermediate calculations where appropriate

#### Error Handling
- Handle insufficient data gracefully (e.g., not enough bars for slow MA)
- Provide clear error messages for invalid strategy parameters
- Validate signal alignment with price data

#### Testing Strategy
- Unit tests for signal generation functions with known inputs/outputs
- Integration tests for full backtest workflow
- Edge case testing (no signals, single signal, etc.)
- Performance benchmarking for large datasets

## Tasks Breakdown
- [ ] Create `src/meqsap/backtest.py` module structure
- [ ] Implement strategy factory pattern and base strategy interface
- [ ] Implement Moving Average Crossover signal generation using pandas-ta
- [ ] Integrate vectorbt for backtesting execution
- [ ] Implement performance metrics calculation and result packaging
- [ ] Create vibe check validation functions
- [ ] Implement robustness check framework
- [ ] Add comprehensive unit tests in `tests/test_backtest.py`
- [ ] Create integration tests for end-to-end backtesting workflow
- [ ] Update CLI module to integrate with backtesting functionality
- [ ] Add documentation and examples for extending strategy types

## Definition of Done
- [ ] All acceptance criteria are met and tested
- [ ] Module passes all unit and integration tests
- [ ] Code follows project style guidelines and type hints
- [ ] Documentation is complete with usage examples
- [ ] Integration with existing config and data modules is seamless
- [ ] Performance benchmarks meet requirements (sub-second for typical strategies)
- [ ] Error handling provides clear, actionable user feedback

## Dependencies
- **Prerequisite**: Story 01 (Project Setup and Configuration) - ✅ Completed
- **Prerequisite**: Story 02 (Data Acquisition and Caching) - ✅ Completed
- **Successor**: Story 04 (Reporting and Presentation Layer)

## Detailed Pseudocode

### Main Backtesting Orchestration Function

**Component:** `Backtest Module`
**Function:** `run_complete_backtest`

**Inputs:**
* The validated `Strategy Configuration` provided by the user
* The `Market Data` for the specified ticker (as a pandas DataFrame)

**Output:**
* A comprehensive `Backtest Analysis Result` object containing performance metrics, vibe check results, and robustness analysis

**Steps:**
1. **Generate Trading Signals.**
   * Call the `generate_signals` function with the `Market Data` and `Strategy Configuration`
   * Return a DataFrame containing boolean columns for entry and exit signals aligned with the market data dates

2. **Execute Primary Backtest.**
   * Call the `run_backtest` function with the `Market Data`, generated signals, and default parameters (initial cash: $10,000, fees: 0.1%)
   * Store the result as the `Primary Backtest Result`

3. **Perform Strategy Validation Checks.**
   * Call the `perform_vibe_checks` function with the `Primary Backtest Result`, `Market Data`, and `Strategy Configuration`
   * Store the results as `Vibe Check Results`

4. **Execute Robustness Analysis.**
   * Call the `perform_robustness_checks` function with the `Market Data`, signals, and `Strategy Configuration`
   * Store the results as `Robustness Check Results`

5. **Assemble Comprehensive Analysis.**
   * Create a new `Backtest Analysis Result` object containing:
     * The complete `Primary Backtest Result`
     * The `Vibe Check Results` with pass/fail status for each check
     * The `Robustness Check Results` with sensitivity metrics
     * An overall recommendation based on all checks

6. **Return the complete analysis** to the calling module (the `CLI Module`)

---

### Signal Generation Function

**Component:** `Backtest Module`
**Function:** `generate_signals`

**Inputs:**
* The `Market Data` for the specified ticker (as a pandas DataFrame with OHLCV columns)
* The validated `Strategy Configuration` containing strategy type and parameters

**Output:**
* A `Signals DataFrame` with boolean columns for 'entry' and 'exit' signals, indexed by date

**Steps:**
1. **Identify Strategy Type.**
   * Extract the `strategy_type` from the `Strategy Configuration`
   * Use a strategy factory pattern to select the appropriate signal generation logic

2. **Extract Strategy Parameters.**
   * For Moving Average Crossover strategy, extract `fast_ma` and `slow_ma` periods from the configuration
   * Validate that sufficient data exists (data length >= slow_ma period)

3. **Calculate Technical Indicators.**
   * Using the `pandas-ta` library, calculate the fast moving average: `ta.sma(close_prices, length=fast_ma)`
   * Using the `pandas-ta` library, calculate the slow moving average: `ta.sma(close_prices, length=slow_ma)`
   * Ensure both moving average series are properly aligned with the original data dates

4. **Generate Entry Signals.**
   * Create entry conditions: Fast MA crosses above Slow MA
   * Use pandas logic: `(fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))`
   * Mark these crossover points as True in the 'entry' column

5. **Generate Exit Signals.**
   * Create exit conditions: Fast MA crosses below Slow MA
   * Use pandas logic: `(fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))`
   * Mark these crossover points as True in the 'exit' column

6. **Validate Signal Integrity.**
   * Ensure no forward-looking bias exists in the signals
   * Verify signals are properly aligned with price data dates
   * Check that at least one signal was generated

7. **Return the `Signals DataFrame`** containing entry and exit boolean columns

---

### Core Backtesting Execution Function

**Component:** `Backtest Module`
**Function:** `run_backtest`

**Inputs:**
* The `Market Data` for the specified ticker (as a pandas DataFrame)
* The `Signals DataFrame` containing entry and exit boolean columns
* The `initial_cash` amount (default: $10,000)
* The `fees` percentage (default: 0.001 = 0.1%)

**Output:**
* A structured `Backtest Result` object containing performance metrics and trade details

**Steps:**
1. **Prepare Data for vectorbt.**
   * Extract the closing prices from the `Market Data` as a pandas Series
   * Ensure the closing prices are aligned with the signal dates
   * Convert the entry and exit signals to the format expected by vectorbt

2. **Configure Portfolio Parameters.**
   * Set the initial cash amount for the portfolio
   * Configure the commission/fees structure for realistic transaction costs
   * Define position sizing rules (default: invest all available cash per trade)

3. **Execute Portfolio Simulation.**
   * Use `vectorbt.Portfolio.from_signals()` to create and run the backtest
   * Provide the function with:
     * The closing prices from the `Market Data`
     * The entry signals from the `Signals DataFrame`
     * The exit signals from the `Signals DataFrame`
     * The configured fees and initial cash parameters

4. **Extract Performance Statistics.**
   * From the vectorbt portfolio result, calculate:
     * Total return percentage
     * Annualized return percentage
     * Sharpe ratio
     * Maximum drawdown percentage
     * Win rate (percentage of profitable trades)
     * Total number of trades executed
     * Average trade duration in days

5. **Extract Trade Details.**
   * Obtain the detailed trade log from vectorbt showing:
     * Entry dates and prices
     * Exit dates and prices
     * Trade profit/loss amounts
     * Trade durations

6. **Extract Portfolio Value Series.**
   * Get the daily portfolio value progression from vectorbt
   * This will be used for plotting and further analysis

7. **Assemble Structured Result.**
   * Create a new `Backtest Result` object (using Pydantic model)
   * Populate it with all extracted metrics, trade details, and portfolio value series

8. **Return the complete `Backtest Result`** to the calling function

---

### Vibe Checks Validation Function

**Component:** `Backtest Module`
**Function:** `perform_vibe_checks`

**Inputs:**
* The `Backtest Result` object from the primary backtest execution
* The original `Market Data` used in the backtest
* The `Strategy Configuration` containing strategy parameters

**Output:**
* A `Vibe Check Results` object containing pass/fail status and explanatory messages for each validation

**Steps:**
1. **Check Minimum Trade Count.**
   * Extract the `total_trades` from the `Backtest Result`
   * Validate that at least 1 trade was executed during the backtest period
   * If zero trades: mark as FAIL with message "Strategy generated no trades - may be inactive or misconfigured"
   * If trades > 0: mark as PASS

2. **Check Signal Quality.**
   * Calculate the signal frequency: total trades divided by total trading days
   * Validate that the signal frequency is reasonable (not too high or too low)
   * If frequency > 0.1 (more than 10% of days): mark as WARNING with message "High signal frequency detected - strategy may be overactive"
   * If frequency < 0.01 (less than 1% of days): mark as WARNING with message "Low signal frequency detected - strategy may be underutilized"
   * Otherwise: mark as PASS

3. **Check Data Coverage.**
   * Extract the strategy parameters (e.g., `slow_ma` period for Moving Average Crossover)
   * Validate that sufficient historical data exists for the strategy to operate properly
   * Calculate minimum required data points: `slow_ma` period + 20 trading days buffer
   * If available data < minimum required: mark as FAIL with message "Insufficient historical data for strategy parameters"
   * Otherwise: mark as PASS

4. **Check Performance Reasonableness.**
   * Extract the Sharpe ratio from the `Backtest Result`
   * Validate that the Sharpe ratio indicates the strategy has some edge
   * If Sharpe ratio < 0: mark as WARNING with message "Negative Sharpe ratio indicates poor risk-adjusted returns"
   * If Sharpe ratio > 3: mark as WARNING with message "Extremely high Sharpe ratio - results may not be realistic"
   * Otherwise: mark as PASS

5. **Determine Overall Status.**
   * If any check marked as FAIL: set overall status to FAIL
   * If only WARNING checks exist: set overall status to PASS_WITH_WARNINGS
   * If all checks marked as PASS: set overall status to PASS

6. **Assemble Results Object.**
   * Create a `Vibe Check Results` object containing:
     * Individual check results (boolean pass/fail for each)
     * Explanatory messages for each check
     * Overall pass/fail status
     * Recommendations for addressing any failures

7. **Return the `Vibe Check Results`** to the calling function

---

### Robustness Analysis Function

**Component:** `Backtest Module`
**Function:** `perform_robustness_checks`

**Inputs:**
* The `Market Data` for the specified ticker
* The `Signals DataFrame` containing entry and exit signals
* The `Strategy Configuration` containing strategy parameters

**Output:**
* A `Robustness Results` object containing sensitivity analysis and stress test results

**Steps:**
1. **Execute Baseline Backtest.**
   * Run the standard backtest with normal fees (0.1%) using the `run_backtest` function
   * Store the Sharpe ratio as `baseline_sharpe`
   * Store the total return as `baseline_return`

2. **Execute High Fees Stress Test.**
   * Re-run the backtest with elevated transaction costs (1.0% fees)
   * Store the Sharpe ratio as `high_fees_sharpe`
   * Store the total return as `high_fees_return`

3. **Calculate Fee Sensitivity.**
   * Calculate the Sharpe ratio degradation: `(baseline_sharpe - high_fees_sharpe) / baseline_sharpe`
   * Calculate the return degradation: `(baseline_return - high_fees_return) / baseline_return`
   * If Sharpe degradation > 50%: mark as HIGH_SENSITIVITY with warning
   * If Sharpe degradation 20-50%: mark as MEDIUM_SENSITIVITY
   * If Sharpe degradation < 20%: mark as LOW_SENSITIVITY

4. **Calculate Portfolio Turnover.**
   * From the baseline backtest trade details, calculate the total value traded
   * Calculate turnover rate: total value traded divided by average portfolio value
   * If turnover > 5.0 (500% annually): mark as HIGH_TURNOVER with warning
   * If turnover 2.0-5.0: mark as MEDIUM_TURNOVER
   * If turnover < 2.0: mark as LOW_TURNOVER

5. **Generate Robustness Score.**
   * Create a composite score based on:
     * Fee sensitivity (lower is better)
     * Turnover rate (lower is generally better)
     * Consistency of returns across stress tests
   * Scale the score from 0-100 where 100 is most robust

6. **Generate Recommendations.**
   * Based on the robustness analysis results, create actionable recommendations:
     * If HIGH_SENSITIVITY: "Strategy is highly sensitive to transaction costs - consider optimizing trade frequency"
     * If HIGH_TURNOVER: "Strategy exhibits high turnover - may not be suitable for retail trading"
     * If robust across tests: "Strategy shows good robustness characteristics"

7. **Assemble Results Object.**
   * Create a `Robustness Results` object containing:
     * Baseline and stress test metrics
     * Sensitivity measurements
     * Turnover analysis
     * Overall robustness score
     * Specific recommendations

8. **Return the `Robustness Results`** to the calling function

---

## Notes
This story represents the core value-add of MEQSAP - the orchestration of powerful libraries (vectorbt, pandas-ta) to provide a simple, configuration-driven backtesting experience. The implementation should prioritize clarity and extensibility while leveraging the performance optimizations available in vectorbt.

The pseudocode above follows the MEQSAP methodology of describing the "happy path" logic clearly, with explicit references to external libraries and configuration parameters. Each function has well-defined inputs/outputs and follows the data's journey through the system as outlined in the architecture document.
