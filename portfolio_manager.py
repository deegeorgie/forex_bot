#!/usr/bin/env python
"""
Multi-Asset Portfolio Manager

Manages and tracks positions across multiple asset types:
- Forex (currency pairs)
- Stocks (equities)
- Indices (stock indices)
- Commodities (gold, oil, etc.)
- Crypto (cryptocurrencies)

Provides unified portfolio metrics regardless of asset class.
"""

import MetaTrader5 as mt5
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime

logging.basicConfig(level=logging.INFO)

class AssetType(Enum):
    """Classification of asset types"""
    FOREX = "forex"
    STOCKS = "stocks"
    INDICES = "indices"
    COMMODITIES = "commodities"
    CRYPTO = "crypto"
    OTHER = "other"

@dataclass
class Position:
    """Enhanced position with asset classification"""
    ticket: int
    symbol: str
    asset_type: AssetType
    type: int  # mt5.ORDER_TYPE_BUY (0) or mt5.ORDER_TYPE_SELL (1)
    volume: float
    price_open: float
    price_current: float
    profit: float
    profit_pct: float
    sl: float
    tp: float
    open_time: datetime
    
    # Asset-specific properties
    contract_size: float = 1.0  # For forex: 100000, stocks: 1
    point_value: float = 1.0    # Value of 1 point move
    is_volatile: bool = False   # True for high-volatility assets

@dataclass
class PortfolioMetrics:
    """Overall portfolio performance metrics"""
    total_positions: int = 0
    total_profit: float = 0.0
    total_profit_pct: float = 0.0
    total_margin_used: float = 0.0
    total_margin_free: float = 0.0
    
    # By asset type
    positions_by_asset: Dict[AssetType, int] = field(default_factory=dict)
    profit_by_asset: Dict[AssetType, float] = field(default_factory=dict)
    profit_pct_by_asset: Dict[AssetType, float] = field(default_factory=dict)
    
    # Risk metrics
    max_profit_position: Optional[Position] = None
    max_loss_position: Optional[Position] = None
    average_profit_pct: float = 0.0
    win_rate: float = 0.0  # Percentage of profitable positions
    
    # Position distribution
    long_positions: int = 0
    short_positions: int = 0
    

