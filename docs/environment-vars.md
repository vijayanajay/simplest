# Adaptive Automated Trading Strategy Discovery System Environment Variables

## 1. Overview

This document lists and describes the environment variables that can be used to configure the Adaptive Automated Trading Strategy Discovery System. While most operational parameters are managed through the `config.yaml` file (see `docs/data-models.md` for its schema), environment variables are primarily used for sensitive information (like API keys), overriding specific logging configurations, or setting a general application environment context.

## 2. Configuration Loading Mechanism

-   **Primary Configuration:** The application primarily loads its configuration from a `config.yaml` file, as specified by the user via a CLI argument (e.g., `--config-file path/to/config.yaml`). Pydantic models are used to parse and validate this file.
-   **Environment Variable Loading:**
    *   Environment variables are accessed directly using `os.environ.get()`.
    *   For local development, a `.env` file can be used to set these variables. This file should be added to `.gitignore` and not committed to the repository. The `python-dotenv` library can be used to automatically load variables from `.env` at application startup.
-   **Precedence:**
    *   Environment variables, when set, can override default values or provide sensitive data not suitable for `config.yaml`.
    *   Specific configurations within `config.yaml` (e.g., `logging_level`) might take precedence over a general environment variable if the application logic is designed that way (e.g., `config.yaml` explicitly sets log level, overriding `APP_LOG_LEVEL` env var). This should be clearly documented if such overrides exist. For this project, `config.yaml` settings for items like `logging_level` are generally considered the primary source if specified there.

## 3. Environment Variables

The following table lists the environment variables recognized by the application:

| Variable Name        | Description                                                                 | Example / Default Value                                  | Required? (Yes/No) | Sensitive? (Yes/No) |
| :------------------- | :-------------------------------------------------------------------------- | :------------------------------------------------------- | :----------------- | :------------------ |
| `APP_ENV`            | Specifies the application environment (e.g., development, test, production). Can influence logging behavior or feature flags if implemented. | `development` / `production` (Default: `development`)    | No                 | No                  |
| `APP_LOG_LEVEL`      | Overrides the logging level set in `config.yaml`. Useful for quick debugging. | `DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL`      | No                 | No                  |
| `YFINANCE_API_KEY`   | API Key for Yahoo Finance if using premium features or a specific data provider that requires it via yfinance. (Currently, standard yfinance usage does not require a key). | `your_api_key_here`                                      | No                 | Yes                 |
| `CACHE_DB_PATH`      | Overrides the default path for the SQLite cache database. Useful if the default location in `config.yaml` is not writable or suitable for the environment. | `/custom/path/to/market_data.sqlite` (Default: `data/cache/market_data.sqlite`) | No                 | No                  |
| `NO_COLOR`           | If set (to any value), disables colored output in the console logs/messages. Useful for CI environments or log files that don't support ANSI color codes. | `1` or `true`                                            | No                 | No                  |
| `PYTHONWARNINGS`     | Standard Python environment variable to control warning behavior (e.g., `ignore`, `default`, `error`). | `ignore`                                                 | No                 | No                  |

## 4. Notes

-   **Secrets Management:**
    *   Sensitive variables like `YFINANCE_API_KEY` must **never** be hardcoded into the source code or committed to `config.yaml`.
    *   For local development, use a `.env` file (added to `.gitignore`).
    *   In production or CI/CD environments (future scope), secrets should be injected securely (e.g., via GitHub Actions secrets, HashiCorp Vault, AWS Secrets Manager).
-   **`.env.example` File:**
    *   An `.env.example` file should be maintained in the root of the repository. This file will list all possible environment variables with placeholder or default values, serving as a template for developers. It should **not** contain any actual secrets.
    ```plaintext
    # .env.example
    APP_ENV=development
    APP_LOG_LEVEL=INFO
    # YFINANCE_API_KEY=your_optional_api_key_here
    # CACHE_DB_PATH=./data/cache/market_data.sqlite
    # NO_COLOR=
    ```
-   **Validation:**
    *   The application should ideally perform a basic check for the presence of required environment variables if any were strictly required (though none are strictly required for MVP).
    *   For optional variables like `APP_LOG_LEVEL`, the application should gracefully fall back to defaults if the variable is not set or contains an invalid value (e.g., log a warning and use the default log level).
-   **Relationship with `config.yaml`:**
    *   `config.yaml` is the primary source for most application settings, especially those related to the trading strategy discovery logic, data sources, feature engineering, GA parameters, backtesting, and reporting.
    *   Environment variables are for settings that are external to the core application logic, are sensitive, or need to vary between deployment environments without altering the committed `config.yaml`.
-   **Integrate with initial setup:** Ensure environment variables are part of the automated initial setup process, including scripts for quick configuration during spike phases.
-   **Support for spike planning and early testing:** Include validation of environment variables in early testing phases to ensure correct setup for high-risk components like GA and backtesting, with clear instructions in the project's setup documentation.

## 5. Change Log

| Change        | Date       | Version | Description                                                     | Author         |
| ------------- | ---------- | ------- | --------------------------------------------------------------- | -------------- |
| Initial Draft | 2025-05-14 | 0.1     | Basic list of potential environment variables.                  | User/AI        |
| Revision 1    | 2025-05-15 | 0.2     | Aligned with template, clarified role vs config.yaml, added details. | Gemini 2.5 Pro |