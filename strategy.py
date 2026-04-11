import pandas as pd
import numpy as np

def compute_indicators(df):
    df['SMA_50'] = df['close'].rolling(50).mean()
    df['SMA_200'] = df['close'].rolling(200).mean()

    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    return df

def generate_signal(df):
    last = df.iloc[-1]

    if last['SMA_50'] > last['SMA_200'] and last['RSI'] < 70:
        return "BUY"
    elif last['SMA_50'] < last['SMA_200'] and last['RSI'] > 30:
        return "SELL"
    else:
        return "HOLD"
