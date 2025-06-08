# Indian Stock Examples - Complete Reference Guide
# MEQSAP Enhanced Parameter Framework Examples
# 
# This directory contains comprehensive Indian stock market examples demonstrating
# the enhanced parameter definition framework and optimization capabilities.

## Quick Reference

| File | Stock | Sector | Strategy Focus | Key Features |
|------|--------|---------|----------------|--------------|
| `indian_stock_sample.yaml` | RELIANCE.NS | Energy | Grid Search | Comprehensive parameter ranges, Indian market optimization |
| `hdfc_banking.yaml` | HDFCBANK.NS | Banking | Random Search | Mixed parameters, banking sector timing |
| `tcs_conservative.yaml` | TCS.NS | IT Services | Fixed Parameters | Backward compatibility, explicit values |
| `adani_aggressive.yaml` | ADANIENT.NS | Infrastructure | Grid Search | High-volatility parameters, total return focus |
| `infosys_sector_optimization.yaml` | INFY.NS | IT Services | Grid Search | Multi-objective framework, sector analysis |
| `sbin_banking_portfolio.yaml` | SBIN.NS | Public Banking | Grid Search | Profit factor optimization, portfolio template |
| `maruti_automotive_winrate.yaml` | MARUTI.NS | Automotive | Grid Search | Win rate optimization, seasonal considerations |
| `tatasteel_risk_management.yaml` | TATASTEEL.NS | Steel | Grid Search | Drawdown minimization, risk management |
| `itc_multi_objective.yaml` | ITC.NS | FMCG | Grid Search | Multiple objective functions, strategy research |
| `ongc_energy_momentum.yaml` | ONGC.NS | Energy | Grid Search | Momentum strategy, commodity correlation |

## Usage Examples

### Basic Optimization
```bash
# Run comprehensive optimization with reporting
python run.py optimize single examples/indian_stock_sample.yaml --report --verbose

# Quick parameter scan without progress bar
python run.py optimize single examples/hdfc_banking.yaml --no-progress

# Traditional fixed parameter analysis (backward compatibility)
python run.py analyze examples/tcs_conservative.yaml --report
```

### Advanced Optimization Workflows
```bash
# High-volatility stock optimization
python run.py optimize single examples/adani_aggressive.yaml --report --output-dir ./high_vol_analysis

# Banking sector systematic analysis
python run.py optimize single examples/sbin_banking_portfolio.yaml --report --verbose

# Risk management focused optimization
python run.py optimize single examples/tatasteel_risk_management.yaml --report
```

### Multi-Objective Analysis
```bash
# Compare different objective functions
python run.py optimize single examples/itc_multi_objective.yaml --report
# Edit file to change objective_function and rerun for comparison

# Sector-wide optimization analysis
python run.py optimize single examples/infosys_sector_optimization.yaml --output-dir ./sector_analysis
```

## Parameter Framework Features Demonstrated

### 1. Parameter Types
- **Fixed Values**: Traditional single-value parameters (`tcs_conservative.yaml`)
- **Ranges**: Continuous parameter optimization (`indian_stock_sample.yaml`)
- **Choices**: Discrete parameter selection (`hdfc_banking.yaml`)
- **Explicit Values**: Named value definitions with descriptions (`tcs_conservative.yaml`)

### 2. Mixed Parameter Strategies
- **Fixed + Range**: Stable base with optimization components (`hdfc_banking.yaml`)
- **Range + Choices**: Comprehensive optimization space (`indian_stock_sample.yaml`)
- **Multi-Type**: Complex parameter combinations (`adani_aggressive.yaml`)

### 3. Optimization Algorithms
- **Grid Search**: Systematic exploration of all combinations
- **Random Search**: Efficient sampling of large parameter spaces (`hdfc_banking.yaml`)

### 4. Objective Functions
- **Sharpe Ratio**: Risk-adjusted returns (default for most examples)
- **Total Return**: Maximum absolute returns (`adani_aggressive.yaml`, `ongc_energy_momentum.yaml`)
- **Max Drawdown**: Risk minimization (`tatasteel_risk_management.yaml`)
- **Profit Factor**: Trade quality optimization (`sbin_banking_portfolio.yaml`)
- **Win Rate**: Consistency optimization (`maruti_automotive_winrate.yaml`)

### 5. Sector-Specific Optimizations
- **Banking**: Interest rate cycle considerations, regulatory impacts
- **IT Services**: USD revenue exposure, technology cycles
- **Automotive**: Seasonal patterns, rural/urban demand cycles
- **Steel**: Commodity price volatility, cyclical trends
- **Energy**: Oil price correlation, geopolitical factors
- **FMCG**: Defensive characteristics, consumption patterns

## Indian Market Specific Considerations

### Market Characteristics
- **Trading Hours**: 9:15 AM - 3:30 PM IST (Monday-Friday)
- **Currency**: All prices in Indian Rupees (INR)
- **Holidays**: Indian stock exchanges observe local holidays
- **Settlement**: T+1 settlement cycle
- **Risk-Free Rate**: ~6% (Indian 10-year government bonds)

### Sector Rotation Patterns
- **Monsoon Impact**: Rural demand sectors (auto, FMCG) affected by rainfall
- **Budget Season**: Policy announcements create volatility (January-February)
- **Results Season**: Quarterly earnings drive short-term movements
- **Festival Demand**: October-November high consumption period
- **Economic Cycles**: Interest rate cycles affect different sectors

### Liquidity Considerations
- **Large Cap**: High liquidity, suitable for all strategies
- **Mid Cap**: Moderate liquidity, consider impact costs
- **Small Cap**: Lower liquidity, require careful position sizing

## Optimization Best Practices

### Parameter Selection Guidelines
1. **Start Conservative**: Begin with proven parameter ranges
2. **Sector-Specific**: Adjust ranges based on sector characteristics
3. **Market Regime**: Consider different parameter sets for bull/bear markets
4. **Validation**: Test parameters across different time periods
5. **Transaction Costs**: Factor in brokerage and impact costs

### Risk Management
1. **Position Sizing**: Use optimization results to determine position sizes
2. **Stop Losses**: Implement based on historical drawdown analysis
3. **Diversification**: Don't over-concentrate in single sectors
4. **Market Exposure**: Consider overall market beta during optimization
5. **Rebalancing**: Regular review and reoptimization of parameters

### Performance Monitoring
1. **Out-of-Sample Testing**: Validate on different time periods
2. **Live Performance**: Track actual vs backtested performance
3. **Parameter Stability**: Monitor for degrading performance over time
4. **Market Conditions**: Assess performance across different market regimes
5. **Benchmark Comparison**: Compare against relevant sector indices

## Getting Started

1. **Choose Your Sector**: Select an example matching your investment focus
2. **Understand the Business**: Review sector-specific notes in each file
3. **Run Basic Optimization**: Start with default parameters and settings
4. **Analyze Results**: Review optimization output and parameter sensitivity
5. **Customize Parameters**: Adjust ranges based on your risk tolerance and goals
6. **Validate Strategy**: Test on different time periods and market conditions
7. **Implement Gradually**: Start with paper trading before live implementation

For detailed documentation on the enhanced parameter framework, see the main README.md file.
