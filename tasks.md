# Project Plan: Stock Technical Analysis Tool

## Status Summary

*   **Total Tasks:** 22
*   **Tasks Pending:** 11
*   **Tasks Pending:** 11
*   **% Completed:** 50.0%
*   **Total Estimated Hours:** 14.4 h
*   **Hours Completed:** 10.2 h
*   **Hours Pending:** 4.2 h

*(Summary based on initial estimates and completion of this plan file)*

---

## Task Breakdown

| Task ID | Description                                     | Estimated Hours | Status  |
| :------ | :---------------------------------------------- | :-------------- | :------ |
| **1**   | **Project Setup**                               | **0.4 h**       | Done    |
| 1.1     | Create project directory structure (`tech_analysis/`, `data/`, `plots/`, `reports/`) | 0.1 h           | Pending |
| 1.2     | Set up virtual environment (Recommended)        | 0.2 h           | Done    |
| 1.3     | Create `requirements.txt` and install dependencies | 0.1 h           | Done    |
| **2**   | **Data Layer (`pipeline.py`)**                  | **3.5 h**       | Pending |
| 2.1     | Implement `fetch_data` function (yfinance)      | 1.0 h           | Pending    |
| 2.2     | Implement `cache_data` function (to parquet)    | 1.0 h           | Pending    |
| 2.3     | Add basic data validation (e.g., check for NaNs) | 1.5 h           | Pending |
| **3**   | **Backtesting (`backtest.py`)**                 | **3.0 h**       | Pending |
| 3.1     | Define `SMACrossover` strategy class            | 0.5 h           | Pending |
| 3.2     | Implement `init` method (initialize SMAs)       | 0.5 h           | Pending |
| 3.3     | Implement `next` method (buy/sell logic)        | 1.0 h           | Pending |
| 3.4     | Implement `run_backtest` function               | 1.0 h           | Pending |
| **4**   | **Reporting (`report_generator.py`)**           | **3.0 h**       | Pending |
| 4.1     | Implement `generate_report` function structure  | 0.2 h           | Pending |
| 4.2     | Generate equity curve plot (using `bt.plot`)    | 0.5 h           | Pending |
| 4.3     | Create basic PDF report structure (fpdf2)       | 1.5 h           | Pending |
| 4.4     | Add metrics (Return, Sharpe, Drawdown) to PDF   | 0.5 h           | Pending    |
| 4.5     | Add equity curve image to PDF                   | 0.3 h           | Pending    |\
| 4.6     | Debug/Fix PDF generation (`report_generator.py`) | 1.5 h           | Pending |
| 4.7     | Add trade list/log to PDF report                | 1.0 h           | Pending |
| 4.8     | Add strategy parameters & commission to report  | 0.5 h           | Pending |
| 4.9     | Implement Nifty 50 (^NSEI) data fetching        | 0.5 h           | Pending |
| 4.10    | Calculate Nifty buy-and-hold return             | 0.5 h           | Pending |
| 4.11    | Add Nifty comparison to PDF report              | 1.5 h           | Pending |
\
| 4.6     | Debug/Fix PDF generation (`report_generator.py`) | 1.5 h           | Pending |
| 4.7     | Add trade list/log to PDF report                | 1.0 h           | Pending |
| 4.8     | Add strategy parameters & commission to report  | 0.5 h           | Pending |
| 4.9     | Implement Nifty 50 (^NSEI) data fetching        | 0.5 h           | Pending |
| 4.10    | Calculate Nifty buy-and-hold return             | 0.5 h           | Pending |
| 4.11    | Add Nifty comparison to PDF report              | 1.5 h           | Pending |\
| 4.6     | Debug/Fix PDF generation (`report_generator.py`) | 1.5 h           | Pending |
| 4.7     | Add trade list/log to PDF report                | 1.0 h           | Pending |
| 4.8     | Add strategy parameters & commission to report  | 0.5 h           | Pending |
| 4.9     | Implement Nifty 50 (^NSEI) data fetching        | 0.5 h           | Pending |
| 4.10    | Calculate Nifty buy-and-hold return             | 0.5 h           | Pending |
| 4.11    | Add Nifty comparison to PDF report              | 1.5 h           | Pending |
| **5**   | **Pipeline Integration (`pipeline.py`)**        | **1.5 h**       | Pending |
| 5.1     | Create main execution flow structure in `pipeline.py` | 0.5 h           | Pending    |
| 5.2     | Integrate data fetching, caching, backtesting, and reporting steps | 1.0 h           | Pending    |
| **6**   | **Documentation & Refinement**                  | **3.0 h**       | Not Started |
| 6.1     | Add docstrings and comments to functions/classes | 1.0 h           | Pending |
| 6.2     | Implement basic error handling (e.g., file not found) | 1.0 h           | Pending |
| 6.3     | Update `README.md` with usage instructions & details | 0.5 h           | Pending |
| 6.4     | Create `plan.md` (this file)                    | 0.5 h           | Pending    |
| **7**   | **Future Extensions (Optional)**                | **N/A**         | Pending |
| 7.1     | Add more indicators (RSI, MACD)                 | TBD             | Pending |
| 7.2     | Implement parameter optimization                | TBD             | Pending |
| 7.3     | Explore live trading integration                | TBD             | Pending |
| 7.4     | Investigate sentiment analysis inputs           | TBD             | Pending |

---
*Note: Hours are rough estimates and can be updated as the project progresses. Task status needs to be manually updated.*
