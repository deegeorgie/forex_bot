#!/usr/bin/env python
"""
Analyze current position situation - EMERGENCY MODE VERSION
"""

from datetime import datetime
import config

# Current state
current_positions = 40
current_time = datetime.utcnow()

print("=" * 70)
print("POSITION ANALYSIS REPORT - EMERGENCY MODE")
print("=" * 70)
print(f"Current Time: {current_time.strftime('%Y-%m-%d %H:%M UTC')}")
print(f"Current Open Positions: {current_positions}")
print()

print("CONFIGURATION STATUS:")
print(f"  Session-aware trading: {'ENABLED' if config.ENABLE_SESSION_AWARE_TRADING else 'DISABLED (temporary)'}")
print(f"  MAX_OPEN_POSITIONS: {config.MAX_OPEN_POSITIONS}")
print(f"  Available symbols: {', '.join(config.AVAILABLE_SYMBOLS)}")
print()

print("=" * 70)
print("STATUS ANALYSIS:")
print("=" * 70)

if current_positions <= config.MAX_OPEN_POSITIONS:
    available_slots = config.MAX_OPEN_POSITIONS - current_positions
    print(f"✅ WITHIN LIMIT")
    print(f"   Current: {current_positions} | Max: {config.MAX_OPEN_POSITIONS}")
    print(f"   Available slots: {available_slots}")
    print()
    print("✅ You CAN open new positions and trade today")
else:
    overage = current_positions - config.MAX_OPEN_POSITIONS
    print(f"⚠️  OVER LIMIT by {overage} positions")
    print(f"   Current: {current_positions} | Max: {config.MAX_OPEN_POSITIONS}")
    print()
    print("❌ You CANNOT open new positions")

print()
print("=" * 70)
print("NEXT STEPS:")
print("=" * 70)
print()
print("1. IMMEDIATE (Next 1-2 hours):")
print(f"   • Your 40 positions are now allowed (emergency mode)")
print("   • You can trade and place new orders up to 60 total")
print()
print("2. SHORT-TERM (Next 24 hours):")
print("   • Close ~20-25 positions to reduce to ~15-20")
print("   • This frees margin and reduces risk")
print("   • Prioritize:")
print("     - Losing positions (cut losses, free margin)")
print("     - Oldest positions (take profits)")
print("     - Duplicate symbols (consolidate)")
print()
print("3. THEN RE-ENABLE SESSION-AWARE TRADING:")
print("   • Once at 15-20 positions, we'll re-enable session-aware trading")
print("   • This provides better risk management")
print("   • Edit config.py and change:")
print("     ENABLE_SESSION_AWARE_TRADING = true  # re-enable")
print()
print("=" * 70)
print("⚠️  IMPORTANT: THIS IS TEMPORARY EMERGENCY MODE")
print("=" * 70)
print("Remember to:")
print("• Close positions gradually over next 24 hours")
print("• Re-enable session-aware trading once at ~15 positions")
print("• Reduce MAX_OPEN_POSITIONS back to 50 afterwards")
print()
print()
