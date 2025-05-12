# Automated Strategy Discovery Report

**Run ID:** [Unique Identifier for the optimization run]
**Date Generated:** [Date of report generation]
**Target Instrument(s):** [e.g., RELIANCE.NS, NIFTY 50 constituents]
**Analysis Period:** [e.g., 2018-01-01 to 2023-12-31 (In-Sample: 2018-2022, OOS: 2023)]

---

### Executive Summary

*   **Best Strategy Found:** Strategy ID `[Strategy_ID]` emerged as the top performer based on [Primary Fitness Metric, e.g., Sharpe Ratio].
*   **Core Performance:** Achieved a Net Profit of [Value]% and Sharpe Ratio of [Value] during the full period backtest.
*   **Validation Status:** **[PASSED / FAILED / WARNING]** - The strategy [passed/failed/showed warnings on] the predefined robustness and validation checks. [Add brief reason if failed/warning, e.g., "failed due to significant performance drop in low volatility regime"].
*   **Key Heuristics:** Characterized by [e.g., `Trend Following`, `Low Drawdown`].
*   **Common Failures This Run:** The optimization process frequently encountered strategies failing due to `[Most Common Failure Tag, e.g., Whipsaw]` (approx. [X]% of discarded strategies).

---

### Top Strategy Details: `[Strategy_ID]`

*   **Strategy Logic (Human Readable):**
    *   **Entry Condition (Long):**
        *   [e.g., 14-period RSI crosses above 30]
        *   **AND** [e.g., Close price is above the 50-period Simple Moving Average]
        *   **AND** [e.g., Average Directional Index (ADX 14) is greater than 20]
    *   **Exit Condition (Long):**
        *   [e.g., 14-period RSI crosses below 70]
        *   **OR** [e.g., Stop Loss triggered at 2x Average True Range (ATR 14) below entry price]
*   **Parameters:**
    *   `RSI Period`: 14
    *   `RSI Overbought`: 70
    *   `RSI Oversold`: 30
    *   `SMA Period`: 50
    *   `ADX Period`: 14
    *   `ADX Threshold`: 20
    *   `ATR Period (for Stop Loss)`: 14
    *   `ATR Multiplier (for Stop Loss)`: 2.0
*   **Heuristic Profile:** [`Robust`, `Low Drawdown`, `Trend Following`, `Volatility Filtered`] *(Tags assigned by the StrategyAnalyzer)*

---

### Performance Metrics (`[Strategy_ID]`)

| Metric             | In-Sample ([Start]-[End]) | Out-of-Sample ([Start]-[End]) | Full Period ([Start]-[End]) | Baseline ([Name]) |
| :----------------- | :------------------------ | :---------------------------- | :-------------------------- | :---------------- |
| Net Profit (%)     | [Value]%                  | [Value]%                      | **[Value]%**                | [Value]%          |
| Sharpe Ratio       | [Value]                   | [Value]                       | **[Value]**                 | [Value]           |
| Max Drawdown (%)   | [Value]%                  | [Value]%                      | **[Value]%**                | [Value]%          |
| Sortino Ratio      | [Value]                   | [Value]                       | **[Value]**                 | [Value]           |
| Calmar Ratio       | [Value]                   | [Value]                       | **[Value]**                 | [Value]           |
| Win Rate (%)       | [Value]%                  | [Value]%                      | **[Value]%**                | [Value]%          |
| Avg Trades / Year  | [Value]                   | [Value]                       | **[Value]**                 | [Value]           |
| Profit Factor      | [Value]                   | [Value]                       | **[Value]**                 | [Value]           |

*   **Equity Curve:** [Link to Equity Curve Image file, e.g., ./equity_curve_strategy_[ID].png]
*   **In-Sample vs Out-of-Sample:** [Brief comment on consistency, e.g., "Performance metrics remained relatively stable OOS, indicating good generalization.", or "Significant drop in Sharpe Ratio OOS suggests potential overfitting."]

---

### Robustness & Validation (`[Strategy_ID]`)

*   **Overall Validation Status:** **[PASSED / FAILED / WARNING]**
*   **Out-of-Sample Test:** [Passed/Failed] - Performance met acceptable thresholds compared to in-sample.
*   **Performance Degradation Check:** [Passed/Failed] - No significant performance decay observed across validation window segments.
*   **Adversarial Simulation / Regime Performance:**

    | Market Regime          | Period Tested     | Sharpe Ratio | Net Profit (%) | Consistency Notes                                  |
    | :--------------------- | :---------------- | :----------- | :------------- | :------------------------------------------------- |
    | High Volatility        | [Dates]           | [Value]      | [Value]%       | [e.g., Performed well]                             |
    | Low Volatility         | [Dates]           | [Value]      | [Value]%       | [e.g., Underperformed, tagged `Regime Specific`?] |
    | Strong Bull Market     | [Dates]           | [Value]      | [Value]%       | [e.g., Consistent]                                 |
    | Strong Bear Market     | [Dates]           | [Value]      | [Value]%       | [e.g., Reduced profit but positive Sharpe]         |
    | Stress Event ([Name])  | [Dates]           | [Value]      | [Value]%       | [e.g., Handled drawdown effectively]               |
*   **Validation Summary:** [Overall assessment, e.g., "Strategy demonstrates robustness across most tested regimes, though caution advised in low-volatility environments."]

---

### Evolution & Failure Analysis Insights (Run `[Run_ID]`)

*   **Strategy Evolution:** The top strategy (`[Strategy_ID]`) likely evolved from [e.g., simpler RSI mean-reversion rules by incorporating trend (SMA) and volatility (ADX) filters around generation X, likely influenced by penalties against `Whipsaw` tags]. *(High-level insight from StrategyOptimizer logs/analysis)*
*   **Common Failure Tags Observed:**
    *   `Whipsaw`: [X]% (Frequent losses in range-bound markets)
    *   `Late Entry`: [Y]% (Signals often occurred after significant price moves)
    *   `Overfitting`: [Z]% (Strategies performed poorly on validation segments)
    *   `Noisy Indicator`: [Indicator Name, e.g., Stochastic Oscillator] frequently led to poor trades without confirmation.
*   **Underperforming Patterns:** [e.g., Simple short-term MA crossovers without additional filters consistently underperformed during this run.]

---

### Trade Log Summary (`[Strategy_ID]`)

*   **Total Trades:** [Value]
*   **Average Holding Period:** [Value] [Days/Hours]
*   **Percent Profitable:** [Value]%
*   **Ratio Avg Win / Avg Loss:** [Value]
*   **Detailed Trade Log:** [Link to detailed CSV/log file, e.g., ./trade_log_strategy_[ID].csv] (Optional)

---

### Run Configuration

*   **Feature Set Used:** [e.g., Standard Price/Vol/Indicators, No Correlation Features]
*   **GA Parameters:**
    *   Population Size: [Value]
    *   Generations: [Value]
    *   Mutation Rate: [Value]
    *   Crossover Rate: [Value]
    *   Fitness Metric: [e.g., Sharpe Ratio + Drawdown Penalty]
*   **Backtester Settings:**
    *   Commission: [Value]%
    *   Slippage Model: [e.g., Fixed ticks]
*   **Full Configuration:** [Link to YAML/JSON config file used, e.g., ./config_run_[ID].yaml]

---