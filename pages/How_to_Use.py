import streamlit as st

st.title("📚 How to Use - Forex Algo Trading Dashboard")

st.markdown("""
Welcome to your comprehensive Forex Algorithmic Trading Dashboard! This guide will help you understand how to effectively use all the features of this application for successful trading.
""")

# Overview Section
st.header("🎯 Overview")
st.markdown("""
This application provides a complete trading solution with:
- **Real-time trading** with MetaTrader 5 integration
- **Advanced technical analysis** with 7+ indicators (SMA, RSI, MACD, Bollinger Bands, ATR, Momentum, RSI Divergence)
- **Machine learning signals** with Random Forest models
- **Strategy optimization** with 5 preset configurations
- **Comprehensive settings** with tabbed interface
- **Risk management** with dynamic position sizing
- **Backtesting** with ML signal integration
- **Paper trading** mode for safe practice
""")

# Getting Started
st.header("🚀 Getting Started")

with st.expander("1. MetaTrader 5 Setup", expanded=True):
    st.markdown("""
    **Before using the app, you need to set up MetaTrader 5:**

    1. **Install MetaTrader 5** from your broker's website
    2. **Create a demo account** (recommended for beginners)
    3. **Enable algorithmic trading**:
       - Open MT5 terminal
       - Click the **"Algo Trading"** button in the toolbar
       - Make sure it shows as **enabled** (green)
    4. **Configure account credentials** in the Settings page
    """)

with st.expander("2. Application Setup"):
    st.markdown("""
    **First time setup:**

    1. **Navigate to Settings page** using the sidebar
    2. **Enter your MT5 credentials**:
       - Login number
       - Password
       - Server name
    3. **Test the connection** to ensure everything works
    4. **Configure trading parameters** (risk management, lot sizes, etc.)
    """)

# Trading Dashboard
st.header("📊 Trading Dashboard")

with st.expander("Understanding the Interface"):
    st.markdown("""
    The Trading Dashboard is your main trading interface:

    **📈 Charts & Indicators:**
    - Real-time price charts with candlestick patterns
    - Technical indicators: SMA, RSI, MACD, Bollinger Bands
    - Machine learning signals (when enabled)

    **⚙️ Sidebar Controls:**
    - **Symbol selection**: Choose currency pairs to trade
    - **Timeframe**: Select chart timeframe (1M, 5M, 15M, 1H, etc.)
    - **Lot size**: Set position size (0.01 to 1.0 lots)
    - **Risk management**: Enable automatic position sizing
    - **Paper trading**: Practice without real money
    - **Auto trading**: Let ML signals execute trades automatically
    """)

with st.expander("Manual Trading"):
    st.markdown("""
    **To place manual trades:**

    1. **Select your symbol** (e.g., EURUSD, GBPUSD)
    2. **Choose timeframe** for analysis
    3. **Analyze indicators**:
       - Green signals suggest BUY
       - Red signals suggest SELL
    4. **Set lot size** in sidebar
    5. **Enable Paper Trading** if practicing
    6. **Click BUY or SELL** buttons to execute

    **Risk Management:**
    - Enable "Use Risk Management" for automatic lot sizing
    - Set stop loss and take profit levels in config
    """)

with st.expander("Automated Trading"):
    st.markdown("""
    **Machine Learning Trading:**

    1. **Enable "Use Machine Learning for Signals"**
    2. **Enable "Enable Auto Trading"** (use with caution!)
    3. **Monitor signals** in the chart
    4. **The system will automatically execute** trades based on ML predictions

    ⚠️ **Warning**: Auto trading carries significant risk. Start with paper trading!
    """)

# Backtesting
st.header("📈 Backtesting")

with st.expander("Strategy Testing"):
    st.markdown("""
    **Test your strategies before live trading:**

    1. **Go to Backtesting page**
    2. **Select symbol** and date range (30-90 days recommended)
    3. **Enable ML Signals** checkbox for enhanced predictions
    4. **Choose strategy parameters** or use presets from Strategy Optimizer
    5. **Run backtest** to see historical performance
    6. **Analyze comprehensive results**:
       - Total return and profit factor
       - Win rate and total trades
       - Maximum drawdown and Sharpe ratio
       - Equity curve visualization
       - Individual trade history
    """)

with st.expander("ML-Enhanced Backtesting"):
    st.markdown("""
    **Machine Learning Integration:**

    - **🤖 Use ML Signals**: Combines technical analysis with AI predictions
    - **Enhanced Features**: Includes ATR, momentum, and RSI divergence
    - **Dynamic Position Sizing**: Automatically adjusts lot sizes based on risk
    - **Advanced Metrics**: Sharpe ratio, profit factor, and drawdown analysis

    **ML Signal Benefits:**
    - More sophisticated entry/exit signals
    - Reduced false signals through pattern recognition
    - Better performance in various market conditions
    - Probability-based trading decisions
    """)

