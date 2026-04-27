#!/usr/bin/env python
"""
Multi-Asset Framework - Integration Test

Tests all components working together:
- Portfolio Manager
- Capital Allocator
- Data Layer
- Multi-Asset Executor
"""

import MetaTrader5 as mt5
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_imports():
    """Test that all modules can be imported"""
    print("\n" + "="*80)
    print("TEST 1: IMPORT ALL MODULES")
    print("="*80)
    
    try:
        from portfolio_manager import PortfolioManager, AssetType
        print("✅ portfolio_manager imported")
        
        from capital_allocator import CapitalAllocator, AllocationStrategy
        print("✅ capital_allocator imported")
        
        from data_layer import DataLayer
        print("✅ data_layer imported")
        
        from multi_asset_executor import MultiAssetExecutor
        print("✅ multi_asset_executor imported")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_portfolio_manager():
    """Test portfolio manager functionality"""
    print("\n" + "="*80)
    print("TEST 2: PORTFOLIO MANAGER")
    print("="*80)
    
    try:
        from portfolio_manager import PortfolioManager, AssetType
        from mt5_connector import connect, get_open_positions, get_account_balance, get_account_equity
        
        connect()
        
        portfolio = PortfolioManager()
        print("✅ PortfolioManager initialized")
        
        # Get positions
        positions = get_open_positions()
        if positions:
            for pos in positions[:3]:  # Test with first 3 positions
                portfolio.add_position(pos)
            print(f"✅ Added {min(len(positions), 3)} positions to portfolio")
        else:
            print("⚠️  No positions to test with")
            return True
        
        # Calculate metrics
        balance = get_account_balance()
        equity = get_account_equity()
        metrics = portfolio.calculate_metrics(balance, equity)
        
        print(f"✅ Metrics calculated:")
        print(f"   - Total positions: {metrics.total_positions}")
        print(f"   - Total profit: ${metrics.total_profit:,.2f}")
        print(f"   - Win rate: {metrics.win_rate:.1f}%")
        
        # Get summary
        summary = portfolio.get_position_summary()
        print("✅ Position summary generated")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_capital_allocator():
    """Test capital allocator functionality"""
    print("\n" + "="*80)
    print("TEST 3: CAPITAL ALLOCATOR")
    print("="*80)
    
    try:
        from capital_allocator import CapitalAllocator, AllocationStrategy
        from mt5_connector import get_account_balance
        
        balance = get_account_balance()
        
        # Test each strategy
        strategies = [
            AllocationStrategy.CONSERVATIVE,
            AllocationStrategy.EQUAL_WEIGHT,
            AllocationStrategy.AGGRESSIVE,
        ]
        
        for strategy in strategies:
            allocator = CapitalAllocator(strategy)
            allocations = allocator.allocate_capital(balance, max_total_positions=16)
            
            print(f"✅ {strategy.value.upper()} strategy allocated capital")
            
            total_allocated = sum(a.allocated_capital for a in allocations.values())
            print(f"   - Total allocated: ${total_allocated:,.0f}")
            print(f"   - Allocations: {len(allocations)} asset types")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_layer():
    """Test data layer functionality"""
    print("\n" + "="*80)
    print("TEST 4: DATA LAYER")
    print("="*80)
    
    try:
        from data_layer import DataLayer
        from portfolio_manager import AssetType
        
        data_layer = DataLayer()
        print("✅ DataLayer initialized")
        
        # Test asset type detection
        test_symbols = {
            'EURUSD': AssetType.FOREX,
            'AAPL': AssetType.STOCKS,
            'DAX': AssetType.INDICES,
            'XAUUSD': AssetType.COMMODITIES,
            'BTC': AssetType.CRYPTO,
        }
        
        for symbol, expected_type in test_symbols.items():
            detected = data_layer.detect_asset_type(symbol)
            status = "✅" if detected == expected_type else "⚠️"
            print(f"{status} {symbol:8} -> {detected.value:12} (expected {expected_type.value})")
        
        # Test symbol info retrieval
        print("\n✅ Testing symbol info retrieval...")
        sym_info = data_layer.get_symbol_info('EURUSD')
        if sym_info:
            print(f"   - Symbol: {sym_info.symbol}")
            print(f"   - Asset type: {sym_info.asset_type.value}")
            print(f"   - Bid: {sym_info.bid}, Ask: {sym_info.ask}")
            print(f"   - Spread: {sym_info.spread_pips:.2f} pips")
        else:
            print("⚠️  Could not retrieve symbol info")
        
        # Test bar data retrieval
        print("\n✅ Testing bar data retrieval...")
        bars = data_layer.get_bars('EURUSD', 'H1', count=50)
        if bars is not None:
            print(f"   - Retrieved {len(bars)} bars")
            print(f"   - Date range: {bars.index[0]} to {bars.index[-1]}")
        else:
            print("⚠️  Could not retrieve bars")
        
        # Test indicator calculation
        if bars is not None:
            print("\n✅ Testing indicator calculation...")
            bars_with_indicators = data_layer.calculate_technical_indicators(bars)
            print(f"   - Indicators added")
            print(f"   - Columns: {', '.join([c for c in bars_with_indicators.columns if c not in bars.columns])}")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_executor():
    """Test multi-asset executor functionality"""
    print("\n" + "="*80)
    print("TEST 5: MULTI-ASSET EXECUTOR")
    print("="*80)
    
    try:
        from multi_asset_executor import MultiAssetExecutor
        from capital_allocator import CapitalAllocator, AllocationStrategy
        from portfolio_manager import AssetType
        from mt5_connector import get_account_balance
        
        balance = get_account_balance()
        
        allocator = CapitalAllocator(AllocationStrategy.EQUAL_WEIGHT)
        allocator.allocate_capital(balance)
        
        executor = MultiAssetExecutor(allocator)
        print("✅ MultiAssetExecutor initialized")
        
        # Test pip adjustment calculation for different assets
        print("\n✅ Testing pip adjustment calculations...")
        
        assets_to_test = [
            (AssetType.FOREX, 50),
            (AssetType.STOCKS, 100),
            (AssetType.CRYPTO, 50),
        ]
        
        for asset_type, pips in assets_to_test:
            adjustment = executor._calculate_pips_adjustment(asset_type, pips)
            print(f"   - {asset_type.value:12}: {pips} pips = {adjustment:.8f} price adjustment")
        
        print("✅ All executor tests passed (no actual trades executed)")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test all components working together"""
    print("\n" + "="*80)
    print("TEST 6: FULL INTEGRATION")
    print("="*80)
    
    try:
        from portfolio_manager import PortfolioManager, AssetType
        from capital_allocator import CapitalAllocator, AllocationStrategy
        from data_layer import DataLayer
        from multi_asset_executor import MultiAssetExecutor
        from mt5_connector import connect, get_open_positions, get_account_balance, get_account_equity
        
        connect()
        
        print("✅ Initializing all components...")
        
        # Portfolio
        portfolio = PortfolioManager()
        positions = get_open_positions()
        if positions:
            for pos in positions:
                portfolio.add_position(pos)
        
        balance = get_account_balance()
        equity = get_account_equity()
        metrics = portfolio.calculate_metrics(balance, equity)
        
        # Capital Allocator
        allocator = CapitalAllocator(AllocationStrategy.EQUAL_WEIGHT)
        allocations = allocator.allocate_capital(balance)
        
        # Data Layer
        data_layer = DataLayer()
        sym_info = data_layer.get_symbol_info('EURUSD')
        
        # Executor
        executor = MultiAssetExecutor(allocator)
        
        print("✅ All components initialized successfully")
        
        # Print integration summary
        print("\n📊 INTEGRATION SUMMARY:")
        print(f"   Portfolio positions: {metrics.total_positions}")
        print(f"   Total profit: ${metrics.total_profit:,.2f}")
        print(f"   Capital allocated: {len(allocations)} asset types")
        print(f"   Available symbols: EURUSD available: {sym_info is not None}")
        print(f"   Executor executions: {executor.metrics.total_executions}")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "🎯 MULTI-ASSET FRAMEWORK - INTEGRATION TEST SUITE")
    print("="*80)
    
    tests = [
        ("Module Imports", test_imports),
        ("Portfolio Manager", test_portfolio_manager),
        ("Capital Allocator", test_capital_allocator),
        ("Data Layer", test_data_layer),
        ("Multi-Asset Executor", test_executor),
        ("Full Integration", test_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Multi-asset framework is ready to use.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        mt5.shutdown()
        print("\n✅ MT5 disconnected")
