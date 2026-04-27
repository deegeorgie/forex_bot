#!/usr/bin/env python
"""
Multi-Asset Data Layer

Provides unified interface for retrieving market data across asset types:
- OHLC (bar) data
- Current prices
- Technical indicators
- Symbol information
- All data flows through MT5 (single source of truth)
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict, Tuple, List
from datetime import datetime, timedelta
from dataclasses import dataclass

from portfolio_manager import AssetType

logging.basicConfig(level=logging.INFO)

@dataclass
class SymbolData:
    """Unified symbol information"""
    symbol: str
    asset_type: AssetType
    ask: float
    bid: float
    spread_pips: float
    is_tradable: bool
    visible: bool
    trade_mode: int
    min_volume: float
    max_volume: float

@dataclass
class BarData:
    """Unified bar data"""
    symbol: str
    asset_type: AssetType
    timeframe: int
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    time: datetime

class DataLayer:
    """Unified data access layer for multi-asset portfolio"""
    
    # Asset type detection by symbol patterns
    ASSET_TYPE_PATTERNS = {
        AssetType.FOREX: r'^[A-Z]{6}$',           # EURUSD, GBPUSD
        AssetType.STOCKS: r'^[A-Z]{1,5}$',        # AAPL, MSFT, etc
        AssetType.INDICES: r'^(DAX|SPX|FTSE)',    # DAX, SPXC, etc
        AssetType.COMMODITIES: r'^(XAU|XAG|WTI)',  # XAUUSD, XAGUSD
        AssetType.CRYPTO: r'^(BTC|ETH|ADA)',       # BTC, ETH, ADA
    }
    
    def __init__(self):
        """Initialize data layer"""
        self.cache: Dict[str, Dict] = {}  # Simple caching
        self.asset_type_cache: Dict[str, AssetType] = {}
    
    def detect_asset_type(self, symbol: str) -> AssetType:
        """Detect asset type from symbol"""
        if symbol in self.asset_type_cache:
            return self.asset_type_cache[symbol]
        
        symbol_upper = symbol.upper()
        
        # Check patterns
        import re
        for asset_type, pattern in self.ASSET_TYPE_PATTERNS.items():
            if re.match(pattern, symbol_upper):
                self.asset_type_cache[symbol] = asset_type
                return asset_type
        
        # Default to stocks for unknown single symbols
        asset_type = AssetType.STOCKS
        self.asset_type_cache[symbol] = asset_type
        return asset_type
    
    def get_symbol_info(self, symbol: str) -> Optional[SymbolData]:
        """Get symbol information
        
        Args:
            symbol: Trading symbol
            
        Returns:
            SymbolData or None if symbol not found
        """
        try:
            # Ensure symbol is selected
            if not mt5.symbol_select(symbol, True):
                logging.warning(f"Could not select symbol {symbol}")
            
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logging.error(f"Symbol {symbol} not found")
                return None
            
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logging.error(f"Could not get tick for {symbol}")
                return None
            
            # Calculate spread in pips
            spread_pips = (tick.ask - tick.bid) * 10000  # Assumes 4 decimal places
            
            asset_type = self.detect_asset_type(symbol)
            
            data = SymbolData(
                symbol=symbol,
                asset_type=asset_type,
                ask=tick.ask,
                bid=tick.bid,
                spread_pips=spread_pips,
                is_tradable=symbol_info.trade_mode != 0,
                visible=symbol_info.visible,
                trade_mode=symbol_info.trade_mode,
                min_volume=symbol_info.volume_min,
                max_volume=symbol_info.volume_max,
            )
            
            # Cache it
            self.cache[symbol] = {'symbol_info': data, 'timestamp': datetime.now()}
            
            return data
        
        except Exception as e:
            logging.error(f"Failed to get symbol info for {symbol}: {e}")
            return None
    
    def get_bars(
        self,
        symbol: str,
        timeframe: str = 'M15',
        count: int = 500,
    ) -> Optional[pd.DataFrame]:
        """Get OHLC bars for a symbol
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (M1, M5, M15, H1, D1, etc.)
            count: Number of bars to retrieve
            
        Returns:
            DataFrame with OHLC data or None on failure
        """
        try:
            # Convert timeframe string to MT5 constant
            timeframe_map = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15,
                'M30': mt5.TIMEFRAME_M30,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1,
                'W1': mt5.TIMEFRAME_W1,
                'MN1': mt5.TIMEFRAME_MN1,
            }
            
            mt5_timeframe = timeframe_map.get(timeframe, mt5.TIMEFRAME_M15)
            
            # Ensure symbol is selected
            if not mt5.symbol_select(symbol, True):
                logging.warning(f"Could not select {symbol}")
            
            # Copy rates from MT5
            bars = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, count)
            
            if bars is None or len(bars) == 0:
                logging.warning(f"No bars retrieved for {symbol} {timeframe}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(bars)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'tick_volume': 'Volume',
            }, inplace=True)
            
            df = df[['time', 'Open', 'High', 'Low', 'Close', 'Volume']]
            df.set_index('time', inplace=True)
            
            # Cache it
            cache_key = f"{symbol}_{timeframe}"
            self.cache[cache_key] = {'bars': df, 'timestamp': datetime.now()}
            
            logging.info(f"Retrieved {len(df)} bars for {symbol} {timeframe}")
            
            return df
        
        except Exception as e:
            logging.error(f"Failed to get bars for {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[Tuple[float, float]]:
        """Get current bid/ask price
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Tuple of (ask, bid) or None on failure
        """
        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logging.error(f"Could not get price for {symbol}")
                return None
            
            return (tick.ask, tick.bid)
        
        except Exception as e:
            logging.error(f"Failed to get price for {symbol}: {e}")
            return None
    
    def calculate_technical_indicators(
        self,
        df: pd.DataFrame,
        indicators: List[str] = None,
    ) -> pd.DataFrame:
        """Calculate technical indicators on bar data
        
        Args:
            df: DataFrame with OHLC data
            indicators: List of indicators to calculate
                       ('RSI', 'MACD', 'BB', 'SMA', 'ATR')
            
        Returns:
            DataFrame with indicators added
        """
        if df is None or len(df) == 0:
            return df
        
        if indicators is None:
            indicators = ['RSI', 'MACD', 'BB', 'SMA']
        
        df_copy = df.copy()
        
        # RSI
        if 'RSI' in indicators:
            df_copy['RSI'] = self._calculate_rsi(df_copy['Close'], period=14)
        
        # MACD
        if 'MACD' in indicators:
            macd, signal, hist = self._calculate_macd(df_copy['Close'])
            df_copy['MACD'] = macd
            df_copy['MACD_Signal'] = signal
            df_copy['MACD_Hist'] = hist
        
        # Bollinger Bands
        if 'BB' in indicators:
            upper, middle, lower = self._calculate_bollinger_bands(df_copy['Close'], period=20, std_dev=2)
            df_copy['BB_Upper'] = upper
            df_copy['BB_Middle'] = middle
            df_copy['BB_Lower'] = lower
        
        # Simple Moving Averages
        if 'SMA' in indicators:
            df_copy['SMA_50'] = df_copy['Close'].rolling(window=50).mean()
            df_copy['SMA_200'] = df_copy['Close'].rolling(window=200).mean()
        
        # ATR (Average True Range)
        if 'ATR' in indicators:
            df_copy['ATR'] = self._calculate_atr(df_copy, period=14)
        
        return df_copy
    
    @staticmethod
    def _calculate_rsi(prices, period=14):
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def _calculate_macd(prices, fast=12, slow=26, signal=9):
        """Calculate MACD indicator"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    @staticmethod
    def _calculate_bollinger_bands(prices, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower
    
    @staticmethod
    def _calculate_atr(df, period=14):
        """Calculate Average True Range"""
        high = df['High']
        low = df['Low']
        close = df['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def clear_cache(self, older_than_minutes: int = 60):
        """Clear cached data older than specified minutes"""
        cutoff = datetime.now() - timedelta(minutes=older_than_minutes)
        
        keys_to_delete = []
        for key, data in self.cache.items():
            if data.get('timestamp', datetime.now()) < cutoff:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self.cache[key]
        
        if keys_to_delete:
            logging.info(f"Cleared {len(keys_to_delete)} cache entries")


# Example usage
if __name__ == "__main__":
    from mt5_connector import connect
    
    connect()
    
    data_layer = DataLayer()
    
    # Get symbol info
    sym_info = data_layer.get_symbol_info('EURUSD')
    if sym_info:
        print(f"Symbol: {sym_info.symbol}")
        print(f"Asset Type: {sym_info.asset_type.value}")
        print(f"Ask/Bid: {sym_info.ask:.5f} / {sym_info.bid:.5f}")
        print(f"Spread: {sym_info.spread_pips:.2f} pips")
    
    # Get bars and calculate indicators
    bars = data_layer.get_bars('EURUSD', 'H1', count=100)
    if bars is not None:
        bars_with_indicators = data_layer.calculate_technical_indicators(bars)
        print(f"\nBars with indicators:")
        print(bars_with_indicators.tail())
    
    mt5.shutdown()