# Settings
st.header("⚙️ Settings & Configuration")

with st.expander("Comprehensive Settings Interface"):
    st.markdown("""
    **The Settings page now features 5 organized tabs:**

    **📊 Basic Tab:**
    - Trading symbol selection (EURUSD, GBPUSD, etc.)
    - Chart timeframe (M1, M5, M15, H1, D1)
    - Lot size configuration

    **🎯 Strategy Tab:**
    - **SMA Settings**: Short and long period moving averages
    - **RSI Configuration**: Period, overbought/oversold levels
    - **MACD Parameters**: Fast, slow, and signal periods
    - **Bollinger Bands**: Period and standard deviation
    - **Signal Confirmation**: Minimum indicators required for trade signals

    **🔗 MT5 Tab:**
    - Account login credentials
    - Server configuration
    - Connection testing

    **💰 Risk Tab:**
    - Stop loss and take profit levels (in pips)
    - Risk percentage per trade
    - Maximum drawdown limits
    - Dynamic position sizing options

    **� Risk Tab:**
    - Stop loss and take profit levels (in pips)
    - Risk percentage per trade
    - Maximum drawdown limits
    - Dynamic position sizing options

    **🔄 Advanced Tab:**
    - Data points for analysis (200-5000)
    - Machine learning toggle
    - Additional configuration options
    """)

with st.expander("Quick Configuration Tips"):
    st.markdown("""
    **For Beginners:**
    - Start with default settings
    - Use "Balanced" preset from Strategy Optimizer
    - Enable paper trading first

    **For Advanced Users:**
    - Fine-tune individual parameters
    - Test changes in backtesting
    - Save successful configurations
    """)

# Strategy Optimization
st.header("🎯 Strategy Optimization")

with st.expander("Strategy Presets Overview"):
    st.markdown("""
    **The Strategy Optimizer provides 5 pre-configured trading strategies:**

    **🏎️ Aggressive Preset:**
    - Fast signals with tight parameters
    - Higher frequency trading
    - Best for: Active traders, shorter timeframes
    - Risk: More false signals, higher trading costs

    **⚖️ Balanced Preset:**
    - Moderate parameters for steady performance
    - Good balance of win rate and profit factor
    - Best for: Most traders, general market conditions
    - Recommended for beginners

    **🛡️ Conservative Preset:**
    - Strict criteria for high-quality signals
    - Lower frequency but higher accuracy
    - Best for: Risk-averse traders, trending markets
    - Focus: Quality over quantity

    **📈 Trending Preset:**
    - Optimized for strong directional moves
    - Wider stops for trending markets
    - Best for: Bull/bear markets, longer timeframes
    - Strategy: Catch major moves

    **📊 Oscillating Preset:**
    - Designed for range-bound markets
    - Frequent signals in sideways markets
    - Best for: Ranging markets, pairs with low volatility
    - Focus: Mean reversion strategies
    """)

with st.expander("Using Strategy Presets"):
    st.markdown("""
    **How to apply presets:**

    1. **Navigate to Strategy Optimizer page**
    2. **Review preset descriptions** and performance expectations
    3. **Compare parameters** in the side-by-side table
    4. **Click "Apply Preset"** for your chosen strategy
    5. **Test in Backtesting** before live trading
    6. **Fine-tune parameters** if needed in Settings

    **Timeframe Recommendations:**
    - **M1/M5**: Use Aggressive or Oscillating presets
    - **M15/H1**: Balanced or Conservative presets work well
    - **H4/D1**: Trending preset for longer-term moves
    """)

with st.expander("Optimization Tips"):
    st.markdown("""
    **Strategy Selection Guide:**
    - **High volatility pairs** (GBPUSD, GBPJPY): Use Conservative preset
    - **Low volatility pairs** (EURCHF, USDCHF): Try Oscillating preset
    - **Trending markets**: Trending preset
    - **Sideways markets**: Oscillating preset
    - **General use**: Start with Balanced preset

    **Performance Metrics to Monitor:**
    - **Win Rate**: Target 50%+
    - **Profit Factor**: Target 1.5+
    - **Max Drawdown**: Keep under 10%
    - **Sharpe Ratio**: Values >1.0 indicate good risk-adjusted returns
    """)

# Safety & Best Practices
st.header("🛡️ Safety & Best Practices")

