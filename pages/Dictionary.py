import streamlit as st

# Dictionary of technical terms
TECHNICAL_TERMS = {
    "SMA (Simple Moving Average)": {
        "definition": "A calculation that takes the arithmetic mean of a given set of values over a specific time period.",
        "formula": "SMA = (Sum of closing prices over n periods) / n",
        "usage": "Used to identify trends and support/resistance levels."
    },
    "RSI (Relative Strength Index)": {
        "definition": "A momentum oscillator that measures the speed and change of price movements on a scale from 0 to 100.",
        "formula": "RSI = 100 - (100 / (1 + RS)) where RS = Average Gain / Average Loss",
        "usage": "Identifies overbought (>70) and oversold (<30) conditions."
    },
    "MACD (Moving Average Convergence Divergence)": {
        "definition": "A trend-following momentum indicator that shows the relationship between two moving averages of a security's price.",
        "formula": "MACD = EMA(12) - EMA(26), Signal = EMA(9) of MACD",
        "usage": "Signals when to buy/sell based on crossovers and divergences."
    },
    "Bollinger Bands": {
        "definition": "A volatility indicator consisting of a moving average and two standard deviation bands above and below it.",
        "formula": "Upper Band = SMA + (2 × Standard Deviation), Lower Band = SMA - (2 × Standard Deviation)",
        "usage": "Identifies volatility breakouts and price reversals."
    },
    "Support Level": {
        "definition": "A price level where buying pressure is strong enough to prevent the price from falling further.",
        "usage": "Areas where traders expect buying interest to emerge."
    },
    "Resistance Level": {
        "definition": "A price level where selling pressure is strong enough to prevent the price from rising further.",
        "usage": "Areas where traders expect selling interest to emerge."
    },
    "Pip": {
        "definition": "The smallest price move that a given exchange rate can make. Most currency pairs are priced to four decimal places.",
        "usage": "Used to measure price movements and calculate profit/loss."
    },
    "Lot Size": {
        "definition": "The number of currency units in a trading position. Standard lot = 100,000 units.",
        "usage": "Determines position size and risk exposure."
    },
    "Stop Loss": {
        "definition": "A predetermined price level where a trade will be automatically closed to limit losses.",
        "usage": "Risk management tool to protect capital."
    },
    "Take Profit": {
        "definition": "A predetermined price level where a trade will be automatically closed to secure profits.",
        "usage": "Locks in gains when target price is reached."
    },
    "ATR (Average True Range)": {
        "definition": "A volatility indicator that measures the average range between high and low prices over a specified period.",
        "formula": "ATR = (Previous ATR × (n-1) + Current TR) / n where TR = max(High-Low, High-Previous Close, Low-Previous Close)",
        "usage": "Measures market volatility and helps determine appropriate stop loss levels and position sizing."
    },
    "Momentum Indicator": {
        "definition": "A technical indicator that measures the rate of change in price movements over a specified period.",
        "formula": "Momentum = Current Price - Price n periods ago",
        "usage": "Identifies the strength and speed of price movements. Positive values indicate upward momentum, negative values indicate downward momentum."
    },
    "RSI Divergence": {
        "definition": "A situation where the price trend and RSI indicator move in opposite directions, signaling potential reversals.",
        "usage": "Bullish divergence: Price makes lower lows while RSI makes higher lows. Bearish divergence: Price makes higher highs while RSI makes lower highs."
    },
    "Signal Confirmation Count": {
        "definition": "The minimum number of technical indicators that must align in the same direction before a trade signal is generated.",
        "usage": "Reduces false signals by requiring multiple confirmations. Higher counts mean more conservative trading with fewer but higher-quality signals."
    },
    "Strategy Presets": {
        "definition": "Pre-configured parameter sets optimized for different market conditions and trading styles.",
        "usage": "Quick way to switch between trading strategies: Aggressive (fast signals), Balanced (moderate), Conservative (high-quality signals), Trending (directional moves), Oscillating (range-bound markets)."
    },
    "Dynamic Position Sizing": {
        "definition": "Automatic adjustment of trade size based on account balance and risk percentage to maintain consistent risk exposure.",
        "formula": "Lot Size = (Account Balance × Risk Percentage) / (Stop Loss Pips × 10000)",
        "usage": "Ensures each trade risks the same percentage of account equity, automatically reducing position size as account grows or shrinks."
    },
    "Sharpe Ratio": {
        "definition": "A measure of risk-adjusted return that indicates the excess return per unit of risk taken.",
        "formula": "Sharpe Ratio = (Portfolio Return - Risk-Free Rate) / Portfolio Standard Deviation",
        "usage": "Higher values indicate better risk-adjusted performance. Values above 1.0 are generally considered good, above 2.0 excellent."
    },
    "Profit Factor": {
        "definition": "The ratio of gross profit to gross loss over a period of time.",
        "formula": "Profit Factor = Total Profits / Total Losses",
        "usage": "Values above 1.5 indicate profitable strategies. Higher values suggest better risk-reward ratios."
    },
    "Volatility": {
        "definition": "A statistical measure of the dispersion of returns for a given security or market index.",
        "usage": "Higher volatility means larger price swings and potentially higher risk/reward."
    },
    "Machine Learning Model": {
        "definition": "An algorithm trained on historical data to make predictions about future price movements.",
        "usage": "Combines multiple indicators to generate more sophisticated trading signals."
    },
    "Random Forest": {
        "definition": "An ensemble learning method that constructs multiple decision trees and merges their results.",
        "usage": "Reduces overfitting and improves prediction accuracy compared to single decision trees."
    }
        "usage": "Measures risk and portfolio performance."
    },
    "Volatility": {
        "definition": "A statistical measure of the dispersion of returns for a given security or market index.",
        "usage": "Higher volatility means larger price swings and potentially higher risk/reward."
    },
    "Machine Learning Model": {
        "definition": "An algorithm trained on historical data to make predictions about future price movements.",
        "usage": "Combines multiple indicators to generate more sophisticated trading signals."
    },
    "Random Forest": {
        "definition": "An ensemble learning method that constructs multiple decision trees and merges their results.",
        "usage": "Reduces overfitting and improves prediction accuracy compared to single decision trees."
    }
}

