#!/usr/bin/env python
"""
Multi-Asset Capital Allocator

Intelligently allocates capital across different asset types:
- Calculates position sizing based on asset volatility
- Adjusts lot sizes for different contract types
- Balances risk across asset classes
- Respects margin requirements per asset type
"""

import MetaTrader5 as mt5
import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from enum import Enum

from portfolio_manager import AssetType

logging.basicConfig(level=logging.INFO)

class AllocationStrategy(Enum):
    """Risk allocation strategies"""
    EQUAL_WEIGHT = "equal_weight"           # Equal capital to each asset type
    VOLATILITY_ADJUSTED = "volatility"      # More capital to less volatile assets
    RISK_PARITY = "risk_parity"             # Equal risk contribution
    AGGRESSIVE = "aggressive"                # More positions, higher leverage
    CONSERVATIVE = "conservative"           # Fewer positions, lower leverage

@dataclass
class AssetAllocation:
    """Capital allocation for an asset type"""
    asset_type: AssetType
    allocated_capital: float
    capital_percentage: float
    max_positions: int
    lot_size: float
    margin_per_position: float
    max_drawdown_pips: int
    leverage: float = 1.0

@dataclass
class VolatilityMetrics:
    """Volatility metrics for an asset"""
    asset_type: AssetType
    symbol: str
    atr: float              # Average True Range
    volatility_pct: float   # Volatility as percentage
    recommendation: str     # Allocation recommendation

