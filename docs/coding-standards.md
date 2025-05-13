# Adaptive Automated Trading Strategy Discovery System Coding Standards and Patterns

## 1. Overview

This document outlines the coding standards, design patterns, and best practices to be followed during the development of the Adaptive Automated Trading Strategy Discovery System. Adherence to these standards will ensure code consistency, maintainability, readability, and quality. This document is intended for all developers, including AI agents, contributing to the project.

## 2. Architectural / Design Patterns Adopted

The system employs several key architectural patterns to ensure modularity, maintainability, and clarity, as detailed in the `docs/architecture.md`.

-   **Pattern 1: Data Pipeline Architecture**
    -   **Description:** A sequential processing pipeline where data flows from raw stock data ingestion, feature engineering, strategy optimization (via Genetic Algorithms), backtesting, analysis, and finally to reporting.
    -   **Rationale/Reference:** This allows for modular development of distinct components, clear interfaces and data contracts between stages, and easier unit and integration testing. (See `docs/architecture.md` - "Key Architectural Decisions & Patterns")
-   **Pattern 2: Genetic Algorithm (GA) for Strategy Evolution**
    -   **Description:** Core optimization technique using GAs to discover and evolve trading strategies based on a defined fitness function and genetic operators (selection, crossover, mutation).
    -   **Rationale/Reference:** GAs provide an efficient method to explore a vast search space of potential trading rules and adapt strategies based on multiple success criteria. (See `docs/architecture.md` - "Key Architectural Decisions & Patterns", PRD Capability 1)
-   **Pattern 3: Configuration-Driven System**
    -   **Description:** System behavior, including data sources, feature sets, GA parameters, backtesting settings, and reporting options, is primarily controlled through external configuration files (`config.yaml`).
    -   **Rationale/Reference:** Promotes flexibility, reproducibility of experiments, and allows users (analysts) to easily customize system runs without code changes. (See `docs/architecture.md` - "Key Architectural Decisions & Patterns", PRD User Stories & NFRs)
-   **Pattern 4: Modular Component Design**
    -   **Description:** The system is broken down into distinct, loosely coupled components (e.g., Data Fetcher, Feature Factory, Strategy Optimizer, Backtester, Analyzer, Reporter).
    -   **Rationale/Reference:** Enhances maintainability, testability, and allows for independent development and potential reuse of components. (See `docs/architecture.md` - "Component View")
-   **Pattern 5: Pydantic for Data Validation and Settings Management**
    -   **Description:** Pydantic models are used for defining and validating data structures, configuration settings, and API contracts (internal data flow).
    -   **Rationale/Reference:** Ensures data integrity, provides clear data schemas, and offers automatic parsing and validation of configuration files. (PRD NFRs)

## 3. Coding Standards

-   **Primary Language(s):** Python
    -   **Version:** 3.10+ (as specified in `docs/tech-stack.md` and to support modern type hinting and features).
-   **Primary Runtime(s):** Standard Python interpreter.
    -   **Target OS (MVP):** Windows 10/11.
-   **Style Guide & Linter:**
    *   **Style Guide:** PEP 8 (Strict adherence).
    *   **Formatter:** Black (with default settings).
        -   _Configuration:_ `pyproject.toml` will contain Black's configuration.
    *   **Linter:** Flake8 (with plugins like `flake8-bugbear`, `flake8-comprehensions`).
        -   _Configuration:_ `.flake8` file in the project root.
    *   **Import Sorting:** isort.
        -   _Configuration:_ `pyproject.toml` (compatible with Black).
    *   **Pre-commit Hooks:** Use `pre-commit` framework to automatically run Black, isort, Flake8, and MyPy on staged files before each commit.
