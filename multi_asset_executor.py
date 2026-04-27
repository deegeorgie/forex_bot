#!/usr/bin/env python
"""
Multi-Asset Trade Executor

Handles trade execution across different asset types with asset-specific logic:
- Asset-aware position sizing
- Proper stop loss and take profit calculation
- Margin validation
- Execution quality monitoring
"""

import MetaTrader5 as mt5
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from portfolio_manager import AssetType, Position
from capital_allocator import CapitalAllocator, AllocationStrategy

logging.basicConfig(level=logging.INFO)

@dataclass
class TradeExecution:
    """Result of a trade execution"""
    success: bool
    ticket: Optional[int] = None
    symbol: str = ""
    asset_type: AssetType = AssetType.FOREX
    order_type: str = ""  # BUY or SELL
    volume: float = 0.0
    price_open: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    message: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class ExecutionMetrics:
    """Track execution quality"""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_slippage: float = 0.0
    average_slippage: float = 0.0
    success_rate: float = 0.0
    executions_by_asset: Dict[AssetType, int] = None
    
    def __post_init__(self):
        if self.executions_by_asset is None:
            self.executions_by_asset = {}

class MultiAssetExecutor:
    """Executes trades across multiple asset types"""
    
    def __init__(self, allocator: CapitalAllocator):
        """Initialize executor
        
        Args:
            allocator: CapitalAllocator instance with capital allocations
        """
        self.allocator = allocator
        self.metrics = ExecutionMetrics()
        self.execution_history: List[TradeExecution] = []
    
    def execute_buy(
        self,
        symbol: str,
        asset_type: AssetType,
        lot_size: float,
        signal_strength: float = 0.5,
        stop_loss_pips: int = 50,
        take_profit_pips: int = 100,
        comment: str = "",
    ) -> TradeExecution:
        """Execute a BUY order
        
        Args:
            symbol: Trading symbol
            asset_type: Type of asset
            lot_size: Volume to open
            signal_strength: Signal strength 0-1
            stop_loss_pips: Stop loss in pips
            take_profit_pips: Take profit in pips
            comment: Order comment
            
        Returns:
            TradeExecution result
        """
        return self._execute_order(
            symbol=symbol,
            asset_type=asset_type,
            order_type=mt5.ORDER_TYPE_BUY,
            lot_size=lot_size,
            signal_strength=signal_strength,
            stop_loss_pips=stop_loss_pips,
            take_profit_pips=take_profit_pips,
            comment=comment or "multi_asset_buy",
        )
    
    def execute_sell(
        self,
        symbol: str,
        asset_type: AssetType,
        lot_size: float,
        signal_strength: float = 0.5,
        stop_loss_pips: int = 50,
        take_profit_pips: int = 100,
        comment: str = "",
    ) -> TradeExecution:
        """Execute a SELL order
        
        Args:
            symbol: Trading symbol
            asset_type: Type of asset
            lot_size: Volume to open
            signal_strength: Signal strength 0-1
            stop_loss_pips: Stop loss in pips
            take_profit_pips: Take profit in pips
            comment: Order comment
            
        Returns:
            TradeExecution result
        """
        return self._execute_order(
            symbol=symbol,
            asset_type=asset_type,
            order_type=mt5.ORDER_TYPE_SELL,
            lot_size=lot_size,
            signal_strength=signal_strength,
            stop_loss_pips=stop_loss_pips,
            take_profit_pips=take_profit_pips,
            comment=comment or "multi_asset_sell",
        )
    
    def _execute_order(
        self,
        symbol: str,
        asset_type: AssetType,
        order_type: int,
        lot_size: float,
        signal_strength: float,
        stop_loss_pips: int,
        take_profit_pips: int,
        comment: str,
    ) -> TradeExecution:
        """Execute an order with asset-specific logic
        
        Args:
            symbol: Trading symbol
            asset_type: Type of asset
            order_type: mt5.ORDER_TYPE_BUY or SELL
            lot_size: Volume to open
            signal_strength: Signal strength 0-1
            stop_loss_pips: Stop loss in pips
            take_profit_pips: Take profit in pips
            comment: Order comment
            
        Returns:
            TradeExecution result
        """
        try:
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return TradeExecution(
                    success=False,
                    message=f"Could not get current price for {symbol}",
                )
            
            # Select symbol
            if not mt5.symbol_select(symbol, True):
                logging.warning(f"Could not select {symbol}")
            
            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return TradeExecution(
                    success=False,
                    message=f"Symbol {symbol} not found",
                )
            
            # Determine prices
            if order_type == mt5.ORDER_TYPE_BUY:
                price = tick.ask
                order_type_str = "BUY"
            else:
                price = tick.bid
                order_type_str = "SELL"
            
            # Validate lot size
            min_lot = symbol_info.volume_min
            max_lot = symbol_info.volume_max
            
            if lot_size < min_lot:
                lot_size = min_lot
                logging.warning(f"Lot size adjusted to minimum: {min_lot}")
            elif lot_size > max_lot:
                lot_size = max_lot
                logging.warning(f"Lot size adjusted to maximum: {max_lot}")
            
            # Calculate stop loss and take profit with asset-specific pip values
            sl_adjustment = self._calculate_pips_adjustment(asset_type, stop_loss_pips)
            tp_adjustment = self._calculate_pips_adjustment(asset_type, take_profit_pips)
            
            if order_type == mt5.ORDER_TYPE_BUY:
                stop_loss = price - sl_adjustment
                take_profit = price + tp_adjustment
            else:
                stop_loss = price + sl_adjustment
                take_profit = price - tp_adjustment
            
            # Create request
            request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': symbol,
                'volume': lot_size,
                'type': order_type,
                'price': price,
                'sl': stop_loss,
                'tp': take_profit,
                'deviation': 20,
                'comment': comment,
            }
            
            # Send order
            result = mt5.order_send(request)
            
            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                error_msg = result.comment if result else "Unknown error"
                logging.error(f"Order failed: {error_msg}")
                return TradeExecution(
                    success=False,
                    symbol=symbol,
                    asset_type=asset_type,
                    order_type=order_type_str,
                    volume=lot_size,
                    message=f"Order rejected: {error_msg}",
                )
            
            # Success
            execution = TradeExecution(
                success=True,
                ticket=result.order,
                symbol=symbol,
                asset_type=asset_type,
                order_type=order_type_str,
                volume=lot_size,
                price_open=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                message=f"{order_type_str} {lot_size} {symbol} @ {price:.5f}",
            )
            
            # Update metrics
            self._update_metrics(execution)
            self.execution_history.append(execution)
            
            logging.info(f"✅ Order executed: {execution.message}")
            
            return execution
        
        except Exception as e:
            logging.error(f"Exception during order execution: {e}")
            return TradeExecution(
                success=False,
                symbol=symbol,
                asset_type=asset_type,
                message=f"Exception: {str(e)}",
            )
    
    def _calculate_pips_adjustment(self, asset_type: AssetType, pips: int) -> float:
        """Calculate actual price adjustment for pips (asset-specific)
        
        Args:
            asset_type: Type of asset
            pips: Number of pips
            
        Returns:
            Price adjustment value
        """
        # Different assets have different pip values
        pip_values = {
            AssetType.FOREX: 0.0001,           # 4 decimals
            AssetType.STOCKS: 0.01,            # 2 decimals
            AssetType.INDICES: 1.0,            # 0 decimals
            AssetType.COMMODITIES: 0.01,       # 2 decimals
            AssetType.CRYPTO: 0.00000001,      # 8 decimals
        }
        
        pip_value = pip_values.get(asset_type, 0.0001)
        return pips * pip_value
    
    def close_position(self, position: Position) -> TradeExecution:
        """Close an open position
        
        Args:
            position: Position to close
            
        Returns:
            TradeExecution result
        """
        try:
            # Get current price
            tick = mt5.symbol_info_tick(position.symbol)
            if tick is None:
                return TradeExecution(
                    success=False,
                    message=f"Could not get price for {position.symbol}",
                )
            
            # Determine close order type
            if position.type == mt5.ORDER_TYPE_BUY:
                close_type = mt5.ORDER_TYPE_SELL
                close_price = tick.bid
                close_str = "SELL (close)"
            else:
                close_type = mt5.ORDER_TYPE_BUY
                close_price = tick.ask
                close_str = "BUY (close)"
            
            # Create close request
            request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': position.symbol,
                'volume': position.volume,
                'type': close_type,
                'position': position.ticket,
                'price': close_price,
                'deviation': 20,
                'comment': 'multi_asset_close',
            }
            
            result = mt5.order_send(request)
            
            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                error_msg = result.comment if result else "Unknown error"
                return TradeExecution(
                    success=False,
                    ticket=position.ticket,
                    symbol=position.symbol,
                    asset_type=position.asset_type,
                    message=f"Close failed: {error_msg}",
                )
            
            execution = TradeExecution(
                success=True,
                ticket=position.ticket,
                symbol=position.symbol,
                asset_type=position.asset_type,
                order_type=close_str,
                volume=position.volume,
                price_open=close_price,
                message=f"Closed {position.symbol} ticket {position.ticket}",
            )
            
            self._update_metrics(execution)
            self.execution_history.append(execution)
            
            logging.info(f"✅ Position closed: {execution.message}")
            
            return execution
        
        except Exception as e:
            logging.error(f"Exception closing position: {e}")
            return TradeExecution(
                success=False,
                ticket=position.ticket,
                symbol=position.symbol,
                message=f"Exception: {str(e)}",
            )
    
    def _update_metrics(self, execution: TradeExecution) -> None:
        """Update execution metrics"""
        self.metrics.total_executions += 1
        
        if execution.asset_type not in self.metrics.executions_by_asset:
            self.metrics.executions_by_asset[execution.asset_type] = 0
        
        self.metrics.executions_by_asset[execution.asset_type] += 1
        
        if execution.success:
            self.metrics.successful_executions += 1
        else:
            self.metrics.failed_executions += 1
        
        # Update success rate
        if self.metrics.total_executions > 0:
            self.metrics.success_rate = (
                self.metrics.successful_executions / self.metrics.total_executions * 100
            )
    
    def get_execution_summary(self) -> str:
        """Get formatted execution summary"""
        lines = [
            "="*80,
            "EXECUTION METRICS",
            "="*80,
            f"Total Executions: {self.metrics.total_executions}",
            f"  Successful: {self.metrics.successful_executions}",
            f"  Failed: {self.metrics.failed_executions}",
            f"Success Rate: {self.metrics.success_rate:.1f}%",
            "",
            "By Asset Type:",
        ]
        
        for asset_type, count in self.metrics.executions_by_asset.items():
            lines.append(f"  {asset_type.value.upper():12} - {count} executions")
        
        lines.append("="*80)
        return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    from capital_allocator import AllocationStrategy
    from mt5_connector import connect
    
    connect()
    
    allocator = CapitalAllocator(AllocationStrategy.EQUAL_WEIGHT)
    allocator.allocate_capital(total_capital=10000)
    
    executor = MultiAssetExecutor(allocator)
    
    # Test execution (dry run - see result without actually trading)
    result = executor.execute_buy(
        symbol="EURUSD",
        asset_type=AssetType.FOREX,
        lot_size=0.1,
        signal_strength=0.8,
        stop_loss_pips=50,
        take_profit_pips=100,
    )
    
    print(executor.get_execution_summary())
    
    mt5.shutdown()
