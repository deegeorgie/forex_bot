import streamlit as st
import MetaTrader5 as mt5
from mt5_connector import connect, place_order
from data import get_data
from strategy import compute_indicators, generate_signal
import config
import plotly.graph_objects as go

st.title("Forex Algo Trading Dashboard")

connect()

symbol = st.text_input("Symbol", config.SYMBOL)
lot = st.slider("Lot size", 0.01, 1.0, config.LOT)
auto_trade = st.checkbox("Enable Auto Trading")

df = get_data(symbol)
df = compute_indicators(df)

signal = generate_signal(df)

st.subheader(f"Signal: {signal}")

fig = go.Figure()
fig.add_trace(go.Scatter(x=df['time'], y=df['close'], name="Price"))
fig.add_trace(go.Scatter(x=df['time'], y=df['SMA_50'], name="SMA 50"))
fig.add_trace(go.Scatter(x=df['time'], y=df['SMA_200'], name="SMA 200"))

st.plotly_chart(fig)

if st.button("Buy"):
    place_order(symbol, lot, mt5.ORDER_TYPE_BUY)

if st.button("Sell"):
    place_order(symbol, lot, mt5.ORDER_TYPE_SELL)

if auto_trade:
    if signal == "BUY":
        place_order(symbol, lot, mt5.ORDER_TYPE_BUY)
        st.success("BUY order executed")
    elif signal == "SELL":
        place_order(symbol, lot, mt5.ORDER_TYPE_SELL)
        st.warning("SELL order executed")
