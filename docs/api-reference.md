# Adaptive Automated Trading Strategy Discovery System API Reference

## 1. Overview

This document provides a reference for the external APIs consumed by the system and the primary interfaces (CLI and configuration files) through which users interact with the system. It also touches upon key internal data structures that act as contracts between components.

## 2. External APIs Consumed

### Yahoo Finance (via `yfinance` library)

-   **Purpose:** To download historical End-of-Day (EOD) and potentially intraday stock market data (OHLCV - Open, High, Low, Close, Volume) for specified equity symbols. This is the primary source of market data for the system.
-   **Library Used:** `yfinance` (Python library)
    -   Version: `0.2.18+` (as specified in `docs/tech-stack.md`)
-   **Base URL(s):** Not directly used; the `yfinance` library handles communication with Yahoo Finance servers.
-   **Authentication:**
    *   Standard `yfinance` usage for public historical data typically does not require an API key or authentication.
    *   If specific premium features were ever used or if Yahoo Finance changes its policies, an API key might be required. In such a case, it would be managed via an environment variable (e.g., `YFINANCE_API_KEY` as mentioned in `docs/environment-vars.md`).
-   **Key `yfinance` Operations Used (Conceptual Python SDK-like usage):**
    *   **`yf.Ticker("SYMBOL")`**: Creates a Ticker object for a specific stock symbol.
        -   Example: `msft = yf.Ticker("MSFT")`
    *   **`ticker.history(period="max", interval="1d", start="YYYY-MM-DD", end="YYYY-MM-DD")`**: Fetches historical data.
        -   Description: Retrieves OHLCV data for the specified symbol and parameters.
        -   Parameters used by the system (driven by `config.yaml`):
            *   `symbol`: Stock ticker (e.g., "RELIANCE.NS").
            *   `start`: Start date for data fetching.
            *   `end`: End date for data fetching.
            *   `interval`: Data interval (e.g., "1d" for daily, "1h" for hourly).
        -   Example Response (Pandas DataFrame):
            ```
            Open    High    Low     Close   Volume  Dividends   Stock Splits
            Date
            2023-01-02  120.5   122.3   120.0   121.7   100000      0.0         0.0
            ...
            ```
    *   Other `yfinance` functionalities (e.g., fetching company info, financials) are not core to the MVP's strategy discovery but might be used for extended analysis if implemented.
-   **Rate Limits:**
    *   Yahoo Finance may impose rate limits on API requests. The `yfinance` library might handle some of this, but excessive requests can lead to temporary blocks.
    *   The system's data fetching component includes configurable retries with backoff (see `docs/coding-standards.md` and PRD) to manage transient issues.
    *   Local caching (SQLite database, see `docs/data-models.md`) is implemented to minimize repeated API calls.
-   **Link to Official Docs:**
    *   `yfinance` library: [https://pypi.org/project/yfinance/](https://pypi.org/project/yfinance/)
    *   Yahoo Finance: While direct API documentation from Yahoo is scarce for the public endpoints `yfinance` uses, general financial data terms apply.

## 3. System Interface (CLI & Configuration)

The primary way users interact with the system is through its Command Line Interface (CLI) and the `config.yaml` file.

### Command Line Interface (CLI)

-   **Tool:** Implemented using `Typer` (built on `Click`).
-   **Main Command:** `tradefinder` (or a similar name defined in `pyproject.toml` script entry points).
-   **Key Sub-Commands:**
    *   **`tradefinder discover`**: The main command to run the full strategy discovery and backtesting pipeline.
        -   **Arguments/Options:**
            *   `--config-file <PATH_TO_CONFIG_YAML>` or `-c <PATH_TO_CONFIG_YAML>`:
                -   Description: Path to the YAML configuration file that defines all parameters for the run.
                -   Required: Yes.
                -   Schema: See "Configuration File (`config.yaml`) Schema" below and `docs/data-models.md` (`CLIConfiguration` Pydantic model).
            *   `--log-level <LEVEL>` (Optional):
                -   Description: Overrides the logging level specified in the config file or `APP_LOG_LEVEL` environment variable.
                -   Values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
            *   `--run-id <ID>` (Optional):
                -   Description: Specify a custom run ID. If not provided, a UUID will be generated.
        -   **Example Usage:**
            ```bash
            tradefinder discover --config-file ./config/my_large_cap_config.yaml --log-level DEBUG
            ```
    *   **`tradefinder backtest`** (Potential future command): To backtest a single, already defined strategy.
        -   Arguments: `--strategy-file <PATH_TO_STRATEGY_JSON>`, `--config-file <PATH_TO_BACKTEST_CONFIG_YAML>`
    *   **`tradefinder utils [sub-command]`** (Potential future command group): For utility functions.
        -   Example: `tradefinder utils clear-cache --symbols MSFT AAPL`

### Configuration File (`config.yaml`) Schema

-   **Purpose:** This YAML file is the primary way to define all parameters for a strategy discovery run, including data sources, feature engineering settings, Genetic Algorithm parameters, backtesting settings, and reporting options.
-   **Schema Definition:** The structure of this file is formally defined by the `CLIConfiguration` Pydantic model in `docs/data-models.md`. Please refer to that document for the detailed schema, including all fields, types, descriptions, and default values.
-   **Example Snippet (Illustrative - see `docs/data-models.md` for full structure):**
    ```yaml
    # docs/data-models.md -> CLIConfiguration
    run_id: "my_first_run_20250515" # Optional

    data_source:
      provider: "yfinance"
      symbols: ["RELIANCE.NS", "INFY.NS", "HDFCBANK.NS"]
      start_date: "2018-01-01"
      end_date: "2023-12-31"
      interval: "1d"

    genetic_algorithm:
      population_size: 100
      generations: 50
      # ... other GA params

    # ... other sections like feature_engineering, backtesting, reporting
    ```

## 4. Key Internal Data "APIs" / Contracts

While not external APIs, certain internal data structures serve as critical contracts between components. These are defined as Pydantic models in `docs/data-models.md`.

### TradingStrategy Model

-   **Purpose:** Defines the structure of an evolved trading strategy, including its rules and parameters. This is the primary output of the GA and input to the backtester and reporter.
-   **Schema:** See `TradingStrategy` Pydantic model in `docs/data-models.md`.
    *   Includes `buy_rules` and `sell_rules`, which are lists of `StrategyRule` objects.
    *   Each `StrategyRule` contains a list of `StrategyRuleCondition` objects, matching the JSON format described in PRD (Capability 2).
-   **Example JSON representation of a rule condition (as per PRD):**
    ```json
    {
        "indicator": "SMA_20",
        "operator": "crosses_above",
        "value_type": "indicator",
        "value": "SMA_50"
    }
    ```

### BacktestMetrics Model

-   **Purpose:** Defines the structure for reporting the performance of a backtested strategy.
-   **Schema:** See `BacktestMetrics` Pydantic model in `docs/data-models.md`.

### StockDataPoint Model

-   **Purpose:** Standardized representation of a single data point (OHLCV + indicators) as it flows through the system.
-   **Schema:** See `StockDataPoint` Pydantic model in `docs/data-models.md`.

## 5. Cloud Service SDK Usage

-   Not applicable for the MVP, as the system is designed for local execution. Future cloud-based versions would detail SDK usage here (e.g., AWS SDK for S3, Lambda, EventBridge).

## 6. Change Log

| Change        | Date       | Version | Description                                     | Author         |
| ------------- | ---------- | ------- | ----------------------------------------------- | -------------- |
| Initial Draft | 2025-05-15 | 0.1     | Created based on template and PRD requirements. | Gemini 2.5 Pro |