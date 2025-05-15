# Adaptive Automated Trading Strategy Discovery System

This system discovers and optimizes trading strategies for Indian NSE stocks using genetic algorithms. It performs feature engineering, strategy optimization, backtesting, and result analysis.

## Features

- Configure the system via YAML config files
- Discover trading strategies using genetic algorithms
- Backtest strategies with historical data
- Generate comprehensive reports

## System Requirements

- Python 3.10 or higher
- Windows 10 or 11

## Installation

### Option 1: Install from Source using Poetry (Recommended)

Poetry provides a clean, isolated environment for the application:

1. **Install Python 3.10+**: Download and install from [python.org](https://www.python.org/downloads/)

2. **Install Poetry**:
   ```
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
   ```

3. **Clone the repository**:
   ```
   git clone <repository-url>
   cd adaptive-trading-system
   ```

4. **Install dependencies**:
   ```
   poetry install
   ```

5. **Activate the environment**:
   ```
   poetry shell
   ```

### Option 2: Install from Source using pip and venv

1. **Install Python 3.10+**: Download and install from [python.org](https://www.python.org/downloads/)

2. **Clone the repository**:
   ```
   git clone <repository-url>
   cd adaptive-trading-system
   ```

3. **Create and activate a virtual environment**:
   ```
   python -m venv venv
   .\venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```
   pip install -e .
   ```

## Configuration

The system is configured through YAML files. Two example files are provided:

- `config/default_config.yaml`: Contains all possible settings with default values
- `config/user_config_example.yaml`: A minimal example for customization

To create your own configuration:

1. Copy `config/user_config_example.yaml` to a new file:
   ```
   copy config\user_config_example.yaml my_config.yaml
   ```

2. Edit the file to customize stock symbols, date ranges, and other parameters.

### Required Configuration

At minimum, your configuration file must include:

```yaml
data_source:
  symbols:
    - SYMBOL1.NS
    - SYMBOL2.NS
  start_date: 2022-01-01
  end_date: 2022-12-31
```

## Usage

### Running the Application

With Poetry:
```
poetry run tradefinder discover --config-file my_config.yaml
```

With activated venv:
```
tradefinder discover --config-file my_config.yaml
```

### Command Line Options

```
tradefinder discover --config-file CONFIG_FILE [--log-level LEVEL] [--verbose]
tradefinder version
```

Options:
- `--config-file, -c`: Path to the configuration file (required)
- `--log-level, -l`: Override logging level from config (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--verbose, -v`: Enable verbose output

## Environment Variables

You can customize certain aspects of the system with environment variables. Create a `.env` file in the project root with any of these settings:

```
APP_ENV=development
APP_LOG_LEVEL=INFO
YFINANCE_API_KEY=your_api_key_here  # If using premium features
CACHE_DB_PATH=./data/cache/market_data.sqlite
```

## Project Structure

The project follows a modular design:

- `src/adaptive_trading_system/`: Main package
  - `cli/`: Command line interface
  - `config/`: Configuration loading and validation
  - `common/`: Utilities and shared code
  - `components/`: Core pipeline components
- `config/`: Example configuration files
- `tests/`: Automated tests

## Development

### Running Tests

```
pytest
```

### Code Formatting

```
black src tests
isort src tests
```

## License

[Your chosen license] 