class PortfolioManager:
    """Manages multi-asset portfolio"""
    
    # Asset type detection patterns
    FOREX_SYMBOLS = {
        'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD',
        'AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'CADCHF',
    }
    
    COMMODITY_SYMBOLS = {
        'XAUUSD', 'XAGUSD', 'WTIUSD', 'XAUG',  # Gold, Silver, Oil, Gold Micro
    }
    
    INDEX_SYMBOLS = {
        'DAX', 'SPXC', 'SPXE', 'SPXL', 'SPXN', 'SPXT', 'SPXU', 'SPXV', 'SPXX',
    }
    
    CRYPTO_KEYWORDS = {'BTC', 'ETH', 'DOGE', 'ADA', 'XRP'}
    
    def __init__(self):
        """Initialize portfolio manager"""
        self.positions: List[Position] = []
        self.metrics = PortfolioMetrics()
        self.asset_configs = self._initialize_asset_configs()
        
    def _initialize_asset_configs(self) -> Dict[AssetType, Dict]:
        """Initialize configuration for each asset type"""
        return {
            AssetType.FOREX: {
                'contract_size': 100000,
                'point_value': 0.0001,
                'min_lot': 0.01,
                'max_lot': 100.0,
            },
            AssetType.STOCKS: {
                'contract_size': 1,
                'point_value': 0.01,
                'min_lot': 1,
                'max_lot': 10000,
            },
            AssetType.INDICES: {
                'contract_size': 1,
                'point_value': 1.0,
                'min_lot': 0.01,
                'max_lot': 100.0,
            },
            AssetType.COMMODITIES: {
                'contract_size': 1,
                'point_value': 0.01,
                'min_lot': 0.01,
                'max_lot': 1000.0,
            },
            AssetType.CRYPTO: {
                'contract_size': 1,
                'point_value': 0.00000001,
                'min_lot': 0.001,
                'max_lot': 1000.0,
            },
        }
    
    def _detect_asset_type(self, symbol: str) -> AssetType:
        """Detect asset type from symbol name"""
        symbol_upper = symbol.upper()
        
        # Check explicit patterns
        if symbol_upper in self.FOREX_SYMBOLS or len(symbol_upper) == 6 and symbol_upper[3:].isalpha():
            return AssetType.FOREX
        
        if symbol_upper in self.COMMODITY_SYMBOLS:
            return AssetType.COMMODITIES
        
        if symbol_upper in self.INDEX_SYMBOLS:
            return AssetType.INDICES
        
        if any(keyword in symbol_upper for keyword in self.CRYPTO_KEYWORDS):
            return AssetType.CRYPTO
        
        # Default: assume stocks (most common for single symbols)
        return AssetType.STOCKS
    
    def _get_asset_config(self, asset_type: AssetType) -> Dict:
        """Get configuration for asset type"""
        return self.asset_configs.get(asset_type, self.asset_configs[AssetType.OTHER])
    
    def add_position(self, mt5_position) -> None:
        """Add position from MT5 to portfolio
        
        Args:
            mt5_position: Position object from mt5.positions_get()
        """
        try:
            symbol = mt5_position.symbol
            asset_type = self._detect_asset_type(symbol)
            config = self._get_asset_config(asset_type)
            
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            price_current = tick.ask if mt5_position.type == mt5.ORDER_TYPE_BUY else tick.bid
            
            # Calculate profit percentage
            price_diff = price_current - mt5_position.price_open
            profit_pct = (price_diff / mt5_position.price_open * 100) if mt5_position.price_open > 0 else 0
            if mt5_position.type == mt5.ORDER_TYPE_SELL:
                profit_pct = -profit_pct
            
            position = Position(
                ticket=mt5_position.ticket,
                symbol=symbol,
                asset_type=asset_type,
                type=mt5_position.type,
                volume=mt5_position.volume,
                price_open=mt5_position.price_open,
                price_current=price_current,
                profit=mt5_position.profit,
                profit_pct=profit_pct,
                sl=mt5_position.sl,
                tp=mt5_position.tp,
                open_time=datetime.fromtimestamp(mt5_position.time),
                contract_size=config['contract_size'],
                point_value=config['point_value'],
                is_volatile=asset_type in [AssetType.CRYPTO, AssetType.STOCKS],
            )
            
            self.positions.append(position)
            logging.info(f"Added {asset_type.value} position: {symbol} (ticket {mt5_position.ticket})")
            
        except Exception as e:
            logging.error(f"Failed to add position {mt5_position.symbol}: {e}")
    
    def calculate_metrics(self, balance: float, equity: float) -> PortfolioMetrics:
        """Calculate comprehensive portfolio metrics
        
        Args:
            balance: Account balance
            equity: Account equity
            
        Returns:
            PortfolioMetrics with all calculations
        """
        metrics = PortfolioMetrics()
        metrics.total_positions = len(self.positions)
        
        if not self.positions:
            return metrics
        
        # Initialize asset-type tracking
        positions_by_asset = {}
        profit_by_asset = {}
        profits = []
        winning_positions = 0
        
        for asset_type in AssetType:
            positions_by_asset[asset_type] = 0
            profit_by_asset[asset_type] = 0.0
        
        # Calculate totals
        for pos in self.positions:
            metrics.total_profit += pos.profit
            profits.append(pos.profit_pct)
            
            # Track by asset type
            positions_by_asset[pos.asset_type] = positions_by_asset.get(pos.asset_type, 0) + 1
            profit_by_asset[pos.asset_type] = profit_by_asset.get(pos.asset_type, 0) + pos.profit
            
            # Track position direction
            if pos.type == mt5.ORDER_TYPE_BUY:
                metrics.long_positions += 1
            else:
                metrics.short_positions += 1
            
            # Track profitable positions
            if pos.profit >= 0:
                winning_positions += 1
            
            # Track best/worst positions
            if metrics.max_profit_position is None or pos.profit > metrics.max_profit_position.profit:
                metrics.max_profit_position = pos
            
            if metrics.max_loss_position is None or pos.profit < metrics.max_loss_position.profit:
                metrics.max_loss_position = pos
        
        # Calculate percentages
        metrics.total_profit_pct = (metrics.total_profit / balance * 100) if balance > 0 else 0
        metrics.average_profit_pct = sum(profits) / len(profits) if profits else 0
        metrics.win_rate = (winning_positions / len(self.positions) * 100) if self.positions else 0
        
        # Store by-asset metrics
        metrics.positions_by_asset = positions_by_asset
        metrics.profit_by_asset = profit_by_asset
        
        # Calculate profit % by asset
        for asset_type in AssetType:
            count = positions_by_asset.get(asset_type, 0)
            if count > 0:
                metrics.profit_pct_by_asset[asset_type] = profit_by_asset.get(asset_type, 0) / balance * 100 if balance > 0 else 0
        
        self.metrics = metrics
        return metrics
    
    def get_positions_by_asset(self, asset_type: AssetType) -> List[Position]:
        """Get all positions of a specific asset type
        
        Args:
            asset_type: Type of asset to filter
            
        Returns:
            List of positions matching the asset type
        """
        return [pos for pos in self.positions if pos.asset_type == asset_type]
    
    def get_position_summary(self) -> str:
        """Get formatted portfolio summary"""
        lines = [
            "="*70,
            "PORTFOLIO SUMMARY",
            "="*70,
            f"Total Positions: {self.metrics.total_positions}",
            f"  Long: {self.metrics.long_positions}  |  Short: {self.metrics.short_positions}",
            f"Total Profit: ${self.metrics.total_profit:,.2f} ({self.metrics.total_profit_pct:.2f}%)",
            f"Average Profit per Position: {self.metrics.average_profit_pct:.2f}%",
            f"Win Rate: {self.metrics.win_rate:.1f}%",
            "",
            "By Asset Type:",
        ]
        
        for asset_type in AssetType:
            count = self.metrics.positions_by_asset.get(asset_type, 0)
            profit = self.metrics.profit_by_asset.get(asset_type, 0)
            profit_pct = self.metrics.profit_pct_by_asset.get(asset_type, 0)
            if count > 0:
                lines.append(f"  {asset_type.value.upper():12} - {count:3} positions | Profit: ${profit:10,.2f} ({profit_pct:7.2f}%)")
        
        lines.extend([
            "",
            f"Best Position: {self.metrics.max_profit_position.symbol if self.metrics.max_profit_position else 'N/A':8} +${self.metrics.max_profit_position.profit:,.2f}" if self.metrics.max_profit_position else "Best Position: N/A",
            f"Worst Position: {self.metrics.max_loss_position.symbol if self.metrics.max_loss_position else 'N/A':8} ${self.metrics.max_loss_position.profit:,.2f}" if self.metrics.max_loss_position else "Worst Position: N/A",
            "="*70,
        ])
        
        return "\n".join(lines)
    
    def get_metrics_dict(self) -> Dict:
        """Get metrics as dictionary for API/dashboard use"""
        return {
            'total_positions': self.metrics.total_positions,
            'total_profit': self.metrics.total_profit,
            'total_profit_pct': self.metrics.total_profit_pct,
            'average_profit_pct': self.metrics.average_profit_pct,
            'win_rate': self.metrics.win_rate,
            'long_positions': self.metrics.long_positions,
            'short_positions': self.metrics.short_positions,
            'positions_by_asset': {k.value: v for k, v in self.metrics.positions_by_asset.items()},
            'profit_by_asset': {k.value: v for k, v in self.metrics.profit_by_asset.items()},
            'profit_pct_by_asset': {k.value: v for k, v in self.metrics.profit_pct_by_asset.items()},
        }


# Example usage
if __name__ == "__main__":
    # This would be used like:
    # manager = PortfolioManager()
    # positions = mt5.positions_get()
    # for pos in positions:
    #     manager.add_position(pos)
    # metrics = manager.calculate_metrics(balance=10000, equity=10500)
    # print(manager.get_position_summary())
    print("Portfolio Manager loaded successfully")
