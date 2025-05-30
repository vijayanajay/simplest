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
    from .config import StrategyConfig, BaseStrategyParams, MovingAverageCrossoverParams
except ImportError:
    # For imports when running tests
    from src.meqsap.config import StrategyConfig, BaseStrategyParams, MovingAverageCrossoverParams


class BacktestError(Exception):
    """Exception raised for backtesting errors."""
    pass


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
    
    @staticmethod
    def generate_signals(data: pd.DataFrame, strategy_config: StrategyConfig) -> pd.DataFrame:
        """Generate trading signals based on strategy configuration.
        
        Args:
            data: OHLCV market data DataFrame
            strategy_config: Validated strategy configuration
            
        Returns:
            DataFrame with 'entry' and 'exit' boolean columns
            
        Raises:
            BacktestError: If signal generation fails
        """
        try:
            if strategy_config.strategy_type == "MovingAverageCrossover":
                return StrategySignalGenerator._generate_ma_crossover_signals(data, strategy_config)
            else:
                raise BacktestError(f"Unknown strategy type: {strategy_config.strategy_type}")
                
        except Exception as e:
            raise BacktestError(f"Signal generation failed: {str(e)}") from e
    
    @staticmethod
    def _generate_ma_crossover_signals(data: pd.DataFrame, strategy_config: StrategyConfig) -> pd.DataFrame:
        """Generate Moving Average Crossover signals."""
        # Validate strategy parameters
        validated_params = strategy_config.validate_strategy_params()
        if not isinstance(validated_params, MovingAverageCrossoverParams):
            raise BacktestError("Invalid parameters for MovingAverageCrossover strategy")
        fast_ma = validated_params.fast_ma
        slow_ma = validated_params.slow_ma
        
        # Validate MA period ordering
        if fast_ma >= slow_ma:
            raise BacktestError(f"Invalid MA period ordering: fast_ma ({fast_ma}) must be less than slow_ma ({slow_ma})")
        
        # Check data sufficiency
        if len(data) < slow_ma:
            raise BacktestError(f"Insufficient data: need at least {slow_ma} bars, got {len(data)}")
        
        # Extract close prices
        close_prices = data['Close']
          # Calculate moving averages using pandas-ta
        fast_ma_series = ta.sma(close_prices, length=fast_ma)
        slow_ma_series = ta.sma(close_prices, length=slow_ma)
        
        # Find valid index range where both MAs have non-NaN values
        valid_mask = fast_ma_series.notna() & slow_ma_series.notna()
        valid_index = data.index[valid_mask]
        
        if len(valid_index) == 0:
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


# Set up a logger for debugging
logger = logging.getLogger(__name__)

def safe_float(value, default=0.0):
    """Safely convert a value to float, returning a default if conversion fails."""
    if value is None:
        return default
    try:
        result = float(value)
        # Check for NaN and infinite values
        if np.isnan(result) or np.isinf(result):
            logger.warning(f"Value '{value}' converted to NaN or inf, using default: {default}")
            return default
        return result
    except (ValueError, TypeError):
        logger.warning(f"Could not convert '{value}' (type: {type(value).__name__}) to float, using default: {default}")
        return default

