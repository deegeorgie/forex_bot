import streamlit as st
import MetaTrader5 as mt5
from mt5_connector import connect, place_order, get_account_balance, get_account_equity, calculate_lot_size, is_algorithmic_trading_enabled
from data import get_data
from strategy import compute_indicators, generate_signal, train_ml_model, load_ml_model
import config
import plotly.graph_objects as go
import logging
import pandas as pd
from typing import List, Dict

logging.basicConfig(level=logging.INFO)

st.title("📊 Forex Algo Trading Dashboard")

# Sidebar controls
st.sidebar.header("⚙️ Trading Controls")

# Account connection
try:
    connect()
    balance = get_account_balance()
    equity = get_account_equity()
    drawdown = (balance - equity) / balance if balance > 0 else 0

    st.sidebar.success("✅ MT5 Connected")
    st.sidebar.metric("Balance", f"${balance:.2f}")
    st.sidebar.metric("Equity", f"${equity:.2f}")
    st.sidebar.metric("Drawdown", f"{drawdown:.1%}")

    if drawdown > config.MAX_DRAWDOWN_PERCENTAGE:
        st.sidebar.error("⚠️ Maximum drawdown exceeded!")
        trading_enabled = False
    else:
        trading_enabled = True

except Exception as e:
    st.sidebar.error(f"❌ MT5 Connection Failed: {e}")
    st.stop()

# Trading parameters
symbol = st.sidebar.selectbox("Symbol", config.AVAILABLE_SYMBOLS,
                              index=config.AVAILABLE_SYMBOLS.index(config.SYMBOL))

timeframe_options = {"M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5,
                    "M15": mt5.TIMEFRAME_M15, "H1": mt5.TIMEFRAME_H1}
timeframe_label = st.sidebar.selectbox("Timeframe", list(timeframe_options.keys()),
                                       index=list(timeframe_options.keys()).index(config.TIMEFRAME))
timeframe = timeframe_options[timeframe_label]

lot = st.sidebar.slider("Lot size", 0.01, 1.0, config.LOT)
use_risk_management = st.sidebar.checkbox("Use Risk Management")
paper_trading = st.sidebar.checkbox("Paper Trading Mode")
auto_trade = st.sidebar.checkbox("Enable Auto Trading")
use_ml_signals = st.sidebar.checkbox("Use Machine Learning for Signals")

# Check algorithmic trading status
if not paper_trading:
    algo_trading_enabled = is_algorithmic_trading_enabled()
    if algo_trading_enabled:
        st.sidebar.success("✅ Algorithmic trading enabled")
    else:
        st.sidebar.error("❌ Algorithmic trading disabled")
        st.sidebar.info("💡 Enable 'Algo Trading' button in MT5 terminal")

# Risk management
if use_risk_management:
    try:
        calculated_lot = calculate_lot_size(balance, config.RISK_PERCENTAGE, config.STOP_LOSS_PIPS, symbol)
        lot = min(lot, calculated_lot)
        st.sidebar.info(f"📊 Calculated lot: {calculated_lot:.2f}")
    except Exception as e:
        st.sidebar.error(f"❌ Risk calculation failed: {e}")

# Cache data
@st.cache_data(ttl=300)
def get_cached_data(symbol, timeframe):
    return get_data(symbol, timeframe)

@st.cache_data
def get_cached_indicators(df):
    return compute_indicators(df)

def execute_trade(action, symbol, lot, paper_trading):
    """Execute a trade order."""
    try:
        if paper_trading:
            st.success(f"📝 Paper {action} order simulated - {lot} lots of {symbol}")
        else:
            # Check if algorithmic trading is enabled
            if not is_algorithmic_trading_enabled():
                st.error("❌ Algorithmic trading is disabled in MetaTrader 5 terminal. Please enable the 'Algo Trading' button in MT5.")
                st.info("💡 To enable algorithmic trading: Open MetaTrader 5 → Click the 'Algo Trading' button in the toolbar → Make sure it's green/active")
                return

            order_type = mt5.ORDER_TYPE_BUY if action == "BUY" else mt5.ORDER_TYPE_SELL
            place_order(symbol, lot, order_type, config.STOP_LOSS_PIPS, config.TAKE_PROFIT_PIPS)
            st.success(f"✅ {action} order executed - {lot} lots of {symbol}")
    except Exception as e:
        st.error(f"❌ Failed to execute {action} order: {e}")

