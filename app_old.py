import streamlit as st
import MetaTrader5 as mt5
from mt5_connector import connect, place_order, get_account_balance, get_account_equity, calculate_lot_size
from data import get_data
from strategy import compute_indicators, generate_signal
import config
import plotly.graph_objects as go
import logging
from backtest import backtest_strategy
import pandas as pd
from typing import List, Dict

logging.basicConfig(level=logging.INFO)

st.title("Forex Algo Trading Dashboard")

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_data(symbol, timeframe):
    return get_data(symbol, timeframe)

@st.cache_data
def get_cached_indicators(df):
    return compute_indicators(df)

# Trade history storage
if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []

def log_trade(trade):
    st.session_state.trade_history.append(trade)
    logging.info(f"Trade logged: {trade}")

try:
    connect()
    balance = get_account_balance()
    equity = get_account_equity()
    drawdown = (balance - equity) / balance if balance > 0 else 0
    st.subheader(f"Account Balance: ${balance:.2f}")
    st.subheader(f"Current Drawdown: {drawdown:.2%}")
    if drawdown > config.MAX_DRAWDOWN_PERCENTAGE:
        st.error("Maximum drawdown exceeded. Trading disabled.")
        trading_enabled = False
    else:
        trading_enabled = True
except Exception as e:
    if "login failed" in str(e).lower():
        st.error("**MT5 Login Failed!** Please check your credentials in the .env file:")
        st.code("""
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server
        """)
        st.info("Make sure MetaTrader 5 terminal is installed and running.")
    else:
        st.error(f"Failed to connect to MT5: {e}")
    st.stop()

