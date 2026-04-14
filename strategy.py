import pandas as pd
import numpy as np
import logging
from typing import Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os

logging.basicConfig(level=logging.INFO)

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute technical indicators with configurable parameters."""
    try:
        import config
        
        # Moving Averages with configurable periods
        df['SMA_short'] = df['close'].rolling(config.SMA_SHORT).mean()
        df['SMA_long'] = df['close'].rolling(config.SMA_LONG).mean()
        df['SMA_50'] = df['SMA_short']  # For backward compatibility
        df['SMA_200'] = df['SMA_long']  # For backward compatibility

        # RSI with configurable period
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(config.RSI_PERIOD).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(config.RSI_PERIOD).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # MACD with configurable parameters
        ema_fast = df['close'].ewm(span=config.MACD_FAST, adjust=False).mean()
        ema_slow = df['close'].ewm(span=config.MACD_SLOW, adjust=False).mean()
        df['MACD'] = ema_fast - ema_slow
        df['MACD_signal'] = df['MACD'].ewm(span=config.MACD_SIGNAL, adjust=False).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']

        # Bollinger Bands with configurable parameters
        df['BB_middle'] = df['close'].rolling(config.BB_PERIOD).mean()
        df['BB_std'] = df['close'].rolling(config.BB_PERIOD).std()
        df['BB_upper'] = df['BB_middle'] + (df['BB_std'] * config.BB_STD_DEV)
        df['BB_lower'] = df['BB_middle'] - (df['BB_std'] * config.BB_STD_DEV)

        # Additional features for ML
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(20).std()
        df['high_low_ratio'] = df['high'] / df['low']
        
        # ATR (Average True Range) for volatility assessment
        df['tr'] = np.maximum(df['high'] - df['low'], np.maximum(abs(df['high'] - df['close'].shift()), abs(df['low'] - df['close'].shift())))
        df['ATR'] = df['tr'].rolling(14).mean()
        
        # RSI divergence detection (peak/trough analysis)
        df['RSI_peak'] = df['RSI'].rolling(3, center=True).max() == df['RSI']
        df['RSI_trough'] = df['RSI'].rolling(3, center=True).min() == df['RSI']
        
        # Price momentum for additional signal confirmation
        df['momentum'] = df['close'] - df['close'].shift(10)
        df['momentum_direction'] = np.where(df['momentum'] > 0, 1, -1)

        logging.info("Indicators computed successfully")
        return df
    except Exception as e:
        logging.error(f"Failed to compute indicators: {e}")
        raise

def train_ml_model(df: pd.DataFrame):
    """Train a machine learning model for trading signals."""
    try:
        # Prepare features
        features = ['SMA_50', 'SMA_200', 'RSI', 'MACD', 'MACD_signal', 'MACD_histogram',
                   'BB_middle', 'BB_upper', 'BB_lower', 'returns', 'volatility', 'high_low_ratio',
                   'ATR', 'momentum']

        # Create target variable (future price movement)
        df['future_return'] = df['close'].shift(-5) / df['close'] - 1  # 5-period future return
        df['target'] = np.where(df['future_return'] > 0.001, 1,  # Buy signal
                               np.where(df['future_return'] < -0.001, -1, 0))  # Sell signal, Hold otherwise

        # Remove NaN values
        df_ml = df.dropna()

        if len(df_ml) < 200:
            logging.warning("Not enough data for ML training")
            return None

        X = df_ml[features]
        y = df_ml['target']

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train_scaled, y_train)

        # Save model and scaler
        joblib.dump(model, 'ml_model.pkl')
        joblib.dump(scaler, 'scaler.pkl')

        # Calculate accuracy
        accuracy = model.score(X_test_scaled, y_test)
        logging.info(f"ML model trained with accuracy: {accuracy:.2f}")

        return model, scaler
    except Exception as e:
        logging.error(f"Failed to train ML model: {e}")
        return None

def load_ml_model():
    """Load trained ML model."""
    try:
        if os.path.exists('ml_model.pkl') and os.path.exists('scaler.pkl'):
            model = joblib.load('ml_model.pkl')
            scaler = joblib.load('scaler.pkl')
            return model, scaler
        else:
            logging.info("No trained model found")
            return None, None
    except Exception as e:
        logging.error(f"Failed to load ML model: {e}")
        return None, None

def generate_signal(df: pd.DataFrame, use_ml: bool = False) -> str:
    """Generate trading signal using technical analysis or ML."""
    try:
        last = df.iloc[-1]

        if use_ml:
            # Use ML model
            model, scaler = load_ml_model()
            if model and scaler:
                features = ['SMA_50', 'SMA_200', 'RSI', 'MACD', 'MACD_signal', 'MACD_histogram',
                           'BB_middle', 'BB_upper', 'BB_lower', 'returns', 'volatility', 'high_low_ratio']
                X = pd.DataFrame([last[features]])
                X_scaled = scaler.transform(X)
                prediction = model.predict(X_scaled)[0]

                if prediction == 1:
                    signal = "BUY"
                elif prediction == -1:
                    signal = "SELL"
                else:
                    signal = "HOLD"
            else:
                # Fallback to technical analysis
                signal = generate_technical_signal(last)
        else:
            # Use technical analysis
            signal = generate_technical_signal(last)

        logging.info(f"Generated signal: {signal}")
        return signal
    except Exception as e:
        logging.error(f"Failed to generate signal: {e}")
        raise

def generate_technical_signal(last_row) -> str:
    """Generate signal using technical indicators with strict confirmation."""
    try:
        import config
        
        # MACD crossover signals
        macd_bullish = last_row['MACD'] > last_row['MACD_signal']
        macd_bearish = last_row['MACD'] < last_row['MACD_signal']
        macd_histogram_positive = last_row['MACD_histogram'] > 0
        macd_histogram_negative = last_row['MACD_histogram'] < 0

        # Bollinger Bands signals - stricter conditions
        bb_upper_touch = last_row['close'] >= last_row['BB_upper'] * 0.995  # Closer to upper band
        bb_lower_touch = last_row['close'] <= last_row['BB_lower'] * 1.005  # Closer to lower band

        # RSI conditions with configurable thresholds
        rsi_oversold = last_row['RSI'] < config.RSI_OVERSOLD
        rsi_overbought = last_row['RSI'] > config.RSI_OVERBOUGHT

        # Moving average crossover
        sma_bullish = last_row['SMA_short'] > last_row['SMA_long']
        sma_bearish = last_row['SMA_short'] < last_row['SMA_long']
        sma_separation = abs(last_row['SMA_short'] - last_row['SMA_long']) / last_row['SMA_long'] * 100

        # ATR-based volatility filter (only trade in normal volatility)
        atr_threshold = last_row['ATR'] * 2 if not np.isnan(last_row['ATR']) else 0.001
        
        # Momentum confirmation
        momentum_bullish = last_row['momentum_direction'] > 0 if 'momentum_direction' in last_row else False
        momentum_bearish = last_row['momentum_direction'] < 0 if 'momentum_direction' in last_row else False

        # Count buy signals (require multiple confirmations)
        buy_signals = 0
        if macd_bullish and macd_histogram_positive:
            buy_signals += 1
        if bb_lower_touch and rsi_oversold:
            buy_signals += 1
        if sma_bullish and sma_separation > 0.5:  # Ensure clear trend
            buy_signals += 1
        if rsi_oversold:
            buy_signals += 1
        if momentum_bullish:  # Additional momentum confirmation
            buy_signals += 1

        # Count sell signals
        sell_signals = 0
        if macd_bearish and macd_histogram_negative:
            sell_signals += 1
        if bb_upper_touch and rsi_overbought:
            sell_signals += 1
        if sma_bearish and sma_separation > 0.5:  # Ensure clear trend
            sell_signals += 1
        if rsi_overbought:
            sell_signals += 1
        if momentum_bearish:  # Additional momentum confirmation
            sell_signals += 1

        # Generate signal based on confirmation count
        min_signals_required = max(1, config.SIGNAL_CONFIRMATION_COUNT - 1)
        
        if buy_signals >= min_signals_required and buy_signals > sell_signals:
            signal = "BUY"
        elif sell_signals >= min_signals_required and sell_signals > buy_signals:
            signal = "SELL"
        else:
            signal = "HOLD"

        logging.info(f"Signal: {signal} (Buy:{buy_signals}, Sell:{sell_signals})")
        return signal
    except Exception as e:
        logging.error(f"Failed to generate technical signal: {e}")
        return "HOLD"