# Load and process data
try:
    df = get_cached_data(symbol, timeframe)
    df = get_cached_indicators(df)
    signal = generate_signal(df, use_ml=use_ml_signals)
except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
    st.stop()

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"📈 {symbol} - {timeframe_label} | Signal: **{signal}**")

    # Price chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['time'], y=df['close'], name="Price", line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df['time'], y=df['SMA_50'], name="SMA 50", line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df['time'], y=df['SMA_200'], name="SMA 200", line=dict(color='red')))
    fig.update_layout(title=f"{symbol} Price Chart", xaxis_title="Time", yaxis_title="Price")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Trading buttons
    st.subheader("🎯 Quick Trade")

    if st.button("🟢 BUY", type="primary", disabled=not trading_enabled):
        execute_trade("BUY", symbol, lot, paper_trading)

    if st.button("🔴 SELL", type="secondary", disabled=not trading_enabled):
        execute_trade("SELL", symbol, lot, paper_trading)

    # Signal indicator
    st.subheader("📊 Current Signal")
    if signal == "BUY":
        st.success("🟢 BUY SIGNAL")
    elif signal == "SELL":
        st.error("🔴 SELL SIGNAL")
    else:
        st.warning("🟡 HOLD SIGNAL")

# Technical indicators charts
st.header("📊 Technical Analysis")

tab1, tab2, tab3 = st.tabs(["RSI", "MACD", "Bollinger Bands"])

with tab1:
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df['time'], y=df['RSI'], name="RSI", line=dict(color='purple')))
    fig_rsi.add_hline(y=70, line_dash="dash", annotation_text="Overbought")
    fig_rsi.add_hline(y=30, line_dash="dash", annotation_text="Oversold")
    fig_rsi.update_layout(title="RSI Indicator", xaxis_title="Time", yaxis_title="RSI")
    st.plotly_chart(fig_rsi, use_container_width=True)

with tab2:
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(x=df['time'], y=df['MACD'], name="MACD", line=dict(color='blue')))
    fig_macd.add_trace(go.Scatter(x=df['time'], y=df['MACD_signal'], name="Signal", line=dict(color='red')))
    fig_macd.add_trace(go.Bar(x=df['time'], y=df['MACD_histogram'], name="Histogram"))
    fig_macd.update_layout(title="MACD Indicator", xaxis_title="Time", yaxis_title="MACD")
    st.plotly_chart(fig_macd, use_container_width=True)

with tab3:
    fig_bb = go.Figure()
    fig_bb.add_trace(go.Scatter(x=df['time'], y=df['close'], name="Price", line=dict(color='blue')))
    fig_bb.add_trace(go.Scatter(x=df['time'], y=df['BB_upper'], name="BB Upper", line=dict(color='red', dash='dash')))
    fig_bb.add_trace(go.Scatter(x=df['time'], y=df['BB_middle'], name="BB Middle", line=dict(color='orange', dash='dot')))
    fig_bb.add_trace(go.Scatter(x=df['time'], y=df['BB_lower'], name="BB Lower", line=dict(color='green', dash='dash')))
    fig_bb.update_layout(title="Bollinger Bands", xaxis_title="Time", yaxis_title="Price")
    st.plotly_chart(fig_bb, use_container_width=True)

# ML Model section
st.header("🤖 Machine Learning Model")

col1, col2 = st.columns(2)

with col1:
    if st.button("🧠 Train ML Model"):
        with st.spinner("Training ML model..."):
            result = train_ml_model(df)
            if result is not None:
                st.success("✅ ML model trained successfully!")
            else:
                st.warning("⚠️ Not enough data for training. Need at least 200 data points.")

with col2:
    if st.button("🔍 Check ML Status"):
        model, scaler = load_ml_model()
        if model:
            st.success("✅ ML model is loaded and ready!")
        else:
            st.warning("⚠️ No trained ML model found.")