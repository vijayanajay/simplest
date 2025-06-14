"""
Signal Generation and Backtesting Module for MEQSAP.

This module provides signal generation, backtesting execution, and validation
functionality using pandas-ta for technical indicators and vectorbt for 
high-performance backtesting operations.
"""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import date
import warnings
import logging

# Set up a logger for debugging
logger = logging.getLogger(__name__)

# Suppress pandas_ta pkg_resources deprecation warning
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API", category=UserWarning)

try:
    import pandas_ta as ta
except ImportError:
    raise ImportError("pandas-ta is required. Install with: pip install pandas-ta")

try:
    import vectorbt as vbt
except ImportError:
    raise ImportError("vectorbt is required. Install with: pip install vectorbt")

from pydantic import BaseModel, Field

try:
    # For direct imports when used as a package
    from .config import StrategyConfig, BaseStrategyParams
    from .exceptions import BacktestError
    from .indicators_core.registry import get_indicator_registry # New import
    # Import indicators_core to trigger indicator registration
    from . import indicators_core
except ImportError: # For imports when running tests or if structure changes
    from src.meqsap.config import StrategyConfig, BaseStrategyParams # type: ignore
    from src.meqsap.exceptions import BacktestError # type: ignore


class BacktestResult(BaseModel):
    """Results from a backtest execution."""
    
    total_return: float = Field(..., description="Total return percentage")
    annualized_return: float = Field(..., description="Annualized return percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")
    total_trades: int = Field(..., description="Total number of trades")
    win_rate: float = Field(..., description="Percentage of winning trades")
    profit_factor: float = Field(..., description="Ratio of gross profit to gross loss")
    final_value: float = Field(..., description="Final portfolio value")
    
    # Additional metrics from vectorbt
    volatility: float = Field(..., description="Annualized volatility")
    calmar_ratio: float = Field(..., description="Calmar ratio (annual return / max drawdown)")
    
    # Trade details
    trade_details: List[Dict[str, Any]] = Field(default_factory=list, description="Individual trade details")
    portfolio_value_series: Dict[str, float] = Field(default_factory=dict, description="Daily portfolio values")
    
    # Trade duration statistics
    avg_trade_duration_days: Optional[float] = Field(None, description="Average trade duration in days")
    pct_trades_in_target_hold_period: Optional[float] = Field(None, description="Percentage of trades within target hold period")
    trade_durations_days: Optional[List[int]] = Field(None, description="List of individual trade durations in days")


class VibeCheckResults(BaseModel):
    """Results from strategy validation checks."""
    
    minimum_trades_check: bool = Field(..., description="At least one trade was executed")
    signal_quality_check: bool = Field(..., description="Signal frequency is reasonable")
    data_coverage_check: bool = Field(..., description="Sufficient data for strategy parameters")
    overall_pass: bool = Field(..., description="All vibe checks passed")
    
    # Detailed messages
    check_messages: List[str] = Field(default_factory=list, description="Detailed check messages")


class RobustnessResults(BaseModel):
    """Results from robustness analysis."""
    
    baseline_sharpe: float = Field(..., description="Sharpe ratio from baseline scenario")
    high_fees_sharpe: float = Field(..., description="Sharpe ratio with elevated fees")
    turnover_rate: float = Field(..., description="Portfolio turnover rate")
    
    # Performance degradation metrics
    sharpe_degradation: float = Field(..., description="Percentage degradation in Sharpe ratio")
    return_degradation: float = Field(..., description="Percentage degradation in returns")
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list, description="Strategy recommendations")


class BacktestAnalysisResult(BaseModel):
    """Comprehensive backtest analysis result."""
    
    primary_result: BacktestResult = Field(..., description="Primary backtest results")
    vibe_checks: VibeCheckResults = Field(..., description="Strategy validation results")
    robustness_checks: RobustnessResults = Field(..., description="Robustness analysis results")
    
    # Configuration used
    strategy_config: Dict[str, Any] = Field(..., description="Strategy configuration used")