-   **Naming Conventions:**
    *   Variables: `snake_case` (e.g., `closing_price`, `moving_average`)
    *   Functions: `snake_case` (e.g., `calculate_rsi`, `fetch_stock_data`)
    *   Methods: `snake_case` (e.g., `my_object.process_data()`)
    *   Classes: `PascalCase` (e.g., `TradingStrategy`, `FeatureFactory`)
    *   Type Aliases: `PascalCase` (e.g., `PriceData = Dict[str, float]`)
    *   Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_HOLDING_PERIOD = 20`)
    *   Modules/Packages: `snake_case` (e.g., `feature_factory`, `strategy_optimizer`)
    *   Files: `snake_case.py` (e.g., `data_fetcher.py`)
-   **File Structure:** Adhere to the layout defined in `docs/project-structure.md`.
-   **Asynchronous Operations:**
    *   For I/O-bound operations like API calls to `yfinance`, `asyncio` with `aiohttp` (or `httpx`) should be used to improve concurrency and performance, especially when fetching data for multiple symbols.
    *   CPU-bound tasks within the GA or extensive backtesting loops should leverage the `multiprocessing` module for parallelism, as outlined in PRD NFRs.
    *   Synchronous code is acceptable for simpler sequences or where async/multiprocessing adds undue complexity for the MVP, but profile before optimizing.
-   **Type Safety:**
    *   **Type Hints:** Python type hints (PEP 484) must be used for all function signatures (arguments and return types), class attributes, and complex variable assignments.
    *   **Type Checking:** MyPy will be used for static type checking.
        -   _Configuration:_ `mypy.ini` or `pyproject.toml` with strict settings enabled (e.g., `disallow_untyped_defs = True`, `warn_return_any = True`).
        -   MyPy checks will be integrated into the CI pipeline.
    *   _Type Definitions:_ Core data structures and Pydantic models will be defined as per `docs/data-models.md` and typically reside in `src/common/data_models.py` or within specific component packages if tightly coupled.
-   **Comments & Documentation:**
    *   **Docstrings:** Use Google Python Style Docstrings (parsable by Sphinx with Napoleon extension) for all public modules, functions, classes, and methods. Docstrings must explain the purpose, arguments (Args:), return values (Returns:), and any exceptions raised (Raises:).
    *   **Inline Comments:** Use inline comments (`#`) to explain complex, non-obvious, or critical sections of code. Focus on *why* something is done, not just *what* is done.
    *   **`TODO` / `FIXME` Comments:** Use `TODO:` for planned enhancements and `FIXME:` for known issues needing attention. Include a brief explanation.
    *   **READMEs:** Maintain `README.md` files within sub-packages/modules if they represent significant, self-contained units of functionality, explaining their role and usage.
-   **Dependency Management:**
    *   **Tool:** Poetry (using `pyproject.toml` for dependency specification and `poetry.lock` for locking). A `requirements.txt` can be exported for environments where Poetry is not used. (PRD NFRs)
    *   **Policy:**
        *   Minimize dependencies. Each new dependency must be justified.
        *   Prefer well-maintained and reputable libraries.
        *   Regularly review and update dependencies using `poetry update`.
        *   Pin dependencies to specific compatible versions in `pyproject.toml` to ensure reproducible builds.

## 4. Error Handling Strategy

-   **General Approach:**
    *   Use exceptions for signaling and handling errors. Avoid returning error codes or `None` to indicate failure where an exception is more appropriate.
    *   Define custom, specific exception classes inheriting from base Python exceptions (e.g., `ValueError`, `IOError`, `RuntimeError`) for application-specific error conditions. Examples: `DataFetchingError`, `StrategyValidationError`, `ConfigurationError`. These should be defined in a common exceptions module (e.g., `src/common/exceptions.py`).
-   **Logging:**
    *   **Library/Method:** Python `logging` module, configured at application startup.
    *   **Format:** Structured logging in JSON format. Each log record should include at least: `timestamp`, `level`, `module`, `function`, `lineno`, `message`, and any relevant contextual data (e.g., `run_id`, `stock_symbol`, `strategy_id`). (PRD NFRs)
    *   **Levels:**
        *   `DEBUG`: Detailed information, typically of interest only when diagnosing problems.
        *   `INFO`: Confirmation that things are working as expected, routine operations.
        *   `WARNING`: An indication that something unexpected happened, or indicative of some problem in the near future (e.g., ‘disk space low’). The software is still working as expected.
        *   `ERROR`: Due to a more serious problem, the software has not been able to perform some function.
        *   `CRITICAL`: A serious error, indicating that the program itself may be unable to continue running.
    *   **Context:** Include relevant contextual information in logs using `logging.LoggerAdapter` or by passing `extra` dict to logging calls.
    *   **Output:** Log to both console (for interactive runs) and a rotating log file (e.g., `app.log`) for persistent records. Log file paths should be configurable.