symbol = st.selectbox("Symbol", config.AVAILABLE_SYMBOLS, index=config.AVAILABLE_SYMBOLS.index(config.SYMBOL))
timeframe_options = {"M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5, "M15": mt5.TIMEFRAME_M15, "H1": mt5.TIMEFRAME_H1}
timeframe_label = st.selectbox("Timeframe", list(timeframe_options.keys()), index=list(timeframe_options.keys()).index(config.TIMEFRAME))
timeframe = timeframe_options[timeframe_label]

lot = st.slider("Lot size", 0.01, 1.0, config.LOT)
use_risk_management = st.checkbox("Use Risk Management (calculate lot size based on risk)")
paper_trading = st.checkbox("Paper Trading Mode")
auto_trade = st.checkbox("Enable Auto Trading")
use_ml_signals = st.checkbox("Use Machine Learning for Signals")

if use_risk_management:
    try:
        calculated_lot = calculate_lot_size(balance, config.RISK_PERCENTAGE, config.STOP_LOSS_PIPS, symbol)
        lot = min(lot, calculated_lot)  # Use the smaller of user input or calculated
        st.info(f"Calculated lot size based on risk: {calculated_lot:.2f}")
    except Exception as e:
        st.error(f"Failed to calculate lot size: {e}")

try:
    df = get_cached_data(symbol, timeframe)
    df = get_cached_indicators(df)
    signal = generate_signal(df, use_ml=use_ml_signals)
except Exception as e:
    st.error(f"Failed to fetch data or compute indicators: {e}")
    st.stop()

# ML Model Training Section
st.subheader("🤖 Machine Learning Model")
col1, col2 = st.columns(2)

with col1:
    if st.button("Train ML Model"):
        try:
            with st.spinner("Training ML model... This may take a moment."):
                from strategy import train_ml_model
                result = train_ml_model(df)
                if result is not None:
                    model, scaler = result
                    st.success("✅ ML model trained successfully!")
                    st.info("Model saved as 'ml_model.pkl'")
                else:
                    st.warning("⚠️ Not enough data for training. Need at least 200 data points.")
        except Exception as e:
            st.error(f"❌ Failed to train ML model: {e}")

with col2:
    if st.button("Check ML Model Status"):
        try:
            from strategy import load_ml_model
            model, scaler = load_ml_model()
            if model:
                st.success("✅ ML model is loaded and ready!")
            else:
                st.warning("⚠️ No trained ML model found. Please train the model first.")
        except Exception as e:
            st.error(f"❌ Error checking ML model: {e}")

st.subheader(f"Signal: {signal}")

fig = go.Figure()
fig.add_trace(go.Scatter(x=df['time'], y=df['close'], name="Price"))
fig.add_trace(go.Scatter(x=df['time'], y=df['SMA_50'], name="SMA 50"))
fig.add_trace(go.Scatter(x=df['time'], y=df['SMA_200'], name="SMA 200"))

st.plotly_chart(fig)

# RSI Chart
fig_rsi = go.Figure()
fig_rsi.add_trace(go.Scatter(x=df['time'], y=df['RSI'], name="RSI"))
fig_rsi.add_hline(y=70, line_dash="dash", annotation_text="Overbought")
fig_rsi.add_hline(y=30, line_dash="dash", annotation_text="Oversold")
st.subheader("RSI Indicator")
st.plotly_chart(fig_rsi)

# Bollinger Bands Chart
st.subheader("Bollinger Bands")
fig_bb = go.Figure()
fig_bb.add_trace(go.Scatter(x=df['time'], y=df['close'], name="Price", line=dict(color='blue')))
fig_bb.add_trace(go.Scatter(x=df['time'], y=df['BB_upper'], name="BB Upper", line=dict(color='red', dash='dash')))
fig_bb.add_trace(go.Scatter(x=df['time'], y=df['BB_middle'], name="BB Middle", line=dict(color='orange', dash='dot')))
fig_bb.add_trace(go.Scatter(x=df['time'], y=df['BB_lower'], name="BB Lower", line=dict(color='green', dash='dash')))
st.plotly_chart(fig_bb)

# MACD Chart
st.subheader("MACD Indicator")
fig_macd = go.Figure()
fig_macd.add_trace(go.Scatter(x=df['time'], y=df['MACD'], name="MACD", line=dict(color='blue')))
fig_macd.add_trace(go.Scatter(x=df['time'], y=df['MACD_signal'], name="Signal", line=dict(color='red')))
fig_macd.add_trace(go.Bar(x=df['time'], y=df['MACD_histogram'], name="Histogram", marker_color='gray'))
st.plotly_chart(fig_macd)

if st.button("Buy") and trading_enabled:
    try:
        if paper_trading:
            log_trade({"type": "BUY", "symbol": symbol, "lot": lot, "price": df.iloc[-1]['close'], "time": pd.Timestamp.now()})
            st.success("Paper BUY order simulated")
        else:
            place_order(symbol, lot, mt5.ORDER_TYPE_BUY, config.STOP_LOSS_PIPS, config.TAKE_PROFIT_PIPS)
            log_trade({"type": "BUY", "symbol": symbol, "lot": lot, "price": df.iloc[-1]['close'], "time": pd.Timestamp.now()})
            st.success("BUY order executed")
    except Exception as e:
        st.error(f"Failed to execute BUY order: {e}")

if st.button("Sell") and trading_enabled:
    try:
        if paper_trading:
            log_trade({"type": "SELL", "symbol": symbol, "lot": lot, "price": df.iloc[-1]['close'], "time": pd.Timestamp.now()})
            st.success("Paper SELL order simulated")
        else:
            place_order(symbol, lot, mt5.ORDER_TYPE_SELL, config.STOP_LOSS_PIPS, config.TAKE_PROFIT_PIPS)
            log_trade({"type": "SELL", "symbol": symbol, "lot": lot, "price": df.iloc[-1]['close'], "time": pd.Timestamp.now()})
            st.warning("SELL order executed")
    except Exception as e:
        st.error(f"Failed to execute SELL order: {e}")

if auto_trade and trading_enabled:
    try:
        if signal == "BUY":
            if paper_trading:
                log_trade({"type": "BUY", "symbol": symbol, "lot": lot, "price": df.iloc[-1]['close'], "time": pd.Timestamp.now()})
                st.success("Paper BUY order simulated")
            else:
                place_order(symbol, lot, mt5.ORDER_TYPE_BUY, config.STOP_LOSS_PIPS, config.TAKE_PROFIT_PIPS)
                log_trade({"type": "BUY", "symbol": symbol, "lot": lot, "price": df.iloc[-1]['close'], "time": pd.Timestamp.now()})
                st.success("BUY order executed")
        elif signal == "SELL":
            if paper_trading:
                log_trade({"type": "SELL", "symbol": symbol, "lot": lot, "price": df.iloc[-1]['close'], "time": pd.Timestamp.now()})
                st.success("Paper SELL order simulated")
            else:
                place_order(symbol, lot, mt5.ORDER_TYPE_SELL, config.STOP_LOSS_PIPS, config.TAKE_PROFIT_PIPS)
                log_trade({"type": "SELL", "symbol": symbol, "lot": lot, "price": df.iloc[-1]['close'], "time": pd.Timestamp.now()})
                st.warning("SELL order executed")
    except Exception as e:
        st.error(f"Failed to execute auto trade: {e}")

if st.button("Run Backtest"):
    try:
        results = backtest_strategy(df)
        st.subheader("Backtest Results")
        st.write(f"Total Trades: {results['total_trades']}")
        st.write(f"Win Rate: {results['win_rate']:.2%}")
        st.write(f"Total P&L: ${results['total_pnl']:.2f}")
        st.write(f"Final Balance: ${results['final_balance']:.2f}")
        st.write(f"Max Drawdown: {results['max_drawdown']:.2%}")
    except Exception as e:
        st.error(f"Backtest failed: {e}")

# Trade History
if st.session_state.trade_history:
    st.subheader("Trade History")
    history_df = pd.DataFrame(st.session_state.trade_history)
    st.dataframe(history_df)