class StrategySignalGenerator:
    """Factory for generating trading signals based on strategy type."""
    
    def __init__(self, indicator_registry=None):
        """Initialize with an optional indicator registry."""
        self.indicator_registry = indicator_registry or get_indicator_registry()
    
    @staticmethod
    def generate_signals(
        data: pd.DataFrame, 
        strategy_config: StrategyConfig
    ) -> pd.DataFrame:
        """Generate trading signals based on strategy configuration.
        
        Args:
            data: OHLCV market data DataFrame
            strategy_config: Validated strategy configuration
        
        Returns:
            DataFrame with 'entry' and 'exit' boolean columns
        """
        generator_instance = StrategySignalGenerator()
        try:
            # Extract concrete parameters from the strategy config.
            # For optimization, the config object is created with the trial's specific params.
            validated_params_model = strategy_config.validate_strategy_params()
            concrete_params = generator_instance._extract_concrete_params(validated_params_model)            
            if strategy_config.strategy_type == "MovingAverageCrossover":
                return generator_instance._generate_ma_crossover_signals(data, concrete_params)
            elif strategy_config.strategy_type == "BuyAndHold":
                return generator_instance._generate_buy_and_hold_signals(data)
            else:
                raise BacktestError(f"Unsupported strategy type: {strategy_config.strategy_type}")
        except Exception as e:
            logger.error(f"Signal generation failed: {e}")
            raise

    
    def _extract_concrete_params(self, strategy_params_model: BaseStrategyParams) -> Dict[str, Any]:
        """
        Extracts concrete parameter values from a strategy parameters model.
        For complex types (range, choice), it picks a default (e.g., start of range, first choice).
        """
        concrete = {}
        for param_name, param_def in strategy_params_model.model_dump().items(): # Use model_dump for Pydantic v2
            if isinstance(param_def, (int, float, str, bool)):
                concrete[param_name] = param_def
            elif isinstance(param_def, dict): # Handles ParameterRange, ParameterChoices, ParameterValue
                param_type = param_def.get("type")
                if param_type == "value":
                    concrete[param_name] = param_def["value"]
                elif param_type == "choices":
                    concrete[param_name] = param_def["values"][0] # Default to first choice
                elif param_type == "range":
                    concrete[param_name] = param_def["start"] # Default to start of range
                else: # Assume it's a direct value if no type, or could raise error
                    concrete[param_name] = param_def 
            else: # Fallback for simple values not caught by initial isinstance
                concrete[param_name] = param_def
        return concrete    
        
    def _generate_ma_crossover_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """Generate Moving Average Crossover signals."""
        # Extract and validate MA periods with type conversion
        fast_ma_raw = params['fast_ma']
        slow_ma_raw = params['slow_ma']
        
        logger.debug(f"Raw MA periods: fast_ma={fast_ma_raw} (type: {type(fast_ma_raw)}), slow_ma={slow_ma_raw} (type: {type(slow_ma_raw)})")
        
        # Convert to integers and validate
        try:
            fast_ma_period = int(fast_ma_raw)
            slow_ma_period = int(slow_ma_raw)
        except (ValueError, TypeError) as e:
            raise BacktestError(f"MA periods must be convertible to integers: fast_ma={fast_ma_raw}, slow_ma={slow_ma_raw}. Error: {e}")
        
        logger.debug(f"Converted MA periods: fast_ma={fast_ma_period}, slow_ma={slow_ma_period}")
        
        # Validate MA period values
        if fast_ma_period <= 0:
            raise BacktestError(f"Fast MA period must be positive: {fast_ma_period}")
        if slow_ma_period <= 0:
            raise BacktestError(f"Slow MA period must be positive: {slow_ma_period}")
            
        # Validate MA period ordering
        if fast_ma_period >= slow_ma_period:
            raise BacktestError(f"Invalid MA period ordering: fast_ma ({fast_ma_period}) must be less than slow_ma ({slow_ma_period})")
        
        # Check data sufficiency
        if len(data) < slow_ma_period:
            raise BacktestError(f"Insufficient data: need at least {slow_ma_period} bars, got {len(data)}")
        
        # Extract close prices - expects 'close' column after normalization in data.py
        if 'close' not in data.columns:
            raise BacktestError(f"Standardized 'close' column not found in data. Available columns: {list(data.columns)}")
        _close_prices_intermediate: pd.Series | pd.DataFrame
        _close_prices_intermediate = data['close']

        # Ensure _close_prices_intermediate is a Series for pandas-ta
        close_prices_for_ta: pd.Series
        if isinstance(_close_prices_intermediate, pd.DataFrame):
            logger.warning(
                f"Warning: Extracted close prices object is a DataFrame (shape: {_close_prices_intermediate.shape}). "
                f"Attempting to convert to Series."
            )
            if _close_prices_intermediate.shape[1] == 1:
                close_prices_for_ta = _close_prices_intermediate.iloc[:, 0]
                logger.info(f"Successfully converted single-column DataFrame of close prices to Series ('{close_prices_for_ta.name}').")
            else:
                raise BacktestError(
                    f"Extracted close prices object is a DataFrame with multiple columns ({_close_prices_intermediate.columns.tolist()}). "
                    "Expected a Series or a single-column DataFrame."
                )
        elif isinstance(_close_prices_intermediate, pd.Series):
            close_prices_for_ta = _close_prices_intermediate
        else:
            raise BacktestError(f"Extracted close prices object is not a pandas Series or DataFrame. Type: {type(_close_prices_intermediate)}")
 
        # Get SMA indicator from registry
        sma_indicator_cls = self.indicator_registry.get('simple_moving_average')
        if sma_indicator_cls is None:
            raise BacktestError("SimpleMovingAverage indicator not found in registry.")
        
        fast_ma_series = sma_indicator_cls.calculate(close_prices_for_ta, period=fast_ma_period)
        if fast_ma_series is None:
            raise BacktestError(
                f"Failed to calculate Fast MA (period {fast_ma_period}). "
                "The technical indicator calculation returned None. This may be due to an empty, "
                "all-NaN, or non-numeric input price series for the indicator."
            )

        slow_ma_series = sma_indicator_cls.calculate(close_prices_for_ta, period=slow_ma_period)
        if slow_ma_series is None:
            raise BacktestError(
                f"Failed to calculate Slow MA (period {slow_ma_period}). "
                "The technical indicator calculation returned None. This may be due to an empty, "
                "all-NaN, or non-numeric input price series for the indicator."
            )
            
        # Find valid index range where both MAs have non-NaN values
        # This line is now safer due to the checks above.
        valid_mask = fast_ma_series.notna() & slow_ma_series.notna()
        valid_index = data.index[valid_mask]
        
        if not valid_mask.any():
            raise BacktestError("No valid data points after moving average calculation")
        
        # Create signals DataFrame restricted to valid index range
        signals = pd.DataFrame(index=valid_index)
        signals['entry'] = False
        signals['exit'] = False
        
        # Extract valid MA series for signal generation
        fast_ma_valid = fast_ma_series[valid_mask]
        slow_ma_valid = slow_ma_series[valid_mask]
        
        # Generate crossover signals using only valid MA values
        # Entry: Fast MA crosses above Slow MA
        ma_cross_up = (fast_ma_valid > slow_ma_valid) & (fast_ma_valid.shift(1) <= slow_ma_valid.shift(1))
        signals.loc[ma_cross_up, 'entry'] = True
          # Exit: Fast MA crosses below Slow MA  
        ma_cross_down = (fast_ma_valid < slow_ma_valid) & (fast_ma_valid.shift(1) >= slow_ma_valid.shift(1))
        signals.loc[ma_cross_down, 'exit'] = True
        if signals.empty:
            raise BacktestError("No valid signals generated after removing NaN values")
        
        return signals

    def _generate_buy_and_hold_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate Buy & Hold signals: buy on first day, hold forever.
        
        Args:
            data: OHLCV market data DataFrame
            
        Returns:
            DataFrame with 'entry' and 'exit' boolean columns
        """
        # Create signals DataFrame with same index as data
        signals = pd.DataFrame(index=data.index)
        signals['entry'] = False
        signals['exit'] = False
        
        # Entry signal only on first day
        if len(signals) > 0:
            signals.iloc[0, signals.columns.get_loc('entry')] = True
        
        logger.debug(f"Generated Buy & Hold signals: {signals['entry'].sum()} entry signals, {signals['exit'].sum()} exit signals")
        
        return signals


def safe_float(value, default=0.0, metric_name: Optional[str] = None, raise_on_type_error: bool = False):
    """Safely convert a value to float, returning a default if conversion fails."""
    metric_log_name = f" for metric '{metric_name}'" if metric_name else ""
    if value is None:
        logger.warning(f"Value is None{metric_log_name}, using default: {default}")
        return default
    try:
        result = float(value)
        # Check for NaN and infinite values
        if np.isnan(result) or np.isinf(result):
            logger.warning(f"Value '{value}'{metric_log_name} converted to NaN or inf, using default: {default}")
            return default
        return result
    except (ValueError, TypeError) as e:
        log_msg = f"Could not convert '{value}' (type: {type(value).__name__}) to float{metric_log_name}"
        if raise_on_type_error:
            logger.error(f"{log_msg}. Raising BacktestError as it's a critical metric.")
            # Ensure the original exception type and message are preserved for clarity
            if isinstance(e, ValueError):
                raise BacktestError(f"{log_msg}: Invalid value for float conversion ('{value}').") from e
            else: # TypeError
                raise BacktestError(f"{log_msg}: Incorrect type for float conversion (got {type(value).__name__}).") from e
        else:
            logger.warning(f"{log_msg}, using default: {default}")
            return default

def run_backtest(
    prices_data: pd.DataFrame,
    signals_data: pd.DataFrame,
    initial_cash: int = 10000,
    fees: float = 0.001
) -> BacktestResult:
    """Run a backtest with the given price data and signals.

    Args:
        prices_data: OHLCV market data DataFrame. Must include a 'Close' column (case-insensitive check)
                     or be a Series of close prices. Index must be datetime.
        signals_data: DataFrame with 'entry' and 'exit' boolean columns. Index must be datetime and align with prices_data.
        initial_cash: Starting portfolio value (default: 10000).
        fees: Transaction costs as a decimal (default: 0.001 = 0.1%).

    Returns:
        BacktestResult object with performance metrics

    Raises:
        BacktestError: If backtesting execution fails, data is misaligned, or inputs are invalid.
    """
    logger.debug(f"Starting run_backtest with prices_data type: {type(prices_data)}, signals_data type: {type(signals_data)}")

    try:
        # Verify we have the needed data
        if not isinstance(prices_data, (pd.DataFrame, pd.Series)):
            raise BacktestError(f"Price data must be a DataFrame or Series, got {type(prices_data).__name__}")

        if not isinstance(signals_data, (pd.DataFrame, pd.Series)):
            raise BacktestError(f"Signals data must be a DataFrame or Series, got {type(signals_data).__name__}")

        logger.debug(f"Prices data columns: {getattr(prices_data, 'columns', 'No columns (Series)')}")
        logger.debug(f"Signals data columns: {getattr(signals_data, 'columns', 'No columns (Series)')}")

        # Align data and signals
        try:
            common_index = prices_data.index.intersection(signals_data.index)
            logger.debug(f"Common index length: {len(common_index)}")
        except AttributeError as e:
            raise BacktestError(f"Data alignment failed - ensure both prices and signals have proper index: {str(e)}")

        if len(common_index) == 0:
            raise BacktestError("No common dates between data and signals")

        aligned_data = prices_data.loc[common_index]
        aligned_signals = signals_data.loc[common_index]

        logger.debug(f"Aligned data shape: {aligned_data.shape}")
        logger.debug(f"Aligned signals shape: {aligned_signals.shape}")
        
        # Extract close prices for vectorbt - expects 'close' column after normalization in data.py
        if isinstance(aligned_data, pd.DataFrame):
            logger.debug(f"Processing DataFrame with columns: {aligned_data.columns.tolist()}")
            if 'close' not in aligned_data.columns:
                raise BacktestError(f"Standardized 'close' column not found in aligned_data. Available columns: {list(aligned_data.columns)}")
            close_prices = aligned_data['close']
            logger.debug("Using standardized 'close' column")
        else:
            # Assume it's already a Series of close prices
            close_prices = aligned_data
            logger.debug("Using aligned_data as Series directly (assumed to be close prices)")
        
        logger.debug(f"Close prices type: {type(close_prices)}")
        logger.debug(f"Close prices shape: {close_prices.shape}")
        
        # Convert signals to vectorbt format
        if isinstance(aligned_signals, pd.DataFrame):
            logger.debug(f"Processing signals DataFrame with columns: {aligned_signals.columns.tolist()}")
            if 'entry' in aligned_signals.columns:
                entries = aligned_signals['entry']
                logger.debug("Using 'entry' column")
            else:
                entries = aligned_signals.iloc[:, 0]  # First column
                logger.debug("Using first column as entries")
            
            if 'exit' in aligned_signals.columns:
                exits = aligned_signals['exit']
                logger.debug("Using 'exit' column")
            else:
                exits = pd.Series(False, index=entries.index)
                logger.debug("Created empty exits Series")
        else:
            # Assume signals is a Series
            entries = aligned_signals
            exits = pd.Series(False, index=entries.index)
            logger.debug("Using signals as Series directly")

        logger.debug(f"Entries type: {type(entries)}, shape: {entries.shape}")
        logger.debug(f"Exits type: {type(exits)}, shape: {exits.shape}")
        logger.debug(f"Entry signals sum: {entries.sum()}")
        logger.debug(f"Exit signals sum: {exits.sum()}")

        # Suppress vectorbt warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            logger.debug("Creating vectorbt portfolio...")
            # Create portfolio from signals
            portfolio = vbt.Portfolio.from_signals(
                close_prices,
                entries=entries,
                exits=exits,
                init_cash=initial_cash,
                fees=fees,
                freq='D'  # Daily frequency
            )
            logger.debug("Portfolio created successfully")

            # Get the asset column name used by vectorbt for this portfolio.
            # This is crucial if vectorbt treats the portfolio as multi-column internally,
            # even if we logically have one asset.
            if not portfolio.wrapper.columns.empty:
                asset_col = portfolio.wrapper.columns[0]
            else:
                # Fallback or error if no columns found, though unlikely if portfolio was built
                # and from_signals was successful.
                raise BacktestError("Portfolio has no columns identified by vectorbt wrapper.")
        
        # Extract performance statistics
        logger.debug("Extracting portfolio stats...")
        stats = portfolio.stats(column=asset_col) # Get stats for the specific asset column
        logger.debug(f"Stats type: {type(stats)}")
        logger.debug(f"Stats keys: {stats.keys() if hasattr(stats, 'keys') else 'No keys method'}")

        portfolio_returns_data = portfolio.returns() # This may be a DataFrame or Series
        if isinstance(portfolio_returns_data, pd.DataFrame):
            returns = portfolio_returns_data[asset_col] # Ensure returns is a Series
        else: # Assuming it's already a Series if not a DataFrame
            returns = portfolio_returns_data
        logger.debug(f"Returns type: {type(returns)}")
        
        # Handle cases where no trades occurred
        try:
            total_trades = int(stats.get('Total Trades', 0))
            logger.debug(f"Total trades: {total_trades}")
        except (TypeError, AttributeError) as e:
            logger.error(f"Error getting total trades: {str(e)}")
            logger.debug(f"Stats content: {stats}")
            # Try alternative access methods
            try:
                if hasattr(stats, 'Total Trades'):
                    total_trades = int(getattr(stats, 'Total Trades', 0))
                elif isinstance(stats, dict):
                    total_trades = int(stats.get('Total Trades', 0))
                else:
                    total_trades = 0
                logger.debug(f"Alternative total trades: {total_trades}")
            except Exception as e2:
                logger.error(f"Alternative access failed: {str(e2)}")
                total_trades = 0
        
        if total_trades == 0:
            logger.debug("No trades case - returning minimal metrics")
            # No trades case - return minimal metrics
            return BacktestResult(
                total_return=0.0,
                annualized_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                total_trades=0,
                win_rate=0.0,
                profit_factor=0.0,
                final_value=initial_cash,
                volatility=0.0,
                calmar_ratio=0.0,
                trade_details=[],
                portfolio_value_series={}
            )
        logger.debug("Extracting performance metrics...")
        # Replace float conversions with safe_float where needed
        total_return = safe_float(stats.get('Total Return [%]'), default=0.0, 
                                  metric_name="Total Return", raise_on_type_error=True)
        
        # Calculate annualized return manually since vectorbt doesn't provide it directly
        # Use the total return and the period to annualize
        try:
            period_days = (returns.index[-1] - returns.index[0]).days if len(returns) > 1 else 365
            years = period_days / 365.25  # Account for leap years
            if years > 0 and total_return != 0:
                annualized_return = ((1 + total_return / 100) ** (1 / years) - 1) * 100
            else:
                annualized_return = 0.0
            logger.debug(f"Calculated annualized return: {annualized_return}% (period: {period_days} days, {years:.2f} years)")
        except Exception as e:
            logger.warning(f"Could not calculate annualized return: {str(e)}, using 0.0")
            annualized_return = 0.0
        # Sharpe can be legitimately 0 or negative. Defaulting to 0.0 if non-numeric is okay,
        # but a string like "N/A" should raise an error.
        sharpe_ratio = safe_float(stats.get('Sharpe Ratio'), default=0.0,
                                  metric_name="Sharpe Ratio", raise_on_type_error=True)
        # Max Drawdown is typically negative or zero.
        max_drawdown = safe_float(stats.get('Max Drawdown [%]'), default=0.0,
                                  metric_name="Max Drawdown", raise_on_type_error=True)
        # Final value is critical. If it's missing from stats, initial_cash is a sensible default.
        # If it's present but malformed (e.g. string "error"), it should raise.
        final_value = safe_float(stats.get('End Value'), default=initial_cash,
                                 metric_name="End Value", raise_on_type_error=True)
        logger.debug(f"Basic metrics extracted: TR={total_return}, AR={annualized_return}, SR={sharpe_ratio}")
        
        # Calculate win rate and profit factor
        logger.debug("Getting trade records...")
        trades = portfolio.trades.records_readable
        logger.debug(f"Trades type: {type(trades)}, length: {len(trades)}")
        
        if len(trades) > 0:
            # Get column mapping for different vectorbt versions
            columns = trades.columns.tolist()
            logger.debug(f"Trade columns: {columns}")
            
            # Helper function to find column by patterns
            def find_column_by_patterns(columns: list, patterns: list, default: str) -> str:
                """Find column name that matches any of the given patterns (case-insensitive)."""
                for pattern in patterns:
                    for col in columns:
                        if pattern.lower() in col.lower():
                            return col
                return default
            
            # Create column name mappings with robust pattern matching
            entry_time_col = find_column_by_patterns(
                columns, 
                ['entry timestamp', 'entry time', 'open time', 'start time'], 
                'Entry Timestamp'
            )
            exit_time_col = find_column_by_patterns(
                columns, 
                ['exit timestamp', 'exit time', 'close time', 'end time'], 
                'Exit Timestamp'
            )
            entry_price_col = find_column_by_patterns(
                columns, 
                ['avg entry price', 'entry price', 'open price', 'buy price'], 
                'Avg Entry Price'
            )
            exit_price_col = find_column_by_patterns(
                columns, 
                ['avg exit price', 'exit price', 'close price', 'sell price'], 
                'Avg Exit Price'
            )
            pnl_col = find_column_by_patterns(
                columns, 
                ['pnl', 'profit', 'p&l', 'p/l'], 
                'PnL'
            )
            return_pct_col = find_column_by_patterns(
                columns, 
                ['return', 'ret', '%', 'pct'], 
                'Return'
            )
            
            # Verify required columns exist after mapping
            mapped_cols = [entry_time_col, exit_time_col, entry_price_col, exit_price_col, pnl_col, return_pct_col]
            missing_cols = [col for col in mapped_cols if col not in columns]
            
            if missing_cols:
                logger.warning(f"Could not find required columns after pattern matching. Missing: {missing_cols}")
                logger.warning(f"Available columns: {columns}")
                logger.warning("Proceeding with best-effort mapping - some calculations may fail")
            else:
                logger.debug(f"Successfully mapped all columns: entry={entry_time_col}, exit={exit_time_col}, entry_price={entry_price_col}, exit_price={exit_price_col}, pnl={pnl_col}, return={return_pct_col}")
              # Ensure PnL and Return columns are numeric before calculations
            trades[pnl_col] = pd.to_numeric(trades[pnl_col], errors='coerce')
            trades[return_pct_col] = pd.to_numeric(trades[return_pct_col], errors='coerce')
            
            winning_trades = len(trades[trades[pnl_col] > 0])
            win_rate = (winning_trades / len(trades)) * 100
            
            gross_profit = trades[trades[pnl_col] > 0][pnl_col].sum()
            gross_loss = abs(trades[trades[pnl_col] < 0][pnl_col].sum())
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            logger.debug(f"Trade metrics: WR={win_rate}, PF={profit_factor}")
            
            # Calculate trade duration statistics
            try:
                trades[entry_time_col] = pd.to_datetime(trades[entry_time_col])
                trades[exit_time_col] = pd.to_datetime(trades[exit_time_col])
                trade_durations = (trades[exit_time_col] - trades[entry_time_col]).dt.days
                avg_trade_duration_days = trade_durations.mean()
                trade_durations_list = trade_durations.tolist()
                logger.debug(f"Trade duration stats: avg={avg_trade_duration_days:.2f} days")
            except Exception as e:
                logger.warning(f"Could not calculate trade durations: {str(e)}")
                avg_trade_duration_days = None
                trade_durations_list = None
        else:
            win_rate = 0.0
            profit_factor = 0.0
            avg_trade_duration_days = None
            trade_durations_list = None
            logger.debug("No trades for win rate calculation")
        
        # Calculate volatility
        try:
            volatility = float(returns.std() * np.sqrt(252) * 100)  # Annualized volatility
            # If returns is a Series (due to column selection), returns.std() is a float.
            # The float() call is redundant but harmless.
            logger.debug(f"Volatility: {volatility}") # type: ignore

        except (ValueError, TypeError) as e:
            logger.warning(f"Could not calculate volatility: {str(e)}, using 0.0")
            volatility = 0.0
        
        # Calculate Calmar ratio
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0.0
        logger.debug(f"Calmar ratio: {calmar_ratio}")
          # Extract trade details
        logger.debug("Extracting trade details...")
        trade_details = []
        if len(trades) > 0:
            for idx, trade in trades.iterrows():
                try:
                    # Convert timestamps to strings properly
                    entry_date_str = pd.to_datetime(trade[entry_time_col]).strftime('%Y-%m-%d') if pd.notna(trade[entry_time_col]) else 'N/A'
                    exit_date_str = pd.to_datetime(trade[exit_time_col]).strftime('%Y-%m-%d') if pd.notna(trade[exit_time_col]) else 'N/A'
                    
                    trade_details.append({
                        'entry_date': entry_date_str,
                        'exit_date': exit_date_str,
                        'entry_price': safe_float(trade[entry_price_col], metric_name=f"Trade Entry Price (idx {idx})", raise_on_type_error=True),
                        'exit_price': safe_float(trade[exit_price_col], metric_name=f"Trade Exit Price (idx {idx})", raise_on_type_error=True),
                        'pnl': safe_float(trade[pnl_col], metric_name=f"Trade PnL (idx {idx})", raise_on_type_error=True),
                        'return_pct': safe_float(trade[return_pct_col] * 100, metric_name=f"Trade Return % (idx {idx})", raise_on_type_error=True)  # Convert to percentage
                    })
                except Exception as e:
                    logger.warning(f"Error processing trade at index {idx}: {str(e)}")
                    continue
        
        # Extract portfolio value series
        logger.debug("Extracting portfolio values...")
        try:
            portfolio_values = portfolio.value()
            # Ensure portfolio_values is iterable (Series or DataFrame)
            if not hasattr(portfolio_values, 'items') and not isinstance(portfolio_values, (pd.Series, pd.DataFrame)):
                raise BacktestError(f"Portfolio values are not in an iterable format (Series/DataFrame). Got: {type(portfolio_values)}")

            if isinstance(portfolio_values, pd.Series):
                portfolio_value_series = {str(idx): safe_float(val) for idx, val in portfolio_values.items()}
            elif isinstance(portfolio_values, pd.DataFrame):
                # Use the first column if DataFrame
                series_data = portfolio_values.iloc[:, 0]
                portfolio_value_series = {str(idx): safe_float(val) for idx, val in series_data.items()}
            else:
                # This case should ideally not be hit if portfolio.value() behaves as expected
                logger.warning(f"Unexpected type for portfolio_values: {type(portfolio_values)}. Attempting direct iteration.")
                portfolio_value_series = {str(k): safe_float(v, metric_name=f"Portfolio Value ({k})", raise_on_type_error=True) for k, v in getattr(portfolio_values, 'items', lambda: {} )()}
            logger.debug(f"Portfolio values extracted: {len(portfolio_value_series)} entries")
        except Exception as e:
            logger.warning(f"Error extracting portfolio values: {str(e)}")
            portfolio_value_series = {}
        
        logger.debug("Creating BacktestResult...")
        result = BacktestResult(
            total_return=total_return,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            total_trades=total_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            final_value=final_value,
            volatility=volatility,
            calmar_ratio=calmar_ratio,
            trade_details=trade_details,
            avg_trade_duration_days=avg_trade_duration_days,
            trade_durations_days=trade_durations_list,
            portfolio_value_series=portfolio_value_series
        )
        logger.debug("BacktestResult created successfully")
        return result
        
    except Exception as e:
        logger.error(f"Backtest execution failed: {str(e)}", exc_info=True)
        raise BacktestError(f"Backtest execution failed: {str(e)}")


def perform_vibe_checks(
    result: BacktestResult, 
    data: pd.DataFrame, 
    strategy_config: StrategyConfig
) -> VibeCheckResults:
    """Perform strategy validation checks.
    
    Args:
        result: Backtest result to validate
        data: Original market data
        strategy_config: Strategy configuration used
        
    Returns:
        VibeCheckResults with validation status
    """
    messages = []
    
    # Check 1: Minimum trade count
    min_trades_pass = result.total_trades > 0
    if min_trades_pass:
        messages.append(f"✓ Minimum trades check: {result.total_trades} trades executed")
    else:
        messages.append("✗ Minimum trades check: No trades executed")
    
    # Check 2: Signal quality (frequency)
    total_days = len(data)
    if result.total_trades > 0:
        signal_frequency = result.total_trades / total_days
        # Reasonable range: not more than 10% of days should have trades
        signal_quality_pass = signal_frequency <= 0.1
        if signal_quality_pass:
            messages.append(f"✓ Signal quality check: {signal_frequency:.3f} trades per day (reasonable)")
        else:
            messages.append(f"✗ Signal quality check: {signal_frequency:.3f} trades per day (too frequent)")
    else:
        signal_quality_pass = False
        messages.append("✗ Signal quality check: No signals to evaluate")
    
    # Check 3: Data coverage
    validated_params = strategy_config.validate_strategy_params() # Returns specific param instance
    strategy_required_bars = validated_params.get_required_data_coverage_bars()
    
    if strategy_required_bars is not None:
        # Apply a safety factor for the check, e.g., 2x the strategy's raw requirement
        check_threshold_bars = strategy_required_bars * 2
        data_coverage_pass = len(data) >= check_threshold_bars
        if data_coverage_pass:
            messages.append(f"✓ Data coverage check: {len(data)} bars >= {check_threshold_bars} (strategy needs {strategy_required_bars}, check uses 2x)")
        else:
            messages.append(f"✗ Data coverage check: {len(data)} bars < {check_threshold_bars} (strategy needs {strategy_required_bars}, check uses 2x)")
    else:
        data_coverage_pass = False # Fail if requirement is not specified or is None
        messages.append("✗ Data coverage check: FAILED - Strategy did not explicitly define data coverage bar requirements. This is a critical configuration or implementation error.")
    
    # Overall pass status
    overall_pass = min_trades_pass and signal_quality_pass and data_coverage_pass
    
    return VibeCheckResults(
        minimum_trades_check=min_trades_pass,
        signal_quality_check=signal_quality_pass,
        data_coverage_check=data_coverage_pass,
        overall_pass=overall_pass,
        check_messages=messages
    )


def perform_robustness_checks(
    data: pd.DataFrame, 
    signals: pd.DataFrame, 
    strategy_config: StrategyConfig
) -> RobustnessResults:
    """Perform robustness analysis on the strategy.
    
    Args:
        data: Market data DataFrame
        signals: Generated signals DataFrame
        strategy_config: Strategy configuration
        
    Returns:
        RobustnessResults with sensitivity analysis
    """
    try:
        # Baseline backtest (low fees)
        baseline_result = run_backtest(prices_data=data, signals_data=signals, fees=0.001)  # 0.1%
        baseline_sharpe = baseline_result.sharpe_ratio
        baseline_return = baseline_result.annualized_return
        
        # High fees backtest
        high_fees_result = run_backtest(prices_data=data, signals_data=signals, fees=0.01)  # 1.0%
        high_fees_sharpe = high_fees_result.sharpe_ratio
        high_fees_return = high_fees_result.annualized_return
        
        # Calculate degradation
        sharpe_degradation = ((baseline_sharpe - high_fees_sharpe) / abs(baseline_sharpe) * 100) if baseline_sharpe != 0 else 0
        return_degradation = ((baseline_return - high_fees_return) / abs(baseline_return) * 100) if baseline_return != 0 else 0
        
        # Calculate turnover rate
        total_trades = baseline_result.total_trades
        trading_days = len(data)
        turnover_rate = (total_trades / trading_days) * 100 if trading_days > 0 else 0
        
        # Generate recommendations
        recommendations = []
        
        if sharpe_degradation > 50:
            recommendations.append("High sensitivity to fees - consider reducing trade frequency")
        
        if turnover_rate > 20:
            recommendations.append(f"High turnover rate ({turnover_rate:.1f}%) - strategy may be overtrading")
        
        if baseline_result.total_trades < 5:
            recommendations.append("Very few trades - consider longer backtest period or different parameters")
        
        if baseline_result.max_drawdown > 30:
            recommendations.append(f"High maximum drawdown ({baseline_result.max_drawdown:.1f}%) - consider risk management")
        
        if not recommendations:
            recommendations.append("Strategy shows good robustness characteristics")
        
        return RobustnessResults(
            baseline_sharpe=baseline_sharpe,
            high_fees_sharpe=high_fees_sharpe,
            turnover_rate=turnover_rate,
            sharpe_degradation=sharpe_degradation,
            return_degradation=return_degradation,
            recommendations=recommendations
        )
        
    except Exception as e:
        # Return minimal results if robustness checks fail
        return RobustnessResults(
            baseline_sharpe=0.0,
            high_fees_sharpe=0.0,
            turnover_rate=0.0,
            sharpe_degradation=0.0,
            return_degradation=0.0,
            recommendations=[f"Robustness analysis failed: {str(e)}"]
        )


def run_complete_backtest(strategy_config, data, objective_params=None):
    """Execute complete backtest analysis including validation and robustness checks."""
    logger.debug(f"Starting complete backtest for ticker: {strategy_config.ticker}")
    try:
        if isinstance(data, dict):
            actual_prices_df = data['prices']
            if 'signals' in data:
                actual_signals_df = data['signals']
            else:
                actual_signals_df = StrategySignalGenerator.generate_signals(actual_prices_df, strategy_config)
        else:  # data is a DataFrame of prices
            actual_prices_df = data
            actual_signals_df = StrategySignalGenerator.generate_signals(actual_prices_df, strategy_config)

        # Execute primary backtest
        primary_result = run_backtest(prices_data=actual_prices_df, signals_data=actual_signals_df)

        # Calculate pct_trades_in_target_hold_period if applicable
        if primary_result.trade_durations_days and objective_params:
            min_hold = objective_params.get('min_hold_days')
            max_hold = objective_params.get('max_hold_days')
            if min_hold is not None and max_hold is not None:
                in_range_count = sum(1 for d in primary_result.trade_durations_days if min_hold <= d <= max_hold)
                if primary_result.total_trades > 0:
                    primary_result.pct_trades_in_target_hold_period = (in_range_count / primary_result.total_trades) * 100
                else:
                    primary_result.pct_trades_in_target_hold_period = 0.0

        # Step 3: Perform vibe checks
        vibe_checks = perform_vibe_checks(primary_result,
                                          actual_prices_df,
                                          strategy_config)

        # Step 4: Perform robustness checks
        robustness_checks = perform_robustness_checks(
            actual_prices_df,
            actual_signals_df,
            strategy_config)

        # Step 5: Assemble comprehensive analysis
        return BacktestAnalysisResult(
            primary_result=primary_result,
            vibe_checks=vibe_checks,
            robustness_checks=robustness_checks,
            strategy_config=strategy_config.model_dump()
        )
    except Exception as e:
        logger.error(f"Complete backtest analysis failed: {str(e)}", exc_info=True)
        raise BacktestError(f"Complete backtest analysis failed: {str(e)}") from e