def show_dictionary():
    st.title("📚 Technical Dictionary")
    st.markdown("---")

    st.markdown("""
    ### Understanding Trading Terminology

    This dictionary explains the key technical terms and concepts used in forex trading and algorithmic strategies.
    Click on any term below to expand its explanation.
    """)

    # Search functionality
    search_term = st.text_input("🔍 Search terms:", placeholder="Type to search...")

    # Filter terms based on search
    if search_term:
        filtered_terms = {k: v for k, v in TECHNICAL_TERMS.items()
                         if search_term.lower() in k.lower() or
                         search_term.lower() in str(v).lower()}
    else:
        filtered_terms = TECHNICAL_TERMS

    st.markdown(f"**Showing {len(filtered_terms)} of {len(TECHNICAL_TERMS)} terms**")

    # Display terms in expandable sections
    for term, details in filtered_terms.items():
        with st.expander(f"**{term}**"):
            st.markdown(f"**Definition:** {details['definition']}")

            if 'formula' in details:
                st.markdown(f"**Formula:** `{details['formula']}`")

            st.markdown(f"**Usage:** {details['usage']}")

            st.markdown("---")

    # Additional resources section
    st.markdown("---")
    st.header("📖 Additional Resources")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Technical Analysis")
        st.markdown("""
        - **Candlestick Patterns**: Price action patterns that predict reversals
        - **Fibonacci Retracements**: Mathematical ratios for support/resistance
        - **Volume Analysis**: Trading volume indicators and patterns
        """)

    with col2:
        st.subheader("🤖 Algorithmic Trading")
        st.markdown("""
        - **Backtesting**: Testing strategies on historical data
        - **Risk Management**: Position sizing and drawdown control
        - **Performance Metrics**: Sharpe ratio, win rate, profit factor
        """)

if __name__ == "__main__":
    show_dictionary()