import os
from dotenv import load_dotenv

load_dotenv()

SYMBOL = os.getenv("SYMBOL", "EURUSD")
LOT = float(os.getenv("LOT", "0.1"))
STOP_LOSS_PIPS = int(os.getenv("STOP_LOSS_PIPS", "50"))
TAKE_PROFIT_PIPS = int(os.getenv("TAKE_PROFIT_PIPS", "100"))
RISK_PERCENTAGE = float(os.getenv("RISK_PERCENTAGE", "0.02"))
MAX_DRAWDOWN_PERCENTAGE = float(os.getenv("MAX_DRAWDOWN_PERCENTAGE", "0.1"))
AUTO_CLOSE_MAX_LOSS_PERCENTAGE = float(os.getenv("AUTO_CLOSE_MAX_LOSS_PERCENTAGE", "1.0"))
TIMEFRAME = os.getenv("TIMEFRAME", "M15")  # Default to M15 for lower noise and stronger signals
AVAILABLE_SYMBOLS = [
    symbol.strip().upper()
    for symbol in os.getenv("AVAILABLE_SYMBOLS", "EURUSD,GBPUSD,USDJPY,AUDUSD,USDCAD").split(",")
    if symbol.strip()
]

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

# Risk and execution controls
MAX_OPEN_POSITIONS = int(os.getenv("MAX_OPEN_POSITIONS", "3"))
MAX_SPREAD_PIPS = float(os.getenv("MAX_SPREAD_PIPS", "3.0"))
MAX_SLIPPAGE_PIPS = float(os.getenv("MAX_SLIPPAGE_PIPS", "3.0"))
BACKTEST_SPREAD_PIPS = float(os.getenv("BACKTEST_SPREAD_PIPS", "0.5"))
BACKTEST_SLIPPAGE_PIPS = float(os.getenv("BACKTEST_SLIPPAGE_PIPS", "0.5"))
MAX_ORDER_TRIES = int(os.getenv("MAX_ORDER_TRIES", "3"))

# MetaTrader 5 Configuration
MT5_LOGIN = int(os.getenv("MT5_LOGIN", "0"))
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
MT5_SERVER = os.getenv("MT5_SERVER", "")
