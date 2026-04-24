"""
MULTI-ASSET IMPLEMENTATION TEMPLATES
═════════════════════════════════════════════════════════════════════════════

These are code templates/stubs for the new components. Use these as starting
points for implementation.


1. PORTFOLIO MANAGER
═════════════════════════════════════════════════════════════════════════════

File: portfolio_manager.py

```python
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import logging

@dataclass
class AssetClass:
    \"\"\"Represents a tradeable asset class (forex, stocks, commodities)\"\"\"
    name: str  # "forex", "stocks", "commodities"
    capital_allocation_pct: float  # e.g., 0.40 for 40%
    symbols: List[str]  # ["EURUSD", "GBPUSD", "USDJPY"]
    risk_per_trade_pct: float  # e.g., 0.02 for 2%
    max_positions: int  # e.g., 10 max forex positions
    leverage: float  # e.g., 100 for forex, 2 for stocks
    contract_size: float  # 100000 for forex, 1 for stocks
    point_value: float  # 0.0001 for forex 4-decimal
    spread_type: str  # "pips" for forex, "percentage" for stocks
    market_hours: Dict[str, List[str]]  # {"EURUSD": ["london", "overlap"]}
    data_source: str  # "mt5", "alphatrade", "binance"


class PortfolioManager:
    \"\"\"Manages multi-asset portfolio initialization and configuration\"\"\"
    
    def __init__(self, total_capital: float, asset_classes: Dict[str, AssetClass]):
        self.total_capital = total_capital
        self.asset_classes = asset_classes
        self.initialized = False
        self.logger = logging.getLogger(__name__)
    
    def initialize_portfolio(self) -> bool:
        \"\"\"
        Initialize the portfolio by:
        1. Validating configuration
        2. Allocating capital to each asset class
        3. Setting up position tracking
        4. Initializing risk budgets
        \"\"\"
        try:
            # Validate total allocation sums to 100%
            total_pct = sum(ac.capital_allocation_pct for ac in self.asset_classes.values())
            if abs(total_pct - 1.0) > 0.01:
                raise ValueError(f"Asset allocations sum to {total_pct*100}%, must be 100%")
            
            # Calculate allocated capital per asset class
            for asset_name, asset_class in self.asset_classes.items():
                allocated = self.total_capital * asset_class.capital_allocation_pct
                self.logger.info(f"{asset_name}: ${allocated:.2f} ({asset_class.capital_allocation_pct*100:.0f}%)")
            
            self.initialized = True
            return True
        
        except Exception as e:
            self.logger.error(f"Portfolio initialization failed: {e}")
            return False
    
    def get_asset_class(self, asset_type: str) -> Optional[AssetClass]:
        \"\"\"Get asset class configuration\"\"\"
        return self.asset_classes.get(asset_type)
    
    def get_allocated_capital(self, asset_type: str) -> float:
        \"\"\"Get total capital allocated to an asset class\"\"\"
        asset_class = self.get_asset_class(asset_type)
        if asset_class:
            return self.total_capital * asset_class.capital_allocation_pct
        return 0
    
    def get_risk_budget(self, asset_type: str) -> float:
        \"\"\"Get total risk budget (dollars) for an asset class\"\"\"
        allocated = self.get_allocated_capital(asset_type)
        asset_class = self.get_asset_class(asset_type)
        if asset_class:
            return allocated * asset_class.risk_per_trade_pct
        return 0
    
    def is_active_trading_time(self, asset_type: str, symbol: str) -> bool:
        \"\"\"Check if symbol is in active trading hours\"\"\"
        # Implementation would check current UTC time vs market hours
        # For now, placeholder
        return True
    
    def validate_symbol(self, asset_type: str, symbol: str) -> bool:
        \"\"\"Validate that symbol is configured and tradeable in this asset class\"\"\"
        asset_class = self.get_asset_class(asset_type)
        if not asset_class:
            return False
        return symbol in asset_class.symbols


# USAGE EXAMPLE:
if __name__ == "__main__":
    forex = AssetClass(
        name="forex",
        capital_allocation_pct=0.40,
        symbols=["EURUSD", "GBPUSD", "USDJPY"],
        risk_per_trade_pct=0.02,
        max_positions=10,
        leverage=100,
        contract_size=100000,
        point_value=0.0001,
        spread_type="pips",
        market_hours={"EURUSD": ["london", "overlap"]},
        data_source="mt5"
    )
    
    stocks = AssetClass(
        name="stocks",
        capital_allocation_pct=0.30,
        symbols=["AAPL", "GOOGL", "MSFT"],
        risk_per_trade_pct=0.01,
        max_positions=8,
        leverage=2,
        contract_size=1,
        point_value=0.01,
        spread_type="percentage",
        market_hours={"AAPL": ["ny_market"]},
        data_source="alphatrade"
    )
    
    portfolio = PortfolioManager(
        total_capital=10000,
        asset_classes={"forex": forex, "stocks": stocks}
    )
    
    portfolio.initialize_portfolio()
    print(f"Forex allocation: ${portfolio.get_allocated_capital('forex')}")
    print(f"Forex risk budget: ${portfolio.get_risk_budget('forex')}")
```


2. CAPITAL ALLOCATOR
═════════════════════════════════════════════════════════════════════════════

File: capital_allocator.py

```python
from typing import Dict, Optional
import logging
from portfolio_manager import PortfolioManager

class CapitalAllocator:
    \"\"\"Manages capital distribution and dynamic lot sizing across assets\"\"\"
    
    def __init__(self, portfolio: PortfolioManager, account_balance: float):
        self.portfolio = portfolio
        self.account_balance = account_balance
        self.position_tracking = {}  # Track margin used per asset
        self.logger = logging.getLogger(__name__)
    
    def get_allocated_capital_summary(self, asset_type: str) -> Dict:
        \"\"\"
        Returns comprehensive capital summary for an asset class
        
        Returns:
        {
            'total_allocation': 4000,           # 40% of $10k
            'margin_used': 3000,                # From existing positions
            'free_capital': 1000,               # Remaining available
            'available_for_new_positions': 800, # Reserve 20% buffer
            'risk_budget': 80,                  # 2% of allocation = $80
            'max_new_positions': 2,             # Can open 2 more positions
            'margin_utilization_pct': 75        # 3000/4000
        }
        \"\"\"
        total_allocated = self.portfolio.get_allocated_capital(asset_type)
        
        # Get margin used (from position tracking)
        margin_used = self.position_tracking.get(asset_type, 0)
        
        free_capital = total_allocated - margin_used
        buffer = total_allocated * 0.20  # 20% safety buffer
        available_for_trades = max(0, free_capital - buffer)
        
        # Get asset class config
        asset_class = self.portfolio.get_asset_class(asset_type)
        risk_budget = self.portfolio.get_risk_budget(asset_type)
        
        # Estimate max new positions (rough: available / margin_per_position)
        margin_per_position = total_allocated / asset_class.max_positions if asset_class else 0
        max_new = int(available_for_trades / margin_per_position) if margin_per_position > 0 else 0
        
        return {
            'total_allocation': total_allocated,
            'margin_used': margin_used,
            'free_capital': free_capital,
            'available_for_new_positions': available_for_trades,
            'risk_budget': risk_budget,
            'max_new_positions': max_new,
            'margin_utilization_pct': (margin_used / total_allocated * 100) if total_allocated > 0 else 0
        }
    
    def calculate_lot_size(
        self,
        asset_type: str,
        symbol: str,
        stop_loss: float,
        stop_loss_unit: str = "pips"  # "pips" for forex, "%" for stocks
    ) -> float:
        \"\"\"
        Calculate dynamic lot size based on:
        • Asset allocation
        • Risk budget
        • Stop loss distance
        • Leverage limits
        
        Example:
            lot_size = allocator.calculate_lot_size(
                asset_type='forex',
                symbol='EURUSD',
                stop_loss=50,
                stop_loss_unit='pips'
            )
            # Returns: 0.16 (micro lots)
        \"\"\"
        
        summary = self.get_allocated_capital_summary(asset_type)
        asset_class = self.portfolio.get_asset_class(asset_type)
        
        if not asset_class or summary['available_for_new_positions'] <= 0:
            return 0
        
        risk_budget = summary['risk_budget']
        
        if stop_loss_unit == "pips":
            # For forex: risk = lot_size * pips * point_value * contract_size
            # Solve for lot_size:
            lot_size = risk_budget / (stop_loss * asset_class.point_value * asset_class.contract_size)
        
        elif stop_loss_unit == "%":
            # For stocks: risk = position_value * stop_loss_pct
            # This would need current price to calculate
            # Simplified version
            lot_size = risk_budget / (stop_loss / 100)
        
        # Apply leverage limits
        max_lot = asset_class.contract_size / asset_class.leverage
        lot_size = min(lot_size, max_lot)
        
        self.logger.info(f"{asset_type}/{symbol}: lot_size={lot_size:.4f}")
        return lot_size
    
    def update_position_margin(self, asset_type: str, lot_size: float, action: str = "add"):
        \"\"\"Track margin used when positions are opened/closed\"\"\"
        # Placeholder - implementation would track actual margin used
        if action == "add":
            self.position_tracking[asset_type] = self.position_tracking.get(asset_type, 0) + lot_size * 100
        elif action == "remove":
            self.position_tracking[asset_type] = max(0, self.position_tracking.get(asset_type, 0) - lot_size * 100)
    
    def rebalance_portfolio(self) -> Dict:
        \"\"\"
        Rebalance portfolio on drawdown or schedule
        Reduces lot sizes if risk gets too high
        \"\"\"
        return {
            'status': 'rebalanced',
            'changes': []
        }


# USAGE EXAMPLE:
if __name__ == "__main__":
    portfolio = PortfolioManager(10000, {...})  # Initialize portfolio
    portfolio.initialize_portfolio()
    
    allocator = CapitalAllocator(portfolio, account_balance=10000)
    
    # Check capital situation
    summary = allocator.get_allocated_capital_summary('forex')
    print(f"Forex free capital: ${summary['available_for_new_positions']:.2f}")
    
    # Calculate lot size for new trade
    lot = allocator.calculate_lot_size('forex', 'EURUSD', stop_loss=50, stop_loss_unit='pips')
    print(f"Calculated lot size: {lot:.4f}")
```


3. DATA SOURCE ABSTRACTION
═════════════════════════════════════════════════════════════════════════════

File: data_sources/data_source.py

```python
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict
import pandas as pd

class DataSource(ABC):
    \"\"\"Abstract base class for all data sources\"\"\"
    
    @abstractmethod
    def get_price(self, symbol: str) -> Tuple[float, float]:
        \"\"\"Get current bid and ask price for symbol\"\"\"
        pass
    
    @abstractmethod
    def get_historical_data(self, symbol: str, timeframe: str, bars: int = 1000) -> pd.DataFrame:
        \"\"\"Get historical OHLC data\"\"\"
        pass
    
    @abstractmethod
    def place_order(self, symbol: str, lot_size: float, order_type: str, sl_pips: int, tp_pips: int) -> Dict:
        \"\"\"Place a market order\"\"\"
        # order_type: "BUY" or "SELL"
        # Returns: {'success': bool, 'order_id': str, 'entry_price': float, 'error': str}
        pass
    
    @abstractmethod
    def close_position(self, position_id: str) -> bool:
        \"\"\"Close an open position\"\"\"
        pass
    
    @abstractmethod
    def get_open_positions(self) -> list:
        \"\"\"Get list of open positions for this asset type\"\"\"
        pass


class MT5DataSource(DataSource):
    \"\"\"Data source for MT5 (Forex, Commodities)\"\"\"
    
    def __init__(self):
        self.asset_type = "forex"  # or "commodities"
    
    def get_price(self, symbol: str) -> Tuple[float, float]:
        import MetaTrader5 as mt5
        tick = mt5.symbol_info_tick(symbol)
        return tick.ask, tick.bid
    
    def get_historical_data(self, symbol: str, timeframe: str, bars: int = 1000) -> pd.DataFrame:
        import MetaTrader5 as mt5
        # Convert timeframe string to MT5 constant
        timeframe_map = {'M1': mt5.TIMEFRAME_M1, 'M5': mt5.TIMEFRAME_M5, 'M15': mt5.TIMEFRAME_M15}
        tf = timeframe_map.get(timeframe, mt5.TIMEFRAME_M5)
        
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    
    def place_order(self, symbol: str, lot_size: float, order_type: str, sl_pips: int, tp_pips: int) -> Dict:
        import MetaTrader5 as mt5
        # Implementation from existing mt5_connector.place_order
        # TODO: copy existing logic here
        return {'success': True, 'order_id': '12345'}
    
    def close_position(self, position_id: str) -> bool:
        # TODO: implement
        return True
    
    def get_open_positions(self) -> list:
        # TODO: implement
        return []


class StockDataSource(DataSource):
    \"\"\"Data source for Stocks (Alpha Vantage, IB, etc)\"\"\"
    
    def __init__(self, api_key: str = None):
        self.asset_type = "stocks"
        self.api_key = api_key
    
    def get_price(self, symbol: str) -> Tuple[float, float]:
        # TODO: Implement Alpha Vantage or other stock API call
        # Returns bid and ask (or close price as both)
        return 150.25, 150.35
    
    def get_historical_data(self, symbol: str, timeframe: str, bars: int = 1000) -> pd.DataFrame:
        # TODO: Fetch from stock API
        pass
    
    def place_order(self, symbol: str, lot_size: float, order_type: str, sl_pips: int, tp_pips: int) -> Dict:
        # TODO: Place order via stock broker API
        pass
    
    def close_position(self, position_id: str) -> bool:
        # TODO: Close via stock broker
        return True
    
    def get_open_positions(self) -> list:
        # TODO: Get positions from stock broker
        return []


# Factory pattern for data source selection
def get_data_source(asset_type: str) -> DataSource:
    \"\"\"Factory to get appropriate data source\"\"\"
    if asset_type in ["forex", "commodities"]:
        return MT5DataSource()
    elif asset_type == "stocks":
        return StockDataSource(api_key="YOUR_API_KEY")
    else:
        raise ValueError(f"Unknown asset type: {asset_type}")
```


4. TRADE EXECUTOR
═════════════════════════════════════════════════════════════════════════════

File: trade_executor.py

```python
from typing import List, Dict, Optional
import logging
from portfolio_manager import PortfolioManager
from capital_allocator import CapitalAllocator
from data_sources.data_source import get_data_source
from strategy import generate_signal
from risk_management import validate_risk

class Signal:
    \"\"\"Represents a trading signal\"\"\"
    def __init__(self, asset_type: str, symbol: str, signal: str, score: float):
        self.asset_type = asset_type
        self.symbol = symbol
        self.signal = signal  # "BUY", "SELL", "HOLD"
        self.score = score
        self.lot_size = 0


class TradeExecutor:
    \"\"\"Executes trades across multiple assets\"\"\"
    
    def __init__(self, portfolio: PortfolioManager, allocator: CapitalAllocator):
        self.portfolio = portfolio
        self.allocator = allocator
        self.data_sources = {}
        self.logger = logging.getLogger(__name__)
    
    def generate_signals(self) -> List[Signal]:
        \"\"\"
        Generate signals for all assets in portfolio
        Returns list of Signal objects ready for evaluation
        \"\"\"
        signals = []
        
        for asset_type, asset_class in self.portfolio.asset_classes.items():
            data_source = get_data_source(asset_type)
            
            for symbol in asset_class.symbols:
                # Skip if not in active trading hours
                if not self.portfolio.is_active_trading_time(asset_type, symbol):
                    continue
                
                try:
                    # Get data and generate signal
                    df = data_source.get_historical_data(symbol, '15M')
                    signal_type = generate_signal(df)
                    score = 7  # Placeholder
                    
                    if signal_type in ["BUY", "SELL"]:
                        signal = Signal(asset_type, symbol, signal_type, score)
                        signals.append(signal)
                
                except Exception as e:
                    self.logger.warning(f"Failed to generate signal for {asset_type}/{symbol}: {e}")
        
        return signals
    
    def validate_execution(self, signal: Signal) -> bool:
        \"\"\"
        Validate that a signal can be executed
        Checks: position limit, margin, risk budget, market hours, spread
        \"\"\"
        
        # Check market hours
        if not self.portfolio.is_active_trading_time(signal.asset_type, signal.symbol):
            self.logger.debug(f"{signal.symbol} not in active trading hours")
            return False
        
        # Check position limit
        asset_class = self.portfolio.get_asset_class(signal.asset_type)
        # TODO: Track position count per asset type
        # if current_positions[signal.asset_type] >= asset_class.max_positions:
        #     return False
        
        # Check margin and risk
        summary = self.allocator.get_allocated_capital_summary(signal.asset_type)
        if summary['available_for_new_positions'] <= 0:
            self.logger.debug(f"{signal.asset_type} has no available capital")
            return False
        
        # Check spread
        data_source = get_data_source(signal.asset_type)
        bid, ask = data_source.get_price(signal.symbol)
        spread = ask - bid
        # TODO: validate spread vs asset_class.max_spread
        
        return True
    
    def execute_trade(self, signal: Signal) -> Dict:
        \"\"\"Execute a validated signal\"\"\"
        
        # Calculate lot size
        signal.lot_size = self.allocator.calculate_lot_size(
            asset_type=signal.asset_type,
            symbol=signal.symbol,
            stop_loss=50,  # TODO: use from config
            stop_loss_unit="pips"
        )
        
        if signal.lot_size <= 0:
            return {'success': False, 'reason': 'Invalid lot size'}
        
        # Execute via appropriate data source
        data_source = get_data_source(signal.asset_type)
        
        try:
            result = data_source.place_order(
                symbol=signal.symbol,
                lot_size=signal.lot_size,
                order_type=signal.signal,
                sl_pips=50,  # TODO: from config
                tp_pips=100  # TODO: from config
            )
            
            self.logger.info(f"Executed: {signal.asset_type}/{signal.symbol} {signal.signal} {signal.lot_size} lots")
            return result
        
        except Exception as e:
            self.logger.error(f"Execution failed for {signal.asset_type}/{signal.symbol}: {e}")
            return {'success': False, 'reason': str(e)}


# USAGE EXAMPLE:
if __name__ == "__main__":
    portfolio = PortfolioManager(10000, {...})
    allocator = CapitalAllocator(portfolio, 10000)
    executor = TradeExecutor(portfolio, allocator)
    
    # Generate signals from all assets
    signals = executor.generate_signals()
    
    # Validate and execute
    for signal in signals:
        if executor.validate_execution(signal):
            result = executor.execute_trade(signal)
            print(f"{signal.symbol}: {result}")
```


TESTING
═════════════════════════════════════════════════════════════════════════════

File: test_multi_asset.py

```python
import pytest
from portfolio_manager import PortfolioManager, AssetClass
from capital_allocator import CapitalAllocator

def test_portfolio_initialization():
    forex = AssetClass(
        name="forex",
        capital_allocation_pct=0.40,
        symbols=["EURUSD"],
        risk_per_trade_pct=0.02,
        max_positions=10,
        leverage=100,
        contract_size=100000,
        point_value=0.0001,
        spread_type="pips",
        market_hours={"EURUSD": ["london"]},
        data_source="mt5"
    )
    
    portfolio = PortfolioManager(10000, {"forex": forex})
    assert portfolio.initialize_portfolio() == True
    assert portfolio.get_allocated_capital("forex") == 4000

def test_capital_allocation():
    # Setup
    forex = AssetClass(...)
    portfolio = PortfolioManager(10000, {"forex": forex})
    portfolio.initialize_portfolio()
    
    allocator = CapitalAllocator(portfolio, 10000)
    summary = allocator.get_allocated_capital_summary('forex')
    
    assert summary['total_allocation'] == 4000
    assert summary['margin_used'] == 0
    assert summary['free_capital'] == 4000

def test_lot_calculation():
    # Setup
    portfolio = PortfolioManager(10000, {...})
    portfolio.initialize_portfolio()
    allocator = CapitalAllocator(portfolio, 10000)
    
    lot_size = allocator.calculate_lot_size(
        asset_type='forex',
        symbol='EURUSD',
        stop_loss=50,
        stop_loss_unit='pips'
    )
    
    assert lot_size > 0
    assert lot_size <= 10  # Some reasonable max
```

═════════════════════════════════════════════════════════════════════════════

These templates provide a solid foundation. Next steps:
1. Fill in the TODO sections with actual implementation
2. Add comprehensive error handling
3. Add logging throughout
4. Add comprehensive tests
5. Integrate with existing dashboard
6. Test with live market data

"""
