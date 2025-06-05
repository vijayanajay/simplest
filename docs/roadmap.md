## End System Vision

The envisioned system will empower analysts by automating significant parts of the strategy development lifecycle. An analyst will:

1.  **Define a problem space**: Specify target stocks, a set of preferred indicators (or allow the system to choose from a broader library), desired holding periods (e.g., > 3 days, < 1 month), and a baseline strategy for comparison. This is done via an enhanced YAML configuration.
2.  **Initiate Automated Discovery**: Run a command like `meqsap discover-strategy config.yaml`.
3.  **System Execution**:
    * The system explores indicator parameters and combinations, guided by optimization algorithms.
    * It continuously backtests generated strategies, focusing on the target hold period and comparing against the baseline.
    * If a strategy underperforms, the **Strategy Doctor** module analyzes *why* (e.g., "Excessive whipsaws in non-trending conditions for stock X," "Trades not aligning with target hold period due to premature exits triggered by Y indicator parameter").
    * Based on diagnostics, it proposes modifications (e.g., "Add ADX filter," "Optimize RSI exit levels for stock X's volatility profile," "Adjust MA periods to target longer hold times").
    * It iteratively refines strategies, attempting to beat the baseline and meet objectives.
4.  **Review & Refine**: The analyst receives:
    * The best strategy configuration(s) found.
    * A report detailing the optimization path, diagnostic insights, and performance comparisons.
    * The system might present several candidates that meet different trade-offs (e.g., one with higher Sharpe but fewer trades, another with more trades aligning with the hold period).
5.  **Iterative Collaboration**: The analyst can then take these system-generated strategies, perhaps tweak them further based on their domain expertise, or use them as new starting points for further automated discovery.

The analyst's role shifts from manual iteration to defining constraints, objectives, and overseeing an automated discovery process, with the system providing explanations for its choices.

---
## Roadmap for Automated Strategy Discovery & Optimization

Here's a 10-phase roadmap:

### Phase 1: Enhanced Indicator & Parameter Definition Framework

* **Goal**: Create a robust and extensible framework for defining indicators and their parameter spaces, enabling automated tuning.
* **Building on**: `src/meqsap/config.py`, `src/meqsap/backtest.py`.
* **Details**:
    1.  **Refactor `BaseStrategyParams`**:
        * Modify `BaseStrategyParams` (and its children like `MovingAverageCrossoverParams`) in `src/meqsap/config.py` to support parameter definitions as ranges, choices, or steps (e.g., `fast_ma: {"type": "range", "start": 5, "stop": 20, "step": 1}`).
        * Ensure `get_required_data_coverage_bars` in `BaseStrategyParams` (and its overrides) is now strictly enforced (as per `FLAW-20250602-002`) and can handle dynamic parameter definitions (e.g., uses the maximum possible value from a range for coverage calculation).
    2.  **Update `StrategyConfig`**: Allow the YAML to specify these parameter search spaces.
    3.  **Adapt `StrategySignalGenerator`**: Modify `src/meqsap/backtest.py::StrategySignalGenerator` to accept concrete parameter sets (drawn from the search space) for generating signals.
    4.  **Documentation**: Update all relevant documentation (`architecture.md`, example YAMLs) to reflect this new parameter definition.
* **Python Module**: `meqsap_indicators_core` (initially an internal module within `src/meqsap/`)
    * **Purpose**: Standardize definition of technical indicators, their parameters, and parameter search space descriptions.
    * **Modules**:
        * `indicator_definition.py`: Base classes like `IndicatorBase`, `ParameterDefinition`, `ParameterSpace`.
        * `technical_indicators/`: Directory for concrete indicator implementations (e.g., `ma.py`, `rsi.py`), adhering to `IndicatorBase`. These would wrap `pandas-ta` or provide custom logic.
        * `registry.py`: A way to register and discover available indicators.
    * **Integration**: `meqsap.config` would use this library to understand strategy parameter definitions from YAML. `meqsap.backtest` would use it to get indicator calculation logic.

---
### Phase 2: Parameter Optimization Engine (Single Indicator)