def run_backtest(data, signals=None, initial_cash=10000, fees=0.001):
    """Run a backtest with the given data and signals.
    
    Args:
        data: OHLCV market data DataFrame or dictionary with 'prices' and optionally 'signals'
        signals: DataFrame with 'entry' and 'exit' boolean columns (optional if provided in data)
        initial_cash: Starting portfolio value (default: 10000)
        fees: Transaction costs as a decimal (default: 0.001 = 0.1%)
        
    Returns:
        BacktestResult object with performance metrics
        
    Raises:
        BacktestError: If backtesting execution fails
    """
    logger.debug(f"Starting run_backtest with data type: {type(data)}")
    logger.debug(f"Data structure: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
    
    try:
        # Handle different input formats
        if isinstance(data, dict):
            logger.debug("Data is dictionary format")
            # Extract data from dictionary format
            prices_data = data.get('prices')
            logger.debug(f"Prices data type: {type(prices_data)}")
            
            if prices_data is None:
                raise BacktestError("Dictionary data must contain 'prices' key")
            
            if signals is None:
                signals = data.get('signals')
                logger.debug(f"Signals data type: {type(signals)}")
                if signals is None:
                    raise BacktestError("No signals provided in data dictionary or as separate parameter")
        else:
            logger.debug("Data is direct DataFrame format")
            # Assume data is a DataFrame with OHLCV columns
            prices_data = data
            if signals is None:
                raise BacktestError("Signals must be provided when data is not a dictionary")
        
        logger.debug(f"Final prices_data type: {type(prices_data)}")
        logger.debug(f"Final signals type: {type(signals)}")
        
        # Verify we have the needed data
        if not isinstance(prices_data, (pd.DataFrame, pd.Series)):
            raise BacktestError(f"Price data must be a DataFrame or Series, got {type(prices_data).__name__}")
        
        if not isinstance(signals, (pd.DataFrame, pd.Series)):
            raise BacktestError(f"Signals must be a DataFrame or Series, got {type(signals).__name__}")
        
        logger.debug(f"Prices data columns: {getattr(prices_data, 'columns', 'No columns (Series)')}")
        logger.debug(f"Signals data columns: {getattr(signals, 'columns', 'No columns (Series)')}")
        
        # Align data and signals
        try:
            common_index = prices_data.index.intersection(signals.index)
            logger.debug(f"Common index length: {len(common_index)}")
        except AttributeError as e:
            raise BacktestError(f"Data alignment failed - ensure both prices and signals have proper index: {str(e)}")
        
        if len(common_index) == 0:
            raise BacktestError("No common dates between data and signals")
        
        aligned_data = prices_data.loc[common_index]
        aligned_signals = signals.loc[common_index]
        
        logger.debug(f"Aligned data shape: {aligned_data.shape}")
        logger.debug(f"Aligned signals shape: {aligned_signals.shape}")
        
        # Extract close prices for vectorbt
        if isinstance(aligned_data, pd.DataFrame):
            logger.debug(f"Processing DataFrame with columns: {aligned_data.columns.tolist()}")
            if 'Close' in aligned_data.columns:
                close_prices = aligned_data['Close']
                logger.debug("Using 'Close' column")
            elif 'close' in aligned_data.columns:
                close_prices = aligned_data['close']
                logger.debug("Using 'close' column")
            else:
                # Try to find a price column
                price_columns = [col for col in aligned_data.columns if 'price' in col.lower() or 'close' in col.lower()]
                if price_columns:
                    close_prices = aligned_data[price_columns[0]]
                    logger.debug(f"Using price column: {price_columns[0]}")
                else:
                    raise BacktestError("No suitable price column found in DataFrame")
        else:
            # Assume it's already a Series
            close_prices = aligned_data
            logger.debug("Using data as Series directly")
        
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
        
        # Extract performance statistics
        logger.debug("Extracting portfolio stats...")
        stats = portfolio.stats()
        logger.debug(f"Stats type: {type(stats)}")
        logger.debug(f"Stats keys: {stats.keys() if hasattr(stats, 'keys') else 'No keys method'}")
        
        # Calculate additional metrics
        returns = portfolio.returns()
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
        total_return = safe_float(stats.get('Total Return [%]', 0.0))        
        annualized_return = safe_float(stats.get('Annualized Return [%]', 0.0))
        sharpe_ratio = safe_float(stats.get('Sharpe Ratio', 0.0))
        max_drawdown = safe_float(stats.get('Max Drawdown [%]', 0.0))
        final_value = safe_float(stats.get('End Value', initial_cash))
        logger.debug(f"Basic metrics extracted: TR={total_return}, AR={annualized_return}, SR={sharpe_ratio}")
        
        # Calculate win rate and profit factor
        logger.debug("Getting trade records...")
        trades = portfolio.trades.records_readable
        logger.debug(f"Trades type: {type(trades)}, length: {len(trades)}")
        
        if len(trades) > 0:
            # Get column mapping for different vectorbt versions
            columns = trades.columns.tolist()
            logger.debug(f"Trade columns: {columns}")
            
            # Create column name mappings with fallbacks
            entry_time_col = next((c for c in ['entry_time', 'Entry Time', 'Entry Timestamp', 'entry_timestamp'] 
                                if c in columns), columns[0] if len(columns) > 0 else 'entry_time')
            exit_time_col = next((c for c in ['exit_time', 'Exit Time', 'Exit Timestamp', 'exit_timestamp'] 
                               if c in columns), columns[1] if len(columns) > 1 else 'exit_time')
            entry_price_col = next((c for c in ['entry_price', 'Entry Price', 'EntryPrice'] 
                                  if c in columns), columns[2] if len(columns) > 2 else 'entry_price')
            exit_price_col = next((c for c in ['exit_price', 'Exit Price', 'ExitPrice'] 
                                 if c in columns), columns[3] if len(columns) > 3 else 'exit_price')
            pnl_col = next((c for c in ['pnl', 'PnL', 'profit_loss'] 
                          if c in columns), columns[4] if len(columns) > 4 else 'PnL')
            return_pct_col = next((c for c in ['return_pct', 'Return [%]', 'return'] 
                                  if c in columns), columns[5] if len(columns) > 5 else 'Return [%]')
            
            logger.debug(f"Column mapping: entry={entry_time_col}, exit={exit_time_col}, pnl={pnl_col}")
            
            winning_trades = len(trades[trades[pnl_col] > 0])
            win_rate = (winning_trades / len(trades)) * 100
            
            gross_profit = trades[trades[pnl_col] > 0][pnl_col].sum()
            gross_loss = abs(trades[trades[pnl_col] < 0][pnl_col].sum())
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            logger.debug(f"Trade metrics: WR={win_rate}, PF={profit_factor}")
        else:
            win_rate = 0.0
            profit_factor = 0.0
            logger.debug("No trades for win rate calculation")
        
        # Calculate volatility
        try:
            volatility = float(returns.std() * np.sqrt(252) * 100)  # Annualized volatility
            logger.debug(f"Volatility: {volatility}")
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
            # Column mappings are already defined above
            for _, trade in trades.iterrows():
                try:
                    trade_details.append({
                        'entry_date': str(trade[entry_time_col]),
                        'exit_date': str(trade[exit_time_col]),
                        'entry_price': safe_float(trade[entry_price_col]),
                        'exit_price': safe_float(trade[exit_price_col]),
                        'pnl': safe_float(trade[pnl_col]),
                        'return_pct': safe_float(trade[return_pct_col])
                    })
                except Exception as e:
                    logger.warning(f"Error processing trade: {str(e)}")
                    continue
        
        # Extract portfolio value series
        logger.debug("Extracting portfolio values...")
        try:
            portfolio_values = portfolio.value()
            portfolio_value_series = {str(date): safe_float(value) for date, value in portfolio_values.items()}
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
    validated_params = strategy_config.validate_strategy_params()
    if isinstance(validated_params, MovingAverageCrossoverParams):
        required_bars = validated_params.slow_ma
        data_coverage_pass = len(data) >= required_bars * 2  # At least 2x the slow MA period
        if data_coverage_pass:
            messages.append(f"✓ Data coverage check: {len(data)} bars >= {required_bars * 2} required")
        else:
            messages.append(f"✗ Data coverage check: {len(data)} bars < {required_bars * 2} required")
    else:
        data_coverage_pass = True  # Default pass for unknown strategies
        messages.append("✓ Data coverage check: Passed (unknown strategy type)")
    
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
        baseline_result = run_backtest(data, signals, fees=0.001)  # 0.1%
        baseline_sharpe = baseline_result.sharpe_ratio
        baseline_return = baseline_result.annualized_return
        
        # High fees backtest
        high_fees_result = run_backtest(data, signals, fees=0.01)  # 1.0%
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


def run_complete_backtest(strategy_config, data):
    """Execute complete backtest analysis including validation and robustness checks."""
    logger.debug(f"Starting complete backtest for ticker: {strategy_config.ticker}")
    
    try:
        # Handle different input formats
        if isinstance(data, dict) and 'signals' in data:
            # If signals are already provided in data dictionary
            signals = data['signals']
        else:
            # Generate signals from data using the strategy config
            signals = StrategySignalGenerator.generate_signals(data, strategy_config)
        
        # Package data for backtest
        if isinstance(data, dict) and 'prices' in data:
            backtest_data = data
        else:
            # Data is a DataFrame, package it for run_backtest
            backtest_data = {'prices': data, 'signals': signals}
        
        # Execute primary backtest
        primary_result = run_backtest(backtest_data)
        
        # Step 3: Perform vibe checks
        vibe_checks = perform_vibe_checks(primary_result, 
                                          data.get('prices') if isinstance(data, dict) else data, 
                                          strategy_config)
        
        # Step 4: Perform robustness checks
        robustness_checks = perform_robustness_checks(
            data.get('prices') if isinstance(data, dict) else data,
            signals, 
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
