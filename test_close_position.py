#!/usr/bin/env python
"""
Test and debug the close position logic
"""

import MetaTrader5 as mt5
import logging
from mt5_connector import connect, get_open_positions, close_position

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

print("="*70)
print("CLOSE POSITION LOGIC TEST")
print("="*70)
print()

try:
    # Connect to MT5
    print("1. Connecting to MT5...")
    connect()
    print("   ✅ Connected\n")
    
    # Get open positions
    print("2. Fetching open positions...")
    positions = get_open_positions()
    
    if not positions:
        print("   ⚠️  No open positions found")
    else:
        print(f"   ✅ Found {len(positions)} open positions\n")
        
        # Analyze first position
        position = positions[0]
        print(f"3. Analyzing first position (Ticket: {position.ticket}):")
        print(f"   Symbol: {position.symbol}")
        print(f"   Type: {position.type} (0=BUY, 1=SELL)")
        print(f"   Volume: {position.volume}")
        print(f"   Open Price: {position.price_open}")
        print(f"   Current Profit: ${position.profit:.2f}")
        print()
        
        # Test the order type logic
        print(f"4. Testing order_type logic:")
        order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        print(f"   Position.type = {position.type}")
        print(f"   mt5.ORDER_TYPE_BUY = {mt5.ORDER_TYPE_BUY}")
        print(f"   mt5.ORDER_TYPE_SELL = {mt5.ORDER_TYPE_SELL}")
        print(f"   Calculated order_type = {order_type}")
        print(f"   Expected: {'SELL' if order_type == mt5.ORDER_TYPE_SELL else 'BUY'}")
        print()
        
        # Test price retrieval
        print(f"5. Testing price retrieval:")
        tick = mt5.symbol_info_tick(position.symbol)
        if tick:
            print(f"   Ask: {tick.ask}")
            print(f"   Bid: {tick.bid}")
            price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask
            print(f"   Selected price for {('SELL' if order_type == mt5.ORDER_TYPE_SELL else 'BUY')}: {price}")
        else:
            print(f"   ❌ Failed to get tick for {position.symbol}")
        print()
        
        # Test symbol info
        print(f"6. Testing symbol info:")
        symbol_info = mt5.symbol_info(position.symbol)
        if symbol_info:
            print(f"   Symbol exists: ✅")
            print(f"   Mode: {symbol_info.trade_mode}")  # 0=disabled, 1=closeonly, 2=full
            print(f"   Fill Mode: {symbol_info.trade_fill_mode}")
        else:
            print(f"   ❌ Symbol info not found")
        print()
        
        # Ask user before attempting close
        print(f"7. Ready to attempt close on position {position.ticket}?")
        response = input("   Type 'YES' to close: ").strip().upper()
        
        if response == 'YES':
            print(f"\n   Attempting to close position {position.ticket}...")
            try:
                result = close_position(position)
                print(f"   Result: {result}")
                print(f"   ✅ Close successful" if result.retcode == mt5.TRADE_RETCODE_DONE else f"   ❌ Close failed: {result.comment}")
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        else:
            print("   Skipped close attempt")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("\n8. Disconnecting...")
    mt5.shutdown()
    print("   Done")