* **Goal**: Implement an engine to find optimal parameters for *single-indicator* strategies based on a defined objective function and respecting the target hold period.
* **Building on**: Phase 1, `src/meqsap/backtest.py`.
* **Details**:
    1.  **Objective Function Definition**:
        * Create a module for objective functions (e.g., Sharpe Ratio, Calmar Ratio, Profit Factor).
        * Crucially, incorporate the **hold period constraint** (trades > 3 days and < 1 month). This can be done by:
            * Modifying `BacktestResult` to include detailed trade duration statistics (average hold, percentage of trades in target range).
            * The objective function will then heavily penalize strategies where the average hold period or majority of trades fall outside the desired range.
    2.  **Optimization Algorithms**:
        * Implement initial algorithms: Grid Search and Random Search.
    3.  **Optimization Engine Core**:
        * Takes a strategy with defined parameter spaces (from Phase 1).
        * Iterates through parameter combinations using the chosen algorithm.
        * For each combination, calls `run_complete_backtest` (from `meqsap.backtest`).
        * Evaluates results using the objective function.
        * Tracks the best-performing parameter set.
    4.  **CLI Integration**: Add a new command (e.g., `meqsap optimize-single config.yaml`) to `meqsap.cli`.
    5.  **Reporting**:
        * Output the best parameters found and their detailed performance.
        * Log the optimization process (parameters tested, scores).
        * Explicitly report on how well the optimized strategy meets the hold period criteria.
* **Python Library Candidate**: `meqsap_optimizer`
    * **Purpose**: Provide a generic optimization framework.
    * **Modules**:
        * `algorithms/`: `grid_search.py`, `random_search.py`.
        * `objective_functions.py`: Standard financial metrics and a framework for custom objectives incorporating hold period stats.
        * `engine.py`: Core optimization loop logic.
    * **Integration**: `meqsap.cli` would invoke this engine. The engine uses `meqsap.backtest`.

---
### Phase 3: Baseline Definition and Comparative Analysis

* **Goal**: Establish a clear baseline for strategy performance and enhance reporting to quantitatively and qualitatively compare optimized strategies against this baseline.
* **Building on**: Phase 2, `src/meqsap/reporting.py`.
* **Details**:
    1.  **Baseline Configuration**:
        * Allow users to define a baseline strategy in the YAML (e.g., Buy & Hold, or a simple fixed-parameter MA Crossover).
        * If no baseline is provided, default to Buy & Hold for the given stock and period.
    2.  **Automated Baseline Run**: The system (CLI/optimization engine) automatically runs the backtest for the baseline strategy.
    3.  **Enhanced Reporting**:
        * Modify `BacktestAnalysisResult` or create a new `ComparativeAnalysisResult` to hold results for both the candidate strategy and the baseline.
        * Update `meqsap.reporting` to generate side-by-side comparison tables and visualizations.
        * Clearly indicate if the candidate strategy "beats" the baseline based on the primary objective function and other key metrics (including hold period alignment).
* **Python Library Candidate**: Initially part of `meqsap.reporting`. If comparison logic becomes very sophisticated (e.g., statistical significance testing), it could spin off to `meqsap_evaluator`.

---
### Phase 4: Expanding Indicator Suite & Generic Signal Logic

* **Goal**: Broaden the range of available technical indicators and generalize the signal generation mechanism.
* **Building on**: Phase 1, `meqsap_indicators_core`, `src/meqsap/backtest.py`.
* **Details**:
    1.  **Add New Indicators**:
        * Implement definitions and parameter spaces for more indicators (e.g., RSI, MACD, Bollinger Bands, ATR, Stochastics) within `meqsap_indicators_core`.
        * Ensure each new indicator correctly defines `get_required_data_coverage_bars`.
    2.  **Generic Signal Generation**:
        * Refactor `StrategySignalGenerator` in `meqsap.backtest`. Instead of bespoke methods like `_generate_ma_crossover_signals`, create a more generic way to define entry/exit conditions based on indicator outputs.
        * For example, a signal could be defined as `RSI(14) < 30` (for entry) or `Close > BollingerBand(20,2).upper` (for exit). This requires indicator outputs to be standardized (e.g., named series).
    3.  **Optimization Compatibility**: The `meqsap_optimizer` from Phase 2 should seamlessly work with these new single-indicator strategies.
