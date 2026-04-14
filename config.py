import os
from dotenv import load_dotenv

load_dotenv()

SYMBOL = os.getenv("SYMBOL", "EURUSD")
LOT = float(os.getenv("LOT", "0.1"))
STOP_LOSS_PIPS = int(os.getenv("STOP_LOSS_PIPS", "50"))
TAKE_PROFIT_PIPS = int(os.getenv("TAKE_PROFIT_PIPS", "100"))
RISK_PERCENTAGE = float(os.getenv("RISK_PERCENTAGE", "0.02"))
MAX_DRAWDOWN_PERCENTAGE = float(os.getenv("MAX_DRAWDOWN_PERCENTAGE", "0.1"))
TIMEFRAME = os.getenv("TIMEFRAME", "M5")  # Default to M5
AVAILABLE_SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]  # Add more as needed

# Strategy Configuration - Adjustable Parameters
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))
RSI_OVERSOLD = int(os.getenv("RSI_OVERSOLD", "30"))
RSI_OVERBOUGHT = int(os.getenv("RSI_OVERBOUGHT", "70"))
BB_PERIOD = int(os.getenv("BB_PERIOD", "20"))
BB_STD_DEV = float(os.getenv("BB_STD_DEV", "2.0"))
MACD_FAST = int(os.getenv("MACD_FAST", "12"))
MACD_SLOW = int(os.getenv("MACD_SLOW", "26"))
MACD_SIGNAL = int(os.getenv("MACD_SIGNAL", "9"))
SMA_SHORT = int(os.getenv("SMA_SHORT", "50"))
SMA_LONG = int(os.getenv("SMA_LONG", "200"))
SIGNAL_CONFIRMATION_COUNT = int(os.getenv("SIGNAL_CONFIRMATION_COUNT", "2"))  # Require N signals to align

# MetaTrader 5 Configuration
MT5_LOGIN = int(os.getenv("MT5_LOGIN", "0"))
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
MT5_SERVER = os.getenv("MT5_SERVER", "")
