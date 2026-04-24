"""
MULTI-ASSET ARCHITECTURE DIAGRAM
═════════════════════════════════════════════════════════════════════════════

CURRENT ARCHITECTURE (Forex-Only):

    config.py
        ↓
    MT5 Connector ← → Trading Dashboard
        ↓
    Risk Management
        ↓
    Strategy/Indicators
        ↓
    Position Manager

Problems:
• Tightly coupled to MT5 and forex
• Single data source
• No asset class abstraction
• Capital allocation is implicit


NEW ARCHITECTURE (Multi-Asset):

┌─────────────────────────────────────────────────────────────────────────┐
│                         PORTFOLIO LAYER                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │           PortfolioManager                                   │    │
│  │  • Initialize portfolio (Forex 40%, Commodities 30%, etc)   │    │
│  │  • Track allocations per asset class                        │    │
│  │  • Manage market hours per asset                            │    │
│  └──────────────┬───────────────────────────────────────────────┘    │
│                 │                                                     │
└─────────────────┼─────────────────────────────────────────────────────┘
                  │
┌─────────────────┼─────────────────────────────────────────────────────┐
│                 │        CAPITAL ALLOCATION LAYER                     │
├─────────────────┼─────────────────────────────────────────────────────┤
│                 │                                                     │
│  ┌──────────────▼───────────────────────────────────────┐            │
│  │         CapitalAllocator                             │            │
│  │  • Get allocated capital per asset ($10k total)      │            │
│  │  • Calculate dynamic lot sizes                       │            │
│  │  • Track margin per asset class                      │            │
│  │  • Rebalance on drawdown                             │            │
│  └────┬────────────┬────────────┬──────────────────┬────┘            │
│       │            │            │                  │                  │
│  ┌────▼──┐  ┌──────▼──┐  ┌─────▼───┐  ┌────────────▼───────┐      │
│  │ Forex │  │Commodity│  │ Stocks  │  │ Rebalancer         │      │
│  │ $4k   │  │ $3k     │  │ $3k     │  │ (Risk management)  │      │
│  └───────┘  └─────────┘  └─────────┘  └────────────────────┘      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                  │
┌─────────────────┼─────────────────────────────────────────────────────┐
│                 │      DATA SOURCE ABSTRACTION LAYER                   │
├─────────────────┼─────────────────────────────────────────────────────┤
│                 │                                                     │
│  ┌──────────────▼────────────────────────────────────────────┐      │
│  │         DataSourceFactory                                │      │
│  │         (Determines which data source for each asset)    │      │
│  └──────┬────────────┬─────────────┬──────────────────┐─────┘      │
│         │            │             │                  │             │
│    ┌────▼─────┐  ┌───▼──────┐  ┌──▼────────┐  ┌──────▼──────┐    │
│    │   MT5    │  │  Stock   │  │ Commodity │  │   Crypto    │    │
│    │ DataSrc  │  │ DataSrc  │  │  DataSrc  │  │   DataSrc   │    │
│    │(Forex,   │  │(IB, Yahoo│  │(Futures)  │  │ (Binance)   │    │
│    │ Commodit)│  │ Finance) │  │           │  │             │    │
│    └────┬─────┘  └───┬──────┘  └──┬────────┘  └──────┬──────┘    │
│         │            │             │                  │            │
└─────────┼────────────┼─────────────┼──────────────────┼────────────┘
          │            │             │                  │
┌─────────┼────────────┼─────────────┼──────────────────┼────────────┐
│         │    EXECUTION LAYER                        │            │
├─────────┼────────────┼─────────────┼──────────────────┼────────────┤
│         │            │             │                  │            │
│  ┌──────▼────────────▼─────────────▼──────────────────▼────┐      │
│  │              TradeExecutor                              │      │
│  │  • Generate signals (all assets)                       │      │
│  │  • Validate risk across all assets                     │      │
│  │  • Calculate asset-specific lot sizes                  │      │
│  │  • Route to appropriate data source                    │      │
│  │  • Execute trades (asset-aware)                        │      │
│  └──────┬─────────────────────────────────────────────────┘      │
│         │                                                        │
└─────────┼────────────────────────────────────────────────────────┘
          │
┌─────────┼────────────────────────────────────────────────────────┐
│         │         STRATEGY / INDICATORS LAYER                     │
├─────────┼────────────────────────────────────────────────────────┤
│         │                                                        │
│  ┌──────▼────────────────────────────────────────────────────┐ │
│  │    SignalGenerator (Asset-Aware)                          │ │
│  │  • RSI, MACD, Bollinger Bands (universal)               │ │
│  │  • Volatility-adjusted stop loss (asset-specific)       │ │
│  │  • Market hours validation per asset                    │ │
│  │  • Asset-specific confirmation rules                    │ │
│  └──────┬─────────────────────────────────────────────────────┘ │
│         │                                                        │
└─────────┼────────────────────────────────────────────────────────┘
          │
┌─────────┼────────────────────────────────────────────────────────┐
│         │      POSITION MANAGEMENT LAYER                         │
├─────────┼────────────────────────────────────────────────────────┤
│         │                                                        │
│  ┌──────▼────────────────────────────────────────────────────┐ │
│  │    PositionManager (Asset-Aware)                          │ │
│  │  • Track positions per asset class                       │ │
│  │  • Calculate P&L per asset and total                     │ │
│  │  • Manage stop loss/take profit (asset-specific)         │ │
│  │  • Close positions on risk thresholds                    │ │
│  └──────┬─────────────────────────────────────────────────────┘ │
│         │                                                        │
└─────────┼────────────────────────────────────────────────────────┘
          │
┌─────────▼────────────────────────────────────────────────────────┐
│                  DASHBOARD / REPORTING                            │
├──────────────────────────────────────────────────────────────────┤
│  • Portfolio overview (allocation % and capital)                 │
│  • Per-asset performance metrics                                 │
│  • Risk metrics per asset class                                  │
│  • Live position tracking (multi-asset)                          │
│  • Trade execution history by asset                              │
└──────────────────────────────────────────────────────────────────┘


DATA FLOW EXAMPLE: New Signal in Forex
═════════════════════════════════════════════════════════════════════════════

1. PortfolioManager
   └─→ "EURUSD available 08:19 UTC (London session active)"

2. TradeExecutor.generate_signals()
   ├─→ Get data source: MT5DataSource
   ├─→ Fetch EURUSD price data
   └─→ SignalGenerator.generate_signal(EURUSD data)
       ├─→ Compute indicators (RSI, MACD, BB)
       ├─→ Generate: BUY signal, confidence: 8/10
       └─→ Return signal with asset_class='forex'

3. TradeExecutor.validate_execution()
   ├─→ Check: Is EURUSD in active trading hours? YES
   ├─→ Check: Position limit for forex? 3/10 ✓
   ├─→ Check: Margin available? $1,000 free in forex allocation ✓
   ├─→ Check: Spread acceptable? 1.2 pips < 3.0 max ✓
   ├─→ Check: Risk budget? $80 risk budget remaining ✓
   └─→ Validation passed

4. CapitalAllocator.calculate_lot_size()
   ├─→ Get forex allocation: $4,000
   ├─→ Get risk budget: $80
   ├─→ Get stop loss: 50 pips
   ├─→ Calculate: 0.16 lots (80 / (50 * 0.1))
   └─→ Return: lot_size = 0.16

5. TradeExecutor.execute_trade()
   ├─→ Data source: MT5DataSource
   ├─→ Place BUY order: EURUSD 0.16 lots
   ├─→ Log trade with asset_class='forex'
   ├─→ Update PositionManager (add position)
   └─→ Update CapitalAllocator (reduce free capital)

6. Dashboard Update
   ├─→ Show: Forex 4/10 positions
   ├─→ Show: Capital allocated to forex $4k
   ├─→ Show: Current P&L by asset class
   └─→ Show: Risk metrics by asset


COMPARISON: Old vs New Position Counting
═════════════════════════════════════════════════════════════════════════════

OLD (Forex-only):
  Positions: 40/60 global
  └─ No distinction between assets
  └─ No capital tracking per asset
  └─ No leverage awareness

NEW (Multi-asset):
  Forex:      3/10 positions   | $4,000 allocated   | 75% margin used
  Commodities: 2/5  positions  | $3,000 allocated   | 13% margin used
  Stocks:      2/8  positions  | $3,000 allocated   | 50% margin used
  ──────────────────────────────────────────────────────────────────────
  Total:      7/23 positions   | $10,000 total      | 48% margin used
  
  Benefits:
  • Can see concentration per asset (is forex over-leveraged?)
  • Can limit positions per asset independently
  • Can apply different risk per asset
  • Can manage market hours per asset


KEY FILES TO CREATE
═════════════════════════════════════════════════════════════════════════════

1. portfolio_manager.py
   └─ PortfolioManager class
   └─ AssetClass model
   └─ Portfolio initialization

2. capital_allocator.py
   └─ CapitalAllocator class
   └─ Dynamic lot sizing
   └─ Capital tracking per asset

3. data_sources/
   ├─ data_source.py (abstract base)
   ├─ mt5_data_source.py (existing MT5 logic)
   ├─ stock_data_source.py (new - Alpha Vantage/IB)
   └─ factory.py (DataSourceFactory)

4. trade_executor.py
   └─ TradeExecutor class
   └─ Asset-aware signal generation
   └─ Asset-aware validation & execution

5. position_manager.py (update existing)
   └─ Track positions per asset class
   └─ Calculate P&L per asset

6. config_multi_asset.py (new config format)
   └─ PORTFOLIO_CONFIG with asset definitions
   └─ Market hours per asset
   └─ Risk parameters per asset


MIGRATION STRATEGY
═════════════════════════════════════════════════════════════════════════════

Phase 0 (Current): Forex-only app
Phase 1: Foundation (PortfolioManager, CapitalAllocator work side-by-side)
Phase 2: Data abstraction (Multiple data sources)
Phase 3: Full multi-asset execution
Phase 4: Migration complete (old code removable)

The key: New components can coexist with old ones during transition
"""