* **Python Library Candidate**: `meqsap_indicators_core` (enhancements).

---
### Phase 5: Multi-Signal/Indicator Combination Framework (Rule-Based)

* **Goal**: Enable the creation and backtesting of strategies that combine signals from multiple indicators using user-defined logical rules.
* **Building on**: Phase 4.
* **Details**:
    1.  **YAML Rule Definition**:
        * Extend `StrategyConfig` (YAML structure) to allow users to define strategies by listing multiple indicator "blocks" and then specifying entry/exit rules using logical operators (AND, OR, NOT) that reference these blocks.
        * Example:
            ```yaml
            strategy_type: CombinedRuleStrategy
            components:
              ma_cross:
                indicator: MovingAverageCrossover
                params: { fast_ma: {value: 10}, slow_ma: {value: 20} } # Or search spaces
              rsi_filter:
                indicator: RSI
                params: { period: {value: 14} }
            entry_rules:
              - condition: "ma_cross.entry AND rsi_filter.value < 30"
            exit_rules:
              - condition: "ma_cross.exit"
            ```
    2.  **Rule Parsing & Signal Aggregation**:
        * `StrategySignalGenerator` needs to parse these rules.
        * Each component indicator generates its primary signal series (e.g., `ma_cross.entry`, `rsi_filter.value`).
        * A new module/class will be responsible for taking these intermediate signal/value series and applying the logical rules to produce final entry/exit DataFrames.
* **Python Library Candidate**: `meqsap_signal_combiner`
    * **Purpose**: Parse rule strings and combine boolean/continuous signal series.
    * **Modules**:
        * `rule_engine.py`: Parses the rule strings (could use a simple expression evaluator or a dedicated parsing library if complex).
        * `aggregator.py`: Takes multiple pandas Series (signals/indicator values) and applies the parsed rules to generate final entry/exit signals.
    * **Integration**: `meqsap.backtest` uses this to generate signals for combined strategies.

---
### Phase 6: Automated Parameter Tuning for Combined Strategies

* **Goal**: Extend the `meqsap_optimizer` to tune parameters for the multi-indicator/signal strategies defined in Phase 5.
* **Building on**: Phase 2 (`meqsap_optimizer`), Phase 5 (`meqsap_signal_combiner`).
* **Details**:
    1.  **Expanded Parameter Space**: The optimizer now needs to handle a combined parameter space from all components of the strategy. If `ma_cross` has 2 tunable params and `rsi_filter` has 1, the search space is 3-dimensional.
    2.  **Optimizer Adaptation**: `meqsap_optimizer`'s `engine.py` should be capable of handling these larger, structured parameter sets.
    3.  **Objective Function & Constraints**: The objective function (including hold period considerations) remains central.
* **Python Library Candidate**: `meqsap_optimizer` (enhancements).

---
### Phase 7: Market Regime Detection and Initial Adaptation

* **Goal**: Introduce basic market regime detection and allow strategies to use different parameter sets or slightly varied rules for different regimes.
* **Building on**: All previous phases.
* **Details**:
    1.  **Regime Detection Module**:
        * Implement simple regime detection models (e.g., ATR for volatility, ADX for trend strength, a basic classifier on price patterns).
        * This module will output a regime series (e.g., "trending", "ranging", "volatile") for each day in the backtest period.
    2.  **Regime-Specific Configuration**:
        * Extend YAML to allow regime-specific parameter overrides or rule variations.
            ```yaml
            strategy_type: CombinedRuleStrategy
            # ... components ...
            regime_config:
              default_params: # Default component params
                ma_cross: { fast_ma: 20, slow_ma: 50 }
                rsi_filter: { period: 14 }
              regimes:
                - name: high_volatility
                  # condition_logic: e.g., ATR(10) > historical_ATR_percentile(75)
                  param_overrides:
                    ma_cross: { fast_ma: 10, slow_ma: 30 } # Tighter for volatility
                # - name: strong_trend ...
            # ... entry_rules, exit_rules ... (could also be regime-specific if logic gets complex)
            ```
    3.  **Backtesting Adaptation**:
        * The backtesting engine (`meqsap.backtest`) or the `StrategySignalGenerator` needs to:
            * Be aware of the current market regime for each data point.
            * Use the appropriate parameter set for signal generation based on the active regime.
            * `vectorbt`'s `Portfolio.from_signals` can accept `group_by` which could be used if signals are pre-generated per regime, or parameters are adjusted segment-wise. This can be complex.
