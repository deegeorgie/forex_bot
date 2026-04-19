import streamlit as st
import MetaTrader5 as mt5
import config
from data import get_data
from strategy import compute_indicators, generate_signal
from backtest import backtest_strategy
import plotly.graph_objects as go
import pandas as pd

st.title("📈 Strategy Backtesting")
st.markdown("---")

st.markdown("""
### Test Your Trading Strategy

Backtesting allows you to evaluate how your trading strategy would have performed
on historical data. This helps you understand the strategy's strengths and weaknesses
before using it with real money.
""")

# Backtesting parameters
st.sidebar.header("⚙️ Backtesting Parameters")

available_symbols = config.AVAILABLE_SYMBOLS or ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]
symbol = st.sidebar.selectbox("Symbol", available_symbols, index=0)

timeframe_options = {"M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5,
                    "M15": mt5.TIMEFRAME_M15, "H1": mt5.TIMEFRAME_H1}
timeframe_label = st.sidebar.selectbox("Timeframe", list(timeframe_options.keys()), index=1)
timeframe = timeframe_options[timeframe_label]

# Date range selection
st.sidebar.subheader("📅 Date Range")
start_date = st.sidebar.date_input("Start Date", value=pd.Timestamp.now() - pd.Timedelta(days=30))
end_date = st.sidebar.date_input("End Date", value=pd.Timestamp.now())

# Strategy parameters
st.sidebar.subheader("🎯 Strategy Settings")
initial_balance = st.sidebar.number_input("Initial Balance ($)", min_value=1000, value=10000, step=1000)
risk_per_trade = st.sidebar.slider("Risk per Trade (%)", 0.1, 5.0, 1.0, 0.1)
use_ml = st.sidebar.checkbox("🤖 Use ML Signals", value=False,
                              help="Combine technical analysis with machine learning predictions")

def display_backtest_results(results, symbol, timeframe, start_date, end_date):
    """Display backtest results in a comprehensive format."""

    st.header("📊 Backtest Results")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Trades", results['total_trades'])
        st.metric("Win Rate", f"{results.get('win_rate', 0):.1f}%")

    with col2:
        st.metric("Final Balance", f"${results['final_balance']:.2f}")
        pnl = results['final_balance'] - results.get('initial_balance', 10000)
        st.metric("Total P&L", f"${pnl:.2f}", delta=f"${pnl:.2f}")

    with col3:
        st.metric("Max Drawdown", f"{results.get('max_drawdown', 0):.2f}%")
        st.metric("Sharpe Ratio", f"{results.get('sharpe_ratio', 0):.2f}")

    with col4:
        st.metric("Profit Factor", f"{results.get('profit_factor', 0):.2f}")
        st.metric("Avg Trade", f"${results.get('avg_trade_pnl', 0):.2f}")

    # Performance chart
    st.subheader("💰 Equity Curve")
    if 'equity_curve' in results:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(range(len(results['equity_curve']))),
                                y=results['equity_curve'],
                                mode='lines',
                                name='Equity',
                                line=dict(color='green', width=2)))
        fig.update_layout(title="Equity Curve",
                         xaxis_title="Trades",
                         yaxis_title="Balance ($)")
        st.plotly_chart(fig, use_container_width=True)

    # Trade analysis
    if 'trades' in results and results['trades']:
        st.subheader("📋 Trade History")

        trades_df = pd.DataFrame(results['trades'])
        if not trades_df.empty:
            # Format the dataframe for display
            display_df = trades_df.copy()
            display_df['Return %'] = ((display_df['exit'] - display_df['entry']) / display_df['entry'] * 100).round(2)
            display_df = display_df.rename(columns={'type': 'Type', 'entry': 'Entry', 'exit': 'Exit', 'pnl': 'P&L'})
            display_df['P&L'] = display_df['P&L'].round(2)
            display_df['Entry'] = display_df['Entry'].round(5)
            display_df['Exit'] = display_df['Exit'].round(5)

            st.dataframe(display_df[['Type', 'Entry', 'Exit', 'P&L', 'Return %']].tail(20),
                        use_container_width=True)

            # Trade statistics
            winning_trades = len([t for t in results['trades'] if t['pnl'] > 0])
            losing_trades = len([t for t in results['trades'] if t['pnl'] < 0])

            st.subheader("📈 Trade Statistics")
            stat_col1, stat_col2, stat_col3 = st.columns(3)

            with stat_col1:
                st.metric("Winning Trades", winning_trades)
            with stat_col2:
                st.metric("Losing Trades", losing_trades)
            with stat_col3:
                st.metric("Breakeven Trades", results['total_trades'] - winning_trades - losing_trades)

    # Strategy insights
    st.subheader("🎯 Strategy Insights")

    insights = []

    if results.get('win_rate', 0) > 60:
        insights.append("✅ Excellent win rate above 60%")
    elif results.get('win_rate', 0) > 50:
        insights.append("👍 Good win rate above 50%")
    else:
        insights.append("⚠️ Win rate below 50% - consider strategy improvements")

    if results.get('profit_factor', 0) > 1.5:
        insights.append("✅ Strong profit factor above 1.5")
    elif results.get('profit_factor', 0) > 1.0:
        insights.append("👍 Profitable strategy (profit factor > 1.0)")
    else:
        insights.append("❌ Unprofitable strategy (profit factor < 1.0)")

    if results.get('max_drawdown', 100) < 10:
        insights.append("✅ Low drawdown under 10%")
    elif results.get('max_drawdown', 100) < 20:
        insights.append("👍 Moderate drawdown under 20%")
    else:
        insights.append("⚠️ High drawdown - consider risk management improvements")

    for insight in insights:
        st.info(insight)

def run_backtest(symbol, timeframe, start_date, end_date, initial_balance, risk_per_trade, use_ml):
    """Run the backtesting analysis."""
    try:
        with st.spinner("Running backtest... This may take a moment."):

            # Fetch data
            df = get_data(symbol, timeframe, 5000)  # Get plenty of data

            # Filter by date range
            df['time'] = pd.to_datetime(df['time'])
            mask = (df['time'].dt.date >= start_date) & (df['time'].dt.date <= end_date)
            df = df[mask]

            if len(df) < 100:
                st.error("❌ Not enough data for the selected date range. Try a longer period.")
                return
            
            # Check for large datasets that may be memory intensive
            if len(df) > 5000:
                st.warning(f"⚠️ Large dataset ({len(df)} rows) may be memory intensive. Consider shorter date ranges for better performance.")

            # Compute indicators
            df = compute_indicators(df)

            # Run backtest with dynamic risk management
            results = backtest_strategy(df, initial_balance, risk_per_trade / 100.0, use_ml)

        # Display results
        display_backtest_results(results, symbol, timeframe, start_date, end_date)

    except Exception as e:
        st.error(f"❌ Backtest failed: {e}")
        st.info("💡 Make sure MT5 is running and you have sufficient historical data.")

# Run backtest button
if st.sidebar.button("🚀 Run Backtest", type="primary"):
    run_backtest(symbol, timeframe, start_date, end_date, initial_balance, risk_per_trade, use_ml)