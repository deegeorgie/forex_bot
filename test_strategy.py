import pytest
import pandas as pd
import numpy as np
from strategy import compute_indicators, generate_signal

def test_compute_indicators():
    # Create sample data
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    data = {
        'time': dates,
        'close': np.random.uniform(1.0, 1.5, 100),
        'open': np.random.uniform(1.0, 1.5, 100),
        'high': np.random.uniform(1.0, 1.5, 100),
        'low': np.random.uniform(1.0, 1.5, 100),
        'tick_volume': np.random.randint(100, 1000, 100),
        'spread': np.random.randint(1, 10, 100),
        'real_volume': np.random.randint(1000, 10000, 100)
    }
    df = pd.DataFrame(data)
    
    result = compute_indicators(df)
    
    assert 'SMA_50' in result.columns
    assert 'SMA_200' in result.columns
    assert 'RSI' in result.columns
    assert not result['SMA_50'].isna().all()
    assert not result['RSI'].isna().all()

def test_generate_signal_buy():
    # Create data where SMA_50 > SMA_200 and RSI < 70
    data = {
        'time': pd.date_range('2023-01-01', periods=100, freq='D'),
        'close': [1.1] * 100,
        'SMA_50': [1.05] * 100,
        'SMA_200': [1.0] * 100,
        'RSI': [60] * 100
    }
    df = pd.DataFrame(data)
    
    signal = generate_signal(df)
    assert signal == "BUY"

def test_generate_signal_sell():
    # Create data where SMA_50 < SMA_200 and RSI > 30
    data = {
        'time': pd.date_range('2023-01-01', periods=100, freq='D'),
        'close': [1.1] * 100,
        'SMA_50': [1.0] * 100,
        'SMA_200': [1.05] * 100,
        'RSI': [40] * 100
    }
    df = pd.DataFrame(data)
    
    signal = generate_signal(df)
    assert signal == "SELL"

def test_generate_signal_hold():
    # Create data that doesn't meet buy or sell conditions
    data = {
        'time': pd.date_range('2023-01-01', periods=100, freq='D'),
        'close': [1.1] * 100,
        'SMA_50': [1.05] * 100,
        'SMA_200': [1.0] * 100,
        'RSI': [80] * 100  # RSI > 70
    }
    df = pd.DataFrame(data)
    
    signal = generate_signal(df)
    assert signal == "HOLD"