* **Python Library Candidate**: `meqsap_market_regime`
    * **Purpose**: Detect market regimes and provide this information to the strategy execution.
    * **Modules**:
        * `detectors.py`: Implementations of various regime detection algorithms.
        * `regime_processor.py`: Logic to integrate regime data into the backtesting flow.
    * **Integration**: `meqsap.data` might be augmented to fetch/calculate regime data. `meqsap.backtest` would consume this.

---
### Phase 8: Automated Strategy Improvement - Heuristic Diagnostics & Modifications

* **Goal**: Implement the first version of the automated improvement loop. If a strategy underperforms its baseline, the system attempts to diagnose issues and heuristically apply modifications.
* **Building on**: Phase 3 (Baseline), Phase 6 (Combined Strategy Tuning), Phase 7 (Regimes).
* **Details**:
    1.  **Diagnostic Engine**:
        * Analyze backtest results: trade lists (especially losing trades), drawdown periods, performance in different regimes, hold period statistics.
        * Define a knowledge base of common strategy flaws and their potential indicators. Examples:
            * *Flaw*: Whipsaws. *Indicators*: Many small losses, low profit factor, high trade count in ranging markets. *Hold Period Link*: Short, unprofitable trades.
            * *Flaw*: Premature exits. *Indicators*: Small wins, missed larger moves, trades shorter than target hold.
            * *Flaw*: Late entries. *Indicators*: Entering after significant part of a move.
            * *Flaw*: Poor regime fit. *Indicators*: Good performance in one regime, bad in another.
    2.  **Modification Engine (Heuristic-Based)**:
        * Based on diagnostics, propose modifications to the strategy's YAML configuration (internally):
            * *Whipsaws?* -> "Try adding a trend filter (e.g., ADX)." "Try increasing MA periods." "Optimize parameters for current stock's volatility."
            * *Premature exits?* -> "Try wider take-profit levels." "Remove/adjust indicator X causing early exits." "Optimize exit parameters to align with target hold period."
            * *Poor regime fit?* -> "Try different parameters for regime Y." "Disable strategy in regime Z."
    3.  **Improvement Loop**:
        * Run initial/optimized strategy, compare to baseline.
        * If underperforming:
            * Invoke Diagnostic Engine.
            * Invoke Modification Engine to get a candidate modification.
            * Apply modification (generating a new internal strategy configuration).
            * Re-run parameter optimization (Phase 6) on this modified strategy.
            * Compare new result to baseline and previous best.
            * Repeat N times or until improvement goals are met.
    4.  **Explanation**: The "why" a strategy fails is based on the triggered diagnostic rules. The "improvement" is the modification applied.
* **Python Library Candidate**: `meqsap_strategy_doctor`
    * **Purpose**: Diagnose strategy weaknesses and suggest/apply heuristic improvements.
    * **Modules**:
        * `diagnostics.py`: Contains rules and functions for analyzing backtest results and trade patterns, including hold period adherence.
        * `modification_rules.py`: Knowledge base of heuristic modifications linked to diagnoses.
        * `improvement_engine.py`: Orchestrates the diagnose-modify-retest-compare loop.
    * **Integration**: Called by `meqsap.cli` after an initial optimization run if further improvement is desired. Uses all other modules.

---
### Phase 9: Advanced Optimization Techniques & Enhanced Explainability

