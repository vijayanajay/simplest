# Adaptive Automated Trading Strategy Discovery System Project Structure

## 1. Overview

This document outlines the standardized directory and file structure for the Adaptive Automated Trading Strategy Discovery System. A consistent structure is crucial for maintainability, ease of navigation, and collaboration, especially when involving AI agents in development.

## 2. Project Directory Structure Diagram

```plaintext
adaptive-trading-system/
├── .github/                    # GitHub specific files
│   └── workflows/              # GitHub Actions CI/CD workflows
│       └── main.yml            # Main CI pipeline (lint, test, type-check)
├── .vscode/                    # VSCode editor settings (optional, for consistency)
│   └── settings.json           # e.g., Python interpreter, linter, formatter settings
├── config/                     # Example and user configuration files
│   ├── default_config.yaml     # A default, complete configuration file
│   └── user_config_example.yaml # An example for users to copy and customize
├── data/                       # Local data storage (often git-ignored, or contains samples)
│   ├── cache/                  # For SQLite database, other cached items
│   │   └── market_data.sqlite  # Example cache DB name
│   ├── raw_data_samples/       # Sample raw input data (if any, for testing)
│   └── interim_data/           # Intermediate data files during processing (if any)
├── docs/                       # Project documentation
│   ├── architecture.md
│   ├── coding-standards.md
│   ├── data-models.md
│   ├── environment-vars.md
│   ├── prd.md
│   ├── project_brief.md
│   ├── project-structure.md
│   ├── sample_report_template.md # Template for what a report might look like
│   ├── tech-stack.md
│   └── testing-strategy.md
│   └── api-reference.md        # (To be created)
├── notebooks/                  # Jupyter notebooks for exploration, analysis, visualization (optional)
│   ├── 01_data_exploration.ipynb
│   └── 02_strategy_analysis.ipynb
├── reports/                    # Default output directory for generated reports (git-ignored)
│   └── {run_id}/               # Reports for a specific run
│       ├── report.html
│       ├── report.md
│       └── summary_metrics.csv
├── scripts/                    # Utility and helper scripts
│   ├── setup_env.sh            # Script for setting up development environment
│   ├── run_pipeline.sh         # Example script to run the main application
│   └── manage_data.py          # Scripts for data management tasks (e.g., clearing cache)
├── src/                        # Main application source code
│   ├── adaptive_trading_system/ # The core Python package
│   │   ├── __init__.py
│   │   ├── cli/                # Command Line Interface logic (Typer/Click)
│   │   │   ├── __init__.py
│   │   │   └── commands.py     # CLI command definitions
│   │   ├── common/             # Shared utilities, types, constants, base classes
│   │   │   ├── __init__.py
│   │   │   ├── data_models.py  # Core Pydantic models (or link to docs/data-models.md)
│   │   │   ├── exceptions.py   # Custom exception classes
│   │   │   └── utils.py        # General utility functions
│   │   ├── components/         # Core functional components of the system
│   │   │   ├── __init__.py
│   │   │   ├── data_fetcher.py # Module for fetching market data
│   │   │   ├── feature_factory.py# Module for feature engineering
│   │   │   ├── strategy_optimizer.py # GA implementation
│   │   │   ├── strategy_backtester.py # Backtesting engine
│   │   │   ├── strategy_analyzer.py # Analysis of backtest results
│   │   │   └── reporter.py       # Report generation logic
│   │   ├── config/             # Configuration loading and validation logic
│   │   │   ├── __init__.py
│   │   │   └── settings.py     # Pydantic models for config.yaml parsing
│   │   └── main.py             # Main application entry point (invoked by CLI)
│   └── __init__.py             # Makes 'src' a discoverable namespace package (optional)
├── state/                      # Persistent state files (e.g., GA checkpoints, git-ignored)
│   └── ga_checkpoints/         # Genetic Algorithm checkpoints
│       └── gen_10.pkl
├── tests/                      # Automated tests
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures and configuration
│   ├── unit/                   # Unit tests (mirroring src structure)
│   │   ├── __init__.py
│   │   ├── common/
│   │   │   └── test_utils.py
│   │   └── components/
│   │       └── test_data_fetcher.py
│   ├── integration/            # Integration tests
│   │   ├── __init__.py
│   │   └── test_pipeline_flow.py
│   └── e2e/                    # End-to-end tests (e.g., CLI interaction)
│       ├── __init__.py
│       └── test_cli_commands.py
│       └── test_data/          # Sample data for E2E tests
├── .env.example                # Example environment variables file
├── .gitignore                  # Specifies intentionally untracked files that Git should ignore
├── LICENSE                     # Project license file (e.g., MIT, Apache 2.0)
├── poetry.lock                 # Poetry lock file for reproducible dependencies
├── pyproject.toml              # Project metadata, dependencies (Poetry), tool configurations (Black, MyPy, isort)
├── README.md                   # Project overview, setup, and usage instructions
└── tox.ini                     # tox configuration for testing in multiple environments (optional)
```

