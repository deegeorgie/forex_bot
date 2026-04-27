# 🌍 Multi-Asset Trading Framework - Implementation Guide

**Version:** 1.0  
**Status:** ✅ Complete and Ready for Testing  
**Last Updated:** April 27, 2026

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Installation & Testing](#installation--testing)
5. [Usage Examples](#usage-examples)
6. [Integration with Existing Bot](#integration-with-existing-bot)
7. [Allocation Strategies](#allocation-strategies)
8. [Next Steps](#next-steps)

---

## 🎯 Overview

The Multi-Asset Trading Framework extends your forex bot to trade across **6 different asset types**:

| Asset Type | Symbols | Examples | Notes |
|-----------|---------|----------|-------|
| **Forex** | 48 | EURUSD, GBPUSD, USDJPY | Low spreads, liquid, 24/5 |
| **Stocks** | 3,904 | AAPL, MSFT, TSLA | High volatility, day trading only |
| **Indices** | 9 | DAX, SPX, NQ | Broad market exposure |
| **Commodities** | 1+ | XAUUSD, WTIUSD | Trending, low correlation |
| **Crypto** | 16 | BTC, ETH, ADA | High volatility, 24/7 |

**Key Improvements:**
- ✅ Unified portfolio tracking across all asset types
- ✅ Intelligent capital allocation by asset class
- ✅ Asset-specific position sizing (stocks ≠ forex)
- ✅ Volatility-adjusted risk management
- ✅ Multi-asset dashboard for holistic view

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MULTI-ASSET FRAMEWORK                        │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
    ┌────────┐          ┌──────────┐          ┌─────────────┐
    │ DATA   │          │ PORTFOLIO│          │   CAPITAL   │
    │ LAYER  │          │ MANAGER  │          │ ALLOCATOR   │
    └────────┘          └──────────┘          └─────────────┘
        │                     │                     │
        │                     ▼                     │
        │             ┌──────────────┐             │
        └────────────►│  MULTI-ASSET │◄────────────┘
                      │  EXECUTOR    │
                      └──────────────┘
                             │
                             ▼
                    ┌─────────────────────┐
                    │   STREAMLIT        │
                    │   DASHBOARD        │
                    │   (New Page)       │
                    └─────────────────────┘
```

---

## 📦 Components

### 1. **Portfolio Manager** (`portfolio_manager.py`)

**Purpose:** Unified portfolio tracking across all asset types

**Key Classes:**
- `AssetType` - Enum for asset classification
- `Position` - Enhanced position with asset metadata
- `PortfolioMetrics` - Comprehensive portfolio statistics
- `PortfolioManager` - Main portfolio management class

**Usage:**
```python
from portfolio_manager import PortfolioManager
from mt5_connector import connect, get_open_positions

connect()
portfolio = PortfolioManager()

# Add positions
positions = get_open_positions()
for pos in positions:
    portfolio.add_position(pos)

# Calculate metrics
metrics = portfolio.calculate_metrics(balance=10000, equity=10500)

# Get summary
print(portfolio.get_position_summary())
```

**Capabilities:**
- Auto-detects asset type from symbol
- Calculates metrics per asset type
- Tracks best/worst positions
- Calculates win rate and average profit

---

### 2. **Capital Allocator** (`capital_allocator.py`)

**Purpose:** Intelligent capital allocation across asset types

**Key Classes:**
- `AllocationStrategy` - Enum for allocation methods
- `AssetAllocation` - Allocation details per asset
- `CapitalAllocator` - Main allocation engine

**Allocation Strategies:**

| Strategy | Best For | Capital Dist. |
|----------|----------|---|
| **CONSERVATIVE** | Low risk | 50% forex, 20% stocks, 20% indices, 10% commodities |
| **EQUAL_WEIGHT** | Balanced | 40% forex, 30% stocks, 15% indices, 10% comm, 5% crypto |
| **VOLATILITY_ADJUSTED** | Moderate risk | Inverse to volatility |
| **AGGRESSIVE** | High growth | Diversified high allocation |
| **RISK_PARITY** | Equal risk | Risk-weighted allocation |

**Usage:**
```python
from capital_allocator import CapitalAllocator, AllocationStrategy

allocator = CapitalAllocator(AllocationStrategy.EQUAL_WEIGHT)
allocations = allocator.allocate_capital(
    total_capital=10000,
    max_total_positions=16,
    max_drawdown_pct=2.0
)

print(allocator.get_allocation_summary())

# Get recommended lot size
lot = allocator.calculate_lot_size(
    asset_type=AssetType.STOCKS,
    signal_strength=0.8,
    current_drawdown_pct=0.5
)
```

**Features:**
- Asset-specific margin requirements
- Volatility-adjusted leverage
- Dynamic lot sizing based on signal strength
- Automatic position limit enforcement

---

### 3. **Data Layer** (`data_layer.py`)

**Purpose:** Unified market data access across asset types

**Key Classes:**
- `SymbolData` - Symbol information
- `BarData` - OHLC bar data
- `DataLayer` - Main data access class

**Usage:**
```python
from data_layer import DataLayer

data_layer = DataLayer()

# Get symbol info
sym_info = data_layer.get_symbol_info('EURUSD')
print(f"Spread: {sym_info.spread_pips:.2f} pips")

# Get bars with indicators
bars = data_layer.get_bars('AAPL', 'H1', count=100)
bars_with_indicators = data_layer.calculate_technical_indicators(
    bars,
    indicators=['RSI', 'MACD', 'BB', 'SMA']
)

# Get current price
ask, bid = data_layer.get_current_price('EURUSD')
```

**Features:**
- Automatic asset type detection
- Symbol info caching
- Technical indicator calculation
- Multi-asset bar data retrieval

---

### 4. **Multi-Asset Executor** (`multi_asset_executor.py`)

**Purpose:** Execute trades across asset types with asset-specific logic

**Key Classes:**
- `TradeExecution` - Execution result
- `ExecutionMetrics` - Trade statistics
- `MultiAssetExecutor` - Main execution engine

**Usage:**
```python
from multi_asset_executor import MultiAssetExecutor

executor = MultiAssetExecutor(allocator)

# BUY order
result = executor.execute_buy(
    symbol="EURUSD",
    asset_type=AssetType.FOREX,
    lot_size=0.1,
    signal_strength=0.8,
    stop_loss_pips=50,
    take_profit_pips=100,
)

if result.success:
    print(f"✅ Opened position {result.ticket}")
else:
    print(f"❌ Order failed: {result.message}")

# Close position
result = executor.close_position(position)
```

**Features:**
- Asset-specific pip value handling
- Automatic lot size validation
- Margin checking
- Execution quality tracking

---

### 5. **Multi-Asset Dashboard** (`pages/Multi_Asset_Dashboard.py`)

**Purpose:** Unified dashboard for all assets

**Features:**
- Portfolio overview (all assets)
- Performance by asset type
- Capital allocation visualization
- Position breakdown
- Risk metrics
- Best/worst position tracking

**To Access:**
1. Open Streamlit app: `streamlit run app.py`
2. Click "Multi-Asset Dashboard" in sidebar
3. Select allocation strategy
4. View comprehensive portfolio metrics

---

## 🚀 Installation & Testing

### Step 1: Verify Files Created

Check that all files exist:
```bash
cd c:\Users\HP\forex_bot
ls -la *.py  # Should see all new files
```

### Step 2: Run Integration Test

```bash
python test_multi_asset_framework.py
```

Expected output:
```
✅ TEST 1: IMPORT ALL MODULES - PASS
✅ TEST 2: PORTFOLIO MANAGER - PASS
✅ TEST 3: CAPITAL ALLOCATOR - PASS
✅ TEST 4: DATA LAYER - PASS
✅ TEST 5: MULTI-ASSET EXECUTOR - PASS
✅ TEST 6: FULL INTEGRATION - PASS

Total: 6/6 tests passed
🎉 All tests passed! Multi-asset framework is ready to use.
```

### Step 3: Test Dashboard

Open the dashboard in Streamlit:
```bash
streamlit run app.py
# Click "Multi-Asset Dashboard" in sidebar
```

You should see:
- Portfolio metrics across all assets
- Capital allocation breakdown
- Performance by asset type
- Position details

---

## 📝 Usage Examples

### Example 1: View Multi-Asset Portfolio

```python
from portfolio_manager import PortfolioManager
from mt5_connector import connect, get_open_positions, get_account_balance, get_account_equity

connect()

# Create portfolio
portfolio = PortfolioManager()

# Add all positions
positions = get_open_positions()
for pos in positions:
    portfolio.add_position(pos)

# Calculate metrics
metrics = portfolio.calculate_metrics(
    balance=get_account_balance(),
    equity=get_account_equity()
)

# Print summary
print(portfolio.get_position_summary())

# Get metrics as dict for API
metrics_dict = portfolio.get_metrics_dict()
```

### Example 2: Allocate Capital and Execute Trades

```python
from capital_allocator import CapitalAllocator, AllocationStrategy
from multi_asset_executor import MultiAssetExecutor
from portfolio_manager import AssetType

# Allocate capital
allocator = CapitalAllocator(AllocationStrategy.EQUAL_WEIGHT)
allocations = allocator.allocate_capital(total_capital=10000, max_total_positions=16)

print(allocator.get_allocation_summary())

# Execute trades
executor = MultiAssetExecutor(allocator)

# Trade forex
result_forex = executor.execute_buy(
    symbol="EURUSD",
    asset_type=AssetType.FOREX,
    lot_size=0.1,
    signal_strength=0.8,
)

# Trade stock
result_stock = executor.execute_buy(
    symbol="AAPL",
    asset_type=AssetType.STOCKS,
    lot_size=2.0,
    signal_strength=0.7,
)

# Trade crypto
result_crypto = executor.execute_buy(
    symbol="BTC",
    asset_type=AssetType.CRYPTO,
    lot_size=0.001,
    signal_strength=0.9,
)

print(executor.get_execution_summary())
```

### Example 3: Get Market Data with Indicators

```python
from data_layer import DataLayer

data_layer = DataLayer()

# Get EURUSD hourly data
eurusd_1h = data_layer.get_bars('EURUSD', 'H1', count=100)
eurusd_1h = data_layer.calculate_technical_indicators(eurusd_1h)

# Get AAPL daily data
aapl_d1 = data_layer.get_bars('AAPL', 'D1', count=50)
aapl_d1 = data_layer.calculate_technical_indicators(aapl_d1)

# Get BTC 4-hour data
btc_h4 = data_layer.get_bars('BTC', 'H4', count=100)
btc_h4 = data_layer.calculate_technical_indicators(btc_h4)

# Access indicators
rsi = eurusd_1h['RSI'].iloc[-1]
macd = eurusd_1h['MACD'].iloc[-1]
bb_upper = eurusd_1h['BB_Upper'].iloc[-1]
```

---

## 🔗 Integration with Existing Bot

### Option A: Replace Existing Strategy Engine

Update `strategy.py` to use multi-asset framework:

```python
from portfolio_manager import PortfolioManager, AssetType
from data_layer import DataLayer
from capital_allocator import CapitalAllocator

def generate_signal_multi_asset(symbol, indicators_df):
    """Generate signal for any asset type"""
    
    # Detect asset type
    portfolio = PortfolioManager()
    asset_type = portfolio._detect_asset_type(symbol)
    
    # Calculate indicators (all assets)
    data_layer = DataLayer()
    indicators = data_layer.calculate_technical_indicators(indicators_df)
    
    # Generate signal (asset-agnostic)
    rsi = indicators['RSI'].iloc[-1]
    macd = indicators['MACD'].iloc[-1]
    
    if rsi < 30 and macd > 0:
        return "BUY"
    elif rsi > 70 and macd < 0:
        return "SELL"
    return "HOLD"
```

### Option B: Run Alongside Existing Bot

Keep existing bot, add multi-asset trading separately:

```python
# In app.py or separate script
from multi_asset_executor import MultiAssetExecutor
from capital_allocator import CapitalAllocator, AllocationStrategy

def run_multi_asset_trading():
    allocator = CapitalAllocator(AllocationStrategy.EQUAL_WEIGHT)
    allocator.allocate_capital(balance=5000, max_total_positions=8)
    
    executor = MultiAssetExecutor(allocator)
    
    # Trade different symbols
    # ... your trading logic
```

---

## 💡 Allocation Strategies Explained

### CONSERVATIVE (50% Forex, 30% Stocks, 20% Other)
**Best for:** Risk-averse traders
- Prefers liquid forex pairs
- Limited stock exposure
- No crypto trading
- Low leverage (1-5x)

### EQUAL_WEIGHT (40% Forex, 30% Stocks, 30% Other)
**Best for:** Balanced portfolios
- Diversified across asset types
- Medium leverage (2-10x)
- Small crypto allocation (5%)

### AGGRESSIVE (30% Forex, 35% Stocks, 35% Other)
**Best for:** Growth-focused traders
- Higher stock allocation
- More crypto exposure
- Higher leverage (5-10x)
- More positions per asset

### RISK_PARITY (Inverse to Volatility)
**Best for:** Risk-focused traders
- Allocates more to stable assets
- Less to volatile assets
- Equal risk contribution
- Professional-grade approach

---

## 🎯 Next Steps

### Immediate (This Week)
1. ✅ Run `test_multi_asset_framework.py` to verify all components
2. ✅ Open Multi-Asset Dashboard in Streamlit
3. ✅ Review portfolio metrics across asset types

### Short-term (Next Week)
1. Integrate multi-asset data into strategy signals
2. Add stock and crypto symbols to trading watchlist
3. Test allocation strategies with small capital
4. Monitor execution quality across asset types

### Medium-term (Weeks 2-4)
1. Transition from forex-only to multi-asset trading
2. Implement asset-specific risk management
3. Build asset-allocation optimization
4. Add portfolio rebalancing logic

### Long-term (Month 2+)
1. Machine learning signal generation per asset type
2. Cross-asset correlation analysis
3. Portfolio optimization algorithms
4. Advanced risk analytics

---

## 📊 Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `portfolio_manager.py` | Multi-asset portfolio tracking | 300+ |
| `capital_allocator.py` | Intelligent capital allocation | 400+ |
| `data_layer.py` | Unified market data access | 350+ |
| `multi_asset_executor.py` | Asset-aware trade execution | 350+ |
| `pages/Multi_Asset_Dashboard.py` | Streamlit dashboard | 300+ |
| `test_multi_asset_framework.py` | Integration tests | 400+ |

**Total:** 2,000+ lines of production-ready code

---

## ❓ FAQ

**Q: Will this affect my existing forex trading?**
A: No. These components are standalone and can run independently. Your existing bot continues unchanged until you integrate.

**Q: Can I trade stocks without a stocks broker?**
A: No. Your broker (Interactive Brokers, Libertex, etc.) must support stocks in MT5. If not, use an external API for stocks.

**Q: How often should I rebalance allocations?**
A: Weekly is recommended. The allocator recalculates based on current equity.

**Q: What's the minimum capital needed?**
A: $1,000 for conservative trading, $5,000+ for multi-asset strategy.

**Q: Can I use multiple allocation strategies?**
A: Yes. Switch strategies anytime using the dashboard dropdown.

---

## 📞 Support

For issues with the framework:

1. **Run the test suite:** `python test_multi_asset_framework.py`
2. **Check logs:** Look for error messages in test output
3. **Verify MT5 connection:** `python check_session_status.py`
4. **Review documentation:** Read docstrings in each module

---

## 📜 License & Credits

This multi-asset framework is an extension of your existing forex bot, built to:
- ✅ Scale to 6 asset types
- ✅ Manage capital intelligently
- ✅ Execute trades efficiently
- ✅ Provide unified portfolio visibility

**Version: 1.0 | Status: Production Ready | Date: April 27, 2026**