-   **Specific Handling Patterns:**
    *   **External API Calls (e.g., `yfinance`):**
        *   Wrap API calls in `try-except` blocks to catch common exceptions (e.g., `requests.exceptions.RequestException`, `ConnectionError`, specific API client errors).
        *   Implement a retry mechanism with exponential backoff and jitter for transient network or API rate limit issues (as per PRD for `yfinance` wrapper).
        *   Log detailed error information, including the endpoint, parameters, and the error received.
        *   If data from an external API is critical and unrecoverable, raise a specific custom exception (e.g., `ExternalAPIFailureError`).
    *   **Input Validation:**
        *   **Configuration Files (`config.yaml`):** Validate rigorously using Pydantic models upon loading. If validation fails, raise a `ConfigurationError` with a clear, user-friendly message detailing the specific validation issue(s) and terminate gracefully. (PRD UX requirements)
        *   **Function/Method Arguments:** Use type hints for static analysis. For runtime validation of critical inputs, Pydantic models or assertions can be used, especially at component boundaries.
        *   **CLI Inputs:** Leverage the validation capabilities of the chosen CLI framework (e.g., Typer/Click).
    *   **File Operations:**
        *   Wrap file I/O in `try-except-finally` blocks to handle `IOError` and ensure files are closed properly.
        *   Validate file paths and permissions before attempting operations.
    *   **Graceful Degradation vs. Critical Failure:**
        *   **Graceful Degradation:** For non-critical errors (e.g., failure to process one stock in a large batch, a non-essential feature failing), log the error, notify the user if appropriate, and attempt to continue with the remaining work. The system should clearly report partial successes/failures.
        *   **Critical Failure:** For errors that prevent the core functionality from proceeding (e.g., invalid core configuration, inability to write to essential output directories, critical data source unavailable), log the error, provide a clear message to the user, and terminate the program with a non-zero exit code.

## 5. Security Best Practices

-   **Input Sanitization/Validation:**
    *   All external inputs, including `config.yaml` content, CLI arguments, and data from `yfinance`, must be treated as untrusted and validated.
    *   Use Pydantic for validating the structure and types of configuration data.
    *   Be cautious with file paths read from configuration; normalize paths and ensure they are restricted to expected base directories to prevent directory traversal attacks.
-   **Secrets Management:**
    *   **API Keys (e.g., `YF_API_KEY` if used in the future):** Must not be hardcoded in the source code or committed to version control.
    *   For local development (MVP), API keys and other secrets should be managed via environment variables, loaded using a library like `python-dotenv` from a `.env` file (which is git-ignored).
    *   The `config.yaml` file should not contain sensitive secrets. It can reference environment variable names if needed.
    *   Refer to `docs/environment-vars.md` for details on environment variable usage and management.
-   **Dependency Security:**
    *   **Automated Scanning:** Use tools like `safety` (integrated with Poetry) or GitHub Dependabot to scan for known vulnerabilities in dependencies. (PRD NFRs)
    *   **Regular Updates:** Keep dependencies up-to-date by regularly running `poetry update` and testing thoroughly.
    *   **Lock Files:** Always commit `poetry.lock` to ensure reproducible builds with vetted dependency versions.
-   **Authentication/Authorization Checks:**
    *   Currently not applicable for the MVP's local execution model, which does not involve user accounts or remote access.
    *   If future versions introduce web interfaces or multi-user capabilities, robust authentication (e.g., OAuth2, JWT) and authorization mechanisms must be implemented.
-   **File System Access:**
    *   Write outputs only to designated, user-configurable output directories.
    *   Avoid constructing file paths by directly concatenating unvalidated user inputs. Use `os.path.join` and ensure paths are canonicalized and validated.
-   **Code Execution:**
    *   Avoid using `eval()`, `exec()`, or `pickle`/`dill` with untrusted data, as these can lead to arbitrary code execution vulnerabilities. If deserialization is needed for GA state, ensure the source is trusted or use safer serialization formats like JSON for simpler data if possible. For complex objects like GA individuals, if `pickle` is used for checkpointing, ensure checkpoints are from trusted sources or internal processes only.
-   **Error Reporting:**
    *   Ensure that detailed internal error messages and stack traces do not inadvertently leak into user-facing reports or console outputs if they contain sensitive information. Log detailed errors internally for debugging, but present summarized, user-friendly errors externally.
-   **Data Handling:**
    *   Be mindful of any PII if user-specific data were ever to be introduced (not in current scope).
    *   Ensure temporary files are handled securely and cleaned up properly.

## 6. Tools and Enforcement

-   **Type Checker:** MyPy.
-   **CI/CD Pipeline:** GitHub Actions will be configured to run all checks (linting, formatting, type checking, unit tests, integration tests) on every push and pull request. Build failures will block merges.
-   **Code Reviews:** All code contributions (including from AI agents) must be peer-reviewed before merging. Reviews should focus on adherence to these standards, correctness, performance, and maintainability.

## 7. Change Log

| Change        | Date       | Version | Description                                       | Author         |
| ------------- | ---------- | ------- | ------------------------------------------------- | -------------- |
| Initial Draft | 2025-05-14 | 0.1     | First draft based on project brief.               | User/AI        |
| Revision 1    | 2025-05-15 | 0.2     | Expanded based on template and PRD.               | Gemini 2.5 Pro |