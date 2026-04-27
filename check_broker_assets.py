#!/usr/bin/env python
"""
Check what asset classes your MT5 broker supports
Run this to see if you can trade stocks, commodities, crypto, etc.
"""

import MetaTrader5 as mt5
import logging

logging.basicConfig(level=logging.INFO)

def check_broker_assets():
    """Scan all available symbols and categorize them"""
    
    try:
        if not mt5.initialize():
            print("❌ MT5 not initialized. Start MetaTrader 5 first.")
            return
        
        print("=" * 70)
        print("BROKER ASSET AVAILABILITY CHECK")
        print("=" * 70)
        
        # Get all available symbols
        symbols = mt5.symbols_get()
        if not symbols:
            print("❌ No symbols found. Check your MT5 terminal.")
            return
        
        print(f"\n✅ Found {len(symbols)} total symbols\n")
        
        # Categorize symbols
        categories = {
            'Forex': [],
            'Commodities': [],
            'Indices': [],
            'Stocks': [],
            'Crypto': [],
            'Other': []
        }
        
        for symbol in symbols:
            name = symbol.name
            
            # Categorize by symbol name patterns
            if len(name) == 6 and name[-3:] in ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD']:
                categories['Forex'].append(name)
            elif name.startswith('XAU') or name.startswith('XAG') or name in ['WTIUSD', 'BRENTUSD', 'NGAS']:
                categories['Commodities'].append(name)
            elif name.startswith('SPX') or name.startswith('NDX') or name.startswith('DAX') or 'INDEX' in name.upper():
                categories['Indices'].append(name)
            elif name.startswith('BTC') or name.startswith('ETH') or name.startswith('XRP'):
                categories['Crypto'].append(name)
            elif len(name) <= 6 and name.isupper() and len(name) >= 4:
                # Likely a stock symbol (AAPL, GOOGL, MSFT, etc.)
                categories['Stocks'].append(name)
            else:
                categories['Other'].append(name)
        
        # Print results
        for category, symbols_list in categories.items():
            if symbols_list:
                status = "✅"
                symbol_str = ", ".join(sorted(symbols_list)[:10])  # Show first 10
                if len(symbols_list) > 10:
                    symbol_str += f", ... and {len(symbols_list) - 10} more"
                print(f"{status} {category:15} ({len(symbols_list):3} symbols): {symbol_str}")
            else:
                status = "❌"
                print(f"{status} {category:15} (  0 symbols): NOT AVAILABLE")
        
        print("\n" + "=" * 70)
        print("RECOMMENDATION FOR YOUR MULTI-ASSET BOT:")
        print("=" * 70)
        
        if categories['Stocks']:
            print("\n✅ Your broker SUPPORTS stocks in MT5!")
            print(f"   Available stocks: {', '.join(categories['Stocks'][:5])}")
            print("\n   RECOMMENDATION:")
            print("   • Use MT5 for ALL assets (forex + commodities + stocks)")
            print("   • Architecture is simpler (one data source)")
            print("   • No need for external stock APIs")
            
            example_stocks = categories['Stocks'][:3]
            print(f"\n   You can trade: {', '.join(example_stocks)}")
        else:
            print("\n❌ Your broker does NOT support stocks in MT5")
            print("   Only forex and commodities available")
            print("\n   RECOMMENDATIONS:")
            print("   • Option 1: Use only forex + commodities for now")
            print("   • Option 2: Switch brokers (try IB, Libertex, FXOpen)")
            print("   • Option 3: Add external stock API later (Alpha Vantage)")
        
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure MT5 is running and connected to a broker")
    
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    check_broker_assets()