with st.expander("Risk Management"):
    st.markdown("""
    **Essential risk management rules:**

    ✅ **Always start with paper trading**
    ✅ **Use stop loss orders** (never trade without them)
    ✅ **Risk no more than 1-2%** of your account per trade
    ✅ **Diversify** across different currency pairs
    ✅ **Avoid emotional trading** - stick to your strategy
    ✅ **Regularly review** your trading performance
    """)

with st.expander("Common Mistakes to Avoid"):
    st.markdown("""
    ❌ **Don't over-leverage** (keep lot sizes small)
    ❌ **Don't chase the market** (wait for proper signals)
    ❌ **Don't trade based on emotions** (fear/greed)
    ❌ **Don't ignore risk management** rules
    ❌ **Don't trade with money you can't afford to lose**
    ❌ **Don't enable auto-trading** without thorough testing
    """)

# Understanding Indicators
st.header("📊 Understanding Indicators")

with st.expander("Technical Indicators"):
    st.markdown("""
    **SMA (Simple Moving Average):**
    - Shows average price over a period
    - Crossovers can signal trend changes
    - Configurable short/long periods (default: 50/200)

    **RSI (Relative Strength Index):**
    - Measures price momentum (0-100)
    - Above 70: Overbought (potential sell)
    - Below 30: Oversold (potential buy)
    - Configurable period and levels (default: 14, 30/70)

    **MACD (Moving Average Convergence Divergence):**
    - Shows relationship between two moving averages
    - Signal line crossovers indicate momentum changes
    - Configurable fast/slow/signal periods (default: 12/26/9)

    **Bollinger Bands:**
    - Shows volatility and price levels
    - Price touching upper band: Potential sell signal
    - Price touching lower band: Potential buy signal
    - Configurable period and standard deviation (default: 20, 2.0)

    **ATR (Average True Range):**
    - Measures market volatility
    - Higher values indicate more volatile markets
    - Used for dynamic stop loss placement and position sizing

    **Momentum Indicator:**
    - Measures rate of price change
    - Positive values: Upward momentum
    - Negative values: Downward momentum
    - Helps confirm trend strength

    **RSI Divergence:**
    - Identifies potential reversals
    - Bullish: Price lower lows, RSI higher lows
    - Bearish: Price higher highs, RSI lower highs
    - Advanced signal confirmation tool
    """)

with st.expander("Signal Confirmation System"):
    st.markdown("""
    **Multi-Indicator Signals:**
    - System requires 1-4 indicators to align for trade signals
    - Configurable confirmation count in Settings
    - Higher counts = more conservative (fewer but better signals)
    - Lower counts = more aggressive (more signals, higher risk)

    **Signal Types:**
    - **MACD + Histogram**: Momentum confirmation
    - **Bollinger Bands + RSI**: Volatility + momentum
    - **SMA Trend**: Moving average alignment
    - **RSI Alone**: Pure momentum signal
    - **Momentum**: Price acceleration confirmation
    """)

with st.expander("Machine Learning Signals"):
    st.markdown("""
    **Enhanced ML Model:**
    - Trained on 5000+ historical data points
    - Features: All technical indicators + ATR + momentum
    - Random Forest algorithm for robust predictions
    - Combines multiple signals for higher accuracy

    **Signal Interpretation:**
    - **Strong Buy/Sell**: High confidence signals (>70% probability)
    - **Neutral**: Wait for better conditions
    - **Combined with technical analysis** for best results
    - **Dynamic position sizing** based on signal strength
    """)

# Troubleshooting
st.header("🔧 Troubleshooting")

with st.expander("Common Issues"):
    st.markdown("""
    **"AutoTrading disabled by client":**
    - Enable the "Algo Trading" button in MT5 terminal

    **"Unsupported filling mode":**
    - This is automatically handled by the app (tries multiple modes)

    **Connection errors:**
    - Check MT5 credentials in Settings
    - Ensure MT5 terminal is running
    - Verify internet connection

    **No signals appearing:**
    - Check if ML model is trained (Settings page)
    - Ensure sufficient historical data
    """)

# Final Notes
st.header("📝 Final Notes")

st.markdown("""
**Remember:**
- Trading involves risk - only trade with money you can afford to lose
- Start with paper trading to gain experience
- Backtest strategies before using them live
- Keep learning and adapting your approach
- Use proper risk management at all times

**Happy Trading!** 🎯

For questions or issues, check the troubleshooting section above or review the Dictionary page for trading terminology.
""")

# Footer
st.markdown("---")
st.markdown("*Forex Algo Trading Dashboard v2.0 - Advanced Edition*")