## 3. Key Directory & File Descriptions

-   **`.github/workflows/`**: Contains CI/CD pipeline configurations for GitHub Actions (e.g., running linters, tests, type checkers on pushes/PRs).
-   **`config/`**: Holds example configuration files (`default_config.yaml`, `user_config_example.yaml`). Users will typically copy an example and modify it for their runs.
-   **`data/`**: Intended for local data storage.
    -   `cache/`: Stores cached data like downloaded market prices in an SQLite database to speed up subsequent runs. Typically git-ignored.
    -   `raw_data_samples/`: Can hold small, anonymized samples of raw data if needed for testing or demonstration.
-   **`docs/`**: Contains all project documentation, including this file, PRD, architecture design, coding standards, data models, etc.
-   **`notebooks/`**: Jupyter notebooks for experimental work, data analysis, and visualization. Useful for research and development phases but not part of the core application.
-   **`reports/`**: Default output directory for generated strategy reports. This directory should be in `.gitignore`. Each run might create a subdirectory named with a unique `run_id`.
-   **`scripts/`**: Utility scripts for various tasks like environment setup, data management, or running predefined analysis tasks.
-   **`src/adaptive_trading_system/`**: The main Python source code for the application, structured as an installable package.
    -   `cli/`: Handles command-line interface parsing and command definitions using Typer/Click.
    -   `common/`: Shared utilities, base classes, custom exceptions, and core Pydantic data models used across multiple components.
    -   `components/`: Contains the core logic for each distinct functional part of the system (Data Fetcher, Feature Factory, Strategy Optimizer, Backtester, Analyzer, Reporter). Each component should be a well-defined module.
    -   `config/`: Logic related to loading, parsing, and validating the `config.yaml` file using Pydantic settings models.
    -   `main.py`: The primary entry point of the application, typically invoked by the CLI script.
-   **`state/`**: Stores persistent state information that is not suitable for version control but needs to survive between application runs, such as Genetic Algorithm checkpoints. Should be in `.gitignore`.
-   **`tests/`**: Contains all automated tests.
    -   `unit/`: Unit tests for individual modules and functions, isolated from external dependencies. Structure often mirrors `src/`.
    -   `integration/`: Tests interactions between multiple components of the system.
    -   `e2e/`: End-to-end tests that simulate user interaction with the CLI and verify the overall system behavior.
    -   `conftest.py`: Common Pytest fixtures and hooks.
-   **`.env.example`**: Template for environment variables. Developers copy this to `.env` (git-ignored) for local configuration.
-   **`.gitignore`**: Specifies files and directories that Git should ignore (e.g., `__pycache__/`, `*.pyc`, `.env`, `build/`, `dist/`, `reports/`, `data/cache/`, `state/`).
-   **`LICENSE`**: Contains the full text of the project's license.
-   **`poetry.lock`**: Auto-generated by Poetry, ensures deterministic builds by locking dependency versions. **Must be committed.**
-   **`pyproject.toml`**: Defines project metadata, dependencies for Poetry, and configurations for tools like Black, MyPy, isort, and Flake8.
-   **`README.md`**: Top-level project overview, instructions for setup, installation, basic usage, and contribution guidelines.

## 4. Notes

-   **Modularity:** The `src/adaptive_trading_system/components/` directory is key to maintaining a modular design. Each component should have well-defined responsibilities and interfaces.
-   **Python Package:** The code within `src/adaptive_trading_system/` is structured as a Python package, allowing it to be installed (e.g., using `poetry install`) and imported cleanly.
-   **Configuration vs. Code:** Keep configurable parameters in `config.yaml` and avoid hardcoding them in the source code.
-   **Git Ignore:** Ensure that generated files, sensitive information, environment-specific files, and large data files are appropriately listed in `.gitignore`.

## 5. Change Log

| Change        | Date       | Version | Description                                                                 | Author         |
| ------------- | ---------- | ------- | --------------------------------------------------------------------------- | -------------- |
| Initial Draft | 2025-05-14 | 0.1     | Basic directory structure outline.                                          | User/AI        |
| Revision 1    | 2025-05-15 | 0.2     | Expanded with detailed diagram, Python project conventions, and descriptions. | Gemini 2.5 Pro |
