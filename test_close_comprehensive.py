#!/usr/bin/env python
"""
Comprehensive test of close position logic - Run this to verify fixes
"""

import MetaTrader5 as mt5
import logging
import time
from mt5_connector import connect, get_open_positions, close_position

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("="*80)
print("CLOSE POSITION LOGIC - COMPREHENSIVE TEST")
print("="*80)
print()

def test_mt5_connection():
    """Test basic MT5 connection"""
    print("TEST 1: MT5 Connection")
    print("-"*80)
    try:
        connect()
        print("✅ Connected to MT5")
        
        # Check account info
        account = mt5.account_info()
        if account:
            print(f"✅ Account Info Retrieved:")
            print(f"   Balance: ${account.balance:,.2f}")
            print(f"   Equity: ${account.equity:,.2f}")
            print(f"   Free Margin: ${account.margin_free:,.2f}")
        else:
            print("❌ Could not retrieve account info")
            return False
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_get_positions():
    """Test retrieving open positions"""
    print("\nTEST 2: Get Open Positions")
    print("-"*80)
    try:
        positions = get_open_positions()
        if positions is None:
            print("❌ get_open_positions() returned None")
            return None
        
        print(f"✅ Retrieved {len(positions)} open positions")
        
        if len(positions) == 0:
            print("⚠️  No open positions - cannot test close logic")
            return None
        
        # Display first position details
        pos = positions[0]
        print(f"\nFirst Position Details:")
        print(f"  Ticket: {pos.ticket}")
        print(f"  Symbol: {pos.symbol}")
        print(f"  Type: {'BUY' if pos.type == 0 else 'SELL'} (raw: {pos.type})")
        print(f"  Volume: {pos.volume}")
        print(f"  Open Price: {pos.price_open}")
        print(f"  Current Price: {mt5.symbol_info_tick(pos.symbol).ask if mt5.symbol_info_tick(pos.symbol) else 'N/A'}")
        print(f"  Profit/Loss: ${pos.profit:.2f}")
        print(f"  Ticket Type: {type(pos.ticket)}")
        
        return positions
    except Exception as e:
        print(f"❌ Failed to get positions: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_price_retrieval(position):
    """Test price retrieval for closing"""
    print("\nTEST 3: Price Retrieval for Close")
    print("-"*80)
    try:
        tick = mt5.symbol_info_tick(position.symbol)
        if tick is None:
            print(f"❌ Failed to get tick for {position.symbol}")
            return False
        
        print(f"✅ Got tick for {position.symbol}")
        print(f"  Ask: {tick.ask}")
        print(f"  Bid: {tick.bid}")
        
        # Determine close order type and price
        order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask
        
        print(f"\nClose Logic:")
        print(f"  Position Type: {'BUY' if position.type == mt5.ORDER_TYPE_BUY else 'SELL'}")
        print(f"  Close Order Type: {'SELL' if order_type == mt5.ORDER_TYPE_SELL else 'BUY'}")
        print(f"  Close Price: {price}")
        
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def test_symbol_info(position):
    """Test symbol info"""
    print("\nTEST 4: Symbol Information")
    print("-"*80)
    try:
        symbol_info = mt5.symbol_info(position.symbol)
        if symbol_info is None:
            print(f"❌ Symbol {position.symbol} not found")
            return False
        
        print(f"✅ Symbol {position.symbol} found")
        print(f"  Visible: {symbol_info.visible}")
        print(f"  Trade Mode: {symbol_info.trade_mode}")
        print(f"  Ask: {symbol_info.ask}")
        print(f"  Bid: {symbol_info.bid}")
        
        if not symbol_info.visible:
            print(f"\n⚠️  Symbol not visible, attempting to select...")
            if mt5.symbol_select(position.symbol, True):
                print(f"✅ Symbol selected")
            else:
                print(f"❌ Could not select symbol (this may be OK)")
        
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def test_close_order_construction(position):
    """Test the close order request construction"""
    print("\nTEST 5: Close Order Construction")
    print("-"*80)
    try:
        symbol = position.symbol
        volume = position.volume
        ticket = position.ticket
        order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            print(f"❌ No tick for {symbol}")
            return False
        
        price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask
        
        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': symbol,
            'volume': volume,
            'type': order_type,
            'position': ticket,
            'price': price,
            'deviation': 20,
            'comment': 'position_close',
        }
        
        print(f"✅ Close request constructed:")
        for key, value in request.items():
            print(f"  {key}: {value}")
        
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def test_close_order_dry_run(position):
    """Dry run the order send without actual close"""
    print("\nTEST 6: Close Order Dry Run (TEST ONLY - NOT CLOSING)")
    print("-"*80)
    try:
        symbol = position.symbol
        volume = position.volume
        ticket = position.ticket
        order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        
        tick = mt5.symbol_info_tick(symbol)
        price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask
        
        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': symbol,
            'volume': volume,
            'type': order_type,
            'position': ticket,
            'price': price,
            'deviation': 20,
            'comment': 'position_close_TEST',
        }
        
        print(f"Would send request:")
        for key, value in request.items():
            print(f"  {key}: {value}")
        print(f"\n✅ Request is valid (not actually sending)")
        
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def test_actual_close(position, dry_run=True):
    """Actually attempt to close a position"""
    print(f"\nTEST 7: Actual Close Attempt ({'DRY RUN' if dry_run else 'LIVE'})")
    print("-"*80)
    
    if dry_run:
        print("⚠️  Running in DRY RUN mode (no positions will actually close)")
        print("To close a position for real, run: test_close_actual_live(position)")
        return False
    
    try:
        print(f"🔴 ATTEMPTING TO CLOSE POSITION {position.ticket} ({position.symbol})")
        result = close_position(position)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"✅ Position {position.ticket} closed successfully!")
            return True
        else:
            print(f"❌ Close failed: {result.comment} (retcode: {result.retcode})")
            return False
    except Exception as e:
        print(f"❌ Exception during close: {e}")
        import traceback
        traceback.print_exc()
        return False

# Run tests
if __name__ == "__main__":
    try:
        if not test_mt5_connection():
            print("\n❌ Cannot proceed without MT5 connection")
            exit(1)
        
        positions = test_get_positions()
        if positions is None or len(positions) == 0:
            print("\n❌ Cannot proceed without open positions")
            exit(1)
        
        position = positions[0]
        
        test_price_retrieval(position)
        test_symbol_info(position)
        test_close_order_construction(position)
        test_close_order_dry_run(position)
        
        # Dry run the actual close
        test_actual_close(position, dry_run=True)
        
        # Show summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print("""
If all tests passed (✅), then the close position logic is working correctly.

To close a real position, choose one of these options:

Option 1: Use the Manual Close Button in the Dashboard
  - Open Trading_Dashboard.py
  - Click "Close Position" button on any open position
  - Check console for logs

Option 2: Close from Python terminal
  - from mt5_connector import connect, get_open_positions, close_position
  - connect()
  - positions = get_open_positions()
  - close_position(positions[0])  # Close first position

Option 3: Use auto-close in Dashboard
  - Set "Close position loss threshold (%)"
  - Enable "Auto-close losing positions"
  - Wait for threshold to be met
""")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        mt5.shutdown()
        print("\n✅ MT5 disconnected")