* **Goal**: Integrate more sophisticated optimization algorithms and improve the system's ability to explain its decisions.
* **Building on**: Phase 8, `meqsap_optimizer`, `meqsap_strategy_doctor`.
* **Details**:
    1.  **Advanced Optimizers**:
        * Integrate Bayesian Optimization, Genetic Algorithms, or Particle Swarm Optimization into `meqsap_optimizer`. These can be more efficient for the potentially large and complex parameter spaces of combined, regime-aware strategies.
    2.  **Enhanced Explainability**:
        * Improve `meqsap_strategy_doctor`'s diagnostic output: Provide more detailed reasoning for identified flaws and chosen modifications.
        * Log the decision tree/path of the improvement loop: "Strategy A failed due to X. Tried modification M1, performance became P1. Tried M2, performance became P2. Selected M2 because..."
        * Visualization: If possible, visualize parameter sensitivity or feature importance (if any ML components are ever added, though current plan is heuristic).
        * Reporting: The final report should clearly articulate the "story" of how the strategy was improved, citing specific data points (e.g., "Reduced whipsaw losses by 15% by adding ADX filter, improving Sharpe from 0.5 to 0.8 in ranging periods for MSFT.").
* **Python Library Candidate**: `meqsap_optimizer` (enhancements), `meqsap_strategy_doctor` (enhancements).

---
### Phase 10: Analyst-in-the-Loop Interface & Strategy Management

* **Goal**: Provide a more refined interface for analysts to guide the automated discovery, review system suggestions, and manage the library of generated strategies.
* **Building on**: All previous phases.
* **Details**:
    1.  **Interactive CLI Enhancements (if not a web UI)**:
        * Allow analyst to set more nuanced goals (e.g., target Sharpe, max drawdown constraint, specific hold period distribution).
        * After a discovery run, present top N candidate strategies with their trade-offs.
        * Allow analyst to pick a strategy and request further refinement on specific aspects (e.g., "Improve exits for this strategy," "Make this strategy more robust to fees for Stock Y").
    2.  **Strategy Versioning/Templating**:
        * Ability to save promising strategy configurations (including parameter spaces and rules) found by the system.
        * These saved configurations can be used as starting points for new discovery tasks or for specific stocks.
    3.  **Enhanced Reporting for Discovery**:
        * Reports that summarize the entire discovery process: what was explored, what worked, what didn't, and why.
        * Comparative views of multiple auto-generated strategies.
    4.  **Override Mechanism**: Allow analysts to "lock" certain parameters or rules if they have strong convictions, while letting the system optimize others.
* **Python Library Candidate**: Primarily enhancements to `meqsap.cli` and `meqsap.reporting`. A new small utility `meqsap_strategy_manager` could handle saving/loading/versioning of strategy templates if it becomes complex.


## Proposed Python Libraries

Here are the libraries envisioned to modularize the advanced automation features for MEQSAP:

### 1. `meqsap_indicators_core` ⚙️

* **Core Features**:
    * Standardized definitions for technical indicators.
    * Management of indicator parameters, including fixed values, ranges, steps, and choices for optimization.
    * Calculation logic for each indicator, often wrapping libraries like `pandas-ta` but providing a consistent interface.
    * A registry for discovering and accessing available indicators.
    * Functionality for each indicator to declare its minimum required data length (e.g., `get_required_data_coverage_bars`).
* **Key Inputs**:
    * Market data (`pandas.DataFrame` with OHLCV columns).
    * Specific parameter values for an indicator (e.g., `{'period': 14}` for RSI).
    * Indicator name or type to instantiate.
* **Key Outputs**:
    * Calculated indicator series (`pandas.Series` or `pandas.DataFrame`, e.g., RSI values, MACD lines, Bollinger Bands).
    * Indicator metadata (name, parameter definitions, required data length).
    * Definitions of parameter search spaces for optimization.

---
### 2. `meqsap_optimizer` 📈

* **Core Features**:
    * Implementation of various parameter optimization algorithms (e.g., Grid Search, Random Search, Bayesian Optimization, Genetic Algorithms).
    * A framework for defining and using objective functions (e.g., Sharpe Ratio, Calmar Ratio, custom scores).
    * Integration with the backtesting engine to evaluate different parameter sets.
    * Management of the optimization process, including logging and tracking of tested parameters and their scores.
    * Support for constraints, including the target trade holding period.
* **Key Inputs**:
    * A strategy configuration object that includes parameter search spaces (from `meqsap_indicators_core` or combined strategy definitions).
    * A reference to the backtesting function (`run_complete_backtest` from the main MEQSAP project).
    * An objective function to maximize or minimize.
    * Market data (passed through to the backtester).
    * Optimization algorithm choice and its settings (e.g., number of iterations).
