# Project Plan: Stock Technical Analysis Tool

## Status Summary

*   **Total Tasks:** 19
*   **Tasks Done:** 5
*   **Tasks Pending:** 14
*   **% Completed:** 26.3%
*   **Total Estimated Hours:** 13.4 h
*   **Hours Completed:** 2.4 h
*   **Hours Pending:** 11.0 h

*(Summary based on initial estimates and completion of this plan file)*

---

## Task Breakdown

| Task ID | Description                                     | Estimated Hours | Status  |
| :------ | :---------------------------------------------- | :-------------- | :------ |
| **1**   | **Project Setup**                               | **0.4 h**       | Done    |
| 1.1     | Create project directory structure (`tech_analysis/`, `data/`, `plots/`, `reports/`) | 0.1 h           | Done    |
| 1.2     | Set up virtual environment (Recommended)        | 0.2 h           | Done    |
| 1.3     | Create `requirements.txt` and install dependencies | 0.1 h           | Done    |
| **2**   | **Data Layer (`pipeline.py`)**                  | **3.0 h**       | In Progress |
| 2.1     | Implement `fetch_data` function (yfinance)      | 1.0 h           | Done    |
| 2.2     | Implement `cache_data` function (to parquet)    | 1.0 h           | Done    |
| 2.3     | Add basic data validation (e.g., check for NaNs) | 1.0 h           | Pending |
| **3**   | **Backtesting (`backtest.py`)**                 | **3.0 h**       | Pending |
| 3.1     | Define `SMACrossover` strategy class & `init` method | 1.0 h           | Pending |
| 3.2     | Implement `next` method (buy/sell logic)        | 1.0 h           | Pending |
| 3.3     | Implement `run_backtest` function               | 1.0 h           | Pending |
| **4**   | **Reporting (`report_generator.py`)**           | **3.0 h**       | Pending |
| 4.1     | Implement `generate_report` function structure  | 0.2 h           | Pending |
| 4.2     | Generate equity curve plot (`bt.plot` to file)  | 0.5 h           | Pending |
| 4.3     | Create basic PDF report structure (fpdf2)       | 1.5 h           | Pending |
| 4.4     | Add metrics (Return, Sharpe, Drawdown) to PDF   | 0.5 h           | Pending |
| 4.5     | Add equity curve image to PDF                   | 0.3 h           | Pending |
| **5**   | **Pipeline Integration (`pipeline.py`)**        | **1.5 h**       | Pending |
| 5.1     | Create main execution flow structure in `pipeline.py` | 0.5 h           | Pending |
| 5.2     | Integrate data fetching, caching, backtesting, and reporting steps | 1.0 h           | Pending |
| **6**   | **Documentation & Refinement**                  | **2.5 h**       | Pending |
| 6.1     | Add docstrings and comments to functions/classes | 1.0 h           | Pending |
| 6.2     | Implement basic error handling (e.g., file not found) | 1.0 h           | Pending |
| 6.3     | Update `README.md` with usage instructions & details | 0.5 h           | Pending |

---
*Note: Hours are rough estimates and can be updated as the project progresses. Task status needs to be manually updated.*
