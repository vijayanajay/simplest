# Environment Variables for Adaptive Automated Trading Strategy Discovery System

## Overview

This document lists and describes the environment variables used in the system to manage configuration, secrets, and runtime settings, ensuring security and flexibility.

## Key Environment Variables

- **YF_API_KEY**: Optional API key for yfinance if rate limiting is an issue; defaults to public access if not set.
- **GA_POPULATION_SIZE**: Integer value for the genetic algorithm population size (default: 100).
- **GA_GENERATIONS**: Number of generations to run the GA (default: 50).
- **DATA_CACHE_PATH**: Path to the local cache directory for historical data (default: './cache/data_cache.json').
- **TRANSACTION_COST**: Float representing the transaction cost per trade (default: 0.001 for 0.1%).
- **SLIPPAGE_FACTOR**: Float for slippage adjustment in backtesting (default: 0.005).
- **STOCK_LIST**: Comma-separated list of NSE stock symbols to evaluate (e.g., 'INFY,RELIANCE,TCS').
- **LOG_LEVEL**: Logging verbosity level (e.g., 'DEBUG', 'INFO', 'ERROR'; default: 'INFO').

## Usage Guidelines

- Set these variables in a .env file or via system environment for security.
- Use a library like python-dotenv to load them in the application.
- Avoid hardcoding sensitive values; always use environment variables for keys and paths.

## Rationale

- Promotes separation of configuration from code, enhancing portability and security.

## Change Log

| Change        | Date       | Version | Description                  | Author         |
| ------------- | ---------- | ------- | ---------------------------- | -------------- |
| Initial draft | 2025-05-15 | 0.1     | Initial environment vars doc | AI Architect   | 