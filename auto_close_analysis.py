#!/usr/bin/env python
"""
Auto-close logic analysis and testing
"""

print("="*70)
print("AUTO-CLOSE LOGIC ANALYSIS")
print("="*70)
print()

print("Current Auto-Close Logic (line 400-401 in Trading_Dashboard.py):")
print("-"*70)
print("""
position_loss_pct = abs(position.profit) / balance * 100 if position.profit < 0 else 0
if position_loss_pct >= auto_close_loss_pct:
    close_position(position)
""")
print()

print("ISSUES IDENTIFIED:")
print("-"*70)
print("""
❌ Issue 1: Loss Percentage Calculation
   Current: abs(position.profit) / balance * 100
   Problem: This calculates loss as % of account balance, NOT position loss
   
   Example:
   - Position profit: -50 (losing 50 units)
   - Account balance: 10,000
   - Calculated loss %: (50 / 10,000) * 100 = 0.5%
   - Auto-close threshold: 1.0%
   - Result: Position WON'T be closed even though it's losing
   
   Better calculation:
   - Calculate loss as % of position's initial margin or entry price
   - OR calculate loss as % of account balance but in more meaningful way

❌ Issue 2: Position Object Properties Unknown
   Current code assumes position.profit contains profit/loss in currency
   Need to verify:
   - Does position.profit contain value in account currency?
   - Is there better way to calculate position loss percentage?
   - Should we use position margin instead of account balance?

⚠️  Issue 3: Auto-close UI Says "Enabled" but May Not Be Triggering
   - Button "Run Auto-Close Now" doesn't actually trigger anything
   - Auto-close only runs on page refresh/auto-refresh cycle
   - No clear feedback if positions were closed
""")
print()

print("RECOMMENDED FIX:")
print("-"*70)
print("""
✅ Solution 1: Calculate Loss Relative to Position Entry Value
   - For each position, calculate the loss as percentage of entry amount
   - This gives more intuitive loss percentage
   
   position_loss_pct = abs(position.profit) / (position.volume * position.price_open * 100000) * 100
   
   This way:
   - If you buy 1 lot at 1.2000 EURUSD ($120,000 notional)
   - Lose $500: loss % = (500 / 120000) * 100 = 0.42%
   - This is a more meaningful percentage

✅ Solution 2: Add Clearer Feedback
   - Log which positions are being checked
   - Show which positions meet auto-close criteria
   - Add debug logging for troubleshooting

✅ Solution 3: Add "Run Auto-Close Now" Button Functionality
   - Currently button does nothing
   - Should immediately trigger auto-close check
   - Should show results
""")
print()

print("="*70)
print("Testing auto-close logic correctness...")
print("="*70)
print()

# Simulate a position
class MockPosition:
    def __init__(self, profit, volume, price_open):
        self.profit = profit
        self.volume = volume  # in lots
        self.price_open = price_open
        self.ticket = 12345
        
position = MockPosition(profit=-500, volume=1, price_open=1.2000)
balance = 10000
auto_close_loss_pct = 1.0

# Current (potentially broken) logic
position_loss_pct_current = abs(position.profit) / balance * 100 if position.profit < 0 else 0

# Better logic (using entry value)
position_entry_value = position.volume * position.price_open * 100000  # Notional value
position_loss_pct_better = abs(position.profit) / position_entry_value * 100 if position.profit < 0 else 0

print(f"Position Details:")
print(f"  Profit/Loss: ${position.profit}")
print(f"  Volume: {position.volume} lot")
print(f"  Entry Price: {position.price_open}")
print(f"  Notional Value: ${position_entry_value:,.0f}")
print()

print(f"Auto-Close Threshold: {auto_close_loss_pct}%")
print()

print(f"Loss % Calculation (CURRENT):")
print(f"  Formula: abs(profit) / balance * 100")
print(f"  Result: {position_loss_pct_current:.2f}%")
print(f"  Status: {'❌ WILL NOT CLOSE' if position_loss_pct_current < auto_close_loss_pct else '✅ WILL CLOSE'}")
print()

print(f"Loss % Calculation (BETTER):")
print(f"  Formula: abs(profit) / entry_value * 100")
print(f"  Result: {position_loss_pct_better:.2f}%")
print(f"  Status: {'❌ WILL NOT CLOSE' if position_loss_pct_better < auto_close_loss_pct else '✅ WILL CLOSE'}")
print()

print("="*70)
print("RECOMMENDATION: Update position_loss_pct calculation")
print("="*70)
