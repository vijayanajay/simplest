# Project Structure for Adaptive Automated Trading Strategy Discovery System

## Overview

This document describes the organization of the project's directory and file structure, promoting modularity, maintainability, and scalability.

## High-Level Directory Structure

- **docs/**: Contains all documentation files, including PRD, architecture, tech stack, and other guides.
- **src/**: Houses the core application code, divided into modules for each component.
- **tests/**: Includes unit and integration tests.
- **scripts/**: Scripts for utilities, data processing, and automation.
- **config/**: Configuration files like config.yaml for settings.

## Detailed Breakdown

- **src/**
  - **feature_factory.py**: Fetches data and generates features.
  - **strategy_optimizer.py**: Implements the GA logic.
  - **strategy_backtester.py**: Handles backtesting routines.
  - **strategy_analyzer.py**: Generates reports and analytics.
  - **utils/**: Shared utilities like data caching and logging.

- **tests/**
  - **test_feature_factory.py**
  - **test_strategy_optimizer.py**
  - Etc., following a similar naming convention.

- **scripts/**
  - **run.py**: Entry point for executing the system.
  - **data_fetcher.py**: Standalone script for data retrieval.

- **config/**
  - **config.yaml**: Defines parameters for GA, data sources, and backtesting settings.

## Rationale

- Modular structure separates concerns, making it easier to maintain and extend.
- Follows standard Python project layouts for familiarity.

## Change Log

| Change        | Date       | Version | Description                  | Author         |
| ------------- | ---------- | ------- | ---------------------------- | -------------- |
| Initial draft | 2025-05-15 | 0.1     | Initial project structure    | AI Architect   | 