class CapitalAllocator:
    """Allocates capital across multi-asset portfolio"""
    
    # Default volatility reference (forex = 100%)
    VOLATILITY_SCALE = {
        AssetType.FOREX: 1.0,           # Base volatility
        AssetType.STOCKS: 2.0,          # ~2x more volatile than forex
        AssetType.INDICES: 1.5,         # ~1.5x more volatile
        AssetType.COMMODITIES: 1.8,     # ~1.8x more volatile
        AssetType.CRYPTO: 4.0,          # ~4x more volatile (very risky)
    }
    
    # Margin requirements (in pips worth of capital per lot)
    MARGIN_REQUIREMENTS = {
        AssetType.FOREX: 0.01,          # 1% of notional value
        AssetType.STOCKS: 0.02,         # 2% of notional value
        AssetType.INDICES: 0.015,       # 1.5% of notional value
        AssetType.COMMODITIES: 0.025,   # 2.5% of notional value
        AssetType.CRYPTO: 0.05,         # 5% of notional value
    }
    
    # Position limits per asset type (max positions per strategy)
    POSITION_LIMITS = {
        AllocationStrategy.CONSERVATIVE: {
            AssetType.FOREX: 3,
            AssetType.STOCKS: 2,
            AssetType.INDICES: 2,
            AssetType.COMMODITIES: 1,
            AssetType.CRYPTO: 0,
        },
        AllocationStrategy.EQUAL_WEIGHT: {
            AssetType.FOREX: 6,
            AssetType.STOCKS: 4,
            AssetType.INDICES: 3,
            AssetType.COMMODITIES: 2,
            AssetType.CRYPTO: 1,
        },
        AllocationStrategy.AGGRESSIVE: {
            AssetType.FOREX: 10,
            AssetType.STOCKS: 8,
            AssetType.INDICES: 5,
            AssetType.COMMODITIES: 3,
            AssetType.CRYPTO: 2,
        },
    }
    
    def __init__(self, strategy: AllocationStrategy = AllocationStrategy.EQUAL_WEIGHT):
        """Initialize capital allocator
        
        Args:
            strategy: Risk allocation strategy
        """
        self.strategy = strategy
        self.allocations: Dict[AssetType, AssetAllocation] = {}
        
    def allocate_capital(
        self,
        total_capital: float,
        max_total_positions: int = 16,
        max_drawdown_pct: float = 2.0,
    ) -> Dict[AssetType, AssetAllocation]:
        """Allocate capital across asset types
        
        Args:
            total_capital: Total account capital available
            max_total_positions: Maximum total open positions across all assets
            max_drawdown_pct: Maximum acceptable drawdown percentage
            
        Returns:
            Dictionary of allocations per asset type
        """
        allocations = {}
        
        # Determine allocation percentages based on strategy
        if self.strategy == AllocationStrategy.EQUAL_WEIGHT:
            allocation_pcts = {
                AssetType.FOREX: 0.40,
                AssetType.STOCKS: 0.30,
                AssetType.INDICES: 0.15,
                AssetType.COMMODITIES: 0.10,
                AssetType.CRYPTO: 0.05,
            }
        
        elif self.strategy == AllocationStrategy.VOLATILITY_ADJUSTED:
            # Lower capital to higher volatility assets
            allocation_pcts = {
                AssetType.FOREX: 0.35,
                AssetType.STOCKS: 0.25,
                AssetType.INDICES: 0.20,
                AssetType.COMMODITIES: 0.15,
                AssetType.CRYPTO: 0.05,
            }
        
        elif self.strategy == AllocationStrategy.CONSERVATIVE:
            # Conservative: mostly forex and indices
            allocation_pcts = {
                AssetType.FOREX: 0.50,
                AssetType.STOCKS: 0.20,
                AssetType.INDICES: 0.20,
                AssetType.COMMODITIES: 0.10,
                AssetType.CRYPTO: 0.00,
            }
        
        elif self.strategy == AllocationStrategy.AGGRESSIVE:
            # Aggressive: more diverse, higher allocations
            allocation_pcts = {
                AssetType.FOREX: 0.30,
                AssetType.STOCKS: 0.35,
                AssetType.INDICES: 0.15,
                AssetType.COMMODITIES: 0.15,
                AssetType.CRYPTO: 0.05,
            }
        
        else:  # RISK_PARITY
            # Equal risk contribution (inverse of volatility)
            allocation_pcts = {
                AssetType.FOREX: 0.30,
                AssetType.STOCKS: 0.20,
                AssetType.INDICES: 0.25,
                AssetType.COMMODITIES: 0.20,
                AssetType.CRYPTO: 0.05,
            }
        
        # Get position limits for strategy
        position_limits = self.POSITION_LIMITS.get(self.strategy, self.POSITION_LIMITS[AllocationStrategy.EQUAL_WEIGHT])
        
        # Calculate allocation per asset type
        max_drawdown_pips = max_drawdown_pct * 100  # Convert to pips
        
        for asset_type in AssetType:
            if asset_type == AssetType.OTHER:
                continue
            
            capital_pct = allocation_pcts.get(asset_type, 0)
            allocated_capital = total_capital * capital_pct
            
            # Get position limits
            max_positions = position_limits.get(asset_type, 0)
            max_positions = min(max_positions, max_total_positions - sum(a.max_positions for a in allocations.values()))
            
            if max_positions == 0:
                continue
            
            # Calculate lot size based on capital and positions
            # lot_size = allocated_capital / (max_positions * margin_per_position)
            margin_requirement = self.MARGIN_REQUIREMENTS.get(asset_type, 0.02)
            
            # Estimate position value for margin calculation
            # For stocks: ~$100-300 per share on average
            # For forex: $100,000 per lot
            # For crypto: $50,000+ per position
            position_value_estimate = self._estimate_position_value(asset_type)
            margin_per_position = position_value_estimate * margin_requirement
            
            # Calculate lot size
            lot_size = allocated_capital / (max_positions * margin_per_position) if margin_per_position > 0 else 0.1
            lot_size = max(0.01, min(lot_size, 100))  # Clamp between 0.01 and 100
            
            allocation = AssetAllocation(
                asset_type=asset_type,
                allocated_capital=allocated_capital,
                capital_percentage=capital_pct * 100,
                max_positions=max_positions,
                lot_size=lot_size,
                margin_per_position=margin_per_position,
                max_drawdown_pips=int(max_drawdown_pips),
                leverage=self._calculate_leverage(asset_type),
            )
            
            allocations[asset_type] = allocation
            logging.info(f"Allocated {asset_type.value:12} - ${allocated_capital:10,.0f} ({capital_pct*100:5.1f}%) | Max {max_positions} positions | Lot: {lot_size:.3f}")
        
        self.allocations = allocations
        return allocations
    
    def _estimate_position_value(self, asset_type: AssetType) -> float:
        """Estimate average position value for asset type"""
        estimates = {
            AssetType.FOREX: 100000,           # 1 standard lot
            AssetType.STOCKS: 10000,           # 100 shares @ $100
            AssetType.INDICES: 10000,          # 100 index units
            AssetType.COMMODITIES: 50000,      # Gold/Oil typical contracts
            AssetType.CRYPTO: 50000,           # Typical crypto positions
        }
        return estimates.get(asset_type, 10000)
    
    def _calculate_leverage(self, asset_type: AssetType) -> float:
        """Calculate appropriate leverage for asset type"""
        leverage_map = {
            AssetType.FOREX: 10.0,       # Higher leverage, more liquid
            AssetType.STOCKS: 5.0,       # Medium leverage
            AssetType.INDICES: 8.0,      # Higher leverage, liquid
            AssetType.COMMODITIES: 5.0,  # Medium leverage
            AssetType.CRYPTO: 2.0,       # Low leverage, volatile
        }
        return leverage_map.get(asset_type, 1.0)
    
    def calculate_lot_size(
        self,
        asset_type: AssetType,
        signal_strength: float = 0.5,
        current_drawdown_pct: float = 0.0,
    ) -> float:
        """Calculate dynamic lot size based on conditions
        
        Args:
            asset_type: Type of asset
            signal_strength: Signal strength 0-1 (0.5 = neutral, 1.0 = very strong)
            current_drawdown_pct: Current drawdown percentage
            
        Returns:
            Recommended lot size
        """
        if asset_type not in self.allocations:
            logging.warning(f"No allocation for {asset_type.value}")
            return 0.1
        
        allocation = self.allocations[asset_type]
        base_lot = allocation.lot_size
        
        # Adjust based on signal strength
        # Strong signal (1.0) = full lot, weak signal (0.5) = half lot
        strength_multiplier = signal_strength / 0.5
        
        # Reduce lot size if already in drawdown
        max_drawdown_pips = allocation.max_drawdown_pips
        if current_drawdown_pct > max_drawdown_pips * 0.5:
            strength_multiplier *= 0.5  # Half lot size if in significant drawdown
        
        recommended_lot = base_lot * strength_multiplier
        
        # Clamp to reasonable bounds
        min_lot = allocation.lot_size * 0.1
        max_lot = allocation.lot_size * 2.0
        
        return max(min_lot, min(recommended_lot, max_lot))
    
    def should_open_position(
        self,
        asset_type: AssetType,
        current_positions_by_asset: Dict[AssetType, int],
    ) -> bool:
        """Determine if a new position should be opened
        
        Args:
            asset_type: Type of asset
            current_positions_by_asset: Current position count per asset type
            
        Returns:
            True if position can be opened
        """
        if asset_type not in self.allocations:
            return False
        
        allocation = self.allocations[asset_type]
        current_positions = current_positions_by_asset.get(asset_type, 0)
        
        # Check if within position limits
        if current_positions >= allocation.max_positions:
            logging.warning(f"Cannot open {asset_type.value} position: limit {allocation.max_positions} reached")
            return False
        
        return True
    
    def get_allocation_summary(self) -> str:
        """Get formatted allocation summary"""
        lines = [
            "="*80,
            f"CAPITAL ALLOCATION ({self.strategy.value.upper()})",
            "="*80,
        ]
        
        total_capital = sum(a.allocated_capital for a in self.allocations.values())
        
        for asset_type, allocation in self.allocations.items():
            lines.append(
                f"{asset_type.value.upper():12} | "
                f"${allocation.allocated_capital:10,.0f} ({allocation.capital_percentage:5.1f}%) | "
                f"Max {allocation.max_positions} positions | "
                f"Lot: {allocation.lot_size:.3f} | "
                f"Leverage: {allocation.leverage:.1f}x"
            )
        
        lines.extend([
            "-"*80,
            f"Total Capital: ${total_capital:,.0f}",
            "="*80,
        ])
        
        return "\n".join(lines)
    
    def get_allocations_dict(self) -> Dict:
        """Get allocations as dictionary for API/dashboard"""
        return {
            'strategy': self.strategy.value,
            'allocations': {
                asset_type.value: {
                    'allocated_capital': allocation.allocated_capital,
                    'capital_percentage': allocation.capital_percentage,
                    'max_positions': allocation.max_positions,
                    'lot_size': allocation.lot_size,
                    'leverage': allocation.leverage,
                    'max_drawdown_pips': allocation.max_drawdown_pips,
                }
                for asset_type, allocation in self.allocations.items()
            }
        }


# Example usage
if __name__ == "__main__":
    allocator = CapitalAllocator(AllocationStrategy.EQUAL_WEIGHT)
    allocations = allocator.allocate_capital(total_capital=10000, max_total_positions=16)
    print(allocator.get_allocation_summary())
    
    # Test lot size calculation
    lot_eurusd = allocator.calculate_lot_size(AssetType.FOREX, signal_strength=0.8)
    lot_aapl = allocator.calculate_lot_size(AssetType.STOCKS, signal_strength=0.7)
    
    print(f"\nLot sizes:")
    print(f"  EURUSD (forex, strong signal): {lot_eurusd:.3f}")
    print(f"  AAPL (stock, good signal): {lot_aapl:.3f}")
