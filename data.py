import MetaTrader5 as mt5
import pandas as pd
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)

def get_data(symbol: str, timeframe: int = mt5.TIMEFRAME_M5, n: int = 5000) -> pd.DataFrame:
    """Fetch historical data for a symbol."""
    try:
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n)
        if rates is None or len(rates) == 0:
            raise Exception(f"No data available for {symbol}")
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        logging.info(f"Fetched {len(df)} data points for {symbol}")
        return df
    except Exception as e:
        logging.error(f"Failed to get data for {symbol}: {e}")
        raise