* **Key Outputs**:
    * The set of best-performing parameters found.
    * The performance score achieved by the best parameters.
    * Optionally, a history or log of the optimization process (e.g., all parameters tried and their scores).

---
### 3. `meqsap_signal_combiner` 🔗

* **Core Features**:
    * Parsing of rule strings or structured rule definitions that specify how to combine multiple signals or indicator conditions (e.g., "signal_A AND (indicator_B_value > X)").
    * Aggregation of multiple boolean signal series or continuous indicator value series based on the parsed logical rules (AND, OR, NOT, comparisons).
    * Generation of final entry and exit signal series (`pandas.DataFrame` with 'entry' and 'exit' boolean columns).
* **Key Inputs**:
    * A set of named intermediate signal series or indicator value series (`pandas.Series` or dict of Series).
    * A rule definition (e.g., a string like "entry_A AND condition_B", or a more structured JSON/dict representation of the logic).
* **Key Outputs**:
    * A final `pandas.DataFrame` containing 'entry' and 'exit' boolean columns, representing the combined signals.

---
### 4. `meqsap_market_regime` 🌪️☀️ (Optional, could be simpler if integrated)

* **Core Features**:
    * Implementations of algorithms to detect different market regimes (e.g., trending, mean-reverting, high/low volatility).
    * Methods to classify historical data into regimes based on indicators like ATR, ADX, or simple price action patterns.
    * Output a time series of regime states.
* **Key Inputs**:
    * Market data (`pandas.DataFrame` with OHLCV columns).
    * Configuration for the regime detection model (e.g., lookback periods, thresholds).
* **Key Outputs**:
    * A `pandas.Series` indexed by date, with values representing the detected market regime for each period (e.g., "trending", "ranging").

---
### 5. `meqsap_strategy_doctor` 🩺

* **Core Features**:
    * **Diagnostic Engine**: Analyzes backtest results (trade lists, performance metrics, drawdown periods, regime performance, hold period statistics) to identify common strategy flaws.
    * **Knowledge Base**: Contains a set of predefined strategy pitfalls (e.g., whipsaws, premature exits, poor regime fit) and their typical symptoms.
    * **Modification Engine**: Based on diagnostic findings, heuristically suggests or applies modifications to a strategy configuration. Modifications can include:
        * Adding/removing indicator filters.
        * Adjusting parameter ranges for re-optimization.
        * Changing combination rules.
        * Suggesting different indicators for specific regimes.
    * **Improvement Loop Orchestration**: Manages the iterative cycle of diagnose -> modify -> re-test (re-optimize) -> compare.
    * **Explanation Generation**: Provides reasons for diagnosed flaws and the rationale behind suggested modifications, including how they relate to the target hold period.
* **Key Inputs**:
    * Full backtest analysis results (including detailed trade logs, performance metrics, and baseline comparison).
    * The current strategy configuration (potentially with parameter search spaces).
    * Baseline strategy performance.
    * Target hold period constraints.
* **Key Outputs**:
    * Diagnostic reports explaining identified strategy weaknesses.
    * A modified strategy configuration (as a data structure, e.g., dict for new YAML) with suggested changes.
    * A log of the improvement attempts and their outcomes.

---
### 6. `meqsap_strategy_manager` 🗂️ (Potential utility)

* **Core Features**:
    * Saving promising strategy configurations (including parameters, rules, and parameter search spaces) to a structured format (e.g., enhanced YAML or a simple database).
    * Loading saved strategy configurations to be used as templates or starting points for new analyses or automated discovery tasks.
    * Basic versioning or tagging of saved strategies.
* **Key Inputs**:
    * Strategy configuration objects or dictionaries.
    * Metadata for the strategy (e.g., name, description, performance summary).
    * Commands to save, load, list, or delete strategies.
* **Key Outputs**:
    * Stored strategy files/records.
    * Loaded strategy configuration objects.
    * Lists of available saved strategies.

These libraries would allow MEQSAP's main `src/meqsap/` codebase (especially `cli.py`, `backtest.py`, and `config.py`) to orchestrate these more advanced capabilities by calling functions and classes from these specialized, independently developed, and testable modules.