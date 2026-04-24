"""
MULTI-ASSET TRADING EXTENSION BRAINSTORM
========================================

Current State: Forex-only trading bot
Goal: Support Forex, Gold (XAUUSD), Stocks, etc.

Three Key Components Breakdown:
1. Portfolio Initialization
2. Capital Allocation  
3. Trade Execution Based on Allocation

═══════════════════════════════════════════════════════════════════════════════
1. PORTFOLIO INITIALIZATION
═══════════════════════════════════════════════════════════════════════════════

WHAT NEEDS TO CHANGE:
├─ Asset Class Definition
├─ Initial Capital Distribution
├─ Risk Profile Per Asset
└─ Market Hour Configuration

CURRENT STRUCTURE:
  config.AVAILABLE_SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY"]  ← Forex only

PROPOSED STRUCTURE:

  config.py:
  ──────────
  PORTFOLIO_CONFIG = {
      "total_capital": 10000,  # Total trading capital
      "asset_classes": {
          "forex": {
              "capital_allocation": 0.40,  # 40% to forex
              "symbols": ["EURUSD", "GBPUSD", "USDJPY"],
              "risk_per_trade": 0.02,
              "max_positions": 10,
              "leverage": 100,
              "market_hours": {
                  "EURUSD": ["london", "overlap"],
                  "GBPUSD": ["london", "overlap"],
                  "USDJPY": ["asian", "london", "overlap"]
              }
          },
          "commodities": {
              "capital_allocation": 0.30,  # 30% to commodities (gold, oil, etc.)
              "symbols": ["XAUUSD", "XAGUSD", "WTIUSD"],
              "risk_per_trade": 0.015,
              "max_positions": 5,
              "leverage": 50,
              "market_hours": {
                  "XAUUSD": ["24h"],  # Gold trades 24/5
                  "XAGUSD": ["24h"],
                  "WTIUSD": ["new_york"]
              }
          },
          "stocks": {
              "capital_allocation": 0.30,  # 30% to stocks
              "symbols": ["AAPL", "GOOGL", "MSFT", "TSLA"],
              "risk_per_trade": 0.01,
              "max_positions": 8,
              "leverage": 2,
              "market_hours": {
                  "AAPL": ["ny_market"],     # NYSE hours
                  "GOOGL": ["ny_market"],
                  "MSFT": ["ny_market"],
                  "TSLA": ["ny_market"]
              }
          }
      }
  }

ARCHITECTURE:

  NEW: AssetClass Model (abstract base)
  ──────────────────────────────────────
  class AssetClass:
      asset_type: str  # "forex", "commodity", "stock", "crypto"
      leverage: float
      spread_type: "pips" vs "percentage" vs "fixed"
      min_lot_size: float
      lot_step: float
      market_hours: List[TimeRange]
      contract_size: float  # 100000 for forex, 1 for stocks
      point_value: float    # Pip value calculation

  NEW: PortfolioManager
  ─────────────────────
  class PortfolioManager:
      def initialize_portfolio():
          """
          1. Validate total capital
          2. Distribute capital per asset class
          3. Calculate risk budgets per asset
          4. Initialize position limits per asset
          5. Set up margin requirements per asset
          """
          
      def get_allocated_capital(asset_class: str) -> float
      def get_risk_budget(asset_class: str) -> float
      def get_max_positions_per_asset(asset_class: str) -> int

INITIALIZATION FLOW:

  Step 1: Portfolio Setup
  ──────────────────────
  PortfolioManager.initialize_portfolio()
    ├─ Validate: total_capital > 0
    ├─ Validate: allocations sum to 100%
    ├─ For each asset class:
    │   ├─ Calculate allocated capital
    │   ├─ Calculate margin requirements
    │   ├─ Set risk budget
    │   └─ Initialize position tracking
    └─ Store configuration

  Step 2: Asset Registration
  ──────────────────────────
  For each asset in portfolio:
    ├─ Connect to data source (MT5 for forex/commodities, API for stocks)
    ├─ Fetch symbol metadata (contract size, spreads, trading hours)
    ├─ Validate symbol is tradeable
    └─ Load historical data for indicators

  Step 3: Risk Initialization
  ──────────────────────────
  For each asset class:
    ├─ Calculate max lot size per trade
    ├─ Set stop loss points (pips for forex, % for stocks)
    ├─ Set take profit points
    ├─ Calculate max positions limit
    └─ Set drawdown limits per asset


═══════════════════════════════════════════════════════════════════════════════
2. CAPITAL ALLOCATION
═══════════════════════════════════════════════════════════════════════════════

WHAT NEEDS TO CHANGE:
├─ Dynamic Capital Distribution
├─ Margin Management Across Assets
├─ Risk Balancing
└─ Rebalancing Logic

CURRENT STRUCTURE:
  # All capital goes to one account
  account_balance = get_account_balance()
  max_positions_global = 50
  risk_per_trade = 0.02  # Fixed percentage

PROPOSED STRUCTURE:

  NEW: CapitalAllocator
  ────────────────────
  class CapitalAllocator:
      def allocate_capital():
          """
          1. Get total available capital
          2. Calculate margin used per asset class
          3. Distribute remaining capital per allocation %
          4. Calculate tradeable capital per asset
          """
          
      def get_tradeable_capital(asset_class: str) -> float
      def calculate_lot_size(asset_class: str, symbol: str) -> float
      def rebalance_portfolio() -> Dict
      def check_margin_health() -> Dict

ALLOCATION FLOW:

  Example: Account with $10,000
  ──────────────────────────────
  
  Total Capital: $10,000
  
  1. INITIAL ALLOCATION (by config percentages):
     ├─ Forex:       40% = $4,000
     ├─ Commodities: 30% = $3,000
     └─ Stocks:      30% = $3,000

  2. CALCULATE MARGIN REQUIRED:
     ├─ Forex:
     │   ├─ 3 positions × 1.0 lot × $100k contract ÷ 100 leverage = $3,000 margin
     │   └─ Remaining tradeable: $4,000 - $3,000 = $1,000
     │
     ├─ Commodities:
     │   ├─ 2 positions × 10 contracts × $100/contract ÷ 50 leverage = $400 margin
     │   └─ Remaining tradeable: $3,000 - $400 = $2,600
     │
     └─ Stocks:
         ├─ 2 positions × 10 shares × $150/share ÷ 2 leverage = $1,500 margin
         └─ Remaining tradeable: $3,000 - $1,500 = $1,500

  3. DYNAMIC LOT CALCULATION:
     ───────────────────────
     For new trade signal on EURUSD:
       
       allocated_capital = $4,000 (forex allocation)
       margin_used = $3,000 (existing 3 positions)
       free_capital = $1,000
       risk_per_trade = 2% of forex allocation = $80
       
       With stop loss of 50 pips:
         lot_size = risk / (pips × point_value)
         lot_size = $80 / (50 × 0.1) = 16 micro lots

  4. POSITION COUNTING:
     ─────────────────
     BEFORE: 40/60 global (too simple)
     
     AFTER:
       Forex Positions:       3/10   (30%)
       Commodity Positions:   2/5    (40%)
       Stock Positions:       2/8    (25%)
       ─────────────────────────────
       Total: 7/23  (30% utilized)

DYNAMIC REBALANCING:

  Trigger: Every 4 hours or when drawdown > threshold
  
  IF drawdown_pct > max_drawdown_forex:
    • Reduce lot sizes for forex trades by 20%
    • Stop opening new forex positions
    • Keep other assets unaffected
    
  IF total_drawdown_pct > max_drawdown_total:
    • Reduce all position sizes by 15%
    • Close weakest performers
    • Preserve capital

NEW FUNCTIONS:

  def get_allocated_capital_by_asset(asset_class: str) -> Dict:
      """
      Returns:
      {
          'total_allocation': 4000,      # e.g., 40% of $10k
          'margin_used': 3000,
          'free_capital': 1000,
          'available_for_new_positions': 800,  # Reserve buffer
          'risk_budget': 80,             # 2% of allocation
          'max_new_positions': 2
      }
      """
      
  def calculate_lot_size_per_asset(asset_class: str, symbol: str) -> float:
      """
      Dynamic lot sizing considering:
      • Asset class allocation
      • Risk per trade (asset-specific)
      • Stop loss distance
      • Margin availability
      • Leverage limits
      """


═══════════════════════════════════════════════════════════════════════════════
3. TRADE EXECUTION BASED ON ALLOCATION
═══════════════════════════════════════════════════════════════════════════════

WHAT NEEDS TO CHANGE:
├─ Symbol-Specific Execution Logic
├─ Data Source Abstraction
├─ Asset-Aware Risk Checks
└─ Market Hour Validation

CURRENT STRUCTURE:
  mt5_connector.place_order(symbol, lot, order_type, ...)
  └─ Only works for MT5 (forex/commodities)

PROPOSED STRUCTURE:

  NEW: DataSourceFactory
  ──────────────────────
  class DataSource (abstract):
      def get_price(symbol) -> Tuple[bid, ask]
      def get_historical_data(symbol, timeframe) -> DataFrame
      def place_order(symbol, lot, order_type) -> OrderResult
      def close_position(position_id) -> bool

  Implementations:
    • MT5DataSource (for forex, commodities)
    • AlphaVantageDataSource (for stocks)
    • BinanceDataSource (for crypto, if added later)

  def get_data_source(asset_type: str) -> DataSource:
      if asset_type == "forex": return MT5DataSource()
      if asset_type == "stocks": return AlphaVantageDataSource()
      if asset_type == "crypto": return BinanceDataSource()

EXECUTION FLOW:

  1. SIGNAL GENERATION
     ─────────────────
     for asset_class in portfolio.asset_classes:
         for symbol in asset_class.symbols:
             # Check if symbol is in active trading hours
             if is_trading_hours(asset_class, symbol):
                 df = get_data(asset_class, symbol)
                 signal = generate_signal(df)
                 
                 if signal == "BUY" or signal == "SELL":
                     signals.append({
                         'asset_class': asset_class,
                         'symbol': symbol,
                         'signal': signal,
                         'score': score,
                         'data_source': get_data_source(asset_class)
                     })

  2. RISK VALIDATION
     ────────────────
     for signal in ranked_signals:
         risk_check = {
             'has_margin': check_margin_for_asset(signal.asset_class),
             'within_position_limit': check_position_limit(signal.asset_class),
             'within_risk_budget': check_risk_budget(signal.asset_class),
             'market_hours_ok': is_active_trading_time(signal),
             'spread_acceptable': check_spread(signal)
         }
         
         if all(risk_check.values()):
             signals_approved.append(signal)

  3. LOT CALCULATION
     ────────────────
     for signal in signals_approved:
         allocated_capital = get_allocated_capital_by_asset(signal.asset_class)
         lot_size = calculate_lot_size(
             asset_class=signal.asset_class,
             symbol=signal.symbol,
             risk_budget=allocated_capital['risk_budget'],
             stop_loss=config[signal.asset_class]['stop_loss']
         )
         signal['lot_size'] = lot_size

  4. EXECUTION
     ──────────
     for signal in signals_ready_to_execute:
         data_source = get_data_source(signal.asset_class)
         
         try:
             result = data_source.place_order(
                 symbol=signal.symbol,
                 lot=signal.lot_size,
                 order_type=signal.signal_to_order_type()
             )
             
             # Log trade with asset class metadata
             log_trade({
                 'asset_class': signal.asset_class,
                 'symbol': signal.symbol,
                 'result': result
             })
         except Exception as e:
             handle_execution_error(signal, e)

NEW STRUCTURE:

  NEW: TradeExecutor
  ──────────────────
  class TradeExecutor:
      def __init__(self, portfolio_manager, capital_allocator):
          self.portfolio = portfolio_manager
          self.allocator = capital_allocator
          self.data_sources = {
              'forex': MT5DataSource(),
              'commodities': MT5DataSource(),
              'stocks': AlphaVantageDataSource()
          }
      
      def generate_signals(self) -> List[Signal]:
          """Generate signals for all assets in portfolio"""
          
      def validate_execution(self, signal: Signal) -> bool:
          """Check all constraints before execution"""
          
      def execute_trade(self, signal: Signal) -> TradeResult:
          """Execute trade on appropriate data source"""
          
      def manage_position(self, position: Position) -> None:
          """Update position P&L, check stop loss/take profit"""


═══════════════════════════════════════════════════════════════════════════════
IMPLEMENTATION PLAN (Phased)
═══════════════════════════════════════════════════════════════════════════════

PHASE 1: Foundation (Week 1)
────────────────────────────
□ Create portfolio configuration format
□ Build AssetClass model
□ Implement PortfolioManager
□ Build CapitalAllocator
□ Write unit tests

PHASE 2: Data Sources (Week 2)
──────────────────────────────
□ Create DataSource abstraction
□ Implement MT5DataSource (wrap existing code)
□ Implement StockDataSource (Alpha Vantage API)
□ Add market hours validation per asset

PHASE 3: Execution (Week 3)
───────────────────────────
□ Build TradeExecutor with asset-aware logic
□ Implement dynamic lot sizing per asset class
□ Create risk validation per asset
□ Integrate with existing dashboard

PHASE 4: Integration & Testing (Week 4)
────────────────────────────────────────
□ Full end-to-end testing
□ Backtesting on multi-asset data
□ Dashboard updates
□ Documentation


═══════════════════════════════════════════════════════════════════════════════
CODE EXAMPLES
═══════════════════════════════════════════════════════════════════════════════

1. PORTFOLIO INITIALIZATION:

  from portfolio_manager import PortfolioManager
  
  portfolio = PortfolioManager(
      total_capital=10000,
      config=PORTFOLIO_CONFIG
  )
  portfolio.initialize()
  # Result: Portfolio ready with capital allocated to each asset class


2. CAPITAL ALLOCATION:

  from capital_allocator import CapitalAllocator
  
  allocator = CapitalAllocator(portfolio)
  
  forex_info = allocator.get_allocated_capital('forex')
  print(forex_info)
  # Output:
  # {
  #     'total_allocation': 4000,
  #     'margin_used': 3000,
  #     'free_capital': 1000,
  #     'risk_budget': 80
  # }
  
  lot_size = allocator.calculate_lot_size(
      asset_class='forex',
      symbol='EURUSD',
      stop_loss_pips=50
  )
  # Output: 0.16 lots


3. TRADE EXECUTION:

  from trade_executor import TradeExecutor
  
  executor = TradeExecutor(portfolio, allocator)
  
  signals = executor.generate_signals()
  # Signals from all asset classes: forex, commodities, stocks
  
  for signal in signals:
      if executor.validate_execution(signal):
          result = executor.execute_trade(signal)
          print(f"{signal.asset_class}/{signal.symbol}: {result}")


═══════════════════════════════════════════════════════════════════════════════
KEY CONSIDERATIONS
═══════════════════════════════════════════════════════════════════════════════

1. MARGIN MANAGEMENT
   • Different leverage per asset (100x forex vs 2x stocks)
   • Track margin usage per asset class
   • Rebalance if total margin utilization > threshold

2. MARKET HOURS
   • Forex: 24/5 with session differences
   • Stocks: NYSE/NASDAQ specific hours
   • Commodities: Variable (gold 24/5, oil has limited hours)

3. RISK PARAMETERS
   • Stop loss in different units (pips vs % vs fixed)
   • Contract sizes vary dramatically
   • Volatility normalization needed

4. DATA SOURCES
   • MT5 for forex/commodities
   • Stock APIs (Alpha Vantage, IB, etc.)
   • Different data quality and latency

5. POSITION TRACKING
   • Need to distinguish positions by asset class
   • Different reporting per asset
   • Cross-asset performance analysis


═══════════════════════════════════════════════════════════════════════════════
QUESTIONS TO ANSWER BEFORE IMPLEMENTATION
═══════════════════════════════════════════════════════════════════════════════

1. What stock broker/API will you use? (IB, Alpha Vantage, etc.)
2. Do you want dynamic allocation or fixed percentages?
3. Should drawdown limits apply per-asset or global?
4. How should positions be counted? (Per asset, by notional value, by risk %)
5. What rebalancing frequency? (Daily, weekly, on drawdown)
6. Should you support leverage for stocks?
7. How to handle different market hours for signal generation?
8. Should portfolio have correlation-aware position sizing?

"""
